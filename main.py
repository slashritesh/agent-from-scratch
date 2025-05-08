import json
import os
from dotenv import load_dotenv
import streamlit as st
import instructor
from groq import Groq
from pydantic import BaseModel, Field
from typing import Literal
from tools.db import get_all_expenses, search_expenses, add_expense

load_dotenv()

# Client Initialization
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
client = instructor.from_groq(groq, instructor.Mode.JSON)

st.title("AI Powered Expense Tracker")

# Initialize message history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []


class ToolCall(BaseModel):
    input_text: str = Field(description="The user's input text")
    tool_name: str = Field(description="The name of the tool to call")
    tool_parameters: dict = Field(description="JSON string of tool parameters")


class ResponseModal(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[ToolCall]


class QueryValidator(BaseModel):
    res :  str

tool_schema = [
    {
        "name": "add_expense",
        "description": "Add an expense with details such as amount and item name.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "The amount spent (e.g., 50.75).",
                },
                "title": {
                    "type": "string",
                    "description": "The name of the item/service (e.g., 'Lunch').",
                },
                "category": {
                    "type": "string",
                    "description": "The category of the item (e.g., 'Personal','Travel').",
                },
            },
            "required": ["title", "amount", "category"],
        },
    },
    {
        "name": "get_all_expenses",
        "description": "Retrieve all expenses from the database.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "search_expenses",
        "description": "Search for expenses based on their title. The search is case-insensitive and supports partial matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title or partial title of the expense to search for.",
                }
            },
            "required": ["title"],
        },
    },
]

available_functions = {
    "add_expense": add_expense,
    "get_all_expenses": get_all_expenses,
    "search_expenses": search_expenses,
}

system_prompt = f"""
You are an AI assistant capable of using tools to assist users efficiently. You have access to the following tool: {tool_schema}.

<instruction>
    1. make sure never discuss about tools with user.
    2. tool calls must done one by one.
    3. Extarct tool name , parameters from user query only.
    4. use only tools if needed.
    5. after getting tool call ready then give sucess response like "xyz item addes sucessfully"
    6. Also get item name and amount spend get from user query.
    7. use privious chat as context if needed like may be you get item name fisrt and then in next query you will get prize.
</instruction> 

Example :
user - "i buy jeans from zara"
assiatant - "how much you spend on it"
user - "200 rs"
assistant - "added expense sucessfully (tool calls - tool='add_expense',tool_parameters=(item_name="jeans from zara",amount=200),input_text='"i buy jeans from zara" + "200 rs")"
"""


messages = [
    {"role": "system", "content": system_prompt},
    {"role":"user","content":"My name is Ritesh mane  Senior software engineer at brainfog"},
    *st.session_state.messages
]


def get_response(input_text: str) -> ResponseModal:
    """Generate response from LLM based on user input and message history."""
    messages = [
        {"role": "system", "content": system_prompt},
        *st.session_state.messages,
    ]

    res = client.chat.completions.create(
        messages=messages, model="llama-3.3-70b-versatile", response_model=ResponseModal
    )

    return res


def call_llm(input_text: str, context: str):
    """Generate response from LLM based on user input + Context give by db"""
    system_prompt = f"""
Given the following context:  
**Context:**  
{context}  

Respond to the user's input strictly based on the provided context. Ensure that the response is relevant, precise, and formatted using Markdown for better readability. If the input falls outside the given context, politely inform the user that you can only answer within the specified scope.  

Use appropriate formatting such as:  
- **Bold** for key points  
- *Italics* for emphasis  
- `Code blocks` for technical responses  
- Bullet points or tables for structured information when needed  
"""
    messages = [
        {
            "role": "system",
            "content": "Understand user query and decide weather you need more context or it need tool call response with item name and amount",
        },
        {"role": "user", "content": input},
    ]

    res = client.chat.completions.create(
        messages=messages, model="deepseek-r1-distill-llama-70b", response_model=ToolResponse
    )

    return res


# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# Chat input handling
if prompt := st.chat_input("Start Chatting"):
    with st.chat_message("user"):
        st.write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        result = get_response(prompt)

        if len(result.tool_calls) > 0:
            print("use tools :", len(result.tool_calls))
            for tool in result.tool_calls:
                func_args = tool.tool_parameters
                func_name = tool.tool_name
                func_to_call = available_functions[func_name]
                func_res = func_to_call(**func_args)

                context = json.dumps(func_res)
                tool_response = call_llm(input_text=tool.input_text, context=context)
                print(tool_response)

        

        st.markdown(result.content)
        st.session_state.messages.append(
            {"role": "assistant", "content": result.content}
        )
