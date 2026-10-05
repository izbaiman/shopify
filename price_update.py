import streamlit as st
import requests
import sqlite3
import time
import re
import os
import shutil
import subprocess
import urllib3
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# =====================================================
# US ZIP PRESETS
# =====================================================

US_ZIP_PRESETS = {
    "New York, NY":     "10001",
    "Los Angeles, CA":  "90001",
    "Chicago, IL":      "60601",
    "Houston, TX":      "77001",
    "Phoenix, AZ":      "85001",
    "Philadelphia, PA": "19101",
    "San Antonio, TX":  "78201",
    "Dallas, TX":       "75201",
    "Miami, FL":        "33101",
    "Seattle, WA":      "98101",
    "Custom ZIP...":    "",
}


# =====================================================
# DATABASE — SQLite, stores per-store credentials
# =====================================================

DB_PATH = "shopify_stores.db"


def db_init():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name      TEXT    UNIQUE NOT NULL,
            domain        TEXT    NOT NULL,
            client_id     TEXT    NOT NULL,
            client_secret TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    con.commit()
    con.close()


def db_save_store(store_name, domain, client_id, client_secret):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT INTO stores (store_name, domain, client_id, client_secret)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(store_name) DO UPDATE SET
            domain        = excluded.domain,
            client_id     = excluded.client_id,
            client_secret = excluded.client_secret
    """, (store_name, domain, client_id, client_secret))
    con.commit()
    con.close()


def db_load_stores():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT store_name, domain, client_id, client_secret FROM stores ORDER BY store_name"
    ).fetchall()
    con.close()
    return rows   # list of (Storename, domain, client_id, client_secret)


def db_delete_store(store_name):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM stores WHERE store_name = ?", (store_name,))
    con.commit()
    con.close()


# =====================================================
# SHOPIFY OAUTH — fresh token every run
# =====================================================

def get_oauth_token(domain, client_id, client_secret):
    url = f"https://{domain}/admin/oauth/access_token"
    payload = {
        "client_id":     client_id,
        "client_secret": client_secret,
        "grant_type":    "client_credentials",
    }
    try:
        r = requests.post(url, json=payload, timeout=15, verify=False)
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            if token:
                return token, ""
            return "", "Response OK but no access_token in response"
        return "", f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return "", str(e)


# =====================================================
# PROFIT MATRIX
# Amazon price → profit to add on top
# =====================================================

def profit_for(cost):
    table = [
        (15,  10), (50,  16), (100, 22), (150, 27),
        (200, 33), (250, 37), (300, 45), (350, 55),
        (400, 60), (450, 65), (500, 70), (550, 75),
        (600, 78), (650, 80),
    ]
    for threshold, profit in table:
        if cost <= threshold:
            return profit
    return 100


# =====================================================
# CLEAN OLD DRIVER CACHE
# =====================================================

def clean_uc_cache():
    paths = [
        os.path.join(os.environ.get("APPDATA", ""), "undetected_chromedriver"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "undetected_chromedriver"),
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=True)
            except:
                pass


# =====================================================
# CHROME VERSION
# =====================================================

def get_chrome_version():
    try:
        command = r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
        output = subprocess.check_output(command, shell=True).decode()
        version = output.strip().split()[-1]
        return int(version.split(".")[0])
    except:
        return 148


# =====================================================
# CREATE DRIVER
# =====================================================

def create_driver():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-allow-origins=*")
    return uc.Chrome(version_main=get_chrome_version(), options=options, use_subprocess=True)


# =====================================================
# FETCH ALL SHOPIFY PRODUCTS (cursor pagination)
# =====================================================

def fetch_all_products(shop_domain, headers, log_fn):
    all_products = []
    url = f"https://{shop_domain}/admin/api/2024-10/products.json?limit=250"
    page = 1
    while url:
        log_fn(f"   ↳ Fetching page {page} ...")
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        batch = resp.json().get("products", [])
        all_products.extend(batch)
        log_fn(f"   ↳ Page {page}: {len(batch)} products (total: {len(all_products)})")
        link_header = resp.headers.get("Link", "")
        next_url = None
        for part in link_header.split(","):
            if 'rel="next"' in part:
                m = re.search(r'<([^>]+)>', part)
                if m:
                    next_url = m.group(1)
                    break
        url = next_url
        page += 1
    return all_products


# =====================================================
# SET AMAZON DELIVERY ZIP
# =====================================================

def set_amazon_zip(driver, zip_code, log_fn=None):
    def _log(m):
        if log_fn: log_fn(m)
    try:
        _log(f"🌍 Setting Amazon delivery ZIP: {zip_code} ...")
        driver.get("https://www.amazon.com")
        time.sleep(4)
        wait = WebDriverWait(driver, 10)
        for sel in ["#nav-global-location-popover-link", "#glow-ingress-line2"]:
            try:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel))).click()
                _log("   ↳ Opened location popup")
                break
            except: pass
        time.sleep(2)
        inp = None
        for sel in ["input[data-action-type='MODAL_INPUT']", "#GLUXZipUpdateInput",
                    "input[placeholder*='ZIP']", "input[placeholder*='zip']"]:
            try:
                inp = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, sel)))
                inp.clear(); inp.send_keys(zip_code)
                _log(f"   ↳ Entered ZIP: {zip_code}")
                break
            except: pass
        time.sleep(1)
        for sel in ["span[data-action-type='MODAL_SUBMIT'] input",
                    "#GLUXZipUpdate", "input.a-button-input"]:
            try:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel))).click()
                _log("   ↳ Applied ZIP")
                break
            except: pass
        time.sleep(2)
        for sel in ["button[data-action-type='DISMISS']", "#GLUXConfirmClose"]:
            try: driver.find_element(By.CSS_SELECTOR, sel).click(); break
            except: pass
        time.sleep(2)
        _log(f"✅ Amazon location set → ZIP {zip_code}")
        return True
    except Exception as e:
        _log(f"⚠️  Location set failed: {str(e)[:100]}")
        return False


# =====================================================
# SKU → ASIN
# =====================================================

def sku_to_asin(sku):
    if not sku:
        return None
    sku = str(sku).strip()
    if len(sku) < 3 or "-" in sku:
        return None
    return "B0" + sku[2:]


# =====================================================
# SCRAPE AMAZON PRICE
# =====================================================

def scrape_amazon_price(driver, asin):
    driver.get(f"https://www.amazon.com/dp/{asin}?th=1")
    time.sleep(5)
    selectors = [
        ".a-price .a-offscreen",
        "#corePriceDisplay_desktop_feature_div .a-offscreen",
        ".priceToPay .a-offscreen",
        "#price_inside_buybox",
        "#priceblock_ourprice",
        ".aok-offscreen",
    ]
    for sel in selectors:
        try:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                txt = el.get_attribute("innerHTML") or el.text or ""
                price = re.sub(r"[^\d.]", "", txt.strip())
                if price:
                    val = float(price)
                    if 0.5 < val < 10000:
                        return val
        except: pass
    return None


# ╔══════════════════════════════════════════════════╗
# ║               STREAMLIT UI                       ║
# ╚══════════════════════════════════════════════════╝

db_init()

st.set_page_config(page_title="Amazon ↔ Shopify Price Sync", layout="wide")
st.title("🔄 Amazon ↔ Shopify Price Sync")
st.caption("Fetches ALL products → ASIN lookup → dynamic profit matrix → updates Shopify")

# ── Tabs: Run Tool | Manage Stores ──────────────────
tab_run, tab_stores = st.tabs(["🚀 Run Sync", "🏪 Manage Stores"])


# ════════════════════════════════════════════════════
# TAB 2 — MANAGE STORES (add / view / delete)
# ════════════════════════════════════════════════════

with tab_stores:
    st.subheader("Saved Stores")

    stores = db_load_stores()
    if stores:
        import pandas as pd
        df = pd.DataFrame(stores, columns=["Store Name", "Domain", "Client ID", "Client Secret"])
        df["Client Secret"] = df["Client Secret"].apply(lambda x: x[:6] + "••••••")
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No stores saved yet. Add one below.")

    st.divider()
    st.subheader("➕ Add / Update Store")

    col1, col2 = st.columns(2)
    with col1:
        new_nick   = st.text_input("Store Name (label for this store)", placeholder="My Pet Store")
        new_domain = st.text_input("Store Domain", placeholder="your-store.myshopify.com")
    with col2:
        new_cid    = st.text_input("Client ID")
        new_csec   = st.text_input("Client Secret", type="password")

    if st.button("💾 Save Store"):
        if new_nick and new_domain and new_cid and new_csec:
            db_save_store(new_nick.strip(), new_domain.strip(), new_cid.strip(), new_csec.strip())
            st.success(f"✅ Store '{new_nick}' saved!")
            st.rerun()
        else:
            st.error("Fill in all four fields.")

    st.divider()
    st.subheader("🗑️ Delete Store")
    if stores:
        del_choice = st.selectbox("Select store to delete", [s[0] for s in stores], key="del_sel")
        if st.button("Delete Selected Store", type="secondary"):
            db_delete_store(del_choice)
            st.success(f"Deleted '{del_choice}'")
            st.rerun()


# ════════════════════════════════════════════════════
# TAB 1 — RUN SYNC
# ════════════════════════════════════════════════════

with tab_run:

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("⚙️ Settings")

        stores = db_load_stores()
        store_names = [s[0] for s in stores]

        if store_names:
            selected_store = st.selectbox("Select Store", ["— select —"] + store_names)
        else:
            selected_store = None
            st.warning("No stores saved. Go to **Manage Stores** tab to add one.")

        st.caption("Profit is calculated automatically using the matrix below.")

        st.divider()
        st.subheader("📍 Amazon Delivery ZIP")
        preset_choice = st.selectbox("City", list(US_ZIP_PRESETS.keys()))
        if preset_choice == "Custom ZIP...":
            zip_code = st.text_input("Enter ZIP Code", placeholder="10001", max_chars=10).strip()
        else:
            zip_code = US_ZIP_PRESETS[preset_choice]
            st.text_input("ZIP Code", value=zip_code, disabled=True)

        st.divider()
        st.subheader("📊 Profit Matrix")
        matrix_data = [
            ("≤ $15",  "$10"), ("≤ $50",  "$16"), ("≤ $100", "$22"),
            ("≤ $150", "$27"), ("≤ $200", "$33"), ("≤ $250", "$37"),
            ("≤ $300", "$45"), ("≤ $350", "$55"), ("≤ $400", "$60"),
            ("≤ $450", "$65"), ("≤ $500", "$70"), ("≤ $550", "$75"),
            ("≤ $600", "$78"), ("≤ $650", "$80"), ("> $650", "$100"),
        ]
        import pandas as pd
        st.dataframe(
            pd.DataFrame(matrix_data, columns=["Amazon Price", "Profit Added"]),
            width='stretch',
            hide_index=True,
        )

    with col_right:
        st.subheader("📋 Live Log")

        logs = []
        log_box = st.empty()

        def add_log(msg):
            logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")
            log_box.markdown(
                f"""
                <div style="
                    background:#0d0d0d; color:#00ff88;
                    padding:15px; height:480px; overflow-y:auto;
                    font-family:'Courier New',monospace; font-size:13px;
                    border-radius:10px; border:1px solid #00ff8833;
                ">
                {'<br>'.join(logs[::-1])}
                </div>
                """,
                unsafe_allow_html=True,
            )

        results_placeholder = st.empty()
        results = []

        def refresh_results():
            if results:
                results_placeholder.dataframe(
                    pd.DataFrame(results),
                    width='stretch',
                    hide_index=True,
                )

        if st.button("🚀 START PRICE SYNC", type="primary"):

            # ── Validate inputs ────────────────────────────
            if not selected_store or selected_store == "— select —":
                st.error("❌ Please select a store.")
                st.stop()
            if not zip_code:
                st.error("❌ Please select or enter a ZIP code.")
                st.stop()

            # ── Load store credentials ─────────────────────
            store_row = next((s for s in db_load_stores() if s[0] == selected_store), None)
            if not store_row:
                st.error("❌ Store not found in database.")
                st.stop()

            _, shop_domain, client_id, client_secret = store_row

            # ── Get fresh OAuth token ──────────────────────
            add_log(f"🔑 Getting fresh access token for: {shop_domain}")
            token, err = get_oauth_token(shop_domain, client_id, client_secret)
            if err or not token:
                add_log(f"💥 Token error: {err}")
                st.error(f"Could not get access token: {err}")
                st.stop()
            add_log("✅ Access token obtained")

            headers = {
                "X-Shopify-Access-Token": token,
                "Content-Type": "application/json",
            }

            clean_uc_cache()

            # ── Fetch all products ─────────────────────────
            try:
                add_log("📦 Fetching ALL products (paginated)...")
                products = fetch_all_products(shop_domain, headers, add_log)
                if not products:
                    add_log("❌ No products found.")
                    st.stop()
                add_log(f"✅ Total: {len(products)} products")
            except Exception as e:
                add_log(f"💥 Shopify API Error: {str(e)}")
                st.error(str(e))
                st.stop()

            # ── Launch browser ─────────────────────────────
            add_log(f"🌐 Chrome version: {get_chrome_version()}")
            add_log("🚀 Launching browser...")
            try:
                driver = create_driver()
            except Exception as e:
                add_log(f"💥 Browser failed: {str(e)}")
                st.stop()

            set_amazon_zip(driver, zip_code, log_fn=add_log)

            # ── Process products ───────────────────────────
            updated_count = skipped_count = error_count = 0

            for product in products:
                title    = product.get("title") or "Unknown"
                variants = product.get("variants") or []

                for variant in variants:
                    raw_sku = variant.get("sku")
                    sku     = str(raw_sku).strip() if raw_sku is not None else ""

                    variant_id        = variant["id"]
                    inventory_item_id = variant.get("inventory_item_id")

                    try:
                        shopify_price = float(variant.get("price") or 0)
                    except:
                        shopify_price = 0.0

                    if not sku:
                        add_log(f"⚠️  Skip (no SKU): '{title[:40]}'")
                        skipped_count += 1
                        continue

                    asin = sku_to_asin(sku)
                    if not asin:
                        add_log(f"⚠️  Skip (bad SKU): '{sku}'")
                        skipped_count += 1
                        results.append({
                            "Product": title[:40], "SKU": sku, "ASIN": "—",
                            "Old Price": f"${shopify_price}", "Amazon": "—",
                            "Profit": "—", "New Price": "—", "Action": "⚠️ Bad SKU",
                        })
                        refresh_results()
                        continue

                    add_log(f"🔎 {sku} → {asin}  |  '{title[:35]}'")

                    try:
                        amazon_price = scrape_amazon_price(driver, asin)
                    except Exception as e:
                        add_log(f"❌ Scrape error ({asin}): {str(e)[:80]}")
                        error_count += 1
                        continue

                    if amazon_price is None:
                        add_log(f"❌ Price not found — ASIN: {asin}")
                        error_count += 1
                        results.append({
                            "Product": title[:40], "SKU": sku, "ASIN": asin,
                            "Old Price": f"${shopify_price}", "Amazon": "Not Found",
                            "Profit": "—", "New Price": "—", "Action": "❌ Not Found",
                        })
                        refresh_results()
                        continue

                    # ── Profit matrix ──────────────────────
                    profit    = profit_for(amazon_price)
                    new_price = round(amazon_price + profit, 2)

                    add_log(
                        f"💰 Amazon: ${amazon_price}  "
                        f"+ Profit: ${profit}  "
                        f"= New Price: ${new_price}  "
                        f"(was ${shopify_price})"
                    )

                    try:
                        requests.put(
                            f"https://{shop_domain}/admin/api/2024-10"
                            f"/variants/{variant_id}.json",
                            headers=headers,
                            json={"variant": {
                                "id":               variant_id,
                                "price":            str(new_price),
                                "compare_at_price": str(amazon_price),
                            }},
                            timeout=15,
                        ).raise_for_status()

                        if inventory_item_id:
                            requests.put(
                                f"https://{shop_domain}/admin/api/2024-10"
                                f"/inventory_items/{inventory_item_id}.json",
                                headers=headers,
                                json={"inventory_item": {
                                    "id":   inventory_item_id,
                                    "cost": str(amazon_price),
                                }},
                                timeout=15,
                            )

                        add_log(f"✅ UPDATED: '{title[:35]}' → ${new_price}")
                        updated_count += 1
                        results.append({
                            "Product":   title[:40],
                            "SKU":       sku,
                            "ASIN":      asin,
                            "Old Price": f"${shopify_price}",
                            "Amazon":    f"${amazon_price}",
                            "Profit":    f"+${profit}",
                            "New Price": f"${new_price}",
                            "Action":    "✅ Updated",
                        })

                    except Exception as e:
                        add_log(f"❌ Shopify update failed: {str(e)[:80]}")
                        error_count += 1
                        results.append({
                            "Product":   title[:40], "SKU": sku, "ASIN": asin,
                            "Old Price": f"${shopify_price}", "Amazon": f"${amazon_price}",
                            "Profit":    f"+${profit}", "New Price": "—",
                            "Action":    "❌ Update Failed",
                        })

                    refresh_results()

            driver.quit()

            add_log("─" * 55)
            add_log(
                f"🏁 DONE  |  ✅ Updated: {updated_count}  "
                f"|  ⚠️ Skipped: {skipped_count}  "
                f"|  ❌ Errors: {error_count}"
            )
            st.success(
                f"✅ Done! Updated: {updated_count} | "
                f"Skipped: {skipped_count} | Errors: {error_count}"
            )
            st.balloons()