#----------------------------------------------------------------------------------------------------
# Script that scrapes song lyrics from azlyrics using a cycling proxy
#
# Brandon Chan, 2018
#
# Specify a list of artists in the artistlist variable. Running script will 
# print various progress messages to console and ultimately save the lyrics as a .csv
#----------------------------------------------------------------------------------------------------
# Load in required packages
import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import random
import re
import urllib3
from lxml.html import fromstring
from itertools import cycle

user_agents = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0' ]
# Get list of proxies
'''
# Attempts to use TOR 
session = requests.session()
session.proxies = {}
session.proxies['https']='socks5h://localhost:9050'
session.proxies['http']='socks5h://localhost:9050'
'''

# Get a list of proxies from free-proxy-list.net
def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

# Function to check if proxy is good 
def check_proxy(proxy):
    sleep(random.randint(2,10))
    r = requests.get('http://www.azlyrics.com/',headers = {'User-Agent': random.choice(user_agents)} ,proxies={'http': proxy, 'https': proxy})
    print(r.status_code)
    if (r.status_code == 200):
        return True
    else:
        return False

print('prepping for scrape...')	
print('getting proxies...')
proxies = get_proxies()
proxy_pool = cycle(proxies)
print('proxies:',proxies)
print('')

print('initializing dataframe...')
columns = ['Artist','SongName','Lyrics']
songdata = pd.DataFrame(columns=columns)
print('')

artistlist = ['masonramsey','urban','degraw','carrieunderwood','dierksbentley',
              'ericchurch','zacbrownband','bandperry','samhunt','twain',
              'mcgraw','brooks','jasonaldean','paisley','thomasrhett',
              'keith','floridageorgialine','hunterhayes']

# Initialize counters
i = 0
proxycount = 0

# Initialize base URL
# URL format 
# https://www.azlyrics.com/f/floridageorgialine.html
# http://www.azlyrics.com/[artistnamefirstletter]/[artist].html
base = 'http://www.azlyrics.com'

print('starting scrape...')

for artist in artistlist:
	# Take next proxy from the pool
    proxy = next(proxy_pool)
    if (check_proxy(proxy) == False): # If proxy does not work, cycle until a valid one is found
        while (check_proxy(proxy) == False):
            proxy = next(proxy_pool)
            proxycount = proxycount + 1
            if (proxycount > 5): # If 5 proxies in a row fail, fetch a new list of proxies
                proxycount = 0
                print("getting new proxies...")
                proxies = get_proxies()
                proxy_pool = cycle(proxies)
   
    url = base + '/' + artist[0] + '/' + artist + '.html'
    response = session.get(url),headers = {'User-Agent': random.choice(user_agents)},proxies = {'http': proxy})
    soup = BeautifulSoup(response.content,'lxml')
    print('Artist Found...',artist)

    for song in soup.findAll(target='_blank'):
		# Cycle a new proxy for every song
        proxy = next(proxy_pool)
        if (check_proxy(proxy) == False):
            while (check_proxy(proxy) == False):
                proxy = next(proxy_pool)
                proxycount = proxycount + 1
                if (proxycount > 5):
                    proxycount = 0
                    print("getting new proxies...")
                    proxies = get_proxies()
                    proxy_pool = cycle(proxies)
       
        print(song.get_text())
        songlink = base + str(song['href'][2:])
        song_response = session.get(songlink) #headers = {'User-Agent': random.choice(user_agents)},proxies = {'http': proxy})
        song_soup = BeautifulSoup(song_response.text,'html.parser')

        sleep(random.randint(5,20)) # Force random delay between calls

		# Clean lyrics and store in dataframe
        for lyrics in song_soup.find_all("div", {"class":""}):
            lyric = re.sub('[(<.!,;?>/\-)]', " ",  str(lyrics.text)).split()
            if lyric:
                songdata.loc[i] = [artist, song.get_text(), " ".join(lyric)]
                i = i + 1
            #songdata[str(song.get_text())] = lyric

# Save dataframe as csv
songdata.to_csv('songs_country.csv')