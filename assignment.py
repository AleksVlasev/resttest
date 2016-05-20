import requests
import collections
import argparse
from tabulate import tabulate

"Error definitions"
"--------------------------------------------------------------------------------"
class APIError(Exception):
	def __init__(self, status_code):
		self.status_code = status_code

	def __str__(self):
		return "APIError: status code = {}".format(self.status_code)


class NumberOfTransactionsError(Exception):
	def __init__(self, received_transactions, given_transactions):
		self.received_transactions = received_transactions
		self.given_transactions = given_transactions

	def __str__(self):
		return "NumberOfTransactionsError: The number of transactions given ({}) " \
			   "and the number of transactions received ({}) do not match. " \
			   "There may be some transactions missing".format(self.received_transactions, self.given_transactions)
"--------------------------------------------------------------------------------"


"Parameters and helper functions"
"--------------------------------------------------------------------------------"
indent = '    '
base_url = "http://resttest.bench.co/transactions/"


def page_url(num):
	return base_url + str(num) + ".json"


def print_dict(dictionary, indent_str='', inline=False):
	if inline:
		print indent_str,
		for item in dictionary:
			print item + ": " + str(dictionary[item]) + ',',
		print ''
	else:
		for item in dictionary:
			print indent_str + item + ": " + str(dictionary[item])


def print_headline(string):
	print "\n\n================================================================================"
	print string
	print "================================================================================\n"

def find_duplicates(lis):
	uniques = []
	duplicates = []
	for entry in lis:
		if entry in uniques:
			duplicates.append(entry)
		else:
			uniques.append(entry)
	return uniques, duplicates


def categorize_by_key(list_of_dicts, key):
	categories = {}
	for dictionary in list_of_dicts:
		cat = dictionary[key]
		try:
			categories[cat].append(dictionary)
		except KeyError:
			categories[cat] = [dictionary]
	return categories


def decategorize(categories):
	"If one wishes to undo the categorization."
	list_of_dicts = []
	for cat in categories:
		for dictionary in categories[cat]:
			list_of_dicts.append(dictionary)
	return list_of_dicts
"--------------------------------------------------------------------------------"


"Functions working with the API."
"--------------------------------------------------------------------------------"
def get_json_data(url):
	response = requests.get(url)
	if response.status_code != 200:
		raise APIError(response.status_code)
	return response.json()


def get_transactions():
	page_num = 0
	all_ok = True
	transactions = []
	given_transactions = 0
	while all_ok:
		page_num += 1
		try:
			page = get_json_data(page_url(page_num))
			given_transactions = page['totalCount']
			transactions.extend(page['transactions'])
		except APIError:
			all_ok = False
	received_transactions = len(transactions)
	if received_transactions != given_transactions:
		raise NumberOfTransactionsError(received_transactions, given_transactions)
	return transactions
"--------------------------------------------------------------------------------"


"Data manipulation functions."
"--------------------------------------------------------------------------------"
def clean_company_names(transactions):
	"TODO: Implement this function :)"
	return transactions


def balance(transactions, initial_balance=0.0):
	total = initial_balance
	for tr in transactions:
		total += float(tr['Amount'])
	return total


def daily_accumulated_balances(transactions):
	ordered_transactions = sorted(transactions, key=lambda t: t['Date'])
	balances = {}
	runnning_total = 0.
	for tran in ordered_transactions:
		runnning_total += float(tran['Amount'])
		date = tran['Date']
		balances[date] = runnning_total
	return to_list(balances)


def to_list(dictionary):
	lis = [[key, dictionary[key]] for key in dictionary]
	lis.sort(key=lambda x: x[0])
	return lis
"--------------------------------------------------------------------------------"

if __name__ == '__main__':
	"App argument parser construction"
	"--------------------------------------------------------------------------------"
	parser = argparse.ArgumentParser(description='Resttest assignment.')
	parser.add_argument('-c', '--clean',
						help='clean up the company names',
						action='store_true')
	parser.add_argument('-u', '--unique',
						help='keep only the unique transactions',
						action='store_true')
	parser.add_argument('-d', '--duplicates',
						help='print out the duplicated transactions',
						action='store_true')
	parser.add_argument('-a', '--accumulate',
						help='print out the daily accumulated balances',
						action='store_true')
	parser.add_argument('-ul', '--uncategorized',
						help='print out all transactions as received',
						action='store_true')
	parser.add_argument('-cl', '--categorized',
						help='print out all transactions by expense category',
						action='store_true')
	args = parser.parse_args()
	"--------------------------------------------------------------------------------"

	"App logic."
	"--------------------------------------------------------------------------------"
	args.duplicates = True
	args.accumulate = True
	args.categorized = True
	args.clean = True
	args.unique = True
	args.uncategorized = True

	trans = get_transactions()
	if args.clean:
		trans = clean_company_names(trans)

	if args.duplicates or args.unique:
		uniques, duplicates = find_duplicates(trans)
		if args.duplicates:
			print_headline("Duplicate transactions")
			print tabulate(duplicates, headers='keys')
		if args.unique:
			trans = uniques

	print "\nOverall Balance: {}".format(balance(trans))

	if args.accumulate:
		print_headline("Daily balances")
		balances = daily_accumulated_balances(trans)
		print tabulate(balances, headers=['Date', 'Amount'])

	if args.uncategorized:
		print_headline("List of transactions")
		print tabulate(trans, headers='keys')

	if args.categorized:
		print_headline("List of transactions by expense category")
		by_expense = categorize_by_key(trans, key='Ledger')
		for cat in by_expense:
			print "\nCategory: {}\nBalance: {}\n".format(cat, balance(by_expense[cat]))
			print tabulate(by_expense[cat], headers='keys')
			print ''
		summarized = [[cat, balance(by_expense[cat])] for cat in by_expense]
		print_headline("Summary of categorized expenses")
		print tabulate(summarized, headers=['Ledger', 'Balance'])
	"--------------------------------------------------------------------------------"

