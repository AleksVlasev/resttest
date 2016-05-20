This is my work on the restTest at Bench.co. I coded the assignment in Python, since I'm most comfortable with this
language. However, I'll quickly learn one of the other languages if given the opportunity. The basic functionality of
the app done by running

    python assignment.py

with optional arguments

    -h, --help            show this help message and exit
    -c, --clean           clean up the company names (not yet implemented)
    -u, --unique          keep only the unique transactions
    -d, --duplicates      print out the duplicated transactions
    -a, --accumulate      print out the daily accumulated balances
    -ul, --uncategorized  print out all transactions as received
    -cl, --categorized    print out all transactions by expense category

The basic execution is to download all the data from the available pages and calculate the balance. Optionally, after
the download, we can perform a clean up of the company names and then keep only the unique transactions. Afterwards,
we can optionally do a number of things like show duplicated transactions, show daily accumulated balances, and so on.

The assignment was fun, feedback is greatly appreciated and I would love to take the process further.