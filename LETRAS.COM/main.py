# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import time
import random
import codecs
import json
import os
import re
import linecache
import sys
import logging
import datetime
import csv
import unicodecsv

import configparser
config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(level=logging.INFO)


class IO(object):

    @staticmethod
    def save_text_to_file(text, filename):
        with codecs.open(filename, 'a', 'utf-8') as f:
            f.write(text)

    @staticmethod
    def write_to_csv(outfile_path,row,mode = "a"):
        try:
            with open(outfile_path, str(mode)) as f:
                writer = unicodecsv.writer(f, encoding='utf-8')
                writer.writerow(row)  
        except Exception as e:
            logging.error('Error in writing File : "{}"'.format(str(e)))

    @staticmethod
    def create_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def create_file(filename):
        with codecs.open(filename, 'w', 'utf-8') as f:
            pass
        return

    @staticmethod
    def create_log_file():
        with codecs.open(config.get('Files','json_logfile'), 'w', 'utf-8') as f:
            pass
        return
 
    @staticmethod
    def read_list_of_lists_from_file_usung_csv_v1(filename):
        """

        :param filename:
        :return: [[p11, p12],[p21, p22]]
        """
        datas = []
        with codecs.open(filename, 'r') as f:
            r = csv.reader(f, delimiter=str(config.get('Files','csv_delimeter')))
            for l in r:
                unicode(l).encode("utf-8")
                datas.append(l)
        return datas     

class SeleniumScraperMixin(object):

    @staticmethod
    def init_webdriver(use_webdriver):
        if use_webdriver == 'phantomjs':
            #driver = webdriver.PhantomJS()
            driver = webdriver.PhantomJS(desired_capabilities=webdriver.DesiredCapabilities.PHANTOMJS)
        elif use_webdriver == 'chrome':
            driver = webdriver.Chrome()
        else:
            # default
            driver = webdriver.Firefox()
        return driver

    def __del__(self):
        try:
            self.driver.close()
        except:
            pass
            
        del self.driver

    def get_text(self, elem):
        try:
            text = (elem.text or elem.get_attribute('innerHTML')).strip()
        except:
            text = "ERROR. {0}".format(sys.exc_info())
        return text

    def get_elem_text_safe(self, parent, css_selector):
        elems = parent.find_elements_by_css_selector(css_selector)
        #print('elem:',elems)
        if elems:
            return self.get_text(elems[0])
        else:
            #print('else part')
            return u''

    def get_elem_attr_safe(self, parent, css_selector, attr_name):
        elems = parent.find_elements_by_css_selector(css_selector)
        if elems:
            return elems[0].get_attribute(attr_name)
        else:
            return u''

    def _get_elems_with_waiting(self,css_selector,wait=4):
        try:
            elems = WebDriverWait(self.driver, wait).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
            )
        except:
            elems = None
        return elems

    def wait_and_get_elems(self, css_selector, timeout=int(config.get('Timer','max_timeout')), try_except=True):
        """
        try_except = True: wrap it here
        try_except = False: wrap in the code
        """
        def _get_elems():
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
            )

        if not try_except:
            # if exception handle it in the main part
            return _get_elems()
        else:
            while 1:
                # 3? times to auto find element at the page, then manually
                for t in range(int(config.get('Timer','autoattempts'))):
                    try:
                        while 1:
                            # 3? times auto then manual for "is any elem displayed?"
                            for i in range(int(config.get('Timer','autoattempts'))):
                                # TimeoutException if elem not appears while MAX_TIMEOUT
                                elems = _get_elems()
                                # check for visible
                                # if not visible then click() function will fails

                                #--- any elem displayed?
                                if reduce(lambda x, y: x or y, [elem.is_displayed() for elem in elems]):
                                    return elems
                                else:
                                    logging.warning('{} displayed: {}'.format(css_selector, elems[0].is_displayed()))
                                    logging.warning('Autoretry during {} seconds'.format(self.max_timeout/2))
                                    time.sleep(self.max_timeout)
                                    continue

                            logging.warning('{0} not displayed'.format(css_selector))
                            #s = raw_input('Wait for display and press Enter key (preferred) or enter Q to return in main loop (may shut down the script with exception): ', )
                            logging.warning('Elems not found. Return False')
                            s = 'Q'     # hard coded Quit
                            if re.findall('(?i)[QqЙй]', s):
                                # quit and return to main loop
                                return
                            # still try for is_displayed = True
                            continue
                    except:
                        logging.warning("Problem with getting {0}. Element doesn't exist".format(css_selector))
                        logging.warning('Autoretry during {0} seconds'.format(self.max_timeout/2))
                        time.sleep(self.max_timeout/2)
                        continue

                logging.warning("Problem with getting {0}. Element doesn't exist".format(css_selector))
                logging.warning(sys.exc_info()[0])
                # s = raw_input('Wait for element and press Enter key (preferred) or enter Q to return in main loop (may shut down the script with exception): ', )
                s = 'Q'     # hard coded Quit
                logging.warning('Elems not found. Return False')
                if re.findall('(?i)[Qq]', s):
                    # quit and return to main loop
                    return
                continue

class PageElems(object):
    url = 'http://www.letras.com/letra/'

    artists_links_cell = 'div[class="artistas-a js-alphabet-cnt"]>ul[class="cnt-list cnt-list--col3"]>li>a'
    #sort_by_song_cell = 'a[onclick="return showSong();"]'
    
    all_songs_view_cell = 'a[data-action="all"]'
    songs_links_cell_all = 'div[class="cnt-list--alp"] ul li>a'
    songs_links_cell_pop = 'div[class="artista-top g-sp g-pr"] ol li>a'

    artist_name_cell = 'div[class="cnt-head_title"] h2 a'
    song_name_cell = 'div[class="cnt-head_title"] h1'

    song_lyrics_cell = 'div[class="g-pr g-sp"] article'
    #song_lyrics_cell_2 = 'div[class="col-xs-12 col-lg-8 text-center"]>div:nth-child(10)'
    #song_album_cell = 'div[class="panel album-panel noprint"]>a'
    song_credits_cell = 'div[class="letra-info_comp"]'
    #song_feat_cell = 'span[class="feat"]'


class LETRAS(SeleniumScraperMixin,object):

    def __init__(self, *a, **kw):
        
        self.incoming_data_file = kw.get('incoming_data_file','')
        self.tempdir = kw.get('tempdir', config.get('Files','outdir'))
        self.output_data_file =os.path.abspath(os.path.join(self.tempdir, kw.get('output_data_file', config.get('Files','output_data_file'))) )
        
        self.is_first_file_item = True  # to add ',' only before second and next saving entries
        IO.create_dir(self.tempdir)
        IO.create_file(self.output_data_file)
        self.header =['Url','ArtistName','SongName','SongLyrics','Credits']
        self.use_webdriver = kw.get('use_webdriver', config.get('Driver','default_webdriver'))
        self.driver = self.init_webdriver(self.use_webdriver)
        self.max_timeout = int(config.get('Timer','max_timeout'))
        self.el_id_xPath = self.driver.find_element_by_xpath
        self.els_id_xPath = self.driver.find_elements_by_xpath
        self.el_id = self.driver.find_element_by_id
        self.el = self.driver.find_element_by_css_selector
        self.els = self.driver.find_elements_by_css_selector
        self.read_csv_artists()


    def get_all_artists_on_page_by_alphabet(self,alpha):
        for t in range(int(config.get('Timer','autoattempts'))):
            try:
                artist_alphabet = alpha.strip().upper()
                url = str(PageElems.url+artist_alphabet+"/artistas.html")
                logging.info(url)
                self.driver.get(url)
                #time.sleep(3)
                break
            except Exception as e:
                url = ""
                logging.warning('Autoretry  {0}/{0} Times'.format(int(t),int(config.get('Timer','autoattempts'))))
                logging.error(str(e))
                logging.error("Can't Query This Search  ... Returning False")    
                continue

        all_links = []
        try:
            artists_links_elems = self._get_elems_with_waiting(PageElems.artists_links_cell)
            logging.info('Extracting all links [{}] For artists at: "{}"'.format(len(artists_links_elems),url))
            for index,a_links in enumerate(artists_links_elems):
                exrtacted_data = {
                    'artist_link_name' : '',
                    'artist_link_href' : ''
                } 
                exrtacted_data['artist_link_name'] = a_links.text
                exrtacted_data['artist_link_href'] = a_links.get_attribute('href')
                logging.info("{}/{}=> (Extracted Link : '{}')".format(index+1,len(artists_links_elems),exrtacted_data))
                all_links.append(exrtacted_data)
        except Exception as e:
            logging.error("in get_all_artists_on_page_by_alphabet: {}".format(str(e)))
        return all_links

    def get_all_songs_on_page_by_artist(self,url):
        for t in range(int(config.get('Timer','autoattempts'))):
            try:
                logging.info(url)
                self.driver.get(url)
                try:
                    songs_links_cell = PageElems.songs_links_cell_pop
                    all_s =self._get_elems_with_waiting(PageElems.all_songs_view_cell)
                    if len(all_s)>0:
                        songs_links_cell = PageElems.songs_links_cell_all
                    else:
                        songs_links_cell = PageElems.songs_links_cell_pop

                except:
                    songs_links_cell = PageElems.songs_links_cell_pop
                #time.sleep(3)
                break
            except Exception as e:
                logging.warning('Autoretry  {0}/{0} Times'.format(int(t),int(config.get('Timer','autoattempts'))))
                logging.error(str(e))
                logging.error("Can't get_all_songs_on_page_by_artist ... Returning False")    
                continue
        if not self.driver.current_url == url:
            return []
        all_links = []
        try: 
            songs_links_elems = self.wait_and_get_elems(songs_links_cell)
            logging.info('Extracting all song links [{}] For artists at: "{}"'.format(len(songs_links_elems),url))
            for index,s_links in enumerate(songs_links_elems):
                exrtacted_data = {
                    'song_link_name' : '',
                    'song_link_href' : ''
                }   
                exrtacted_data['song_link_name'] = s_links.text
                exrtacted_data['song_link_href'] = s_links.get_attribute('href')
                if exrtacted_data['song_link_href']:
                    logging.info("{}/{}=> (Extracted song Link : '{}')".format(index+1,len(songs_links_elems),exrtacted_data))
                    all_links.append(exrtacted_data)

        except Exception as e:
            logging.error("in get_all_songs_on_page_by_artist: {}".format(str(e)))
        return all_links

    def get_songs_data_on_page(self,url):

        url = str(url)
        exrtacted_data = {
            'Url': url,
            'SongName' : '',
            'ArtistName' : '',
            'SongLyrics' : '',
            'Credits' : ''
        }
        for t in range(int(config.get('Timer','autoattempts'))):
            try:
                #logging.info("in get_songs_data_on_page: {}".format(url))
                self.driver.get(url)
                logging.info('Extracting song Data For: <"{}">'.format(url))

                exrtacted_data['SongName'] = self.wait_and_get_elems(PageElems.song_name_cell)[0].text
                
                exrtacted_data['ArtistName'] = self.wait_and_get_elems(PageElems.artist_name_cell)[0].text.replace(" LYRICS","")
                
                try:
                    songLyrics = self._get_elems_with_waiting(PageElems.song_lyrics_cell)
                    if songLyrics:
                        songLyrics = songLyrics[0].text
                except Exception as e:
                    songLyrics = ''

                exrtacted_data['SongLyrics'] = songLyrics if songLyrics else ""

                try:
                    exrtacted_data['Credits'] = self._get_elems_with_waiting(PageElems.song_credits_cell)[0].get_attribute('innerHTML')
                    try:
                        exrtacted_data['Credits'] =  exrtacted_data['Credits'].split("<a href=")[0].strip()
                    except:
                        exrtacted_data['Credits'] =  exrtacted_data['Credits']
                except Exception as e:
                    exrtacted_data['Credits'] = ''
                
                #print 'here 7'
                logging.info("Extracted Song Data:'{}'".format(exrtacted_data['SongName']))
                
            except Exception as e:
                logging.warning('Autoretry get_songs_data_on_page  {0}/{0} Times'.format(int(t),int(config.get('Timer','autoattempts'))))   
                continue

            return exrtacted_data     


    def read_csv_artists(self):
        queries = IO.read_list_of_lists_from_file_usung_csv_v1(self.incoming_data_file)

        #IO.save_text_to_file('[', self.output_data_file)
        IO.write_to_csv(self.output_data_file,self.header,"w+")
        
        data_list = list()     # open json list
        
        for index,query_list in enumerate(queries):
            try:
                try:
                    alphabet = query_list[0]
                except:
                    alphabet = None

                try:
                    artist = query_list[1]
                except:
                    artist = None

                logging.info('{}/{}=> (Artist <"{}"> AT LETRAS)'.format(index+1,len(queries),alphabet))
                all_artist_links_list = self.get_all_artists_on_page_by_alphabet(alphabet)
                all_artist_links_list=all_artist_links_list
                for index,artists_link in enumerate(all_artist_links_list):
                    logging.info('{}/{}=> (Processing artist link :"{}" )'.format(index+1,len(all_artist_links_list),artists_link))
                    all_songs_list = self.get_all_songs_on_page_by_artist(artists_link['artist_link_href'])
                    artists_link['songs_list'] = all_songs_list
                    for index,song_link in enumerate(artists_link['songs_list']):
                        logging.info('{}/{}=> (Processing song link :"{}" )'.format(index+1,len(all_songs_list),song_link))
                        #print "song_link : ",song_link
                        if not song_link['song_link_href']:
                            continue
                        songs_data = self.get_songs_data_on_page(song_link['song_link_href'])
                        song_link['song_data'] = songs_data
                        if songs_data:
                            row =[songs_data['Url'],songs_data['ArtistName'],songs_data['SongName'],
                                  songs_data['SongLyrics'],songs_data['Credits']
                                 ]
                            IO.write_to_csv(self.output_data_file,row,"a") 
                            logging.info("Data Saved For Song: <{}>".format(songs_data['SongName']))
                
                data_list.append(all_artist_links_list)     

            except Exception as e:
                    logging.error('IN MAIN :: {} '.format(str(e)))
                    continue           

            time.sleep(int(config.get('DELAY_BETWEEN_QUERIES','from')) + random.random()*(int(config.get('DELAY_BETWEEN_QUERIES','to'))-int(config.get('DELAY_BETWEEN_QUERIES','from'))) )
        

if __name__ == '__main__':
    songs_book =  LETRAS(
        output_data_file=str(config.get('Files','output_data_file')) ,
        incoming_data_file=str(config.get('Files','incoming_data_file'))
        )   
