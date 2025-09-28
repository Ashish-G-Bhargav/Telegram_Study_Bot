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
    return False

def download_pdf(link, file_path):
    d_link = make_download_link(link)
    
    if not d_link:
        print(f"Failed to create download link for: {link}")
        return False
    
    try:
        print(f"Downloading: {file_path}")
        with requests.get(d_link, stream=True, headers=header) as response:
            response.raise_for_status()
            
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded successfully: {file_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {e}")
        return False

def download(lst, sub_code):
    os.makedirs(f"notes/{sub_code}", exist_ok=True)
    downloaded_count = 0
    
    for i in lst:
        if len(i) >= 2:  
            name = i[1]  
            link = i[0]  
            
            
            clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            
            if download_pdf(link, f"notes/{sub_code}/{clean_name}.pdf"):
                downloaded_count += 1
    
    print(f"Downloaded {downloaded_count} files for {sub_code}")
    return downloaded_count > 0

def load_sources(src):
    try:
        with open(src, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_sources(sources_dict, src):
    try:
        with open(src, "w") as f:
            json.dump(sources_dict, f, indent=4)
        print(f"Saved {src} successfully")
    except Exception as e:
        print(f"Error saving {src}: {e}")


sources = load_sources("sources.json")
notes_link = load_sources("notes_link.json")
sub_name = load_sources("sub_name.json")

def get_source(branch, sub_code):
    global sources, sub_name  
    
    
    if sub_code in sources:
        print(f"Found existing source for {sub_code}")
        return sources[sub_code]
    
    try: 
        link = f"https://saividya.ac.in/study-material-{branch}.html"
        print(f"Fetching source page: {link}")
        
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
                        subject_name = tds[1].u.a.text.strip()
                        
                        
                        sources[sub_code] = sub_source
                        sub_name[sub_code] = subject_name

                        pass
                        save_sources(sources, "sources.json")
                        save_sources(sub_name, "sub_name.json")
                        
                        print(f"Found and saved source for {sub_code}: {subject_name}")
                        return sub_source
        
        print(f"Subject {sub_code} not found in {branch}")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not fetch the webpage. Details: {e}")
        return False

def get_notes(branch, sub_code):
    global notes_link  
    
    print(f"Getting notes for {sub_code} in {branch}")
    
    
    source = get_source(branch, sub_code)
    
    if not source:
        print(f"No source found for {sub_code}")
        return False
    
    
    if sub_code in notes_link:
        print(f"Found existing notes for {sub_code}")
        return notes_link[sub_code]
    
    try:
        print(f"Scraping notes from: {source}")
        lst = []
        web_page = requests.get(source, headers=header).text
        scrape = BeautifulSoup(web_page, "lxml")
        
        iframes = scrape.find_all("iframe")
        if iframes:
            iframes.pop()  
        
        doc_names = scrape.find_all("h3", class_="post-title entry-title")
        
        print(f"Found {len(iframes)} iframes and {len(doc_names)} document names")
        
        for iframe, doc in zip(iframes, doc_names):
            iframe_src = iframe.get("src", "")
            doc_text = doc.text.strip()
            
            
            note_item = [iframe_src, doc_text]
            lst.append(note_item)
            print(f"Added: {doc_text} -> {iframe_src}")
        
        if lst:
            
            notes_link[sub_code] = lst
            
            
            save_sources(notes_link, "notes_link.json")
            
            print(f"Found {len(lst)} notes for {sub_code}")
            
            
            download_success = download(lst, sub_code)
            
            if download_success:
                print(f"Successfully processed notes for {sub_code}")
            else:
                print(f"Warning: Some downloads failed for {sub_code}")
            
            return lst
        else:
            print(f"No notes found for {sub_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not fetch the webpage. Details: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def save_all_sources():
    save_sources(sources, "sources.json")
    save_sources(notes_link, "notes_link.json")
    save_sources(sub_name, "sub_name.json")


def test_scraper():
    print("Testing scraper...")
    result = get_notes("cseds", "BCD5I5C")  
    print(f"Test result: {result}")
    save_all_sources()

if __name__ == "__main__":
    
    #save_all_sources()
    pass
    #test_scraper()















