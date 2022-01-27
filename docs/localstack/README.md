# Localstack

[Localstack](https://github.com/localstack/localstack) is "a fully functional local AWS cloud stack." It supports a variety of services, but currently the primary focus is [S3](https://aws.amazon.com/s3/).

## Access via CLI

For more complete instructions, see [the localstack docs](https://github.com/localstack/localstack#accessing-the-infrastructure-via-cli-or-code).

To test/configure the service from your local system, you can use Amazon's `aws` CLI tool, which is a Python package:

    pip install awscli

Run the `configure` command, which will set up the relevant settings/credentials in your `~/.aws` folder.

    aws configure --profile default

Suggested settings:

- *AWS Access Key ID* : `test`
- *AWS Secret Access Key* : `test`
- *Default region name* : `us-west-1`
- *Default output format* : leave blank

Then you should be able to run commands. Be sure to specify your local endpoint!

    # Create a new S3 bucket
    aws --endpoint-url=http://localhost:4566 s3 mb s3://mybucket
    # Copy the contents of a local directory to it
    aws --endpoint-url=http://localhost:4566 s3 cp ./my-s3-data s3://mybucket --recursive
    