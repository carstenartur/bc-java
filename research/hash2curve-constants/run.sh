#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HERE/evidence"
java -version 2>&1 | tee "$HERE/evidence/java.txt"
uname -a > "$HERE/evidence/uname.txt"
if command -v lscpu >/dev/null; then lscpu > "$HERE/evidence/cpu.txt"; fi
mvn --batch-mode --no-transfer-progress -f "$HERE/pom.xml" package 2>&1 | tee "$HERE/evidence/maven.log"
# No timing overrides: this plan is fixed before the first hosted run.
java -cp "$HERE/target/benchmarks.jar:$HERE/lib/bc-core.jar" org.openjdk.jmh.Main \
  'org.bouncycastle.research.hash2curve.ConstantsBenchmark.*' \
  -f 2 -wi 3 -i 5 -w 500ms -r 500ms -t 1 -prof gc -foe true \
  -jvmArgs '-Xms256m -Xmx512m' -rf json -rff "$HERE/evidence/jmh.json" \
  2>&1 | tee "$HERE/evidence/jmh.log"
python3 "$HERE/summarize.py" "$HERE/evidence/jmh.json" | tee "$HERE/evidence/summary.md"
