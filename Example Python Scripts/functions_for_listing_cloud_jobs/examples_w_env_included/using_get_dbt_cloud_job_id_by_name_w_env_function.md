# Get dbt Cloud Job ID by Job Name and Environment ID


### When to use this function
- When you are dynamically creating dbt Cloud jobs and need to get the job ID by passing the job name
- When you have jobs with the same name across different environments and need to target a specific environment


### Example of using this function
``` python

# Example usage:
api_key = "<<your dbt cloud API service token>>"
account_id = 123456  # Replace with your account ID
environment_id = 456456  # Replace with your environment ID
job_name = "your_job_name"

# state defaults to 1 (active jobs only)
job_id = get_dbt_cloud_job_id(api_key, account_id, environment_id, job_name)
print(f"Job ID for '{job_name}' in environment {environment_id}: {job_id}")

# returns: Job ID for 'your_job_name' in environment 456456: 272244

# to include deleted jobs, pass state=2; for all jobs, pass state=None
job_id = get_dbt_cloud_job_id(api_key, account_id, environment_id, job_name, state=2)

```
