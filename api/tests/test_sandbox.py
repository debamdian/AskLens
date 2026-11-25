"""Unit tests for the isolated Python analysis sandbox."""

import pytest
from app.analysis.sandbox import PythonSandbox, SandboxExecutionError


@pytest.fixture
def sandbox():
    return PythonSandbox(timeout_seconds=3)


def test_sandbox_valid_computation(sandbox):
    code = """
import numpy as np
arr = np.array([10, 20, 30, 40, 50])
mean_val = float(np.mean(arr))
print(json.dumps({"mean": mean_val}))
"""
    result = sandbox.execute_code(code)
    assert result.get("mean") == 30.0


def test_sandbox_blocks_os_system(sandbox):
    code = "import os; os.system('echo hacked')"
    with pytest.raises(SandboxExecutionError, match="Banned keyword"):
        sandbox.execute_code(code)


def test_sandbox_blocks_subprocess(sandbox):
    code = "import subprocess; subprocess.run(['calc'])"
    with pytest.raises(SandboxExecutionError, match="Banned keyword"):
        sandbox.execute_code(code)


def test_sandbox_blocks_network_socket(sandbox):
    code = "import socket; s = socket.socket()"
    with pytest.raises(SandboxExecutionError, match="Banned keyword"):
        sandbox.execute_code(code)


def test_sandbox_timeout_enforcement():
    slow_sandbox = PythonSandbox(timeout_seconds=1)
    code = """
import time
time.sleep(3)
print(json.dumps({"done": True}))
"""
    with pytest.raises(SandboxExecutionError, match="Execution Timeout"):
        slow_sandbox.execute_code(code)
