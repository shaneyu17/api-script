# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/11


class Config(object):
    log_dir = "../logs/"
    log_level = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_when = "MIDNIGHT"
    log_backup_count = 50
    enable_console = True

    bypass_front_appid_headers = "appId"
    bypass_front_appid_content = "299ed7bf6e774eebb3e162b589aa91ad"
    bypass_front_signs_headers = "Primepay-Signature"

    encryption_body_key = "WLT-LaC9-sudi89D"
    sig_hed_private_key = "MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBALmZDB7KK+JflGG6iKuCuIewIjGozUPdTHmYqHuHFgalt5P6/eeiK64dHK0U5uXeWCwlAYp7/bWraNKjVdM6" \
                          "/oyiMvY2AqC1Kld7Zygj8onkKXJEaeC9841PUd76sr4ndufkKbuO68rr1lOlRweMKLuM2JYBSlw64A+65XOaBPPjAgMBAAECgYEAmI35jXFmovsnbzExV7DqVvXrFWCH4ImNa8GUc3z1GN+sRuGfRH9jYgmh4Y71v+qEFT0RyC" \
                          "/kuig70C/bwvWR9sY8OU0AwvYTM2pQ0bPnazyBRRKpZZuwWy5TELBOGQoV5Mdd3wInPlpChEivYMK3oVBrn/vC3xl+raJUdiA9vRECQQDkb4Rwmky5em0kZfvwUyw6m0oux8KuzkbQ7KVsiSZ5nyoWQyyMSZ" \
                          "/ojN54Zcdw0oYT8qWJhijDHcnMgayiXhGJAkEAz/5ATvT4vYgOR2DE7AFXvcm+FxhAt5Dyuhx7VaAwQSsMojqbAUENkL0mLWizxZW" \
                          "/Hxq3UyCJzif8Qbmf8qrbCwJAZGG44j573rm0wlzqdDYoZmydEaeInoZYyjBjlSlDtghCV1wXdGJaGbflfyTCmop4jsV/BsrkmLE7X1nQgd0yeQJAc/JyexGJEG8mNpg1brMY7I3oUAuPGEXPafyyrHsOK2YKNu2gt0RCgatP" \
                          "+wRhIwZlcrt78vUynSAhOap3BdpFHQJAT1oAKS1k3ezx9IS+JYN1yWil6W8HHlCFcCS8iSCe9x4L7YHReIlZGc30ZPiVaynobfMuin7oQCJ52Y9ATXfjiw=="

    api_test_sheet_name = "API-TESTING"
    api_order_no_prefix = "API-TESTING"
    api_test_report_path = "./report/"
    api_test_suites_title = "测试用例"
    api_test_report_title = "测试报告"
