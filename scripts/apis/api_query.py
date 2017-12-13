import asyncio
from asyncio import CancelledError
import aiohttp
import logging
import json
from aiohttp import ClientSession
from aiohttp import ClientError, ClientResponseError
from apis import sources, Emotions, GoogleAPI, KairosAPI, FaceplusAPI, AzureAPI

from pathlib import Path
import csv
import glob
import os

# setting up logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(message)s"
)
errlogger = logging.getLogger('err')
hdlr = logging.FileHandler('errors.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
errlogger.addHandler(hdlr)
errlogger.setLevel(logging.WARNING)

apis = [AzureAPI]
# get image names
links = [os.path.basename(f) for f in glob.glob('img\*.jpg')]

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
            
            logging.debug('Consuming: {}.jpg | API: {} | queue size: {}'.format(id, api.source, str(queue.qsize())))

            # set post or get http method
            if api.request_method == 'post':
                ses = session.post
            else:
                ses = session.get

            # to send a json object I could use json=api.request_data() so I wouldn't need to use json.dumps() (see GoogleAPI)
            async with ses(api.url, data=api.request_data(), timeout=50, headers=api.headers()) as response:
                logging.debug('Waiting for API response: {}.jpg | {}'.format(id, api.source))

                # raise error if the response status is >400 (error)
                response.raise_for_status()

                # wait for the response from the api
                res = await response.json()
                # extract emotions from the json response
                emotions_raw = api.std_output(res, id)
                # convert above response in a common format
                id, source, emotions = emotions_raw.formatted_output()

                logging.debug('Got response for {}.jpg | {}: {}'.format(id, api.source, json.dumps(emotions)))

                # append result to csv file (which should already exist with the appropriate headers)
                with open(source+'.csv', 'a', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(list(emotions.values()))
                    logging.debug('Results for {}.jpg | {} written to file'.format(id, api.source))
                
                logging.debug('{} API consumer sleeps for {}s'.format(api.source, api.sleep))
                await asyncio.sleep(api.sleep)
                queue.task_done()

            logging.debug('Task {}.jpg | {} completed'.format(id, api.source))
        except (ClientResponseError, asyncio.TimeoutError) as e:
            # handle specific errors
            logging.debug('Response error on: {} | {}'.format(id, api.source))
            logging.debug(e)

            errlogger.error('Response error on: {} | {} | {}'.format(id, api.source, e))

            # TODO: we could put the task in the dlq, so other consumers wil handle it
            # logging.debug("Problem with {}, Moving to DLQ. main_queue: ({}))".format(item, str(queue.qsize())))            
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
            logging.debug('There was an error on: {} | {}'.format(id, api.source))
            logging.debug(e)

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
    e = Emotions()
    id, source, o = e.formatted_output()
    for api in sources.values():
        with open(api+'.csv', 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(list(o.keys()))

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

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()