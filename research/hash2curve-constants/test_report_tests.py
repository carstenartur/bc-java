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
    def run_report(self, outcome=None, omit=False, build_log=None, exit_code=None, check_build=False):
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
            command = [sys.executable, str(SCRIPT), directory]
            if check_build:
                log = Path(directory) / 'build.log'
                receipt = Path(directory) / 'exit-code.txt'
                if build_log is not None:
                    log.write_text(build_log)
                if exit_code is not None:
                    receipt.write_text(exit_code)
                command += ['--build-log', str(log), '--exit-code', str(receipt)]
            return subprocess.run(command, text=True, capture_output=True)

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


    def test_completed_build_accepted(self):
        result = self.run_report(build_log='BUILD SUCCESSFUL in 3s\n', exit_code='0\n', check_build=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout).get('build_complete'))

    def test_partial_green_xml_without_build_completion_rejected(self):
        result = self.run_report(build_log='> Task :core:test\n> Task :pg:test\n', check_build=True)
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_missing_build_log_rejected(self):
        result = self.run_report(exit_code='0\n', check_build=True)
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_missing_exit_receipt_rejected(self):
        result = self.run_report(build_log='BUILD SUCCESSFUL in 3s\n', check_build=True)
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_nonzero_gradle_exit_rejected(self):
        result = self.run_report(build_log='BUILD SUCCESSFUL in 3s\n', exit_code='1\n', check_build=True)
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_failed_build_with_green_xml_rejected(self):
        result = self.run_report(build_log='BUILD FAILED in 3s\n', exit_code='0\n', check_build=True)
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_later_failed_build_not_hidden_by_earlier_success(self):
        result = self.run_report(build_log='BUILD SUCCESSFUL in 3s\nBUILD FAILED in 1s\n',
                                 exit_code='0\n', check_build=True)
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_unchecked_build_not_reported_as_complete(self):
        result = self.run_report()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIsNone(json.loads(result.stdout).get('build_complete'))


if __name__ == '__main__':
    unittest.main()
