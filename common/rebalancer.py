# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/24

import os
import json
from time import sleep
from decimal import Decimal
from multiprocessing import Pool

from conn.httpconn import HttpRequest
from common import factory
from common.util import get_traceback
from common.logger import (Logger, LoggerContext)
from common.errors import (InvalidParameter, HTTPError, UncaughtError)

logger = Logger.get_logger(__name__)


class Chain(object):
    (GET, POST) = ("get", "post")
    (IN, OUT) = ("IN", "OUT")
    METHODs = (GET, POST)
    TIMEOUT = 20  # 秒
    RETRIES = 3 * 100

    def __init__(self, currency):
        if isinstance(currency, dict) and len(currency):
            for key, val in currency.items():
                setattr(self, key, val)
        else:
            raise InvalidParameter(currency)

    @property
    def url(self):
        return self.domain

    @property
    def payload(self):
        return {}

    @property
    def dict(self):
        return {
            "url": self.url,
            "timeout": self.TIMEOUT,
            "json" if self.method == self.POST else "params": self.payload,
            }

    def mapping(self,
                transaction_balance_in,
                transaction_balance_ot,
                transaction_counter_in,
                transaction_counter_ot,
                chain_transactions,
                transaction_fee_ot,
                chain_balance_sum,
                transaction_balance_diff,
                transaction_abnormal,
                ):
        return {
            "交易币种": self.currency,  # 币种
            "交易地址": self.address,  # 地址
            "钱包类型": self.type,  # 地址类型
            "充币金额": "{:f}".format(transaction_balance_in / Decimal(str(self.precision))),  # 充币金额
            "提币金额": "{:f}".format(transaction_balance_ot / Decimal(str(self.precision))),  # 提币金额
            "充币次数": transaction_counter_in,  # 充币次数
            "提币次数": transaction_counter_ot,  # 提币次数
            "交易总数": len(chain_transactions),  # 总交易数
            "提币费用": "{:f}".format(transaction_fee_ot / Decimal(str(self.precision))),  # 提币费用
            "链上余额": "{:f}".format(chain_balance_sum),  # 链上余额
            "计算余额": "{:f}".format(transaction_balance_diff / Decimal(str(self.precision))),  # 计算余额
            "异常交易": transaction_abnormal,  # 异常交易
            "对账结果": True if transaction_balance_diff / Decimal(str(self.precision)) == chain_balance_sum else False,  # 账务是否平衡
            }

    def process(self):
        count = self.RETRIES
        response = None

        # TODO HTTPAdapter(max_retries=count)
        while count > 0:
            try:
                response = getattr(HttpRequest, self.method)(self)
                break
            except HTTPError as ex:
                logger.info(ex=ex, traceback=get_traceback())

                count -= 1
                if count == 0:
                    raise HTTPError("MaxRetries||{}".format(str(ex)))

                sleep(1)
            except Exception as ex:
                logger.info(ex=str(ex), traceback=get_traceback())
                raise UncaughtError(str(ex))

        return response


class Etherscan(Chain):
    def __init__(self, tx_hash, action):
        currency = {
            "method": "get",
            "domain": "http://api.etherscan.io/api",
            "currency": "ETH",
            "type": "READY",
            "tx_hash": tx_hash,
            "action": action,
            "page": 1,
            }
        super().__init__(currency)

    @property
    def payload(self):
        return {
            "module": "proxy",
            "action": self.action,
            "txhash": self.tx_hash,
            "apikey": "YourApiKeyToken"
            }


class ETH(object):
    def __init__(self, tx_hash):
        self.tx_hash = tx_hash
        self.currency = "ETH"
        self.source = "cb62e9cdff7c49709fa3e430a140e0f1"

    def get_eth_api(self, action):
        result = Etherscan(self.tx_hash, action).process()
        if isinstance(result, dict) and isinstance(result.get("result"), dict):
            result = result.get("result")
        else:
            result = None

        return result

    def get_eth_transaction(self):
        # 交易hash查询交易详情
        return self.get_eth_api("eth_getTransactionByHash")

    def get_transaction_receipt(self):
        # 交易hash查询交易凭证
        return self.get_eth_api("eth_getTransactionReceipt")

    @staticmethod
    def from_hex_to_string(hex_string):
        string1 = int(hex_string, 16)
        string2 = str(string1)
        return string2

    def mapping(self, item, item1):
        amount = "{:f}".format(Decimal(self.from_hex_to_string(item["value"])) / Decimal(1E18))
        fee = "{:f}".format(Decimal(self.from_hex_to_string(item1["gasUsed"])) * Decimal(self.from_hex_to_string(item["gasPrice"])) / Decimal(1E18))
        mapping_data1 = {
            "type": "READY",
            "mode": "BALANCE",
            "vin": [{
                "tx_hash": item["hash"],
                "currency_name": self.currency,
                "in_address": item["from"],
                "mode": "BALANCE",
                "amount": amount,
                "fee": fee,
                }],
            "vot": [{
                "tx_hash": item["hash"],
                "currency_name": self.currency,
                "out_address": item["to"],
                "in_address": item["from"],
                "amount": amount,
                "fee": fee,
                "source": self.source,
                }]
            }

        return mapping_data1

    @property
    def data(self):
        response1 = self.get_eth_transaction()
        response2 = self.get_transaction_receipt()
        response_result_list = []
        if isinstance(response1, dict) and response1.get("hash") == self.tx_hash and isinstance(response2, dict) and response2.get("gasUsed"):
            response_result_list.append(self.mapping(response1, response2))

        return response_result_list

    @staticmethod
    def factory(tx_hash):
        ctx = LoggerContext(logger, tx_hash=tx_hash)

        data = []
        try:
            data = ETH(tx_hash).data
        except Exception as ex:
            logger.error(message="UncaughtError()", ex=str(ex), traceback=get_traceback())
        finally:
            ctx.exit(chain_data=data, length=len(data))

        return data


class Airflow(object):
    COUNT = 50

    @staticmethod
    def save_json(filename, data):
        with open(filename, "w", encoding='utf-8') as f:
            f.write("{}".format(json.dumps(data, indent=4, ensure_ascii=False)))

    @staticmethod
    def pool_process(func, count, proc):
        result = []
        try:
            pool = Pool(count)
            result = pool.starmap(func=func, iterable=proc)
            pool.close()
            pool.join()
        except Exception as ex:
            logger.error(message="UncaughtError()", ex=str(ex), traceback=get_traceback())

        return result
