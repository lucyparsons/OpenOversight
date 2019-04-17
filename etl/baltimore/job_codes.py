import requests
from bs4 import BeautifulSoup
import csv

url = 'https://www.governmentjobs.com/careers/classspecifications/index'

if __name__ == '__main__':
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    page = 1
    jobs = {}
    while True:
        params = {'agency': 'baltimorecity', 'sort': 'ClassTitle', 'isDescendingSort': 'false', 'page': page}
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            raise Exception('Error {}: {}'.format(resp.status_code, resp.text))
        soup = BeautifulSoup(resp.text, 'html.parser')
        if 'No class specifications at this time.' in soup.stripped_strings:
            break
        tbody = soup.find('tbody')
        for row in tbody.find_all('tr'):
            title = row.find('a',class_='item-details-link').string
            code = int(row.find('td',class_='class-spec-table-code').string)
            jobs[code] = title
            print('{}: {}'.format(code, title))
        page += 1
    with open('job_codes.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Job Code', 'Job Title'])
        for code, title in jobs.items():
            writer.writerow([code, title])
    print('Done.')
