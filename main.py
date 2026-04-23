

from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import json
import os
import uuid
from datetime import datetime
from bs4 import BeautifulSoup

l1=[]
l2=[]
  # Lists

name_list = []
address_list = []
address_line_list = []
area_list = []
zip_code_list = []
country_list = []
located_in_list = []
website_list = []
phone_number_list = []
reviews_count_list = []
reviews_average_list = []
in_store_shopping_list = []
in_store_pickup_list = []
store_delivery_list = []
place_type_list = []
opens_at_list = []
about_list = []
orders_links1_list = []
orders_links2_list = []
orders_links3_list = []
facebook_link_list = []
twitter_link_list = []
instagram_link_list = []
tiktok_link_list = []
linkedin_link_list = []
is_ad_list = []



Name = ""
Address = ""
Address_line = ""
Area = ""
Zip_Code = ""
Country = ""
Located_In = ""
Website = ""
Phone_Number = ""
Reviews_Count = 0
Reviews_Average = 0
In_Store_Shopping = ""
In_Store_Pickup = ""
Store_Delivery = ""
Place_Type = ""
Opens_At = ""
About = ""

Orders_Links1 = ""
Orders_Links2 = ""
Orders_Links3 = ""
Facebook_Link = ""
Twitter_Link = ""
Instagram_Link = ""
TikTok_Link = ""
Linkedin_Link = ""

  




def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("1. Opening Google Maps...")
        maps_url = f"https://www.google.com/maps/search/{search_for.replace(' ', '+')}"
        page.goto(maps_url, timeout=60000)
        page.wait_for_timeout(3000)

        print("2. Accepting cookies...")
        try:
            page.locator('button:has-text("Tout accepter"), button:has-text("Accept all")').first.click(timeout=3000)
            page.wait_for_timeout(1000)
        except:
            pass

        print("3. Maps URL:", page.url)
        
        
        

        
        # Scroll the results panel to load enough listings
        LISTING_SEL = 'a.hfpxzc'
        previously_counted = 0
        print("4. Scrolling to load leads...")
        while True:
            current_count = page.locator(LISTING_SEL).count()
            print(f"   Leads found: {current_count}")
            if current_count >= total:
                break
            if current_count == previously_counted:
                print("   No more leads available.")
                break
            previously_counted = current_count
            # Scroll inside the results panel
            panel = page.locator('div[role="feed"]')
            if panel.count() > 0:
                panel.evaluate("el => el.scrollBy(0, 3000)")
            else:
                page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2000)

        listings = page.locator(LISTING_SEL).all()[:total]
        print(f"Total Listings Found: {len(listings)}")

        # Scrape each listing
        for i, listing in enumerate(listings):
            listing.click()
            page.wait_for_timeout(3000)
            print(f"  Scraping {i+1}/{len(listings)}...")

            def get_text(sel):
                el = page.locator(sel)
                return el.first.inner_text().strip() if el.count() > 0 else ""

            def get_href(sel):
                el = page.locator(sel)
                return el.first.get_attribute('href') or "" if el.count() > 0 else ""

            # Name
            Name = get_text('h1.DUwDvf')
            name_list.append(Name)

            listing_text = ""
            listing_aria = ""
            try:
                listing_text = listing.inner_text(timeout=1000) or ""
            except:
                listing_text = ""
            try:
                listing_aria = listing.get_attribute("aria-label") or ""
            except:
                listing_aria = ""
            listing_blob = f"{listing_text}\n{listing_aria}".lower()
            is_ad_list.append(
                any(token in listing_blob for token in ("sponsored", "sponsorisé", "ad", "annonce", "promoted"))
            )

            # Place type
            Place_Type = get_text('button.DkEaL')
            place_type_list.append(Place_Type)

            # Address
            Address = get_text('button[data-item-id="address"] .Io6YTe')
            address_list.append(Address)
            if Address:
                tokens = Address.split(', ')
                if len(tokens) >= 4:
                    Address_line = tokens[0]
                    Area = tokens[1]
                    Zip_Code = tokens[2]
                    Country = tokens[3]
                elif len(tokens) == 3:
                    Address_line = tokens[0]
                    Area = tokens[1]
                    Zip_Code = ""
                    Country = tokens[2]
                else:
                    Address_line = Address
                    Area = Zip_Code = Country = ""
            else:
                Address_line = Area = Zip_Code = Country = ""
            address_line_list.append(Address_line)
            area_list.append(Area)
            zip_code_list.append(Zip_Code)
            country_list.append(Country)

            # Phone
            Phone_Number = get_text('button[data-item-id*="phone"] .Io6YTe')
            phone_number_list.append(Phone_Number or "Not Given")

            # Website
            Website = get_href('a[data-item-id="authority"]')
            website_list.append(Website or "Not Given")

            # Reviews
            rating_el = page.locator('div.F7nice span[aria-hidden="true"]')
            Reviews_Average = rating_el.first.inner_text().strip() if rating_el.count() > 0 else ""
            reviews_average_list.append(Reviews_Average)

            import re
            f7 = page.locator('div.F7nice')
            if f7.count() > 0:
                full = f7.first.inner_text()  # e.g. "4,7\n(3 005)"
                # Extract number inside parentheses
                m = re.search(r'\(([0-9\s\u202f\xa0]+)\)', full)
                Reviews_Count = int(re.sub(r'\D', '', m.group(1))) if m else ""
            else:
                Reviews_Count = ""
            reviews_count_list.append(Reviews_Count)

            # Hours
            hours_el = page.locator('div[aria-label*="ours"] .G8aQO, div.t39EBf')
            Opens_At = hours_el.first.inner_text().strip() if hours_el.count() > 0 else "Not Given"
            opens_at_list.append(Opens_At)

            # Located in
            located_el = page.locator('button[data-item-id*="localityuniversal"] .Io6YTe')
            Located_In = located_el.first.inner_text().strip() if located_el.count() > 0 else "Not Given"
            located_in_list.append(Located_In)

            # Service options
            service_text = get_text('div[jsaction*="pane.optin"] div.iP2t7d, div.LTs0Rc')
            In_Store_Shopping = 'Yes' if 'in-store' in service_text.lower() or 'shop' in service_text.lower() else 'No'
            In_Store_Pickup = 'Yes' if 'pickup' in service_text.lower() or 'pick' in service_text.lower() else 'No'
            Store_Delivery = 'Yes' if 'delivery' in service_text.lower() else 'No'
            in_store_shopping_list.append(In_Store_Shopping)
            in_store_pickup_list.append(In_Store_Pickup)
            store_delivery_list.append(Store_Delivery)

            # About
            about_el = page.locator('div.PYvSYb, div[class*="PYvSYb"]')
            About = about_el.first.inner_text().strip() if about_el.count() > 0 else "Not Given"
            about_list.append(About)

            # Social links (Maps doesn't expose them directly — set empty)
            facebook_link_list.append("Not Given")
            twitter_link_list.append("Not Given")
            instagram_link_list.append("Not Given")
            tiktok_link_list.append("Not Given")
            linkedin_link_list.append("Not Given")
            orders_links1_list.append("Not Given")
            orders_links2_list.append("Not Given")
            orders_links3_list.append("Not Given")

       
        browser.close()
        df = pd.DataFrame(list(zip(name_list, address_list, address_line_list, area_list, zip_code_list, country_list, located_in_list, website_list,phone_number_list,reviews_count_list, reviews_average_list,in_store_shopping_list,in_store_pickup_list,store_delivery_list,place_type_list, opens_at_list,about_list,orders_links1_list,orders_links2_list,orders_links3_list, facebook_link_list, twitter_link_list, instagram_link_list, tiktok_link_list,linkedin_link_list,is_ad_list)),
                           columns =["Name","Address","Address Line","Area","Zip Code", "Country", "Located in", "Website", "Phone Number", "Reviews Count", "Reviews Average","In Store Shopping", "In Store Pickup","Store Delivery","Place Type","Opens at","About","Orders Links1", "Orders Links2", "Orders Links3", "Facebook Link", "Twitter Link", "Instagram Link", "TikTok Link", "Linkedin Link","Is Ad"])
        columns_to_delete = []
        for col in df.columns:
            if df[col].nunique() == 1:
                columns_to_delete.append(col)

        df.drop(columns=columns_to_delete, inplace=True)
        df.to_csv(r'results.csv', index = False)

        # Build JSON records for the prospecting UI
        new_records = []
        for _, row in df.iterrows():
            record = {
                "id": str(uuid.uuid4()),
                "search_query": search_for,
                "scraped_at": datetime.now().isoformat(),
                "status": "to_contact",  # to_contact | contacted | interested | not_interested
                "notes": "",
                "contacted_at": "",
                "is_ad": bool(row.get("Is Ad", False)),
                "name": row.get("Name", ""),
                "address": row.get("Address", ""),
                "address_line": row.get("Address Line", ""),
                "area": row.get("Area", ""),
                "zip_code": row.get("Zip Code", ""),
                "country": row.get("Country", ""),
                "located_in": row.get("Located in", ""),
                "website": row.get("Website", ""),
                "phone": row.get("Phone Number", ""),
                "reviews_count": row.get("Reviews Count", ""),
                "reviews_average": row.get("Reviews Average", ""),
                "place_type": row.get("Place Type", ""),
                "opens_at": row.get("Opens at", ""),
                "about": row.get("About", ""),
                "facebook": row.get("Facebook Link", ""),
                "instagram": row.get("Instagram Link", ""),
                "twitter": row.get("Twitter Link", ""),
                "tiktok": row.get("TikTok Link", ""),
                "linkedin": row.get("Linkedin Link", ""),
            }
            new_records.append(record)

        # Aggregate with existing data (multi-search support)
        db_path = "prospects.json"
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []

        # Avoid duplicates by name+address
        existing_keys = {(r["name"], r["address"]) for r in existing}
        added = 0
        for rec in new_records:
            key = (rec["name"], rec["address"])
            if key not in existing_keys:
                existing.append(rec)
                added += 1

        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        print(f"\n✓ {added} new prospects added to {db_path} ({len(existing)} total)")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()

    if args.search:
        search_for = args.search
    else:
       
        search_for = "subways restaurants in us"

    
    if args.total:
        total = args.total
    else:
        total = 1

    main()
