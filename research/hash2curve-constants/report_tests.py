#!/usr/bin/env python3
"""Summarize actual JUnit XML; a successful command with no tests is not evidence."""
import argparse
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('root', nargs='?', default='.')
parser.add_argument('--build-log', type=Path, help='Log of the complete Gradle invocation')
parser.add_argument('--exit-code', type=Path, help='Exit status written after that invocation returns')
args = parser.parse_args()
if (args.build_log is None) != (args.exit_code is None):
    parser.error('--build-log and --exit-code must be supplied together')
root = Path(args.root)
paths = sorted(root.glob('**/build/test-results/**/TEST-*.xml'))
suites = []
new_tests = set()
for path in paths:
    suite = ET.parse(path).getroot()
    cases = list(suite.iter('testcase'))
    for case in cases:
        if (case.get('classname', '').endswith('.GenericSqrtRatioConstantsTest')
                and case.find('skipped') is None):
            new_tests.add(case.get('name'))
    suites.append({'file': str(path), 'tests': len(cases),
                   'failures': [c.get('classname', '') + '.' + c.get('name', '') for c in cases
                                if c.find('failure') is not None or c.find('error') is not None],
                   'skipped': sum(c.find('skipped') is not None for c in cases)})
report = {'test_cases': sum(s['tests'] for s in suites), 'suites': suites,
          'new_constant_tests': sorted(new_tests), 'build_complete': None}
if args.build_log is not None:
    report['build_complete'] = False
    try:
        exit_code = int(args.exit_code.read_text().strip())
        outcomes = re.findall(r'^BUILD (SUCCESSFUL|FAILED)(?:\s|$)',
                              args.build_log.read_text(), re.MULTILINE)
        report['build_exit_code'] = exit_code
        report['build_complete'] = exit_code == 0 and bool(outcomes) and outcomes[-1] == 'SUCCESSFUL'
    except (OSError, ValueError) as error:
        report['build_evidence_error'] = str(error)
print(json.dumps(report, indent=2))
if not report['test_cases']:
    raise SystemExit('No actual JUnit XML test cases found')
expected = {'testInitializationUsesSingleModularExponentiation', 'testConstantsMatchDirectPowersForSmallFields',
            'testConstantsMatchDirectPowersForLargeFields', 'testRepeatedRatiosOverSmallFields'}
if not expected.issubset(new_tests):
    raise SystemExit('The four new constant tests were not all executed')
if any(s['failures'] for s in suites):
    raise SystemExit('JUnit reported failures; see the summary above')
if report['build_complete'] is False:
    raise SystemExit('Incomplete or failed build; green partial JUnit XML is not full-run evidence')
