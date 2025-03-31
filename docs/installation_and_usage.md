## Installation

### Source Code 

```bash
# Clone the repository
git clone https://github.com/vkuusk/codemorf-ai.git
cd codemorf-ai

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in your project root (or copy from `examples/.env.example`):

```ini
# LLM Provider Configuration
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3:8b
OLLAMA_HOST=http://localhost:11434
OLLAMA_API_ENABLED=true

# For OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_key_here
# OPENAI_MODEL=gpt-4-turbo-preview

# For Anthropic
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your_key_here
# ANTHROPIC_MODEL=claude-3-opus-20240229

# Log Level
LOG_LEVEL=INFO
```

## Usage

### Docker container

```bash
docker run ghcr.io/vkuusk/codemorf:latest
```

### From Source Code

```bash
python src/cli/codemorf.py \
    --original-code input/original.py \
    --convertion-rules input/conversion_rules.txt \
    --testcases input/testcases.txt \
    --output-file output/refactored.py \
    --save-test-commands output/test_commands.json \
    --max-retries 3
```

### Input File Formats (suggested)

#### Conversion Rules Format
```text
Refactoring Requirements:
1. Requirement 1
2. Requirement 2
...
```

#### Test Cases Format
```text
Test Cases:
if a=value1 and b=value2 then the output should be expected_result
...
```

## Supported Languages

**Python** - actually the only one at the moment

More languages coming after Python support stabilizes.

## Architecture

The tool implements a LangGraph workflow with 4 nodes:
1.Test Execs Generation
2. Refactoring
3. Test Execution
4. Validation

## Development

### Adding Support for New Languages

To add support for a new programming language:
1. Create a new test runner in `src/core/test_{language}.py`
2. Implement the language-specific test function
3. Update the test execution logic in `src/core/utils.py`

### Running Tests

```bash
cd test/cli
./test-cli.sh
# or to test docker image after local docker build
./test-cli-docker.sh
```

## Building

```bash
cd pkg
make docker
