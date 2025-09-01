# YNAB Budget Analyzer

This project provides a deeper analysis of your YNAB budget data. It connects to the YNAB API to fetch your latest budget and transaction data, and then generates a report that helps you understand your spending habits and identify areas where you are over or under budget.

## Features

- **YNAB API Integration:** Fetches your latest data directly from YNAB, so your analysis is always up-to-date.
- **Budget vs. Actuals Analysis:** Compares your budgeted amounts with your actual spending for each category.
- **Detailed Reporting:** Generates a summary report and visualizations to help you quickly identify the categories with the largest budget variances.
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

The script will print a summary report to the console and display plots showing the budget vs. actuals analysis.

## Contributing

Contributions are welcome! If you have any ideas for new features or improvements, please open an issue or submit a pull request.
