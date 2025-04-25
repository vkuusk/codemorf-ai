# core/workflow.py - LangGraph workflow for "Code Refactoring"
from typing import Dict, List, Annotated, TypedDict, Optional, Any
from langgraph.graph import StateGraph, END

import re
import json
import os
import logging
try:
    from core.llm import get_llm_client, LLMClient
    from core.utils import run_tests
except ImportError:
    from src.core.llm import get_llm_client, LLMClient
    from src.core.utils import run_tests



class RefactorState(TypedDict):
    original_code: str
    requirements: str
    refactored_code: Optional[str]
    test_cases: List[Dict]
    test_commands: List[Dict]  # New field for test commands
    test_results: Optional[Dict[str, Any]]
    iteration: int
    llm: LLMClient  # Add LLM client to state
    max_retries: int  # Maximum number of retries for refactoring attempts
    code_language: str  # Programming language of the code
    save_test_commands: Optional[str]  # New field for save_test_commands path
    output_file: str  # Path to the output file
    logger: Optional[logging.Logger]  # Add logger to state


def clean_code_response(response: str) -> str:
    """Clean the LLM response to ensure only Python code is returned."""
    # Remove any markdown code block markers
    response = response.replace('```python', '').replace('```', '')

    # Split into lines and process
    lines = response.strip().split('\n')
    code_blocks = []
    current_block = []
    in_code = False

    for line in lines:
        # Skip empty lines at the start
        if not line.strip():
            continue

        # Skip lines that look like explanations or thinking
        if any(marker in line.lower() for marker in [
            'here', 'thinking', 'explanation', 'let me', 'i will', 'first', 'then',
            'next', 'finally', 'now', 'we', 'this code', 'the code', 'solution'
        ]):
            # If we were in a code block, save it and start fresh
            if in_code and current_block:
                code_blocks.append('\n'.join(current_block))
                current_block = []
                in_code = False
            continue

        # Start collecting at function definition, imports, or class definition
        if (line.startswith('def ') or line.startswith('class ') or
                line.startswith('import ') or line.startswith('from ')):
            # If we were in a code block, save it and start fresh
            if in_code and current_block:
                code_blocks.append('\n'.join(current_block))
                current_block = []
            in_code = True

        # If we're in code mode and hit a non-code line, end the block
        if in_code and line and not line[0].isspace() and not any(
                line.startswith(x) for x in ['def ', 'class ', 'import ', 'from ', '@', '#']
        ):
            if current_block:
                code_blocks.append('\n'.join(current_block))
                current_block = []
            in_code = False
            continue

        # Collect the line if we're in code mode
        if in_code:
            current_block.append(line)

    # Add the last block if there is one
    if current_block:
        code_blocks.append('\n'.join(current_block))

    # If we found no code blocks, try a more lenient approach
    if not code_blocks:
        current_block = []
        for line in lines:
            if line.strip() and not any(marker in line.lower() for marker in [
                'here', 'thinking', 'explanation', 'let me', 'i will', 'first', 'then',
                'next', 'finally', 'now', 'we', 'this code', 'the code', 'solution'
            ]):
                current_block.append(line)
        if current_block:
            code_blocks.append('\n'.join(current_block))

    # Return only the last code block (most recent version)
    return code_blocks[-1] if code_blocks else ""


def refactor_code(state: RefactorState) -> RefactorState:
    """Refactor the code using the LLM."""
    logger = state.get("logger", logging.getLogger('codemorf'))
    logger.debug("Starting refactor_code")
    logger.debug(f"Iteration: {state.get('iteration', 0)}")
    
    llm = state["llm"]  # Use LLM client from state

    # Extract original function name from the input code
    original_code = state['original_code']
    function_name_match = re.search(r'def\s+(\w+)\s*\(', original_code)
    if not function_name_match:
        logger.error("Could not find function definition in original code")
        return state
    original_function_name = function_name_match.group(1)
    logger.debug(f"Original function name: {original_function_name}")

    if state.get("iteration", 0) == 0 or not state.get("refactored_code"):
        # First refactoring attempt
        prompt = f"""You are a Python code refactoring assistant. Your task is to refactor the given code according to the requirements.
IMPORTANT: 
1. Keep the EXACT same function name and signature as the original code
2. Parameter 'b' is always an integer
3. Format your response exactly as follows:

<REFACTORED_CODE>
# Your refactored Python code here, including imports and docstring
# KEEP THE ORIGINAL FUNCTION NAME: {original_function_name}
</REFACTORED_CODE>

Original Code:
{state['original_code']}

Requirements:
{state['requirements']}

Test Cases:
{state['test_cases']}

Return ONLY the refactored Python code between the <REFACTORED_CODE> tags."""
    else:
        # Fixing code based on test results
        prompt = f"""Fix this Python code to pass the tests. 
IMPORTANT:
1. Keep the EXACT same function name and signature as the original code
2. Parameter 'b' is always an integer
3. Format your response exactly as follows:

<REFACTORED_CODE>
# Your fixed Python code here, including imports and docstring
# KEEP THE ORIGINAL FUNCTION NAME: {original_function_name}
</REFACTORED_CODE>

Current Code:
{state['refactored_code']}

Test Results:
{state['test_results']}

Requirements:
{state['requirements']}

Return ONLY the fixed Python code between the <REFACTORED_CODE> tags."""

    logger.debug("Calling LLM generate")


    try:
        response = llm.generate(prompt)
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        # Set a default value or use original code
        state["refactored_code"] = state['original_code']
        return state






    logger.debug("Got LLM response")

    # Extract only the code part using the new separator
    code_match = re.search(r'<REFACTORED_CODE>\n?(.*?)\n?</REFACTORED_CODE>', response, re.DOTALL)
    if code_match:
        cleaned_code = code_match.group(1).strip()
    else:
        # Fallback to the original cleaning method if no tags found
        cleaned_code = clean_code_response(response)

    # Verify the function name is correct
    if f'def {original_function_name}' not in cleaned_code:
        logger.debug(f"Function name was changed, fixing it")
        # Find any function definition in the cleaned code
        new_function_match = re.search(r'def\s+(\w+)\s*\(', cleaned_code)
        if new_function_match:
            new_function_name = new_function_match.group(1)
            cleaned_code = cleaned_code.replace(f'def {new_function_name}(', f'def {original_function_name}(')
        else:
            logger.error("Could not find function definition in refactored code")

    state["refactored_code"] = cleaned_code
    state["iteration"] = state.get("iteration", 0) + 1
    logger.debug(f"Completed iteration {state['iteration']}")
    return state


def generate_test_commands(state: RefactorState) -> RefactorState:
    """Generate test commands from original code and test cases."""
    logger = state.get("logger", logging.getLogger('codemorf'))
    logger.debug("Starting generate_test_commands")
    logger.debug(f"save_test_commands path: {state.get('save_test_commands')}")
    
    llm = state["llm"]
    
    # Get the module name from the output file path
    output_file = state["output_file"]
    module_name = os.path.splitext(os.path.basename(output_file))[0]
    logger.debug(f"Using module name: {module_name}")
    
    prompt = f"""Generate test commands for the following code and test cases.
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
{state['original_code']}

Test Cases:
{state['test_cases']}

Return ONLY the JSON array, no other text or explanation."""

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

        # Save test commands if path is provided
        save_path = state.get("save_test_commands")
        logger.debug(f"Checking save_test_commands path: {save_path}")
        if save_path:
            try:
                # Create output directory if it doesn't exist
                output_dir = os.path.dirname(save_path)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    logger.debug(f"Created output directory: {output_dir}")
                
                with open(save_path, "w") as f:
                    json.dump(test_commands, f, indent=2)
                logger.debug(f"Saved test commands to {save_path}")
            except Exception as e:
                logger.error(f"Error saving test commands: {e}")
                logger.debug(f"Current working directory: {os.getcwd()}")
        
    except Exception as e:
        logger.error(f"Error parsing test commands: {e}")
        logger.debug(f"Response that caused error: {response}")
        # Create a default test command if parsing fails
        state["test_commands"] = [{
            "command": f"python -c 'from {module_name} import multiply_a_b; print(multiply_a_b(2, 3))'",
            "expected_result": "6"
        }]

    return state


def run_tests_node(state: RefactorState) -> RefactorState:
    """Run tests on the refactored code."""
    logger = state.get("logger", logging.getLogger('codemorf'))
    logger.debug("Starting run_tests_node")
    logger.debug(f"Output file: {state.get('output_file')}")
    
    test_results = run_tests(
        state["refactored_code"],
        state["test_commands"],
        state["code_language"],
        state["output_file"]  # Pass the output file path
    )
    state["test_results"] = test_results
    return state


def should_fix_code(state: RefactorState) -> str:
    """Determine if the code needs to be fixed based on test results."""
    logger = state.get("logger", logging.getLogger('codemorf'))
    logger.debug("Starting should_fix_code")
    
    # Get max_retries from state, default to 3 if not set
    max_iterations = state.get("max_retries", 3)
    logger.debug(f"Max retries set to {max_iterations}")

    if not state.get("test_results"):
        logger.debug("No test results, returning output")
        return "output"

    if state["test_results"].get("all_passed", False):
        logger.debug("All tests passed, returning output")
        return "output"

    if state.get("iteration", 0) >= max_iterations:
        logger.debug(f"Max iterations ({max_iterations}) reached, returning output")
        return "output"  # Stop after max iterations even if not fixed

    logger.debug("Tests failed, returning fix")
    return "fix"


def create_refactoring_workflow(llm: LLMClient, logger: logging.Logger = None):
    """Create the refactoring workflow."""
    logger = logger or logging.getLogger('codemorf')
    logger.debug("Creating workflow")
    
    # Define initial state with iteration counter and LLM client
    initial_state = {
        "iteration": 0,
        "original_code": "",
        "requirements": "",
        "refactored_code": None,  # Initialize with None as in the working version
        "test_cases": [],
        "test_commands": [],  # New field for test commands
        "test_results": None,
        "llm": llm,
        "max_retries": 3,
        "code_language": "python",
        "save_test_commands": None,  # New field for save_test_commands path
        "output_file": "",  # New field for output_file path
        "logger": logger  # Add logger to initial state
    }

    # Create workflow with initial state
    workflow = StateGraph(RefactorState, initial_state)

    # Add nodes
    workflow.add_node("generate_tests", generate_test_commands)  # New node
    workflow.add_node("refactor", refactor_code)
    workflow.add_node("test", run_tests_node)
    workflow.add_node("fix", refactor_code)

    # Set entry point to generate_tests
    workflow.set_entry_point("generate_tests")

    # Add edges
    workflow.add_edge("generate_tests", "refactor")  # Generate tests first
    workflow.add_edge("refactor", "test")
    workflow.add_conditional_edges(
        "test",
        should_fix_code,
        {
            "fix": "fix",
            "output": END
        }
    )
    workflow.add_edge("fix", "test")  # Loop back to test after fixing

    logger.debug("Workflow created")
    return workflow.compile()  # Return the compiled workflow