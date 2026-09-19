#!/usr/bin/env python3
"""Summarize actual JUnit XML; a successful command with no tests is not evidence."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
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
          'new_constant_tests': sorted(new_tests)}
print(json.dumps(report, indent=2))
if not report['test_cases']:
    raise SystemExit('No actual JUnit XML test cases found')
expected = {'testInitializationUsesSingleModularExponentiation', 'testConstantsMatchDirectPowersForSmallFields',
            'testConstantsMatchDirectPowersForLargeFields', 'testRepeatedRatiosOverSmallFields'}
if not expected.issubset(new_tests):
    raise SystemExit('The four new constant tests were not all executed')
if any(s['failures'] for s in suites):
    raise SystemExit('JUnit reported failures; see the summary above')
