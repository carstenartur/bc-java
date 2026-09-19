# Public-API transfer experiment (fixed plan)

This fork-only follow-up answers whether the already measured constant-initialization change also reduces the cost of `HashToEllipticCurve.getInstance(profile, dst).hashToCurve(message)`. It does not modify the previous calculator experiment. Commit this plan and harness before the first timings. Keep research infrastructure out of the upstream production patch.

## Exact comparison

Baseline commit: `ab16374d37c7e18c4090eb8838ebbd72a92593f2`.
Calculator source blobs: baseline `acf5666f51eb82688878bde8c447a58b6bdd73d1`, optimized `693f65df02ea381a25339a2cb9f40106e5b3d35e`.

Build the current core once. Compile both calculator sources with the same compiler and flags (`--release 8 -g:none`) and insert them into otherwise identical core JARs. Both variants have the original class and method names. Reject any other differing JAR entry. The JMH harness does not include BC classes; each fork loads exactly one variant. This avoids the differently named legacy classes used by the preceding experiment.

## Predeclared cases

Three real public profiles: P256_XMD_SHA_256, P384_XMD_SHA_384, P521_XMD_SHA_512. Do not extrapolate to the public Curve25519 suite, which uses a different mapping.

Three workloads, each returning its actual API result to JMH:
- `getInstance`: full factory call, no hash.
- `createAndHash` (primary): factory call and one complete `hashToCurve` call.
- `reuseHash` (control): hash with an already-created instance. Its algorithm is unchanged.

All hash timings rotate through 64 deterministic 32-byte messages (seed 938019). Message creation and point encoding are outside timing. A constant test-specific domain separation tag is used for both variants. Before timing, compare 201 exact encoded points (67 inputs including empty, abc and a 256-byte message, on each profile); fresh and reused objects must agree too. Each JMH trial checks all 67 outputs for its profile against the baseline transcript before measurement. These differential checks supplement, not replace, the existing RFC vector tests.

JMH 1.37, average time in microseconds/op; 2 forks, 3 x 500ms warmups and 5 x 500ms measurements; 1 thread, GC profiler, 256/512 MB initial/max heap. Nine case pairs per JVM, 18 invocations, 180 primary samples. Fixed field/workload order, alternating which variant is measured first by pair. No case selection, threshold tuning or timing-based CI pass gate. Report all time/error/allocation values, equal-profile geometric ratios and all reuse controls. JVM 21 and 25 run on separate hosted jobs; do not compare absolute times across different machines.

These are warm-JVM allocation/first-use costs, not JVM cold start, a server workload, a threading guarantee or a security improvement. Independence of JIT/runner effects is not assumed. A full test/style run is separately required for merge readiness.

## Run

From a checkout of this experiment branch with JDK 25, Maven and Python 3.9+:

```sh
git fetch --no-tags --depth=1 origin ab16374d37c7e18c4090eb8838ebbd72a92593f2
./gradlew --no-daemon --max-workers=2 -Dorg.gradle.jvmargs=-Xmx2g :core:classes
python3 research/hash2curve-public-api/prepare.py
python3 -m unittest discover -s research/hash2curve-public-api -v
# Choose benchmark JAVA_HOME (21 or 25), then:
python3 research/hash2curve-public-api/run.py
```

The standalone preparation also accepts `--core-jar`, `--baseline-source` and `--optimized-source` for repeating against a downloaded current-core artifact. Source hashes and single-entry JAR equality checks are still mandatory. Raw data, logs, command lines, sources/JAR hashes and exit status are preserved under `evidence/`. The existing calculator benchmarks and full-test workflow are left unchanged.
