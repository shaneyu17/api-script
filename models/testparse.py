# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/12


import json
import pandas as pd
from copy import deepcopy
from itertools import groupby
from collections import namedtuple

from config.config import Config
from common.util import CustomerUtil
from models.testengine import (TestCase, TestStep)


class RowData(object):
    """
    行内数据对象
    """
    row_mock = namedtuple("mockdata", ["currency", "amount", "address", "tag", "token", "fee", "callback", "node", "enable", "status"])
    row_case = namedtuple("testcase", ["title", "step", "purpose", "method", "api", "timeout", "encryption", "body", "expectation"])

    def __init__(self, row):
        self.row = row

    @property
    def mock(self):
        return self.row_mock(*self.row)

    @property
    def case(self):
        return self.row_case(*self.row)


class Parser(object):
    """
    解析文件对象
    """

    def __init__(self, file_path, sheet_name):
        self.file_path = file_path
        self.sheet_name = sheet_name

        self._data_frame = None
        self._testcases_ = []

    def parse(self):
        with pd.ExcelFile(self.file_path) as xls:
            data_frame = pd.read_excel(xls, sheet_name=self.sheet_name, dtype=str, na_filter=False)

        return data_frame

    @property
    def data(self):
        if self._data_frame is None:
            self._data_frame = self.parse()
        return self._data_frame


class MockData(object):
    """
    用例数据对象
    """

    def __init__(self, parser):
        self.parser = parser

    @property
    def raw(self):
        data = []
        for _, row1 in self.parser.data.iterrows():
            row1.token = True if row1.token == "是" else False
            row1.enable = True if row1.enable == "是" else False
            row2 = RowData(row1[:10])
            row_mock = row2.mock
            data.append(row_mock)

        return data

    @property
    def data(self):
        return self.raw


class CaseData(object):
    """
    用例集合对象
    """

    def __init__(self, parser, mock):
        self.parser = parser
        self.mock_data = mock.data

    @staticmethod
    def transfer_json(data1, data2, data3):
        if isinstance(data1, str):
            json_data = json.loads(data1)
        elif isinstance(data1, dict):
            json_data = data1
        else:
            raise RuntimeError(data1)

        for field, value in json_data.items():
            if isinstance(value, str):
                if getattr(data2, value, None) is not None:
                    json_data[field] = getattr(data2, value)
                elif value == "auto" and data3.get(field) is not None:
                    json_data[field] = data3[field]
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, str) and getattr(data2, item, None) is not None:
                        value[index] = getattr(data2, item)
            elif isinstance(value, dict):
                CaseData.transfer_json(value, data2, data3)

        return json_data

    @staticmethod
    def transfer_string(data1, data2):
        data = data1 if getattr(data2, data1, None) is None else getattr(data2, data1)

        return data

    @staticmethod
    def split_title(data):
        return data.split("|")[-1]

    @property
    def testcase_template(self):
        data = []
        for title1, steps in groupby(self.raw, lambda x: x.title):
            title2 = CaseData.split_title(title1)
            testcase = TestCase(title2)
            for step in steps:
                teststep = TestStep(step.step, step.purpose, step.method, step.api, step.timeout, step.encryption, step.body, step.expectation)
                testcase.steps.append(teststep)
            data.append(testcase)

        return data

    @property
    def raw(self):
        data = []
        for _, row1 in self.parser.data.iterrows():
            row2 = RowData(row1[:9])
            row_case = row2.case
            data.append(row_case)

        return data

    @property
    def data(self):
        testcase_data = []
        for index, data in enumerate(self.mock_data, 1):
            for testcase1 in self.testcase_template:
                testcase2 = deepcopy(testcase1)
                testcase2.title = testcase2.title.format(index=index, currency=data.currency)
                testcase2.enable = data.enable
                auto = {"orderNo": CustomerUtil.gen_order_no(), "source": Config.bypass_front_appid_content, }
                for step in testcase2.steps:
                    step.api = self.transfer_string(step.api, data)
                    step.body = self.transfer_json(step.body, data, auto)
                    step.expectation = self.transfer_json(step.expectation, data, auto)
                    step.encryption = True if step.encryption == "是" else False
                    step.timeout = int(step.timeout) if step.timeout else 0

                testcase_data.append(testcase2)

        return testcase_data


def main():
    mock_data_path = r"C:\Work\Git\wallet-tools-script\api-test\file\mock-data.xlsx"
    mock_data_parser = Parser(mock_data_path, Config.api_test_sheet_name)
    mock_data = MockData(mock_data_parser)

    case_data_path = r"C:\Work\Git\wallet-tools-script\api-test\file\scenario-test.xlsx"
    case_data_parser = Parser(case_data_path, Config.api_test_sheet_name)
    case_data = CaseData(case_data_parser, mock_data).data

    print(list(map(lambda x: x.dict, case_data)))


if __name__ == "__main__":
    main()
