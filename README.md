# Lambda Slack AI Bot

A multi-AI serverless Slack bot powered by **OpenAI** (GPT-4o, DALL-E 3) and **Google Gemini** (2.0 Flash, Vision), built with AWS Lambda, API Gateway, and DynamoDB.

![Bot](images/bot.png)

## Features

### 🎯 4-Stage Intelligent Workflow
- **Stage 1**: Intent Analysis using OpenAI (understands complex multi-part requests)
- **Stage 2**: Task Planning (breaks down requests into executable actions)
- **Stage 3**: Direct Execution & Response (immediate results without AI summarization)
- **Stage 4**: Completion notification

### 🤖 Multi-AI Capabilities
- **Dual AI Models**: Choose between OpenAI GPT-4o and Google Gemini 2.0 Flash
- **Conversational AI**: Chat with either AI model in Slack channels and DMs
- **Complex Request Handling**: Processes multi-part requests like "Gemini로 설명하고 DALL-E로 이미지 그려줘"
- **Image Generation**: Create images using DALL-E 3 with smart Korean-to-English translation
- **Advanced Image Analysis**: Choose between GPT-4 Vision or Gemini Vision for image analysis
- **Thread Summarization**: Intelligent summarization using GPT-4o
- **Real-time Streaming**: Live text response updates as AI generates content
- **Automatic Fallback**: Unsupported features automatically fallback to alternative models

### 💬 Slack Integration
- **Thread Context**: Maintains conversation history within threads
- **Smart Formatting**: Automatically handles long messages and code blocks
- **Instant Image Upload**: Generated images appear immediately in Slack
- **Duplicate Prevention**: Prevents duplicate responses using DynamoDB
- **Auto Cleanup**: Conversation context expires after 1 hour (TTL)

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

# Google Gemini Configuration (either key works)
GOOGLE_API_KEY="AIza-xxxx"           # Google AI Studio API Key
# OR
GEMINI_API_KEY="AIza-xxxx"           # Alternative Gemini API Key
```

### Optional Variables

```bash
# Bot Behavior
BOT_CURSOR=":loading:"                # Loading indicator emoji
SYSTEM_MESSAGE="너는 최대한 정확하고 신뢰할 수 있는 정보를 알려줘. 너는 항상 사용자를 존중해."
TEMPERATURE="0.5"                    # AI response creativity (0.0-1.0)

# AI Models
OPENAI_MODEL="gpt-4o"                # OpenAI chat model
GEMINI_TEXT_MODEL="gemini-2.0-flash-001"  # Gemini text model
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
- Google AI Studio: https://aistudio.google.com/apikey

## Usage

### 🔥 Complex Multi-AI Requests
The bot can handle sophisticated requests using multiple AI models:
```
@botname AI에 대해 설명하고 로봇 이미지도 그려줘
@botname Gemini로 머신러닝 설명하고 DALL-E로 다이어그램 그려줘
@botname [upload image] Gemini로 분석하고 GPT로 보고서 작성해줘
@botname 두 모델로 비교 답변해줘
@botname 스레드 요약해줘
```

### 💬 Multi-Model Conversations
**Choose your AI model:**
```
@botname GPT로 코딩 질문 답변해줘
@botname Gemini로 한국 문화 설명해줘
@botname Hello! How can you help me?  # Auto-selects best model
```

**Direct Messages:**
```
Explain quantum computing in simple terms
Gemini로 파이썬 설명해줘
Write a Python function to sort a list
```

### 🎨 Image Generation
Smart Korean-to-English translation for DALL-E:
```
@botname 귀여운 고양이 그려줘
@botname 미래 도시의 스카이라인을 그려줘
@botname Draw a robot in a cyberpunk style
```

### 🖼️ Advanced Image Analysis
Choose between GPT-4 Vision or Gemini Vision:
```
@botname [upload image] What do you see in this image?  # Auto-selects model
@botname [upload chart] Gemini로 분석해줘
@botname [upload code screenshot] GPT Vision으로 설명해줘
@botname [upload image] 두 모델로 비교 분석해줘
```

### 🧵 Thread Conversations & Summarization
Reply in threads for contextual conversations. The bot remembers:
- Previous messages in the thread
- User reactions (for emoji responses)  
- Uploaded images and analysis results
- Multi-step task progress

**Thread Summarization:**
```
@botname 스레드 요약해줘
@botname summarize this thread
@botname 이 스레드 내용 정리해줘
```

The bot will analyze all messages in the current thread and provide:
- Key topics and main points
- Important decisions or conclusions
- Participant opinions and perspectives
- Organized summary in 3-5 paragraphs

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
Slack → API Gateway → Lambda → 4-Stage Workflow Engine → Multi-AI Routing
                        ↓                                        ↓
                   DynamoDB (Context)              OpenAI API + Google Gemini API
                                                        ↓
                                                 DALL-E (Images) + Vision Models
```

### 🔄 4-Stage Workflow Engine

```
1. Intent Analysis (OpenAI GPT-4o)
   ↓
2. Task Planning & Model Selection
   ↓
3. Multi-AI Execution & Response
   ├── OpenAI: Text (GPT-4o), Images (DALL-E 3), Vision
   ├── Gemini: Text (2.0 Flash), Vision Analysis
   ├── Auto Fallback: Unsupported → Alternative Model
   └── Thread Summarization (GPT-4o)
   ↓
4. Completion Notification
```

### Key Components

#### Core System
- **`handler.py`**: Main Lambda entry point with 4-stage workflow support
- **`src/handlers/message_handler.py`**: Simplified workflow-centered message handling
- **`src/api/slack_api.py`**: Slack API wrapper with caching and file upload
- **`src/api/openai_api.py`**: OpenAI API wrapper with retry logic
- **`src/api/gemini_api.py`**: Google Gemini API wrapper with google-genai SDK
- **`src/utils/context_manager.py`**: DynamoDB context management with TTL
- **`src/utils/logger.py`**: Structured logging utilities
- **`src/config/settings.py`**: Environment configuration

#### Workflow Engine
- **`src/workflow/workflow_engine.py`**: 4-stage intelligent workflow processor
- **`src/workflow/task_executor.py`**: Individual task execution engine
- **`src/workflow/slack_utils.py`**: Slack integration utilities

### Data Flow

#### Simple Requests
1. Slack sends events to API Gateway
2. Lambda processes through basic workflow
3. Single task execution and immediate response

#### Complex Requests  
1. **Stage 1**: OpenAI analyzes user intent and required tasks
2. **Stage 2**: Tasks planned based on bot capabilities
3. **Stage 3**: Multi-AI task execution with immediate results
   - Text: OpenAI GPT-4o or Gemini 2.0 Flash (real-time streaming)
   - Images: DALL-E 3 generation with instant upload
   - Analysis: GPT-4 Vision or Gemini Vision processing
   - Auto-fallback: Unsupported features → alternative models
4. **Stage 4**: Completion notification
5. Context stored in DynamoDB for thread continuity

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
