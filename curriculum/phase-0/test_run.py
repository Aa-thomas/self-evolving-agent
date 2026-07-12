import json
import subprocess
from pathlib import Path

import typer

FIXTURES = Path(__file__).resolve().parent

# =============================================================================
# JSON TESTS
# =============================================================================


def test_readjson():
    # Open an existing JSON file in read mode.
    with (FIXTURES / "jsonfile.json").open("r") as file:
        # Convert the JSON file contents into a Python dictionary.
        result = json.load(file)

    # The dictionary we expect to get from the file.
    expected = {"name": "John", "age": 30, "city": "New York"}

    # Confirm the loaded JSON matches the expected dictionary.
    assert result == expected


def test_writejson(tmp_path: Path):
    # The dictionary that will be written to the JSON file.
    data = {"name": "sathiyajith", "rollno": 56, "cgpa": 8.6, "phone": "9976770500"}

    output = tmp_path / "write.json"

    # Open/create a temporary output file and write the dictionary as JSON.
    with output.open("w") as file:
        json.dump(data, file)

    # Re-open the written file in read mode.
    with output.open("r") as file:
        # Convert the JSON file contents back into a Python dictionary.
        result = json.load(file)

    # Confirm the data read from the file matches what we originally wrote.
    assert result == data


def test_validatekeys():
    # Open the previously written JSON file.
    with (FIXTURES / "write.json").open("r") as file:
        # Convert the JSON file contents into a Python dictionary.
        result = json.load(file)

    # Expected values for specific dictionary keys.
    expected_name = "sathiyajith"
    expected_rollno = 56
    expected_cgpa = 8.6
    expected_phone = "9976770500"

    # Check that each key contains the expected value.
    assert result["name"] == expected_name
    assert result["rollno"] == expected_rollno
    assert result["cgpa"] == expected_cgpa
    assert result["phone"] == expected_phone


# =============================================================================
# CLI TESTS / COMMANDS
# =============================================================================

# Create the Typer application object.
# Every @app.command() function becomes a CLI command.
app = typer.Typer()


@app.command()
def hello():
    # Print a basic message to stdout.
    print("hello")


@app.command()
def goodbye():
    # Print a basic message to stdout.
    print("goodbye")


@app.command()
def print_json() -> None:
    # Ask the user for their name from the terminal.
    name = typer.prompt("What is your name?")

    # Ask the user for their age and convert it to an integer.
    age = typer.prompt("What is your age?", type=int)

    # Store the captured values in a dictionary.
    data = {"name": name, "age": age}

    # Print the dictionary to stdout.
    print(data)


@app.command()
def run(command: str) -> None:
    # Run the command through the shell.
    # shell=True allows commands like "ls -la" as one string.
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Store the command result in a structured dictionary.
    data = {
        "command": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
    }

    # Print the captured result.
    print(data)


@app.command()
def timeout(command: str, timeout: int = 3) -> None:
    try:
        # Run the command with a maximum allowed runtime.
        # command.split() turns "echo hello" into ["echo", "hello"].
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # If the command finishes before the timeout, store the normal result.
        data = {
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "timed_out": False,
        }

    except subprocess.TimeoutExpired as err:
        # If the command takes too long, Python raises TimeoutExpired.
        data = {
            "command": command,
            "stdout": err.stdout or "",
            "stderr": err.stderr or "",
            "exit_code": None,
            "timed_out": True,
        }

    # Print the result whether it succeeded or timed out.
    print(data)


# =============================================================================
# SANDBOXING
# =============================================================================

# The only folder this program should allow file access inside.
# resolve() converts it into an absolute path.
SANDBOX_DIR = Path("sandbox").resolve()


def validate_path(user_path: str) -> Path:
    # Combine the sandbox folder with the user-provided path.
    # resolve() cleans up things like "../" and gives the real absolute path.
    safe_path = (SANDBOX_DIR / user_path).resolve()

    # Reject the path if it is not actually inside the sandbox folder.
    if not safe_path.is_relative_to(SANDBOX_DIR):
        raise ValueError("Path traversal rejected")

    # Return the validated safe path.
    return safe_path


# =============================================================================
# PROGRAM INIT
# =============================================================================

# This only runs the Typer app when this file is executed directly.
# It does not run when the file is imported by pytest or another module.
if __name__ == "__main__":
    app()
