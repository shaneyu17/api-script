# 工程目录
工程主要包含 接口测试 项目代码

## 主要目录
| Folder  | Contents |
|---------|----------|
|./api-test|接口测试项目代码

## WO目录
| Folder  | Contents |
|---------|----------|
|./common|公共组件
|./config|配置文件
|./conn|连接方法
|./logs|工程日志
|./models|数据方法
|./report|测试报告
|./tool|工程工具

# 运行程序
## 安装依赖
    进入api-test目录，python≥3.6.5环境执行pip install -r requirements.txt安装依赖

## 查看帮助
    (api) [root@192 api-test]# python scenario.py -h
	usage: scenario.py [-h] testcase testdata

	用法:
	python scenario.py "./file/scenario-test.xlsx" "./file/mock-data.xlsx"

	positional arguments:
	  testcase    测试用例文件
	  testdata    测试数据文件

	optional arguments:
	  -h, --help  show this help message and exit



# 发版记录
## [1.1.0]2018-10-18
场景测试用例执行

## [1.0.0]2018-10-16
API测试用例执行
