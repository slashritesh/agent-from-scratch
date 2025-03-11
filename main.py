import json
import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from artifacts.prompt import system_prompt

load_dotenv()

# client = instructor.from_groq(Groq(api_key= os.getenv("GROQ_API_KEY")),instructor.Mode.JSON)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


st.title("AI Chat Interface")


if prompt := st.chat_input("What is up?"):
    with st.chat_message("user"):
        st.write(prompt)

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    with st.chat_message("assistant"):
        chat = client.chat.completions.create(
            messages=messages,
            response_format={"type": "json_object"},
            model="llama-3.3-70b-versatile",
        )
        result = json.loads(chat.choices[0].message.content)

        print(result)
        st.markdown(result["type"])
