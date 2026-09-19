import copy
import unittest
from study import CLASS, FIELDS, WORKLOADS, check_entries, summarize


def rows():
    result = []
    for field in FIELDS:
        for work in WORKLOADS:
            for variant, score in [('baseline', 10.), ('optimized', 8.)]:
                result.append({'variant': variant, 'jmh': {
                    'benchmark': 'org.bouncycastle.research.hash2curveapi.PublicApiBenchmark.' + work,
                    'params': {'field': field}, 'mode': 'avgt', 'forks': 2,
                    'warmupIterations': 3, 'measurementIterations': 5, 'threads': 1,
                    'warmupTime': '500 ms', 'measurementTime': '500 ms',
                    'primaryMetric': {'score': score, 'scoreError': .1, 'scoreUnit': 'us/op',
                                      'scoreConfidence': [score-.1, score+.1], 'rawData': [[score]*5]*2},
                    'secondaryMetrics': {'gc.alloc.rate.norm': {'score': 128., 'scoreUnit': 'B/op'}}}})
    return result


class StudyTest(unittest.TestCase):
    def test_complete_report(self):
        r = summarize(rows())
        self.assertEqual(9, len(r['pairs']))
        self.assertAlmostEqual(.8, r['ratios']['createAndHash'])

    def test_missing_row(self):
        with self.assertRaises(ValueError): summarize(rows()[:-1])

    def test_duplicate_row(self):
        r = rows()
        with self.assertRaises(ValueError): summarize(r[:-1] + [r[0]])

    def test_missing_samples(self):
        r = rows(); r[0]['jmh']['primaryMetric']['rawData'] = [[10.]*5]
        with self.assertRaises(ValueError): summarize(r)

    def test_wrong_unit(self):
        r = rows(); r[0]['jmh']['primaryMetric']['scoreUnit'] = 'ns/op'
        with self.assertRaises(ValueError): summarize(r)

    def test_wrong_duration(self):
        r = rows(); r[0]['jmh']['warmupTime'] = '1 s'
        with self.assertRaises(ValueError): summarize(r)

    def test_nonfinite(self):
        r = rows(); r[0]['jmh']['primaryMetric']['score'] = float('nan')
        with self.assertRaises(ValueError): summarize(r)

    def test_jar_diff(self):
        check_entries({CLASS:b'old', 'x':b'same'}, {CLASS:b'new', 'x':b'same'})

    def test_extra_jar_change_rejected(self):
        with self.assertRaises(ValueError):
            check_entries({CLASS:b'old', 'x':b'same'}, {CLASS:b'new', 'x':b'changed'})

    def test_missing_jar_file_rejected(self):
        with self.assertRaises(ValueError): check_entries({CLASS:b'old'}, {CLASS:b'new', 'x':b'new'})

    def test_identical_jars_rejected(self):
        with self.assertRaises(ValueError): check_entries({CLASS:b'old'}, {CLASS:b'old'})

if __name__ == '__main__': unittest.main()
