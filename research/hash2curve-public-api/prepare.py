#!/usr/bin/env python3
"""Build two same-name BC libraries, differing only in the calculator class."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
from study import CLASS, check_entries

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = 'ab16374d37c7e18c4090eb8838ebbd72a92593f2'
SOURCE = 'core/src/main/java/org/bouncycastle/crypto/hash2curve/impl/GenericSqrtRatioCalculator.java'
OLD_BLOB = 'acf5666f51eb82688878bde8c447a58b6bdd73d1'
NEW_BLOB = '693f65df02ea381a25339a2cb9f40106e5b3d35e'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--core-jar', type=Path)
    parser.add_argument('--baseline-source', type=Path)
    parser.add_argument('--optimized-source', type=Path)
    args = parser.parse_args()
    old = args.baseline_source.read_bytes() if args.baseline_source else git('show', BASE + ':' + SOURCE)
    new = args.optimized_source.read_bytes() if args.optimized_source else (ROOT / SOURCE).read_bytes()
    if blob(old) != OLD_BLOB or blob(new) != NEW_BLOB:
        raise ValueError('Source does not match the predeclared production comparison')
    marker = b'    public SqrtRatio sqrtRatio'
    if old[old.index(marker):] != new[new.index(marker):]:
        raise ValueError('The reused operation must be unchanged')
    lib = HERE / 'lib'; lib.mkdir(exist_ok=True)
    evidence = HERE / 'evidence'; evidence.mkdir(exist_ok=True)
    input_jar = args.core_jar
    if input_jar is None:
        classes = ROOT / 'core/build/classes/java/main'
        if not (classes / CLASS).is_file(): raise RuntimeError('Build :core:classes first')
        input_jar = lib / 'input-core.jar'
        cmd = ['jar', 'cf', str(input_jar), '-C', str(classes), '.']
        resources = ROOT / 'core/build/resources/main'
        if resources.is_dir(): cmd += ['-C', str(resources), '.']
        subprocess.run(cmd, check=True)
    input_jar = input_jar.resolve()
    with zipfile.ZipFile(input_jar) as z:
        entries = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    if CLASS not in entries: raise ValueError('Input JAR has no calculator')
    outputs = {}
    for variant, source in [('baseline', old), ('optimized', new)]:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source_file = tmp / 'src' / CLASS.replace('.class', '.java')
            source_file.parent.mkdir(parents=True); source_file.write_bytes(source)
            classes = tmp / 'classes'; classes.mkdir()
            subprocess.run(['javac', '--release', '8', '-g:none', '-proc:none', '-cp', str(input_jar),
                            '-d', str(classes), str(source_file)], check=True)
            output = dict(entries); output[CLASS] = (classes / CLASS).read_bytes()
        jar = lib / (variant + '.jar')
        with zipfile.ZipFile(jar, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, data in sorted(output.items()):
                info = zipfile.ZipInfo(name, (2026, 9, 19, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, data)
        outputs[variant] = output
    check_entries(outputs['baseline'], outputs['optimized'])
    metadata = {'baseline_commit': BASE, 'baseline_source_blob': blob(old), 'optimized_source_blob': blob(new),
                'compiler': subprocess.check_output(['javac', '-version'], stderr=subprocess.STDOUT).decode().strip(),
                'input_core_sha256': hashlib.sha256(input_jar.read_bytes()).hexdigest(),
                'changed_jar_entries': [CLASS], 'entry_count': len(entries),
                'jars': {v: hashlib.sha256((lib/(v+'.jar')).read_bytes()).hexdigest() for v in outputs}}
    (evidence/'libraries.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__': main()
