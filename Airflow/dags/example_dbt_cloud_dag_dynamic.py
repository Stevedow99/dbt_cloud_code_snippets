from datetime import datetime
import random

from airflow.models import DAG
from airflow.operators.dummy import DummyOperator
from airflow.providers.dbt.cloud.operators.dbt import (
    DbtCloudRunJobOperator,
)


def generate_random():
    random_number = random.randint(100000, 400000)  # Generate a random number between 1 and 100
    print(f"Generated random number: {random_number}")
    return random_number


with DAG(
    dag_id="example_dbt_cloud_dag_dynamic",
    default_args={"dbt_cloud_conn_id": "dbt_cloud_account_connection", "account_id": 12345},
    start_date=datetime(2021, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:


    extract = DummyOperator(task_id="extract")
    load = DummyOperator(task_id="load")
    ml_training = DummyOperator(task_id="ml_training")

    # get a random number to pass to dbt Cloud
    rand_num = generate_random()

    trigger_dbt_cloud_job_run = DbtCloudRunJobOperator(
        task_id="trigger_dynamic_dbt_cloud_job_run",
        steps_override=['dbt source freshness --select "source:customer_data_source.customer_dim"',
                        f'dbt build --select +tag:customer_reporting --vars "{{large_customer_threshold: {rand_num} }}"'
                        ],
        job_id=494574,
        check_interval=10,
        timeout=300,
    )

    extract >> load >> trigger_dbt_cloud_job_run >> ml_training