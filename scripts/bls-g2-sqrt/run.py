#!/usr/bin/env python3
"""Run independent, alternating JMH forks and retain raw measurements."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]
CLASS = "org.bouncycastle.crypto.bls.BLSG2SqrtBenchmark"
SOURCE = "core/src/main/java/org/bouncycastle/crypto/bls/BLS12_381G2HashToCurve.java"
METHODS = (
    "sqrtOrSqrtZ", "hashToCurve", "signReusedKey", "signFreshKey",
    "verifyReusedKey", "verifyFreshKey",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk", type=Path, required=True, help="JDK 21 installation")
    parser.add_argument("--baseline", default="6560e91d0a164b8ab58266f141ee6daeec21a340")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--seconds", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if min(args.rounds, args.warmup, args.iterations, args.seconds) < 1:
        parser.error("all run counts and durations must be positive")

    java = str(args.jdk.resolve() / "bin/java")
    javac = str(args.jdk.resolve() / "bin/javac")
    build = ROOT / "core/build/bls-sqrt"
    classpath = (build / "classpath.txt").read_text().strip()
    baseline_source = subprocess.check_output(
        ["git", "show", args.baseline + ":" + SOURCE], cwd=ROOT
    )
    current_source = (ROOT / SOURCE).read_bytes()
    classpaths = {}
    for variant, source in (("baseline", baseline_source), ("optimized", current_source)):
        source_file = build / (variant + "-source/org/bouncycastle/crypto/bls/BLS12_381G2HashToCurve.java")
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_bytes(source)
        classes = build / variant
        classes.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [javac, "--release", "11", "-Xlint:all", "-Werror", "-proc:none", "-implicit:none",
             "-cp", classpath, "-d", str(classes), str(source_file)],
            cwd=ROOT, check=True,
        )
        classpaths[variant] = str(classes) + os.pathsep + classpath
    fingerprints = {}
    for variant, cp in classpaths.items():
        fingerprints[variant] = subprocess.check_output(
            [java, "-XX:-UsePerfData", "-Xmx512m", "-cp", cp, CLASS],
            cwd=ROOT, text=True,
        ).strip()
    if fingerprints["baseline"] != fingerprints["optimized"]:
        raise RuntimeError("canonical hash-to-curve/signature outputs differ")

    cpu_model = "unknown"
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        cpu_model = next((line.split(":", 1)[1].strip()
                          for line in cpuinfo.read_text().splitlines()
                          if line.startswith("model name")), "unknown")
    result = {
        "baselineRevision": args.baseline,
        "workingRevision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "sourceSha256": {"baseline": hashlib.sha256(baseline_source).hexdigest(),
                         "optimized": hashlib.sha256(current_source).hexdigest()},
        "canonicalOutputSha256": fingerprints["baseline"],
        "javaVersion": subprocess.check_output(
            [java, "-version"], stderr=subprocess.STDOUT, text=True).strip(),
        "platform": platform.platform(),
        "cpuModel": cpu_model,
        "logicalCpus": os.cpu_count(),
        "rounds": args.rounds,
        "warmupIterations": args.warmup,
        "measurementIterations": args.iterations,
        "secondsPerIteration": args.seconds,
        "seed": "0x3819380",
        "messageBytes": 32,
        "messageCount": 16,
        "fieldInputCount": 256,
        "forkOrder": "baseline/optimized in even rounds; optimized/baseline in odd rounds",
        "runs": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    logs = build / "runs"
    logs.mkdir(parents=True, exist_ok=True)
    for method in METHODS:
        for round_number in range(args.rounds):
            variants = ("baseline", "optimized") if round_number % 2 == 0 else ("optimized", "baseline")
            for variant in variants:
                name = method + "-" + str(round_number) + "-" + variant
                raw_json = logs / (name + ".json")
                command = [java, "-XX:-UsePerfData", "-cp", classpaths[variant],
                           "org.openjdk.jmh.Main", "^" + CLASS + r"\." + method + "$",
                           "-f", "1", "-t", "1", "-wi", str(args.warmup),
                           "-i", str(args.iterations), "-w", str(args.seconds) + "s",
                           "-r", str(args.seconds) + "s", "-prof", "gc", "-rf", "json",
                           "-rff", str(raw_json), "-foe", "true",
                           "-jvmArgs", "-Xms512m -Xmx512m -XX:-UsePerfData"]
                started = time.time()
                with (logs / (name + ".log")).open("w") as log:
                    subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
                measurements = json.loads(raw_json.read_text())
                if len(measurements) != 1:
                    raise RuntimeError("expected exactly one JMH result for " + name)
                result["runs"].append({"variant": variant, "round": round_number,
                                       "startedUnixSeconds": started, "jmh": measurements[0]})
                # Checkpoint every completed fork. Logs and classes stay in the ignored build tree.
                args.output.write_text(json.dumps(result, separators=(",", ":")) + "\n")
                score = measurements[0]["primaryMetric"]["score"]
                print(name + ": %.3f us/op" % score, flush=True)
    print("Results: " + str(args.output), flush=True)


if __name__ == "__main__":
    main()
