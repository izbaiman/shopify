

import streamlit as st
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# 🎨 FRONTEND CONFIG
# ==========================================
st.set_page_config(page_title="Amazon Hunter Pro", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ Amazon Product Hunter Pro")

# ==========================================
# 📂 CATEGORY DATABASE
# ==========================================
CATEGORY_MAP = {
    "Kitchen & Dining": ["Air Fryers", "Blenders", "Coffee Makers", "Food Storage", "Kitchen Utensils", "Toasters", "Water Bottles", "Cutlery Sets"],
    "Home & Living": ["Bedding", "Bath Towels", "Curtains", "Wall Art", "Vacuum Cleaners", "Storage Bins", "Lamps"],
    "Electronics": ["Headphones", "Bluetooth Speakers", "Smart Watches", "Phone Cases", "Charging Cables", "Gaming Mice", "Keyboards"],
    "Beauty & Personal Care": ["Face Serums", "Makeup Brushes", "Hair Dryers", "Shampoo", "Electric Shavers", "Nail Polish"],
    "Pet Supplies": ["Dog Toys", "Cat Scratchers", "Pet Beds", "Dog Leashes", "Aquarium Filters"],
    "Sports & Outdoors": ["Yoga Mats", "Resistance Bands", "Water Bottles", "Camping Lights", "Sleeping Bags"]
}

# ==========================================
# ⚙️ SIDEBAR - CRITERIA
# ==========================================
st.sidebar.header("1. Criteria")
min_price = st.sidebar.number_input("Min Price ($)", value=10.0)
max_price = st.sidebar.number_input("Max Price ($)", value=200.0)
max_reviews = st.sidebar.number_input("Max Reviews (Competition)", value=1000)
min_rating = st.sidebar.number_input("Min Rating", value=4.0)
min_sales = st.sidebar.number_input("Min Sales (Approx)", value=100)

st.sidebar.header("2. Location")
zip_code = st.sidebar.text_input("Zip Code", placeholder="e.g. 10001 (Leave empty to skip)")

# ==========================================
# 🔍 SEARCH INPUTS (UPDATED)
# ==========================================
st.subheader("Search Settings")

# 1. Choose Method
search_method = st.radio("How do you want to search?", ["Type Specific Keyword", "Select Category"], horizontal=True)

col1, col2 = st.columns([3, 1])

with col1:
    if search_method == "Type Specific Keyword":
        # OPTION A: User types manually
        search_term = st.text_input("Enter Keyword or URL", placeholder="e.g. Wireless charger for iphone")
    else:
        # OPTION B: User selects category
        c1, c2 = st.columns(2)
        with c1:
            main_cat = st.selectbox("Main Category", list(CATEGORY_MAP.keys()))
        with c2:
            sub_options = CATEGORY_MAP[main_cat]
            sub_cat = st.selectbox("Sub-Category", sub_options)
            search_term = sub_cat  # The bot will search for the sub-category name

with col2:
    # THE SCAN LIMIT (User can set this to 1000)
    scan_limit = st.number_input("Items to Scan", value=50, step=50, help="Set this to 1000 to scan many pages.")

start_btn = st.button("🚀 Start Hunting", type="primary")
status_area = st.empty()

# ==========================================
# 🛠️ BACKEND LOGIC
# ==========================================

def init_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_argument("--headless") # Uncomment to hide browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    return driver

def change_location(driver, zip_code):
    if not zip_code: return
    st.toast(f"✈️ Changing location to {zip_code}...")
    driver.get("https://www.amazon.com")
    time.sleep(3)
    try:
        driver.find_element(By.ID, "nav-global-location-popover-link").click()
        time.sleep(2)
        zip_input = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput")))
        zip_input.clear()
        zip_input.send_keys(zip_code) 
        time.sleep(1)
        driver.find_element(By.ID, "GLUXZipUpdate").click()
        time.sleep(1)
        try:
            driver.find_element(By.NAME, "glowDoneButton").click()
        except:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "Done" in btn.text or "Continue" in btn.text:
                    btn.click()
                    break
        time.sleep(3)
        st.toast("✅ Location Updated!")
    except:
        st.error("⚠️ Auto-Location Failed. Please set it manually in the popup.")
        time.sleep(5)

def extract_data(card):
    data = {}
    
    # 1. TITLE
    try: data['Title'] = card.find_element(By.CSS_SELECTOR, "h2").text
    except: data['Title'] = "Unknown"
    
    # 2. PRICE
    try:
        el = card.find_element(By.CSS_SELECTOR, ".a-price .a-offscreen")
        data['Price'] = float(el.get_attribute("innerHTML").replace("$","").replace(",","").split("<")[0])
    except: 
        try:
            el = card.find_element(By.CSS_SELECTOR, "span.a-price-whole")
            data['Price'] = float(el.text.replace(",","").replace(".",""))
        except:
            data['Price'] = 0.0
    
    # 3. REVIEWS
    data['Reviews'] = 0
    try:
        el = card.find_element(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
        data['Reviews'] = int(el.text.replace(",","").replace("(","").replace(")",""))
    except: pass

    # 4. RATING
    try:
        el = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
        data['Rating'] = float(el.get_attribute("innerHTML").split(" ")[0])
    except: data['Rating'] = 0.0
    
    # 5. SALES
    try:
        el = card.find_element(By.CSS_SELECTOR, "span.a-size-base.a-color-secondary")
        text = el.text.lower()
        if "bought" in text:
            num = text.split(" bought")[0].replace("+","").strip()
            if "k" in num: data['Sales'] = float(num.replace("k","")) * 1000
            else: data['Sales'] = float(num)
        else: data['Sales'] = 0
    except: data['Sales'] = 0

    # 6. LINK
    data['Link'] = "No Link"
    try:
        data['Link'] = card.find_element(By.CSS_SELECTOR, "h2 a").get_attribute("href")
    except:
        try:
            data['Link'] = card.find_element(By.CSS_SELECTOR, "a.s-no-outline").get_attribute("href")
        except: pass
    
    return data

# ==========================================
# 🏃 RUN LOGIC
# ==========================================
if start_btn:
    if not search_term:
        st.error("❌ Please enter a keyword or select a category.")
    else:
        status_area.info("🚀 Initializing Browser...")
        driver = init_driver()
        change_location(driver, zip_code)
        
        # Build URL
        if "http" in search_term:
            target_url = search_term
        else:
            target_url = f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}"
            
        driver.get(target_url)
        time.sleep(2)
        
        scanned_count = 0
        all_winning_products = []
        page_num = 1
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        # --- 🔄 LOOP UNTIL LIMIT REACHED (e.g. 1000 items) ---
        while scanned_count < scan_limit:
            
            # Scroll to load
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2) 
            driver.execute_script("window.scrollTo(0, 0);") 
            
            cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
            
            if not cards:
                st.warning(f"⚠️ No products found on page {page_num}. Ending.")
                break
                
            status_text.write(f"🔎 Scanning Page {page_num}... Found {len(cards)} items here. (Total Scanned: {scanned_count}/{scan_limit})")

            for card in cards:
                if scanned_count >= scan_limit: 
                    break
                
                item = extract_data(card)
                scanned_count += 1
                progress_bar.progress(min(scanned_count / scan_limit, 1.0))
                
                if item['Price'] == 0.0: continue

                # CHECK CRITERIA
                if (item['Price'] >= min_price and 
                    item['Price'] <= max_price and 
                    item['Reviews'] <= max_reviews and 
                    item['Rating'] >= min_rating and 
                    item['Sales'] >= min_sales):
                    
                    all_winning_products.append(item)
            
            if scanned_count >= scan_limit:
                break
            
            # --- NEXT PAGE LOGIC ---
            try:
                next_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.s-pagination-next"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                time.sleep(1)
                next_btn.click()
                page_num += 1
                time.sleep(random.uniform(2, 5)) # Wait before next page
            except:
                st.warning("⚠️ No more pages available.")
                break

        driver.quit()
        status_area.success("🎉 Hunt Complete!")
        
        if all_winning_products:
            df = pd.DataFrame(all_winning_products)
            st.subheader(f"✅ Found {len(all_winning_products)} Winning Products")
            
            st.dataframe(
                df, 
                column_config={
                    "Link": st.column_config.LinkColumn("Product Link"),
                    "Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
                    "Price": st.column_config.NumberColumn(format="$%.2f")
                }
            )
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name='amazon_hunter_results.csv',
                mime='text/csv',
            )
        else:
            st.error(f"😔 Scanned {scanned_count} items but found 0 matches. Relax your filters.")