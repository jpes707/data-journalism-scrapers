import requests
import json
import re
from datetime import datetime
import time
import urllib


CITY = 'Durham, NC, USA'


def get_jobs(page):
    return requests.get('https://careers.google.com/api/v3/search/?location={}&page={}&q='.format(urllib.parse.quote(CITY), page)).json()['jobs']


all_jobs = []
current_page = 1
jobs = get_jobs(1)
while jobs:
    print('Running scraper on {} jobs page {}...'.format(CITY, current_page))
    for job in jobs:
        job['detail_url'] = 'https://careers.google.com/jobs/results/{}'.format(job['id'][5:])
        r = re.findall(r'\$(\d?\d?\d,\d\d\d)', job['description'])
        job['average_colorado_salary'] = int(sum([int(s.replace(',', '')) for s in r]) / len(r)) if r else None
        all_jobs.append(job)
    current_page += 1
    jobs = get_jobs(current_page)

file = open('google_results.json', 'r')
previous_results = json.load(file)
file.close()

file = open('google_results.json', 'w')
if not CITY in previous_results:
    previous_results[CITY] = {}
previous_results[CITY][str(datetime.fromtimestamp(time.time()))[:10]] = all_jobs
json.dump(previous_results, file, indent=4)
print('Done! Added {} jobs.'.format(len(all_jobs)))
