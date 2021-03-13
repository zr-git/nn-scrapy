############### import packages
import os, nltk, numpy as np, pandas as pd, time, textstat, re, csv, gc, random, requests
from bs4 import BeautifulSoup
from nltk import word_tokenize
from tqdm import tqdm

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

# ############### Set working directory to parent directory
# if os.getcwd() != r'F:\github\narrative_conservatism\code':
#     os.chdir(r'F:\github\narrative_conservatism\code')


# In[4]:


############### Read LM disctionary
# LM = pd.read_excel(dictionary_dir + 'LM\\LoughranMcDonald_MasterDictionary_2018.xlsx', encoding = "utf-8")
LM = pd.read_csv(dictionary_dir + 'LM\\LoughranMcDonald_MasterDictionary_2018.csv', sep=',', encoding="utf-8")

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

############# Create a negation word list
gt_negation = ['no', 'not', 'none', 'neither', 'never', 'nobody']  ## Gunnel Totie, 1991, Negation in Speech and Writing

# In[5]:


############### Read GI disctionary
GI_cols = ['Entry', 'Source', 'Positiv', 'Negativ']
# GI = pd.read_excel(dictionary_dir + 'GI\\inquirerbasic.xls', encoding = "utf-8", usecols = GI_cols)
GI = pd.read_csv(dictionary_dir + 'GI\\inquirerbasic.csv', sep=',', encoding="utf-8", usecols=GI_cols)
GI = GI[(GI['Entry'].str.endswith('#1') == True) | (GI['Entry'].str.contains('#') == False)]
GI['Entry'] = GI['Entry'].str.replace('#1', '')

############### Create negative, positive, uncertainty, litigious, constraining and modal word lists
gi_neg = GI.loc[GI['Negativ'].notnull()]['Entry'].values.tolist()
gi_pos = GI.loc[GI['Positiv'].notnull()]['Entry'].values.tolist()

gi_neg = [w.lower() for w in gi_neg]
gi_pos = [w.lower() for w in gi_pos]

# In[6]:


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

# In[7]:


#####################################################################
#################### FOR ALL PROCESSED FILES LOOP ###################
#####################################################################

# ############# OPTION 1: Create input txt file index from disk
# processed = []
# for subdir, dirs, files in os.walk(raw_filing_dir):
#     for file in files:
#         processed.append(os.path.join(subdir, file))

############# OPTION 2: Create input txt file index: from list of true positive files
id_data = pd.read_csv(input_csv_dir,
                      dtype={'cik': str, 'bazip': str, 'sic': str, 'fye': str, 'film': str, 'irs': str, 'web_url': str})
id_data = id_data[(id_data.duplicated('accnum') == False) & (id_data['accnum'].notnull())]
web_url = id_data['web_url'].values.tolist()
# web_url = random.sample(processed, 10086)
len(web_url)


# In[8]:


#### Define the function sublist_per to make sublists inside a list for every "step" (=5000) elements
#### so that once after every 5000 filing information have been extracted, they are saved to disk, and scraping can resume from where it was interrupted last time
#### to avoid time loss due to system crash
def sublist_per(source, step):
    return [source[i - step:i] for i in list(range(len(source)))[::step][1:]] + [
        source[list(range(len(source)))[::step][-1]:]]


# print(processed)
web_url = sublist_per(web_url[:1045], 100)
web_url[0][:10]


# In[9]:


#### Define a function count_occurrence to count the number of words in tup that pertaining to a list
def count_occurrence(tup, lst):
    count = 0
    for item in tup:
        if item in lst:
            count += 1

    return count


### Define a function count_negation to count cases where negation occurs within four or fewer words from a word identified in list.
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


# In[10]:


def process_data(contents):
    ############ Word Tokenization
    ## Raw tokens: including punctuations, numbers etc.
    tokens = word_tokenize(contents)

    ## Convert all words into small cases
    ## Keep tokens that purely consist of alphabetic characters only
    ## Delete single-character words except for 'I'
    words = [w.lower() for w in tokens if w.isalpha() and len(w) > 1 or w == 'i']

    ########### Delete words with lenth smaller than 1% and largr than 99% of the document
    # wordlen99 = np.quantile([len(w) for w in words], 0.99)
    # wordlen1 = np.quantile([len(w) for w in words], 0.01)
    # words = [w for w in words if len(w)<wordlen99 and len(w)>wordlen1]
    # vocab = sorted(set(words))

    ########### Save text statistics
    ##### 1. nw 2. nvocab 3. nsyllable 4.nsentence 5. tone 6. readability

    ## 1. nw
    nw.append(len(words))

    ## 2. nvocab
    # nvocab.append(len(vocab))

    ## 3. syllable
    # nsyllable.append(textstat.syllable_count(contents))

    ## 4. sentence
    # nsentence.append(textstat.sentence_count(contents))

    ## 5. tone
    ### LM dictionary
    n_neg_lm.append(count_occurrence(words, lm_neg))
    n_pos_lm.append(count_occurrence(words, lm_pos))
    n_uctt_lm.append(count_occurrence(words, lm_uctt))
    n_lit_lm.append(count_occurrence(words, lm_lit))
    #         n_cstr_lm.append(count_occurrence(words, lm_cstr))
    #         n_modal1_lm.append(count_occurrence(words, lm_modal1))
    #         n_modal2_lm.append(count_occurrence(words, lm_modal2))
    #         n_modal3_lm.append(count_occurrence(words, lm_modal3))
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
    #         fre_i = textstat.flesch_reading_ease(contents)
    #         if fre_i > 100:
    #             fre_i = 100
    #         if fre_i < 0:
    #             fre_i = float('NaN')
    #         fre.append(fre_i)

    #         fkg_i = textstat.flesch_kincaid_grade(contents)
    #         if fkg_i < 0:
    #             fkg_i = float('NaN')
    #         fkg.append(fkg_i)
    #         #RIX
    #         cl_i = textstat.coleman_liau_index(contents)
    #         if cl_i < 0:
    #             cl_i = float('NaN')
    #         cl.append(cl_i)

    fog.append(textstat.gunning_fog(contents))
    ari.append(textstat.automated_readability_index(contents))
    smog.append(textstat.smog_index(contents))
    # LIX


# In[11]:


def get_content(url):
    time.sleep(time_waiting)  # SEC does not allow to exceed 10 requests/sec
    doc_resp = requests.get(url, headers=headers)
    if doc_resp.status_code == 429:
        time.sleep(10 * 60 + 5)  # if exceeds cool off for 10 mins
        doc_resp = requests.get(url, headers=headers)
    else:
        pass
    return doc_resp


# In[12]:


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'}

if os.path.exists(output_csv_dir) == False:
    with open(output_csv_dir, mode='w') as file:
        writer = csv.writer(file, delimiter=',')
        if (obj_type == '10-K') | (obj_type == '10-Q'):
            writer.writerow(['web_url', 'nw_' + item_type, 'n_neg_lm_' + item_type, 'n_pos_lm_' + item_type,
                             'n_neg_gi_' + item_type, 'n_pos_gi_' + item_type, 'n_neg_hr_' + item_type,
                             'n_pos_hr_' + item_type, 'n_uctt_lm_' + item_type, 'n_lit_lm_' + item_type,
                             'n_negation_lm_' + item_type, 'n_negation_gi_' + item_type, 'n_negation_hr_' + item_type,
                             'fog_' + item_type, 'ari_' + item_type, 'smog_' + item_type])
        else:
            writer.writerow(
                ['web_url', 'nw', 'n_neg_lm', 'n_pos_lm', 'n_neg_gi', 'n_pos_gi', 'n_neg_hr', 'n_pos_hr', 'n_uctt_lm',
                 'n_lit_lm', 'n_negation_lm', 'n_negation_gi', 'n_negation_hr', 'fog', 'ari', 'smog'])
for sublist in web_url:
    ############ Full Text Raw Count
    url_list = []

    nw = []
    # nvocab = []
    # nsyllable = []
    # nsentence = []

    n_neg_lm = []
    n_pos_lm = []
    n_neg_gi = []
    n_pos_gi = []
    n_neg_hr = []
    n_pos_hr = []
    n_uctt_lm = []
    n_lit_lm = []
    # n_cstr_lm = []
    # n_modal1_lm = []
    # n_modal2_lm = []
    # n_modal3_lm = []
    n_negation_lm = []
    n_negation_gi = []
    n_negation_hr = []

    # fre = []
    # fkg = []
    # cl = []
    fog = []
    ari = []
    smog = []

    ############ Word Tokenization, count nword and nvocab, count negative, positive, uncertainty, litigious, constraining and modal words
    for url in tqdm(sublist):
        ### use url, instead of accnum, as key to link to id_data
        url_list.append(url)
        ############# Read txt file from EDGAR
        doc_resp = get_content(url)
        soup = BeautifulSoup(doc_resp.text, 'html.parser')
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
        process_data(contents)

    #### save scraped data locally
    if (obj_type == '10-K') | (obj_type == '10-Q'):
        d = {'web_url': url_list, 'nw_' + item_type: nw, 'n_neg_lm_' + item_type: n_neg_lm,
             'n_pos_lm_' + item_type: n_pos_lm, 'n_neg_gi_' + item_type: n_neg_gi, 'n_pos_gi_' + item_type: n_pos_gi,
             'n_neg_hr_' + item_type: n_neg_hr, 'n_pos_hr_' + item_type: n_pos_hr, 'n_uctt_lm_' + item_type: n_uctt_lm,
             'n_lit_lm_' + item_type: n_lit_lm, 'n_negation_lm_' + item_type: n_negation_lm,
             'n_negation_gi_' + item_type: n_negation_gi, 'n_negation_hr_' + item_type: n_negation_hr,
             'fog_' + item_type: fog, 'ari_' + item_type: ari, 'smog_' + item_type: smog}
    else:
        d = {'web_url': url_list, 'nw': nw, 'n_neg_lm': n_neg_lm, 'n_pos_lm': n_pos_lm, 'n_neg_gi': n_neg_gi,
             'n_pos_gi': n_pos_gi, 'n_neg_hr': n_neg_hr, 'n_pos_hr': n_pos_hr, 'n_uctt_lm': n_uctt_lm,
             'n_lit_lm': n_lit_lm, 'n_negation_lm': n_negation_lm, 'n_negation_gi': n_negation_gi,
             'n_negation_hr': n_negation_hr, 'fog': fog, 'ari': ari, 'smog': smog}

    text_data = pd.DataFrame(data=d)

    text_data_saved = pd.read_csv(output_csv_dir)
    text_data = pd.concat([text_data_saved, text_data])
    text_data.to_csv(output_csv_dir, index=False)
    # delete text_data_saved to release memory
    del text_data_saved
    del text_data
    n = gc.collect()

# In[ ]:


# #####################################################################
# ################### FOR SINGLE FILE INSPECTION ######################
# #####################################################################

# ############ Word Tokenization
# ## Raw tokens: including punctuations, numbers etc.
# with open(processed[1], 'r',  encoding = "utf-8") as file:
#     contents = file.read().replace('\n', ' ').replace('\xa0', ' ')
# tokens = word_tokenize(contents)

# #tokens

# ## Convert all words into small cases
# ## And keep tokens that purely consist of alphabetic characters only
# words = [w.lower() for w in tokens if w.isalpha() and len(w)>1 or w =='i']
# vocab = sorted(set(words))

# # words[2500:2600]
# # vocab[:50]


# In[ ]:


# def count_occurrence(tup, lst):
#     count = 0
#     for item in tup:
#         if item in lst:
#             count+= 1

#     return count

# count_occurrence(words, lm_neg)


# In[ ]:


# gt_negation = ['no', 'not', 'none', 'neither', 'never', 'nobody'] ## Gunnel Totie, 1991, Negation in Speech and Writing

# def count_negation(tup, lst, negation):
#     count = 0
#     for item in tup:
#         if item in lst:
#             if tup.index(item)-4 > 0 and tup.index(item)+4 < len(tup):
#                 neighbor = tup[tup.index(item)-4:tup.index(item)+4]
#                 for neighborw in neighbor:
#                     if neighborw in negation:
#                         count+= 1

#             if tup.index(item)-4 < 0:
#                 pre = tup[0:tup.index(item)+4]
#                 for prew in pre:
#                     if prew in negation:
#                         count+= 1

#             if tup.index(item)+4 > len(tup):
#                 post = tup[tup.index(item)-4:len(tup)]
#                 for postw in post:
#                     if postw in negation:
#                         count+= 1
#     return count

# count_negation(words, lm_pos, gt_negation)


# In[ ]:


# ########### Winsorize words with lenth smaller than 1% and largr than 99% of the document
# wordlen99 = np.quantile([len(w) for w in words], 0.99)
# wordlen1 = np.quantile([len(w) for w in words], 0.01)
# words = [w for w in words if len(w)<wordlen99 and len(w)>wordlen1]
# vocab = sorted(set(words))

# vocab[:50]


# In[23]:


######### See the most common 20 words
# fdist = nltk.FreqDist(words)
# fdist.most_common(30)

