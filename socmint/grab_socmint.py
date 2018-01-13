import subprocess
from tqdm import tqdm
from sys import argv

def main():
    accounts_file_location = 'chicago.txt'
    if len(argv) == 2:
        accounts_file_location = argv[1]

    account_file = open(accounts_file_location, 'r')
    accounts = account_file.readlines()
    for account in tqdm(accounts):
        print('[*] Scraping {}'.format(account))
        subprocess.call(['python3', './src/run.py', '--num', '1000000', '--retweets', '--replies', account])

    return None


if __name__ == '__main__':
    main()
