#!/usr/bin/env bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set ROOT_DIR by going up two directories from the script location
ROOT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Test file names
TEST_CODE_FILE=testcode.py
CONVERSION_RULES_FILE=conversion_rules.txt
TESTCASES_FILE=testcases.txt
OUTPUT_FILE=new_${TEST_CODE_FILE}
RESULTS_FILE=results.txt
TEST_COMMANDS_FILE=test_commands.json
LOG_FILE=refactoring.log

# Push current directory to stack and change to script directory
pushd "$SCRIPT_DIR" > /dev/null

# Run the refactoring tool using Docker
docker run --rm \
    -v "$SCRIPT_DIR/input:/app/input" \
    -v "$SCRIPT_DIR/output:/app/output" \
    -v "$SCRIPT_DIR/.env:/app/.env" \
    codemorf:latest \
    --original-code input/$TEST_CODE_FILE \
    --convertion-rules input/$CONVERSION_RULES_FILE \
    --testcases input/$TESTCASES_FILE \
    --output-file output/$OUTPUT_FILE \
    --results-file output/$RESULTS_FILE \
    --save-test-commands output/$TEST_COMMANDS_FILE \
    --log-file output/$LOG_FILE

# Return to original directory by popping from the stack
popd > /dev/null 