# lambda-slack-ai-bot Development Guide

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

This is a serverless Slack bot built on AWS Lambda with a **4-Stage Intelligent Workflow Engine** that integrates with OpenAI's GPT-4o, DALL-E 3, and Vision models.

### 🔄 4-Stage Workflow Engine

**Stage 1: Intent Analysis**
- OpenAI analyzes user message + bot capabilities
- Identifies required tasks for complex requests
- Handles multi-part requests like "AI 설명하고 로봇 이미지도 그려줘"

**Stage 2: Task Planning**
- Converts analysis into executable task list
- Adds context (thread history, uploaded images)
- Determines execution order and dependencies

**Stage 3: Direct Execution & Response**
- Executes tasks and sends results immediately to Slack
- No AI summarization or aggregation
- Real-time streaming for text, instant upload for images

**Stage 4: Completion Notification**
- Simple completion message
- Performance logging

### Core Components

1. **AWS Lambda Function** (`handler.py`): Main entry point with 4-stage workflow support
2. **Workflow Engine** (`src/workflow/`):
   - `workflow_engine.py`: 4-stage workflow processor
   - `task_executor.py`: Individual task execution
   - `slack_utils.py`: Slack integration utilities
3. **Message Handler** (`src/handlers/message_handler.py`): Simplified workflow-centered handler
4. **API Layer** (`src/api/`): Slack and OpenAI API interfaces
5. **Configuration** (`src/config/settings.py`): Environment variables and settings
6. **Utilities** (`src/utils/`): Logging, context management, DynamoDB operations

### Data Flow

#### Simple Requests (Single Task)
1. Slack → API Gateway → Lambda → Basic workflow processing
2. Single task execution → Immediate response

#### Complex Requests (Multi-Task)
1. Slack → API Gateway → Lambda → **4-Stage Workflow Engine**
2. **Stage 1**: OpenAI intent analysis → Task identification
3. **Stage 2**: Task planning with context
4. **Stage 3**: Execute each task → Send results immediately to Slack
5. **Stage 4**: Completion notification
6. Context stored in DynamoDB for thread continuity

### Key Features

- **Complex Multi-Task Support**: "AI 설명하고 로봇 이미지도 그려줘" → Text + Image generation
- **Instant Response**: No AI summarization, results sent immediately as completed
- **Streaming Text**: Real-time text generation with 800-character updates
- **Instant Images**: Generated images uploaded directly to Slack
- **Korean-English Translation**: Automatic translation for DALL-E prompts
- **Thread Context**: Maintains conversation history using DynamoDB with TTL
- **Error Isolation**: Failed tasks don't block other tasks

## Code Patterns

### Workflow Components
- **WorkflowEngine**: Main 4-stage coordinator
- **TaskExecutor**: Handles text_generation, image_generation, image_analysis
- **SlackMessageUtils**: Streaming responses and file uploads

### Environment Variables
- Required vars: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `OPENAI_API_KEY`
- Use `os.environ.get("VAR_NAME", "default")` for optional configuration
- All settings centralized in `src/config/settings.py`

### Error Handling
- Use try/except blocks with specific exceptions
- Always log errors with context using `logger.log_error()`
- Workflow errors fall back to basic processing
- Task-level error isolation

### Naming Conventions
- Functions: `snake_case` (e.g., `lambda_handler`, `execute_and_respond_tasks`)
- Constants: `UPPER_CASE` (e.g., `SLACK_BOT_TOKEN`, `IMAGE_MODEL`)
- Classes: `PascalCase` (e.g., `WorkflowEngine`, `TaskExecutor`)

### Message Processing
- All requests processed through workflow-centered `MessageHandler`
- Complex requests → 4-stage workflow
- Simple requests → Basic processing
- Streaming responses with buffer management

### DynamoDB Integration
- Table: `{BASE_NAME}-{STAGE}` (e.g., "slack-ai-bot-dev")
- TTL enabled for automatic cleanup (1 hour)
- Used for duplicate prevention and conversation context

## Development Guidelines

### Adding New Task Types
1. Add new task type to `TaskExecutor.execute_single_task()`
2. Implement corresponding `_execute_[task_type]()` method
3. Update `WorkflowEngine._send_task_result()` for response handling
4. Update bot capabilities in `docs/bot-capabilities.md`

### Modifying Workflow Behavior
- Intent analysis prompt in `WorkflowEngine.analyze_user_intent()`
- Task planning logic in `WorkflowEngine.create_task_list()`
- Response handling in `WorkflowEngine._send_task_result()`

### File Structure Guidelines
- Keep workflow files focused and under 500 lines
- Separate workflow logic from basic Slack/OpenAI integration
- Use utility modules for shared Slack operations
- Maintain clear separation between stages

### Performance Considerations
- Workflow engine processes complex requests only
- Simple requests use fast basic processing
- Streaming responses for better UX
- Immediate task result delivery (no aggregation delay)