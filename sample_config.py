# Sample config.
# To use, remove 'sample_' prefix and save as 'config.py'

from datetime import datetime, timedelta

start_date = datetime.today() - timedelta(days=14)
end_date = datetime.today()
excluded_payees = ['payee 1', 'payee 2', 'payee n']
excluded_prefixes = 'Transfer'
excluded_categories = 'Reimbursement Acct'
excluded_accounts = 'American Express - Business'