# core/workflow.py - LangGraph workflow for "Code Refactoring"
from typing import Dict, List, Annotated, TypedDict, Optional, Any
from langgraph.graph import StateGraph, END

import sys
import logging



try:
    from .llm import get_llm_client, LLMClient
    # import core.prompts as pmt
    from .workflow_state import WorkflowState
    from .nodes.test_generate import node_generate_executable_tests
    from .nodes.test_execute import node_run_tests
    from .nodes.code_modify import node_code_modify
except ImportError:
    print("Failed to import Submodules in file: {}".format(__file__))
    print('Either reinstall package OR For local development: use "pip install -e ." in repo root')
    sys.exit(1)

def should_fix_code(state: WorkflowState) -> str:
    """Determine if the code needs to be fixed based on test results."""
    logger = state.get("logger", logging.getLogger('codemorf'))

    logger.info("in function: SHOULD_FIX_CODE")
    logger.debug(state)

    # Get max_retries from state
    max_iterations = state.get("max_retries")
    logger.debug(f"Max retries set to {max_iterations}")
    iteration = state.get("iteration")

    if not state.get("test_results"):
        logger.error("No test results, returning output")
        return "output"

    if state["test_results"].get("all_passed"):
        logger.debug("All tests passed, returning output")
        return "output"

    if iteration >= max_iterations:
        logger.error(f"Max iterations ({max_iterations}) reached, Stopping cycle. returning output")
        return "output"  # Stop after max iterations even if not fixed

    logger.debug(f"iteration # {iteration} : Tests failed, returning fix")
    logger.debug("exiting function: SHOULD_FIX_CODE")
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
        "refactored_code": "# No Code Generated",
        "test_target": "original_code",
        "test_cases": [],
        "test_commands": [],  # New field for test commands
        "test_results": {"all_passed": False, "test_results": [], "errors": []},
        "llm": llm,
        "max_retries": 3,
        "iteration": 0,
        "code_language": "python",
        "output_file": "",  # New field for output_file path
        "logger": logger  # Add logger to initial state
    }

    # Create workflow with initial state
    workflow = StateGraph(WorkflowState, initial_state)

    # Add Nodes
    # generates tests for the code in question
    workflow.add_node("generate_tests", node_generate_executable_tests)  # New node
    # validate tests against original code . note: starting "test_target = original_code"
    workflow.add_node("validate_tests", node_run_tests)
    workflow.add_node("refactor", node_code_modify)
    workflow.add_node("test", node_run_tests)
    workflow.add_node("fix", node_code_modify)

    # set GENERATE_TESTS as an ENTRY_PINT
    workflow.set_entry_point("generate_tests")

    # Add Edges
    workflow.add_edge("generate_tests", "validate_tests")
    workflow.add_edge("validate_tests", "refactor")  # Generate tests first
    workflow.add_edge("refactor", "test")
    workflow.add_edge("fix", "test")  # Loop back to test after fixing
    workflow.add_conditional_edges(
        "test",
        should_fix_code,
        {
            "fix": "fix",
            "output": END
        }
    )

    return workflow.compile()  # Return the compiled workflow