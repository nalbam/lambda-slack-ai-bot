# Lambda Slack AI Bot - Architecture

This document outlines the architecture of the Lambda Slack AI Bot, a serverless application that integrates Slack with OpenAI's GPT-4o, DALL-E 3, and Vision models through an intelligent 4-stage workflow engine.

## System Overview

The Lambda Slack AI Bot is a sophisticated serverless application that handles complex multi-task requests through a 4-stage intelligent workflow engine. It can process requests like "Explain AI and draw a robot image" by automatically breaking them into separate tasks and executing them with immediate results delivery to Slack.

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

#### Core System
- **Workflow Engine** (`src/workflow/workflow_engine.py`): 4-stage intelligent workflow processor
- **Task Executor** (`src/workflow/task_executor.py`): Individual task execution engine  
- **Message Handler** (`src/handlers/message_handler.py`): Workflow-centered message processing
- **Slack Utils** (`src/workflow/slack_utils.py`): Slack integration utilities

#### API Layer
- **Slack API** (`src/api/slack_api.py`): Slack Bolt framework wrapper with file handling
- **OpenAI API** (`src/api/openai_api.py`): OpenAI client with retry logic and streaming

#### Utilities
- **Context Manager** (`src/utils/context_manager.py`): DynamoDB operations with TTL
- **Logger** (`src/utils/logger.py`): Structured logging system
- **Settings** (`src/config/settings.py`): Environment configuration management

## 4-Stage Workflow Data Flow

### Simple Requests (Single Task)
1. **Event Reception**: Slack → API Gateway → Lambda
2. **Basic Processing**: MessageHandler → Direct execution → Immediate response

### Complex Requests (Multi-Task) - 4-Stage Workflow

#### Stage 1: Intent Analysis
1. **Event Reception**: Slack → API Gateway → Lambda → MessageHandler
2. **Workflow Trigger**: Complex request detected → WorkflowEngine activated
3. **Intent Analysis**: OpenAI analyzes user message + bot capabilities → Task identification

#### Stage 2: Task Planning  
4. **Task Creation**: Convert analysis into executable task list
5. **Context Integration**: Add thread history, uploaded images, dependencies
6. **Priority Sorting**: Arrange tasks by dependencies and priority

#### Stage 3: Direct Execution & Response
7. **Sequential Processing**: Execute each task immediately
8. **Real-time Results**: Send results to Slack as soon as each task completes
   - **Text Generation**: GPT-4o → Streaming response → Slack
   - **Image Generation**: Korean→English → DALL-E 3 → Download → Upload → Slack  
   - **Image Analysis**: GPT-4 Vision → Analysis → Streaming → Slack
   - **Thread Summary**: Collect messages → GPT-4o → Structured summary → Slack

#### Stage 4: Completion
9. **Completion Notification**: "✅ All tasks completed" message
10. **Context Storage**: Thread history → DynamoDB with TTL
11. **Performance Logging**: Execution metrics and errors

### Task Execution Details

#### Text Generation Flow
```
User Request → Intent Analysis → Task Planning → GPT-4o API → 
Streaming Response (800 chars/update) → Slack Real-time Updates
```

#### Image Generation Flow  
```
User Request → Intent Analysis → Korean Text Detection → 
Translation (if needed) → DALL-E 3 API → Image Download → 
Slack File Upload → Instant Display
```

#### Thread Summary Flow
```
Summary Request → Thread Message Collection → Message Formatting → 
GPT-4o Analysis → Structured Summary → Slack Response
```

## Technical Details

### Serverless Configuration

The application is deployed using the Serverless Framework with the following configuration:
- **Runtime**: Python 3.12 (upgraded for better performance)
- **Timeout**: 300 seconds (5 minutes) - optimized for complex workflows
- **Memory**: 5120 MB (high memory for image processing)
- **Region**: us-east-1 (default, configurable during deployment)
- **Architecture**: Serverless with process_before_response=True for better UX

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

The modular 4-stage workflow architecture allows for several extension possibilities:

### Adding New Task Types
- Implement new `_execute_[task_type]()` methods in TaskExecutor
- Update WorkflowEngine intent analysis prompts  
- Add fallback logic for new task types
- Update bot capabilities documentation

### Enhanced AI Capabilities
- Integration with new OpenAI models (GPT-5, updated DALL-E)
- Support for video generation or audio processing
- Multi-modal task combinations
- Advanced reasoning workflows

### Workflow Enhancements  
- Parallel task execution for independent tasks
- Task dependency chains and conditional execution
- User approval steps for sensitive operations
- Workflow templates and saved procedures

### Integration Expansions
- Microsoft Teams, Discord support
- Integration with productivity tools (Notion, Confluence)
- Enterprise authentication (SSO, LDAP)
- Custom model hosting and fine-tuning

### Performance & Monitoring
- Real-time analytics and usage metrics
- A/B testing for different workflow strategies  
- Cost optimization and rate limiting
- Advanced error recovery and retry mechanisms

## Performance Characteristics

### Optimizations Implemented
- **Code Cleanup**: Removed 780+ lines of unused code for faster load times
- **Streaming Responses**: Real-time text delivery (800 chars/update)
- **Immediate Results**: No AI aggregation delay - results sent instantly
- **Smart Fallbacks**: Robust error handling with graceful degradation
- **Memory Efficiency**: Optimized for 5GB Lambda memory allocation

### Scalability Considerations
- **Stateless Design**: Each request processed independently
- **DynamoDB TTL**: Automatic context cleanup prevents data accumulation
- **Retry Logic**: Exponential backoff for API resilience
- **Error Isolation**: Failed tasks don't impact other operations
