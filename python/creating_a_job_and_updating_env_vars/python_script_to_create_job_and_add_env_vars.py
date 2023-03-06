# Databricks notebook source
# MAGIC %md
# MAGIC ### Import Dependencies 

# COMMAND ----------

import requests
import json

# COMMAND ----------

# MAGIC %md
# MAGIC ### Define account configs and Token
# MAGIC 
# MAGIC - Note for the account configs you can programmatically grab them using an API call if needed

# COMMAND ----------

# pull in my dbt Cloud Service token
dbt_st = <<ST>>

# define my dbt Cloud account ID
dbt_cloud_account_id = 123456

# define my dbt Cloud project ID
# cloud use API call to grab if more tha one project
# to get this manually click on the enviroment in the UI and grab it from the URL https://cloud.getdbt.com/deploy/123456/projects/<<<<THIS>>>
dbt_cloud_project_id = 345678

# define my dbt Cloud enviorment ID
# cloud use API call to grab if more tha one enviorment
# to get this manually click on the enviroment in the UI and grab it from the URL https://cloud.getdbt.com/deploy/123456/projects/345678/environments/<<<<THIS>>>
dbt_cloud_env_id = 912345


# COMMAND ----------

# MAGIC %md
# MAGIC ### Build out payload

# COMMAND ----------

# defining the github payload to create a job

# define the name of the job we are creating
# this would likely be done programmatically 
dbt_job_name = "Run Project 44"


# setting this job up to not be trigger because i'll likely kick it off via the API
create_job_payload = {
    "account_id": dbt_cloud_account_id,
    "project_id": dbt_cloud_project_id,
    "id": None,
    "environment_id": dbt_cloud_env_id,
    "name": dbt_job_name,
    "dbt_version": "1.0.1",
    "triggers": {
      "github_webhook": False,
      "schedule": False,
      "custom_branch_only": False
    },
    "execute_steps": [
      "dbt run"
    ],
    "settings": {
      "threads": 1,
      "target_name": "default"
    },
    "state": 1,
    "generate_docs": False,
    "schedule": {
        "date": {
            "type": "every_day"
        },
        "time": {
            "type": "every_hour",
            "interval": 1
        }
    }
}

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create the job

# COMMAND ----------

# create the URL
create_job_url = f"https://cloud.getdbt.com/api/v2/accounts/{dbt_cloud_account_id}/jobs/"

# define auth head
headers = {'Authorization': f"Token {dbt_st}"}

# post payload to create job in account
response = requests.request("POST", create_job_url, headers=headers, json=create_job_payload)

# log the status
print(response.json()['status']['is_success'])

# COMMAND ----------

# MAGIC %md
# MAGIC ### Add env var override to job

# COMMAND ----------

# get the job id for the job that was created
job_id = response.json()['data']['id']

# create the URL
env_var_post_url = f"https://cloud.getdbt.com/api/v3/accounts/{dbt_cloud_account_id}/projects/{dbt_cloud_project_id}/environment-variables/"

# the subdir value - which is the sub directory path of the dbt project I just created in my repo
# normally you would grab this from elsewhere but i'll enter mnaully for the example 
env_var_override_value = 'dbt_project_forty_four'

# defining the env var name 
env_var_name = "DBT_SUB_DIRECTORY_PATH"

# define body payload
env_var_overirde_payload = {
    "id": None,
    "account_id": dbt_cloud_account_id,
    "project_id": dbt_cloud_project_id,
    "job_definition_id": job_id,
    "type": "job",
    "name": env_var_name,
    "raw_value": env_var_override_value
}


# post payload to update env var
response = requests.request("POST", env_var_post_url, headers=headers, json=env_var_overirde_payload)

# log the status
print(response.json()['status']['is_success'])

# COMMAND ----------

# MAGIC %md
# MAGIC ### [Optional] Trigger the job 

# COMMAND ----------


# create the URL
trigger_job_url = f"https://cloud.getdbt.com/api/v2/accounts/{dbt_cloud_account_id}/jobs/{job_id}/run/"

# define payload
trigger_job_payload = {
  "cause": "Kicked off first run of this job"
}

# trigger job
# post payload to update env var
response = requests.request("POST", trigger_job_url, headers=headers, json=trigger_job_payload)

# log the status of triggering the job
print(response.json()['status']['is_success'])

# COMMAND ----------

# MAGIC %md
# MAGIC ### END OF SCRIPT
