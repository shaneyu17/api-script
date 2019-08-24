# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/6/18

import os
import sys
from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

from common.util import get_traceback


class FileLock:
    def __init__(self, filename):
        self.filename = "{filename}.lock".format(filename=filename)
        self.fp = None

    def __enter__(self):
        self.fp = open(self.filename, "ab")
        os.lockf(self.fp.fileno(), os.F_LOCK, 0)

    def __exit__(self, *args):
        if self.fp is not None:
            os.lockf(self.fp.fileno(), os.F_ULOCK, 0)
            self.fp.close()


class MyRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when=None, interval=1, backup_count=0, encoding=None, delay=False, utc=False, at_aime=None):
        super().__init__(filename, when=when, interval=interval, backupCount=backup_count, encoding=encoding, delay=delay, utc=utc, atTime=at_aime)

    def _open(self):
        """
        open without buffering and binary mode
        """

        return open(self.baseFilename, "{}b".format(self.mode), buffering=0, encoding=self.encoding)

    def emit(self, record):
        """
        double check file size protected by file lock, write in binary mode
        """
        try:
            if self.shouldRollover(record):
                # anyway, we need close it first
                if self.stream is not None:
                    self.stream.close()
                    self.stream = None
                with FileLock(self.baseFilename):
                    # double check
                    if self.shouldRollover(record):
                        self.doRollover()
                    # endif
                # end with
            # endif
            try:
                if self.stream is None:
                    self.stream = self._open()
                msg = self.format(record)
                msg += self.terminator
                stream = self.stream
                stream.write(msg.encode())
            except Exception as ex:
                print(str(ex))
                self.handleError(record)
        except Exception as ex:
            print(str(ex))
            self.handleError(record)


class Logger(object):
    #
    # copy from logging to avoid caller import logging
    #
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTEST = logging.NOTSET

    access_log_file = None  # 定位API访问日志
    access_log_level = logging.INFO
    error_log_file = None  # 定位异常日志
    ledger_log_file = None  # 同步区块日志
    transaction_log_file = None  # 日志监控

    access_log_handler = None
    error_log_handler = None
    ledger_log_handler = None
    transaction_log_handler = None
    stream_log_handler = None

    current_context = {}
    context_text = ""
    context_level = logging.INFO

    def __init__(self, module=None, level=None):
        self.module = module
        self.log_level = level if level else Logger.access_log_level  # INFO

    @staticmethod
    def setup(access_log_file=None, access_log_level=logging.INFO, error_log_file=None, ledger_log_file=None, transaction_log_file=None, when=None, backup_count=0, enable_console=False):
        Logger.access_log_file = access_log_file
        Logger.access_log_level = access_log_level
        Logger.error_log_file = error_log_file
        Logger.ledger_log_file = ledger_log_file
        Logger.transaction_log_file = transaction_log_file

        Logger.access_log_handler = MyRotatingFileHandler(Logger.access_log_file, when=when, backup_count=backup_count) if Logger.access_log_file else logging.StreamHandler(sys.stderr)
        Logger.error_log_handler = MyRotatingFileHandler(Logger.error_log_file, when=when, backup_count=backup_count) if Logger.error_log_file else logging.NullHandler()
        Logger.ledger_log_handler = MyRotatingFileHandler(Logger.ledger_log_file, when=when, backup_count=backup_count) if Logger.ledger_log_file else logging.NullHandler()
        Logger.transaction_log_handler = MyRotatingFileHandler(Logger.transaction_log_file, when=when, backup_count=backup_count) if Logger.transaction_log_file else logging.NullHandler()
        Logger.stream_log_handler = logging.StreamHandler(sys.stderr) if enable_console else logging.NullHandler()

        formatter = logging.Formatter(fmt="%(asctime)s||pid=%(process)d||level=%(levelname)s||%(message)s")
        Logger.access_log_handler.setFormatter(formatter)
        Logger.error_log_handler.setFormatter(formatter)
        Logger.stream_log_handler.setFormatter(formatter)

        formatter2 = logging.Formatter(fmt="%(asctime)s||pid=%(process)d||%(message)s")
        Logger.ledger_log_handler.setFormatter(formatter2)
        Logger.transaction_log_handler.setFormatter(formatter2)

        Logger.current_context = {}
        Logger.context_text = ""

    @staticmethod
    def get_logger(module=None, level=None):

        return Logger(module, level)

    @staticmethod
    def format_msg(depth, fmt, *args, **kw):
        """
        :param depth: 获取调用堆栈的深度
        :param fmt: 待打印信息fmt
        :param args: fmt对应参数
        :param kw: 关键字参数
        :return: 格式化后的msg
        """
        # 从调用堆栈中获取指定深度的帧信息
        frame = sys._getframe(depth + 1)
        filename = os.path.join(*frame.f_code.co_filename.split(os.path.sep)[-3:])
        lineno = frame.f_lineno
        prefix = "{}file={}:{}".format(Logger.context_text, filename, str(lineno))

        msg = "{}||{}".format(prefix, (fmt % args)) if fmt else prefix
        for k, v in kw.items():
            msg += "||{}={}".format(str(k), str(v))

        return msg

    def info2(self, depth, msg=None, *args, **kw):
        try:
            if self.log_level > logging.INFO:
                return

            msg = self.format_msg(depth + 1, msg, *args, **kw)
            record = logging.LogRecord(self.module, logging.INFO, __file__, 1, msg, None, None)

            Logger.access_log_handler.emit(record)
            Logger.access_log_handler.flush()

            Logger.stream_log_handler.emit(record)
            Logger.stream_log_handler.flush()
        except Exception as ex:
            print("INFO2 got an exception: {}, depth={}, msg={}, args={}, kw={}, traceback={}".format(ex, depth, msg, args, kw, get_traceback()))

    def info(self, msg=None, *args, **kw):
        self.info2(1, msg, *args, **kw)

    def debug(self, msg=None, *args, **kw):
        try:
            if self.log_level > logging.DEBUG:
                return

            msg = self.format_msg(1, msg, *args, **kw)
            record = logging.LogRecord(self.module, logging.DEBUG, __file__, 1, msg, None, None)

            Logger.access_log_handler.emit(record)
            Logger.access_log_handler.flush()

            Logger.stream_log_handler.emit(record)
            Logger.stream_log_handler.flush()
        except Exception as ex:
            print("DEBUG got an exception: {}, msg={}, args={}, kw={}, traceback={}".format(ex, msg, args, kw, get_traceback()))

    def warn(self, msg=None, *args, **kw):
        try:
            if self.log_level > logging.WARNING:
                return

            msg = self.format_msg(1, msg, *args, **kw)
            record = logging.LogRecord(self.module, logging.WARNING, __file__, 1, msg, None, None)

            Logger.access_log_handler.emit(record)
            Logger.access_log_handler.flush()

            Logger.stream_log_handler.emit(record)
            Logger.stream_log_handler.flush()
        except Exception as ex:
            print("WARN got an exception: {}, msg={}, args={}, kw={}, traceback={}".format(ex, msg, args, kw, get_traceback()))

    def error2(self, depth, msg=None, *args, **kw):
        try:
            if self.log_level > logging.ERROR:
                return

            msg = self.format_msg(depth + 1, msg, *args, **kw)
            record = logging.LogRecord(self.module, logging.ERROR, __file__, 1, msg, None, None)

            Logger.access_log_handler.emit(record)
            Logger.access_log_handler.flush()

            Logger.error_log_handler.emit(record)
            Logger.error_log_handler.flush()

            Logger.stream_log_handler.emit(record)
            Logger.stream_log_handler.flush()
        except Exception as ex:
            print("ERROR2 got an exception: {}, depth={}, msg={}, args={}, kw={}, traceback={}".format(ex, depth, msg, args, kw, get_traceback()))

    def error(self, msg=None, *args, **kw):
        self.error2(1, msg, *args, **kw)

    def critical(self, msg=None, *args, **kw):
        try:
            if self.log_level > logging.CRITICAL:
                return

            msg = self.format_msg(1, msg, *args, **kw)
            record = logging.LogRecord(self.module, logging.CRITICAL, __file__, 1, msg, None, None)

            Logger.access_log_handler.emit(record)
            Logger.access_log_handler.flush()

            Logger.error_log_handler.emit(record)
            Logger.error_log_handler.flush()

            Logger.stream_log_handler.emit(record)
            Logger.stream_log_handler.flush()
        except Exception as ex:
            print("CRITICAL got an exception: {}, msg={}, args={}, kw={}, traceback={}".format(ex, msg, args, kw, get_traceback()))

    def transaction2(self, depth, msg=None, *args, **kw):
        try:
            msg = self.format_msg(depth + 1, msg, *args, **kw)
            record = logging.LogRecord(self.module, logging.ERROR, __file__, 1, msg, None, None)

            Logger.access_log_handler.emit(record)
            Logger.access_log_handler.flush()

            Logger.transaction_log_handler.emit(record)
            Logger.transaction_log_handler.flush()

            Logger.stream_log_handler.emit(record)
            Logger.stream_log_handler.flush()
        except Exception as ex:
            print("TRANSACTION2 got an exception: {}, depth={}, msg={}, args={}, kw={}, traceback={}".format(ex, depth, msg, args, kw, get_traceback()))

    def transaction(self, msg=None, *args, **kw):
        return self.transaction2(1, msg, *args, **kw)

    def ledger(self, msg=None, *args, **kw):
        try:
            msg = self.format_msg(1, msg, *args, **kw)
            record = logging.LogRecord(self.module, logging.INFO, __file__, 1, msg, None, None)

            Logger.ledger_log_handler.emit(record)
            Logger.ledger_log_handler.flush()

            Logger.stream_log_handler.emit(record)
            Logger.stream_log_handler.flush()
        except Exception as ex:
            print("ACCESS got an exception: {}, , msg={}, args={}, kw={}, traceback={}".format(ex, msg, args, kw, get_traceback()))

    def enter(self, context_level, *args, **kw):
        """
        设置日志上下文环境
        :param context_level: 上下文日志级别
        :param args: 可变参数,设置一些关键字,如routes上下文
        :param kw: 关键字参数,设置一些关键字,如http上下文
        :return: logger
        """
        Logger.current_context = {}
        Logger.context_text = ""
        Logger.context_level = context_level

        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    Logger.current_context[k] = v
                # endfor
            # endif
        # endfor
        for k, v in kw.items():
            Logger.current_context[k] = v
        # endfor

        for k in sorted(Logger.current_context.keys()):
            if Logger.context_text == "":
                Logger.context_text += "{}={}".format(str(k), str(Logger.current_context[k]))
            else:
                Logger.context_text += "||{}={}".format(str(k), str(Logger.current_context[k]))
        # endfor

        if len(Logger.current_context) > 0:
            Logger.context_text += "||"

        return self

    def exit2(self, depth, msg=None, *args, **kw):
        if len(kw) > 0:
            if Logger.context_level == Logger.INFO:
                self.info2(depth + 1, msg, *args, **kw)
            else:
                self.transaction2(depth + 1, msg, *args, **kw)

        Logger.current_context = {}
        Logger.context_text = ""

    def exit(self, msg=None, *args, **kw):

        return self.exit2(1, msg, *args, **kw)

    @staticmethod
    def application_handler():
        # re-setup flask and sqlaclchemy logging level
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

        logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
        logging.getLogger('sqlalchemy.engine').addHandler(Logger.transaction_log_handler)

class LoggerContext(object):
    def __init__(self, logger, *args, **kw):
        assert logger is not None
        self.start_time = datetime.now()
        self.end_time = datetime.now()
        self.logger = logger
        self.logger.enter(Logger.INFO, *args, **kw)

    def __del__(self):
        if self.logger is not None:
            self.logger.exit()
        self.logger = None

    def transaction(self, msg=None, *args, **kw):
        Logger.context_level = Logger.ERROR
        self.logger.transaction2(1, msg, *args, **kw)

    def info(self, msg=None, *args, **kw):
        Logger.context_level = Logger.INFO
        self.logger.info2(1, msg, *args, **kw)

    def exit(self, msg=None, *args, **kw):
        self.end_time = datetime.now()
        kw["costtime"] = "{:.0f}ms".format((self.end_time - self.start_time).total_seconds() * 1000)
        self.logger.exit2(1, msg, *args, **kw)
        self.logger = None


# default output to STDERR, caller can  re-setup to change them
Logger.setup(access_log_level=Logger.DEBUG)

