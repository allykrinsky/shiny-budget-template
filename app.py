

import faicons
import pandas as pd
# from shared import files_df, process, watch_folder, app_dir
from shiny import reactive, req
import datetime

from shiny.express import input, render, session, ui, output
import seaborn as sns
import requests
import shiny

from data import fetch_data, fetch_summary, fetch_months, add_month, fetch_budget, add_category, add_transaction, edit_category, delete_category, update_transactions, batch_transactions

ui.page_opts(fillable=True)

months = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}


with ui.sidebar(position="left", bg="#f8f8f8"):  
    # with ui.card():
        
        # with ui.card_header(class_="d-flex justify-content-between align-items-center"):
    ui.h1("2024 Budget Dashboard")

    # Month Selector
    options = reactive.Value(fetch_months())
    currentMonth = reactive.Value(datetime.datetime.today().month)
    # budgets = reactive.Value(fetch_budget())
    # print

    button_clicked = reactive.Value(False)

    @output()
    @render.ui
    def select_month():
        return ui.input_selectize(
            "add_tab",
            "Select a Month to view Transactions",
            options(),
            # selected="August"
            # selected=currentMonth.get() # this breaks it
        )  
    
    @reactive.effect
    @reactive.event(input.add_tab)
    def update_month():
    
        newMonth = input.add_tab()
        currentMonth.set(newMonth)


    
    # Create new month
    with ui.popover(title="New Month", placement='left'):
        ui.input_action_button("newtab", "New Month")
        ui.input_select(  
            "monthNum",  
            "New Monthly Expense Report",  
            months,  
        )
        ui.input_action_button("add", "Create New")

        @render.text()
        @reactive.event(input.add)
        def submit():
            num = input.monthNum()
            add_month(months[int(num)], num)

    uploaded_data = reactive.Value(None)  
    ui.input_file("file_upload", "(Optional) Upload CSV File", multiple=False)
    @reactive.Effect
    @reactive.event(input.file_upload)
    def read_uploaded_file():
        # Get the file info
        file_info = input.file_upload()
        if file_info is None:
            uploaded_data.set(None)
            return
        
        file_content = file_info[0]["datapath"]
        csv_data = pd.read_csv(file_content)

        csv_data.columns = ['date', 'item', 'amount', 'category']

        csv_data['date'] = pd.to_datetime(csv_data['date'])
        csv_data['date'] = csv_data['date'].apply(lambda x: x.isoformat())

        data = csv_data.to_dict(orient="records")
        batch_transactions(data)
        uploaded_data.set(csv_data)
    

with ui.layout_columns(col_widths=[8, 4]):

    # Update dropdown options when the button is clicked
    @reactive.Effect
    def update_dropdown():
        if input.add() > 0:  # Check if the button has been clicked
            options.set(fetch_months())  # Refresh options
        

    # Summary Viz
    with ui.card():
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Monthly Summary"
        
        # Render Summary Chart
        @render.plot
        def category_sum():
            df = fetch_summary(month=currentMonth.get())
            
            if len(df) > 0:
                df['percent'] = (df['total'] / df['budget']) * 100
                
                
                def choose_color(precent):
                    if precent < 50:
                        return "low"
                    elif precent < 90:
                        return "med"
                    else :
                        return "high"
                
                df['color'] = [choose_color(i) for i in df['percent']] #TODO fix thiis 
                colors = {
                    "low": "#a7e8bd", 
                    "med" : "#ffd97d",
                    "high": "#ee6055"
                }

                df['total'] = "$" + df['total'].astype('int').astype('str')
             
                ax = sns.barplot(df, x='percent', y='category') 
                for container in ax.containers:
                    ax.bar_label(container, labels=df['total'], label_type='edge', padding=5)
                    for i, bar in enumerate(container):
                        color = colors[df['color'][i]]
                        bar.set_facecolor(color)

            else :
                ax = sns.barplot(df) 
            
            ax.set(title="Monthly Budget Status", xlabel='Progress (%)', ylabel='Budget Category')
            sns.despine(left=True, bottom=True)

    
    def budgets():
        return fetch_budget()
    
    
    def get_cat_id(cat):
        df = budgets()

        result = df.loc[df['Category'] == cat, 'ID']
        if not result.empty:
            return result.iloc[0]
        else:
            return None
        

    def budget_list():
        return budgets()['Category'].tolist()
        
    # Budget Card
    with ui.card():
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "View Budget"
            with ui.popover(title="Edit Budget Category", placement="left"):
                faicons.icon_svg("pencil")

                ui.input_select(
                    "editCat",
                    "Budget Category",
                    budget_list()  
                )
                ui.input_text("editBudget", "Budget", placeholder="Budget...") 
                ui.input_action_button("submitEdit", "Save")
                ui.input_action_button("submitDelete", "Delete")

                @render.text()
                @reactive.event(input.submitEdit)
                def editBud():
                    edit_category(get_cat_id(input.editCat()), input.editCat(), input.editBudget())

                @render.text()
                @reactive.event(input.submitDelete)
                def deleteCat():
                    delete_category(get_cat_id(input.editCat()))

                @reactive.Effect
                def refresh_budget():
                    if input.submitEdit() or input.submitDelete():
                        # render_budget()
                        print("edit")


            with ui.popover(title="New Budget Category", placement="left"):
                faicons.icon_svg("plus")
                # ui.input_action_button("newCat", "Manage Budget")

                ui.input_text("catName", "Category", placeholder="Category...") 
                ui.input_text("budget", "Budget", placeholder="Budget...") 
                ui.input_action_button("submitCat", "Add")

                @render.text()
                @reactive.event(input.submitCat)
                def newBudget():
                    add_category(input.catName(), input.budget())

        # data_summary = reactive.value(fetch_summary(currentMonth.get()))
        
        #Budget Df
        @render.data_frame
        def render_budget():
            data = fetch_summary(currentMonth.get())
            # print(data)
            data.columns = ['Category', 'Total', "Budget"]
            return render.DataTable(data)      
        
    # Transaction Card
    with ui.card():
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Monthly Transactions"

            # Create new transaction
            with ui.popover(title="New Transaction", placement="left"):
                
                faicons.icon_svg("plus")
                
                ui.input_date("date", "Date")
                ui.input_text("tName", "Item", placeholder="Item...") 
                ui.input_select(
                    "addBCat",
                    "Budget Category",
                    budget_list()  
                )
                ui.input_text("tAmount", "Amount", placeholder="Amount...") 

                ui.input_action_button("submitBudget", "Add")

                @render.text()
                @reactive.event(input.submitBudget)
                def newTransaction():
                    add_transaction(date=str(input.date()), item=input.tName(), amount=input.tAmount(), category=input.addBCat())


        # @reactive.calc
        @render.code
        def rows():
            # print("is this even working")
            data_ids = fetch_data(month=currentMonth.get())

            old_data = show_transactions.data()
            # print("old data")
            # print(old_data.head())

            data_selected = show_transactions.data_view()
            # print("new data")
            # print(data_selected.head())
            diff = []
            if len(data_selected) > 0 :
                diff = data_selected.compare(old_data)
                # print(diff)
        
            if len(diff) > 0 :
                row = data_ids.iloc[diff.index, :]
                id = row['id'].iloc[0]
                new_data = data_selected.iloc[diff.index, :]
                # print(new_data)
                payload = {
                    "date": str(datetime.datetime.strptime(new_data["Date"].iloc[0]+"/2024", "%m/%d/%Y")),
                    "item": new_data['Item'].iloc[0],
                    "amount": new_data["Amount"].iloc[0],
                    "category": new_data["Category"].iloc[0],
                    "id": str(id)
                }
                # print(payload)
        
                return update_transactions(id, payload)
            
            
        # Show Transactions
        @render.data_frame
        def show_transactions():
            
            data = fetch_data(month=currentMonth.get())

            data = data[['Date', "Item", "Amount", "Category"]]

            return render.DataTable(data, editable=True)
        


    
