import java.io.File;
import java.lang.management.ManagementFactory;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;
import java.util.function.IntUnaryOperator;

import com.sun.management.ThreadMXBean;
import org.bouncycastle.crypto.digests.SHAKEDigest;
import org.bouncycastle.crypto.kems.mlkem.MLKEMEngine;
import org.bouncycastle.crypto.params.MLDSAParameters;
import org.bouncycastle.crypto.params.MLKEMParameters;
import org.bouncycastle.crypto.params.MLKEMPrivateKeyParameters;
import org.bouncycastle.crypto.params.MLKEMPublicKeyParameters;
import org.bouncycastle.crypto.signers.mldsa.MLDSAEngine;

/**
 * Paired full-operation benchmark for two separately compiled BC trees (JDK 17+).
 * Pass dsa or kem, followed by the baseline and candidate classpaths. Each path
 * must include these benchmark classes. Each result row measures one batch of
 * operations; alternate order across batches and rerun in fresh JVMs.
 */
public class MontgomeryOperations
{
    private static final byte[][] inputs = new byte[16][32];
    private static final int warmup = Integer.getInteger("warmup", 512);
    private static final int count = Integer.getInteger("count", 128);
    private static final ThreadMXBean memory = ManagementFactory.getPlatformMXBean(ThreadMXBean.class);

    // Keep two isolated copies of BC in the same VM so adjacent samples see similar system load.
    private static Map<String, IntUnaryOperator> load(String family, String paths)
        throws Exception
    {
        String[] entries = paths.split(File.pathSeparator);
        URL[] urls = new URL[entries.length];
        for (int i = 0; i < entries.length; ++i)
        {
            urls[i] = new File(entries[i]).toURI().toURL();
        }
        URLClassLoader loader = new URLClassLoader(urls, ClassLoader.getPlatformClassLoader());
        Class<?> worker = Class.forName("MontgomeryOperations", true, loader);
        @SuppressWarnings("unchecked")
        Map<String, IntUnaryOperator> operations = (Map<String, IntUnaryOperator>)worker
            .getMethod("operations", String.class).invoke(null, family);
        return operations;
    }

    public static void main(String[] args)
        throws Exception
    {
        Map<String, IntUnaryOperator> baseline = load(args[0], args[1]), candidate = load(args[0], args[2]);
        if (memory != null && memory.isThreadAllocatedMemorySupported())
        {
            memory.setThreadAllocatedMemoryEnabled(true);
        }
        System.out.println("scheme,operation,sample,variant,wall_ns_per_op,cpu_ns_per_op,bytes_per_op,checksum");
        for (String name : baseline.keySet())
        {
            String selected = System.getProperty("only");
            if (selected != null && !selected.equals(name))
            {
                continue;
            }
            IntUnaryOperator a = baseline.get(name), b = candidate.get(name);
            for (int i = 0; i < warmup; ++i)
            {
                int input = i % inputs.length;
                if (a.applyAsInt(input) != b.applyAsInt(input))
                {
                    throw new IllegalStateException("different results: " + name);
                }
            }
            for (int sample = 0; sample < 8; ++sample)
            {
                boolean reversed = ((sample & 1) != 0) != Boolean.getBoolean("reverse");
                if (reversed)
                {
                    measure(name, sample, "candidate", b);
                    measure(name, sample, "base", a);
                }
                else
                {
                    measure(name, sample, "base", a);
                    measure(name, sample, "candidate", b);
                }
            }
        }
    }

    public static Map<String, IntUnaryOperator> operations(String family)
    {
        Map<String, IntUnaryOperator> operations = new LinkedHashMap<String, IntUnaryOperator>();
        Random random = new Random(20261120);
        for (byte[] input : inputs)
        {
            random.nextBytes(input);
        }
        if ("dsa".equals(family))
        {
            for (MLDSAParameters p : new MLDSAParameters[]{ MLDSAParameters.ml_dsa_44,
                MLDSAParameters.ml_dsa_65, MLDSAParameters.ml_dsa_87 })
            {
                signatureOperations(p, operations);
            }
        }
        else if ("kem".equals(family))
        {
            for (MLKEMParameters p : new MLKEMParameters[]{ MLKEMParameters.ml_kem_512,
                MLKEMParameters.ml_kem_768, MLKEMParameters.ml_kem_1024 })
            {
                kemOperations(p, operations);
            }
        }
        else
        {
            throw new IllegalArgumentException("expected dsa or kem");
        }
        return operations;
    }

    private static void signatureOperations(MLDSAParameters p, Map<String, IntUnaryOperator> operations)
    {
        MLDSAEngine keygen = MLDSAEngine.getInstance(p, null);
        byte[][] key = keygen.generateKeyPairInternal(inputs[0]);
        MLDSAEngine signer = MLDSAEngine.getInstance(p, null);
        signer.initSign(key[2], false, new byte[0]);
        MLDSAEngine verifier = MLDSAEngine.getInstance(p, null);
        verifier.initVerify(key[0], key[6], false, new byte[0]);
        byte[][] signatures = new byte[inputs.length][];
        for (int i = 0; i < inputs.length; i++)
        {
            signatures[i] = sign(signer, key, i);
        }
        operations.put(p.getName() + ",keygen", i -> keygen.generateKeyPairInternal(inputs[i])[6][i]);
        operations.put(p.getName() + ",sign", i -> sign(signer, key, i)[i]);
        operations.put(p.getName() + ",verify", i ->
        {
            SHAKEDigest digest = verifier.getShake256Digest();
            digest.update(inputs[i], 0, inputs[i].length);
            if (!verifier.verifyInternal(signatures[i], signatures[i].length, digest, key[0], key[6]))
            {
                throw new IllegalStateException("signature verification failed");
            }
            return signatures[i][i];
        });
    }

    private static byte[] sign(MLDSAEngine signer, byte[][] key, int i)
    {
        return signer.signInternal(inputs[i], inputs[i].length, key[0], key[1], key[5], key[3], key[4], inputs[i]);
    }

    private static void kemOperations(MLKEMParameters p, Map<String, IntUnaryOperator> operations)
    {
        MLKEMEngine engine = MLKEMEngine.getInstance(p);
        byte[][] key = engine.generateKemKeyPairInternal(inputs[0], inputs[1]);
        MLKEMPrivateKeyParameters sk = new MLKEMPrivateKeyParameters(p, key[2], key[3], key[4], key[0], key[1]);
        MLKEMPublicKeyParameters pk = sk.getPublicKeyParameters();
        byte[][] ciphertexts = new byte[inputs.length][];
        for (int i = 0; i < inputs.length; ++i)
        {
            byte[][] result = engine.kemEncrypt(pk, inputs[i]);
            ciphertexts[i] = result[1];
            if (!java.util.Arrays.equals(result[0], engine.kemDecrypt(sk, result[1])))
            {
                throw new IllegalStateException("decapsulation failed");
            }
        }
        operations.put(p.getName() + ",keygen", i -> engine.generateKemKeyPairInternal(inputs[i], inputs[1])[0][i]);
        operations.put(p.getName() + ",encap", i -> engine.kemEncrypt(pk, inputs[i])[1][i]);
        operations.put(p.getName() + ",decap", i -> engine.kemDecrypt(sk, ciphertexts[i])[i]);
    }

    private static void measure(String name, int sample, String variant, IntUnaryOperator operation)
    {
        long checksum = 0;
        long startBytes = allocated();
        long cpuStart = cpuTime();
        long start = System.nanoTime();
        for (int i = 0; i < count; i++)
        {
            checksum += operation.applyAsInt(i % inputs.length);
        }
        long elapsed = System.nanoTime() - start;
        long cpuEnd = cpuTime();
        long bytes = allocated();
        System.out.printf("%s,%d,%s,%.1f,%.1f,%.1f,%d%n", name, sample, variant, (double)elapsed / count,
            cpuStart < 0 ? -1.0 : (double)(cpuEnd - cpuStart) / count, bytes < 0 ? -1.0 : (double)(bytes - startBytes) / count, checksum);
    }

    private static long cpuTime()
    {
        return memory != null && memory.isCurrentThreadCpuTimeSupported() ? memory.getCurrentThreadCpuTime() : -1;
    }

    private static long allocated()
    {
        return memory != null && memory.isThreadAllocatedMemorySupported()
            ? memory.getThreadAllocatedBytes(Thread.currentThread().getId()) : -1;
    }
}
