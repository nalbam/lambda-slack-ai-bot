import boto3
import json
import openai
import os

from slack_bolt import App, Say
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

# Set up OpenAI API credentials
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "text-davinci-003")
OPENAI_MAX_TOKENS = int(os.environ.get("OPENAI_MAX_TOKENS", 1024))
OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", 0.5))
OPENAI_CURSOR = os.environ.get("OPENAI_CURSOR", ":robot_face:")

openai.api_key = OPENAI_API_KEY

# Set up Slack API credentials
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# Initialize Slack app
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    process_before_response=True,
)

# Keep track of conversation history by thread
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "openai-slack-bot-history")

dynamodb = boto3.client("dynamodb")


# Get the conversation history for a thread
def get_context(thread_ts):
    response = dynamodb.get_item(
        TableName=DYNAMODB_TABLE_NAME,
        Key={"thread_ts": {"S": thread_ts}},
        ConsistentRead=True,
    )
    item = response.get("Item")
    if item is None:
        conversation = ""
    else:
        conversation = item.get("conversation", {"S": ""}).get("S", "")
    print("get_context {}: {}".format(thread_ts, conversation))
    return conversation


# Update the conversation history for a thread
def put_context(thread_ts, conversation):
    print("put_context {}: {}".format(thread_ts, conversation))
    dynamodb.put_item(
        TableName=DYNAMODB_TABLE_NAME,
        Item={
            "thread_ts": {"S": thread_ts},
            "conversation": {"S": conversation},
        },
    )


# Update the message in Slack
def chat_update(channel, message, latest_ts):
    print("chat_update: {}".format(message))
    app.client.chat_update(
        channel=channel,
        text=message,
        ts=latest_ts,
    )


# Handle the openai conversation
def conversation(thread_ts, prompt, channel, say: Say):
    print(thread_ts, prompt)

    # Keep track of the latest message timestamp
    result = say(text=OPENAI_CURSOR, thread_ts=thread_ts)
    latest_ts = result["ts"]

    # Get conversation history for this thread, if any
    conversation = get_context(thread_ts)

    if conversation == "":
        response = openai.Completion.create(
            # engine="davinci",
            model=OPENAI_MODEL,
            prompt=prompt,
            max_tokens=OPENAI_MAX_TOKENS,
            n=1,
            stop=None,
            temperature=OPENAI_TEMPERATURE,
            stream=True,
        )
        prompt = "User: " + prompt
        message = "\nAnswer: "
    else:
        prompt = "\n\nUser: " + prompt
        message = ""
        response = openai.Completion.create(
            # engine="davinci",
            model=OPENAI_MODEL,
            prompt=conversation + prompt,
            max_tokens=OPENAI_MAX_TOKENS,
            n=1,
            stop=None,
            temperature=OPENAI_TEMPERATURE,
            stream=True,
            presence_penalty=0.6,
            frequency_penalty=0.6,
        )

    # Stream each message in the response to the user in the same thread
    counter = 0
    for completions in response:
        message = message + completions.choices[0].text

        # Send or update the message, depending on whether it's the first or subsequent messages
        if counter % 16 == 10:
            chat_update(channel, message + " " + OPENAI_CURSOR, latest_ts)

            # Update the prompt with the latest message
            put_context(thread_ts, conversation + prompt + "\n" + message)

        counter = counter + 1

    if message != "":
        chat_update(channel, message, latest_ts)

        # Update the prompt with the latest message
        put_context(thread_ts, conversation + prompt + "\n" + message)


# Handle the app_mention event
@app.event("app_mention")
def handle_app_mentions(body: dict, say: Say):
    print("handle_app_mentions: {}".format(body))

    event = body["event"]

    thread_ts = event["thread_ts"] if "thread_ts" in event else event["ts"]
    prompt = event["text"].split("<@")[1].split(">")[1].strip()

    # # Check if this is a message from the bot itself, or if it doesn't mention the bot
    # if "bot_id" in event or f"<@{app.client.users_info(user=SLACK_BOT_TOKEN)['user']['id']}>" not in text:
    #     return

    conversation(thread_ts, prompt, event["channel"], say)


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
    token = body["event"]["client_msg_id"]
    prompt = get_context(token)
    if prompt == "":
        put_context(token, body["event"]["text"])
    else:
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"status": "Success"}),
        }

    # Handle the event
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
