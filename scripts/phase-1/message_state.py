import typer
from openai import OpenAI
from dotenv import load_dotenv
import os


## =============================================================================
## Setup
## =============================================================================
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

app = typer.Typer()


@app.command()
## =============================================================================
## Application
## =============================================================================
def message_state(messages: list, new_message: str) -> None:
    # messages must be objects that follow this form
    user_message = {"role": "user", "content": new_message}

    # append mutates the messages array in place. it does not return the array. it returns None
    messages.append(user_message)
    prompt = messages

    response = client.chat.completions.create(
        model="cohere/north-mini-code:free",
        messages=prompt,
    )

    print(response)


## =============================================================================
## Program Init
## =============================================================================
if __name__ == "__main__":
    app()
