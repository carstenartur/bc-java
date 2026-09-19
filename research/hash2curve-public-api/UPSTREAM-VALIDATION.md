# Upstream candidate validation

Date: 19 September 2026. This supersedes the pending-full-build status at the end of `RESULTS-2026-09-19.md`; the measurements and their scope are unchanged. The public API experiment comprises two successful benchmark jobs in one workflow, not two separate workflows.

## Completed repository tests and style

The complete default repository command `test :core:checkstyleMain` succeeded in [run 35450706050](https://github.com/carstenartur/bc-java/actions/runs/35450706050), job 105917796160. The downloaded artifact contains an exit-code receipt of `0`, `BUILD SUCCESSFUL in 38m 30s`, and `98 actionable tasks: 98 executed`. The completed log includes `:core:checkstyleMain`, whose XML contains zero findings.

Recounting the actual JUnit XML independently gives **3,602 test cases, zero failures/errors, and zero skipped cases**:

| Module | Saved JUnit cases |
|---|---:|
| core | 948 |
| prov | 793 |
| pkix | 846 |
| tls | 723 |
| mail | 154 |
| util | 51 |
| mls | 39 |
| pg | 32 |
| misc | 8 |
| tls-klog | 4 |
| pgsc | 3 |
| test | 1 |
| Total | 3,602 |

The separately executed 181-case hash-to-curve suite overlaps core and must not be added to this total. These results describe the default test tasks selected in this Java 25 run, not every optional legacy-JVM configuration. Existing compiler/deprecation warnings remain; a successful build is not a claim that the repository is warning-free.

Artifact: `hash2curve-full-tests-35450706050`, ID `10586983545`, 505,516 bytes.
SHA-256 checked after download: `0f82441e38c1084602e7233e8faf4cd749dbaa011e3edc03e07c6b6f2fbe9b26`.
Actual tested merge checkout: `a7a87a3525bfa806ff4e1b4befe715cc3a0a086f`, corresponding to research head `7325f1866a788060f5d79daf1851d9ae87f14282` on base `ab16374d37c7e18c4090eb8838ebbd72a92593f2`.

## Minimal submission

The minimal candidate is commit `3d56837c3fe6c4a30fc7639b806958649e143210`, branch `perf/hash2curve-constants-upstream`: one commit directly on that upstream base, three files, 152 additions and two deletions. Only four production lines replace two; the rest is test coverage and suite registration. It contains no experimental build dependencies, workflows or reports.

The following source blobs are identical between the fully tested research branch and the minimal candidate:

| File | Git blob |
|---|---|
| GenericSqrtRatioCalculator.java | `693f65df02ea381a25339a2cb9f40106e5b3d35e` |
| GenericSqrtRatioConstantsTest.java | `a79833c5fe3889a05596575a6329b0dbc7acd534` |
| hash2curve/test/AllTests.java | `285530eae79efeb0749ecfc319b3dc26cb9aadad` |

A separately isolated [exact-candidate QA job](https://github.com/carstenartur/bc-java/actions/runs/35453202543) additionally checks out the minimal candidate by SHA and runs the 181-case focused suite plus complete core main-source style. Its workflow is not part of the submitted branch. At this record's creation that supplementary job is still running; its completion is not asserted here.

[Copilot's completed Lite review](https://github.com/carstenartur/bc-java/pull/2#pullrequestreview-5256274437) reports no findings. This is an automated review, not a human approval or a cryptographic audit. Normal upstream maintainer review is still required.

## Performance scope

The [fixed public-API experiment](README.md) and [full measured report](RESULTS-2026-09-19.md) show 14.13% and 14.79% less elapsed time for `getInstance(...).hashToCurve(message)` in the respective Java 21 and Java 25 jobs, across the three tested NIST profiles with 64 rotating 32-byte messages. All six primary intervals are separated; all six reused-instance controls overlap. Source/JAR hashes, all 360 primary samples, and the 201-point exact transcript in each environment were rechecked after download.

This is a small initialization optimization, not a faster steady-state hash algorithm, JVM cold-start measurement, all-curve claim, or security improvement. The mathematical rewrite was supplied during AI-assisted development, not discovered autonomously by Regelsuche. No main branch, cryptographic parameter or repository protection setting was changed.
