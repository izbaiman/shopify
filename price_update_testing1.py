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
import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # =====================================================
# # US ZIP PRESETS
# # =====================================================
#
# US_ZIP_PRESETS = {
#     "New York, NY": "10001",
#     "Los Angeles, CA": "90001",
#     "Chicago, IL": "60601",
#     "Houston, TX": "77001",
#     "Phoenix, AZ": "85001",
#     "Philadelphia, PA": "19101",
#     "San Antonio, TX": "78201",
#     "Dallas, TX": "75201",
#     "Miami, FL": "33101",
#     "Seattle, WA": "98101",
#     "Custom ZIP...": "",
# }
# =====================================================
# AMAZON MARKETPLACE CONFIGURATION
# =====================================================

AMAZON_MARKETPLACES = {
    "🇺🇸 United States": {
        "domain": "www.amazon.com",
        "country": "US",
        "location_label": "ZIP Code",
        "currency": "USD",
        "symbol": "$",
        "locations": {
            "New York, NY": "10001",
            "Los Angeles, CA": "90001",
            "Chicago, IL": "60601",
            "Houston, TX": "77001",
            "Phoenix, AZ": "85001",
            "Philadelphia, PA": "19101",
            "San Antonio, TX": "78201",
            "Dallas, TX": "75201",
            "Miami, FL": "33101",
            "Seattle, WA": "98101",
            "Custom ZIP...": "",
        },
    },

    "🇬🇧 United Kingdom": {
        "domain": "www.amazon.co.uk",
        "country": "UK",
        "location_label": "Postcode",
        "currency": "GBP",
        "symbol": "£",
        "locations": {
            "London": "SW1A 1AA",
            "Birmingham": "B1 1AA",
            "Manchester": "M1 1AA",
            "Liverpool": "L1 1AA",
            "Leeds": "LS1 1UR",
            "Custom Postcode...": "",
        },
    },

    "🇨🇦 Canada": {
        "domain": "www.amazon.ca",
        "country": "CA",
        "location_label": "Postal Code",
        "currency": "CAD",
        "symbol": "C$",
        "locations": {
            "Toronto": "M5V 2T6",
            "Vancouver": "V6B 1A1",
            "Montreal": "H2Y 1C6",
            "Calgary": "T2P 1J9",
            "Ottawa": "K1P 1J1",
            "Custom Postal Code...": "",
        },
    },

    "🇦🇺 Australia": {
        "domain": "www.amazon.com.au",
        "country": "AU",
        "location_label": "Postcode",
        "currency": "AUD",
        "symbol": "A$",
        "locations": {
            "Sydney": "2000",
            "Melbourne": "3000",
            "Brisbane": "4000",
            "Perth": "6000",
            "Adelaide": "5000",
            "Custom Postcode...": "",
        },
    },
}

# =====================================================
# DATABASE — SQLite, stores per-store credentials
# =====================================================

DB_PATH = "shopify_stores.db"
BATCH_SIZE = 100
def create_shopify_session():
    session = requests.Session()

    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        pool_connections=5,
        pool_maxsize=5,
        max_retries=retry,
    )

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "Connection": "keep-alive",
    })

    return session

# Each saved Shopify store can update stock only at its own inventory location.
SHOPIFY_INVENTORY_LOCATIONS = {
    "Cart Shape-ca": "Canada",
    "CartShape-Uk": "Shop location",
    "WazaCart": "WazaCart",
    "Apron mart": "5900 Balcones Drive # 19097",
    "MarketOneo": "251 Meeting Street",
    "Gadgets key": "Shop location",
    "thetailstore": "94 Legend Ln",
    "Testing": "30 N Gould St, Ste R",
}


def db_init():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
                CREATE TABLE IF NOT EXISTS stores
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    store_name
                    TEXT
                    UNIQUE
                    NOT
                    NULL,
                    domain
                    TEXT
                    NOT
                    NULL,
                    client_id
                    TEXT
                    NOT
                    NULL,
                    client_secret
                    TEXT
                    NOT
                    NULL,
                    created_at
                    TEXT
                    DEFAULT (
                    datetime
                (
                    'now'
                ))
                    )
                """)
    con.execute("""
                CREATE TABLE IF NOT EXISTS sync_progress
                (
                    progress_key TEXT PRIMARY KEY,
                    next_index INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                """)
    con.commit()
    con.close()


def db_save_store(store_name, domain, client_id, client_secret):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
                INSERT INTO stores (store_name, domain, client_id, client_secret)
                VALUES (?, ?, ?, ?) ON CONFLICT(store_name) DO
                UPDATE SET
                    domain = excluded.domain,
                    client_id = excluded.client_id,
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
    return rows  # list of (Storename, domain, client_id, client_secret)


def db_delete_store(store_name):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM stores WHERE store_name = ?", (store_name,))
    con.commit()
    con.close()


def db_load_sync_progress(progress_key):
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT next_index FROM sync_progress WHERE progress_key = ?",
        (progress_key,),
    ).fetchone()
    con.close()
    return row[0] if row else 0


def db_save_sync_progress(progress_key, next_index):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
                INSERT INTO sync_progress (progress_key, next_index, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(progress_key) DO UPDATE SET
                    next_index = excluded.next_index,
                    updated_at = excluded.updated_at
                """, (progress_key, next_index))
    con.commit()
    con.close()


# =====================================================
# SHOPIFY OAUTH — fresh token every run
# =====================================================

def get_oauth_token(domain, client_id, client_secret):
    url = f"https://{domain}/admin/oauth/access_token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    shopify_session = create_shopify_session()
    try:
        r = shopify_session.post(url, json=payload, timeout=30, verify=False)
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            if token:
                return token, ""
            return "", "Response OK but no access_token in response"
        return "", f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return "", str(e)
    finally:
        shopify_session.close()


def get_shopify_location_id(shop_domain, headers, location_name, session):
    """Return the Shopify location ID for the configured inventory location."""
    try:
        response = session.get(
            f"https://{shop_domain}/admin/api/2024-10/locations.json?limit=250",
            headers=headers,
            timeout=(10, 60),
        )
        response.raise_for_status()
        for location in response.json().get("locations", []):
            if location.get("name", "").strip().lower() == location_name.lower():
                return location["id"], ""
        return None, f"Shopify location '{location_name}' was not found"
    except Exception as e:
        return None, str(e)


def set_shopify_out_of_stock(shop_domain, headers, inventory_item_id, location_id, session):
    """Set one Shopify inventory item to zero at the configured location."""
    try:
        response = session.post(
            f"https://{shop_domain}/admin/api/2024-10/inventory_levels/set.json",
            headers=headers,
            json={
                "location_id": location_id,
                "inventory_item_id": inventory_item_id,
                "available": 0,
            },
            timeout=(10, 60),
        )
        response.raise_for_status()
        return True, ""
    except Exception as e:
        return False, str(e)


# # =====================================================
# # PROFIT MATRIX
# # Amazon price → profit to add on top
# # =====================================================
#
# def profit_for(cost):
#     table = [
#         (15, 10), (50, 16), (100, 22), (150, 27),
#         (200, 33), (250, 37), (300, 45), (350, 55),
#         (400, 60), (450, 65), (500, 70), (550, 75),
#         (600, 78), (650, 80),
#     ]
#     for threshold, profit in table:
#         if cost <= threshold:
#             return profit
#     return 100
#
# =====================================================
# PROFIT MATRICES
# Each marketplace uses its own native currency
# =====================================================

PROFIT_MATRICES = {
    "USD": [
        (15, 10), (50, 16), (100, 22), (150, 27),
        (200, 33), (250, 37), (300, 45), (350, 55),
        (400, 60), (450, 65), (500, 70), (550, 75),
        (600, 78), (650, 80),
    ],

    "GBP": [
        (15, 10), (50, 16), (100, 22), (150, 27),
        (200, 33), (250, 37), (300, 45), (350, 55),
        (400, 60), (450, 65), (500, 70), (550, 75),
        (600, 78), (650, 80),
    ],

    "CAD": [
        (15, 10), (50, 16), (100, 22), (150, 27),
        (200, 33), (250, 37), (300, 45), (350, 55),
        (400, 60), (450, 65), (500, 70), (550, 75),
        (600, 78), (650, 80),
    ],

    "AUD": [
        (15, 10), (50, 16), (100, 22), (150, 27),
        (200, 33), (250, 37), (300, 45), (350, 55),
        (400, 60), (450, 65), (500, 70), (550, 75),
        (600, 78), (650, 80),
    ],
}


def profit_for(cost, currency):
    table = PROFIT_MATRICES.get(currency)

    if not table:
        raise ValueError(f"Unsupported currency: {currency}")

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

def safe_quit_driver(driver, log_fn=None):
    if driver is None:
        return

    try:
        driver.quit()

        if log_fn:
            log_fn("🧹 Chrome driver closed successfully.")

    except Exception as e:

        if log_fn:
            log_fn(
                f"⚠️ Chrome driver cleanup failed: "
                f"{str(e)[:100]}"
            )


# =====================================================
# FETCH ALL SHOPIFY PRODUCTS (cursor pagination)
# =====================================================

# def fetch_all_products(shop_domain, headers, log_fn):
#     all_products = []
#     url = f"https://{shop_domain}/admin/api/2024-10/products.json?limit=250"
#     page = 1
#     while url:
#         log_fn(f"   ↳ Fetching page {page} ...")
#         resp = requests.get(url, headers=headers, timeout=30)
#         resp.raise_for_status()
#         batch = resp.json().get("products", [])
#         all_products.extend(batch)
#         log_fn(f"   ↳ Page {page}: {len(batch)} products (total: {len(all_products)})")
#         link_header = resp.headers.get("Link", "")
#         next_url = None
#         for part in link_header.split(","):
#             if 'rel="next"' in part:
#                 m = re.search(r'<([^>]+)>', part)
#                 if m:
#                     next_url = m.group(1)
#                     break
#         url = next_url
#         page += 1
#     return all_products
def fetch_all_products(shop_domain, headers, log_fn, session):
    all_products = []
    url = f"https://{shop_domain}/admin/api/2024-10/products.json?limit=250"
    page = 1

    while url:
        log_fn(f"   ↳ Fetching page {page} ...")

        resp = session.get(
            url,
            headers=headers,
            timeout=(10, 60),
        )

        resp.raise_for_status()

        batch = resp.json().get("products", [])
        all_products.extend(batch)

        log_fn(
            f"   ↳ Page {page}: {len(batch)} products "
            f"(total: {len(all_products)})"
        )

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

# # =====================================================
# # SET AMAZON DELIVERY ZIP
# # =====================================================
#
# def set_amazon_zip(driver, zip_code, log_fn=None):
#     def _log(m):
#         if log_fn: log_fn(m)
#
#     try:
#         _log(f"🌍 Setting Amazon delivery ZIP: {zip_code} ...")
#         driver.get("https://www.amazon.com")
#         time.sleep(4)
#         wait = WebDriverWait(driver, 10)
#         for sel in ["#nav-global-location-popover-link", "#glow-ingress-line2"]:
#             try:
#                 wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel))).click()
#                 _log("   ↳ Opened location popup")
#                 break
#             except:
#                 pass
#         time.sleep(2)
#         inp = None
#         for sel in ["input[data-action-type='MODAL_INPUT']", "#GLUXZipUpdateInput",
#                     "input[placeholder*='ZIP']", "input[placeholder*='zip']"]:
#             try:
#                 inp = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, sel)))
#                 inp.clear();
#                 inp.send_keys(zip_code)
#                 _log(f"   ↳ Entered ZIP: {zip_code}")
#                 break
#             except:
#                 pass
#         time.sleep(1)
#         for sel in ["span[data-action-type='MODAL_SUBMIT'] input",
#                     "#GLUXZipUpdate", "input.a-button-input"]:
#             try:
#                 wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel))).click()
#                 _log("   ↳ Applied ZIP")
#                 break
#             except:
#                 pass
#         time.sleep(2)
#         for sel in ["button[data-action-type='DISMISS']", "#GLUXConfirmClose"]:
#             try:
#                 driver.find_element(By.CSS_SELECTOR, sel).click(); break
#             except:
#                 pass
#         time.sleep(2)
#         _log(f"✅ Amazon location set → ZIP {zip_code}")
#         # Force USD currency
#         try:
#             driver.get("https://www.amazon.com")
#             time.sleep(2)
#
#             driver.add_cookie({
#                 "name": "i18n-prefs",
#                 "value": "USD",
#                 "domain": ".amazon.com"
#             })
#
#             driver.refresh()
#             time.sleep(2)
#
#             _log("✅ Currency forced to USD")
#
#         except Exception as e:
#             _log(f"⚠ Currency cookie failed: {e}")
#         return True
#     except Exception as e:
#         _log(f"⚠️  Location set failed: {str(e)[:100]}")
#         return False
# =====================================================
# SET AMAZON DELIVERY LOCATION + CURRENCY
# =====================================================

def set_amazon_location(
    driver,
    amazon_domain,
    zip_code,
    currency,
    log_fn=None
):
    def _log(message):
        if log_fn:
            log_fn(message)

    try:
        amazon_url = f"https://{amazon_domain}"

        _log(f"🌍 Opening Amazon marketplace: {amazon_domain}")
        driver.get(amazon_url)
        time.sleep(4)

        wait = WebDriverWait(driver, 15)

        # -------------------------------------------------
        # OPEN AMAZON LOCATION POPUP
        # -------------------------------------------------

        location_selectors = [
            "#nav-global-location-popover-link",
            "#glow-ingress-line2",
        ]

        location_opened = False

        for sel in location_selectors:
            try:
                wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, sel)
                    )
                ).click()

                _log("   ↳ Opened location popup")
                location_opened = True
                break

            except Exception:
                pass

        if not location_opened:
            _log("⚠️ Could not open Amazon location popup")
            return False

        time.sleep(2)

        # -------------------------------------------------
        # FIND ZIP / POSTCODE / POSTAL CODE INPUT
        # -------------------------------------------------

        location_inputs = [
            "input[data-action-type='MODAL_INPUT']",
            "#GLUXZipUpdateInput",
            "input[placeholder*='ZIP']",
            "input[placeholder*='zip']",
            "input[placeholder*='Postal']",
            "input[placeholder*='postal']",
            "input[placeholder*='Postcode']",
            "input[placeholder*='postcode']",
        ]

        location_input = None

        # Amazon Canada may render the postal code as two separate inputs.
        split_inputs = [
            element
            for element in driver.find_elements(
                By.CSS_SELECTOR,
                "input[id*='GLUXZipUpdateInput'], input[name*='zip'], input[name*='postal']"
            )
            if element.is_displayed() and element.is_enabled()
        ]

        if len(split_inputs) >= 2:
            postal_code = re.sub(r"\s+", "", str(zip_code)).upper()
            if len(postal_code) >= 6:
                split_inputs[0].clear()
                split_inputs[0].send_keys(postal_code[:3])
                split_inputs[1].clear()
                split_inputs[1].send_keys(postal_code[3:6])
                location_input = split_inputs[0]
                _log(f"   ↳ Entered postal code: {zip_code}")

        for sel in location_inputs if location_input is None else []:
            try:
                location_input = wait.until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, sel)
                    )
                )

                location_input.clear()
                location_input.send_keys(zip_code)

                _log(f"   ↳ Entered location: {zip_code}")
                break

            except Exception:
                pass

        if location_input is None:
            _log("⚠️ Could not find ZIP/Postcode input")
            return False

        time.sleep(1)

        # -------------------------------------------------
        # APPLY LOCATION
        # -------------------------------------------------

        submit_selectors = [
            "span[data-action-type='MODAL_SUBMIT'] input",
            "#GLUXZipUpdate",
            "input.a-button-input",
        ]

        location_applied = False

        for sel in submit_selectors:
            try:
                wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, sel)
                    )
                ).click()

                _log("   ↳ Applied delivery location")
                location_applied = True
                break

            except Exception:
                pass

        if not location_applied:
            _log("⚠️ Could not apply Amazon delivery location")
            return False

        time.sleep(2)

        # -------------------------------------------------
        # CLOSE CONFIRMATION POPUP
        # -------------------------------------------------

        close_selectors = [
            "button[data-action-type='DISMISS']",
            "#GLUXConfirmClose",
        ]

        for sel in close_selectors:
            try:
                driver.find_element(
                    By.CSS_SELECTOR,
                    sel
                ).click()

                break

            except Exception:
                pass

        time.sleep(2)

        # -------------------------------------------------
        # FORCE MARKETPLACE CURRENCY
        # -------------------------------------------------

        driver.get(amazon_url)
        time.sleep(3)

        currency_cookie = {
            "USD": "USD",
            "GBP": "GBP",
            "CAD": "CAD",
            "AUD": "AUD",
        }.get(currency)

        if currency_cookie:

            try:
                driver.add_cookie({
                    "name": "i18n-prefs",
                    "value": currency_cookie,
                    "domain": f".{amazon_domain}",
                })

                driver.refresh()
                time.sleep(3)

                _log(
                    f"✅ Currency forced to {currency}"
                )

            except Exception as e:
                _log(
                    f"⚠️ Currency cookie failed: "
                    f"{str(e)[:100]}"
                )

        _log(
            f"✅ Amazon marketplace ready → "
            f"{amazon_domain} | "
            f"Location: {zip_code} | "
            f"Currency: {currency}"
        )

        return True

    except Exception as e:

        _log(
            f"⚠️ Amazon location setup failed: "
            f"{str(e)[:150]}"
        )

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
    if sku.startswith("CSC"):
        return "B0" + sku[3:]
    if sku.startswith("CS"):
        asin = sku[2:]
        return asin if asin.startswith("B0") else "B0" + asin
    return "B0" + sku[2:]


# =====================================================
# SCRAPE AMAZON PRICE
# =====================================================


# def scrape_amazon_price(driver, asin):
#     driver.get(f"https://www.amazon.com/dp/{asin}?th=1")
#
#     WebDriverWait(driver, 15).until(
#         EC.presence_of_element_located(
#             (By.CSS_SELECTOR, ".priceToPay .a-offscreen")
#         )
#     )
#     # basis_selectors = [
#     #     "span.a-price.a-text-price.apex-basisprice-value .a-offscreen",
#     # ]
#     #
#     # for sel in basis_selectors:
#     #     try:
#     #         elements = driver.find_elements(By.CSS_SELECTOR, sel)
#     #
#     #         for el in elements:
#     #             txt = (el.get_attribute("innerHTML") or el.text or "").strip()
#     #
#     #             print(f"BASIS PRICE RAW ({asin}): {txt}")
#     #
#     #             if "$" not in txt:
#     #                 continue
#     #
#     #             price_text = txt.replace("$", "").replace(",", "").strip()
#     #
#     #             try:
#     #                 price = float(price_text)
#     #
#     #                 if 0.5 < price < 10000:
#     #                     print(f"FOUND BASIS PRICE: {price}")
#     #                     return price
#     #
#     #             except:
#     #                 pass
#     #
#     #     except Exception:
#     #         pass
#     selectors = [
#         ".priceToPay .a-offscreen",
#         "#corePriceDisplay_desktop_feature_div .priceToPay .a-offscreen",
#         "#price_inside_buybox",
#         "#priceblock_ourprice",
#         "#corePrice_feature_div .a-price .a-offscreen",
#     ]
#
#     for sel in selectors:
#         try:
#             elements = driver.find_elements(By.CSS_SELECTOR, sel)
#
#             for el in elements:
#                 txt = (el.get_attribute("innerHTML") or el.text or "").strip()
#
#                 # Debug
#                 print(f"RAW PRICE ({asin}):", txt)
#
#                 # Ignore non-USD currencies
#                 if "$" not in txt:
#                     print("Skipping non-USD price")
#                     continue
#
#                 # Remove $ and commas
#                 price_text = txt.replace("$", "").replace(",", "").strip()
#
#                 try:
#                     price = float(price_text)
#
#                     if 0.5 < price < 10000:
#                         print(f"FOUND USD PRICE: {price}")
#                         return price
#
#                 except:
#                     pass
#
#         except Exception:
#             pass
#
#     return None
# def scrape_amazon_price(driver, asin):
# def scrape_amazon_price(driver, asin, amazon_domain):
#     # driver.get(f"https://www.amazon.com/dp/{asin}?th=1")
#     driver.get(f"https://{amazon_domain}/dp/{asin}?th=1")
#     WebDriverWait(driver, 15).until(
#         EC.presence_of_element_located(
#             (By.CSS_SELECTOR, ".priceToPay .a-offscreen")
#         )
#     )
#
#     selectors = [
#         ".priceToPay .a-offscreen",
#         "#corePriceDisplay_desktop_feature_div .priceToPay .a-offscreen",
#         "#price_inside_buybox",
#         "#priceblock_ourprice",
#         "#corePrice_feature_div .a-price .a-offscreen",
#     ]
#
#     for sel in selectors:
#         try:
#             elements = driver.find_elements(By.CSS_SELECTOR, sel)
#
#             for el in elements:
#                 txt = (
#                     el.get_attribute("innerHTML")
#                     or el.text
#                     or ""
#                 ).strip()
#
#                 print(f"RAW PRICE ({asin}): {txt}")
#
#                 # Supported Amazon currencies:
#                 # USD = $
#                 # GBP = £
#                 # CAD = C$
#                 # AUD = A$
#                 currency_symbols = ["$", "£", "C$", "A$"]
#
#                 if not any(symbol in txt for symbol in currency_symbols):
#                     print("Skipping unsupported currency")
#                     continue
#
#                 # Remove currency symbols and commas
#                 price_text = (
#                     txt.replace("C$", "")
#                        .replace("A$", "")
#                        .replace("$", "")
#                        .replace("£", "")
#                        .replace(",", "")
#                        .strip()
#                 )
#
#                 try:
#                     price = float(price_text)
#
#                     if 0.5 < price < 10000:
#                         print(f"FOUND AMAZON PRICE: {price}")
#                         return price
#
#                 except Exception:
#                     pass
#
#         except Exception:
#             pass
#
#     return None
# def scrape_amazon_price(driver, asin, amazon_domain):
#     url = f"https://{amazon_domain}/dp/{asin}?th=1"
#
#     try:
#         driver.get(url)
#         time.sleep(3)
#
#         # -------------------------------------------------
#         # CHECK AMAZON PAGE STATUS FIRST
#         # -------------------------------------------------
#
#         try:
#             body_text = driver.find_element(
#                 By.TAG_NAME,
#                 "body"
#             ).text.lower()
#         except Exception:
#             body_text = ""
#
#         unavailable_keywords = [
#             "currently unavailable",
#             "currently out of stock",
#             "temporarily out of stock",
#             "out of stock",
#             "we don't know when or if this item will be back in stock",
#             "this item is currently unavailable",
#             "not available",
#             "web address you entered is not a functioning page",
#             "page not found",
#         ]
#
#         for keyword in unavailable_keywords:
#             if keyword in body_text:
#                 print(
#                     f"AMAZON UNAVAILABLE ({asin}): {keyword}"
#                 )
#                 return None
#
#         # -------------------------------------------------
#         # FIND SELLING PRICE
#         # -------------------------------------------------
#
#         selectors = [
#             ".priceToPay .a-offscreen",
#             "#corePriceDisplay_desktop_feature_div .priceToPay .a-offscreen",
#             "#price_inside_buybox",
#             "#priceblock_ourprice",
#             "#corePrice_feature_div .a-price .a-offscreen",
#         ]
#
#         for sel in selectors:
#             try:
#                 elements = driver.find_elements(
#                     By.CSS_SELECTOR,
#                     sel
#                 )
#
#                 for el in elements:
#
#                     txt = (
#                         el.get_attribute("innerHTML")
#                         or el.text
#                         or ""
#                     ).strip()
#
#                     print(
#                         f"RAW PRICE ({asin}): {txt}"
#                     )
#
#                     currency_symbols = [
#                         "$",
#                         "£",
#                         "C$",
#                         "A$"
#                     ]
#
#                     if not any(
#                         symbol in txt
#                         for symbol in currency_symbols
#                     ):
#                         continue
#
#                     price_text = (
#                         txt
#                         .replace("C$", "")
#                         .replace("A$", "")
#                         .replace("$", "")
#                         .replace("£", "")
#                         .replace(",", "")
#                         .strip()
#                     )
#
#                     try:
#                         price = float(price_text)
#
#                         if 0.5 < price < 10000:
#                             print(
#                                 f"FOUND AMAZON PRICE: {price}"
#                             )
#                             return price
#
#                     except Exception:
#                         pass
#
#             except Exception:
#                 pass
#
#         print(
#             f"AMAZON PRICE NOT FOUND ({asin})"
#         )
#
#         return None
#
#     except Exception as e:
#         raise RuntimeError(
#             f"Amazon page/scrape failed for {asin}: "
#             f"{str(e)[:200]}"
#         )

def scrape_amazon_price(driver, asin, amazon_domain):
    url = f"https://{amazon_domain}/dp/{asin}?th=1"

    try:
        driver.get(url)
        time.sleep(3)

        # -------------------------------------------------
        # READ AMAZON PAGE
        # -------------------------------------------------

        try:
            body_text = driver.find_element(
                By.TAG_NAME,
                "body"
            ).text.lower()
        except Exception:
            body_text = ""

        # -------------------------------------------------
        # CHECK IF PRODUCT IS UNAVAILABLE / OUT OF STOCK
        # -------------------------------------------------

        unavailable_keywords = [
            "currently unavailable",
            "currently out of stock",
            "temporarily out of stock",
            "out of stock",
            "this item is currently unavailable",
            "we don't know when or if this item will be back in stock",
        ]

        for keyword in unavailable_keywords:
            if keyword in body_text:
                print(
                    f"AMAZON UNAVAILABLE ({asin}): {keyword}"
                )
                return None, "unavailable"

        # -------------------------------------------------
        # CHECK AMAZON PAGE NOT FOUND
        # -------------------------------------------------

        not_found_keywords = [
            "page not found",
            "web address you entered is not a functioning page",
            "looking for something?",
            "the web address you entered is not a functioning page",
        ]

        for keyword in not_found_keywords:
            if keyword in body_text:
                print(
                    f"AMAZON PAGE NOT FOUND ({asin}): {keyword}"
                )
                return None, "not_found"

        # -------------------------------------------------
        # FIND SELLING PRICE
        # -------------------------------------------------

        selectors = [
            ".priceToPay .a-offscreen",
            "#corePriceDisplay_desktop_feature_div .priceToPay .a-offscreen",
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#corePrice_feature_div .a-price .a-offscreen",
        ]

        for sel in selectors:
            try:
                elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    sel
                )

                for el in elements:

                    txt = (
                        el.get_attribute("innerHTML")
                        or el.text
                        or ""
                    ).strip()

                    print(
                        f"RAW PRICE ({asin}): {txt}"
                    )

                    currency_symbols = [
                        "$",
                        "£",
                        "C$",
                        "A$"
                    ]

                    if not any(
                        symbol in txt
                        for symbol in currency_symbols
                    ):
                        continue

                    price_text = (
                        txt
                        .replace("C$", "")
                        .replace("A$", "")
                        .replace("$", "")
                        .replace("£", "")
                        .replace(",", "")
                        .strip()
                    )

                    try:
                        price = float(price_text)

                        if 0.5 < price < 10000:
                            print(
                                f"FOUND AMAZON PRICE: {price}"
                            )

                            return price, "ok"

                    except Exception:
                        pass

            except Exception:
                pass

        # -------------------------------------------------
        # PRICE NOT FOUND
        # -------------------------------------------------

        print(
            f"AMAZON PRICE NOT FOUND ({asin})"
        )

        return None, "price_not_found"

    except Exception as e:
        raise RuntimeError(
            f"Amazon page/scrape failed for {asin}: "
            f"{str(e)[:200]}"
        )
# =====================================================
# SCRAPE AMAZON INVENTORY COST
# (List Price -> Typical Price -> Selling Price)
# =====================================================


# def scrape_inventory_cost(driver, asin):
def scrape_inventory_cost(driver, asin, amazon_domain):
    driver.get(f"https://{amazon_domain}/dp/{asin}?th=1")
    time.sleep(3)
    # ---------- Try List Price / Typical Price ----------
    basis_selectors = [
        "span.a-price.a-text-price.apex-basisprice-value .a-offscreen",
    ]

    for sel in basis_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)

            for el in elements:

                txt = (
                    el.get_attribute("innerHTML")
                    or el.text
                    or ""
                ).strip()

                print(f"RAW INVENTORY PRICE ({asin}): {txt}")

                # Supported currencies:
                # USD = $
                # GBP = £
                # CAD = C$
                # AUD = A$
                currency_symbols = ["$", "£", "C$", "A$"]

                if not any(symbol in txt for symbol in currency_symbols):
                    print("Skipping unsupported inventory currency")
                    continue

                price_text = (
                    txt.replace("C$", "")
                       .replace("A$", "")
                       .replace("$", "")
                       .replace("£", "")
                       .replace(",", "")
                       .strip()
                )

                try:
                    price = float(price_text)

                    if 0.5 < price < 10000:
                        print(f"FOUND INVENTORY COST: {price}")
                        return price

                except Exception:
                    pass

        except Exception:
            pass

    # ---------- Fallback to Selling Price ----------
    selectors = [
        ".priceToPay .a-offscreen",
        "#corePriceDisplay_desktop_feature_div .priceToPay .a-offscreen",
        "#price_inside_buybox",
        "#priceblock_ourprice",
        "#corePrice_feature_div .a-price .a-offscreen",
    ]

    for sel in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)

            for el in elements:

                txt = (
                    el.get_attribute("innerHTML")
                    or el.text
                    or ""
                ).strip()

                print(f"RAW FALLBACK PRICE ({asin}): {txt}")

                currency_symbols = ["$", "£", "C$", "A$"]

                if not any(symbol in txt for symbol in currency_symbols):
                    print("Skipping unsupported fallback currency")
                    continue

                price_text = (
                    txt.replace("C$", "")
                       .replace("A$", "")
                       .replace("$", "")
                       .replace("£", "")
                       .replace(",", "")
                       .strip()
                )

                try:
                    price = float(price_text)

                    if 0.5 < price < 10000:
                        print(f"FALLBACK INVENTORY COST: {price}")
                        return price

                except Exception:
                    pass

        except Exception:
            pass

    return None
# def scrape_amazon_price(driver, asin):
#    driver.get(f"https://www.amazon.com/dp/{asin}?th=1")
#    time.sleep(5)
#    selectors = [
#        ".a-price .a-offscreen",
#        "#corePriceDisplay_desktop_feature_div .a-offscreen",
#        ".priceToPay .a-offscreen",
#        "#price_inside_buybox",
#        "#priceblock_ourprice",
#        ".aok-offscreen",
#    ]
#    for sel in selectors:
#        try:
#            for el in driver.find_elements(By.CSS_SELECTOR, sel):
#                txt = el.get_attribute("innerHTML") or el.text or ""
#                price = re.sub(r"[^\d.]", "", txt.strip())
#                if price:
#                   val = float(price)
#                    if 0.5 < val < 10000:
#                        return val
#        except: pass
#    return None


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
        new_nick = st.text_input("Store Name (label for this store)", placeholder="My Pet Store")
        new_domain = st.text_input("Store Domain", placeholder="your-store.myshopify.com")
    with col2:
        new_cid = st.text_input("Client ID")
        new_csec = st.text_input("Client Secret", type="password")

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
        #
        # st.divider()
        # st.subheader("📍 Amazon Delivery ZIP")
        # preset_choice = st.selectbox("City", list(US_ZIP_PRESETS.keys()))
        # if preset_choice == "Custom ZIP...":
        #     zip_code = st.text_input("Enter ZIP Code", placeholder="10001", max_chars=10).strip()
        # else:
        #     zip_code = US_ZIP_PRESETS[preset_choice]
        #     st.text_input("ZIP Code", value=zip_code, disabled=True)
        st.divider()
        st.subheader("🌎 Amazon Marketplace")

        marketplace_name = st.selectbox(
            "Select Amazon Country",
            list(AMAZON_MARKETPLACES.keys())
        )

        marketplace = AMAZON_MARKETPLACES[marketplace_name]

        amazon_domain = marketplace["domain"]
        amazon_country = marketplace["country"]
        currency = marketplace["currency"]
        currency_symbol = marketplace["symbol"]

        st.caption(
            f"Marketplace: **{amazon_domain}**  |  "
            f"Currency: **{currency} ({currency_symbol})**"
        )

        st.divider()
        st.subheader(f"📍 Amazon Delivery {marketplace['location_label']}")

        locations = marketplace["locations"]

        location_choice = st.selectbox(
            "Select Location",
            list(locations.keys())
        )

        if location_choice.startswith("Custom"):
            zip_code = st.text_input(
                f"Enter {marketplace['location_label']}",
                placeholder="Enter location code",
                max_chars=12
            ).strip()
        else:
            zip_code = locations[location_choice]

        st.caption(
            f"Selected {marketplace['location_label']}: **{zip_code}**"
        )
        st.divider()
        st.subheader("📊 Profit Matrix")
        # matrix_data = [
        #     ("≤ $15", "$10"), ("≤ $50", "$16"), ("≤ $100", "$22"),
        #     ("≤ $150", "$27"), ("≤ $200", "$33"), ("≤ $250", "$37"),
        #     ("≤ $300", "$45"), ("≤ $350", "$55"), ("≤ $400", "$60"),
        #     ("≤ $450", "$65"), ("≤ $500", "$70"), ("≤ $550", "$75"),
        #     ("≤ $600", "$78"), ("≤ $650", "$80"), ("> $650", "$100"),
        # ]
        matrix_data = [
            (f"≤ {currency_symbol}15", f"{currency_symbol}10"),
            (f"≤ {currency_symbol}50", f"{currency_symbol}16"),
            (f"≤ {currency_symbol}100", f"{currency_symbol}22"),
            (f"≤ {currency_symbol}150", f"{currency_symbol}27"),
            (f"≤ {currency_symbol}200", f"{currency_symbol}33"),
            (f"≤ {currency_symbol}250", f"{currency_symbol}37"),
            (f"≤ {currency_symbol}300", f"{currency_symbol}45"),
            (f"≤ {currency_symbol}350", f"{currency_symbol}55"),
            (f"≤ {currency_symbol}400", f"{currency_symbol}60"),
            (f"≤ {currency_symbol}450", f"{currency_symbol}65"),
            (f"≤ {currency_symbol}500", f"{currency_symbol}70"),
            (f"≤ {currency_symbol}550", f"{currency_symbol}75"),
            (f"≤ {currency_symbol}600", f"{currency_symbol}78"),
            (f"≤ {currency_symbol}650", f"{currency_symbol}80"),
            (f"> {currency_symbol}650", f"{currency_symbol}100"),
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

            shopify_session = create_shopify_session()

            inventory_location_name = SHOPIFY_INVENTORY_LOCATIONS.get(selected_store)
            if not inventory_location_name:
                inventory_location_id = None
                location_error = (
                    f"No Shopify inventory location is configured for '{selected_store}'"
                )
            else:
                inventory_location_id, location_error = get_shopify_location_id(
                    shop_domain,
                    headers,
                    inventory_location_name,
                    shopify_session,
                )

            if inventory_location_id:
                add_log(
                    f"✅ Shopify inventory location found: "
                    f"{inventory_location_name}"
                )
            else:
                add_log(
                    f"⚠️ Out-of-stock sync unavailable: {location_error}"
                )

            clean_uc_cache()

            # ── Fetch all products ─────────────────────────
            try:
                add_log("📦 Fetching ALL products (paginated)...")
                products = fetch_all_products(shop_domain, headers, add_log, shopify_session)
                if not products:
                    add_log("❌ No products found.")
                    st.stop()
                add_log(f"✅ Total: {len(products)} products")
            except Exception as e:
                add_log(f"💥 Shopify API Error: {str(e)}")
                st.error(str(e))
                st.stop()

            work_items = [
                (product, variant)
                for product in products
                for variant in (product.get("variants") or [])
            ]
            progress_key = "|".join((
                shop_domain,
                amazon_domain,
                currency,
                zip_code,
            ))
            start_index = db_load_sync_progress(progress_key)
            if start_index >= len(work_items):
                start_index = 0
                db_save_sync_progress(progress_key, 0)

            end_index = min(start_index + BATCH_SIZE, len(work_items))
            total_items = len(work_items)
            run_total = end_index - start_index
            progress_bar = st.progress(0, text="Preparing price sync...")
            progress_status = st.empty()

            def show_live_progress(completed):
                """Refresh the visible counters after each processed variant."""
                overall_position = start_index + completed
                remaining_total = total_items - overall_position
                remaining_run = run_total - completed
                percentage = int((completed / run_total) * 100) if run_total else 100

                status_text = (
                    f"This run: {completed}/{run_total} | "
                    f"Remaining this run: {remaining_run} | "
                    f"Overall position: {overall_position}/{total_items} | "
                    f"Remaining total: {remaining_total}"
                )
                progress_bar.progress(percentage, text=status_text)
                progress_status.info(status_text)

            add_log(
                f"📌 Resuming at item {start_index + 1} of {len(work_items)} "
                f"(this run: up to {BATCH_SIZE})"
            )
            # add_log(
            #     f"📊 This run: 0/{run_total} | Remaining this run: {run_total} | "
            #     f"Overall remaining: {total_items - start_index}"
            # )
            show_live_progress(0)

            # ── Launch browser ─────────────────────────────
            # add_log(f"🌐 Chrome version: {get_chrome_version()}")
            # add_log("🚀 Launching browser...")
            # # try:
            # #     driver = create_driver()
            # # except Exception as e:
            # #     add_log(f"💥 Browser failed: {str(e)}")
            # #     st.stop() 

            # # try:
            # #    location_ready = set_amazon_location(
            # #       driver,
            # #       amazon_domain,
            # #       zip_code,
            # #       currency,
            # #       log_fn=add_log
            # #     )

            # #     if not location_ready:
            # #       add_log("❌ Amazon delivery location was not applied. Sync stopped.")
            # #       st.error("Amazon delivery location could not be applied.")
            # #       st.stop()
            # try:
            #    driver = create_driver()
            # except Exception as e:
            #     add_log(f"💥 Browser failed: {str(e)}")
            #     st.stop()
            # try:
            #    location_ready = set_amazon_location(
            #    driver,
            #    amazon_domain,
            #    zip_code,
            #    currency,
            #    log_fn=add_log
            # )

            # if not location_ready:
            #    add_log("❌ Amazon delivery location was not applied. Sync stopped.")
            #    safe_quit_driver(driver, add_log)
            #    st.error("Amazon delivery location could not be applied.")
            #    st.stop()
            # ── Launch browser ─────────────────────────────
            add_log(f"🌐 Chrome version: {get_chrome_version()}")
            add_log("🚀 Launching browser...")

            try:
               driver = create_driver()
            except Exception as e:
                add_log(f"💥 Browser failed: {str(e)}")
                st.error(f"Browser failed: {str(e)}")
                st.stop()
            try:
            # set_amazon_zip(driver, zip_code, log_fn=add_log)
                location_ready = set_amazon_location(
                 driver,
                 amazon_domain,
                 zip_code,
                 currency,
                 log_fn=add_log
                )

                if not location_ready:
                 add_log("❌ Amazon delivery location was not applied. Sync stopped.")
                 driver.quit()
                 st.error("Amazon delivery location could not be applied.")
                 st.stop()

            except Exception as e:
                add_log(f"💥 Amazon location setup failed: {str(e)[:150]}")
                driver.quit()
                st.error(f"Amazon location setup failed: {str(e)[:150]}")
                st.stop()

    # =================================================
    # YOUR EXISTING PRODUCT PROCESSING CODE STARTS HERE
    # =================================================
            # try:
            # # set_amazon_zip(driver, zip_code, log_fn=add_log)
            #    location_ready = set_amazon_location(
            #     driver,
            #     amazon_domain,
            #     zip_code,
            #     currency,
            #     log_fn=add_log
            # )

            # if not location_ready:
            #     add_log("❌ Amazon delivery location was not applied. Sync stopped.")
            #     driver.quit()
            #     st.error("Amazon delivery location could not be applied.")
            #     st.stop()

            # ── Process products ───────────────────────────
            updated_count = skipped_count = error_count = 0

            for batch_index, (product, variant) in enumerate(
                work_items[start_index:end_index],
                start=start_index,
            ):
                title = product.get("title") or "Unknown"
                db_save_sync_progress(progress_key, batch_index)
                completed = batch_index - start_index + 1
                add_log(
                    f"🔄 Processing {completed}/{run_total} this run | "
                    f"Item {batch_index + 1}/{total_items} overall | "
                    f"Remaining: {total_items - batch_index - 1}"
                )
                show_live_progress(completed)
                for variant in [variant]:
                    raw_sku = variant.get("sku")
                    sku = str(raw_sku).strip() if raw_sku is not None else ""

                    variant_id = variant["id"]
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
                            "Old Price": f"{currency_symbol}{shopify_price}", "Amazon": "—",
                            "Profit": "—", "New Price": "—", "Action": "⚠️ Bad SKU",
                        })
                        refresh_results()
                        continue

                    add_log(f"🔎 {sku} → {asin}  |  '{title[:35]}'")

                    # try:
                        # amazon_price = scrape_amazon_price(driver, asin)
                        # amazon_price = scrape_amazon_price(
                        #     driver,
                        #     asin,
                        #     amazon_domain
                        # )
                        # # inventory_cost = scrape_inventory_cost(driver, asin)
                        # inventory_cost = scrape_inventory_cost(
                        #     driver,
                        #     asin,
                        #     amazon_domain
                        # )
                    try:
                            amazon_price, amazon_status = scrape_amazon_price(
                                driver,
                                asin,
                                amazon_domain
                            )

                            # inventory_cost = scrape_inventory_cost(driver, asin)
                            inventory_cost = scrape_inventory_cost(
                                driver,
                                asin,
                                amazon_domain
                            )
                    except Exception as e:
                        add_log(f"❌ Scrape error ({asin}): {str(e)[:80]}")
                        error_count += 1
                        continue

                    # if amazon_price is None:
                    #     add_log(f"❌ Price not found — ASIN: {asin}")
                    #     error_count += 1
                    #     # results.append({
                    #     #     "Product": title[:40], "SKU": sku, "ASIN": asin,
                    #     #     "Old Price": f"{currency_symbol}{shopify_price}", "Amazon": "Not Found",
                    #     #     "Profit": "—", "New Price": "—", "Action": "❌ Not Found",
                    #     # })
                    #     results.append({
                    #         "Product": title[:40],
                    #         "SKU": sku,
                    #         "ASIN": asin,
                    #         "Old Price": f"{currency_symbol}{shopify_price}",
                    #         "Amazon": "Not Found",
                    #         "Profit": "—",
                    #         "New Price": "—",
                    #         "Action": "❌ Not Found",
                    #     })
                    #     refresh_results()
                    #     continue
                    if amazon_status in (
                        "unavailable", "not_found", "price_not_found"
                    ):
                        amazon_status_details = {
                            "unavailable": ("Unavailable", "Amazon product unavailable"),
                            "not_found": ("Page Not Found", "Amazon page not found"),
                            "price_not_found": (
                                "Price Not Found", "Amazon price not found"
                            ),
                        }
                        amazon_label, log_message = amazon_status_details[amazon_status]
                        add_log(f"⚠️ {log_message} — ASIN: {asin}")

                        stock_action = f"⚠️ {amazon_label}"
                        if not inventory_item_id:
                            add_log("⚠️ Shopify inventory item ID is missing")
                        elif not inventory_location_id:
                            add_log("⚠️ Shopify stock was not changed (location unavailable)")
                        else:
                            stock_set, stock_error = set_shopify_out_of_stock(
                                shop_domain,
                                headers,
                                inventory_item_id,
                                inventory_location_id,
                                shopify_session,
                            )
                            if stock_set:
                                stock_action = (
                                    f"⚠️ {amazon_label} — Shopify stock set to 0"
                                )
                                add_log(
                                    f"📦 Shopify stock set to 0 at "
                                    f"{inventory_location_name}"
                                )
                            else:
                                stock_action = f"⚠️ {amazon_label} — stock update failed"
                                error_count += 1
                                add_log(
                                    f"❌ Shopify stock update failed: {stock_error[:80]}"
                                )

                        results.append({
                            "Product": title[:40],
                            "SKU": sku,
                            "ASIN": asin,
                            "Old Price": f"{currency_symbol}{shopify_price}",
                            "Amazon": amazon_label,
                            "Profit": "—",
                            "New Price": "—",
                            "Action": stock_action,
                        })

                        skipped_count += 1
                        refresh_results()
                        continue
                    # ── Profit matrix ──────────────────────
                    if inventory_cost is None:
                        add_log(
                            f"❌ Inventory cost not found — ASIN: {asin}"
                        )
                        error_count += 1

                        results.append({
                            "Product": title[:40],
                            "SKU": sku,
                            "ASIN": asin,
                            "Old Price": f"{currency_symbol}{shopify_price}",
                            "Amazon": f"{currency_symbol}{amazon_price}",
                            "Profit": "—",
                            "New Price": "—",
                            "Action": "❌ Inventory Cost Not Found",
                        })

                        refresh_results()
                        continue
                    # profit = profit_for(inventory_cost)
                    # new_price = round(inventory_cost + profit, 2)
                    # ── Profit matrix ──────────────────────
                    # profit = profit_for(inventory_cost, currency)
                    # new_price = round(inventory_cost + profit, 2)

                    # compare_at_price = round(new_price + random.randint(10, 15), 2)
                    profit = profit_for(inventory_cost, currency)
                    new_price = round(inventory_cost + profit, 2)

                    variant_payload = {
                        "id": variant_id,
                        "price": str(new_price),
                    }
                    compare_at_price = None
                    if selected_store != "Testing":
                        compare_at_price = round(new_price + random.randint(10, 15), 2)
                        variant_payload["compare_at_price"] = str(compare_at_price)


                    # add_log(
                    #     f"💰 Amazon: ${amazon_price}  "
                    #     f"+ Profit: ${profit}  "
                    #     f"= New Price: ${new_price}  "
                    #     f"| Compare: ${compare_at_price}  "
                    #     f"Amazon Selling: ${amazon_price} | Inventory Cost: ${inventory_cost}"
                    #     f"(was ${shopify_price})"
                    # )
                    compare_log = (
                        f"| Compare: {currency_symbol}{compare_at_price}  "
                        if compare_at_price is not None else ""
                    )
                    # add_log(
                    #     f"💰 Amazon: {currency_symbol}{amazon_price}  "
                    #     f"+ Profit: {currency_symbol}{profit}  "
                    #     f"= New Price: {currency_symbol}{new_price}  "
                    #     f"| Compare: {currency_symbol}{compare_at_price}  "
                    #     f"Amazon Selling: {currency_symbol}{amazon_price} | "
                    #     f"Inventory Cost: {currency_symbol}{inventory_cost} "
                    #     f"(was {currency_symbol}{shopify_price})"
                    # )
                    add_log(
                        f"💰 Amazon: {currency_symbol}{amazon_price}  "
                        f"+ Profit: {currency_symbol}{profit}  "
                        f"= New Price: {currency_symbol}{new_price}  "
                        f"{compare_log}"
                        f"Amazon Selling: {currency_symbol}{amazon_price} | "
                        f"Inventory Cost: {currency_symbol}{inventory_cost} "
                        f"(was {currency_symbol}{shopify_price})"
                    )

                    try:
                        shopify_session.put(
                            f"https://{shop_domain}/admin/api/2024-10"
                            f"/variants/{variant_id}.json",
                            headers=headers,
                            # json={"variant": {
                            #     "id": variant_id,
                            #     "price": str(new_price),
                            #     "compare_at_price": str(compare_at_price),
                            # }},
                            json={"variant": variant_payload},
                            timeout=(10, 60),
                        ).raise_for_status()

                        if inventory_item_id:
                            shopify_session.put(
                                f"https://{shop_domain}/admin/api/2024-10"
                                f"/inventory_items/{inventory_item_id}.json",
                                headers=headers,
                                json={"inventory_item": {
                                    "id": inventory_item_id,
                                    "cost": str(inventory_cost),
                                }},
                                timeout=(10, 60)
                            ).raise_for_status()

                        # add_log(f"✅ UPDATED: '{title[:35]}' → ${new_price}")
                        add_log(
                            f"✅ UPDATED: '{title[:35]}' → "
                            f"{currency_symbol}{new_price}"
                        )
                        updated_count += 1
                        # results.append({
                        #     "Product": title[:40],
                        #     "SKU": sku,
                        #     "ASIN": asin,
                        #     "Old Price": f"${shopify_price}",
                        #     "Amazon": f"${amazon_price}",
                        #     "Profit": f"+${profit}",
                        #     "New Price": f"${new_price}",
                        #     "Action": "✅ Updated",
                        # })
                        results.append({
                             "Product": title[:40],
                             "SKU": sku,
                             "ASIN": asin,
                             "Old Price": f"{currency_symbol}{shopify_price}",
                             "Amazon": f"{currency_symbol}{amazon_price}",
                             "Profit": f"+{currency_symbol}{profit}",
                             "New Price": f"{currency_symbol}{new_price}",
                             "Action": "✅ Updated",
                         })
                    except Exception as e:
                        add_log(f"❌ Shopify update failed: {str(e)[:80]}")
                        error_count += 1
                        # results.append({
                        #     "Product": title[:40], "SKU": sku, "ASIN": asin,
                        #     "Old Price": f"${shopify_price}", "Amazon": f"${amazon_price}",
                        #     "Profit": f"+${profit}", "New Price": "—",
                        #     "Action": "❌ Update Failed",
                        # })
                        results.append({
                            "Product": title[:40],
                            "SKU": sku,
                            "ASIN": asin,
                            "Old Price": f"{currency_symbol}{shopify_price}",
                            "Amazon": f"{currency_symbol}{amazon_price}",
                            "Profit": f"+{currency_symbol}{profit}",
                            "New Price": "—",
                            "Action": "❌ Update Failed",
                        })

                    refresh_results()

            db_save_sync_progress(progress_key, end_index)
            show_live_progress(run_total)
            add_log(
                f"📌 Batch saved. Next run starts at item "
                f"{end_index + 1} of {len(work_items)}"
            )
            try:
               driver.quit()
               add_log("🧹 Chrome driver closed successfully.")
            except Exception as e:
               add_log(f"⚠️ Chrome driver cleanup failed: {str(e)[:100]}")
            

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

