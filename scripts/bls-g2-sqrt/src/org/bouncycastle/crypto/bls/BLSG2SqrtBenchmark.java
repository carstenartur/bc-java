package org.bouncycastle.crypto.bls;

import java.math.BigInteger;
import java.util.Random;
import java.util.concurrent.TimeUnit;

import org.bouncycastle.crypto.CryptoException;
import org.bouncycastle.crypto.digests.SHA256Digest;
import org.bouncycastle.crypto.params.BLSParameters;
import org.bouncycastle.crypto.params.BLSPrivateKeyParameters;
import org.bouncycastle.crypto.params.BLSPublicKeyParameters;
import org.bouncycastle.crypto.signers.BLSSigner;
import org.bouncycastle.util.encoders.Hex;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Threads;
import org.openjdk.jmh.annotations.Warmup;

/** The same public input corpus and encoded key material are used in every fork. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 8, time = 1)
@Fork(value = 3, jvmArgsAppend = {"-Xms512m", "-Xmx512m"})
@Threads(1)
public class BLSG2SqrtBenchmark
{
    private final Fp2Element[] fieldInputs = new Fp2Element[256];
    private final Fp2Element[] root = new Fp2Element[1];
    private final byte[][] messages = new byte[16][32];
    private final byte[][] signatures = new byte[16][];

    private BLS12_381G2HashToCurve hasher;
    private BLSPrivateKeyParameters privateKey;
    private BLSPublicKeyParameters publicKey;
    private byte[] secretEncoding;
    private byte[] publicEncoding;
    private int fieldIndex;
    private int messageIndex;

    @Setup
    public void setup()
        throws CryptoException
    {
        // Reproducible benchmark fixtures; this is not production key generation.
        Random random = new Random(0x3819380L);
        for (int i = 0; i < fieldInputs.length; ++i)
        {
            BigInteger a = new BigInteger(Fp2Element.P.bitLength(), random).mod(Fp2Element.P);
            BigInteger b = new BigInteger(Fp2Element.P.bitLength(), random).mod(Fp2Element.P);
            fieldInputs[i] = Fp2Element.of(a, b);
        }
        byte[] ikm = new byte[32];
        random.nextBytes(ikm);
        secretEncoding = BLS12_381BasicScheme.keyGenEncoded(ikm, new byte[0]);
        privateKey = new BLSPrivateKeyParameters(BLSParameters.bls12_381, secretEncoding);
        publicKey = new BLSPublicKeyParameters(BLSParameters.bls12_381,
            BLS12_381BasicScheme.skToPk(secretEncoding));
        publicEncoding = publicKey.getEncoded();
        hasher = new BLS12_381G2HashToCurve(BLS12_381BasicScheme.DST);
        for (int i = 0; i < messages.length; ++i)
        {
            random.nextBytes(messages[i]);
            signatures[i] = sign(privateKey, messages[i]);
        }
        if (!verify(publicKey, messages[0], signatures[0]))
        {
            throw new IllegalStateException("benchmark signature must verify");
        }
    }

    @Benchmark
    public Fp2Element sqrtOrSqrtZ()
    {
        BLS12_381G2HashToCurve.sqrtOrSqrtZ(fieldInputs[fieldIndex++ & 255], root);
        return root[0];
    }

    @Benchmark
    public BLS12_381G2Point hashToCurve()
    {
        return hasher.hashToCurve(messages[messageIndex++ & 15]);
    }

    @Benchmark
    public byte[] signReusedKey()
        throws CryptoException
    {
        return sign(privateKey, messages[messageIndex++ & 15]);
    }

    @Benchmark
    public byte[] signFreshKey()
        throws CryptoException
    {
        BLSPrivateKeyParameters fresh = new BLSPrivateKeyParameters(BLSParameters.bls12_381, secretEncoding);
        return sign(fresh, messages[messageIndex++ & 15]);
    }

    @Benchmark
    public boolean verifyReusedKey()
    {
        int i = messageIndex++ & 15;
        return verify(publicKey, messages[i], signatures[i]);
    }

    @Benchmark
    public boolean verifyFreshKey()
    {
        int i = messageIndex++ & 15;
        BLSPublicKeyParameters fresh = new BLSPublicKeyParameters(BLSParameters.bls12_381,
            BLS12_381Serialization.decompressG1(publicEncoding, BLS12_381G1.createCurve()));
        return verify(fresh, messages[i], signatures[i]);
    }

    /** Compare canonical public outputs before timing either implementation. */
    public static void main(String[] args)
        throws CryptoException
    {
        BLSG2SqrtBenchmark data = new BLSG2SqrtBenchmark();
        data.setup();
        SHA256Digest digest = new SHA256Digest();
        digest.update(data.publicEncoding, 0, data.publicEncoding.length);
        for (int i = 0; i < data.messages.length; ++i)
        {
            byte[] point = BLS12_381Serialization.compressG2(data.hasher.hashToCurve(data.messages[i]));
            digest.update(point, 0, point.length);
            digest.update(data.signatures[i], 0, data.signatures[i].length);
            if (!verify(data.publicKey, data.messages[i], data.signatures[i]))
            {
                throw new IllegalStateException("benchmark signature must verify");
            }
        }
        byte[] result = new byte[digest.getDigestSize()];
        digest.doFinal(result, 0);
        System.out.println(Hex.toHexString(result));
    }

    private static byte[] sign(BLSPrivateKeyParameters key, byte[] message)
        throws CryptoException
    {
        BLSSigner signer = new BLSSigner();
        signer.init(true, key);
        signer.update(message, 0, message.length);
        return signer.generateSignature();
    }

    private static boolean verify(BLSPublicKeyParameters key, byte[] message, byte[] signature)
    {
        BLSSigner verifier = new BLSSigner();
        verifier.init(false, key);
        verifier.update(message, 0, message.length);
        return verifier.verifySignature(signature);
    }
}
