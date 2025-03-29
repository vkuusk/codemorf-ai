#!/usr/bin/env python3

import argparse
import json
import os
import logging
from dotenv import load_dotenv

def process_all_args():
    parser = argparse.ArgumentParser(description="Code Refactoring Tool")
    parser.add_argument("--original-code", required=True, help="Path to code file to refactor")
    parser.add_argument("--convertion-rules", required=True, help="Path to requirements file")
    parser.add_argument("--testcases", required=True, help="Path to test cases file")
    parser.add_argument("--output-file", required=True, help="Path to save refactored code")
    parser.add_argument("--results-file", help="Path to save test results")
    parser.add_argument("--save-test-commands", help="Path to save generated test commands")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retries for LLM calls")
    parser.add_argument("--code-language", default="python", choices=["python"], help="Programming language of the code to refactor")
    parser.add_argument("--log-file", help="Path to log file. If not provided, logs to stdout/stderr")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output when logging to file")

    args = parser.parse_args()
    return args

def main():
    args = process_all_args()

    # Load environment variables first
    current_dir = os.getcwd()
    env_path = os.path.join(current_dir, '.env')
    if os.path.isfile(env_path):
        dotenv_result = load_dotenv(env_path)
        print(f"load_dotenv result: {dotenv_result}")
    else:
        print(f"No .env file found at {env_path}")

    # Set up logging
    handlers = []
    
    # Add file handler if log file is specified
    if args.log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(args.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(args.log_file))
    
    # Add console handler if not quiet or no log file specified
    if not args.quiet or not args.log_file:
        handlers.append(logging.StreamHandler())

    # Get log level from environment variable, default to INFO if not set
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    print(f"Setting log level to: {log_level_str} ({log_level})")

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    logger = logging.getLogger('codemorf')

    try:
        # import when package is installed
        from core.workflow import create_refactoring_workflow, RefactorState
        from core.llm import get_llm_client
        from core.utils import run_tests
    except ImportError:
        # import during development
        from src.core.workflow import create_refactoring_workflow, RefactorState
        from src.core.llm import get_llm_client
        from src.core.utils import run_tests

    # Read input files
    with open(args.original_code, "r") as f:
        code = f.read()

    with open(args.convertion_rules, "r") as f:
        rules = f.read()

    with open(args.testcases, "r") as f:
        tests = f.read()

    # Create LLM client
    llm = get_llm_client()

    # Create input for workflow
    inputs = {
        "original_code": code,
        "requirements": rules,
        "test_cases": tests,
        "test_results": None,
        "llm": llm,  # Add the LLM client to the inputs
        "iteration": 0,  # Add iteration counter
        "max_retries": args.max_retries,  # Add max retries setting
        "code_language": args.code_language,  # Add code language setting
        "save_test_commands": args.save_test_commands,  # Add save_test_commands setting
        "output_file": args.output_file,  # Add output_file path
        "logger": logger  # Add logger to inputs
    }

    workflow = create_refactoring_workflow(llm, logger)
    result = workflow.invoke(inputs)

    # Save outputs
    with open(args.output_file, "w") as f:
        f.write(result["refactored_code"])

    if args.results_file:
        with open(args.results_file, "w") as f:
            json.dump(result["test_results"], f, indent=2)

    logger.info(f"Refactoring complete. Output saved to {args.output_file}")

if __name__ == "__main__":
    main()