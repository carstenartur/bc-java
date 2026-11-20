package org.bouncycastle.crypto.kems.mlkem;

import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.util.Random;

import org.bouncycastle.crypto.params.MLKEMParameters;

/** Measures complete 256-coefficient dot products with the production PolyVec implementation. */
public class MontgomeryKemKernel
{
    public static void main(String[] args)
    {
        Random random = new Random(20261120);
        ThreadMXBean timer = ManagementFactory.getThreadMXBean();
        for (MLKEMParameters p : new MLKEMParameters[]{ MLKEMParameters.ml_kem_512,
            MLKEMParameters.ml_kem_768, MLKEMParameters.ml_kem_1024 })
        {
            MLKEMEngine engine = MLKEMEngine.getInstance(p);
            int k = engine.getK();
            PolyVec a = new PolyVec(k), b = new PolyVec(k);
            Poly dest = new Poly();
            for (int row = 0; row < k; ++row)
            {
                for (int j = 0; j < 256; ++j)
                {
                    a.vec[row].setCoeffIndex(j, (short)random.nextInt(4096));
                    b.vec[row].setCoeffIndex(j, (short)random.nextInt(3330));
                }
            }
            for (int sample = 0; sample < 4; ++sample)
            {
                int count = 100000;
                long sum = 0L;
                long start = timer.getCurrentThreadCpuTime();
                for (int i = 0; i < count; ++i)
                {
                    a.vec[0].setCoeffIndex(0, (short)(i & 4095));
                    PolyVec.pointwiseAccountMontgomery(dest, a, b, engine);
                    sum += Reduce.condSubQ(dest.getCoeffIndex(i & 255));
                }
                System.out.printf("%s,%d,%.1f,%d%n", p.getName(), sample,
                    (double)(timer.getCurrentThreadCpuTime() - start) / count, sum);
            }
        }
    }
}
