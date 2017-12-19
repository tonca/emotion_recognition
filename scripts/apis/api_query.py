import asyncio
from asyncio import CancelledError
import aiohttp
import logging
import json
from aiohttp import ClientSession, ClientResponseError
from api_structure import sources, Emotions, GoogleAPI, KairosAPI, FaceplusAPI, AzureAPI, AmazonAPI
from api_keys import amazon
import boto3
import multiprocessing
from itertools import repeat
import sys
import csv
import glob
import os

# setting up loggers
log = logging.getLogger('std')
shdlr = logging.StreamHandler()
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
shdlr.setFormatter(formatter)
log.addHandler(shdlr)

errlogger = logging.getLogger('err')
hdlr = logging.FileHandler('errors.log')
hdlr.setFormatter(formatter)
errlogger.addHandler(hdlr)
errlogger.setLevel(logging.WARNING)

# save output to json and csv format
def save_output(json_res, csv_res, image, source):
    # save raw json
    with open('o_json/{}_{}.json'.format(os.path.splitext(image)[0], source), 'w') as json_file:
        json.dump(json_res, json_file)
    # append formatted result to csv file (which should already exist with the appropriate headers)
    # with open('o_csv/' + source + '.csv', 'a', newline='') as csv_file:
    with open('o_csv/out.csv', 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(csv_res)
    log.debug('Results for {} | {} written to file'.format(image, source))


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
            id = os.path.splitext(image)[0]
            
            log.debug('Consuming: {} | API: {} | queue size: {}'.format(image, api.source, str(queue.qsize())))

            # set post or get http method
            if api.request_method == 'post':
                ses = session.post
            else:
                ses = session.get

            # to send a json object I could use json=api.request_data() so I wouldn't need to use json.dumps() (see GoogleAPI)
            async with ses(api.url, data=api.request_data(), timeout=50, headers=api.headers()) as response:
                log.debug('Waiting for API response: {} | {}'.format(image, api.source))

                # raise error if the response status is >400 (error)
                response.raise_for_status()

                # wait for the response from the api
                res = await response.json()
                # extract emotions from the json response
                emotions_raw = api.std_output(res, id)
                # convert above response in a common format
                id, source, emotions = emotions_raw.formatted_output()

                log.debug('Got response for {} | {}: {}'.format(image, api.source, json.dumps(emotions)))

                # save output to csv and json
                save_output(res, list(emotions.values()), image, api.source)
                
                log.debug('{} API consumer sleeps for {}s'.format(api.source, api.sleep))
                await asyncio.sleep(api.sleep)
                queue.task_done()

            log.debug('Task {} | {} completed'.format(image, api.source))
        except (ClientResponseError, asyncio.TimeoutError) as e:
            # handle specific errors
            log.debug('Response error on: {} | {}'.format(image, api.source))
            log.debug(e)

            errlogger.error('Response error on: {} | {} | {}'.format(image, api.source, e))

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
            # when an exception is thrown the current queue hangs although queue is defined and apparently task_done() gets called
            queue.task_done()
            log.debug('There was an error on: {} | {}'.format(id, api.source))
            log.debug(e)

            errlogger.error('There was an error on {} | {}: {}'.format(id, api.source, e))
            break

async def run():
    # generate a queue for each API
    queues = []
    for q in apis:
        queues.append(asyncio.Queue(maxsize=1000))

    # TODO: eventually use a semaphore to limit concurrent requests
    # sem = asyncio.Semaphore(10)

    async with ClientSession() as session:
        # create consumers
        consumers = []
        for q in queues:
            # TODO: custom ranges
            # some APIs are not restricted to a maximum number of simultaneous connections
            # for example Google does not have this restriction, therefore the value in the
            # range could be set to a higher value (eg. 8) to speed up the process
            consumers.append(
                [asyncio.ensure_future(consume(q, session)) for _ in range(1)]
            )

        # set up producer
        producer = await produce(queues, links)

        # wait for queues to finish
        for q in queues:
            await q.join()

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
    res = AmazonAPI(response, os.path.splitext(filename)[0])
    # save output to file
    id, source, emotions = res.formatted_output()
    save_output(response, list(emotions.values()), filename, sources['amz'])

if __name__ == '__main__':
    # all the APIs that are going to be used
    apis = [GoogleAPI, KairosAPI, FaceplusAPI, AzureAPI]

    # ask if this operation is a resume of a previous one
    resume = input('Are you resuming a previous operation? If not, all files in the /o_csv and /o_json will be deleted. [y,n]') == 'y'
    if resume:
        resume_confirm = input('Old files will not be deleted and new results will be appended to the /o_csv/out.csv file. Are you sure?') == 'y'
        if not resume_confirm:
            sys.exit('Script exits since user is not sure on what to do...')
    # delete all output files
    if not resume:
        out_dir = ['o_csv', 'o_json']
        for d in out_dir:
            fileList = os.listdir(d)
            for f in fileList:
                os.remove(d + '/' + f)

    # get image names
    imgs = glob.glob('img/*')
    # removing path from image name
    links = [os.path.basename(f) for f in glob.glob('img/*')]

    # create initial csv files
    e = Emotions()
    id, source, o = e.formatted_output()

    # create initial csv file that will store all results
    if not resume:
        with open('o_csv/out.csv', 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(list(o.keys()))

    # check if using Amazon too, which requires an independent routine
    using_amz = input('Using Amazon Rekognition too? [y,n]') == 'y'
    if using_amz:
        # check if images should be uploaded
        should_upload = input('Should images in /img folder be uploaded to the {} bucket? [y,n]'.format(amazon['bucket_name'])) == 'y'
        if should_upload and not resume:
            # delete all previous images
            bucket = boto3.resource(
                's3',
                aws_access_key_id = amazon['id'],
                aws_secret_access_key = amazon['key']
            ).Bucket(amazon['bucket_name'])
            bucket.objects.all().delete()
        
        # start jobs
        pool_size = multiprocessing.cpu_count()
        with multiprocessing.Pool(processes = pool_size) as pool:
            pool.starmap(send_to_amz, zip(imgs, repeat(should_upload)))
        log.debug('[AMAZON] - queue task completed')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()