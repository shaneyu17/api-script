# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/10/20

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator

default_args = {
    "owner": "Shane",
    "depends_on_past": False,
    "start_date": datetime(2018, 8, 24),
    "email": ["shane@primeledger.cn"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    }

dag = DAG(
        dag_id="reconciliaction",
        default_args=default_args,
        description="A simple reconciliaction test DAG",
        schedule_interval="@daily",
        )

t1 = BashOperator(
        task_id="chain_balance",
        bash_command="""/data/home/admin/wallet/api-test/script/start_reconciliaction.sh "{{params.START}}"  """,
        params={"START": "airflow"},
        dag=dag)

t0 = BashOperator(
        task_id='begin',
        bash_command="echo begin ",
        dag=dag)

t2 = BashOperator(
        task_id='ended',
        bash_command="echo ended ",
        dag=dag)

t0.set_downstream(t1)
t1.set_downstream(t2)