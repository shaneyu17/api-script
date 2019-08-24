# !/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__: Shane
# _datetime_: 2018/08/24

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
        dag_id="rebalance",
        default_args=default_args,
        description="A simple rebalance test DAG",
        schedule_interval="@daily",
        )

t10 = BashOperator(
        task_id="colleciton_chain_data",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_collection_chain_data.sh "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)
t101 = BashOperator(
        task_id="colleciton_etc_data",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_collection_etc_data.sh "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)
t11 = BashOperator(
        task_id="colleciton_rebalance",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_collection_rebalance.sh "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)

t20 = BashOperator(
        task_id="internal_transaction_chain_data",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_internal_transaction_chain_data.sh "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)
t21 = BashOperator(
        task_id="internal_transaction_rebalance",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_internal_transaction_rebalance.sh "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)

t30 = BashOperator(
        task_id="offline_chain_data",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_offline_chain_data.sh "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)
t31 = BashOperator(
        task_id="offline_rebalance",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_offline_rebalance.sh "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)

t40 = BashOperator(
        task_id="withdraw_tx_chain_data",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_withdraw_chain_data.sh "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)
t41 = BashOperator(
        task_id="withdraw_tx_rebalance",
        bash_command="""/data/home/admin/wallet/rebalance/script/start_withdraw_rebalance.sh  "{{params.START}}" """,
        params={"START": "airflow"},
        dag=dag)

t0 = BashOperator(
        task_id='begin',
        bash_command="echo begin ",
        dag=dag)

t1 = BashOperator(
        task_id='ended',
        bash_command="echo ended ",
        dag=dag)

t0.set_downstream(t10)
t0.set_downstream(t101)
t0.set_downstream(t20)
t0.set_downstream(t30)
t0.set_downstream(t40)

t10.set_downstream(t11)
t101.set_downstream(t11)
t20.set_downstream(t21)
t30.set_downstream(t31)
t40.set_downstream(t41)

t11.set_downstream(t1)
t21.set_downstream(t1)
t31.set_downstream(t1)
t41.set_downstream(t1)
