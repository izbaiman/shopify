

# # # import streamlit as st
# # # import pandas as pd
# # # import time
# # # import random
# # # import re
# # # import base64

# # # from selenium import webdriver
# # # from selenium.webdriver.chrome.service import Service
# # # from selenium.webdriver.chrome.options import Options
# # # from webdriver_manager.chrome import ChromeDriverManager

# # # from selenium.webdriver.common.by import By
# # # from selenium.webdriver.support.ui import WebDriverWait
# # # from selenium.webdriver.support import expected_conditions as EC


# # # # ==========================================
# # # # 🛡️ DEDUPLICATION TRACKER
# # # # ==========================================
# # # seen_asins = set()


# # # # ==========================================
# # # # 🎨 FRONTEND CONFIG & CSS
# # # # ==========================================
# # # st.set_page_config(page_title="Amazon Global Hunter Pro", page_icon="🕵️‍♂️", layout="wide")

# # # st.markdown("""
# # #     <style>
# # #     .stApp { background-color: #f8f9fa; }
# # #     div[data-testid="stMetricValue"] { font-size: 1.2rem; color: #232F3E; font-weight: bold; }
# # #     .stProgress > div > div > div > div { background-color: #FF9900; }
# # #     </style>
# # # """, unsafe_allow_html=True)

# # # st.title("🕵️‍♂️ Amazon Global Hunter Pro (Final)")

# # # # ==========================================
# # # # 🌍 COUNTRY & MARKETPLACE DATABASE
# # # # ==========================================
# # # COUNTRY_SETTINGS = {
# # #     "United States 🇺🇸": {"url": "https://www.amazon.com", "symbol": "$"},
# # #     "Canada 🇨🇦": {"url": "https://www.amazon.ca", "symbol": "C$"},
# # #     "Australia 🇦🇺": {"url": "https://www.amazon.com.au", "symbol": "A$"},
# # #     "United Kingdom 🇬🇧": {"url": "https://www.amazon.co.uk", "symbol": "£"},
# # #     "Germany 🇩🇪": {"url": "https://www.amazon.de", "symbol": "€"},
# # #     "France 🇫🇷": {"url": "https://www.amazon.fr", "symbol": "€"},
# # #     "Italy 🇮🇹": {"url": "https://www.amazon.it", "symbol": "€"},
# # #     "Spain 🇪🇸": {"url": "https://www.amazon.es", "symbol": "€"},
# # #     "India 🇮🇳": {"url": "https://www.amazon.in", "symbol": "₹"},
# # # }

# # # # ==========================================
# # # # 📂 CATEGORY DATABASE
# # # # ==========================================
# # # CATEGORY_MAP = {
# # #     "Home & Garden": ["Pest Control Products", "Garden Tools", "Planters", "Outdoor Lighting", "Gardening Gloves"],
# # #     "Smart Home": ["Smart Plugs", "Smart Bulbs", "Security Cameras", "Video Doorbells", "Smart Thermostats"],
# # #     "Household & Everyday": ["Cleaning Supplies", "Storage Bins", "Trash Bags", "Batteries", "Laundry Organizers"],
# # #     "Bath & Decor": ["Bath Mats", "Shower Curtains", "Towel Racks", "Soap Dispensers", "Wall Art", "Mirrors"],
# # #     "Tools & Home Improvement": ["Power Drills", "Screwdriver Sets", "Measuring Tapes", "Flashlights", "Tool Kits"],
# # #     "Electronics & Mobile": ["Mobile Cases", "Screen Protectors", "Charging Cables", "Power Banks", "Headphones", "Phone Mounts"],
# # #     "Personal Care": ["Electric Shavers", "Hair Dryers", "Oral Care", "Skin Care Tools", "Manicure Sets", "Massagers"],
# # #     "Pet Supplies": ["Dog Toys", "Cat Scratchers", "Pet Beds", "Dog Leashes", "Grooming Tools", "Aquarium Supplies"],
# # #     "Sports & Outdoors": ["Yoga Mats", "Resistance Bands", "Camping Gear", "Water Bottles", "Gym Gloves", "Flashlights"],
# # #     "Toys & Games": ["Outdoor Toys", "Board Games", "Building Blocks", "Educational Toys", "Puzzles"],
# # #     "Baby Accessories": ["Diaper Bags", "Baby Monitors", "Stroller Organizers", "Teething Toys", "Bibs"],
# # #     "Automotive": ["Car Organizers", "Car Vacuums", "Phone Mounts", "Car Cleaning Kits", "Seat Covers", "Air Fresheners"],
# # #     "Office & Stationery": ["Notebooks", "Pens", "Desk Organizers", "Sticky Notes", "File Holders"],
# # # }

# # # # ==========================================
# # # # ⚙️ SIDEBAR - CRITERIA
# # # # ==========================================
# # # st.sidebar.header("1. Marketplace")
# # # selected_country_name = st.sidebar.selectbox("Select Country", list(COUNTRY_SETTINGS.keys()))
# # # current_config = COUNTRY_SETTINGS[selected_country_name]
# # # BASE_URL = current_config["url"]
# # # CURRENCY = current_config["symbol"]

# # # st.sidebar.header("2. Criteria")
# # # min_price = st.sidebar.number_input(f"Min Price ({CURRENCY})", value=10.0)
# # # max_price = st.sidebar.number_input(f"Max Price ({CURRENCY})", value=200.0)
# # # min_rating = st.sidebar.number_input("Min Rating", value=4.0)
# # # min_sales = st.sidebar.number_input("Min Sales (Approx)", value=100)

# # # st.sidebar.header("3. Location")
# # # zip_code = st.sidebar.text_input("Postal/Zip Code", placeholder="e.g. 10001 (US), M5V 2T6 (CA), SW1A 1AA (UK)")

# # # st.sidebar.header("4. Debug")
# # # show_sales_raw = st.sidebar.checkbox("Show Sales Raw Text (debug)", value=True)

# # # # ==========================================
# # # # 🔍 SEARCH INPUTS
# # # # ==========================================
# # # st.subheader(f"Search Settings ({selected_country_name})")

# # # search_method = st.radio("How do you want to search?", ["Type Specific Keyword", "Select Category"], horizontal=True)

# # # if search_method == "Type Specific Keyword":
# # #     search_term = st.text_input("Enter Keyword", placeholder="e.g. Wireless charger")
# # # else:
# # #     c1, c2 = st.columns(2)
# # #     with c1:
# # #         main_cat = st.selectbox("Main Category", list(CATEGORY_MAP.keys()))
# # #     with c2:
# # #         sub_cat = st.selectbox("Sub-Category", CATEGORY_MAP[main_cat])
# # #         search_term = sub_cat

# # # st.markdown("---")
# # # start_btn = st.button("🚀 Start Hunting (Scans All Available Items)", type="primary")
# # # status_area = st.empty()


# # # # ==========================================
# # # # 🛠️ BACKEND LOGIC
# # # # ==========================================

# # # def get_driver():
# # #     options = Options()
# # #     options.add_argument("--disable-blink-features=AutomationControlled")
# # #     options.add_argument("--start-maximized")
# # #     options.add_experimental_option("excludeSwitches", ["enable-automation"])
# # #     options.add_argument(
# # #         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
# # #         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
# # #     )
# # #     # options.add_argument("--headless=new")  # you can enable if you want
# # #     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# # #     driver.maximize_window()
# # #     return driver


# # # def clean_price(price_str):
# # #     if not price_str:
# # #         return 0.0
# # #     try:
# # #         # 1. Remove unit prices like ($0.83 / count)
# # #         s = str(price_str).split("(")[0]
        
# # #         # 2. Extract only numbers and decimals/commas
# # #         # Hum sirf digits, dots aur commas rakhen ge
# # #         clean = re.sub(r"[^\d.,]", "", s)

# # #         if not clean:
# # #             return 0.0

# # #         # 3. European format handle karna (e.g. 1.200,50 -> 1200.50)
# # #         if "," in clean and "." in clean:
# # #             if clean.rfind(",") > clean.rfind("."): # Comma decimal hai
# # #                 clean = clean.replace(".", "").replace(",", ".")
# # #             else: # Dot decimal hai
# # #                 clean = clean.replace(",", "")
# # #         elif "," in clean:
# # #             # Agar sirf ek comma hai aur uske baad 2 digits hain to wo decimal hai
# # #             parts = clean.split(",")
# # #             if len(parts[-1]) == 2:
# # #                 clean = clean.replace(",", ".")
# # #             else:
# # #                 clean = clean.replace(",", "")
        
# # #         return float(clean)
# # #     except:
# # #         return 0.0

# # # def smart_scroll(driver):
# # #     """Slow scroll to trigger lazy loading."""
# # #     total_height = int(driver.execute_script("return document.body.scrollHeight"))
# # #     step = 650
# # #     for y in range(1, total_height, step):
# # #         driver.execute_script(f"window.scrollTo(0, {y});")
# # #         time.sleep(0.12)
# # #     time.sleep(0.7)


# # # def handle_blocking(driver):
# # #     """Click common anti-bot modals / region prompts where possible."""
# # #     try:
# # #         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping') or contains(text(), 'Done')]")
# # #         if not btns:
# # #             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
# # #         for btn in btns:
# # #             t = (btn.text or "").lower()
# # #             if "continue" in t or "done" in t:
# # #                 btn.click()
# # #                 time.sleep(0.8)
# # #                 return True
# # #     except:
# # #         pass
# # #     return False


# # # def change_location(driver, zip_code, base_url):
# # #     if not zip_code:
# # #         return
# # #     st.toast(f"✈️ Changing location to {zip_code}...")
# # #     driver.get(base_url)
# # #     time.sleep(2)
# # #     handle_blocking(driver)
# # #     try:
# # #         driver.find_element(By.ID, "nav-global-location-popover-link").click()
# # #         time.sleep(2)
# # #         zip_input = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
# # #         zip_input.clear()
# # #         zip_input.send_keys(zip_code)
# # #         time.sleep(0.7)
# # #         driver.find_element(By.ID, "GLUXZipUpdate").click()
# # #         time.sleep(1.0)
# # #         try:
# # #             driver.find_element(By.NAME, "glowDoneButton").click()
# # #         except:
# # #             handle_blocking(driver)
# # #         time.sleep(2)
# # #         st.toast("✅ Location Updated!")
# # #     except:
# # #         st.warning("⚠️ Auto-Location Failed. Proceeding anyway.")
# # #         time.sleep(1.5)


# # # def parse_bought_sales(raw_text: str) -> int:
# # #     """
# # #     Parses:
# # #       '2K+ bought in past month' -> 2000
# # #       '40K+ bought...' -> 40000
# # #       '5,000 bought...' -> 5000
# # #       '1.5K bought...' -> 1500
# # #       '1,5K bought...' -> 1500
# # #     Only multiplies when K is attached to the number.
# # #     """
# # #     if not raw_text:
# # #         return 0
# # #     t = raw_text.strip()
# # #     low = t.lower()
# # #     if "bought" not in low:
# # #         return 0

# # #     # number + optional decimal + optional K right next to it, then bought
# # #     m = re.search(r"(\d{1,3}(?:[.,]\d{1,2})?)(\s*[kK])?\+?\s*bought", t)
# # #     if m:
# # #         num_str = m.group(1)

# # #         # normalize decimals: "1,5" -> "1.5"
# # #         if "," in num_str and "." not in num_str:
# # #             num_str = num_str.replace(",", ".")
# # #         else:
# # #             num_str = num_str.replace(",", "")

# # #         try:
# # #             num = float(num_str)
# # #         except:
# # #             return 0

# # #         has_k = m.group(2) is not None
# # #         return int(num * 1000) if has_k else int(num)

# # #     # fallback plain integer before bought
# # #     m2 = re.search(r"(\d[\d,]*)\+?\s*bought", t)
# # #     if m2:
# # #         try:
# # #             return int(m2.group(1).replace(",", ""))
# # #         except:
# # #             return 0

# # #     return 0


# # # def extract_title(card) -> str:
# # #     """Multi-selector title extraction (kills 'Unknown' most of the time)."""
# # #     selectors = [
# # #         "h2 a span",
# # #         "h2 span",
# # #         "span.a-size-medium.a-color-base.a-text-normal",
# # #         "span.a-size-base-plus.a-color-base.a-text-normal",
# # #         "h2.a-size-mini span",
# # #         "a.a-link-normal span",
# # #         "a.a-link-normal"
# # #     ]
# # #     for sel in selectors:
# # #         try:
# # #             el = card.find_element(By.CSS_SELECTOR, sel)
# # #             txt = (el.get_attribute("textContent") or el.text or "").strip()
# # #             if txt and len(txt) > 5:
# # #                 return txt
# # #         except:
# # #             continue
# # #     return "Unknown"


# # # def extract_link(card) -> str:
# # #     """Best effort: get product link from the title anchor."""
# # #     link_selectors = [
# # #         "h2 a.a-link-normal",
# # #         "a.a-link-normal.s-no-outline",
# # #         "h2 a",
# # #     ]
# # #     for sel in link_selectors:
# # #         try:
# # #             a = card.find_element(By.CSS_SELECTOR, sel)
# # #             href = a.get_attribute("href")
# # #             if href:
# # #                 if href.startswith("/"):
# # #                     return BASE_URL + href
# # #                 return href
# # #         except:
# # #             continue
# # #     return "No Link"



# # # def extract_price(card) -> float:
# # #     # In selectors ko priority wise check kiya jayega
# # #     price_selectors = [
# # #         "span.a-price span.a-offscreen", 
# # #         "span.a-price-whole", 
# # #         "span.a-color-price",
# # #         ".a-size-base.a-color-price"
# # #     ]
    
# # #     for sel in price_selectors:
# # #         try:
# # #             el = card.find_element(By.CSS_SELECTOR, sel)
# # #             raw = el.get_attribute("textContent") or el.text
# # #             if raw:
# # #                 val = clean_price(raw)
# # #                 if val > 0:
# # #                     return val
# # #         except:
# # #             continue

# # #     # Fallback: Agar upar wala fail ho jaye to Whole aur Fraction ko mila kar check karein
# # #     try:
# # #         whole = card.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
# # #         try:
# # #             fraction = card.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
# # #         except:
# # #             fraction = "00"
        
# # #         raw = f"{whole}.{fraction}"
# # #         return clean_price(raw)
# # #     except:
# # #         return 0.0

# # # def extract_list_price(card, live_price: float) -> float:
# # #     """
# # #     Label-aware list/typical/was/MRP extraction + strikethrough fallback.
# # #     Search *inside card only*.
# # #     """
# # #     # Strategy A: label-aware (Typical price / List price / Was / M.R.P.)
# # #     try:
# # #         label_words = ["typical price", "list price", "was", "m.r.p", "m.r.p."]

# # #         # Look for label anywhere, then nearest offscreen $ after it
# # #         # Note: XPath against the card element
# # #         for lab in label_words:
# # #             xp_label = (
# # #                 ".//*[contains(translate(normalize-space(.),"
# # #                 " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
# # #                 f" '{lab}')]"
# # #             )
# # #             try:
# # #                 label_els = card.find_elements(By.XPATH, xp_label)
# # #             except:
# # #                 label_els = []

# # #             if label_els:
# # #                 # nearest price after first label occurrence
# # #                 xps = [
# # #                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
# # #                     xp_label + "/following::*[contains(text(),'$') or contains(text(),'£') or contains(text(),'€') or contains(text(),'₹')][1]",
# # #                 ]
# # #                 for xp in xps:
# # #                     try:
# # #                         el = card.find_element(By.XPATH, xp)
# # #                         raw = el.get_attribute("textContent") or el.text
# # #                         val = clean_price(raw)
# # #                         if val > 0 and (live_price <= 0 or val >= live_price):
# # #                             # sanity: list should not be tiny compared to live
# # #                             if live_price > 0:
# # #                                 if val - live_price >= 0.25 and val <= live_price * 10:
# # #                                     return val
# # #                             else:
# # #                                 return val
# # #                     except:
# # #                         pass
# # #     except:
# # #         pass

# # #     # Strategy B: strikethrough price blocks
# # #     list_selectors = [
# # #         "span.a-price.a-text-price span.a-offscreen",
# # #         "span[data-a-strike='true'] span.a-offscreen",
# # #         "span.a-text-price span.a-offscreen",
# # #     ]
# # #     for sel in list_selectors:
# # #         try:
# # #             el = card.find_element(By.CSS_SELECTOR, sel)
# # #             raw = el.get_attribute("textContent") or el.text
# # #             low = (raw or "").lower()
# # #             # skip unit prices
# # #             if any(w in low for w in [" per ", "/count", "/ count", "/oz", "/ oz", "fl oz", "each", "item"]):
# # #                 continue

# # #             val = clean_price(raw)
# # #             if val > 0 and (live_price <= 0 or val > live_price):
# # #                 if live_price > 0:
# # #                     if val - live_price >= 0.25 and val <= live_price * 10:
# # #                         return val
# # #                 else:
# # #                     return val
# # #         except:
# # #             continue

# # #     return 0.0


# # # def extract_reviews(card) -> int:
# # #     try:
# # #         el = card.find_element(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
# # #         txt = (el.get_attribute("textContent") or el.text or "").strip()
# # #         # keep digits only
# # #         n = re.sub(r"[^\d]", "", txt.replace(",", ""))
# # #         return int(n) if n else 0
# # #     except:
# # #         return 0


# # # def extract_rating(card) -> float:
# # #     try:
# # #         el = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
# # #         txt = (el.get_attribute("textContent") or el.text or "").strip()
# # #         m = re.search(r"(\d+[.,]\d+|\d+)", txt)
# # #         if m:
# # #             return float(m.group(1).replace(",", "."))
# # #         return 0.0
# # #     except:
# # #         return 0.0


# # # def extract_sales(card) -> tuple[int, str]:
# # #     """
# # #     Returns (sales_int, raw_text_used).
# # #     Scans all secondary text spans because Amazon moves it around.
# # #     """
# # #     try:
# # #         spans = card.find_elements(By.CSS_SELECTOR, "span.a-size-base.a-color-secondary")
# # #         for sp in spans:
# # #             raw = (sp.get_attribute("textContent") or sp.text or "").strip()
# # #             s = parse_bought_sales(raw)
# # #             if s > 0:
# # #                 return s, raw
# # #     except:
# # #         pass
# # #     return 0, ""


# # # def extract_card_data(card):
# # #     """Extract all data from a search result card. Returns dict or None."""
# # #     asin = ""
# # #     try:
# # #         asin = (card.get_attribute("data-asin") or "").strip()
# # #     except:
# # #         asin = ""

# # #     # Skip non-product blocks
# # #     if not asin:
# # #         return None

# # #     data = {}
# # #     data["ASIN"] = asin

# # #     # Title
# # #     data["Title"] = extract_title(card)

# # #     # Link
# # #     data["Link"] = extract_link(card)

# # #     # Price
# # #     data["Price"] = extract_price(card)

# # #     # List price / typical / was
# # #     data["List Price"] = extract_list_price(card, data["Price"])

# # #     # Discount
# # #     if data["List Price"] > 0 and data["Price"] > 0 and data["List Price"] >= data["Price"]:
# # #         diff = data["List Price"] - data["Price"]
# # #         data["Discount %"] = int(round((diff / data["List Price"]) * 100))
# # #     else:
# # #         data["Discount %"] = 0

# # #     # Reviews + Rating
# # #     data["Reviews"] = extract_reviews(card)
# # #     data["Rating"] = extract_rating(card)

# # #     # Sales (Bought...)
# # #     sales, sales_raw = extract_sales(card)
# # #     data["Sales"] = sales
# # #     if show_sales_raw:
# # #         data["Sales Raw"] = sales_raw

# # #     return data


# # # def get_csv_download_link(df):
# # #     csv = df.to_csv(index=False).encode("utf-8")
# # #     b64 = base64.b64encode(csv).decode()
# # #     return (
# # #         f'<a href="data:file/csv;base64,{b64}" download="amazon_hunter_results.csv" '
# # #         f'style="text-decoration:none;background:#232F3E;color:white;padding:12px;'
# # #         f'border-radius:6px;display:block;text-align:center;font-weight:bold;">'
# # #         f'💾 Download Full Results CSV</a>'
# # #     )


# # # # ==========================================
# # # # 🏃 RUN LOGIC
# # # # ==========================================
# # # if start_btn:
# # #     if not search_term:
# # #         st.error("❌ Please enter a keyword or select a category.")
# # #     else:
# # #         seen_asins.clear()

# # #         status_area.info(f"🚀 Initializing Browser for {selected_country_name}...")
# # #         driver = get_driver()
# # #         change_location(driver, zip_code, BASE_URL)

# # #         search_query = search_term.replace(" ", "+")
# # #         target_url = f"{BASE_URL}/s?k={search_query}&s=exact-aware-popularity-rank"

# # #         driver.get(target_url)
# # #         time.sleep(2.2)

# # #         scan_limit = 3000
# # #         scanned_count = 0
# # #         all_winning_products = []
# # #         page_num = 1

# # #         status_text = st.empty()
# # #         results_placeholder = st.empty()
# # #         prog = st.progress(0)

# # #         while scanned_count < scan_limit:
# # #             handle_blocking(driver)
# # #             status_text.write(f"🔎 Scanning Page {page_num}... (scrolling)")
# # #             smart_scroll(driver)

# # #             cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")

# # #             if not cards:
# # #                 status_text.warning("⚠️ Empty page. Retrying refresh...")
# # #                 driver.refresh()
# # #                 time.sleep(3.5)
# # #                 smart_scroll(driver)
# # #                 cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
# # #                 if not cards:
# # #                     break

# # #             status_text.write(f"🧪 Processing {len(cards)} cards on Page {page_num}... (Scanned: {scanned_count})")

# # #             for card in cards:
# # #                 if scanned_count >= scan_limit:
# # #                     break

# # #                 item = extract_card_data(card)
# # #                 if not item:
# # #                     continue

# # #                 if item["ASIN"] in seen_asins:
# # #                     continue

# # #                 seen_asins.add(item["ASIN"])
# # #                 scanned_count += 1

# # #                 # skip if no valid price
# # #                 if item["Price"] <= 0:
# # #                     continue

# # #                 # ✅ CRITERIA CHECK (STRICT)
# # #                 passes_criteria = True

# # #                 if not (min_price <= item["Price"] <= max_price):
# # #                     passes_criteria = False

# # #                 if item["Rating"] < min_rating:
# # #                     passes_criteria = False

# # #                 if item["Sales"] < min_sales:
# # #                     passes_criteria = False

# # #                 if passes_criteria:
# # #                     all_winning_products.append(item)

# # #                 # live display
# # #                 if all_winning_products and (scanned_count % 30 == 0):
# # #                     df_temp = pd.DataFrame(all_winning_products)
# # #                     results_placeholder.dataframe(
# # #                         df_temp.tail(8),
# # #                         column_config={
# # #                             "Link": st.column_config.LinkColumn("Product"),
# # #                             "Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
# # #                             "List Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
# # #                             "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
# # #                         },
# # #                         use_container_width=True,
# # #                     )

# # #                 prog.progress(min(scanned_count / scan_limit, 1.0))

# # #             if scanned_count >= scan_limit:
# # #                 break

# # #             # next page
# # #             try:
# # #                 handle_blocking(driver)
# # #                 next_btn = WebDriverWait(driver, 6).until(
# # #                     EC.element_to_be_clickable((By.CSS_SELECTOR, "a.s-pagination-next"))
# # #                 )
# # #                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
# # #                 time.sleep(0.8)
# # #                 next_btn.click()
# # #                 page_num += 1
# # #                 time.sleep(random.uniform(2.2, 4.0))
# # #             except:
# # #                 st.warning("⚠️ Reached end of results (No more pages).")
# # #                 break

# # #         driver.quit()

# # #         # Final dedupe safety net (should already be clean)
# # #         if all_winning_products:
# # #             seen_final = set()
# # #             unique_products = []
# # #             for p in all_winning_products:
# # #                 if p["ASIN"] not in seen_final:
# # #                     seen_final.add(p["ASIN"])
# # #                     unique_products.append(p)
# # #             all_winning_products = unique_products

# # #         status_area.success("🎉 Hunt Complete!")

# # #         if all_winning_products:
# # #             df = pd.DataFrame(all_winning_products)

# # #             desired_order = ["ASIN", "Title", "Price", "List Price", "Discount %", "Rating", "Reviews", "Sales"]
# # #             if show_sales_raw:
# # #                 desired_order.append("Sales Raw")
# # #             desired_order.append("Link")

# # #             df = df[[c for c in desired_order if c in df.columns]]

# # #             st.subheader(f"✅ Found {len(all_winning_products)} Winning Products")
# # #             st.dataframe(
# # #                 df,
# # #                 column_config={
# # #                     "Link": st.column_config.LinkColumn("Link"),
# # #                     "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
# # #                     "Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
# # #                     "List Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
# # #                 },
# # #                 use_container_width=True,
# # #             )
# # #             st.markdown(get_csv_download_link(df), unsafe_allow_html=True)
# # #         else:
# # #             st.error(f"😔 Scanned {scanned_count} items but found 0 matches. Try lowering the sales criteria.")





# # import streamlit as st
# # import pandas as pd
# # import time
# # import random
# # import re
# # import base64

# # from selenium import webdriver
# # from selenium.webdriver.chrome.service import Service
# # from selenium.webdriver.chrome.options import Options
# # from webdriver_manager.chrome import ChromeDriverManager

# # from selenium.webdriver.common.by import By
# # from selenium.webdriver.support.ui import WebDriverWait
# # from selenium.webdriver.support import expected_conditions as EC


# # # ==========================================
# # # 🛡️ DEDUPLICATION TRACKER
# # # ==========================================
# # seen_asins = set()


# # # ==========================================
# # # 🎨 FRONTEND CONFIG & CSS
# # # ==========================================
# # st.set_page_config(page_title="Amazon Global Hunter Pro", page_icon="🕵️‍♂️", layout="wide")

# # st.markdown("""
# #     <style>
# #     .stApp { background-color: #f8f9fa; }
# #     div[data-testid="stMetricValue"] { font-size: 1.2rem; color: #232F3E; font-weight: bold; }
# #     .stProgress > div > div > div > div { background-color: #FF9900; }
# #     </style>
# # """, unsafe_allow_html=True)

# # st.title("🕵️‍♂️ Amazon Global Hunter Pro (Final)")

# # # ==========================================
# # # 🌍 COUNTRY & MARKETPLACE DATABASE
# # # ==========================================
# # COUNTRY_SETTINGS = {
# #     "United States 🇺🇸": {"url": "https://www.amazon.com", "symbol": "$"},
# #     "Canada 🇨🇦": {"url": "https://www.amazon.ca", "symbol": "C$"},
# #     "Australia 🇦🇺": {"url": "https://www.amazon.com.au", "symbol": "A$"},
# #     "United Kingdom 🇬🇧": {"url": "https://www.amazon.co.uk", "symbol": "£"},
# #     "Germany 🇩🇪": {"url": "https://www.amazon.de", "symbol": "€"},
# #     "France 🇫🇷": {"url": "https://www.amazon.fr", "symbol": "€"},
# #     "Italy 🇮🇹": {"url": "https://www.amazon.it", "symbol": "€"},
# #     "Spain 🇪🇸": {"url": "https://www.amazon.es", "symbol": "€"},
# #     "India 🇮🇳": {"url": "https://www.amazon.in", "symbol": "₹"},
# # }

# # # ==========================================
# # # 📂 CATEGORY DATABASE
# # # ==========================================
# # CATEGORY_MAP = {
# #     "Home & Garden": ["Pest Control Products", "Garden Tools", "Planters", "Outdoor Lighting", "Gardening Gloves"],
# #     "Smart Home": ["Smart Plugs", "Smart Bulbs", "Security Cameras", "Video Doorbells", "Smart Thermostats"],
# #     "Household & Everyday": ["Cleaning Supplies", "Storage Bins", "Trash Bags", "Batteries", "Laundry Organizers"],
# #     "Bath & Decor": ["Bath Mats", "Shower Curtains", "Towel Racks", "Soap Dispensers", "Wall Art", "Mirrors"],
# #     "Tools & Home Improvement": ["Power Drills", "Screwdriver Sets", "Measuring Tapes", "Flashlights", "Tool Kits"],
# #     "Electronics & Mobile": ["Mobile Cases", "Screen Protectors", "Charging Cables", "Power Banks", "Headphones", "Phone Mounts"],
# #     "Personal Care": ["Electric Shavers", "Hair Dryers", "Oral Care", "Skin Care Tools", "Manicure Sets", "Massagers"],
# #     "Pet Supplies": ["Dog Toys", "Cat Scratchers", "Pet Beds", "Dog Leashes", "Grooming Tools", "Aquarium Supplies"],
# #     "Sports & Outdoors": ["Yoga Mats", "Resistance Bands", "Camping Gear", "Water Bottles", "Gym Gloves", "Flashlights"],
# #     "Toys & Games": ["Outdoor Toys", "Board Games", "Building Blocks", "Educational Toys", "Puzzles"],
# #     "Baby Accessories": ["Diaper Bags", "Baby Monitors", "Stroller Organizers", "Teething Toys", "Bibs"],
# #     "Automotive": ["Car Organizers", "Car Vacuums", "Phone Mounts", "Car Cleaning Kits", "Seat Covers", "Air Fresheners"],
# #     "Office & Stationery": ["Notebooks", "Pens", "Desk Organizers", "Sticky Notes", "File Holders"],
# # }

# # # ==========================================
# # # ⚙️ SIDEBAR - CRITERIA
# # # ==========================================
# # st.sidebar.header("1. Marketplace")
# # selected_country_name = st.sidebar.selectbox("Select Country", list(COUNTRY_SETTINGS.keys()))
# # current_config = COUNTRY_SETTINGS[selected_country_name]
# # BASE_URL = current_config["url"]
# # CURRENCY = current_config["symbol"]

# # st.sidebar.header("2. Criteria")
# # min_price = st.sidebar.number_input(f"Min Price ({CURRENCY})", value=10.0)
# # max_price = st.sidebar.number_input(f"Max Price ({CURRENCY})", value=200.0)
# # min_rating = st.sidebar.number_input("Min Rating", value=4.0)
# # min_sales = st.sidebar.number_input("Min Sales (Approx)", value=100)

# # st.sidebar.header("3. Location")
# # zip_code = st.sidebar.text_input("Postal/Zip Code", placeholder="e.g. 10001 (US), M5V 2T6 (CA), SW1A 1AA (UK)")

# # st.sidebar.header("4. Debug")
# # show_sales_raw = st.sidebar.checkbox("Show Sales Raw Text (debug)", value=True)

# # # ==========================================
# # # 🔍 SEARCH INPUTS
# # # ==========================================
# # st.subheader(f"Search Settings ({selected_country_name})")

# # search_method = st.radio("How do you want to search?", ["Type Specific Keyword", "Select Category"], horizontal=True)

# # if search_method == "Type Specific Keyword":
# #     search_term = st.text_input("Enter Keyword", placeholder="e.g. Wireless charger")
# # else:
# #     c1, c2 = st.columns(2)
# #     with c1:
# #         main_cat = st.selectbox("Main Category", list(CATEGORY_MAP.keys()))
# #     with c2:
# #         sub_cat = st.selectbox("Sub-Category", CATEGORY_MAP[main_cat])
# #         search_term = sub_cat

# # st.markdown("---")
# # start_btn = st.button("🚀 Start Hunting (Scans All Available Items)", type="primary")
# # status_area = st.empty()


# # # ==========================================
# # # 🛠️ BACKEND LOGIC
# # # ==========================================

# # def get_driver():
# #     options = Options()
# #     options.add_argument("--disable-blink-features=AutomationControlled")
# #     options.add_argument("--start-maximized")
# #     options.add_experimental_option("excludeSwitches", ["enable-automation"])
# #     options.add_argument(
# #         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
# #         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
# #     )
# #     # options.add_argument("--headless=new")  # you can enable if you want
# #     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# #     driver.maximize_window()
# #     return driver


# # def clean_price(price_str):
# #     if not price_str:
# #         return 0.0
# #     try:
# #         # 1. Remove unit prices like ($0.83 / count)
# #         s = str(price_str).split("(")[0]
        
# #         # 2. Extract only numbers and decimals/commas
# #         # Hum sirf digits, dots aur commas rakhen ge
# #         clean = re.sub(r"[^\d.,]", "", s)

# #         if not clean:
# #             return 0.0

# #         # 3. European format handle karna (e.g. 1.200,50 -> 1200.50)
# #         if "," in clean and "." in clean:
# #             if clean.rfind(",") > clean.rfind("."): # Comma decimal hai
# #                 clean = clean.replace(".", "").replace(",", ".")
# #             else: # Dot decimal hai
# #                 clean = clean.replace(",", "")
# #         elif "," in clean:
# #             # Agar sirf ek comma hai aur uske baad 2 digits hain to wo decimal hai
# #             parts = clean.split(",")
# #             if len(parts[-1]) == 2:
# #                 clean = clean.replace(",", ".")
# #             else:
# #                 clean = clean.replace(",", "")
        
# #         return float(clean)
# #     except:
# #         return 0.0

# # def smart_scroll(driver):
# #     """Slow scroll to trigger lazy loading."""
# #     total_height = int(driver.execute_script("return document.body.scrollHeight"))
# #     step = 650
# #     for y in range(1, total_height, step):
# #         driver.execute_script(f"window.scrollTo(0, {y});")
# #         time.sleep(0.12)
# #     time.sleep(0.7)


# # def handle_blocking(driver):
# #     """Click common anti-bot modals / region prompts where possible."""
# #     try:
# #         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping') or contains(text(), 'Done')]")
# #         if not btns:
# #             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
# #         for btn in btns:
# #             t = (btn.text or "").lower()
# #             if "continue" in t or "done" in t:
# #                 btn.click()
# #                 time.sleep(0.8)
# #                 return True
# #     except:
# #         pass
# #     return False


# # def change_location(driver, zip_code, base_url):
# #     if not zip_code:
# #         return
# #     st.toast(f"✈️ Changing location to {zip_code}...")
# #     driver.get(base_url)
# #     time.sleep(2)
# #     handle_blocking(driver)
# #     try:
# #         driver.find_element(By.ID, "nav-global-location-popover-link").click()
# #         time.sleep(2)
# #         zip_input = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
# #         zip_input.clear()
# #         zip_input.send_keys(zip_code)
# #         time.sleep(0.7)
# #         driver.find_element(By.ID, "GLUXZipUpdate").click()
# #         time.sleep(1.0)
# #         try:
# #             driver.find_element(By.NAME, "glowDoneButton").click()
# #         except:
# #             handle_blocking(driver)
# #         time.sleep(2)
# #         st.toast("✅ Location Updated!")
# #     except:
# #         st.warning("⚠️ Auto-Location Failed. Proceeding anyway.")
# #         time.sleep(1.5)


# # def parse_bought_sales(raw_text: str) -> int:
# #     """
# #     Parses:
# #       '2K+ bought in past month' -> 2000
# #       '40K+ bought...' -> 40000
# #       '5,000 bought...' -> 5000
# #       '1.5K bought...' -> 1500
# #       '1,5K bought...' -> 1500
# #     Only multiplies when K is attached to the number.
# #     """
# #     if not raw_text:
# #         return 0
# #     t = raw_text.strip()
# #     low = t.lower()
# #     if "bought" not in low:
# #         return 0

# #     # number + optional decimal + optional K right next to it, then bought
# #     m = re.search(r"(\d{1,3}(?:[.,]\d{1,2})?)(\s*[kK])?\+?\s*bought", t)
# #     if m:
# #         num_str = m.group(1)

# #         # normalize decimals: "1,5" -> "1.5"
# #         if "," in num_str and "." not in num_str:
# #             num_str = num_str.replace(",", ".")
# #         else:
# #             num_str = num_str.replace(",", "")

# #         try:
# #             num = float(num_str)
# #         except:
# #             return 0

# #         has_k = m.group(2) is not None
# #         return int(num * 1000) if has_k else int(num)

# #     # fallback plain integer before bought
# #     m2 = re.search(r"(\d[\d,]*)\+?\s*bought", t)
# #     if m2:
# #         try:
# #             return int(m2.group(1).replace(",", ""))
# #         except:
# #             return 0

# #     return 0


# # def extract_title(card) -> str:
# #     """Multi-selector title extraction (kills 'Unknown' most of the time)."""
# #     selectors = [
# #         "h2 a span",
# #         "h2 span",
# #         "span.a-size-medium.a-color-base.a-text-normal",
# #         "span.a-size-base-plus.a-color-base.a-text-normal",
# #         "h2.a-size-mini span",
# #         "a.a-link-normal span",
# #         "a.a-link-normal"
# #     ]
# #     for sel in selectors:
# #         try:
# #             el = card.find_element(By.CSS_SELECTOR, sel)
# #             txt = (el.get_attribute("textContent") or el.text or "").strip()
# #             if txt and len(txt) > 5:
# #                 return txt
# #         except:
# #             continue
# #     return "Unknown"


# # def extract_link(card) -> str:
# #     """Best effort: get product link from the title anchor."""
# #     link_selectors = [
# #         "h2 a.a-link-normal",
# #         "a.a-link-normal.s-no-outline",
# #         "h2 a",
# #     ]
# #     for sel in link_selectors:
# #         try:
# #             a = card.find_element(By.CSS_SELECTOR, sel)
# #             href = a.get_attribute("href")
# #             if href:
# #                 if href.startswith("/"):
# #                     return BASE_URL + href
# #                 return href
# #         except:
# #             continue
# #     return "No Link"



# # # def extract_price(card) -> float:
# # #     # In selectors ko priority wise check kiya jayega
# # #     price_selectors = [
# # #         "span.a-price span.a-offscreen",
# # #         "span.a-price-whole",
# # #         "span.a-color-price",
# # #         ".a-size-base.a-color-price"
# # #     ]
# # #
# # #     for sel in price_selectors:
# # #         try:
# # #             el = card.find_element(By.CSS_SELECTOR, sel)
# # #             raw = el.get_attribute("textContent") or el.text
# # #             if raw:
# # #                 val = clean_price(raw)
# # #                 if val > 0:
# # #                     return val
# # #         except:
# # #             continue
# # #
# # #     # Fallback: Agar upar wala fail ho jaye to Whole aur Fraction ko mila kar check karein
# # #     try:
# # #         whole = card.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
# # #         try:
# # #             fraction = card.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
# # #         except:
# # #             fraction = "00"
# # #
# # #         raw = f"{whole}.{fraction}"
# # #         return clean_price(raw)
# # #     except:
# # #         return 0.0


# # def extract_price(card) -> float:
# #     """
# #     Extract the REAL live selling price only.
# #     Avoids:
# #     - unit prices
# #     - subscription prices
# #     - struck prices
# #     - coupon values
# #     """

# #     # Priority selectors for CURRENT LIVE PRICE
# #     selectors = [
# #         "span.a-price:not(.a-text-price) span.a-offscreen",
# #         ".a-price.aok-align-center span.a-offscreen",
# #         ".a-price-range span.a-offscreen",
# #     ]

# #     for sel in selectors:
# #         try:
# #             elements = card.find_elements(By.CSS_SELECTOR, sel)

# #             for el in elements:
# #                 raw = (el.get_attribute("textContent") or el.text or "").strip()

# #                 if not raw:
# #                     continue

# #                 low = raw.lower()

# #                 # ❌ Skip unit prices
# #                 bad_words = [
# #                     "/count",
# #                     "/ count",
# #                     "/oz",
# #                     "/ oz",
# #                     "per count",
# #                     "each",
# #                     "subscribe",
# #                     "delivery",
# #                     "coupon",
# #                     "off"
# #                 ]

# #                 if any(b in low for b in bad_words):
# #                     continue

# #                 value = clean_price(raw)

# #                 # sanity checks
# #                 if value > 0 and value < 100000:
# #                     return value

# #         except:
# #             continue

# #     # fallback method
# #     try:
# #         whole = card.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
# #         fraction = "00"

# #         try:
# #             fraction = card.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
# #         except:
# #             pass

# #         raw = f"{whole}.{fraction}"

# #         value = clean_price(raw)

# #         if value > 0:
# #             return value

# #     except:
# #         pass

# #     return 0.0



# # def extract_list_price(card, live_price: float) -> float:
# #     """
# #     Label-aware list/typical/was/MRP extraction + strikethrough fallback.
# #     Search *inside card only*.
# #     """
# #     # Strategy A: label-aware (Typical price / List price / Was / M.R.P.)
# #     try:
# #         label_words = ["typical price", "list price", "was", "m.r.p", "m.r.p."]

# #         # Look for label anywhere, then nearest offscreen $ after it
# #         # Note: XPath against the card element
# #         for lab in label_words:
# #             xp_label = (
# #                 ".//*[contains(translate(normalize-space(.),"
# #                 " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
# #                 f" '{lab}')]"
# #             )
# #             try:
# #                 label_els = card.find_elements(By.XPATH, xp_label)
# #             except:
# #                 label_els = []

# #             if label_els:
# #                 # nearest price after first label occurrence
# #                 xps = [
# #                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
# #                     xp_label + "/following::*[contains(text(),'$') or contains(text(),'£') or contains(text(),'€') or contains(text(),'₹')][1]",
# #                 ]
# #                 for xp in xps:
# #                     try:
# #                         el = card.find_element(By.XPATH, xp)
# #                         raw = el.get_attribute("textContent") or el.text
# #                         val = clean_price(raw)
# #                         if val > 0 and (live_price <= 0 or val >= live_price):
# #                             # sanity: list should not be tiny compared to live
# #                             if live_price > 0:
# #                                 if val - live_price >= 0.25 and val <= live_price * 10:
# #                                     return val
# #                             else:
# #                                 return val
# #                     except:
# #                         pass
# #     except:
# #         pass

# #     # Strategy B: strikethrough price blocks
# #     list_selectors = [
# #         "span.a-price.a-text-price span.a-offscreen",
# #         "span[data-a-strike='true'] span.a-offscreen",
# #         "span.a-text-price span.a-offscreen",
# #     ]
# #     for sel in list_selectors:
# #         try:
# #             el = card.find_element(By.CSS_SELECTOR, sel)
# #             raw = el.get_attribute("textContent") or el.text
# #             low = (raw or "").lower()
# #             # skip unit prices
# #             if any(w in low for w in [" per ", "/count", "/ count", "/oz", "/ oz", "fl oz", "each", "item"]):
# #                 continue

# #             val = clean_price(raw)
# #             if val > 0 and (live_price <= 0 or val > live_price):
# #                 if live_price > 0:
# #                     if val - live_price >= 0.25 and val <= live_price * 10:
# #                         return val
# #                 else:
# #                     return val
# #         except:
# #             continue

# #     return 0.0


# # def extract_reviews(card) -> int:
# #     try:
# #         el = card.find_element(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
# #         txt = (el.get_attribute("textContent") or el.text or "").strip()
# #         # keep digits only
# #         n = re.sub(r"[^\d]", "", txt.replace(",", ""))
# #         return int(n) if n else 0
# #     except:
# #         return 0


# # def extract_rating(card) -> float:
# #     try:
# #         el = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
# #         txt = (el.get_attribute("textContent") or el.text or "").strip()
# #         m = re.search(r"(\d+[.,]\d+|\d+)", txt)
# #         if m:
# #             return float(m.group(1).replace(",", "."))
# #         return 0.0
# #     except:
# #         return 0.0


# # def extract_sales(card) -> tuple[int, str]:
# #     """
# #     Returns (sales_int, raw_text_used).
# #     Scans all secondary text spans because Amazon moves it around.
# #     """
# #     try:
# #         spans = card.find_elements(By.CSS_SELECTOR, "span.a-size-base.a-color-secondary")
# #         for sp in spans:
# #             raw = (sp.get_attribute("textContent") or sp.text or "").strip()
# #             s = parse_bought_sales(raw)
# #             if s > 0:
# #                 return s, raw
# #     except:
# #         pass
# #     return 0, ""


# # def extract_card_data(card):
# #     """Extract all data from a search result card. Returns dict or None."""
# #     asin = ""
# #     try:
# #         asin = (card.get_attribute("data-asin") or "").strip()
# #     except:
# #         asin = ""

# #     # Skip non-product blocks
# #     if not asin:
# #         return None

# #     data = {}
# #     data["ASIN"] = asin

# #     # Title
# #     data["Title"] = extract_title(card)

# #     # Link
# #     data["Link"] = extract_link(card)

# #     # Price
# #     data["Price"] = extract_price(card)

# #     # List price / typical / was
# #     # data["List Price"] = extract_list_price(card, data["Price"])

# #     # Extract list price
# #     list_price = extract_list_price(card, data["Price"])

# #     # If no list price found, use actual price
# #     if list_price <= 0:
# #         list_price = data["Price"]

# #     data["List Price"] = list_price


# #     # Discount
# #     # if data["List Price"] > 0 and data["Price"] > 0 and data["List Price"] >= data["Price"]:
# #     #     diff = data["List Price"] - data["Price"]
# #     #     data["Discount %"] = int(round((diff / data["List Price"]) * 100))
# #     # else:
# #     #     data["Discount %"] = 0

# #     if (
# #             data["List Price"] > 0
# #             and data["Price"] > 0
# #             and data["List Price"] > data["Price"]
# #     ):
# #         diff = data["List Price"] - data["Price"]
# #         data["Discount %"] = int(round((diff / data["List Price"]) * 100))
# #     else:
# #         data["Discount %"] = 0

# #     # Reviews + Rating
# #     data["Reviews"] = extract_reviews(card)
# #     data["Rating"] = extract_rating(card)

# #     # Sales (Bought...)
# #     sales, sales_raw = extract_sales(card)
# #     data["Sales"] = sales
# #     if show_sales_raw:
# #         data["Sales Raw"] = sales_raw

# #     return data


# # def get_csv_download_link(df):
# #     csv = df.to_csv(index=False).encode("utf-8")
# #     b64 = base64.b64encode(csv).decode()
# #     return (
# #         f'<a href="data:file/csv;base64,{b64}" download="amazon_hunter_results.csv" '
# #         f'style="text-decoration:none;background:#232F3E;color:white;padding:12px;'
# #         f'border-radius:6px;display:block;text-align:center;font-weight:bold;">'
# #         f'💾 Download Full Results CSV</a>'
# #     )


# # # ==========================================
# # # 🏃 RUN LOGIC
# # # ==========================================
# # if start_btn:
# #     if not search_term:
# #         st.error("❌ Please enter a keyword or select a category.")
# #     else:
# #         seen_asins.clear()

# #         status_area.info(f"🚀 Initializing Browser for {selected_country_name}...")
# #         driver = get_driver()
# #         change_location(driver, zip_code, BASE_URL)

# #         search_query = search_term.replace(" ", "+")
# #         target_url = f"{BASE_URL}/s?k={search_query}&s=exact-aware-popularity-rank"

# #         driver.get(target_url)
# #         time.sleep(2.2)

# #         scan_limit = 3000
# #         scanned_count = 0
# #         all_winning_products = []
# #         page_num = 1

# #         status_text = st.empty()
# #         results_placeholder = st.empty()
# #         prog = st.progress(0)

# #         while scanned_count < scan_limit:
# #             handle_blocking(driver)
# #             status_text.write(f"🔎 Scanning Page {page_num}... (scrolling)")
# #             smart_scroll(driver)

# #             cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")

# #             if not cards:
# #                 status_text.warning("⚠️ Empty page. Retrying refresh...")
# #                 driver.refresh()
# #                 time.sleep(3.5)
# #                 smart_scroll(driver)
# #                 cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
# #                 if not cards:
# #                     break

# #             status_text.write(f"🧪 Processing {len(cards)} cards on Page {page_num}... (Scanned: {scanned_count})")

# #             for card in cards:
# #                 if scanned_count >= scan_limit:
# #                     break

# #                 item = extract_card_data(card)
# #                 if not item:
# #                     continue

# #                 if item["ASIN"] in seen_asins:
# #                     continue

# #                 seen_asins.add(item["ASIN"])
# #                 scanned_count += 1

# #                 # skip if no valid price
# #                 if item["Price"] <= 0:
# #                     continue

# #                 # ✅ CRITERIA CHECK (STRICT)
# #                 passes_criteria = True

# #                 if not (min_price <= item["Price"] <= max_price):
# #                     passes_criteria = False

# #                 if item["Rating"] < min_rating:
# #                     passes_criteria = False

# #                 if item["Sales"] < min_sales:
# #                     passes_criteria = False

# #                 if passes_criteria:
# #                     all_winning_products.append(item)

# #                 # live display
# #                 if all_winning_products and (scanned_count % 30 == 0):
# #                     df_temp = pd.DataFrame(all_winning_products)
# #                     results_placeholder.dataframe(
# #                         df_temp.tail(8),
# #                         column_config={
# #                             "Link": st.column_config.LinkColumn("Product"),
# #                             "Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
# #                             "List Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
# #                             "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
# #                         },
# #                         use_container_width=True,
# #                     )

# #                 prog.progress(min(scanned_count / scan_limit, 1.0))

# #             if scanned_count >= scan_limit:
# #                 break

# #             # next page
# #             try:
# #                 handle_blocking(driver)
# #                 next_btn = WebDriverWait(driver, 6).until(
# #                     EC.element_to_be_clickable((By.CSS_SELECTOR, "a.s-pagination-next"))
# #                 )
# #                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
# #                 time.sleep(0.8)
# #                 next_btn.click()
# #                 page_num += 1
# #                 time.sleep(random.uniform(2.2, 4.0))
# #             except:
# #                 st.warning("⚠️ Reached end of results (No more pages).")
# #                 break

# #         driver.quit()

# #         # Final dedupe safety net (should already be clean)
# #         if all_winning_products:
# #             seen_final = set()
# #             unique_products = []
# #             for p in all_winning_products:
# #                 if p["ASIN"] not in seen_final:
# #                     seen_final.add(p["ASIN"])
# #                     unique_products.append(p)
# #             all_winning_products = unique_products

# #         status_area.success("🎉 Hunt Complete!")

# #         if all_winning_products:
# #             df = pd.DataFrame(all_winning_products)

# #             desired_order = ["ASIN", "Title", "Price", "List Price", "Discount %", "Rating", "Reviews", "Sales"]
# #             if show_sales_raw:
# #                 desired_order.append("Sales Raw")
# #             desired_order.append("Link")

# #             df = df[[c for c in desired_order if c in df.columns]]

# #             st.subheader(f"✅ Found {len(all_winning_products)} Winning Products")
# #             st.dataframe(
# #                 df,
# #                 column_config={
# #                     "Link": st.column_config.LinkColumn("Link"),
# #                     "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
# #                     "Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
# #                     "List Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
# #                 },
# #                 use_container_width=True,
# #             )
# #             st.markdown(get_csv_download_link(df), unsafe_allow_html=True)
# #         else:
# #             st.error(f"😔 Scanned {scanned_count} items but found 0 matches. Try lowering the sales criteria.")

# #######################################Old Code
# import streamlit as st
# import pandas as pd
# import time
# import random
# import re
# import base64

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC


# # ==========================================
# # 🛡️ DEDUPLICATION TRACKER
# # ==========================================
# seen_asins = set()


# # ==========================================
# # 🎨 FRONTEND CONFIG & CSS
# # ==========================================
# st.set_page_config(page_title="Amazon Global Hunter Pro", page_icon="🕵️‍♂️", layout="wide")

# st.markdown("""
#     <style>
#     .stApp { background-color: #f8f9fa; }
#     div[data-testid="stMetricValue"] { font-size: 1.2rem; color: #232F3E; font-weight: bold; }
#     .stProgress > div > div > div > div { background-color: #FF9900; }
#     </style>
# """, unsafe_allow_html=True)

# st.title("🕵️‍♂️ Amazon Global Hunter Pro (Final)")

# # ==========================================
# # 🌍 COUNTRY & MARKETPLACE DATABASE
# # ==========================================
# COUNTRY_SETTINGS = {
#     "United States 🇺🇸": {"url": "https://www.amazon.com", "symbol": "$"},
#     "Canada 🇨🇦": {"url": "https://www.amazon.ca", "symbol": "C$"},
#     "Australia 🇦🇺": {"url": "https://www.amazon.com.au", "symbol": "A$"},
#     "United Kingdom 🇬🇧": {"url": "https://www.amazon.co.uk", "symbol": "£"},
#     "Germany 🇩🇪": {"url": "https://www.amazon.de", "symbol": "€"},
#     "France 🇫🇷": {"url": "https://www.amazon.fr", "symbol": "€"},
#     "Italy 🇮🇹": {"url": "https://www.amazon.it", "symbol": "€"},
#     "Spain 🇪🇸": {"url": "https://www.amazon.es", "symbol": "€"},
#     "India 🇮🇳": {"url": "https://www.amazon.in", "symbol": "₹"},
# }

# # ==========================================
# # 📂 CATEGORY DATABASE
# # ==========================================
# CATEGORY_MAP = {
#     "Home & Garden": ["Pest Control Products", "Garden Tools", "Planters", "Outdoor Lighting", "Gardening Gloves"],
#     "Smart Home": ["Smart Plugs", "Smart Bulbs", "Security Cameras", "Video Doorbells", "Smart Thermostats"],
#     "Household & Everyday": ["Cleaning Supplies", "Storage Bins", "Trash Bags", "Batteries", "Laundry Organizers"],
#     "Bath & Decor": ["Bath Mats", "Shower Curtains", "Towel Racks", "Soap Dispensers", "Wall Art", "Mirrors"],
#     "Tools & Home Improvement": ["Power Drills", "Screwdriver Sets", "Measuring Tapes", "Flashlights", "Tool Kits"],
#     "Electronics & Mobile": ["Mobile Cases", "Screen Protectors", "Charging Cables", "Power Banks", "Headphones", "Phone Mounts"],
#     "Personal Care": ["Electric Shavers", "Hair Dryers", "Oral Care", "Skin Care Tools", "Manicure Sets", "Massagers"],
#     "Pet Supplies": ["Dog Toys", "Cat Scratchers", "Pet Beds", "Dog Leashes", "Grooming Tools", "Aquarium Supplies"],
#     "Sports & Outdoors": ["Yoga Mats", "Resistance Bands", "Camping Gear", "Water Bottles", "Gym Gloves", "Flashlights"],
#     "Toys & Games": ["Outdoor Toys", "Board Games", "Building Blocks", "Educational Toys", "Puzzles"],
#     "Baby Accessories": ["Diaper Bags", "Baby Monitors", "Stroller Organizers", "Teething Toys", "Bibs"],
#     "Automotive": ["Car Organizers", "Car Vacuums", "Phone Mounts", "Car Cleaning Kits", "Seat Covers", "Air Fresheners"],
#     "Office & Stationery": ["Notebooks", "Pens", "Desk Organizers", "Sticky Notes", "File Holders"],
# }

# # ==========================================
# # ⚙️ SIDEBAR - CRITERIA
# # ==========================================
# st.sidebar.header("1. Marketplace")
# selected_country_name = st.sidebar.selectbox("Select Country", list(COUNTRY_SETTINGS.keys()))
# current_config = COUNTRY_SETTINGS[selected_country_name]
# BASE_URL = current_config["url"]
# CURRENCY = current_config["symbol"]

# st.sidebar.header("2. Criteria")
# min_price = st.sidebar.number_input(f"Min Price ({CURRENCY})", value=10.0)
# max_price = st.sidebar.number_input(f"Max Price ({CURRENCY})", value=200.0)
# min_rating = st.sidebar.number_input("Min Rating", value=4.0)
# min_sales = st.sidebar.number_input("Min Sales (Approx)", value=100)

# st.sidebar.header("3. Location")
# zip_code = st.sidebar.text_input("Postal/Zip Code", placeholder="e.g. 10001 (US), M5V 2T6 (CA), SW1A 1AA (UK)")

# st.sidebar.header("4. Debug")
# show_sales_raw = st.sidebar.checkbox("Show Sales Raw Text (debug)", value=True)

# # ==========================================
# # 🔍 SEARCH INPUTS
# # ==========================================
# st.subheader(f"Search Settings ({selected_country_name})")

# search_method = st.radio("How do you want to search?", ["Type Specific Keyword", "Select Category"], horizontal=True)

# if search_method == "Type Specific Keyword":
#     search_term = st.text_input("Enter Keyword", placeholder="e.g. Wireless charger")
# else:
#     c1, c2 = st.columns(2)
#     with c1:
#         main_cat = st.selectbox("Main Category", list(CATEGORY_MAP.keys()))
#     with c2:
#         sub_cat = st.selectbox("Sub-Category", CATEGORY_MAP[main_cat])
#         search_term = sub_cat

# st.markdown("---")
# start_btn = st.button("🚀 Start Hunting (Scans All Available Items)", type="primary")
# status_area = st.empty()


# # ==========================================
# # 🛠️ BACKEND LOGIC
# # ==========================================

# def get_driver():
#     options = Options()
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_argument("--start-maximized")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
#     )
#     # options.add_argument("--headless=new")  # you can enable if you want
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     driver.maximize_window()
#     return driver


# def clean_price(price_str):
#     if not price_str:
#         return 0.0
#     try:
#         # 1. Remove unit prices like ($0.83 / count)
#         s = str(price_str).split("(")[0]
        
#         # 2. Extract only numbers and decimals/commas
#         # Hum sirf digits, dots aur commas rakhen ge
#         clean = re.sub(r"[^\d.,]", "", s)

#         if not clean:
#             return 0.0

#         # 3. European format handle karna (e.g. 1.200,50 -> 1200.50)
#         if "," in clean and "." in clean:
#             if clean.rfind(",") > clean.rfind("."): # Comma decimal hai
#                 clean = clean.replace(".", "").replace(",", ".")
#             else: # Dot decimal hai
#                 clean = clean.replace(",", "")
#         elif "," in clean:
#             # Agar sirf ek comma hai aur uske baad 2 digits hain to wo decimal hai
#             parts = clean.split(",")
#             if len(parts[-1]) == 2:
#                 clean = clean.replace(",", ".")
#             else:
#                 clean = clean.replace(",", "")
        
#         return float(clean)
#     except:
#         return 0.0

# def smart_scroll(driver):
#     """Slow scroll to trigger lazy loading."""
#     total_height = int(driver.execute_script("return document.body.scrollHeight"))
#     step = 650
#     for y in range(1, total_height, step):
#         driver.execute_script(f"window.scrollTo(0, {y});")
#         time.sleep(0.12)
#     time.sleep(0.7)


# def handle_blocking(driver):
#     """Click common anti-bot modals / region prompts where possible."""
#     try:
#         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping') or contains(text(), 'Done')]")
#         if not btns:
#             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
#         for btn in btns:
#             t = (btn.text or "").lower()
#             if "continue" in t or "done" in t:
#                 btn.click()
#                 time.sleep(0.8)
#                 return True
#     except:
#         pass
#     return False


# def change_location(driver, zip_code, base_url):
#     if not zip_code:
#         return
#     st.toast(f"✈️ Changing location to {zip_code}...")
#     driver.get(base_url)
#     time.sleep(2)
#     handle_blocking(driver)
#     try:
#         driver.find_element(By.ID, "nav-global-location-popover-link").click()
#         time.sleep(2)
#         zip_input = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
#         zip_input.clear()
#         zip_input.send_keys(zip_code)
#         time.sleep(0.7)
#         driver.find_element(By.ID, "GLUXZipUpdate").click()
#         time.sleep(1.0)
#         try:
#             driver.find_element(By.NAME, "glowDoneButton").click()
#         except:
#             handle_blocking(driver)
#         time.sleep(2)
#         st.toast("✅ Location Updated!")
#     except:
#         st.warning("⚠️ Auto-Location Failed. Proceeding anyway.")
#         time.sleep(1.5)


# def parse_bought_sales(raw_text: str) -> int:
#     """
#     Parses:
#       '2K+ bought in past month' -> 2000
#       '40K+ bought...' -> 40000
#       '5,000 bought...' -> 5000
#       '1.5K bought...' -> 1500
#       '1,5K bought...' -> 1500
#     Only multiplies when K is attached to the number.
#     """
#     if not raw_text:
#         return 0
#     t = raw_text.strip()
#     low = t.lower()
#     if "bought" not in low:
#         return 0

#     # number + optional decimal + optional K right next to it, then bought
#     m = re.search(r"(\d{1,3}(?:[.,]\d{1,2})?)(\s*[kK])?\+?\s*bought", t)
#     if m:
#         num_str = m.group(1)

#         # normalize decimals: "1,5" -> "1.5"
#         if "," in num_str and "." not in num_str:
#             num_str = num_str.replace(",", ".")
#         else:
#             num_str = num_str.replace(",", "")

#         try:
#             num = float(num_str)
#         except:
#             return 0

#         has_k = m.group(2) is not None
#         return int(num * 1000) if has_k else int(num)

#     # fallback plain integer before bought
#     m2 = re.search(r"(\d[\d,]*)\+?\s*bought", t)
#     if m2:
#         try:
#             return int(m2.group(1).replace(",", ""))
#         except:
#             return 0

#     return 0


# def extract_title(card) -> str:
#     """Multi-selector title extraction (kills 'Unknown' most of the time)."""
#     selectors = [
#         "h2 a span",
#         "h2 span",
#         "span.a-size-medium.a-color-base.a-text-normal",
#         "span.a-size-base-plus.a-color-base.a-text-normal",
#         "h2.a-size-mini span",
#         "a.a-link-normal span",
#         "a.a-link-normal"
#     ]
#     for sel in selectors:
#         try:
#             el = card.find_element(By.CSS_SELECTOR, sel)
#             txt = (el.get_attribute("textContent") or el.text or "").strip()
#             if txt and len(txt) > 5:
#                 return txt
#         except:
#             continue
#     return "Unknown"


# def extract_link(card) -> str:
#     """Best effort: get product link from the title anchor."""
#     link_selectors = [
#         "h2 a.a-link-normal",
#         "a.a-link-normal.s-no-outline",
#         "h2 a",
#     ]
#     for sel in link_selectors:
#         try:
#             a = card.find_element(By.CSS_SELECTOR, sel)
#             href = a.get_attribute("href")
#             if href:
#                 if href.startswith("/"):
#                     return BASE_URL + href
#                 return href
#         except:
#             continue
#     return "No Link"



# # def extract_price(card) -> float:
# #     # In selectors ko priority wise check kiya jayega
# #     price_selectors = [
# #         "span.a-price span.a-offscreen",
# #         "span.a-price-whole",
# #         "span.a-color-price",
# #         ".a-size-base.a-color-price"
# #     ]
# #
# #     for sel in price_selectors:
# #         try:
# #             el = card.find_element(By.CSS_SELECTOR, sel)
# #             raw = el.get_attribute("textContent") or el.text
# #             if raw:
# #                 val = clean_price(raw)
# #                 if val > 0:
# #                     return val
# #         except:
# #             continue
# #
# #     # Fallback: Agar upar wala fail ho jaye to Whole aur Fraction ko mila kar check karein
# #     try:
# #         whole = card.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
# #         try:
# #             fraction = card.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
# #         except:
# #             fraction = "00"
# #
# #         raw = f"{whole}.{fraction}"
# #         return clean_price(raw)
# #     except:
# #         return 0.0


# def extract_price(card) -> float:
#     """
#     Extract the REAL live selling price only.
#     Avoids:
#     - unit prices
#     - subscription prices
#     - struck prices
#     - coupon values
#     """

#     # Priority selectors for CURRENT LIVE PRICE
#     selectors = [
#         "span.a-price:not(.a-text-price) span.a-offscreen",
#         ".a-price.aok-align-center span.a-offscreen",
#         ".a-price-range span.a-offscreen",
#     ]

#     for sel in selectors:
#         try:
#             elements = card.find_elements(By.CSS_SELECTOR, sel)

#             for el in elements:
#                 raw = (el.get_attribute("textContent") or el.text or "").strip()

#                 if not raw:
#                     continue

#                 low = raw.lower()

#                 # ❌ Skip unit prices
#                 bad_words = [
#                     "/count",
#                     "/ count",
#                     "/oz",
#                     "/ oz",
#                     "per count",
#                     "each",
#                     "subscribe",
#                     "delivery",
#                     "coupon",
#                     "off"
#                 ]

#                 if any(b in low for b in bad_words):
#                     continue

#                 value = clean_price(raw)

#                 # sanity checks
#                 if value > 0 and value < 100000:
#                     return value

#         except:
#             continue

#     # fallback method
#     try:
#         whole = card.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
#         fraction = "00"

#         try:
#             fraction = card.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
#         except:
#             pass

#         raw = f"{whole}.{fraction}"

#         value = clean_price(raw)

#         if value > 0:
#             return value

#     except:
#         pass

#     return 0.0



# def extract_list_price(card, live_price: float) -> float:
#     """
#     Label-aware list/typical/was/MRP extraction + strikethrough fallback.
#     Search *inside card only*.
#     """
#     # Strategy A: label-aware (Typical price / List price / Was / M.R.P.)
#     try:
#         label_words = ["typical price", "list price", "was", "m.r.p", "m.r.p."]

#         # Look for label anywhere, then nearest offscreen $ after it
#         # Note: XPath against the card element
#         for lab in label_words:
#             xp_label = (
#                 ".//*[contains(translate(normalize-space(.),"
#                 " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
#                 f" '{lab}')]"
#             )
#             try:
#                 label_els = card.find_elements(By.XPATH, xp_label)
#             except:
#                 label_els = []

#             if label_els:
#                 # nearest price after first label occurrence
#                 xps = [
#                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
#                     xp_label + "/following::*[contains(text(),'$') or contains(text(),'£') or contains(text(),'€') or contains(text(),'₹')][1]",
#                 ]
#                 for xp in xps:
#                     try:
#                         el = card.find_element(By.XPATH, xp)
#                         raw = el.get_attribute("textContent") or el.text
#                         val = clean_price(raw)
#                         if val > 0 and (live_price <= 0 or val >= live_price):
#                             # sanity: list should not be tiny compared to live
#                             if live_price > 0:
#                                 if val - live_price >= 0.25 and val <= live_price * 10:
#                                     return val
#                             else:
#                                 return val
#                     except:
#                         pass
#     except:
#         pass

#     # Strategy B: strikethrough price blocks
#     list_selectors = [
#         "span.a-price.a-text-price span.a-offscreen",
#         "span[data-a-strike='true'] span.a-offscreen",
#         "span.a-text-price span.a-offscreen",
#     ]
#     for sel in list_selectors:
#         try:
#             el = card.find_element(By.CSS_SELECTOR, sel)
#             raw = el.get_attribute("textContent") or el.text
#             low = (raw or "").lower()
#             # skip unit prices
#             if any(w in low for w in [" per ", "/count", "/ count", "/oz", "/ oz", "fl oz", "each", "item"]):
#                 continue

#             val = clean_price(raw)
#             if val > 0 and (live_price <= 0 or val > live_price):
#                 if live_price > 0:
#                     if val - live_price >= 0.25 and val <= live_price * 10:
#                         return val
#                 else:
#                     return val
#         except:
#             continue

#     return 0.0


# def extract_reviews(card) -> int:
#     try:
#         el = card.find_element(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
#         txt = (el.get_attribute("textContent") or el.text or "").strip()
#         # keep digits only
#         n = re.sub(r"[^\d]", "", txt.replace(",", ""))
#         return int(n) if n else 0
#     except:
#         return 0


# def extract_rating(card) -> float:
#     try:
#         el = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
#         txt = (el.get_attribute("textContent") or el.text or "").strip()
#         m = re.search(r"(\d+[.,]\d+|\d+)", txt)
#         if m:
#             return float(m.group(1).replace(",", "."))
#         return 0.0
#     except:
#         return 0.0


# def extract_sales(card) -> tuple[int, str]:
#     """
#     Returns (sales_int, raw_text_used).
#     Scans all secondary text spans because Amazon moves it around.
#     """
#     try:
#         spans = card.find_elements(By.CSS_SELECTOR, "span.a-size-base.a-color-secondary")
#         for sp in spans:
#             raw = (sp.get_attribute("textContent") or sp.text or "").strip()
#             s = parse_bought_sales(raw)
#             if s > 0:
#                 return s, raw
#     except:
#         pass
#     return 0, ""


# def extract_card_data(card):
#     """Extract all data from a search result card. Returns dict or None."""
#     asin = ""
#     try:
#         asin = (card.get_attribute("data-asin") or "").strip()
#     except:
#         asin = ""

#     # Skip non-product blocks
#     if not asin:
#         return None

#     data = {}
#     data["ASIN"] = asin

#     # Title
#     data["Title"] = extract_title(card)

#     # Link
#     data["Link"] = extract_link(card)

#     # Price
#     data["Price"] = extract_price(card)

#     # List price / typical / was
#     # data["List Price"] = extract_list_price(card, data["Price"])

#     # Extract list price
#     list_price = extract_list_price(card, data["Price"])

#     # If no list price found, use actual price
#     if list_price <= 0:
#         list_price = data["Price"]

#     data["List Price"] = extract_list_price(card, data["Price"])


#     # Discount
#     # if data["List Price"] > 0 and data["Price"] > 0 and data["List Price"] >= data["Price"]:
#     #     diff = data["List Price"] - data["Price"]
#     #     data["Discount %"] = int(round((diff / data["List Price"]) * 100))
#     # else:
#     #     data["Discount %"] = 0

#     if (
#             data["List Price"] > 0
#             and data["Price"] > 0
#             and data["List Price"] > data["Price"]
#     ):
#         diff = data["List Price"] - data["Price"]
#         data["Discount %"] = int(round((diff / data["List Price"]) * 100))
#     else:
#         data["Discount %"] = 0

#     # Reviews + Rating
#     data["Reviews"] = extract_reviews(card)
#     data["Rating"] = extract_rating(card)

#     # Sales (Bought...)
#     sales, sales_raw = extract_sales(card)
#     data["Sales"] = sales
#     if show_sales_raw:
#         data["Sales Raw"] = sales_raw

#     return data


# def get_csv_download_link(df):
#     csv = df.to_csv(index=False).encode("utf-8")
#     b64 = base64.b64encode(csv).decode()
#     return (
#         f'<a href="data:file/csv;base64,{b64}" download="amazon_hunter_results.csv" '
#         f'style="text-decoration:none;background:#232F3E;color:white;padding:12px;'
#         f'border-radius:6px;display:block;text-align:center;font-weight:bold;">'
#         f'💾 Download Full Results CSV</a>'
#     )


# # ==========================================
# # 🏃 RUN LOGIC
# # ==========================================
# if start_btn:
#     if not search_term:
#         st.error("❌ Please enter a keyword or select a category.")
#     else:
#         seen_asins.clear()

#         status_area.info(f"🚀 Initializing Browser for {selected_country_name}...")
#         driver = get_driver()
#         change_location(driver, zip_code, BASE_URL)

#         search_query = search_term.replace(" ", "+")
#         target_url = f"{BASE_URL}/s?k={search_query}&s=exact-aware-popularity-rank"

#         driver.get(target_url)
#         time.sleep(2.2)

#         scan_limit = 3000
#         scanned_count = 0
#         all_winning_products = []
#         page_num = 1

#         status_text = st.empty()
#         results_placeholder = st.empty()
#         prog = st.progress(0)

#         while scanned_count < scan_limit:
#             handle_blocking(driver)
#             status_text.write(f"🔎 Scanning Page {page_num}... (scrolling)")
#             smart_scroll(driver)

#             cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")

#             if not cards:
#                 status_text.warning("⚠️ Empty page. Retrying refresh...")
#                 driver.refresh()
#                 time.sleep(3.5)
#                 smart_scroll(driver)
#                 cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
#                 if not cards:
#                     break

#             status_text.write(f"🧪 Processing {len(cards)} cards on Page {page_num}... (Scanned: {scanned_count})")

#             for card in cards:
#                 if scanned_count >= scan_limit:
#                     break

#                 item = extract_card_data(card)
#                 if not item:
#                     continue

#                 if item["ASIN"] in seen_asins:
#                     continue

#                 seen_asins.add(item["ASIN"])
#                 scanned_count += 1

#                 # skip if no valid price
#                 if item["Price"] <= 0:
#                     continue

#                 # ✅ CRITERIA CHECK (STRICT)
#                 passes_criteria = True

#                 if not (min_price <= item["Price"] <= max_price):
#                     passes_criteria = False

#                 if item["Rating"] < min_rating:
#                     passes_criteria = False

#                 if item["Sales"] < min_sales:
#                     passes_criteria = False

#                 if passes_criteria:
#                     all_winning_products.append(item)

#                 # live display
#                 if all_winning_products and (scanned_count % 30 == 0):
#                     df_temp = pd.DataFrame(all_winning_products)
#                     results_placeholder.dataframe(
#                         df_temp.tail(8),
#                         column_config={
#                             "Link": st.column_config.LinkColumn("Product"),
#                             "Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
#                             "List Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
#                             "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
#                         },
#                         use_container_width=True,
#                     )

#                 prog.progress(min(scanned_count / scan_limit, 1.0))

#             if scanned_count >= scan_limit:
#                 break

#             # next page
#             try:
#                 handle_blocking(driver)
#                 next_btn = WebDriverWait(driver, 6).until(
#                     EC.element_to_be_clickable((By.CSS_SELECTOR, "a.s-pagination-next"))
#                 )
#                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
#                 time.sleep(0.8)
#                 next_btn.click()
#                 page_num += 1
#                 time.sleep(random.uniform(2.2, 4.0))
#             except:
#                 st.warning("⚠️ Reached end of results (No more pages).")
#                 break

#         driver.quit()

#         # Final dedupe safety net (should already be clean)
#         if all_winning_products:
#             seen_final = set()
#             unique_products = []
#             for p in all_winning_products:
#                 if p["ASIN"] not in seen_final:
#                     seen_final.add(p["ASIN"])
#                     unique_products.append(p)
#             all_winning_products = unique_products

#         status_area.success("🎉 Hunt Complete!")

#         if all_winning_products:
#             df = pd.DataFrame(all_winning_products)

#             desired_order = ["ASIN", "Title", "Price", "List Price", "Discount %", "Rating", "Reviews", "Sales"]
#             if show_sales_raw:
#                 desired_order.append("Sales Raw")
#             desired_order.append("Link")

#             df = df[[c for c in desired_order if c in df.columns]]

#             st.subheader(f"✅ Found {len(all_winning_products)} Winning Products")
#             st.dataframe(
#                 df,
#                 column_config={
#                     "Link": st.column_config.LinkColumn("Link"),
#                     "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
#                     "Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
#                     "List Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
#                 },
#                 use_container_width=True,
#             )
#             st.markdown(get_csv_download_link(df), unsafe_allow_html=True)
#         else:
#             st.error(f"😔 Scanned {scanned_count} items but found 0 matches. Try lowering the sales criteria.")


###################################Latest Code

import streamlit as st
import pandas as pd
import time
import random
import re
import base64

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==========================================
# 🛡️ DEDUPLICATION TRACKER
# ==========================================
seen_asins = set()


# ==========================================
# 🎨 FRONTEND CONFIG & CSS
# ==========================================
st.set_page_config(page_title="Amazon Global Hunter Pro", page_icon="🕵️‍♂️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; color: #232F3E; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #FF9900; }
    </style>
""", unsafe_allow_html=True)

st.title("🕵️‍♂️ Amazon Global Hunter Pro (Final)")

# ==========================================
# 🌍 COUNTRY & MARKETPLACE DATABASE
# ==========================================
COUNTRY_SETTINGS = {
    "United States 🇺🇸": {"url": "https://www.amazon.com", "symbol": "$", "currency": "USD"},
    "Canada 🇨🇦": {"url": "https://www.amazon.ca", "symbol": "C$", "currency": "CAD"},
    "Australia 🇦🇺": {"url": "https://www.amazon.com.au", "symbol": "A$", "currency": "AUD"},
    "United Kingdom 🇬🇧": {"url": "https://www.amazon.co.uk", "symbol": "£", "currency": "GBP"},
    "Germany 🇩🇪": {"url": "https://www.amazon.de", "symbol": "€", "currency": "EUR"},
    "France 🇫🇷": {"url": "https://www.amazon.fr", "symbol": "€", "currency": "EUR"},
    "Italy 🇮🇹": {"url": "https://www.amazon.it", "symbol": "€", "currency": "EUR"},
    "Spain 🇪🇸": {"url": "https://www.amazon.es", "symbol": "€", "currency": "EUR"},
    "India 🇮🇳": {"url": "https://www.amazon.in", "symbol": "₹", "currency": "INR"},
}

LOCATION_PRESETS = {
    "https://www.amazon.com": {
        "New York, NY": "10001", "Los Angeles, CA": "90001",
        "Chicago, IL": "60601", "Houston, TX": "77001", "Miami, FL": "33101",
    },
    "https://www.amazon.ca": {
        "Toronto": "M5V 2T6", "Vancouver": "V6B 1A1",
        "Montreal": "H2Y 1C6", "Calgary": "T2P 1J9", "Ottawa": "K1P 1J1",
    },
    "https://www.amazon.com.au": {
        "Sydney": "2000", "Melbourne": "3000", "Brisbane": "4000",
        "Perth": "6000", "Adelaide": "5000",
    },
    "https://www.amazon.co.uk": {
        "London": "SW1A 1AA", "Birmingham": "B1 1AA", "Manchester": "M1 1AA",
        "Liverpool": "L1 1AA", "Leeds": "LS1 1UR",
    },
    "https://www.amazon.de": {
        "Berlin": "10115", "Munich": "80331", "Hamburg": "20095", "Frankfurt": "60311",
    },
    "https://www.amazon.fr": {"Paris": "75001", "Lyon": "69001", "Marseille": "13001"},
    "https://www.amazon.it": {"Rome": "00100", "Milan": "20121", "Naples": "80100"},
    "https://www.amazon.es": {"Madrid": "28001", "Barcelona": "08001", "Valencia": "46001"},
    "https://www.amazon.in": {"New Delhi": "110001", "Mumbai": "400001", "Bengaluru": "560001"},
}

# ==========================================
# 📂 CATEGORY DATABASE
# ==========================================
CATEGORY_MAP = {
    "Home & Garden": ["Pest Control Products", "Garden Tools", "Planters", "Outdoor Lighting", "Gardening Gloves"],
    "Smart Home": ["Smart Plugs", "Smart Bulbs", "Security Cameras", "Video Doorbells", "Smart Thermostats"],
    "Household & Everyday": ["Cleaning Supplies", "Storage Bins", "Trash Bags", "Batteries", "Laundry Organizers"],
    "Bath & Decor": ["Bath Mats", "Shower Curtains", "Towel Racks", "Soap Dispensers", "Wall Art", "Mirrors"],
    "Tools & Home Improvement": ["Power Drills", "Screwdriver Sets", "Measuring Tapes", "Flashlights", "Tool Kits"],
    "Electronics & Mobile": ["Mobile Cases", "Screen Protectors", "Charging Cables", "Power Banks", "Headphones", "Phone Mounts"],
    "Personal Care": ["Electric Shavers", "Hair Dryers", "Oral Care", "Skin Care Tools", "Manicure Sets", "Massagers"],
    "Pet Supplies": ["Dog Toys", "Cat Scratchers", "Pet Beds", "Dog Leashes", "Grooming Tools", "Aquarium Supplies"],
    "Sports & Outdoors": ["Yoga Mats", "Resistance Bands", "Camping Gear", "Water Bottles", "Gym Gloves", "Flashlights"],
    "Toys & Games": ["Outdoor Toys", "Board Games", "Building Blocks", "Educational Toys", "Puzzles"],
    "Baby Accessories": ["Diaper Bags", "Baby Monitors", "Stroller Organizers", "Teething Toys", "Bibs"],
    "Automotive": ["Car Organizers", "Car Vacuums", "Phone Mounts", "Car Cleaning Kits", "Seat Covers", "Air Fresheners"],
    "Office & Stationery": ["Notebooks", "Pens", "Desk Organizers", "Sticky Notes", "File Holders"],
}

# ==========================================
# ⚙️ SIDEBAR - CRITERIA
# ==========================================
st.sidebar.header("1. Marketplace")
selected_country_name = st.sidebar.selectbox("Select Country", list(COUNTRY_SETTINGS.keys()))
current_config = COUNTRY_SETTINGS[selected_country_name]
BASE_URL = current_config["url"]
CURRENCY = current_config["symbol"]
AMAZON_CURRENCY = current_config["currency"]

st.sidebar.header("2. Criteria")
min_price = st.sidebar.number_input(f"Min Price ({CURRENCY})", value=10.0)
max_price = st.sidebar.number_input(f"Max Price ({CURRENCY})", value=200.0)
min_rating = st.sidebar.number_input("Min Rating", value=4.0)
min_sales = st.sidebar.number_input("Min Sales (Approx)", value=100)

st.sidebar.header("3. Location")
location_presets = LOCATION_PRESETS[BASE_URL]
location_choice = st.sidebar.selectbox(
    "Select City", list(location_presets) + ["Custom location..."]
)
if location_choice == "Custom location...":
    zip_code = st.sidebar.text_input(
        "Postal/Zip Code", placeholder="Enter your own postcode or ZIP code"
    ).strip()
else:
    zip_code = location_presets[location_choice]
    st.sidebar.caption(f"Selected code: {zip_code}")

st.sidebar.header("4. Debug")
show_sales_raw = st.sidebar.checkbox("Show Sales Raw Text (debug)", value=True)

# ==========================================
# 🔍 SEARCH INPUTS
# ==========================================
st.subheader(f"Search Settings ({selected_country_name})")

search_method = st.radio("How do you want to search?", ["Type Specific Keyword", "Select Category"], horizontal=True)

if search_method == "Type Specific Keyword":
    search_term = st.text_input("Enter Keyword", placeholder="e.g. Wireless charger")
else:
    c1, c2 = st.columns(2)
    with c1:
        main_cat = st.selectbox("Main Category", list(CATEGORY_MAP.keys()))
    with c2:
        sub_cat = st.selectbox("Sub-Category", CATEGORY_MAP[main_cat])
        search_term = sub_cat

st.markdown("---")
start_btn = st.button("🚀 Start Hunting (Scans All Available Items)", type="primary")
status_area = st.empty()


# ==========================================
# 🛠️ BACKEND LOGIC
# ==========================================

def get_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    # options.add_argument("--headless=new")  # you can enable if you want
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    return driver


def clean_price(price_str):
    if not price_str:
        return 0.0
    try:
        # 1. Remove unit prices like ($0.83 / count)
        s = str(price_str).split("(")[0]
        
        # 2. Extract only numbers and decimals/commas
        # Hum sirf digits, dots aur commas rakhen ge
        clean = re.sub(r"[^\d.,]", "", s)

        if not clean:
            return 0.0

        # 3. European format handle karna (e.g. 1.200,50 -> 1200.50)
        if "," in clean and "." in clean:
            if clean.rfind(",") > clean.rfind("."): # Comma decimal hai
                clean = clean.replace(".", "").replace(",", ".")
            else: # Dot decimal hai
                clean = clean.replace(",", "")
        elif "," in clean:
            # Agar sirf ek comma hai aur uske baad 2 digits hain to wo decimal hai
            parts = clean.split(",")
            if len(parts[-1]) == 2:
                clean = clean.replace(",", ".")
            else:
                clean = clean.replace(",", "")
        
        return float(clean)
    except:
        return 0.0

def smart_scroll(driver):
    """Slow scroll to trigger lazy loading."""
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    step = 650
    for y in range(1, total_height, step):
        driver.execute_script(f"window.scrollTo(0, {y});")
        time.sleep(0.12)
    time.sleep(0.7)


def handle_blocking(driver):
    """Click common anti-bot modals / region prompts where possible."""
    try:
        btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping') or contains(text(), 'Done')]")
        if not btns:
            btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
        for btn in btns:
            t = (btn.text or "").lower()
            if "continue" in t or "done" in t:
                btn.click()
                time.sleep(0.8)
                return True
    except:
        pass
    return False


def change_location(driver, zip_code, base_url):
    if not zip_code:
        st.warning("⚠️ No postal/ZIP code was selected.")
        return
    st.toast(f"✈️ Changing location to {zip_code}...")
    driver.get(base_url)
    time.sleep(2)
    handle_blocking(driver)
    try:
        driver.find_element(By.ID, "nav-global-location-popover-link").click()
        time.sleep(2)
        postal_code = re.sub(r"\s+", "", str(zip_code)).upper()
        split_inputs = [
            element
            for element in driver.find_elements(
                By.CSS_SELECTOR,
                "input[id*='GLUXZipUpdateInput'], input[id*='Postal'], "
                "input[name*='postal'], input[name*='zip']",
            )
            if element.is_displayed() and element.is_enabled()
        ]
        if len(split_inputs) >= 2 and len(postal_code) >= 6:
            split_inputs[0].clear()
            split_inputs[0].send_keys(postal_code[:3])
            split_inputs[1].clear()
            split_inputs[1].send_keys(postal_code[3:6])
        else:
            zip_input = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput"))
            )
            zip_input.clear()
            zip_input.send_keys(zip_code)
        time.sleep(0.7)
        driver.find_element(By.ID, "GLUXZipUpdate").click()
        time.sleep(1.0)
        try:
            driver.find_element(By.NAME, "glowDoneButton").click()
        except:
            handle_blocking(driver)
        time.sleep(2)
        st.toast("✅ Location Updated!")
    except Exception as error:
        st.warning(f"⚠️ Auto-location failed. Proceeding anyway: {str(error)[:80]}")


def set_amazon_currency(driver, base_url, currency_code):
    """Force Amazon to show prices in the selected marketplace currency."""
    try:
        domain = base_url.replace("https://", "").split("/")[0]
        driver.get(base_url)
        time.sleep(2)
        driver.add_cookie({
            "name": "i18n-prefs",
            "value": currency_code,
            "domain": f".{domain}",
        })
        driver.refresh()
        time.sleep(2)
        st.toast(f"✅ Currency set to {currency_code}")
    except Exception as error:
        st.warning(f"⚠️ Could not set Amazon currency: {str(error)[:80]}")


def parse_bought_sales(raw_text: str) -> int:
    """
    Parses:
      '2K+ bought in past month' -> 2000
      '40K+ bought...' -> 40000
      '5,000 bought...' -> 5000
      '1.5K bought...' -> 1500
      '1,5K bought...' -> 1500
    Only multiplies when K is attached to the number.
    """
    if not raw_text:
        return 0
    t = raw_text.strip()
    low = t.lower()
    if "bought" not in low:
        return 0

    # number + optional decimal + optional K right next to it, then bought
    m = re.search(r"(\d{1,3}(?:[.,]\d{1,2})?)(\s*[kK])?\+?\s*bought", t)
    if m:
        num_str = m.group(1)

        # normalize decimals: "1,5" -> "1.5"
        if "," in num_str and "." not in num_str:
            num_str = num_str.replace(",", ".")
        else:
            num_str = num_str.replace(",", "")

        try:
            num = float(num_str)
        except:
            return 0

        has_k = m.group(2) is not None
        return int(num * 1000) if has_k else int(num)

    # fallback plain integer before bought
    m2 = re.search(r"(\d[\d,]*)\+?\s*bought", t)
    if m2:
        try:
            return int(m2.group(1).replace(",", ""))
        except:
            return 0

    return 0


def extract_title(card) -> str:
    """Multi-selector title extraction (kills 'Unknown' most of the time)."""
    selectors = [
        "h2 a span",
        "h2 span",
        "span.a-size-medium.a-color-base.a-text-normal",
        "span.a-size-base-plus.a-color-base.a-text-normal",
        "h2.a-size-mini span",
        "a.a-link-normal span",
        "a.a-link-normal"
    ]
    for sel in selectors:
        try:
            el = card.find_element(By.CSS_SELECTOR, sel)
            txt = (el.get_attribute("textContent") or el.text or "").strip()
            if txt and len(txt) > 5:
                return txt
        except:
            continue
    return "Unknown"


def extract_link(card) -> str:
    """Best effort: get product link from the title anchor."""
    link_selectors = [
        "h2 a.a-link-normal",
        "a.a-link-normal.s-no-outline",
        "h2 a",
    ]
    for sel in link_selectors:
        try:
            a = card.find_element(By.CSS_SELECTOR, sel)
            href = a.get_attribute("href")
            if href:
                if href.startswith("/"):
                    return BASE_URL + href
                return href
        except:
            continue
    return "No Link"



# def extract_price(card) -> float:
#     # In selectors ko priority wise check kiya jayega
#     price_selectors = [
#         "span.a-price span.a-offscreen",
#         "span.a-price-whole",
#         "span.a-color-price",
#         ".a-size-base.a-color-price"
#     ]
#
#     for sel in price_selectors:
#         try:
#             el = card.find_element(By.CSS_SELECTOR, sel)
#             raw = el.get_attribute("textContent") or el.text
#             if raw:
#                 val = clean_price(raw)
#                 if val > 0:
#                     return val
#         except:
#             continue
#
#     # Fallback: Agar upar wala fail ho jaye to Whole aur Fraction ko mila kar check karein
#     try:
#         whole = card.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
#         try:
#             fraction = card.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
#         except:
#             fraction = "00"
#
#         raw = f"{whole}.{fraction}"
#         return clean_price(raw)
#     except:
#         return 0.0


def extract_price(card) -> float:
    """
    Extract the REAL live selling price only.
    Avoids:
    - unit prices
    - subscription prices
    - struck prices
    - coupon values
    """

    # Priority selectors for CURRENT LIVE PRICE
    selectors = [
        "span.a-price:not(.a-text-price) span.a-offscreen",
        ".a-price.aok-align-center span.a-offscreen",
        ".a-price-range span.a-offscreen",
    ]

    for sel in selectors:
        try:
            elements = card.find_elements(By.CSS_SELECTOR, sel)

            for el in elements:
                raw = (el.get_attribute("textContent") or el.text or "").strip()

                if not raw:
                    continue

                low = raw.lower()

                # ❌ Skip unit prices
                bad_words = [
                    "/count",
                    "/ count",
                    "/oz",
                    "/ oz",
                    "per count",
                    "each",
                    "subscribe",
                    "delivery",
                    "coupon",
                    "off"
                ]

                if any(b in low for b in bad_words):
                    continue

                value = clean_price(raw)

                # sanity checks
                if value > 0 and value < 100000:
                    return value

        except:
            continue

    # fallback method
    try:
        whole = card.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
        fraction = "00"

        try:
            fraction = card.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
        except:
            pass

        raw = f"{whole}.{fraction}"

        value = clean_price(raw)

        if value > 0:
            return value

    except:
        pass

    return 0.0



def extract_list_price(card, live_price: float) -> float:
    """
    Label-aware list/typical/was/MRP extraction + strikethrough fallback.
    Search *inside card only*.
    """
    # Strategy A: label-aware (Typical price / List price / Was / M.R.P.)
    try:
        label_words = ["typical price", "list price", "was", "m.r.p", "m.r.p."]

        # Look for label anywhere, then nearest offscreen $ after it
        # Note: XPath against the card element
        for lab in label_words:
            xp_label = (
                ".//*[contains(translate(normalize-space(.),"
                " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
                f" '{lab}')]"
            )
            try:
                label_els = card.find_elements(By.XPATH, xp_label)
            except:
                label_els = []

            if label_els:
                # nearest price after first label occurrence
                xps = [
                    xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
                    xp_label + "/following::*[contains(text(),'$') or contains(text(),'£') or contains(text(),'€') or contains(text(),'₹')][1]",
                ]
                for xp in xps:
                    try:
                        el = card.find_element(By.XPATH, xp)
                        raw = el.get_attribute("textContent") or el.text
                        val = clean_price(raw)
                        if val > 0 and (live_price <= 0 or val >= live_price):
                            # sanity: list should not be tiny compared to live
                            if live_price > 0:
                                if val - live_price >= 0.25 and val <= live_price * 10:
                                    return val
                            else:
                                return val
                    except:
                        pass
    except:
        pass

    # Strategy B: strikethrough price blocks
    list_selectors = [
        "span.a-price.a-text-price span.a-offscreen",
        "span[data-a-strike='true'] span.a-offscreen",
        "span.a-text-price span.a-offscreen",
    ]
    for sel in list_selectors:
        try:
            el = card.find_element(By.CSS_SELECTOR, sel)
            raw = el.get_attribute("textContent") or el.text
            low = (raw or "").lower()
            # skip unit prices
            if any(w in low for w in [" per ", "/count", "/ count", "/oz", "/ oz", "fl oz", "each", "item"]):
                continue

            val = clean_price(raw)
            if val > 0 and (live_price <= 0 or val > live_price):
                if live_price > 0:
                    if val - live_price >= 0.25 and val <= live_price * 10:
                        return val
                else:
                    return val
        except:
            continue

    return 0.0


def extract_reviews(card) -> int:
    try:
        el = card.find_element(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
        txt = (el.get_attribute("textContent") or el.text or "").strip()
        # keep digits only
        n = re.sub(r"[^\d]", "", txt.replace(",", ""))
        return int(n) if n else 0
    except:
        return 0


def extract_rating(card) -> float:
    try:
        el = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
        txt = (el.get_attribute("textContent") or el.text or "").strip()
        m = re.search(r"(\d+[.,]\d+|\d+)", txt)
        if m:
            return float(m.group(1).replace(",", "."))
        return 0.0
    except:
        return 0.0


def extract_sales(card) -> tuple[int, str]:
    """
    Returns (sales_int, raw_text_used).
    Scans all secondary text spans because Amazon moves it around.
    """
    try:
        spans = card.find_elements(By.CSS_SELECTOR, "span.a-size-base.a-color-secondary")
        for sp in spans:
            raw = (sp.get_attribute("textContent") or sp.text or "").strip()
            s = parse_bought_sales(raw)
            if s > 0:
                return s, raw
    except:
        pass
    return 0, ""


def extract_card_data(card):
    """Extract all data from a search result card. Returns dict or None."""
    asin = ""
    try:
        asin = (card.get_attribute("data-asin") or "").strip()
    except:
        asin = ""

    # Skip non-product blocks
    if not asin:
        return None

    data = {}
    data["ASIN"] = asin

    # Title
    data["Title"] = extract_title(card)

    # Link
    data["Link"] = extract_link(card)

    # Price
    data["Price"] = extract_price(card)

    # List price / typical / was
    # data["List Price"] = extract_list_price(card, data["Price"])

    # Extract list price
    list_price = extract_list_price(card, data["Price"])

    # If no list price found, use actual price
    if list_price <= 0:
        list_price = data["Price"]

    data["List Price"] = extract_list_price(card, data["Price"])


    # Discount
    # if data["List Price"] > 0 and data["Price"] > 0 and data["List Price"] >= data["Price"]:
    #     diff = data["List Price"] - data["Price"]
    #     data["Discount %"] = int(round((diff / data["List Price"]) * 100))
    # else:
    #     data["Discount %"] = 0

    if (
            data["List Price"] > 0
            and data["Price"] > 0
            and data["List Price"] > data["Price"]
    ):
        diff = data["List Price"] - data["Price"]
        data["Discount %"] = int(round((diff / data["List Price"]) * 100))
    else:
        data["Discount %"] = 0

    # Reviews + Rating
    data["Reviews"] = extract_reviews(card)
    data["Rating"] = extract_rating(card)

    # Sales (Bought...)
    sales, sales_raw = extract_sales(card)
    data["Sales"] = sales
    if show_sales_raw:
        data["Sales Raw"] = sales_raw

    return data


def get_csv_download_link(df):
    csv = df.to_csv(index=False).encode("utf-8")
    b64 = base64.b64encode(csv).decode()
    return (
        f'<a href="data:file/csv;base64,{b64}" download="amazon_hunter_results.csv" '
        f'style="text-decoration:none;background:#232F3E;color:white;padding:12px;'
        f'border-radius:6px;display:block;text-align:center;font-weight:bold;">'
        f'💾 Download Full Results CSV</a>'
    )


# ==========================================
# 🏃 RUN LOGIC
# ==========================================
if start_btn:
    if not search_term:
        st.error("❌ Please enter a keyword or select a category.")
    else:
        seen_asins.clear()

        status_area.info(f"🚀 Initializing Browser for {selected_country_name}...")
        driver = get_driver()
        set_amazon_currency(driver, BASE_URL, AMAZON_CURRENCY)
        change_location(driver, zip_code, BASE_URL)

        search_query = search_term.replace(" ", "+")
        target_url = f"{BASE_URL}/s?k={search_query}&s=exact-aware-popularity-rank"

        driver.get(target_url)
        time.sleep(2.2)

        scan_limit = 3000
        scanned_count = 0
        all_winning_products = []
        page_num = 1

        status_text = st.empty()
        results_placeholder = st.empty()
        prog = st.progress(0)

        while scanned_count < scan_limit:
            handle_blocking(driver)
            status_text.write(f"🔎 Scanning Page {page_num}... (scrolling)")
            smart_scroll(driver)

            cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")

            if not cards:
                status_text.warning("⚠️ Empty page. Retrying refresh...")
                driver.refresh()
                time.sleep(3.5)
                smart_scroll(driver)
                cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
                if not cards:
                    break

            status_text.write(f"🧪 Processing {len(cards)} cards on Page {page_num}... (Scanned: {scanned_count})")

            for card in cards:
                if scanned_count >= scan_limit:
                    break

                item = extract_card_data(card)
                if not item:
                    continue

                if item["ASIN"] in seen_asins:
                    continue

                seen_asins.add(item["ASIN"])
                scanned_count += 1

                # skip if no valid price
                if item["Price"] <= 0:
                    continue

                # ✅ CRITERIA CHECK (STRICT)
                passes_criteria = True

                if not (min_price <= item["Price"] <= max_price):
                    passes_criteria = False

                if item["Rating"] < min_rating:
                    passes_criteria = False

                if item["Sales"] < min_sales:
                    passes_criteria = False

                if passes_criteria:
                    all_winning_products.append(item)

                # live display
                if all_winning_products and (scanned_count % 30 == 0):
                    df_temp = pd.DataFrame(all_winning_products)
                    results_placeholder.dataframe(
                        df_temp.tail(8),
                        column_config={
                            "Link": st.column_config.LinkColumn("Product"),
                            "Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
                            "List Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
                            "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
                        },
                        use_container_width=True,
                    )

                prog.progress(min(scanned_count / scan_limit, 1.0))

            if scanned_count >= scan_limit:
                break

            # next page
            try:
                handle_blocking(driver)
                next_btn = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.s-pagination-next"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                time.sleep(0.8)
                next_btn.click()
                page_num += 1
                time.sleep(random.uniform(2.2, 4.0))
            except:
                st.warning("⚠️ Reached end of results (No more pages).")
                break

        driver.quit()

        # Final dedupe safety net (should already be clean)
        if all_winning_products:
            seen_final = set()
            unique_products = []
            for p in all_winning_products:
                if p["ASIN"] not in seen_final:
                    seen_final.add(p["ASIN"])
                    unique_products.append(p)
            all_winning_products = unique_products

        status_area.success("🎉 Hunt Complete!")

        if all_winning_products:
            df = pd.DataFrame(all_winning_products)

            desired_order = ["ASIN", "Title", "Price", "List Price", "Discount %", "Rating", "Reviews", "Sales"]
            if show_sales_raw:
                desired_order.append("Sales Raw")
            desired_order.append("Link")

            df = df[[c for c in desired_order if c in df.columns]]

            st.subheader(f"✅ Found {len(all_winning_products)} Winning Products")
            st.dataframe(
                df,
                column_config={
                    "Link": st.column_config.LinkColumn("Link"),
                    "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
                    "Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
                    "List Price": st.column_config.NumberColumn(format=f"{CURRENCY}%.2f"),
                },
                use_container_width=True,
            )
            st.markdown(get_csv_download_link(df), unsafe_allow_html=True)
        else:
            st.error(f"😔 Scanned {scanned_count} items but found 0 matches. Try lowering the sales criteria.")
