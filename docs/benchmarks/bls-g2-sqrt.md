# Inverse-free square roots in BLS12-381 G2 hash-to-curve

## Change and scope

The non-real branch of `BLS12_381G2HashToCurve.sqrtOfSquare` now derives both root coordinates from one inverse-square-root exponentiation. It removes one per-call `BigInteger.modInverse` and the second, conditional exponentiation used when the first candidate is a non-residue. The outer norm calculation, the real-input branch, SWU selection, isogeny, cofactor clearing, and RFC sign normalization retain their existing implementations.

The comparison baseline is upstream commit `6560e91d0a164b8ab58266f141ee6daeec21a340`. This is a local application of known combined square-root/inversion techniques, not a new mathematical algorithm. See Michael Scott, [A note on the calculation of some functions in finite fields: Tricks of the Trade](https://eprint.iacr.org/2020/1497.pdf), especially the quadratic-extension square-root discussion in section 6.3 of the inspected version.

## Field identity

All equations in this section are in the prime field. Let `p = 3 (mod 4)`, let `I^2 = -1`, and suppose the caller supplies `a`, `b`, and `g` with

```
g^2 = a^2 + b^2.
```

For the non-real case `b != 0`, define

```
delta   = (a + g)/2
t       = delta^((p - 3)/4)
c       = delta*t
d       = b*t/2
epsilon = delta*t^2 = delta^((p - 1)/2).
```

`delta` cannot be zero: `a + g = 0` would imply `g^2 = a^2`, hence `b^2 = 0`, contradicting `b != 0`. Euler's criterion therefore gives `epsilon` equal to either `1` or `-1`.

The norm identity yields

```
delta^2 - b^2/4 = a*delta.
```

Multiplying by `t^2` and expanding the imaginary coordinate gives

```
c^2 - d^2 = epsilon*a
2*c*d     = epsilon*b
(c+d*I)^2 = epsilon*(a+b*I).
```

If `epsilon = 1`, `(c,d)` is a root. If `epsilon = -1`, multiplication by `-I` gives the root `(d,-c)`, because `(-I)^2 = -1`. The code tests `c^2 == delta`; since `c^2 = epsilon*delta` and `delta != 0`, this is equivalent to testing `epsilon == 1`. It needs no extra exponentiation to decide the branch. This reasoning permits either choice of the supplied norm root `g`.

The existing `b == 0` branch remains necessary. For a real input, `s = a^((p+1)/4)` satisfies `s^2 = a` or `s^2 = -a`, so `(s,0)` or `(0,s)` is a root respectively. It also returns zero for zero. Treating that case separately avoids the possible `delta = 0` in the inverse-square-root construction.

## Compatibility of root signs

The helper promises an arbitrary root of `w`, or of `Z*w` when `w` is a non-square. The optimized helper can select the negative of the old root. That is permitted by the helper contract: a nonzero square in a field of odd characteristic has exactly two roots, differing by sign.

`mapToCurveAndIso3` subsequently chooses the sign using the existing `u.sgn0() != yPrime.sgn0()` comparison. Thus both root choices produce the same normalized curve point. This is the sign choice specified by [RFC 9380, section 6.6.2 and Appendix F.2](https://www.rfc-editor.org/rfc/rfc9380.html). The existing [Appendix J.10.1](https://www.rfc-editor.org/rfc/rfc9380.html#appendix-J.10.1) tests compare the actual intermediate and final coordinates, not merely their squares.

The class remains variable time and works on values derived from the public message. The change makes no constant-time claim for `BigInteger` arithmetic or this hash-to-curve implementation.

## Verification

The tests were added and run against the unchanged upstream implementation before the production edit. A behavior-preserving performance change is expected to pass both before and after the edit.

- The G2 test class contains 11 tests, including the existing RFC coordinate vectors.
- Fourteen explicit new fixtures cover zero, real residues, real non-residues, purely imaginary inputs, both non-real quadratic-character branches, and non-squares whose `Z` multiple is real. `7 + 13*I` exercises `epsilon = 1`; `2*I` exercises `epsilon = -1`.
- A 256-input deterministic differential test transcribes the old inversion-based formula. It checks the square/non-square verdict, squares the returned root, and compares old and new roots up to sign. The seed is `0x3819380`.
- The registered `org.bouncycastle.crypto.hash2curve.test.AllTests` suite passed 220 tests on the baseline and after the change. It includes the RFC G1/G2 vectors, BLS Basic/Augmentation/Proof-of-Possession schemes, Eth2 known-answer tests, serialization, subgroup checks, key generation, and `BLSSigner`.
- The broader `:core:cleanTest :core:test` run was started and then stopped after more than twelve minutes while unrelated post-quantum vector suites were still executing. It had reported no failure before interruption, but did not complete and is **not** claimed as passing. The completed verification covers the registered hash-to-curve/BLS suite and the strict touched-source gates described here.
- The benchmark runner additionally requires byte-identical SHA-256 fingerprints of the encoded public key, 16 compressed hash-to-curve outputs, and 16 compressed signatures, and verifies those signatures under both implementations before timing.
- After timing, the exact optimized class used by JMH passed the registered 220-test suite again. A separate strict-compiled sanity check also compared fresh/reused signing outputs and confirmed both verification paths for all 16 benchmark messages, under both baseline and optimized class overlays.

### Compiler and style gates

The ordinary core build keeps the repository's Java 8 release target and existing Error Prone settings. The untouched baseline emits 39 main-source diagnostics and three Java-8-option diagnostics from the test compilation on the available JDK 25; they are not introduced by this change.

The optional `benchmark.gradle` init script creates separate compile tasks for the touched main class, touched test class, and benchmark. They use `-Xlint:all -Werror` and explicitly enable Error Prone for main **and test** sources. The test opt-in matters because the repository's root build ordinarily disables Error Prone on test tasks. No javac lint category is disabled; the repository's existing Error Prone check policy is retained. The JDK 21 compiler uses `--release 11` for this additional diagnostics pass because current JDK 21 also warns that the `--release 8` option itself is obsolete; the ordinary compilation still checks Java 8 compatibility. Error Prone on JDK 21 also requires `-XDaddTypeAnnotationsToSymbol=true`.

All three strict compile tasks completed without warnings. `:core:checkstyleMain` also passed for the full main source tree. A final `:core:blsSqrtCheck` run passed all 11 focused tests. Gradle reports existing build-script deprecations separately; they are not Java source diagnostics.

## Benchmark design and reproduction

The runner uses the repository's existing JMH 1.33 dependency. Only the changed class is recompiled for each variant: its exact baseline source is read with `git show`, and its current source is read from the checkout. Both are compiled with the same compiler, release target, and flags. Each variant's class directory precedes the same common runtime classpath. The common classes are the Gradle main outputs, without the packaged multi-release JAR overlays. The raw results record both source hashes so an uncommitted working-tree edit remains identifiable.

In the recorded run, `workingRevision` is the checkout's HEAD before the local implementation commit, while the patch was present in the working tree. `sourceSha256.optimized` binds the exact tested production source. The observed metadata is retained as recorded; it is not retrospectively replaced with the later commit ID.

The six methods measure the square-root helper, full `hashToCurve`, full serialized signing with reused/fresh private-key objects, and full serialized verification with reused/fresh public-key objects. Fresh means constructing a new key object from the same encoding on every invocation; it does not include generating a new random key. Fresh verification includes public-key decompression and constructor validation. Both signing modes create a new `BLSSigner`, initialize it, feed the whole message, and return the encoded signature; verification similarly creates a signer and consumes an encoded signature. JMH consumes every returned result.

Inputs use deterministic `java.util.Random(0x3819380)` data: 256 field elements and sixteen 32-byte messages. These are reproducible benchmark fixtures, not production key material. Every variant receives the same inputs and encoded keys. Setup and signature preparation are outside the timing loop.

For each method there are three independent forks per variant, five one-second warmup iterations and eight one-second measurement iterations. Baseline then optimized is run in rounds 0 and 2; the order is reversed in round 1. Each fork has one benchmark thread and a fixed 512 MiB heap. `-prof gc` collects allocation and collection metrics. `-XX:-UsePerfData` avoids unrelated runtime counter-file collisions in the container and is identical for both variants.

Build the ordinary sources and the optional strict/benchmark tasks with JDK 25 as the Gradle runtime and a full JDK 21 available through `BC_JDK21`:

```sh
JAVA_HOME=/path/to/jdk25 BC_JDK21=/path/to/jdk21 ./gradlew \
  --no-daemon --max-workers=2 -I scripts/bls-g2-sqrt/benchmark.gradle \
  :core:compileJava :core:compileTestJava :core:blsSqrtCheck \
  :core:blsSqrtBenchmarkClasspath :core:checkstyleMain

python3 scripts/bls-g2-sqrt/run.py --jdk /path/to/jdk21 \
  --output docs/benchmarks/bls-g2-sqrt-results.json
```

Run the timed command after builds and tests have finished. The runner checkpoints compact raw JMH JSON after every completed fork. Full console logs, generated sources, and class files remain in the ignored `core/build/bls-sqrt` directory. All run counts can be overridden explicitly; the checked-in evidence uses the stated defaults.

The broader core suite can be run separately with `./gradlew :core:cleanTest :core:test`; it is not a prerequisite for the benchmark and was not completed in this measurement session.

## Measurement interpretation

This benchmark measures one runtime, machine, message size, and workload. The arithmetic removes the stated operations independently of the timing result, but signing and verification spend much of their time in scalar multiplication, serialization, subgroup checks, and pairings. A clear improvement in the isolated helper need not yield a statistically separable end-to-end change. Timing confidence intervals and allocation measurements must be considered alongside the point estimates; a paired speedup interval containing 1 does not resolve a gain in this experiment.

## Recorded results

Measured on 2026-11-26 in a Linux container on an AMD EPYC 7763, with nine logical CPUs visible, using Temurin OpenJDK 21.0.13.1+2-LTS. Builds, tests, and other deliberate CPU-heavy work were stopped before timing. CPU affinity and host frequency were not fixed, so these results describe this environment rather than every deployment.

All 36 forks completed successfully. The [compact raw results](bls-g2-sqrt-results.json) retain all 288 primary timing samples, per-fork identities and timestamps, and the GC profiler's raw allocation/collection measurements. The combined canonical-output fingerprint was identical for both variants:

```
d5fe8cfd4f6e8eacb458c24e6707baf34e6d80b3201915594c5808b760a44c85
```

Times below are the arithmetic means of the three independent fork means. Speedup is the geometric mean of the three paired baseline/optimized time ratios; values above 1 favor the optimized implementation. The 95% interval is calculated on those three log ratios with Student's t critical value `4.302652729911275` (two degrees of freedom), then exponentiated. This treats the independent fork pairs as the units of replication, rather than treating all iterations within one fork as independent experiments. The raw files also retain JMH's own per-fork statistics.

| Operation | Baseline (us/op) | Optimized (us/op) | Paired speedup, 95% interval | Interpretation |
| --- | ---: | ---: | ---: | --- |
| `sqrtOrSqrtZ` | 133.85 | 90.96 | 1.4714 [1.4198, 1.5249] | 32.0% lower mean latency |
| `hashToCurve` | 1171.98 | 1074.95 | 1.0903 [1.0843, 1.0963] | 8.3% lower mean latency |
| Sign, reused key | 2833.38 | 2734.38 | 1.0362 [1.0176, 1.0552] | 3.5% lower mean latency |
| Sign, fresh key object | 2832.03 | 2714.98 | 1.0431 [1.0273, 1.0592] | 4.1% lower mean latency |
| Verify, reused key | 7663.46 | 7547.35 | 1.0154 [0.9996, 1.0315] | No resolved gain; interval includes 1 |
| Verify, fresh key object | 7923.41 | 7926.82 | 0.9997 [0.9653, 1.0353] | No resolved gain; interval includes 1 |

Allocation is the mean of `gc.alloc.rate.norm` across the three forks, rounded to the nearest byte:

| Operation | Baseline (B/op) | Optimized (B/op) | Reduction |
| --- | ---: | ---: | ---: |
| `sqrtOrSqrtZ` | 16,196 | 13,115 | 19.02% |
| `hashToCurve` | 770,332 | 763,921 | 0.83% |
| Sign, reused key | 2,538,073 | 2,531,621 | 0.25% |
| Sign, fresh key object | 2,538,158 | 2,531,738 | 0.25% |
| Verify, reused key | 9,168,247 | 9,160,727 | 0.08% |
| Verify, fresh key object | 9,453,580 | 9,446,792 | 0.07% |

The measurements support the helper, hash-to-curve, and signing improvements in this workload. They do not establish an end-to-end verification speedup. The three-pair protocol was kept fixed; no additional forks were collected to turn the verification result into a positive claim.
