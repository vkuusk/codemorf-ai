#!/usr/bin/env python3

import argparse
import json
import os
import logging

try:
    # import when package is installed
    from core.workflow import create_refactoring_workflow, RefactorState
    from core.llm import get_llm_client
    from core.utils import run_tests
    import cbxconfig
except ImportError:
    # import during development
    from src.core.workflow import create_refactoring_workflow, RefactorState
    from src.core.llm import get_llm_client
    from src.core.utils import run_tests
    import src.cbxconfig as cbxconfig



APP_NAME = "codemorf"
# Default configuration values
DEFAULT_CONFIG = {
    #
    'input_dir': '',
    'output_dir': '',
    'work_dir': '',
    'current_dir': '',
    #
    'input_code_file': '',
    'output_code_prefix': '',
    'conversion_rules_file': '',
    'testcases_file': '',
    #
    'save_workflow_stages': False,
    'max_retries': 3,
    'code-language': 'python',
    #
    'llm_provider': 'none',
    'ollama_host': 'http://localhost:11434',
    'ollama_model': 'DeepSeek-R1:latest',
    'ollama_api_enabled': True, # When True - use direct API calls, when False - use ollama package
    'openai_api_key': '',
    'openai_model': 'gpt-4o-mini',
    'anthropic_api_key': '',
    'anthropic_model': 'claude-3-haiku-20240307'
}


def process_all_args():
    parser = argparse.ArgumentParser(description="Code Refactoring Tool")
    parser.add_argument("--input-code-file",
                        required=True,
                        help="Path to code file to refactor")
    parser.add_argument("--conversion-rules",
                        required=True,
                        help="Path to file with conversion rules")
    parser.add_argument("--test-cases",
                        required=True,
                        help="Path to test cases file")
    parser.add_argument("--output-file",
                        required=True,
                        help="Path to save refactored code")
    
    #
    parser.add_argument("--input-dir",
                        default="",
                        help="Path to dir with input files")
    parser.add_argument("--output-dir",
                        default="",
                        help="Path to dir with output files")
    parser.add_argument("--work-dir",
                        default="",
                        help="Path to dir with temp work files ")
    #
    parser.add_argument("--save-workflow-stages",
                        action='store_true',
                        default=False,
                        help="Path to save test results")
    parser.add_argument("--max-retries",
                        type=int,
                        default=3,
                        help="Maximum number of retries for LLM calls")
    parser.add_argument("--code-language",
                        default="python",
                        choices=["python"],
                        help="Programming language of the code to refactor")
    #
    parser.add_argument("--openai-api-key",
                        default="",
                        help="OpenAI API key")
    parser.add_argument("--anthropic-api-key",
                        default="",
                        help="Anthropic API key")
    #
    parser.add_argument("--log-file",
                        default=None,
                        help="Path to log file. If not provided, logs to stdout/stderr")
    parser.add_argument("--quiet",
                        action="store_true", help="Suppress console output when logging to file")


    args = parser.parse_args()
    return args

def update_dirs(appcfg):
    cwd = appcfg.get('current_dir')
    input_dir = appcfg.get('input_dir')
    output_dir = appcfg.get('output_dir')
    work_dir = appcfg.get('work_dir')
    if not input_dir:
        input_dir = cwd
    else:
        # Check if input_dir is an absolute path
        if not os.path.isabs(input_dir):
            # It's a relative path, prepend the current working directory
            input_dir = os.path.join(cwd, input_dir)
    if not output_dir:
        output_dir = cwd
    else:
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(cwd, output_dir)
    if not work_dir:
        work_dir = cwd
    else:
        if not os.path.isabs(work_dir):
            work_dir = os.path.join(cwd, work_dir)

    appcfg.set('input_dir', input_dir)
    appcfg.set('output_dir', output_dir)
    appcfg.set('work_dir', work_dir)
    appcfg.set('current_dir', cwd)
    return appcfg


def main():
    args = process_all_args()

    cbxconfig.configure_logging(args.log_file, args.quiet)
    logger = logging.getLogger(__name__)

    appcfg = cbxconfig.load_config(APP_NAME, DEFAULT_CONFIG)

    update_dirs(appcfg)


    appcfg.save_to_file("testing-config.json")

    input_scr_file = os.path.join(appcfg.get('input_dir'), appcfg.get('input_code_file'))
    print(input_scr_file)

    # Read input files
    with open(input_scr_file, "r") as f:
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