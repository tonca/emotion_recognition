import asyncio
from asyncio import CancelledError
import aiohttp
import logging
import json
from aiohttp import ClientSession
from aiohttp import ClientError, ClientResponseError
from api_structure import sources, Emotions, GoogleAPI, KairosAPI, FaceplusAPI, AzureAPI, AmazonAPI
from api_keys import amazon
import boto3
import multiprocessing
from itertools import repeat
import sys

from pathlib import Path
import csv
import glob
import os

# setting up logger
log = logging.getLogger('std')
shdlr = logging.StreamHandler()
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
shdlr.setFormatter(formatter)
log.addHandler(shdlr)

# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s:%(message)s"
# )
errlogger = logging.getLogger('err')
hdlr = logging.FileHandler('errors.log')
hdlr.setFormatter(formatter)
errlogger.addHandler(hdlr)
errlogger.setLevel(logging.WARNING)

apis = [AzureAPI]

# save output to json and csv format
def save_output(json_res, csv_res, id, source):
    # save raw json
    with open('o_json/{}_{}.json'.format(id, source), 'w') as json_file:
        json.dump(json_res, json_file)
    # append formatted result to csv file (which should already exist with the appropriate headers)
    # with open('o_csv/' + source + '.csv', 'a', newline='') as csv_file:
    with open('o_csv/out.csv', 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(csv_res)
    log.debug('Results for {}.jpg | {} written to file'.format(id, source))


# producer, creates tasks and put into respective queues
async def produce(queue, itr_items):
    for i, q in enumerate(queue):
        for item in itr_items:
            await q.put([item, apis[i]])

# consumes queue tasks
async def consume(queue, session):
    while True:
        try:
            # get first item in queue
            image, Api_Class = await queue.get()

            # create the class
            api = Api_Class(image)
            id = image.replace('.jpg', '')
            
            log.debug('Consuming: {}.jpg | API: {} | queue size: {}'.format(id, api.source, str(queue.qsize())))

            # set post or get http method
            if api.request_method == 'post':
                ses = session.post
            else:
                ses = session.get

            # to send a json object I could use json=api.request_data() so I wouldn't need to use json.dumps() (see GoogleAPI)
            async with ses(api.url, data=api.request_data(), timeout=50, headers=api.headers()) as response:
                log.debug('Waiting for API response: {}.jpg | {}'.format(id, api.source))

                # raise error if the response status is >400 (error)
                response.raise_for_status()

                # wait for the response from the api
                res = await response.json()
                # extract emotions from the json response
                emotions_raw = api.std_output(res, id)
                # convert above response in a common format
                id, source, emotions = emotions_raw.formatted_output()

                log.debug('Got response for {}.jpg | {}: {}'.format(id, api.source, json.dumps(emotions)))

                # save output to csv and json
                save_output(res, list(emotions.values()), id, api.source)
                
                log.debug('{} API consumer sleeps for {}s'.format(api.source, api.sleep))
                await asyncio.sleep(api.sleep)
                queue.task_done()

            log.debug('Task {}.jpg | {} completed'.format(id, api.source))
        except (ClientResponseError, asyncio.TimeoutError) as e:
            # handle specific errors
            log.debug('Response error on: {} | {}'.format(id, api.source))
            log.debug(e)

            errlogger.error('Response error on: {} | {} | {}'.format(id, api.source, e))

            # TODO: we could put the task in the dlq, so other consumers wil handle it
            # log.debug("Problem with {}, Moving to DLQ. main_queue: ({}))".format(item, str(queue.qsize())))            
            # await dlq.put(url)
            # lower the pace
            # asyncio.sleep(5)

            queue.task_done()
            break
        except CancelledError as e:
            # this gets called everytime a queue finishes
            break
        except Exception as e:
            # generic error
            # TODO: fix this problem
            # when an exception is thrown the current queue hangs althous queue is defined and apparently task_done() gets called)
            queue.task_done()
            log.debug('There was an error on: {} | {}'.format(id, api.source))
            log.debug(e)

            errlogger.error('There was an error on {} | {}: {}'.format(id, api.source, e))
            break

async def run():
    # generate a queue for each API
    queues = []
    for q in apis:
        queues.append(asyncio.Queue(maxsize=10))
    # queue, kai, google = , asyncio.Queue(maxsize=10), asyncio.Queue(maxsize=10)

    # TODO: eventually use a semaphore to limit concurrent requests
    # sem = asyncio.Semaphore(10)

    # create csv files
    # e = Emotions()
    # id, source, o = e.formatted_output()
    # for api in sources.values():
    #      with open('o_csv\\' + api + '.csv', 'w', newline='') as csv_file:
    #         writer = csv.writer(csv_file)
    #         writer.writerow(list(o.keys()))

    async with ClientSession() as session:
        # create consumers
        consumers = []
        for q in queues:
            # TODO: custom ranges (google = 8)
            consumers.append(
                [asyncio.ensure_future(consume(q, session)) for _ in range(1)]
            )
        # consumers     = [asyncio.ensure_future(consume(queue, session)) for _ in range(1)]
        # kai_cons     = [asyncio.ensure_future(consume(kai, session)) for _ in range(1)]
        # google_cons     = [asyncio.ensure_future(consume(google, session)) for _ in range(8)]
        # dlq_consumers = [asyncio.ensure_future(consume(dlq, dlq, session)) for _ in range(1)]

        # set up producer
        producer = await produce(queues, links)

        # wait for queues to finish
        for q in queues:
            await q.join()
        # await kai.join()
        # await google.join()
        # await dlq.join()

        # terminate all pending tasks
        for consumer_array in consumers:
            for c in consumer_array:
                c.cancel()
        # return responses

# ask client if using amazon api and if images should be uploaded
def send_to_amz(filepath, upload = False):
    filename = os.path.basename(filepath)
    s3_client = boto3.client(
        's3',
        aws_access_key_id = amazon['id'],
        aws_secret_access_key = amazon['key']
    )
    if upload:
        # upload if needed
        log.debug('Uploading {} to amz'.format(filepath))
        s3_client.upload_file(filepath, amazon['bucket_name'], filename)
    
    # send the image to amz Rekognition
    client=boto3.client(
        'rekognition',
        region_name=amazon['region_name'],
        aws_access_key_id=amazon['id'],
        aws_secret_access_key=amazon['key']
    )
    response = client.detect_faces(
        Image={'S3Object':{'Bucket':amazon['bucket_name'],'Name':filename}},
        Attributes=['ALL']
    )
    print('got response from amazon')
    res = AmazonAPI(response, filename.replace('.jpg', ''))
    # save output to file
    id, source, emotions = res.formatted_output()
    save_output(response, list(emotions.values()), filename.replace('.jpg', ''), sources['amz'])

if __name__ == '__main__':
    # delete all output files
    out_dir = ['o_csv', 'o_json']
    for d in out_dir:
        fileList = os.listdir(d)
        for f in fileList:
            os.remove(d + '/' + f)

    # get image names
    imgs = glob.glob('img/*.jpg')
    # removing path from image name
    links = [os.path.basename(f) for f in glob.glob('img/*.jpg')]

    # create initial csv files
    e = Emotions()
    id, source, o = e.formatted_output()
    # for api in sources.values():
    #     with open('o_csv/' + api + '.csv', 'w', newline='') as csv_file:
    #         writer = csv.writer(csv_file)
    #         writer.writerow(list(o.keys()))
    with open('o_csv/out.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(list(o.keys()))

    # check if using Amazon too, which requires an independent routine
    using_amz = input('Using Amazon Rekognition too? [y,n]') == 'y'
    if using_amz:
        # check if images should be uploaded
        should_upload = input('Should images in /img folder be uplaoded to the {} bucket? [y,n]'.format(amazon['bucket_name'])) == 'y'
        if should_upload:
            # delete all previous images
            bucket = boto3.resource(
                's3',
                aws_access_key_id = amazon['id'],
                aws_secret_access_key = amazon['key']
            ).Bucket(amazon['bucket_name'])
            bucket.objects.all().delete()
        
        # start jobs
        # builtin_outputs = map(send_to_amz, list_of_inputs)
        pool_size = multiprocessing.cpu_count()
        # pool = multiprocessing.Pool(
        #     processes = pool_size
        # )
        # 
        # pool_outputs = pool.map(send_to_amz, list_of_inputs)
        with multiprocessing.Pool(processes = pool_size) as pool:
            pool.starmap(send_to_amz, zip(imgs, repeat(should_upload)))
        # pool.close()
        # pool.join()
        log.debug('[AMAZON] - queue task completed')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()