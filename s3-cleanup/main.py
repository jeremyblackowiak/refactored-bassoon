import argparse
import boto3

default_number_deployments_to_keep = 2
default_delete_older_than_days = None
default_bucket_name = "localstack-test-bucket"

def connect_to_s3():
    endpoint_url = "http://localhost.localstack.cloud:4566"
    client = boto3.client('s3', endpoint_url=endpoint_url)
    return client
    result = client.list_buckets()
    print(result)
    pass

def list_s3_bucket_prefixes(s3_client, bucket_name):
    top_level_directories = []
    paginator = s3_client.get_paginator('list_objects')
    result = paginator.paginate(Bucket=bucket_name, Delimiter='/')
    for prefix in result.search('CommonPrefixes'):
        top_level_directories.append(prefix.get('Prefix'))
    # print(top_level_directories)
    return top_level_directories
    # response = s3_client.list_objects_v2(Bucket=bucket_name)
    # call_contents = response.get('Contents', [])
    # print(call_contents)
    # return call_contents

def determine_prefix_dates(s3_client, deployments):
    deployments_enriched_with_dates = []
    for deployment in deployments:
        deployment_objects_call = s3_client.list_objects_v2(Bucket=default_bucket_name, Prefix=deployment)
        # Find the most recently modified object? Idk
        deployment_objects_contents = deployment_objects_call.get('Contents', [])
        # This sorts by last modified. But what's the actual sort order? Need to confirm. 
        sorted_deployments = sorted(deployment_objects_contents, key=lambda x: x['LastModified'])
        # Grabbing last item in the list, aka the most recent
        deployments_enriched_with_dates.append(sorted_deployments[-1])
    # this is a list of dicts. each dict is a representative object for a given prefix. 
    # it would probably be cleaner to create a dict with values "deployment" and "calculated_last_modified" 
    # I'm also sorting the final list for the rest of the script 
    deployments_enriched_with_dates = sorted(deployments_enriched_with_dates, key=lambda x: x['LastModified'])
    return deployments_enriched_with_dates

def parse_deployments_to_keep(deployments_sorted_by_creation, number_deployments_to_keep, delete_older_than_days):
    deployments_to_keep = []
    deployments_to_keep.append(deployments_sorted_by_creation[-number_deployments_to_keep:])
    deployments_to_keep_keys = [deployment['Key'].split('/')[0] for deployment in deployments_to_keep]
    return deployments_to_keep_keys

def parse_deployments_to_delete(s3_client, deployments, deployments_to_keep):
    deployments_to_delete = []
    for deployment in deployments:
        if deployment not in deployments_to_keep:
            deployments_to_delete.append(deployment)
    return deployments_to_delete

def delete_deployment_objects(s3_client, deployments_to_delete):
    objects_to_delete = []
    for deployment in deployments_to_delete:
        response = s3_client.list_objects_v2(Bucket=default_bucket_name, Prefix=deployment)
        for object in response['Contents']:
            objects_to_delete.append({'Key': object['Key']})
    if objects_to_delete:
        response = s3_client.delete_objects(Bucket=default_bucket_name, Delete={'Objects': objects_to_delete})
        print(response)

def main(number_deployments_to_keep, delete_older_than_days):
    s3_client = connect_to_s3()
    deployments = list_s3_bucket_prefixes(s3_client, default_bucket_name)
    deployments_sorted_by_creation = determine_prefix_dates(s3_client, deployments)
    deployments_to_keep = parse_deployments_to_keep(deployments_sorted_by_creation, number_deployments_to_keep, delete_older_than_days)
    deployments_to_delete = parse_deployments_to_delete(s3_client, deployments, deployments_to_keep)
    delete_deployment_objects(s3_client, deployments_to_delete)
    # delete_expired_deployments(deployments_to_delete)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process my inputs!')
    parser.add_argument('--number_deployments_to_keep', type=int, help='The number of most recent deploys to keep. Any deployments older than these will be deleted.', default=default_number_deployments_to_keep)
    parser.add_argument('--delete_older_than_days', type=int, help='The age in days of deploys to keep. Any deployments older than this value will be deleted. If you also pass deployments_to_keep, at least that number will be retained, even if older than this argument value.', default=default_delete_older_than_days)
  
    args = parser.parse_args()
    main(args.number_deployments_to_keep, args.delete_older_than_days)

## pseudo code for functions
# create s3 client
# get list of bucket contents
# sort deployments keys by date created
# determine which deployments to keep using args and filter logic 

## Notes / doodles
# How separated should the exercise's primary delete function + the bonus instruction be? Same script, different functions? Different scripts?
# How to orchestrate usage of localstack for local dev? For CI? Could use NX. Needs to boot it, then create the creds, create the bucket, then create the data.
    # localstack cmds for now
        # poetry run awslocal iam create-user --user-name test
        # poetry run awslocal iam create-access-key --user-name test
            # place as env vars
        # poetry run awslocal s3 mb s3://localstack-test-bucket
        # poetry run awslocal s3 sync s3-cleanup/example_data/ s3://localstack-test-bucket
# How to handle aws auth in CI?
# Current issue I'm thinking about is how to decide what is the canonical "date" for a "directory" of objects. s3 doesn't actually have directories, just has objects with prefixes. 
# I can take the last modified date of the most recently modified object in a "directory" as the "date" of the "directory".