import requests

def get_dbt_cloud_job_id(api_key, account_id, environment_id, job_name, *, state=1):
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    
    base_url = f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/jobs"

    url = (
        f"{base_url}"
        f"?environment_id={environment_id}"
        f"&state={state}"
        f"&limit=100"
        f"&name__icontains={job_name}"
    )
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    response_json = response.json()
    
    if len(response_json["data"]) > 0 and (response_json["data"][0]['name']).upper() == job_name.upper():
        
        job_id = response_json["data"][0]['id']
        
        return job_id
        
    else:
        raise ValueError(f"Job not found with name: {job_name} in environment: {environment_id}")
