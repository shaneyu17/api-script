# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/6/19


from datetime import datetime


class MyException(Exception):
    """
    各种错误码,以及API标准响应数据template
    """
    SUB_CODE_ONE = "0001"
    SUB_CODE_TWO = "0002"
    SUB_CODE_THR = "0003"
    SUB_CODE_FOR = "0004"
    SUB_CODE_FIV = "0005"
    SUB_CODE_SIX = "0006"
    SUB_CODE_SEN = "0007"
    SUB_CODE_EHT = "0008"
    SUB_CODE_NIE = "0009"
    SUB_CODE_TEN = "0010"

    ERROR_COMMON_SUCCESS = "1000"  # 通用成功
    ERROR_COMMON_SUCCESS_SUB_CODE_ONE = SUB_CODE_ONE  # 通用成功

    ERROR_COMMON_FAILURE = "2000"  # 通用失败
    ERROR_COMMON_INVALID_PARAMETER = SUB_CODE_ONE  # 无效的参数
    ERROR_COMMON_ITEM_NOT_FOUND = SUB_CODE_TWO  # 条目未找到
    ERROR_COMMON_MYSQL_EXCEPTION = SUB_CODE_THR  # MySQL异常
    ERROR_COMMON_NOTSUFFICIENTCASH = SUB_CODE_FOR  # 现金不足
    ERROR_COMMON_TOOMANYREQUESTS = SUB_CODE_FIV  # 请求过多
    ERROR_COMMON_UNCAUGHT_EXCEPTION = SUB_CODE_TEN  # 未捕获异常

    ERROR_HTTP_NETWORK_FAILURE = "3000"  # Http通用错误
    ERROR_HTTP_NETWORK_TIMEOUT = SUB_CODE_ONE  # 网络超时
    ERROR_HTTP_UNCAUGHT_EXCEPTION = SUB_CODE_TEN  # 未捕获异常

    ERROR_RPC_NETWORK_FAILURE = "4000"  # Rpc通用错误
    ERROR_RPC_NETWORK_TIMEOUT = SUB_CODE_ONE  # 网络超时
    ERROR_RPC_UNCAUGHT_EXCEPTION = SUB_CODE_TEN  # 未捕获异常

    def __init__(self, code, sub_code, msg, console=True):
        super().__init__()
        self.code = code  # 错误码
        self.sub_code = sub_code  # 错误子码
        self.msg = msg  # 错误详细信息
        self.console = console  # 是否数据日志

    def get_return_data(self, data=None):
        """
        API响应数据结构
        """
        content = {
            "code": self.code,
            "data": {} if not data else data,
            "msg": self.msg,
            "sub_code": self.sub_code,
            "success": self.code == self.ERROR_COMMON_SUCCESS
            }

        return content

    @staticmethod
    def is_success(response):
        """
        判断是否是标准成功响应,主要用于回调front API响应的结果的判断
        """
        success_flag = False
        if response and isinstance(response, dict) and response.get("code") == MyException.ERROR_COMMON_SUCCESS:
            success_flag = True

        return success_flag

    def __str__(self):
        return "{}".format(self.msg)

    __repr__ = __str__


class InvalidParameter(MyException):
    """
    无效的参数
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_COMMON_FAILURE, self.ERROR_COMMON_INVALID_PARAMETER, msg)
        self.msg = "InvalidParameter()||detail={}".format(msg)


class NotFound(MyException):
    """
    条目不存在
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_COMMON_FAILURE, self.ERROR_COMMON_ITEM_NOT_FOUND, msg)
        self.msg = "ItemNotFound()||detail={}".format(msg)


class MisMatched(MyException):
    """
    不匹配的
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_COMMON_FAILURE, self.ERROR_COMMON_ITEM_NOT_FOUND, msg)
        self.msg = "MisMatched()||detail={}".format(msg)


class NotSufficientCash(MyException):
    """
    现金不足
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_COMMON_FAILURE, self.ERROR_COMMON_NOTSUFFICIENTCASH, msg)
        self.msg = "NotSufficientCash()||detail={}".format(msg)


class MySQLError(MyException):
    """
    数据库错误
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_COMMON_FAILURE, self.ERROR_COMMON_MYSQL_EXCEPTION, msg)
        self.msg = "MySQLError()||detail={}".format(msg)


class HTTPError(MyException):
    """
    HTTP错误
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_HTTP_NETWORK_FAILURE, self.ERROR_HTTP_UNCAUGHT_EXCEPTION, msg)
        self.msg = "HTTPError()||detail={}".format(msg)


class RPCError(MyException):
    """
    RPC错误
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_RPC_NETWORK_FAILURE, self.ERROR_RPC_UNCAUGHT_EXCEPTION, msg)
        self.msg = "RPCError()||detail={}".format(msg)


class UncaughtError(MyException):
    """
    未捕获错误
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_COMMON_FAILURE, self.ERROR_COMMON_UNCAUGHT_EXCEPTION, msg)
        self.msg = "UncaughtError()||detail={}".format(msg)


class APILimiter(MyException):
    """
    API限流错误
    """

    def __init__(self, msg):
        super().__init__(self.ERROR_COMMON_FAILURE, self.ERROR_COMMON_TOOMANYREQUESTS, msg)
        self.msg = "TooManyRequests(429)||detail=ratelimit exceeded={}".format(msg)


class Success(MyException):
    """
    成功结果
    """

    def __init__(self, msg="SUCCESS"):
        super().__init__(self.ERROR_COMMON_SUCCESS, self.ERROR_COMMON_SUCCESS_SUB_CODE_ONE, msg)
        self.msg = "{}".format(msg)


class Monitor(Exception):
    TEMPLATE = "Monitor,{monitor_name},{monitor_type},{monitor_time},{monitor_logs},ex={monitor_msgs}"

    def __init__(self, monitor_type=None):
        self.monitor_name = "NEO"
        self.monitor_logs = "TEXT"
        self.monitor_type = monitor_type

    def record(self, msg=None):
        # 生成一条监控日志
        record1 = {
            "monitor_name": self.monitor_name,
            "monitor_type": self.monitor_type,
            "monitor_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "monitor_logs": self.monitor_logs,
            "monitor_msgs": msg,
            }

        return Monitor.TEMPLATE.format(**record1)

    @classmethod
    def data(cls, msg):
        # 子类拿一监控日志
        return cls().record(msg)

    def __str__(self):
        return self.record

    __repr__ = __str__


class SyncMonitor(Monitor):
    def __init__(self):
        super().__init__("WATCH_ONLY_SYNC_BLCOK_UNCAUGHT_EXCEPTION")
