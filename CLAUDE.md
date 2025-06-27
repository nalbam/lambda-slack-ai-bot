# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
- Install Python dependencies: `python -m pip install --upgrade -r requirements.txt`
- Install serverless plugins: `sls plugin install -n serverless-python-requirements && sls plugin install -n serverless-dotenv-plugin`
- Setup environment: `cp .env.example .env` (then configure Slack and OpenAI credentials)

### Deployment
- Deploy to AWS: `sls deploy --stage dev --region us-east-1`
- Deploy to production: `sls deploy --stage prod --region us-east-1`

### Testing
- Test Slack webhook: Use the curl command in README.md for Slack verification
- Test OpenAI integration: Use the curl commands in README.md for API validation

## Architecture Overview

This is a serverless Slack bot built on AWS Lambda that integrates with OpenAI's GPT and DALL-E models.

### Core Components

1. **AWS Lambda Function** (`handler.py`): Main entry point that processes Slack events
2. **Message Handler** (`src/handlers/message_handler.py`): Handles conversation logic and AI integration
3. **API Layer** (`src/api/`): Interfaces with Slack and OpenAI APIs
4. **Configuration** (`src/config/settings.py`): Environment variables and app settings
5. **Utilities** (`src/utils/`): Logging, context management, and DynamoDB operations

### Data Flow

1. Slack → API Gateway → Lambda (`handler.lambda_handler`)
2. Event validation and duplicate prevention using DynamoDB
3. Message processing in `MessageHandler` class
4. OpenAI API calls for text generation or image creation
5. Response streaming back to Slack

### Key Features

- **Conversation Context**: Maintains thread context using DynamoDB with TTL
- **Streaming Responses**: Real-time text generation with periodic updates
- **Image Generation**: DALL-E integration triggered by "그려줘" keyword
- **Image Description**: GPT-4 Vision for describing uploaded images
- **Message Splitting**: Handles Slack's message size limits automatically

## Code Patterns

### Environment Variables
- Required vars: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `OPENAI_API_KEY`
- Use `os.environ.get("VAR_NAME", "default")` for optional configuration
- All settings centralized in `src/config/settings.py`

### Error Handling
- Use try/except blocks with specific exceptions
- Always log errors with context using `logger.log_error()`
- Return meaningful error messages to users

### Naming Conventions
- Functions: `snake_case` (e.g., `lambda_handler`, `get_context`)
- Constants: `UPPER_CASE` (e.g., `SLACK_BOT_TOKEN`, `IMAGE_MODEL`)
- Classes: `PascalCase` (e.g., `MessageHandler`)

### Message Processing
- All Slack messages go through `MessageHandler` class
- Content type detection: "text", "image", "emoji"
- Thread handling with conversation history
- Streaming responses with buffer management

### DynamoDB Integration
- Table: `{BASE_NAME}-{STAGE}` (e.g., "slack-ai-bot-dev")
- TTL enabled for automatic cleanup (1 hour)
- Used for duplicate prevention and conversation context

## Development Guidelines

### Adding New Features
1. Extend `MessageHandler` class for new conversation types
2. Add configuration to `settings.py` if needed
3. Update serverless.yml for new AWS resources
4. Test with both Slack events and OpenAI API responses

### Modifying AI Behavior
- Adjust prompts in `settings.py` (COMMAND_DESCRIBE, COMMAND_GENERATE)
- Modify system message via SYSTEM_MESSAGE environment variable
 - Temperature and model settings configurable via environment

### File Structure
- Keep handlers under 500 lines (current MessageHandler is at ~500 lines)
- Separate API logic from business logic
- Use utility modules for shared functionality
