# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/11


import sys
import argparse
import textwrap

from config.config import Config
from common import factory
from common.errors import NotFound
from common.logger import Logger
from common.util import CustomerUtil
from models.testparse import (Parser, MockData, CaseData)
from models.testengine import (TestSuite, TestRunner, TestAssert)
from models.testreport import TestReport

logger = Logger.get_logger(__name__)


def parse_cmd(argv=sys.argv[1:]):
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(
                                             """
                                             用法:
                                             python scenario.py "./file/scenario-test.xlsx" "./file/mock-data.xlsx"
                                             """))
    parser.add_argument("testcase", type=str, help="测试用例文件")
    parser.add_argument("testdata", type=str, help="测试数据文件")
    opts = parser.parse_args(argv)
    return vars(opts)


def parse_path(file_name):
    """
    文件路径/报告路径
    """
    if not file_name:
        raise NotFound("not_exist||file_name={}".format(file_name))

    file_dirpath = CustomerUtil.get_file_dirpath(__file__)
    file_abspath = CustomerUtil.get_file_joinpath(file_dirpath, file_name)

    if not CustomerUtil.is_file_exists(file_abspath):
        raise NotFound("not_exist||file_path={}".format(file_abspath))

    report_path = CustomerUtil.get_report_path(file_dirpath, file_name)

    return file_abspath, report_path


def file_info():
    """
    测试用例路径/测试数据路径/测试报告路径
    """
    testcase_file = parse_cmd().get("testcase")
    testdata_file = parse_cmd().get("testdata")

    testcase_file_path, report_file_path = parse_path(testcase_file)
    testdata_file_path, _ = parse_path(testdata_file)

    return testcase_file_path, testdata_file_path, report_file_path


def main():
    # 1)基本信息
    sheet_name = Config.api_test_sheet_name
    api_title = Config.api_test_suites_title
    report_title = Config.api_test_report_title
    testcase_file_path, testdata_file_path, report_file_path = file_info()

    # 2)测试数据
    mock_data_parser = Parser(testdata_file_path, sheet_name)
    mock_data = MockData(mock_data_parser)

    # 3)测试用例
    case_data_parser = Parser(testcase_file_path, sheet_name)
    case_data = CaseData(case_data_parser, mock_data)

    # 4)融合用例
    testcases = case_data.data

    # 5)执行测试
    testsuite = TestSuite(api_title, testcases)
    testrunner = TestRunner(testsuite)
    testrunner.run_testsuite()

    # 6)关联断言
    TestAssert.run_special_assert(testsuite)

    # 7)测试报告
    testreport = TestReport(testsuite.json, report_file_path)
    testreport.report()

    # 8)测试提示
    logger.info("{}||path={}".format(report_title, report_file_path))


if __name__ == "__main__":
    main()
