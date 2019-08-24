# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/12


import json

from config.config import Config


class TestReport(object):
    def __init__(self, json_data, report_name):
        self.json_data = json_data
        self.report_name = report_name

    @staticmethod
    def replace(data):
        return json.dumps(data, ensure_ascii=False).replace('"', "&quot;")

    @property
    def config(self):
        return {
            "reportFilename": Config.api_test_report_title,
            "reportDir": "report",
            "reportTitle": Config.api_test_report_title,
            "reportPageTitle": "Report",
            "inline": False,
            "inlineAssets": False,
            "cdn": True,
            "charts": True,
            "enableCharts": True,
            "code": True,
            "enableCode": True,
            "autoOpen": False,
            "overwrite": True,
            "timestamp": False,
            "ts": False,
            "showPassed": True,
            "showFailed": True,
            "showPending": True,
            "showSkipped": False,
            "showHooks": "failed",
            "saveJson": True,
            "saveHtml": True,
            "dev": False,
            "assetsDir": "report\\assets",
            "jsonFile": "",
            "htmlFile": ""
            }

    @staticmethod
    def html():
        return """<!doctype html>
<html lang="en">
<head>
    <meta charSet="utf-8"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>测试报告</title>
    <link rel="stylesheet" href="https://unpkg.com/mochawesome-report-generator@3.1.2/dist/app.css"/>
</head>
<body data-raw="{data_raw}"
      data-config="{data_config}">
<div id="report"></div>
<script src="https://unpkg.com/mochawesome-report-generator@3.1.2/dist/app.js"></script>
</body>
</html>"""

    @property
    def content(self):
        return self.html().format(data_raw=self.replace(self.json_data), data_config=self.replace(self.config))

    def report(self):
        with open(self.report_name, "wb") as f:
            f.write(self.content.encode())
            f.flush()
