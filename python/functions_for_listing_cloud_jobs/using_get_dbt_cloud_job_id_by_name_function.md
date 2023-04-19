# Get dbt Cloud Job ID by Job Name


### When to use this function
- When you are dynamically creating dbt Cloud jobs and need to get the job ID by passing the job name


### Example of using this function
``` python

# Example usage:
api_key = "<<your dbt cloud API service token>>"
account_id = 123456  # Replace with your account ID
project_id = 789789  # Replace with your project ID
job_name = "your_job_name"

job_id = get_dbt_cloud_job_id(api_key, account_id, project_id, job_name)
print(f"Job ID for '{job_name}': {job_id}")

# returns: Job ID for 'your_job_name': 272244

```