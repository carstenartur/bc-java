#!/usr/bin/env python3
"""Prepare an exact-source baseline and an uninstrumented current-core JAR."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "ab16374d37c7e18c4090eb8838ebbd72a92593f2"
SOURCE = "core/src/main/java/org/bouncycastle/crypto/hash2curve/impl/GenericSqrtRatioCalculator.java"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    old = git("show", BASE + ":" + SOURCE)
    expected_blob = "acf5666f51eb82688878bde8c447a58b6bdd73d1"
    blob = hashlib.sha1(b"blob " + str(len(old)).encode() + b"\0" + old).hexdigest()
    if blob != expected_blob:
        raise RuntimeError("Frozen baseline source hash mismatch")
    current = (ROOT / SOURCE).read_bytes()
    marker = b"    public SqrtRatio sqrtRatio"
    if marker not in old or marker not in current or old[old.index(marker):] != current[current.index(marker):]:
        raise RuntimeError("The reuse control requires a byte-identical sqrtRatio method")
    generated = HERE / "src/main/java/org/bouncycastle/crypto/hash2curve/impl/LegacyGenericSqrtRatioCalculator.java"
    generated.parent.mkdir(parents=True, exist_ok=True)
    generated.write_bytes(old.replace(b"GenericSqrtRatioCalculator", b"LegacyGenericSqrtRatioCalculator"))
    classes = ROOT / "core/build/classes/java/main"
    if not (classes / "org/bouncycastle/crypto/hash2curve/impl/GenericSqrtRatioCalculator.class").is_file():
        raise RuntimeError("Run ./gradlew :core:classes before preparing the benchmark")
    library = HERE / "lib/bc-core.jar"
    library.parent.mkdir(exist_ok=True)
    command = ["jar", "cf", str(library), "-C", str(classes), "."]
    resources = ROOT / "core/build/resources/main"
    if resources.is_dir():
        command += ["-C", str(resources), "."]
    subprocess.run(command, check=True)
    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    paths = [ROOT / SOURCE, generated, HERE / "pom.xml", HERE / "prepare.py", HERE / "run.sh",
             HERE / "src/main/java/org/bouncycastle/research/hash2curve/ConstantsBenchmark.java", library]
    metadata = {"baseline_commit": BASE, "baseline_source_blob": blob,
                "checkout_commit": git("rev-parse", "HEAD").decode().strip(),
                "platform": platform.platform(),
                "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (evidence / "sources.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
