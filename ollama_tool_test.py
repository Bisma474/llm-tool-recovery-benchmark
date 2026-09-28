import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def calculator(expression: str) -> str:
    parts = expression.strip().split()

    if len(parts) != 3:
        return "Rejected: use number operator number."

    left_text, operator, right_text = parts

    try:
        left = float(left_text)
        right = float(right_text)
    except ValueError:
        return "Rejected: both values must be numbers."

    if operator == "+":
        result = left + right
    elif operator == "-":
        result = left - right
    elif operator == "*":
        result = left * right
    elif operator == "/":
        if right == 0:
            return "Rejected: cannot divide by zero."
        result = left / right
    else:
        return "Rejected: unsupported operator."

    return str(result)


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate one basic arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Example: 5 + 2 or 27 * 14"
                    }
                },
                "required": ["expression"],
                "additionalProperties": False
            }
        }
    }
]

messages = [
    {
        "role": "user",
        "content": "Use the calculator tool to calculate 5 + 2."
    }
]

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    tools=tools,
    tool_choice="auto",
    max_tokens=128,
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    }
)

assistant_message = response.choices[0].message

if not assistant_message.tool_calls:
    print("The model did not request the calculator.")
    print("Model answer:", assistant_message.content)
else:
    messages.append(assistant_message)

    for tool_call in assistant_message.tool_calls:
        if tool_call.function.name != "calculator":
            print("Rejected unknown tool:", tool_call.function.name)
            continue

        arguments = json.loads(tool_call.function.arguments)
        result = calculator(**arguments)

        print("Tool called:", tool_call.function.name)
        print("Arguments:", arguments)
        print("Tool result:", result)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    final_response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
        max_tokens=128,
        extra_body={
            "thinking": {
                "type": "disabled"
            }
        }
    )

    print("Final answer:", final_response.choices[0].message.content)