# DbtCloudGetRunLogsOperator

The `DbtCloudGetRunLogsOperator` is a custom Airflow operator designed to retrieve and save logs from a dbt Cloud run. This operator is capable of fetching either console logs or debug logs based on the configuration. The code for this custom operator can be found in this repo under `Airflow/plugins/operators/dbt_cloud_get_run_logs_operator.py`

## Operator Parameters

- **dbt_cloud_conn_id** (*str*): The connection ID for dbt Cloud. This should be set up in the Airflow connections with the host, login (account ID), and password (API token).
- **log_type** (*str*): The type of logs to retrieve. Valid options are 'console_logs' or 'debug_logs'.
- **log_target_directory_path** (*str*): The file path where the logs will be saved.
- **log_file_name** (*str*): The name of the file to save the logs, the operator will add the run id as a pre-fix to the file name to ensure uniqueness -- _e.g. if log_file_name is set to `awesome_logs.log` and the dbt Cloud run id is `12344554` then the output will be `12344554_awesome_logs.log`_ 
- **dbt_cloud_run_id** (*str*, *optional*): The ID of the dbt Cloud run from which to retrieve logs 
  - Note: while both `dbt_cloud_run_id` and `dbt_cloud_run_url` are optional you must provide at least one of them, if both are provided it will use `dbt_cloud_run_id`
- **dbt_cloud_run_url** (*str*, *optional*): The URL of the dbt Cloud run. The run ID will be extracted from this URL if `dbt_cloud_run_id` is not provided
  - Note: while both `dbt_cloud_run_id` and `dbt_cloud_run_url` are optional you must provide at least one of them, if both are provided it will use `dbt_cloud_run_id`

## Usage

   - The operator retrieves the dbt Cloud connection details based on the `dbt_cloud_conn_id` and the provided `dbt_cloud_run_id`
   - It constructs the request to the dbt Cloud API to fetch the run details, including the related run steps and debug logs.
   - It processes the API response, extracting the requested type of logs (console or debug) from the run steps.
   - If the `log_target_directory_path` doesn't exist, it creates the directory.
   - It saves the logs to the specified file in the specified directory.

## Notes
   - This operator allows you to leverage [Airflow Trigger Rules](https://airflow.apache.org/docs/apache-airflow/1.10.9/concepts.html#trigger-rules)
     - This allows for running of the operator even if the a previous task like running a dbt Cloud job fails
     - The first example shows this by setting `trigger_rule=all_done` meaning the logs will upload even if kicking off the dbt Cloud job fails


## Example One: Grabbing dbt Cloud debug logs and uploading them to AWS S3 regardless of dbt Cloud job run Status

```python
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from plugins.operators.dbt_cloud_get_run_logs_operator import DbtCloudGetRunLogsOperator
from airflow.providers.amazon.aws.transfers.local_to_s3 import LocalFilesystemToS3Operator
from airflow.providers.dbt.cloud.operators.dbt import (
    DbtCloudRunJobOperator, DbtCloudGetJobRunArtifactOperator
)


default_args = {"dbt_cloud_conn_id": "dbt_cloud_account_connection", "account_id": 77338}


with DAG(
    dag_id='example_dbt_cloud_dag_w_upload_logs_override_failures',
    default_args=default_args,
    description='A simple DAG to call DBT Cloud API and save debug logs',
    schedule_interval=None,
    start_date=days_ago(1),
    tags=['example'],
) as dag:
    
    # Trigger the dbt Cloud Job
    trigger_dbt_cloud_job_run_that_will_fail = DbtCloudRunJobOperator(
        task_id="trigger_dbt_cloud_job_run_that_will_fail",
        job_id=695789,
        check_interval=10,
        timeout=300,
    )

    # grab the job run url and parse out run id
    dbt_cloud_run_url = "{{ task_instance.xcom_pull(task_ids='trigger_dbt_cloud_job_run_that_will_fail', key='job_run_url') }}"

    # Download the detailed debug logs
    download_cloud_run_debug_logs = DbtCloudGetRunLogsOperator(
        task_id='download_cloud_run_debug_logs',
        dbt_cloud_run_url=dbt_cloud_run_url,
        log_type='debug_logs',
        log_target_directory_path='./a_sample_folder/',
        # note the dbt cloud run id will be pre_fixed on to this string to ensure unqiueness
        log_file_name=f'_dbt_cloud_debug_console_logs',
        trigger_rule='all_done'
    )

    # grab the log download information
    dbt_cloud_run_id = "{{ task_instance.xcom_pull(task_ids='download_cloud_run_debug_logs', key='dbt_cloud_run_id') }}"
    dbt_cloud_debug_logs_path = "{{ task_instance.xcom_pull(task_ids='download_cloud_run_debug_logs', key='log_file_path') }}"

    # upload debug logs to S3
    upload_cloud_run_debug_logs_to_s3 = LocalFilesystemToS3Operator(
        task_id='upload_dbt_run_debug_logs_to_s3',
        filename=dbt_cloud_debug_logs_path,
        dest_key=f's3://steve-d-sandbox-bucket/dbt_cloud_run_logs/{dbt_cloud_run_id}/dbt_cloud_run_{dbt_cloud_run_id}_debug_logs.log',
        aws_conn_id='aws_sales_sandbox',
        replace=True,
        trigger_rule='all_done'
    )

    # Setting the run order
    trigger_dbt_cloud_job_run_that_will_fail >> download_cloud_run_debug_logs >> upload_cloud_run_debug_logs_to_s3

```
## Example Two: Grabbing dbt Cloud debug and console logs plus a run artifact and uploading them to AWS S3 only if the dbt Cloud job run Status is successful  

```python
from airflow import DAG
from airflow.utils.dates import days_ago
from plugins.operators.dbt_cloud_get_run_logs_operator import DbtCloudGetRunLogsOperator
from airflow.providers.amazon.aws.transfers.local_to_s3 import LocalFilesystemToS3Operator
from airflow.providers.dbt.cloud.operators.dbt import (
    DbtCloudRunJobOperator, DbtCloudGetJobRunArtifactOperator
)



default_args = {"dbt_cloud_conn_id": "dbt_cloud_account_connection", "account_id": 77338}

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

    # grab the console log download information and the run id which will be reused
    dbt_cloud_run_id = "{{ task_instance.xcom_pull(task_ids='download_cloud_run_console_logs', key='dbt_cloud_run_id') }}"
    dbt_cloud_console_logs_path = "{{ task_instance.xcom_pull(task_ids='download_cloud_run_console_logs', key='log_file_path') }}"

    # Download the detailed debug logs
    download_cloud_run_debug_logs = DbtCloudGetRunLogsOperator(
        task_id='download_cloud_run_debug_logs',
        dbt_cloud_run_id=trigger_dbt_cloud_job_run.output,
        log_type='debug_logs',
        log_target_directory_path='./a_sample_folder/',
        log_file_name=f'dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_debug_logs.log',
    )

    # grab the debug log download information 
    dbt_cloud_debug_logs_path = "{{ task_instance.xcom_pull(task_ids='download_cloud_run_debug_logs', key='log_file_path') }}"

    # Download a dbt run artifact (manifest.json or run_results.json)
    download_cloud_run_results_artifact = DbtCloudGetJobRunArtifactOperator(
        task_id="download_cloud_run_results_artifact", 
        run_id=trigger_dbt_cloud_job_run.output, 
        path="run_results.json"
    )

    # upload debug logs to S3
    upload_cloud_run_debug_logs_to_s3 = LocalFilesystemToS3Operator(
        task_id='upload_dbt_run_debug_logs_to_s3',
        filename=dbt_cloud_debug_logs_path,
        dest_key=f's3://steve-d-sandbox-bucket/dbt_cloud_run_logs/{dbt_cloud_run_id}/dbt_cloud_run_{dbt_cloud_run_id}_debug_logs.log',
        aws_conn_id='aws_sales_sandbox',
        replace=True
    )

    # upload debug logs to S3
    upload_cloud_run_console_logs_to_s3 = LocalFilesystemToS3Operator(
        task_id='upload_cloud_run_console_logs_to_s3',
        filename=dbt_cloud_console_logs_path,
        dest_key=f's3://steve-d-sandbox-bucket/dbt_cloud_run_logs/{dbt_cloud_run_id}/dbt_cloud_run_{dbt_cloud_run_id}_console_logs.log',
        aws_conn_id='aws_sales_sandbox',
        replace=True
    )

    # upload artifact to S3
    upload_cloud_run_artifact_to_s3 = LocalFilesystemToS3Operator(
        task_id='upload_cloud_run_artifact_to_s3',
        filename=f'./{dbt_cloud_run_id}_run_results.json',
        dest_key=f's3://steve-d-sandbox-bucket/dbt_cloud_run_logs/{dbt_cloud_run_id}/dbt_cloud_run_{dbt_cloud_run_id}_run_results.json',
        aws_conn_id='aws_sales_sandbox',
        replace=True
    )

    # Setting the run order
    trigger_dbt_cloud_job_run >> download_cloud_run_debug_logs >> upload_cloud_run_debug_logs_to_s3
    trigger_dbt_cloud_job_run >> download_cloud_run_console_logs >> upload_cloud_run_console_logs_to_s3
    trigger_dbt_cloud_job_run >> download_cloud_run_results_artifact >> upload_cloud_run_artifact_to_s3
``` 