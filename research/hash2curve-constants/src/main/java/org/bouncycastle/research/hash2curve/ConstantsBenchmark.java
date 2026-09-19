package org.bouncycastle.research.hash2curve;

import java.math.BigInteger;
import java.util.Random;
import java.util.concurrent.TimeUnit;

import org.bouncycastle.crypto.hash2curve.impl.GenericSqrtRatioCalculator;
import org.bouncycastle.crypto.hash2curve.impl.LegacyGenericSqrtRatioCalculator;
import org.bouncycastle.crypto.hash2curve.impl.SqrtRatio;
import org.bouncycastle.math.ec.ECCurve;
import org.bouncycastle.math.ec.custom.sec.SecP256R1Curve;
import org.bouncycastle.math.ec.custom.sec.SecP384R1Curve;
import org.bouncycastle.math.ec.custom.sec.SecP521R1Curve;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Level;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Param;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;

@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
public class ConstantsBenchmark
{
    @Param({ "P256", "P384", "P521", "CURVE25519" })
    public String field;

    private ECCurve curve;
    private BigInteger z;
    private final BigInteger[] numerators = new BigInteger[64];
    private final BigInteger[] denominators = new BigInteger[64];
    private int index;
    private GenericSqrtRatioCalculator optimized;
    private LegacyGenericSqrtRatioCalculator baseline;

    @Setup(Level.Trial)
    public void setup()
    {
        if ("P256".equals(field))
        {
            curve = new SecP256R1Curve();
            z = BigInteger.valueOf(-10);
        }
        else if ("P384".equals(field))
        {
            curve = new SecP384R1Curve();
            z = BigInteger.valueOf(-12);
        }
        else if ("P521".equals(field))
        {
            curve = new SecP521R1Curve();
            z = BigInteger.valueOf(-4);
        }
        else if ("CURVE25519".equals(field))
        {
            BigInteger q = BigInteger.ONE.shiftLeft(255).subtract(BigInteger.valueOf(19));
            curve = new ECCurve.Fp(q, BigInteger.ONE, BigInteger.ONE, null, null, true);
            z = BigInteger.valueOf(2);
        }
        else
        {
            throw new IllegalArgumentException(field);
        }
        optimized = new GenericSqrtRatioCalculator(curve, z);
        baseline = new LegacyGenericSqrtRatioCalculator(curve, z);
        BigInteger q = curve.getField().getCharacteristic();
        Random random = new Random(9380L);
        for (int i = 0; i < numerators.length; ++i)
        {
            numerators[i] = new BigInteger(q.bitLength(), random).mod(q);
            denominators[i] = new BigInteger(q.bitLength(), random).mod(q.subtract(BigInteger.ONE)).add(BigInteger.ONE);
        }
        numerators[0] = BigInteger.ZERO;
        numerators[1] = BigInteger.ONE;
        numerators[2] = q.subtract(BigInteger.ONE);
        denominators[0] = BigInteger.ONE;
        denominators[1] = q.subtract(BigInteger.ONE);
        // Check exact roots AND flags before every trial, outside the measured region.
        for (int i = 0; i < numerators.length; ++i)
        {
            SqrtRatio expected = baseline.sqrtRatio(numerators[i], denominators[i]);
            SqrtRatio actual = optimized.sqrtRatio(numerators[i], denominators[i]);
            if (expected.isQR() != actual.isQR() || !expected.getRatio().equals(actual.getRatio()))
            {
                throw new IllegalStateException("Differential failure: " + field + "/" + i);
            }
        }
    }

    @Benchmark
    public LegacyGenericSqrtRatioCalculator baselineConstructor()
    {
        return new LegacyGenericSqrtRatioCalculator(curve, z);
    }

    @Benchmark
    public GenericSqrtRatioCalculator optimizedConstructor()
    {
        return new GenericSqrtRatioCalculator(curve, z);
    }

    @Benchmark
    public SqrtRatio baselineConstructAndRatio()
    {
        int sample = index++ & 63;
        return new LegacyGenericSqrtRatioCalculator(curve, z).sqrtRatio(numerators[sample], denominators[sample]);
    }

    @Benchmark
    public SqrtRatio optimizedConstructAndRatio()
    {
        int sample = index++ & 63;
        return new GenericSqrtRatioCalculator(curve, z).sqrtRatio(numerators[sample], denominators[sample]);
    }

    @Benchmark
    public SqrtRatio baselineReuse()
    {
        int sample = index++ & 63;
        return baseline.sqrtRatio(numerators[sample], denominators[sample]);
    }

    @Benchmark
    public SqrtRatio optimizedReuse()
    {
        int sample = index++ & 63;
        return optimized.sqrtRatio(numerators[sample], denominators[sample]);
    }
}
