import csv
import io
import logging
import os


import boto3
from botocore.config import Config

REGION = os.environ['AWS_REGION']

BUCKET = os.environ['BUCKET']
MINIFIGURE_FILE_NAME = os.environ['MF_FILE']

LEFT_BRACKET = '&#40;'
RIGHT_BRACKET = '&#41;'


def minifigure_search_request(search_str: str):
    logging.info("[s3client] Initializing Minifigure Search Request for keyword: {}".format(search_str))
    result_dict = list()
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
                result_dict.append({
                                        'num': row['code'],
                                        'name': row['name'],
                                        'year': row['year']
                                    })

        s3.close()
        logging.info("[s3client] Search for \"" + search_str + '" successful with number of results: ' + str(len(result_dict)))
    except Exception as e:
        logging.error("[s3client] Error reading CSV from AWS S3")
        logging.error(e)
    return result_dict


def write_minifigs_to_file(data_dict):
    # creating a file buffer
    file_buff = io.StringIO()
    # writing csv data to file buffer
    fig_writer = csv.writer(file_buff, dialect='excel')
    fig_writer.writerow(['code', 'name', 'year'])
    for code, item in data_dict.items():
        fig_writer.writerow([code, item['name'].replace(LEFT_BRACKET, '(').replace(RIGHT_BRACKET, ')'), item['year']])

    # creating s3 client connection
    client = boto3.client('s3')
    # placing file to S3, file_buff.getvalue() is the CSV body for the file
    client.put_object(Body=file_buff.getvalue(), Bucket=BUCKET, Key=MINIFIGURE_FILE_NAME)

