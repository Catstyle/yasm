# -*- coding: utf-8 -*-
import os
import coverage
import unittest

import click


def run_test_case():
    loader = unittest.TestLoader()
    tests = loader.discover('tests')
    runner = unittest.runner.TextTestRunner()
    result = runner.run(tests)
    return 0 if result.wasSuccessful() else 1


@click.command()
@click.option('-t', 'test', is_flag=True, default=True, help='run test cases')
def main(test):
    omit = ['cover.py', 'tests/*']
    env = os.environ.get('VIRTUAL_ENV')
    if isinstance(env, str):
        omit.append(env + '/*')
    omit.append('')

    cov = coverage.coverage(omit=omit)
    cov.start()
    result = 0
    if test:
        result = run_test_case()

    cov.stop()
    cov.save()
    try:
        cov.report()
        cov.html_report(directory='coverage_html')
    except coverage.misc.CoverageException as ex:
        if ex.message == 'No data to report.':
            pass
        else:
            raise
    cov.erase()
    exit(result)


if __name__ == '__main__':
    main()
