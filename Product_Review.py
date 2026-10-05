

import streamlit as st
import pandas as pd
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# ================= 1. APP CONFIGURATION =================
st.set_page_config(
    page_title="Amazon Intelligence Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a professional look
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stDataFrame { border: 1px solid #ddd; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# ================= 2. CORE LOGIC (BACKEND) =================

def get_driver():
    """Initializes a robust Chrome driver with anti-crash options."""
    options = Options()
    # options.add_argument("--headless=new") # Uncomment for invisible mode
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def clean_price(price_str):
    """Safely converts price string to float."""
    try:
        if pd.isna(price_str) or str(price_str).strip() == "": return None
        clean = re.sub(r'[^\d.]', '', str(price_str))
        return float(clean)
    except:
        return None

def change_location(driver, zip_code):
    """Robust location changer that handles popups gracefully."""
    try:
        driver.get("https://www.amazon.com")
        time.sleep(2)
        
        # Check if location is already set (optional optimization) to avoid reload
        # skipping for stability in this demo
        
        try:
            driver.find_element(By.ID, "nav-global-location-popover-link").click()
        except:
            return False # Button not found, maybe blocked

        time.sleep(1.5)
        
        # Wait for Input
        try:
            input_box = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput"))
            )
            input_box.clear()
            input_box.send_keys(zip_code)
            
            # Click Apply
            driver.find_element(By.ID, "GLUXZipUpdate").click()
            time.sleep(1)
            
            # Click "Continue" or "Done"
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, "div.a-popover-footer span.a-button-inner input")
                if btns: btns[0].click()
            except: pass
            
            time.sleep(2) # Allow page refresh
            return True
        except:
            return False
    except:
        return False

def scrape_item(driver, url):
    """Scrapes one item with heavy error handling."""
    data = {
        "Title": "Error", "Live Price": 0.0, 
        "Stock": "Unknown", "Strategy": "Unknown", 
        "BSR": "N/A", "Status": "Failed"
    }
    
    try:
        driver.get(url)
        # Random sleep to prevent bot detection
        time.sleep(random.uniform(1.5, 3.0)) 
        
        # 1. Title
        try: 
            data["Title"] = driver.find_element(By.ID, "productTitle").text.strip()[:30] + "..."
            data["Status"] = "Success"
        except: 
            data["Status"] = "Captcha/Error"
            return data # Exit early if we can't even see the page

        # 2. Price (Try multiple selectors)
        try:
            whole = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text
            frac = driver.find_element(By.CSS_SELECTOR, ".a-price-fraction").text
            data["Live Price"] = float(f"{whole}.{frac}")
        except:
            try:
                raw_p = driver.find_element(By.ID, "priceblock_ourprice").text
                data["Live Price"] = clean_price(raw_p)
            except:
                data["Live Price"] = None

        # 3. Stock
        try:
            stk = driver.find_element(By.ID, "availability").text.lower()
            data["Stock"] = "In Stock" if "in stock" in stk or "left in stock" in stk else "Out of Stock"
        except: 
            data["Stock"] = "Unknown"

        # 4. Strategy
        try:
            ships_from = ""
            boxes = driver.find_elements(By.CSS_SELECTOR, "div.tabular-buybox-text")
            for b in boxes:
                if "Ships from" in b.text:
                    ships_from = b.text
                    break
            data["Strategy"] = "FBA" if "Amazon" in ships_from else "FBM"
        except: 
            data["Strategy"] = "Unknown"

        # 5. BSR
        try:
            page = driver.find_element(By.TAG_NAME, "body").text
            if "Best Sellers Rank" in page:
                start = page.find("Best Sellers Rank")
                data["BSR"] = page[start:start+40].split(":")[1].split("(")[0].strip()
        except: 
            data["BSR"] = "-"

    except Exception:
        data["Status"] = "Crash"
    
    return data

# ================= 3. FRONTEND UI =================

def main():
    # --- Sidebar ---
    st.sidebar.header("⚙️ Configuration")
    use_ny = st.sidebar.checkbox("Check New York (10001)", value=True)
    use_ca = st.sidebar.checkbox("Check Beverly Hills (90210)", value=True)
    
    st.sidebar.divider()
    uploaded_file = st.sidebar.file_uploader("📂 Upload Product List", type=['xlsx', 'csv'])

    # --- Main Header ---
    st.title("🛒 Amazon Intelligence Dashboard")
    st.markdown("Monitor Price, Stock, and Buy Box Strategy in real-time.")

    if uploaded_file:
        # Load Data
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        df.columns = df.columns.str.strip() # Clean headers

        # Validation
        if 'Product Link' not in df.columns:
            st.error("❌ File missing 'Product Link' column.")
            return
        
        # Stats Placeholders
        c1, c2, c3, c4 = st.columns(4)
        m_total = c1.empty()
        m_success = c2.empty()
        m_increase = c3.empty()
        m_decrease = c4.empty()

        # Data Table Placeholder
        st.subheader("📡 Live Data Feed")
        table_placeholder = st.empty()
        
        # Start Button
        if st.sidebar.button("🚀 Start Scan", type="primary"):
            
            # Init Driver
            with st.status("Initializing System...", expanded=True) as status:
                st.write("🔧 Launching Chrome Driver...")
                try:
                    driver = get_driver()
                except Exception as e:
                    st.error(f"Failed to launch Chrome: {e}")
                    return

                # Init Tracking
                results = []
                count_ok = 0
                count_inc = 0
                count_dec = 0
                
                # --- PROCESSING LOOP ---
                total_rows = len(df)
                progress_bar = st.progress(0)

                # Set Initial Location
                current_zip = "10001" if use_ny else None
                if current_zip:
                    st.write(f"📍 Setting Location to NY ({current_zip})...")
                    change_location(driver, current_zip)

                for index, row in df.iterrows():
                    link = row.get('Product Link')
                    old_price = clean_price(row.get('Amazon Price', 0))

                    if pd.isna(link) or "http" not in str(link):
                        continue

                    # Fallback logic check
                    if index > 0 and results[-1]['Status'] == "Captcha/Error":
                        st.write("⚠️ Pausing for 5 seconds due to detection...")
                        time.sleep(5)

                    # Scrape
                    status.update(label=f"Scanning {index+1}/{total_rows}: Product ID {index}...", state="running")
                    item_data = scrape_item(driver, link)

                    # Check for fallback location (Price missing in NY)
                    if use_ca and (item_data['Live Price'] is None or item_data['Stock'] == "Out of Stock"):
                        st.write("✈️ Switching to CA (90210) to check stock...")
                        change_location(driver, "90210")
                        item_data = scrape_item(driver, link) # Re-scrape
                        # Reset back to NY for next item
                        if use_ny: change_location(driver, "10001")

                    # Logic
                    item_data['Link'] = link
                    item_data['Old Price'] = old_price
                    
                    trend = "SAME"
                    if item_data['Live Price'] and old_price:
                        if item_data['Live Price'] > old_price:
                            trend = "INCREASED"
                            count_inc += 1
                        elif item_data['Live Price'] < old_price:
                            trend = "DECREASED"
                            count_dec += 1
                    
                    item_data['Trend'] = trend
                    if item_data['Status'] == 'Success': count_ok += 1

                    results.append(item_data)
                    
                    # --- UPDATE UI ---
                    # 1. Update Metrics
                    m_total.metric("Scraped", f"{index+1}/{total_rows}")
                    m_success.metric("Success Rate", f"{round((count_ok/(index+1))*100)}%")
                    m_increase.metric("Price Hikes", count_inc, delta_color="inverse")
                    m_decrease.metric("Price Drops", count_dec, delta_color="normal")

                    # 2. Update Table
                    res_df = pd.DataFrame(results)
                    
                    # Reorder columns for readability
                    cols = ["Title", "Old Price", "Live Price", "Trend", "Stock", "Strategy", "BSR", "Status"]
                    final_view = res_df[cols]

                    # Styled Dataframe
                    table_placeholder.dataframe(
                        final_view, 
                        height=400,
                        use_container_width=True
                    )
                    
                    progress_bar.progress((index+1)/total_rows)

                driver.quit()
                status.update(label="✅ Scan Complete", state="complete", expanded=False)
            
            # Download
            st.success("Analysis Finished.")
            final_csv = pd.DataFrame(results).to_csv(index=False).encode('utf-8')
            st.sidebar.download_button(
                "📥 Download Report", 
                final_csv, 
                "amazon_report.csv", 
                "text/csv"
            )

    else:
        st.info("👈 Please upload your Excel or CSV file in the sidebar to begin.")

if __name__ == "__main__":
    main()