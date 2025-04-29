# core/nodes/code_modify/code_modify.py

import logging
import re

from core.workflow_state import WorkflowState

def node_code_modify(state: WorkflowState) -> WorkflowState:
    """Refactor the code using the LLM."""
    logger = state.get("logger", logging.getLogger('codemorf'))

    logger.info("Entering Node Function: CODE_MODIFY")
    state["iteration"] += 1
    logger.info(f"Iteration: {state["iteration"]}")

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
        prompt = MODIFY_CODE_PROMPT.format(
            original_function_name=original_function_name,
            original_code=state['original_code'],
            requirements=state['requirements'],
            test_cases=state['test_cases']
        )
    else:
        # Fixing code based on test results
        prompt = FIX_CODE_PROMPT.format(
            original_function_name=original_function_name,
            refactored_code=state['refactored_code'],
            test_results=state['test_results'],
            requirements=state['requirements']
        )

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

    state["test_target"] = "refactored_code"
    logger.debug(f"Completed iteration {state['iteration']}")
    return state

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


# Promts


MODIFY_CODE_PROMPT = """You are a Python code refactoring assistant. Your task is to refactor the given code according to the requirements.
IMPORTANT: 
1. Keep the EXACT same function name and signature as the original code
2. Parameter 'b' is always an integer
3. Format your response exactly as follows:

<REFACTORED_CODE>
# Your refactored Python code here, including imports and docstring
# KEEP THE ORIGINAL FUNCTION NAME: {original_function_name}
</REFACTORED_CODE>

Original Code:
{original_code}

Requirements:
{requirements}

Test Cases:
{test_cases}

Return ONLY the refactored Python code between the <REFACTORED_CODE> tags."""


FIX_CODE_PROMPT = """Fix this Python code to pass the tests. 
IMPORTANT:
1. Keep the EXACT same function name and signature as the original code
2. Parameter 'b' is always an integer
3. Format your response exactly as follows:

<REFACTORED_CODE>
# Your fixed Python code here, including imports and docstring
# KEEP THE ORIGINAL FUNCTION NAME: {original_function_name}
</REFACTORED_CODE>

Current Code:
{refactored_code}

Test Results:
{test_results}

Requirements:
{requirements}

Return ONLY the fixed Python code between the <REFACTORED_CODE> tags."""

