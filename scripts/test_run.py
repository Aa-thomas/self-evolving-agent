import json
import typer
import subprocess


## JSON TESTS
## =============================================================================
def test_readjson():
    with open("scripts/jsonfile.json", "r") as file:
        result = json.load(file)

    expected = {"name": "John", "age": 30, "city": "New York"}

    assert result == expected


def test_writejson():
    # this is the data that will be written
    data = {"name": "sathiyajith", "rollno": 56, "cgpa": 8.6, "phone": "9976770500"}

    # this is the act of writing the data
    with open("scripts/write.json", "w") as file:
        json.dump(data, file)

    # this is where we open the file that was written
    with open("scripts/write.json", "r") as file:
        result = json.load(file)

    # this is where we check that the result of opening the file is equal to the data we expected to be written
    assert result == data


def test_validatekeys():
    # open the file and save it to result
    with open("scripts/write.json", "r") as file:
        result = json.load(file)

    expected_name = "sathiyajith"
    expected_rollno = 56
    expected_cgpa = 8.6
    expected_phone = "9976770500"

    assert result["name"] == expected_name


## =============================================================================
## CLI TESTS
## =============================================================================
app = typer.Typer()


@app.command()
def hello():
    print("hello")


@app.command()
def goodbye():
    print("goodbye")


@app.command()
def print_json() -> None:
    name = typer.prompt("What is your name?")
    age = typer.prompt("What is your age?")

    json = {"name": name, "age": age}

    print(json)


@app.command()
def run(command: str) -> None:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    data = {
        "command": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
    }

    print(data)


@app.command()
def timeout(command: str, timeout: int = 3) -> None:
    try:
        result = subprocess.run(
            command.split(), capture_output=True, text=True, timeout=timeout
        )

        data = {
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "timed_out": False,
        }

    except subprocess.TimeoutExpired as err:
        data = {
            "command": command,
            "stdout": err.stdout,
            "stderr": err.stderr,
            "exit_code": None,
            "timed_out": True,
        }

        print(data)


if __name__ == "__main__":
    app()
