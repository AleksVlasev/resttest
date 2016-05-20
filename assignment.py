import requests
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
	"Error message that comes up if the number of transactions downloaded is different from the stated number."
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


def page_url(number):
	return base_url + str(number) + ".json"


def print_headline(string):
	print "\n\n================================================================================"
	print string
	print "================================================================================\n"


def find_duplicates(lis):
	"""
	For each item, if we've already seen it, we add it to a list of duplicates. We keep the unique ones in a list too.
	The complexity of this is O(n^2), where n is the number of entries. For hashable elements, we could have used
	a dictionary for a large speed up. Given the small number of transactions, I went with a simple solution for now.
	"""
	uniques = []
	duplicates = []
	for entry in lis:
		if entry in uniques:
			duplicates.append(entry)
		else:
			uniques.append(entry)
	return uniques, duplicates


def categorize_by_key(list_of_dicts, key):
	"""
	The list of dictionaries need to consist of dictionaries that have the same sets of keys. The function groups
	together dictionaries that have the same value for the chosen key. The result is a dictionary, where the keys are
	the different groups and the values are all the dictionaries that are in the same group.
	"""
	categories = {}
	for dictionary in list_of_dicts:
		cat = dictionary[key]
		try:
			categories[cat].append(dictionary)
		except KeyError:
			categories[cat] = [dictionary]
	return categories


def decategorize(categories):
	list_of_dicts = []
	for cat in categories:
		for dictionary in categories[cat]:
			list_of_dicts.append(dictionary)
	return list_of_dicts


def to_list(dictionary, sort=False):
	lis = [[key, dictionary[key]] for key in dictionary]
	if sort:
		lis.sort(key=lambda x: x[0])
	return lis
"--------------------------------------------------------------------------------"


"Functions working with the API."
"--------------------------------------------------------------------------------"
def get_json_data(url):
	response = requests.get(url)
	if response.status_code != 200:
		raise APIError(response.status_code)
	return response.json()


def get_transactions():
	"""
	I thought a lot about how to do this and settled on the following. While there are no errors,
	we keep downloading the data and moving onto a new page. Once we run out of pages or if there
	are any other errors, the process stops. Finally, the function checks that we have the same number of
	transactions as stated in the received data and raises an exception otherwise.

	Possible issue:
		- What if there are a million pages or more and we start running out of resources?
		- What if the pages are there, but we get other errors?
	"""
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
	"""
	I realized this function would require some regex most likely and since my experience with this
	is very limited, I chose to keep it simple for now, and learn how to do it later.

	Another issue here is that I don't know the user. For me, what is garbage may not be what is garbage for the
	customer. And vice versa. Possible things to remove from the name are: city and province, store numbers,
	account numbers, usd conversions, company website. It depends on what the customer desires.
	"""
	return transactions


def balance(transactions, initial_balance=0.0):
	"""
	Given a list of transactions, the function tallies up their amounts, with the option for starting with an
	initial balance. I have assumed it would be enough to work with floats for now. A more robust solution would be
	to use a class of 'real money' and integer arithmetic to avoid round-off errors. Unless there is interest calculated.
	"""
	total = initial_balance
	for tr in transactions:
		total += float(tr['Amount'])
	return total


def daily_accumulated_balances(transactions):
	"""
	Given a list of transactions, the function sorts them by date, and then computes a running total of the balance,
	tallying up the balance after each day in a dictionary. It outputs a list of pairs (also list) of dates and
	daily accumulated balances.
	"""
	ordered_transactions = sorted(transactions, key=lambda t: t['Date'])
	balances = {}
	runnning_total = 0.
	for tran in ordered_transactions:
		runnning_total += float(tran['Amount'])
		date = tran['Date']
		balances[date] = runnning_total
	print balances
	return to_list(balances, sort=True)
"--------------------------------------------------------------------------------"

if __name__ == '__main__':
	"App argument parser construction"
	"--------------------------------------------------------------------------------"
	"""
	I decided to run with a command-line approach using flags, where all the arguments can be used in parallel.
	If we had a proper function to clean up the company names, it is performed first. If the user chooses to
	only keep unique items, this is done second. Then the rest of the tasks are performed on that cleaned up and
	possibly-unique data.
	"""
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

	trans = get_transactions()
	if args.clean:
		trans = clean_company_names(trans)

	if args.duplicates or args.unique:
		uniques, duplicates = find_duplicates(trans)
		if args.duplicates:
			print_headline("Duplicate transactions")
			print tabulate(duplicates, headers='keys', floatfmt=".2f")
		if args.unique:
			trans = uniques

	print "\nOverall Balance: {}".format(balance(trans))

	if args.accumulate:
		print_headline("Daily balances")
		balances = daily_accumulated_balances(trans)
		print tabulate(balances, headers=['Date', 'Amount'], floatfmt=".2f")

	if args.uncategorized:
		print_headline("List of transactions")
		print tabulate(trans, headers='keys', floatfmt=".2f")

	if args.categorized:
		print_headline("List of transactions by expense category")
		by_expense = categorize_by_key(trans, key='Ledger')
		for cat in by_expense:
			print "\nCategory: {}\nBalance: {}\n".format(cat, balance(by_expense[cat]))
			print tabulate(by_expense[cat], headers='keys', floatfmt=".2f")
			print ''
		summarized = [[cat, balance(by_expense[cat])] for cat in by_expense]
		print_headline("Summary of categorized expenses")
		print tabulate(summarized, headers=['Ledger', 'Balance'], floatfmt=".2f")
	"--------------------------------------------------------------------------------"

