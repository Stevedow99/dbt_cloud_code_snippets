import json
import boto3
import logging
import hmac
import hashlib

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    
    # ---------------------------------------------------
    # authorization of the webhook coming in
    # ---------------------------------------------------
    
    # Get the headers from the call
    headers = event.get('headers', {})
    
    # Grab the authorization header input
    headers_authorization = headers.get('authorization', None)
    
    # set up secrets manager to grab webhook token
    aws_sec_manager = boto3.client('secretsmanager')

    # the name of the secret you want to retrieve
    secret_name = "sdsa_dbt_cloud_webhook_auth_token"
    
    # get the payload from the webhook (this is used for auth)
    webhook_body = event['body']
    
    # encoding webhook body
    webhook_body_encoded = webhook_body.encode('utf-8')
    
    # retrieve the dbt cloud webhook from AWS secrets manager
    aws_sec_manager_response = aws_sec_manager.get_secret_value(SecretId=secret_name)
    secret_string = aws_sec_manager_response['SecretString']
    webhook_secret = json.loads(secret_string)['dbt_webhook_token']
    encoded_webhook_secret =  webhook_secret.encode('utf-8')
    
    # create the webhook signature 
    webhook_signature = hmac.new(encoded_webhook_secret, webhook_body_encoded, hashlib.sha256).hexdigest()
    
    
    # compare the auth header with the webhook sig to determine if the webhook is authorized
    if headers_authorization != webhook_signature:
        
        # logging unauthorized access attempt
        logger.info("Unauthorized access attempt")
    
        # return a response indicating unauthorized access
        return {
            'statusCode': 401,
            'body': json.dumps('Unauthorized access')
        }

    # --------------------------------------------------------
    # assuming authorization passed, grabbing the webhook body
    # -------------------------------------------------------
        
    # get the payload parsed
    webhook_parsed_payload = json.loads(webhook_body)
    
    
    # ------------------------------------------------------------------------------------------
    # at this point you can do pretty much anything with the webhook data
    # some examples:
    #   - get the run ID and then call dbt Cloud APIs to pull the run logs then save them to S3
    #   - kick off some other aws process after testing if the run was sucessful
    #   - etc.
    #
    #   for this example, to keep it simple, i'll just save the body to S3 as a JSON file
    # -------------------------------------------------------------------------------------------
    
    # get the corresponding job name from data
    dbt_cloud_job_name = ((webhook_parsed_payload['data']['jobName']).lower()).replace(' ', '_')
    
    # get the corresponding run id from data
    dbt_cloud_run_id = webhook_parsed_payload['data']['runId']
    
    # create a unique file name for saving to S3
    s3_file_name = f"{dbt_cloud_job_name}__{dbt_cloud_run_id}__output.json"
    
    # converting the webhook dictionary to a JSON string
    webhook_json_data = json.dumps(webhook_parsed_payload)

    # AWS S3 setup
    s3_client = boto3.client('s3')
    s3_bucket_name = 'steve-d-sandbox-bucket'
    s3_folder_name = 'webhook-output-example'

    # Full path where the file will be stored
    s3_file_path = f"{s3_folder_name}/{s3_file_name}"

    # Upload the JSON to S3
    s3_client.put_object(Body=webhook_json_data, Bucket=s3_bucket_name, Key=s3_file_path)
    
    # Return back 200 status
    return {
        'statusCode': 200,
        'body': json.dumps('JSON file successfully saved to S3')
    }