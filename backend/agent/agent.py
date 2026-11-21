import inspect
from typing import Callable, Dict, Any, List

from google import genai
from google.genai import types
from backend.config import settings
from backend.tools.customer_tools import get_customer_metrics
from backend.tools.product_tools import get_top_products
from backend.tools.sales_tools import generate_chart, get_monthly_revenue, get_sales_metrics
from backend.agent.prompts import SYSTEM_PROMPT

# import asyncio

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)

ALL_TOOLS: List[Callable] = [
    get_sales_metrics,
    get_monthly_revenue,
    get_top_products,
    get_customer_metrics,
    generate_chart,
]

TOOL_MAP: Dict[str, Callable] = {fn.__name__: fn for fn in ALL_TOOLS}

# tool execution function
async def execute_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """
    Safely executes a registered tool function.
    Handles both async coroutines and regular synchronous functions,
    plus catches exceptions so the agent doesn't crash on bad inputs
    """
    if tool_name not in TOOL_MAP:
        return {"error": f"{tool_name} is not recognized."}

    func = TOOL_MAP[tool_name]

    try:
        if inspect.iscoroutinefunction(func):
            return await func(**args)
        else:
            result = func(**args)
        return result
    except Exception as e:
        return {"error": f"failed execution {tool_name}: {str(e)}"}
    
# agent runner loop
async def run_agent(user_question: str) -> Dict[str, Any]:
    """
    Main Agent reasoning & tool-execution loop:
    1. Creates an async chat session configured with system prompt and tools.
    2. Sends the user's question.
    3. If Gemini asks to call one or more tools, executes them asynchronously.
    4. Feeds the data back to Gemini using Part.from_function_response.
    5. Repeats if Gemini needs more information (multi-step reasoning).
    6. Returns the grounded text answer and a log of tools called.
    """

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        temperature=0.2,
    )

    chat = client.aio.chats.create(
        model="gemini-3.5-flash-lite",
        config=config
    )

    tools_used: List[Dict[str, Any]] = []
    chart_path = None

    response = await chat.send_message(user_question)

    step = 0
    max_steps = 5

    while response.function_calls and step < max_steps:
        step += 1
        function_response_parts = []

        for call in response.function_calls:
            tool_name = call.name
            tool_args = dict(call.args) if call.args else {}

            tools_used.append({
                "tool_name": tool_name,
                "tool_args": tool_args,
            })

            tool_output = await execute_tool(tool_name, tool_args)

            if isinstance(tool_output, dict) and "chart_path" in tool_output:
                chart_path = tool_output["chart_path"]

            part = types.Part.from_function_response(
                name=tool_name,
                response={"result": tool_output},
            )
            function_response_parts.append(part)

        response = await chat.send_message(function_response_parts)

    return {
        "question": user_question,
        "answer": response.text,
        "tools_used": tools_used,
        "chart_path": chart_path,
    }

# async def main():
#     result = await run_agent("What are the top 5 products by revenue?")
#     print(result)

# if __name__ == "__main__":
#     asyncio.run(main())

