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

Create  ~/.codemorf/config.toml 
```bash
# Basic configuration

# LLM Provider Configuration
# Choose which provider to use: "ollama", "openai", or "anthropic"
# "loopback" will skip calling LLM and return the echo of prompt back with

llm_provider = "openai"

# OpenAI config
openai_model = "gpt-4.1-nano"

# OLLAMA config
# ollama_host = "http://10.0.0.25:11434"
# ollama_model = "DeepSeek-R1:latest"
```
Create ~/.codemorf/secrets.toml 

```bash
# OpenAI Configuration
openai_api_key = <your_key_here>
```

## Usage

### Docker container

```bash
docker run ghcr.io/vkuusk/codemorf:v0.1.0
```

### From Source Code

```bash
# add venv with python and install requirements
# activate venv

# from repo root
python ./src/cli/codemorf.py \
    --input-code-file $INPUT_CODE_FILE \
    --rules-file $CONVERSION_RULES_FILE \
    --testcases-file $TESTCASES_FILE \
    --output-code-prefix $OUTPUT_CODE_PREFIX \
    --save-workflow-stages \
    --log-file $LOG_FILE \
    --log-level $LOG_LEVEL

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
```

