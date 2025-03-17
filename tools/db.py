import requests


def add_expense(title: str, amount: float, category: str):
    """
    Sends a POST request to add a new expense.

    :param title: Name of the expense item (e.g., 'Lunch', 'Groceries').
    :param amount: Amount spent (e.g., 15.75).
    :param category: Category of the expense (e.g., 'Food', 'Rent').
    :return: Response JSON or error message.
    """
    url = "http://localhost:3030/api/expenses"  # API Endpoint
    data = {
        "title": title,
        "amount": amount,
        "category": category
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
        return response.json()  # Return JSON response if successful
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_all_expenses():
    """
    Sends a GET request to retrieve all expenses.

    :return: List of expenses (JSON) or error message.
    """
    url = "http://localhost:3030/api/expenses"  # API Endpoint

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
        return response.json()  # Return list of expenses
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def search_expenses(title: str):
    """
    Sends a GET request to search for expenses by title (case-insensitive).

    :param title: Title or partial title of the expense to search for.
    :return: List of matching expenses (JSON) or error message.
    """
    url = "http://localhost:3030/api/expenses/search"  # API Endpoint
    params = {"title": title}  # Query parameter

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
        return response.json()  # Return list of found expenses
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

