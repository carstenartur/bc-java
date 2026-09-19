#!/usr/bin/env python3
"""Run all predeclared cases, paired across same-named BC class implementations."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from study import FIELDS, WORKLOADS, PREFIX, markdown, summarize

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE/'evidence'


def execute(command, log):
    with log.open('w') as f:
        result = subprocess.run(command, cwd=HERE, stdout=f, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(), file=sys.stderr)
        raise RuntimeError('Command failed: ' + repr(command))


def main():
    EVIDENCE.mkdir(exist_ok=True)
    execute(['mvn', '--batch-mode', '--no-transfer-progress', 'package'], EVIDENCE/'maven.log')
    jar = HERE/'target/benchmarks.jar'
    with zipfile.ZipFile(jar) as z:
        if any(n.startswith(('org/bouncycastle/crypto/', 'org/bouncycastle/math/')) for n in z.namelist()):
            raise RuntimeError('The harness must not shadow the selected BC library')
    for variant in ('baseline', 'optimized'):
        command = ['java', '-cp', str(jar)+os.pathsep+str(HERE/'lib'/(variant+'.jar')),
                   'org.bouncycastle.research.hash2curveapi.ApiVectors']
        with (EVIDENCE/(variant+'-vectors.txt')).open('w') as out, (EVIDENCE/(variant+'-origins.txt')).open('w') as err:
            subprocess.run(command, stdout=out, stderr=err, check=True)
    expected = EVIDENCE/'baseline-vectors.txt'
    if len(expected.read_text().splitlines()) != 201 or expected.read_bytes() != (EVIDENCE/'optimized-vectors.txt').read_bytes():
        raise RuntimeError('The 201 exact public API point comparisons must agree')
    execute(['java','-version'], EVIDENCE/'java.txt')
    execute(['uname','-a'], EVIDENCE/'uname.txt')
    if sys.platform.startswith('linux'): execute(['lscpu'], EVIDENCE/'cpu.txt')
    rows = []; commands = []
    for i, (field, work) in enumerate((f,w) for f in FIELDS for w in WORKLOADS):
        # Alternate first variant by case; fixed before observing measurements.
        variants = ('baseline', 'optimized') if i % 2 == 0 else ('optimized', 'baseline')
        for variant in variants:
            name = field+'-'+work+'-'+variant
            output = EVIDENCE/(name+'.json')
            command = ['java', '-cp', str(jar)+os.pathsep+str(HERE/'lib'/(variant+'.jar')),
                       'org.openjdk.jmh.Main', PREFIX+work+'$', '-p', 'field='+field,
                       '-f', '2', '-wi', '3', '-i', '5', '-w', '500ms', '-r', '500ms',
                       '-t', '1', '-prof', 'gc', '-foe', 'true', '-jvmArgs',
                       '-Xms256m -Xmx512m -Dbc.api.expected='+str(expected),
                       '-rf', 'json', '-rff', str(output)]
            commands.append(command)
            (EVIDENCE/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
            print('Measuring ' + name, flush=True)
            execute(command, EVIDENCE/(name+'.log'))
            data = json.loads(output.read_text())
            if len(data) != 1: raise ValueError('Each invocation must produce exactly one case')
            rows.append({'variant': variant, 'jmh': data[0]})
    (EVIDENCE/'all-rows.json').write_text(json.dumps(rows, indent=2)+'\n')
    report = summarize(rows)
    (EVIDENCE/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    (EVIDENCE/'summary.md').write_text(markdown(report))
    hashes = {str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in HERE.rglob('*') if p.is_file() and
              (p.suffix in ('.java','.py','.xml','.jar') or p.name=='README.md') and '__pycache__' not in str(p)}
    (EVIDENCE/'file-hashes.json').write_text(json.dumps(hashes, indent=2)+'\n')
    (EVIDENCE/'exit-code.txt').write_text('0\n')
    print(markdown(report))


if __name__ == '__main__': main()
