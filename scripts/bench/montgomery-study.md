# Bouncy Castle delayed Montgomery reductions

Both ML-KEM and ML-DSA use a delayed Montgomery reduction in the lightweight implementation on branch `codex/montgomery-dot-products`. The engine interfaces and encoded formats are unchanged. This study supports fewer reductions and lower kernel timings in the tested environment. End-to-end latency depends on operation, parameter set, JVM and load.

## Local development records and changed files

The following commit IDs identify the local development records used for validation. The published branches preserve the source trees and have their own commit IDs.

- d55ba9434f66f8691be089a9638b724bf86ffe94 Accumulate ML-KEM base products before Montgomery reduction
  - `ant/bc+-build.xml`
  - `core/src/main/java/org/bouncycastle/crypto/kems/mlkem/Ntt.java`
  - `core/src/main/java/org/bouncycastle/crypto/kems/mlkem/Poly.java`
  - `core/src/main/java/org/bouncycastle/crypto/kems/mlkem/PolyVec.java`
  - `core/src/test/java/org/bouncycastle/crypto/kems/mlkem/AllTests.java`
  - `core/src/test/java/org/bouncycastle/crypto/kems/mlkem/PointwiseProductTest.java`
- 9818663b7b1e514b775586497cfe9c813fed8266 Verify that ML-KEM keeps its dot-product operands intact
  - `core/src/test/java/org/bouncycastle/crypto/kems/mlkem/PointwiseProductTest.java`
- 6e9feffcefbc456eb66bee25f02b52ddca62a59a Reduce each ML-DSA matrix row product once per coefficient
  - `ant/bc+-build.xml`
  - `core/src/main/java/org/bouncycastle/crypto/signers/mldsa/Poly.java`
  - `core/src/test/java/org/bouncycastle/crypto/signers/mldsa/AllTests.java`
- 96d678b8488a2ba689d7a600eec5edbebb7c5094 Add reproducible Montgomery dot-product measurements
  - `scripts/bench/MontgomeryDsaKernel.java`
  - `scripts/bench/MontgomeryKemKernel.java`
  - `scripts/bench/MontgomeryOperations.java`

For ML-KEM, use branch `codex/fork-mlkem-montgomery` in `carstenartur/bc-java`. For ML-DSA, use `codex/fork-mldsa-montgomery` in the same fork. The combined study branch `codex/montgomery-dot-products` contains both implementations and the three standalone measurement programs. The Ant file keeps the two package-private test classes out of legacy artifact staging. The legacy signed Ant distributions were not executed.

## Verification

* Pinned upstream source bb81bfa75c9fa81c7fde467a6314374d22715472. Pinned vector source bcgit/bc-test-data ac45cc057be4e72a87e9cdded470b2e36e5cde50. The full test-data tree was fetched and checked out. No standalone stub/research-vector run is included in the reported test counts.
* Before production edits, the two new deterministic differential tests passed the upstream package-private production classes. They compare the old per-product expression independently at each coefficient, check normalized results after inverse NTT, and exercise every public dimension. ML-KEM tests all 16 mixed endpoint choices for each of the 128 two-lane blocks in every size, plus seeded random cases. ML-DSA covers ±34,162,429 and matrix q−1, plus seeded random cases. Distinct and aliased output cases compare all unaliased input arrays coefficient-for-coefficient. The extra malformed-key regression digests were generated from the unmodified upstream production classes and replayed against both old and new implementations.
* Selected mathematical kernels on JDKs 17.0.21.1, 21.0.13 and 25.0.5 each passed **47/47** tests in the complete upstream MLDSATest, MLDSAWycheproofTest, MLKEMTest, the ML-DSA internal tests and the ML-KEM dot tests. The suites cover all ML-KEM/ML-DSA parameter sets, ACVP keygen/encap/decap and keygen/sign/verify vectors, exact outputs, malformed keys and signatures, mutated inputs, prehash and round trips. The three Wycheproof verification files assert **631 vectors** (180, 210, 241 including 404 invalid). The ML-KEM internal tests also exercise the decode path for noncanonical 12-bit coefficients and the ML-DSA internal tests exercise malformed eta codings under key derivation. The four-reduction laboratory schedule also passed its package differential and **all 17 upstream MLKEMTest methods**.
* All 49 upstream Java core suite entry points were exercised in a direct JDK 21 JUnit preflight with the first bounded ML-DSA schedule and the selected ML-KEM. **1,068/1,068** methods passed after two unaffiliated memory-intensive suites (Argon2 and TupleHash) were rerun at 4 GiB instead of 768 MiB. The later two malformed-key methods and revised operand-preservation assertions were tested separately and in the final run. Gradle 9.1.0/JDK 25 also compiled the core and its tests with Error Prone and passed **:core:checkstyleMain**. The initial Gradle distribution download required using the environment proxy; concurrent Gradle daemons contended on the caches, and the final core task was rerun on its own. The default Gradle core verification on the final implementation completed successfully, including :core:test and its JaCoCo report. Across 178 JUnit XML result files it recorded **1070 tests, 0 failures, 0 errors, 0 skipped**. Those files include the new ML-DSA/ML-KEM internal tests and the upstream MLDSAWycheproofTest. This is the regular core suite with its default sampling settings.

### Independent validation on the carstenartur/bc-java fork

| Fork main | Published branch | Local validation commit IDs | Exact-branch validation |
|---|---|---|---|
| ab16374d37c7e18c4090eb8838ebbd72a92593f2 | codex/fork-mlkem-montgomery | 32394be followed by 6b1431136102954a227f5095cfacde18e8a54c0c | Full native MLKEMTest plus package AllTests, **17/17** on JDK 21 |
| same | codex/fork-mldsa-montgomery | 95e2b2b9d78453c85000ffd03b428cf8c0d04ca4 | Full native MLDSATest plus package AllTests, **15/15** on JDK 21 |

Each fork worktree compiled **all its own core production sources** with JDK 25 javac --release 8 and its own test sources. The tests in the fork and the same pinned external vectors drove the focused runs. The two arithmetic patches are independent and each branch has a clean working tree. The fork patches preserve its main history.

The relevant ML-KEM Poly, PolyVec, Ntt and Reduce blobs match the upstream baseline exactly. ML-DSA Poly differs only in the SHAKE purpose in challenge, outside this method, and its source patch cherry-picked cleanly. At both baselines there are the same four call sites per algorithm with the same alias arrangements, q, coefficient ranges and normalization points. On fork main the older ML-KEM matrix sampler differs on the rare stream-refill path, but rejection still enforces coefficient <q on every path. It is preserved as-is. Standalone public-key length/modulus checks and expanded-private-key hash checks do not replace the 12-bit decode bound. ML-DSA’s newer expanded-key tr consistency check is absent on fork main; malformed s1/s2 still obey the full eta decoding bounds above. The new package tests include the corresponding malformed representations. Fork main lacks the newer ML-KEM internal AllTests/SampleNttTest and MLDSAWycheproofTest. A small KEM test-suite registration plus its legacy Ant staging exclusion were adapted to this base. No unrelated tests, digest-purpose changes, sampler corrections or validation changes were imported from upstream.


## Equality and effect contract

In both reducers let R be the power-of-two radix, q the odd modulus and t the signed low word of a·q⁻¹. Then M(a) = (a − t·q)/R is integral and is congruent to a/R modulo q. For every valid signed low word, |M(a)| ≤ |a|/R + q/2. The low-word multiplication is intentionally modular. All newly formed accumulator sums, products used in Montgomery numerators, signed subtractions, narrowed outputs and butterfly sums below fit their destination widths. The existing Barrett routine retains its short casts; its full-domain image below includes their Java semantics. The ML-DSA unsigned long shift followed by the int cast selects exactly the signed quotient bits.

The former kernels add representatives reduced separately. The replacement returns a congruent representative that can differ by a multiple of q. Raw intermediate arrays and their contents during writes are outside the protocol contract. The proof covers the four callers in each pinned engine, using their actual dimensions, operand ranges and independently owned outputs. Neither package-private Poly type is externally constructible via the API. Public engine methods accept encodings, seeds and digests, never these output buffers. The argument does not assert equivalence for arbitrary arrays, reflection, data races, or new caller arrangements.

Both dot loops allocate no objects. Their loop counts, subscripts and conditional dispatch depend only on the public parameter set and coefficient index. No secret-dependent branch, input-indexed lookup, division or early exit was added. This is a Java-source control-flow and address argument. No native timing/side-channel certification is claimed.

### ML-DSA

| Engine call | Matrix and vector input | Output and first consumers |
|---|---|---|
| generateKeyPairInternal | Independent expanded A, copied s1hat, NTT of eta-sampled s1 with absolute value ≤4 | New t1, reduce32, inverse NTT, add s2, conditionalAddQ and power2Round |
| deriveT1 | Expanded A, independent s1hat copied after unpacking encoded secret. Even malformed bytes decode to 2 − [0,7] or 4 − [0,15], giving absolute value ≤11 | New t1, same reduction and rounding path. Expanded-key consistency checks follow. |
| generateSignature | Expanded A, z copied from independent y and transformed. Gamma1 is 2¹⁷ or 2¹⁹, with y from fixed-width decoding in [1−gamma1,gamma1]. Secret s1 and s2 are separate operands in later operations. | Separate w1, reduce32, inverse NTT, conditionalAddQ, decompose and packW1; identical challenge input. |
| doVerifyInternal | Expanded A, decoded signature z in [1−gamma1,gamma1]. Length, encoding and norm checks precede NTT. | Independent w1 minus independently computed c·2ᴰt1, then reduce32, inverse NTT, conditionalAddQ, useHint and packW1 |

PolyVecMatrix.expandMatrix fills K freshly allocated vectors of L freshly allocated polynomials. rejectUniform accepts only 23-bit nonnegative values below q. PolyVec/Poly constructors allocate distinct coefficient arrays. The engine allocates all output vectors separately. copyTo uses System.arraycopy; it does not share arrays. The package-only setCoeffs is unused in these call paths. Other operations deliberately permitting in-place multiplication, such as t1.pointwisePolyMontgomery(cp,t1), still call the separate per-product method.

For q = 8,380,417, R = 2³², q⁻¹ = 58,728,449 and max absolute zeta 4,108,315, start B₀ = 524,288. Each forward stage obeys Bnext = B + ceil(4,108,315·B/R + q/2). Eight upper bounds are 4,714,999; 8,909,718; 13,108,450; 17,311,198; 21,517,966; 25,728,758; 29,943,578; 34,162,429. Thus

    |dot| ≤ 7·(q−1)·34,162,429 = 2,004,067,566,133,248
          < q·2³¹ = 17,996,808,470,921,216.

The long accumulator and the subtraction by t·q fit long, and the new output has absolute value ≤4,656,817. Only the low 32 bits of a·q⁻¹ are used, even when that long product wraps. The old per-term bound is 4,256,867 and its seven-term sum fits int.

For verification, the sparse challenge starts with |c|≤1, and decoded ten-bit t1 shifted left by 13 starts at ≤8,380,416. The same recurrence gives final bounds 33,634,114 and 42,078,875. Their Montgomery product is ≤4,519,731 in absolute value. After subtraction the old bound is 34,317,800 and the new bound is 9,176,548. Both allow the addition inside reduce32 without overflow. Throughout these paths |(a+2²²)>>23|≤5. Because q=2²³−8191, the reduced absolute value is at most 2²² + 5·8191 < 4,300,000. The inverse butterflies grow by at most a factor 2 per stage from that conservative bound (the zeta multiplication is bounded by 2·B·4,108,315/R + q/2). All int stages, including the last, stay below 256·4,300,000. The final factor 41978 gives absolute output ≤4,200,968. Adding at most 11 in the key path keeps the value strictly between −q and q. ConditionalAddQ therefore gives the exact canonical integer, also in signing and verification. Equal canonical values imply equal packed keys, challenges, signatures and verification decisions, including the deterministic retry decisions for identical coins.

### ML-KEM

| MLKEMIndCpa call | First operand | Second operand and output |
|---|---|---|
| generateKeyPair | New matrixA row, sampled below q | NTT/Barrett of secretKey; separate publicKey[i], convertToMont, add reduced e, reduce and toBytes |
| encrypt, bp row | New transposed matrix row, sampled below q | NTT/Barrett of sampled sp; separate bp[i], inverse NTT, add error, reduce and compress |
| encrypt, v | Public-key vector decoded with & 0xFFF | Same separately owned sp; separate v, inverse NTT, add error and message, reduce and compress |
| decrypt | Secret polynomial vector decoded with & 0xFFF | NTT/Barrett of decompressed ciphertext vector bp; separate mp, inverse NTT, subtract from decoded v, reduce and toMsg |

All four allocate independent Poly or PolyVec outputs. Each Poly owns a final short[256] and each vector owns its polynomials. getCoeffs exposes an internal array to package code. Public ciphertexts/keys enter as bytes and do not alias these arrays. An expanded private key checks length and its embedded public-key hash, which does not imply modulus validity. Decryption and re-encryption therefore still need the full 12-bit bound for a. Both standalone public-key constructors perform the stricter modulus check. The second operand passes through Poly.polyNtt, whose final Barrett reduction returns integers in [0,3329], including 3329. This bound follows for every signed short: with v=20159, vq=2²⁶+447, the Barrett quotient differs from floor(a/q) by at most one, only at multiples within the supported range; exhaustive verification over all 65,536 shorts gives the same [0,q] image. Thus malformed ciphertexts preserve the bound as well.

With q=3329, R=65536, q⁻¹=62209 (signed low 16 = −3327), k≤4, 0≤a≤4095 and 0≤b≤3329, A00,A11≤54,529,020, Across≤109,058,040, Aplus≤218,116,080. For the selected three-reduction formula v=M(A11), even=M(A00+zeta·v), odd=M(Across). Since zeta is a Montgomery-scaled root, the terms match the upstream base product at precisely the same scale: zeta·A11/R² + A00/R and Across/R. Reversing the sign on the second pair of every four coefficients preserves the original NTT order. |v|≤2,497, |even|≤2,624 and |odd|≤3,329. The alternative Karatsuba schedule uses u=M(A00), v=M(A11), even=u+M(zeta·v), odd=M(Aplus)−u−v. Its odd interval is contained in [−6,656,8,320]. For either variant the largest conservative reduction numerator is at most 218,116,080 + 32,768·3,329 = 327,200,752, safely inside int. The multiplication a·Qinv is intentionally truncated to 16 bits. Both variants retain Barrett on each lane before returning.

Raw Barrett outputs in [0,q] can differ only in representing zero as 0 or q. In convertToMont the factor is R² mod q <q. Keygen adds a reduced e and invokes Barrett then condSubQ in serialization. For inverse NTT, an invariant is |coefficient|≤3329; the sums/differences fit a signed short, Barrett sums remain in [0,q], and |M(zeta·difference)|≤2,004 with |zeta|≤3328. The final inverse scale preserves |coefficient|≤3329. Adding at most 3 of noise and 1665 of message, or subtracting from a decompressed value ≤3329, fits short. Final Barrett plus condSubQ before encoding, compression or message extraction yields the exact canonical integer. This preserves ciphertext comparisons, implicit rejection selection and the returned shared secret.

Aliasing the first row of the left vector as destination works for the old and new low-level methods and is regression-tested. Neither previous kernel promised the correct dot when the destination aliases a *later* vector entry: the old loop could overwrite an operand before reading it. The engine never requests that arrangement. A malformed short buffer or null key that fails before the dot still fails at the original public decode/length/hash sites. No claim covers invalid synthetic PolyVec object graphs.

## Measurements

The selected ML-KEM uses 384 Montgomery reductions per polynomial dot instead of 1,280, 1,920 or 2,560; individual two-lane blocks use three instead of 5K. It performs 4K+1 ordinary products per block. The Karatsuba candidate needs 512 reductions per polynomial and 3K+1 ordinary products per block. Both remove the temporary Poly and its short[256]. The chosen ML-DSA loop uses 256 reductions per row instead of 1,024, 1,280 or 1,792, with the same L products per coefficient and no new allocations. Only public L/K or array indices select the optional rows.

Host: Linux x86_64, Intel Xeon Platinum 8573C, OpenJDK 21.0.13+9 Debian HotSpot. These are package-level lightweight **engine operations**, including the full lattice work, using the fixed key/coins/message inputs of the program. Signing/verifying contexts are prepared before measurement. The results do not measure provider key-object creation, ASN.1, RNG latency, a fresh key for each signature or an entire application.

Independent short pilot JVMs showed high load/JIT variation. The decision runs use three fresh forked JVMs with separately loaded baseline and candidate core classes in each VM. Flags: `-Xms384m -Xmx384m -Xbatch -XX:-TieredCompilation -XX:CompileThreshold=100 -XX:+UseSerialGC -XX:ActiveProcessorCount=1`. Affinity was CPU 4 for the selected ML-DSA, CPU 6 for ML-KEM. Each operation warms both implementations on 512 complete invocations, then uses eight adjacent baseline/candidate pairs of 128 invocations cycling over 16 seeded inputs. Sample order alternates and the second fork reverses it. During warmup the harness compares one output byte per invocation. The timed signing loop consumes a byte from each generated signature. The separate verification loop repeatedly verifies 16 precomputed signatures. KEM setup checks all 16 shared-secret round trips. Each measured batch prints its accumulated byte checksum. Full output comparisons come from the KAT and differential tests. Neither the stored key nor message setup is timed. Bytes/op uses the HotSpot per-thread allocation counter.

The table gives median absolute CPU time per variant, the median within-pair candidate/base time change for CPU and elapsed time, and the median candidate-minus-baseline allocation. These are distinct statistics, so a ratio of the two absolute medians can differ from the paired result. Negative changes favor the candidate. Each regular row has 24 pairs. The similarly structured A/A control loaded the baseline twice. Its entire 24-pair rows ranged from −2.7% to +2.3% CPU and −2.6% to +4.1% wall; individual batches had substantially larger spreads. No statistical or environment-independent speed guarantee follows.

| Schedule | Set | Operation | Base CPU μs | Candidate CPU μs | Paired CPU | Paired wall | Δ B/op |
|---|---|---|---:|---:|---:|---:|---:|
| selected | ml-dsa-44 | keygen | 180.2 | 194.4 | +6.5% | +6.4% | +0 |
| selected | ml-dsa-44 | sign | 594.7 | 572.5 | -2.9% | -1.4% | +0 |
| selected | ml-dsa-44 | verify | 173.2 | 173.8 | -2.8% | -6.0% | +0 |
| selected | ml-dsa-65 | keygen | 309.2 | 303.0 | -4.6% | -6.9% | +0 |
| selected | ml-dsa-65 | sign | 1432.5 | 1434.2 | -1.6% | -1.7% | +0 |
| selected | ml-dsa-65 | verify | 318.6 | 298.8 | -0.8% | +2.4% | +0 |
| selected | ml-dsa-87 | keygen | 490.1 | 464.5 | -3.6% | -3.7% | +0 |
| selected | ml-dsa-87 | sign | 1189.5 | 1163.1 | -2.1% | -7.7% | +0 |
| selected | ml-dsa-87 | verify | 469.3 | 439.6 | -6.0% | -7.4% | +0 |
| longer follow-up | ml-dsa-44 | keygen | 175.5 | 171.7 | +1.5% | +0.8% | +0 |
| selected | ML-KEM-512 | keygen | 102.1 | 117.5 | -1.3% | -7.0% | -1056 |
| selected | ML-KEM-512 | encap | 137.6 | 127.1 | -6.6% | -9.4% | -1584 |
| selected | ML-KEM-512 | decap | 80.9 | 77.8 | -3.2% | -3.0% | -2112 |
| selected | ML-KEM-768 | keygen | 82.4 | 82.5 | -3.4% | +0.5% | -1584 |
| selected | ML-KEM-768 | encap | 90.7 | 90.1 | -4.0% | -4.4% | -2112 |
| selected | ML-KEM-768 | decap | 119.2 | 114.8 | -4.1% | -5.3% | -2640 |
| selected | ML-KEM-1024 | keygen | 126.0 | 126.8 | -4.7% | -10.5% | -2112 |
| selected | ML-KEM-1024 | encap | 149.0 | 140.7 | -7.4% | -2.7% | -2640 |
| selected | ML-KEM-1024 | decap | 187.5 | 180.1 | -3.4% | -7.8% | -3168 |
| Karatsuba | ML-KEM-512 | keygen | 61.5 | 60.7 | +0.5% | +0.5% | -1056 |
| Karatsuba | ML-KEM-512 | encap | 77.4 | 70.7 | -2.6% | -6.5% | -1584 |
| Karatsuba | ML-KEM-512 | decap | 76.9 | 71.5 | -4.9% | -5.5% | -2112 |
| Karatsuba | ML-KEM-768 | keygen | 87.4 | 83.5 | -5.1% | -4.4% | -1584 |
| Karatsuba | ML-KEM-768 | encap | 96.1 | 88.7 | -6.0% | -5.3% | -2112 |
| Karatsuba | ML-KEM-768 | decap | 117.2 | 113.3 | -4.6% | -0.8% | -2640 |
| Karatsuba | ML-KEM-1024 | keygen | 138.1 | 134.2 | -2.5% | -1.3% | -2112 |
| Karatsuba | ML-KEM-1024 | encap | 145.2 | 141.5 | -2.7% | -2.3% | -2640 |
| Karatsuba | ML-KEM-1024 | decap | 186.1 | 176.4 | -3.1% | -2.0% | -3168 |

The direct ML-KEM formula with row arrays captured before the coefficient loop was selected. Across K=2,3,4 it consistently reduces allocation. In the first kernel sweep the alternative Karatsuba schedule was faster at K=3, and the direct formula at K=2,4. In the same-CPU repeat below, the direct formula was faster at all three sizes. Complete operations and CPU/elapsed results were mixed within this comparison. One public-size-independent formula avoids tuning dispatch to this host. The +0.5% elapsed-time result for ML-KEM-768 keygen is recorded above.

ML-DSA uses a single coefficient loop and tests only its public supported sizes. This layout gives clear kernel reductions at all three lengths. In the initial full-operation measurement ML-DSA-44 keygen was 6.5% slower by CPU/6.4% by wall time. A fresh targeted experiment using 4,096 warmup invocations per engine and batches of 1,024 on that operation gave +1.5% CPU/+0.8% elapsed; these are within the variation seen in the A/A control. ML-DSA-65 verification elapsed time rose 2.4% in the primary run. We have no established material full-operation regression or uniform full-operation acceleration. Other measured schedules (three separately unrolled loops, grouped four-coefficient sums, a shared tail and a baseline path for L=5) did not justify extra parameter-specific dispatch. The cumulative row allocations for both ML-DSA schedules were the same to counter precision.

Kernel CPU times are median ns for one full 256-coefficient result. Each fork runs one untimed-for-summary warmup batch and three measured batches, each of 100,000 invocations. Each call changes one coefficient and consumes a different output lane. Three forks give nine steady-state samples per cell. The selected ML-DSA baseline and selected layouts were pinned to CPU 2; the initial three-loop experiment also ran on CPU 2. ML-KEM generic variants and baseline used CPU 3; the hoisted variants used CPU 7. Absolute timings can reflect host-core differences.

| Set | Baseline | Direct, inner row loop | Karatsuba, inner row loop | Direct, arrays hoisted | Karatsuba, arrays hoisted |
|---|---:|---:|---:|---:|---:|
| ML-KEM-1024 | 5203.8 | 3906.6 | 3884.4 | 2786.3 | 3547.2 |
| ML-KEM-512 | 2444.2 | 2511.0 | 2587.2 | 1427.2 | 1715.1 |
| ML-KEM-768 | 3827.5 | 3172.2 | 3403.4 | 2206.0 | 2115.8 |

| Set | Baseline | Fixed L-specific loops | Four coefficient accumulators | Selected common loop |
|---|---:|---:|---:|---:|
| ml-dsa-44 | 2359.7 | 1710.5 | 2266.6 | 1826.4 |
| ml-dsa-65 | 2756.6 | 2462.2 | 2634.3 | 1656.6 |
| ml-dsa-87 | 4514.2 | 3186.6 | 3487.4 | 2266.6 |

### Independent fork-baseline measurements

Each fork PR is based directly on carstenartur/bc-java main at ab16374d37c7e18c4090eb8838ebbd72a92593f2. Same pinned CPU 4 and benchmark protocol; both baseline and candidate were compiled from those exact trees, and the benchmark ran three fresh JVMs per algorithm. This is a second environment/load sample; the fork also predates upstream SHAKE/policy and sampler changes. Independent full-operation timings must be interpreted in that context.

| Set | Operation | Base CPU μs | Candidate CPU μs | Paired CPU | Paired wall | Δ B/op |
|---|---|---:|---:|---:|---:|---:|
| ml-dsa-44 | keygen | 182.8 | 195.1 | +2.8% | +1.6% | +0 |
| ml-dsa-44 | sign | 610.6 | 575.4 | -5.9% | -7.3% | +0 |
| ml-dsa-44 | verify | 188.5 | 173.3 | -3.5% | -5.6% | +0 |
| ml-dsa-65 | keygen | 299.1 | 307.5 | +0.3% | +2.2% | +0 |
| ml-dsa-65 | sign | 1308.2 | 1254.8 | -2.8% | -2.7% | +0 |
| ml-dsa-65 | verify | 284.9 | 283.2 | -3.0% | -3.1% | +0 |
| ml-dsa-87 | keygen | 455.2 | 461.3 | +1.8% | +4.3% | +0 |
| ml-dsa-87 | sign | 1284.3 | 1201.6 | -1.2% | -1.3% | +0 |
| ml-dsa-87 | verify | 486.1 | 454.1 | -1.8% | -1.0% | +0 |
| ML-KEM-512 | keygen | 85.8 | 88.9 | +0.7% | -0.3% | -1056 |
| ML-KEM-512 | encap | 97.9 | 87.7 | -7.9% | -9.8% | -1584 |
| ML-KEM-512 | decap | 78.6 | 77.1 | -7.6% | -7.2% | -2112 |
| ML-KEM-768 | keygen | 98.1 | 93.2 | -2.6% | +1.2% | -1584 |
| ML-KEM-768 | encap | 103.2 | 93.9 | -8.3% | -8.4% | -2112 |
| ML-KEM-768 | decap | 128.4 | 118.3 | -6.6% | -6.7% | -2640 |
| ML-KEM-1024 | keygen | 139.6 | 131.6 | -4.6% | -4.6% | -2112 |
| ML-KEM-1024 | encap | 156.0 | 153.5 | -1.5% | -4.4% | -2640 |
| ML-KEM-1024 | decap | 199.1 | 184.9 | -8.9% | -10.2% | -3168 |

### ML-KEM kernel repeat on a common logical CPU

This repeat pins all three variants to CPU 7, with three forks per variant and the same warmup, batch size, median and checksums. Fork order was baseline/direct/Karatsuba, Karatsuba/baseline/direct, direct/Karatsuba/baseline.

| Set | Baseline ns | Direct ns | Karatsuba ns |
|---|---:|---:|---:|
| ML-KEM-1024 | 4288.7 | 2294.4 | 3326.6 |
| ML-KEM-512 | 2092.7 | 1467.3 | 1667.0 |
| ML-KEM-768 | 3203.6 | 1866.6 | 2006.5 |

## Reproduction

Start in a fresh directory with JDK 25 for javac/Gradle and JDK 21 for the measurement JVM. The commands clone the published `codex/montgomery-dot-products` study branch as the complete candidate, fetch the pinned baseline directly from `bcgit/bc-java`, and compile the two source trees separately. The two java DSA and KEM kernel harnesses run separately on each class tree. The candidate comparison harness uses the isolated loaders described above. Leave both loaders on the baseline for A/A.

```bash
set -eu
git clone --single-branch --branch codex/montgomery-dot-products https://github.com/carstenartur/bc-java.git montgomery-study
cd montgomery-study
revision=bb81bfa75c9fa81c7fde467a6314374d22715472
git fetch --no-tags --depth=1 https://github.com/bcgit/bc-java.git "$revision"
benchdir="$PWD/build/reproduce-dot"
mkdir -p "$benchdir"/{oldsrc,base,candidate,harness}
git archive "$revision" core/src/main/java | tar -x -C "$benchdir/oldsrc"
find "$benchdir/oldsrc/core/src/main/java" -name '*.java' > "$benchdir/old.java-list"
find core/src/main/java -name '*.java' > "$benchdir/new.java-list"
javac --release 8 -d "$benchdir/base" @"$benchdir/old.java-list"
javac --release 8 -d "$benchdir/candidate" @"$benchdir/new.java-list"
javac --release 17 -cp "$benchdir/base" -d "$benchdir/harness" scripts/bench/*.java
git clone https://github.com/bcgit/bc-test-data.git "$benchdir/bc-test-data"
git -C "$benchdir/bc-test-data" checkout --detach ac45cc057be4e72a87e9cdded470b2e36e5cde50
export BC_TEST_DATA_HOME="$benchdir/bc-test-data"
export BC_JDK25="$JAVA_HOME"
./gradlew --console=plain :core:test :core:checkstyleMain
opts=(-Xms384m -Xmx384m -Xbatch -XX:-TieredCompilation -XX:CompileThreshold=100 -XX:+UseSerialGC -XX:ActiveProcessorCount=1)
for family in dsa kem; do
  for fork in 1 2 3; do
    rev=false
    if [ "$fork" = 2 ]; then rev=true; fi
    java "${opts[@]}" -Dreverse="$rev" -cp "$benchdir/harness:$benchdir/base" MontgomeryOperations "$family" \
      "$benchdir/harness:$benchdir/base" "$benchdir/harness:$benchdir/candidate" > "$benchdir/$family-$fork.csv"
  done
done
# For the longer 44/keygen follow-up, add these JVM properties to the dsa command:
# -Donly=ml-dsa-44,keygen -Dwarmup=4096 -Dcount=1024
for impl in base candidate; do
  for fork in 1 2 3; do
    java "${opts[@]}" -cp "$benchdir/harness:$benchdir/$impl" org.bouncycastle.crypto.signers.mldsa.MontgomeryDsaKernel
    java "${opts[@]}" -cp "$benchdir/harness:$benchdir/$impl" org.bouncycastle.crypto.kems.mlkem.MontgomeryKemKernel
  done
done
```
For the hoisted Karatsuba comparison, keep the same array binds, loops, zeta sign, final casts and Barrett. Replace each cross-row summand `a[j]*b[next]+a[next]*b[j]` by `(a[j]+a[next])*(b[j]+b[next])`; compute u=M(a00), v=M(a11), even=u+M(zeta*v), odd=M(cross)−u−v. The tables also show the exploratory schedules. The committed Java harnesses run against separately compiled baseline and candidate classes.

## Measurement data

The operation samples include the primary decisions, both ML-KEM schedules, the longer ML-DSA-44 keygen follow-up, the A/A control and the independent fork runs. The kernel file includes the warmup batches, numbered zero. The summaries exclude batch zero. Within an implementation and a K/L, each kernel batch emits the same checksum.

[Full-operation samples](montgomery-data/operation-samples.csv) · [Kernel samples](montgomery-data/kernel-samples.csv)
