#!/usr/bin/env python3


import re
import sys
import time
import json
import regex
import logging
#logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(message)s')
import requests
from bs4 import BeautifulSoup

from ParseOut import ParseOutTitle, ParseOutContent, ParseOutTag, ParseOutURL

class Crawler:

    def __init__(self, key,
                 exclude=[],
                 page_list=range(5),
                 author = None,
                 source = None,
                 only_in_title=False,
                 patent = True,
                 sort_by_date = True,
                 y_since = None,
                 y_until = None,
                 count_per_page = 10,
                 key_score={'p': 1, 'n': -3, 'none': -5},
                 weighting={'title': 1.5, 'content': 1},
                 score_threshold=0,
                 parser='html.parser',
                 baseURL='http://scholar.google.com.tw/scholar?q='):
        self.p_key = key
        self.n_key = exclude
        self.score_threshold = score_threshold
        self.key_score = key_score
        self.weighting = weighting
        self.parser = parser
        self.pagesURL = []
        baseURL = baseURL + ('+'.join(self.p_key)) + ('+author%3A{}'.format(author) if author else '') + ('+source%3A{}'.format(source) if source else '') + ('&as_occt=title' if only_in_title else '') + ('&as_sdt=0,5' if patent else '') + ('&scisbd=1' if sort_by_date else '') + ('&as_ylo={}'.format(y_since) if y_since else '') + ('&as_yhi={}'.format(y_until) if y_until else '') + ('&num={}'.format(count_per_page))
        print('Base url:', baseURL)
        if isinstance(page_list, range):
            for page in page_list:
                self.pagesURL.append([page+1, baseURL+'&start={}'.format(int(page*count_per_page))])
        elif isinstance(page_list, list):
            for page in page_list:
                self.pagesURL.append([page, baseURL+'&start={}'.format(int((page-1)*count_per_page))])
        elif isinstance(page_list, int):
            self.pagesURL.append([page_list, baseURL+'&start={}'.format(int((page_list-1)*count_per_page))])
        else: raise ValueError('page_list must be a list, range or integer object !')

    def crawl(self):
        logger = logging.getLogger('crawl')
        results = []
        for index, page_url in self.pagesURL:
            res = requests.get(page_url)
            soup = BeautifulSoup(res.text, self.parser)
            print("### Turn to page", index, "###")
            ### Test if the crawler is blocked by the Google robot check
            page_links = soup.select('div[id="gs_nml"] a')
            if not page_links:
                logger.info('Google robot check or Out of maximum range !!')
            ### Try to crawl the page no matter it might be banned by Google robot check
            results += self.crawlPage(soup, index)
            time.sleep(4)
        print('Total acquired number:', len(results))
        return results

    #def __findPages(self):
        #logger = logging.getLogger('__findPages')
        #res = requests.get(self.url)
        #soup = BeautifulSoup(res.text, self.parser)
        #page_urls = []
        #page_links = soup.select('div[id="gs_nml"] a')
        #if not page_links:
        #    logger.debug('Can not find the pages link in the start URL!!')
        #    logger.info('1.Google robot check might ban you from crawling!!')
        #    logger.info('2.You might not crawl the page of google scholar')
        #else:
        #    counter = 0
        #    for page_link in page_links:
        #        counter += 1
        #        if (counter >= self.page):
        #            break
        #        page_url.append(self.__googleScholarURL + page_link['href'])
        #return page_urls

    def crawlPage(self, soup, page_index):
        logger = logging.getLogger('__crawlBlock')
        counter = 0; results = []
        blocks = soup.select('div[class="gs_r gs_or gs_scl"]')
        for idx, block in enumerate(blocks):
            counter += 1; result = {}
            try:
                result['title'] = block.select('h3 a')[0].text #Title
            except:
                logger.debug("No Title in Page %s Item %s", page_index, counter)
                continue
            try:
                result['url'] = ParseOutURL(block.select('h3 a')[0]['href'])
            except:
                logger.debug("No URL in Page %s Item %s", page_index, counter)
                result['url'] = None
            try: # need to be updated
                cite = block.select('div[class="gs_fl"]')[0].text.strip()
                if 'Cited by ' in cite: 
                    result['cite'] = int(cite.replace('Cited by ','').split(' ')[0])
                else: 
                    result['cite'] = 0
            except: 
                result['cite'] = 0
            try:
                result['year'] = int(block.select('div[class="gs_a"]')[0].text.split(' - ')[-2][-4:])
            except:
                logger.debug("No year in Page %s Item %s", page_index, counter); result['year'] = None

            fail = False
            source = block.select('div[class="gs_a"]')[0].text.split(' - ')[-1] #Publication type
            if 'Google Patents' in source: 
                result['type'] = 'patent'; result['journal'] = 'Google Patents'
            elif 'books.google.com' in source: 
                result['type'] = 'book'; result['journal'] = 'Book'
            elif ('arxiv.org' in source) | ('biorxiv.org' in source) | ('engrxiv.org' in source): 
                result['type'] = 'pre-print'; result['journal'] = source
            else: 
                result['type'] = 'paper'
            
            if 'Elsevier' in source:
                try:
                    res_ = requests.get('https://scholar.google.com.tw'+block.find_all('a',attrs={'href':re.compile('/scholar?')})[0]['href'])
                    soup_ = BeautifulSoup(res_.text, self.parser)
                    block = soup_.select('div[class="gs_r gs_or gs_scl"]')[1]
                    result['url'] = ParseOutURL(block.select('h3 a')[0]['href'])
                except:
                    logger.debug("No URL accessible in Page %s Item %s", page_index, counter)
                    result['url'] = None
            
            if result['url'] != None:
                if 'pdf' not in result['url']:
                    res_ = requests.get(result['url']); soup_ = BeautifulSoup(res_.text, self.parser)
                    if result['type'] == 'patent': 
                        try: 
                            if '\xa0' in result['title']: result['title'] = soup_.select('title')[0].string.replace(' \n        - Google Patents','')
                        except: True
                        try: 
                            result['abstract'] = soup_.select('div[class="abstract"]')[0].string.lower()
                            result['complete'] = True
                        except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); fail = True
                        try: result['authors'] = ', '.join([tag.string.replace(',','') for tag in soup_.find_all('dd', itemprop="inventor")])
                        except Exception as e:
                            _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno)
                            try: result['authors'] = block.select('div[class="gs_a"]')[0].text.split(' - ')[0]
                            except: logger.debug("No Author in Page %s Item %s", page_index, counter)
                    elif result['type'] == 'book': fail = True
                    elif result['type'] == 'pre-print': 
                        try: 
                            if '\xa0' in result['title']: result['title'] = soup_.find_all('meta', attrs={'name':'citation_title'})[0]['content']
                        except: True
                        try: 
                            if 'arxiv.org' in source:
                                result['abstract']=soup_.find_all('meta',attrs={'property':'og:description'})[0]['content'].replace('\n',' ')
                            else:
                                result['abstract']=soup_.find_all('meta', attrs={'name':'citation_abstract'})[0]['content'].split('<p>')[-1].split('</p>')[0]
                            result['abstract'] = result['abstract'].strip().lower()
                            result['complete'] = True
                        except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); fail = True
                        try:
                            if 'arxiv.org' in source:
                                result['authors'] = ', '.join([tag.string.replace(',','') for tag in soup_.select('div[class="authors"]')[0].find_all('a')])
                            else:
                                result['authors'] = ', '.join([tag['content'].replace(',','') for tag in soup_.find_all('meta', attrs={'name':'citation_author'})])
                        except Exception as e:
                            _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno)
                            try: result['authors'] = block.select('div[class="gs_a"]')[0].text.split(' - ')[0]
                            except: logger.debug("No Author in Page %s Item %s", page_index, counter)
                    elif 'ieee' in source:
                        pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}'); userInfo = None
                        for dic in pattern.findall(soup_.get_text()):
                            if 'userInfo' in dic: userInfo =  json.loads(dic)
                        if userInfo == None: fail = True
                        else:
                            try: 
                                if '\xa0' in result['title']: result['title'] = userInfo['title']
                            except: True
                            try:
                                result['url'] = 'https://doi.org/' + userInfo['doi'].replace('doi:',''); print(idx+1, result['url'])
                                result['abstract'] = userInfo['abstract'].lower(); result['complete'] = True
                            except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); fail = True
                            try: result['journal'] = userInfo['publicationTitle']
                            except: result['journal'] = 'IEEE'
                            try:
                                result['authors'] = ', '.join([author['name'].replace('  ',' ').replace(',','') for author in userInfo['authors']])
                            except Exception as e:
                                _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno)
                                try: result['authors'] = block.select('div[class="gs_a"]')[0].text.split(' - ')[0]
                                except: logger.debug("No Author in Page %s Item %s", page_index, counter)
                    else: 
                        doi = soup_.find_all('meta', attrs={'name':re.compile('doi')})
                        if len(doi) > 0: doi = doi[0]['content'].replace('doi:','')
                        else: 
                            try: ## search doi in NCBI
                                res_=requests.get('https://www.ncbi.nlm.nih.gov/pubmed?term=('+result['title'].replace('\xa0','')+'[Title])')
                                soup_ = BeautifulSoup(res_.text, self.parser)
                                doi_title = soup_.select('title')[0].string.replace('  - PubMed - NCBI\n','')
                                if ('[Title]' in doi_title) | ('No items found' in doi_title):
                                    raise ValueError(str(idx+1) + ' DOI cannot be captured')
                                else: 
                                    doi = soup_.find_all('a', attrs={'href':re.compile('doi')})
                                    if len(doi) > 0: doi = doi[0].string.replace('doi:','')
                                    else: raise ValueError(str(idx+1) + ' DOI cannot be captured')
                            except: doi = None
                        if doi != None:
                            try:
                                res_ = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term='+doi)
                                soup_ = BeautifulSoup(res_.text, self.parser)
                                if len(soup_.select('errorlist'))>0: raise ValueError(str(idx+1) + ' DOI not in PubMed')
                                PMID = soup_.select('id')[0].string
                                res_ = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id='+PMID)
                                soup_ = BeautifulSoup(res_.text, self.parser)
                                if '\xa0' in result['title']: result['title'] = soup_.select('articletitle')[0].string
                                result['abstract'] = soup_.select('abstracttext')[0].string.lower()
                                result['journal'] = soup_.select('title')[0].string
                                result['authors'] = ', '.join([
                                    (a.select('lastname')[0].string if len(a.select('lastname')) > 0 else '')+' '+(a.select('forename')[0].string if len(a.select('forename')) > 0 else '') for a in soup_.find_all('author')
                                ])
                                result['url'] = 'https://doi.org/' + doi; print(idx+1, result['url'])
                                result['complete'] = True
                            except Exception as e: 
                                _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno)
                                res_ = requests.get(result['url']); soup_ = BeautifulSoup(res_.text, self.parser)
                                result['url'] = 'https://doi.org/' + doi; print(idx+1, result['url'])
                                ## need to be updated soup_.find_all('div', attrs={'class':re.compile('NLM_paragraph')})
                                try:
                                    if '\xa0' in result['title']: result['title'] = soup_.select('title')[0].string
                                except: True
                                try: result['journal'] = soup_.find_all('meta', attrs={'name':'citation_journal_title'})[0]['content']
                                except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); result['journal'] = source
                                try: result['authors'] = ', '.join([author['content'].replace('  ',' ').replace(',','') for author in soup_.find_all('meta', attrs={'name':'citation_author'})])
                                except Exception as e:
                                    _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno)
                                    try: result['authors'] = block.select('div[class="gs_a"]')[0].text.split(' - ')[0]
                                    except: logger.debug("No Author in Page %s Item %s", page_index, counter)
                                try: result['abstract'] = soup_.find_all('meta', attrs={'name':re.compile('description')})[0]['content']
                                except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); fail = True
                                try: 
                                    if result['abstract'][-3:] == '...': result['complete'] = False
                                    else: result['complete'] = True
                                except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); fail = True
                        else:
                            res_ = requests.get(result['url']); soup_ = BeautifulSoup(res_.text, self.parser)
                            ## need to be updated soup_.find_all('div', attrs={'class':re.compile('NLM_paragraph')})
                            try:
                                if '\xa0' in result['title']: result['title'] = soup_.select('title')[0].string
                            except: True
                            try: result['journal'] = soup_.find_all('meta', attrs={'name':'citation_journal_title'})[0]['content']
                            except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); result['journal'] = source
                            try: result['authors'] = ', '.join([author['content'].replace('  ',' ').replace(',','') for author in soup_.find_all('meta', attrs={'name':'citation_author'})])
                            except Exception as e:
                                _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno)
                                try: result['authors'] = block.select('div[class="gs_a"]')[0].text.split(' - ')[0]
                                except: logger.debug("No Author in Page %s Item %s", page_index, counter)
                            try: result['abstract'] = soup_.find_all('meta', attrs={'name':re.compile('description')})[0]['content']
                            except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); fail = True
                            try: 
                                if result['abstract'][-3:] == '...': result['complete'] = False
                                else: result['complete'] = True
                            except Exception as e: _,_,etb = sys.exc_info(); print(idx+1, e, 'at line', etb.tb_lineno); fail = True
                else: fail = True
            else: fail = True
            
            if result['url'] == None:
                try:
                    result['url'] = ParseOutURL(block.select('h3 a')[0]['href'])
                except:
                    logger.debug("No URL in Page %s Item %s", page_index, counter)
                    result['url'] = None

            if fail:
                result['complete'] = False; result['journal'] = source; print(idx+1, 'abstract may not complete')
                try:
                    result['abstract'] = block.select('div[class="gs_rs"]')[0].text
                except:
                    logger.debug("No Abstract in Page %s Item %s", page_index, counter)
            
            ### Check keywords in titles and contents
            ### Evaluate the score of titles and contents by keywords
            t_score = ParseOutTitle(result['title'], self.p_key, self.n_key, self.key_score)
            c_score = ParseOutContent(result['abstract'], self.p_key, self.n_key, self.key_score)
            result['require'], result['score'] = self.requireThesis(t_score, c_score)
            link = block.select('div[class="gs_ggsd"] a')
            if link: result['pdf_link'] = link[0]['href']
            ### Set result['download'] to False,
            ### because the thesis hasn't been downloaded
            #result['download'] = False
            ### test only the first link in each page
            #break
            results.append(result)

        return results

    def requireThesis(self, t_score, c_score):
        score = self.weighting['title'] * t_score + self.weighting['content'] * c_score
        if (score > self.score_threshold):
            return (True, score)
        else:
            return (False, score)

#    def __getPDF(self, url, title, year):
#        res = requests.get(url)
#        print "in __getPDF"
#        f_name = year + " - " + title.strip() + '.pdf'
#        with open(f_name, 'wb') as f:
#            print "Downloading PDF... " + title
#            f.write(res.content)

#    def __getHTML2PDF(self, url, title, year):
#        options = {'page-size': 'A4', 'dpi': 400}
#        f_name = year + " - " + title.strip() + '.pdf'
#        pdfkit.from_url(url, f_name, options = options)
