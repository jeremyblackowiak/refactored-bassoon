import argparse
import boto3

default_deployments_to_keep = None
default_delete_older_than_days = None


def connect_to_s3():
    endpoint_url = "http://localhost.localstack.cloud:4566"
    client = boto3.client('s3', endpoint_url=endpoint_url)
    return client
    result = client.list_buckets()
    print(result)
    pass

def list_s3_bucket_contents(s3_client, bucket_name):
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    print(response)
    pass


def main(deployments_to_keep, delete_older_than_days):
    s3_client = connect_to_s3()
    list_s3_bucket_contents(s3_client, "localstack-test-bucket")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process my inputs!')
    parser.add_argument('--deployments_to_keep', type=int, help='The number of most recent deploys to keep. Any deployments older than these will be deleted.', default=default_deployments_to_keep)
    parser.add_argument('--delete_older_than_days', type=int, help='The age in days of deploys to keep. Any deployments older than this value will be deleted. If you also pass deployments_to_keep, at least that number will be retained, even if older than this argument value.', default=default_delete_older_than_days)
  
    args = parser.parse_args()
    main(args.deployments_to_keep, args.delete_older_than_days)

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
        # poetry run awslocal s3api put-object --bucket localstack-test-bucket --key deployment1/test.txt
            # TODO use source example data in the right structure and just copy that in. Can I mock up the date values I need? 
# How to handle aws auth in CI?