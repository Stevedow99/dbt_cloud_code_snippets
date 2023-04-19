# importing string - used for getting the letters of the alphabet to optimize the order we grab a list of job
# this isn't necessary just increases performance if you have a lot of jobs
import string
import requests

def get_dbt_cloud_job_id(api_key, account_id, project_id, job_name):
    
    # define headers
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    
    # set base url for dbt Cloud
    base_url = f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/jobs"

    # offset to start on when listing jobs
    offset = 0
    
    # doing some optimization to start with a reversed order if job name starts with a letter in the back half of the alphabet
    order_by_sequence = "name" if job_name[0] in list(string.ascii_lowercase)[:13] else "-name"

    # call the api 
    while True:
        
        # set the url that will get called
        url = f"{base_url}?project_id={project_id}&limit=100&offset={offset}&order_by={order_by_sequence}"
        
        # get the response
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # parse response json
        response_json = response.json()
        
        # get a list of the jobs from the response
        jobs = response_json["data"]
        
        # gather total job count from the response - this will be used to determine if going to the next page is needed
        total_job_count = response_json["extra"]["pagination"]["total_count"]
        
        # looping through the list of jobs, if the job name is found we return job id and break, if not we increase offset below
        for job in jobs:
            if job["name"] == job_name:
                return job["id"]
                break
            
        # checking to see if the total number of results returned so far is greater than the total number of jobs
        # if it's less than the total number of jobs we increase the offset by 100
        if (offset+100) <= total_job_count:

            # increase the offset
            offset += 100
            
        # if it's less than or equal to the total job count, that means we've searched through all jobs and the job was not found
        # in this case we raise an error
        else:
            raise ValueError(f"Job not found with name: {job_name}")