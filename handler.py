import os
import openai
# import openai_secret_manager

from slack_bolt import App

# Set up OpenAI API credentials
# assert "openai" in openai_secret_manager.get_services()
# secrets = openai_secret_manager.get_secret("openai")
openai.api_key = os.environ["OPENAI_API_KEY"]

# Set up Slack API credentials
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)


# Define message event handler
def handle_message(event, context):
    # Retrieve user's message
    message = event["body"]
    # Call OpenAI API to generate response
    response = openai.Completion.create(
        engine="davinci",
        prompt=message,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    # Send response to Slack channel
    app.client.chat_postMessage(
        channel=event["headers"]["X-Slack-Channel-Id"], text=response.choices[0].text
    )
