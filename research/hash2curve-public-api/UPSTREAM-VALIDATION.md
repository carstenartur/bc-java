# Upstream candidate validation and submission

Date: 19 September 2026. This supersedes the pending-full-build status in `RESULTS-2026-09-19.md`; the measurements and their scope are unchanged. The public API experiment comprises two successful benchmark jobs in one workflow.

## Completed repository tests and style

The complete default repository command `test :core:checkstyleMain` succeeded in [run 35450706050](https://github.com/carstenartur/bc-java/actions/runs/35450706050), job 105917796160. The downloaded artifact contains exit-code receipt `0`, `BUILD SUCCESSFUL in 38m 30s`, and `98 actionable tasks: 98 executed`. The core main-source Checkstyle XML contains zero findings.

Independent recounting of the JUnit XML gives **3,602 cases, zero failures/errors and zero skipped cases**:

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

The focused 181-case hash-to-curve suite overlaps core; do not add it to this total. These are the default tasks selected in this Java 25 run, not every optional legacy-JVM configuration. Existing compiler/deprecation warnings remain.

Artifact `10586983545`, `hash2curve-full-tests-35450706050`, 505,516 bytes, downloaded SHA-256:
`0f82441e38c1084602e7233e8faf4cd749dbaa011e3edc03e07c6b6f2fbe9b26`.
Tested merge checkout: `a7a87a3525bfa806ff4e1b4befe715cc3a0a086f`, research head `7325f1866a788060f5d79daf1851d9ae87f14282`, base `ab16374d37c7e18c4090eb8838ebbd72a92593f2`.

## Exact minimal candidate also verified

Candidate commit `3d56837c3fe6c4a30fc7639b806958649e143210`, branch `perf/hash2curve-constants-upstream`, is one commit directly on that upstream base: three files, 152 additions and two deletions. Only four production lines replace two; the rest is tests and suite registration. No experimental dependencies, workflows or reports are included.

Source blobs are identical to the fully tested research branch:

| File | Git blob |
|---|---|
| GenericSqrtRatioCalculator.java | `693f65df02ea381a25339a2cb9f40106e5b3d35e` |
| GenericSqrtRatioConstantsTest.java | `a79833c5fe3889a05596575a6329b0dbc7acd534` |
| hash2curve/test/AllTests.java | `285530eae79efeb0749ecfc319b3dc26cb9aadad` |

The additional [exact-candidate QA run 35453202543](https://github.com/carstenartur/bc-java/actions/runs/35453202543), job 105923832520, **also completed successfully**. It checked out this precise candidate SHA, ran all 181 hash-to-curve cases without failures/errors/skips, and checked every core main-source file with zero Checkstyle findings. Its workflow lives only in a separate validation branch.

Artifact `10587293581`, `upstream-candidate-qa-35453202543`, 35,189 bytes, downloaded SHA-256:
`399d8e11ec442c508eefb37ee83213e5927be8931857d00b7b94440cc1360a30`.
The source receipt, JUnit XML, Checkstyle XML, zero exit code and terminal `BUILD SUCCESSFUL` were independently checked after download.

[Copilot's completed Lite review](https://github.com/carstenartur/bc-java/pull/2#pullrequestreview-5256274437) reports no findings. This is an automated review, not human approval or a cryptographic audit. Normal upstream maintainer review is still required.

## Public API effect and limits

The [fixed experiment](README.md) and [measured report](RESULTS-2026-09-19.md) show 14.13% and 14.79% less elapsed time for `getInstance(...).hashToCurve(message)` in the respective Java 21 and Java 25 jobs. All three tested NIST profiles and all 64 rotating 32-byte messages were retained. All six primary intervals are separated; all six reused-instance controls overlap. All 360 primary samples, artifact/source hashes, the single-entry JAR differences, and the 201-point transcript per environment were rechecked.

This is an initialization optimization, not a faster steady-state hash algorithm, cold-start measurement, all-curve claim or security improvement. The rewrite was supplied during AI-assisted development, not discovered autonomously by Regelsuche.

## Submission access block

After the above gates passed, creation of a ready-for-review PR in `bcgit/bc-java` was attempted with head `carstenartur:perf/hash2curve-constants-upstream` and base `main`. GitHub returned **HTTP 403: Resource not accessible by integration**. No upstream PR was created. The installed GitHub integration is available for fork writes, but this upstream write was denied. No permission or branch-protection settings were changed.

The reviewed minimal patch is in [fork PR #2](https://github.com/carstenartur/bc-java/pull/2). The upstream comparison is prepared here:

[Open upstream PR creation](https://github.com/bcgit/bc-java/compare/main...carstenartur:bc-java:perf/hash2curve-constants-upstream?expand=1)

Use the title `Reuse a modular power when initializing generic sqrt_ratio constants`, describe only the initialization improvement, and link this validation record and the public-API measurements. The prepared full submission text is provided with the evidence bundle. Submitting in the user's GitHub session is the remaining action; main branches remain unchanged.
