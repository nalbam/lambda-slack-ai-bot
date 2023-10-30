import boto3
import json
import openai
import os
import time

# import deepl

from slack_bolt import App, Say
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

BOT_CURSOR = os.environ.get("BOT_CURSOR", ":robot_face:")

# Keep track of conversation history by thread
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "openai-slack-bot-context")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Set up Slack API credentials
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# Initialize Slack app
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    process_before_response=True,
)

# Set up OpenAI API credentials
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

OPENAI_HISTORY = int(os.environ.get("OPENAI_HISTORY", 10))
OPENAI_SYSTEM = os.environ.get("OPENAI_SYSTEM", "")
OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", 0.5))

# # Set up DeepL API credentials
# DEEPL_API_KEY = os.environ["DEEPL_API_KEY"]
# DEEPL_TARGET_LANG = os.environ.get("DEEPL_TARGET_LANG", "KR")


# Get the context from DynamoDB
def get_context(id, default=""):
    item = table.get_item(Key={"id": id}).get("Item")
    return (item["conversation"]) if item else (default)


# Put the context in DynamoDB
def put_context(id, conversation=""):
    current_time = int(time.time())
    expire_at = current_time + (86400 * 10)  # +10 days

    table.put_item(
        Item={
            "id": id,
            "conversation": conversation,
            "expire_at": expire_at,
        }
    )


# Update the message in Slack
def chat_update(channel, message, latest_ts):
    print("chat_update: {}".format(message))
    app.client.chat_update(
        channel=channel,
        text=message,
        ts=latest_ts,
    )


# # Handle the translate test
# def translate(message, target_lang=DEEPL_TARGET_LANG, source_lang=None):
#     print("translate: {}".format(message))

#     translator = deepl.Translator(DEEPL_API_KEY)

#     result = translator.translate_text(message, target_lang=target_lang, source_lang=source_lang)

#     print("translate: {}".format(result))

#     return result


# Handle the openai conversation
def conversation(thread_ts, prompt, channel, client_msg_id, say: Say):
    print(thread_ts, prompt)

    openai.api_key = OPENAI_API_KEY

    # Keep track of the latest message timestamp
    result = say(text=BOT_CURSOR, thread_ts=thread_ts)
    latest_ts = result["ts"]

    messages = []

    if OPENAI_SYSTEM != "":
        messages.append(
            {
                "role": "system",
                "content": OPENAI_SYSTEM,
            }
        )

    # # Get conversation history for this thread, if any
    # messages = json.loads(get_context(thread_ts, "[]"))
    # messages = messages[-OPENAI_HISTORY:]

    if thread_ts != None:
        # Get thread messages using conversations.replies API method
        response = app.client.conversations_replies(channel=channel, ts=thread_ts)

        print("conversations_replies", response)

        if not response.get("ok"):
            print("Failed to retrieve thread messages")

        for message in response.get("messages", [])[-OPENAI_HISTORY:]:
            if message.get("client_msg_id", "") == client_msg_id:
                break

            role = "user"
            if message.get("bot_id", "") != "":
                role = "assistant"

            content = message.get("text", "")
            if message.get("user", "") != "":
                content = "<@{}> {}".format(message.get("user"), content)

            messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    # Add the user message to the conversation history
    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:
        print("messages", messages)

        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=OPENAI_TEMPERATURE,
            stream=True,
        )

        # Stream each message in the response to the user in the same thread
        counter = 0
        message = ""
        for completions in response:
            if counter == 0:
                print("completions", completions)

            if "content" in completions.choices[0].delta:
                message = message + completions.choices[0].delta.get("content")

            # Send or update the message, depending on whether it's the first or subsequent messages
            if counter % 32 == 1:
                chat_update(channel, message + " " + BOT_CURSOR, latest_ts)

            counter = counter + 1

        # Send the final message
        chat_update(channel, message, latest_ts)

        if message != "":
            messages.append(
                {
                    "role": "assistant",
                    "content": message,
                }
            )
            put_context(thread_ts, json.dumps(messages))

    except Exception as e:
        chat_update(channel, message, latest_ts)

        message = "Error handling message: {}".format(e)
        say(text=message, thread_ts=thread_ts)

        print(thread_ts, message)

        message = "Sorry, I could not process your request.\nhttps://status.openai.com"
        say(text=message, thread_ts=thread_ts)


# Handle the app_mention event
@app.event("app_mention")
def handle_mention(body: dict, say: Say):
    print("handle_mention: {}".format(body))

    event = body["event"]

    channel = event["channel"]
    client_msg_id = event["client_msg_id"]
    thread_ts = event["thread_ts"] if "thread_ts" in event else event["ts"]
    prompt = event["text"].split("<@")[1].split(">")[1].strip()

    # # Check if this is a message from the bot itself, or if it doesn't mention the bot
    # if "bot_id" in event or f"<@{app.client.users_info(user=SLACK_BOT_TOKEN)['user']['id']}>" not in text:
    #     return

    conversation(thread_ts, prompt, channel, client_msg_id, say)


# Handle the DM (direct message) event
@app.event("message")
def handle_message(body: dict, say: Say):
    print("handle_message: {}".format(body))

    event = body["event"]

    channel = event["channel"]
    client_msg_id = event["client_msg_id"]
    prompt = event["text"].strip()

    if "bot_id" in event:  # Ignore messages from the bot itself
        return

    # Use thread_ts=None for regular messages, and user ID for DMs
    conversation(None, prompt, channel, client_msg_id, say)


# Handle the message event
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
