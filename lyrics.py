import requests,bs4,os
from bs4 import BeautifulSoup

## /html/body/div[2]/div[2]/div[2]/div[5]
## html body.az-song-text div.container.main-page div.row div.col-xs-12.col-lg-8.text-center div
def from_az(artist,song):
    artist0=artist.replace('\'','').replace(' ','').lower()
    song0=song.replace('\'','').replace(' ','').lower()
    print(f'{artist0}\n{song0}')
    with requests.get('https://www.azlyrics.com/lyrics/{artist0}/{song0}.html') as req:
        soup =  BeautifulSoup(req.text,'html.parser')
        print(req.text)

    divs = soup.select('html body.az-song-text div.container.main-page div.row div.col-xs-12.col-lg-8.text-center div')
    for d0 in divs:
        if len(d0.attrs) == 0:
            if d0.find('img') == None:
                try:
                    os.remove(f'{song}.txt')
                except:
                    0
                
                fs = open(f'{song}.txt','x',encoding='utf-8')
                fs.writelines(str(d0))
                fs.close()

                fs = open(f'{song}.txt','r',encoding='utf-8')
                ls = fs.read()
                fs.close()
                ls:str

                nls = ls.replace('<br/>','').\
                    replace('<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->','').\
                    replace('</div>','').\
                    replace('<div>','')
                fs = open(f'{song}.txt','w',encoding='utf-8')
                fs.writelines(nls)
                fs.close()


## html body#s4-page-lyric div#page-container div#main.container div.row div#content-main.col-sm-8.col-sm-push-4 div#content-body div.clearfix div.lyric.clearfix pre#lyric-body-text.lyric-body.wselect-cnt
## html body div.flex-wrapper div.flex-panel-main div.main-panel div.main-panel-content

def flashlyrics(artist,song):
    artist0=artist.replace(' ','-')
    song0=song.replace(' ','-')
    print(f'{artist0}/{song0}')

    req = requests.get('https://www.flashlyrics.com/lyrics/car-seat-headrest/fill-in-the-blank-17')
    fs = open('index.html','x')
    fs.write(req.text)
    fs.close()
    with open('index.html','r') as lyric_text:
        soup = BeautifulSoup(lyric_text,'html.parser')
        pre = soup.select('html body div.flex-wrapper div.flex-panel-main div.main-panel div.main-panel-content')
        print(pre)
        # <div class="main-panel-banner">
        print(pre[0].contents )
        for p0 in pre[0].contents:
            try:
                if p0.name != 'div' and p0.string.strip() != '' and p0.string.strip() != '\\n':
                    print(f'{p0.string.replace('<span>','').replace('</span>','')}')
            except:
                pass

def songlyrics():
    # with requests.get('https://www.songlyrics.com/car-seat-headrest/fill-in-the-blank-lyrics/') as req:
        # print(req.text)
        # fs = open('index.html','x')
        # fs.write(req.text)
        # fs.close()
        ## html body div#wrapper div.wrapper-inner.footer-ad div#colone-container.lyrics-inner-col-wrap div.col-one.col-one-leftad div#songLyricsContainer div#songLyricsDiv-outer p#songLyricsDiv.songLyricsV14.iComment-text
    with open('index.html','r') as lyric_text:
        soup = BeautifulSoup(lyric_text,'html.parser')
        pre = soup.select('html body div#wrapper div.wrapper-inner.footer-ad div#colone-container.lyrics-inner-col-wrap div.col-one.col-one-leftad div#songLyricsContainer div#songLyricsDiv-outer p#songLyricsDiv.songLyricsV14.iComment-text')
        print(pre)
        # <div class="main-panel-banner">
        print(  pre[0].contents )
        for p0 in pre[0].contents:
            try:
                if p0.name != 'div' and p0.string.strip() != '' and p0.string.strip() != '\\n':
                    print(f'{p0.string.replace('<span>','').replace('</span>','')}')
            except:
                pass