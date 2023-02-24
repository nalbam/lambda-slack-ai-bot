import boto3
import json
import openai
import os

from slack_bolt import App, Say
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

# Set up OpenAI API credentials
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_ENGINE = os.environ.get("OPENAI_ENGINE", "text-davinci-003")
OPENAI_STREAM = os.environ.get("OPENAI_STREAM", True)

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
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "chatgpt-slack-history")

dynamodb = boto3.client("dynamodb")


def get_context(thread_ts):
    response = dynamodb.get_item(
        TableName=DYNAMODB_TABLE_NAME,
        Key={"thread_ts": {"S": thread_ts}},
        ConsistentRead=True,
    )
    item = response.get("Item")
    if item is None:
        return ""
    else:
        return item.get("prompt", {"S": ""}).get("S", "")


def put_context(thread_ts, prompt):
    dynamodb.put_item(
        TableName=DYNAMODB_TABLE_NAME,
        Item={
            "thread_ts": {"S": thread_ts},
            "prompt": {"S": prompt},
        },
    )


# Handle the app_mention event
@app.event("app_mention")
def handle_app_mentions(body: dict, say: Say):
    print("handle_app_mentions: {}".format(body))

    event = body["event"]

    text = event["text"].split("<@")[1].split(">")[1].strip()
    thread_ts = event["thread_ts"] if "thread_ts" in event else event["ts"]

    print("call_chatgpt [{}] [{}]".format(thread_ts, text))

    # # Check if this is a message from the bot itself, or if it doesn't mention the bot
    # if "bot_id" in event or f"<@{app.client.users_info(user=SLACK_BOT_TOKEN)['user']['id']}>" not in text:
    #     return

    # Get conversation history for this thread, if any
    prompt = get_context(thread_ts) + text + "\n"

    message = ""

    # Update the prompt with the latest message
    put_context(thread_ts, prompt)

    if OPENAI_STREAM:
        # Create a new completion and stream the response
        stream = openai.Completion.create(
            engine=OPENAI_ENGINE,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
            stream=True,
        )

        # Keep track of the latest message timestamp
        latest_ts = None

        # Stream each message in the response to the user in the same thread
        cnt = 0
        for completions in stream:
            message = message + completions.choices[0].text

            # Send or update the message, depending on whether it's the first or subsequent messages
            if latest_ts is None:
                result = say(text=message, thread_ts=thread_ts)
                latest_ts = result["ts"]
            else:
                if cnt % 16 == 0:
                    print(thread_ts, message)

                    app.client.chat_update(
                        channel=event["channel"],
                        text=message,
                        ts=latest_ts,
                    )
            cnt = cnt + 1

        if latest_ts is not None:
            app.client.chat_update(
                channel=event["channel"],
                text=message,
                ts=latest_ts,
            )
    else:
        # Create a new completion
        completions = openai.Completion.create(
            engine=OPENAI_ENGINE,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )

        # Get the first response from the OpenAI API
        message = completions.choices[0].text

        # Send the response to the user in the same thread
        say(text=message, thread_ts=thread_ts)

    print(thread_ts, prompt, message)

    # Update the prompt with the latest message
    put_context(thread_ts, prompt + message + "\n")


def lambda_handler(event, context):
    body = json.loads(event["body"])

    if "challenge" in body:
        # Respond to the Slack Event Subscription Challenge
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"challenge": body["challenge"]}),
        }

    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
