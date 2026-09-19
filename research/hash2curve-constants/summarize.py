#!/usr/bin/env python3
"""Report all fixed-plan JMH pairs; reject incomplete or mismatched data."""
import json
import math
from pathlib import Path
import sys

FIELDS = ('P256', 'P384', 'P521', 'CURVE25519')
WORKLOADS = ('Constructor', 'ConstructAndRatio', 'Reuse')
PREFIX = 'org.bouncycastle.research.hash2curve.ConstantsBenchmark.'


def summarize(rows):
    expected = {(f, v + w) for f in FIELDS for v in ('baseline', 'optimized') for w in WORKLOADS}
    found = {}
    for row in rows:
        name = row['benchmark']
        key = (row['params']['field'], name.removeprefix(PREFIX))
        metric = row['primaryMetric']
        raw = metric['rawData']
        allocation = row['secondaryMetrics']['gc.alloc.rate.norm']
        if (not name.startswith(PREFIX) or key not in expected or key in found
                or row['mode'] != 'avgt' or row['forks'] != 2
                or metric['scoreUnit'] != 'us/op' or allocation['scoreUnit'] != 'B/op'
                or len(raw) != 2 or any(len(fork) != 5 for fork in raw)
                or not math.isfinite(metric['score']) or metric['score'] <= 0
                or not math.isfinite(metric['scoreError'])
                or not math.isfinite(allocation['score'])
                or any(not math.isfinite(x) or x <= 0 for fork in raw for x in fork)):
            raise ValueError('Invalid, duplicate, or incomplete JMH row: ' + str(key))
        found[key] = row
    if set(found) != expected:
        raise ValueError('Incomplete fixed-plan workload/field matrix')
    lines = ['# Generic sqrt_ratio constructor experiment', '',
             'Times are JMH means +/- its reported 99.9% error interval (us/op).',
             'Reuse is an unchanged-code control, not an optimization target.', '']
    for workload in WORKLOADS:
        lines += ['## ' + workload, '',
                  '| Field | Baseline us/op | Optimized us/op | Time reduction | Alloc. reduction | Non-overlapping time intervals |',
                  '|---|---:|---:|---:|---:|---|']
        ratios = []
        for field in FIELDS:
            b = found[field, 'baseline' + workload]
            o = found[field, 'optimized' + workload]
            bm, om = b['primaryMetric'], o['primaryMetric']
            ratio = om['score'] / bm['score']
            ratios.append(ratio)
            ba = b['secondaryMetrics']['gc.alloc.rate.norm']['score']
            oa = o['secondaryMetrics']['gc.alloc.rate.norm']['score']
            allocation = f'{100 * (1 - oa / ba):.2f}%' if ba else 'n/a'
            separation = 'optimized lower' if om['scoreConfidence'][1] < bm['scoreConfidence'][0] else (
                'optimized higher' if bm['scoreConfidence'][1] < om['scoreConfidence'][0] else 'overlap')
            lines.append(f'| {field} | {bm["score"]:.3f} +/- {bm["scoreError"]:.3f} | '
                         f'{om["score"]:.3f} +/- {om["scoreError"]:.3f} | '
                         f'{100 * (1 - ratio):.2f}% | {allocation} | {separation} |')
        gm = math.exp(sum(map(math.log, ratios)) / len(ratios))
        lines += ['', f'Equal-field geometric mean optimized/baseline: {gm:.6f} '
                      f'({100 * (1 - gm):.2f}% less time).', '']
    lines += ['These are descriptive measurements on this runner/JVM, not a cryptographic security claim,',
              'a general application speedup, or an automatic performance acceptance gate.']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: summarize.py JMH.json')
    print(summarize(json.loads(Path(sys.argv[1]).read_text())), end='')
