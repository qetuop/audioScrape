from bs4 import BeautifulSoup
import requests
import urllib.request
import os
import time
import eyed3
import json

DOWNLOAD_DIR = ''

def grabUrls():
    with open("urls.txt") as file:  # Use file to refer to the file object
        data = [line.strip() for line in file.readlines() if line.strip()]
        return data


def createSaveDir(URL):
    global DOWNLOAD_DIR

    config = json.loads(open('config.json').read())
    downloads = config['downloads']

    bookName = URL.split('/')[-2]
    print(bookName)
    DOWNLOAD_DIR = os.path.join(downloads, bookName)

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    sourceFile = os.path.join(DOWNLOAD_DIR,"audioScrape.txt")
    print(sourceFile)
    with open(sourceFile, 'w') as file:
        file.write(URL)

# Check if there are multiple pages
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
    print(URL)
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')

    results = soup.find_all(class_='wp-audio-shortcode')
    for elem in results:
        print(elem)
        href = elem.a['href']
        print(href)

        filename = href.split('/')[-1]
        localFileName = os.path.join(DOWNLOAD_DIR, filename)
        print(localFileName)

        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(href, localFileName)

        t = eyed3.load(localFileName)
        print(t.tag.title)

'''
<img src="https://bigaudiobooks.b-cdn.net/wp-content/uploads/2018/11/517UdroKvTL._SX319_BO1,204,203,200_.jpg" 
alt="The Colour Of Magic Audiobook" width="178" height="277">
'''
def grabCover(soup):
    results = soup.find_all('img')
    for elem in results:
        coverImg = elem.get('src')
        coverName = elem.get('alt')

        if ( 'https://bigaudiobooks.b-cdn.net/wp-content/uploads' in coverImg ):
            coverName = coverName + '.jpg'
            localFileName = os.path.join(DOWNLOAD_DIR, coverName)

            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(coverImg, localFileName)



if __name__ == "__main__":
    start_time = time.monotonic()
    #URL = 'https://bigaudiobooks.net/thud/'  # multiple pages
    #URL = 'https://bigaudiobooks.net/the-colour-of-magic/'   # 1 page

    urls = grabUrls()
    print(urls)

    for url in urls:
        print(url)
        page = requests.get(url)
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
            pass#grabAudio(page)

    print('minutes: ', (time.monotonic() - start_time) / 60)

