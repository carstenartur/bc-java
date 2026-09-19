#!/usr/bin/env python3
"""Strict validation of the fixed public-API experiment; no timing acceptance threshold."""
import json
import math
from pathlib import Path
import sys

CLASS = 'org/bouncycastle/crypto/hash2curve/impl/GenericSqrtRatioCalculator.class'
FIELDS = ('P256', 'P384', 'P521')
WORKLOADS = ('getInstance', 'createAndHash', 'reuseHash')
PREFIX = 'org.bouncycastle.research.hash2curveapi.PublicApiBenchmark.'


def check_entries(old, new):
    if old.keys() != new.keys() or {k for k in old if old[k] != new[k]} != {CLASS}:
        raise ValueError('Library JARs must differ in exactly the calculator class')


def summarize(rows):
    expected = {(f, w, v) for f in FIELDS for w in WORKLOADS for v in ('baseline', 'optimized')}
    found = {}
    for entry in rows:
        r = entry['jmh']; m = r['primaryMetric']; a = r['secondaryMetrics']['gc.alloc.rate.norm']
        key = (r['params']['field'], r['benchmark'].removeprefix(PREFIX), entry['variant'])
        samples = m['rawData']
        values = [m['score'], m['scoreError'], *m['scoreConfidence'], a['score']]
        if (not r['benchmark'].startswith(PREFIX) or key not in expected or key in found
                or r['mode'] != 'avgt' or r['forks'] != 2 or r['threads'] != 1
                or r['warmupIterations'] != 3 or r['measurementIterations'] != 5
                or r['warmupTime'] != '500 ms' or r['measurementTime'] != '500 ms'
                or m['scoreUnit'] != 'us/op' or a['scoreUnit'] != 'B/op'
                or len(samples) != 2 or any(len(f) != 5 for f in samples)
                or any(not math.isfinite(x) for x in values)
                or m['score'] <= 0 or m['scoreError'] < 0 or a['score'] < 0
                or any(not math.isfinite(x) or x <= 0 for f in samples for x in f)):
            raise ValueError('Invalid/duplicate/incomplete row: ' + str(key))
        flat = [x for f in samples for x in f]
        if not math.isclose(sum(flat) / len(flat), m['score'], rel_tol=1e-10):
            raise ValueError('Mean does not match raw data')
        found[key] = r
    if set(found) != expected:
        raise ValueError('Incomplete fixed-plan matrix')
    pairs = []; ratios = {}
    for w in WORKLOADS:
        per_field = []
        for f in FIELDS:
            b = found[f,w,'baseline']; o = found[f,w,'optimized']
            bm = b['primaryMetric']; om = o['primaryMetric']
            ratio = om['score']/bm['score']; per_field.append(ratio)
            ba = b['secondaryMetrics']['gc.alloc.rate.norm']['score']; oa = o['secondaryMetrics']['gc.alloc.rate.norm']['score']
            separated = ('optimized lower' if om['scoreConfidence'][1] < bm['scoreConfidence'][0]
                         else 'optimized higher' if bm['scoreConfidence'][1] < om['scoreConfidence'][0] else 'overlap')
            pairs.append({'field': f, 'workload': w, 'baseline_us': bm['score'], 'optimized_us': om['score'],
                          'baseline_error': bm['scoreError'], 'optimized_error': om['scoreError'],
                          'time_ratio': ratio, 'baseline_bytes': ba, 'optimized_bytes': oa,
                          'allocation_ratio': oa/ba if ba else None, 'intervals': separated})
        ratios[w] = math.exp(sum(math.log(x) for x in per_field)/len(per_field))
    return {'pairs': pairs, 'ratios': ratios, 'primary_samples': len(rows)*10,
            'scope': 'Public API; 64 rotating 32-byte messages; no serialization in timed calls. Reuse is unchanged-code control.'}


def markdown(report):
    lines = ['# Public hash-to-curve API results', '', report['scope'], '',
             'JMH means +/- reported 99.9% intervals, microseconds per operation.', '',
             '| Workload | Field | Baseline | Optimized | Less time | Intervals |',
             '|---|---|---:|---:|---:|---|']
    for p in report['pairs']:
        lines.append('| {workload} | {field} | {baseline_us:.3f} +/- {baseline_error:.3f} | '
                     '{optimized_us:.3f} +/- {optimized_error:.3f} | {pct:.2f}% | {intervals} |'.format(
                         pct=100*(1-p['time_ratio']), **p))
    for w, r in report['ratios'].items():
        lines.append('\nEqual-field geometric optimized/baseline, {}: {:.6f} ({:.2f}% less time).'.format(w,r,100*(1-r)))
    return '\n'.join(lines)+'\n'


if __name__ == '__main__':
    report = summarize(json.loads(Path(sys.argv[1]).read_text()))
    print(markdown(report))
