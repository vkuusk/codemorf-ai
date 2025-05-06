from typing import Dict, List, Annotated, TypedDict, Optional, Any
import logging

from core.llm import LLMClient

class WorkflowState(TypedDict):
    original_code: str
    requirements: str
    refactored_code: Optional[str]
    test_target: str
    test_cases: List[Dict]
    test_commands: List[Dict]  # New field for test commands
    test_results: Optional[Dict[str, Any]]
    iteration: int
    llm: LLMClient  # Add LLM client to state
    max_retries: int  # Maximum number of retries for refactoring attempts
    code_language: str  # Programming language of the code
    save_workflow_stages: bool  # Save interim results
    work_dir: str # where to save interim results
    output_file: str  # Path to the output file
    logger: Optional[logging.Logger]  # Add logger to state