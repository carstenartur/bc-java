package org.bouncycastle.research.hash2curveapi;

import java.util.Random;
import org.bouncycastle.crypto.hash2curve.HashToCurveProfile;
import org.bouncycastle.crypto.hash2curve.HashToEllipticCurve;
import org.bouncycastle.util.Arrays;
import org.bouncycastle.util.encoders.Hex;

/** Exact public-API comparisons, outside every timed region. */
public class ApiVectors
{
    public static final String DST = "BC-PUBLIC-API-COMPARISON-9380";

    public static HashToCurveProfile profile(String field)
    {
        if ("P256".equals(field)) return HashToCurveProfile.P256_XMD_SHA_256;
        if ("P384".equals(field)) return HashToCurveProfile.P384_XMD_SHA_384;
        if ("P521".equals(field)) return HashToCurveProfile.P521_XMD_SHA_512;
        throw new IllegalArgumentException(field);
    }

    public static byte[][] messages()
    {
        byte[][] values = new byte[67][];
        Random random = new Random(938019L);
        for (int i = 0; i < 64; ++i)
        {
            values[i] = new byte[32];
            random.nextBytes(values[i]);
        }
        values[64] = new byte[0];
        values[65] = new byte[]{97, 98, 99};
        values[66] = new byte[256];
        random.nextBytes(values[66]);
        return values;
    }

    public static void main(String[] args)
    {
        System.err.println("API: " + HashToEllipticCurve.class.getProtectionDomain().getCodeSource().getLocation());
        String[] fields = { "P256", "P384", "P521" };
        byte[][] inputs = messages();
        for (int f = 0; f < fields.length; ++f)
        {
            HashToCurveProfile profile = profile(fields[f]);
            HashToEllipticCurve reused = HashToEllipticCurve.getInstance(profile, DST);
            for (int i = 0; i < inputs.length; ++i)
            {
                byte[] expected = reused.hashToCurve(inputs[i]).getEncoded(false);
                byte[] actual = HashToEllipticCurve.getInstance(profile, DST).hashToCurve(inputs[i]).getEncoded(false);
                if (!Arrays.areEqual(expected, actual)) throw new IllegalStateException("Fresh/reused mismatch");
                System.out.println(fields[f] + " " + i + " " + Hex.toHexString(actual));
            }
        }
    }
}
