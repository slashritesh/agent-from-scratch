from datetime import datetime

from groq import Groq

import os
from dotenv import load_dotenv

# client intialization
client = Groq(api_key=os.getenv("GROQ_API_KEY"))



load_dotenv()

messages = []


# Sample in-memory database (replace with actual database integration)
expenses_db = []
expense_id_counter = 1


def add_expense(amount: float, category: str, date: str = None, note: str = "") -> dict:
    """Adds a new expense record."""
    global expense_id_counter

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")  # Default to today's date

    expense = {
        "id": str(expense_id_counter),
        "amount": amount,
        "category": category,
        "date": date,
        "note": note,
    }
    expenses_db.append(expense)
    expense_id_counter += 1

    return {
        "status": "success",
        "message": "Expense added successfully",
        "data": expense,
    }


def update_expense(
    expense_id: str,
    amount: float = None,
    category: str = None,
    date: str = None,
    note: str = None,
) -> dict:
    """Updates an existing expense record."""
    for expense in expenses_db:
        if expense["id"] == expense_id:
            if amount is not None:
                expense["amount"] = amount
            if category is not None:
                expense["category"] = category
            if date is not None:
                expense["date"] = date
            if note is not None:
                expense["note"] = note

            return {
                "status": "success",
                "message": "Expense updated successfully",
                "data": expense,
            }

    return {"status": "error", "message": "Expense not found"}


def read_expense(filter: str = None, date_range: tuple = None) -> dict:
    """Retrieves expenses based on filter and date range."""
    filtered_expenses = expenses_db

    if filter:
        filtered_expenses = [
            exp
            for exp in expenses_db
            if filter.lower() in exp["category"].lower()
            or filter.lower() in exp["note"].lower()
        ]

    if date_range:
        start_date, end_date = date_range
        filtered_expenses = [
            exp for exp in filtered_expenses if start_date <= exp["date"] <= end_date
        ]

    return {"status": "success", "data": filtered_expenses}


def delete_expense(expense_id: str) -> dict:
    """Deletes an expense record."""
    global expenses_db
    expenses_db = [exp for exp in expenses_db if exp["id"] != expense_id]

    return {"status": "success", "message": "Expense deleted successfully"}


def call_llm(prompt):
    system_prompt = """
    You are an intelligent expense-tracking assistant that helps users manage their expenses through conversation.  
    You can **add, update, delete, and retrieve expenses** using the following tool calls:  

    ### **Available Tools:**  
        - `update_expense(expense_id: str, amount: float, category: str, date: str, note: str)` → Update an existing expense. 
        - `add_expense(amount: float, category: str, date: str, note: str)` → Add a new expense.  
        - `read_expense(filter: str, date_range: str)` → Retrieve expenses based on filters.  
        - `delete_expense(expense_id: str)` → Remove an expense.  
        
    ### **Response Handling:**  
    1. **Handle low-context queries**  
        - If details are missing, ask relevant follow-up questions before calling a tool.  
        - Example:  
            - **User:** "I bought jeans."  
            - **Assistant:** "How much did you spend?"  
            - **User:** "2000 Rs"  
            - **Assistant:** "You bought jeans for 2000 Rs. Can I add this expense?"  
            - (If confirmed, call `add_expense` with required parameters.)  
    
    2. **Confirm before executing tool calls**  
        - Before running a tool, **reconfirm** details with the user.  
        
    3. **Handle incorrect or vague inputs**  
    - If a user provides an unclear request, guide them toward a valid one.  
        - Example:  
        - **User:** "Delete all expenses!"  
        - **Assistant:** "Are you sure? This action cannot be undone."  
        
    4. **Ensure natural conversation flow**  
        - Maintain a friendly, concise, and user-friendly tone while handling expenses.  
        
    ### **User's Input:**  
    {input_prompt}  
    Process the query accordingly and determine if a tool call is required.
    
    """

    tools = [
        {
            "type": "function",
            "function": {
                "name": "add_expense",
                "description": "Add a new expense record",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "The amount spent in the expense",
                        },
                        "category": {
                            "type": "string",
                            "description": "The category of the expense, e.g., Food, Travel, Shopping",
                        },
                        "date": {
                            "type": "string",
                            "format": "date",
                            "description": "The date of the expense in YYYY-MM-DD format. Defaults to today’s date.",
                        },
                        "note": {
                            "type": "string",
                            "description": "An optional note for the expense",
                        },
                    },
                    "required": ["amount", "category"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_expense",
                "description": "Update an existing expense record",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expense_id": {
                            "type": "string",
                            "description": "The unique identifier of the expense to be updated",
                        },
                        "amount": {
                            "type": "number",
                            "description": "The updated amount spent",
                        },
                        "category": {
                            "type": "string",
                            "description": "The updated category of the expense",
                        },
                        "date": {
                            "type": "string",
                            "format": "date",
                            "description": "The updated date of the expense in YYYY-MM-DD format",
                        },
                        "note": {
                            "type": "string",
                            "description": "The updated note for the expense",
                        },
                    },
                    "required": ["expense_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_expense",
                "description": "Retrieve expense records based on filters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "A keyword to filter expenses by category or note",
                        },
                        "date_range": {
                            "type": "object",
                            "properties": {
                                "start_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "The start date for filtering expenses in YYYY-MM-DD format",
                                },
                                "end_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "The end date for filtering expenses in YYYY-MM-DD format",
                                },
                            },
                            "description": "Optional date range to filter expenses",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "delete_expense",
                "description": "Delete an expense record",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expense_id": {
                            "type": "string",
                            "description": "The unique identifier of the expense to be deleted",
                        }
                    },
                    "required": ["expense_id"],
                },
            },
        },
    ]

    res = client.chat.completions.create(
        tool_choice='auto',
        tools=tools,
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    print(res.choices[0].message.tool_calls)

    return res


## chatbot
while True:
    prompt = input("User : ")
    res = call_llm(prompt)
    print("🤖 : ", res.choices[0].message.content)

