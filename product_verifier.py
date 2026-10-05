


# # import streamlit as st
# # import pandas as pd
# # import time
# # import random
# # import re
# # import base64
# # from selenium import webdriver
# # from selenium.webdriver.chrome.service import Service
# # from selenium.webdriver.chrome.options import Options
# # from selenium.webdriver.common.by import By
# # from selenium.webdriver.support.ui import WebDriverWait
# # from selenium.webdriver.support import expected_conditions as EC
# # from webdriver_manager.chrome import ChromeDriverManager

# # # ================= 1. INITIALIZATION & SESSION STATE =================
# # # Ye variables scan khatam hone ke baad bhi data ko save rakhte hain
# # if 'final_df' not in st.session_state:
# #     st.session_state.final_df = None
# # if 'is_scanning' not in st.session_state:
# #     st.session_state.is_scanning = False

# # # ================= 2. APP CONFIGURATION & CSS =================
# # st.set_page_config(
# #     page_title="Amazon Intelligence Pro",
# #     page_icon="🛒",
# #     layout="wide"
# # )

# # # Professional UI Styling
# # st.markdown("""
# #     <style>
# #     .stApp { background-color: #f8f9fa; }
# #     div[data-testid="stMetricValue"] { font-size: 1.4rem; color: #232F3E; font-weight: bold; }
# #     div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #555; }
# #     .stProgress > div > div > div > div { background-color: #FF9900; }
# #     .custom-dl-btn {
# #         display: inline-block; padding: 0.8em 1.5em; margin: 10px 0;
# #         border-radius: 0.4em; text-decoration: none; font-family: 'Roboto',sans-serif;
# #         font-weight: 600; color: #FFFFFF !important; background-color: #232F3E;
# #         text-align: center; transition: all 0.2s; width: 100%; border: 1px solid #232F3E;
# #     }
# #     .custom-dl-btn:hover { background-color: #FF9900; border-color: #FF9900; color: white !important; }
# #     </style>
# # """, unsafe_allow_html=True)

# # # ================= 3. CORE BACKEND SCRAPER LOGIC =================

# # def get_driver():
# #     options = Options()
# #     options.add_argument("--start-maximized")
# #     options.add_argument("--disable-gpu")
# #     options.add_argument("--no-sandbox")
# #     options.add_argument("--disable-dev-shm-usage")
# #     options.add_argument("--disable-blink-features=AutomationControlled")
# #     options.page_load_strategy = 'eager'
# #     # Use standard User-Agent to avoid early detection
# #     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
# #     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# #     return driver

# # def clean_price(price_str):
# #     """
# #     STRICT PRICE CLEANER:
# #     Splits text at '(' to discard unit prices like ($0.83 / count).
# #     """
# #     try:
# #         if pd.isna(price_str) or str(price_str).strip() == "": return None
# #         # Split at parenthesis to remove unit info
# #         clean_str = str(price_str).split('(')[0]
# #         # Remove currency symbols and non-numeric chars except dot
# #         clean_str = re.sub(r'[^\d.]', '', clean_str)
# #         if clean_str.count('.') > 1:
# #             parts = clean_str.split('.')
# #             clean_str = f"{parts[0]}.{parts[1]}"
# #         return float(clean_str)
# #     except:
# #         return None

# # def handle_blocking(driver):
# #     """Attempts to click 'Continue shopping' if blocked."""
# #     try:
# #         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping')]")
# #         if not btns:
# #             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
# #         for btn in btns:
# #             if "continue" in btn.text.lower():
# #                 btn.click()
# #                 time.sleep(1.5)
# #                 return True
# #     except:
# #         pass
# #     return False

# # def change_location(driver, zip_code):
# #     """Changes Amazon shipping location to target ZIP."""
# #     try:
# #         driver.get("https://www.amazon.com")
# #         handle_blocking(driver)
# #         try:
# #             WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
# #         except:
# #             return False
# #         time.sleep(1)
# #         try:
# #             input_box = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
# #             input_box.clear()
# #             input_box.send_keys(zip_code)
# #             driver.find_element(By.ID, "GLUXZipUpdate").click()
# #             time.sleep(1)
# #             # Confirm close if needed
# #             try:
# #                 driver.find_element(By.CSS_SELECTOR, "div.a-popover-footer input, #GLUXConfirmClose").click()
# #             except:
# #                 pass
# #             time.sleep(2)
# #             return True
# #         except:
# #             return False
# #     except:
# #         return False

# # def _find_labeled_price_in_box(price_box, labels):
# #     """Extracts specific price types (List, Typical, Was) using text labels."""
# #     for lab in labels:
# #         xp_label = (
# #             ".//*[contains(translate(normalize-space(.),"
# #             " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
# #             f" '{lab}')]"
# #         )
# #         try:
# #             label_els = price_box.find_elements(By.XPATH, xp_label)
# #             for _ in label_els:
# #                 xps = [
# #                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
# #                     xp_label + "/following::*[contains(text(),'$')][1]",
# #                 ]
# #                 for xp in xps:
# #                     try:
# #                         el = price_box.find_element(By.XPATH, xp)
# #                         raw = el.get_attribute("innerHTML") or el.text
# #                         val = clean_price(raw)
# #                         if val and val > 1.0:
# #                             return val
# #                     except: pass
# #         except: pass
# #     return None

# # def scrape_item(driver, url, current_zip):
# #     """Main function to scrape specific product data."""
# #     data = {
# #         "Title": "Error", "Live Price": None, "List Price": None, "Discount %": "0%",
# #         "Strategy": "Unknown", "BSR": "N/A", "Stock": "Unknown", "Rating": "N/A",
# #         "Reviews": 0, "Zip Used": current_zip, "Status": "Failed",
# #         "Has Images": "No", "Has Prime": "No", "Brand": "Unknown", "Seller Count": 0, "Verified": "❌"
# #     }

# #     try:
# #         driver.get(url)
# #         handle_blocking(driver)
# #         time.sleep(random.uniform(1.5, 3.0))

# #         # 1. Product Title
# #         try:
# #             data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:60] + "..."
# #             data["Status"] = "Success"
# #         except:
# #             data["Status"] = "Blocked/Captcha"
# #             return data

# #         # 2. Live Price (What you pay now)
# #         try:
# #             whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
# #             frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
# #             data["Live Price"] = float(f"{whole}.{frac}")
# #         except:
# #             try:
# #                 raw = driver.find_element(By.CSS_SELECTOR, "span.apexPriceToPay span.a-offscreen").get_attribute("innerHTML")
# #                 data["Live Price"] = clean_price(raw)
# #             except: pass

# #         # 3. List / Typical Price Logic
# #         try:
# #             price_containers = driver.find_elements(By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div, #corePrice_desktop_feature_div, #apex_desktop")
# #             labels = ["typical price", "list price", "was:", "m.r.p"]
# #             for box in price_containers:
# #                 found_val = _find_labeled_price_in_box(box, labels)
# #                 if found_val:
# #                     data["List Price"] = found_val
# #                     break
# #         except: pass

# #         # 4. Discount Percentage
# #         if data["Live Price"] and data["List Price"]:
# #             diff = data["List Price"] - data["Live Price"]
# #             if diff >= 0.20:
# #                 pct = round((diff / data["List Price"]) * 100)
# #                 data["Discount %"] = f"{pct}%"

# #         # 5. Stock Checking
# #         try:
# #             if driver.find_elements(By.ID, "add-to-cart-button") or driver.find_elements(By.ID, "buy-now-button"):
# #                 data["Stock"] = "In Stock"
# #             else:
# #                 data["Stock"] = "Out of Stock"
# #         except: data["Stock"] = "Unknown"

# #         # 6. Fulfillment Strategy
# #         try:
# #             merchant_text = driver.find_element(By.ID, "merchant-info").text.lower()
# #             if "amazon" in merchant_text: data["Strategy"] = "FBA"
# #             else: data["Strategy"] = "FBM"
# #         except: data["Strategy"] = "Unknown"

# #         # 7. BSR & Ratings
# #         try:
# #             body_text = driver.find_element(By.TAG_NAME, "body").text
# #             bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
# #             data["BSR"] = f"#{bsr_match.group(1)}" if bsr_match else "N/A"
            
# #             rating_el = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt")
# #             data["Rating"] = rating_el.get_attribute("innerHTML").split(" ")[0]
            
# #             rev_el = driver.find_element(By.ID, "acrCustomerReviewText")
# #             data["Reviews"] = rev_el.text.split(" ")[0]
# #         except: pass

# #         # 8. Product Verification Metrics
# #         if driver.find_elements(By.CSS_SELECTOR, "#altImages img, #main-image-container img"):
# #             data["Has Images"] = "Yes"
# #         if driver.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, span.a-icon-prime"):
# #             data["Has Prime"] = "Yes"
# #         try:
# #             brand_el = driver.find_element(By.ID, "bylineInfo")
# #             data["Brand"] = brand_el.text.replace("Visit the", "").replace("Store", "").strip()
# #         except: pass

# #         # 9. Seller Count
# #         try:
# #             s_text = driver.find_element(By.ID, "olp_feature_div").text
# #             s_match = re.search(r'(\d+)', s_text)
# #             if s_match: data["Seller Count"] = int(s_match.group(1))
# #         except: pass

# #         # FINAL VERIFICATION SCORE
# #         v_score = 0
# #         if data["Has Images"] == "Yes": v_score += 1
# #         if data["Live Price"] is not None: v_score += 1
# #         if data["Rating"] != "N/A": v_score += 1
# #         if data["Brand"] != "Unknown": v_score += 1
        
# #         if v_score >= 4: data["Verified"] = "✅"
# #         elif v_score >= 2: data["Verified"] = "⚠️"
# #         else: data["Verified"] = "❌"

# #     except Exception as e:
# #         data["Status"] = f"Error"
    
# #     return data

# # def get_csv_download_link(df, filename="amazon_results.csv"):
# #     """Generates a persistent base64 download link."""
# #     csv = df.to_csv(index=False)
# #     b64 = base64.b64encode(csv.encode()).decode()
# #     href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="custom-dl-btn">📥 DOWNLOAD CSV REPORT</a>'
# #     return href

# # # ================= 4. FRONTEND UI LOGIC =================

# # def main():
# #     st.sidebar.title("⚙️ Amazon Scraper Config")

# #     # PERSISTENT DOWNLOAD SECTION
# #     if st.session_state.final_df is not None:
# #         st.sidebar.success("✅ Results from last scan available")
# #         st.sidebar.markdown(get_csv_download_link(st.session_state.final_df), unsafe_allow_html=True)
# #         if st.sidebar.button("🗑️ Clear All Results"):
# #             st.session_state.final_df = None
# #             st.rerun()
    
# #     st.sidebar.divider()
    
# #     # Location Settings
# #     LOCATIONS = {
# #         "New York (10001)": "10001",
# #         "Beverly Hills (90210)": "90210",
# #         "Chicago (60601)": "60601",
# #         "Tax Free (19701)": "19701"
# #     }
# #     sel_loc = st.sidebar.selectbox("📍 Target Location", list(LOCATIONS.keys()))
# #     target_zip = LOCATIONS[sel_loc]

# #     # Filters
# #     st.sidebar.subheader("🎯 Scan Filters")
# #     min_disc = st.sidebar.slider("Min Discount %", 0, 90, 0)
# #     uploaded_file = st.sidebar.file_uploader("📂 Upload CSV/XLSX Product Link List", type=['xlsx', 'csv'])

# #     st.title("🛒 Amazon Intelligence Pro")
# #     st.info("Upload a file containing a column 'Product Link' to start scanning.")

# #     if uploaded_file:
# #         # Load Data
# #         if uploaded_file.name.endswith('.csv'):
# #             try: df = pd.read_csv(uploaded_file)
# #             except: df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
# #         else:
# #             df = pd.read_excel(uploaded_file)

# #         df.columns = df.columns.str.strip()
# #         if 'Product Link' not in df.columns:
# #             st.error("❌ Column 'Product Link' not found!")
# #             return

# #         # Setup Visual Columns
# #         c1, c2, c3, c4 = st.columns(4)
# #         m_scanned = c1.empty()
# #         m_stock = c2.empty()
# #         m_fba = c3.empty()
# #         m_disc = c4.empty()

# #         st.subheader("📡 Live Data Extraction")
# #         table_placeholder = st.empty()

# #         if st.sidebar.button("🚀 START SCAN", type="primary"):
# #             st.session_state.is_scanning = True
# #             results = []
# #             cnt_fba = 0
# #             cnt_disc = 0
# #             cnt_out = 0
            
# #             with st.status("Initializing Engine...", expanded=True) as status:
# #                 driver = get_driver()
                
# #                 # Step 1: Change Location
# #                 status.update(label=f"Setting location to {target_zip}...")
# #                 change_location(driver, target_zip)
                
# #                 # Step 2: Iterate Links
# #                 total = len(df)
# #                 prog_bar = st.progress(0)

# #                 for idx, row in df.iterrows():
# #                     url = row['Product Link']
# #                     if pd.isna(url) or "amazon" not in str(url): continue
                    
# #                     status.update(label=f"Scanning {idx+1}/{total}: {url[:40]}...")
                    
# #                     data = scrape_item(driver, url, target_zip)
                    
# #                     # Apply Discount Filter
# #                     d_val = int(data["Discount %"].replace('%', ''))
# #                     if d_val < min_disc:
# #                         continue

# #                     # Update Metrics
# #                     if data["Stock"] == "Out of Stock": cnt_out += 1
# #                     if data["Strategy"] == "FBA": cnt_fba += 1
# #                     if d_val > 0: cnt_disc += 1
                    
# #                     results.append(data)
# #                     st.session_state.final_df = pd.DataFrame(results) # Save to session

# #                     # Live UI Update
# #                     m_scanned.metric("Processed", f"{idx+1}/{total}")
# #                     m_stock.metric("Out Stock", cnt_out)
# #                     m_fba.metric("FBA Found", cnt_fba)
# #                     m_disc.metric("Discounts", cnt_disc)
                    
# #                     # Show last 10 rows
# #                     table_placeholder.dataframe(st.session_state.final_df.tail(10), use_container_width=True)
# #                     prog_bar.progress((idx+1)/total)

# #                 driver.quit() # EXIT AFTER LOOP
# #                 status.update(label="✅ Scan Complete!", state="complete")
            
# #             st.session_state.is_scanning = False
# #             st.success("Verification complete. Use the sidebar to download your CSV.")
# #             st.rerun() # Refresh to show final download button

# #     # Show full results if already scanned
# #     elif st.session_state.final_df is not None:
# #         st.subheader("📊 Last Scanned Results")
# #         st.dataframe(st.session_state.final_df, use_container_width=True)

# # if __name__ == "__main__":
# #     main()




# # import streamlit as st
# # import pandas as pd
# # import time
# # import random
# # import re
# # import base64
# # import sqlite3
# # import requests
# # import urllib3
# # import json
# # from selenium import webdriver
# # from selenium.webdriver.chrome.service import Service
# # from selenium.webdriver.chrome.options import Options
# # from selenium.webdriver.common.by import By
# # from selenium.webdriver.support.ui import WebDriverWait
# # from selenium.webdriver.support import expected_conditions as EC
# # from webdriver_manager.chrome import ChromeDriverManager

# # urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # DB = "shopify_stores.db"

# # def init_db():
# #     with sqlite3.connect(DB) as conn:
# #         conn.execute("""
# #             CREATE TABLE IF NOT EXISTS stores (
# #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
# #                 store_name TEXT,
# #                 domain TEXT,
# #                 client_id TEXT,
# #                 client_secret TEXT
# #             )
# #         """)
# #         conn.commit()

# # def save_store(name, domain, client_id, secret):
# #     with sqlite3.connect(DB) as conn:
# #         conn.execute("""
# #             INSERT INTO stores
# #             (store_name, domain, client_id, client_secret)
# #             VALUES (?, ?, ?, ?)
# #         """, (name, domain, client_id, secret))
# #         conn.commit()

# # def all_stores():
# #     with sqlite3.connect(DB) as conn:
# #         return pd.read_sql_query("SELECT * FROM stores", conn)

# # init_db()

# # # =====================================
# # # SHOPIFY FUNCTIONS
# # # =====================================

# # def sh_headers(token):
# #     return {
# #         "X-Shopify-Access-Token": token,
# #         "Content-Type": "application/json"
# #     }


# # def get_access_token(domain, client_id, client_secret):
# #     url = f"https://{domain}/admin/oauth/access_token"

# #     payload = {
# #         "client_id": client_id,
# #         "client_secret": client_secret,
# #         "grant_type": "client_credentials"
# #     }

# #     try:
# #         r = requests.post(url, json=payload, verify=False)

# #         if r.status_code == 200:
# #             return r.json()["access_token"], ""

# #         return "", r.text

# #     except Exception as e:
# #         return "", str(e)

# # def fetch_all_products(domain, token):

# #     products = []
# #     url = f"https://{domain}/admin/api/2024-10/products.json?limit=250"

# #     while url:

# #         r = requests.get(
# #             url,
# #             headers=sh_headers(token),
# #             verify=False
# #         )

# #         if r.status_code != 200:
# #             break

# #         products.extend(r.json()["products"])

# #         link = r.headers.get("Link", "")

# #         next_url = None

# #         if 'rel="next"' in link:

# #             for part in link.split(","):

# #                 if 'rel="next"' in part:
# #                     next_url = part.split(";")[0].strip("<> ")

# #         url = next_url

# #     return products
# # def get_asin_from_tags(tags):
# #     """
# #     Extract ASIN from Shopify product tags.
# #     Example:
# #     Electrical, ASIN:B01F9EU16O, Home
# #     """

# #     if not tags:
# #         return None

# #     for tag in tags.split(","):
# #         tag = tag.strip()

# #         if tag.upper().startswith("ASIN:"):
# #             return tag.split(":", 1)[1].strip()

# #     return None


# # def build_shopify_dataframe(products):
# #     """
# #     Convert Shopify products into DataFrame
# #     containing ASIN, SKU and Amazon URL.
# #     """

# #     rows = []

# #     for product in products:

# #         asin = get_asin_from_tags(product.get("tags", ""))

# #         if not asin:
# #             continue

# #         # sku = ""
# #         #
# #         # if product.get("variants"):
# #         #     sku = product["variants"][0].get("sku", "")
# #         #
# #         # rows.append({
# #         #
# #         #     "ASIN": asin,
# #         #
# #         #     "SKU": sku,
# #         #
# #         #     "Shopify Title": product.get("title", ""),
# #         #
# #         #     "Product Link": f"https://www.amazon.com/dp/{asin}"
# #         #
# #         # })
# #         sku = ""
# #         shopify_price = ""

# #         if product.get("variants"):
# #             sku = product["variants"][0].get("sku", "")
# #             shopify_price = product["variants"][0].get("price", "")

# #         rows.append({

# #             "ASIN": asin,

# #             "SKU": sku,

# #             "Shopify Title": product.get("title", ""),

# #             "Shopify Price": shopify_price,

# #             "Product Link": f"https://www.amazon.com/dp/{asin}"

# #         })

# #     return pd.DataFrame(rows)


# # # ================= 1. INITIALIZATION & SESSION STATE =================
# # # Ye variables scan khatam hone ke baad bhi data ko save rakhte hain
# # if 'final_df' not in st.session_state:
# #     st.session_state.final_df = None
# # if 'is_scanning' not in st.session_state:
# #     st.session_state.is_scanning = False

# # # ================= 2. APP CONFIGURATION & CSS =================
# # st.set_page_config(
# #     page_title="Amazon Intelligence Pro",
# #     page_icon="🛒",
# #     layout="wide"
# # )

# # # Professional UI Styling
# # st.markdown("""
# #     <style>
# #     .stApp { background-color: #f8f9fa; }
# #     div[data-testid="stMetricValue"] { font-size: 1.4rem; color: #232F3E; font-weight: bold; }
# #     div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #555; }
# #     .stProgress > div > div > div > div { background-color: #FF9900; }
# #     .custom-dl-btn {
# #         display: inline-block; padding: 0.8em 1.5em; margin: 10px 0;
# #         border-radius: 0.4em; text-decoration: none; font-family: 'Roboto',sans-serif;
# #         font-weight: 600; color: #FFFFFF !important; background-color: #232F3E;
# #         text-align: center; transition: all 0.2s; width: 100%; border: 1px solid #232F3E;
# #     }
# #     .custom-dl-btn:hover { background-color: #FF9900; border-color: #FF9900; color: white !important; }
# #     </style>
# # """, unsafe_allow_html=True)

# # # ================= 3. CORE BACKEND SCRAPER LOGIC =================

# # def get_driver():
# #     options = Options()
# #     options.add_argument("--start-maximized")
# #     options.add_argument("--disable-gpu")
# #     options.add_argument("--no-sandbox")
# #     options.add_argument("--disable-dev-shm-usage")
# #     options.add_argument("--disable-blink-features=AutomationControlled")
# #     options.page_load_strategy = 'eager'
# #     # Use standard User-Agent to avoid early detection
# #     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
# #     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# #     return driver

# # def clean_price(price_str):
# #     """
# #     STRICT PRICE CLEANER:
# #     Splits text at '(' to discard unit prices like ($0.83 / count).
# #     """
# #     try:
# #         if pd.isna(price_str) or str(price_str).strip() == "": return None
# #         # Split at parenthesis to remove unit info
# #         clean_str = str(price_str).split('(')[0]
# #         # Remove currency symbols and non-numeric chars except dot
# #         clean_str = re.sub(r'[^\d.]', '', clean_str)
# #         if clean_str.count('.') > 1:
# #             parts = clean_str.split('.')
# #             clean_str = f"{parts[0]}.{parts[1]}"
# #         return float(clean_str)
# #     except:
# #         return None

# # def handle_blocking(driver):
# #     """Attempts to click 'Continue shopping' if blocked."""
# #     try:
# #         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping')]")
# #         if not btns:
# #             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
# #         for btn in btns:
# #             if "continue" in btn.text.lower():
# #                 btn.click()
# #                 time.sleep(1.5)
# #                 return True
# #     except:
# #         pass
# #     return False

# # def change_location(driver, zip_code):
# #     """Changes Amazon shipping location to target ZIP."""
# #     try:
# #         driver.get("https://www.amazon.com")
# #         handle_blocking(driver)
# #         try:
# #             WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
# #         except:
# #             return False
# #         time.sleep(1)
# #         try:
# #             input_box = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
# #             input_box.clear()
# #             input_box.send_keys(zip_code)
# #             driver.find_element(By.ID, "GLUXZipUpdate").click()
# #             time.sleep(1)
# #             # Confirm close if needed
# #             try:
# #                 driver.find_element(By.CSS_SELECTOR, "div.a-popover-footer input, #GLUXConfirmClose").click()
# #             except:
# #                 pass
# #             time.sleep(2)
# #             return True
# #         except:
# #             return False
# #     except:
# #         return False

# # def _find_labeled_price_in_box(price_box, labels):
# #     """Extracts specific price types (List, Typical, Was) using text labels."""
# #     for lab in labels:
# #         xp_label = (
# #             ".//*[contains(translate(normalize-space(.),"
# #             " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
# #             f" '{lab}')]"
# #         )
# #         try:
# #             label_els = price_box.find_elements(By.XPATH, xp_label)
# #             for _ in label_els:
# #                 xps = [
# #                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
# #                     xp_label + "/following::*[contains(text(),'$')][1]",
# #                 ]
# #                 for xp in xps:
# #                     try:
# #                         el = price_box.find_element(By.XPATH, xp)
# #                         raw = el.get_attribute("innerHTML") or el.text
# #                         val = clean_price(raw)
# #                         if val and val > 1.0:
# #                             return val
# #                     except: pass
# #         except: pass
# #     return None

# # def scrape_item(driver, url, current_zip):
# #     """Main function to scrape specific product data."""
# #     data = {
# #         "Title": "Error", "Live Price": None, "List Price": None, "Discount %": "0%",
# #         "Strategy": "Unknown", "BSR": "N/A", "Stock": "Unknown", "Rating": "N/A",
# #         "Reviews": 0, "Zip Used": current_zip, "Status": "Failed",
# #         "Has Images": "No", "Has Prime": "No", "Brand": "Unknown", "Verified": "❌"
# #     }

# #     try:
# #         # driver.get(url)
# #         # # handle_blocking(driver)
# #         # time.sleep(random.uniform(0.5, 1.0))
# #         driver.get(url)

# #         try:
# #             WebDriverWait(driver, 5).until(
# #                 EC.presence_of_element_located((By.ID, "productTitle"))
# #             )
# #         except:
# #             pass

# #         # 1. Product Title
# #         try:
# #             data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:60] + "..."
# #             data["Status"] = "Success"
# #         except:
# #             data["Status"] = "Blocked/Captcha"
# #             return data

# #         # 2. Live Price (What you pay now)
# #         try:
# #             whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
# #             frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
# #             data["Live Price"] = float(f"{whole}.{frac}")
# #         except:
# #             try:
# #                 raw = driver.find_element(By.CSS_SELECTOR, "span.apexPriceToPay span.a-offscreen").get_attribute("innerHTML")
# #                 data["Live Price"] = clean_price(raw)
# #             except: pass

# #         # 3. List / Typical Price Logic
# #         try:
# #             price_containers = driver.find_elements(By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div, #corePrice_desktop_feature_div, #apex_desktop")
# #             labels = ["typical price", "list price", "was:", "m.r.p"]
# #             for box in price_containers:
# #                 found_val = _find_labeled_price_in_box(box, labels)
# #                 if found_val:
# #                     data["List Price"] = found_val
# #                     break
# #         except: pass

# #         # 4. Discount Percentage
# #         if data["Live Price"] and data["List Price"]:
# #             diff = data["List Price"] - data["Live Price"]
# #             if diff >= 0.20:
# #                 pct = round((diff / data["List Price"]) * 100)
# #                 data["Discount %"] = f"{pct}%"

# #         # 5. Stock Checking
# #         try:
# #             if driver.find_elements(By.ID, "add-to-cart-button") or driver.find_elements(By.ID, "buy-now-button"):
# #                 data["Stock"] = "In Stock"
# #             else:
# #                 data["Stock"] = "Out of Stock"
# #         except: data["Stock"] = "Unknown"

# #         # 6. Fulfillment Strategy
# #         try:
# #             merchant_text = driver.find_element(By.ID, "merchant-info").text.lower()
# #             if "amazon" in merchant_text: data["Strategy"] = "FBA"
# #             else: data["Strategy"] = "FBM"
# #         except: data["Strategy"] = "Unknown"

# #         # # 7. BSR & Ratings
# #         # try:
# #         #     body_text = driver.find_element(By.TAG_NAME, "body").text
# #         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
# #         #     data["BSR"] = f"#{bsr_match.group(1)}" if bsr_match else "N/A"
# #         #
# #         #     # Fallback if first method fails
# #         #     if data["BSR"] == "N/A":
# #         #
# #         #         match = re.search(
# #         #             r"#([\d,]+)\s+in",
# #         #             driver.page_source,
# #         #             re.IGNORECASE
# #         #         )
# #         #
# #         #         if match:
# #         #             data["BSR"] = f"#{match.group(1)}"
# #         # 7. BSR & Ratings
# #         try:
# #             body_text = driver.find_element(By.TAG_NAME, "body").text

# #             bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)

# #             if bsr_match:
# #                 data["BSR"] = int(bsr_match.group(1).replace(",", ""))
# #             else:
# #                 data["BSR"] = None

# #             # Fallback if first method fails
# #             if data["BSR"] is None:

# #                 match = re.search(
# #                     r"#([\d,]+)\s+in",
# #                     driver.page_source,
# #                     re.IGNORECASE
# #                 )

# #                 if match:
# #                     data["BSR"] = int(match.group(1).replace(",", ""))

# #             if data["BSR"] is None:
# #                 data["BSR"] = ""

# #             rating_el = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt")
# #             data["Rating"] = rating_el.get_attribute("innerHTML").split(" ")[0]

# #             rev_el = driver.find_element(By.ID, "acrCustomerReviewText")
# #             # data["Reviews"] = rev_el.text.split(" ")[0]
# #             reviews = re.sub(r"[^\d,]", "", rev_el.text)
# #             data["Reviews"] = reviews
# #         except: pass

# #         # 8. Product Verification Metrics
# #         if driver.find_elements(By.CSS_SELECTOR, "#altImages img, #main-image-container img"):
# #             data["Has Images"] = "Yes"
# #         if driver.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, span.a-icon-prime"):
# #             data["Has Prime"] = "Yes"
# #         try:
# #             brand_el = driver.find_element(By.ID, "bylineInfo")
# #             data["Brand"] = brand_el.text.replace("Visit the", "").replace("Store", "").strip()
# #         except: pass

# #         # # 9. Seller Count
# #         # try:
# #         #     s_text = driver.find_element(By.ID, "olp_feature_div").text
# #         #     s_match = re.search(r'(\d+)', s_text)
# #         #     if s_match: data["Seller Count"] = int(s_match.group(1))
# #         # except: pass

# #         # FINAL VERIFICATION SCORE
# #         v_score = 0
# #         if data["Has Images"] == "Yes": v_score += 1
# #         if data["Live Price"] is not None: v_score += 1
# #         if data["Rating"] != "N/A": v_score += 1
# #         if data["Brand"] != "Unknown": v_score += 1

# #         if v_score >= 4: data["Verified"] = "✅ PASS"
# #         elif v_score >= 2: data["Verified"] = "⚠️ PARTIAL"
# #         else: data["Verified"] = "❌ FAIL"

# #     except Exception as e:
# #         data["Status"] = f"Error"

# #     return data

# # def get_csv_download_link(df, filename="amazon_results.csv"):
# #     """Generates a persistent base64 download link."""
# #     csv = df.to_csv(index=False)
# #     b64 = base64.b64encode(csv.encode()).decode()
# #     href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="custom-dl-btn">📥 DOWNLOAD CSV REPORT</a>'
# #     return href

# # # ================= 4. FRONTEND UI LOGIC =================

# # def main():
# #     st.sidebar.title("⚙️ Amazon Scraper Config")
# #     st.sidebar.markdown("---")
# #     st.sidebar.subheader("🏪 Shopify Store")

# #     stores = all_stores()

# #     if stores.empty:
# #         st.sidebar.error("No store found in database.")
# #         st.stop()

# #     # store_names = stores["store_name"].tolist()
# #     #
# #     # selected_store_name = st.sidebar.selectbox(
# #     #     "Select Store",
# #     #     store_names
# #     # )
# #     #
# #     # selected_store = stores[
# #     #     stores["store_name"] == selected_store_name
# #     #     ].iloc[0]
# #     store_names = ["Select Store"] + stores["store_name"].tolist()

# #     selected_store_name = st.sidebar.selectbox(
# #         "Select Store",
# #         store_names,
# #         index=0
# #     )

# #     if selected_store_name == "Select Store":
# #         st.sidebar.info("👈 Please select a Shopify store.")
# #         st.stop()

# #     selected_store = stores[
# #         stores["store_name"] == selected_store_name
# #         ].iloc[0]

# #     st.sidebar.success(f"Selected: {selected_store_name}")
# #     st.sidebar.caption(selected_store["domain"])

# #     token, err = get_access_token(
# #         selected_store["domain"],
# #         selected_store["client_id"],
# #         selected_store["client_secret"]
# #     )

# #     if not token:
# #         st.sidebar.error("❌ Token Failed")
# #         st.sidebar.code(err)
# #         st.stop()

# #     st.sidebar.success("✅ Shopify Connected")
# #     products = fetch_all_products(
# #         selected_store["domain"],
# #         token
# #     )
# #     st.sidebar.info(f"📦 Products in Store: {len(products)}")
# #     # PERSISTENT DOWNLOAD SECTION
# #     if st.session_state.final_df is not None:
# #         st.sidebar.success("✅ Results from last scan available")
# #         st.sidebar.markdown(get_csv_download_link(st.session_state.final_df), unsafe_allow_html=True)
# #         if st.sidebar.button("🗑️ Clear All Results"):
# #             st.session_state.final_df = None
# #             st.rerun()

# #     st.sidebar.divider()

# #     # Location Settings
# #     LOCATIONS = {
# #         "New York (10001)": "10001",
# #         "Beverly Hills (90210)": "90210",
# #         "Chicago (60601)": "60601",
# #         "Tax Free (19701)": "19701"
# #     }
# #     sel_loc = st.sidebar.selectbox("📍 Target Location", list(LOCATIONS.keys()))
# #     target_zip = LOCATIONS[sel_loc]

# #     # Filters
# #     st.sidebar.subheader("🎯 Scan Filters")
# #     min_disc = st.sidebar.slider("Min Discount %", 0, 90, 0)
# #     # uploaded_file = st.sidebar.file_uploader("📂 Upload CSV/XLSX Product Link List", type=['xlsx', 'csv'])
# #     shopify_df = build_shopify_dataframe(products)

# #     st.title("🛒 Amazon Intelligence Pro")
# #     st.info("Select a Shopify Store and click START SCAN to analyze all products.")

# #     # if uploaded_file:
# #     if not shopify_df.empty:
# #         # # Load Data
# #         # if uploaded_file.name.endswith('.csv'):
# #         #     try: df = pd.read_csv(uploaded_file)
# #         #     except: df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
# #         # else:
# #         #     df = pd.read_excel(uploaded_file)
# #         #
# #         # df.columns = df.columns.str.strip()
# #         # if 'Product Link' not in df.columns:
# #         #     st.error("❌ Column 'Product Link' not found!")
# #         #     return
# #         df = shopify_df.copy()

# #         # Setup Visual Columns
# #         c1, c2, c3, c4 = st.columns(4)
# #         m_scanned = c1.empty()
# #         m_stock = c2.empty()
# #         m_fba = c3.empty()
# #         m_disc = c4.empty()

# #         st.subheader("📡 Live Data Extraction")
# #         table_placeholder = st.empty()

# #         if st.sidebar.button("🚀 START SCAN", type="primary"):
# #             st.session_state.is_scanning = True
# #             results = []
# #             cnt_fba = 0
# #             cnt_disc = 0
# #             cnt_out = 0

# #             with st.status("Initializing Engine...", expanded=True) as status:
# #                 driver = get_driver()

# #                 # Step 1: Change Location
# #                 status.update(label=f"Setting location to {target_zip}...")
# #                 change_location(driver, target_zip)

# #                 # Step 2: Iterate Links
# #                 total = len(df)
# #                 prog_bar = st.progress(0)

# #                 for idx, row in df.iterrows():
# #                     url = row['Product Link']
# #                     if pd.isna(url) or "amazon" not in str(url): continue

# #                     status.update(label=f"Scanning {idx+1}/{total}: {url[:40]}...")

# #                     data = scrape_item(driver, url, target_zip)

# #                     data["ASIN"] = row["ASIN"]
# #                     data["SKU"] = row["SKU"]
# #                     data["Shopify Price"] = row["Shopify Price"]

# #                     shopify_price = clean_price(row["Shopify Price"])

# #                     if shopify_price is not None and data["Live Price"] is not None:

# #                         # difference = round(shopify_price - data["Live Price"], 2)
# #                         #
# #                         # data["Price Difference"] = difference
# #                         #
# #                         # if difference > 0:
# #                         #     data["Price Status"] = "Shopify Higher"
# #                         #
# #                         # elif difference < 0:
# #                         #     data["Price Status"] = "Amazon Higher"
# #                         #
# #                         # else:
# #                         #     data["Price Status"] = "Same Price"
# #                         difference = round(shopify_price - data["Live Price"], 2)

# #                         # Always show positive value with $
# #                         data["Price Difference"] = f"${abs(difference):.2f}"

# #                         if difference > 0:
# #                             data["Price Status"] = "🟢 Shopify Higher"

# #                         elif difference < 0:
# #                             data["Price Status"] = "🔴 Amazon Higher"

# #                         else:
# #                             data["Price Status"] = "🟡 Same Price"

# #                     else:
# #                         data["Price Difference"] = ""
# #                         data["Price Status"] = ""

# #                     # Apply Discount Filter
# #                     d_val = int(data["Discount %"].replace('%', ''))
# #                     if d_val < min_disc:
# #                         continue

# #                     # Update Metrics
# #                     if data["Stock"] == "Out of Stock": cnt_out += 1
# #                     if data["Strategy"] == "FBA": cnt_fba += 1
# #                     if d_val > 0: cnt_disc += 1

# #                     results.append(data)
# #                     st.session_state.final_df = pd.DataFrame(results) # Save to session

# #                     # Live UI Update
# #                     m_scanned.metric("Processed", f"{idx+1}/{total}")
# #                     m_stock.metric("Out Stock", cnt_out)
# #                     m_fba.metric("FBA Found", cnt_fba)
# #                     m_disc.metric("Discounts", cnt_disc)

# #                     # Show last 10 rows
# #                     # table_placeholder.dataframe(st.session_state.final_df.tail(10), use_container_width=True)
# #                     if (idx + 1) % 5 == 0 or idx == total - 1:
# #                         table_placeholder.dataframe(
# #                             st.session_state.final_df.tail(10),
# #                             use_container_width=True
# #                         )
# #                     prog_bar.progress((idx+1)/total)

# #                 driver.quit() # EXIT AFTER LOOP
# #                 status.update(label="✅ Scan Complete!", state="complete")

# #             st.session_state.is_scanning = False
# #             st.success("Verification complete. Use the sidebar to download your CSV.")
# #             # st.rerun() # Refresh to show final download button
# #     if st.session_state.final_df is not None:

# #         st.subheader("📊 Scan Results")

# #         st.dataframe(
# #             st.session_state.final_df,
# #             use_container_width=True,
# #             height=600
# #         )
# #     # # Show full results if already scanned
# #     # elif st.session_state.final_df is not None:
# #     #     st.subheader("📊 Last Scanned Results")
# #     #     st.dataframe(st.session_state.final_df, use_container_width=True)

# # if __name__ == "__main__":
# #     main()


# import streamlit as st
# import pandas as pd
# import time
# import random
# import re
# import base64
# import sqlite3
# import requests
# import urllib3
# import json
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# DB = "shopify_stores.db"

# def init_db():
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS stores (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 store_name TEXT,
#                 domain TEXT,
#                 client_id TEXT,
#                 client_secret TEXT
#             )
#         """)
#         conn.commit()

# def save_store(name, domain, client_id, secret):
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#             INSERT INTO stores
#             (store_name, domain, client_id, client_secret)
#             VALUES (?, ?, ?, ?)
#         """, (name, domain, client_id, secret))
#         conn.commit()

# def all_stores():
#     with sqlite3.connect(DB) as conn:
#         return pd.read_sql_query("SELECT * FROM stores", conn)

# init_db()

# # =====================================
# # SHOPIFY FUNCTIONS
# # =====================================

# def sh_headers(token):
#     return {
#         "X-Shopify-Access-Token": token,
#         "Content-Type": "application/json"
#     }


# def get_access_token(domain, client_id, client_secret):
#     url = f"https://{domain}/admin/oauth/access_token"

#     payload = {
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "grant_type": "client_credentials"
#     }

#     try:
#         r = requests.post(url, json=payload, verify=False)

#         if r.status_code == 200:
#             return r.json()["access_token"], ""

#         return "", r.text

#     except Exception as e:
#         return "", str(e)

# def fetch_all_products(domain, token):

#     products = []
#     url = f"https://{domain}/admin/api/2024-10/products.json?limit=250"

#     while url:

#         r = requests.get(
#             url,
#             headers=sh_headers(token),
#             verify=False
#         )

#         if r.status_code != 200:
#             break

#         products.extend(r.json()["products"])

#         link = r.headers.get("Link", "")

#         next_url = None

#         if 'rel="next"' in link:

#             for part in link.split(","):

#                 if 'rel="next"' in part:
#                     next_url = part.split(";")[0].strip("<> ")

#         url = next_url

#     return products
# def get_asin_from_tags(tags):
#     """
#     Extract ASIN from Shopify product tags.
#     Example:
#     Electrical, ASIN:B01F9EU16O, Home
#     """

#     if not tags:
#         return None

#     for tag in tags.split(","):
#         tag = tag.strip()

#         if tag.upper().startswith("ASIN:"):
#             return tag.split(":", 1)[1].strip()

#     return None


# def build_shopify_dataframe(products):
#     """
#     Convert Shopify products into DataFrame
#     containing ASIN, SKU and Amazon URL.
#     """

#     rows = []

#     for product in products:

#         asin = get_asin_from_tags(product.get("tags", ""))

#         if not asin:
#             continue

#         # sku = ""
#         #
#         # if product.get("variants"):
#         #     sku = product["variants"][0].get("sku", "")
#         #
#         # rows.append({
#         #
#         #     "ASIN": asin,
#         #
#         #     "SKU": sku,
#         #
#         #     "Shopify Title": product.get("title", ""),
#         #
#         #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#         #
#         # })
#         sku = ""
#         # shopify_price = ""

#         if product.get("variants"):
#             sku = product["variants"][0].get("sku", "")
#             # shopify_price = product["variants"][0].get("price", "")

#         rows.append({

#             "ASIN": asin,

#             "SKU": sku,

#             "Shopify Title": product.get("title", ""),

#             # "Shopify Price": shopify_price,

#             "Product Link": f"https://www.amazon.com/dp/{asin}"

#         })

#     return pd.DataFrame(rows)


# # ================= 1. INITIALIZATION & SESSION STATE =================
# # Ye variables scan khatam hone ke baad bhi data ko save rakhte hain
# if 'final_df' not in st.session_state:
#     st.session_state.final_df = None
# if 'is_scanning' not in st.session_state:
#     st.session_state.is_scanning = False

# # ================= 2. APP CONFIGURATION & CSS =================
# st.set_page_config(
#     page_title="Amazon Intelligence Pro",
#     page_icon="🛒",
#     layout="wide"
# )

# # Professional UI Styling
# st.markdown("""
#     <style>
#     .stApp { background-color: #f8f9fa; }
#     div[data-testid="stMetricValue"] { font-size: 1.4rem; color: #232F3E; font-weight: bold; }
#     div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #555; }
#     .stProgress > div > div > div > div { background-color: #FF9900; }
#     .custom-dl-btn {
#         display: inline-block; padding: 0.8em 1.5em; margin: 10px 0;
#         border-radius: 0.4em; text-decoration: none; font-family: 'Roboto',sans-serif;
#         font-weight: 600; color: #FFFFFF !important; background-color: #232F3E;
#         text-align: center; transition: all 0.2s; width: 100%; border: 1px solid #232F3E;
#     }
#     .custom-dl-btn:hover { background-color: #FF9900; border-color: #FF9900; color: white !important; }
#     </style>
# """, unsafe_allow_html=True)

# # ================= 3. CORE BACKEND SCRAPER LOGIC =================

# def get_driver():
#     options = Options()
#     options.add_argument("--start-maximized")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.page_load_strategy = 'eager'
#     # Use standard User-Agent to avoid early detection
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver

# # def clean_price(price_str):
# #     """
# #     STRICT PRICE CLEANER:
# #     Splits text at '(' to discard unit prices like ($0.83 / count).
# #     """
# #     try:
# #         if pd.isna(price_str) or str(price_str).strip() == "": return None
# #         # Split at parenthesis to remove unit info
# #         clean_str = str(price_str).split('(')[0]
# #         # Remove currency symbols and non-numeric chars except dot
# #         clean_str = re.sub(r'[^\d.]', '', clean_str)
# #         if clean_str.count('.') > 1:
# #             parts = clean_str.split('.')
# #             clean_str = f"{parts[0]}.{parts[1]}"
# #         return float(clean_str)
# #     except:
# #         return None

# def handle_blocking(driver):
#     """Attempts to click 'Continue shopping' if blocked."""
#     try:
#         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping')]")
#         if not btns:
#             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
#         for btn in btns:
#             if "continue" in btn.text.lower():
#                 btn.click()
#                 time.sleep(1.5)
#                 return True
#     except:
#         pass
#     return False

# def change_location(driver, zip_code):
#     """Changes Amazon shipping location to target ZIP."""
#     try:
#         driver.get("https://www.amazon.com")
#         handle_blocking(driver)
#         try:
#             WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
#         except:
#             return False
#         time.sleep(1)
#         try:
#             input_box = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
#             input_box.clear()
#             input_box.send_keys(zip_code)
#             driver.find_element(By.ID, "GLUXZipUpdate").click()
#             time.sleep(1)
#             # Confirm close if needed
#             try:
#                 driver.find_element(By.CSS_SELECTOR, "div.a-popover-footer input, #GLUXConfirmClose").click()
#             except:
#                 pass
#             time.sleep(2)
#             return True
#         except:
#             return False
#     except:
#         return False

# # def _find_labeled_price_in_box(price_box, labels):
# #     """Extracts specific price types (List, Typical, Was) using text labels."""
# #     for lab in labels:
# #         xp_label = (
# #             ".//*[contains(translate(normalize-space(.),"
# #             " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
# #             f" '{lab}')]"
# #         )
# #         try:
# #             label_els = price_box.find_elements(By.XPATH, xp_label)
# #             for _ in label_els:
# #                 xps = [
# #                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
# #                     xp_label + "/following::*[contains(text(),'$')][1]",
# #                 ]
# #                 for xp in xps:
# #                     try:
# #                         el = price_box.find_element(By.XPATH, xp)
# #                         raw = el.get_attribute("innerHTML") or el.text
# #                         val = clean_price(raw)
# #                         if val and val > 1.0:
# #                             return val
# #                     except: pass
# #         except: pass
# #     return None

# def scrape_item(driver, url, current_zip):
#     """Main function to scrape specific product data."""
#     # data = {
#     #     "Title": "Error", "Live Price": None, "List Price": None, "Discount %": "0%",
#     #     "Strategy": "Unknown", "BSR": "N/A", "Stock": "Unknown", "Rating": "N/A",
#     #     "Reviews": 0, "Zip Used": current_zip, "Status": "Failed",
#     #     "Has Images": "No", "Has Prime": "No", "Brand": "Unknown", "Verified": "❌"
#     # }
#     data = {
#         "Title": "Error",
#         "Stock": "Unknown",
#         "Zip Used": current_zip,
#         "Status": "Failed",
#         "Verified": ""
#     }

#     try:
#         # driver.get(url)
#         # # handle_blocking(driver)
#         # time.sleep(random.uniform(0.5, 1.0))
#         driver.get(url)

#         try:
#             WebDriverWait(driver, 5).until(
#                 EC.presence_of_element_located((By.ID, "productTitle"))
#             )
#         except:
#             pass


#         # try:
#         #     data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:60] + "..."
#         #     data["Status"] = "Success"
#         # except:
#         #     data["Status"] = "Blocked/Captcha"
#         #     return data
#         # 1. Product Title
#         try:
#             data["Title"] = driver.find_element(
#                 By.ID,
#                 "productTitle"
#             ).text.strip()[:60] + "..."

#             data["Status"] = "Success"

#         except:

#             page = driver.page_source.lower()

#             if "we couldn't find that page" in page:
#                 data["Status"] = "Page Not Found"

#             elif "robot check" in page:
#                 data["Status"] = "Captcha"

#             elif "sorry, something went wrong" in page:
#                 data["Status"] = "Amazon Error"

#             else:
#                 data["Status"] = "Unknown Error"

#             return data
#         # # 2. Live Price (What you pay now)
#         # try:
#         #     whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
#         #     frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
#         #     data["Live Price"] = float(f"{whole}.{frac}")
#         # except:
#         #     try:
#         #         raw = driver.find_element(By.CSS_SELECTOR, "span.apexPriceToPay span.a-offscreen").get_attribute("innerHTML")
#         #         data["Live Price"] = clean_price(raw)
#         #     except: pass
#         #
#         # # 3. List / Typical Price Logic
#         # try:
#         #     price_containers = driver.find_elements(By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div, #corePrice_desktop_feature_div, #apex_desktop")
#         #     labels = ["typical price", "list price", "was:", "m.r.p"]
#         #     for box in price_containers:
#         #         found_val = _find_labeled_price_in_box(box, labels)
#         #         if found_val:
#         #             data["List Price"] = found_val
#         #             break
#         # except: pass
#         #
#         # # 4. Discount Percentage
#         # if data["Live Price"] and data["List Price"]:
#         #     diff = data["List Price"] - data["Live Price"]
#         #     if diff >= 0.20:
#         #         pct = round((diff / data["List Price"]) * 100)
#         #         data["Discount %"] = f"{pct}%"

#         # 5. Stock Checking
#         try:
#             if driver.find_elements(By.ID, "add-to-cart-button") or driver.find_elements(By.ID, "buy-now-button"):
#                 data["Stock"] = "In Stock"
#             else:
#                 data["Stock"] = "Out of Stock"
#         except: data["Stock"] = "Unknown"

#         # # 6. Fulfillment Strategy
#         # try:
#         #     merchant_text = driver.find_element(By.ID, "merchant-info").text.lower()
#         #     if "amazon" in merchant_text: data["Strategy"] = "FBA"
#         #     else: data["Strategy"] = "FBM"
#         # except: data["Strategy"] = "Unknown"

#         # # 7. BSR & Ratings
#         # try:
#         #     body_text = driver.find_element(By.TAG_NAME, "body").text
#         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
#         #     data["BSR"] = f"#{bsr_match.group(1)}" if bsr_match else "N/A"
#         #
#         #     # Fallback if first method fails
#         #     if data["BSR"] == "N/A":
#         #
#         #         match = re.search(
#         #             r"#([\d,]+)\s+in",
#         #             driver.page_source,
#         #             re.IGNORECASE
#         #         )
#         #
#         #         if match:
#         #             data["BSR"] = f"#{match.group(1)}"
#         # # 7. BSR & Ratings
#         # try:
#         #     body_text = driver.find_element(By.TAG_NAME, "body").text
#         #
#         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
#         #
#         #     if bsr_match:
#         #         data["BSR"] = int(bsr_match.group(1).replace(",", ""))
#         #     else:
#         #         data["BSR"] = None
#         #
#         #     # Fallback if first method fails
#         #     if data["BSR"] is None:
#         #
#         #         match = re.search(
#         #             r"#([\d,]+)\s+in",
#         #             driver.page_source,
#         #             re.IGNORECASE
#         #         )
#         #
#         #         if match:
#         #             data["BSR"] = int(match.group(1).replace(",", ""))
#         #
#         #     if data["BSR"] is None:
#         #         data["BSR"] = ""
#         #
#         #     rating_el = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt")
#         #     data["Rating"] = rating_el.get_attribute("innerHTML").split(" ")[0]
#         #
#         #     rev_el = driver.find_element(By.ID, "acrCustomerReviewText")
#         #     # data["Reviews"] = rev_el.text.split(" ")[0]
#         #     reviews = re.sub(r"[^\d,]", "", rev_el.text)
#         #     data["Reviews"] = reviews
#         # except: pass

#         # # 8. Product Verification Metrics
#         # if driver.find_elements(By.CSS_SELECTOR, "#altImages img, #main-image-container img"):
#         #     data["Has Images"] = "Yes"
#         # if driver.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, span.a-icon-prime"):
#         #     data["Has Prime"] = "Yes"
#         # try:
#         #     brand_el = driver.find_element(By.ID, "bylineInfo")
#         #     data["Brand"] = brand_el.text.replace("Visit the", "").replace("Store", "").strip()
#         # except: pass

#         # # 9. Seller Count
#         # try:
#         #     s_text = driver.find_element(By.ID, "olp_feature_div").text
#         #     s_match = re.search(r'(\d+)', s_text)
#         #     if s_match: data["Seller Count"] = int(s_match.group(1))
#         # except: pass

#         # FINAL VERIFICATION SCORE
#         # v_score = 0
#         # if data["Has Images"] == "Yes": v_score += 1
#         # if data["Live Price"] is not None: v_score += 1
#         # if data["Rating"] != "N/A": v_score += 1
#         # if data["Brand"] != "Unknown": v_score += 1
#         #
#         # if v_score >= 4: data["Verified"] = "✅ PASS"
#         # elif v_score >= 2: data["Verified"] = "⚠️ PARTIAL"
#         # else: data["Verified"] = "❌ FAIL"
#         # if data["Status"] == "Success":
#         #     data["Verified"] = "✅ PASS"
#         # else:
#         #     data["Verified"] = "❌ FAIL"
#         if data["Status"] == "Success":
#             data["Verified"] = "✅ PASS"

#         elif data["Status"] == "Page Not Found":
#             data["Verified"] = "❌ Invalid ASIN"

#         elif data["Status"] == "Captcha":
#             data["Verified"] = "⚠ Retry"

#         else:
#             data["Verified"] = "❌ FAIL"

#     except Exception as e:
#         data["Status"] = f"Error"

#     return data

# def get_csv_download_link(df, filename="amazon_results.csv"):
#     """Generates a persistent base64 download link."""
#     csv = df.to_csv(index=False)
#     b64 = base64.b64encode(csv.encode()).decode()
#     href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="custom-dl-btn">📥 DOWNLOAD CSV REPORT</a>'
#     return href

# # ================= 4. FRONTEND UI LOGIC =================

# def main():
#     st.sidebar.title("⚙️ Amazon Scraper Config")
#     st.sidebar.markdown("---")
#     st.sidebar.subheader("🏪 Shopify Store")

#     stores = all_stores()

#     if stores.empty:
#         st.sidebar.error("No store found in database.")
#         st.stop()

#     # store_names = stores["store_name"].tolist()
#     #
#     # selected_store_name = st.sidebar.selectbox(
#     #     "Select Store",
#     #     store_names
#     # )
#     #
#     # selected_store = stores[
#     #     stores["store_name"] == selected_store_name
#     #     ].iloc[0]
#     store_names = ["Select Store"] + stores["store_name"].tolist()

#     selected_store_name = st.sidebar.selectbox(
#         "Select Store",
#         store_names,
#         index=0
#     )

#     if selected_store_name == "Select Store":
#         st.sidebar.info("👈 Please select a Shopify store.")
#         st.stop()

#     selected_store = stores[
#         stores["store_name"] == selected_store_name
#         ].iloc[0]

#     st.sidebar.success(f"Selected: {selected_store_name}")
#     st.sidebar.caption(selected_store["domain"])

#     token, err = get_access_token(
#         selected_store["domain"],
#         selected_store["client_id"],
#         selected_store["client_secret"]
#     )

#     if not token:
#         st.sidebar.error("❌ Token Failed")
#         st.sidebar.code(err)
#         st.stop()

#     st.sidebar.success("✅ Shopify Connected")
#     products = fetch_all_products(
#         selected_store["domain"],
#         token
#     )
#     st.sidebar.info(f"📦 Products in Store: {len(products)}")
#     # PERSISTENT DOWNLOAD SECTION
#     if st.session_state.final_df is not None:
#         st.sidebar.success("✅ Results from last scan available")
#         st.sidebar.markdown(get_csv_download_link(st.session_state.final_df), unsafe_allow_html=True)
#         if st.sidebar.button("🗑️ Clear All Results"):
#             st.session_state.final_df = None
#             st.rerun()

#     st.sidebar.divider()

#     # Location Settings
#     LOCATIONS = {
#         "New York (10001)": "10001",
#         "Beverly Hills (90210)": "90210",
#         "Chicago (60601)": "60601",
#         "Tax Free (19701)": "19701"
#     }
#     sel_loc = st.sidebar.selectbox("📍 Target Location", list(LOCATIONS.keys()))
#     target_zip = LOCATIONS[sel_loc]

#     # Filters
#     st.sidebar.subheader("🎯 Scan Filters")
#     # min_disc = st.sidebar.slider("Min Discount %", 0, 90, 0)
#     # uploaded_file = st.sidebar.file_uploader("📂 Upload CSV/XLSX Product Link List", type=['xlsx', 'csv'])
#     shopify_df = build_shopify_dataframe(products)

#     st.title("🛒 Amazon Intelligence Pro")
#     st.info("Select a Shopify Store and click START SCAN to analyze all products.")

#     # if uploaded_file:
#     if not shopify_df.empty:
#         # # Load Data
#         # if uploaded_file.name.endswith('.csv'):
#         #     try: df = pd.read_csv(uploaded_file)
#         #     except: df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
#         # else:
#         #     df = pd.read_excel(uploaded_file)
#         #
#         # df.columns = df.columns.str.strip()
#         # if 'Product Link' not in df.columns:
#         #     st.error("❌ Column 'Product Link' not found!")
#         #     return
#         df = shopify_df.copy()

#         # # Setup Visual Columns
#         # c1, c2, c3, c4 = st.columns(4)
#         c1, c2 = st.columns(2)
#         m_scanned = c1.empty()
#         m_stock = c2.empty()
#         # m_fba = c3.empty()
#         # m_disc = c4.empty()

#         st.subheader("📡 Live Data Extraction")
#         table_placeholder = st.empty()

#         if st.sidebar.button("🚀 START SCAN", type="primary"):
#             st.session_state.is_scanning = True
#             results = []
#             # cnt_fba = 0
#             # cnt_disc = 0
#             cnt_out = 0

#             with st.status("Initializing Engine...", expanded=True) as status:
#                 driver = get_driver()

#                 # Step 1: Change Location
#                 status.update(label=f"Setting location to {target_zip}...")
#                 change_location(driver, target_zip)

#                 # Step 2: Iterate Links
#                 total = len(df)
#                 prog_bar = st.progress(0)

#                 for idx, row in df.iterrows():
#                     url = row['Product Link']
#                     if pd.isna(url) or "amazon" not in str(url): continue

#                     status.update(label=f"Scanning {idx+1}/{total}: {url[:40]}...")

#                     data = scrape_item(driver, url, target_zip)

#                     data["ASIN"] = row["ASIN"]
#                     data["SKU"] = row["SKU"]
#                     # data["Shopify Price"] = row["Shopify Price"]

#                     # shopify_price = clean_price(row["Shopify Price"])
#                     #
#                     # if shopify_price is not None and data["Live Price"] is not None:
#                     #
#                     #     # difference = round(shopify_price - data["Live Price"], 2)
#                     #     #
#                     #     # data["Price Difference"] = difference
#                     #     #
#                     #     # if difference > 0:
#                     #     #     data["Price Status"] = "Shopify Higher"
#                     #     #
#                     #     # elif difference < 0:
#                     #     #     data["Price Status"] = "Amazon Higher"
#                     #     #
#                     #     # else:
#                     #     #     data["Price Status"] = "Same Price"
#                     #     difference = round(shopify_price - data["Live Price"], 2)
#                     #
#                     #     # Always show positive value with $
#                     #     data["Price Difference"] = f"${abs(difference):.2f}"
#                     #
#                     #     if difference > 0:
#                     #         data["Price Status"] = "🟢 Shopify Higher"
#                     #
#                     #     elif difference < 0:
#                     #         data["Price Status"] = "🔴 Amazon Higher"
#                     #
#                     #     else:
#                     #         data["Price Status"] = "🟡 Same Price"
#                     #
#                     # else:
#                     #     data["Price Difference"] = ""
#                     #     data["Price Status"] = ""
#                     #
#                     # # Apply Discount Filter
#                     # d_val = int(data["Discount %"].replace('%', ''))
#                     # if d_val < min_disc:
#                     #     continue

#                     # Update Metrics
#                     if data["Stock"] == "Out of Stock": cnt_out += 1
#                     # if data["Strategy"] == "FBA": cnt_fba += 1
#                     # if d_val > 0: cnt_disc += 1

#                     results.append(data)
#                     st.session_state.final_df = pd.DataFrame(results) # Save to session

#                     # Live UI Update
#                     m_scanned.metric("Processed", f"{idx+1}/{total}")
#                     m_stock.metric("Out Stock", cnt_out)
#                     # m_fba.metric("FBA Found", cnt_fba)
#                     # m_disc.metric("Discounts", cnt_disc)

#                     # Show last 10 rows
#                     # table_placeholder.dataframe(st.session_state.final_df.tail(10), use_container_width=True)
#                     if (idx + 1) % 5 == 0 or idx == total - 1:
#                         table_placeholder.dataframe(
#                             st.session_state.final_df.tail(10),
#                             use_container_width=True
#                         )
#                     prog_bar.progress((idx+1)/total)

#                 driver.quit() # EXIT AFTER LOOP
#                 status.update(label="✅ Scan Complete!", state="complete")

#             st.session_state.is_scanning = False
#             st.success("Verification complete. Use the sidebar to download your CSV.")
#             # st.rerun() # Refresh to show final download button
#     if st.session_state.final_df is not None:

#         st.subheader("📊 Scan Results")
#         display_df = st.session_state.final_df[
#             [
#                 "Title",
#                 "ASIN",
#                 "SKU",
#                 "Zip Used",
#                 "Stock",
#                 "Status",
#                 "Verified"
#             ]
#         ]
#         # st.dataframe(
#         #     st.session_state.final_df,
#         #     use_container_width=True,
#         #     height=600
#         # )
#         st.dataframe(
#             display_df,
#             use_container_width=True,
#             height=600
#         )
#     # # Show full results if already scanned
#     # elif st.session_state.final_df is not None:
#     #     st.subheader("📊 Last Scanned Results")
#     #     st.dataframe(st.session_state.final_df, use_container_width=True)

# if __name__ == "__main__":
#     main()
# import streamlit as st
# import pandas as pd
# import time
# import random
# import re
# import base64
# import sqlite3
# import requests
# import urllib3
# import json
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# DB = "shopify_stores.db"

# def init_db():
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS stores (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 store_name TEXT,
#                 domain TEXT,
#                 client_id TEXT,
#                 client_secret TEXT
#             )
#         """)
#         conn.commit()

# def save_store(name, domain, client_id, secret):
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#             INSERT INTO stores
#             (store_name, domain, client_id, client_secret)
#             VALUES (?, ?, ?, ?)
#         """, (name, domain, client_id, secret))
#         conn.commit()

# def all_stores():
#     with sqlite3.connect(DB) as conn:
#         return pd.read_sql_query("SELECT * FROM stores", conn)

# init_db()

# # =====================================
# # SHOPIFY FUNCTIONS
# # =====================================

# def sh_headers(token):
#     return {
#         "X-Shopify-Access-Token": token,
#         "Content-Type": "application/json"
#     }


# def get_access_token(domain, client_id, client_secret):
#     url = f"https://{domain}/admin/oauth/access_token"

#     payload = {
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "grant_type": "client_credentials"
#     }

#     try:
#         r = requests.post(url, json=payload, verify=False)

#         if r.status_code == 200:
#             return r.json()["access_token"], ""

#         return "", r.text

#     except Exception as e:
#         return "", str(e)

# def fetch_all_products(domain, token):

#     products = []
#     # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250"
#     url = f"https://{domain}/admin/api/2024-10/products.json?limit=250&fields=id,title,tags,variants"

#     while url:

#         r = requests.get(
#             url,
#             headers=sh_headers(token),
#             verify=False
#         )

#         if r.status_code != 200:
#             break

#         products.extend(r.json()["products"])

#         link = r.headers.get("Link", "")

#         next_url = None

#         if 'rel="next"' in link:

#             for part in link.split(","):

#                 if 'rel="next"' in part:
#                     next_url = part.split(";")[0].strip("<> ")

#         url = next_url

#     return products
# def get_asin_from_tags(tags):
#     """
#     Extract ASIN from Shopify product tags.
#     Example:
#     Electrical, ASIN:B01F9EU16O, Home
#     """

#     if not tags:
#         return None

#     for tag in tags.split(","):
#         tag = tag.strip()

#         if tag.upper().startswith("ASIN:"):
#             return tag.split(":", 1)[1].strip()

#     return None


# def build_shopify_dataframe(products):
#     """
#     Convert Shopify products into DataFrame
#     containing ASIN, SKU and Amazon URL.
#     """

#     rows = []
#     # for product in products:
#     #
#     #     # asin = get_asin_from_tags(product.get("tags", ""))
#     #     #
#     #     # if not asin:
#     #     #     continue
#     #     asin = get_asin_from_tags(product.get("tags", ""))
#     #
#     #     sku = ""
#     #
#     #     if product.get("variants"):
#     #         sku = product["variants"][0].get("sku", "")
#     #
#     #     # Fallback:
#     #     # if not asin and sku.startswith("GK"):
#     #     #     asin = "B0" + sku[2:]
#     #     if (
#     #             not asin
#     #             and sku
#     #             and sku.startswith("GK")
#     #             and len(sku) > 2
#     #     ):
#     #         asin = "B0" + sku[2:]
#     #
#     #     # Agar phir bhi ASIN nahi bana
#     #     if not asin:
#     #         continue
#     #
#     #     # sku = ""
#     #     #
#     #     # if product.get("variants"):
#     #     #     sku = product["variants"][0].get("sku", "")
#     #     #
#     #     # rows.append({
#     #     #
#     #     #     "ASIN": asin,
#     #     #
#     #     #     "SKU": sku,
#     #     #
#     #     #     "Shopify Title": product.get("title", ""),
#     #     #
#     #     #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     #
#     #     # })
#     #     sku = ""
#     #     # shopify_price = ""
#     #
#     #     if product.get("variants"):
#     #         sku = product["variants"][0].get("sku", "")
#     #         # shopify_price = product["variants"][0].get("price", "")
#     #
#     #     # rows.append({
#     #     #
#     #     #     "ASIN": asin,
#     #     #
#     #     #     "SKU": sku,
#     #     #
#     #     #     "Shopify Title": product.get("title", ""),
#     #     #
#     #     #     # "Shopify Price": shopify_price,
#     #     #
#     #     #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     #
#     #     # })
#     #     rows.append({
#     #         "ASIN": asin,
#     #         "SKU": sku,
#     #         "Shopify Title": product.get("title", ""),
#     #         "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     })
#     for product in products:

#         # 1. Try ASIN from Shopify tags
#         asin = get_asin_from_tags(product.get("tags", ""))

#         # 2. Read SKU
#         sku = ""

#         if product.get("variants"):
#             sku = product["variants"][0].get("sku", "")

#         # 3. Fallback:
#         # If ASIN tag is missing, generate ASIN from SKU
#         if (
#                 not asin
#                 and sku
#                 and sku.startswith("GK")
#                 and len(sku) > 2
#         ):
#             asin = "B0" + sku[2:]

#         # 4. Skip only if ASIN still not found
#         if not asin:
#             continue

#         rows.append({

#             "ASIN": asin,

#             "SKU": sku,

#             "Shopify Title": product.get("title", ""),

#             "Product Link": f"https://www.amazon.com/dp/{asin}"

#         })

#     return pd.DataFrame(rows)


# # ================= 1. INITIALIZATION & SESSION STATE =================
# # Ye variables scan khatam hone ke baad bhi data ko save rakhte hain
# if 'final_df' not in st.session_state:
#     st.session_state.final_df = None
# if 'is_scanning' not in st.session_state:
#     st.session_state.is_scanning = False

# # ================= 2. APP CONFIGURATION & CSS =================
# st.set_page_config(
#     page_title="Amazon Intelligence Pro",
#     page_icon="🛒",
#     layout="wide"
# )

# # Professional UI Styling
# st.markdown("""
#     <style>
#     .stApp { background-color: #f8f9fa; }
#     div[data-testid="stMetricValue"] { font-size: 1.4rem; color: #232F3E; font-weight: bold; }
#     div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #555; }
#     .stProgress > div > div > div > div { background-color: #FF9900; }
#     .custom-dl-btn {
#         display: inline-block; padding: 0.8em 1.5em; margin: 10px 0;
#         border-radius: 0.4em; text-decoration: none; font-family: 'Roboto',sans-serif;
#         font-weight: 600; color: #FFFFFF !important; background-color: #232F3E;
#         text-align: center; transition: all 0.2s; width: 100%; border: 1px solid #232F3E;
#     }
#     .custom-dl-btn:hover { background-color: #FF9900; border-color: #FF9900; color: white !important; }
#     </style>
# """, unsafe_allow_html=True)

# # ================= 3. CORE BACKEND SCRAPER LOGIC =================

# def get_driver():
#     options = Options()
#     options.add_argument("--start-maximized")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.page_load_strategy = 'eager'
#     # Use standard User-Agent to avoid early detection
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver

# # def clean_price(price_str):
# #     """
# #     STRICT PRICE CLEANER:
# #     Splits text at '(' to discard unit prices like ($0.83 / count).
# #     """
# #     try:
# #         if pd.isna(price_str) or str(price_str).strip() == "": return None
# #         # Split at parenthesis to remove unit info
# #         clean_str = str(price_str).split('(')[0]
# #         # Remove currency symbols and non-numeric chars except dot
# #         clean_str = re.sub(r'[^\d.]', '', clean_str)
# #         if clean_str.count('.') > 1:
# #             parts = clean_str.split('.')
# #             clean_str = f"{parts[0]}.{parts[1]}"
# #         return float(clean_str)
# #     except:
# #         return None

# def handle_blocking(driver):
#     """Attempts to click 'Continue shopping' if blocked."""
#     try:
#         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping')]")
#         if not btns:
#             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
#         for btn in btns:
#             if "continue" in btn.text.lower():
#                 btn.click()
#                 time.sleep(1.5)
#                 return True
#     except:
#         pass
#     return False

# def change_location(driver, zip_code):
#     """Changes Amazon shipping location to target ZIP."""
#     try:
#         driver.get("https://www.amazon.com")
#         handle_blocking(driver)
#         try:
#             WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
#         except:
#             return False
#         time.sleep(1)
#         try:
#             input_box = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
#             input_box.clear()
#             input_box.send_keys(zip_code)
#             driver.find_element(By.ID, "GLUXZipUpdate").click()
#             time.sleep(1)
#             # Confirm close if needed
#             try:
#                 driver.find_element(By.CSS_SELECTOR, "div.a-popover-footer input, #GLUXConfirmClose").click()
#             except:
#                 pass
#             time.sleep(2)
#             return True
#         except:
#             return False
#     except:
#         return False

# # def _find_labeled_price_in_box(price_box, labels):
# #     """Extracts specific price types (List, Typical, Was) using text labels."""
# #     for lab in labels:
# #         xp_label = (
# #             ".//*[contains(translate(normalize-space(.),"
# #             " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
# #             f" '{lab}')]"
# #         )
# #         try:
# #             label_els = price_box.find_elements(By.XPATH, xp_label)
# #             for _ in label_els:
# #                 xps = [
# #                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
# #                     xp_label + "/following::*[contains(text(),'$')][1]",
# #                 ]
# #                 for xp in xps:
# #                     try:
# #                         el = price_box.find_element(By.XPATH, xp)
# #                         raw = el.get_attribute("innerHTML") or el.text
# #                         val = clean_price(raw)
# #                         if val and val > 1.0:
# #                             return val
# #                     except: pass
# #         except: pass
# #     return None

# def scrape_item(driver, url, current_zip):
#     """Main function to scrape specific product data."""
#     # data = {
#     #     "Title": "Error", "Live Price": None, "List Price": None, "Discount %": "0%",
#     #     "Strategy": "Unknown", "BSR": "N/A", "Stock": "Unknown", "Rating": "N/A",
#     #     "Reviews": 0, "Zip Used": current_zip, "Status": "Failed",
#     #     "Has Images": "No", "Has Prime": "No", "Brand": "Unknown", "Verified": "❌"
#     # }
#     data = {
#         "Title": "Error",
#         "Stock": "Unknown",
#         "Zip Used": current_zip,
#         "Status": "Failed",
#         "Verified": ""
#     }

#     try:
#         # driver.get(url)
#         # # handle_blocking(driver)
#         # time.sleep(random.uniform(0.5, 1.0))
#         driver.get(url)

#         try:
#             WebDriverWait(driver, 5).until(
#                 EC.presence_of_element_located((By.ID, "productTitle"))
#             )
#         except:
#             pass


#         # try:
#         #     data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:60] + "..."
#         #     data["Status"] = "Success"
#         # except:
#         #     data["Status"] = "Blocked/Captcha"
#         #     return data
#         # 1. Product Title
#         try:
#             data["Title"] = driver.find_element(
#                 By.ID,
#                 "productTitle"
#             ).text.strip()[:60] + "..."

#             data["Status"] = "Success"

#         except:

#             page = driver.page_source.lower()

#             if "we couldn't find that page" in page:
#                 data["Status"] = "Page Not Found"

#             elif "robot check" in page:
#                 data["Status"] = "Captcha"

#             elif "sorry, something went wrong" in page:
#                 data["Status"] = "Amazon Error"

#             else:
#                 data["Status"] = "Unknown Error"

#             return data
#         # # 2. Live Price (What you pay now)
#         # try:
#         #     whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
#         #     frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
#         #     data["Live Price"] = float(f"{whole}.{frac}")
#         # except:
#         #     try:
#         #         raw = driver.find_element(By.CSS_SELECTOR, "span.apexPriceToPay span.a-offscreen").get_attribute("innerHTML")
#         #         data["Live Price"] = clean_price(raw)
#         #     except: pass
#         #
#         # # 3. List / Typical Price Logic
#         # try:
#         #     price_containers = driver.find_elements(By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div, #corePrice_desktop_feature_div, #apex_desktop")
#         #     labels = ["typical price", "list price", "was:", "m.r.p"]
#         #     for box in price_containers:
#         #         found_val = _find_labeled_price_in_box(box, labels)
#         #         if found_val:
#         #             data["List Price"] = found_val
#         #             break
#         # except: pass
#         #
#         # # 4. Discount Percentage
#         # if data["Live Price"] and data["List Price"]:
#         #     diff = data["List Price"] - data["Live Price"]
#         #     if diff >= 0.20:
#         #         pct = round((diff / data["List Price"]) * 100)
#         #         data["Discount %"] = f"{pct}%"

#         # 5. Stock Checking
#         try:
#             if driver.find_elements(By.ID, "add-to-cart-button") or driver.find_elements(By.ID, "buy-now-button"):
#                 data["Stock"] = "In Stock"
#             else:
#                 data["Stock"] = "Out of Stock"
#         except: data["Stock"] = "Unknown"

#         # # 6. Fulfillment Strategy
#         # try:
#         #     merchant_text = driver.find_element(By.ID, "merchant-info").text.lower()
#         #     if "amazon" in merchant_text: data["Strategy"] = "FBA"
#         #     else: data["Strategy"] = "FBM"
#         # except: data["Strategy"] = "Unknown"

#         # # 7. BSR & Ratings
#         # try:
#         #     body_text = driver.find_element(By.TAG_NAME, "body").text
#         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
#         #     data["BSR"] = f"#{bsr_match.group(1)}" if bsr_match else "N/A"
#         #
#         #     # Fallback if first method fails
#         #     if data["BSR"] == "N/A":
#         #
#         #         match = re.search(
#         #             r"#([\d,]+)\s+in",
#         #             driver.page_source,
#         #             re.IGNORECASE
#         #         )
#         #
#         #         if match:
#         #             data["BSR"] = f"#{match.group(1)}"
#         # # 7. BSR & Ratings
#         # try:
#         #     body_text = driver.find_element(By.TAG_NAME, "body").text
#         #
#         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
#         #
#         #     if bsr_match:
#         #         data["BSR"] = int(bsr_match.group(1).replace(",", ""))
#         #     else:
#         #         data["BSR"] = None
#         #
#         #     # Fallback if first method fails
#         #     if data["BSR"] is None:
#         #
#         #         match = re.search(
#         #             r"#([\d,]+)\s+in",
#         #             driver.page_source,
#         #             re.IGNORECASE
#         #         )
#         #
#         #         if match:
#         #             data["BSR"] = int(match.group(1).replace(",", ""))
#         #
#         #     if data["BSR"] is None:
#         #         data["BSR"] = ""
#         #
#         #     rating_el = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt")
#         #     data["Rating"] = rating_el.get_attribute("innerHTML").split(" ")[0]
#         #
#         #     rev_el = driver.find_element(By.ID, "acrCustomerReviewText")
#         #     # data["Reviews"] = rev_el.text.split(" ")[0]
#         #     reviews = re.sub(r"[^\d,]", "", rev_el.text)
#         #     data["Reviews"] = reviews
#         # except: pass

#         # # 8. Product Verification Metrics
#         # if driver.find_elements(By.CSS_SELECTOR, "#altImages img, #main-image-container img"):
#         #     data["Has Images"] = "Yes"
#         # if driver.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, span.a-icon-prime"):
#         #     data["Has Prime"] = "Yes"
#         # try:
#         #     brand_el = driver.find_element(By.ID, "bylineInfo")
#         #     data["Brand"] = brand_el.text.replace("Visit the", "").replace("Store", "").strip()
#         # except: pass

#         # # 9. Seller Count
#         # try:
#         #     s_text = driver.find_element(By.ID, "olp_feature_div").text
#         #     s_match = re.search(r'(\d+)', s_text)
#         #     if s_match: data["Seller Count"] = int(s_match.group(1))
#         # except: pass

#         # FINAL VERIFICATION SCORE
#         # v_score = 0
#         # if data["Has Images"] == "Yes": v_score += 1
#         # if data["Live Price"] is not None: v_score += 1
#         # if data["Rating"] != "N/A": v_score += 1
#         # if data["Brand"] != "Unknown": v_score += 1
#         #
#         # if v_score >= 4: data["Verified"] = "✅ PASS"
#         # elif v_score >= 2: data["Verified"] = "⚠️ PARTIAL"
#         # else: data["Verified"] = "❌ FAIL"
#         # if data["Status"] == "Success":
#         #     data["Verified"] = "✅ PASS"
#         # else:
#         #     data["Verified"] = "❌ FAIL"
#         if data["Status"] == "Success":
#             data["Verified"] = "✅ PASS"

#         elif data["Status"] == "Page Not Found":
#             data["Verified"] = "❌ Invalid ASIN"

#         elif data["Status"] == "Captcha":
#             data["Verified"] = "⚠ Retry"

#         else:
#             data["Verified"] = "❌ FAIL"

#     # except Exception as e:
#     #     data["Status"] = f"Error"
#     except Exception as e:
#         data["Status"] = f"Error: {type(e).__name__}"

#     return data

# def get_csv_download_link(df, filename="amazon_results.csv"):
#     """Generates a persistent base64 download link."""
#     csv = df.to_csv(index=False)
#     b64 = base64.b64encode(csv.encode()).decode()
#     href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="custom-dl-btn">📥 DOWNLOAD CSV REPORT</a>'
#     return href

# # ================= 4. FRONTEND UI LOGIC =================

# def main():
#     st.sidebar.title("⚙️ Amazon Scraper Config")
#     st.sidebar.markdown("---")
#     st.sidebar.subheader("🏪 Shopify Store")

#     stores = all_stores()

#     if stores.empty:
#         st.sidebar.error("No store found in database.")
#         st.stop()

#     # store_names = stores["store_name"].tolist()
#     #
#     # selected_store_name = st.sidebar.selectbox(
#     #     "Select Store",
#     #     store_names
#     # )
#     #
#     # selected_store = stores[
#     #     stores["store_name"] == selected_store_name
#     #     ].iloc[0]
#     store_names = ["Select Store"] + stores["store_name"].tolist()

#     selected_store_name = st.sidebar.selectbox(
#         "Select Store",
#         store_names,
#         index=0
#     )

#     if selected_store_name == "Select Store":
#         st.sidebar.info("👈 Please select a Shopify store.")
#         st.stop()

#     selected_store = stores[
#         stores["store_name"] == selected_store_name
#         ].iloc[0]

#     st.sidebar.success(f"Selected: {selected_store_name}")
#     st.sidebar.caption(selected_store["domain"])

#     token, err = get_access_token(
#         selected_store["domain"],
#         selected_store["client_id"],
#         selected_store["client_secret"]
#     )

#     if not token:
#         st.sidebar.error("❌ Token Failed")
#         st.sidebar.code(err)
#         st.stop()

#     st.sidebar.success("✅ Shopify Connected")
#     products = fetch_all_products(
#         selected_store["domain"],
#         token
#     )
#     st.sidebar.info(f"📦 Products Ready to Scan: {len(products)}")
#     # PERSISTENT DOWNLOAD SECTION
#     if st.session_state.final_df is not None:
#         st.sidebar.success("✅ Results from last scan available")
#         st.sidebar.markdown(get_csv_download_link(st.session_state.final_df), unsafe_allow_html=True)
#         if st.sidebar.button("🗑️ Clear All Results"):
#             st.session_state.final_df = None
#             st.rerun()

#     st.sidebar.divider()

#     # Location Settings
#     LOCATIONS = {
#         "New York (10001)": "10001",
#         "Beverly Hills (90210)": "90210",
#         "Chicago (60601)": "60601",
#         "Tax Free (19701)": "19701"
#     }
#     sel_loc = st.sidebar.selectbox("📍 Target Location", list(LOCATIONS.keys()))
#     target_zip = LOCATIONS[sel_loc]

#     # Filters
#     st.sidebar.subheader("🎯 Scan Filters")
#     # min_disc = st.sidebar.slider("Min Discount %", 0, 90, 0)
#     # uploaded_file = st.sidebar.file_uploader("📂 Upload CSV/XLSX Product Link List", type=['xlsx', 'csv'])
#     shopify_df = build_shopify_dataframe(products)

#     st.title("🛒 Amazon Intelligence Pro")
#     st.info("Select a Shopify Store and click START SCAN to analyze all products.")

#     # if uploaded_file:
#     if not shopify_df.empty:
#         # # Load Data
#         # if uploaded_file.name.endswith('.csv'):
#         #     try: df = pd.read_csv(uploaded_file)
#         #     except: df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
#         # else:
#         #     df = pd.read_excel(uploaded_file)
#         #
#         # df.columns = df.columns.str.strip()
#         # if 'Product Link' not in df.columns:
#         #     st.error("❌ Column 'Product Link' not found!")
#         #     return
#         df = shopify_df.copy()

#         # # Setup Visual Columns
#         # c1, c2, c3, c4 = st.columns(4)
#         c1, c2 = st.columns(2)
#         m_scanned = c1.empty()
#         m_stock = c2.empty()
#         # m_fba = c3.empty()
#         # m_disc = c4.empty()

#         st.subheader("📡 Live Data Extraction")
#         table_placeholder = st.empty()

#         if st.sidebar.button("🚀 START SCAN", type="primary"):
#             st.session_state.is_scanning = True
#             results = []
#             # cnt_fba = 0
#             # cnt_disc = 0
#             cnt_out = 0

#             with st.status("Initializing Engine...", expanded=True) as status:
#                 driver = get_driver()

#                 # Step 1: Change Location
#                 status.update(label=f"Setting location to {target_zip}...")
#                 change_location(driver, target_zip)

#                 # Step 2: Iterate Links
#                 total = len(df)
#                 prog_bar = st.progress(0)

#                 for idx, row in df.iterrows():
#                     url = row['Product Link']
#                     if pd.isna(url) or "amazon" not in str(url): continue

#                     status.update(label=f"Scanning {idx+1}/{total}: {url[:40]}...")

#                     data = scrape_item(driver, url, target_zip)

#                     data["ASIN"] = row["ASIN"]
#                     data["SKU"] = row["SKU"]
#                     # data["Shopify Price"] = row["Shopify Price"]

#                     # shopify_price = clean_price(row["Shopify Price"])
#                     #
#                     # if shopify_price is not None and data["Live Price"] is not None:
#                     #
#                     #     # difference = round(shopify_price - data["Live Price"], 2)
#                     #     #
#                     #     # data["Price Difference"] = difference
#                     #     #
#                     #     # if difference > 0:
#                     #     #     data["Price Status"] = "Shopify Higher"
#                     #     #
#                     #     # elif difference < 0:
#                     #     #     data["Price Status"] = "Amazon Higher"
#                     #     #
#                     #     # else:
#                     #     #     data["Price Status"] = "Same Price"
#                     #     difference = round(shopify_price - data["Live Price"], 2)
#                     #
#                     #     # Always show positive value with $
#                     #     data["Price Difference"] = f"${abs(difference):.2f}"
#                     #
#                     #     if difference > 0:
#                     #         data["Price Status"] = "🟢 Shopify Higher"
#                     #
#                     #     elif difference < 0:
#                     #         data["Price Status"] = "🔴 Amazon Higher"
#                     #
#                     #     else:
#                     #         data["Price Status"] = "🟡 Same Price"
#                     #
#                     # else:
#                     #     data["Price Difference"] = ""
#                     #     data["Price Status"] = ""
#                     #
#                     # # Apply Discount Filter
#                     # d_val = int(data["Discount %"].replace('%', ''))
#                     # if d_val < min_disc:
#                     #     continue

#                     # Update Metrics
#                     if data["Stock"] == "Out of Stock": cnt_out += 1
#                     # if data["Strategy"] == "FBA": cnt_fba += 1
#                     # if d_val > 0: cnt_disc += 1

#                     results.append(data)
#                     st.session_state.final_df = pd.DataFrame(results) # Save to session

#                     # Live UI Update
#                     m_scanned.metric("Processed", f"{idx+1}/{total}")
#                     m_stock.metric("Out Stock", cnt_out)
#                     # m_fba.metric("FBA Found", cnt_fba)
#                     # m_disc.metric("Discounts", cnt_disc)

#                     # Show last 10 rows
#                     # table_placeholder.dataframe(st.session_state.final_df.tail(10), use_container_width=True)
#                     if (idx + 1) % 5 == 0 or idx == total - 1:
#                         table_placeholder.dataframe(
#                             st.session_state.final_df.tail(10),
#                             use_container_width=True
#                         )
#                     prog_bar.progress((idx+1)/total)

#                 driver.quit() # EXIT AFTER LOOP
#                 status.update(label="✅ Scan Complete!", state="complete")

#             st.session_state.is_scanning = False
#             st.success("Verification complete. Use the sidebar to download your CSV.")
#             # st.rerun() # Refresh to show final download button
#     if st.session_state.final_df is not None:

#         st.subheader("📊 Scan Results")
#         display_df = st.session_state.final_df[
#             [
#                 "Title",
#                 "ASIN",
#                 "SKU",
#                 "Zip Used",
#                 "Stock",
#                 "Status",
#                 "Verified"
#             ]
#         ]
#         # st.dataframe(
#         #     st.session_state.final_df,
#         #     use_container_width=True,
#         #     height=600
#         # )
#         st.dataframe(
#             display_df,
#             use_container_width=True,
#             height=600
#         )
#     # # Show full results if already scanned
#     # elif st.session_state.final_df is not None:
#     #     st.subheader("📊 Last Scanned Results")
#     #     st.dataframe(st.session_state.final_df, use_container_width=True)

# if __name__ == "__main__":
#     main()

# import streamlit as st
# import pandas as pd
# import time
# import random
# import re
# import base64
# import sqlite3
# import requests
# import urllib3
# import json
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# DB = "shopify_stores.db"

# def init_db():
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS stores (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 store_name TEXT,
#                 domain TEXT,
#                 client_id TEXT,
#                 client_secret TEXT
#             )
#         """)
#         conn.commit()

# def save_store(name, domain, client_id, secret):
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#             INSERT INTO stores
#             (store_name, domain, client_id, client_secret)
#             VALUES (?, ?, ?, ?)
#         """, (name, domain, client_id, secret))
#         conn.commit()

# def all_stores():
#     with sqlite3.connect(DB) as conn:
#         return pd.read_sql_query("SELECT * FROM stores", conn)

# init_db()

# # =====================================
# # SHOPIFY FUNCTIONS
# # =====================================

# def sh_headers(token):
#     return {
#         "X-Shopify-Access-Token": token,
#         "Content-Type": "application/json"
#     }

# def get_location_id(domain, token):

#     url = f"https://{domain}/admin/api/2024-10/locations.json"

#     r = requests.get(
#         url,
#         headers=sh_headers(token),
#         verify=False
#     )

#     if r.status_code != 200:
#         return None

#     locations = r.json()["locations"]

#     if not locations:
#         return None

#     return locations[0]["id"]

# def get_access_token(domain, client_id, client_secret):
#     url = f"https://{domain}/admin/oauth/access_token"

#     payload = {
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "grant_type": "client_credentials"
#     }

#     try:
#         r = requests.post(url, json=payload, verify=False)

#         if r.status_code == 200:
#             return r.json()["access_token"], ""

#         return "", r.text

#     except Exception as e:
#         return "", str(e)

# def fetch_all_products(domain, token):

#     products = []
#     # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250"
#     # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250&fields=id,title,tags,variants"
#     # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250&fields=id,title,tags,variants"
#     url = (
#     f"https://{domain}/admin/api/2024-10/products.json"
#     "?limit=250"
#     "&fields=id,title,tags,variants"
#      )

#     while url:

#         r = requests.get(
#             url,
#             headers=sh_headers(token),
#             verify=False
#         )

#         if r.status_code != 200:
#             break

#         products.extend(r.json()["products"])

#         link = r.headers.get("Link", "")

#         next_url = None

#         if 'rel="next"' in link:

#             for part in link.split(","):

#                 if 'rel="next"' in part:
#                     next_url = part.split(";")[0].strip("<> ")

#         url = next_url

#     return products
# def get_asin_from_tags(tags):
#     """
#     Extract ASIN from Shopify product tags.
#     Example:
#     Electrical, ASIN:B01F9EU16O, Home
#     """

#     if not tags:
#         return None

#     for tag in tags.split(","):
#         tag = tag.strip()

#         if tag.upper().startswith("ASIN:"):
#             return tag.split(":", 1)[1].strip()

#     return None


# def build_shopify_dataframe(products):
#     """
#     Convert Shopify products into DataFrame
#     containing ASIN, SKU and Amazon URL.
#     """

#     rows = []
#     # for product in products:
#     #
#     #     # asin = get_asin_from_tags(product.get("tags", ""))
#     #     #
#     #     # if not asin:
#     #     #     continue
#     #     asin = get_asin_from_tags(product.get("tags", ""))
#     #
#     #     sku = ""
#     #
#     #     if product.get("variants"):
#     #         sku = product["variants"][0].get("sku", "")
#     #
#     #     # Fallback:
#     #     # if not asin and sku.startswith("GK"):
#     #     #     asin = "B0" + sku[2:]
#     #     if (
#     #             not asin
#     #             and sku
#     #             and sku.startswith("GK")
#     #             and len(sku) > 2
#     #     ):
#     #         asin = "B0" + sku[2:]
#     #
#     #     # Agar phir bhi ASIN nahi bana
#     #     if not asin:
#     #         continue
#     #
#     #     # sku = ""
#     #     #
#     #     # if product.get("variants"):
#     #     #     sku = product["variants"][0].get("sku", "")
#     #     #
#     #     # rows.append({
#     #     #
#     #     #     "ASIN": asin,
#     #     #
#     #     #     "SKU": sku,
#     #     #
#     #     #     "Shopify Title": product.get("title", ""),
#     #     #
#     #     #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     #
#     #     # })
#     #     sku = ""
#     #     # shopify_price = ""
#     #
#     #     if product.get("variants"):
#     #         sku = product["variants"][0].get("sku", "")
#     #         # shopify_price = product["variants"][0].get("price", "")
#     #
#     #     # rows.append({
#     #     #
#     #     #     "ASIN": asin,
#     #     #
#     #     #     "SKU": sku,
#     #     #
#     #     #     "Shopify Title": product.get("title", ""),
#     #     #
#     #     #     # "Shopify Price": shopify_price,
#     #     #
#     #     #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     #
#     #     # })
#     #     rows.append({
#     #         "ASIN": asin,
#     #         "SKU": sku,
#     #         "Shopify Title": product.get("title", ""),
#     #         "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     })
#     for product in products:

#         # 1. Try ASIN from Shopify tags
#         asin = get_asin_from_tags(product.get("tags", ""))

#         # 2. Read SKU
#         sku = ""

#         if product.get("variants"):
#             sku = product["variants"][0].get("sku", "")

#         # 3. Fallback:
#         # If ASIN tag is missing, generate ASIN from SKU
#         if (
#                 not asin
#                 and sku
#                 # and sku.startswith("GK")
#                 and len(sku) > 2
#         ):
#             asin = "B0" + sku[2:]

#         # 4. Skip only if ASIN still not found
#         if not asin:
#             rows.append({

#                 "ASIN": "",

#                 "SKU": sku,

#                 "Shopify Title": product.get("title", ""),

#                 "Product Link": ""

#             })
#             continue

#         # rows.append({
#         #
#         #     "ASIN": asin,
#         #
#         #     "SKU": sku,
#         #
#         #     "Shopify Title": product.get("title", ""),
#         #
#         #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#         #
#         # })
#         variant_id = ""
#         inventory_item_id = ""

#         if product.get("variants"):
#             variant = product["variants"][0]
#             variant_id = variant.get("id")
#             inventory_item_id = variant.get("inventory_item_id")

#         rows.append({

#             "ASIN": asin,

#             "SKU": sku,

#             "Variant ID": variant_id,
#             "Inventory Item ID": inventory_item_id,

#             "Shopify Title": product.get("title", ""),

#             "Product Link": f"https://www.amazon.com/dp/{asin}"

#         })

#     return pd.DataFrame(rows)
# # def mark_shopify_out_of_stock(domain, token, variant_id):

# #     url = f"https://{domain}/admin/api/2024-10/variants/{variant_id}.json"

# #     payload = {
# #         "variant": {
# #             "id": variant_id,
# #             "inventory_quantity": 0
# #         }
# #     }

# #     r = requests.put(
# #         url,
# #         headers=sh_headers(token),
# #         json=payload,
# #         verify=False
# #     )

# #     st.write("STATUS:", r.status_code)
# #     st.write("HEADERS:", dict(r.headers))
# #     st.write("TEXT:", repr(r.text))
# #     if r.status_code == 200:
# #         return True
# #     return False

# def get_inventory_item_id(domain, token, variant_id):

#     url = f"https://{domain}/admin/api/2024-10/variants/{variant_id}.json"

#     r = requests.get(
#         url,
#         headers=sh_headers(token),
#         verify=False
#     )

#     if r.status_code != 200:
#         return None

#     return r.json()["variant"]["inventory_item_id"]

# def get_inventory_level(domain, token, inventory_item_id):

#     url = (
#         f"https://{domain}/admin/api/2024-10/inventory_levels.json"
#         f"?inventory_item_ids={inventory_item_id}"
#     )

#     r = requests.get(
#         url,
#         headers=sh_headers(token),
#         verify=False
#     )

#     if r.status_code != 200:
#         return None, None

#     levels = r.json().get("inventory_levels", [])

#     if not levels:
#         return None, None

#     level = levels[0]

#     return level["location_id"], level["available"]

# def set_inventory_zero(domain, token, inventory_item_id, location_id):

#     url = f"https://{domain}/admin/api/2024-10/inventory_levels/set.json"

#     payload = {
#         "location_id": location_id,
#         "inventory_item_id": inventory_item_id,
#         "available": 0
#     }

#     r = requests.post(
#         url,
#         headers=sh_headers(token),
#         json=payload,
#         verify=False
#     )

#     return r.status_code == 200



# # ================= 1. INITIALIZATION & SESSION STATE =================
# # Ye variables scan khatam hone ke baad bhi data ko save rakhte hain
# if 'final_df' not in st.session_state:
#     st.session_state.final_df = None
# if 'is_scanning' not in st.session_state:
#     st.session_state.is_scanning = False

# # ================= 2. APP CONFIGURATION & CSS =================
# st.set_page_config(
#     page_title="Amazon Intelligence Pro",
#     page_icon="🛒",
#     layout="wide"
# )

# # Professional UI Styling
# st.markdown("""
#     <style>
#     .stApp { background-color: #f8f9fa; }
#     div[data-testid="stMetricValue"] { font-size: 1.4rem; color: #232F3E; font-weight: bold; }
#     div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #555; }
#     .stProgress > div > div > div > div { background-color: #FF9900; }
#     .custom-dl-btn {
#         display: inline-block; padding: 0.8em 1.5em; margin: 10px 0;
#         border-radius: 0.4em; text-decoration: none; font-family: 'Roboto',sans-serif;
#         font-weight: 600; color: #FFFFFF !important; background-color: #232F3E;
#         text-align: center; transition: all 0.2s; width: 100%; border: 1px solid #232F3E;
#     }
#     .custom-dl-btn:hover { background-color: #FF9900; border-color: #FF9900; color: white !important; }
#     </style>
# """, unsafe_allow_html=True)

# # ================= 3. CORE BACKEND SCRAPER LOGIC =================

# def get_driver():
#     options = Options()
#     options.add_argument("--start-maximized")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.page_load_strategy = 'eager'
#     # Use standard User-Agent to avoid early detection
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver

# # def clean_price(price_str):
# #     """
# #     STRICT PRICE CLEANER:
# #     Splits text at '(' to discard unit prices like ($0.83 / count).
# #     """
# #     try:
# #         if pd.isna(price_str) or str(price_str).strip() == "": return None
# #         # Split at parenthesis to remove unit info
# #         clean_str = str(price_str).split('(')[0]
# #         # Remove currency symbols and non-numeric chars except dot
# #         clean_str = re.sub(r'[^\d.]', '', clean_str)
# #         if clean_str.count('.') > 1:
# #             parts = clean_str.split('.')
# #             clean_str = f"{parts[0]}.{parts[1]}"
# #         return float(clean_str)
# #     except:
# #         return None

# def handle_blocking(driver):
#     """Attempts to click 'Continue shopping' if blocked."""
#     try:
#         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping')]")
#         if not btns:
#             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
#         for btn in btns:
#             if "continue" in btn.text.lower():
#                 btn.click()
#                 time.sleep(1.5)
#                 return True
#     except:
#         pass
#     return False

# def change_location(driver, zip_code):
#     """Changes Amazon shipping location to target ZIP."""
#     try:
#         driver.get("https://www.amazon.com")
#         handle_blocking(driver)
#         try:
#             WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
#         except:
#             return False
#         time.sleep(1)
#         try:
#             input_box = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
#             input_box.clear()
#             input_box.send_keys(zip_code)
#             driver.find_element(By.ID, "GLUXZipUpdate").click()
#             time.sleep(1)
#             # Confirm close if needed
#             try:
#                 driver.find_element(By.CSS_SELECTOR, "div.a-popover-footer input, #GLUXConfirmClose").click()
#             except:
#                 pass
#             time.sleep(2)
#             return True
#         except:
#             return False
#     except:
#         return False

# # def _find_labeled_price_in_box(price_box, labels):
# #     """Extracts specific price types (List, Typical, Was) using text labels."""
# #     for lab in labels:
# #         xp_label = (
# #             ".//*[contains(translate(normalize-space(.),"
# #             " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
# #             f" '{lab}')]"
# #         )
# #         try:
# #             label_els = price_box.find_elements(By.XPATH, xp_label)
# #             for _ in label_els:
# #                 xps = [
# #                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
# #                     xp_label + "/following::*[contains(text(),'$')][1]",
# #                 ]
# #                 for xp in xps:
# #                     try:
# #                         el = price_box.find_element(By.XPATH, xp)
# #                         raw = el.get_attribute("innerHTML") or el.text
# #                         val = clean_price(raw)
# #                         if val and val > 1.0:
# #                             return val
# #                     except: pass
# #         except: pass
# #     return None

# def scrape_item(driver, url, current_zip):
#     """Main function to scrape specific product data."""
#     # data = {
#     #     "Title": "Error", "Live Price": None, "List Price": None, "Discount %": "0%",
#     #     "Strategy": "Unknown", "BSR": "N/A", "Stock": "Unknown", "Rating": "N/A",
#     #     "Reviews": 0, "Zip Used": current_zip, "Status": "Failed",
#     #     "Has Images": "No", "Has Prime": "No", "Brand": "Unknown", "Verified": "❌"
#     # }
#     data = {
#         "Title": "Error",
#         "Stock": "Unknown",
#         "Zip Used": current_zip,
#         "Status": "Failed",
#         "Verified": ""
#     }

#     try:
#         # driver.get(url)
#         # # handle_blocking(driver)
#         # time.sleep(random.uniform(0.5, 1.0))
#         driver.get(url)

#         try:
#             WebDriverWait(driver, 5).until(
#                 EC.presence_of_element_located((By.ID, "productTitle"))
#             )
#         except:
#             pass


#         # try:
#         #     data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:60] + "..."
#         #     data["Status"] = "Success"
#         # except:
#         #     data["Status"] = "Blocked/Captcha"
#         #     return data
#         # 1. Product Title
#         try:
#             data["Title"] = driver.find_element(
#                 By.ID,
#                 "productTitle"
#             ).text.strip()[:60] + "..."

#             data["Status"] = "Success"

#         except:

#             page = driver.page_source.lower()

#             if "we couldn't find that page" in page:
#                 data["Status"] = "Page Not Found"

#             elif "robot check" in page:
#                 data["Status"] = "Captcha"

#             elif "sorry, something went wrong" in page:
#                 data["Status"] = "Amazon Error"

#             else:
#                 data["Status"] = "Unknown Error"

#             return data
#         # # 2. Live Price (What you pay now)
#         # try:
#         #     whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
#         #     frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
#         #     data["Live Price"] = float(f"{whole}.{frac}")
#         # except:
#         #     try:
#         #         raw = driver.find_element(By.CSS_SELECTOR, "span.apexPriceToPay span.a-offscreen").get_attribute("innerHTML")
#         #         data["Live Price"] = clean_price(raw)
#         #     except: pass
#         #
#         # # 3. List / Typical Price Logic
#         # try:
#         #     price_containers = driver.find_elements(By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div, #corePrice_desktop_feature_div, #apex_desktop")
#         #     labels = ["typical price", "list price", "was:", "m.r.p"]
#         #     for box in price_containers:
#         #         found_val = _find_labeled_price_in_box(box, labels)
#         #         if found_val:
#         #             data["List Price"] = found_val
#         #             break
#         # except: pass
#         #
#         # # 4. Discount Percentage
#         # if data["Live Price"] and data["List Price"]:
#         #     diff = data["List Price"] - data["Live Price"]
#         #     if diff >= 0.20:
#         #         pct = round((diff / data["List Price"]) * 100)
#         #         data["Discount %"] = f"{pct}%"

#         # 5. Stock Checking
#         try:
#             if driver.find_elements(By.ID, "add-to-cart-button") or driver.find_elements(By.ID, "buy-now-button"):
#                 data["Stock"] = "In Stock"
#             else:
#                 data["Stock"] = "Out of Stock"
#         except: data["Stock"] = "Unknown"

#         # # 6. Fulfillment Strategy
#         # try:
#         #     merchant_text = driver.find_element(By.ID, "merchant-info").text.lower()
#         #     if "amazon" in merchant_text: data["Strategy"] = "FBA"
#         #     else: data["Strategy"] = "FBM"
#         # except: data["Strategy"] = "Unknown"

#         # # 7. BSR & Ratings
#         # try:
#         #     body_text = driver.find_element(By.TAG_NAME, "body").text
#         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
#         #     data["BSR"] = f"#{bsr_match.group(1)}" if bsr_match else "N/A"
#         #
#         #     # Fallback if first method fails
#         #     if data["BSR"] == "N/A":
#         #
#         #         match = re.search(
#         #             r"#([\d,]+)\s+in",
#         #             driver.page_source,
#         #             re.IGNORECASE
#         #         )
#         #
#         #         if match:
#         #             data["BSR"] = f"#{match.group(1)}"
#         # # 7. BSR & Ratings
#         # try:
#         #     body_text = driver.find_element(By.TAG_NAME, "body").text
#         #
#         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
#         #
#         #     if bsr_match:
#         #         data["BSR"] = int(bsr_match.group(1).replace(",", ""))
#         #     else:
#         #         data["BSR"] = None
#         #
#         #     # Fallback if first method fails
#         #     if data["BSR"] is None:
#         #
#         #         match = re.search(
#         #             r"#([\d,]+)\s+in",
#         #             driver.page_source,
#         #             re.IGNORECASE
#         #         )
#         #
#         #         if match:
#         #             data["BSR"] = int(match.group(1).replace(",", ""))
#         #
#         #     if data["BSR"] is None:
#         #         data["BSR"] = ""
#         #
#         #     rating_el = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt")
#         #     data["Rating"] = rating_el.get_attribute("innerHTML").split(" ")[0]
#         #
#         #     rev_el = driver.find_element(By.ID, "acrCustomerReviewText")
#         #     # data["Reviews"] = rev_el.text.split(" ")[0]
#         #     reviews = re.sub(r"[^\d,]", "", rev_el.text)
#         #     data["Reviews"] = reviews
#         # except: pass

#         # # 8. Product Verification Metrics
#         # if driver.find_elements(By.CSS_SELECTOR, "#altImages img, #main-image-container img"):
#         #     data["Has Images"] = "Yes"
#         # if driver.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, span.a-icon-prime"):
#         #     data["Has Prime"] = "Yes"
#         # try:
#         #     brand_el = driver.find_element(By.ID, "bylineInfo")
#         #     data["Brand"] = brand_el.text.replace("Visit the", "").replace("Store", "").strip()
#         # except: pass

#         # # 9. Seller Count
#         # try:
#         #     s_text = driver.find_element(By.ID, "olp_feature_div").text
#         #     s_match = re.search(r'(\d+)', s_text)
#         #     if s_match: data["Seller Count"] = int(s_match.group(1))
#         # except: pass

#         # FINAL VERIFICATION SCORE
#         # v_score = 0
#         # if data["Has Images"] == "Yes": v_score += 1
#         # if data["Live Price"] is not None: v_score += 1
#         # if data["Rating"] != "N/A": v_score += 1
#         # if data["Brand"] != "Unknown": v_score += 1
#         #
#         # if v_score >= 4: data["Verified"] = "✅ PASS"
#         # elif v_score >= 2: data["Verified"] = "⚠️ PARTIAL"
#         # else: data["Verified"] = "❌ FAIL"
#         # if data["Status"] == "Success":
#         #     data["Verified"] = "✅ PASS"
#         # else:
#         #     data["Verified"] = "❌ FAIL"
#         if data["Status"] == "Success":
#             data["Verified"] = "✅ PASS"

#         elif data["Status"] == "Page Not Found":
#             data["Verified"] = "❌ Invalid ASIN"

#         elif data["Status"] == "Captcha":
#             data["Verified"] = "⚠ Retry"

#         else:
#             data["Verified"] = "❌ FAIL"

#     # except Exception as e:
#     #     data["Status"] = f"Error"
#     except Exception as e:
#         data["Status"] = f"Error: {type(e).__name__}"
#         data["Verified"] = "❌ FAIL"

#     return data

# def get_csv_download_link(df, filename="amazon_results.csv"):
#     """Generates a persistent base64 download link."""
#     csv = df.to_csv(index=False)
#     b64 = base64.b64encode(csv.encode()).decode()
#     href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="custom-dl-btn">📥 DOWNLOAD CSV REPORT</a>'
#     return href

# # ================= 4. FRONTEND UI LOGIC =================

# def main():
#     st.sidebar.title("⚙️ Amazon Scraper Config")
#     st.sidebar.markdown("---")
#     st.sidebar.subheader("🏪 Shopify Store")

#     stores = all_stores()

#     if stores.empty:
#         st.sidebar.error("No store found in database.")
#         st.stop()

#     # store_names = stores["store_name"].tolist()
#     #
#     # selected_store_name = st.sidebar.selectbox(
#     #     "Select Store",
#     #     store_names
#     # )
#     #
#     # selected_store = stores[
#     #     stores["store_name"] == selected_store_name
#     #     ].iloc[0]
#     store_names = ["Select Store"] + stores["store_name"].tolist()

#     selected_store_name = st.sidebar.selectbox(
#         "Select Store",
#         store_names,
#         index=0
#     )

#     if selected_store_name == "Select Store":
#         st.sidebar.info("👈 Please select a Shopify store.")
#         st.stop()

#     selected_store = stores[
#         stores["store_name"] == selected_store_name
#         ].iloc[0]

#     st.sidebar.success(f"Selected: {selected_store_name}")
#     st.sidebar.caption(selected_store["domain"])

#     token, err = get_access_token(
#         selected_store["domain"],
#         selected_store["client_id"],
#         selected_store["client_secret"]
#     )

#     if not token:
#         st.sidebar.error("❌ Token Failed")
#         st.sidebar.code(err)
#         st.stop()

#     st.sidebar.success("✅ Shopify Connected")
#     products = fetch_all_products(
#         selected_store["domain"],
#         token
#     )
#     location_id = get_location_id(
#     selected_store["domain"],
#     token
#     )
    
#     st.sidebar.info(f"📦 Products Ready to Scan: {len(products)}")
#     # PERSISTENT DOWNLOAD SECTION
#     if st.session_state.final_df is not None:
#         st.sidebar.success("✅ Results from last scan available")
#         st.sidebar.markdown(get_csv_download_link(st.session_state.final_df), unsafe_allow_html=True)
#         if st.sidebar.button("🗑️ Clear All Results"):
#             st.session_state.final_df = None
#             st.rerun()

#     st.sidebar.divider()

#     # Location Settings
#     LOCATIONS = {
#         "New York (10001)": "10001",
#         "Beverly Hills (90210)": "90210",
#         "Chicago (60601)": "60601",
#         "Tax Free (19701)": "19701"
#     }
#     sel_loc = st.sidebar.selectbox("📍 Target Location", list(LOCATIONS.keys()))
#     target_zip = LOCATIONS[sel_loc]

#     # Filters
#     st.sidebar.subheader("🎯 Scan Filters")
#     # min_disc = st.sidebar.slider("Min Discount %", 0, 90, 0)
#     # uploaded_file = st.sidebar.file_uploader("📂 Upload CSV/XLSX Product Link List", type=['xlsx', 'csv'])
#     shopify_df = build_shopify_dataframe(products)

#     st.title("🛒 Amazon Intelligence Pro")
#     st.info("Select a Shopify Store and click START SCAN to analyze all products.")

#     # if uploaded_file:
#     if not shopify_df.empty:
#         # # Load Data
#         # if uploaded_file.name.endswith('.csv'):
#         #     try: df = pd.read_csv(uploaded_file)
#         #     except: df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
#         # else:
#         #     df = pd.read_excel(uploaded_file)
#         #
#         # df.columns = df.columns.str.strip()
#         # if 'Product Link' not in df.columns:
#         #     st.error("❌ Column 'Product Link' not found!")
#         #     return
#         df = shopify_df.copy()

#         # # Setup Visual Columns
#         # c1, c2, c3, c4 = st.columns(4)
#         c1, c2 = st.columns(2)
#         m_scanned = c1.empty()
#         m_stock = c2.empty()
#         # m_fba = c3.empty()
#         # m_disc = c4.empty()

#         st.subheader("📡 Live Data Extraction")
#         table_placeholder = st.empty()

#         if st.sidebar.button("🚀 START SCAN", type="primary"):
#             st.session_state.is_scanning = True
#             results = []
#             # cnt_fba = 0
#             # cnt_disc = 0
#             cnt_out = 0

#             updated_count = 0
#             failed_count = 0
#             nochange_count = 0

#             with st.status("Initializing Engine...", expanded=True) as status:
#                 driver = get_driver()

#                 # Step 1: Change Location
#                 status.update(label=f"Setting location to {target_zip}...")
#                 change_location(driver, target_zip)

#                 # Step 2: Iterate Links
#                 total = len(df)
#                 prog_bar = st.progress(0)

#                 for idx, row in df.iterrows():
#                     # url = row['Product Link']
#                     # if pd.isna(url) or "amazon" not in str(url): continue
#                     url = row["Product Link"]

#                     if pd.isna(url) or "amazon" not in str(url):
#                         data = {

#                             "Title": row["Shopify Title"],

#                             "Stock": "-",

#                             "Zip Used": target_zip,

#                             "Status": "No ASIN",

#                             "Verified": "N/A",

#                             "ASIN": row["ASIN"],

#                             "SKU": row["SKU"],

#                             "Shopify Update": "-"

#                         }

#                         results.append(data)

#                         st.session_state.final_df = pd.DataFrame(results)

#                         m_scanned.metric("Processed", f"{len(results)}/{total}")

#                         table_placeholder.dataframe(
#                             st.session_state.final_df.tail(10),
#                             use_container_width=True
#                         )

#                         continue

#                     status.update(label=f"Scanning {idx+1}/{total}: {url[:40]}...")

#                     data = scrape_item(driver, url, target_zip)

#                     data["ASIN"] = row["ASIN"]
#                     data["SKU"] = row["SKU"]
#                     variant_id = row["Variant ID"]
#                     inventory_item_id = row["Inventory Item ID"]
#                     # data["Shopify Price"] = row["Shopify Price"]

#                     # shopify_price = clean_price(row["Shopify Price"])
#                     #
#                     # if shopify_price is not None and data["Live Price"] is not None:
#                     #
#                     #     # difference = round(shopify_price - data["Live Price"], 2)
#                     #     #
#                     #     # data["Price Difference"] = difference
#                     #     #
#                     #     # if difference > 0:
#                     #     #     data["Price Status"] = "Shopify Higher"
#                     #     #
#                     #     # elif difference < 0:
#                     #     #     data["Price Status"] = "Amazon Higher"
#                     #     #
#                     #     # else:
#                     #     #     data["Price Status"] = "Same Price"
#                     #     difference = round(shopify_price - data["Live Price"], 2)
#                     #
#                     #     # Always show positive value with $
#                     #     data["Price Difference"] = f"${abs(difference):.2f}"
#                     #
#                     #     if difference > 0:
#                     #         data["Price Status"] = "🟢 Shopify Higher"
#                     #
#                     #     elif difference < 0:
#                     #         data["Price Status"] = "🔴 Amazon Higher"
#                     #
#                     #     else:
#                     #         data["Price Status"] = "🟡 Same Price"
#                     #
#                     # else:
#                     #     data["Price Difference"] = ""
#                     #     data["Price Status"] = ""
#                     #
#                     # # Apply Discount Filter
#                     # d_val = int(data["Discount %"].replace('%', ''))
#                     # if d_val < min_disc:
#                     #     continue

#                     # Update Metrics
#                     # if data["Stock"] == "Out of Stock": cnt_out += 1
#                     # if data["Strategy"] == "FBA": cnt_fba += 1
#                     # if d_val > 0: cnt_disc += 1
#                     # if data["Stock"] == "Out of Stock":
#                     #
#                     #     cnt_out += 1
#                     #
#                     #     updated = mark_shopify_out_of_stock(
#                     #         selected_store["domain"],
#                     #         token,
#                     #         variant_id
#                     #     )
#                     #
#                     #     if updated:
#                     #         data["Shopify Update"] = "✅ Updated"
#                     #
#                     #     else:
#                     #         data["Shopify Update"] = "❌ Failed"
#                     #
#                     # else:
#                     #
#                     #     data["Shopify Update"] = "-"
#                     # if data["Stock"] == "Out of Stock":

#                     #     cnt_out += 1

#                     #     updated = mark_shopify_out_of_stock(
#                     #         selected_store["domain"],
#                     #         token,
#                     #         variant_id
#                     #     )

#                     #     if updated:

#                     #         data["Shopify Update"] = "✅ Updated"

#                     #         updated_count += 1

#                     #     else:

#                     #         data["Shopify Update"] = "❌ Failed"

#                     #         failed_count += 1

#                     # else:

#                     #     data["Shopify Update"] = "➖ No Change"

#                     #     nochange_count += 1

#                     results.append(data)
#                     st.session_state.final_df = pd.DataFrame(results) # Save to session

#                     # Live UI Update
#                     m_scanned.metric("Processed", f"{idx+1}/{total}")
#                     m_stock.metric("Out Stock", cnt_out)
#                     # m_fba.metric("FBA Found", cnt_fba)
#                     # m_disc.metric("Discounts", cnt_disc)

#                     # Show last 10 rows
#                     # table_placeholder.dataframe(st.session_state.final_df.tail(10), use_container_width=True)
#                     if (idx + 1) % 5 == 0 or idx == total - 1:
#                         table_placeholder.dataframe(
#                             st.session_state.final_df.tail(10),
#                             use_container_width=True
#                         )
#                     prog_bar.progress((idx+1)/total)

#                 driver.quit() # EXIT AFTER LOOP
#                 status.update(label="✅ Scan Complete!", state="complete")

#             st.session_state.is_scanning = False
#             st.success("Verification complete. Use the sidebar to download your CSV.")
#             st.info(f"""
#             Processed Products : {total}

#             Amazon Out Of Stock : {cnt_out}

#             Shopify Updated : {updated_count}

#             No Change Required : {nochange_count}

#             Failed Updates : {failed_count}
#             """)
#             # st.rerun() # Refresh to show final download button
#     if st.session_state.final_df is not None:

#         st.subheader("📊 Scan Results")
#         display_df = st.session_state.final_df[
#             [
#                 "Title",
#                 "ASIN",
#                 "SKU",
#                 "Zip Used",
#                 "Stock",
#                 "Status",
#                 "Verified",
#                 "Shopify Update"
#             ]
#         ]
#         # st.dataframe(
#         #     st.session_state.final_df,
#         #     use_container_width=True,
#         #     height=600
#         # )
#         st.dataframe(
#             display_df,
#             use_container_width=True,
#             height=600
#         )
#     # # Show full results if already scanned
#     # elif st.session_state.final_df is not None:
#     #     st.subheader("📊 Last Scanned Results")
#     #     st.dataframe(st.session_state.final_df, use_container_width=True)

# if __name__ == "__main__":
#     main()
#Code before inventory testing
# import streamlit as st
# import pandas as pd
# import time
# import random
# import re
# import base64
# import sqlite3
# import requests
# import urllib3
# import json
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# DB = "shopify_stores.db"


# def init_db():
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#                      CREATE TABLE IF NOT EXISTS stores
#                      (
#                          id
#                          INTEGER
#                          PRIMARY
#                          KEY
#                          AUTOINCREMENT,
#                          store_name
#                          TEXT,
#                          domain
#                          TEXT,
#                          client_id
#                          TEXT,
#                          client_secret
#                          TEXT
#                      )
#                      """)
#         conn.commit()


# def save_store(name, domain, client_id, secret):
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#                      INSERT INTO stores
#                          (store_name, domain, client_id, client_secret)
#                      VALUES (?, ?, ?, ?)
#                      """, (name, domain, client_id, secret))
#         conn.commit()


# def all_stores():
#     with sqlite3.connect(DB) as conn:
#         return pd.read_sql_query("SELECT * FROM stores", conn)


# init_db()


# # =====================================
# # SHOPIFY FUNCTIONS
# # =====================================

# def sh_headers(token):
#     return {
#         "X-Shopify-Access-Token": token,
#         "Content-Type": "application/json"
#     }


# def get_location_id(domain, token):
#     url = f"https://{domain}/admin/api/2024-10/locations.json"

#     r = requests.get(
#         url,
#         headers=sh_headers(token),
#         verify=False
#     )

#     if r.status_code != 200:
#         return None

#     locations = r.json()["locations"]

#     if not locations:
#         return None

#     return locations[0]["id"]


# def get_access_token(domain, client_id, client_secret):
#     url = f"https://{domain}/admin/oauth/access_token"

#     payload = {
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "grant_type": "client_credentials"
#     }

#     try:
#         r = requests.post(url, json=payload, verify=False)

#         if r.status_code == 200:
#             return r.json()["access_token"], ""

#         return "", r.text

#     except Exception as e:
#         return "", str(e)


# def fetch_all_products(domain, token):
#     products = []
#     # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250"
#     # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250&fields=id,title,tags,variants"
#     # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250&fields=id,title,tags,variants"
#     url = (
#         f"https://{domain}/admin/api/2024-10/products.json"
#         "?limit=250"
#         "&fields=id,title,tags,variants"
#     )

#     while url:

#         r = requests.get(
#             url,
#             headers=sh_headers(token),
#             verify=False
#         )

#         if r.status_code != 200:
#             break

#         products.extend(r.json()["products"])

#         link = r.headers.get("Link", "")

#         next_url = None

#         if 'rel="next"' in link:

#             for part in link.split(","):

#                 if 'rel="next"' in part:
#                     next_url = part.split(";")[0].strip("<> ")

#         url = next_url

#     return products


# def get_asin_from_tags(tags):
#     """
#     Extract ASIN from Shopify product tags.
#     Example:
#     Electrical, ASIN:B01F9EU16O, Home
#     """

#     if not tags:
#         return None

#     for tag in tags.split(","):
#         tag = tag.strip()

#         if tag.upper().startswith("ASIN:"):
#             return tag.split(":", 1)[1].strip()

#     return None


# def build_shopify_dataframe(products):
#     """
#     Convert Shopify products into DataFrame
#     containing ASIN, SKU and Amazon URL.
#     """

#     rows = []
#     # for product in products:
#     #
#     #     # asin = get_asin_from_tags(product.get("tags", ""))
#     #     #
#     #     # if not asin:
#     #     #     continue
#     #     asin = get_asin_from_tags(product.get("tags", ""))
#     #
#     #     sku = ""
#     #
#     #     if product.get("variants"):
#     #         sku = product["variants"][0].get("sku", "")
#     #
#     #     # Fallback:
#     #     # if not asin and sku.startswith("GK"):
#     #     #     asin = "B0" + sku[2:]
#     #     if (
#     #             not asin
#     #             and sku
#     #             and sku.startswith("GK")
#     #             and len(sku) > 2
#     #     ):
#     #         asin = "B0" + sku[2:]
#     #
#     #     # Agar phir bhi ASIN nahi bana
#     #     if not asin:
#     #         continue
#     #
#     #     # sku = ""
#     #     #
#     #     # if product.get("variants"):
#     #     #     sku = product["variants"][0].get("sku", "")
#     #     #
#     #     # rows.append({
#     #     #
#     #     #     "ASIN": asin,
#     #     #
#     #     #     "SKU": sku,
#     #     #
#     #     #     "Shopify Title": product.get("title", ""),
#     #     #
#     #     #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     #
#     #     # })
#     #     sku = ""
#     #     # shopify_price = ""
#     #
#     #     if product.get("variants"):
#     #         sku = product["variants"][0].get("sku", "")
#     #         # shopify_price = product["variants"][0].get("price", "")
#     #
#     #     # rows.append({
#     #     #
#     #     #     "ASIN": asin,
#     #     #
#     #     #     "SKU": sku,
#     #     #
#     #     #     "Shopify Title": product.get("title", ""),
#     #     #
#     #     #     # "Shopify Price": shopify_price,
#     #     #
#     #     #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     #
#     #     # })
#     #     rows.append({
#     #         "ASIN": asin,
#     #         "SKU": sku,
#     #         "Shopify Title": product.get("title", ""),
#     #         "Product Link": f"https://www.amazon.com/dp/{asin}"
#     #     })
#     for product in products:

#         # 1. Try ASIN from Shopify tags
#         asin = get_asin_from_tags(product.get("tags", ""))

#         # 2. Read SKU
#         sku = ""

#         if product.get("variants"):
#             sku = product["variants"][0].get("sku", "")

#         # 3. Fallback:
#         # If ASIN tag is missing, generate ASIN from SKU
#         if (
#                 not asin
#                 and sku
#                 # and sku.startswith("GK")
#                 and len(sku) > 2
#         ):
#             asin = "B0" + sku[2:]

#         # 4. Skip only if ASIN still not found
#         if not asin:
#             rows.append({

#                 "ASIN": "",

#                 "SKU": sku,

#                 "Shopify Title": product.get("title", ""),

#                 "Product Link": ""

#             })
#             continue

#         # rows.append({
#         #
#         #     "ASIN": asin,
#         #
#         #     "SKU": sku,
#         #
#         #     "Shopify Title": product.get("title", ""),
#         #
#         #     "Product Link": f"https://www.amazon.com/dp/{asin}"
#         #
#         # })
#         variant_id = ""
#         inventory_item_id = ""

#         if product.get("variants"):
#             variant = product["variants"][0]
#             variant_id = variant.get("id")
#             # st.write(product.get("titile"), product["variants"][0]["id"])
#             inventory_item_id = variant.get("inventory_item_id")

#         rows.append({

#             "ASIN": asin,

#             "SKU": sku,

#             "Variant ID": variant_id,
#             "Inventory Item ID": inventory_item_id,

#             "Shopify Title": product.get("title", ""),

#             "Product Link": f"https://www.amazon.com/dp/{asin}"

#         })

#     return pd.DataFrame(rows)


# # def mark_shopify_out_of_stock(domain, token, variant_id):

# #     url = f"https://{domain}/admin/api/2024-10/variants/{variant_id}.json"

# #     payload = {
# #         "variant": {
# #             "id": variant_id,
# #             "inventory_quantity": 0
# #         }
# #     }

# #     r = requests.put(
# #         url,
# #         headers=sh_headers(token),
# #         json=payload,
# #         verify=False
# #     )

# #     st.write("STATUS:", r.status_code)
# #     st.write("HEADERS:", dict(r.headers))
# #     st.write("TEXT:", repr(r.text))
# #     if r.status_code == 200:
# #         return True
# #     return False

# def get_inventory_item_id(domain, token, variant_id):
#     url = f"https://{domain}/admin/api/2024-10/variants/{variant_id}.json"
#     # st.write(url)

#     r = requests.get(
#         url,
#         headers=sh_headers(token),
#         verify=False
#     )

#     if r.status_code != 200:

#     #    st.write("Variant API Status:", r.status_code)
#     #    st.write("Variant API Response:", r.text)

#        return None

#     data = r.json()

#     # st.write(data)

#     return data["variant"]["inventory_item_id"]


# def get_inventory_level(domain, token, inventory_item_id):
#     url = (
#         f"https://{domain}/admin/api/2024-10/inventory_levels.json"
#         f"?inventory_item_ids={inventory_item_id}"
#     )

#     r = requests.get(
#         url,
#         headers=sh_headers(token),
#         verify=False
#     )

#     if r.status_code != 200:
#        st.write("Inventory Level Status:", r.status_code)
#        st.write("Inventory Level Response:")
#        st.code(r.text)
#        return None, None

#     levels = r.json().get("inventory_levels", [])

#     if not levels:
#         return None, None

#     level = levels[0]

#     return level["location_id"], level["available"]



# def set_inventory_zero(domain, token, inventory_item_id, location_id):
#     url = f"https://{domain}/admin/api/2024-10/inventory_levels/set.json"

#     payload = {
#         "location_id": location_id,
#         "inventory_item_id": inventory_item_id,
#         "available": 0
#     }

#     r = requests.post(
#         url,
#         headers=sh_headers(token),
#         json=payload,
#         verify=False
#     )

#     # return r.status_code == 200
#     if r.status_code != 200:
#        st.write("Set Inventory Status:", r.status_code)
#        st.write("Set Inventory Response:")
#        st.code(r.text)

#     return r.status_code == 200


# # ================= 1. INITIALIZATION & SESSION STATE =================
# # Ye variables scan khatam hone ke baad bhi data ko save rakhte hain
# if 'final_df' not in st.session_state:
#     st.session_state.final_df = None
# if 'is_scanning' not in st.session_state:
#     st.session_state.is_scanning = False

# # ================= 2. APP CONFIGURATION & CSS =================
# st.set_page_config(
#     page_title="Amazon Intelligence Pro",
#     page_icon="🛒",
#     layout="wide"
# )

# # Professional UI Styling
# st.markdown("""
#     <style>
#     .stApp { background-color: #f8f9fa; }
#     div[data-testid="stMetricValue"] { font-size: 1.4rem; color: #232F3E; font-weight: bold; }
#     div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #555; }
#     .stProgress > div > div > div > div { background-color: #FF9900; }
#     .custom-dl-btn {
#         display: inline-block; padding: 0.8em 1.5em; margin: 10px 0;
#         border-radius: 0.4em; text-decoration: none; font-family: 'Roboto',sans-serif;
#         font-weight: 600; color: #FFFFFF !important; background-color: #232F3E;
#         text-align: center; transition: all 0.2s; width: 100%; border: 1px solid #232F3E;
#     }
#     .custom-dl-btn:hover { background-color: #FF9900; border-color: #FF9900; color: white !important; }
#     </style>
# """, unsafe_allow_html=True)


# # ================= 3. CORE BACKEND SCRAPER LOGIC =================

# def get_driver():
#     options = Options()
#     options.add_argument("--start-maximized")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.page_load_strategy = 'eager'
#     # Use standard User-Agent to avoid early detection
#     options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver


# # def clean_price(price_str):
# #     """
# #     STRICT PRICE CLEANER:
# #     Splits text at '(' to discard unit prices like ($0.83 / count).
# #     """
# #     try:
# #         if pd.isna(price_str) or str(price_str).strip() == "": return None
# #         # Split at parenthesis to remove unit info
# #         clean_str = str(price_str).split('(')[0]
# #         # Remove currency symbols and non-numeric chars except dot
# #         clean_str = re.sub(r'[^\d.]', '', clean_str)
# #         if clean_str.count('.') > 1:
# #             parts = clean_str.split('.')
# #             clean_str = f"{parts[0]}.{parts[1]}"
# #         return float(clean_str)
# #     except:
# #         return None

# def handle_blocking(driver):
#     """Attempts to click 'Continue shopping' if blocked."""
#     try:
#         btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping')]")
#         if not btns:
#             btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
#         for btn in btns:
#             if "continue" in btn.text.lower():
#                 btn.click()
#                 time.sleep(1.5)
#                 return True
#     except:
#         pass
#     return False


# def change_location(driver, zip_code):
#     """Changes Amazon shipping location to target ZIP."""
#     try:
#         driver.get("https://www.amazon.com")
#         handle_blocking(driver)
#         try:
#             WebDriverWait(driver, 5).until(
#                 EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
#         except:
#             return False
#         time.sleep(1)
#         try:
#             input_box = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
#             input_box.clear()
#             input_box.send_keys(zip_code)
#             driver.find_element(By.ID, "GLUXZipUpdate").click()
#             time.sleep(1)
#             # Confirm close if needed
#             try:
#                 driver.find_element(By.CSS_SELECTOR, "div.a-popover-footer input, #GLUXConfirmClose").click()
#             except:
#                 pass
#             time.sleep(2)
#             return True
#         except:
#             return False
#     except:
#         return False


# # def _find_labeled_price_in_box(price_box, labels):
# #     """Extracts specific price types (List, Typical, Was) using text labels."""
# #     for lab in labels:
# #         xp_label = (
# #             ".//*[contains(translate(normalize-space(.),"
# #             " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
# #             f" '{lab}')]"
# #         )
# #         try:
# #             label_els = price_box.find_elements(By.XPATH, xp_label)
# #             for _ in label_els:
# #                 xps = [
# #                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
# #                     xp_label + "/following::*[contains(text(),'$')][1]",
# #                 ]
# #                 for xp in xps:
# #                     try:
# #                         el = price_box.find_element(By.XPATH, xp)
# #                         raw = el.get_attribute("innerHTML") or el.text
# #                         val = clean_price(raw)
# #                         if val and val > 1.0:
# #                             return val
# #                     except: pass
# #         except: pass
# #     return None

# def scrape_item(driver, url, current_zip):
#     """Main function to scrape specific product data."""
#     # data = {
#     #     "Title": "Error", "Live Price": None, "List Price": None, "Discount %": "0%",
#     #     "Strategy": "Unknown", "BSR": "N/A", "Stock": "Unknown", "Rating": "N/A",
#     #     "Reviews": 0, "Zip Used": current_zip, "Status": "Failed",
#     #     "Has Images": "No", "Has Prime": "No", "Brand": "Unknown", "Verified": "❌"
#     # }
#     data = {
#         "Title": "Error",
#         "Stock": "Unknown",
#         "Zip Used": current_zip,
#         "Status": "Failed",
#         "Verified": ""
#     }

#     try:
#         # driver.get(url)
#         # # handle_blocking(driver)
#         # time.sleep(random.uniform(0.5, 1.0))
#         driver.get(url)

#         try:
#             WebDriverWait(driver, 5).until(
#                 EC.presence_of_element_located((By.ID, "productTitle"))
#             )
#         except:
#             pass

#         # try:
#         #     data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:60] + "..."
#         #     data["Status"] = "Success"
#         # except:
#         #     data["Status"] = "Blocked/Captcha"
#         #     return data
#         # 1. Product Title
#         try:
#             data["Title"] = driver.find_element(
#                 By.ID,
#                 "productTitle"
#             ).text.strip()[:60] + "..."

#             data["Status"] = "Success"

#         except:

#             page = driver.page_source.lower()

#             if "we couldn't find that page" in page:
#                 data["Status"] = "Page Not Found"

#             elif "robot check" in page:
#                 data["Status"] = "Captcha"

#             elif "sorry, something went wrong" in page:
#                 data["Status"] = "Amazon Error"

#             else:
#                 data["Status"] = "Unknown Error"

#             return data
#         # # 2. Live Price (What you pay now)
#         # try:
#         #     whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
#         #     frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
#         #     data["Live Price"] = float(f"{whole}.{frac}")
#         # except:
#         #     try:
#         #         raw = driver.find_element(By.CSS_SELECTOR, "span.apexPriceToPay span.a-offscreen").get_attribute("innerHTML")
#         #         data["Live Price"] = clean_price(raw)
#         #     except: pass
#         #
#         # # 3. List / Typical Price Logic
#         # try:
#         #     price_containers = driver.find_elements(By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div, #corePrice_desktop_feature_div, #apex_desktop")
#         #     labels = ["typical price", "list price", "was:", "m.r.p"]
#         #     for box in price_containers:
#         #         found_val = _find_labeled_price_in_box(box, labels)
#         #         if found_val:
#         #             data["List Price"] = found_val
#         #             break
#         # except: pass
#         #
#         # # 4. Discount Percentage
#         # if data["Live Price"] and data["List Price"]:
#         #     diff = data["List Price"] - data["Live Price"]
#         #     if diff >= 0.20:
#         #         pct = round((diff / data["List Price"]) * 100)
#         #         data["Discount %"] = f"{pct}%"

#         # 5. Stock Checking
#         try:
#             if driver.find_elements(By.ID, "add-to-cart-button") or driver.find_elements(By.ID, "buy-now-button"):
#                 data["Stock"] = "In Stock"
#             else:
#                 data["Stock"] = "Out of Stock"
#         except:
#             data["Stock"] = "Unknown"

#         # # 6. Fulfillment Strategy
#         # try:
#         #     merchant_text = driver.find_element(By.ID, "merchant-info").text.lower()
#         #     if "amazon" in merchant_text: data["Strategy"] = "FBA"
#         #     else: data["Strategy"] = "FBM"
#         # except: data["Strategy"] = "Unknown"

#         # # 7. BSR & Ratings
#         # try:
#         #     body_text = driver.find_element(By.TAG_NAME, "body").text
#         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
#         #     data["BSR"] = f"#{bsr_match.group(1)}" if bsr_match else "N/A"
#         #
#         #     # Fallback if first method fails
#         #     if data["BSR"] == "N/A":
#         #
#         #         match = re.search(
#         #             r"#([\d,]+)\s+in",
#         #             driver.page_source,
#         #             re.IGNORECASE
#         #         )
#         #
#         #         if match:
#         #             data["BSR"] = f"#{match.group(1)}"
#         # # 7. BSR & Ratings
#         # try:
#         #     body_text = driver.find_element(By.TAG_NAME, "body").text
#         #
#         #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
#         #
#         #     if bsr_match:
#         #         data["BSR"] = int(bsr_match.group(1).replace(",", ""))
#         #     else:
#         #         data["BSR"] = None
#         #
#         #     # Fallback if first method fails
#         #     if data["BSR"] is None:
#         #
#         #         match = re.search(
#         #             r"#([\d,]+)\s+in",
#         #             driver.page_source,
#         #             re.IGNORECASE
#         #         )
#         #
#         #         if match:
#         #             data["BSR"] = int(match.group(1).replace(",", ""))
#         #
#         #     if data["BSR"] is None:
#         #         data["BSR"] = ""
#         #
#         #     rating_el = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt")
#         #     data["Rating"] = rating_el.get_attribute("innerHTML").split(" ")[0]
#         #
#         #     rev_el = driver.find_element(By.ID, "acrCustomerReviewText")
#         #     # data["Reviews"] = rev_el.text.split(" ")[0]
#         #     reviews = re.sub(r"[^\d,]", "", rev_el.text)
#         #     data["Reviews"] = reviews
#         # except: pass

#         # # 8. Product Verification Metrics
#         # if driver.find_elements(By.CSS_SELECTOR, "#altImages img, #main-image-container img"):
#         #     data["Has Images"] = "Yes"
#         # if driver.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, span.a-icon-prime"):
#         #     data["Has Prime"] = "Yes"
#         # try:
#         #     brand_el = driver.find_element(By.ID, "bylineInfo")
#         #     data["Brand"] = brand_el.text.replace("Visit the", "").replace("Store", "").strip()
#         # except: pass

#         # # 9. Seller Count
#         # try:
#         #     s_text = driver.find_element(By.ID, "olp_feature_div").text
#         #     s_match = re.search(r'(\d+)', s_text)
#         #     if s_match: data["Seller Count"] = int(s_match.group(1))
#         # except: pass

#         # FINAL VERIFICATION SCORE
#         # v_score = 0
#         # if data["Has Images"] == "Yes": v_score += 1
#         # if data["Live Price"] is not None: v_score += 1
#         # if data["Rating"] != "N/A": v_score += 1
#         # if data["Brand"] != "Unknown": v_score += 1
#         #
#         # if v_score >= 4: data["Verified"] = "✅ PASS"
#         # elif v_score >= 2: data["Verified"] = "⚠️ PARTIAL"
#         # else: data["Verified"] = "❌ FAIL"
#         # if data["Status"] == "Success":
#         #     data["Verified"] = "✅ PASS"
#         # else:
#         #     data["Verified"] = "❌ FAIL"
#         if data["Status"] == "Success":
#             data["Verified"] = "✅ PASS"

#         elif data["Status"] == "Page Not Found":
#             data["Verified"] = "❌ Invalid ASIN"

#         elif data["Status"] == "Captcha":
#             data["Verified"] = "⚠ Retry"

#         else:
#             data["Verified"] = "❌ FAIL"

#     # except Exception as e:
#     #     data["Status"] = f"Error"
#     except Exception as e:
#         data["Status"] = f"Error: {type(e).__name__}"
#         data["Verified"] = "❌ FAIL"

#     return data


# def get_csv_download_link(df, filename="amazon_results.csv"):
#     """Generates a persistent base64 download link."""
#     csv = df.to_csv(index=False)
#     b64 = base64.b64encode(csv.encode()).decode()
#     href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="custom-dl-btn">📥 DOWNLOAD CSV REPORT</a>'
#     return href


# # ================= 4. FRONTEND UI LOGIC =================

# def main():
#     st.sidebar.title("⚙️ Amazon Scraper Config")
#     st.sidebar.markdown("---")
#     st.sidebar.subheader("🏪 Shopify Store")

#     stores = all_stores()

#     if stores.empty:
#         st.sidebar.error("No store found in database.")
#         st.stop()

#     # store_names = stores["store_name"].tolist()
#     #
#     # selected_store_name = st.sidebar.selectbox(
#     #     "Select Store",
#     #     store_names
#     # )
#     #
#     # selected_store = stores[
#     #     stores["store_name"] == selected_store_name
#     #     ].iloc[0]
#     store_names = ["Select Store"] + stores["store_name"].tolist()

#     selected_store_name = st.sidebar.selectbox(
#         "Select Store",
#         store_names,
#         index=0
#     )

#     if selected_store_name == "Select Store":
#         st.sidebar.info("👈 Please select a Shopify store.")
#         st.stop()

#     selected_store = stores[
#         stores["store_name"] == selected_store_name
#         ].iloc[0]

#     st.sidebar.success(f"Selected: {selected_store_name}")
#     st.sidebar.caption(selected_store["domain"])

#     token, err = get_access_token(
#         selected_store["domain"],
#         selected_store["client_id"],
#         selected_store["client_secret"]
#     )

#     if not token:
#         st.sidebar.error("❌ Token Failed")
#         st.sidebar.code(err)
#         st.stop()

#     st.sidebar.success("✅ Shopify Connected")
#     products = fetch_all_products(
#         selected_store["domain"],
#         token
#     )
#     location_id = get_location_id(
#         selected_store["domain"],
#         token
#     )

#     st.sidebar.info(f"📦 Products Ready to Scan: {len(products)}")
#     # PERSISTENT DOWNLOAD SECTION
#     if st.session_state.final_df is not None:
#         st.sidebar.success("✅ Results from last scan available")
#         st.sidebar.markdown(get_csv_download_link(st.session_state.final_df), unsafe_allow_html=True)
#         if st.sidebar.button("🗑️ Clear All Results"):
#             st.session_state.final_df = None
#             st.rerun()

#     st.sidebar.divider()

#     # Location Settings
#     LOCATIONS = {
#         "New York (10001)": "10001",
#         "Beverly Hills (90210)": "90210",
#         "Chicago (60601)": "60601",
#         "Tax Free (19701)": "19701"
#     }
#     sel_loc = st.sidebar.selectbox("📍 Target Location", list(LOCATIONS.keys()))
#     target_zip = LOCATIONS[sel_loc]

#     # Filters
#     st.sidebar.subheader("🎯 Scan Filters")
#     # min_disc = st.sidebar.slider("Min Discount %", 0, 90, 0)
#     # uploaded_file = st.sidebar.file_uploader("📂 Upload CSV/XLSX Product Link List", type=['xlsx', 'csv'])
#     shopify_df = build_shopify_dataframe(products)

#     st.title("🛒 Amazon Intelligence Pro")
#     st.info("Select a Shopify Store and click START SCAN to analyze all products.")

#     # if uploaded_file:
#     if not shopify_df.empty:
#         # # Load Data
#         # if uploaded_file.name.endswith('.csv'):
#         #     try: df = pd.read_csv(uploaded_file)
#         #     except: df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
#         # else:
#         #     df = pd.read_excel(uploaded_file)
#         #
#         # df.columns = df.columns.str.strip()
#         # if 'Product Link' not in df.columns:
#         #     st.error("❌ Column 'Product Link' not found!")
#         #     return
#         df = shopify_df.copy()

#         # # Setup Visual Columns
#         # c1, c2, c3, c4 = st.columns(4)
#         c1, c2 = st.columns(2)
#         m_scanned = c1.empty()
#         m_stock = c2.empty()
#         # m_fba = c3.empty()
#         # m_disc = c4.empty()

#         st.subheader("📡 Live Data Extraction")
#         table_placeholder = st.empty()

#         if st.sidebar.button("🚀 START SCAN", type="primary"):
#             st.session_state.is_scanning = True
#             results = []
#             # cnt_fba = 0
#             # cnt_disc = 0
#             cnt_out = 0

#             updated_count = 0
#             failed_count = 0
#             nochange_count = 0

#             with st.status("Initializing Engine...", expanded=True) as status:
#                 driver = get_driver()

#                 # Step 1: Change Location
#                 status.update(label=f"Setting location to {target_zip}...")
#                 change_location(driver, target_zip)

#                 # Step 2: Iterate Links
#                 total = len(df)
#                 prog_bar = st.progress(0)

#                 for idx, row in df.iterrows():
#                     # url = row['Product Link']
#                     # if pd.isna(url) or "amazon" not in str(url): continue
#                     url = row["Product Link"]

#                     if pd.isna(url) or "amazon" not in str(url):
#                         data = {

#                             "Title": row["Shopify Title"],

#                             "Stock": "-",

#                             "Zip Used": target_zip,

#                             "Status": "No ASIN",

#                             "Verified": "N/A",

#                             "ASIN": row["ASIN"],

#                             "SKU": row["SKU"],

#                             "Shopify Update": "-"

#                         }

#                         results.append(data)

#                         st.session_state.final_df = pd.DataFrame(results)

#                         m_scanned.metric("Processed", f"{len(results)}/{total}")

#                         table_placeholder.dataframe(
#                             st.session_state.final_df.tail(10),
#                             use_container_width=True
#                         )

#                         continue

#                     status.update(label=f"Scanning {idx + 1}/{total}: {url[:40]}...")

#                     data = scrape_item(driver, url, target_zip)

#                     data["ASIN"] = row["ASIN"]
#                     data["SKU"] = row["SKU"]
#                     variant_id = str(int(row["Variant ID"]))
#                     # st.write("Using variant ID:", variant_id)
#                     # st.write(type(variant_id))
#                     inventory_item_id = row["Inventory Item ID"]
#                     inventory_item_id = int(inventory_item_id)
#                     # data["Shopify Price"] = row["Shopify Price"]

#                     # shopify_price = clean_price(row["Shopify Price"])
#                     #
#                     # if shopify_price is not None and data["Live Price"] is not None:
#                     #
#                     #     # difference = round(shopify_price - data["Live Price"], 2)
#                     #     #
#                     #     # data["Price Difference"] = difference
#                     #     #
#                     #     # if difference > 0:
#                     #     #     data["Price Status"] = "Shopify Higher"
#                     #     #
#                     #     # elif difference < 0:
#                     #     #     data["Price Status"] = "Amazon Higher"
#                     #     #
#                     #     # else:
#                     #     #     data["Price Status"] = "Same Price"
#                     #     difference = round(shopify_price - data["Live Price"], 2)
#                     #
#                     #     # Always show positive value with $
#                     #     data["Price Difference"] = f"${abs(difference):.2f}"
#                     #
#                     #     if difference > 0:
#                     #         data["Price Status"] = "🟢 Shopify Higher"
#                     #
#                     #     elif difference < 0:
#                     #         data["Price Status"] = "🔴 Amazon Higher"
#                     #
#                     #     else:
#                     #         data["Price Status"] = "🟡 Same Price"
#                     #
#                     # else:
#                     #     data["Price Difference"] = ""
#                     #     data["Price Status"] = ""
#                     #
#                     # # Apply Discount Filter
#                     # d_val = int(data["Discount %"].replace('%', ''))
#                     # if d_val < min_disc:
#                     #     continue

#                     # Update Metrics
#                     # if data["Stock"] == "Out of Stock": cnt_out += 1
#                     # if data["Strategy"] == "FBA": cnt_fba += 1
#                     # if d_val > 0: cnt_disc += 1
#                     # if data["Stock"] == "Out of Stock":
#                     #
#                     #     cnt_out += 1
#                     #
#                     #     updated = mark_shopify_out_of_stock(
#                     #         selected_store["domain"],
#                     #         token,
#                     #         variant_id
#                     #     )
#                     #
#                     #     if updated:
#                     #         data["Shopify Update"] = "✅ Updated"
#                     #
#                     #     else:
#                     #         data["Shopify Update"] = "❌ Failed"
#                     #
#                     # else:
#                     #
#                     #     data["Shopify Update"] = "-"
#                     # if data["Stock"] == "Out of Stock":

#                     #     cnt_out += 1

#                     #     updated = mark_shopify_out_of_stock(
#                     #         selected_store["domain"],
#                     #         token,
#                     #         variant_id
#                     #     )

#                     #     if updated:

#                     #         data["Shopify Update"] = "✅ Updated"

#                     #         updated_count += 1

#                     #     else:

#                     #         data["Shopify Update"] = "❌ Failed"

#                     #         failed_count += 1

#                     # else:

#                     #     data["Shopify Update"] = "➖ No Change"

#                     #     nochange_count += 1

#                     if data["Stock"] == "Out of Stock":

#                         cnt_out += 1

#                         # inventory_item_id = get_inventory_item_id(
#                         #     selected_store["domain"],
#                         #     token,
#                         #     variant_id
#                         # )

#                         # if inventory_item_id is None:

#                         #     data["Shopify Update"] = "❌ Item ID"

#                         #     failed_count += 1
#                         inventory_item_id = row["Inventory Item ID"]

#                         if pd.isna(inventory_item_id):
#                            data["Shopify Update"] = "❌ Item ID"
#                            failed_count += 1

#                         else:
#                             # Convert pandas value to proper Shopify ID
#                             inventory_item_id = int(float(inventory_item_id))   

#                             location_id, available = get_inventory_level(
#                                 selected_store["domain"],
#                                 token,
#                                 inventory_item_id
#                             )

#                             if location_id is None:

#                                 data["Shopify Update"] = "❌ Location"

#                                 failed_count += 1

#                             else:

#                                 updated = set_inventory_zero(
#                                     selected_store["domain"],
#                                     token,
#                                     inventory_item_id,
#                                     location_id
#                                 )

#                                 if updated:

#                                     data["Shopify Update"] = "✅ Updated"

#                                     updated_count += 1

#                                 else:

#                                     data["Shopify Update"] = "❌ Failed"

#                                     failed_count += 1

#                     else:

#                         data["Shopify Update"] = "➖ No Change"

#                         nochange_count += 1

#                     results.append(data)
#                     st.session_state.final_df = pd.DataFrame(results)  # Save to session

#                     # Live UI Update
#                     m_scanned.metric("Processed", f"{idx + 1}/{total}")
#                     m_stock.metric("Out Stock", cnt_out)
#                     # m_fba.metric("FBA Found", cnt_fba)
#                     # m_disc.metric("Discounts", cnt_disc)

#                     # Show last 10 rows
#                     # table_placeholder.dataframe(st.session_state.final_df.tail(10), use_container_width=True)
#                     if (idx + 1) % 5 == 0 or idx == total - 1:
#                         table_placeholder.dataframe(
#                             st.session_state.final_df.tail(10),
#                             use_container_width=True
#                         )
#                     prog_bar.progress((idx + 1) / total)

#                 driver.quit()  # EXIT AFTER LOOP
#                 status.update(label="✅ Scan Complete!", state="complete")

#             st.session_state.is_scanning = False
#             st.success("Verification complete. Use the sidebar to download your CSV.")
#             st.info(f"""
#             Processed Products : {total}

#             Amazon Out Of Stock : {cnt_out}

#             Shopify Updated : {updated_count}

#             No Change Required : {nochange_count}

#             Failed Updates : {failed_count}
#             """)
#             # st.rerun() # Refresh to show final download button
#     if st.session_state.final_df is not None:
#         st.subheader("📊 Scan Results")
#         display_df = st.session_state.final_df[
#             [
#                 "Title",
#                 "ASIN",
#                 "SKU",
#                 "Zip Used",
#                 "Stock",
#                 "Status",
#                 "Verified",
#                 "Shopify Update"
#             ]
#         ]
#         # st.dataframe(
#         #     st.session_state.final_df,
#         #     use_container_width=True,
#         #     height=600
#         # )
#         st.dataframe(
#             display_df,
#             use_container_width=True,
#             height=600
#         )
#     # # Show full results if already scanned
#     # elif st.session_state.final_df is not None:
#     #     st.subheader("📊 Last Scanned Results")
#     #     st.dataframe(st.session_state.final_df, use_container_width=True)


# if __name__ == "__main__":
#     main()

import streamlit as st
import pandas as pd
import time
import random
import re
import base64
import sqlite3
import requests
import urllib3
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB = "shopify_stores.db"


def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS stores
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         store_name
                         TEXT,
                         domain
                         TEXT,
                         client_id
                         TEXT,
                         client_secret
                         TEXT
                     )
                     """)
        conn.commit()


def save_store(name, domain, client_id, secret):
    with sqlite3.connect(DB) as conn:
        conn.execute("""
                     INSERT INTO stores
                         (store_name, domain, client_id, client_secret)
                     VALUES (?, ?, ?, ?)
                     """, (name, domain, client_id, secret))
        conn.commit()


def all_stores():
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query("SELECT * FROM stores", conn)


init_db()


# =====================================
# SHOPIFY FUNCTIONS
# =====================================

def sh_headers(token):
    return {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }


def get_location_id(domain, token):
    url = f"https://{domain}/admin/api/2024-10/locations.json"

    r = requests.get(
        url,
        headers=sh_headers(token),
        verify=False
    )

    if r.status_code != 200:
        return None

    locations = r.json()["locations"]

    if not locations:
        return None

    return locations[0]["id"]


def get_access_token(domain, client_id, client_secret):
    url = f"https://{domain}/admin/oauth/access_token"

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    try:
        r = requests.post(url, json=payload, verify=False)

        if r.status_code == 200:
            return r.json()["access_token"], ""

        return "", r.text

    except Exception as e:
        return "", str(e)


def fetch_all_products(domain, token):
    products = []
    # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250"
    # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250&fields=id,title,tags,variants"
    # url = f"https://{domain}/admin/api/2024-10/products.json?limit=250&fields=id,title,tags,variants"
    url = (
        f"https://{domain}/admin/api/2024-10/products.json"
        "?limit=250"
        "&fields=id,title,tags,variants"
    )

    while url:

        r = requests.get(
            url,
            headers=sh_headers(token),
            verify=False
        )

        if r.status_code != 200:
            break

        products.extend(r.json()["products"])

        link = r.headers.get("Link", "")

        next_url = None

        if 'rel="next"' in link:

            for part in link.split(","):

                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip("<> ")

        url = next_url

    return products


def get_asin_from_tags(tags):
    """
    Extract ASIN from Shopify product tags.
    Example:
    Electrical, ASIN:B01F9EU16O, Home
    """

    if not tags:
        return None

    for tag in tags.split(","):
        tag = tag.strip()

        if tag.upper().startswith("ASIN:"):
            return tag.split(":", 1)[1].strip()

    return None


def build_shopify_dataframe(products):
    """
    Convert Shopify products into DataFrame
    containing ASIN, SKU and Amazon URL.
    """

    rows = []
    # for product in products:
    #
    #     # asin = get_asin_from_tags(product.get("tags", ""))
    #     #
    #     # if not asin:
    #     #     continue
    #     asin = get_asin_from_tags(product.get("tags", ""))
    #
    #     sku = ""
    #
    #     if product.get("variants"):
    #         sku = product["variants"][0].get("sku", "")
    #
    #     # Fallback:
    #     # if not asin and sku.startswith("GK"):
    #     #     asin = "B0" + sku[2:]
    #     if (
    #             not asin
    #             and sku
    #             and sku.startswith("GK")
    #             and len(sku) > 2
    #     ):
    #         asin = "B0" + sku[2:]
    #
    #     # Agar phir bhi ASIN nahi bana
    #     if not asin:
    #         continue
    #
    #     # sku = ""
    #     #
    #     # if product.get("variants"):
    #     #     sku = product["variants"][0].get("sku", "")
    #     #
    #     # rows.append({
    #     #
    #     #     "ASIN": asin,
    #     #
    #     #     "SKU": sku,
    #     #
    #     #     "Shopify Title": product.get("title", ""),
    #     #
    #     #     "Product Link": f"https://www.amazon.com/dp/{asin}"
    #     #
    #     # })
    #     sku = ""
    #     # shopify_price = ""
    #
    #     if product.get("variants"):
    #         sku = product["variants"][0].get("sku", "")
    #         # shopify_price = product["variants"][0].get("price", "")
    #
    #     # rows.append({
    #     #
    #     #     "ASIN": asin,
    #     #
    #     #     "SKU": sku,
    #     #
    #     #     "Shopify Title": product.get("title", ""),
    #     #
    #     #     # "Shopify Price": shopify_price,
    #     #
    #     #     "Product Link": f"https://www.amazon.com/dp/{asin}"
    #     #
    #     # })
    #     rows.append({
    #         "ASIN": asin,
    #         "SKU": sku,
    #         "Shopify Title": product.get("title", ""),
    #         "Product Link": f"https://www.amazon.com/dp/{asin}"
    #     })
    for product in products:

        # 1. Try ASIN from Shopify tags
        asin = get_asin_from_tags(product.get("tags", ""))

        # 2. Read SKU
        sku = ""

        if product.get("variants"):
            sku = product["variants"][0].get("sku", "")

        # 3. Fallback:
        # If ASIN tag is missing, generate ASIN from SKU
        if (
                not asin
                and sku
                # and sku.startswith("GK")
                and len(sku) > 2
        ):
            asin = "B0" + sku[2:]

        # 4. Skip only if ASIN still not found
        if not asin:
            rows.append({

                "ASIN": "",

                "SKU": sku,

                "Shopify Title": product.get("title", ""),

                "Product Link": ""

            })
            continue

        # rows.append({
        #
        #     "ASIN": asin,
        #
        #     "SKU": sku,
        #
        #     "Shopify Title": product.get("title", ""),
        #
        #     "Product Link": f"https://www.amazon.com/dp/{asin}"
        #
        # })
        variant_id = ""
        inventory_item_id = ""

        if product.get("variants"):
            variant = product["variants"][0]
            variant_id = variant.get("id")
            # st.write(product.get("titile"), product["variants"][0]["id"])
            inventory_item_id = variant.get("inventory_item_id")

        rows.append({

            "ASIN": asin,

            "SKU": sku,

            "Variant ID": variant_id,
            "Inventory Item ID": inventory_item_id,

            "Shopify Title": product.get("title", ""),

            "Product Link": f"https://www.amazon.com/dp/{asin}"

        })

    return pd.DataFrame(rows)


# def mark_shopify_out_of_stock(domain, token, variant_id):

#     url = f"https://{domain}/admin/api/2024-10/variants/{variant_id}.json"

#     payload = {
#         "variant": {
#             "id": variant_id,
#             "inventory_quantity": 0
#         }
#     }

#     r = requests.put(
#         url,
#         headers=sh_headers(token),
#         json=payload,
#         verify=False
#     )

#     st.write("STATUS:", r.status_code)
#     st.write("HEADERS:", dict(r.headers))
#     st.write("TEXT:", repr(r.text))
#     if r.status_code == 200:
#         return True
#     return False

def get_inventory_item_id(domain, token, variant_id):
    url = f"https://{domain}/admin/api/2024-10/variants/{variant_id}.json"
    # st.write(url)

    r = requests.get(
        url,
        headers=sh_headers(token),
        verify=False
    )

    if r.status_code != 200:

    #    st.write("Variant API Status:", r.status_code)
    #    st.write("Variant API Response:", r.text)

       return None

    data = r.json()

    # st.write(data)

    return data["variant"]["inventory_item_id"]


def get_inventory_level(domain, token, inventory_item_id):
    url = (
        f"https://{domain}/admin/api/2024-10/inventory_levels.json"
        f"?inventory_item_ids={inventory_item_id}"
    )

    r = requests.get(
        url,
        headers=sh_headers(token),
        verify=False
    )

    if r.status_code != 200:
       st.write("Inventory Level Status:", r.status_code)
       st.write("Inventory Level Response:")
       st.code(r.text)
       return None, None

    levels = r.json().get("inventory_levels", [])

    if not levels:
        return None, None

    level = levels[0]

    return level["location_id"], level["available"]



def set_inventory_zero(domain, token, inventory_item_id, location_id):
    url = f"https://{domain}/admin/api/2024-10/inventory_levels/set.json"

    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": 0
    }
    # st.write("Payload =", payload)

    r = requests.post(
        url,
        headers=sh_headers(token),
        json=payload,
        verify=False
    )
    # st.write("Set Inventory Status:", r.status_code)

    # return r.status_code == 200
    if r.status_code != 200:
       st.write("Set Inventory Status:", r.status_code)
       st.write("Set Inventory Response:")
       st.code(r.text)

    return r.status_code == 200


# ================= 1. INITIALIZATION & SESSION STATE =================
# Ye variables scan khatam hone ke baad bhi data ko save rakhte hain
if 'final_df' not in st.session_state:
    st.session_state.final_df = None
if 'is_scanning' not in st.session_state:
    st.session_state.is_scanning = False

# ================= 2. APP CONFIGURATION & CSS =================
st.set_page_config(
    page_title="Amazon Intelligence Pro",
    page_icon="🛒",
    layout="wide"
)

# Professional UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; color: #232F3E; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #555; }
    .stProgress > div > div > div > div { background-color: #FF9900; }
    .custom-dl-btn {
        display: inline-block; padding: 0.8em 1.5em; margin: 10px 0;
        border-radius: 0.4em; text-decoration: none; font-family: 'Roboto',sans-serif;
        font-weight: 600; color: #FFFFFF !important; background-color: #232F3E;
        text-align: center; transition: all 0.2s; width: 100%; border: 1px solid #232F3E;
    }
    .custom-dl-btn:hover { background-color: #FF9900; border-color: #FF9900; color: white !important; }
    </style>
""", unsafe_allow_html=True)


# ================= 3. CORE BACKEND SCRAPER LOGIC =================

def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.page_load_strategy = 'eager'
    # Use standard User-Agent to avoid early detection
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


# def clean_price(price_str):
#     """
#     STRICT PRICE CLEANER:
#     Splits text at '(' to discard unit prices like ($0.83 / count).
#     """
#     try:
#         if pd.isna(price_str) or str(price_str).strip() == "": return None
#         # Split at parenthesis to remove unit info
#         clean_str = str(price_str).split('(')[0]
#         # Remove currency symbols and non-numeric chars except dot
#         clean_str = re.sub(r'[^\d.]', '', clean_str)
#         if clean_str.count('.') > 1:
#             parts = clean_str.split('.')
#             clean_str = f"{parts[0]}.{parts[1]}"
#         return float(clean_str)
#     except:
#         return None

def handle_blocking(driver):
    """Attempts to click 'Continue shopping' if blocked."""
    try:
        btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping')]")
        if not btns:
            btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
        for btn in btns:
            if "continue" in btn.text.lower():
                btn.click()
                time.sleep(1.5)
                return True
    except:
        pass
    return False


def change_location(driver, zip_code):
    """Changes Amazon shipping location to target ZIP."""
    try:
        driver.get("https://www.amazon.com")
        handle_blocking(driver)
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
        except:
            return False
        time.sleep(1)
        try:
            input_box = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
            input_box.clear()
            input_box.send_keys(zip_code)
            driver.find_element(By.ID, "GLUXZipUpdate").click()
            time.sleep(1)
            # Confirm close if needed
            try:
                driver.find_element(By.CSS_SELECTOR, "div.a-popover-footer input, #GLUXConfirmClose").click()
            except:
                pass
            time.sleep(2)
            return True
        except:
            return False
    except:
        return False


# def _find_labeled_price_in_box(price_box, labels):
#     """Extracts specific price types (List, Typical, Was) using text labels."""
#     for lab in labels:
#         xp_label = (
#             ".//*[contains(translate(normalize-space(.),"
#             " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
#             f" '{lab}')]"
#         )
#         try:
#             label_els = price_box.find_elements(By.XPATH, xp_label)
#             for _ in label_els:
#                 xps = [
#                     xp_label + "/following::*[contains(@class,'a-offscreen')][1]",
#                     xp_label + "/following::*[contains(text(),'$')][1]",
#                 ]
#                 for xp in xps:
#                     try:
#                         el = price_box.find_element(By.XPATH, xp)
#                         raw = el.get_attribute("innerHTML") or el.text
#                         val = clean_price(raw)
#                         if val and val > 1.0:
#                             return val
#                     except: pass
#         except: pass
#     return None

def scrape_item(driver, url, current_zip):
    """Main function to scrape specific product data."""
    # data = {
    #     "Title": "Error", "Live Price": None, "List Price": None, "Discount %": "0%",
    #     "Strategy": "Unknown", "BSR": "N/A", "Stock": "Unknown", "Rating": "N/A",
    #     "Reviews": 0, "Zip Used": current_zip, "Status": "Failed",
    #     "Has Images": "No", "Has Prime": "No", "Brand": "Unknown", "Verified": "❌"
    # }
    data = {
        "Title": "Error",
        "Stock": "Unknown",
        "Zip Used": current_zip,
        "Status": "Failed",
        "Verified": ""
    }

    try:
        # driver.get(url)
        # # handle_blocking(driver)
        # time.sleep(random.uniform(0.5, 1.0))
        driver.get(url)

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
        except:
            pass

        # try:
        #     data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:60] + "..."
        #     data["Status"] = "Success"
        # except:
        #     data["Status"] = "Blocked/Captcha"
        #     return data
        # 1. Product Title
        try:
            data["Title"] = driver.find_element(
                By.ID,
                "productTitle"
            ).text.strip()[:60] + "..."

            data["Status"] = "Success"

        except:

            page = driver.page_source.lower()

            if "we couldn't find that page" in page:
                data["Status"] = "Page Not Found"

            elif "robot check" in page:
                data["Status"] = "Captcha"

            elif "sorry, something went wrong" in page:
                data["Status"] = "Amazon Error"

            else:
                data["Status"] = "Unknown Error"

            return data
        # # 2. Live Price (What you pay now)
        # try:
        #     whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
        #     frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
        #     data["Live Price"] = float(f"{whole}.{frac}")
        # except:
        #     try:
        #         raw = driver.find_element(By.CSS_SELECTOR, "span.apexPriceToPay span.a-offscreen").get_attribute("innerHTML")
        #         data["Live Price"] = clean_price(raw)
        #     except: pass
        #
        # # 3. List / Typical Price Logic
        # try:
        #     price_containers = driver.find_elements(By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div, #corePrice_desktop_feature_div, #apex_desktop")
        #     labels = ["typical price", "list price", "was:", "m.r.p"]
        #     for box in price_containers:
        #         found_val = _find_labeled_price_in_box(box, labels)
        #         if found_val:
        #             data["List Price"] = found_val
        #             break
        # except: pass
        #
        # # 4. Discount Percentage
        # if data["Live Price"] and data["List Price"]:
        #     diff = data["List Price"] - data["Live Price"]
        #     if diff >= 0.20:
        #         pct = round((diff / data["List Price"]) * 100)
        #         data["Discount %"] = f"{pct}%"

        # 5. Stock Checking
        try:
            if driver.find_elements(By.ID, "add-to-cart-button") or driver.find_elements(By.ID, "buy-now-button"):
                data["Stock"] = "In Stock"
            else:
                data["Stock"] = "Out of Stock"
        except:
            data["Stock"] = "Unknown"

        # # 6. Fulfillment Strategy
        # try:
        #     merchant_text = driver.find_element(By.ID, "merchant-info").text.lower()
        #     if "amazon" in merchant_text: data["Strategy"] = "FBA"
        #     else: data["Strategy"] = "FBM"
        # except: data["Strategy"] = "Unknown"

        # # 7. BSR & Ratings
        # try:
        #     body_text = driver.find_element(By.TAG_NAME, "body").text
        #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
        #     data["BSR"] = f"#{bsr_match.group(1)}" if bsr_match else "N/A"
        #
        #     # Fallback if first method fails
        #     if data["BSR"] == "N/A":
        #
        #         match = re.search(
        #             r"#([\d,]+)\s+in",
        #             driver.page_source,
        #             re.IGNORECASE
        #         )
        #
        #         if match:
        #             data["BSR"] = f"#{match.group(1)}"
        # # 7. BSR & Ratings
        # try:
        #     body_text = driver.find_element(By.TAG_NAME, "body").text
        #
        #     bsr_match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body_text)
        #
        #     if bsr_match:
        #         data["BSR"] = int(bsr_match.group(1).replace(",", ""))
        #     else:
        #         data["BSR"] = None
        #
        #     # Fallback if first method fails
        #     if data["BSR"] is None:
        #
        #         match = re.search(
        #             r"#([\d,]+)\s+in",
        #             driver.page_source,
        #             re.IGNORECASE
        #         )
        #
        #         if match:
        #             data["BSR"] = int(match.group(1).replace(",", ""))
        #
        #     if data["BSR"] is None:
        #         data["BSR"] = ""
        #
        #     rating_el = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt")
        #     data["Rating"] = rating_el.get_attribute("innerHTML").split(" ")[0]
        #
        #     rev_el = driver.find_element(By.ID, "acrCustomerReviewText")
        #     # data["Reviews"] = rev_el.text.split(" ")[0]
        #     reviews = re.sub(r"[^\d,]", "", rev_el.text)
        #     data["Reviews"] = reviews
        # except: pass

        # # 8. Product Verification Metrics
        # if driver.find_elements(By.CSS_SELECTOR, "#altImages img, #main-image-container img"):
        #     data["Has Images"] = "Yes"
        # if driver.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, span.a-icon-prime"):
        #     data["Has Prime"] = "Yes"
        # try:
        #     brand_el = driver.find_element(By.ID, "bylineInfo")
        #     data["Brand"] = brand_el.text.replace("Visit the", "").replace("Store", "").strip()
        # except: pass

        # # 9. Seller Count
        # try:
        #     s_text = driver.find_element(By.ID, "olp_feature_div").text
        #     s_match = re.search(r'(\d+)', s_text)
        #     if s_match: data["Seller Count"] = int(s_match.group(1))
        # except: pass

        # FINAL VERIFICATION SCORE
        # v_score = 0
        # if data["Has Images"] == "Yes": v_score += 1
        # if data["Live Price"] is not None: v_score += 1
        # if data["Rating"] != "N/A": v_score += 1
        # if data["Brand"] != "Unknown": v_score += 1
        #
        # if v_score >= 4: data["Verified"] = "✅ PASS"
        # elif v_score >= 2: data["Verified"] = "⚠️ PARTIAL"
        # else: data["Verified"] = "❌ FAIL"
        # if data["Status"] == "Success":
        #     data["Verified"] = "✅ PASS"
        # else:
        #     data["Verified"] = "❌ FAIL"
        if data["Status"] == "Success":
            data["Verified"] = "✅ PASS"

        elif data["Status"] == "Page Not Found":
            data["Verified"] = "❌ Invalid ASIN"

        elif data["Status"] == "Captcha":
            data["Verified"] = "⚠ Retry"

        else:
            data["Verified"] = "❌ FAIL"

    # except Exception as e:
    #     data["Status"] = f"Error"
    except Exception as e:
        data["Status"] = f"Error: {type(e).__name__}"
        data["Verified"] = "❌ FAIL"

    return data


def get_csv_download_link(df, filename="amazon_results.csv"):
    """Generates a persistent base64 download link."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="custom-dl-btn">📥 DOWNLOAD CSV REPORT</a>'
    return href


# ================= 4. FRONTEND UI LOGIC =================

def main():
    st.sidebar.title("⚙️ Amazon Scraper Config")
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏪 Shopify Store")

    stores = all_stores()

    if stores.empty:
        st.sidebar.error("No store found in database.")
        st.stop()

    # store_names = stores["store_name"].tolist()
    #
    # selected_store_name = st.sidebar.selectbox(
    #     "Select Store",
    #     store_names
    # )
    #
    # selected_store = stores[
    #     stores["store_name"] == selected_store_name
    #     ].iloc[0]
    store_names = ["Select Store"] + stores["store_name"].tolist()

    selected_store_name = st.sidebar.selectbox(
        "Select Store",
        store_names,
        index=0
    )

    if selected_store_name == "Select Store":
        st.sidebar.info("👈 Please select a Shopify store.")
        st.stop()

    selected_store = stores[
        stores["store_name"] == selected_store_name
        ].iloc[0]

    st.sidebar.success(f"Selected: {selected_store_name}")
    st.sidebar.caption(selected_store["domain"])

    token, err = get_access_token(
        selected_store["domain"],
        selected_store["client_id"],
        selected_store["client_secret"]
    )

    if not token:
        st.sidebar.error("❌ Token Failed")
        st.sidebar.code(err)
        st.stop()

    st.sidebar.success("✅ Shopify Connected")
    products = fetch_all_products(
        selected_store["domain"],
        token
    )
    location_id = get_location_id(
        selected_store["domain"],
        token
    )

    st.sidebar.info(f"📦 Products Ready to Scan: {len(products)}")
    # PERSISTENT DOWNLOAD SECTION
    if st.session_state.final_df is not None:
        st.sidebar.success("✅ Results from last scan available")
        st.sidebar.markdown(get_csv_download_link(st.session_state.final_df), unsafe_allow_html=True)
        if st.sidebar.button("🗑️ Clear All Results"):
            st.session_state.final_df = None
            st.rerun()

    st.sidebar.divider()

    # Location Settings
    LOCATIONS = {
        "New York (10001)": "10001",
        "Beverly Hills (90210)": "90210",
        "Chicago (60601)": "60601",
        "Tax Free (19701)": "19701"
    }
    sel_loc = st.sidebar.selectbox("📍 Target Location", list(LOCATIONS.keys()))
    target_zip = LOCATIONS[sel_loc]

    # Filters
    st.sidebar.subheader("🎯 Scan Filters")
    # min_disc = st.sidebar.slider("Min Discount %", 0, 90, 0)
    # uploaded_file = st.sidebar.file_uploader("📂 Upload CSV/XLSX Product Link List", type=['xlsx', 'csv'])
    shopify_df = build_shopify_dataframe(products)

    st.title("🛒 Amazon Intelligence Pro")
    st.info("Select a Shopify Store and click START SCAN to analyze all products.")

    # if uploaded_file:
    if not shopify_df.empty:
        # # Load Data
        # if uploaded_file.name.endswith('.csv'):
        #     try: df = pd.read_csv(uploaded_file)
        #     except: df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
        # else:
        #     df = pd.read_excel(uploaded_file)
        #
        # df.columns = df.columns.str.strip()
        # if 'Product Link' not in df.columns:
        #     st.error("❌ Column 'Product Link' not found!")
        #     return
        df = shopify_df.copy()

        # # Setup Visual Columns
        # c1, c2, c3, c4 = st.columns(4)
        c1, c2 = st.columns(2)
        m_scanned = c1.empty()
        m_stock = c2.empty()
        # m_fba = c3.empty()
        # m_disc = c4.empty()

        st.subheader("📡 Live Data Extraction")
        table_placeholder = st.empty()

        if st.sidebar.button("🚀 START SCAN", type="primary"):
            st.session_state.is_scanning = True
            results = []
            # cnt_fba = 0
            # cnt_disc = 0
            cnt_out = 0

            updated_count = 0
            failed_count = 0
            nochange_count = 0

            with st.status("Initializing Engine...", expanded=True) as status:
                driver = get_driver()

                # Step 1: Change Location
                status.update(label=f"Setting location to {target_zip}...")
                change_location(driver, target_zip)

                # Step 2: Iterate Links
                total = len(df)
                prog_bar = st.progress(0)

                for idx, row in df.iterrows():
                    # url = row['Product Link']
                    # if pd.isna(url) or "amazon" not in str(url): continue
                    url = row["Product Link"]

                    if pd.isna(url) or "amazon" not in str(url):
                        data = {

                            "Title": row["Shopify Title"],

                            "Stock": "-",

                            "Zip Used": target_zip,

                            "Status": "No ASIN",

                            "Verified": "N/A",

                            "ASIN": row["ASIN"],

                            "SKU": row["SKU"],

                            "Shopify Update": "-"

                        }

                        results.append(data)

                        st.session_state.final_df = pd.DataFrame(results)

                        m_scanned.metric("Processed", f"{len(results)}/{total}")

                        table_placeholder.dataframe(
                            st.session_state.final_df.tail(10),
                            use_container_width=True
                        )

                        continue

                    status.update(label=f"Scanning {idx + 1}/{total}: {url[:40]}...")

                    data = scrape_item(driver, url, target_zip)

                    data["ASIN"] = row["ASIN"]
                    data["SKU"] = row["SKU"]
                    variant_id = str(int(row["Variant ID"]))
                    # st.write("Using variant ID:", variant_id)
                    # st.write(type(variant_id))
                    inventory_item_id = row["Inventory Item ID"]
                    inventory_item_id = int(inventory_item_id)
                    # data["Shopify Price"] = row["Shopify Price"]

                    # shopify_price = clean_price(row["Shopify Price"])
                    #
                    # if shopify_price is not None and data["Live Price"] is not None:
                    #
                    #     # difference = round(shopify_price - data["Live Price"], 2)
                    #     #
                    #     # data["Price Difference"] = difference
                    #     #
                    #     # if difference > 0:
                    #     #     data["Price Status"] = "Shopify Higher"
                    #     #
                    #     # elif difference < 0:
                    #     #     data["Price Status"] = "Amazon Higher"
                    #     #
                    #     # else:
                    #     #     data["Price Status"] = "Same Price"
                    #     difference = round(shopify_price - data["Live Price"], 2)
                    #
                    #     # Always show positive value with $
                    #     data["Price Difference"] = f"${abs(difference):.2f}"
                    #
                    #     if difference > 0:
                    #         data["Price Status"] = "🟢 Shopify Higher"
                    #
                    #     elif difference < 0:
                    #         data["Price Status"] = "🔴 Amazon Higher"
                    #
                    #     else:
                    #         data["Price Status"] = "🟡 Same Price"
                    #
                    # else:
                    #     data["Price Difference"] = ""
                    #     data["Price Status"] = ""
                    #
                    # # Apply Discount Filter
                    # d_val = int(data["Discount %"].replace('%', ''))
                    # if d_val < min_disc:
                    #     continue

                    # Update Metrics
                    # if data["Stock"] == "Out of Stock": cnt_out += 1
                    # if data["Strategy"] == "FBA": cnt_fba += 1
                    # if d_val > 0: cnt_disc += 1
                    # if data["Stock"] == "Out of Stock":
                    #
                    #     cnt_out += 1
                    #
                    #     updated = mark_shopify_out_of_stock(
                    #         selected_store["domain"],
                    #         token,
                    #         variant_id
                    #     )
                    #
                    #     if updated:
                    #         data["Shopify Update"] = "✅ Updated"
                    #
                    #     else:
                    #         data["Shopify Update"] = "❌ Failed"
                    #
                    # else:
                    #
                    #     data["Shopify Update"] = "-"
                    # if data["Stock"] == "Out of Stock":

                    #     cnt_out += 1

                    #     updated = mark_shopify_out_of_stock(
                    #         selected_store["domain"],
                    #         token,
                    #         variant_id
                    #     )

                    #     if updated:

                    #         data["Shopify Update"] = "✅ Updated"

                    #         updated_count += 1

                    #     else:

                    #         data["Shopify Update"] = "❌ Failed"

                    #         failed_count += 1

                    # else:

                    #     data["Shopify Update"] = "➖ No Change"

                    #     nochange_count += 1

                    # if data["Stock"] == "Out of Stock":
                    #
                    #     cnt_out += 1
                    #
                    #     # inventory_item_id = get_inventory_item_id(
                    #     #     selected_store["domain"],
                    #     #     token,
                    #     #     variant_id
                    #     # )
                    #
                    #     # if inventory_item_id is None:
                    #
                    #     #     data["Shopify Update"] = "❌ Item ID"
                    #
                    #     #     failed_count += 1
                    #     inventory_item_id = row["Inventory Item ID"]
                    #
                    #     if pd.isna(inventory_item_id):
                    #        data["Shopify Update"] = "❌ Item ID"
                    #        failed_count += 1
                    #
                    #     else:
                    #         # Convert pandas value to proper Shopify ID
                    #         inventory_item_id = int(float(inventory_item_id))
                    #
                    #         location_id, available = get_inventory_level(
                    #             selected_store["domain"],
                    #             token,
                    #             inventory_item_id
                    #         )
                    #
                    #         if location_id is None:
                    #
                    #             data["Shopify Update"] = "❌ Location"
                    #
                    #             failed_count += 1
                    #
                    #         else:
                    #
                    #             updated = set_inventory_zero(
                    #                 selected_store["domain"],
                    #                 token,
                    #                 inventory_item_id,
                    #                 location_id
                    #             )

                    if data["Stock"] == "Out of Stock":

                        cnt_out += 1

                        inventory_item_id = row["Inventory Item ID"]

                        if pd.isna(inventory_item_id):

                            data["Shopify Update"] = "❌ Item ID"

                            failed_count += 1

                        else:

                            # Convert pandas value to proper Shopify ID
                            inventory_item_id = int(float(inventory_item_id))

                            location_id, available = get_inventory_level(
                                selected_store["domain"],
                                token,
                                inventory_item_id
                            )

                            # ===== DEBUG =====
                            # st.success("Inventory Item ID =", inventory_item_id)
                            # st.success("Type =", type(inventory_item_id))
                            # st.success("Location ID =", location_id)
                            # =================
                            # st.success(f"Inventory Item ID = {inventory_item_id}")
                            # st.success(f"Type = {type(inventory_item_id)}")
                            # st.success(f"Location ID = {location_id}")

                            if location_id is None:

                                data["Shopify Update"] = "❌ Location"

                                failed_count += 1

                            else:

                                updated = set_inventory_zero(
                                    selected_store["domain"],
                                    token,
                                    inventory_item_id,
                                    location_id
                                )
                                # st.write("Updated Value =", updated)

                                if updated:

                                    data["Shopify Update"] = "✅ Updated"

                                    updated_count += 1

                                else:

                                    data["Shopify Update"] = "❌ Failed"

                                    failed_count += 1

                    else:

                        data["Shopify Update"] = "➖ No Change"

                        nochange_count += 1

                    results.append(data)
                    st.session_state.final_df = pd.DataFrame(results)  # Save to session

                    # Live UI Update
                    m_scanned.metric("Processed", f"{idx + 1}/{total}")
                    m_stock.metric("Out Stock", cnt_out)
                    # m_fba.metric("FBA Found", cnt_fba)
                    # m_disc.metric("Discounts", cnt_disc)

                    # Show last 10 rows
                    # table_placeholder.dataframe(st.session_state.final_df.tail(10), use_container_width=True)
                    if (idx + 1) % 5 == 0 or idx == total - 1:
                        table_placeholder.dataframe(
                            st.session_state.final_df.tail(10),
                            use_container_width=True
                        )
                    prog_bar.progress((idx + 1) / total)

                driver.quit()  # EXIT AFTER LOOP
                status.update(label="✅ Scan Complete!", state="complete")

            st.session_state.is_scanning = False
            st.success("Verification complete. Use the sidebar to download your CSV.")
            st.info(f"""
            Processed Products : {total}

            Amazon Out Of Stock : {cnt_out}

            Shopify Updated : {updated_count}

            No Change Required : {nochange_count}

            Failed Updates : {failed_count}
            """)
            # st.rerun() # Refresh to show final download button
    if st.session_state.final_df is not None:
        st.subheader("📊 Scan Results")
        display_df = st.session_state.final_df[
            [
                "Title",
                "ASIN",
                "SKU",
                "Zip Used",
                "Stock",
                "Status",
                "Verified",
                "Shopify Update"
            ]
        ]
        # st.dataframe(
        #     st.session_state.final_df,
        #     use_container_width=True,
        #     height=600
        # )
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600
        )
    # # Show full results if already scanned
    # elif st.session_state.final_df is not None:
    #     st.subheader("📊 Last Scanned Results")
    #     st.dataframe(st.session_state.final_df, use_container_width=True)


if __name__ == "__main__":
    main()