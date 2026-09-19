package org.bouncycastle.research.hash2curveapi;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.bouncycastle.crypto.hash2curve.HashToCurveProfile;
import org.bouncycastle.crypto.hash2curve.HashToEllipticCurve;
import org.bouncycastle.math.ec.ECPoint;
import org.bouncycastle.util.encoders.Hex;
import org.openjdk.jmh.annotations.*;

@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
public class PublicApiBenchmark
{
    @Param({"P256", "P384", "P521"})
    public String field;
    private HashToCurveProfile profile;
    private HashToEllipticCurve reused;
    private byte[][] messages;
    private int index;

    @Setup(Level.Trial)
    public void setup() throws Exception
    {
        profile = ApiVectors.profile(field);
        messages = ApiVectors.messages();
        reused = HashToEllipticCurve.getInstance(profile, ApiVectors.DST);
        List<String> expected = Files.readAllLines(Paths.get(System.getProperty("bc.api.expected")), StandardCharsets.UTF_8);
        int checked = 0;
        for (int i = 0; i < messages.length; ++i)
        {
            String result = field + " " + i + " " + Hex.toHexString(reused.hashToCurve(messages[i]).getEncoded(false));
            if (!expected.contains(result)) throw new IllegalStateException("Exact point mismatch: " + field + "/" + i);
            ++checked;
        }
        if (checked != 67 || expected.size() != 201) throw new IllegalStateException("Incomplete vectors");
    }

    @Benchmark
    public HashToEllipticCurve getInstance()
    {
        return HashToEllipticCurve.getInstance(profile, ApiVectors.DST);
    }

    @Benchmark
    public ECPoint createAndHash()
    {
        return HashToEllipticCurve.getInstance(profile, ApiVectors.DST).hashToCurve(messages[index++ & 63]);
    }

    @Benchmark
    public ECPoint reuseHash()
    {
        return reused.hashToCurve(messages[index++ & 63]);
    }
}
