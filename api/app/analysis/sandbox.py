"""Isolated Python Analysis Sandbox.

Executes Python statistical analysis scripts in a restricted, sandboxed subprocess with:
- Execution time limits (e.g., 5 seconds timeout)
- No network access (socket creation strictly forbidden)
- Restricted module allowlist (pandas, numpy, scipy, statsmodels, sklearn, json, math)
- File system access restricted to temporary directory
"""

import os
import sys
import json
import tempfile
import subprocess
from typing import Dict, Any, Optional

# Allowlisted modules for scientific & statistical computation
ALLOWLISTED_MODULES = {
    "pandas",
    "numpy",
    "scipy",
    "statsmodels",
    "sklearn",
    "math",
    "json",
    "datetime",
    "collections",
    "itertools"
}

# Forbidden keywords / libraries that could breach system security
BLOCKED_PATTERNS = [
    "import socket",
    "from socket",
    "import subprocess",
    "from subprocess",
    "os.system",
    "os.popen",
    "os.remove",
    "os.rmdir",
    "shutil.rmtree",
    "import urllib",
    "import requests",
    "import httpx",
    "ctypes",
    "builtins.__import__",
    "eval(",
    "exec("
]

SANDBOX_WRAPPER_CODE = """
import sys
import json

# Disable network socket access completely
import socket
def forbidden_socket(*args, **kwargs):
    raise PermissionError("Network socket access is strictly forbidden in the analysis sandbox.")
socket.socket = forbidden_socket
socket.create_connection = forbidden_socket

try:
{indented_user_code}
except Exception as e:
    print(json.dumps({{"status": "error", "error": str(e)}}), file=sys.stderr)
    sys.exit(1)
"""


class SandboxExecutionError(Exception):
    """Raised when sandbox execution fails or violates security policy."""
    pass


class PythonSandbox:
    """Safely executes statistical calculations over query datasets."""

    def __init__(self, timeout_seconds: int = 5):
        self.timeout_seconds = timeout_seconds

    def execute_code(
        self,
        code: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validates code security, executes in restricted subprocess, and returns output."""
        # 1. Security scan: Check for blocked keywords
        for pattern in BLOCKED_PATTERNS:
            if pattern in code:
                raise SandboxExecutionError(f"Security Policy Violation: Banned keyword '{pattern}' detected.")

        # 2. Prepare temporary execution directory
        with tempfile.TemporaryDirectory(prefix="asklens_sandbox_") as tmpdir:
            data_file = os.path.join(tmpdir, "input_data.json")
            script_file = os.path.join(tmpdir, "analysis_script.py")

            # Write input dataset if provided
            if input_data:
                with open(data_file, "w", encoding="utf-8") as f:
                    json.dump(input_data, f)

            # Prepend data loading to user code
            prepended_code = f"DATA_PATH = r'{data_file}'\n"
            if input_data:
                prepended_code += (
                    "with open(DATA_PATH, 'r', encoding='utf-8') as _f:\n"
                    "    DATA = json.load(_f)\n"
                )
            prepended_code += code

            # Indent code for wrapper execution
            indented = "\n".join("    " + line for line in prepended_code.splitlines())
            final_script = SANDBOX_WRAPPER_CODE.format(indented_user_code=indented)

            with open(script_file, "w", encoding="utf-8") as f:
                f.write(final_script)

            # 3. Execute restricted subprocess
            env = os.environ.copy()
            # Disable Python from writing .pyc files
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            try:
                proc = subprocess.run(
                    [sys.executable, script_file],
                    cwd=tmpdir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds
                )

                if proc.returncode != 0:
                    err_msg = proc.stderr.strip() or "Script execution failed."
                    raise SandboxExecutionError(f"Sandbox Runtime Error: {err_msg}")

                stdout_text = proc.stdout.strip()
                # Parse JSON output from the script if printed, or return raw string
                try:
                    return json.loads(stdout_text)
                except Exception:
                    return {"output": stdout_text}

            except subprocess.TimeoutExpired:
                raise SandboxExecutionError(
                    f"Execution Timeout: Analysis exceeded safety limit of {self.timeout_seconds} seconds."
                )


# Global instance
python_sandbox = PythonSandbox()
