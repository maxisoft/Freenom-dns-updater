import os
import sys
import glob
import unittest

if __name__ == '__main__':
    path = os.path.join(os.path.dirname(__file__), "freenom_dns_updater")
    sys.path.insert(1, path)
    test_files = glob.glob(os.path.join("freenom_dns_updater", 'test', '*test*.py'), recursive=True)
    module_strings = [test_file[0:len(test_file)-3].replace(os.sep, '.') for test_file in test_files]
    suites = [unittest.defaultTestLoader.loadTestsFromName(test_file) for test_file in module_strings]
    testSuite = unittest.TestSuite(suites)
    text_runner = unittest.TextTestRunner().run(testSuite)