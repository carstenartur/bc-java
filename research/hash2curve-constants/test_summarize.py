import copy
import unittest
from summarize import summarize


def samples():
    rows = []
    for field in ('P256', 'P384', 'P521', 'CURVE25519'):
        for workload in ('Constructor', 'ConstructAndRatio', 'Reuse'):
            for variant, score in (('baseline', 2.0), ('optimized', 1.0)):
                rows.append({'benchmark': 'org.bouncycastle.research.hash2curve.ConstantsBenchmark.' + variant + workload,
                             'params': {'field': field}, 'mode': 'avgt', 'forks': 2,
                             'primaryMetric': {'score': score, 'scoreError': 0.1, 'scoreUnit': 'us/op',
                                               'scoreConfidence': [score - 0.1, score + 0.1],
                                               'rawData': [[score] * 5, [score] * 5]},
                             'secondaryMetrics': {'gc.alloc.rate.norm': {'score': 64.0, 'scoreUnit': 'B/op'}}})
    return rows


class SummaryTest(unittest.TestCase):
    def test_complete_data(self):
        report = summarize(samples())
        self.assertIn('50.00%', report)
        self.assertIn('unchanged-code control', report)
        self.assertEqual(3, report.count('geometric mean'))

    def test_missing_pair_rejected(self):
        with self.assertRaises(ValueError):
            summarize(samples()[:-1])

    def test_duplicate_rejected(self):
        rows = samples()
        with self.assertRaises(ValueError):
            summarize(rows[:-1] + [copy.deepcopy(rows[0])])

    def test_wrong_unit_rejected(self):
        rows = samples()
        rows[0]['primaryMetric']['scoreUnit'] = 'ns/op'
        with self.assertRaises(ValueError):
            summarize(rows)

    def test_incomplete_forks_rejected(self):
        rows = samples()
        rows[0]['primaryMetric']['rawData'] = [[1.0] * 5]
        with self.assertRaises(ValueError):
            summarize(rows)


if __name__ == '__main__':
    unittest.main()
