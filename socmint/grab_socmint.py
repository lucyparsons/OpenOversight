import subprocess
from tqdm import tqdm

def main():
    list_of_monitored_accts = ['ChicagoCAPS02', 'ChicagoCAPS03',
                               'Chicago_Police', 'ChicagoCAPS01',
                               'ChicagoCAPS04', 'ChicagoCAPS05',
                               'ChicagoCAPS06', 'ChicagoCAPS07',
                               'ChicagoCAPS08', 'ChicagoCAPS09',
                               'ChicagoCAPS10', 'ChicagoCAPS11',
                               'ChicagoCAPS12', 'ChicagoCAPS14',
                               'ChicagoCAPS16', 'ChicagoCAPS17',
                               'ChicagoCAPS18', 'ChicagoCAPS19',
                               'ChicagoCAPS20', 'ChicagoCAPS22',
                               'ChicagoCAPS24', 'ChicagoCAPS25',
                               'ChicagoCAPSHQ', 'JoinCPD',
                               'ChicagoPDAirSea', 'cpdmemorial']

    for account in tqdm(list_of_monitored_accts):
        print('[*] Scraping {}'.format(account))
        subprocess.call(['python3', 'src/run.py', '--num', '1000000',
                      '--retweets', '--replies', account])

    return None

if __name__ == '__main__':
    main()
