#!/usr/bin/env bash

exec_type=${1:-docker}

# Validate each argument
valid_arg() {
  [[ "$1" == "docker" || "$1" == "local" ]]
}

if valid_arg "$exec_type" ; then
  echo "exec mode: $exec_type"
else
  echo "Usage: $0 <docker|local>"
  exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Set ROOT_DIR by going up two directories from the script location
ROOT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"
# VENV directory if asked for local
VENV_DIR="$SCRIPT_DIR/.venv"

# Set PYTHONPATH to ROOT_DIR and export it
export PYTHONPATH=$ROOT_DIR


# Check if OPENAI_API_KEY exists
if [ -z "${OPENAI_API_KEY}" ]; then
  echo "OPENAI_API_KEY is not set"
  echo " please run:   export OPENAI_API_KEY='your-key_here' "
  exit 1
else
  echo "OPENAI_API_KEY is set"
fi

export CODEMORF_openai_api_key=$OPENAI_API_KEY
export CODEMORF_llm_provider="openai"
export CODEMORF_openai_model="gpt-4.1-nano"

LOG_LEVEL=INFO  # DEBUG


INPUT_DIR="input"
OUTPUT_DIR="output"
# it's where temp files might be stored. e.g. "executable_tests.json
WORK_DIR="output"

INPUT_CODE_FILE="input_code.py"
CONVERSION_RULES_FILE="input_rules.txt"
TESTCASES_FILE="input_testcases.txt"
OUTPUT_CODE_PREFIX="processed"

# Image and Tag to use
IMAGE_NAME="ghcr.io/vkuusk/codemorf"
IMAGE_TAG="v0.1.0"

# Push current directory to stack and change to script directory
pushd "$SCRIPT_DIR" > /dev/null


if [[ "$exec_type" == "docker" ]]; then
  LOG_FILE="/var/log/codemorf/codemorf-cli.log"
  # Run the morphing workflow using Docker
  docker run --rm \
      -v "$SCRIPT_DIR/input:/app/input" \
      -v "$SCRIPT_DIR/output:/app/output" \
      -v "$SCRIPT_DIR/output:/var/log/codemorf" \
      -e CODEMORF_openai_api_key="$CODEMORF_openai_api_key" \
      -e CODEMORF_llm_provider=$CODEMORF_llm_provider \
      -e CODEMORF_openai_model=$CODEMORF_openai_model \
      $IMAGE_NAME:$IMAGE_TAG \
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
else
  LOG_FILE="codemorf-cli.log"

  # Create and activate virtual environment if it doesn't exist
  if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up Python environment for first use..."
    python3 -m venv "$VENV_DIR"
    # Install requirements
    "$VENV_DIR/bin/pip" install -r "$ROOT_DIR/requirements.txt"
    # Install local codemorf in editable mode
    "$VENV_DIR/bin/pip" install -e "$ROOT_DIR"
  fi

  # use venv python first
  export PATH="$VENV_DIR/bin:$PATH"

  # Run the morphing workflow Locally
  "$VENV_DIR/bin/python" $ROOT_DIR/src/cli/codemorf.py \
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
fi

# Return to original directory by popping from the stack
popd > /dev/null


