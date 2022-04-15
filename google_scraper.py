from nbformat import write
import requests
import json
import re
from datetime import datetime
import time
import urllib
import csv
import os


CITY = 'Raleigh, NC, USA'


def get_jobs(page):  # Returns a JSON listing of the jobs for CITY on the given page of Google's website
    return requests.get('https://careers.google.com/api/v3/search/?location={}&page={}&q='.format(urllib.parse.quote(CITY), page)).json()['jobs']


old_jobs = {}  # Load in old jobs from the spreadsheet if it exists
if os.path.exists(CITY + '.csv'):  # Only run if CITY's spreadsheet already exists
    f = open(CITY + '.csv', 'r', encoding='utf-8')
    csv_reader = csv.DictReader(f)
    for rows in csv_reader:  # Convert each row in the csv representing a job listing into a dictionary and add it to old_jobs
        key = rows['id']
        old_jobs[key] = rows
    f.close()

all_jobs = {}  # Store all job postings from Google's website in here
current_page = 1  # Start at page 1
jobs = get_jobs(1)  # Get jobs for page 1
while jobs:  # Run as long as there are still jobs to grab
    print('Running scraper on {} jobs page {}...'.format(CITY, current_page))
    for job in jobs:  # Loop through each job on the page
        if job['id'] in old_jobs.keys():  # Check if the job is already in the spreadsheet
            all_jobs[job['id']] = old_jobs[job['id']]  # If so, add it to the list of existing jobs and move on
            continue
        job['detail_url'] = 'https://careers.google.com/jobs/results/{}'.format(job['id'][5:])  # Store link to the job posting details
        r = re.findall(r'\$(\d?\d?\d,\d\d\d)', job['description'])  # Find the salary range for Colorado if it exists
        job['average_colorado_salary'] = int(sum([int(s.replace(',', '')) for s in r]) / len(r)) if r else None  # Store the average Colorado salary if it exists
        job['date_added'] = str(datetime.fromtimestamp(time.time()))[:10]  # Store the date the job was added to the spreadsheet
        job['date_removed'] = None  # Store the date the job was removed from Google's website (will always exist here)
        all_jobs[job['id']] = job  # Put the job into the collection of all job postings
    current_page += 1  # Continue onto the next page
    jobs = get_jobs(current_page)

for job_id in old_jobs.keys() - all_jobs.keys():  # Loop through each job that was found in the spreadsheet but not on Google's website
    all_jobs[job_id] = old_jobs[job_id]
    if not all_jobs[job_id]['date_removed']:
        all_jobs[job_id]['date_removed'] = str(datetime.fromtimestamp(time.time()))[:10]  # Store today's date, when the job was found to be removed from Google's website

csv_writer = csv.writer(open(CITY + '.csv', 'w'))

write_headers = True  # Prompt to write headers for the CSV file
for job in sorted(all_jobs.values(), key=lambda j: (j['date_added'], j['date_removed'] if j['date_removed'] else '2099-12-31', j['company_name'], j['title'])):  # Sort the job listings and loop through each one
    if write_headers:  # Write headers for the CSV file, only on the first loop
        header = job.keys()
        csv_writer.writerow(header)
        write_headers = False
    for key in job:  # Write each field for the job to the CSV file
        if isinstance(job[key], str):
            job[key] = job[key].replace('\n', '')
    csv_writer.writerow(job.values())  # Write the job posting to a row in the CSV file
