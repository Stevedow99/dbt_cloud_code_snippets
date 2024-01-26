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
    description='A simple DAG to call DBT Cloud API and save debug logs and upload them to S3',
    schedule_interval=None,
    start_date=days_ago(1),
    tags=['example'],
) as dag:
    
    # Trigger the dbt Cloud Job
    trigger_dbt_cloud_job_run = DbtCloudRunJobOperator(
        task_id="trigger_dbt_cloud_job_run",
        job_id=678987,
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

    # Download the detailed debug logs
    download_cloud_run_debug_logs = DbtCloudGetRunLogsOperator(
        task_id='download_cloud_run_debug_logs',
        dbt_cloud_run_id=trigger_dbt_cloud_job_run.output,
        log_type='debug_logs',
        log_target_directory_path='./a_sample_folder/',
        log_file_name=f'dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_debug_logs.log',
    )

    # Download a dbt run artifact (manifest.json or run_results.json)
    download_cloud_run_results_artifact = DbtCloudGetJobRunArtifactOperator(
        task_id="download_cloud_run_results_artifact", 
        run_id=trigger_dbt_cloud_job_run.output, 
        path="run_results.json"
    )

    # upload run console logs to S3
    upload_cloud_run_console_logs_to_s3 = LocalFilesystemToS3Operator(
        task_id='upload_cloud_run_console_logs_to_s3',
        filename=f'./a_sample_folder/dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_console_logs.log',
        dest_key=f's3://sandbox-bucket/dbt_cloud_run_logs/{trigger_dbt_cloud_job_run.output}/dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_console_logs.log',
        aws_conn_id='aws_sandbox_conn_id',
        replace=True
    )

    # upload debug logs to S3
    upload_cloud_run_debug_logs_to_s3 = LocalFilesystemToS3Operator(
        task_id='upload_dbt_run_debug_logs_to_s3',
        filename=f'./a_sample_folder/dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_debug_logs.log',
        dest_key=f's3://sandbox-bucket/dbt_cloud_run_logs/{trigger_dbt_cloud_job_run.output}/dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_debug_logs.log',
        aws_conn_id='aws_sandbox_conn_id',
        replace=True
    )

    # upload artifact to S3
    upload_cloud_run_artifact_to_s3 = LocalFilesystemToS3Operator(
        task_id='upload_cloud_run_artifact_to_s3',
        filename=f'./{trigger_dbt_cloud_job_run.output}_run_results.json',
        dest_key=f's3://sandbox-bucket/dbt_cloud_run_logs/{trigger_dbt_cloud_job_run.output}/dbt_cloud_run_{trigger_dbt_cloud_job_run.output}_run_results.json',
        aws_conn_id='aws_sandbox_conn_id',
        replace=True
    )

    # Setting the run order
    trigger_dbt_cloud_job_run >> download_cloud_run_console_logs >> upload_cloud_run_console_logs_to_s3
    trigger_dbt_cloud_job_run >> download_cloud_run_debug_logs >> upload_cloud_run_debug_logs_to_s3
    trigger_dbt_cloud_job_run >> download_cloud_run_results_artifact >> upload_cloud_run_artifact_to_s3


