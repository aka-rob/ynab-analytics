# YNAB Budget Analyzer

This project provides a deeper analysis of your YNAB budget data. It connects to the YNAB API to fetch your latest budget and transaction data, and then generates a report that helps you understand your spending habits and identify areas where you are over or under budget.

## Features

- **YNAB API Integration:** Fetches your latest data directly from YNAB, so your analysis is always up-to-date.
- **Budget vs. Actuals Analysis:** Compares your budgeted amounts with your actual spending for each category.
- **Spending Forecast:** Uses historical transaction data to predict future spending by category, helping you plan ahead.
- **Percentage-Based Budget Recommendations:** Analyzes historical spending patterns and recommends budget allocations based on actual spending percentages.
- **Detailed Reporting:** Generates comprehensive summary reports and visualizations to help you quickly identify budget variances and opportunities for optimization.
- **Customizable Filtering:** Allows you to exclude certain payees, categories, and accounts from the analysis.

## Getting Started

### Prerequisites

- Python 3.8+
- A YNAB account and your [Personal Access Token](https://app.ynab.com/settings/developer).

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/ynab-analysis.git
   cd ynab-analysis
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application:**
   - Rename the `sample_config.py` file to `config.py`.
   - Open `config.py` and add your YNAB API key and budget ID.
     ```python
     ynab_api_key = 'YOUR_YNAB_API_KEY'
     budget_id = 'YOUR_BUDGET_ID'
     ```
   - You can find your `budget_id` by navigating to your budget in the YNAB web app. The URL will be in the format `https://app.ynab.com/BUDGET_ID/budget/`.
   - You can also customize the `excluded_payees`, `excluded_prefixes`, `excluded_categories`, and `excluded_accounts` lists in `config.py` to filter the analysis.

### Running the Analysis

To run the budget analysis, simply execute the `budget_analyzer.py` script:

```bash
python budget_analyzer.py
```

The script will:
1. Print a budget analysis summary showing over-budget and under-budget categories
2. Generate spending forecasts based on historical data (default: 3 months)
3. Provide percentage-based budget recommendations
4. Display three types of visualizations:
   - Budget vs. Actuals comparison (over/under budget categories)
   - Forecasted spending vs. current budget
   - Percentage-based budget recommendations with pie chart and comparison

## Understanding the Analysis

### Budget vs. Actuals
Compares your current month's budgeted amounts with actual spending, highlighting categories where you're over or under budget.

### Spending Forecast
Analyzes historical spending patterns to predict future spending:
- Calculates average spending per category over the past N months
- Provides confidence bounds (forecasted +/- standard deviation)
- Identifies budget gaps where forecasted spending exceeds current budget

### Percentage-Based Budget Recommendations
Recommends budget allocations based on historical spending patterns:
- Calculates each category's percentage of total historical spending
- Suggests budget amounts that reflect actual spending priorities
- Helps reallocate budget to align with real spending behavior
- Shows adjustment needed for each category

### Key Metrics Explained

- **Forecasted:** Predicted spending based on historical averages
- **Budget Gap:** Difference between forecasted spending and current budget (negative = need more budget)
- **Percentage:** Category's share of total spending
- **Recommended Budget:** Suggested budget allocation based on spending percentage
- **Adjustment Needed:** Difference between recommended and current budget

## Contributing

Contributions are welcome! If you have any ideas for new features or improvements, please open an issue or submit a pull request.
