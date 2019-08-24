# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/12


import json
import time
from decimal import Decimal
from datetime import datetime
from enum import (Enum, unique)
from functools import reduce
from operator import add
from multiprocessing import Pool

from conn.httprunner import HTTPRunner
from common.errors import (InvalidParameter, NotFound, MisMatched)
from common.logger import (Logger, LoggerContext)
from common.util import (get_stringify_uuid, get_traceback)

logger = Logger.get_logger(__name__)


@unique
class ResultState(Enum):
    """
    测试结果状态对象
    """
    PASS = "PASS"  # 测试通过
    FAIL = "FAIL"  # 测试失败
    ERROR = "ERROR"  # 测试异常
    PENDING = "PENDING"  # 测试未执行
    WARNING = "WARNING"  # 测试警告,废弃


@unique
class OrderStatus(Enum):
    """
    提币状态对象
    """
    INITIAL = 0  # initial default
    ACCEPTED = 1  # Order accepted
    MANUAL_SIGNED = 2  # Manual checked
    PROCESSING = 3  # Order processing
    BROADCAST_OPERATION = 9  # Broadcast operation
    BROADCAST_SUCCESS = 10  # Broadcast succeed
    BROADCAST_FAILED = 11  # Broadcast failed
    FIRST_CONFIRM_SUCCESS = 12  # Blockchain first confirmed
    FIRST_CONFIRM_FAILED = 13  # Blockchain confirm failed
    MULTI_CONFIRMED = 14  # Blockchain confirmed specified quantity
    BIZ_CONFIRMED = 15  # Biz callback succeed
    FAILED = 20  # Order failed


class MixIn(object):
    """
    实例字典对象
    """

    @property
    def dict(self):
        # depth = 2
        data1 = {}

        for attr, value in self.__dict__.items():
            if isinstance(value, (list, tuple, set)):
                data1[attr] = []
                for item in value:
                    if getattr(item, "dict", None):
                        data1[attr].append(item.dict)
                    else:
                        data1[attr].append(item)
            elif isinstance(value, dict):
                data1[attr] = {}
                for attr1, value1 in value.items():
                    if getattr(value1, "dict", None):
                        data1[attr][attr1] = value1.dict
                    else:
                        data1[attr][attr1] = value1
            elif getattr(value, "dict", None):
                data1[attr] = value.dict
            else:
                data1[attr] = value

        return data1


class TestBase(object):
    """
    测试基类对象
    """

    def __init__(self):
        self.start_time = datetime.now()  # 开始时间
        self.ended_time = datetime.now()  # 结束时间

    def start(self):
        self.start_time = datetime.now()

    def ended(self):
        self.ended_time = datetime.now()

    @property
    def usage(self):
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def cost(self):
        cost_time1 = (self.ended_time - self.start_time).total_seconds() * 1000.0
        cost_time2 = int(cost_time1)  # 测试用时(ms)

        return cost_time2


class TestResult(TestBase):
    """
    测试结果对象
    """

    def __init__(self):
        super(TestResult, self).__init__()
        self.status = ResultState.PENDING  # 测试结果
        self.detail = None  # 测试详情

    @property
    def is_pass(self):
        return self.status == ResultState.PASS

    @property
    def is_fail(self):
        return self.status == ResultState.FAIL

    @property
    def is_warning(self):
        return self.status == ResultState.WARNING

    @property
    def is_error(self):
        return self.status == ResultState.ERROR

    @property
    def is_pending(self):
        return self.status == ResultState.PENDING

    @property
    def dict(self):
        return {
            "status": self.status.value,
            "detail": self.detail,
            "start": str(self.start_time),
            "ended": str(self.ended_time),
            "cost": self.cost,
            }


class TestStep(MixIn):
    """
    测试步骤对象
    """

    def __init__(self, step, title, method, api, timeout, encryption, body, expectation):
        super(TestStep, self).__init__()

        self.step = step  # 测试步骤
        self.title = title  # 测试目的
        self.method = method  # 请求方式
        self.api = api  # 请求接口
        self.timeout = timeout  # 等待时间
        self.encryption = encryption  # 是否加密
        self.body = body  # 请求数据
        self.expectation = expectation  # 期望结果
        self.result = TestResult()  # 测试结果
        self.sleep = 10  # 休眠时间

    @property
    def ctx(self):
        content = "STEP{step}{title}".format(step=self.step, title=self.title)
        if self.timeout:
            content = "{content}(等待时间{timeout}s)".format(content=content, timeout=self.timeout)
        return content

    @property
    def err_message(self):
        message = ""
        if self.result.is_fail:
            message = "{}||{}".format(self.ctx, self.result.detail.get("exception", ""))

        return message

    @property
    def json(self):
        data1 = """测试步骤: {ctx}\n测试结果: {status}\n请求方式: {method}\n请求接口: {api}\n请求数据:\n{data}\n期望响应:\n{expectation}\n实际响应:\n{result}\n""".format(
                ctx=self.ctx,
                status=self.result.status.value,
                method=self.method,
                api=self.api,
                data=json.dumps(self.body, ensure_ascii=False, indent=8),
                expectation=json.dumps(self.expectation, ensure_ascii=False, indent=8),
                result=json.dumps(self.result.detail, ensure_ascii=False, indent=8),
                )

        return data1


class TestCase(MixIn):
    """
    测试用例对象
    """

    def __init__(self, title, timeout=300 * 1000, enable=True):
        super(TestCase, self).__init__()

        self.uuid = get_stringify_uuid()  # 用例识别码
        self.title = title  # 测试用例
        self.steps = []  # 测试步骤
        self.timeout = timeout  # 超时时间
        self.enable = enable  # 是否测试

    @property
    def cost(self):
        return reduce(add, map(lambda x: x.result.cost, self.steps), 0)

    @property
    def is_pass(self):
        return len(list(filter(lambda x: x.result.is_pass, self.steps))) == len(self.steps)

    @property
    def is_fail(self):
        return len(list(filter(lambda x: x.result.is_fail, self.steps))) > 0

    @property
    def is_pending(self):
        return len(list(filter(lambda x: x.result.is_pending, self.steps))) == len(self.steps)

    @property
    def err_message(self):
        message = ""
        message_list = list(map(lambda x: x.err_message, filter(lambda x: x.err_message, self.steps)))
        if message_list:
            message = "||".join(message_list)

        return message

    @property
    def json(self):
        sep = "\n------------------------------------------\n\n"

        data1 = {
            "title": "{}".format(self.title),
            "fullTitle": "{}".format(self.ctx),
            "timedOut": self.cost > self.timeout,
            "duration": self.cost,
            "state": "",
            "pass": self.is_pass,
            "fail": self.is_fail,
            "pending": self.is_pending,
            "code": "日志追踪: {}\n{}{}".format(self.uuid, sep, sep.join(list(map(lambda x: str(x.json), self.steps)))),
            "err": {"message": self.err_message, "estack": "", },
            "isRoot": False,
            "uuid": self.uuid,
            "isHook": False,
            "skipped": False,
            }

        return data1

    @property
    def ctx(self):
        return "{uuid}||testcase={testcase}".format(uuid=self.uuid, testcase=self.title)


class TestSuite(TestBase):
    """
    测试用例集对象
    """

    def __init__(self, title, testcases):
        super(TestSuite, self).__init__()
        self.uuid = get_stringify_uuid()  # 集合识别码
        self.title = title  # 测试集合名称
        self.testcases = testcases  # 测试用例列表

    @property
    def ctx(self):
        return "{}||title={}".format(self.uuid, self.title)

    @property
    def suites(self):
        return {
            "uuid": self.uuid,
            "title": self.title,
            "fullFile": self.title,
            "file": "",
            "beforeHooks": [],
            "afterHooks": [],
            "tests": list(map(lambda x: x.json, self.testcases)),
            "suites": [],
            "passes": list(map(lambda x: x.uuid, list(filter(lambda x: x.is_pass, self.testcases)))),
            "failures": list(map(lambda x: x.uuid, list(filter(lambda x: x.is_fail, self.testcases)))),
            "pending": list(map(lambda x: x.uuid, list(filter(lambda x: x.is_pending, self.testcases)))),
            "skipped": [],
            "duration": self.cost,
            "root": False,
            "rootEmpty": False,
            "_timeout": 30 * 1000
            }

    @property
    def json(self):
        return {
            "stats": {
                "suites": 1,
                "tests": self.tests,
                "passes": self.passes,
                "pending": self.pending,
                "failures": self.failures,
                "start": str(self.start_time),
                "end": str(self.ended_time),
                "duration": self.cost,
                "testsRegistered": self.tests,
                "passPercent": 100 * self.passes / self.tests if self.tests > 0 else 0,
                "pendingPercent": 100 * self.pending / self.tests if self.tests > 0 else 0,
                "other": 0,
                "hasOther": False,
                "skipped": 0,
                "hasSkipped": False,
                "passPercentClass": "success" if self.tests == self.passes else "danger",
                "pendingPercentClass": "success" if self.tests == self.passes else "danger",
                },
            "suites": self.suites,
            "copyrightYear": 2018
            }

    @property
    def tests(self):
        # 测试用例总数
        return len(self.testcases)

    @property
    def passes(self):
        # 测试通过总数
        result_list = list(filter(lambda x: x.is_pass, self.testcases))
        return len(result_list)

    @property
    def failures(self):
        # 测试失败总数
        result_list = list(filter(lambda x: x.is_fail, self.testcases))
        return len(result_list)

    @property
    def pending(self):
        # 测试未执行总数
        result_list = list(filter(lambda x: x.is_pending, self.testcases))
        return len(result_list)


class TestAssert(object):
    """
    测试断言对象
    """

    def __init__(self, expectation, response):
        if not isinstance(expectation, dict):
            raise InvalidParameter(expectation)

        self.expectation = expectation
        self.response = response.dict

    def default_assert(self, expectation, response):
        for key, val in expectation.items():
            if key in response:
                in_response = response.get(key, None)
                ex = MisMatched("不相等的||关键字={}||测试值={}||期望值={}".format(key, in_response, val))

                if isinstance(val, dict) and isinstance(in_response, dict):
                    self.default_assert(val, in_response)
                elif isinstance(val, list) and isinstance(in_response, list):
                    for index, item in enumerate(val):
                        self.default_assert(item, in_response[index])
                elif isinstance(val, str):
                    special_assert = SpecialAssert(in_response, val)
                    if special_assert.special_items():
                        if not special_assert.run_assert():
                            raise ex
                    else:
                        if val != in_response:
                            raise ex
                else:
                    raise ex
            else:
                raise NotFound("不存在的||关键字={}||测试值=无||期望值={}".format(key, val))

    @staticmethod
    def run_special_assert(testsuite):
        for testcase in testsuite.testcases:
            if testcase.is_pass:
                step1_amount = Decimal(testcase.steps[0].result.detail["data"]["balance"])
                step2_amount = Decimal(testcase.steps[1].body["amount"])
                step4_amount = Decimal(testcase.steps[3].result.detail["data"]["balance"])

                if step1_amount + step2_amount != step4_amount:
                    testcase.steps[3].result.status = ResultState.FAIL
                    msg = "初始金额={}||提币金额={}||最终金额={}".format(step1_amount, step2_amount, step4_amount)
                    testcase.steps[3].result.detail.update({"exception": msg})
                    logger.error(context=testsuite.ctx, testcase=testcase.ctx, ex=str(msg))

    def run_assert(self):
        self.default_assert(self.expectation, self.response)


class SpecialAssert(object):
    SPECIAL_ASSERT_TUPLE = ("gte",)

    def __init__(self, response, expectation):
        self.response1 = response
        self.response2 = response
        self.expectation1 = expectation
        self.expectation2 = expectation
        self.header = ""

    def run_assert(self):
        self.transfer(self.header)

        return getattr(self, self.header)()

    def special_items(self):
        special_flag = False
        for header in self.SPECIAL_ASSERT_TUPLE:
            if self.expectation1.startswith(header):
                special_flag = True
                self.header = header
                break

        return special_flag

    def transfer(self, item):
        self.expectation2 = Decimal(self.expectation2.split(item)[-1])
        self.response2 = Decimal(self.response2)

    def gte(self):
        if self.response2 >= self.expectation2:
            return True
        return False


class TestRunner(object):
    def __init__(self, testsuite, count=50):
        self.testsuite = testsuite
        self.count = count
        self.pool = Pool(count)

    def run_testsuite(self):
        logger.info(context=self.testsuite.ctx, message="测试集合开始{}=".format("+" * 20))
        self.testsuite.start()

        proc_data = [(self.testsuite, testcase) for testcase in self.testsuite.testcases]
        testcases = self.pool.starmap(func=TestRunner.run_testcase, iterable=proc_data)
        self.pool.close()
        self.pool.join()
        self.testsuite.testcases = testcases

        self.testsuite.ended()
        logger.info(context=self.testsuite.ctx, message="测试集合结束{}=".format("-" * 20))

    @staticmethod
    def run_testcase(testsuite, testcase):
        # 执行测试用例
        try:
            if testcase.enable:  # 测试用例启用时,执行测试
                for step in testcase.steps:
                    ctx = LoggerContext(logger, context=testsuite.ctx, testcase=testcase.ctx, teststep=step.ctx)
                    ctx.info(message="记录测试用例开始时间")
                    step.result.start()
                    while True:
                        try:
                            ctx.info(message="执行HTTP拿到测试数据")
                            response = HTTPRunner(step).run_api()
                            step.result.detail = response.dict

                            ctx.info(message="对比测试结果和期望值")
                            testassert = TestAssert(step.expectation, response)
                            testassert.run_assert()
                            step.result.status = ResultState.PASS

                            ctx.exit(message="记录测试用例结束时间")
                            step.result.ended()

                            break
                        except Exception as ex:
                            step.result.status = ResultState.FAIL
                            step.result.ended()

                            ex_data = {"exception": str(ex)}
                            if step.result.detail:  # 断言错误
                                step.result.detail.update(ex_data)
                            else:  # 网络错误
                                step.result.detail = ex_data

                            if step.result.usage < step.timeout:
                                ctx.info(**ex_data, traceback=get_traceback(), step=step.ctx, message="测试用例执行过程抛错,准备{sleep}s后重试".format(sleep=step.sleep))
                                step.result.detail = None
                                time.sleep(step.sleep)
                            else:
                                ctx.exit(**ex_data, traceback=get_traceback(), step=step.ctx, message="测试用例执行过程抛错")
                                raise ex
            # else: # 测试用例没有启用,不执行测试
            #     pass
        except Exception as ex:
            logger.error(context=testsuite.ctx, testcase=testcase.ctx, ex=str(ex))
        finally:
            logger.info(testcase=testcase.dict)
            return testcase
