import requests

def get_dbt_cloud_job_id(api_key, account_id, project_id, job_name):
    
    # define headers
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    
    # set base url for dbt Cloud
    base_url = f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/jobs"

    # set the url that will get called
    url = f"{base_url}?project_id={project_id}&limit=100&name__icontains={job_name}"
    
    # get the response
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # parse response json
    response_json = response.json()
    
    # we make sure that the name of the job matches the name that was passed, if so we return job id. If not, we raise an error that the job doesn't exist
    if len(response_json["data"]) > 0 and (response_json["data"][0]['name']).upper() == job_name.upper():
        
        # grab the job id
        job_id = response_json["data"][0]['id']
        
        # return the job id
        return job_id
        
    else:
        # raise error that the job name was not found
        raise ValueError(f"Job not found with name: {job_name}")