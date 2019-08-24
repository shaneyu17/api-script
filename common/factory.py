# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/6/18


import os
import sys

from config.config import Config
from common.logger import Logger

__app = None  # api客户端,singleton
__rpc = None  # rpc客户端,singleton
__block = None  # block客户端,singleton
__limiter = None  # 限流器,singleton

app_name = None


def __get_app_name(arguments):
    """
    初始化app_name
    """
    global app_name
    if len(arguments) >= 2 and "gunicorn" in arguments[0]:
        for arg in arguments[1:]:
            if arg.endswith(":app"):
                app_name = arg[0:-4]
            # endif
        # endfor
    elif len(arguments) >= 1:
        app_name = os.path.splitext(os.path.basename(arguments[0]))[0]
    # endif
    if app_name is None:
        print("No argument???, can not identify what the program is!")
        print("EXIT NOW!!!")
        exit()


def __get_app_logger():
    """
    初始化Logger
    """
    global app_name
    if Config.log_dir.startswith("/"):
        log_dir = os.path.join(Config.log_dir, app_name)
    else:
        fdir = os.path.dirname(__file__)
        log_dir = os.path.abspath(os.path.join(fdir, Config.log_dir, app_name))
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    # 默认输出到stderr,resetup让日志输出到文件并按照相应规则进行切割
    Config.log_level = getattr(Logger, Config.log_level, Logger.INFO)
    Logger.setup(access_log_file=os.path.join(log_dir, "access.log"),
                 access_log_level=Config.log_level,
                 error_log_file=os.path.join(log_dir, "errors.log"),
                 ledger_log_file=os.path.join(log_dir, "ledger.log"),
                 transaction_log_file=os.path.join(log_dir, "transaction.log"),
                 when=Config.log_when,
                 backup_count=Config.log_backup_count,
                 enable_console=Config.enable_console)

    # 调整application应用日志
    Logger.application_handler()

    # 初始化日志打印输出信息
    logger = Logger.get_logger(__name__)
    logger.info(message="INFO FROM GET APP LOGGER")
    logger.error(message="ERRS FROM GET APP LOGGER")


# 初始化日志名称||初始化日志路径||初始化rpc到全节点的连接
__get_app_name(sys.argv)
__get_app_logger()
