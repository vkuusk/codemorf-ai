#!/usr/bin/env bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set ROOT_DIR by going up two directories from the script location
ROOT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Set PYTHONPATH to ROOT_DIR and export it
export PYTHONPATH=$ROOT_DIR

export CODEMORF_openai_api_key=$OPENAI_API_KEY
export CODEMORF_llm_provider="openai"
export CODEMORF_openai_model="gpt-4.1-nano"

LOG_LEVEL=INFO  # DEBUG
LOG_FILE="/var/log/codemorf/codemorf-cli.log"

INPUT_DIR="input"
OUTPUT_DIR="output"
# it's where temp files might be stored. e.g. "executable_tests.json
WORK_DIR="output"

INPUT_CODE_FILE="input_code.py"
CONVERSION_RULES_FILE="input_rules.txt"
TESTCASES_FILE="input_testcases.txt"
OUTPUT_CODE_PREFIX="processed"

# Image Tag ru test
IMAGE_TAG="develop"

# Push current directory to stack and change to script directory
pushd "$SCRIPT_DIR" > /dev/null

# Run the morphing workflow using Docker
docker run --rm \
    -v "$SCRIPT_DIR/input:/app/input" \
    -v "$SCRIPT_DIR/output:/app/output" \
    -v "$SCRIPT_DIR/output:/var/log/codemorf" \
    -e CODEMORF_openai_api_key="$CODEMORF_openai_api_key" \
    -e CODEMORF_llm_provider=$CODEMORF_llm_provider \
    -e CODEMORF_openai_model=$CODEMORF_openai_model \
    codemorf:$IMAGE_TAG \
    --config-dir "/app" \
    --input-dir $INPUT_DIR \
    --output-dir $OUTPUT_DIR \
    --work-dir $WORK_DIR \
    --input-code-file $INPUT_CODE_FILE \
    --rules-file $CONVERSION_RULES_FILE \
    --testcases-file $TESTCASES_FILE \
    --output-code-prefix $OUTPUT_CODE_PREFIX \
    --save-workflow-stages \
    --log-file $LOG_FILE \
    --log-level $LOG_LEVEL

# Return to original directory by popping from the stack
popd > /dev/null

