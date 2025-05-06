#!/usr/bin/env python3

import argparse
import json
import os
import logging
import sys

# TODO: cleanup import for development
try:
    # import when package is installed
    from core.workflow import create_refactoring_workflow, WorkflowState
    from core.llm import get_llm_client
    from cbxconfig import configure_logging
    from cbxconfig import CbxConfig
except ImportError:
    print("Failed to import Submodules in file: {}".format(__file__))
    print('For local development use "pip install -e ." in repo root')
    sys.exit(1)


APP_NAME = "codemorf"
# Default configuration values
DEFAULT_CONFIG = {
    # Note: _config_dir  will be set to $HOME/.APP_NAME in class constructor !!! can override ONLY on command_line
    #
    # standard for filesystem
    'config_dir': '',
    'input_dir': '',
    'output_dir': '',
    'work_dir': '',
    'log_file': '',
    'log_level': 'INFO',
    'quiet': False,
    # workflow defaults
    'save_workflow_stages': False,
    'max_retries': 3,
    'code_language': 'python',

    'input_code_file': '',
    'output_code_prefix': 'new',
    'rules_file': '',
    'testcases_file': '',
    #

    # LLM configs
    'llm_provider': '',
    'ollama_host': 'http://localhost:11434',
    'ollama_model': 'DeepSeek-R1:latest',
    'ollama_api_enabled': True, # When True - use direct API calls, when False - use ollama package
    'openai_api_key': '',
    'openai_model': 'gpt-4.1-nano',
    'anthropic_api_key': '',
    'anthropic_model': 'claude-3-haiku-latest'
}


def process_all_args(app_name, default_config):

    required_keys = ['input_code_file', 'rules_file', 'testcases_file']

    parser = argparse.ArgumentParser(description=f"{app_name} configuration")

    for key, value in default_config.items():
        # Note: key names don't have hyphens
        arg_name = key.replace('_', '-')

        # required are never BOOL
        if key in required_keys:
            parser.add_argument(
                f"--{arg_name}",
                required=True,
                type=type(value),
                help=f"Required param {arg_name} parameter"
            )
            continue

        if isinstance(value, bool):
            parser.add_argument(
                f"--{arg_name}",
                action='store_true' ,
                help=f"Enable/Disable {key}"
            )
        else:
            parser.add_argument(
                f"--{arg_name}",
                type=type(value),
                help=f"Override config value for:  {key}"
            )

    args = parser.parse_args()
    return args



def main():
    args = process_all_args(APP_NAME, DEFAULT_CONFIG)

    configure_logging(args.log_file, args.quiet, args.log_level)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME}")


    appcfg = CbxConfig(APP_NAME, args, DEFAULT_CONFIG)

    # if args.config_dir:
    #     appcfg.load(args,args.config_dir)
    # else:
    #     appcfg.load(args)


    input_scr_file = os.path.join(appcfg.get('input_dir'), appcfg.get('input_code_file'))
    rules_file = os.path.join(appcfg.get('input_dir'), appcfg.get('rules_file'))
    testcases_file = os.path.join(appcfg.get('input_dir'), appcfg.get('testcases_file'))
    output_filename = "{}_{}".format(appcfg.get('output_code_prefix'), appcfg.get('input_code_file'))
    output_file_full_name= os.path.join(appcfg.get('output_dir'), output_filename)
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
        "test_target": "original_code",
        "test_cases": tests,
        "test_results": None,
        "llm": llm,  # Add the LLM client to the inputs
        "iteration": 0,  # Add iteration counter
        "max_retries": appcfg.get('max_retries'),  # Add max retries setting
        "code_language": appcfg.get('code_language'),  # Add code language setting
        "save_workflow_stages": appcfg.get('save_workflow_stages'),  # Add save_test_commands setting
        "work_dir": appcfg.get('work_dir'),
        "output_file": output_file_full_name,  # Add output_file path
        "logger": logger  # Add logger to inputs
    }

    workflow = create_refactoring_workflow(llm, logger)
    result = workflow.invoke(inputs)


    logger.debug(result)


    # Save outputs
    with open(output_file_full_name, "w") as f:
        f.write(result['refactored_code'])

    if appcfg.get('save_workflow_stages'):
        with open(test_results_file_path, "w") as f:
            json.dump(result["test_results"].get("test_results"), f, indent=2)

    logger.info(f"Refactoring complete. Output saved to {output_file_full_name}")

if __name__ == "__main__":
    main()