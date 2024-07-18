import argparse
import boto3
import datetime
import traceback
from logbook import Logger
from logbook.more import colorize
import logbook

logbook.set_datetime_format("local")
log = Logger("")

# TODO make this "None" when done testing. Maybe move to a config file. 
default_number_deployments_to_keep = 2
default_delete_older_than_days = None
kept_deployments_minimum = 1
kept_deployments_minimum_calculated = max(default_number_deployments_to_keep, kept_deployments_minimum)
default_bucket_name = "localstack-test-bucket"

def validate_args(number_deployments_to_keep, delete_older_than_days):
    if number_deployments_to_keep < kept_deployments_minimum:
        raise ValueError(f"number_deployments_to_keep must be greater than or equal to {kept_deployments_minimum}.")
    if delete_older_than_days and delete_older_than_days < 0:
        raise ValueError("delete_older_than_days must be a positive integer.")
    pass

def connect_to_s3():
    endpoint_url = "http://localhost.localstack.cloud:4566"
    client = boto3.client('s3', endpoint_url=endpoint_url)
    return client

def list_s3_bucket_prefixes(s3_client, bucket_name):
    deployment_directories = []
    paginator = s3_client.get_paginator('list_objects')
    result = paginator.paginate(Bucket=bucket_name, Delimiter='/')
    for prefix in result.search('CommonPrefixes'):
        deployment_directories.append(prefix.get('Prefix'))
    if len(deployment_directories) < kept_deployments_minimum_calculated:
        log.error(colorize("red",f"Only {len(deployment_directories)} deployments found. Cannot meet minimum requirement of {kept_deployments_minimum_calculated}."))
        raise Exception
    return deployment_directories
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
    # If delete_older_than_days is passed, we need to calculate the expiration date
    if delete_older_than_days and number_deployments_to_keep:
        expiration_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=delete_older_than_days)
        print(f"Expiration date: {expiration_date}")
        # Extract deployments newer than the expiration date
        deployments_newer_than_expiration_date = [deployment for deployment in deployments_sorted_by_creation if deployment['LastModified'] > expiration_date]
        # If there aren't enough matching deployments, keep the higher of the provided minimum or hardcoded minimum
        log.info(colorize("blue",f"Provided minimum deployments to keep: {number_deployments_to_keep}."))
        log.info(colorize("blue",f"Hardcoded minimum deployments to keep: {kept_deployments_minimum}."))
        log.info(colorize("blue",f"Larger of the two: {kept_deployments_minimum_calculated}."))
        if len(deployments_newer_than_expiration_date) < kept_deployments_minimum_calculated:
            log.warn(colorize("yellow",f"Warning: Not enough deployments to meet minimum. Keeping {kept_deployments_minimum_calculated} deployments."))
            deployments_to_keep_temp = deployments_sorted_by_creation[-kept_deployments_minimum_calculated:]
        else:
            deployments_to_keep_temp = deployments_newer_than_expiration_date
    elif number_deployments_to_keep:
        deployments_to_keep_temp = deployments_sorted_by_creation[-number_deployments_to_keep:]
    else:
        log.error("Could not determine deployments to keep. Something went wrong.")
        raise Exception
    deployments_to_keep_temp = [deployment['Key'].split('/')[0] + '/' for deployment in deployments_sorted_by_creation]
    log.info(f"Deployments to keep: {len(deployments_to_keep_temp)}")
    return deployments_to_keep_temp

def parse_deployments_to_delete(deployments, deployments_to_keep):
    deployments_to_delete = []
    for deployment in deployments:
        if deployment not in deployments_to_keep:
            deployments_to_delete.append(deployment)
    log.info(f"Deployments to delete: {len(deployments_to_delete)}")
    return deployments_to_delete

def parse_objects_to_delete(s3_client, deployments_to_delete):
    objects_to_delete = []
    for deployment in deployments_to_delete:
        response = s3_client.list_objects_v2(Bucket=default_bucket_name, Prefix=deployment)
        for object in response['Contents']:
            objects_to_delete.append({'Key': object['Key']})
    if objects_to_delete:
        return objects_to_delete
    else:
        raise Exception("No objects to delete.")

def delete_deployment_objects(s3_client, objects_to_delete):
    log.info(f"Total objects to delete: {len(objects_to_delete)}")
    log.info(colorize("blue","Deleting objects. This may take some time."))
    try: 
        s3_client.delete_objects(Bucket=default_bucket_name, Delete={'Objects': objects_to_delete})
    except Exception as e:
        log.error(f"Error deleting objects: {e}")
        raise Exception
    log.info("Objects deleted.")

def log_summary(deployments, deployments_to_keep, deployments_to_delete, objects_to_delete):
    log.info("Summary:")
    log.info(f"Total deployments at start: {len(deployments)}")
    log.info(f"Deployments kept: {len(deployments_to_keep)}")
    log.info(f"Deployments deleted: {len(deployments_to_delete)}. Total objects deleted: {len(objects_to_delete)}")

def main(number_deployments_to_keep, delete_older_than_days):
    try:
        validate_args(number_deployments_to_keep, delete_older_than_days)
        s3_client = connect_to_s3()
        deployments = list_s3_bucket_prefixes(s3_client, default_bucket_name)
        deployments_sorted_by_creation = determine_prefix_dates(s3_client, deployments)
        deployments_to_keep = parse_deployments_to_keep(deployments_sorted_by_creation, number_deployments_to_keep, delete_older_than_days)
        deployments_to_delete = parse_deployments_to_delete(deployments, deployments_to_keep)
        objects_to_delete = parse_objects_to_delete(s3_client, deployments_to_delete)
        delete_deployment_objects(s3_client, objects_to_delete)
        log_summary(deployments, deployments_to_keep, deployments_to_delete, objects_to_delete)
    except Exception as e: 
        print(traceback.format_exc())
        log.error(f"We got a problem here: {e}")

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
# TODO: Verify what's being deleted. I think this is wrong. 
# TODO: add log statements to describe process
# TODO: add error handling
# TODO: support "delete_older_than_days" 
# TODO: add tests, CI, etc 

# Improvements Roadmap 
# Making more AWS calls than I need to. 
# Find a more elegant way to determine deployment date than just choosing the most recent object on a prefix. Right now "deployments_sorted_by_creation" is kind of a misnomer. 
# Add logging / error handling
# separate out the functions into a class
# trim imports to just what I need
# add at least one test assertion 