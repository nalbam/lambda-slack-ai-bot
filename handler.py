import boto3
import datetime
import json
import os
import re
import sys
import time
import base64
import requests

from retry import retry

from openai import OpenAI

from slack_bolt import App, Say
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

BOT_CURSOR = os.environ.get("BOT_CURSOR", ":robot_face:")

# Set up ChatGPT API credentials
OPENAI_ORG_ID = os.environ["OPENAI_ORG_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "dall-e-3")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x1024")
IMAGE_QUALITY = os.environ.get("IMAGE_QUALITY", "standard")

# Set up Slack API credentials
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# Set up System messages
SYSTEM_MESSAGE = os.environ.get("SYSTEM_MESSAGE", "")

TEMPERATURE = float(os.environ.get("TEMPERATURE", 0))

MESSAGE_MAX = int(os.environ.get("MESSAGE_MAX", 4000))

# Initialize Slack app
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    process_before_response=True,
)

bot_id = app.client.api_call("auth.test")["user_id"]

# Initialize OpenAI
openai = OpenAI(
    organization=OPENAI_ORG_ID,
    api_key=OPENAI_API_KEY,
)

# Keep track of conversation history by thread and user
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "chatgpt-slack-thread")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# OpenAI system message
system_message = {
    "role": "system",
    "content": SYSTEM_MESSAGE,
}


# Get the context from DynamoDB
def get_context(thread_ts, user, default=""):
    if thread_ts is None:
        item = table.get_item(Key={"id": user}).get("Item")
    else:
        item = table.get_item(Key={"id": thread_ts}).get("Item")
    return (item["conversation"]) if item else (default)


# Put the context in DynamoDB
def put_context(thread_ts, user, conversation=""):
    expire_at = int(time.time()) + 3600  # 1h
    expire_dt = datetime.datetime.fromtimestamp(expire_at).isoformat()
    if thread_ts is None:
        table.put_item(
            Item={
                "id": user,
                "conversation": conversation,
                "expire_dt": expire_dt,
                "expire_at": expire_at,
            }
        )
    else:
        table.put_item(
            Item={
                "id": thread_ts,
                "conversation": conversation,
                "expire_dt": expire_dt,
                "expire_at": expire_at,
            }
        )


# Update the message in Slack
def chat_update(channel, message, latest_ts):
    # print("chat_update: {}".format(message))
    app.client.chat_update(channel=channel, text=message, ts=latest_ts)


@retry(tries=3, delay=1, backoff=2, max_delay=4)
def reply(messages, channel, latest_ts, user):
    stream = openai.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        stream=True,
        user=user,
    )

    counter = 0
    message = ""
    for part in stream:
        reply = part.choices[0].delta.content or ""

        if reply:
            message += reply

        if counter % 16 == 1:
            chat_update(channel, message + " " + BOT_CURSOR, latest_ts)

        counter = counter + 1

    chat_update(channel, message, latest_ts)

    return message


# Handle the chatgpt conversation
def conversation(say: Say, thread_ts, content, channel, user, client_msg_id):
    print("conversation: {}".format(json.dumps(content)))

    # Keep track of the latest message timestamp
    result = say(text=BOT_CURSOR, thread_ts=thread_ts)
    latest_ts = result["ts"]

    messages = []

    messages.append(
        {
            "role": "user",
            "content": content,
        },
    )

    if thread_ts != None:
        # Get thread messages using conversations.replies API method
        response = app.client.conversations_replies(channel=channel, ts=thread_ts)

        print("conversations_replies: {}".format(response))

        if not response.get("ok"):
            print("Failed to retrieve thread messages.")

        res_messages = response.get("messages", [])
        res_messages.reverse()
        res_messages.pop(0)  # remove the first message

        for message in res_messages:
            if message.get("client_msg_id", "") == client_msg_id:
                continue

            role = "user"
            if message.get("bot_id", "") != "":
                role = "assistant"

            messages.append(
                {
                    "role": role,
                    "content": message.get("text", ""),
                }
            )

            # print("conversation: messages size: {}".format(sys.getsizeof(messages)))

            if sys.getsizeof(messages) > MESSAGE_MAX:
                messages.pop(0)  # remove the oldest message
                break

    messages.append(system_message)

    try:
        messages = messages[::-1]  # reversed

        print("conversation: {}".format(json.dumps(messages)))

        # Send the prompt to ChatGPT
        message = reply(messages, channel, latest_ts, user)

        print("conversation: {}".format(message))

        # if message != "":
        #     messages.append({"role": "assistant", "content": message})
        #     put_context(thread_ts, user, json.dumps(messages))

    except Exception as e:
        print("conversation: Error handling message: {}".format(e))
        print("conversation: OpenAI Model: {}".format(OPENAI_MODEL))

        message = f"Error: ```{e}```"

        # say(text=message, thread_ts=thread_ts)
        chat_update(channel, message, latest_ts)


def image_url_to_base64(image_url):
    response = requests.get(
        image_url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    )

    encoded_image = None

    if response.status_code == 200:
        encoded_image = base64.b64encode(response.content).decode("utf-8")
    else:
        print("Failed to fetch image: {}".format(image_url))

    return encoded_image


def content_from_message(prompt, event):
    content = []
    content.append({"type": "text", "text": prompt})

    if "files" in event:
        files = event.get("files", [])
        for file in files:
            mimetype = file["mimetype"]
            if mimetype.startswith("image"):
                image_url = file.get("url_private")
                base64_image = image_url_to_base64(image_url)
                if base64_image:
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                # "url": image_url,
                                "url": f"data:{mimetype};base64,{base64_image}"
                            },
                        }
                    )

    return content


# Handle the app_mention event
@app.event("app_mention")
def handle_mention(body: dict, say: Say):
    print("handle_mention: {}".format(body))

    event = body["event"]

    if "bot_id" in event:  # Ignore messages from the bot itself
        return

    thread_ts = event["thread_ts"] if "thread_ts" in event else event["ts"]
    prompt = re.sub(f"<@{bot_id}>", "", event["text"]).strip()
    channel = event["channel"]
    user = event["user"]
    client_msg_id = event["client_msg_id"]

    content = content_from_message(prompt, event)

    conversation(say, thread_ts, content, channel, user, client_msg_id)


# Handle the DM (direct message) event
@app.event("message")
def handle_message(body: dict, say: Say):
    print("handle_message: {}".format(body))

    event = body["event"]

    if "bot_id" in event:  # Ignore messages from the bot itself
        return

    prompt = event["text"].strip()
    channel = event["channel"]
    user = event["user"]
    client_msg_id = event["client_msg_id"]

    content = content_from_message(prompt, event)

    # Use thread_ts=None for regular messages, and user ID for DMs
    conversation(say, None, content, channel, user, client_msg_id)


# Handle the summary event
@app.event("summarize")
def handle_summary(body: dict, say: Say):
    print("handle_summary: {}".format(body))

    event = body["event"]

    thread_ts = event["thread_ts"] if "thread_ts" in event else event["ts"]
    prompt = "이 대화를 요약해줘."
    channel = event["channel"]
    user = event["user"]
    client_msg_id = event["client_msg_id"]

    content = content_from_message(prompt, event)

    conversation(say, thread_ts, content, channel, user, client_msg_id)


def lambda_handler(event, context):
    body = json.loads(event["body"])

    if "challenge" in body:
        # Respond to the Slack Event Subscription Challenge
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"challenge": body["challenge"]}),
        }

    print("lambda_handler: {}".format(body))

    # Duplicate execution prevention
    if "event" not in body or "client_msg_id" not in body["event"]:
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"status": "Success"}),
        }

    # Get the context from DynamoDB
    token = body["event"]["client_msg_id"]
    prompt = get_context(token, body["event"]["user"])

    if prompt != "":
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"status": "Success"}),
        }

    # Put the context in DynamoDB
    put_context(token, body["event"]["user"], body["event"]["text"])

    # Handle the event
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
