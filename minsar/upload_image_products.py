import os
import boto3
import botocore

def upload_to_s3(products_directory):

    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

    if S3_ACCESS_KEY is None or S3_SECRET_KEY is None or S3_BUCKET_NAME is None:
        return

    s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)

    products = os.listdir(products_directory)

    print(products)

    for f in products:
        #f = os.path.abspath(f)
        #print(f)
        s3.upload_file(os.path.join(products_directory, f), S3_BUCKET_NAME, f)
        print("{} has been succesfully uploaded to {}".format(f, S3_BUCKET_NAME))
