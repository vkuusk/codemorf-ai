import logging
import os
import json

from core.workflow_state import WorkflowState


def node_generate_executable_tests(state: WorkflowState) -> WorkflowState:
    """Generate test commands from original code and test cases."""
    logger = state.get("logger", logging.getLogger('codemorf'))

    logger.info("Entering Node Function: GENERATE_EXECUTABLE_TESTS")

    logger.debug(f"save_test_commands path: {state.get('save_test_commands')}")

    llm = state["llm"]

    # Get the module name from the output file path
    output_file = state["output_file"]
    module_name = os.path.splitext(os.path.basename(output_file))[0]
    logger.debug(f"Using module name: {module_name}")

    prompt = GENERATE_TEST_CMD.format(
        module_name=module_name,
        original_code=state['original_code'],
        test_cases=state['test_cases']
    )


    logger.debug("Calling LLM generate for test commands")
    response = llm.generate(prompt)
    logger.debug("Got LLM response for test commands")
    logger.debug(f"Raw response: {response}")

    try:
        # Clean the response to ensure it's valid JSON
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()

        # Parse the JSON response
        test_commands = json.loads(response)
        if not isinstance(test_commands, list):
            raise ValueError("Response is not a list")

        # Validate each command has required fields
        for cmd in test_commands:
            if not isinstance(cmd, dict) or 'command' not in cmd or 'expected_result' not in cmd:
                raise ValueError("Each command must have 'command' and 'expected_result' fields")

        state["test_commands"] = test_commands
        logger.debug(f"Generated {len(test_commands)} test commands")

        # Save test commands if flag is set

        if state.get("save_workflow_stages"):
            #
            logger.debug(f"Work Dir: {state.get('work_dir')}")
            file_name = os.path.join(state.get('work_dir'), "executable_tests.json")
            logger.debug(f"Checking save_test_commands path: {file_name}")

            try:
                with open(file_name, "w") as f:
                    json.dump(test_commands, f, indent=2)
                logger.debug(f"Saved test commands to {file_name}")
            except Exception as e:
                logger.error(f"Error saving executable test commands: {e}")
                logger.debug(f"Working directory defined as: {state.get('work_dir')}")

    except Exception as e:
        logger.error(f"Error parsing test commands: {e}")
        logger.debug(f"Response that caused error: {response}")
        # Create a default test command if parsing fails
        state["test_commands"] = [{
            "command": f"python -c 'from {module_name} import multiply_a_b; print(multiply_a_b(2, 3))'",
            "expected_result": "6"
        }]

    return state



# Prompts:

GENERATE_TEST_CMD = """Generate test commands for the following code and test cases.
Each test command should include:
1. The exact command to run the test
2. The expected result

IMPORTANT: Your response must be a valid JSON array of objects. Each object must have exactly two fields:
- "command": string containing the command to run
- "expected_result": string containing the expected output

IMPORTANT: Use '{module_name}' as the module name in the import statements.

Example format:
[
  {{
    "command": "python -c 'from {module_name} import multiply_a_b; print(multiply_a_b(2, 3))'",
    "expected_result": "6"
  }},
  {{
    "command": "python -c 'from {module_name} import multiply_a_b; print(multiply_a_b(0, 5))'",
    "expected_result": "0"
  }}
]

Original Code:
{original_code}

Test Cases:
{test_cases}

Return ONLY the JSON array, no other text or explanation."""
