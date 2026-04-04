import subprocess


def bash_execute(command: str, shell: bool = True, timeout: int = 30) -> dict:
    """Execute a shell command. Returns output, stderr, and exit code."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "output": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"output": "", "stderr": f"Command timed out after {timeout}s", "exit_code": -1}
    except Exception as e:
        return {"output": "", "stderr": str(e), "exit_code": -1}
