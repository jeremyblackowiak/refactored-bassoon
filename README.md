# refactored-bassoon

Welcome to `s3-cleanup`! This project is meant to demonstrate a method for deleting s3 objects . 


## Overview

### Tools Used

- **ASDF:** Toolchain installation management.
- **Poetry:** Package and virtual environment management. 


### What I'd Do With More Time

- Automate localstack testing. 
- Use an AWS role instead of keys
- Making more AWS calls than I need to. 
- Find a more elegant way to determine deployment date than just choosing the most recent object on a prefix. Right now "deployments_sorted_by_creation" is kind of a misnomer. 
- Add logging / error handling
- separate out the functions into a class
- trim imports to just what I need
- add at least one test assertion 
- add a check flag to see what would happen without actually deleting anything



## Prerequisites

## Prerequisites

Before you begin, ensure you have the following:

- **AWS Account:** 
  - **S3 Bucket:** With files you want to delete.
  - **Access Keys:** For reading and deleting S3 objects.

- **Local Machine:** A *nix machine with Docker for Desktop or Rancher installed, if running locally.

- **ASDF:** Installed. Follow the instructions on the [ASDF GitHub page](https://github.com/asdf-vm/asdf) to install it.


## First Time Setup, Metadata and Infrastructure

### Basic Setup

1. **Clone the repository**

   Use your preferred method to clone the repository to your local machine.

2. Run `asdf install`.

3.    # localstack cmds for now
        # poetry run awslocal iam create-user --user-name test
        # poetry run awslocal iam create-access-key --user-name test
            # place as env vars
        # poetry run awslocal s3 mb s3://localstack-test-bucket
        # poetry run awslocal s3 sync s3-cleanup/example_data/ s3://localstack-test-bucket


