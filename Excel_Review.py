

import streamlit as st
import pandas as pd
import time
import random
import re
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ================= 1. APP CONFIGURATION & CSS =================
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
        display: inline-block; padding: 0.6em 1.2em; margin: 0 0.3em 0.3em 0;
        border-radius: 0.3em; text-decoration: none; font-family: 'Roboto',sans-serif;
        font-weight: 600; color: #FFFFFF !important; background-color: #232F3E;
        text-align: center; transition: all 0.2s; width: 100%; border: 1px solid #232F3E;
    }
    .custom-dl-btn:hover { background-color: #FF9900; border-color: #FF9900; }
    </style>
""", unsafe_allow_html=True)

# ================= 2. CORE BACKEND LOGIC =================

def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.page_load_strategy = 'eager' 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def clean_price(price_str):
    """
    STRICT PRICE CLEANER:
    1. Splits text at '(' to immediately discard '($0.83 / count)'.
    2. Removes currency symbols and letters.
    3. Returns pure float of the main price.
    """
    try:
        if pd.isna(price_str) or str(price_str).strip() == "": return None
        
        # KEY FIX: Split at parenthesis to remove unit prices
        # Example: "$4.97 ($0.83 / count)" becomes "$4.97 "
        clean_str = str(price_str).split('(')[0]
        
        # Remove anything that isn't a digit or a dot
        clean_str = re.sub(r'[^\d.]', '', clean_str)
        
        # Handle cases where multiple dots might appear (rare error prevention)
        if clean_str.count('.') > 1:
            parts = clean_str.split('.')
            clean_str = f"{parts[0]}.{parts[1]}"
            
        return float(clean_str)
    except:
        return None

def handle_blocking(driver):
    try:
        btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue shopping')]")
        if not btns:
            btns = driver.find_elements(By.CSS_SELECTOR, "button.a-button-text")
        for btn in btns:
            if "continue" in btn.text.lower():
                btn.click()
                time.sleep(1.5)
                return True
    except: pass
    return False

def change_location(driver, zip_code):
    try:
        driver.get("https://www.amazon.com")
        handle_blocking(driver)
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
        except: return False 
        time.sleep(1)
        try:
            input_box = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
            input_box.clear()
            input_box.send_keys(zip_code)
            driver.find_element(By.ID, "GLUXZipUpdate").click()
            time.sleep(1)
            try: driver.find_element(By.CSS_SELECTOR, "div.a-popover-footer input, #GLUXConfirmClose").click()
            except: pass
            time.sleep(1.5)
            return True
        except: return False
    except: return False

def scrape_item(driver, url, current_zip):
    # Initialize all columns to ensure structure is preserved
    data = {
        "Title": "Error", 
        "Live Price": None, 
        "List Price": None, 
        "Discount %": "0%",
        "Strategy": "Unknown", 
        "BSR": "N/A", 
        "Stock": "Unknown", 
        "Rating": "N/A", 
        "Reviews": 0,
        "Zip Used": current_zip, 
        "Status": "Failed"
    }
    
    try:
        driver.get(url)
        handle_blocking(driver)
        time.sleep(random.uniform(1.2, 2.0))

        # 1. TITLE
        try: 
            data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:60] + "..."
            data["Status"] = "Success"
        except: 
            data["Status"] = "Captcha/Error"
            return data 

        # 2. LIVE PRICE
        try:
            whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
            frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
            data["Live Price"] = float(f"{whole}.{frac}")
        except:
            try:
                # Fallback
                raw = driver.find_element(By.CSS_SELECTOR, "span.apexPriceToPay span.a-offscreen").get_attribute("innerHTML")
                data["Live Price"] = clean_price(raw)
            except: pass

        # 3. LIST PRICE (STRICT FIX)
        # We target the hidden 'a-offscreen' element inside 'a-text-price'.
        # We DO NOT read the text of the parent, because the parent often contains the unit price.
        try:
            # This selector specifically finds the strike-through price numbers
            strike_elements = driver.find_elements(By.CSS_SELECTOR, "span.a-text-price span.a-offscreen")
            
            for elm in strike_elements:
                price_text = elm.get_attribute("innerHTML")
                cleaned = clean_price(price_text)
                # If we get a valid number greater than 0, use it.
                # Since clean_price strips the '(' parts, this is safe.
                if cleaned and cleaned > 0:
                    data["List Price"] = cleaned
                    break
        except:
            data["List Price"] = None
        
        # 4. DISCOUNT %
        try:
            badge = driver.find_element(By.CSS_SELECTOR, "span.savingsPercentage").text
            data["Discount %"] = badge.replace("-", "").strip()
        except:
            if data["Live Price"] and data["List Price"] and data["List Price"] > data["Live Price"]:
                diff = data["List Price"] - data["Live Price"]
                pct = round((diff / data["List Price"]) * 100)
                data["Discount %"] = f"{pct}%"

        # 5. STOCK STATUS (BUTTON CHECK ONLY)
        # If "Add to Cart" or "Buy Now" exists -> In Stock.
        # Otherwise -> Out of Stock.
        try:
            add_btn = driver.find_elements(By.ID, "add-to-cart-button")
            buy_btn = driver.find_elements(By.ID, "buy-now-button")
            
            if len(add_btn) > 0 or len(buy_btn) > 0:
                data["Stock"] = "In Stock"
            else:
                # Check for "See All Buying Options" (In stock but no buybox)
                opts = driver.find_elements(By.XPATH, "//a[contains(text(), 'See All Buying Options')]")
                if len(opts) > 0:
                     data["Stock"] = "In Stock (3rd Party)"
                else:
                    data["Stock"] = "Out of Stock"
        except:
            data["Stock"] = "Out of Stock"

        # 6. STRATEGY (FBA vs FBM)
        try:
            buybox_text = ""
            divs = driver.find_elements(By.CSS_SELECTOR, "#merchant-info, #fulfillment-buy-box")
            for d in divs: buybox_text += d.text + " "
            buybox_text = buybox_text.lower()
            
            if "ships from amazon" in buybox_text: data["Strategy"] = "FBA"
            elif "ships from" in buybox_text: data["Strategy"] = "FBM"
            elif data["Live Price"]: data["Strategy"] = "FBA (Probable)"
            else: data["Strategy"] = "Unknown"
        except: data["Strategy"] = "Unknown"

        # 7. BSR & Ratings
        try:
            body = driver.find_element(By.TAG_NAME, "body").text
            match = re.search(r"Best Sellers Rank:? #?([\d,]+)", body)
            data["BSR"] = f"#{match.group(1)}" if match else "N/A"
            
            rating = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt").get_attribute("innerHTML")
            data["Rating"] = rating.split(" ")[0]
            
            revs = driver.find_element(By.ID, "acrCustomerReviewText").text
            data["Reviews"] = revs.replace("ratings", "").strip()
        except: pass

    except Exception:
        data["Status"] = "Crash"
    
    return data

def get_csv_download_link(df, filename="amazon_results.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="custom-dl-btn">📥 Download CSV</a>'
    return href

# ================= 3. FRONTEND UI =================

def main():
    st.sidebar.title("⚙️ Config Panel")
    
    LOCATIONS = {
        "New York (10001)": "10001",
        "Beverly Hills (90210)": "90210",
        "Chicago (60601)": "60601",
        "Delaware (Tax Free) (19701)": "19701"
    }
    
    sel_locs = st.sidebar.multiselect("📍 Target Locations", list(LOCATIONS.keys()), default=["New York (10001)"])
    zip_codes = [LOCATIONS[k] for k in sel_locs]

    st.sidebar.divider()
    uploaded_file = st.sidebar.file_uploader("📂 Upload Product List", type=['xlsx', 'csv'])
    st.sidebar.divider()
    download_placeholder = st.sidebar.empty()

    st.title("🛒 Amazon Intelligence Pro (Strict Mode)")

    if uploaded_file:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        
        df.columns = df.columns.str.strip()
        if 'Product Link' not in df.columns:
            st.error("❌ Input file must have 'Product Link' column.")
            return

        old_price_col = None
        for c in df.columns:
            if "price" in c.lower() and "link" not in c.lower():
                old_price_col = c
                break

        c1, c2, c3, c4 = st.columns(4)
        m_scanned = c1.empty()
        m_stock = c2.empty()
        m_fba = c3.empty()
        m_disc = c4.empty()

        st.subheader("📡 Live Data Stream")
        table_placeholder = st.empty()

        if st.sidebar.button("🚀 START SCAN", type="primary"):
            with st.status("Processing...", expanded=True) as status:
                driver = get_driver()
                results = []
                cnt_fba = 0
                cnt_disc = 0
                cnt_out_stock = 0
                cnt_inc = 0
                cnt_dec = 0
                
                current_browser_zip = None
                total = len(df)
                prog_bar = st.progress(0)
                
                for idx, row in df.iterrows():
                    link = row.get('Product Link')
                    old_p_val = clean_price(row.get(old_price_col, 0)) if old_price_col else 0
                    
                    if pd.isna(link): continue
                    status.update(label=f"Scanning Item {idx+1}/{total}...", state="running")
                    
                    final_data = None
                    prio_zips = zip_codes
                    if current_browser_zip in zip_codes:
                        prio_zips = [current_browser_zip] + [z for z in zip_codes if z != current_browser_zip]
                    
                    for z_code in prio_zips:
                        if current_browser_zip != z_code:
                            if change_location(driver, z_code): current_browser_zip = z_code
                        data = scrape_item(driver, link, current_browser_zip)
                        if data['Live Price']:
                            final_data = data
                            break
                        final_data = data 
                    
                    # Add back Link and Old Price for reference
                    final_data['Product Link'] = link
                    final_data['Old Price'] = old_p_val
                    
                    # Calculate Trend
                    trend = "SAME"
                    if final_data['Live Price'] and old_p_val:
                        if final_data['Live Price'] > old_p_val:
                            trend = "INCREASED"
                            cnt_inc += 1
                        elif final_data['Live Price'] < old_p_val:
                            trend = "DECREASED"
                            cnt_dec += 1
                    final_data['Trend'] = trend

                    if final_data['Stock'] == "Out of Stock": cnt_out_stock += 1
                    if "FBA" in final_data['Strategy']: cnt_fba += 1
                    if final_data['Discount %'] != "0%": cnt_disc += 1
                    
                    results.append(final_data)
                    
                    m_scanned.metric("Scanned", f"{idx+1}/{total}")
                    m_stock.metric("Out of Stock", cnt_out_stock)
                    m_fba.metric("FBA Found", cnt_fba)
                    m_disc.metric("Discounts", cnt_disc)
                    
                    res_df = pd.DataFrame(results)
                    
                    # FORCE ALL COLUMNS TO SHOW
                    cols_order = [
                        "Title", "Live Price", "List Price", "Discount %", 
                        "Trend", "Old Price", "Strategy", "BSR", 
                        "Stock", "Rating", "Reviews", "Zip Used", "Status", "Product Link"
                    ]
                    
                    # Reorder dataframe columns based on list, keeping any extra ones that might exist
                    existing_cols = [c for c in cols_order if c in res_df.columns]
                    view_df = res_df[existing_cols]
                    
                    table_placeholder.dataframe(view_df.tail(10), use_container_width=True, height=400)
                    download_placeholder.markdown(get_csv_download_link(res_df), unsafe_allow_html=True)
                    prog_bar.progress((idx+1)/total)

                driver.quit()
                status.update(label="✅ Complete!", state="complete", expanded=False)
                st.success("Done.")

if __name__ == "__main__":
    main()

