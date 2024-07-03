import csv
import io
import logging
import os
import re


import boto3
from botocore.config import Config

REGION = os.environ['AWS_REGION']

BUCKET = os.environ['BUCKET']
MINIFIGURE_FILE_NAME = os.environ['MF_FILE']


def minifigure_search_request(search_str: str):
    logging.info("[s3client] Initializing Minifigure Search Request for keyword: {}".format(search_str))
    result_dict = dict()
    config = Config(
        retries={
            'max_attempts': 0,
            'mode': 'standard'
        }
    )
    try:
        s3 = boto3.client('s3', config=config)

        response = s3.get_object(Bucket=BUCKET, Key=MINIFIGURE_FILE_NAME)
        reader = csv.DictReader(io.StringIO(response['Body'].read().decode('utf-8')))
        search_words = search_str.split(' ')
        for row in reader:
            if all(word.lower() in row["name"].lower() for word in search_words):
                result_dict[row['code']] = row['name']
        s3.close()
        logging.info("[s3client] Search for \"" + search_str + '" successful with number of results: ' + str(len(result_dict)))
    except Exception as e:
        logging.error("[s3client] Error reading CSV from AWS S3")
        logging.error(e)
    return result_dict
