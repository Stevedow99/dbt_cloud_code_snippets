from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.models.baseoperator import BaseOperator
from airflow.hooks.base_hook import BaseHook
import requests
import json
import os


class DbtCloudGetRunLogsOperator(BaseOperator):
    template_fields = ('dbt_cloud_run_id', 'log_target_directory_path', 'log_file_name')

    @apply_defaults
    def __init__(
        self,
        dbt_cloud_conn_id: str,
        log_type: str,
        dbt_cloud_run_id: str,
        log_target_directory_path: str,
        log_file_name: str,
        *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.dbt_cloud_conn_id = dbt_cloud_conn_id
        self.log_type = log_type
        self.dbt_cloud_run_id = dbt_cloud_run_id
        self.log_target_directory_path = log_target_directory_path
        self.log_file_name = log_file_name

        # Validate the 'log_type' parameter
        if log_type not in ['console_logs', 'debug_logs']:
            raise ValueError("Invalid value for log_type. It must be 'console_logs' or 'debug_logs'.")
        self.log_type = log_type


    def execute(self, context):

        # Retrieve the connection object dor get clout
        dbt_cloud_conn = BaseHook.get_connection(self.dbt_cloud_conn_id)

        # Get connection parameters
        dbt_cloud_tenant = dbt_cloud_conn.host if dbt_cloud_conn.host not in (None, "") else 'cloud.getdbt.com'
        dbt_cloud_account_id = dbt_cloud_conn.login
        dbt_cloud_token = dbt_cloud_conn.password

        # Creating the URL endpoint
        endpoint = f'https://{dbt_cloud_tenant}/api/v2/accounts/{dbt_cloud_account_id}/runs/{self.dbt_cloud_run_id}/?include_related=["run_steps","debug_logs"]'

        # creating the headers
        headers = {'Authorization': f'Token {dbt_cloud_token}'}

        # Make the API Call to get the data
        response = requests.get(endpoint, headers=headers)
        
        # Check status code
        if response.status_code != 200:
            raise Exception(f"Request failed: {response.text}")
        
        # Turn data into JSON
        data = response.json()

        # Extract logs
        run_steps = data.get('data', {}).get('run_steps', [])

        # Initialize an empty list to store debug logs
        debug_logs = []

        # Determine what type of logs to return
        logs_to_fetch = 'logs' if self.log_type == 'console_logs' else 'debug_logs'

        # Loop through each run_step and extract debug_logs
        for step in run_steps:
            step_logs = step.get(f'{logs_to_fetch}', '')
            debug_logs.append(step_logs)

        # Concatenate all debug logs into a single string
        concatenated_logs = '\n'.join(debug_logs)

        if not os.path.exists(self.log_target_directory_path):
            # Create the directory if it doesn't exist
            os.makedirs(self.log_target_directory_path)

        # Save the concatenated logs to the specified output file
        with open(self.log_target_directory_path + self.log_file_name, 'w') as file:
            file.write(concatenated_logs)
        
        # Logging the completion of the task
        self.log.info(f"Logs saved to {self.log_target_directory_path + self.log_file_name}")
