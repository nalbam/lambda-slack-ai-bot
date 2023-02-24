import os
import openai
import json

# import openai_secret_manager

from slack_bolt import App

# Set up OpenAI API credentials
# assert "openai" in openai_secret_manager.get_services()
# secrets = openai_secret_manager.get_secret("openai")
openai.api_key = os.environ["OPENAI_API_KEY"]

# Set up Slack API credentials
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


# Define message event handler
@app.event("message")
def handle_message(event, say):
    # Ignore messages from bots and the ChatGPT bot itself
    is_bot_message = "bot_id" in event
    is_from_chatgpt = event["bot_id"] == "B01F5J3U40E"
    is_from_bot = (
        event.get("user") == app.client.users_info(user=SLACK_BOT_TOKEN)["user"]["id"]
    )
    if is_bot_message and (is_from_chatgpt or is_from_bot):
        return

    # Call OpenAI API to generate response
    response = openai.Completion.create(
        engine="davinci",
        prompt=event["text"],
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
        stream=True,  # Enable streaming mode
    )

    # Send response to Slack channel
    response_text = ""
    for message in response:
        if "text" in message:
            response_text += message["text"]
        if "finish_reason" in message and message["finish_reason"] in [
            "stop",
            "max_tokens",
        ]:
            break
    say(response_text)


def lambda_handler(event, context):
    body = json.loads(event["body"])
    if "challenge" in body:
        # Respond to the Slack Event Subscription Challenge
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"challenge": body["challenge"]}),
        }

    # Initialize the Slack app
    app.start()

    # Handle the event
    app.dispatch(body)

    # Return a success message
    return {
        "statusCode": 200,
        "headers": {"Content-type": "application/json"},
        "body": json.dumps({"message": "Success"}),
    }
