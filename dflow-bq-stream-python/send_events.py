import argparse
import random
import datetime
import time
import googleapiclient.discovery
import json

from google.cloud import pubsub_v1 as pubsub
from google.oauth2 import service_account

# all transactions will occur in these zip codes
ZIPS = ["95136", "95126", "95404", "94929"]

# handle command-line arguments
# must provide project_id
# can specify values for topic, sub, and service account
parser = argparse.ArgumentParser()
parser.add_argument(
    "--project_id",
    required=True)
parser.add_argument(
    "--topic_id",
    default="demo_topic")
parser.add_argument(
    "--sub_id",
    default="demo_sub")

known_args, extra_args = parser.parse_known_args()

# create the topic in the specified project
publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path(known_args.project_id, known_args.topic_id)
topic_list = publisher.list_topics(project=f"projects/{known_args.project_id}")
if (next((True for x in topic_list if topic_path == x.name), False)):
    topic = publisher.get_topic(topic_path)
else:
    topic = publisher.create_topic(topic_path)

# create the sub in the specified project
subscriber = pubsub.SubscriberClient()
sub_path = subscriber.subscription_path(known_args.project_id, known_args.sub_id)
sub_list = subscriber.list_subscriptions(project=f"projects/{known_args.project_id}")
if (next((True for x in sub_list if sub_path == x.name), False)):
    sub = subscriber.get_subscription(sub_path)
else:
    subscriber.create_subscription(name=sub_path, topic=topic_path)

# send a message every second
while True:
    time.sleep(1)
    pos_id = random.randint(1,9) # there are 10 pos terminals
    timestamp = datetime.datetime.now().isoformat() 
    zip_code = ZIPS[random.randint(0,3)]
    amount =  round(random.uniform(1.00, 1000.0),2)
    body_dict = {"pos_id": pos_id,
        "ts": timestamp,
        "zip": zip_code,
        "sale_amount": amount}
    body = json.dumps(body_dict).encode("utf-8") # create a byte array
    future = publisher.publish(topic_path, body)
    message_id = future.result()
    print("Message published")
    print(f"  - ID:   {message_id}")
    print(f"  - BODY: {body}")