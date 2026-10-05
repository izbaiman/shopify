

import streamlit as st
import pandas as pd
import requests
import json
import time
import re
import os
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile
from pathlib import Path

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shopify Master Bot", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .log-box { background-color: #0e1117; color: #00ff00; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; height: 350px; overflow-y: auto; border: 1px solid #333; }
    .stButton>button { background-color: #ff9900; color: white; border-radius: 8px; font-weight: bold; height: 3em; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---
def clean_uc_cache():
    cache_path = os.path.join(os.environ.get('APPDATA', ''), 'undetected_chromedriver')
    if os.path.exists(cache_path):
        try:
            shutil.rmtree(cache_path, ignore_errors=True)
        except: pass

def scrub_everything(text):
    if not text: return ""
    text = re.sub(r'amazon|walmart|prime|shipped from|sold by', '', text, flags=re.IGNORECASE)
    text = re.sub(r'›?\s*See more product details|›?\s*See details', '', text, flags=re.IGNORECASE)
    return text.strip()

def calculate_matrix_profit(cost):
    # 1. Strict 10% profit if price is <= 15
    if cost <= 15:
        return 10
    elif cost <= 50:
        return 16
    elif cost <= 100:
        return 22
    elif cost <= 150:
        return 27
    elif cost <= 200:
        return 33
    elif cost <= 250:
        return 37
    elif cost <= 300:
        return 45
    elif cost <= 350:
        return 55
    elif cost <= 400:
        return 60
    elif cost <= 450:
        return 65
    elif cost <= 500:
        return 70
    elif cost <= 550:
        return 75
    elif cost <= 600:
        return 78
    elif cost <= 650:
        return 80
    else:
        return 100

def extract_custom_sku_from_amazon(driver, prefix):
    try:
        # Extract the ASIN (Amazon Standard Identification Number)
        asin_element = driver.find_element(By.ID, "ASIN")  # SKU or ASIN element
        if asin_element:
            asin = asin_element.get_attribute("value").strip()  # Get the ASIN value
            # Replace the first two characters of the ASIN with the prefix
            modified_sku = f"{prefix}{asin[2:]}"  # Keep the rest of the ASIN after the first two characters
            return modified_sku
    except Exception as e:
        print(f"Error extracting ASIN: {e}")
        return f"{prefix}-{int(time.time())}"  # Fallback SKU if unable to extract the ASIN

# --- SHOPIFY COLLECTION HELPERS ---
def get_or_create_collection(domain, token, collection_name):
    """
    Checks if a custom collection exists. If yes, returns ID.
    If no, creates it and returns the new ID.
    """
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    
    # 1. Check existing collections
    get_url = f"https://{domain}/admin/api/2024-10/custom_collections.json?limit=250"
    try:
        res = requests.get(get_url, headers=headers, verify=False)
        if res.status_code == 200:
            collections = res.json().get("custom_collections", [])
            for c in collections:
                if c['title'].strip().lower() == collection_name.strip().lower():
                    return c['id']
    except Exception as e:
        st.error(f"Error checking collections: {e}")

    # 2. Create new if not found
    post_url = f"https://{domain}/admin/api/2024-10/custom_collections.json"
    payload = {"custom_collection": {"title": collection_name}}
    try:
        res = requests.post(post_url, headers=headers, json=payload, verify=False)
        if res.status_code == 201:
            return res.json()['custom_collection']['id']
    except Exception as e:
        st.error(f"Error creating collection: {e}")
    
    return None

def add_product_to_collection(domain, token, product_id, collection_id):
    """Links a product to a collection"""
    url = f"https://{domain}/admin/api/2024-10/collects.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    payload = {
        "collect": {
            "product_id": product_id,
            "collection_id": collection_id
        }
    }
    requests.post(url, headers=headers, json=payload, verify=False)

# --- FRONTEND UI ---
st.title("🛡️ SC Collection Master Dashboard")

with st.sidebar:
    st.header("🔑 Credentials & Config")
    
    raw_domain = st.text_input("Shopify Store URL", value="scento-3618.myshopify.com").strip()
    shop_domain = raw_domain.replace("https://", "").replace("http://", "").split('/')[0]
    access_token = st.text_input("Access Token", value="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").strip()
    
    st.divider()
    st.subheader("🛍️ Product Settings")
    # Separate Inputs for Vendor vs Collection
    vendor_name = st.text_input("Vendor Name (Brand)", value="SC Store").strip()
    collection_name_input = st.text_input("Collection Name (Folder)", value="New Arrivals").strip()
    
    sku_input = st.text_input("SKU Prefix (e.g. CS)", value="CS").strip()
    zip_code = st.text_input("Amazon Zip Code", value="10001").strip()
    
    st.divider()
    excel_file = st.file_uploader("Upload Listings Excel", type=["xlsx"])

# --- DASHBOARD COLUMNS ---
col_monitor, col_logs = st.columns([1, 1])

with col_monitor:
    st.subheader("📺 Captcha & Browser Monitor")
    browser_frame = st.empty()
    browser_frame.info("Awaiting Start...")

with col_logs:
    st.subheader("📝 Activity Logs")
    log_window = st.empty()
    logs = []

def build_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # unique profile each run to reduce collisions
    user_data_dir = Path(tempfile.mkdtemp(prefix="uc_profile_"))
    options.add_argument(f"--user-data-dir={user_data_dir}")

    # try normal startup first with version_main=146 to match your system
    try:
        return uc.Chrome(options=options, version_main=146)
    except Exception:
        # remove stale cached patched driver and retry once
        cache_root = Path(os.environ.get("APPDATA", "")) / "undetected_chromedriver"
        stale_driver = cache_root / "undetected_chromedriver.exe"
        stale_unpack = cache_root / "undetected"

        try:
            if stale_driver.exists():
                stale_driver.unlink()
        except Exception:
            pass

        try:
            if stale_unpack.exists():
                shutil.rmtree(stale_unpack, ignore_errors=True)
        except Exception:
            pass

        time.sleep(1)
        return uc.Chrome(options=options, version_main=146)

def add_log(msg):
    logs.append(f"> {time.strftime('%H:%M:%S')} | {msg}")
    log_window.markdown(f'<div class="log-box">{"<br>".join(logs[::-1])}</div>', unsafe_allow_html=True)

# --- BOT LOGIC ---
if st.button("RUN MASTER BOT 🚀"):
    if not excel_file or not access_token:
        st.error("Please upload file and enter Access Token!")
    else:
        sku_prefix_input = sku_input 
        clean_uc_cache()
        add_log("Initializing...")
        
        # 1. SETUP COLLECTION FIRST (Do this once before scraping)
        add_log(f"Checking Collection: '{collection_name_input}'...")
        target_collection_id = get_or_create_collection(shop_domain, access_token, collection_name_input)
        
        if target_collection_id:
            add_log(f"✅ Collection Ready! ID: {target_collection_id}")
        else:
            add_log("⚠️ Could not create collection. Products will be uploaded without collection.")

        driver = build_driver()
        wait = WebDriverWait(driver, 15)
        try:
            # 2. Set Location
            driver.get("https://www.amazon.com")
            time.sleep(2)
            try:
                driver.find_element(By.ID, "nav-global-location-popover-link").click()
                z_input = wait.until(EC.presence_of_element_located((By.ID, "GLUXZipUpdateInput")))
                z_input.send_keys(zip_code)
                driver.find_element(By.ID, "GLUXZipUpdate").click()
                time.sleep(2)
                driver.refresh()
            except: pass

            # 3. Process Products
            df = pd.read_excel(excel_file)
            product_api_url = f"https://{shop_domain}/admin/api/2024-10/products.json"
            headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}

            for index, row in df.iterrows():
                link = str(row.get('Product Link', ''))
                if not link or "http" not in link: continue

                driver.get(link)
                time.sleep(3)
                shot = driver.get_screenshot_as_png()
                browser_frame.image(shot, caption=f"Row {index+1}")

                # --- SCRAPE ---
                try:
                    bc_els = driver.find_elements(By.CSS_SELECTOR, "#wayfinding-breadcrumbs_container li a, .a-breadcrumb li a")
                    tags_list = [el.text.strip() for el in bc_els if el.text.strip() and "‹" not in el.text]
                    final_tags = ", ".join(tags_list)
                except: final_tags = ""

                images = []
                for img in driver.find_elements(By.CSS_SELECTOR, "#altImages img, #landingImage"):
                    src = img.get_attribute("src")
                    if src and "/images/I/" in src:
                        high_res = re.sub(r'\._[A-Z0-9,_-]+_\.', '.', src)
                        if high_res not in images: images.append(high_res)

                try:
                    raw_title = driver.find_element(By.ID, "productTitle").text
                    title = scrub_everything(raw_title)
                except: title = "Product " + str(index)
                
                try:
                    raw_desc = driver.find_element(By.ID, "feature-bullets").get_attribute("innerHTML")
                    desc = scrub_everything(raw_desc)
                except: desc = ""

                # --- CALCULATE ---
                sku = extract_custom_sku_from_amazon(driver, sku_prefix_input)

                cost = float(re.sub(r'[^\d.]', '', str(row.get('Amazon Price', '0'))))
                
                profit = calculate_matrix_profit(cost)
                selling_price = round(cost + profit, 2)
                compare_price = round(selling_price + 8.0, 2)

                # --- UPLOAD PRODUCT ---
                payload = {
                    "product": {
                        "title": title,
                        "body_html": f"<div>{desc}</div>",
                        "vendor": vendor_name, # User Defined Vendor
                        "tags": final_tags,
                        "status": "active",
                        "variants": [{
                            "price": str(selling_price),
                            "compare_at_price": str(compare_price),
                            "cost": str(cost),
                            "sku": sku
                        }],
                        "images": [{"src": img} for img in images[:8]]
                    }
                }

                res = requests.post(product_api_url, headers=headers, json=payload, verify=False)
                
                if res.status_code == 201:
                    new_product = res.json()
                    new_product_id = new_product['product']['id']
                    add_log(f"✅ Created: {sku}")
                    
                    # --- ADD TO COLLECTION ---
                    if target_collection_id:
                        add_product_to_collection(shop_domain, access_token, new_product_id, target_collection_id)
                        add_log(f"   -> Added to Collection: {collection_name_input}")
                else:
                    add_log(f"❌ Error {sku}: {res.text[:50]}")

            add_log("🏁 Completed!")
            st.balloons()

        except Exception as e:
            add_log(f"💥 Error: {str(e)}")
        finally:
            driver.quit()