# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/11


import json

from common.util import (CustomerAES, CustomerSIG)
from common.errors import (Success, InvalidParameter)
from conn.httpconn import (HttpRequest)
from config.config import Config


class CustomerRequest(object):
    """
    HTTP请求对象
    """

    def __init__(self, url, body, sign=None, timeout=10):
        self.url = url
        if isinstance(body, dict):
            self.json = body
        else:
            self.data = body
        self.headers = {Config.bypass_front_appid_headers: Config.bypass_front_appid_content, }
        self.timeout = timeout

        if sign:
            self.headers.update({Config.bypass_front_signs_headers: sign, })

    @property
    def dict(self):
        return self.__dict__


class CustomerResponse(object):
    """
    HTTP响应对象
    """

    def __init__(self, body):
        if not isinstance(body, dict):
            raise InvalidParameter(str(body))
        for key, val in body.items():
            setattr(self, key, val)

    @property
    def dict(self):
        return self.__dict__


class HTTPRunner(object):
    """
    发起HTTP请求并拿到结果
    """

    def __init__(self, teststep):
        self.teststep = teststep

    def req_need_encryption(self):
        # 请求数据加密||签名
        _request_body = self.teststep.body
        _request_sign = None

        if self.teststep.encryption:
            _request_body = json.dumps(_request_body) if isinstance(_request_body, dict) else _request_body
            _request_body = CustomerAES(_request_body).encrypt()
            _request_sign = CustomerSIG().sign_to_urlencode(_request_body)

        return _request_body, _request_sign

    def res_need_decryption(self, response):
        # 响应数据解密||不验证签名
        if self.teststep.encryption and response.code == Success.ERROR_COMMON_SUCCESS:
            response.data = json.loads(CustomerAES(response.data).decrypt())

        return response

    def run_api(self):
        # 执行http请求
        if self.teststep.method == "POST":
            _request_api = self.teststep.api
            _request_body, _request_sign = self.req_need_encryption()

            request = CustomerRequest(_request_api, _request_body, _request_sign)
            result = HttpRequest.post(request)
            response = CustomerResponse(result)
            self.res_need_decryption(response)

            return response
        else:
            # TODO 有新的需求再实现吧
            raise InvalidParameter(self.teststep.method)
