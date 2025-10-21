import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import config
import ynab
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

def calculate_historical_averages(transactions_df, num_months=3):
    """
    Calculate historical spending averages by category.

    Args:
        transactions_df: DataFrame with transaction data
        num_months: Number of historical months to analyze (default: 3)

    Returns:
        DataFrame with historical averages by category
    """
    # Add month column
    df = transactions_df.copy()
    df['Month'] = df['Date'].dt.to_period('M')

    # Group by month and category, sum outflows
    monthly_spending = df.groupby(['Month', 'Category'])['Outflow'].sum().reset_index()

    # Calculate average spending per category across months
    avg_spending = monthly_spending.groupby('Category')['Outflow'].agg([
        ('Average', 'mean'),
        ('StdDev', 'std'),
        ('Min', 'min'),
        ('Max', 'max'),
        ('Count', 'count')
    ]).reset_index()

    # Fill NaN standard deviations (categories with only one month) with 0
    avg_spending['StdDev'] = avg_spending['StdDev'].fillna(0)

    return avg_spending, monthly_spending

def forecast_spending(transactions_df, num_months_history=3, forecast_months=1):
    """
    Forecast future spending based on historical data.

    Args:
        transactions_df: DataFrame with transaction data
        num_months_history: Number of historical months to use for forecast
        forecast_months: Number of months to forecast (default: 1)

    Returns:
        DataFrame with forecasted spending by category
    """
    avg_spending, monthly_spending = calculate_historical_averages(transactions_df, num_months_history)

    # Use average as the forecast (can be enhanced with trend analysis)
    forecast_df = avg_spending[['Category', 'Average', 'StdDev']].copy()
    forecast_df = forecast_df.rename(columns={'Average': 'Forecasted'})

    # Add confidence bounds (forecasted +/- std dev)
    forecast_df['Lower_Bound'] = (forecast_df['Forecasted'] - forecast_df['StdDev']).clip(lower=0)
    forecast_df['Upper_Bound'] = forecast_df['Forecasted'] + forecast_df['StdDev']

    return forecast_df

def calculate_percentage_based_budget(transactions_df, total_budget_amount=None):
    """
    Calculate recommended budget allocation based on historical spending percentages.

    Args:
        transactions_df: DataFrame with transaction data
        total_budget_amount: Target total budget amount (if None, uses total historical spending)

    Returns:
        DataFrame with percentage-based budget recommendations
    """
    # Calculate total spending by category
    category_spending = transactions_df.groupby('Category')['Outflow'].sum().reset_index()

    # Calculate total spending
    total_spending = category_spending['Outflow'].sum()

    # Calculate percentage of total for each category
    category_spending['Percentage'] = (category_spending['Outflow'] / total_spending * 100)

    # If no target budget provided, use total historical spending
    if total_budget_amount is None:
        total_budget_amount = total_spending

    # Calculate recommended budget based on percentages
    category_spending['Recommended_Budget'] = (category_spending['Percentage'] / 100 * total_budget_amount)

    return category_spending.sort_values('Percentage', ascending=False)

def plot_forecast_analysis(forecast_df, budget_df):
    """
    Plot forecasted spending vs current budget.

    Args:
        forecast_df: DataFrame with forecasted spending
        budget_df: DataFrame with current budget data
    """
    # Merge forecast with budget
    comparison_df = pd.merge(forecast_df, budget_df[['Category', 'Budgeted']], on='Category', how='left').fillna(0)
    comparison_df = comparison_df[comparison_df['Forecasted'] > 0]

    if comparison_df.empty:
        print("No forecast data to display")
        return

    # Sort by forecasted amount
    comparison_df = comparison_df.sort_values('Forecasted', ascending=False).head(15)

    # Create plot
    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(comparison_df))
    width = 0.35

    bars1 = ax.bar(x - width/2, comparison_df['Forecasted'], width, label='Forecasted Spend', color='steelblue')
    bars2 = ax.bar(x + width/2, comparison_df['Budgeted'], width, label='Current Budget', color='orange')

    ax.set_xlabel('Category')
    ax.set_ylabel('Amount ($)')
    ax.set_title('Forecasted Spending vs Current Budget (Top 15 Categories)')
    ax.set_xticks(x)
    ax.set_xticklabels(comparison_df['Category'], rotation=90)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, height, f'${height:.0f}',
                       ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.show()

def plot_percentage_budget_recommendations(percentage_df, budget_df):
    """
    Plot percentage-based budget recommendations.

    Args:
        percentage_df: DataFrame with percentage-based recommendations
        budget_df: DataFrame with current budget data
    """
    # Merge with current budget
    comparison_df = pd.merge(percentage_df, budget_df[['Category', 'Budgeted']], on='Category', how='left').fillna(0)

    # Top 15 categories by percentage
    top_categories = comparison_df.head(15)

    if top_categories.empty:
        print("No data to display")
        return

    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Plot 1: Percentage distribution
    colors = plt.cm.Set3(np.linspace(0, 1, len(top_categories)))
    wedges, texts, autotexts = ax1.pie(top_categories['Percentage'],
                                         labels=top_categories['Category'],
                                         autopct='%1.1f%%',
                                         colors=colors,
                                         startangle=90)
    ax1.set_title('Spending Distribution by Category (%)')

    # Make percentage text more readable
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontsize(8)
        autotext.set_weight('bold')

    # Plot 2: Recommended vs Current Budget
    x = np.arange(len(top_categories))
    width = 0.35

    bars1 = ax2.bar(x - width/2, top_categories['Recommended_Budget'], width,
                    label='Recommended Budget', color='green', alpha=0.7)
    bars2 = ax2.bar(x + width/2, top_categories['Budgeted'], width,
                    label='Current Budget', color='blue', alpha=0.7)

    ax2.set_xlabel('Category')
    ax2.set_ylabel('Amount ($)')
    ax2.set_title('Recommended vs Current Budget Allocation')
    ax2.set_xticks(x)
    ax2.set_xticklabels(top_categories['Category'], rotation=90)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.show()

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

def run_forecast_analysis(transactions_df, budget_df, num_months_history=3):
    """
    Run comprehensive forecast analysis including spending predictions and budget recommendations.

    Args:
        transactions_df: DataFrame with transaction data
        budget_df: DataFrame with current budget data
        num_months_history: Number of historical months to use for analysis

    Returns:
        Tuple of (forecast_df, percentage_df)
    """
    print("\n" + "="*80)
    print("FORECAST AND BUDGET RECOMMENDATION ANALYSIS")
    print("="*80)

    # Generate spending forecast
    print(f"\nAnalyzing {num_months_history} months of historical data...")
    forecast_df = forecast_spending(transactions_df, num_months_history=num_months_history)

    # Calculate percentage-based budget recommendations
    percentage_df = calculate_percentage_based_budget(transactions_df)

    # Get total budget and spending
    total_current_budget = budget_df['Budgeted'].sum()
    total_historical_spending = percentage_df['Outflow'].sum()

    print(f"Total Current Budget: ${total_current_budget:,.2f}")
    print(f"Total Historical Spending: ${total_historical_spending:,.2f}")

    # Display forecast summary
    print("\n--- SPENDING FORECAST (Top 10 Categories) ---")
    forecast_summary = pd.merge(
        forecast_df[['Category', 'Forecasted', 'Lower_Bound', 'Upper_Bound']],
        budget_df[['Category', 'Budgeted']],
        on='Category',
        how='left'
    ).fillna(0)
    forecast_summary['Budget_Gap'] = forecast_summary['Forecasted'] - forecast_summary['Budgeted']
    forecast_summary = forecast_summary.sort_values('Forecasted', ascending=False).head(10)

    print(forecast_summary[['Category', 'Forecasted', 'Budgeted', 'Budget_Gap']].to_string(index=False))

    # Display percentage-based recommendations
    print("\n--- PERCENTAGE-BASED BUDGET RECOMMENDATIONS (Top 10 Categories) ---")
    percentage_summary = pd.merge(
        percentage_df[['Category', 'Outflow', 'Percentage', 'Recommended_Budget']],
        budget_df[['Category', 'Budgeted']],
        on='Category',
        how='left'
    ).fillna(0)
    percentage_summary['Adjustment_Needed'] = percentage_summary['Recommended_Budget'] - percentage_summary['Budgeted']
    percentage_summary = percentage_summary.head(10)

    print(percentage_summary[['Category', 'Percentage', 'Recommended_Budget', 'Budgeted', 'Adjustment_Needed']].to_string(index=False))

    # Identify categories needing significant adjustments
    print("\n--- CATEGORIES NEEDING BUDGET ADJUSTMENT (>$50 difference) ---")
    significant_adjustments = forecast_summary[abs(forecast_summary['Budget_Gap']) > 50].sort_values('Budget_Gap')

    if not significant_adjustments.empty:
        print("\nBased on forecasted spending:")
        print(significant_adjustments[['Category', 'Forecasted', 'Budgeted', 'Budget_Gap']].to_string(index=False))
    else:
        print("All budgets are well-aligned with forecasted spending!")

    return forecast_df, percentage_df

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

        print("="*80)
        print("BUDGET ANALYSIS SUMMARY")
        print("="*80)

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

        # Run forecast analysis
        forecast_df, percentage_df = run_forecast_analysis(filtered_transactions_df, budget_df)

        # Generate visualizations
        print("\n" + "="*80)
        print("GENERATING VISUALIZATIONS...")
        print("="*80 + "\n")

        print("1. Budget vs Actuals Analysis")
        plot_budget_analysis(analysis_df)

        print("2. Spending Forecast vs Current Budget")
        plot_forecast_analysis(forecast_df, budget_df)

        print("3. Percentage-Based Budget Recommendations")
        plot_percentage_budget_recommendations(percentage_df, budget_df)

if __name__ == '__main__':
    main()
