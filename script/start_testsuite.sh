#!/usr/bin/bash

hdir=$(cd `dirname $0`; pwd)
mod=scenario

export PYTHONPATH=$hdir
source /data/home/admin/wallet/miniconda3/bin/activate /data/home/admin/wallet/miniconda3/envs/api

function isRunning()
{
	if ps -ef | grep "mock-data" | grep ${mod} >/dev/null 2>&1; then
		return 0
	fi

	return 1
}

function start()
{
	if isRunning; then
		echo "$mod is already running"
		return 0
	fi

	if cd "$hdir"; then
		nohup python /data/home/admin/wallet/api-test/${mod}.py "/data/home/admin/wallet/api-test/file/scenario-test.xlsx" "/data/home/admin/wallet/api-test/file/mock-data.xlsx" > /data/home/admin/wallet/api-test/logs/runtime.log 2>&1 &
		if isRunning; then
			echo "start $mod OK"
		else
			echo "start $mod failed!!!"
		fi
	else
		echo "$hdir does not exist or permission denied"
	fi
}

function airflow()
{
	if isRunning; then
		echo "$mod is already running"
		return 0
	fi

	if cd "$hdir"; then
		python /data/home/admin/wallet/api-test/${mod}.py "/data/home/admin/wallet/api-test/file/scenario-test.xlsx" "/data/home/admin/wallet/api-test/file/mock-data.xlsx"
	else
		echo "$hdir does not exist or permission denied"
	fi
}

function stop()
{
	if ! isRunning; then
		echo "$mod is not running"
		return 0
	fi

	ps -ef | grep "mock-data" | grep ${mod} | awk '{ print $2 }' | xargs kill -9 >/dev/null 2>&1
	sleep 1
	ps -ef | grep "mock-data" | grep ${mod} | awk '{ print $2 }' | xargs kill -9 >/dev/null 2>&1

	if ! isRunning; then
		echo "stop $mod OK"
	else
		echo "stop $mod failed!!!"
	fi
}

function status()
{
	if isRunning; then
		echo "$mod is running"
	else
		echo "$mod is not running"
	fi
}

case "$1" in
	start)
		start
		;;
	airflow)
		airflow
		;;
	stop)
		stop
		;;
	restart)
		stop
		start
		;;
	status)
		status
		;;
	*)
		echo "Usage $0 [ start | airflow | stop | restart | status ]" 1>&2
		status
		;;
esac
