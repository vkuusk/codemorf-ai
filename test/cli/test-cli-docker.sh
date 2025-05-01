#!/usr/bin/env bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set ROOT_DIR by going up two directories from the script location
ROOT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Test file names
LOG_FILE="testing-logs.log"
LOG_LEVEL="DEBUG"

INPUT_CODE_FILE="input_code.py"
CONVERSION_RULES_FILE="input_rules.txt"
TESTCASES_FILE="input_testcases.txt"
OUTPUT_CODE_PREFIX="processed"

# Push current directory to stack and change to script directory
pushd "$SCRIPT_DIR" > /dev/null

# Run the refactoring tool using Docker
docker run --rm \
    -v "$SCRIPT_DIR/:/app" \
    codemorf:develop \
    --input-code-file $INPUT_CODE_FILE \
    --rules-file $CONVERSION_RULES_FILE \
    --testcases-file $TESTCASES_FILE \
    --output-code-prefix $OUTPUT_CODE_PREFIX \
    --save-workflow-stages \
    --log-file $LOG_FILE \
    --log-level $LOG_LEVEL

# Return to original directory by popping from the stack
popd > /dev/null
