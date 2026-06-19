import typer
from openai import OpenAI
import time
import json
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# # First API call with reasoning
# response = client.chat.completions.create(
#     model="cohere/north-mini-code:free",
#     messages=[
#         {"role": "user", "content": "How many r's are in the word 'strawberry'?"}
#     ],
#     extra_body={"reasoning": {"enabled": True}},
# )
#
# # Extract the assistant message with reasoning_details
# response = response.choices[0].message
#
# # Preserve the assistant message with reasoning_details
# messages = [
#     {"role": "user", "content": "How many r's are in the word 'strawberry'?"},
#     {
#         "role": "assistant",
#         "content": response.content,
#         # "reasoning_details": response.reasoning_details  # Pass back unmodified
#     },
#     {"role": "user", "content": "Are you sure? Think carefully."},
# ]
#
# # Second API call - model continues reasoning from where it left off
# response2 = client.chat.completions.create(
#     model="cohere/north-mini-code:free",
#     messages=messages,
#     extra_body={"reasoning": {"enabled": True}},
# )
#
app = typer.Typer()


@app.command()
def ask(prompt: str) -> None:
    start_time = time.perf_counter()

    response = client.chat.completions.create(
        model="cohere/north-mini-code:free",
        messages=[{"role": "user", "content": prompt}],
    )

    latency = time.perf_counter() - start_time

    message = response.choices[0].message
    usage = response.usage

    if usage:
        data = {
            "latency": latency,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }
    else:
        data = {"latency": latency}

    print(message.content)
    print(json.dumps(data, indent=2))


## =============================================================================
## Program Init
## =============================================================================
if __name__ == "__main__":
    app()
