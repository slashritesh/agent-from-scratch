import instructor
from groq import Groq
from pydantic import BaseModel
from typing import Literal
import os
from dotenv import load_dotenv

# client intialization
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
client = instructor.from_groq(groq, instructor.Mode.JSON)


load_dotenv()

messages = []


class QueryValidator(BaseModel):
    label: Literal["low_context", "restrict_action", "response_action"]
    response: str


class LowContextResponse(BaseModel):
    res: str


def handle_low_context(input_prompt):
    system_prompt = f"""
   You are an intelligent expense-tracking assistant. Your job is to identify incomplete user inputs and ask relevant follow-up questions to gather full expense details.

### Objective:
If the user's input lacks key details (like amount and item_name ), ask a clarifying question to complete their intent.

### Guidelines:
1. **Identify missing details** → If a user says, "I bought jeans from Zara," ask, **"How much did you spend?"**  
2. **Ensure clarity** → If a user says, "Dinner expense," ask, **"How much did you spend and when?"**  
3. **Make responses conversational** → Keep the tone natural and helpful.
3. **Use Perivious Conversation** → To understand full context you can use previous chat as well and ask for confirmation if you get deatils for tools

#### User's recent input:
{input_prompt}

Generate a relevant question to complete the intent.
    """
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_model=LowContextResponse,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    messages.append({"role":"assitant","content":res})

    return res


def query_validator(prompt) -> QueryValidator:
    system_prompt = """
You are an advanced NLP expert named Ritesh. Your task is to classify user queries in an expense tracker chat system into one of the following categories:

1. **low_context** → The query lacks details. Ask a follow-up question to complete it.
   - Example: "I bought jeans from Zara." → "How much did you spend?"  

2. **restrict_action** → The query involves a restricted or invalid action.
   - Example: "Delete all expenses!"  

3. **response_action** → The query is clear and should be answered directly.
   - Example: "Get my expenses from last week." → Provide the requested data.  
   - Example: "Hi" → "Hello! How can I help you track your expenses?"  

Additionally, always provide a relevant response in **response_action** queries and a clarifying question for **low_context** queries.
"""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_model=QueryValidator,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    return res


while True:
    prompt = input("User : ")
    messages.append({'role':'user','content':prompt})
    res = query_validator(prompt)

   

    if res.label == "low_context":
        context = handle_low_context(prompt)
        messages.append({'role':'assistant','content': context.res})
        print("🤖 : ", context.res)

    else:
        print("🤖 : ", res.response)
        messages.append({'role':'assistant','content': res.response})
