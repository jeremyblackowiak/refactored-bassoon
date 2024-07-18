# refactored-bassoon

# s3-cleanup

Welcome to `s3-cleanup`! This project demonstrates a method for deleting S3 objects. 

The project assumes your target bucket has objects in the following format, where the top-level prefix represents a deployment directory:

```
s3-bucket-name
	deployhash112/
		index.html
		/css/
			font.css
		/images/
			hey.png 
	dsfsfsl9074/
		root.html
		/styles/
			font.css
		/img/
			hey.png 
	delkjlkploy3/
		base.html
		/fonts/
			font.css
		/png/
			hey.png 
	dsfff1234321/...
	klljkjkl123/...
```

The script takes an input of `{x}` "deployments" to keep and deletes the rest. It also takes a `{Y}` input for the number of days, deleting any deployments older than that value while respecting a minimum number of deployments to keep.

## Overview

### Tools Used

- **ASDF:** Toolchain installation management.
- **Poetry:** Package and virtual environment management. 
- **Python:** Everyone's best friend.
- **LocalStack:** For testing.

### What I'd Do With More Time

- Add an optional "--check" flag to determine what would be deleted without taking any write actions.
- Add unit tests. 
- Automate LocalStack setup, authentication creation, bucket creation, and data creation. 
- Create a GitHub Actions workflow for invoking the script.
- Handle AWS authentication in a more sophisticated way than just asking the user to have their keys set as environment variables.
- Reduce the number of AWS API calls by optimizing the code.
- Find a more elegant way to determine the deployment date than just choosing an object with the most recent "LastModified" date under a given prefix. 
- Trim imports to only include what is necessary.

## Prerequisites

Before you begin, ensure you have the following:

- **AWS Account:** 
  - **S3 Bucket:** With files you want to delete.
  - **Access Keys:** For reading and deleting S3 objects.

- **Local Machine:** A *nix machine with Docker for Desktop or Rancher installed, if running locally.

- **ASDF:** Installed. Follow the instructions on the [ASDF GitHub page](https://github.com/asdf-vm/asdf) to install it.

## First Time Setup, Metadata, and Infrastructure

### Basic Setup

1. **Clone the repository**

   Use your preferred method to clone the repository to your local machine.

2. From the directory root, run `asdf install`.

3. Run `poetry install` 

4. In `s3-cleanup/config.py`, update `bucket_name` to the bucket you'd like to target. Optionally, update `kept_deployments_minimum` to your desired number of deployments to keep, regardless of what a user passes as a script input at runtime. 

5. Make sure your AWS key values are set as environment variables in your shell session. Refer to the [AWS CLI documentation](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html#envvars-set) for more information.

6. Run `poetry run python s3-cleanup/main.py --number_deployments_to_keep {X}`, where `{X}` is the number of most recently created deployments you'd like to keep. The rest will be deleted.

7. To delete any deployments older than `{Y}` days, run `poetry run python s3-cleanup/main.py --number_deployments_to_keep {X} --delete_older_than_days {Y}`. The script will delete all deployments older than `{Y}` days, while ensuring that the bucket retains the specified `number_deployments_to_keep`. If deleting deployments older than `{Y}` days would violate `number_deployments_to_keep`, the script will only delete deployments older than the last `number_deployments_to_keep` specified.

### Running with LocalStack

1. Perform steps 1-3 above.
2. Run `poetry run localstack start -d`
3. Run `poetry run awslocal s3 mb s3://localstack-test-bucket`
4. Run `poetry run awslocal iam create-user --user-name test`
5. Run `poetry run awslocal iam create-access-key --user-name test`. In the output, you will find the access keys that you can set as described in step 5 above. 
6. Run `poetry run awslocal s3 sync s3-cleanup/example_data/ s3://localstack-test-bucket` to seed test data.
7. In `s3-cleanup/config.py`, update `bucket_name` to `localstack-test-bucket`, or whatever you named your bucket. Optionally, update `kept_deployments_minimum` to your desired number of deployments to keep, regardless of what a user passes as a script input at runtime. Uncomment the `default_s3_endpoint_url` line pointing to LocalStack.
8. Run steps 6 or 7 as desired.

