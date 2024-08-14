import pandas as pd
import requests
from shiny import reactive


def fetch_summary(month):
    response = requests.get("http://127.0.0.1:8000/transaction/summary", params={'month' : month})
    df = pd.DataFrame(response.json())
    return df


def fetch_data(month):
    response = requests.get("http://127.0.0.1:8000/transactions", params={'month' : month})

    data = response.json()
    columns = ['Date', 'Item', 'Amount', 'Category', 'id']
    if (len(data) == 0):
        return pd.DataFrame(columns=columns)
        
    df = pd.DataFrame(data)
    df.columns = columns

    df['Date'] = pd.to_datetime(df['Date'])
    df['Date'] = df['Date'].dt.strftime('%m/%d')

    return df
    

def fetch_months():
    response = requests.get("http://127.0.0.1:8000/tabs") 
    df = pd.DataFrame(response.json())

    df = df[['monthName', 'monthNum']]
    df = df.set_index('monthNum')['monthName'].to_dict()

    return df

def fetch_budget():
    response = requests.get("http://127.0.0.1:8000/budget") 
    df = pd.DataFrame(response.json())
    # df = df[['category', 'budget']]

    df.columns = ['Category', 'Budget', "ID"]

    return df

def add_month(monthName, monthNum):    
    response = requests.post("http://127.0.0.1:8000/tabs/", json={
        "monthName": monthName,
        "monthNum": int(monthNum),
        "year": 2024,
        "id" : 0
    })


def add_category(category, budget):    
    response = requests.post("http://127.0.0.1:8000/budget", json={
        "category": category,
        "budget": budget
    })

def add_transaction(date, item, category, amount):    
    response = requests.post("http://127.0.0.1:8000/transactions", json={
        "date": date,
        "item": item,
        "amount": amount,
        "category": category
    })

def edit_category(category_id, category, budget):
    url = "http://127.0.0.1:8000/budget/{budget_id}?category_id="+str(category_id)
    response = requests.patch(url, json={
        "category": category,
        "budget": budget,
        
    })

def delete_category(category_id):
    url = "http://127.0.0.1:8000/budget/{budget_id}?category_id="+str(category_id)
    response = requests.delete(url)


def update_transactions(id, payload):
    url = "http://127.0.0.1:8000/transactions/"+str(id)

    response = requests.patch(url, json=payload)

    print("table updated")
    print(response.json())


def batch_transactions(transactions):
    # data = transactions.to_dict(orient="records")

    # print(requests.post("http://127.0.0.1:8000/transactions", json=transactions[0]).json())
    for t in transactions:
        response = requests.post("http://127.0.0.1:8000/transactions", json=t)
        # print(response.json())
