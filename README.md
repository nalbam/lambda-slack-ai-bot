# lambda-chatgpt-slack-bot

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

```
$ serverless deploy
```
