import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import config
import ynab
from datetime import datetime

def get_ynab_transactions(api_key, budget_id):
    """Fetches transactions from the YNAB API."""
    configuration = ynab.Configuration(api_key={'bearer': api_key})
    api_client = ynab.ApiClient(configuration)
    transactions_api = ynab.TransactionsApi(api_client)

    try:
        transactions_response = transactions_api.get_transactions(budget_id)
        transactions = transactions_response['data']['transactions']

        # Convert to DataFrame
        df = pd.DataFrame(transactions)

        # Convert amount from milliunits to currency units
        df['amount'] = df['amount'] / 1000.0

        # Rename columns to match the old format
        df = df.rename(columns={'date': 'Date', 'payee_name': 'Payee', 'category_name': 'Category', 'amount': 'Outflow'})

        # Set 'Inflow' column
        df['Inflow'] = df.apply(lambda row: row['Outflow'] if row['Outflow'] > 0 else 0, axis=1)
        df['Outflow'] = df.apply(lambda row: -row['Outflow'] if row['Outflow'] < 0 else 0, axis=1)

        # Convert 'Date' column to datetime
        df['Date'] = pd.to_datetime(df['Date'])

        return df
    except ynab.ApiException as e:
        print(f"Error fetching transactions from YNAB API: {e}")
        return None

def get_ynab_budget_data(api_key, budget_id):
    """Fetches budget data from the YNAB API for the current month."""
    configuration = ynab.Configuration(api_key={'bearer': api_key})
    api_client = ynab.ApiClient(configuration)
    categories_api = ynab.CategoriesApi(api_client)

    try:
        # Get the current month in YYYY-MM-DD format
        current_month = datetime.now().strftime('%Y-%m-01')
        budget_month_response = categories_api.get_categories(budget_id, last_knowledge_of_server=None)

        categories = budget_month_response['data']['category_groups']

        budget_data = []
        for group in categories:
            for category in group['categories']:
                budget_data.append({
                    'Category': category['name'],
                    'Budgeted': category['budgeted'] / 1000.0,
                    'Activity': category['activity'] / 1000.0,
                    'Balance': category['balance'] / 1000.0
                })

        return pd.DataFrame(budget_data)
    except ynab.ApiException as e:
        print(f"Error fetching budget data from YNAB API: {e}")
        return None

def filter_data(df):
    """Filters the data based on the configuration."""
    start_date = config.start_date
    end_date = config.end_date
    excluded_payees = config.excluded_payees
    excluded_prefixes = config.excluded_prefixes
    excluded_categories = config.excluded_categories
    excluded_accounts = config.excluded_accounts

    df['Payee'] = df['Payee'].fillna('')

    filtered_df = (df[(df['Date'] >= start_date) &
                      (df['Date'] <= end_date) &
                      (~df['Payee'].isin(excluded_payees)) &
                      (~df['Payee'].str.startswith(config.excluded_prefixes, na=False)) &
                      (~df['Category'].isin(excluded_categories))])
                      # Account filtering will be added later
    return filtered_df

def plot_budget_analysis(df):
    """Plots the budget vs. actuals analysis."""
    df['Variance'] = df['Budgeted'] - df['Outflow']

    over_budget = df[df['Variance'] < 0].sort_values('Variance')
    under_budget = df[df['Variance'] > 0].sort_values('Variance', ascending=False)

    # Plot for over-budget categories
    if not over_budget.empty:
        plt.figure(figsize=(12, 8))
        bars = plt.bar(over_budget['Category'], over_budget['Variance'], color='r')
        plt.xlabel('Category')
        plt.ylabel('Amount Over Budget')
        plt.title('Categories Over Budget')
        plt.xticks(rotation=90)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height, f"${abs(height):.2f}", ha='center', va='bottom')
        plt.tight_layout()
        plt.show()

    # Plot for under-budget categories
    if not under_budget.empty:
        plt.figure(figsize=(12, 8))
        bars = plt.bar(under_budget['Category'], under_budget['Variance'], color='g')
        plt.xlabel('Category')
        plt.ylabel('Amount Under Budget')
        plt.title('Categories Under Budget')
        plt.xticks(rotation=90)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height, f"${height:.2f}", ha='center', va='bottom')
        plt.tight_layout()
        plt.show()

def main():
    """Main function to run the budget analysis."""
    transactions_df = get_ynab_transactions(config.ynab_api_key, config.budget_id)
    budget_df = get_ynab_budget_data(config.ynab_api_key, config.budget_id)

    if transactions_df is not None and budget_df is not None:
        # Filter transactions
        filtered_transactions_df = filter_data(transactions_df.copy())

        # Summarize transactions by category
        spending_by_category = filtered_transactions_df.groupby('Category')['Outflow'].sum().reset_index()

        # Merge budget data with spending data
        analysis_df = pd.merge(budget_df, spending_by_category, on='Category', how='left').fillna(0)

        # Remove categories with no budget and no spending
        analysis_df = analysis_df[(analysis_df['Budgeted'] != 0) | (analysis_df['Outflow'] != 0)]

        print("Budget Analysis Summary:")

        analysis_df['Variance'] = analysis_df['Budgeted'] - analysis_df['Outflow']
        over_budget = analysis_df[analysis_df['Variance'] < 0].sort_values('Variance')
        under_budget = analysis_df[analysis_df['Variance'] > 0].sort_values('Variance', ascending=False)

        print("\n--- Top 5 Over-Budget Categories ---")
        if not over_budget.empty:
            print(over_budget.head(5)[['Category', 'Budgeted', 'Outflow', 'Variance']])
        else:
            print("No categories are over budget. Great job!")

        print("\n--- Top 5 Under-Budget Categories ---")
        if not under_budget.empty:
            print(under_budget.head(5)[['Category', 'Budgeted', 'Outflow', 'Variance']])
        else:
            print("No categories are under budget.")

        print("\n")
        plot_budget_analysis(analysis_df)

if __name__ == '__main__':
    main()
