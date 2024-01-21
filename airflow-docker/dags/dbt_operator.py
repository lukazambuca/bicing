from datetime import datetime

from airflow.models import DAG
from airflow.utils.dates import days_ago
from airflow.operators.dummy import DummyOperator
from airflow.providers.dbt.cloud.operators.dbt import (
    DbtCloudRunJobOperator,
)

#https://cloud.getdbt.com/deploy/227749/projects/326193/jobs/506623/settings

with DAG(
    dag_id="dbt_cloud_transform",
    default_args={"dbt_cloud_conn_id": "dbt_cloud",
                 "account_id": 227749},
    start_date=days_ago(2),
    schedule_interval='@once',
    catchup=False,
) as dag:

    trigger_dbt_cloud_job_run = DbtCloudRunJobOperator(
        task_id="trigger_dbt_cloud_job_run",
        job_id=506623,
        check_interval=10,
        timeout=300,
    )

    trigger_dbt_cloud_job_run