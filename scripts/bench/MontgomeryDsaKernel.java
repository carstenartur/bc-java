package org.bouncycastle.crypto.signers.mldsa;

import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.util.Random;

import org.bouncycastle.crypto.params.MLDSAParameters;

/** Measures complete 256-coefficient dot products with the production PolyVec implementation. */
public class MontgomeryDsaKernel
{
    public static void main(String[] args)
    {
        Random random = new Random(20261120);
        ThreadMXBean timer = ManagementFactory.getThreadMXBean();
        for (MLDSAParameters p : new MLDSAParameters[]{ MLDSAParameters.ml_dsa_44,
            MLDSAParameters.ml_dsa_65, MLDSAParameters.ml_dsa_87 })
        {
            MLDSAEngine engine = MLDSAEngine.getInstance(p, null);
            int k = engine.getDilithiumL();
            PolyVec a = new PolyVec(engine, k), b = new PolyVec(engine, k);
            Poly dest = new Poly(engine);
            for (int row = 0; row < k; ++row)
            {
                for (int j = 0; j < 256; ++j)
                {
                    a.getVectorIndex(row).setCoeffIndex(j, random.nextInt(MLDSAEngine.DilithiumQ));
                    b.getVectorIndex(row).setCoeffIndex(j, random.nextInt(68324859) - 34162429);
                }
            }
            for (int sample = 0; sample < 4; ++sample)
            {
                int count = 100000;
                long sum = 0L;
                long start = timer.getCurrentThreadCpuTime();
                for (int i = 0; i < count; ++i)
                {
                    a.getVectorIndex(0).setCoeffIndex(0, i);
                    dest.pointwiseAccountMontgomery(a, b);
                    sum += Reduce.conditionalAddQ(Reduce.reduce32(dest.getCoeffIndex(i & 255)));
                }
                System.out.printf("%s,%d,%.1f,%d%n", p.getName(), sample,
                    (double)(timer.getCurrentThreadCpuTime() - start) / count, sum);
            }
        }
    }
}
