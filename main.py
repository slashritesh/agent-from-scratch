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

class ToolResponse(BaseModel):
    content : str


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
You are an AI assistant designed to efficiently assist users in tracking expenses using tools. You have access to the following tool: {tool_schema}. Communicate in natural language response must be human language.

Tool Deatils :
1. add_expense – Add an expense with details such as amount and item name.
2. get_all_expenses – Retrieve all expenses from the database.
3. search_expenses – Search for expenses by title, case-insensitively.

Instructions:
- Never discuss tools with the user.
- Make sure be polite and respond in natural language.
- Extract tool name and parameters (item name, amount) only from user queries.
- Use tools only when needed and process tool calls one at a time.
- If a query is incomplete, ask follow-up questions to extract missing details.
- After preparing a tool call, provide a success confirmation:
Example: "Expense added successfully with item name for amount"
Leverage previous messages to infer missing details.
If a user provides an item name first, wait for the amount in the next message.
If a user provides an amount first, ask for the item name.
Example Scenarios
Scenario 1: Missing Amount (Infer from Follow-up Response)
User: "I bought jeans from Zara."
Assistant: "How much did you spend on it?"
User: "200 Rs."
✅ Assistant: "Expense added successfully."

(Tool call: tool='add_expense', tool_parameters='title': 'jeans from Zara', 'amount': 200)

Scenario 2: Amount First, Item Name Later (Infer from Context)
User: "I spent 500 today."
Assistant: "What did you spend it on?"
User: "Dinner at a restaurant."
✅ Assistant: "Expense added successfully with dinner expenses for 500"

(Tool call: tool='add_expense', tool_parameters='title': 'Dinner at a restaurant', 'amount': 500)

Scenario 3: Complete Details in One Input (No Follow-up Needed)
User: "I spent 300 on groceries."
✅ Assistant: "Expense added successfully with groceries for 300"

(Tool call: tool='add_expense', tool_parameters='title': 'groceries', 'amount': 300)
"""


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
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
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
