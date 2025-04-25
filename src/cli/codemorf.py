#!/usr/bin/env python3

import argparse
import json
import os
import logging

# TODO: cleanup import for development
try:
    # import when package is installed
    from core.workflow import create_refactoring_workflow, RefactorState
    from core.llm import get_llm_client
    from core.utils import run_tests
    from cbxconfig import configure_logging
    from cbxconfig import CbxConfig
except ImportError:
    # import during development
    from src.core.workflow import create_refactoring_workflow, RefactorState
    from src.core.llm import get_llm_client
    from src.core.utils import run_tests
    from src.cbxconfig import configure_logging
    from src.cbxconfig import CbxConfig

APP_NAME = "codemorf"
# Default configuration values
DEFAULT_CONFIG = {
    #
    'input_dir': '',
    'output_dir': '',
    'work_dir': '',
    'log_file': '',
    'log_level': 'INFO',
    'save_workflow_stages': False,
    'quiet': False,
    # Note: _config_dir  will be set to $HOME/.APP_NAME in class constructor
    #
    'input_code_file': '',
    'output_code_prefix': 'new',
    'rules_file': '',
    'testcases_file': '',
    #
    'save_workflow_stages': False,
    'max_retries': 3,
    'code_language': 'python',
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

def _flatten_dict(d, parent_key='', sep='.'):
    """Convert nested dict to flat dict with dot-notation keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def process_all_args(app_name, default_config):
    parser = argparse.ArgumentParser(description=f"{app_name} configuration")

    flat_config = _flatten_dict(default_config)
    for key, value in flat_config.items():
        parser.add_argument(
            f"--{key.replace('.', '-')}",
            type=type(value),
            help=f"Override {key}"
        )

    # TODO: add boolen args instead of requireing true/false value


    args = parser.parse_args()
    return args


def main():
    args = process_all_args(APP_NAME, DEFAULT_CONFIG)

    configure_logging(args.log_file, args.quiet, args.log_level)
    logger = logging.getLogger(__name__)

    user_home = os.path.expanduser("~")

    appcfg = CbxConfig(APP_NAME, DEFAULT_CONFIG, user_home=user_home)
    appcfg.load(args)


    appcfg.save_to_file("testing-config.json")

    input_scr_file = os.path.join(appcfg.get('input_dir'), appcfg.get('input_code_file'))
    rules_file = os.path.join(appcfg.get('work_dir'), appcfg.get('rules_file'))
    testcases_file = os.path.join(appcfg.get('work_dir'), appcfg.get('testcases_file'))
    output_file = "{}_{}".format(appcfg.get('output_code_prefix'), appcfg.get('input_code_file'))
    output_file_path= os.path.join(appcfg.get('output_dir'), output_file)
    test_results_file_path = os.path.join(appcfg.get('output_dir'), 'final-test-results.txt')

    # Read input files
    with open(input_scr_file, "r") as f:
        code = f.read()

    with open(rules_file, "r") as f:
        rules = f.read()

    with open(testcases_file, "r") as f:
        tests = f.read()

    # Create LLM client
    llm = get_llm_client(appcfg)

    # Create input for workflow
    inputs = {
        "original_code": code,
        "requirements": rules,
        "test_cases": tests,
        "test_results": None,
        "llm": llm,  # Add the LLM client to the inputs
        "iteration": 0,  # Add iteration counter
        "max_retries": appcfg.get('max_retries'),  # Add max retries setting
        "code_language": appcfg.get('code_language'),  # Add code language setting
        "save_test_commands": appcfg.get('save_workflow_stages'),  # Add save_test_commands setting
        "output_file": output_file_path,  # Add output_file path
        "logger": logger  # Add logger to inputs
    }

    workflow = create_refactoring_workflow(llm, logger)
    result = workflow.invoke(inputs)

    # Save outputs
    with open(output_file_path, "w") as f:
        f.write(result["refactored_code"])

    if appcfg.get('save_workflow_stages'):
        with open(test_results_file_path, "w") as f:
            json.dump(result["test_results"], f, indent=2)

    logger.info(f"Refactoring complete. Output saved to {output_file_path}")

if __name__ == "__main__":
    main()