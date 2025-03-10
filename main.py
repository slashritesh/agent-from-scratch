import json
from groq import Groq
import os
import instructor
from pydantic import BaseModel, Field


# GENERAL_MODEL = ""
# TOOLCALL_MODEL = ""

tool_schema = {
    "name": "get_weather_info",
    "description": "Get the weather information for any location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location for which we want to get the weather information (e.g., New York)",
            }
        },
        "required": ["location"],
    },
}


class ToolCall(BaseModel):
    input_text: str = Field(description="The user's input text")
    tool_name: str = Field(description="The name of the tool to call")
    tool_parameters: str = Field(description="JSON string of tool parameters")


class ResponseModel(BaseModel):
    tool_calls: list[ToolCall]

class EndResponseModel(BaseModel):
    content : str = Field("return location and tempreture with natural response")


client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")))

# Define hook functions
def log_kwargs(**kwargs):
    print(f"Function called with kwargs: {kwargs}")


def log_exception(exception: Exception):
    print(f"An exception occurred: {str(exception)}")

client.on("completion:kwargs", log_kwargs)
client.on("completion:error", log_exception)

def get_weather_info(location):
    return f"30 clecius : {location}"


available_tools = {"get_weather_info": get_weather_info}

messages = [
    {
        "role": "system",
        "content": f"You are an assistant that can use tools. You have access to the following tool: {tool_schema} and Extract event meeting details from give context and user message",
    }
]


def call_llm(user_input) -> ResponseModel:
    messages.append(
        {"role": "user", "content": user_input},
    )

    res,complition = client.chat.completions.create_with_completion(
        response_model=ResponseModel, messages=messages, model="llama-3.3-70b-versatile"
    )

    return res


# tool_calls = call_llm(user_prompt)
# print(tool_calls[0])



async def call_with_tools(tool_calls):
    # calling tools
    for tool_call in tool_calls:
        func_name = tool_call.tool_name
        call_func = available_tools[func_name]
        func_args = json.dumps(tool_call.tool_parameters)
        func_res = await call_func(func_args)

    messages.append(
        {
            "role": "tool",
            "content": str(func_res),
            "tool_name": available_tools[func_name],
        }
    )

    res, compeltion = await client.chat.completions.create_with_completion(
        messages=messages,response_model=EndResponseModel, model="llama-3.3-70b-versatile"
    )

    return res




user_prompt = "What's the weather like in Mumbai City?"

llm_res = call_llm(user_prompt)
print(llm_res)


result = call_with_tools(tool_calls=llm_res.tool_calls)
print(result)
