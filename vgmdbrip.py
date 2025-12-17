from sys import argv
import os
import json
import hashlib
import getpass
import pickle
import requests
import winshell
import ntpath
from win32com.client import Dispatch
from bs4 import BeautifulSoup

# Set these variables to your designed preferences:
add_info_to_output_folder_name = True
add_order_number_to_filename = True
add_source_to_filename = True
allow_approximation_of_invalid_characters = True
allow_input_folder_detection = True
allow_no_arguments = True
allow_search_terms = True
artist_image_filename = "Artist"
back_image_filename = "Back"
create_folder_image = True
create_foobar2000_images = True
default_download_to_script_directory = True
disc_image_filename = "Disc"
front_image_filename = "Folder"
pause_at_end = False
process_each_argument_separately = True
show_initial_query = True
output_tab_padding = 4
use_relative_shortcuts = False

first_image_saved = {
    "Front": False,
    "Back": False,
    "Artist": False,
    "Disc": {}
}

import re

scriptdir = os.path.dirname(argv[0])
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
        source_filename_with_extension = os.path.splitext(os.path.basename(url))[0]
        filename = ""
        if add_order_number_to_filename:
            filename += f"{order_number} "
        filename += title
        if add_source_to_filename:
            filename += f" [{source_filename_with_extension}]"
        filename += url[-4:]

        if create_foobar2000_images:
            if idx == 1:
                # Use .jpg regardless of file extension as a cheat to ensure Windows shows it as the folder thumbnail.
                front_image_filename_with_extension = f"{front_image_filename}.jpg"
                front_shortcut = f"{filename} - Shortcut.lnk"
                if not os.path.exists(os.path.join(folder, front_shortcut)) and not os.path.exists(front_image_filename_with_extension):
                    with open(front_image_filename_with_extension, "wb") as f:
                        f.write(image)
                    # Create shortcut in Scans folder with the scans filename
                    if not os.path.exists(os.path.join(folder, front_shortcut)):
                        create_shortcut(front_image_filename_with_extension, folder, shortcut_name_override=front_shortcut)
                    print(front_image_filename_with_extension + " downloaded")
                    first_image_saved["Front"] = True
                elif not os.path.exists(os.path.join(folder, front_shortcut)) and not os.path.exists(os.path.join(folder, filename)):
                    with open(os.path.join(folder, filename), "wb") as f:
                        f.write(image)
                    print(title + " downloaded.")
            elif "Back" in filename and not first_image_saved["Back"]:
                back_path = f"{back_image_filename}.jpg"
                back_shortcut = f"{filename} - Shortcut.lnk"
                if not os.path.exists(os.path.join(folder, back_shortcut)) and not os.path.exists(back_path):
                    download_image(url, back_path)
                    # Create shortcut in Scans folder with the scans filename
                    if not os.path.exists(os.path.join(folder, back_shortcut)):
                        create_shortcut(back_path, folder, shortcut_name_override=back_shortcut)
                    first_image_saved["Back"] = True
                elif not os.path.exists(os.path.join(folder, back_shortcut)) and not os.path.exists(os.path.join(folder, filename)):
                    with open(os.path.join(folder, filename), "wb") as f:
                        f.write(image)
                    print(title + " downloaded.")
            elif "Artist" in filename and not first_image_saved["Artist"]:
                artist_path = f"{artist_image_filename}.jpg"
                artist_shortcut = f"{filename} - Shortcut.lnk"
                if not os.path.exists(os.path.join(folder, artist_shortcut)) and not os.path.exists(artist_path):
                    download_image(url, artist_path)
                    # Create shortcut in Scans folder with the scans filename
                    if not os.path.exists(os.path.join(folder, artist_shortcut)):
                        create_shortcut(artist_path, folder, shortcut_name_override=artist_shortcut)
                    first_image_saved["Artist"] = True
                elif not os.path.exists(os.path.join(folder, artist_shortcut)) and not os.path.exists(os.path.join(folder, filename)):
                    with open(os.path.join(folder, filename), "wb") as f:
                        f.write(image)
                    print(title + " downloaded.")
            elif re.search(r"Disc(\s+\d+)?", filename.split(' - ')[0].strip()):
                # Extract disc number if present, otherwise use empty string
                disc_match = re.search(r"Disc(?:\s+(\d+))?", filename.split(' - ')[0].strip())
                disc_num = disc_match.group(1) if disc_match and disc_match.group(1) else ""
                # Save disc image in root folder
                if disc_num:
                    # For numbered discs, use full filename
                    disc_filename = filename
                else:
                    # For standalone "Disc", use "Disc.jpg"
                    disc_filename = f"{disc_image_filename}.jpg"
                shortcut_filename = f"{filename} - Shortcut.lnk"
                disc_key = filename  # Use filename as unique key
                if disc_key not in first_image_saved["Disc"] and not os.path.exists(os.path.join(folder, shortcut_filename)) and not os.path.exists(disc_filename):
                    with open(disc_filename, "wb") as f:
                        f.write(image)
                    if not os.path.exists(os.path.join(folder, shortcut_filename)):
                        create_shortcut(disc_filename, folder, shortcut_name_override=shortcut_filename)
                    print(f"{disc_filename} downloaded and shortcut created.")
                    first_image_saved["Disc"][disc_key] = True
                elif not os.path.exists(os.path.join(folder, shortcut_filename)) and not os.path.exists(os.path.join(folder, filename)):
                    with open(os.path.join(folder, filename), "wb") as f:
                        f.write(image)
                    print(title + " downloaded.")
            else:
                if not os.path.exists(os.path.join(folder, filename)):
                    with open(os.path.join(folder, filename), "wb") as f:
                        f.write(image)
                    print(title + " downloaded.")
        else:
            if not os.path.exists(os.path.join(folder, filename)):
                with open(os.path.join(folder, filename), "wb") as f:
                    f.write(image)
                print(title + " downloaded.")
        
        
    pickle.dump(session, open(config, "wb"))


def create_shortcut(shortcut_target, shortcut_path="", shortcut_windows_style=True, shortcut_name_override=None):
    """
    Create a shortcut to the target file/folder (relative or absolute based on config).
    """
    global use_relative_shortcuts

    # Determine shortcut name
    if shortcut_name_override:
        shortcut_name = shortcut_name_override
    else:
        shortcut_name = get_name_with_extension(shortcut_target)
        if get_file_extension(shortcut_name) != '.lnk':
            if shortcut_windows_style:
                shortcut_name = f"{shortcut_name} - Shortcut"
            shortcut_name = f"{shortcut_name}.lnk"

    # Determine shortcut filepath - place in the specified path
    shortcut_filepath = os.path.join(shortcut_path, shortcut_name)

    # Get absolute path of target
    target_abs = os.path.abspath(shortcut_target)

    # Create the shortcut
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortcut(shortcut_filepath)

    if use_relative_shortcuts:
        # Use relative method
        shortcut_dir = os.path.dirname(shortcut_filepath)
        try:
            relative_path = os.path.relpath(target_abs, shortcut_dir)
        except ValueError:
            print(f"Cannot create relative path for {shortcut_target}")
            return

        shortcut.TargetPath = r'%windir%\explorer.exe'
        shortcut.Arguments = f'"{relative_path}"'
        shortcut.WorkingDirectory = ''
        shortcut_type = "Relative"
    else:
        # Use absolute method
        shortcut.TargetPath = target_abs
        shortcut.Arguments = ''
        shortcut.WorkingDirectory = os.path.dirname(target_abs)
        shortcut_type = "Absolute"

    # Set icon to the target file
    shortcut.IconLocation = f'{target_abs},0'

    shortcut.Save()

    print(f"{shortcut_type} shortcut created: {shortcut_filepath}")

def download_image(url, save_path = ""):
    # If save_path is to a folder or save_path doesn't have an extension, set filepath based on URL.
    if os.path.isdir(save_path) or not has_file_extension(save_path):
        file_name_with_extension = get_name_with_extension(url)
        save_path = os.path.join(save_path, file_name_with_extension)

    if not os.path.exists(save_path):
        image = session.get(url).content

        with open(save_path, "wb") as f:
            f.write(image)

        print(f"{os.path.basename(save_path)} downloaded.")
    else:
        print(f"{os.path.basename(save_path)} already exists, skipping download.")

# Return just the file extension of the given path (including the dot).
def get_file_extension(path):
    # If path is to a folder that exists, return an empty string.
    if os.path.isdir(path):
        return ''
    else:
        return os.path.splitext(path)[1]

# Return just the file or folder name of the given path.
def get_name_with_extension(path):
	return ntpath.basename(path)

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

def has_file_extension(path):
    _, extension = os.path.splitext(path)
    return bool(extension)

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

if pause_at_end:
    input("Press Enter to exit...")
