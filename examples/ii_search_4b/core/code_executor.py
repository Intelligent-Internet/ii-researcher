"""
add-apt-repository ppa:deki/firejail
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y install firejail firejail-profiles
"""
import regex as re
import subprocess
import os
import uuid
import shutil
import resource
from typing import Tuple, Optional, Union, List

try:
    from ..configs import SEARCH_TYPE
except ImportError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from configs import SEARCH_TYPE
# Timeout for code execution in seconds
TIMEOUT = 10
PRE_IMPORT_LIBS = "from string import *\nfrom re import *\nfrom datetime import *\nfrom collections import *\nfrom heapq import *\nfrom bisect import *\nfrom copy import *\nfrom math import *\nfrom random import *\nfrom statistics import *\nfrom itertools import *\nfrom functools import *\nfrom operator import *\nfrom io import *\nfrom sys import *\nfrom json import *\nfrom builtins import *\nfrom typing import *\nimport string\nimport re\nimport datetime\nimport collections\nimport heapq\nimport bisect\nimport copy\nimport math\nimport random\nimport statistics\nimport itertools\nimport functools\nimport operator\nimport io\nimport sys\nimport json\nsys.setrecursionlimit(6*10**5)\n\n"
filejail_command_exists = shutil.which("firejail") is not None
current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
if SEARCH_TYPE == "LOCAL":
    PRE_IMPORT_LIBS2 = f"""import os,sys,json\nsys.path.append("{current_directory}")\nfrom search_client import *\n"""
else:
    PRE_IMPORT_LIBS2 = f"""import os,sys,json\nsys.path.append("{current_directory}")\nfrom google_search_client import *\n"""
PRE_IMPORT_LIBS = PRE_IMPORT_LIBS + "\n" + PRE_IMPORT_LIBS2 + "\n\n"


def check_forbidden_imports(code: str) -> bool:
    """
    Checks if the code contains imports of potentially dangerous packages.

    Args:
        code: Python code string to analyze

    Returns:
        Boolean indicating if the code contains forbidden imports
    """
    # List of potentially dangerous modules that could affect the host system
    forbidden_modules = [
        "subprocess",
        "multiprocessing",
        "threading",
        "socket",
        "psutil",
        "resource",
        "ctypes",
    ]

    # Simple string-based check for import statements
    for module in forbidden_modules:
        if f"import {module}" in code or f"from {module}" in code:
            return True

    # Check for os.system, os.popen, and similar dangerous calls
    dangerous_patterns = [
        "os.system",
        "os.popen",
        "os.spawn",
        "os.fork",
        "os.exec",
        "sys.exit",
        "os._exit",
        "os.kill",
    ]

    for pattern in dangerous_patterns:
        if pattern in code:
            return True

    return False


def wrap_code_blocks(code: Union[str, List[str]]) -> str:
    """
    Wraps the provided code blocks with try-except to handle exceptions including syntax errors.
    For previous codes, redirect stdout and stderr to null and export defined functions and variables.

    Args:
        code: List of code strings to wrap

    Returns:
        Wrapped code string
    """
    wrapped_code = ""

    # Convert single string to list for consistent handling
    if isinstance(code, str):
        code = [code]

    # Import needed at the top
    wrapped_code += "import sys, os, io, ast\n\n"

    # Add the safe_exec_with_exports function
    wrapped_code += """
def parse_and_exec_salvageable(code_string):
    # Split the code into lines
    lines = code_string.splitlines()
    
    # Try to execute code incrementally, line by line or in blocks
    current_block = ""
    local_namespace = {}
    
    for line in lines:
        # Add the current line to our accumulating block
        if current_block:
            current_block += "\\n" + line
        else:
            current_block = line
            
        # Skip empty lines or comments
        if not line.strip() or line.strip().startswith('#'):
            continue
            
        # Try to parse the current block to check for syntax
        try:
            ast.parse(current_block)
            
            # If it parses successfully, try to execute it
            try:
                # Create a new local namespace for this execution
                exec(current_block, globals(), local_namespace)
                
                # Clear the block after successful execution
                current_block = ""
            except Exception as e:
                print(f"Runtime error in block: {e}")
                current_block = ""  # Reset the block after a runtime error
                
        except SyntaxError:
            # If we have a syntax error in the accumulated block,
            # don't reset yet - we might need more lines to complete the syntax
            pass
    
    return local_namespace
"""

    for i, block in enumerate(code):
        is_last_block = i == len(code) - 1

        # For all blocks except the last, use safe_exec_with_exports
        if not is_last_block:
            wrapped_block = (
                f"\n# Code block {i+1} (previous)\n"
                f"original_stdout, original_stderr = sys.stdout, sys.stderr\n"
                f"sys.stdout, sys.stderr = io.StringIO(), io.StringIO()\n"
                f"try:\n"
                f"    exported_vars = parse_and_exec_salvageable('''{block}''')\n"
                f"finally:\n"
                f"    sys.stdout, sys.stderr = original_stdout, original_stderr\n\n"
                f"    for name, value in exported_vars.items():\n"
                f"        globals()[name] = value\n"
            )
        else:
            # For the last (current) block, just include the code directly
            wrapped_block = f"\n# Code block {i+1} (current)\n{block}\n"

        wrapped_code += wrapped_block

    return wrapped_code


def clean_traceback(text, base_path):
    # Replace file paths in traceback
    pattern = re.compile(re.escape('File "' + base_path + "/"))
    return pattern.sub('File "', text)


# Set resource limits directly
def set_limits():
    # Memory limit (8GB)
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, resource.RLIM_INFINITY))
    # # Process limit
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT, resource.RLIM_INFINITY))
    # File size limit (500 MB)
    resource.setrlimit(resource.RLIMIT_FSIZE, (500 * 1024 * 1024, 500 * 1024 * 1024))


def execute_python(
    code: Union[str, List[str]],
    timeout: int = TIMEOUT,
    stdin: Optional[str] = None,
    python_path: str = None,
    pre_import_lib: bool = True,
    use_firejail: bool = False,
) -> Tuple[str, bool]:
    """
    Execute Python code in a Firejail sandbox with a timeout.

    Args:
        code: Python code string to execute
        stdin: Optional input to provide to the executed code

    Returns:
        String containing execution output or error message
    """
    # Check for forbidden imports first
    if check_forbidden_imports(code):
        return (
            "",
            "Execution blocked: Code contains potentially dangerous operations or imports.",
            True,
        )

    # Create a minimal environment instead of copying everything
    original_env = os.environ.copy()

    # set cwd to be a temp dir
    cwd = os.path.join(
        os.getcwd(), "tmp/firejail", str(uuid.uuid4().hex)
    )  # local tmp dir
    if not os.path.exists(cwd):
        os.makedirs(cwd, exist_ok=True)
    # write code to a temp file
    file_name = "main.py"
    file_path = os.path.join(cwd, file_name)
    code = wrap_code_blocks(code)

    if pre_import_lib:
        code = PRE_IMPORT_LIBS + code
    code = PRE_IMPORT_LIBS2 + code
    with open(file_path, "w") as f:
        f.write(code)
    # print(code)
    # command.extend(["python3", "-c", code])
    # command.extend(["python3", file_path])
    if not python_path:
        python_path = "python3"
    else:
        assert os.path.exists(python_path), f"Python path {python_path} does not exist."
    if use_firejail and filejail_command_exists:
        env = {}
        # Core system variables
        essential_vars = [
            "PATH",
            "HOME",
            "USER",
            "SHELL",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "TERM",
            # Python-specific
            "PYTHONIOENCODING",
            "PYTHONUNBUFFERED",
            "PYTHONHASHSEED",
            "PYTHONDONTWRITEBYTECODE",
            # Runtime optimization
            "MKL_NUM_THREADS",
            "OMP_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            # Temp directories
            "TMPDIR",
            "TEMP",
            "TMP",
            # Display if needed
            "DISPLAY",
            "XAUTHORITY",
        ]

        # Copy only essential variables if they exist
        for var in essential_vars:
            if var in original_env:
                env[var] = original_env[var]

        # Explicitly set optimization variables
        env["OPENBLAS_NUM_THREADS"] = "1"

        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]
        # Build the firejail command with resource limits
        command = [
            "firejail",
            "--quiet",
            "--seccomp=socket",
            "--noprofile",
            "--rlimit-nproc=32",
            "--rlimit-nofile=32",
            "--rlimit-fsize=2m",  # Limit file size
            "--rlimit-as=1096m",  # Limit address space
        ]
        command.extend([python_path, file_path])
        subprocess_cwd = cwd
    else:
        env = original_env
        command = [python_path, file_name]
        subprocess_cwd = (
            cwd  # Use the temporary directory as the current working directory
        )

    has_error = False
    try:
        result = subprocess.run(
            command,
            input=stdin if stdin else None,
            env=env,
            text=True,
            capture_output=True,
            preexec_fn=set_limits,
            timeout=timeout,
            cwd=subprocess_cwd,
        )
        # Clean both stdout and stderr
        stdout = clean_traceback(result.stdout, cwd)
        stderr = clean_traceback(result.stderr, cwd)
        stderr = stderr if stderr else ""
        if stderr:
            has_error = True
    except subprocess.TimeoutExpired as e:
        has_error = True
        stdout = e.stdout if e.stdout else ""
        stderr = e.stderr if e.stderr else ""
        stdout = stdout.decode("utf-8") if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode("utf-8") if isinstance(stderr, bytes) else stderr
        stderr += f"Execution timed out after {timeout} seconds.\n"
    # Clean up the temporary file
    try:
        # remove cwd
        if os.path.exists(cwd):
            shutil.rmtree(cwd)
    except Exception:
        pass
    assert isinstance(
        stdout, str
    ), f"Expected stdout to be a string, got {type(stdout)}"
    assert isinstance(
        stderr, str
    ), f"Expected stderr to be a string, got {type(stderr)}"
    return stdout, stderr, has_error


class PythonCodeTool:
    tool_type = "python_code"
    timeout = TIMEOUT
    stop_tokens = ["```output", "<output>", "<tool_call>"]
    enable_history_code_execution = False
    done_without_error = False
    python_path = None
    pre_import_lib = True
    use_firejail = False

    def parse_action(self, action: str) -> Tuple[str, bool]:
        """
        Parse the raw action string (which is the llm response) into an actual action and its contents.
        Ensures that the parsed code is valid and safe for execution.

        Args:
            action: Raw action string containing Python code

        Returns:
            Tuple containing the extracted code and a validity flag
        """
        # Try to find Python code in various formats
        all_valid_python_code = re.findall(r"<python>(.*?)</python>", action, re.DOTALL)

        if not all_valid_python_code:
            all_valid_python_code = re.findall(
                r"```\n?python(.*?)```", action, re.DOTALL
            )

        # if not all_valid_python_code:
        #     all_valid_python_code = re.findall(r"<tool_call>(.*?)</tool_call>", action, re.DOTALL)

        if len(all_valid_python_code) == 0:
            return "", False

        # # Use the first code block found (we could extend this to support multiple blocks)
        # parsed_code = all_valid_python_code[0].strip()

        # use all the code blocks
        parsed_code = "\n".join([code.strip() for code in all_valid_python_code])

        return parsed_code, True

    def conduct_action(self, action, extra_field):
        """
        Execute the parsed action in a Firejail sandbox.

        Args:
            trajectory_id: ID for tracking the action
            action: Raw action string
            extra_field: Additional parameters

        Returns:
            Tuple containing observation, done flag, and validity flag
        """
        parsed_action, is_valid = self.parse_action(action)

        if not is_valid:
            # observation = "No valid Python code found. Please provide code in either <python>...</python> tags or ```python...``` code blocks."
            observation = ""
            execution_result = ""
            has_error = True
            code_to_execute = None
            return None, True, parsed_action
        else:
            # Extract stdin if provided in extra_field
            stdin = extra_field.get("stdin", "") if extra_field else None

            test_input = re.findall(r"```input\n(.*?)\n```", action, re.DOTALL)
            if len(test_input) > 0:
                stdin = test_input[0].strip()

            code_to_execute = parsed_action

            stdout, stderr, has_error = execute_python(
                code_to_execute,
                self.timeout,
                stdin,
                self.python_path,
                self.pre_import_lib,
                self.use_firejail,
            )
            execution_result = stdout + "\n" + stderr
            execution_result = execution_result.strip(" \n")
            observation = execution_result

        return observation, has_error, code_to_execute


if __name__ == "__main__":
    tool = PythonCodeTool()
    print(
        tool.conduct_action(
            "dsads```python\nprint(web_search('Who is the president of US in 2004', 4))#\nprint(visit_webpage('https://pubmed.gov/article/pubmed23n0054_6578'))```",
            {},
        )[0]
    )
