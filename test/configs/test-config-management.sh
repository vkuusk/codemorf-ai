#!/usr/bin/env bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set ROOT_DIR by going up two directories from the script location
ROOT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Set PYTHONPATH to ROOT_DIR and export it
export PYTHONPATH=$ROOT_DIR

LOG_FILE="testing-logging.log"

 INPUT_CODE_FILE="src-input.py"
 CONVERSION_RULES_FILE="conversion-rules.txt"
 TESTCASES_FILE="test-cases.txt"
 OUTPUT_FILE="src-output.py"




# Push current directory to stack and change to script directory
pushd "$SCRIPT_DIR" > /dev/null

# Run the refactoring tool
python $ROOT_DIR/src/cli/codemorf.py \
    --input-code-file $INPUT_CODE_FILE \
    --conversion-rules $CONVERSION_RULES_FILE \
    --test-cases $TESTCASES_FILE \
    --output-file $OUTPUT_FILE \
    --save-workflow-stages  \
    --log-file $LOG_FILE



# Return to original directory by popping from the stack
popd > /dev/null


