#!/usr/bin/env python
# coding: utf-8
from numba import jit
import time
import csv
import gc
import logging
import os
import re
import timeit
from time import sleep, perf_counter
from tqdm import tqdm
import pandas as pd
import requests
import textstat
from bs4 import BeautifulSoup
from nltk import word_tokenize

##########################################################
##################### parameter ##########################
##########################################################
obj_type = '8-K'
item_type = ''  # to analyze who document, set item_type to 'full'
period_start = 2014  # included
period_end = 2020  # included

# raw_filing_dir = 'H:\\data\\edgar\\processed\\' + obj_type + '\\' + item_type
if (obj_type == '10-K') | (obj_type == '10-Q'):
    output_csv_dir = '..\\filings\\text_data_' + obj_type + '_' + item_type + '_' + str(period_start) + '-' + str(
        period_end) + '.csv'
else:
    output_csv_dir = '..\\filings\\text_data_' + obj_type + '_' + str(period_start) + '-' + str(period_end) + '.csv'

input_csv_dir = '..\\filings\\id_data_' + obj_type + '_' + str(period_start) + '-' + str(period_end) + '.csv'
dictionary_dir = '..\\..\\dictionary\\'
time_waiting = 0

url_list = []
nw = [0]
nvocab = [0]
nsyllable = [0]
nsentence = [0]
n_neg_lm = [0]
n_pos_lm = [0]
n_neg_gi = [0]
n_pos_gi = [0]
n_neg_hr = [0]
n_pos_hr = [0]
n_uctt_lm = [0]
n_lit_lm = [0]
n_cstr_lm = [0]
n_modal1_lm = [0]
n_modal2_lm = [0]
n_modal3_lm = [0]
n_negation_lm = [0]
n_negation_gi = [0]
n_negation_hr = [0]
fre = ['']
fkg = ['']
cl = ['']
fog = ['']
ari = ['']
smog = ['']
id_data = ['']
web_url = ['']

############# Create a negation word list
gt_negation = ['no', 'not', 'none', 'neither', 'never', 'nobody']  ## Gunnel Totie, 1991, Negation in Speech and Writing

############### Create Henry disctionary (HENRY 2008)
hr_neg = ['negative', 'negatives', 'fail', 'fails', 'failing', 'failure', 'weak', 'weakness', 'weaknesses', 'difficult',
          'difficulty', 'hurdle', 'hurdles', 'obstacle', 'obstacles', 'slump', 'slumps', 'slumping', 'slumped',
          'uncertain', 'uncertainty', 'unsettled', 'unfavorable', 'downturn', 'depressed', 'disappoint', 'disappoints',
          'disappointing', 'disappointed', 'disappointment', 'risk', 'risks', 'risky', 'threat', 'threats', 'penalty',
          'penalties', 'down', 'decrease', 'decreases', 'decreasing', 'decreased', 'decline', 'declines', 'declining',
          'declined', 'fall', 'falls', 'falling', 'fell', 'fallen', 'drop', 'drops', 'dropping', 'dropped',
          'deteriorate', 'deteriorates', 'deteriorating', 'deteriorated', 'worsen', 'worsens', 'worsening', 'weaken',
          'weakens', 'weakening', 'weakened', 'worse', 'worst', 'low', 'lower', 'lowest', 'less', 'least', 'smaller',
          'smallest', 'shrink']
hr_pos = ['positive', 'positives', 'success', 'successes', 'successful', 'succeed', 'succeeds', 'succeeding',
          'succeeded', 'accomplish', 'accomplishes', 'accomplishing', 'accomplished', 'accomplishment',
          'accomplishments', 'strong', 'strength', 'strengths', 'certain', 'certainty', 'definite', 'solid',
          'excellent', 'good', 'leading', 'achieve', 'achieves', 'achieved', 'achieving', 'achievement', 'achievements',
          'progress', 'progressing', 'deliver', 'delivers', 'delivered', 'delivering', 'leader', 'leading', 'pleased',
          'reward', 'rewards', 'rewarding', 'rewarded', 'opportunity', 'opportunities', 'enjoy', 'enjoys', 'enjoying',
          'enjoyed', 'encouraged', 'encouraging', 'up', 'increase', 'increases', 'increasing', 'increased', 'rise',
          'rises', 'rising', 'rose', 'risen', 'improve', 'improves', 'improving', 'improved', 'improvement',
          'improvements', 'strengthen', 'strengthens', 'strengthening', 'strengthened', 'stronger', 'strongest',
          'better', 'best', 'more', 'most', 'above', 'record', 'high', 'higher', 'highest', 'greater', 'greatest',
          'larger', 'largest', 'grow', 'grows', 'growing', 'grew', 'grown', 'growth', 'expand', 'expands', 'expanding',
          'expanded', 'expansion', 'exceed', 'exceeds', 'exceeded', 'exceeding', 'beat', 'beats', 'beating']


def coast_time(func):
    '''https://blog.csdn.net/weixin_38924500/article/details/111679503?utm_medium=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.control&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.control'''

    def fun(*args, **kwargs):
        t = perf_counter()
        result = func(*args, **kwargs)
        print(f'func {func.__name__} coast time:{perf_counter() - t:.8f} s')
        return result

    return fun


@coast_time
def read_lm():
    # LM = pd.read_excel(dictionary_dir + 'LM\\LoughranMcDonald_MasterDictionary_2018.xlsx', encoding = "utf-8")
    # LM = pd.read_excel(dictionary_dir + 'LM\\LoughranMcDonald_MasterDictionary_2018.xlsx')
    LM = pd.read_csv(dictionary_dir + 'LM\\LoughranMcDonald_MasterDictionary_2018.csv', sep=',', encoding="utf-8")

    global lm_neg, lm_pos, lm_uctt, lm_lit, lm_cstr, lm_modal1, lm_modal2, lm_modal3
    ############### Create negative, positive, uncertainty, litigious, constraining and modal word lists
    lm_neg = LM.loc[LM['Negative'] != 0]['Word'].values.tolist()
    lm_pos = LM.loc[LM['Positive'] != 0]['Word'].values.tolist()
    lm_uctt = LM.loc[LM['Uncertainty'] != 0]['Word'].values.tolist()
    lm_lit = LM.loc[LM['Litigious'] != 0]['Word'].values.tolist()
    lm_cstr = LM.loc[LM['Constraining'] != 0]['Word'].values.tolist()
    lm_modal1 = LM.loc[LM['Modal'] == 1]['Word'].values.tolist()
    lm_modal2 = LM.loc[LM['Modal'] == 2]['Word'].values.tolist()
    lm_modal3 = LM.loc[LM['Modal'] == 3]['Word'].values.tolist()
    lm_neg = [w.lower() for w in lm_neg]
    lm_pos = [w.lower() for w in lm_pos]
    lm_uctt = [w.lower() for w in lm_uctt]
    lm_lit = [w.lower() for w in lm_lit]
    lm_cstr = [w.lower() for w in lm_cstr]
    lm_modal1 = [w.lower() for w in lm_modal1]
    lm_modal2 = [w.lower() for w in lm_modal2]
    lm_modal3 = [w.lower() for w in lm_modal3]
    ############## Read and create stop words list
    lm_stop = []
    with open(dictionary_dir + 'LM\\StopWords_Generic.txt', "r") as f:
        for line in f:
            line = line.replace('\n', '')
            lm_stop.append(line)
    lm_stop = [w.lower() for w in lm_stop]


@coast_time
def read_gi():
    global GI
    # GI_cols = ['Entry', 'Source', 'Positiv', 'Negativ']
    # GI = pd.read_excel(dictionary_dir + 'GI\\inquirerbasic.xls', usecols=GI_cols)
    GI = pd.read_csv(dictionary_dir + 'GI\\inquirerbasic.csv', sep=',', encoding="utf-8")
    global GI, gi_neg, gi_pos
    GI = GI[(GI['Entry'].str.endswith('#1') == True) | (GI['Entry'].str.contains('#') == False)]
    GI['Entry'] = GI['Entry'].str.replace('#1', '')
    ############### Create negative, positive, uncertainty, litigious, constraining and modal word lists
    gi_neg = GI.loc[GI['Negativ'].notnull()]['Entry'].values.tolist()
    gi_pos = GI.loc[GI['Positiv'].notnull()]['Entry'].values.tolist()
    gi_neg = [w.lower() for w in gi_neg]
    gi_pos = [w.lower() for w in gi_pos]


@coast_time
def read_csv():
    global id_data
    id_data = pd.read_csv(input_csv_dir,
                          dtype={'cik': str, 'bazip': str, 'sic': str, 'fye': str, 'film': str, 'irs': str,
                                 'web_url': str})
    global id_data, web_url
    id_data = id_data[(id_data.duplicated('accnum') == False) & (id_data['accnum'].notnull())]
    web_url = id_data['web_url'].values.tolist()
    # web_url = random.sample(processed, 10086)
    print(len(web_url))


#### Define the function sublist_per to make sublists inside a list for every "step" (=5000) elements
#### so that once after every 5000 filing information have been extracted, they are saved to disk, and scraping can resume from where it was interrupted last time
#### to avoid time loss due to system crash
@coast_time
def sublist_per(source, step):
    return [source[i - step:i] for i in list(range(len(source)))[::step][1:]] + [
        source[list(range(len(source)))[::step][-1]:]]


#### Define a function count_occurrence to count the number of words in tup that pertaining to a list

@jit(nopython=True)
def count_occurrence(tup, lst):
    count = 0
    for item in tup:
        if item in lst:
            count += 1

    return count


### Define a function count_negation to count cases where negation occurs within four or fewer words from a word identified in list.
@jit(nopython=True)
def count_negation(tup, lst, negation):
    count = 0
    for item in tup:
        if item in lst:
            if tup.index(item) - 4 > 0 and tup.index(item) + 4 < len(tup):
                neighbor = tup[tup.index(item) - 4:tup.index(item) + 4]
                for neighborw in neighbor:
                    if neighborw in negation:
                        count += 1

            if tup.index(item) - 4 < 0:
                pre = tup[0:tup.index(item) + 4]
                for prew in pre:
                    if prew in negation:
                        count += 1

            if tup.index(item) + 4 > len(tup):
                post = tup[tup.index(item) - 4:len(tup)]
                for postw in post:
                    if postw in negation:
                        count += 1
    return count


############# Define a function to count the number of numerical occurrence in a string
def number_digits(inputString):
    return len(re.findall(r'\s?\d+\W?\d+\s?', inputString))


if os.path.exists(output_csv_dir) == False:
    with open(output_csv_dir, mode='w') as file:
        writer = csv.writer(file, delimiter=',')
        if (obj_type == '10-K') | (obj_type == '10-Q'):
            writer.writerow(['web_url', 'nw_' + item_type, 'nvocab_' + item_type, 'nsyllable_' + item_type,
                             'nsentence_' + item_type, 'n_neg_lm_' + item_type, 'n_pos_lm_' + item_type,
                             'n_neg_gi_' + item_type, 'n_pos_gi_' + item_type, 'n_neg_hr_' + item_type,
                             'n_pos_hr_' + item_type, 'n_uctt_lm_' + item_type, 'n_lit_lm_' + item_type,
                             'n_cstr_lm_' + item_type, 'n_modal_strong_lm_' + item_type,
                             'n_modal_moderate_lm_' + item_type, 'n_modal_weak_lm_' + item_type,
                             'n_negation_lm_' + item_type, 'n_negation_gi_' + item_type, 'n_negation_hr_' + item_type,
                             'fre_' + item_type, 'fkg_' + item_type, 'cl_' + item_type, 'fog_' + item_type,
                             'ari_' + item_type, 'smog_' + item_type])
        else:
            writer.writerow(
                ['web_url', 'nw', 'nvocab', 'nsyllable', 'nsentence', 'n_neg_lm', 'n_pos_lm', 'n_neg_gi', 'n_pos_gi',
                 'n_neg_hr', 'n_pos_hr', 'n_uctt_lm', 'n_lit_lm', 'n_cstr_lm', 'n_modal_strong_lm',
                 'n_modal_moderate_lm', 'n_modal_weak_lm', 'n_negation_lm', 'n_negation_gi', 'n_negation_hr', 'fre',
                 'fkg', 'cl', 'fog', 'ari', 'smog'])


@coast_time
def do_html():
    global contents
    ############# Clean HTML tags and nondisplay section #####################
    # 2.1).i): delete nondisplay section
    nondisplay = soup.find('div', style="display:none;") or soup.find('div', style="display:none")
    if nondisplay is not None:
        _ = nondisplay.extract()
    # 2.1).ii): delete tables that contains more than 4 numbers
    table_tag = soup.find_all('table')
    for tab in table_tag:
        if number_digits(tab.get_text()) > 4:
            _ = tab.extract()
    # 2.3): delete html tags
    contents = soup.get_text().replace('\n', ' ').replace(u'\xa0', u' ')
    ############# Clean HTML tags and nondisplay section #####################


@coast_time
def do_tokenize():
    global tokens
    tokens = word_tokenize(contents)


@coast_time
def do_words():
    global words, vocab
    ## Convert all words into small cases
    ## Keep tokens that purely consist of alphabetic characters only
    ## Delete single-character words except for 'I'
    words = [w.lower() for w in tokens if w.isalpha() and len(w) > 1 or w == 'i']
    ########### Delete words with lenth smaller than 1% and largr than 99% of the document
    # wordlen99 = np.quantile([len(w) for w in words], 0.99)
    # wordlen1 = np.quantile([len(w) for w in words], 0.01)
    # words = [w for w in words if len(w)<wordlen99 and len(w)>wordlen1]
    vocab = sorted(set(words))


@coast_time
def get_doc(url):
    global doc_resp
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'}
    ### use url, instead of accnum, as key to link to id_data
    url_list.append(url)
    ############# Read txt file from EDGAR
    sleep(time_waiting)  # SEC does not allow to exceed 10 requests/sec
    doc_resp = requests.get(url, headers=headers)
    if doc_resp.status_code == 429:
        print('---------429-----------')
        sleep(10 * 60 + 5)  # if exceeds cool off for 10 mins
        doc_resp = requests.get(url, headers=headers)
    else:
        pass


# @coast_time
@jit(nopython=True)
def do_datas():
    # logging.info('do_datas')

    ########### Save text statistics
    ##### 1. nw 2. nvocab 3. nsyllable 4.nsentence 5. tone 6. readability
    ## 1. nw
    nw.append(len(words))
    ## 2. nvocab
    nvocab.append(len(vocab))
    ## 3. syllable
    n = textstat.syllable_count(contents)
    nsyllable.append(n)
    ## 4. sentence
    n = textstat.sentence_count(contents)
    nsentence.append(n)
    ## 5. tone
    ### LM dictionary
    n_neg_lm.append(count_occurrence(words, lm_neg))
    n_pos_lm.append(count_occurrence(words, lm_pos))
    n_uctt_lm.append(count_occurrence(words, lm_uctt))
    n_lit_lm.append(count_occurrence(words, lm_lit))
    n_cstr_lm.append(count_occurrence(words, lm_cstr))
    n_modal1_lm.append(count_occurrence(words, lm_modal1))
    n_modal2_lm.append(count_occurrence(words, lm_modal2))
    n_modal3_lm.append(count_occurrence(words, lm_modal3))
    n_negation_lm.append(count_negation(words, lm_pos, gt_negation))
    ### General Inquirer dictionary
    n_neg_gi.append(count_occurrence(words, gi_neg))
    n_pos_gi.append(count_occurrence(words, gi_pos))
    n_negation_gi.append(count_negation(words, gi_pos, gt_negation))
    ### Henry dictionary
    n_neg_hr.append(count_occurrence(words, hr_neg))
    n_pos_hr.append(count_occurrence(words, hr_pos))
    n_negation_hr.append(count_negation(words, gi_pos, gt_negation))
    ## 4. readability
    fre_i = textstat.flesch_reading_ease(contents)
    if fre_i > 100:
        fre_i = 100
    if fre_i < 0:
        fre_i = float('NaN')
    fre.append(fre_i)
    fkg_i = textstat.flesch_kincaid_grade(contents)
    if fkg_i < 0:
        fkg_i = float('NaN')
    fkg.append(fkg_i)
    # RIX
    cl_i = textstat.coleman_liau_index(contents)
    if cl_i < 0:
        cl_i = float('NaN')
    cl.append(cl_i)
    f = textstat.gunning_fog(contents)
    fog.append(f)
    f = textstat.automated_readability_index(contents)
    ari.append(f)
    f = textstat.smog_index(contents)
    smog.append(f)
    # logging.info('end do_datas')
    # LIX


@coast_time
def save_data():
    global text_data, text_data_saved
    if (obj_type == '10-K') | (obj_type == '10-Q'):
        d = {'web_url': url_list, 'nw_' + item_type: nw, 'nvocab_' + item_type: nvocab,
             'nsyllable_' + item_type: nsyllable, 'nsentence_' + item_type: nsentence,
             'n_neg_lm_' + item_type: n_neg_lm, 'n_pos_lm_' + item_type: n_pos_lm, 'n_neg_gi_' + item_type: n_neg_gi,
             'n_pos_gi_' + item_type: n_pos_gi, 'n_neg_hr_' + item_type: n_neg_hr, 'n_pos_hr_' + item_type: n_pos_hr,
             'n_uctt_lm_' + item_type: n_uctt_lm, 'n_lit_lm_' + item_type: n_lit_lm,
             'n_cstr_lm_' + item_type: n_cstr_lm, 'n_modal_strong_lm_' + item_type: n_modal1_lm,
             'n_modal_moderate_lm_' + item_type: n_modal2_lm, 'n_modal_weak_lm_' + item_type: n_modal3_lm,
             'n_negation_lm_' + item_type: n_negation_lm, 'n_negation_gi_' + item_type: n_negation_gi,
             'n_negation_hr_' + item_type: n_negation_hr, 'fre_' + item_type: fre, 'fkg_' + item_type: fkg,
             'cl_' + item_type: cl, 'fog_' + item_type: fog, 'ari_' + item_type: ari, 'smog_' + item_type: smog}
    else:
        d = {'web_url': url_list, 'nw': nw, 'nvocab': nvocab, 'nsyllable': nsyllable, 'nsentence': nsentence,
             'n_neg_lm': n_neg_lm, 'n_pos_lm': n_pos_lm, 'n_neg_gi': n_neg_gi, 'n_pos_gi': n_pos_gi,
             'n_neg_hr': n_neg_hr, 'n_pos_hr': n_pos_hr, 'n_uctt_lm': n_uctt_lm, 'n_lit_lm': n_lit_lm,
             'n_cstr_lm': n_cstr_lm, 'n_modal_strong_lm': n_modal1_lm, 'n_modal_moderate_lm': n_modal2_lm,
             'n_modal_weak_lm': n_modal3_lm, 'n_negation_lm': n_negation_lm, 'n_negation_gi': n_negation_gi,
             'n_negation_hr': n_negation_hr, 'fre': fre, 'fkg': fkg, 'cl': cl, 'fog': fog, 'ari': ari, 'smog': smog}
    text_data = pd.DataFrame(data=d)
    text_data_saved = pd.read_csv(output_csv_dir)
    text_data = pd.concat([text_data_saved, text_data])
    text_data.to_csv(output_csv_dir, index=False)


def p_time(hint, func):
    print(f'{hint} eclipse {timeit.timeit(stmt=func, number=1)}')


logging.basicConfig(level=logging.INFO,  # 控制台打印的日志级别
                    # format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    format='%(asctime)s - [line:%(lineno)d] - %(levelname)s: %(message)s',
                    filename='nn.log',
                    # filemode='a',  # 模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志. a是追加模式，默认如果不写的话，就是追加模式
                    filemode='w',  # 模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志. a是追加模式，默认如果不写的话，就是追加模式
                    )
logging.info('---------MainStart--------')

read_lm()
read_gi()
read_csv()
web_url = sublist_per(web_url[:1000], 100)
web_url[0][:10]

s = '''
UNITED STATES

SECURITIES AND EXCHANGE COMMISSION

Washington, DC 20549

 

 

FORM 8-K

 

 

CURRENT REPORT

PURSUANT TO SECTION 13 OR 15(d)

OF THE SECURITIES EXCHANGE ACT OF 1934

Date of Report (Date of earliest event reported) February 4, 2014

 

 

NICHOLAS FINANCIAL, INC.

(Exact name of registrant as specified in its Charter)

 

 

 

British Columbia, Canada	 	0-26680	 	8736-3354
(State or Other Jurisdiction of

Incorporation or Organization)

 	
(Commission

File Number)

 	
(I.R.S. Employer

Identification No.)

 

2454 McMullen Booth Road, Building C

Clearwater, Florida

 	33759
(Address of Principal Executive Offices)	 	(Zip Code)
(727) 726-0763

(Registrant’s telephone number, Including area code)

Not applicable

(Former name, former address and former fiscal year, if changed since last report)

 

 

Check the appropriate box below if the Form 8-K filing is intended to simultaneously satisfy the filing obligation of the registrant under any of the following provisions (see General Instruction A.2. below):

 

¨	Written communications pursuant to Rule 425 under the Securities Act (17 CFR 230.425)
 

¨	Soliciting material pursuant to Rule 14a-12 under the Exchange Act (17 CFR 240.14a-12)
 

¨	Pre-commencement communications pursuant to Rule 14d-2(b) under the Exchange Act (17 CFR 240.14d-2(b))
 

¨	Pre-commencement communications pursuant to Rule 13e-4(c) under the Exchange Act (17 CFR 240.13e-4(c))
 

 

 

Item 2.02	Results of Operations and Financial Condition
February 4, 2013 – Clearwater, Florida - Nicholas Financial, Inc. (NASDAQ: NICK) announced that for the three months ended December 31, 2013 net earnings decreased 17% to $3,827,000 as compared to $4,596,000 for the three months ended December 31, 2012. Per share diluted net earnings decreased 18% to $0.31 as compared to $0.38 for the three months ended December 31, 2012. Revenue increased 1% to $20,761,000 for the three months ended December 31, 2013 as compared to $20,605,000 for the three months ended December 31, 2012.

Item 9.01 Financial Statements and Exhibits

 

Exhibit #	  	Description
99.1	  	Press release dated February 4, 2014.
SIGNATURES

Pursuant to the requirements of the Securities Exchange Act of 1934, the Registrant has duly caused this Report to be signed on its behalf by the undersigned, hereunto duly authorized.

 

 		 	NICHOLAS FINANCIAL, INC.
 		 	
(Registrant)

Date: February 4, 2014

 		 		 	
/s/ Peter L. Vosotas

 		 		 	Peter L. Vosotas
 		 		 	Chairman, President, Chief Executive Officer
 		 		 	(Principal Executive Officer)
Date: February 4, 2014

 		 		 	
/s/ Ralph T. Finkenbrink

 		 		 	Ralph T. Finkenbrink
 		 		 	Senior Vice President, Chief Financial Officer
 		 		 	(Principal Financial Officer and Accounting Officer)
Exhibit Index

 

Exhibit	  	Description
99.1	  	Press release dated February 4, 2014.
'''

soup = BeautifulSoup(s, 'html.parser')
do_html()
do_tokenize()
do_words()
start = time.time()
do_datas()
end = time.time()

for sublist in web_url:
    ############ Word Tokenization, count nword and nvocab, count negative, positive, uncertainty, litigious, constraining and modal words
    for url in tqdm(sublist):
        # for url in sublist:
        get_doc(url)
        print(f'text len:{len(doc_resp.text)}')
        soup = BeautifulSoup(doc_resp.text, 'html.parser')
        do_html()
        do_tokenize()
        do_words()
        start = time.time()
        do_datas()
        end = time.time()
        print("Elapsed (after compilation) = %s" % (end - start))

        # print(f'get_doc eclipse {timeit.timeit(stmt=get_doc(url), number=1)}')
        # print(f'text len:{len(doc_resp.text)}')
        # soup = BeautifulSoup(doc_resp.text, 'html.parser')
        # print(f'do_html eclipse {timeit.timeit(stmt=do_html, number=1)}')
        # print(f'do_tokenize eclipse {timeit.timeit(stmt=do_tokenize, number=1)}')
        # print(f'do_words eclipse {timeit.timeit(stmt=do_words, number=1)}')
        # print(f'do_datas eclipse {timeit.timeit(stmt=do_datas, number=1)}')

    #### save scraped data locally

    save_data()
    # delete text_data_saved to release memory
    del text_data_saved
    del text_data
    n = gc.collect()
