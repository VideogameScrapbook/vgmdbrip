from sys import argv
import os
import json
import hashlib
import getpass
import pickle
import requests
from bs4 import BeautifulSoup

from pathlib import Path
import re
import sys

scriptdir = os.sep.join(argv[0].split("\\")[:-1])
config = os.path.join(scriptdir, 'vgmdbrip.pkl')
session = requests.Session()

def Soup(data):
  return BeautifulSoup(data, "html.parser")


def login():
    global session
    if os.path.isfile(config):
        session = pickle.load(open(config, "rb"))
    else:
        while True:
            username = input('VGMdb username:\t')
            password = getpass.getpass('VGMdb password:\t')
            base_url = 'https://vgmdb.net/forums/'
            x = session.post(base_url + 'login.php?do=login', {
            'vb_login_username':        username,
            'vb_login_password':        password,
            'vb_login_md5password':     hashlib.md5(password.encode()).hexdigest(),
            'vb_login_md5password_utf': hashlib.md5(password.encode()).hexdigest(),
            'cookieuser': 1,
            'do': 'login',
            's': '',
            'securitytoken': 'guest'
            })
            table = Soup(x.content).find('table', class_='tborder', width="70%")
            panel = table.find('div', class_='panel')
            message = panel.text.strip()
            print(message)

            if message.startswith('You'):
                if message[223] == '5':
                    raise SystemExit(1)
                print(message)
                continue
            elif message.startswith('Wrong'):
                raise SystemExit(1)
            else:
                break


def remove(instring, chars):
    for i in range(len(chars)):
        instring = instring.replace(chars[i],"")
    return instring


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

# Commenting this out to allow prompt approach.
#if(len(argv) < 2):
#    print("usage: " + argv[0] + " vgmdb_album_id")
#    raise SystemExit(1)

login()
soup = ""

def downloadVGMDBArt(query):
    # If query is to a file or folder that exists:
    if os.path.exists(query):
        if os.path.isfile(query):
            os.chdir(os.path.dirname(query))  # Change to the folder path
            # Get the folder name.
            query = os.path.basename(os.path.dirname(query))
        else:
            os.chdir(query)
             # Get the folder name.
            query = os.path.basename(query)
        # If the folder name contains spaces:
        if " " in query:
            # Remove hyphens so that terms aren't excluded.
            query = query.replace("-", "")
        
    while True:
        #print('Query: ' + query)
        query = query.replace("https://vgmdb.net/album/", "")
        if(query.isdigit()):
            soup = Soup(session.get("https://vgmdb.net/album/" + query).content)
            break
        
        soup = Soup(session.get("https://vgmdb.net/search?q=" + query).content)
        if(soup.title.text[:6] != "Search"):
            break
        else:
            soupText = soup.prettify()
            #print(soupText)
            
            # Get all matches and split them into separate lines
            #import re
            matches = re.findall('href="http://vgmdb.net/album/\d+"\s+title="([^"]+)"', soupText)
            ids = re.findall('href="http://vgmdb.net/album/(\d+)"\s+title="[^"]+"', soupText)
            if len(matches) > 0:
                print("Here are the search results:")
                for idx, match in enumerate(matches, start=1):
                    print(f"{idx}. {match}")
                while True:
                    query = input("Enter the number of the match you want or a different query: ")
                    
                    if(not query.isdigit()):
                        print(f"Input is not an integer. Using new query: {query}")
                        break
                    else:
                        matchIndex = int(query)
                        
                        # Adjust for 0-based indexing.
                        matchIndex -= 1
                        
                        if 0 <= matchIndex < len(matches):
                            query = ids[matchIndex]
                            break
                        else:
                            print("Invalid number. Please enter a valid match number.")
                            continue                        
            else:
                query = input("Enter a different query: ")
                continue            
    
    #print('Title: ' + soup.title.text)
    folder = "Scans (VGMdb)"
    gallery = soup.find("div", attrs={"class" : "covertab", "id" : "cover_gallery"})
    for idx, scan in enumerate(gallery.find_all("a", attrs={"class": "highslide"}), start=1):
      url = scan["href"]
      title = remove(scan.text.strip(), "\"*/:<>?\|")
      image = session.get(url).content
      ensure_dir(folder + os.sep)
      orderNumber = str(idx).zfill(2)
      #from pathlib import Path
      sourceFilename = Path(url).stem
      filename = orderNumber + ' ' + title + ' [' + sourceFilename + ']' + url[-4:]
      with open(os.path.join(folder, filename), "wb") as f:
          f.write(image)

      print(title + " downloaded")
    pickle.dump(session, open(config, "wb"))

#import sys
if len(sys.argv) == 1:
    downloadVGMDBArt(input("Enter the VGMdb URL ID or search query for which you want to download album art: "))
else:
    for arg in sys.argv[1:]:
        downloadVGMDBArt(f"{arg}")