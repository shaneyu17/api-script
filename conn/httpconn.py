# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/6/20


import json

import requests

from common.errors import HTTPError
from common.logger import Logger
from common.util import (Parameter, get_traceback)

logger = Logger.get_logger(__name__)


class CustomerMessage(object):
    def __init__(self, message):
        self.message = message
        self.parameter = Parameter()

    def get_request_content(self, req_data):
        """
        一个http请求开始
        """
        return {
            "request_": json.dumps(req_data),
            "message": "{} begin...".format(self.message)
            }

    def get_response_content(self, res_data):
        """
        一个http请求结束
        """
        return {
            "response": json.dumps(res_data),
            "costtime": "{:.1f}ms".format(self.parameter.cost),
            "message": "{} end.".format(self.message)
            }


class HttpRequest(object):
    """
    目前主要是执行front API回调
    """

    @staticmethod
    def post(request):
        try:
            # 1)构建请求数据
            request_data = request.dict

            # 2)请求发出日志
            ctx = CustomerMessage("A http request{}")
            logger.info(**ctx.get_request_content(request_data))

            response_data = requests.post(**request_data)
            response_data.raise_for_status()
            result_data = response_data.json()

            # 3)请求接收日志
            logger.info(**ctx.get_response_content(result_data), headers=response_data.headers)

            # 4)返回响应数据
            return result_data
        except Exception as ex:
            logger.error(request=request, ex=str(ex), traceback=get_traceback())
            raise HTTPError("HttpRequest.post(request={})")

    @staticmethod
    def get(request):
        try:
            # 1)构建请求数据
            request_data = request.dict

            # 2)请求发出日志
            ctx = CustomerMessage("A http request{}")
            logger.info(**ctx.get_request_content(request_data))

            response_data = requests.get(**request_data)
            response_data.raise_for_status()
            result_data = response_data.json()

            # 3)请求接收日志
            logger.info(**ctx.get_response_content(result_data), headers=response_data.headers)

            # 4)返回响应数据
            return result_data
        except Exception as ex:
            logger.error(request=request, ex=str(ex), traceback=get_traceback())
            raise HTTPError("HttpRequest.get(request={})")


def main():
    request = HttpRequest()
    request.dict = {
        "url": "http://10.200.173.57:6090/watchonly/balance",
        "json":
            {
                "currencyName": "XRP",
                "addressList": ["rH999SoukX1MnJKzVrQSNMPpeuazwPrrkc"],
                "token": False
                },
        "headers":
            {
                "appId": "299ed7bf6e774eebb3e162b589aa91ad"
                },
        "timeout": 10,
        }
    request.post(request)


if __name__ == "__main__":
    main()
