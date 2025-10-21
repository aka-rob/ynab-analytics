# YNAB Budget Analyzer Configuration
# Copy this file to config.py and fill in your details

from datetime import datetime, timedelta

# YNAB API Configuration
# Get your API key from: https://app.ynab.com/settings/developer
ynab_api_key = 'YOUR_YNAB_API_KEY_HERE'

# Budget ID - found in the URL when viewing your budget
# Example: https://app.ynab.com/BUDGET_ID_HERE/budget/
budget_id = 'YOUR_BUDGET_ID_HERE'

# Analysis Date Range
# Adjust these to analyze a specific time period
# For forecasting, it's recommended to use at least 3 months of data
end_date = datetime.now()
start_date = end_date - timedelta(days=90)  # Last 3 months

# Filtering Configuration
# Customize these lists to exclude specific items from your analysis

# Exclude specific payees (exact match)
excluded_payees = [
    'Transfer : Savings',
    'Transfer : Checking',
    # Add payees you want to exclude
]

# Exclude payees starting with these prefixes
excluded_prefixes = (
    'Starting Balance',
    'Reconciliation Balance',
    # Add prefixes to exclude
)

# Exclude specific budget categories
excluded_categories = [
    'Inflow: Ready to Assign',
    'Split (Multiple Categories)...',
    # Add categories you want to exclude
]

# Exclude specific accounts
excluded_accounts = [
    # Add account names to exclude
]

# Forecasting Configuration
# Number of historical months to use for forecasting (default: 3)
forecast_months_history = 3

# Budget adjustment threshold (in dollars)
# Categories with forecast gaps larger than this will be highlighted
significant_adjustment_threshold = 50
