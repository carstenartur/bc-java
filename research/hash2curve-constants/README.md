# Shared constants in generic sqrt_ratio

This is a fork-only, reproducible experiment, separate from the cryptographic library's build and API. No timing result is assumed by this plan.

## Change and proof

Baseline: `ab16374d37c7e18c4090eb8838ebbd72a92593f2`.
Baseline calculator blob: `acf5666f51eb82688878bde8c447a58b6bdd73d1`.

RFC 9380 F.2.1.1 defines `c6 = z^c2` and `c7 = z^((c2+1)/2)` in the prime field. Since `c2 = 2*c3+1`, set `t = z^c3`, `c7 = t*z`, and `c6 = t*c7`, reducing after each multiplication. This saves one modular exponentiation; it does not use an inverse or assume `c3 > 0`. Negative/unreduced bases are covered. The public parameters and the complete `sqrtRatio` method remain unchanged.

Reference: https://www.rfc-editor.org/rfc/rfc9380.html#name-sqrt_ratio-for-any-field

This does not prove constant-time execution of Java BigInteger. It adds no secret-dependent branch or table lookup; it is only a rewrite of public-parameter initialization. It is not a new cryptographic algorithm and not an autonomous Regelsuche discovery.

## Fixed measurement plan

Commit this plan and the harness before running the first hosted timings. Do not adjust the cases or settings in response to their results.

- JVMs: Temurin 21 and 25, on separate GitHub-hosted Ubuntu jobs; report each environment separately.
- Fields: P-256 (`z=-10`), P-384 (`z=-12`), P-521 (`z=-4`), and the Curve25519 prime (`z=2`). The last uses a field-only test curve, not a new hash-to-curve suite.
- Primary: construction of the actual calculator object, baseline versus optimized.
- Secondary: construction followed by one ratio operation.
- Negative control: repeated use of an existing calculator. Its computational method must be byte-identical to the baseline.
- JMH 1.37: average time, microseconds, two forks, three 500 ms warmups, five 500 ms measurements, one thread, GC profiler, 256/512 MB initial/max heap. All 24 workload/field/variant combinations are mandatory.
- Before every trial: compare exact roots and flags on the same 64 deterministic inputs, seed 9380, including zero and boundary numerators. Setup work is outside measurement.
- Report all means, JMH 99.9% error intervals, normalized allocation, and equal-field geometric ratios. No post-hoc selection of favorable cases. There is no flaky shared-runner speed threshold in CI.

`prepare.py` extracts the entire legacy class from the pinned Git commit, checks its blob hash, and renames only the class/constructor. It refuses to benchmark a changed `sqrtRatio` method. The optimized class is compiled from the current checkout, not obtained from Maven Central. The ordinary library build gets no additional benchmark dependencies.

## Reproduce

From the repository root with JDK 25, Maven, Python 3.9+, and a `bcgit/bc-test-data` checkout available via `BC_TEST_DATA_HOME`:

```sh
git fetch --no-tags --depth=1 origin ab16374d37c7e18c4090eb8838ebbd72a92593f2
./gradlew --no-daemon --max-workers=2 -I research/hash2curve-constants/ci.gradle :core:test --tests org.bouncycastle.crypto.hash2curve.test.AllTests
python3 research/hash2curve-constants/report_tests.py .
./gradlew --no-daemon --max-workers=2 :core:classes
python3 research/hash2curve-constants/prepare.py
# Select the desired benchmark JVM (21 or 25), then:
bash research/hash2curve-constants/run.sh
```

The Actions workflow also runs the root `test` task and `:core:checkstyleMain` in a separate job. JVM limits in `ci.gradle` change runner resource use, not test selection. The full suite is distinct from the focused hash-to-curve suite and the differential setup checks.

Raw JSON, JMH logs, CPU/JVM details, source hashes, and runnable benchmark/core JARs are uploaded together. `summarize.py` rejects missing pairs, duplicate pairs, wrong units, and incomplete fork samples. Its own tests run with:

```sh
cd research/hash2curve-constants
python3 -m unittest -v test_summarize
```

## Local preliminary evidence (not a full BC build)

Before changing the production constructor, its four directly needed source files were exported and checked against their Git blob hashes. On OpenJDK 21.0.11, using the locally installed `bcprov-1.80.jar` only for supporting EC/util classes, a direct Java smoke test passed 1,840 constant-pair comparisons and 1,240 nonzero ratio equations, then failed exactly at the new operation-count requirement (`expected 1, got 2`). After the rewrite, the same checks passed with one exponentiation. This mixed-dependency smoke test is supplementary; it must not be presented as the current repository's full JUnit suite or as JMH evidence.

A timing claim requires completed hosted measurements. Initialization improvements do not imply faster steady-state hashing, RSA key generation, or greater cryptographic security.
