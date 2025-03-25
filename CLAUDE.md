# lambda-slack-ai-bot Development Guide

## Basic Guidelines
- Focus on solving the specific problem - avoid unnecessary complexity or scope creep.
- Use standard libraries and documented patterns first before creating custom solutions.
- Write clean, well-structured code with meaningful names and clear organization.
- Handle errors and edge cases properly to ensure code robustness.
- Include helpful comments for complex logic while keeping code self-documenting.

## Commands
- Deploy: `sls deploy --region us-east-1`
- Install dependencies: `python -m pip install --upgrade -r requirements.txt`
- Install serverless plugins: `sls plugin install -n serverless-python-requirements && sls plugin install -n serverless-dotenv-plugin`

## Code Style Guidelines
- **Imports**: Standard library imports first, then third-party packages, then local modules
- **Environment Variables**: Use `os.environ.get("VAR_NAME", "default")` pattern for optional vars
- **Error Handling**: Use try/except blocks with specific exception types and logging
- **Naming Conventions**:
  - Functions: snake_case (e.g., `lambda_handler`, `get_context`)
  - Constants: UPPER_CASE (e.g., `SLACK_BOT_TOKEN`, `IMAGE_MODEL`)
- **Comments**: Add descriptive comments for functions and complex logic
- **String Formatting**: Prefer f-strings or `format()` over string concatenation
- **Function Structure**: Keep functions small and focused on a single responsibility

## Architecture
- AWS Lambda + API Gateway for handling Slack events
- DynamoDB for conversation context storage
- OpenAI API integration for chat and image generation
- Slack API for messaging and file handling
