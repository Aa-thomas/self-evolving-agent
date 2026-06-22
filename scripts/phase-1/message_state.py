## =============================================================================
## Imports
## =============================================================================
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

messages = []


## =============================================================================
## Application
## =============================================================================
@app.command()
def message_state(new_message: str) -> None:
    # messages must be objects that follow this form
    user_message = {"role": "user", "content": new_message}

    # append mutates the messages array in place. it does not return the array. it returns None
    messages.append(user_message)

    # capture llm response
    response = client.chat.completions.create(
        model="cohere/north-mini-code:free",
        messages=messages,
    )

    assistant_content = response.choices[0].message.content

    assistant_message = {"role": "assistant", "content": assistant_content}

    # append llm response
    messages.append(assistant_message)

    print(messages)


## =============================================================================
## Program Init
## =============================================================================
if __name__ == "__main__":
    app()
