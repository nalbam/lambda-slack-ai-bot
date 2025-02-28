# Lambda Slack AI Bot - Architecture

This document outlines the architecture of the Lambda Slack AI Bot, a serverless application that integrates Slack with OpenAI's GPT and DALL-E models to provide conversational AI and image generation capabilities.

## System Overview

The Lambda Slack AI Bot is a serverless application built on AWS that connects Slack with OpenAI's AI models. It allows users to interact with AI through Slack by mentioning the bot in channels or sending direct messages. The bot can engage in conversations using OpenAI's GPT models and generate images using DALL-E.

![Architecture Overview](images/bot.png)

## Key Components

### 1. AWS Services

- **AWS Lambda**: Executes the serverless function that processes Slack events and communicates with OpenAI APIs
- **API Gateway**: Provides HTTP endpoints for Slack to send events to the Lambda function
- **DynamoDB**: Stores conversation context to maintain continuity in threaded discussions

### 2. External Services

- **Slack API**: Receives and sends messages through the Slack platform
- **OpenAI API**: Provides access to GPT models for text generation and DALL-E models for image generation

### 3. Application Components

- **Slack Bolt Framework**: Handles Slack event processing and message formatting
- **OpenAI Client**: Manages communication with OpenAI's API services
- **DynamoDB Client**: Manages conversation context storage and retrieval

## Data Flow

1. **Event Reception**:
   - Slack sends events (mentions or direct messages) to the API Gateway endpoint
   - API Gateway forwards these events to the Lambda function

2. **Event Processing**:
   - Lambda function validates the Slack event
   - For new conversations, it stores a record in DynamoDB to prevent duplicate processing
   - It extracts the message content and any attached files (particularly images)

3. **AI Processing**:
   - For text conversations:
     - The function retrieves conversation history from the thread (if applicable)
     - It sends the conversation to OpenAI's GPT model
     - It streams the response back to Slack in chunks for a better user experience

   - For image generation (triggered by the keyword "그려줘"):
     - If an image is attached, it describes the image using GPT
     - It generates an optimized prompt for DALL-E based on the conversation context
     - It sends the prompt to DALL-E to generate an image
     - It uploads the generated image to the Slack thread

4. **Response Handling**:
   - The function formats and posts responses back to the appropriate Slack channel or thread
   - For long responses, it splits the message into multiple parts to comply with Slack's message size limits

## Technical Details

### Serverless Configuration

The application is deployed using the Serverless Framework with the following configuration:
- Runtime: Python 3.9
- Timeout: 600 seconds (10 minutes)
- Memory: Configurable (commented out in serverless.yml)
- Region: us-east-1 (default, can be changed during deployment)

### DynamoDB Schema

- **Table Name**: slack-ai-bot-context (configurable)
- **Primary Key**: id (String)
- **TTL Field**: expire_at (set to 1 hour after creation)
- **Attributes**:
  - id: Thread ID or user ID
  - conversation: Stored conversation content
  - expire_dt: Human-readable expiration datetime
  - expire_at: Unix timestamp for TTL

### Environment Variables

The application uses several environment variables for configuration:
- Slack credentials (bot token, signing secret)
- OpenAI credentials and model settings
- DynamoDB table name
- System message for the AI
- Temperature setting for AI responses
- Message length limits

### Security Considerations

- AWS IAM roles limit the Lambda function's permissions to only what's necessary
- Environment variables store sensitive credentials
- DynamoDB records have a TTL to automatically clean up old conversation contexts

## Deployment Process

The application is deployed using the Serverless Framework:
1. Install dependencies (serverless, plugins, Python packages)
2. Configure environment variables in .env file
3. Deploy using `sls deploy --region us-east-1`

## Extension Points

The architecture allows for several extension possibilities:
- Adding more AI models or capabilities
- Implementing additional Slack event handlers
- Enhancing the conversation context management
- Adding authentication or rate limiting
- Implementing monitoring and analytics
