# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/10


import os
import sys
import uuid
import base64
import random
import binascii
import urllib.parse
import traceback
from datetime import datetime

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA

from config.config import Config


class CustomerCryptoBase(object):
    ENCRYPTION_BODY_KEY = Config.encryption_body_key
    SIG_HED_PRIVATE_KEY = Config.sig_hed_private_key

    @staticmethod
    def cbc_padding(data):
        """
        填充加密数据到指定长度
        """
        BS = AES.block_size
        RE = len(data) % BS
        return data + (BS - RE) * chr(BS - RE).encode()

    @staticmethod
    def cbc_unpadding(data):
        """
        从填充的数据中移除填充数据
        """
        return data[0:-data[-1]]

    @staticmethod
    def b64encode(data):
        """
        base64编码数据
        """
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            raise Exception("data encrypt input type={}".format(data))
        data2 = base64.b64encode(data)
        return data2

    @staticmethod
    def b64decode(data):
        """
        base64解码数据
        """
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            raise Exception("data decrypt input type={}".format(data))
        data2 = base64.b64decode(data)
        return data2

    @staticmethod
    def urlencode(data):
        data1 = urllib.parse.quote(data)
        return data1

    @staticmethod
    def urldecode(data):
        data1 = urllib.parse.unquote(data)
        return data1


class CustomerAES(CustomerCryptoBase):
    """
    加解密数据转换
    """

    def __init__(self, data):
        super(CustomerAES, self).__init__()
        self.key = self.ENCRYPTION_BODY_KEY.encode()
        self.ciper = AES.new(self.key, AES.MODE_ECB)
        self.raw = data

    def encrypt(self):
        """
        加密账户私钥(str,bytes,bytearray=>str)
        """
        data = self.raw
        if isinstance(data, str):
            data = data.encode()  # bytes
        elif isinstance(data, bytearray):
            data = binascii.hexlify(bytes(data))  # 原来实现是转成hex再加密的
        elif not isinstance(data, bytes):
            raise Exception("data encrypt input type={}".format(data))

        data2 = self.cbc_padding(data)
        data3 = self.ciper.encrypt(data2)
        data4 = self.b64encode(data3)

        return data4.decode()

    def decrypt(self):
        """
        解密账户私钥(str=>bytes)
        """
        data = self.raw
        data2 = self.b64decode(data)

        if len(data2) < 1:
            return data2

        data3 = self.ciper.decrypt(data2)
        data4 = self.cbc_unpadding(data3)
        data5 = data4.decode()

        return data5


class CustomerSIG(CustomerCryptoBase):
    def __init__(self):
        super(CustomerSIG, self).__init__()
        private_key1 = self.SIG_HED_PRIVATE_KEY
        private_key2 = self.b64decode(private_key1)

        self.private_key = RSA.importKey(private_key2)
        self.public_key = self.private_key.publickey()

    def sign(self, data):
        """
        签名数据返回base64编码后的数据
        """

        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            raise Exception("data sign input type={}".format(data))

        signer = PKCS1_v1_5.new(self.private_key)
        digest = SHA256.new()
        digest.update(data)
        data2 = signer.sign(digest)
        data3 = self.b64encode(data2)

        return data3.decode()

    def sign_to_urlencode(self, data):
        data1 = self.sign(data)
        data2 = self.urlencode(data1)

        return data2

    def verify(self, data, sig):
        """
        验证签名是否正确,返回boolean
        """

        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            raise Exception("data digest input type={}".format(data))

        if isinstance(sig, str):
            sig = sig.encode()
        elif not isinstance(sig, bytes):
            raise Exception("sig sig input type={}".format(data))

        sig1 = self.b64decode(sig)
        verifier = PKCS1_v1_5.new(self.public_key)
        digest = SHA256.new()
        digest.update(data)

        verified = verifier.verify(digest, sig1)

        return bool(verified)


class CustomerUtil(object):
    @staticmethod
    def gen_order_no(varchar=32):
        data1 = Config.api_order_no_prefix
        data2 = str(int(datetime.now().timestamp() * 1E6))
        data3 = "".join(random.sample(data2, varchar - len(data1) - len(data2)))

        data4 = "{data1}{data2}{data3}".format(data1=data1, data2=data2, data3=data3)

        return data4

    @staticmethod
    def get_file_dirpath(file_path):
        file_dirpath1 = os.path.dirname(file_path)
        file_dirpath2 = CustomerUtil.get_file_abspath(file_dirpath1)

        return file_dirpath2

    @staticmethod
    def get_file_abspath(file_path):
        file_abspath = os.path.abspath(file_path)

        return file_abspath

    @staticmethod
    def get_file_joinpath(base_path, file_path):
        file_joinpath1 = os.path.join(base_path, file_path)
        file_joinpath2 = CustomerUtil.get_file_abspath(file_joinpath1)

        return file_joinpath2

    @staticmethod
    def get_file_basename(file_path):
        file_basename1 = os.path.basename(file_path)
        file_basename2 = os.path.splitext(file_basename1)[0]

        return file_basename2

    @staticmethod
    def get_report_path(base_path, file_path):
        report_path1 = CustomerUtil.get_file_basename(file_path)
        dt = datetime.now()
        dt_str = "%04d-%02d-%02d_%02d-%02d-%02d.%03d" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond / 1000)

        report_path2 = "{}{}-{}.html".format(Config.api_test_report_path, report_path1, dt_str)
        report_path3 = CustomerUtil.get_file_joinpath(base_path, report_path2)

        return report_path3

    @staticmethod
    def get_reconciliation_path(base_path, file_path):
        base_path1 = CustomerUtil.get_file_dirpath(base_path)
        dt = datetime.now()
        dt_str = "%04d-%02d-%02d_%02d-%02d-%02d.%03d" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond / 1000)

        report_path2 = "{}{}-{}.json".format(Config.api_test_report_path, file_path, dt_str)
        report_path3 = CustomerUtil.get_file_joinpath(base_path1, report_path2)

        return report_path3

    @staticmethod
    def is_file_exists(file_path):
        flag = os.path.exists(file_path)

        return flag


class Parameter(object):
    """
    请求过程中需要的参数对象
    """

    def __init__(self, reqid=None):
        self.reqid = get_stringify_uuid() if not reqid else reqid
        self.start_time = datetime.now()
        self.end_time = datetime.now()

    @property
    def cost(self):
        # 请求花费的毫秒
        self.end_time = datetime.now()
        cost_time = (self.end_time - self.start_time).total_seconds() * 1000
        return cost_time


def get_traceback():
    """
    获取指定深度的异常堆栈的格式化信息
    :return: 堆栈字符串
    """
    ex_type, ex_value, ex_traceback = sys.exc_info()
    ex_list = traceback.format_exception(etype=ex_type, value=ex_value, tb=ex_traceback)
    lines = []
    for ex_info in ex_list:
        info_list = ex_info.split("\n")
        for info in info_list:
            data = info.strip()
            if len(data) > 0:
                lines.append(data)
            # end if
        # end for
    # end for
    return "=>".join(lines)


def get_stringify_uuid():
    """
    获取uuid字符串
    """
    return uuid.uuid4().hex
