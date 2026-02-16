from curl_cffi import requests # The secret weapon
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import os
import random
import time

# --- CONFIGURATION ---
def get_dates():
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d"), day_after.strftime("%Y-%m-%d")

checkin, checkout = get_dates()

# VERIFIED URLS (Updated for Varanasi)
COMPETITORS = [
    { "name": "Luxuria by Moustache Varanasi", "url": f"https://www.booking.com/hotel/in/luxuria-varanasi-by-moustache.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Quality Inn Varanasi", "url": f"https://www.booking.com/hotel/in/quality-inn-city-centre-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Balaji Palace", "url": f"https://www.booking.com/hotel/in/balaji-palace-varanasi2.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Pearl Courtyard", "url": f"https://www.booking.com/hotel/in/atithi-satkaar.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Veda Heritage", "url": f"https://www.booking.com/hotel/in/veda-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Hardik", "url": f"https://www.booking.com/hotel/in/hardik-palacio.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Dolphin International", "url": f"https://www.booking.com/hotel/in/dolphin-international-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Vedagram (Vedangam)", "url": f"https://www.booking.com/hotel/in/vedangam.html?checkin={checkin}&checkout={checkout}" }
]

DATA_FILE = "prices.json"

def get_inventory(url):
    try:
        # IMPERSONATION: This line makes the robot look 100% like a real Chrome Browser
        response = requests.get(url, impersonate="chrome120", timeout=30)
        
        # DEBUG: Print the page title to see if we are blocked
        soup = BeautifulSoup(response.text, 'html.parser')
        page_title = soup.title.string.strip() if soup.title else "No Title"
        
        if "Just a moment" in page_title or "Access denied" in page_title:
            print(f"   [BLOCKED] Booking.com detected us. Title: {page_title}")
            return {}

        inventory = {}

        # 1. Try Table View
        rows = soup.select("tr.js-hprt-table-row")
        if rows:
            print(f"   [SUCCESS] Found Table with {len(rows)} rows.")
            for row in rows:
                name_elem = row.select_one(".hprt-roomtype-icon-link")
                price_elem = row.select_one(".bui-price-display__value")
                if not price_elem: price_elem = row.select_one(".prco-valign-middle-helper")
                if not price_elem: price_elem = row.select_one("span[data-testid='price-and-discounted-price']")
                
                if name_elem and price_elem:
                    r_name = " ".join(name_elem.text.split())
                    r_price = float(''.join(c for c in price_elem.text if c.isdigit() or c == '.'))
                    if r_name not in inventory: inventory[r_name] = r_price
                    else: 
                        if r_price < inventory[r_name]: inventory[r_name] = r_price

        # 2. Try Card View (Fallback)
        if not inventory:
            cards = soup.select('[data-testid="property-card"]')
            for card in cards:
                title = card.select_one('[data-testid="title"]')
                price_elem = card.select_one('[data-testid="price-and-discounted-price"]')
                if price_elem:
                    p = float(''.join(c for c in price_elem.text if c.isdigit()))
                    name = title.text.strip() if title else "Standard Offer"
                    inventory[name] = p

        return inventory

    except Exception as e:
        print(f"   [ERROR] {e}")
        return {}

def main():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = []
    else:
        history = []

    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = { "date": today_str, "data": {} }
    
    print(f"--- STARTING SCAN (Chrome 120 Mode) ---")
    
    for hotel in COMPETITORS:
        print(f"Scanning: {hotel['name']}...")
        time.sleep(random.uniform(3, 8))
        
        data = get_inventory(hotel['url'])
        if data:
            new_entry["data"][hotel['name']] = data
        else:
            print(f" -> No data found.")
            new_entry["data"][hotel['name']] = {}

    history.append(new_entry)
    if len(history) > 50: history = history[-50:]

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("--- Scan Complete ---")

if __name__ == "__main__":
    main()
