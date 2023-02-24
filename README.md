# lambda-chatgpt-slack-bot

## Install

```bash
$ brew install python@3.8

$ npm install -g serverless

$ sls plugin install -n serverless-python-requirements
$ sls plugin install -n serverless-dotenv-plugin


$ pip3 install --upgrade -r requirements.txt
```

## Setup

Setup a Slack app by following the guide at https://slack.dev/bolt-js/tutorial/getting-started

Set scopes to Bot Token Scopes in OAuth & Permission:

```
app_mentions:read
channels:join
chat:write
im:history
im:read
im:writ
```

Set scopes in Event Subscriptions - Subscribe to bot events

```
app_mention
message.im
```

## Deployment

In order to deploy the example, you need to run the following command:

```bash
$ sls deploy
```

## Test

```bash
curl -X POST -H "Content-Type: application/json" \
-d " \
{ \
    \"token\": \"Jhj5dZrVaK7ZwHHjRyZWjbDl\", \
    \"challenge\": \"3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P\", \
    \"type\": \"url_verification\" \
}" \
https://tnmahcbgth.execute-api.us-east-1.amazonaws.com/dev/slack/events
```
