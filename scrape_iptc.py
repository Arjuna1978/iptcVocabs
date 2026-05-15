import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# --- CONFIGURATION ---
BASE_URL = "https://cv.iptc.org/newscodes/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
SCHEMES_FILE = "schemes.txt"
DOWNLOAD_DIR = "iptc_vocabularies"

def phase_1_discovery():
    """Finds all 'qcode' cells and matches them to the scheme names."""
    print(f"Phase 1: Discovering schemes via 'qcode' elements...")
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    qcode_cells = soup.find_all('td', class_='qcode')
    
    schemes = []
    for cell in qcode_cells:
        # Extract the URI link
        link_tag = cell.find('a', href=True)
        if not link_tag:
            continue
            
        full_url = link_tag['href']
        
        # Navigate to the row ABOVE this one to get the Name(en-GB)
        parent_row = cell.find_parent('tr')
        prev_row = parent_row.find_previous_sibling('tr')
        
        if prev_row:
            name_cell = prev_row.find('td')
            # The name is often inside a link or nested span, get_text(strip=True) handles both
            name_en = name_cell.get_text(strip=True) if name_cell else "Unknown"
        else:
            name_en = "Unknown"

        # Verify it's a newscodes URI
        if "cv.iptc.org/newscodes/" in full_url:
            schemes.append(f"{name_en}|{full_url}")

    with open(SCHEMES_FILE, "w", encoding="utf-8") as f:
        for item in schemes:
            f.write(f"{item}\n")
            
    print(f"Phase 1 Complete. Found {len(schemes)} valid schemes.")
def phase_2_download():
    """Iterates through schemes.txt and downloads the RDF/Turtle files."""
    if not os.path.exists(SCHEMES_FILE):
        print("Run Phase 1 first.")
        return

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if '|' in line]

    print(f"Phase 2: Processing {len(lines)} downloads...")

    for line in lines:
        # We still have the URL from Phase 1
        _, url = line.split('|')
        
        try:
            time.sleep(0.2) 
            res = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # --- NEW NAME EXTRACTION LOGIC ---
            # Look for <span class="infotext1"> which contains the Name(en-GB)
            name_span = soup.find('span', class_='infotext1')
            if name_span:
                final_name = name_span.get_text(strip=True)
            else:
                # Fallback to the URL slug if the span isn't found
                final_name = url.strip('/').split('/')[-1]
            
            # Target the specific 'RDF/Turtle' link
            turtle_link = None
            for a in soup.find_all('a', href=True):
                if "RDF/Turtle" in a.get_text():
                    turtle_link = a
                    break
            
            if turtle_link:
                dl_url = urljoin(url, turtle_link['href'])
                
                # Sanitize filename
                clean_name = final_name.replace("/", "-").replace("\\", "-").replace(":", "")
                safe_name = "".join([c for c in clean_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                filename = f"{safe_name}.ttl"
                
                print(f"  -> Downloading: {filename}")
                file_data = requests.get(dl_url, headers=HEADERS)
                with open(os.path.join(DOWNLOAD_DIR, filename), 'wb') as f:
                    f.write(file_data.content)
            else:
                print(f"  [!] No Turtle link for: {final_name}")
                
        except Exception as e:
            print(f"  [!] Failed to process {url}: {e}")

    """Iterates through schemes.txt and downloads the RDF/Turtle files."""
    if not os.path.exists(SCHEMES_FILE):
        print("Run Phase 1 first.")
        return

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if '|' in line]

    print(f"Phase 2: Processing {len(lines)} downloads...")

    for line in lines:
        name, url = line.split('|')
        
        try:
            time.sleep(0.2) # Avoid being flagged as a bot
            res = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Target the specific 'RDF/Turtle' link
            turtle_link = None
            for a in soup.find_all('a', href=True):
                if "RDF/Turtle" in a.get_text():
                    turtle_link = a
                    break
            
            if turtle_link:
                dl_url = urljoin(url, turtle_link['href'])
                
                # Sanitize filename for Linux/Windows
                clean_name = name.replace("/", "-").replace("\\", "-").replace(":", "")
                safe_name = "".join([c for c in clean_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                filename = f"{safe_name}.ttl"
                
                print(f"  -> Downloading: {filename}")
                file_data = requests.get(dl_url, headers=HEADERS)
                with open(os.path.join(DOWNLOAD_DIR, filename), 'wb') as f:
                    f.write(file_data.content)
            else:
                print(f"  [!] No Turtle link for: {name}")
                
        except Exception as e:
            print(f"  [!] Failed {name}: {e}")

if __name__ == "__main__":
    phase_1_discovery()
    phase_2_download()
    print("\nAll tasks finished.")