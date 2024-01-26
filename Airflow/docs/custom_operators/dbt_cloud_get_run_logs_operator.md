# DbtCloudGetRunLogsOperator

The `DbtCloudGetRunLogsOperator` is a custom Airflow operator designed to retrieve and save logs from a dbt Cloud run. This operator is capable of fetching either console logs or debug logs based on the configuration.

## Operator Parameters

- **dbt_cloud_conn_id** (*str*): The connection ID for dbt Cloud. This should be set up in the Airflow connections with the host, login (account ID), and password (API token).
- **log_type** (*str*): The type of logs to retrieve. Valid options are 'console_logs' or 'debug_logs'.
- **dbt_cloud_run_id** (*str*): The ID of the dbt Cloud run from which to retrieve logs.
- **log_target_directory_path** (*str*): The file path where the logs will be saved.
- **log_file_name** (*str*): The name of the file to save the logs.

## Usage

   - The operator retrieves the dbt Cloud connection details based on the `dbt_cloud_conn_id` and the provided `dbt_cloud_run_id`
   - It constructs the request to the dbt Cloud API to fetch the run details, including the related run steps and debug logs.
   - It processes the API response, extracting the requested type of logs (console or debug) from the run steps.
   - If the `log_target_directory_path` doesn't exist, it creates the directory.
   - It saves the logs to the specified file in the specified directory.

## Example

Here's an example of how to use the `DbtCloudGetRunLogsOperator` in a DAG:

```python
from airflow import DAG
from airflow.utils.dates import days_ago
from plugins.operators.dbt_cloud_get_run_logs_operator import DbtCloudGetRunLogsOperator
from airflow.providers.amazon.aws.transfers.local_to_s3 import LocalFilesystemToS3Operator
from airflow.providers.dbt.cloud.operators.dbt import (
    DbtCloudRunJobOperator, DbtCloudGetJobRunArtifactOperator
)



default_args = {"dbt_cloud_conn_id": "dbt_cloud_account_connection", "account_id": 12345}

with DAG(
    dag_id='example_dbt_cloud_dag_w_upload_logs',
    default_args=default_args,
    description='A simple DAG to call DBT Cloud API and save debug logs',
    schedule_interval=None,
    start_date=days_ago(1),
    tags=['example'],
) as dag:
    
    # Trigger the dbt Cloud Job
    trigger_dbt_cloud_job_run = DbtCloudRunJobOperator(
        task_id="trigger_dbt_cloud_job_run",
        job_id=494574,
        check_interval=10,
        timeout=300,
    )

    # Download the simple console logs
    download_cloud_run_console_logs = DbtCloudGetRunLogsOperator(
        task_id='download_cloud_run_console_logs',
        dbt_cloud_run_id=trigger_dbt_cloud_job_run.output,
        log_type='console_logs',
        log_target_directory_path='./a_sample_folder/',
        log_file_name= f'dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_console_logs.log',
        
    )

    # upload run console logs to S3
    upload_cloud_run_console_logs_to_s3 = LocalFilesystemToS3Operator(
        task_id='upload_cloud_run_console_logs_to_s3',
        filename=f'./a_sample_folder/dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_console_logs.log',
        dest_key=f's3://sandbox-bucket/dbt_cloud_run_logs/{trigger_dbt_cloud_job_run.output}/dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_console_logs.log',
        aws_conn_id='aws_sandbox_conn_id',
        replace=True
    )

    # Setting the run order
    trigger_dbt_cloud_job_run >> download_cloud_run_console_logs >> upload_cloud_run_console_logs_to_s3