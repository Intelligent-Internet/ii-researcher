import asyncio
import logging
import multiprocessing
import sys
from io import StringIO
from typing import Dict
from ii_researcher.reasoning.tools.base import BaseTool
from ii_researcher.reasoning.config import ConfigConstants
from ii_researcher.reasoning.tools.registry import register_tool
from ii_researcher.reasoning.tools.tool_history import ToolHistory


@register_tool
class PythonExecutorTool(BaseTool):
    """Tool for Executing python code."""

    name = "execute_python"
    description = ("Executes Python code string. Note: Only print outputs are visible,"
                   "function return values are not captured. Use print statements to see results."
                   "source code of the page as a string")
    argument_schema: dict = {
        "code": {
            "type": "string",
            "description": "The Python code to execute. End with a print statements to see results",
        }
    }
    return_type = "string"
    suffix = ConfigConstants.CODE_SUFFIX

    @classmethod
    def reset(cls) -> None:
        """Reset the set of visited URLs."""
        pass

    async def execute(self, tool_history: ToolHistory = None, **kwargs) -> str:
        """Execute the python code."""
        code = kwargs.get("code", "")

        if not code:
            return "No code provided."

        result = await self._execute(code)

        if isinstance(result, Exception):
            logging.error("Error during code execution: %s", str(result))
            return f"Error executing code: {str(result)}\n"

        return str(result)

    async def _execute(
        self,
        code: str,
        timeout: int = 5,
    ) -> Dict:
        """
        Executes the provided Python code with a timeout.

        Args:
            code (str): The Python code to execute.
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'output' with execution output or error message and 'success' status.
        """

        with multiprocessing.Manager() as manager:
            result = manager.dict({"code_output": "", "success": False})
            if isinstance(__builtins__, dict):
                safe_globals = {"__builtins__": __builtins__}
            else:
                safe_globals = {"__builtins__": __builtins__.__dict__.copy()}
            proc = multiprocessing.Process(target=self._run_code, args=(code, result, safe_globals))
            proc.start()
            proc.join(timeout)

            # timeout process
            if proc.is_alive():
                proc.terminate()
                proc.join(1)
                return {
                    "code_output": f"Execution timeout after {timeout} seconds",
                    "success": False,
                }
            print("Execution Results")
            print(result)
            return dict(result)

    def _run_code(self, code: str, result_dict: dict, safe_globals: dict) -> None:
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            exec(code, safe_globals, safe_globals)
            result_dict["code_output"] = output_buffer.getvalue()
            result_dict["success"] = True
        except Exception as e:
            result_dict["code_output"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout


async def main():
    """Test the PythonExecutorTool."""
    # Create an instance of the tool
    python_executor = PythonExecutorTool()

    # Test with a simple print statement
    simple_code = """
print("Hello, World!")
x = 5
y = 10
print(f"The sum of {x} and {y} is {x + y}")
"""
    result = await python_executor.execute(code=simple_code)
    print("Simple code execution result:")
    print(result)

    # Test with some error code
    error_code = """
print("This will run")
# This will cause an error
1/0
print("This won't run")
"""
    result = await python_executor.execute(code=error_code)
    print("\nError code execution result:")
    print(result)

    # Test with a timeout
    timeout_code = """
import time
print("Starting long operation...")
time.sleep(10)  # This should timeout
print("This won't be printed due to timeout")
"""
    result = await python_executor.execute(code=timeout_code)
    print("\nTimeout code execution result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
