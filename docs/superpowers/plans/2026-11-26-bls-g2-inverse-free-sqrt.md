# BLS G2 inverse-free square root implementation plan

> **For agentic workers:** Use the executing-plans workflow. This optimization is already approved; no further design approval is required.

**Goal:** Remove the non-real square root's inversion and possible second exponentiation while preserving RFC 9380 and BLS outputs.

**Architecture:** Keep `sqrtOrSqrtZ`, its norm construction, the real-input branch, and the map's sign normalization. Replace only the non-real branch of `sqrtOfSquare` with the known inverse-square-root construction for primes congruent to 3 modulo 4.

**Tech stack:** Java 8-compatible core sources, JUnit 3-style tests, existing Gradle build, JMH.

**Spec:** The approved task: for `delta=(a+g)/2`, `t=delta^((p-3)/4)`, `c=delta*t`, and `d=b*t/2`, return `(c,d)` if `c^2=delta`, otherwise `(d,-c)`.

## Constraints and review focus

- No public API change, broad field-arithmetic refactor, constant-time claim, or novelty claim.
- Preserve zero, real residues, real non-residues, and non-squares whose `Z` multiple is real.
- Exercise both quadratic-character branches and compare roots up to sign with the previous formula.
- Existing RFC intermediate/final vectors and BLS vectors must pass.
- Enable warnings for the changed main, test, and benchmark sources and fail their strict compile on warnings; retain the existing build gates.
- Benchmark the same seeded workloads on the exact upstream baseline and optimized code, with multiple forks, warmup, consumed results, allocation data, and raw JSON.

## Task 1: Characterize, implement, and verify

- [x] Add deterministic edge cases and a transcription of the previous formula to `BLS12_381G2HashToCurveTest`.
- [x] Compile and run those tests on baseline `6560e91d0a164b8ab58266f141ee6daeec21a340` before changing production code.
- [x] Change `BLS12_381G2HashToCurve.sqrtOfSquare` and update its explanation.
- [x] Run the focused tests, registered BLS/RFC suite, main-source style gate, strict main/test compile, and attempt the core test suite. Record pre-existing diagnostics and the incomplete broader run explicitly.

## Task 2: Measure and document

- [x] Add a focused, reusable JMH runner under `scripts/bls-g2-sqrt` for the sqrt primitive, hash-to-curve, and full sign/verify with reused and freshly constructed keys.
- [x] Run paired baseline/optimized measurements under one JDK and identical JVM/workload settings; retain compact raw JSON.
- [x] Document the field identity, sign equivalence, prior work, exact methodology, results, and limitations in `docs/benchmarks/bls-g2-sqrt.md`.
- [x] Review the diff and fresh verification evidence, then commit locally for the parent agent to publish.

## Execution decisions

- Correctness tests are intentionally expected to pass before and after this behavior-preserving optimization. The approved task explicitly rejects artificial API changes or mocks merely to manufacture a failing test.
- Work uses the dedicated fresh checkout and branch `optimize/bls-g2-inverse-free-sqrt`; no other checkout is modified.
- The normal Java 8 compilation is retained. The additional strict diagnostics compilation targets Java 11 because the current JDK 21 compiler warns that the Java 8 target option itself is obsolete; no javac lint category is disabled. The repository's Error Prone check policy is retained, with the touched test explicitly enabled.
- Independent review found no arithmetic, sign-compatibility, or benchmark-comparability blocker. Its diagnostics-policy wording correction is included in the report.
- The optional full-core run was stopped after more than twelve minutes in unrelated post-quantum suites, with no reported failure but no completed result. The registered 220-test hash-to-curve/BLS suite passed; the parent directed prioritizing the requested JMH measurements after the changed paths were sufficiently verified.
- All 36 measurement forks completed. Final validation checked 288 primary timing samples, matching source hashes, the canonical-output fingerprint, another passing 220-test suite run against the timed optimized class, and fresh/reused key-path output checks for both variants. Verification timing remains unresolved and is reported that way.
