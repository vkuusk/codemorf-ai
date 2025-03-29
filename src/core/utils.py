# core/utils.py - Utility functions for execute tests
import tempfile
import os
import sys
import traceback
import subprocess
import logging
from typing import Dict, List, Any, Union

def run_tests(code: str, test_commands: List[Dict], language: str, output_file: str) -> Dict:
    """Run test commands and return results."""
    logger = logging.getLogger('codemorf')
    logger.debug("Starting run_tests")
    logger.debug(f"Output file: {output_file}")
    
    # Write the code to the output file first
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"Created output directory: {output_dir}")
        
        with open(output_file, "w") as f:
            f.write(code)
        logger.debug(f"Wrote code to {output_file}")
    except Exception as e:
        logger.error(f"Error writing code to file: {e}")
        return {
            "all_passed": False,
            "test_results": [],
            "errors": [f"Failed to write code to file: {str(e)}"]
        }

    # Add the output directory to PYTHONPATH
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.environ["PYTHONPATH"] = output_dir + os.pathsep + os.environ.get("PYTHONPATH", "")
        logger.debug(f"Added {output_dir} to PYTHONPATH")

    results = []
    all_passed = True
    errors = []

    for i, test in enumerate(test_commands, 1):
        logger.debug(f"Running test {i}: {test['command']}")
        try:
            result = subprocess.run(
                test["command"],
                shell=True,
                capture_output=True,
                text=True,
                env=os.environ.copy()  # Use a copy of the environment
            )
            actual = result.stdout.strip()
            error_output = result.stderr.strip()
            return_code = result.returncode

            test_result = {
                "test_number": i,
                "command": test["command"],
                "expected": test["expected_result"],
                "actual": actual,
                "error_output": error_output,
                "passed": actual == test["expected_result"] and return_code == 0,
                "return_code": return_code
            }
            results.append(test_result)

            if not test_result["passed"]:
                all_passed = False
                if error_output:
                    logger.warning(f"Test {i} had error output: {error_output}")
                if return_code != 0:
                    logger.warning(f"Test {i} failed with return code: {return_code}")
                if actual != test["expected_result"]:
                    logger.warning(f"Test {i} failed: expected '{test['expected_result']}', got '{actual}'")

        except Exception as e:
            logger.error(f"Error running test {i}: {e}")
            all_passed = False
            results.append({
                "test_number": i,
                "command": test["command"],
                "expected": test["expected_result"],
                "actual": "",
                "error_output": str(e),
                "passed": False,
                "return_code": -1
            })

    logger.info(f"Test results: {'All tests passed' if all_passed else 'Some tests failed'}")
    return {
        "all_passed": all_passed,
        "test_results": results,
        "errors": errors
    }