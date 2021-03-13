#!/usr/bin/env python
# coding: utf-8

# In[1]:


############### import packages
import os, requests, sys, re, pandas as pd, time, urllib.request, csv, gc, psutil
from bs4 import BeautifulSoup
from tqdm import tqdm

##########################################################
##################### parameter ##########################
##########################################################
obj_type = '8-K'
period_start = 2014 # included
period_end = 2020 # included
raw_filing_dir = 'G:\\8-K\\' ########## directory where you want to save the downloaded EDGAR filings
master_index_dir = 'F:\\github\\python-edgar-master\\edgar-idx' ######### directory where the edgar master index are saved
output_csv_dir = r'..\filings\id_data_' + obj_type + '_' + str(period_start) + '-' + str(period_end) +'.csv' ######### directory of the output id_data.csv
time_waiting = 1/20 ########## sleeping time between the scraping of each filing in order to avoid being blocked by EDGAR
begin_from = 357203
memory_limit = 95

############### Set working directory to parent directory
if os.getcwd() != r'F:\github\narrative_conservatism\code':
    os.chdir(r'F:\github\narrative_conservatism\code')


# In[2]:


#################### Access all fillings through SEC master index #################################
####### indexes downloaded using python-edgar: https://github.com/edouardswiac/python-edgar #######
#### open terminal, and run the following lines:
#### cd F:\github\python-edgar-master (switch dir to where the run.py script is located)
#### python run.py -y 1993 -d edgar_idx (downloading all quarterly master index from 1993 into folder edgar_idx)

#### cd F:\github\python-edgar-master\edgar-idx (switch dir to where the downloaded indexes are located)
#### cat *.tsv > master.tsv (stitch all quarterly indexes into one master index)
#### du -h master.tsv (inspect how large the master index file is)

index_edgar = list()
doc_url = list()

# create an index of downloaded local quarterly master indexes
for subdir, dirs, files in os.walk(master_index_dir):
    for file in files:
        file_year = int(file.split('-')[0])
        if file_year >= period_start and file_year <= period_end:
            index_edgar.append(os.path.join(subdir, file))

# read each index file, select rows with matched file type, and store matched doc_links
for filenameTSV in index_edgar:
    tsv_read = pd.read_csv(filenameTSV, sep='|', header=None, encoding = "utf-8")
    tsv_read.columns = ['1', '2', '3', '4', '5', '6']
    
    # select the rows with filetype equal to predefined type
    tsv_type = tsv_read.loc[tsv_read['3'] == obj_type]
    doc_link = tsv_type['6'].values.tolist()
    doc_link = ['https://www.sec.gov/Archives/' + w for w in doc_link]
    for doc in doc_link:
        doc_url.append(doc)

del index_edgar
len(doc_url)


# In[3]:


############### Extract file identification info from doc_url
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'}

if os.path.exists(output_csv_dir) == False:
    with open(output_csv_dir, mode='w') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(['accnum','cik','name','fd', 'rp','item8k','sic','fye','state','bazip','irs','film','pdc','accepted','nexhibit','ngraph','web_url'])

## define lists
accnum = []
cik = []
name = []
fd = []
rp = []
item8k = []
sic = []
fye = []
state = []
bazip = []
irs = []
film = []
pdc = []
accepted = []
nexhibit = []
ngraph = []
web_url = []

for doc in tqdm(doc_url[begin_from:]):
    if psutil.virtual_memory().percent > memory_limit:
        break
        
    time.sleep(time_waiting) # SEC does not allow to exceed 10 requests/sec
    doc_resp = requests.get(doc, headers=headers)
    if doc_resp.status_code == 429:
        time.sleep(10*60+5) # if exceeds cool off for 10 mins
        doc_resp = requests.get(doc, headers=headers)
    else:
        pass

    soup = BeautifulSoup(doc_resp.text, 'html.parser')

    # Save the SEC accession number (accnum)
    try:
        accnum_i = soup.find('div', id='formHeader').find('div', id='secNum').get_text().split()[3]
        accnum.append(accnum_i)
    except:
        accnum.append(float('NaN'))
        pass

    # Save the Filing Date (0), Accepted Date (Date as of Change) (1), Public Document Count (2) and Reporting Period (3)
    try:
        dates = soup.find('div', class_='formContent').find_all('div', class_='info')
        # Filing Date
        fd.append(dates[0].get_text())
    except:
        fd.append(float('NaN'))
        pass

        # Accepted Date (Date as of Change)
    try:
        accepted.append(dates[1].get_text())
    except:
        accepted.append(float('NaN'))
        pass

        # Public Document Count
    try:
        pdc.append(dates[2].get_text())
    except:
        pdc.append(float('NaN'))
        pass

        # Reporting Period
    try:
        rp.append(dates[3].get_text())
    except:
        rp.append(float('NaN'))
        pass

    # For 8K files, Save item info
    try:
        if obj_type == '8-K':
            clist = re.findall(r'\d.\d\d', dates[4].get_text())
            if clist != []:
                item8k.append(', '.join(clist))
            else:
                clist = re.findall(r'\d+', c = dates[4].get_text())
                item8k.append(', '.join(clist))
        else :
            item8k.append(float('NaN'))
    except:
        item8k.append(float('NaN'))
        pass

    # Save the Company name and CIK
    try:
        comname = soup.find('div', class_='companyInfo').find('span', class_='companyName')
        # Company Name
        name.append(comname.get_text().split("\n")[0].replace(' (Filer)', ''))
    except:
        name.append(float('NaN'))
        pass

        # CIK
    try:
        cik.append(comname.get_text().split("\n")[1].replace('CIK: ', '').replace(' (see all company filings)', ''))
    except:
        cik.append(float('NaN'))
        pass

    # Save Business Address ZIP 
    try:
        div_tag = soup.find_all('div', class_='mailer')[1].find_all('span', class_='mailerAddress')[1]
        ba = div_tag.get_text()
        alist = re.findall(r'\d\d\d\d\d', ba)
        if alist == []:
            div_tag = soup.find_all('div', class_='mailer')[1].find_all('span', class_='mailerAddress')[2]
            ba = div_tag.get_text()
            alist = re.findall(r'\d\d\d\d\d', ba)
        bazip.append(', '.join(alist))
    except:
        bazip.append(float('NaN'))
        pass

        # Save SIC, Fiscal Year End, State of Incorporation, IRS number and film number
    try:
        filinginfo = soup.find('div', class_='companyInfo').find('p', class_='identInfo')
        # SIC
        sic.append(filinginfo.get_text().split("SIC:")[1].split()[0])
    except:
        sic.append(float('NaN'))
        pass

        # Save Fiscal Year End
    try:
        fye.append(filinginfo.get_text().split("Fiscal Year End:")[1].split()[0].replace('Type:', ''))
    except:
        fye.append(float('NaN'))
        pass

        # State
    try:
        state.append(filinginfo.get_text().split("State of Incorp.:")[1].split()[0].replace('Type:', ''))
    except:
        state.append(float('NaN'))
        pass

        # IRS number
    try:
        irs.append(filinginfo.get_text().split("IRS No.:")[1].split()[0].replace('Type:', ''))
    except:
        irs.append(float('NaN'))
        pass

        # film number
    try:
        film.append(filinginfo.get_text().split("Film No.: ")[1].split()[0].replace('SIC:', ''))
    except:
        film.append(float('NaN'))
        pass

    # Save the HTML/TXT website urls from doc_url to raw data folder
    try:
        rows = soup.find('table', class_='tableFile', summary='Document Format Files').find_all('tr')
        cell_html = rows[1].find_all('td')
        html = cell_html[2].a['href'].replace('ix?doc=/', '')
        cell_txt = rows[-1].find_all('td')
        txt = cell_txt[2].a['href']

        if html.endswith("htm") or html.endswith("txt"):
            url = 'https://www.sec.gov' + html
        else:
            url = 'https://www.sec.gov' + txt
        web_url.append(url)

    except:
        web_url.append(float('NaN'))
        pass

    # Count number of exhibits and graphics in this filing
    try:
        ex = 0
        graph = 0
        for row in rows[2:-1]:
            if row.find_all('td')[3].get_text().startswith('EX'):
                ex = ex + 1
            elif row.find_all('td')[3].get_text().startswith('GRAPHIC'):
                graph = graph + 1
            else:
                pass
        ngraph.append(graph)
        nexhibit.append(ex)

    except:
        ngraph.append(float('NaN'))
        nexhibit.append(float('NaN'))
        pass


# In[4]:


#### save scraped data locally 
id_data = pd.DataFrame(data={'accnum': accnum, 'cik': cik, 'name': name, 'fd': fd, 'rp': rp, 'item8k': item8k, 'sic': sic,'fye': fye, 'state': state, 'bazip': bazip,  'irs': irs, 'film': film, 'pdc': pdc, 'accepted': accepted, 'nexhibit': nexhibit, 'ngraph': ngraph, 'web_url': web_url})
id_data_saved = pd.read_csv(output_csv_dir,  dtype = {'cik':str, 'bazip':str, 'sic':str, 'fye':str, 'film':str, 'irs':str, 'web_url':str})
id_data = pd.concat([id_data_saved, id_data])
id_data.to_csv(output_csv_dir, index=False)


# In[ ]:


# downloading the report if necessary (report can be accessed online so actually no need to download)
id_data = pd.read_csv(output_csv_dir, dtype = {'cik':str, 'bazip':str, 'sic':str, 'fye':str, 'film':str, 'irs':str, 'web_url':str})
try:
    if os.path.exists(raw_filing_dir + accnum_i + '.txt') == False:
        urllib.request.urlretrieve(url, raw_filing_dir + accnum_i + '.txt')
except:
    pass


# In[ ]:


id_data = pd.read_csv(output_csv_dir,  dtype = {'cik':str, 'bazip':str, 'sic':str, 'fye':str, 'film':str, 'irs':str, 'web_url':str})
id_data.isnull().sum()

