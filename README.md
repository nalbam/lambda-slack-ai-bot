# Lambda Slack AI Bot

A serverless Slack bot powered by OpenAI's GPT and DALL-E models, built with AWS Lambda, API Gateway, and DynamoDB.

![Bot](images/bot.png)

## Features

- 🤖 **Conversational AI**: Chat with GPT-4o in Slack channels and DMs
- 🎨 **Image Generation**: Create images using DALL-E 3 with the "그려줘" keyword
- 🧵 **Thread Context**: Maintains conversation history within threads
- ⚡ **Real-time Streaming**: Live response updates as AI generates content
- 🖼️ **Image Analysis**: Describes uploaded images using GPT-4 Vision
- 📝 **Smart Formatting**: Automatically handles long messages and code blocks
- 🔄 **Duplicate Prevention**: Prevents duplicate responses using DynamoDB
- ⏰ **Auto Cleanup**: Conversation context expires after 1 hour (TTL)

## Install

```bash
$ brew install python@3.12

$ npm install -g serverless@3.38.0

$ sls plugin install -n serverless-python-requirements
$ sls plugin install -n serverless-dotenv-plugin

$ python -m pip install --upgrade -r requirements.txt
```

## Setup

Setup a Slack app by following the guide at https://slack.dev/bolt-js/tutorial/getting-started

Set scopes to Bot Token Scopes in OAuth & Permission:

```
app_mentions:read
channels:history
channels:join
channels:read
chat:write
files:read
files:write
im:read
im:write
```

Set scopes in Event Subscriptions - Subscribe to bot events

```
app_mention
message.im
```

## Environment Configuration

```bash
$ cp .env.example .env
```

### Required Variables

```bash
# Slack Configuration
SLACK_BOT_TOKEN="xoxb-xxxx"           # Bot User OAuth Token
SLACK_SIGNING_SECRET="xxxx"          # Signing Secret for verification

# OpenAI Configuration
OPENAI_API_KEY="sk-xxxx"             # OpenAI API Key
OPENAI_ORG_ID="org-xxxx"             # OpenAI Organization ID (optional)
```

### Optional Variables

```bash
# Bot Behavior
BOT_CURSOR=":loading:"                # Loading indicator emoji
SYSTEM_MESSAGE="너는 최대한 정확하고 신뢰할 수 있는 정보를 알려줘. 너는 항상 사용자를 존중해."
TEMPERATURE="0.5"                    # AI response creativity (0.0-1.0)

# AI Models
OPENAI_MODEL="gpt-4o"                # Chat model
IMAGE_MODEL="dall-e-3"               # Image generation model
IMAGE_SIZE="1024x1024"               # Generated image size
IMAGE_QUALITY="standard"             # Image quality (standard/hd)

# Message Limits
MAX_LEN_SLACK="3000"                 # Max Slack message length
MAX_LEN_OPENAI="4000"                # Max OpenAI context length

# DynamoDB
DYNAMODB_TABLE_NAME="slack-ai-bot-context"  # Table for conversation storage
```

**Get your API keys:**
- Slack: https://api.slack.com/apps
- OpenAI: https://platform.openai.com/account/api-keys

## Usage

### Mention the Bot
In any channel where the bot is added:
```
@botname Hello! How can you help me?
```

### Direct Messages
Send direct messages to the bot:
```
Explain quantum computing in simple terms
```

### Image Generation
Use the "그려줘" keyword to generate images:
```
@botname 귀여운 고양이 그려줘
```

### Image Analysis
Upload an image and ask about it:
```
@botname [upload image] What do you see in this image?
```

### Thread Conversations
Reply in threads to maintain conversation context. The bot remembers:
- Previous messages in the thread
- User reactions (for emoji responses)
- Uploaded images

## Deployment

### Development
```bash
$ sls deploy --stage dev --region us-east-1
```

### Production
```bash
$ sls deploy --stage prod --region us-east-1
```

### AWS Resources Created
- **Lambda Function**: Main bot logic (`lambda-slack-ai-bot-{stage}-mention`)
- **API Gateway**: HTTP endpoint for Slack events
- **DynamoDB Table**: Conversation context storage with TTL
- **IAM Role**: Permissions for Lambda to access DynamoDB

## Slack Test

```bash
curl -X POST -H "Content-Type: application/json" \
-d " \
{ \
    \"token\": \"Jhj5dZrVaK7ZwHHjRyZWjbDl\", \
    \"challenge\": \"3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P\", \
    \"type\": \"url_verification\" \
}" \
https://xxxx.execute-api.us-east-1.amazonaws.com/dev/slack/events
```

## OpenAi API Test

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

```bash
curl https://api.openai.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "dall-e-3",
    "prompt": "꽁꽁 얼어붙은 한강위로 고양이가 걸어갑니다.",
    "size": "1024x1024",
    "n": 1
  }'
```

## Architecture

```
Slack → API Gateway → Lambda → OpenAI API
                        ↓
                   DynamoDB (Context)
```

### Key Components

- **`handler.py`**: Main Lambda entry point and event processing
- **`src/handlers/message_handler.py`**: Core message processing logic
- **`src/api/slack_api.py`**: Slack API wrapper with caching
- **`src/api/openai_api.py`**: OpenAI API wrapper with retry logic
- **`src/utils/context_manager.py`**: DynamoDB context management
- **`src/utils/logger.py`**: Structured logging utilities
- **`src/config/settings.py`**: Environment configuration

### Data Flow

1. Slack sends events to API Gateway endpoint
2. Lambda validates and processes events
3. Context stored in DynamoDB for duplicate prevention
4. Messages processed through OpenAI API
5. Responses streamed back to Slack in real-time
6. Context automatically expires after 1 hour

## Troubleshooting

### Common Issues

**Bot not responding:**
- Check Lambda logs in CloudWatch
- Verify Slack bot token and signing secret
- Confirm API Gateway endpoint is correct in Slack app settings

**OpenAI API errors:**
- Verify API key is valid and has sufficient credits
- Check rate limits and model availability

**DynamoDB errors:**
- Ensure Lambda has proper IAM permissions
- Check if table exists and is in correct region

### Monitoring

The bot includes comprehensive logging:
- Request/response details
- Error tracking with context
- Performance metrics
- User interaction patterns

## References

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Slack Bolt Framework](https://slack.dev/bolt-python/)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model.html)
- [Serverless Framework](https://www.serverless.com/framework/docs)
