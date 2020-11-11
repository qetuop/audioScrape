import logging
from bs4 import BeautifulSoup
import requests
import urllib.request
import urllib.parse
import os
import time
import eyed3
import json
import sys
from pathvalidate import sanitize_filename
import re

DOWNLOAD_DIR = ''

# given top level site, get all page urls
def grabSite(url):
    urls = []
    page = None

    try:
        page = requests.get(url)
    except:
        logging.ERROR('Could not Parse: {}'.format(url))
        return urls

    soup = BeautifulSoup(page.content, 'html.parser')

    # get all pages for site, grab largest number
    results = soup.find_all("a", {"class": "page-numbers"})
    maxPage = int(1)
    if (len(results) != 0):
        for elem in results:
            href = elem.get_text()
            try:
                maxPage = max(maxPage, int(elem.get_text()))
            except:
                # some other element that is not a page number, don't worry about
                pass
    print('maxPage:',maxPage)

    # iterate over all site pages grabing each book within the page
    currPage = 1
    for currPage in range(1, maxPage+1):
        currUrl = url + 'page/' + str(currPage)
        print(currUrl)
        try:
            page = requests.get(currUrl)
            soup = BeautifulSoup(page.content, 'html.parser')
            results = soup.find_all("h2", {"class": "entry-title"})
            if (len(results) != 0):
                for elem in results:
                    urls.append(elem.a.get('href'))
        except:
            logging.ERROR('Could not Parse: {}'.format(url))

    return urls




# get url list from text file
def grabUrls():
    with open("urls.txt") as file:  # Use file to refer to the file object
        data = [line.strip() for line in file.readlines() if line.strip()]
        return data


def createSaveDir(URL):
    global DOWNLOAD_DIR

    config = json.loads(open('config.json').read().replace('\\', '/'))  # can't handle windows path '\' make sure it is "\\" or figure out a replace here
    downloads = config['downloads']
    #print(downloads)

    bookName = URL.split('/')[-2]
    #print(bookName)
    DOWNLOAD_DIR = os.path.join(downloads, bookName)

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    sourceFile = os.path.join(DOWNLOAD_DIR,"audioScrape.txt")
    #print(sourceFile)
    with open(sourceFile, 'w') as file:
        file.write(URL)

# Check if there are multiple pages per book
def grabPages(soup, pagesToScrapeList):
    # <a href="https://bigaudiobooks.net/thud/3/" class="post-page-numbers">3</a>
    results = soup.find_all(class_='post-page-numbers')
    if (len(results) != 0):
        for elem in results:
            href = elem.get('href')
            if (href and (href not in pagesToScrapeList)):
                pagesToScrapeList.append(href)

'''
<audio 
class="wp-audio-shortcode" id="audio-400-1_html5" 
preload="none" style="width: 100%; height: 100%;" 
src="https://ipaudio4.com/wp-content/uploads/BIG/Thud/09.mp3?_=1">
<source type="audio/mpeg" src="https://ipaudio4.com/wp-content/uploads/BIG/Thud/09.mp3?_=1">
<a href="https://ipaudio4.com/wp-content/uploads/BIG/Thud/09.mp3">https://ipaudio4.com/wp-content/uploads/BIG/Thud/09.mp3</a>
</audio>
'''
def grabAudio(URL):
    logging.info('Grabbing:{}'.format(URL))

    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')

    results = soup.find_all(class_='wp-audio-shortcode')
    for elem in results:
        #print(elem)
        href = elem.a['href']
        #print(href)

        # decode escaped strings, remove any leading/trailing ws after conversion
        filename = urllib.parse.unquote(href.split('/')[-1]).strip() #.encode('ascii', errors='ignore').decode("utf-8") #.encode('ascii', errors='ignore')
        #filename = re.sub(r'[^\x00-\x7f]', r'', filename)
        #print(filename)
        localFileName = os.path.join(DOWNLOAD_DIR, filename)
        #print(localFileName)

        # if leading char of filename part of href is a space urlretrieve will fail
        # https://ipaudio5.com/wp-content/uploads//STARR/40k/Fulgrim/%201.mp3
        # if I remove the hex space "%20" it works.  is this expected?
        # use the 'clean' filename from above, put the hexcode back in.
        # urljoin takes evertyhing up to the last parte (the file name) and replaces with
        # the 2nd argument
        href = urllib.parse.urljoin(href,urllib.parse.quote(filename))
        print(href)

        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(href, localFileName)

        #t = eyed3.load(localFileName)
        #print(t.tag.title)

        logging.info('Grabbed: {}'.format(localFileName))

'''
<img src="https://bigaudiobooks.b-cdn.net/wp-content/uploads/2018/11/517UdroKvTL._SX319_BO1,204,203,200_.jpg" 
alt="The Colour Of Magic Audiobook" width="178" height="277">
'''
def grabCover(soup):

    main = soup.find(id='content')
    results = main.find_all('img')

    for elem in results:
        coverImg = elem.get('src')
        coverName = sanitize_filename(elem.get('alt')) + '.jpg'

        localFileName = os.path.join(DOWNLOAD_DIR, coverName)

        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(coverImg, localFileName)


##############
#       MAIN
##############
if __name__ == "__main__":
    logging.basicConfig(filename='app.log', filemode='w', format='%(levelname)s - %(message)s', level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler())

    start_time = time.monotonic()
    logging.info('Start Time: {}'.format(start_time))

    #URL = 'https://bigaudiobooks.net/thud/'  # multiple pages
    #URL = 'https://bigaudiobooks.net/the-colour-of-magic/'   # 1 page

    # grab all books from an entire site
    # TODO: add to a "sites.txt"
    site = 'https://staraudiobook.com/series/40k/'
    urls = grabSite(site)
    print(urls)
    with open('tmp.txt','w') as file:
        for url in urls:
            file.write("%s\n"%url)

    #sys.exit(0)


    # get urls from text file (urls.txt)
    # TODO: add these to the ones from the sites above
    urls = grabUrls()

    print(urls)

    for url in urls:
        logging.info('Parsing: {}'.format(url))

        try:
            page = requests.get(url)
        except:
            logging.ERROR('Could not Parse: {}'.format(url))
            continue

        soup = BeautifulSoup(page.content, 'html.parser')

        pagesToScrapeList = [url]

        # setup save dir
        createSaveDir(url)

        # cover *should* be on first (or only) page
        grabCover(soup)

        # if the media is spread out over multiple pages, get them
        grabPages(soup, pagesToScrapeList)
        #print(pagesToScrapeList)

        # Grab audio files
        for page in pagesToScrapeList:
            grabAudio(page)

        with open('scrapped.txt', 'a') as file:
            file.write('{}\n'.format(url))

    logging.info('Total Time: {} mins'.format( round( ((time.monotonic() - start_time) / 60),2) ) )



