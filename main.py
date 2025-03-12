import os
from dotenv import load_dotenv
import streamlit as st
import instructor
from groq import Groq
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()

# client intialization
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
client = instructor.from_groq(groq, instructor.Mode.JSON)


st.title("Ai Powered Expense Tracker")

if "messages" not in st.session_state:
    st.session_state.messages = []


class ToolCall(BaseModel):
    input_text: str = Field(description="The user's input text")
    tool_name: str = Field(description="The name of the tool to call")
    tool_parameters: str = Field(description="JSON string of tool parameters")


class ResponseModal(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[ToolCall]


class QueryValidator(BaseModel):
    type: Literal["context", "response"]
    user_input: str


tool_schema = {
    "name": "add_expense",
    "description": "Add an expense with details such as amount and item name.",
    "parameters": {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "The amount spent on the expense (e.g., 50.75).",
            },
            "item_name": {
                "type": "string",
                "description": "The name of the item or service purchased (e.g., 'Lunch', 'Groceries').",
            },
        },
        "required": ["item_name"],
    },
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


messages = [{"role": "system", "content": system_prompt}, *st.session_state.messages]



def get_response(input: str) -> ResponseModal:
    """generate response from llm for user prompt"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input},
    ]
    res = client.chat.completions.create(
        messages=messages, model="llama-3.3-70b-versatile", response_model=ResponseModal
    )
    return res


def query_validator(input: str) -> QueryValidator:
    """Validate query"""
    messages = [
        {"role": "system", "content": "Understand user query and decide weather you need more context or it need tool call response with item name and amount"},
        {"role": "user", "content": input},
    ]
    res = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
        response_model=QueryValidator,
    )
    return res


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if prompt := st.chat_input("Start Chatting"):
    with st.chat_message("user"):
        st.write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})


    with st.chat_message("assistant"):
        result = query_validator(prompt)
        print(result)
        st.markdown(result)
        st.session_state.messages.append(
            {"role": "assistant", "content": result.content}
        )

        print(messages)
