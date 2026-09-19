import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

SCRIPT = Path(__file__).with_name('report_tests.py')
NAMES = ('testInitializationUsesSingleModularExponentiation',
         'testConstantsMatchDirectPowersForSmallFields',
         'testConstantsMatchDirectPowersForLargeFields',
         'testRepeatedRatiosOverSmallFields')


class TestExecutionReportTest(unittest.TestCase):
    def run_report(self, outcome=None, omit=False):
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory) / 'core/build/test-results'
            results.mkdir(parents=True)
            suite = ET.Element('testsuite')
            for i, name in enumerate(NAMES[:-1] if omit else NAMES):
                case = ET.SubElement(suite, 'testcase', {
                    'classname': 'org.bouncycastle.crypto.hash2curve.test.impl.GenericSqrtRatioConstantsTest',
                    'name': name})
                if i == 0 and outcome:
                    ET.SubElement(case, outcome)
            ET.ElementTree(suite).write(results / 'TEST-constants.xml')
            return subprocess.run([sys.executable, str(SCRIPT), directory],
                                  text=True, capture_output=True)

    def test_all_executed(self):
        result = self.run_report()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(4, json.loads(result.stdout)['test_cases'])

    def test_skipped_new_test_rejected(self):
        result = self.run_report('skipped')
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_failed_new_test_rejected(self):
        self.assertNotEqual(0, self.run_report('failure').returncode)

    def test_missing_new_test_rejected(self):
        self.assertNotEqual(0, self.run_report(omit=True).returncode)


if __name__ == '__main__':
    unittest.main()
