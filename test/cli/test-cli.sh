#!/usr/bin/env bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set ROOT_DIR by going up two directories from the script location
ROOT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Set PYTHONPATH to ROOT_DIR and export it
export PYTHONPATH=$ROOT_DIR

# uncomment if secrets.toml is not set and $OPENAI_API_KEY is exported outside this script
#export CODEMORF_openai_api_key=$OPENAI_API_KEY  # set this manually OPENAI_API_KEY


LOG_LEVEL=INFO  # DEBUG
LOG_FILE="codemorf-cli.log"

INPUT_DIR="input"
OUTPUT_DIR="output"
# it's where temp files might be stored. e.g. "executable_tests.json
WORK_DIR="output"

INPUT_CODE_FILE="input_code.py"
CONVERSION_RULES_FILE="input_rules.txt"
TESTCASES_FILE="input_testcases.txt"
OUTPUT_CODE_PREFIX="processed"




# Push current directory to stack and change to script directory
pushd "$SCRIPT_DIR" > /dev/null

# Run the morfing workflow Locally
python $ROOT_DIR/src/cli/codemorf.py \
    --input-dir=$INPUT_DIR \
    --output-dir=$OUTPUT_DIR \
    --work-dir=$WORK_DIR \
    --input-code-file $INPUT_CODE_FILE \
    --rules-file $CONVERSION_RULES_FILE \
    --testcases-file $TESTCASES_FILE \
    --output-code-prefix $OUTPUT_CODE_PREFIX \
    --save-workflow-stages \
    --log-file $LOG_FILE \
    --log-level $LOG_LEVEL

# Return to original directory by popping from the stack
popd > /dev/null
