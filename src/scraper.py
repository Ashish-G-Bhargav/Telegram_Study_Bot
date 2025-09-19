from bs4 import BeautifulSoup
import requests
import json
import os

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def make_download_link(link):
    if not link:
        return False
    
    link_elems = link.split("/")
    if "d" in link_elems:
        uid_index = link_elems.index("d") + 1

        if uid_index < len(link_elems):
            file_id = link_elems[uid_index]
            return f"https://drive.google.com/uc?export=download&id={file_id}"

def download_pdf(link, file_path):
    d_link = make_download_link(link)

    if not d_link:
        return False
    
    try:
        with requests.get(d_link, stream=True, headers=header) as response:
            response.raise_for_status()

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {e}")

def download(lst, sub_code):
    os.makedirs(f"notes/{sub_code}", exist_ok=True)
    for i in lst:
        name = lst.index(i)
        download_pdf(i, f"notes/{sub_code}/{name}.pdf")

def load_sources(src):
    try:
        with open(src, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

sources = load_sources("data/sources.json")
notes_link = load_sources("data/notes_link.json")

def save_sources(sources_dict, src):
    with open(src, "w") as f:
        json.dump(sources_dict, f, indent=4)

def get_source(branch, sub_code):
    obreak = False
    if sub_code in sources:
        return sources[sub_code]
    
    try: 
        link = f"https://saividya.ac.in/study-material-{branch}.html"

        web_page = requests.get(link, headers=header).text
        scrape = BeautifulSoup(web_page, "lxml")
        tables = scrape.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                tds = row.find_all("td")
                
                if len(tds) > 1:
                    if sub_code in tds[0].text.strip():
                        sub_source = tds[1].u.a["href"]
                        sources[sub_code] = sub_source
                        obreak = True
                        break

            if obreak:
                break
        if obreak:
            return sub_source
        else:
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not fetch the webpage. Details: {e}")

def get_notes(branch, sub_code):
    source = get_source(branch, sub_code)

    if not source:
        return False
    
    if sub_code in notes_link:
        return notes_link[sub_code]
    
    try:
        lst = []
        web_page = requests.get(source, headers=header).text
        scrape = BeautifulSoup(web_page, "lxml")
        iframes = scrape.find_all("iframe")

        for iframe in iframes:
            lst.append(iframe["src"])

        lst.pop()
        notes_link[sub_code] = lst
        download(notes_link[sub_code], sub_code)

        return lst
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not fetch the webpage. Details: {e}")

save_sources(sources, "data/sources.json")
save_sources(notes_link, "data/notes_link.json")