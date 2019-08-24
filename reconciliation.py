# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/9


import json
from decimal import Decimal

from common.errors import InvalidParameter
from common.rebalancer import (Chain, Airflow)
from common.logger import Logger, LoggerContext
from common.util import (get_traceback, CustomerUtil)

logger = Logger.get_logger(__name__)


class XRP(Chain):
    class Balance(Chain):
        def __init__(self, currency):
            super().__init__(currency)

        @property
        def url(self):
            url1 = self.domain_cash_balance.format(address=self.address)

            return url1

        @property
        def payload(self):
            payload1 = {}

            return payload1

        @property
        def data(self):
            response = self.process()
            if isinstance(response, dict) and response.get("result") == "success" and isinstance(response.get("balances"), list):
                currency_balances = filter(lambda x: x.get("currency") == self.currency, response.get("balances"))
                balances = Decimal(0)
                for item in currency_balances:
                    balances += Decimal(str(item.get("value", "0")))

                return balances
            else:
                raise InvalidParameter(response)

    class Transaction(Chain):
        def __init__(self, currency):
            super().__init__(currency)

        @property
        def url(self):
            url1 = self.domain_transactions.format(address=self.address)

            return url1

        @property
        def payload(self):
            payload1 = {"limit": self.limit, "type": "Payment", }
            if self.marker:
                payload1.update({"marker": self.marker})

            return payload1

        @property
        def data(self):
            result = []

            while True:
                response = self.process()
                if isinstance(response, dict) and response.get("result") == "success" and isinstance(response.get("transactions"), list):
                    result.extend(response.get("transactions"))
                    if response.get("marker"):
                        self.marker = response.get("marker")
                    else:
                        break
                else:
                    raise InvalidParameter(response)

            return result

    def __init__(self, currency):
        super().__init__(currency)

        self.balance = self.Balance(currency)
        self.transactions = self.Transaction(currency)

    @property
    def data(self):
        chain_balance_sum = self.balance.data  # 链上实际余额
        chain_transactions = self.transactions.data  # 链上交易信息

        transaction_balance_in = 0  # 交易充币金额
        transaction_counter_in = 0  # 交易充币次数

        transaction_balance_ot = 0  # 交易提币金额
        transaction_counter_ot = 0  # 交易提币次数
        transaction_fee_ot = 0  # 交易提币费用

        transaction_abnormal = []  # 异常交易信息

        for transaction in chain_transactions:
            if isinstance(transaction, dict) and isinstance(transaction.get("tx"), dict) and isinstance(transaction.get("meta"), dict):
                tx = transaction.get("tx")
                meta = transaction.get("meta")
                deposit = tx.get("Destination") == self.address
                withdraw = tx.get("Account") == self.address
                fee = tx.get("Fee")
                transaction_result = meta.get("TransactionResult") == "tesSUCCESS"
                delivered_amount = meta.get("delivered_amount")

                if transaction_result:
                    if deposit:
                        transaction_balance_in += Decimal(delivered_amount)
                        transaction_counter_in += 1
                    elif withdraw:
                        transaction_balance_ot += Decimal(delivered_amount)
                        transaction_counter_ot += 1
                        transaction_fee_ot += Decimal(fee)
                    else:
                        raise InvalidParameter(transaction)
                else:
                    if withdraw:
                        transaction_fee_ot += Decimal(fee)
                        transaction_counter_ot += 1

                    transaction_abnormal.append(transaction)
            else:
                raise InvalidParameter(transaction)

        transaction_balance_diff = transaction_balance_in - transaction_balance_ot - transaction_fee_ot  # 交易计算余额

        return self.mapping(transaction_balance_in,
                            transaction_balance_ot,
                            transaction_counter_in,
                            transaction_counter_ot,
                            chain_transactions,
                            transaction_fee_ot,
                            chain_balance_sum,
                            transaction_balance_diff,
                            transaction_abnormal,
                            )


class NEO(Chain):
    class Balance(Chain):
        def __init__(self, currency):
            super().__init__(currency)

        @property
        def url(self):
            url1 = self.domain_cash_balance.format(address=self.address)

            return url1

        @property
        def payload(self):
            payload1 = {}

            return payload1

        @property
        def data(self):
            response = self.process()
            if isinstance(response, dict) and response.get("address") == self.address and isinstance(response.get("balance"), list):
                currency_balances = filter(lambda x: x.get("asset") == self.currency, response.get("balance"))
                balances = Decimal(0)
                for item in currency_balances:
                    balances += Decimal(str(item.get("amount", "0")))

                return balances
            else:
                raise InvalidParameter(response)

    class Transaction(Chain):
        def __init__(self, currency):
            super().__init__(currency)

        @property
        def url(self):
            url1 = self.domain_transactions.format(address=self.address, page=self.page)

            return url1

        @property
        def payload(self):
            payload1 = {}

            return payload1

        @property
        def data(self):
            result = []

            while True:
                response = self.process()
                if isinstance(response, dict) and isinstance(response.get("entries"), list):
                    result.extend(response.get("entries"))
                    if len(response.get("entries")) > 0:
                        self.page += 1
                    else:
                        break
                else:
                    raise InvalidParameter(response)

            return result

    def __init__(self, currency):
        super().__init__(currency)

        self.balance = self.Balance(currency)
        self.transactions = self.Transaction(currency)

    @property
    def data(self):
        chain_balance_sum = self.balance.data  # 链上实际余额
        chain_transactions = self.transactions.data  # 链上交易信息

        transaction_balance_in = 0  # 交易充币金额
        transaction_counter_in = 0  # 交易充币次数

        transaction_balance_ot = 0  # 交易提币金额
        transaction_counter_ot = 0  # 交易提币次数
        transaction_fee_ot = 0  # 交易提币费用

        transaction_abnormal = []  # 异常交易信息

        for transaction in chain_transactions:
            if isinstance(transaction, dict) and transaction.get("asset") == self.assetid:
                deposit = transaction.get("address_to") == self.address
                withdraw = transaction.get("address_from") == self.address
                delivered_amount = transaction.get("amount")

                if deposit:
                    transaction_balance_in += Decimal(delivered_amount)
                    transaction_counter_in += 1
                elif withdraw:
                    transaction_balance_ot += Decimal(delivered_amount)
                    transaction_counter_ot += 1
                else:
                    raise InvalidParameter(transaction)
            else:
                transaction_abnormal.append(transaction)

        transaction_balance_diff = transaction_balance_in - transaction_balance_ot - transaction_fee_ot  # 交易计算余额

        return self.mapping(transaction_balance_in,
                            transaction_balance_ot,
                            transaction_counter_in,
                            transaction_counter_ot,
                            chain_transactions,
                            transaction_fee_ot,
                            chain_balance_sum,
                            transaction_balance_diff,
                            transaction_abnormal,
                            )


class Executor(Airflow):

    @staticmethod
    def exe_chain(currency_list):
        # 各币种链上数据交易
        native = Executor.exe_native(currency_list)

        data = native
        file_path = CustomerUtil.get_reconciliation_path(__file__, "reconciliation")
        Executor.save_json(file_path, data)

    @staticmethod
    def exe_native(currency_list):
        proc = [(currency,) for currency in currency_list if currency["currency"] != "LTC"]
        result = Executor.pool_process(Executor.process, Executor.COUNT, proc)

        data = result
        logger.info(native_transaction=json.dumps(data, ensure_ascii=False), length=len(data))

        return data

    @staticmethod
    def process(currency):
        ctx = LoggerContext(logger, currency=currency["currency"], address=currency["address"], type=currency["type"])
        mappings = {
            "NEO": NEO,
            "XRP": XRP,
            }
        data = []
        try:
            func = mappings.get(currency.get("currency"))
            data = func(currency).data if func else []
        except Exception as ex:
            logger.error(message="UncaughtError()", ex=str(ex), traceback=get_traceback())
        finally:
            ctx.exit(chain_data=data, length=len(data))

        return data


def main():
    # 待测试钱包地址
    currency_list = [
        {
            "method": "get",
            "domain_transactions": "https://data.ripple.com/v2/accounts/{address}/transactions",
            "domain_cash_balance": "https://data.ripple.com/v2/accounts/{address}/balances",
            "currency": "XRP",
            "address": "r33A7DdKzxenN7dNowJhXDhpr5y5H8CnBT",
            "type": "FUNDS",
            "limit": 999,
            "marker": "",
            "page": 1,
            "precision": 1E6,
            },
        {
            "method": "get",
            "domain_transactions": "https://data.ripple.com/v2/accounts/{address}/transactions",
            "domain_cash_balance": "https://data.ripple.com/v2/accounts/{address}/balances",
            "currency": "XRP",
            "address": "r9f6dJXMKynXz6gR4FPAgJcDMrmgwmkqZJ",
            "type": "READY",
            "limit": 999,
            "marker": "",
            "page": 1,
            "precision": 1E6,
            },
        {
            "method": "get",
            "domain_transactions": "https://data.ripple.com/v2/accounts/{address}/transactions",
            "domain_cash_balance": "https://data.ripple.com/v2/accounts/{address}/balances",
            "currency": "XRP",
            "address": "rPYMpi5SFDgH5e9LYd2Zw5D5MkSTzc48aU",
            "type": "FUNDS",
            "limit": 999,
            "marker": "",
            "page": 1,
            "precision": 1E6,
            },
        {
            "method": "get",
            "domain_transactions": "https://data.ripple.com/v2/accounts/{address}/transactions",
            "domain_cash_balance": "https://data.ripple.com/v2/accounts/{address}/balances",
            "currency": "XRP",
            "address": "rLWFaRSTuYHYkhNJJkj27ubtW6iA2SGYzP",
            "type": "READY",
            "limit": 999,
            "marker": "",
            "page": 1,
            "precision": 1E6,
            },
        {
            "method": "get",
            "domain_transactions": "https://data.ripple.com/v2/accounts/{address}/transactions",
            "domain_cash_balance": "https://data.ripple.com/v2/accounts/{address}/balances",
            "currency": "XRP",
            "address": "rLSAMJZMyMioMxbxg2YYvEyxZe1kD9iRyN",
            "type": "FUNDS",
            "limit": 999,
            "marker": "",
            "page": 1,
            "precision": 1E6,
            },
        {
            "method": "get",
            "domain_transactions": "https://data.ripple.com/v2/accounts/{address}/transactions",
            "domain_cash_balance": "https://data.ripple.com/v2/accounts/{address}/balances",
            "currency": "XRP",
            "address": "rLMW9fLtje3LojJwMpgpms7Nb3q1SuqitB",
            "type": "READY",
            "limit": 999,
            "marker": "",
            "page": 1,
            "precision": 1E6,
            },
        {
            "method": "get",
            "domain_transactions": "https://api.neoscan.io/api/main_net/v1/get_address_abstracts/{address}/{page}",
            "domain_cash_balance": "https://api.neoscan.io/api/main_net/v1/get_balance/{address}",
            "currency": "NEO",
            "assetid": "c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
            "address": "ANgA8bHVmvm6vvQJS24Fn9s5xegzzMviZp",
            "type": "READY",
            "page": 1,
            "precision": 1E0,
            },
        {
            "method": "get",
            "domain_transactions": "https://api.neoscan.io/api/main_net/v1/get_address_abstracts/{address}/{page}",
            "domain_cash_balance": "https://api.neoscan.io/api/main_net/v1/get_balance/{address}",
            "currency": "NEO",
            "assetid": "c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
            "address": "AaKZaN3RiLHiBueS1wtCM7nwyKoXhqU7KN",
            "type": "READY",
            "page": 1,
            "precision": 1E0,
            },
        {
            "method": "get",
            "domain_transactions": "https://api.neoscan.io/api/main_net/v1/get_address_abstracts/{address}/{page}",
            "domain_cash_balance": "https://api.neoscan.io/api/main_net/v1/get_balance/{address}",
            "currency": "NEO",
            "assetid": "c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
            "address": "AeQySRFFgYEj6TSGkLsP4YiKqsSKd6qLRz",
            "type": "READY",
            "page": 1,
            "precision": 1E0,
            },
        {
            "method": "get",
            "domain_transactions": "https://api.neoscan.io/api/main_net/v1/get_address_abstracts/{address}/{page}",
            "domain_cash_balance": "https://api.neoscan.io/api/main_net/v1/get_balance/{address}",
            "currency": "NEO",
            "assetid": "c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
            "address": "APnrHkHP7MSe6ixUpErhc3L6rjrrnjQJHB",
            "type": "READY",
            "page": 1,
            "precision": 1E0,
            },
        ]

    # 原生链上的数据交易
    # grep "native_transaction" access.log | grep -o "length.*"
    Executor.exe_chain(currency_list)

    # 错误日志
    # grep "UncaughtError" access.log | grep -o "ex.*traceback"


if __name__ == "__main__":
    main()
