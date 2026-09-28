from ollama import Client


def calculator(expression: str) -> str:
    """Calculate a simple expression such as 5 + 2 or 27 * 14."""
    allowed = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a / b if b != 0 else None,
    }

    parts = expression.strip().split()

    if len(parts) != 3:
        return "Rejected: use the format number operator number."

    left, operator, right = parts

    try:
        left = float(left)
        right = float(right)
    except ValueError:
        return "Rejected: both values must be numbers."

    if operator not in allowed:
        return "Rejected: only +, -, *, and / are allowed."

    result = allowed[operator](left, right)

    if result is None:
        return "Rejected: cannot divide by zero."

    return str(result)


client = Client(timeout=300)

messages = [
    {
        "role": "user",
        "content": "Use the calculator tool to calculate 5 + 3."
    }
]

response = client.chat(
    model="nemotron-3-super:cloud",
    messages=messages,
    tools=[calculator],
    think=False,
    options={"num_predict": 64},
)

if response.message.tool_calls:
    messages.append(response.message)

    for tool_call in response.message.tool_calls:
        if tool_call.function.name == "calculator":
            arguments = tool_call.function.arguments
            result = calculator(**arguments)

            print("Tool called:", tool_call.function.name)
            print("Arguments:", arguments)
            print("Tool result:", result)

            messages.append({
                "role": "tool",
                "tool_name": "calculator",
                "content": result,
            })

    final_response = client.chat(
        model="nemotron-3-super:cloud",
        messages=messages,
    )

    print("Final answer:", final_response.message.content)

else:
    print("The model did not request the calculator tool.")
    print("Model response:", response.message.content)