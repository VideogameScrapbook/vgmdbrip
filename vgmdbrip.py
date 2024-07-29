from sys import argv
import os
import json
import hashlib
import getpass
import pickle
import requests
from bs4 import BeautifulSoup

# Set these variables to your designed preferences:
add_info_to_output_folder_name = True
add_order_number_to_filename = True
add_source_to_filename = True
allow_approximation_of_invalid_characters = True
allow_input_folder_detection = True
allow_no_arguments = True
allow_search_terms = True
create_folder_image = True
default_download_to_script_directory = True
process_each_argument_separately = True
show_initial_query = True
output_tab_padding = 4

if allow_search_terms:
    import re

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

def print_aligned_columns(arr):
    global output_tab_padding
    
    # Split each row by tabs and transpose the matrix.
    columns = zip(*[row.split('\t') for row in arr])
    
    # Calculate the maximum width for each column.
    max_widths = [max(len(cell) + output_tab_padding - 1 for cell in col) for col in columns]
    
    # Print each row with aligned columns.
    for row in arr:
        cells = row.split('\t')
        formatted_row = ' '.join(f"{cell:{width}}" for cell, width in zip(cells, max_widths))
        print(formatted_row)

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
if default_download_to_script_directory:
    os.chdir(scriptdir)

def download_vgmdb_art(query):
    ids = []
    choice_index = 0
    
    # If allow_input_folder_detection is enabled and query is to a file or folder that exists:
    if allow_input_folder_detection and os.path.exists(query):
        if os.path.isfile(query):
            # Change to the folder path.
            os.chdir(os.path.dirname(query))
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
    
    if show_initial_query:
        print('Query: ' + query)
    
    while True:
        #print('Query: ' + query)
        query = query.replace("https://vgmdb.net/album/", "")
        if(query.isdigit()):
            soup = Soup(session.get("https://vgmdb.net/album/" + query).content)
            break
        
        if allow_search_terms:
            soup = Soup(session.get("https://vgmdb.net/search?q=" + query).content)
        else:
            soup = Soup(session.get("https://vgmdb.net/search?q=\"" + query + "\"").content)
            
        if(soup.title.text[:6] != "Search"):
            break
        else:
            if not allow_search_terms:
                print("stuck at search results")
                exit(1)
            
            soupHTML = str(soup)
            #print(soupHTML)
            
            # Get all matches and split them into separate lines
            #import re
            ids = re.findall('href="http://vgmdb.net/album/(\d+)"\s+title="[^"]+"', soupHTML)
            catalogs = re.findall('span class="catalog[^"]*">([^<]+)</span>', soupHTML)
            album_titles = re.findall('href="http://vgmdb.net/album/\d+"\s+title="([^"]+)"', soupHTML)
            release_dates = re.findall('"View albums released on ([^"]+)', soupHTML)
            release_dates += re.findall('text-align: right[^>]+>(\d\d\d\d)<', soupHTML)
            media_formats = re.findall('text-align: right[^>]+>([^<>\r\n]+[^<>\r\n\d])<', soupHTML)
            
            if len(ids) > 0:
                search_result = ""
                search_results = []
                print("Here are the search results:")
                for idx, match in enumerate(ids):
                    search_result = f"{idx + 1}."
                    if len(catalogs) == len(ids): search_result += f"\t{catalogs[idx]}"
                    if len(album_titles) == len(ids): search_result += f"\t{album_titles[idx]}"
                    if len(release_dates) == len(ids): search_result += f"\t{release_dates[idx]}"
                    if len(media_formats) == len(ids): search_result += f"\t{media_formats[idx]}"
                    search_results.append(search_result)
                print_aligned_columns(search_results)
                
                while True:
                    query = input("Enter the number of the match you want or a different query: ")
                    
                    if(not query.isdigit()):
                        print(f"Input is not an integer. Using new query: {query}")
                        break
                    else:
                        choice_index = int(query)
                        
                        # Adjust for 0-based indexing.
                        choice_index -= 1
                        
                        if 0 <= choice_index < len(ids):
                            query = ids[choice_index]
                            break
                        else:
                            print("Invalid number. Please enter a valid match number.")
                            continue                        
            else:
                query = input("Enter a different query: ")
                continue            
    
    print('Title: ' + soup.title.text)
    folder = "Scans (VGMdb)"
    if add_info_to_output_folder_name and len(ids) > 0:
        if len(media_formats) == len(ids): folder += f" ({media_formats[choice_index]})"
        if len(catalogs) == len(ids) and catalogs[choice_index] != "N/A": folder += f" [{catalogs[choice_index]}]"
        folder = get_valid_windows_name(folder, allow_approximation_of_invalid_characters)
    gallery = soup.find("div", attrs={"class" : "covertab", "id" : "cover_gallery"})
    for idx, scan in enumerate(gallery.find_all("a", attrs={"class": "highslide"}), start=1):
        url = scan["href"]
        title = get_valid_windows_name(scan.text, allow_approximation_of_invalid_characters)
        image = session.get(url).content
        ensure_dir(folder + os.sep)
        order_number = str(idx).zfill(2)
        source_filename = os.path.splitext(os.path.basename(url))[0]
        filename = ""
        if add_order_number_to_filename: filename += f"{order_number} "
        filename += title
        if add_source_to_filename: filename += f" [{source_filename}]"
        filename += url[-4:]        
        if idx == 1 and create_folder_image:
            # Use .jpg regardless of file extension as cheat to ensure Windows shows it as folder thumbnail.
            folder_image_filename = "folder.jpg"
            # Use this instead if you want to use proper filename.
            #folder_image_filename = f"folder{url[-4:]}"
            if not os.path.exists(folder_image_filename):
                with open(folder_image_filename, "wb") as f:
                    f.write(image)
                print(folder_image_filename + " downloaded")
        with open(os.path.join(folder, filename), "wb") as f:
            f.write(image)
        print(title + " downloaded")
        
        
    pickle.dump(session, open(config, "wb"))

def get_valid_windows_name(filename, approximation):
    """
    Replaces forbidden characters in filename.
    Args:
        filename (str): The input text to process.
        approximation (bool): Whether to replace illegal characters using unusual characters that approximate them.
    Returns:
        str: The processed text with forbidden characters replaced.
    """
    
    # Strip leading and trailing whitespace from the filename.
    filename = filename.strip()
    
    if not approximation:
        filename = remove(filename, "\"*/:<>?\|")
    else:        
        # Define a dictionary of filename bad characters and their replacements.
        replacements = {
            '"': '“',
            '>': '＞',
            '<': '＜',
            '?': '？',
            ':': '：',
            '*': '✱',
            '|': '│',
            '\\': '＼',
            '/': '／'
        }
        
        # Replace all bad characters with their equivalent replacements.
        for char in replacements:
            filename = filename.replace(char, replacements[char])
    
    return filename

if len(argv) < 2:
    if allow_no_arguments:
        download_vgmdb_art(input("Enter the VGMdb URL ID or search query for which you want to download album art: "))
    else:
        print("usage: " + argv[0] + " vgmdb_album_id")
        raise SystemExit(1)
else:
    if process_each_argument_separately:
        for arg in argv[1:]:
            download_vgmdb_art(f"{arg}")
    else:
        download_vgmdb_art(" ".join(argv[1:]))