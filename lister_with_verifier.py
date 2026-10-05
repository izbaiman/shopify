# # # # """
# # # # SC Shopify CSV Uploader
# # # # =======================
# # # # - Upload products directly from a CSV (no browser / Selenium needed)
# # # # - Auth via Client ID + Client Secret (stored per store in SQLite)
# # # # - Duplicate check in real-time by ASIN stored as a metafield tag
# # # # - CSV columns expected: ASIN, Title, Price, List Price, Link
# # # #   (Discount%, Rating, Reviews, Sales columns are optional / ignored)
# # # # """

# # # # import streamlit as st
# # # # import pandas as pd
# # # # import requests
# # # # import sqlite3
# # # # import time
# # # # import re
# # # # import io

# # # # # ─────────────────────────────────────────────
# # # # # PAGE CONFIG
# # # # # ─────────────────────────────────────────────
# # # # st.set_page_config(page_title="SC Shopify Uploader", layout="wide", page_icon="🛍️")

# # # # st.markdown("""
# # # # <style>
# # # # @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

# # # # html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

# # # # /* Dark terminal log */
# # # # .log-box {
# # # #     background: #0a0c10;
# # # #     color: #39ff14;
# # # #     padding: 16px;
# # # #     border-radius: 10px;
# # # #     font-family: 'JetBrains Mono', monospace;
# # # #     font-size: 12px;
# # # #     height: 400px;
# # # #     overflow-y: auto;
# # # #     border: 1px solid #1e2430;
# # # #     line-height: 1.7;
# # # # }
# # # # .log-skip  { color: #f0a500; }
# # # # .log-ok    { color: #39ff14; }
# # # # .log-err   { color: #ff4b4b; }
# # # # .log-info  { color: #5bc8ff; }

# # # # /* Stat cards */
# # # # .stat-card {
# # # #     background: #111827;
# # # #     border: 1px solid #1f2937;
# # # #     border-radius: 12px;
# # # #     padding: 20px;
# # # #     text-align: center;
# # # # }
# # # # .stat-num  { font-size: 2.4rem; font-weight: 800; line-height: 1; }
# # # # .stat-lbl  { font-size: 0.75rem; color: #6b7280; margin-top: 4px; letter-spacing: 0.08em; text-transform: uppercase; }

# # # # /* Buttons */
# # # # .stButton>button {
# # # #     background: linear-gradient(135deg, #ff6a00, #ff9900);
# # # #     color: #fff;
# # # #     border: none;
# # # #     border-radius: 10px;
# # # #     font-weight: 700;
# # # #     font-size: 1rem;
# # # #     height: 3.2em;
# # # #     width: 100%;
# # # #     letter-spacing: 0.04em;
# # # #     transition: opacity 0.2s;
# # # # }
# # # # .stButton>button:hover { opacity: 0.88; }

# # # # /* Progress bar colour */
# # # # .stProgress > div > div { background: #ff9900 !important; }
# # # # </style>
# # # # """, unsafe_allow_html=True)


# # # # # ─────────────────────────────────────────────
# # # # # DATABASE  (stores: name / domain / client_id / client_secret)
# # # # # ─────────────────────────────────────────────
# # # # DB = "shopify_stores.db"

# # # # def init_db():
# # # #     with sqlite3.connect(DB) as conn:
# # # #         # Create table if it doesn't exist at all
# # # #         conn.execute("""
# # # #             CREATE TABLE IF NOT EXISTS stores (
# # # #                 id            INTEGER PRIMARY KEY AUTOINCREMENT,
# # # #                 store_name    TEXT,
# # # #                 domain        TEXT,
# # # #                 client_id     TEXT,
# # # #                 client_secret TEXT
# # # #             )""")
# # # #         conn.commit()

# # # #         # Check if store_name has a UNIQUE index; if not, rebuild the table
# # # #         indexes = conn.execute(
# # # #             "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='stores'"
# # # #         ).fetchall()
# # # #         has_unique = any(
# # # #             row[0] and "store_name" in row[0].upper() and "UNIQUE" in row[0].upper()
# # # #             for row in indexes
# # # #         )
# # # #         # Also check if it was declared UNIQUE inline in the CREATE TABLE
# # # #         table_sql = conn.execute(
# # # #             "SELECT sql FROM sqlite_master WHERE type='table' AND name='stores'"
# # # #         ).fetchone()
# # # #         inline_unique = table_sql and "UNIQUE" in (table_sql[0] or "").upper()

# # # #         if not has_unique and not inline_unique:
# # # #             # Migrate: rename old → temp, recreate with UNIQUE, copy data, drop temp
# # # #             conn.execute("ALTER TABLE stores RENAME TO stores_old")
# # # #             conn.execute("""
# # # #                 CREATE TABLE stores (
# # # #                     id            INTEGER PRIMARY KEY AUTOINCREMENT,
# # # #                     store_name    TEXT UNIQUE,
# # # #                     domain        TEXT,
# # # #                     client_id     TEXT,
# # # #                     client_secret TEXT
# # # #                 )""")
# # # #             conn.execute("""
# # # #                 INSERT OR IGNORE INTO stores (id, store_name, domain, client_id, client_secret)
# # # #                 SELECT id, store_name, domain, client_id, client_secret FROM stores_old
# # # #             """)
# # # #             conn.execute("DROP TABLE stores_old")
# # # #             conn.commit()

# # # # def save_store(name, domain, client_id, secret):
# # # #     with sqlite3.connect(DB) as conn:
# # # #         conn.execute("""
# # # #             INSERT INTO stores (store_name, domain, client_id, client_secret)
# # # #             VALUES (?,?,?,?)
# # # #             ON CONFLICT(store_name) DO UPDATE SET
# # # #                 domain=excluded.domain,
# # # #                 client_id=excluded.client_id,
# # # #                 client_secret=excluded.client_secret
# # # #         """, (name, domain, client_id, secret))
# # # #         conn.commit()

# # # # def all_stores() -> pd.DataFrame:
# # # #     with sqlite3.connect(DB) as conn:
# # # #         return pd.read_sql_query("SELECT * FROM stores", conn)

# # # # def delete_store(sid: int):
# # # #     with sqlite3.connect(DB) as conn:
# # # #         conn.execute("DELETE FROM stores WHERE id=?", (sid,))
# # # #         conn.commit()

# # # # init_db()


# # # # # ─────────────────────────────────────────────
# # # # # SHOPIFY AUTH  — client_credentials flow
# # # # # ─────────────────────────────────────────────
# # # # def get_access_token(domain: str, client_id: str, client_secret: str) -> str | None:
# # # #     """Exchange client_id + client_secret for a short-lived access token."""
# # # #     url = f"https://{domain}/admin/oauth/access_token"
# # # #     try:
# # # #         r = requests.post(url, json={
# # # #             "client_id": client_id,
# # # #             "client_secret": client_secret,
# # # #             "grant_type": "client_credentials"
# # # #         }, timeout=10)
# # # #         if r.status_code == 200:
# # # #             return r.json().get("access_token")
# # # #         # Some private apps use the secret directly — fall back to using it as token
# # # #         st.warning(f"OAuth failed ({r.status_code}). Trying secret as direct token…")
# # # #         return client_secret          # private-app fallback
# # # #     except Exception as e:
# # # #         st.error(f"Auth error: {e}")
# # # #         return None


# # # # # ─────────────────────────────────────────────
# # # # # SHOPIFY HELPERS
# # # # # ─────────────────────────────────────────────
# # # # def sh_headers(token: str) -> dict:
# # # #     return {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

# # # # def get_or_create_collection(domain, token, name) -> int | None:
# # # #     h = sh_headers(token)
# # # #     r = requests.get(
# # # #         f"https://{domain}/admin/api/2024-10/custom_collections.json?limit=250",
# # # #         headers=h, verify=False)
# # # #     if r.status_code == 200:
# # # #         for c in r.json().get("custom_collections", []):
# # # #             if c["title"].strip().lower() == name.strip().lower():
# # # #                 return c["id"]
# # # #     r2 = requests.post(
# # # #         f"https://{domain}/admin/api/2024-10/custom_collections.json",
# # # #         headers=h, json={"custom_collection": {"title": name}}, verify=False)
# # # #     if r2.status_code == 201:
# # # #         return r2.json()["custom_collection"]["id"]
# # # #     return None

# # # # def add_to_collection(domain, token, product_id, collection_id):
# # # #     requests.post(
# # # #         f"https://{domain}/admin/api/2024-10/collects.json",
# # # #         headers=sh_headers(token),
# # # #         json={"collect": {"product_id": product_id, "collection_id": collection_id}},
# # # #         verify=False)

# # # # def fetch_all_products(domain, token) -> list:
# # # #     """Pages through all products and returns them."""
# # # #     products, url = [], f"https://{domain}/admin/api/2024-10/products.json?limit=250"
# # # #     while url:
# # # #         r = requests.get(url, headers=sh_headers(token), verify=False)
# # # #         if r.status_code == 200:
# # # #             products.extend(r.json().get("products", []))
# # # #             link = r.headers.get("Link", "")
# # # #             url = None
# # # #             if 'rel="next"' in link:
# # # #                 for part in link.split(","):
# # # #                     if 'rel="next"' in part:
# # # #                         url = part.split(";")[0].strip("<> ")
# # # #         elif r.status_code == 429:
# # # #             time.sleep(2)
# # # #         else:
# # # #             break
# # # #     return products

# # # # def build_asin_set(products: list) -> set:
# # # #     """
# # # #     Collects all ASINs that already exist in the store.
# # # #     We store the ASIN inside the product tags as  'ASIN:B0XXXXXXXX'
# # # #     so we can look them up without metafields.
# # # #     """
# # # #     asins = set()
# # # #     for p in products:
# # # #         for tag in (p.get("tags") or "").split(","):
# # # #             t = tag.strip()
# # # #             if t.upper().startswith("ASIN:"):
# # # #                 asins.add(t[5:].strip().upper())
# # # #     return asins

# # # # def build_sku_set(products: list) -> set:
# # # #     skus = set()
# # # #     for p in products:
# # # #         for v in p.get("variants", []):
# # # #             s = (v.get("sku") or "").strip().upper()
# # # #             if s:
# # # #                 skus.add(s)
# # # #     return skus


# # # # # ─────────────────────────────────────────────
# # # # # PRICING MATRIX
# # # # # ─────────────────────────────────────────────
# # # # def profit_for(cost: float) -> float:
# # # #     table = [
# # # #         (15, 10), (50, 16), (100, 22), (150, 27), (200, 33),
# # # #         (250, 37), (300, 45), (350, 55), (400, 60), (450, 65),
# # # #         (500, 70), (550, 75), (600, 78), (650, 80),
# # # #     ]
# # # #     for threshold, profit in table:
# # # #         if cost <= threshold:
# # # #             return profit
# # # #     return 100


# # # # # ─────────────────────────────────────────────
# # # # # CSV PARSING
# # # # # ─────────────────────────────────────────────
# # # # REQUIRED_COLS = {"ASIN", "Title", "Price", "Link"}

# # # # def parse_csv(uploaded_file) -> pd.DataFrame | None:
# # # #     """Accepts tab-separated or comma-separated CSV / TSV."""
# # # #     try:
# # # #         raw = uploaded_file.read()
# # # #         # Try tab first (matches the sample), then comma
# # # #         for sep in ("\t", ","):
# # # #             try:
# # # #                 df = pd.read_csv(io.BytesIO(raw), sep=sep, dtype=str)
# # # #                 df.columns = [c.strip() for c in df.columns]
# # # #                 if REQUIRED_COLS.issubset(set(df.columns)):
# # # #                     return df
# # # #             except Exception:
# # # #                 continue
# # # #         st.error("CSV must have at minimum: ASIN, Title, Price, Link columns.")
# # # #         return None
# # # #     except Exception as e:
# # # #         st.error(f"Failed to read file: {e}")
# # # #         return None

# # # # def clean(text: str) -> str:
# # # #     if not text:
# # # #         return ""
# # # #     return re.sub(
# # # #         r'amazon|walmart|prime|shipped from|sold by|'
# # # #         r'›?\s*See more product details|›?\s*See details',
# # # #         '', str(text), flags=re.IGNORECASE
# # # #     ).strip()


# # # # # ─────────────────────────────────────────────
# # # # # SIDEBAR
# # # # # ─────────────────────────────────────────────
# # # # with st.sidebar:
# # # #     st.markdown("## 🛍️ SC Uploader")
# # # #     st.divider()

# # # #     stores_df = all_stores()
# # # #     store_names = stores_df["store_name"].tolist() if not stores_df.empty else []

# # # #     if store_names:
# # # #         selected_store_name = st.selectbox("Select Store", store_names)
# # # #         selected_store = stores_df[stores_df["store_name"] == selected_store_name].iloc[0]
# # # #     else:
# # # #         st.warning("No stores saved yet. Go to ⚙️ Manage Stores tab.")
# # # #         selected_store = None
# # # #         selected_store_name = None

# # # #     st.divider()
# # # #     st.subheader("📦 Product Settings")
# # # #     vendor_name     = st.text_input("Vendor / Brand Name",  value="SC Store")
# # # #     collection_name = st.text_input("Collection Name",      value="New Arrivals")
# # # #     sku_prefix      = st.text_input("SKU Prefix",           value="CS").strip().upper()

# # # #     st.divider()
# # # #     uploaded_csv = st.file_uploader("📄 Upload Product CSV", type=["csv", "tsv", "txt"])

# # # #     st.divider()
# # # #     st.caption("Built for SC Store — no browser needed 🚀")


# # # # # ─────────────────────────────────────────────
# # # # # MAIN TABS
# # # # # ─────────────────────────────────────────────
# # # # st.title("🛍️ SC Shopify CSV Uploader")

# # # # tab_upload, tab_audit, tab_stores_tab = st.tabs([
# # # #     "🚀 Upload Products",
# # # #     "🔍 SKU / ASIN Audit",
# # # #     "⚙️ Manage Stores",
# # # # ])


# # # # # ══════════════════════════════════════════════
# # # # # TAB 1 — UPLOAD
# # # # # ══════════════════════════════════════════════
# # # # with tab_upload:

# # # #     # Live stat counters
# # # #     c1, c2, c3, c4 = st.columns(4)
# # # #     stat_total    = c1.empty()
# # # #     stat_uploaded = c2.empty()
# # # #     stat_skipped  = c3.empty()
# # # #     stat_errors   = c4.empty()

# # # #     def render_stats(total=0, uploaded=0, skipped=0, errors=0):
# # # #         for holder, num, label, colour in [
# # # #             (stat_total,    total,    "Total Rows",  "#5bc8ff"),
# # # #             (stat_uploaded, uploaded, "Uploaded",    "#39ff14"),
# # # #             (stat_skipped,  skipped,  "Skipped",     "#f0a500"),
# # # #             (stat_errors,   errors,   "Errors",      "#ff4b4b"),
# # # #         ]:
# # # #             holder.markdown(f"""
# # # #             <div class="stat-card">
# # # #               <div class="stat-num" style="color:{colour}">{num}</div>
# # # #               <div class="stat-lbl">{label}</div>
# # # #             </div>""", unsafe_allow_html=True)

# # # #     render_stats()

# # # #     progress_bar = st.progress(0)
# # # #     log_box      = st.empty()
# # # #     log_lines: list[str] = []

# # # #     def log(msg: str, kind: str = "info"):
# # # #         ts   = time.strftime("%H:%M:%S")
# # # #         css  = {"ok": "log-ok", "skip": "log-skip",
# # # #                 "err": "log-err", "info": "log-info"}.get(kind, "log-info")
# # # #         line = f'<span class="{css}">[{ts}] {msg}</span>'
# # # #         log_lines.insert(0, line)
# # # #         log_box.markdown(
# # # #             f'<div class="log-box">{"<br>".join(log_lines)}</div>',
# # # #             unsafe_allow_html=True)

# # # #     if st.button("🚀 START UPLOAD"):
# # # #         if not selected_store is not None and selected_store_name:
# # # #             st.error("Please select a store from the sidebar.")
# # # #         elif not uploaded_csv:
# # # #             st.error("Please upload a CSV file.")
# # # #         else:
# # # #             domain   = selected_store["domain"].strip()
# # # #             c_id     = selected_store["client_id"].strip()
# # # #             c_secret = selected_store["client_secret"].strip()

# # # #             # ── 1. Authenticate ─────────────────────
# # # #             log("Authenticating with Shopify…")
# # # #             token = get_access_token(domain, c_id, c_secret)
# # # #             if not token:
# # # #                 st.error("Authentication failed. Check your Client ID & Secret.")
# # # #                 st.stop()
# # # #             log("✅ Authenticated!", "ok")

# # # #             # ── 2. Collection ───────────────────────
# # # #             log(f"Checking collection '{collection_name}'…")
# # # #             coll_id = get_or_create_collection(domain, token, collection_name)
# # # #             if coll_id:
# # # #                 log(f"✅ Collection ready (ID {coll_id})", "ok")
# # # #             else:
# # # #                 log("⚠️  Collection unavailable — uploading without it.", "skip")

# # # #             # ── 3. Load ALL existing ASINs & SKUs ──
# # # #             log("🔎 Fetching existing products from Shopify…")
# # # #             existing_products = fetch_all_products(domain, token)
# # # #             existing_asins    = build_asin_set(existing_products)
# # # #             existing_skus     = build_sku_set(existing_products)
# # # #             log(f"📋 Store has {len(existing_products)} products | "
# # # #                 f"{len(existing_asins)} tagged ASINs | {len(existing_skus)} SKUs", "info")

# # # #             # ── 4. Parse CSV ────────────────────────
# # # #             df = parse_csv(uploaded_csv)
# # # #             if df is None:
# # # #                 st.stop()

# # # #             total    = len(df)
# # # #             uploaded = skipped = errors = 0
# # # #             render_stats(total)
# # # #             log(f"📄 CSV loaded — {total} rows to process", "info")

# # # #             api_url = f"https://{domain}/admin/api/2024-10/products.json"
# # # #             headers = sh_headers(token)

# # # #             for idx, row in df.iterrows():
# # # #                 progress_bar.progress((idx + 1) / total)

# # # #                 asin  = str(row.get("ASIN", "")).strip().upper()
# # # #                 title = clean(str(row.get("Title", f"Product {idx}")))
# # # #                 link  = str(row.get("Link", "")).strip()

# # # #                 if not asin or not link or "http" not in link:
# # # #                     log(f"Row {idx+1} — skipped (missing ASIN or Link)", "skip")
# # # #                     skipped += 1
# # # #                     render_stats(total, uploaded, skipped, errors)
# # # #                     continue

# # # #                 # ── REAL-TIME DUPLICATE CHECK ───────
# # # #                 if asin in existing_asins:
# # # #                     log(f"⏭️  SKIP — ASIN {asin} already in store | {title[:55]}…", "skip")
# # # #                     skipped += 1
# # # #                     render_stats(total, uploaded, skipped, errors)
# # # #                     continue

# # # #                 sku = f"{sku_prefix}{asin[2:]}"          # CS + last 8 chars of ASIN
# # # #                 if sku.upper() in existing_skus:
# # # #                     log(f"⏭️  SKIP — SKU {sku} already in store | {title[:55]}…", "skip")
# # # #                     skipped += 1
# # # #                     render_stats(total, uploaded, skipped, errors)
# # # #                     continue

# # # #                 # ── PRICING ─────────────────────────
# # # #                 try:
# # # #                     cost = float(re.sub(r"[^\d.]", "", str(row.get("Price", "0"))))
# # # #                 except ValueError:
# # # #                     cost = 0.0

# # # #                 list_price_raw = str(row.get("List Price", "")).strip()
# # # #                 try:
# # # #                     list_price = float(re.sub(r"[^\d.]", "", list_price_raw))
# # # #                 except ValueError:
# # # #                     list_price = 0.0

# # # #                 profit        = profit_for(cost)
# # # #                 selling_price = round(cost + profit, 2)
# # # #                 compare_price = round(list_price if list_price > selling_price
# # # #                                       else selling_price + 8.0, 2)

# # # #                 # ── TAGS (breadcrumbs + ASIN marker) ─
# # # #                 tag_parts = [f"ASIN:{asin}"]             # key tag for future dupe checks
# # # #                 rating = str(row.get("Rating", "")).strip()
# # # #                 if rating and rating != "nan":
# # # #                     tag_parts.append(f"Rating:{rating}")
# # # #                 final_tags = ", ".join(tag_parts)

# # # #                 # ── BUILD PAYLOAD ────────────────────
# # # #                 # Images: we can't scrape without a browser, but the Amazon URL
# # # #                 # gives us one hero image via the ASIN — add it as a fallback.
# # # #                 # If you also have an "Image" column in CSV, that takes priority.
# # # #                 images = []
# # # #                 img_col = str(row.get("Image", "")).strip()
# # # #                 if img_col and img_col.startswith("http"):
# # # #                     images = [{"src": img_col}]

# # # #                 payload = {
# # # #                     "product": {
# # # #                         "title": title,
# # # #                         "body_html": (
# # # #                             f'<p><strong>Rating:</strong> {rating} ⭐</p>'
# # # #                             f'<p>Source: <a href="{link}" target="_blank">'
# # # #                             f'View on Amazon</a></p>'
# # # #                         ),
# # # #                         "vendor": vendor_name,
# # # #                         "tags": final_tags,
# # # #                         "status": "active",
# # # #                         "variants": [{
# # # #                             "price": str(selling_price),
# # # #                             "compare_at_price": str(compare_price),
# # # #                             "cost": str(cost),
# # # #                             "sku": sku,
# # # #                         }],
# # # #                         **({"images": images} if images else {}),
# # # #                     }
# # # #                 }

# # # #                 # ── UPLOAD ───────────────────────────
# # # #                 r = requests.post(api_url, headers=headers,
# # # #                                   json=payload, verify=False)

# # # #                 if r.status_code == 201:
# # # #                     pid = r.json()["product"]["id"]
# # # #                     # Register new ASIN + SKU so subsequent rows are checked too
# # # #                     existing_asins.add(asin)
# # # #                     existing_skus.add(sku.upper())

# # # #                     if coll_id:
# # # #                         add_to_collection(domain, token, pid, coll_id)

# # # #                     uploaded += 1
# # # #                     log(f"✅ Uploaded — {sku} | £{selling_price} | {title[:50]}…", "ok")
# # # #                 elif r.status_code == 429:
# # # #                     log("⏳ Rate limited — waiting 3 s…", "info")
# # # #                     time.sleep(3)
# # # #                     errors += 1
# # # #                     log(f"❌ Error — {sku}: {r.text[:80]}", "err")
# # # #                 else:
# # # #                     errors += 1
# # # #                     log(f"❌ Error — {sku}: {r.text[:80]}", "err")

# # # #                 render_stats(total, uploaded, skipped, errors)
# # # #                 time.sleep(0.3)          # gentle rate limit

# # # #             progress_bar.progress(1.0)
# # # #             log("─" * 60, "info")
# # # #             log(f"🏁 Done!  Uploaded: {uploaded}  |  Skipped: {skipped}  |  Errors: {errors}", "ok")
# # # #             if uploaded:
# # # #                 st.balloons()


# # # # # ══════════════════════════════════════════════
# # # # # TAB 2 — SKU / ASIN AUDIT
# # # # # ══════════════════════════════════════════════
# # # # with tab_audit:
# # # #     st.subheader("🔍 Scan Store for Duplicate SKUs or ASINs")

# # # #     if selected_store is None:
# # # #         st.warning("Please select a store in the sidebar first.")
# # # #     else:
# # # #         a_col, b_col = st.columns(2)

# # # #         with a_col:
# # # #             if st.button("🚀 Run Full Duplicate Audit", use_container_width=True):
# # # #                 with st.spinner("Authenticating…"):
# # # #                     tok = get_access_token(
# # # #                         selected_store["domain"],
# # # #                         selected_store["client_id"],
# # # #                         selected_store["client_secret"])
# # # #                 if not tok:
# # # #                     st.error("Auth failed.")
# # # #                 else:
# # # #                     with st.spinner("Fetching products…"):
# # # #                         prods = fetch_all_products(selected_store["domain"], tok)

# # # #                     sku_map: dict = {}
# # # #                     for p in prods:
# # # #                         for v in p.get("variants", []):
# # # #                             sku = (v.get("sku") or "").strip()
# # # #                             if sku:
# # # #                                 sku_map.setdefault(sku, []).append({
# # # #                                     "Product Title": p.get("title"),
# # # #                                     "Variant ID": v.get("id"),
# # # #                                     "Price": v.get("price"),
# # # #                                 })
# # # #                     dupes = {s: items for s, items in sku_map.items() if len(items) > 1}
# # # #                     st.session_state["dupes"] = dupes
# # # #                     st.session_state["total_prods"] = len(prods)

# # # #         with b_col:
# # # #             if st.button("📊 Count Unique ASINs & SKUs", use_container_width=True):
# # # #                 with st.spinner("Loading…"):
# # # #                     tok = get_access_token(
# # # #                         selected_store["domain"],
# # # #                         selected_store["client_id"],
# # # #                         selected_store["client_secret"])
# # # #                     if tok:
# # # #                         prods  = fetch_all_products(selected_store["domain"], tok)
# # # #                         asins  = build_asin_set(prods)
# # # #                         skus   = build_sku_set(prods)
# # # #                         st.info(
# # # #                             f"**{len(prods)}** products  |  "
# # # #                             f"**{len(asins)}** tagged ASINs  |  "
# # # #                             f"**{len(skus)}** unique SKUs")

# # # #         if "dupes" in st.session_state:
# # # #             dupes = st.session_state["dupes"]
# # # #             total_p = st.session_state.get("total_prods", "?")
# # # #             st.caption(f"Scanned **{total_p}** products total")

# # # #             if not dupes:
# # # #                 st.balloons()
# # # #                 st.success("✅ No duplicate SKUs found — your store is clean!")
# # # #             else:
# # # #                 st.warning(f"⚠️ Found **{len(dupes)}** duplicate SKU(s)")
# # # #                 rows = []
# # # #                 for sku, items in dupes.items():
# # # #                     for item in items:
# # # #                         rows.append({"SKU": sku, **item})
# # # #                 df_d = pd.DataFrame(rows)
# # # #                 st.dataframe(df_d, use_container_width=True)
# # # #                 csv_bytes = df_d.to_csv(index=False).encode()
# # # #                 st.download_button(
# # # #                     "📥 Download Report (CSV)",
# # # #                     csv_bytes, "duplicate_skus.csv", "text/csv")


# # # # # ══════════════════════════════════════════════
# # # # # TAB 3 — MANAGE STORES
# # # # # ══════════════════════════════════════════════
# # # # with tab_stores_tab:
# # # #     st.subheader("➕ Add or Update a Store")

# # # #     with st.form("store_form"):
# # # #         fc1, fc2 = st.columns(2)
# # # #         f_name   = fc1.text_input("Store Nickname  (e.g. My Main Store)")
# # # #         f_domain = fc2.text_input("Shopify Domain  (e.g. mystore.myshopify.com)")
# # # #         fc3, fc4 = st.columns(2)
# # # #         f_cid    = fc3.text_input("Client ID")
# # # #         f_secret = fc4.text_input("Client Secret", type="password")

# # # #         submitted = st.form_submit_button("💾 Save Store")
# # # #         if submitted:
# # # #             if f_name and f_domain and f_cid and f_secret:
# # # #                 save_store(f_name,
# # # #                            f_domain.replace("https://","").replace("http://",""),
# # # #                            f_cid, f_secret)
# # # #                 st.success(f"Store **{f_name}** saved!")
# # # #                 st.rerun()
# # # #             else:
# # # #                 st.error("Please fill in all four fields.")

# # # #     st.divider()
# # # #     st.subheader("Saved Stores")
# # # #     stores_df = all_stores()
# # # #     if stores_df.empty:
# # # #         st.info("No stores saved yet.")
# # # #     else:
# # # #         for _, row in stores_df.iterrows():
# # # #             with st.expander(f"🏪 {row['store_name']}  —  {row['domain']}"):
# # # #                 st.code(f"Client ID : {row['client_id']}", language=None)
# # # #                 st.code(f"Domain    : {row['domain']}",    language=None)
# # # #                 if st.button(f"🗑️ Delete {row['store_name']}", key=f"del_{row['id']}"):
# # # #                     delete_store(int(row["id"]))
# # # #                     st.rerun()





# # # """
# # # SC Shopify Master Uploader
# # # ==========================
# # # - CSV provides the product list (ASIN, Title, Price, List Price, Link)
# # # - Selenium scrapes each Amazon link for: images, description, tags
# # # - Access token stored per store in SQLite — just select store name to run
# # # - Real-time duplicate check by ASIN tag + SKU before scraping/uploading
# # # """
# # # """
# # # SC Shopify Master Uploader
# # # ==========================
# # # - CSV provides the product list (ASIN, Title, Price, List Price, Link)
# # # - Selenium scrapes each Amazon link for: images, description, tags
# # # - Access token stored per store in SQLite — just select store name to run
# # # - Real-time duplicate check by ASIN tag + SKU before scraping/uploading
# # # """

# # # import streamlit as st
# # # import pandas as pd
# # # import requests
# # # import sqlite3
# # # import time
# # # import re
# # # import io
# # # import os
# # # import shutil
# # # import tempfile
# # # import urllib3
# # # from pathlib import Path
# # # import random
# # # import undetected_chromedriver as uc
# # # from selenium.webdriver.common.by import By
# # # from selenium.webdriver.support.ui import WebDriverWait
# # # from selenium.webdriver.support import expected_conditions as EC

# # # urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # # # PAGE CONFIG
# # # st.set_page_config(page_title="SC Shopify Uploader", layout="wide", page_icon="\U0001f6cd\ufe0f")

# # # st.markdown("""
# # # <style>
# # # @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
# # # html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
# # # .log-box {
# # #     background: #0a0c10; color: #39ff14; padding: 16px; border-radius: 10px;
# # #     font-family: 'JetBrains Mono', monospace; font-size: 12px;
# # #     height: 420px; overflow-y: auto; border: 1px solid #1e2430; line-height: 1.8;
# # # }
# # # .log-skip { color: #f0a500; } .log-ok { color: #39ff14; }
# # # .log-err  { color: #ff4b4b; } .log-info { color: #5bc8ff; }
# # # .stat-card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; text-align: center; }
# # # .stat-num  { font-size: 2.4rem; font-weight: 800; line-height: 1; }
# # # .stat-lbl  { font-size: 0.75rem; color: #6b7280; margin-top: 4px; letter-spacing: 0.08em; text-transform: uppercase; }
# # # .stButton>button {
# # #     background: linear-gradient(135deg, #ff6a00, #ff9900); color: #fff; border: none;
# # #     border-radius: 10px; font-weight: 700; font-size: 1rem; height: 3.2em; width: 100%;
# # #     letter-spacing: 0.04em; transition: opacity 0.2s;
# # # }
# # # .stButton>button:hover { opacity: 0.88; }
# # # .stProgress > div > div { background: #ff9900 !important; }
# # # </style>
# # # """, unsafe_allow_html=True)

# # # # DATABASE
# # # DB = "shopify_stores.db"

# # # def init_db():
# # #     with sqlite3.connect(DB) as conn:
# # #         conn.execute("""
# # #             CREATE TABLE IF NOT EXISTS stores (
# # #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #                 store_name TEXT, domain TEXT, client_id TEXT, client_secret TEXT
# # #             )""")
# # #         conn.commit()
# # #         table_sql = (conn.execute(
# # #             "SELECT sql FROM sqlite_master WHERE type='table' AND name='stores'"
# # #         ).fetchone() or ("",))[0]
# # #         indexes = conn.execute(
# # #             "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='stores'"
# # #         ).fetchall()
# # #         has_unique_index = any(
# # #             r[0] and "store_name" in r[0].upper() and "UNIQUE" in r[0].upper()
# # #             for r in indexes
# # #         )
# # #         if "UNIQUE" not in table_sql.upper() and not has_unique_index:
# # #             conn.execute("ALTER TABLE stores RENAME TO stores_old")
# # #             conn.execute("""
# # #                 CREATE TABLE stores (
# # #                     id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #                     store_name TEXT UNIQUE, domain TEXT, client_id TEXT, client_secret TEXT
# # #                 )""")
# # #             conn.execute("""
# # #                 INSERT OR IGNORE INTO stores (id,store_name,domain,client_id,client_secret)
# # #                 SELECT id,store_name,domain,client_id,client_secret FROM stores_old
# # #             """)
# # #             conn.execute("DROP TABLE stores_old")
# # #             conn.commit()

# # # def save_store(name, domain, client_id, secret):
# # #     with sqlite3.connect(DB) as conn:
# # #         conn.execute("""
# # #             INSERT INTO stores (store_name,domain,client_id,client_secret) VALUES (?,?,?,?)
# # #             ON CONFLICT(store_name) DO UPDATE SET
# # #                 domain=excluded.domain, client_id=excluded.client_id, client_secret=excluded.client_secret
# # #         """, (name, domain, client_id, secret))
# # #         conn.commit()

# # # def all_stores():
# # #     with sqlite3.connect(DB) as conn:
# # #         return pd.read_sql_query("SELECT * FROM stores", conn)

# # # def delete_store(sid):
# # #     with sqlite3.connect(DB) as conn:
# # #         conn.execute("DELETE FROM stores WHERE id=?", (sid,))
# # #         conn.commit()

# # # init_db()

# # # # SHOPIFY HELPERS
# # # def sh_headers(token):
# # #     return {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

# # # def get_oauth_token(domain, client_id, client_secret):
# # #     """
# # #     Generate a fresh access token using Client ID + Client Secret.
# # #     This is the correct flow for Shopify custom apps using client credentials.
# # #     Returns (token_string, error_message)
# # #     """
# # #     url = f"https://{domain}/admin/oauth/access_token"
# # #     payload = {
# # #         "client_id": client_id,
# # #         "client_secret": client_secret,
# # #         "grant_type": "client_credentials"
# # #     }
# # #     try:
# # #         r = requests.post(url, json=payload, timeout=15, verify=False)
# # #         if r.status_code == 200:
# # #             token = r.json().get("access_token", "")
# # #             if token:
# # #                 return token, ""
# # #             return "", "Response OK but no access_token in response"
# # #         return "", f"HTTP {r.status_code}: {r.text[:200]}"
# # #     except Exception as e:
# # #         return "", str(e)

# # # def verify_token(domain, token):
# # #     """Verify a token works by calling shop.json. Returns (bool, status, reason)."""
# # #     try:
# # #         r = requests.get(
# # #             f"https://{domain}/admin/api/2024-10/shop.json",
# # #             headers=sh_headers(token), timeout=15, verify=False)
# # #         if r.status_code == 200:
# # #             return True, 200, ""
# # #         return False, r.status_code, r.text[:200]
# # #     except Exception as e:
# # #         return False, 0, str(e)

# # # def get_or_create_collection(domain, token, name):
# # #     h = sh_headers(token)
# # #     r = requests.get(f"https://{domain}/admin/api/2024-10/custom_collections.json?limit=250",
# # #                      headers=h, verify=False)
# # #     if r.status_code == 200:
# # #         for c in r.json().get("custom_collections", []):
# # #             if c["title"].strip().lower() == name.strip().lower():
# # #                 return c["id"]
# # #     r2 = requests.post(f"https://{domain}/admin/api/2024-10/custom_collections.json",
# # #                        headers=h, json={"custom_collection": {"title": name}}, verify=False)
# # #     return r2.json()["custom_collection"]["id"] if r2.status_code == 201 else None

# # # def add_to_collection(domain, token, product_id, collection_id):
# # #     requests.post(f"https://{domain}/admin/api/2024-10/collects.json",
# # #                   headers=sh_headers(token),
# # #                   json={"collect": {"product_id": product_id, "collection_id": collection_id}},
# # #                   verify=False)

# # # def fetch_all_products(domain, token):
# # #     products, url = [], f"https://{domain}/admin/api/2024-10/products.json?limit=250"
# # #     while url:
# # #         r = requests.get(url, headers=sh_headers(token), verify=False)
# # #         if r.status_code == 200:
# # #             products.extend(r.json().get("products", []))
# # #             lh = r.headers.get("Link", "")
# # #             url = None
# # #             if 'rel="next"' in lh:
# # #                 for part in lh.split(","):
# # #                     if 'rel="next"' in part:
# # #                         url = part.split(";")[0].strip("<> ")
# # #         elif r.status_code == 429:
# # #             time.sleep(2)
# # #         else:
# # #             break
# # #     return products

# # # def build_asin_set(products):
# # #     asins = set()
# # #     for p in products:
# # #         for tag in (p.get("tags") or "").split(","):
# # #             t = tag.strip()
# # #             if t.upper().startswith("ASIN:"):
# # #                 asins.add(t[5:].strip().upper())
# # #     return asins

# # # def build_sku_set(products):
# # #     skus = set()
# # #     for p in products:
# # #         for v in p.get("variants", []):
# # #             s = (v.get("sku") or "").strip().upper()
# # #             if s:
# # #                 skus.add(s)
# # #     return skus

# # # # PRICING MATRIX
# # # def profit_for(cost):
# # #     table = [(15,10),(50,16),(100,22),(150,27),(200,33),(250,37),
# # #              (300,45),(350,55),(400,60),(450,65),(500,70),(550,75),(600,78),(650,80)]
# # #     for t, p in table:
# # #         if cost <= t:
# # #             return p
# # #     return 100

# # # # CSV PARSING
# # # REQUIRED_COLS = {"ASIN", "Title", "Price", "Link"}

# # # def parse_csv(uploaded_file):
# # #     try:
# # #         raw = uploaded_file.read()
# # #         for sep in ("\t", ",", ";"):
# # #             try:
# # #                 df = pd.read_csv(io.BytesIO(raw), sep=sep, dtype=str)
# # #                 df.columns = [c.strip() for c in df.columns]
# # #                 if REQUIRED_COLS.issubset(set(df.columns)):
# # #                     return df
# # #             except:
# # #                 continue
# # #         st.error("CSV needs: ASIN, Title, Price, Link columns.")
# # #         return None
# # #     except Exception as e:
# # #         st.error(f"Read error: {e}")
# # #         return None

# # # def scrub(text):
# # #     if not text: return ""
# # #     text = re.sub(r'amazon|walmart|prime|shipped from|sold by', '', str(text), flags=re.IGNORECASE)
# # #     text = re.sub(r'\u203a?\s*See more product details|\u203a?\s*See details', '', text, flags=re.IGNORECASE)
# # #     return text.strip()

# # # import subprocess
# # # import json

# # # # SELENIUM
# # # def clean_uc_cache():
# # #     p = os.path.join(os.environ.get("APPDATA", ""), "undetected_chromedriver")
# # #     if os.path.exists(p):
# # #         shutil.rmtree(p, ignore_errors=True)

# # # def get_chrome_version():
# # #     """Auto-detect installed Chrome major version."""
# # #     paths = [
# # #         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
# # #         r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
# # #         r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get("USERNAME","")),
# # #     ]
# # #     for path in paths:
# # #         if os.path.exists(path):
# # #             try:
# # #                 result = subprocess.run(
# # #                     [path, "--version"], capture_output=True, text=True, timeout=5)
# # #                 ver = result.stdout.strip()
# # #                 match = re.search(r"(\d+)\.\d+\.\d+\.\d+", ver)
# # #                 if match:
# # #                     return int(match.group(1))
# # #             except:
# # #                 pass
# # #     # Fallback: try registry
# # #     try:
# # #         import winreg
# # #         key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
# # #             r"Software\Google\Chrome\BLBeacon")
# # #         ver, _ = winreg.QueryValueEx(key, "version")
# # #         winreg.CloseKey(key)
# # #         return int(ver.split(".")[0])
# # #     except:
# # #         pass
# # #     return None  # will let uc auto-detect

# # # def build_driver():
# # #     clean_uc_cache()
# # #     opts = uc.ChromeOptions()
# # #     opts.add_argument("--no-sandbox")
# # #     opts.add_argument("--disable-dev-shm-usage")
# # #     opts.add_argument("--start-maximized")
# # #     opts.add_argument("--disable-blink-features=AutomationControlled")
# # #     opts.add_argument(f"--user-data-dir={Path(tempfile.mkdtemp(prefix='uc_'))}")

# # #     chrome_ver = get_chrome_version()

# # #     kwargs = {"options": opts, "use_subprocess": True}
# # #     if chrome_ver:
# # #         kwargs["version_main"] = chrome_ver

# # #     try:
# # #         driver = uc.Chrome(**kwargs)
# # #         return driver
# # #     except Exception as e1:
# # #         # Clear stale driver files and retry without version pin
# # #         root = Path(os.environ.get("APPDATA","")) / "undetected_chromedriver"
# # #         for p in [root/"undetected_chromedriver.exe", root/"undetected"]:
# # #             try:
# # #                 if p.is_file(): p.unlink()
# # #                 elif p.is_dir(): shutil.rmtree(p, ignore_errors=True)
# # #             except: pass
# # #         time.sleep(2)
# # #         try:
# # #             driver = uc.Chrome(options=opts, use_subprocess=True)
# # #             return driver
# # #         except Exception as e2:
# # #             raise RuntimeError(
# # #                 f"Chrome failed to start.\n"
# # #                 f"Detected version: {chrome_ver}\n"
# # #                 f"Error: {e2}\n\n"
# # #                 f"Fix: Make sure Google Chrome is installed and up to date."
# # #             )

# # # # SIDEBAR
# # # with st.sidebar:
# # #     st.markdown("## \U0001f6cd\ufe0f SC Uploader")
# # #     st.divider()
# # #     stores_df   = all_stores()
# # #     store_names = stores_df["store_name"].tolist() if not stores_df.empty else []
# # #     if store_names:
# # #         selected_store_name = st.selectbox("Select Store", store_names)
# # #         selected_store = stores_df[stores_df["store_name"] == selected_store_name].iloc[0]
# # #         cid_preview = selected_store["client_id"] or ""
# # #         if cid_preview:
# # #             st.caption(f"Client ID: {cid_preview[:8]}...")
# # #             st.caption(f"Domain: {selected_store['domain']}")
# # #         else:
# # #             st.warning("No Client ID saved — update in Manage Stores.")
# # #     else:
# # #         st.warning("No stores yet — add one in Manage Stores tab.")
# # #         selected_store = None; selected_store_name = None
# # #     st.divider()
# # #     st.subheader("\U0001f4e6 Product Settings")
# # #     vendor_name     = st.text_input("Vendor / Brand Name", value="SC Store")
# # #     collection_name = st.text_input("Collection Name",     value="New Arrivals")
# # #     sku_prefix      = st.text_input("SKU Prefix",          value="CS").strip().upper()
# # #     zip_code        = st.text_input("Amazon Zip Code",     value="10001").strip()
# # #     st.divider()
# # #     uploaded_csv = st.file_uploader("\U0001f4c4 Upload Product CSV", type=["csv","tsv","txt"])
# # #     st.caption("Needs: ASIN, Title, Price, Link columns")

# # # # MAIN TABS
# # # st.title("\U0001f6cd\ufe0f SC Shopify Master Uploader")

# # # tab_upload, tab_audit, tab_stores_tab = st.tabs([
# # #     "\U0001f680 Upload Products", "\U0001f50d SKU / ASIN Audit", "\u2699\ufe0f Manage Stores"
# # # ])

# # # # TAB 1 — UPLOAD
# # # with tab_upload:
# # #     col_browser, col_right = st.columns([1,1])
# # #     with col_browser:
# # #         st.subheader("\U0001f4fa Browser Monitor")
# # #         browser_frame = st.empty()
# # #         browser_frame.info("Awaiting start…")
# # #     with col_right:
# # #         st.subheader("\U0001f4ca Progress")
# # #         c1,c2,c3,c4 = st.columns(4)
# # #         stat_total=c1.empty(); stat_uploaded=c2.empty()
# # #         stat_skipped=c3.empty(); stat_errors=c4.empty()

# # #     def render_stats(total=0,uploaded=0,skipped=0,errors=0):
# # #         for holder,num,label,colour in [
# # #             (stat_total,total,"Total","#5bc8ff"),(stat_uploaded,uploaded,"Uploaded","#39ff14"),
# # #             (stat_skipped,skipped,"Skipped","#f0a500"),(stat_errors,errors,"Errors","#ff4b4b")
# # #         ]:
# # #             holder.markdown(f'''<div class="stat-card"><div class="stat-num" style="color:{colour}">{num}</div><div class="stat-lbl">{label}</div></div>''', unsafe_allow_html=True)

# # #     render_stats()
# # #     progress_bar = st.progress(0)
# # #     log_box = st.empty()
# # #     log_lines = []

# # #     def log(msg, kind="info"):
# # #         ts = time.strftime("%H:%M:%S")
# # #         css = {"ok":"log-ok","skip":"log-skip","err":"log-err","info":"log-info"}.get(kind,"log-info")
# # #         log_lines.insert(0, f'<span class="{css}">[{ts}] {msg}</span>')
# # #         log_box.markdown(f'<div class="log-box">{"<br>".join(log_lines)}</div>', unsafe_allow_html=True)

# # #     if st.button("\U0001f680 START UPLOAD"):
# # #         if selected_store is None:
# # #             st.error("Select a store from the sidebar first."); st.stop()
# # #         if not uploaded_csv:
# # #             st.error("Upload a CSV file first."); st.stop()

# # #         domain      = selected_store["domain"].strip()
# # #         client_id   = selected_store["client_id"].strip()
# # #         client_secret = selected_store["client_secret"].strip()

# # #         log(f"\U0001f510 Generating access token for {domain}…")
# # #         log(f"   Client ID: {client_id[:8]}...", "info")

# # #         token, err = get_oauth_token(domain, client_id, client_secret)
# # #         if not token:
# # #             log(f"\u274c OAuth failed: {err}", "err")
# # #             st.error(
# # #                 f"Failed to generate access token.\n\n"
# # #                 f"Error: {err}\n\n"
# # #                 f"Make sure your Client ID and Client Secret are correct.\n"
# # #                 f"Get them from: Shopify Admin → Settings → Apps → Develop apps → your app → API credentials."
# # #             )
# # #             st.stop()
# # #         log(f"\u2705 Token generated! ({token[:12]}...)", "ok")

# # #         log(f"Checking collection '{collection_name}'…")
# # #         coll_id = get_or_create_collection(domain, token, collection_name)
# # #         log(f"\u2705 Collection ready (ID {coll_id})" if coll_id else "\u26a0\ufe0f No collection — uploading without it.",
# # #             "ok" if coll_id else "skip")

# # #         log("\U0001f50e Fetching existing products…")
# # #         existing_products = fetch_all_products(domain, token)
# # #         existing_asins    = build_asin_set(existing_products)
# # #         existing_skus     = build_sku_set(existing_products)
# # #         log(f"\U0001f4cb {len(existing_products)} products | {len(existing_asins)} ASINs | {len(existing_skus)} SKUs in store","info")

# # #         df = parse_csv(uploaded_csv)
# # #         if df is None: st.stop()
# # #         total = len(df)
# # #         uploaded = skipped = errors = 0
# # #         render_stats(total)
# # #         log(f"\U0001f4c4 CSV: {total} rows","info")

# # #         log("\U0001f310 Detecting Chrome version and launching browser…")
# # #         try:
# # #             driver = build_driver()
# # #         except RuntimeError as chrome_err:
# # #             log(f"\u274c Chrome launch failed: {chrome_err}", "err")
# # #             st.error(str(chrome_err))
# # #             st.stop()
# # #         wait = WebDriverWait(driver, 15)
# # #         log("\u2705 Chrome launched successfully!", "ok")
# # #         zip_set = False
# # #         api_url = f"https://{domain}/admin/api/2024-10/products.json"
# # #         headers = sh_headers(token)

# # #         try:
# # #             for idx, row in df.iterrows():
# # #                 progress_bar.progress(min((idx + 1) / total, 1.0))
# # #                 asin_csv = str(row.get("ASIN", "")).strip().upper()
# # #                 title_csv = scrub(str(row.get("Title", f"Product {idx}")))
# # #                 link = str(row.get("Link", "")).strip()

# # #                 if not link or "http" not in link:
# # #                     log(f"Row {idx + 1} — no link, skipped", "skip")
# # #                     skipped += 1;
# # #                     render_stats(total, uploaded, skipped, errors);
# # #                     continue

# # #                 # ── PRE-SCRAPE duplicate check ──────────────────────────────────────
# # #                 if asin_csv and asin_csv in existing_asins:
# # #                     log(f"⏭️ SKIP (ASIN exists) — {asin_csv} | {title_csv[:50]}", "skip")
# # #                     skipped += 1;
# # #                     render_stats(total, uploaded, skipped, errors);
# # #                     continue

# # #                 # ✅ FIX: generate SKU the SAME way as later, using asin_csv
# # #                 sku_pre = (f"{sku_prefix}{asin_csv[2:]}" if len(asin_csv) > 2 else "").upper()
# # #                 if sku_pre and sku_pre in existing_skus:
# # #                     log(f"⏭️ SKIP (SKU exists pre-check) — {sku_pre}", "skip")
# # #                     skipped += 1;
# # #                     render_stats(total, uploaded, skipped, errors);
# # #                     continue

# # #                 log(f"🔍 Scraping row {idx + 1}: {title_csv[:55]}…", "info")

# # #                 if not zip_set:
# # #                     driver.get("https://www.amazon.com")
# # #                     time.sleep(2)
# # #                     try:
# # #                         driver.find_element(By.ID,"nav-global-location-popover-link").click()
# # #                         z = wait.until(EC.presence_of_element_located((By.ID,"GLUXZipUpdateInput")))
# # #                         z.clear(); z.send_keys(zip_code)
# # #                         driver.find_element(By.ID,"GLUXZipUpdate").click()
# # #                         time.sleep(1); driver.refresh(); time.sleep(2)
# # #                     except: pass
# # #                     zip_set = True

# # #                 driver.get(link)
# # #                 time.sleep(3)

# # #                 try:
# # #                     browser_frame.image(driver.get_screenshot_as_png(),
# # #                                         caption=f"Row {idx+1} — {title_csv[:40]}")
# # #                 except: pass

# # #                 # ASIN from page
# # #                 asin = asin_csv  # default to CSV value
# # #                 try:
# # #                     ap = driver.find_element(By.ID, "ASIN").get_attribute("value").strip().upper()
# # #                     if ap: asin = ap
# # #                 except:
# # #                     pass

# # #                 sku = (f"{sku_prefix}{asin[2:]}" if len(asin) > 2 else f"{sku_prefix}{int(time.time())}").upper()

# # #                 if asin in existing_asins:
# # #                     log(f"⏭️ SKIP (page ASIN exists) — {asin}", "skip")
# # #                     skipped += 1;
# # #                     render_stats(total, uploaded, skipped, errors);
# # #                     continue

# # #                 if sku in existing_skus:
# # #                     log(f"⏭️ SKIP (SKU exists post-scrape) — {sku}", "skip")
# # #                     skipped += 1;
# # #                     render_stats(total, uploaded, skipped, errors);
# # #                     continue

# # #                 # IMAGES — main image first, then thumbnails
# # #                 images = []
# # #                 try:
# # #                     ms = driver.find_element(By.ID,"landingImage").get_attribute("src") or ""
# # #                     if ms.startswith("http"):
# # #                         images.append(re.sub(r'\._[A-Z0-9,_]+_\.','.',ms))
# # #                 except: pass
# # #                 try:
# # #                     for img in driver.find_elements(By.CSS_SELECTOR,"#altImages ul li img"):
# # #                         src = img.get_attribute("src") or ""
# # #                         if "/images/I/" in src:
# # #                             hi = re.sub(r'\._[A-Z0-9,_-]+_\.','.',src)
# # #                             if hi not in images: images.append(hi)
# # #                 except: pass
# # #                 images = [i for i in images if i.startswith("http")][:8]

# # #                 # DESCRIPTION
# # #                 desc = ""
# # #                 try:
# # #                     desc = scrub(driver.find_element(By.ID,"feature-bullets").get_attribute("innerHTML"))
# # #                 except: pass
# # #                 if not desc:
# # #                     try:
# # #                         desc = scrub(driver.find_element(By.ID,"productDescription").get_attribute("innerHTML"))
# # #                     except: pass

# # #                 # TITLE from page
# # #                 title = title_csv
# # #                 try:
# # #                     pt = scrub(driver.find_element(By.ID,"productTitle").text)
# # #                     if pt: title = pt
# # #                 except: pass

# # #                 # TAGS from breadcrumbs
# # #                 tags = ""
# # #                 try:
# # #                     bc = driver.find_elements(By.CSS_SELECTOR,
# # #                         "#wayfinding-breadcrumbs_container li a, .a-breadcrumb li a")
# # #                     tp = [e.text.strip() for e in bc if e.text.strip() and "\u2039" not in e.text]
# # #                     tags = ", ".join(tp)
# # #                 except: pass
# # #                 asin_tag = f"ASIN:{asin}"
# # #                 tags = f"{tags}, {asin_tag}" if tags else asin_tag

# # #             #     # PRICING
# # #             #     try: cost = float(re.sub(r"[^\d.]","",str(row.get("Price","0"))))
# # #             #     except: cost = 0.0
# # #             #     try: list_price = float(re.sub(r"[^\d.]","",str(row.get("List Price","0"))))
# # #             #     except: list_price = 0.0

# # #             #    # profit        = profit_for(cost)
# # #             #    # selling_price = round(cost + profit, 2)
# # #             #    # compare_price = round(list_price if list_price > selling_price else selling_price + 8.0, 2)

# # #             #     profit = profit_for(cost)
# # #             #     selling_price = round(cost + profit, 2)

# # #             #     # Compare-at price 20%–40% higher than selling price
# # #             #     compare_price = round(
# # #             #         selling_price * random.uniform(1.20, 1.40),
# # #             #         2
# # #             #     )
# # #  # Amazon Selling Price (Price column)
# # #                 try:
# # #                     amazon_price = float(re.sub(r"[^\d.]", "", str(row.get("Price", "0"))))
# # #                 except:
# # #                     amazon_price = 0.0

# # #                 # Inventory Cost (List Price / Typical Price)
# # #                 try:
# # #                     inventory_cost = float(re.sub(r"[^\d.]", "", str(row.get("List Price", "0"))))
# # #                 except:
# # #                     inventory_cost = 0.0

# # #                 # Agar List Price nahi mili to Amazon price use karo
# # #                 if inventory_cost <= 0:
# # #                     inventory_cost = amazon_price

# # #                 # Profit inventory cost ke hisaab se
# # #                 profit = profit_for(inventory_cost)

# # #                 # Shopify Selling Price
# # #                 selling_price = round(inventory_cost + profit, 2)

# # #                 # Compare Price
# # #                 compare_price = round(
# # #                     selling_price * random.uniform(1.20, 1.40),
# # #                     2
# # #                 )
# # #                 # Console Log (debug)
# # #                 print(f"""
# # #                 Amazon Selling : ${amazon_price}
# # #                 Inventory Cost : ${inventory_cost}
# # #                 Profit         : ${profit}
# # #                 New Price      : ${selling_price}
# # #                 Compare        : ${compare_price}
# # #                 """)
# # #                 payload = {
# # #                     "product": {
# # #                         "title": title,
# # #                         "body_html": f"<div>{desc}</div>" if desc else "",
# # #                         "vendor": vendor_name,
# # #                         "tags": tags,
# # #                         "status": "active",
# # #                         "variants": [{"price":str(selling_price),"compare_at_price":str(compare_price),
# # #                                       "cost":str(inventory_cost),"sku":sku}],
# # #                         **({"images":[{"src":i} for i in images]} if images else {}),
# # #                     }
# # #                 }

# # #                 r = requests.post(api_url, headers=headers, json=payload, verify=False)

# # #                 if r.status_code == 201:
# # #                     pid = r.json()["product"]["id"]
# # #                     existing_asins.add(asin); existing_skus.add(sku.upper())
# # #                     if coll_id: add_to_collection(domain,token,pid,coll_id)
# # #                     uploaded+=1
# # #                     log(f"\u2705 {sku} | \u00a3{selling_price} | {len(images)} imgs | {title[:45]}","ok")
# # #                 elif r.status_code == 429:
# # #                     log("\u23f3 Rate limited — waiting 4s…","info"); time.sleep(4)
# # #                     r2 = requests.post(api_url,headers=headers,json=payload,verify=False)
# # #                     if r2.status_code == 201:
# # #                         pid=r2.json()["product"]["id"]
# # #                         existing_asins.add(asin); existing_skus.add(sku.upper())
# # #                         if coll_id: add_to_collection(domain,token,pid,coll_id)
# # #                         uploaded+=1; log(f"\u2705 {sku} (retry OK)","ok")
# # #                     else:
# # #                         errors+=1; log(f"\u274c {sku}: {r2.text[:100]}","err")
# # #                 else:
# # #                     errors+=1; log(f"\u274c {sku}: {r.text[:100]}","err")

# # #                 render_stats(total,uploaded,skipped,errors)
# # #                 time.sleep(0.5)

# # #         except Exception as e:
# # #             log(f"\U0001f4a5 Fatal: {e}","err")
# # #         finally:
# # #             driver.quit()
# # #             log("\U0001f310 Browser closed.","info")

# # #         progress_bar.progress(1.0)
# # #         log("\u2500"*55,"info")
# # #         log(f"\U0001f3c1 Done! Uploaded:{uploaded} | Skipped:{skipped} | Errors:{errors}","ok")
# # #         if uploaded: st.balloons()

# # # # TAB 2 — AUDIT
# # # with tab_audit:
# # #     st.subheader("\U0001f50d Scan for Duplicate SKUs / ASINs")
# # #     if selected_store is None:
# # #         st.warning("Select a store in the sidebar first.")
# # #     else:
# # #         a_col, b_col = st.columns(2)
# # #         with a_col:
# # #             if st.button("\U0001f680 Run Duplicate SKU Audit"):
# # #                 with st.spinner("Generating access token…"):
# # #                     audit_token, aerr = get_oauth_token(
# # #                         selected_store["domain"],
# # #                         selected_store["client_id"],
# # #                         selected_store["client_secret"])
# # #                 if not audit_token:
# # #                     st.error(f"Auth failed: {aerr}")
# # #                 else:
# # #                     with st.spinner("Fetching products…"):
# # #                         prods = fetch_all_products(selected_store["domain"], audit_token)
# # #                     sku_map={}
# # #                     for p in prods:
# # #                         for v in p.get("variants",[]):
# # #                             s=(v.get("sku") or "").strip()
# # #                             if s: sku_map.setdefault(s,[]).append({"Product Title":p.get("title"),"Variant ID":v.get("id"),"Price":v.get("price")})
# # #                     dupes={s:items for s,items in sku_map.items() if len(items)>1}
# # #                     st.session_state["dupes"]=dupes; st.session_state["total_prods"]=len(prods)
# # #         with b_col:
# # #             if st.button("\U0001f4ca Count ASINs & SKUs"):
# # #                 with st.spinner("Generating access token…"):
# # #                     audit_tok2, aerr2 = get_oauth_token(
# # #                         selected_store["domain"],
# # #                         selected_store["client_id"],
# # #                         selected_store["client_secret"])
# # #                 if not audit_tok2:
# # #                     st.error(f"Auth failed: {aerr2}")
# # #                 else:
# # #                     with st.spinner("Loading…"):
# # #                         prods=fetch_all_products(selected_store["domain"], audit_tok2)
# # #                         asins=build_asin_set(prods); skus=build_sku_set(prods)
# # #                     st.info(f"**{len(prods)}** products | **{len(asins)}** ASINs | **{len(skus)}** SKUs")
# # #         if "dupes" in st.session_state:
# # #             dupes=st.session_state["dupes"]; total_p=st.session_state.get("total_prods","?")
# # #             st.caption(f"Scanned **{total_p}** products")
# # #             if not dupes:
# # #                 st.balloons(); st.success("\u2705 No duplicate SKUs — store is clean!")
# # #             else:
# # #                 st.warning(f"\u26a0\ufe0f {len(dupes)} duplicate SKU(s)")
# # #                 rows=[]
# # #                 for s,items in dupes.items():
# # #                     for item in items: rows.append({"SKU":s,**item})
# # #                 df_d=pd.DataFrame(rows)
# # #                 st.dataframe(df_d)
# # #                 st.download_button("\U0001f4e5 Download CSV",df_d.to_csv(index=False).encode(),"duplicates.csv","text/csv")

# # # # TAB 3 — MANAGE STORES
# # # with tab_stores_tab:
# # #     st.subheader("\u2795 Add / Update a Store")
# # #     st.info(
# # #         "**How to get your credentials:**\n\n"
# # #         "1. Shopify Admin → Settings → Apps and sales channels → Develop apps\n"
# # #         "2. Create app → Configure Admin API scopes → enable **write_products, read_products, write_inventory**\n"
# # #         "3. Install the app\n"
# # #         "4. Go to **API credentials** tab\n"
# # #         "5. Copy **Client ID** and **Client Secret** — paste both below\n\n"
# # #         "The app will generate a fresh access token automatically each time you run it."
# # #     )
# # #     with st.form("store_form"):
# # #         fc1,fc2=st.columns(2)
# # #         f_name=fc1.text_input("Store Nickname")
# # #         # RESTORED DOMAIN FIELD
# # #         f_domain = fc2.text_input(
# # #             "Domain (e.g. mystore.myshopify.com)"
# # #         )
# # #         fc3,fc4=st.columns(2)
# # #         f_cid=fc3.text_input("Client ID", help="From Shopify: Settings → Apps → Develop apps → your app → API credentials")
# # #         f_token=fc4.text_input("Client Secret", type="password", help="From the same page as Client ID")
# # #         if st.form_submit_button("\U0001f4be Save Store"):
# # #             if f_name and f_domain and f_cid and f_token:
# # #                 save_store(f_name,
# # #                            f_domain.replace("https://","").replace("http://","").rstrip("/"),
# # #                            f_cid, f_token)
# # #                 st.success(f"\u2705 Store **{f_name}** saved!")
# # #                 st.rerun()
# # #             else:
# # #                 st.error("Nickname, Domain, Client ID, and Client Secret are all required.")
# # #     st.divider()
# # #     st.subheader("Saved Stores")
# # #     stores_df=all_stores()
# # #     if stores_df.empty:
# # #         st.info("No stores saved yet.")
# # #     else:
# # #         for _,row in stores_df.iterrows():
# # #             with st.expander(f"\U0001f3ea {row['store_name']} — {row['domain']}"):
# # #                 st.code(f"Domain : {row['domain']}", language=None)
# # #                 if row["client_id"]: st.code(f"Client ID: {row['client_id']}", language=None)
# # #                 st.caption("Access token hidden for security.")
# # #                 if st.button(f"\U0001f5d1\ufe0f Delete {row['store_name']}", key=f"del_{row['id']}"):
# # #                     delete_store(int(row["id"])); st.rerun()

# # """
# # SC Shopify Master Uploader
# # ==========================
# # - CSV provides the product list (ASIN, Title, Price, List Price, Link)
# # - Selenium scrapes each Amazon link for: images, description, tags
# # - Access token stored per store in SQLite — just select store name to run
# # - Real-time duplicate check by ASIN tag + SKU before scraping/uploading
# # """
# # """
# # SC Shopify Master Uploader
# # ==========================
# # - CSV provides the product list (ASIN, Title, Price, List Price, Link)
# # - Selenium scrapes each Amazon link for: images, description, tags
# # - Access token stored per store in SQLite — just select store name to run
# # - Real-time duplicate check by ASIN tag + SKU before scraping/uploading
# # """

# # import streamlit as st
# # import pandas as pd
# # import requests
# # import sqlite3
# # import time
# # import re
# # import io
# # import os
# # import shutil
# # import tempfile
# # import urllib3
# # from pathlib import Path
# # import random
# # import undetected_chromedriver as uc
# # from selenium.webdriver.common.by import By
# # from selenium.webdriver.support.ui import WebDriverWait
# # from selenium.webdriver.support import expected_conditions as EC

# # urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # # PAGE CONFIG
# # st.set_page_config(page_title="SC Shopify Uploader", layout="wide", page_icon="\U0001f6cd\ufe0f")

# # st.markdown("""
# # <style>
# # @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
# # html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
# # .log-box {
# #     background: #0a0c10; color: #39ff14; padding: 16px; border-radius: 10px;
# #     font-family: 'JetBrains Mono', monospace; font-size: 12px;
# #     height: 420px; overflow-y: auto; border: 1px solid #1e2430; line-height: 1.8;
# # }
# # .log-skip { color: #f0a500; } .log-ok { color: #39ff14; }
# # .log-err  { color: #ff4b4b; } .log-info { color: #5bc8ff; }
# # .stat-card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; text-align: center; }
# # .stat-num  { font-size: 2.4rem; font-weight: 800; line-height: 1; }
# # .stat-lbl  { font-size: 0.75rem; color: #6b7280; margin-top: 4px; letter-spacing: 0.08em; text-transform: uppercase; }
# # .stButton>button {
# #     background: linear-gradient(135deg, #ff6a00, #ff9900); color: #fff; border: none;
# #     border-radius: 10px; font-weight: 700; font-size: 1rem; height: 3.2em; width: 100%;
# #     letter-spacing: 0.04em; transition: opacity 0.2s;
# # }
# # .stButton>button:hover { opacity: 0.88; }
# # .stProgress > div > div { background: #ff9900 !important; }
# # </style>
# # """, unsafe_allow_html=True)

# # # DATABASE
# # DB = "shopify_stores.db"

# # def init_db():
# #     with sqlite3.connect(DB) as conn:
# #         conn.execute("""
# #             CREATE TABLE IF NOT EXISTS stores (
# #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
# #                 store_name TEXT, domain TEXT, client_id TEXT, client_secret TEXT
# #             )""")
# #         conn.commit()
# #         table_sql = (conn.execute(
# #             "SELECT sql FROM sqlite_master WHERE type='table' AND name='stores'"
# #         ).fetchone() or ("",))[0]
# #         indexes = conn.execute(
# #             "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='stores'"
# #         ).fetchall()
# #         has_unique_index = any(
# #             r[0] and "store_name" in r[0].upper() and "UNIQUE" in r[0].upper()
# #             for r in indexes
# #         )
# #         if "UNIQUE" not in table_sql.upper() and not has_unique_index:
# #             conn.execute("ALTER TABLE stores RENAME TO stores_old")
# #             conn.execute("""
# #                 CREATE TABLE stores (
# #                     id INTEGER PRIMARY KEY AUTOINCREMENT,
# #                     store_name TEXT UNIQUE, domain TEXT, client_id TEXT, client_secret TEXT
# #                 )""")
# #             conn.execute("""
# #                 INSERT OR IGNORE INTO stores (id,store_name,domain,client_id,client_secret)
# #                 SELECT id,store_name,domain,client_id,client_secret FROM stores_old
# #             """)
# #             conn.execute("DROP TABLE stores_old")
# #             conn.commit()

# # def save_store(name, domain, client_id, secret):
# #     with sqlite3.connect(DB) as conn:
# #         conn.execute("""
# #             INSERT INTO stores (store_name,domain,client_id,client_secret) VALUES (?,?,?,?)
# #             ON CONFLICT(store_name) DO UPDATE SET
# #                 domain=excluded.domain, client_id=excluded.client_id, client_secret=excluded.client_secret
# #         """, (name, domain, client_id, secret))
# #         conn.commit()

# # def all_stores():
# #     with sqlite3.connect(DB) as conn:
# #         return pd.read_sql_query("SELECT * FROM stores", conn)

# # def delete_store(sid):
# #     with sqlite3.connect(DB) as conn:
# #         conn.execute("DELETE FROM stores WHERE id=?", (sid,))
# #         conn.commit()

# # init_db()

# # # SHOPIFY HELPERS
# # def sh_headers(token):
# #     return {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

# # def get_oauth_token(domain, client_id, client_secret):
# #     """
# #     Generate a fresh access token using Client ID + Client Secret.
# #     This is the correct flow for Shopify custom apps using client credentials.
# #     Returns (token_string, error_message)
# #     """
# #     url = f"https://{domain}/admin/oauth/access_token"
# #     payload = {
# #         "client_id": client_id,
# #         "client_secret": client_secret,
# #         "grant_type": "client_credentials"
# #     }
# #     try:
# #         r = requests.post(url, json=payload, timeout=15, verify=False)
# #         if r.status_code == 200:
# #             token = r.json().get("access_token", "")
# #             if token:
# #                 return token, ""
# #             return "", "Response OK but no access_token in response"
# #         return "", f"HTTP {r.status_code}: {r.text[:200]}"
# #     except Exception as e:
# #         return "", str(e)

# # def verify_token(domain, token):
# #     """Verify a token works by calling shop.json. Returns (bool, status, reason)."""
# #     try:
# #         r = requests.get(
# #             f"https://{domain}/admin/api/2024-10/shop.json",
# #             headers=sh_headers(token), timeout=15, verify=False)
# #         if r.status_code == 200:
# #             return True, 200, ""
# #         return False, r.status_code, r.text[:200]
# #     except Exception as e:
# #         return False, 0, str(e)

# # def get_or_create_collection(domain, token, name):
# #     h = sh_headers(token)
# #     r = requests.get(f"https://{domain}/admin/api/2024-10/custom_collections.json?limit=250",
# #                      headers=h, verify=False)
# #     if r.status_code == 200:
# #         for c in r.json().get("custom_collections", []):
# #             if c["title"].strip().lower() == name.strip().lower():
# #                 return c["id"]
# #     r2 = requests.post(f"https://{domain}/admin/api/2024-10/custom_collections.json",
# #                        headers=h, json={"custom_collection": {"title": name}}, verify=False)
# #     return r2.json()["custom_collection"]["id"] if r2.status_code == 201 else None

# # def add_to_collection(domain, token, product_id, collection_id):
# #     requests.post(f"https://{domain}/admin/api/2024-10/collects.json",
# #                   headers=sh_headers(token),
# #                   json={"collect": {"product_id": product_id, "collection_id": collection_id}},
# #                   verify=False)

# # def fetch_all_products(domain, token):
# #     products, url = [], f"https://{domain}/admin/api/2024-10/products.json?limit=250"
# #     while url:
# #         r = requests.get(url, headers=sh_headers(token), verify=False)
# #         if r.status_code == 200:
# #             products.extend(r.json().get("products", []))
# #             lh = r.headers.get("Link", "")
# #             url = None
# #             if 'rel="next"' in lh:
# #                 for part in lh.split(","):
# #                     if 'rel="next"' in part:
# #                         url = part.split(";")[0].strip("<> ")
# #         elif r.status_code == 429:
# #             time.sleep(2)
# #         else:
# #             break
# #     return products
# # # def delete_product(domain, token, product_id):
# # #     r = requests.delete(
# # #         f"https://{domain}/admin/api/2024-10/products/{product_id}.json",
# # #         headers=sh_headers(token),
# # #         verify=False
# # #     )
# # #     return r.status_code == 200
# # def delete_product(domain, token, product_id):
# #     try:
# #         r = requests.delete(
# #             f"https://{domain}/admin/api/2024-10/products/{product_id}.json",
# #             headers=sh_headers(token),
# #             timeout=20,
# #             verify=False
# #         )

# #         return r.status_code in (200, 204)

# #     except Exception:
# #         return False
# # def build_asin_set(products):
# #     asins = set()
# #     for p in products:
# #         for tag in (p.get("tags") or "").split(","):
# #             t = tag.strip()
# #             if t.upper().startswith("ASIN:"):
# #                 asins.add(t[5:].strip().upper())
# #     return asins

# # def build_sku_set(products):
# #     skus = set()
# #     for p in products:
# #         for v in p.get("variants", []):
# #             s = (v.get("sku") or "").strip().upper()
# #             if s:
# #                 skus.add(s)
# #     return skus

# # # PRICING MATRIX
# # def profit_for(cost):
# #     table = [(15,10),(50,16),(100,22),(150,27),(200,33),(250,37),
# #              (300,45),(350,55),(400,60),(450,65),(500,70),(550,75),(600,78),(650,80)]
# #     for t, p in table:
# #         if cost <= t:
# #             return p
# #     return 100

# # # CSV PARSING
# # REQUIRED_COLS = {"ASIN", "Title", "Price", "Link"}

# # def parse_csv(uploaded_file):
# #     try:
# #         raw = uploaded_file.read()
# #         for sep in ("\t", ",", ";"):
# #             try:
# #                 df = pd.read_csv(io.BytesIO(raw), sep=sep, dtype=str)
# #                 df.columns = [c.strip() for c in df.columns]
# #                 if REQUIRED_COLS.issubset(set(df.columns)):
# #                     return df
# #             except:
# #                 continue
# #         st.error("CSV needs: ASIN, Title, Price, Link columns.")
# #         return None
# #     except Exception as e:
# #         st.error(f"Read error: {e}")
# #         return None

# # def scrub(text):
# #     if not text: return ""
# #     text = re.sub(r'amazon|walmart|prime|shipped from|sold by', '', str(text), flags=re.IGNORECASE)
# #     text = re.sub(r'\u203a?\s*See more product details|\u203a?\s*See details', '', text, flags=re.IGNORECASE)
# #     return text.strip()

# # import subprocess
# # import json

# # # SELENIUM
# # def clean_uc_cache():
# #     p = os.path.join(os.environ.get("APPDATA", ""), "undetected_chromedriver")
# #     if os.path.exists(p):
# #         shutil.rmtree(p, ignore_errors=True)

# # def get_chrome_version():
# #     """Auto-detect installed Chrome major version."""
# #     paths = [
# #         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
# #         r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
# #         r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get("USERNAME","")),
# #     ]
# #     for path in paths:
# #         if os.path.exists(path):
# #             try:
# #                 result = subprocess.run(
# #                     [path, "--version"], capture_output=True, text=True, timeout=5)
# #                 ver = result.stdout.strip()
# #                 match = re.search(r"(\d+)\.\d+\.\d+\.\d+", ver)
# #                 if match:
# #                     return int(match.group(1))
# #             except:
# #                 pass
# #     # Fallback: try registry
# #     try:
# #         import winreg
# #         key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
# #             r"Software\Google\Chrome\BLBeacon")
# #         ver, _ = winreg.QueryValueEx(key, "version")
# #         winreg.CloseKey(key)
# #         return int(ver.split(".")[0])
# #     except:
# #         pass
# #     return None  # will let uc auto-detect

# # def build_driver():
# #     clean_uc_cache()
# #     opts = uc.ChromeOptions()
# #     opts.add_argument("--no-sandbox")
# #     opts.add_argument("--disable-dev-shm-usage")
# #     opts.add_argument("--start-maximized")
# #     opts.add_argument("--disable-blink-features=AutomationControlled")
# #     opts.add_argument(f"--user-data-dir={Path(tempfile.mkdtemp(prefix='uc_'))}")

# #     chrome_ver = get_chrome_version()

# #     kwargs = {"options": opts, "use_subprocess": True}
# #     if chrome_ver:
# #         kwargs["version_main"] = chrome_ver

# #     try:
# #         driver = uc.Chrome(**kwargs)
# #         return driver
# #     except Exception as e1:
# #         # Clear stale driver files and retry without version pin
# #         root = Path(os.environ.get("APPDATA","")) / "undetected_chromedriver"
# #         for p in [root/"undetected_chromedriver.exe", root/"undetected"]:
# #             try:
# #                 if p.is_file(): p.unlink()
# #                 elif p.is_dir(): shutil.rmtree(p, ignore_errors=True)
# #             except: pass
# #         time.sleep(2)
# #         try:
# #             driver = uc.Chrome(options=opts, use_subprocess=True)
# #             return driver
# #         except Exception as e2:
# #             raise RuntimeError(
# #                 f"Chrome failed to start.\n"
# #                 f"Detected version: {chrome_ver}\n"
# #                 f"Error: {e2}\n\n"
# #                 f"Fix: Make sure Google Chrome is installed and up to date."
# #             )

# # # SIDEBAR
# # with st.sidebar:
# #     st.markdown("## \U0001f6cd\ufe0f SC Uploader")
# #     st.divider()
# #     stores_df   = all_stores()
# #     store_names = stores_df["store_name"].tolist() if not stores_df.empty else []
# #     if store_names:
# #         selected_store_name = st.selectbox("Select Store", store_names)
# #         selected_store = stores_df[stores_df["store_name"] == selected_store_name].iloc[0]
# #         cid_preview = selected_store["client_id"] or ""
# #         if cid_preview:
# #             st.caption(f"Client ID: {cid_preview[:8]}...")
# #             st.caption(f"Domain: {selected_store['domain']}")
# #         else:
# #             st.warning("No Client ID saved — update in Manage Stores.")
# #     else:
# #         st.warning("No stores yet — add one in Manage Stores tab.")
# #         selected_store = None; selected_store_name = None
# #     st.divider()
# #     st.subheader("\U0001f4e6 Product Settings")
# #     vendor_name     = st.text_input("Vendor / Brand Name", value="SC Store")
# #     collection_name = st.text_input("Collection Name",     value="New Arrivals")
# #     sku_prefix      = st.text_input("SKU Prefix",          value="CS").strip().upper()
# #     zip_code        = st.text_input("Amazon Zip Code",     value="10001").strip()
# #     st.divider()
# #     uploaded_csv = st.file_uploader("\U0001f4c4 Upload Product CSV", type=["csv","tsv","txt"])
# #     st.caption("Needs: ASIN, Title, Price, Link columns")

# # # MAIN TABS
# # st.title("\U0001f6cd\ufe0f SC Shopify Master Uploader")

# # tab_upload, tab_audit, tab_stores_tab = st.tabs([
# #     "\U0001f680 Upload Products", "\U0001f50d SKU / ASIN Audit", "\u2699\ufe0f Manage Stores"
# # ])

# # # TAB 1 — UPLOAD
# # with tab_upload:
# #     col_browser, col_right = st.columns([1,1])
# #     with col_browser:
# #         st.subheader("\U0001f4fa Browser Monitor")
# #         browser_frame = st.empty()
# #         browser_frame.info("Awaiting start…")
# #     with col_right:
# #         st.subheader("\U0001f4ca Progress")
# #         c1,c2,c3,c4 = st.columns(4)
# #         stat_total=c1.empty(); stat_uploaded=c2.empty()
# #         stat_skipped=c3.empty(); stat_errors=c4.empty()

# #     def render_stats(total=0,uploaded=0,skipped=0,errors=0):
# #         for holder,num,label,colour in [
# #             (stat_total,total,"Total","#5bc8ff"),(stat_uploaded,uploaded,"Uploaded","#39ff14"),
# #             (stat_skipped,skipped,"Skipped","#f0a500"),(stat_errors,errors,"Errors","#ff4b4b")
# #         ]:
# #             holder.markdown(f'''<div class="stat-card"><div class="stat-num" style="color:{colour}">{num}</div><div class="stat-lbl">{label}</div></div>''', unsafe_allow_html=True)

# #     render_stats()
# #     progress_bar = st.progress(0)
# #     log_box = st.empty()
# #     log_lines = []

# #     def log(msg, kind="info"):
# #         ts = time.strftime("%H:%M:%S")
# #         css = {"ok":"log-ok","skip":"log-skip","err":"log-err","info":"log-info"}.get(kind,"log-info")
# #         log_lines.insert(0, f'<span class="{css}">[{ts}] {msg}</span>')
# #         log_box.markdown(f'<div class="log-box">{"<br>".join(log_lines)}</div>', unsafe_allow_html=True)

# #     if st.button("\U0001f680 START UPLOAD"):
# #         if selected_store is None:
# #             st.error("Select a store from the sidebar first."); st.stop()
# #         if not uploaded_csv:
# #             st.error("Upload a CSV file first."); st.stop()

# #         domain      = selected_store["domain"].strip()
# #         client_id   = selected_store["client_id"].strip()
# #         client_secret = selected_store["client_secret"].strip()

# #         log(f"\U0001f510 Generating access token for {domain}…")
# #         log(f"   Client ID: {client_id[:8]}...", "info")

# #         token, err = get_oauth_token(domain, client_id, client_secret)
# #         if not token:
# #             log(f"\u274c OAuth failed: {err}", "err")
# #             st.error(
# #                 f"Failed to generate access token.\n\n"
# #                 f"Error: {err}\n\n"
# #                 f"Make sure your Client ID and Client Secret are correct.\n"
# #                 f"Get them from: Shopify Admin → Settings → Apps → Develop apps → your app → API credentials."
# #             )
# #             st.stop()
# #         log(f"\u2705 Token generated! ({token[:12]}...)", "ok")

# #         log(f"Checking collection '{collection_name}'…")
# #         coll_id = get_or_create_collection(domain, token, collection_name)
# #         log(f"\u2705 Collection ready (ID {coll_id})" if coll_id else "\u26a0\ufe0f No collection — uploading without it.",
# #             "ok" if coll_id else "skip")

# #         log("\U0001f50e Fetching existing products…")
# #         existing_products = fetch_all_products(domain, token)
# #         existing_asins    = build_asin_set(existing_products)
# #         existing_skus     = build_sku_set(existing_products)
# #         log(f"\U0001f4cb {len(existing_products)} products | {len(existing_asins)} ASINs | {len(existing_skus)} SKUs in store","info")

# #         df = parse_csv(uploaded_csv)
# #         if df is None: st.stop()
# #         total = len(df)
# #         uploaded = skipped = errors = 0
# #         render_stats(total)
# #         log(f"\U0001f4c4 CSV: {total} rows","info")

# #         log("\U0001f310 Detecting Chrome version and launching browser…")
# #         try:
# #             driver = build_driver()
# #         except RuntimeError as chrome_err:
# #             log(f"\u274c Chrome launch failed: {chrome_err}", "err")
# #             st.error(str(chrome_err))
# #             st.stop()
# #         wait = WebDriverWait(driver, 15)
# #         log("\u2705 Chrome launched successfully!", "ok")
# #         zip_set = False
# #         api_url = f"https://{domain}/admin/api/2024-10/products.json"
# #         headers = sh_headers(token)

# #         try:
# #             for idx, row in df.iterrows():
# #                 progress_bar.progress(min((idx + 1) / total, 1.0))
# #                 asin_csv = str(row.get("ASIN", "")).strip().upper()
# #                 title_csv = scrub(str(row.get("Title", f"Product {idx}")))
# #                 link = str(row.get("Link", "")).strip()

# #                 if not link or "http" not in link:
# #                     log(f"Row {idx + 1} — no link, skipped", "skip")
# #                     skipped += 1;
# #                     render_stats(total, uploaded, skipped, errors);
# #                     continue

# #                 # ── PRE-SCRAPE duplicate check ──────────────────────────────────────
# #                 if asin_csv and asin_csv in existing_asins:
# #                     log(f"⏭️ SKIP (ASIN exists) — {asin_csv} | {title_csv[:50]}", "skip")
# #                     skipped += 1;
# #                     render_stats(total, uploaded, skipped, errors);
# #                     continue

# #                 # ✅ FIX: generate SKU the SAME way as later, using asin_csv
# #                 sku_pre = (f"{sku_prefix}{asin_csv[2:]}" if len(asin_csv) > 2 else "").upper()
# #                 if sku_pre and sku_pre in existing_skus:
# #                     log(f"⏭️ SKIP (SKU exists pre-check) — {sku_pre}", "skip")
# #                     skipped += 1;
# #                     render_stats(total, uploaded, skipped, errors);
# #                     continue

# #                 log(f"🔍 Scraping row {idx + 1}: {title_csv[:55]}…", "info")

# #                 if not zip_set:
# #                     driver.get("https://www.amazon.com")
# #                     time.sleep(2)
# #                     try:
# #                         driver.find_element(By.ID,"nav-global-location-popover-link").click()
# #                         z = wait.until(EC.presence_of_element_located((By.ID,"GLUXZipUpdateInput")))
# #                         z.clear(); z.send_keys(zip_code)
# #                         driver.find_element(By.ID,"GLUXZipUpdate").click()
# #                         time.sleep(1); driver.refresh(); time.sleep(2)
# #                     except: pass
# #                     zip_set = True

# #                 driver.get(link)
# #                 time.sleep(3)

# #                 try:
# #                     browser_frame.image(driver.get_screenshot_as_png(),
# #                                         caption=f"Row {idx+1} — {title_csv[:40]}")
# #                 except: pass

# #                 # ASIN from page
# #                 asin = asin_csv  # default to CSV value
# #                 try:
# #                     ap = driver.find_element(By.ID, "ASIN").get_attribute("value").strip().upper()
# #                     if ap: asin = ap
# #                 except:
# #                     pass

# #                 sku = (f"{sku_prefix}{asin[2:]}" if len(asin) > 2 else f"{sku_prefix}{int(time.time())}").upper()

# #                 if asin in existing_asins:
# #                     log(f"⏭️ SKIP (page ASIN exists) — {asin}", "skip")
# #                     skipped += 1;
# #                     render_stats(total, uploaded, skipped, errors);
# #                     continue

# #                 if sku in existing_skus:
# #                     log(f"⏭️ SKIP (SKU exists post-scrape) — {sku}", "skip")
# #                     skipped += 1;
# #                     render_stats(total, uploaded, skipped, errors);
# #                     continue

# #                 # IMAGES — main image first, then thumbnails
# #                 images = []
# #                 try:
# #                     ms = driver.find_element(By.ID,"landingImage").get_attribute("src") or ""
# #                     if ms.startswith("http"):
# #                         images.append(re.sub(r'\._[A-Z0-9,_]+_\.','.',ms))
# #                 except: pass
# #                 try:
# #                     for img in driver.find_elements(By.CSS_SELECTOR,"#altImages ul li img"):
# #                         src = img.get_attribute("src") or ""
# #                         if "/images/I/" in src:
# #                             hi = re.sub(r'\._[A-Z0-9,_-]+_\.','.',src)
# #                             if hi not in images: images.append(hi)
# #                 except: pass
# #                 images = [i for i in images if i.startswith("http")][:8]

# #                 # DESCRIPTION
# #                 desc = ""
# #                 try:
# #                     desc = scrub(driver.find_element(By.ID,"feature-bullets").get_attribute("innerHTML"))
# #                 except: pass
# #                 if not desc:
# #                     try:
# #                         desc = scrub(driver.find_element(By.ID,"productDescription").get_attribute("innerHTML"))
# #                     except: pass

# #                 # TITLE from page
# #                 title = title_csv
# #                 try:
# #                     pt = scrub(driver.find_element(By.ID,"productTitle").text)
# #                     if pt: title = pt
# #                 except: pass

# #                 # TAGS from breadcrumbs
# #                 tags = ""
# #                 try:
# #                     bc = driver.find_elements(By.CSS_SELECTOR,
# #                         "#wayfinding-breadcrumbs_container li a, .a-breadcrumb li a")
# #                     tp = [e.text.strip() for e in bc if e.text.strip() and "\u2039" not in e.text]
# #                     tags = ", ".join(tp)
# #                 except: pass
# #                 asin_tag = f"ASIN:{asin}"
# #                 tags = f"{tags}, {asin_tag}" if tags else asin_tag

# #                #  # PRICING
# #                #  try: cost = float(re.sub(r"[^\d.]","",str(row.get("Price","0"))))
# #                #  except: cost = 0.0
# #                #  try: list_price = float(re.sub(r"[^\d.]","",str(row.get("List Price","0"))))
# #                #  except: list_price = 0.0
# #                #
# #                # # profit        = profit_for(cost)
# #                # # selling_price = round(cost + profit, 2)
# #                # # compare_price = round(list_price if list_price > selling_price else selling_price + 8.0, 2)
# #                #
# #                #  profit = profit_for(cost)
# #                #  selling_price = round(cost + profit, 2)
# #                #
# #                #  # Compare-at price 20%–40% higher than selling price
# #                #  compare_price = round(
# #                #      selling_price * random.uniform(1.20, 1.40),
# #                #      2
# #                #  )
# #                 # Amazon Selling Price (Price column)
# #                 try:
# #                     amazon_price = float(re.sub(r"[^\d.]", "", str(row.get("Price", "0"))))
# #                 except:
# #                     amazon_price = 0.0

# #                 # Inventory Cost (List Price / Typical Price)
# #                 try:
# #                     inventory_cost = float(re.sub(r"[^\d.]", "", str(row.get("List Price", "0"))))
# #                 except:
# #                     inventory_cost = 0.0

# #                 # Agar List Price nahi mili to Amazon price use karo
# #                 if inventory_cost <= 0:
# #                     inventory_cost = amazon_price

# #                 # Profit inventory cost ke hisaab se
# #                 profit = profit_for(inventory_cost)

# #                 # Shopify Selling Price
# #                 selling_price = round(inventory_cost + profit, 2)

# #                 # Compare Price
# #                 compare_price = round(
# #                     selling_price * random.uniform(1.20, 1.40),
# #                     2
# #                 )
# #                 # Console Log (debug)
# #                 print(f"""
# #                 Amazon Selling : ${amazon_price}
# #                 Inventory Cost : ${inventory_cost}
# #                 Profit         : ${profit}
# #                 New Price      : ${selling_price}
# #                 Compare        : ${compare_price}
# #                 """)
# #                 payload = {
# #                     "product": {
# #                         "title": title,
# #                         "body_html": f"<div>{desc}</div>" if desc else "",
# #                         "vendor": vendor_name,
# #                         "tags": tags,
# #                         "status": "active",
# #                         "variants": [{"price":str(selling_price),"compare_at_price":str(compare_price),
# #                                       "cost":str(inventory_cost),"sku":sku}],
# #                         **({"images":[{"src":i} for i in images]} if images else {}),
# #                     }
# #                 }

# #                 r = requests.post(api_url, headers=headers, json=payload, verify=False)

# #                 if r.status_code == 201:
# #                     pid = r.json()["product"]["id"]
# #                     existing_asins.add(asin); existing_skus.add(sku.upper())
# #                     if coll_id: add_to_collection(domain,token,pid,coll_id)
# #                     uploaded+=1
# #                     log(f"\u2705 {sku} | \u00a3{selling_price} | {len(images)} imgs | {title[:45]}","ok")
# #                 elif r.status_code == 429:
# #                     log("\u23f3 Rate limited — waiting 4s…","info"); time.sleep(4)
# #                     r2 = requests.post(api_url,headers=headers,json=payload,verify=False)
# #                     if r2.status_code == 201:
# #                         pid=r2.json()["product"]["id"]
# #                         existing_asins.add(asin); existing_skus.add(sku.upper())
# #                         if coll_id: add_to_collection(domain,token,pid,coll_id)
# #                         uploaded+=1; log(f"\u2705 {sku} (retry OK)","ok")
# #                     else:
# #                         errors+=1; log(f"\u274c {sku}: {r2.text[:100]}","err")
# #                 else:
# #                     errors+=1; log(f"\u274c {sku}: {r.text[:100]}","err")

# #                 render_stats(total,uploaded,skipped,errors)
# #                 time.sleep(0.5)

# #         except Exception as e:
# #             log(f"\U0001f4a5 Fatal: {e}","err")
# #         finally:
# #             driver.quit()
# #             log("\U0001f310 Browser closed.","info")

# #         progress_bar.progress(1.0)
# #         log("\u2500"*55,"info")
# #         log(f"\U0001f3c1 Done! Uploaded:{uploaded} | Skipped:{skipped} | Errors:{errors}","ok")
# #         if uploaded: st.balloons()

# # # TAB 2 — AUDIT
# # with tab_audit:
# #     st.subheader("\U0001f50d Scan for Duplicate SKUs / ASINs")
# #     if selected_store is None:
# #         st.warning("Select a store in the sidebar first.")
# #     else:
# #         a_col, b_col = st.columns(2)
# #         with a_col:
# #             if st.button("\U0001f680 Run Duplicate SKU Audit"):
# #                 with st.spinner("Generating access token…"):
# #                     audit_token, aerr = get_oauth_token(
# #                         selected_store["domain"],
# #                         selected_store["client_id"],
# #                         selected_store["client_secret"])
# #                 if not audit_token:
# #                     st.error(f"Auth failed: {aerr}")
# #                 else:
# #                     with st.spinner("Fetching products…"):
# #                         prods = fetch_all_products(selected_store["domain"], audit_token)
# #                     # sku_map={}
# #                     # for p in prods:
# #                     #     for v in p.get("variants",[]):
# #                     #         s=(v.get("sku") or "").strip()
# #                     #         if s: sku_map.setdefault(s,[]).append({"Product Title":p.get("title"),"Variant ID":v.get("id"),"Price":v.get("price")})
# #                     # sku_map = {}
# #                     #
# #                     # for p in prods:
# #                     #     for v in p.get("variants", []):
# #                     #         s = (v.get("sku") or "").strip()
# #                     #         if s:
# #                     #             sku_map.setdefault(s, []).append({
# #                     #                 "Product ID": p.get("id"),
# #                     #                 "Product Title": p.get("title"),
# #                     #                 "Variant ID": v.get("id"),
# #                     #                 "Price": v.get("price"),
# #                     #                 "Created At": p.get("created_at")
# #                     #             })
# #                     # dupes={s:items for s,items in sku_map.items() if len(items)>1}
# #                     sku_map = {}
# #                     asin_map = {}

# #                     for p in prods:

# #                         created = p.get("created_at")
# #                         product_id = p.get("id")
# #                         title = p.get("title")
# #                         tags = p.get("tags", "")

# #                         # ---------- SKU ----------
# #                         for v in p.get("variants", []):

# #                             sku = (v.get("sku") or "").strip()

# #                             if sku:
# #                                 sku_map.setdefault(sku, []).append({
# #                                     "Type": "SKU",
# #                                     "Value": sku,
# #                                     "Product ID": product_id,
# #                                     "Product Title": title,
# #                                     "Variant ID": v.get("id"),
# #                                     "Price": v.get("price"),
# #                                     "Created At": created
# #                                 })

# #                         # ---------- ASIN ----------
# #                         for tag in tags.split(","):

# #                             tag = tag.strip()

# #                             if tag.upper().startswith("ASIN:"):
# #                                 asin = tag.split(":", 1)[1].strip().upper()

# #                                 asin_map.setdefault(asin, []).append({
# #                                     "Type": "ASIN",
# #                                     "Value": asin,
# #                                     "Product ID": product_id,
# #                                     "Product Title": title,
# #                                     "Variant ID": "",
# #                                     "Price": "",
# #                                     "Created At": created
# #                                 })
# #                     dupes = {}
# #                     for key, items in sku_map.items():
# #                         if len(items) > 1:
# #                             dupes[f"SKU::{key}"] = items

# #                     for key, items in asin_map.items():
# #                         if len(items) > 1:
# #                             dupes[f"ASIN::{key}"] = items
# #                     st.session_state["dupes"]=dupes; st.session_state["total_prods"]=len(prods)
# #         with b_col:
# #             if st.button("\U0001f4ca Count ASINs & SKUs"):
# #                 with st.spinner("Generating access token…"):
# #                     audit_tok2, aerr2 = get_oauth_token(
# #                         selected_store["domain"],
# #                         selected_store["client_id"],
# #                         selected_store["client_secret"])
# #                 if not audit_tok2:
# #                     st.error(f"Auth failed: {aerr2}")
# #                 else:
# #                     with st.spinner("Loading…"):
# #                         prods=fetch_all_products(selected_store["domain"], audit_tok2)
# #                         asins=build_asin_set(prods); skus=build_sku_set(prods)
# #                     st.info(f"**{len(prods)}** products | **{len(asins)}** ASINs | **{len(skus)}** SKUs")
# #         if "dupes" in st.session_state:
# #             dupes=st.session_state["dupes"]; total_p=st.session_state.get("total_prods","?")
# #             st.caption(f"Scanned **{total_p}** products")
# #             if not dupes:
# #                 st.balloons(); st.success("\u2705 No duplicate SKUs — store is clean!")
# #             else:
# #                 st.warning(f"\u26a0\ufe0f {len(dupes)} duplicate SKU(s)")
# #                 rows = []

# #                 for key, items in dupes.items():

# #                     for item in items:
# #                         rows.append({
# #                             "Duplicate Type": item["Type"],
# #                             "Duplicate Value": item["Value"],
# #                             **item
# #                         })
# #                 df_d=pd.DataFrame(rows)
# #                 st.dataframe(df_d)
# #                 st.download_button("\U0001f4e5 Download CSV",df_d.to_csv(index=False).encode(),"duplicates.csv","text/csv")
# #                 confirm = st.checkbox(
# #                     "I understand that duplicate products will be permanently deleted."
# #                 )

# #                 if confirm:

# #                     if st.button("🗑 Delete Duplicate Products"):

# #                         deleted = 0
# #                         failed = 0
# #                         kept = 0
# #                         deleted_products = set()
# #                         with st.spinner("Deleting duplicate products..."):

# #                             audit_token, err = get_oauth_token(
# #                                 selected_store["domain"],
# #                                 selected_store["client_id"],
# #                                 selected_store["client_secret"]
# #                             )

# #                             if not audit_token:
# #                                 st.error(err)

# #                             else:

# #                                 for sku, items in dupes.items():

# #                                     # items.sort(key=lambda x: x["Created At"])
# #                                     items.sort(
# #                                         key=lambda x: (
# #                                             x.get("Created At") or "9999-12-31",
# #                                             x.get("Product ID")
# #                                         )
# #                                     )

# #                                     kept += 1

# #                                     for item in items[1:]:

# #                                         product_id = item["Product ID"]

# #                                         if product_id in deleted_products:
# #                                             continue

# #                                         ok = delete_product(
# #                                             selected_store["domain"],
# #                                             audit_token,
# #                                             product_id
# #                                         )

# #                                         if ok:
# #                                             deleted_products.add(product_id)
# #                                             deleted += 1
# #                                         else:
# #                                             failed += 1

# #                         st.success(
# #                             f"✅ Deleted: {deleted}\n\n"
# #                             f"✅ Kept: {kept}\n\n"
# #                             f"❌ Failed: {failed}"
# #                         )
# #                         st.session_state.pop("dupes", None)
# #                         st.rerun()

# # # TAB 3 — MANAGE STORES
# # with tab_stores_tab:
# #     st.subheader("\u2795 Add / Update a Store")
# #     st.info(
# #         "**How to get your credentials:**\n\n"
# #         "1. Shopify Admin → Settings → Apps and sales channels → Develop apps\n"
# #         "2. Create app → Configure Admin API scopes → enable **write_products, read_products, write_inventory**\n"
# #         "3. Install the app\n"
# #         "4. Go to **API credentials** tab\n"
# #         "5. Copy **Client ID** and **Client Secret** — paste both below\n\n"
# #         "The app will generate a fresh access token automatically each time you run it."
# #     )
# #     with st.form("store_form"):
# #         fc1,fc2=st.columns(2)
# #         f_name=fc1.text_input("Store Nickname")
# #         # RESTORED DOMAIN FIELD
# #         f_domain = fc2.text_input(
# #             "Domain (e.g. mystore.myshopify.com)"
# #         )
# #         fc3,fc4=st.columns(2)
# #         f_cid=fc3.text_input("Client ID", help="From Shopify: Settings → Apps → Develop apps → your app → API credentials")
# #         f_token=fc4.text_input("Client Secret", type="password", help="From the same page as Client ID")
# #         if st.form_submit_button("\U0001f4be Save Store"):
# #             if f_name and f_domain and f_cid and f_token:
# #                 save_store(f_name,
# #                            f_domain.replace("https://","").replace("http://","").rstrip("/"),
# #                            f_cid, f_token)
# #                 st.success(f"\u2705 Store **{f_name}** saved!")
# #                 st.rerun()
# #             else:
# #                 st.error("Nickname, Domain, Client ID, and Client Secret are all required.")
# #     st.divider()
# #     st.subheader("Saved Stores")
# #     stores_df=all_stores()
# #     if stores_df.empty:
# #         st.info("No stores saved yet.")
# #     else:
# #         for _,row in stores_df.iterrows():
# #             with st.expander(f"\U0001f3ea {row['store_name']} — {row['domain']}"):
# #                 st.code(f"Domain : {row['domain']}", language=None)
# #                 if row["client_id"]: st.code(f"Client ID: {row['client_id']}", language=None)
# #                 st.caption("Access token hidden for security.")
# #                 if st.button(f"\U0001f5d1\ufe0f Delete {row['store_name']}", key=f"del_{row['id']}"):
# #                     delete_store(int(row["id"])); st.rerun()

###################old code
# """
# SC Shopify Master Uploader
# ==========================
# - CSV provides the product list (ASIN, Title, Price, List Price, Link)
# - Selenium scrapes each Amazon link for: images, description, tags
# - Access token stored per store in SQLite — just select store name to run
# - Real-time duplicate check by ASIN tag + SKU before scraping/uploading
# """
# """
# SC Shopify Master Uploader
# ==========================
# - CSV provides the product list (ASIN, Title, Price, List Price, Link)
# - Selenium scrapes each Amazon link for: images, description, tags
# - Access token stored per store in SQLite — just select store name to run
# - Real-time duplicate check by ASIN tag + SKU before scraping/uploading
# """

# import streamlit as st
# import pandas as pd
# import requests
# import sqlite3
# import time
# import re
# import io
# import os
# import shutil
# import tempfile
# import urllib3
# from pathlib import Path
# import random
# import undetected_chromedriver as uc
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # PAGE CONFIG
# st.set_page_config(page_title="SC Shopify Uploader", layout="wide", page_icon="\U0001f6cd\ufe0f")

# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
# html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
# .log-box {
#     background: #0a0c10; color: #39ff14; padding: 16px; border-radius: 10px;
#     font-family: 'JetBrains Mono', monospace; font-size: 12px;
#     height: 420px; overflow-y: auto; border: 1px solid #1e2430; line-height: 1.8;
# }
# .log-skip { color: #f0a500; } .log-ok { color: #39ff14; }
# .log-err  { color: #ff4b4b; } .log-info { color: #5bc8ff; }
# .stat-card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; text-align: center; }
# .stat-num  { font-size: 2.4rem; font-weight: 800; line-height: 1; }
# .stat-lbl  { font-size: 0.75rem; color: #6b7280; margin-top: 4px; letter-spacing: 0.08em; text-transform: uppercase; }
# .stButton>button {
#     background: linear-gradient(135deg, #ff6a00, #ff9900); color: #fff; border: none;
#     border-radius: 10px; font-weight: 700; font-size: 1rem; height: 3.2em; width: 100%;
#     letter-spacing: 0.04em; transition: opacity 0.2s;
# }
# .stButton>button:hover { opacity: 0.88; }
# .stProgress > div > div { background: #ff9900 !important; }
# </style>
# """, unsafe_allow_html=True)

# # DATABASE
# DB = "shopify_stores.db"

# def init_db():
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS stores (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 store_name TEXT, domain TEXT, client_id TEXT, client_secret TEXT
#             )""")
#         conn.commit()
#         table_sql = (conn.execute(
#             "SELECT sql FROM sqlite_master WHERE type='table' AND name='stores'"
#         ).fetchone() or ("",))[0]
#         indexes = conn.execute(
#             "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='stores'"
#         ).fetchall()
#         has_unique_index = any(
#             r[0] and "store_name" in r[0].upper() and "UNIQUE" in r[0].upper()
#             for r in indexes
#         )
#         if "UNIQUE" not in table_sql.upper() and not has_unique_index:
#             conn.execute("ALTER TABLE stores RENAME TO stores_old")
#             conn.execute("""
#                 CREATE TABLE stores (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     store_name TEXT UNIQUE, domain TEXT, client_id TEXT, client_secret TEXT
#                 )""")
#             conn.execute("""
#                 INSERT OR IGNORE INTO stores (id,store_name,domain,client_id,client_secret)
#                 SELECT id,store_name,domain,client_id,client_secret FROM stores_old
#             """)
#             conn.execute("DROP TABLE stores_old")
#             conn.commit()

# def save_store(name, domain, client_id, secret):
#     with sqlite3.connect(DB) as conn:
#         conn.execute("""
#             INSERT INTO stores (store_name,domain,client_id,client_secret) VALUES (?,?,?,?)
#             ON CONFLICT(store_name) DO UPDATE SET
#                 domain=excluded.domain, client_id=excluded.client_id, client_secret=excluded.client_secret
#         """, (name, domain, client_id, secret))
#         conn.commit()

# def all_stores():
#     with sqlite3.connect(DB) as conn:
#         return pd.read_sql_query("SELECT * FROM stores", conn)

# def delete_store(sid):
#     with sqlite3.connect(DB) as conn:
#         conn.execute("DELETE FROM stores WHERE id=?", (sid,))
#         conn.commit()

# init_db()

# # SHOPIFY HELPERS
# def sh_headers(token):
#     return {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
# def shopify_graphql(domain, token, query, variables=None):
#     """
#     Run a Shopify Admin GraphQL query.
#     Returns (data, error_message)
#     """
#     url = f"https://{domain}/admin/api/2024-10/graphql.json"

#     payload = {
#         "query": query,
#         "variables": variables or {}
#     }

#     try:
#         r = requests.post(
#             url,
#             headers=sh_headers(token),
#             json=payload,
#             timeout=20,
#             verify=False
#         )

#         if r.status_code != 200:
#             return None, f"HTTP {r.status_code}: {r.text[:300]}"

#         result = r.json()

#         if result.get("errors"):
#             return None, str(result["errors"])[:500]

#         return result.get("data"), ""

#     except Exception as e:
#         return None, str(e)


# def search_shopify_categories(domain, token, search_term):
#     """
#     Search Shopify Standard Product Taxonomy
#     and return matching categories.
#     """

#     if not search_term:
#         return []

#     query = """
#     query SearchTaxonomy($search: String!, $first: Int!) {
#         taxonomy {
#             categories(search: $search, first: $first) {
#                 nodes {
#                     id
#                     name
#                     fullName
#                     isLeaf
#                     isArchived
#                 }
#             }
#         }
#     }
#     """

#     variables = {
#         "search": search_term,
#         "first": 20
#     }

#     data, error = shopify_graphql(
#         domain,
#         token,
#         query,
#         variables
#     )

#     if error:
#         print(f"Category search failed: {error}")
#         return []

#     try:
#         return data["taxonomy"]["categories"]["nodes"]
#     except Exception:
#         return []

# def get_best_shopify_category(domain, token, breadcrumbs):
#     """
#     Find the most specific Shopify category from Amazon breadcrumbs.
#     Tries the most specific breadcrumb first.
#     """

#     if not breadcrumbs:
#         return None

#     # Most specific category first
#     search_terms = list(reversed([
#         x.strip() for x in breadcrumbs if x.strip()
#     ]))

#     for term in search_terms:
#         categories = search_shopify_categories(
#             domain,
#             token,
#             term
#         )

#         if not categories:
#             continue

#         # Ignore archived categories
#         categories = [
#             c for c in categories
#             if not c.get("isArchived", False)
#         ]

#         if not categories:
#             continue

#         # Prefer exact name match
#         exact = [
#             c for c in categories
#             if c.get("name", "").strip().lower() == term.lower()
#         ]

#         if exact:
#             return exact[0]

#         # Otherwise use first available result
#         return categories[0]

#     return None
# def assign_shopify_category(domain, token, product_id, category_gid):
#     """
#     Assign a Shopify Product Category to an existing product.
#     Returns (True, "") on success, otherwise (False, error).
#     """

#     if not product_id or not category_gid:
#         return False, "Missing product ID or category ID"

#     mutation = """
#     mutation UpdateProductCategory($input: ProductInput!) {
#         productUpdate(input: $input) {
#             product {
#                 id
#                 title
#                 category {
#                     id
#                     name
#                     fullName
#                 }
#             }
#             userErrors {
#                 field
#                 message
#             }
#         }
#     }
#     """

#     variables = {
#         "input": {
#             "id": f"gid://shopify/Product/{product_id}",
#             "category": category_gid
#         }
#     }

#     data, error = shopify_graphql(
#         domain,
#         token,
#         mutation,
#         variables
#     )

#     if error:
#         return False, error

#     try:
#         user_errors = data["productUpdate"]["userErrors"]

#         if user_errors:
#             return False, str(user_errors)

#         category = data["productUpdate"]["product"]["category"]

#         if category:
#             return True, (
#                 f"{category.get('name')} | "
#                 f"{category.get('fullName')} | "
#                 f"{category.get('id')}"
#             )

#         return False, "Product updated but category was not returned"

#     except Exception as e:
#         return False, f"Category assignment response error: {e}"
# def get_oauth_token(domain, client_id, client_secret):
#     """
#     Generate a fresh access token using Client ID + Client Secret.
#     This is the correct flow for Shopify custom apps using client credentials.
#     Returns (token_string, error_message)
#     """
#     url = f"https://{domain}/admin/oauth/access_token"
#     payload = {
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "grant_type": "client_credentials"
#     }
#     try:
#         r = requests.post(url, json=payload, timeout=15, verify=False)
#         if r.status_code == 200:
#             token = r.json().get("access_token", "")
#             if token:
#                 return token, ""
#             return "", "Response OK but no access_token in response"
#         return "", f"HTTP {r.status_code}: {r.text[:200]}"
#     except Exception as e:
#         return "", str(e)

# def verify_token(domain, token):
#     """Verify a token works by calling shop.json. Returns (bool, status, reason)."""
#     try:
#         r = requests.get(
#             f"https://{domain}/admin/api/2024-10/shop.json",
#             headers=sh_headers(token), timeout=15, verify=False)
#         if r.status_code == 200:
#             return True, 200, ""
#         return False, r.status_code, r.text[:200]
#     except Exception as e:
#         return False, 0, str(e)

# def get_or_create_collection(domain, token, name):
#     h = sh_headers(token)
#     r = requests.get(f"https://{domain}/admin/api/2024-10/custom_collections.json?limit=250",
#                      headers=h, verify=False)
#     if r.status_code == 200:
#         for c in r.json().get("custom_collections", []):
#             if c["title"].strip().lower() == name.strip().lower():
#                 return c["id"]
#     r2 = requests.post(f"https://{domain}/admin/api/2024-10/custom_collections.json",
#                        headers=h, json={"custom_collection": {"title": name}}, verify=False)
#     return r2.json()["custom_collection"]["id"] if r2.status_code == 201 else None

# def add_to_collection(domain, token, product_id, collection_id):
#     requests.post(f"https://{domain}/admin/api/2024-10/collects.json",
#                   headers=sh_headers(token),
#                   json={"collect": {"product_id": product_id, "collection_id": collection_id}},
#                   verify=False)

# def fetch_all_products(domain, token):
#     products, url = [], f"https://{domain}/admin/api/2024-10/products.json?limit=250"
#     while url:
#         r = requests.get(url, headers=sh_headers(token), verify=False)
#         if r.status_code == 200:
#             products.extend(r.json().get("products", []))
#             lh = r.headers.get("Link", "")
#             url = None
#             if 'rel="next"' in lh:
#                 for part in lh.split(","):
#                     if 'rel="next"' in part:
#                         url = part.split(";")[0].strip("<> ")
#         elif r.status_code == 429:
#             time.sleep(2)
#         else:
#             break
#     return products
# # def delete_product(domain, token, product_id):
# #     r = requests.delete(
# #         f"https://{domain}/admin/api/2024-10/products/{product_id}.json",
# #         headers=sh_headers(token),
# #         verify=False
# #     )
# #     return r.status_code == 200
# def delete_product(domain, token, product_id):
#     try:
#         r = requests.delete(
#             f"https://{domain}/admin/api/2024-10/products/{product_id}.json",
#             headers=sh_headers(token),
#             timeout=20,
#             verify=False
#         )

#         return r.status_code in (200, 204)

#     except Exception:
#         return False
# def build_asin_set(products):
#     asins = set()
#     for p in products:
#         for tag in (p.get("tags") or "").split(","):
#             t = tag.strip()
#             if t.upper().startswith("ASIN:"):
#                 asins.add(t[5:].strip().upper())
#     return asins

# def build_sku_set(products):
#     skus = set()
#     for p in products:
#         for v in p.get("variants", []):
#             s = (v.get("sku") or "").strip().upper()
#             if s:
#                 skus.add(s)
#     return skus

# # PRICING MATRIX
# def profit_for(cost):
#     table = [(15,10),(50,16),(100,22),(150,27),(200,33),(250,37),
#              (300,45),(350,55),(400,60),(450,65),(500,70),(550,75),(600,78),(650,80)]
#     for t, p in table:
#         if cost <= t:
#             return p
#     return 100

# # CSV PARSING
# REQUIRED_COLS = {"ASIN", "Title", "Price", "Link"}

# def parse_csv(uploaded_file):
#     try:
#         raw = uploaded_file.read()
#         for sep in ("\t", ",", ";"):
#             try:
#                 df = pd.read_csv(io.BytesIO(raw), sep=sep, dtype=str)
#                 df.columns = [c.strip() for c in df.columns]
#                 if REQUIRED_COLS.issubset(set(df.columns)):
#                     return df
#             except:
#                 continue
#         st.error("CSV needs: ASIN, Title, Price, Link columns.")
#         return None
#     except Exception as e:
#         st.error(f"Read error: {e}")
#         return None

# def scrub(text):
#     if not text: return ""
#     text = re.sub(r'amazon|walmart|prime|shipped from|sold by', '', str(text), flags=re.IGNORECASE)
#     text = re.sub(r'\u203a?\s*See more product details|\u203a?\s*See details', '', text, flags=re.IGNORECASE)
#     return text.strip()

# import subprocess
# import json

# # SELENIUM
# def clean_uc_cache():
#     p = os.path.join(os.environ.get("APPDATA", ""), "undetected_chromedriver")
#     if os.path.exists(p):
#         shutil.rmtree(p, ignore_errors=True)

# def get_chrome_version():
#     """Auto-detect installed Chrome major version."""
#     paths = [
#         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
#         r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
#         r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get("USERNAME","")),
#     ]
#     for path in paths:
#         if os.path.exists(path):
#             try:
#                 result = subprocess.run(
#                     [path, "--version"], capture_output=True, text=True, timeout=5)
#                 ver = result.stdout.strip()
#                 match = re.search(r"(\d+)\.\d+\.\d+\.\d+", ver)
#                 if match:
#                     return int(match.group(1))
#             except:
#                 pass
#     # Fallback: try registry
#     try:
#         import winreg
#         key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
#             r"Software\Google\Chrome\BLBeacon")
#         ver, _ = winreg.QueryValueEx(key, "version")
#         winreg.CloseKey(key)
#         return int(ver.split(".")[0])
#     except:
#         pass
#     return None  # will let uc auto-detect

# def build_driver():
#     clean_uc_cache()
#     opts = uc.ChromeOptions()
#     opts.add_argument("--no-sandbox")
#     opts.add_argument("--disable-dev-shm-usage")
#     opts.add_argument("--start-maximized")
#     opts.add_argument("--disable-blink-features=AutomationControlled")
#     opts.add_argument(f"--user-data-dir={Path(tempfile.mkdtemp(prefix='uc_'))}")

#     chrome_ver = get_chrome_version()

#     kwargs = {"options": opts, "use_subprocess": True}
#     if chrome_ver:
#         kwargs["version_main"] = chrome_ver

#     try:
#         driver = uc.Chrome(**kwargs)
#         return driver
#     except Exception as e1:
#         # Clear stale driver files and retry without version pin
#         root = Path(os.environ.get("APPDATA","")) / "undetected_chromedriver"
#         for p in [root/"undetected_chromedriver.exe", root/"undetected"]:
#             try:
#                 if p.is_file(): p.unlink()
#                 elif p.is_dir(): shutil.rmtree(p, ignore_errors=True)
#             except: pass
#         time.sleep(2)
#         try:
#             driver = uc.Chrome(options=opts, use_subprocess=True)
#             return driver
#         except Exception as e2:
#             raise RuntimeError(
#                 f"Chrome failed to start.\n"
#                 f"Detected version: {chrome_ver}\n"
#                 f"Error: {e2}\n\n"
#                 f"Fix: Make sure Google Chrome is installed and up to date."
#             )

# # SIDEBAR
# with st.sidebar:
#     st.markdown("## \U0001f6cd\ufe0f SC Uploader")
#     st.divider()
#     stores_df   = all_stores()
#     store_names = stores_df["store_name"].tolist() if not stores_df.empty else []
#     if store_names:
#         selected_store_name = st.selectbox("Select Store", store_names)
#         selected_store = stores_df[stores_df["store_name"] == selected_store_name].iloc[0]
#         cid_preview = selected_store["client_id"] or ""
#         if cid_preview:
#             st.caption(f"Client ID: {cid_preview[:8]}...")
#             st.caption(f"Domain: {selected_store['domain']}")
#         else:
#             st.warning("No Client ID saved — update in Manage Stores.")
#     else:
#         st.warning("No stores yet — add one in Manage Stores tab.")
#         selected_store = None; selected_store_name = None
#     st.divider()
#     st.subheader("\U0001f4e6 Product Settings")
#     vendor_name     = st.text_input("Vendor / Brand Name", value="SC Store")
#     collection_name = st.text_input("Collection Name",     value="New Arrivals")
#     sku_prefix      = st.text_input("SKU Prefix",          value="CS").strip().upper()
#     zip_code        = st.text_input("Amazon Zip Code",     value="10001").strip()
#     st.divider()
#     uploaded_csv = st.file_uploader("\U0001f4c4 Upload Product CSV", type=["csv","tsv","txt"])
#     st.caption("Needs: ASIN, Title, Price, Link columns")

# # MAIN TABS
# st.title("\U0001f6cd\ufe0f SC Shopify Master Uploader")

# tab_upload, tab_audit, tab_stores_tab = st.tabs([
#     "\U0001f680 Upload Products", "\U0001f50d SKU / ASIN Audit", "\u2699\ufe0f Manage Stores"
# ])

# # TAB 1 — UPLOAD
# with tab_upload:
#     col_browser, col_right = st.columns([1,1])
#     with col_browser:
#         st.subheader("\U0001f4fa Browser Monitor")
#         browser_frame = st.empty()
#         browser_frame.info("Awaiting start…")
#     with col_right:
#         st.subheader("\U0001f4ca Progress")
#         c1,c2,c3,c4 = st.columns(4)
#         stat_total=c1.empty(); stat_uploaded=c2.empty()
#         stat_skipped=c3.empty(); stat_errors=c4.empty()

#     def render_stats(total=0,uploaded=0,skipped=0,errors=0):
#         for holder,num,label,colour in [
#             (stat_total,total,"Total","#5bc8ff"),(stat_uploaded,uploaded,"Uploaded","#39ff14"),
#             (stat_skipped,skipped,"Skipped","#f0a500"),(stat_errors,errors,"Errors","#ff4b4b")
#         ]:
#             holder.markdown(f'''<div class="stat-card"><div class="stat-num" style="color:{colour}">{num}</div><div class="stat-lbl">{label}</div></div>''', unsafe_allow_html=True)

#     render_stats()
#     progress_bar = st.progress(0)
#     log_box = st.empty()
#     log_lines = []

#     def log(msg, kind="info"):
#         ts = time.strftime("%H:%M:%S")
#         css = {"ok":"log-ok","skip":"log-skip","err":"log-err","info":"log-info"}.get(kind,"log-info")
#         log_lines.insert(0, f'<span class="{css}">[{ts}] {msg}</span>')
#         log_box.markdown(f'<div class="log-box">{"<br>".join(log_lines)}</div>', unsafe_allow_html=True)

#     if st.button("\U0001f680 START UPLOAD"):
#         if selected_store is None:
#             st.error("Select a store from the sidebar first."); st.stop()
#         if not uploaded_csv:
#             st.error("Upload a CSV file first."); st.stop()

#         domain      = selected_store["domain"].strip()
#         client_id   = selected_store["client_id"].strip()
#         client_secret = selected_store["client_secret"].strip()

#         log(f"\U0001f510 Generating access token for {domain}…")
#         log(f"   Client ID: {client_id[:8]}...", "info")

#         token, err = get_oauth_token(domain, client_id, client_secret)
#         if not token:
#             log(f"\u274c OAuth failed: {err}", "err")
#             st.error(
#                 f"Failed to generate access token.\n\n"
#                 f"Error: {err}\n\n"
#                 f"Make sure your Client ID and Client Secret are correct.\n"
#                 f"Get them from: Shopify Admin → Settings → Apps → Develop apps → your app → API credentials."
#             )
#             st.stop()
#         log(f"\u2705 Token generated! ({token[:12]}...)", "ok")

#         log(f"Checking collection '{collection_name}'…")
#         coll_id = get_or_create_collection(domain, token, collection_name)
#         log(f"\u2705 Collection ready (ID {coll_id})" if coll_id else "\u26a0\ufe0f No collection — uploading without it.",
#             "ok" if coll_id else "skip")

#         log("\U0001f50e Fetching existing products…")
#         existing_products = fetch_all_products(domain, token)
#         existing_asins    = build_asin_set(existing_products)
#         existing_skus     = build_sku_set(existing_products)
#         log(f"\U0001f4cb {len(existing_products)} products | {len(existing_asins)} ASINs | {len(existing_skus)} SKUs in store","info")

#         df = parse_csv(uploaded_csv)
#         if df is None: st.stop()
#         total = len(df)
#         uploaded = skipped = errors = 0
#         render_stats(total)
#         log(f"\U0001f4c4 CSV: {total} rows","info")

#         log("\U0001f310 Detecting Chrome version and launching browser…")
#         try:
#             driver = build_driver()
#         except RuntimeError as chrome_err:
#             log(f"\u274c Chrome launch failed: {chrome_err}", "err")
#             st.error(str(chrome_err))
#             st.stop()
#         wait = WebDriverWait(driver, 15)
#         log("\u2705 Chrome launched successfully!", "ok")
#         zip_set = False
#         api_url = f"https://{domain}/admin/api/2024-10/products.json"
#         headers = sh_headers(token)

#         try:
#             for idx, row in df.iterrows():
#                 progress_bar.progress(min((idx + 1) / total, 1.0))
#                 asin_csv = str(row.get("ASIN", "")).strip().upper()
#                 title_csv = scrub(str(row.get("Title", f"Product {idx}")))
#                 link = str(row.get("Link", "")).strip()

#                 if not link or "http" not in link:
#                     log(f"Row {idx + 1} — no link, skipped", "skip")
#                     skipped += 1;
#                     render_stats(total, uploaded, skipped, errors);
#                     continue

#                 # ── PRE-SCRAPE duplicate check ──────────────────────────────────────
#                 if asin_csv and asin_csv in existing_asins:
#                     log(f"⏭️ SKIP (ASIN exists) — {asin_csv} | {title_csv[:50]}", "skip")
#                     skipped += 1;
#                     render_stats(total, uploaded, skipped, errors);
#                     continue

#                 # ✅ FIX: generate SKU the SAME way as later, using asin_csv
#                 sku_pre = (f"{sku_prefix}{asin_csv[2:]}" if len(asin_csv) > 2 else "").upper()
#                 if sku_pre and sku_pre in existing_skus:
#                     log(f"⏭️ SKIP (SKU exists pre-check) — {sku_pre}", "skip")
#                     skipped += 1;
#                     render_stats(total, uploaded, skipped, errors);
#                     continue

#                 log(f"🔍 Scraping row {idx + 1}: {title_csv[:55]}…", "info")

#                 if not zip_set:
#                     driver.get("https://www.amazon.com")
#                     time.sleep(2)
#                     try:
#                         driver.find_element(By.ID,"nav-global-location-popover-link").click()
#                         z = wait.until(EC.presence_of_element_located((By.ID,"GLUXZipUpdateInput")))
#                         z.clear(); z.send_keys(zip_code)
#                         driver.find_element(By.ID,"GLUXZipUpdate").click()
#                         time.sleep(1); driver.refresh(); time.sleep(2)
#                     except: pass
#                     zip_set = True

#                 driver.get(link)
#                 time.sleep(3)

#                 try:
#                     browser_frame.image(driver.get_screenshot_as_png(),
#                                         caption=f"Row {idx+1} — {title_csv[:40]}")
#                 except: pass

#                 # ASIN from page
#                 asin = asin_csv  # default to CSV value
#                 try:
#                     ap = driver.find_element(By.ID, "ASIN").get_attribute("value").strip().upper()
#                     if ap: asin = ap
#                 except:
#                     pass

#                 sku = (f"{sku_prefix}{asin[2:]}" if len(asin) > 2 else f"{sku_prefix}{int(time.time())}").upper()

#                 if asin in existing_asins:
#                     log(f"⏭️ SKIP (page ASIN exists) — {asin}", "skip")
#                     skipped += 1;
#                     render_stats(total, uploaded, skipped, errors);
#                     continue

#                 if sku in existing_skus:
#                     log(f"⏭️ SKIP (SKU exists post-scrape) — {sku}", "skip")
#                     skipped += 1;
#                     render_stats(total, uploaded, skipped, errors);
#                     continue

#                 # # IMAGES — main image first, then thumbnails
#                 # images = []
#                 # try:
#                 #     ms = driver.find_element(By.ID,"landingImage").get_attribute("src") or ""
#                 #     if ms.startswith("http"):
#                 #         images.append(re.sub(r'\._[A-Z0-9,_]+_\.','.',ms))
#                 # except: pass
#                 # try:
#                 #     for img in driver.find_elements(By.CSS_SELECTOR,"#altImages ul li img"):
#                 #         src = img.get_attribute("src") or ""
#                 #         if "/images/I/" in src:
#                 #             hi = re.sub(r'\._[A-Z0-9,_-]+_\.','.',src)
#                 #             if hi not in images: images.append(hi)
#                 # except: pass
#                 # images = [i for i in images if i.startswith("http")][:8]
#                 # IMAGES — real product images only, skip Amazon video thumbnails
#                 images = []

#                 # Main product image
#                 try:
#                     ms = driver.find_element(By.ID, "landingImage").get_attribute("src") or ""

#                     # Make sure it is a real Amazon image
#                     if ms.startswith("http") and "/images/I/" in ms:
#                         clean_ms = re.sub(r'\._[A-Z0-9,_-]+\_.', '.', ms)

#                         if clean_ms not in images:
#                             images.append(clean_ms)
#                 except:
#                     pass

#                 # Additional product images
#                 try:
#                     for img in driver.find_elements(By.CSS_SELECTOR, "#altImages ul li img"):

#                         # Check the parent/thumbnail container
#                         try:
#                             parent_html = img.find_element(
#                                 By.XPATH, "./ancestor::li[1]"
#                             ).get_attribute("outerHTML") or ""
#                         except:
#                             parent_html = ""

#                         # Skip Amazon video thumbnails
#                         video_markers = [
#                             "play-icon",
#                             "video",
#                             "video-icon",
#                             "a-icon-play",
#                             "playOverlay",
#                             "play-overlay",
#                             "videoThumbnail"
#                         ]

#                         if any(marker.lower() in parent_html.lower() for marker in video_markers):
#                             continue

#                         src = img.get_attribute("src") or ""

#                         if not src.startswith("http"):
#                             continue

#                         if "/images/I/" not in src:
#                             continue

#                         # Skip obvious video/play thumbnails
#                         src_lower = src.lower()

#                         if any(marker in src_lower for marker in [
#                             "play-icon",
#                             "video",
#                             "play-overlay",
#                             "play_icon"
#                         ]):
#                             continue

#                         # Convert thumbnail URL to high-resolution image
#                         hi = re.sub(r'\._[A-Z0-9,_-]+\_.', '.', src)

#                         if hi not in images:
#                             images.append(hi)

#                 except:
#                     pass

#                 # Final safety limit
#                 images = [
#                     i for i in images
#                     if i.startswith("http")
#                        and "/images/I/" in i
#                 ][:8]

#                 print(f"FINAL IMAGES: {len(images)}")
#                 for img_url in images:
#                     print(f"IMAGE: {img_url}")

#                 # DESCRIPTION
#                 desc = ""
#                 try:
#                     desc = scrub(driver.find_element(By.ID,"feature-bullets").get_attribute("innerHTML"))
#                 except: pass
#                 if not desc:
#                     try:
#                         desc = scrub(driver.find_element(By.ID,"productDescription").get_attribute("innerHTML"))
#                     except: pass

#                 # TITLE from page
#                 title = title_csv
#                 try:
#                     pt = scrub(driver.find_element(By.ID,"productTitle").text)
#                     if pt: title = pt
#                 except: pass
#                 #
#                 # # TAGS from breadcrumbs
#                 # tags = ""
#                 # try:
#                 #     bc = driver.find_elements(By.CSS_SELECTOR,
#                 #         "#wayfinding-breadcrumbs_container li a, .a-breadcrumb li a")
#                 #     tp = [e.text.strip() for e in bc if e.text.strip() and "\u2039" not in e.text]
#                 #     tags = ", ".join(tp)
#                 # except: pass
#                 # print("AMAZON BREADCRUMBS:", tp)
#                 # asin_tag = f"ASIN:{asin}"
#                 # # SHOPIFY PRODUCT CATEGORY
#                 # shopify_category = None
#                 #
#                 # try:
#                 #     shopify_category = get_best_shopify_category(
#                 #         domain,
#                 #         token,
#                 #         tp
#                 #     )
#                 #
#                 #     if shopify_category:
#                 #         print(
#                 #             f"SHOPIFY CATEGORY: "
#                 #             f"{shopify_category.get('name')} | "
#                 #             f"{shopify_category.get('fullName')} | "
#                 #             f"{shopify_category.get('id')}"
#                 #         )
#                 #     else:
#                 #         print("SHOPIFY CATEGORY: No matching category found")
#                 #
#                 # except Exception as category_err:
#                 #     print(f"SHOPIFY CATEGORY ERROR: {category_err}")
#                 # tags = f"{tags}, {asin_tag}" if tags else asin_tag
#                 # TAGS from breadcrumbs
#                 tags = ""
#                 tp = []

#                 try:
#                     bc = driver.find_elements(
#                         By.CSS_SELECTOR,
#                         "#wayfinding-breadcrumbs_container li a, .a-breadcrumb li a"
#                     )

#                     tp = [
#                         e.text.strip()
#                         for e in bc
#                         if e.text.strip() and "\u2039" not in e.text
#                     ]

#                     tags = ", ".join(tp)

#                 except Exception as e:
#                     print(f"AMAZON BREADCRUMBS ERROR: {e}")

#                 print("AMAZON BREADCRUMBS:", tp)

#                 asin_tag = f"ASIN:{asin}"

#                 # SHOPIFY PRODUCT CATEGORY
#                 shopify_category = None

#                 try:
#                     shopify_category = get_best_shopify_category(
#                         domain,
#                         token,
#                         tp
#                     )

#                     if shopify_category:
#                         print(
#                             f"SHOPIFY CATEGORY: "
#                             f"{shopify_category.get('name')} | "
#                             f"{shopify_category.get('fullName')} | "
#                             f"{shopify_category.get('id')}"
#                         )
#                     else:
#                         print("SHOPIFY CATEGORY: No matching category found")

#                 except Exception as category_err:
#                     print(f"SHOPIFY CATEGORY ERROR: {category_err}")

#                 tags = f"{tags}, {asin_tag}" if tags else asin_tag
#                #  # PRICING
#                #  try: cost = float(re.sub(r"[^\d.]","",str(row.get("Price","0"))))
#                #  except: cost = 0.0
#                #  try: list_price = float(re.sub(r"[^\d.]","",str(row.get("List Price","0"))))
#                #  except: list_price = 0.0
#                #
#                # # profit        = profit_for(cost)
#                # # selling_price = round(cost + profit, 2)
#                # # compare_price = round(list_price if list_price > selling_price else selling_price + 8.0, 2)
#                #
#                #  profit = profit_for(cost)
#                #  selling_price = round(cost + profit, 2)
#                #
#                #  # Compare-at price 20%–40% higher than selling price
#                #  compare_price = round(
#                #      selling_price * random.uniform(1.20, 1.40),
#                #      2
#                #  )
#                 # Amazon Selling Price (Price column)
#                 try:
#                     amazon_price = float(re.sub(r"[^\d.]", "", str(row.get("Price", "0"))))
#                 except:
#                     amazon_price = 0.0

#                 # Inventory Cost (List Price / Typical Price)
#                 try:
#                     inventory_cost = float(re.sub(r"[^\d.]", "", str(row.get("List Price", "0"))))
#                 except:
#                     inventory_cost = 0.0

#                 # Agar List Price nahi mili to Amazon price use karo
#                 if inventory_cost <= 0:
#                     inventory_cost = amazon_price

#                 # Profit inventory cost ke hisaab se
#                 profit = profit_for(inventory_cost)

#                 # Shopify Selling Price
#                 selling_price = round(inventory_cost + profit, 2)

#                 # Compare Price
#                 compare_price = round(
#                     selling_price * random.uniform(1.20, 1.40),
#                     2
#                 )
#                 # Console Log (debug)
#                 print(f"""
#                 Amazon Selling : ${amazon_price}
#                 Inventory Cost : ${inventory_cost}
#                 Profit         : ${profit}
#                 New Price      : ${selling_price}
#                 Compare        : ${compare_price}
#                 """)
#                 payload = {
#                     "product": {
#                         "title": title,
#                         "body_html": f"<div>{desc}</div>" if desc else "",
#                         "vendor": vendor_name,
#                         "tags": tags,
#                         "status": "active",
#                         "variants": [{"price":str(selling_price),"compare_at_price":str(compare_price),
#                                       "cost":str(inventory_cost),"sku":sku}],
#                         **({"images":[{"src":i} for i in images]} if images else {}),
#                     }
#                 }

#                 r = requests.post(api_url, headers=headers, json=payload, verify=False)

#                 if r.status_code == 201:
#                     pid = r.json()["product"]["id"]
#                     existing_asins.add(asin); existing_skus.add(sku.upper())
#                     if coll_id: add_to_collection(domain,token,pid,coll_id)
#                     # ── ASSIGN SHOPIFY PRODUCT CATEGORY ─────────────────────
#                     if shopify_category:
#                         category_ok, category_msg = assign_shopify_category(
#                             domain,
#                             token,
#                             pid,
#                             shopify_category["id"]
#                         )

#                         if category_ok:
#                             log(f"🏷️ CATEGORY SET — {category_msg}", "ok")
#                         else:
#                             log(f"⚠️ CATEGORY FAILED — {category_msg}", "err")
#                     else:
#                         log("⚠️ No Shopify category found — product uploaded without category", "skip")
#                     uploaded+=1
#                     log(f"\u2705 {sku} | \u00a3{selling_price} | {len(images)} imgs | {title[:45]}","ok")
#                 elif r.status_code == 429:
#                     log("\u23f3 Rate limited — waiting 4s…","info"); time.sleep(4)
#                     r2 = requests.post(api_url,headers=headers,json=payload,verify=False)
#                     if r2.status_code == 201:
#                         pid=r2.json()["product"]["id"]
#                         existing_asins.add(asin); existing_skus.add(sku.upper())
#                         if coll_id: add_to_collection(domain,token,pid,coll_id)
#                         # ── ASSIGN SHOPIFY PRODUCT CATEGORY ─────────────────────
#                         if shopify_category:
#                             category_ok, category_msg = assign_shopify_category(
#                                 domain,
#                                 token,
#                                 pid,
#                                 shopify_category["id"]
#                             )

#                             if category_ok:
#                                 log(f"🏷️ CATEGORY SET — {category_msg}", "ok")
#                             else:
#                                 log(f"⚠️ CATEGORY FAILED — {category_msg}", "err")
#                         else:
#                             log(
#                                 "⚠️ No Shopify category found — product uploaded without category",
#                                 "skip"
#                             )
#                         uploaded+=1; log(f"\u2705 {sku} (retry OK)","ok")
#                     else:
#                         errors+=1; log(f"\u274c {sku}: {r2.text[:100]}","err")
#                 else:
#                     errors+=1; log(f"\u274c {sku}: {r.text[:100]}","err")

#                 render_stats(total,uploaded,skipped,errors)
#                 time.sleep(0.5)

#         except Exception as e:
#             log(f"\U0001f4a5 Fatal: {e}","err")
#         finally:
#             driver.quit()
#             log("\U0001f310 Browser closed.","info")

#         progress_bar.progress(1.0)
#         log("\u2500"*55,"info")
#         log(f"\U0001f3c1 Done! Uploaded:{uploaded} | Skipped:{skipped} | Errors:{errors}","ok")
#         if uploaded: st.balloons()

# # TAB 2 — AUDIT
# with tab_audit:
#     st.subheader("\U0001f50d Scan for Duplicate SKUs / ASINs")
#     if selected_store is None:
#         st.warning("Select a store in the sidebar first.")
#     else:
#         a_col, b_col = st.columns(2)
#         with a_col:
#             if st.button("\U0001f680 Run Duplicate SKU Audit"):
#                 with st.spinner("Generating access token…"):
#                     audit_token, aerr = get_oauth_token(
#                         selected_store["domain"],
#                         selected_store["client_id"],
#                         selected_store["client_secret"])
#                 if not audit_token:
#                     st.error(f"Auth failed: {aerr}")
#                 else:
#                     with st.spinner("Fetching products…"):
#                         prods = fetch_all_products(selected_store["domain"], audit_token)
#                     # sku_map={}
#                     # for p in prods:
#                     #     for v in p.get("variants",[]):
#                     #         s=(v.get("sku") or "").strip()
#                     #         if s: sku_map.setdefault(s,[]).append({"Product Title":p.get("title"),"Variant ID":v.get("id"),"Price":v.get("price")})
#                     # sku_map = {}
#                     #
#                     # for p in prods:
#                     #     for v in p.get("variants", []):
#                     #         s = (v.get("sku") or "").strip()
#                     #         if s:
#                     #             sku_map.setdefault(s, []).append({
#                     #                 "Product ID": p.get("id"),
#                     #                 "Product Title": p.get("title"),
#                     #                 "Variant ID": v.get("id"),
#                     #                 "Price": v.get("price"),
#                     #                 "Created At": p.get("created_at")
#                     #             })
#                     # dupes={s:items for s,items in sku_map.items() if len(items)>1}
#                     sku_map = {}
#                     asin_map = {}

#                     for p in prods:

#                         created = p.get("created_at")
#                         product_id = p.get("id")
#                         title = p.get("title")
#                         tags = p.get("tags", "")

#                         # ---------- SKU ----------
#                         for v in p.get("variants", []):

#                             sku = (v.get("sku") or "").strip()

#                             if sku:
#                                 sku_map.setdefault(sku, []).append({
#                                     "Type": "SKU",
#                                     "Value": sku,
#                                     "Product ID": product_id,
#                                     "Product Title": title,
#                                     "Variant ID": v.get("id"),
#                                     "Price": v.get("price"),
#                                     "Created At": created
#                                 })

#                         # ---------- ASIN ----------
#                         for tag in tags.split(","):

#                             tag = tag.strip()

#                             if tag.upper().startswith("ASIN:"):
#                                 asin = tag.split(":", 1)[1].strip().upper()

#                                 asin_map.setdefault(asin, []).append({
#                                     "Type": "ASIN",
#                                     "Value": asin,
#                                     "Product ID": product_id,
#                                     "Product Title": title,
#                                     "Variant ID": "",
#                                     "Price": "",
#                                     "Created At": created
#                                 })
#                     dupes = {}
#                     for key, items in sku_map.items():
#                         if len(items) > 1:
#                             dupes[f"SKU::{key}"] = items

#                     for key, items in asin_map.items():
#                         if len(items) > 1:
#                             dupes[f"ASIN::{key}"] = items
#                     st.session_state["dupes"]=dupes; st.session_state["total_prods"]=len(prods)
#         with b_col:
#             if st.button("\U0001f4ca Count ASINs & SKUs"):
#                 with st.spinner("Generating access token…"):
#                     audit_tok2, aerr2 = get_oauth_token(
#                         selected_store["domain"],
#                         selected_store["client_id"],
#                         selected_store["client_secret"])
#                 if not audit_tok2:
#                     st.error(f"Auth failed: {aerr2}")
#                 else:
#                     with st.spinner("Loading…"):
#                         prods=fetch_all_products(selected_store["domain"], audit_tok2)
#                         asins=build_asin_set(prods); skus=build_sku_set(prods)
#                     st.info(f"**{len(prods)}** products | **{len(asins)}** ASINs | **{len(skus)}** SKUs")
#         if "dupes" in st.session_state:
#             dupes=st.session_state["dupes"]; total_p=st.session_state.get("total_prods","?")
#             st.caption(f"Scanned **{total_p}** products")
#             if not dupes:
#                 st.balloons(); st.success("\u2705 No duplicate SKUs — store is clean!")
#             else:
#                 st.warning(f"\u26a0\ufe0f {len(dupes)} duplicate SKU(s)")
#                 rows = []

#                 for key, items in dupes.items():

#                     for item in items:
#                         rows.append({
#                             "Duplicate Type": item["Type"],
#                             "Duplicate Value": item["Value"],
#                             **item
#                         })
#                 df_d=pd.DataFrame(rows)
#                 st.dataframe(df_d)
#                 st.download_button("\U0001f4e5 Download CSV",df_d.to_csv(index=False).encode(),"duplicates.csv","text/csv")
#                 confirm = st.checkbox(
#                     "I understand that duplicate products will be permanently deleted."
#                 )

#                 if confirm:

#                     if st.button("🗑 Delete Duplicate Products"):

#                         deleted = 0
#                         failed = 0
#                         kept = 0
#                         deleted_products = set()
#                         with st.spinner("Deleting duplicate products..."):

#                             audit_token, err = get_oauth_token(
#                                 selected_store["domain"],
#                                 selected_store["client_id"],
#                                 selected_store["client_secret"]
#                             )

#                             if not audit_token:
#                                 st.error(err)

#                             else:

#                                 for sku, items in dupes.items():

#                                     # items.sort(key=lambda x: x["Created At"])
#                                     items.sort(
#                                         key=lambda x: (
#                                             x.get("Created At") or "9999-12-31",
#                                             x.get("Product ID")
#                                         )
#                                     )

#                                     kept += 1

#                                     for item in items[1:]:

#                                         product_id = item["Product ID"]

#                                         if product_id in deleted_products:
#                                             continue

#                                         ok = delete_product(
#                                             selected_store["domain"],
#                                             audit_token,
#                                             product_id
#                                         )

#                                         if ok:
#                                             deleted_products.add(product_id)
#                                             deleted += 1
#                                         else:
#                                             failed += 1

#                         st.success(
#                             f"✅ Deleted: {deleted}\n\n"
#                             f"✅ Kept: {kept}\n\n"
#                             f"❌ Failed: {failed}"
#                         )
#                         st.session_state.pop("dupes", None)
#                         st.rerun()

# # TAB 3 — MANAGE STORES
# with tab_stores_tab:
#     st.subheader("\u2795 Add / Update a Store")
#     st.info(
#         "**How to get your credentials:**\n\n"
#         "1. Shopify Admin → Settings → Apps and sales channels → Develop apps\n"
#         "2. Create app → Configure Admin API scopes → enable **write_products, read_products, write_inventory**\n"
#         "3. Install the app\n"
#         "4. Go to **API credentials** tab\n"
#         "5. Copy **Client ID** and **Client Secret** — paste both below\n\n"
#         "The app will generate a fresh access token automatically each time you run it."
#     )
#     with st.form("store_form"):
#         fc1,fc2=st.columns(2)
#         f_name=fc1.text_input("Store Nickname")
#         # RESTORED DOMAIN FIELD
#         f_domain = fc2.text_input(
#             "Domain (e.g. mystore.myshopify.com)"
#         )
#         fc3,fc4=st.columns(2)
#         f_cid=fc3.text_input("Client ID", help="From Shopify: Settings → Apps → Develop apps → your app → API credentials")
#         f_token=fc4.text_input("Client Secret", type="password", help="From the same page as Client ID")
#         if st.form_submit_button("\U0001f4be Save Store"):
#             if f_name and f_domain and f_cid and f_token:
#                 save_store(f_name,
#                            f_domain.replace("https://","").replace("http://","").rstrip("/"),
#                            f_cid, f_token)
#                 st.success(f"\u2705 Store **{f_name}** saved!")
#                 st.rerun()
#             else:
#                 st.error("Nickname, Domain, Client ID, and Client Secret are all required.")
#     st.divider()
#     st.subheader("Saved Stores")
#     stores_df=all_stores()
#     if stores_df.empty:
#         st.info("No stores saved yet.")
#     else:
#         for _,row in stores_df.iterrows():
#             with st.expander(f"\U0001f3ea {row['store_name']} — {row['domain']}"):
#                 st.code(f"Domain : {row['domain']}", language=None)
#                 if row["client_id"]: st.code(f"Client ID: {row['client_id']}", language=None)
#                 st.caption("Access token hidden for security.")
#                 if st.button(f"\U0001f5d1\ufe0f Delete {row['store_name']}", key=f"del_{row['id']}"):
#                     delete_store(int(row["id"])); st.rerun()

##############################new code

"""
SC Shopify Master Uploader
==========================
- CSV provides the product list (ASIN, Title, Price, List Price, Link)
- Selenium scrapes each Amazon link for: images, description, tags
- Access token stored per store in SQLite — just select store name to run
- Real-time duplicate check by ASIN tag + SKU before scraping/uploading
"""
"""
SC Shopify Master Uploader
==========================
- CSV provides the product list (ASIN, Title, Price, List Price, Link)
- Selenium scrapes each Amazon link for: images, description, tags
- Access token stored per store in SQLite — just select store name to run
- Real-time duplicate check by ASIN tag + SKU before scraping/uploading
"""

import streamlit as st
import pandas as pd
import requests
import sqlite3
import time
import re
import io
import os
import shutil
import tempfile
import urllib3
from pathlib import Path
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Amazon marketplace, currency, and delivery-location presets.
AMAZON_MARKETPLACES = {
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
    "https://www.amazon.de": {"Berlin": "10115", "Munich": "80331", "Hamburg": "20095", "Frankfurt": "60311"},
    "https://www.amazon.fr": {"Paris": "75001", "Lyon": "69001", "Marseille": "13001"},
    "https://www.amazon.it": {"Rome": "00100", "Milan": "20121", "Naples": "80100"},
    "https://www.amazon.es": {"Madrid": "28001", "Barcelona": "08001", "Valencia": "46001"},
    "https://www.amazon.in": {"New Delhi": "110001", "Mumbai": "400001", "Bengaluru": "560001"},
}

# PAGE CONFIG
st.set_page_config(page_title="SC Shopify Uploader", layout="wide", page_icon="\U0001f6cd\ufe0f")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.log-box {
    background: #0a0c10; color: #39ff14; padding: 16px; border-radius: 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    height: 420px; overflow-y: auto; border: 1px solid #1e2430; line-height: 1.8;
}
.log-skip { color: #f0a500; } .log-ok { color: #39ff14; }
.log-err  { color: #ff4b4b; } .log-info { color: #5bc8ff; }
.stat-card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; text-align: center; }
.stat-num  { font-size: 2.4rem; font-weight: 800; line-height: 1; }
.stat-lbl  { font-size: 0.75rem; color: #6b7280; margin-top: 4px; letter-spacing: 0.08em; text-transform: uppercase; }
.stButton>button {
    background: linear-gradient(135deg, #ff6a00, #ff9900); color: #fff; border: none;
    border-radius: 10px; font-weight: 700; font-size: 1rem; height: 3.2em; width: 100%;
    letter-spacing: 0.04em; transition: opacity 0.2s;
}
.stButton>button:hover { opacity: 0.88; }
.stProgress > div > div { background: #ff9900 !important; }
</style>
""", unsafe_allow_html=True)

# DATABASE
DB = "shopify_stores.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_name TEXT, domain TEXT, client_id TEXT, client_secret TEXT
            )""")
        conn.commit()
        table_sql = (conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='stores'"
        ).fetchone() or ("",))[0]
        indexes = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='stores'"
        ).fetchall()
        has_unique_index = any(
            r[0] and "store_name" in r[0].upper() and "UNIQUE" in r[0].upper()
            for r in indexes
        )
        if "UNIQUE" not in table_sql.upper() and not has_unique_index:
            conn.execute("ALTER TABLE stores RENAME TO stores_old")
            conn.execute("""
                CREATE TABLE stores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_name TEXT UNIQUE, domain TEXT, client_id TEXT, client_secret TEXT
                )""")
            conn.execute("""
                INSERT OR IGNORE INTO stores (id,store_name,domain,client_id,client_secret)
                SELECT id,store_name,domain,client_id,client_secret FROM stores_old
            """)
            conn.execute("DROP TABLE stores_old")
            conn.commit()

def save_store(name, domain, client_id, secret):
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            INSERT INTO stores (store_name,domain,client_id,client_secret) VALUES (?,?,?,?)
            ON CONFLICT(store_name) DO UPDATE SET
                domain=excluded.domain, client_id=excluded.client_id, client_secret=excluded.client_secret
        """, (name, domain, client_id, secret))
        conn.commit()

def all_stores():
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query("SELECT * FROM stores", conn)

def delete_store(sid):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM stores WHERE id=?", (sid,))
        conn.commit()

init_db()

# SHOPIFY HELPERS
def sh_headers(token):
    return {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
def shopify_graphql(domain, token, query, variables=None):
    """
    Run a Shopify Admin GraphQL query.
    Returns (data, error_message)
    """
    url = f"https://{domain}/admin/api/2024-10/graphql.json"

    payload = {
        "query": query,
        "variables": variables or {}
    }

    try:
        r = requests.post(
            url,
            headers=sh_headers(token),
            json=payload,
            timeout=20,
            verify=False
        )

        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"

        result = r.json()

        if result.get("errors"):
            return None, str(result["errors"])[:500]

        return result.get("data"), ""

    except Exception as e:
        return None, str(e)


def search_shopify_categories(domain, token, search_term):
    """
    Search Shopify Standard Product Taxonomy
    and return matching categories.
    """

    if not search_term:
        return []

    query = """
    query SearchTaxonomy($search: String!, $first: Int!) {
        taxonomy {
            categories(search: $search, first: $first) {
                nodes {
                    id
                    name
                    fullName
                    isLeaf
                    isArchived
                }
            }
        }
    }
    """

    variables = {
        "search": search_term,
        "first": 20
    }

    data, error = shopify_graphql(
        domain,
        token,
        query,
        variables
    )

    if error:
        print(f"Category search failed: {error}")
        return []

    try:
        return data["taxonomy"]["categories"]["nodes"]
    except Exception:
        return []

def get_best_shopify_category(domain, token, breadcrumbs):
    """
    Find the most specific Shopify category from Amazon breadcrumbs.
    Tries the most specific breadcrumb first.
    """

    if not breadcrumbs:
        return None

    # Most specific category first
    search_terms = list(reversed([
        x.strip() for x in breadcrumbs if x.strip()
    ]))

    for term in search_terms:
        categories = search_shopify_categories(
            domain,
            token,
            term
        )

        if not categories:
            continue

        # Ignore archived categories
        categories = [
            c for c in categories
            if not c.get("isArchived", False)
        ]

        if not categories:
            continue

        # Prefer exact name match
        exact = [
            c for c in categories
            if c.get("name", "").strip().lower() == term.lower()
        ]

        if exact:
            return exact[0]

        # Otherwise use first available result
        return categories[0]

    return None
def assign_shopify_category(domain, token, product_id, category_gid):
    """
    Assign a Shopify Product Category to an existing product.
    Returns (True, "") on success, otherwise (False, error).
    """

    if not product_id or not category_gid:
        return False, "Missing product ID or category ID"

    mutation = """
    mutation UpdateProductCategory($input: ProductInput!) {
        productUpdate(input: $input) {
            product {
                id
                title
                category {
                    id
                    name
                    fullName
                }
            }
            userErrors {
                field
                message
            }
        }
    }
    """

    variables = {
        "input": {
            "id": f"gid://shopify/Product/{product_id}",
            "category": category_gid
        }
    }

    data, error = shopify_graphql(
        domain,
        token,
        mutation,
        variables
    )

    if error:
        return False, error

    try:
        user_errors = data["productUpdate"]["userErrors"]

        if user_errors:
            return False, str(user_errors)

        category = data["productUpdate"]["product"]["category"]

        if category:
            return True, (
                f"{category.get('name')} | "
                f"{category.get('fullName')} | "
                f"{category.get('id')}"
            )

        return False, "Product updated but category was not returned"

    except Exception as e:
        return False, f"Category assignment response error: {e}"
def get_oauth_token(domain, client_id, client_secret):
    """
    Generate a fresh access token using Client ID + Client Secret.
    This is the correct flow for Shopify custom apps using client credentials.
    Returns (token_string, error_message)
    """
    url = f"https://{domain}/admin/oauth/access_token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
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

def verify_token(domain, token):
    """Verify a token works by calling shop.json. Returns (bool, status, reason)."""
    try:
        r = requests.get(
            f"https://{domain}/admin/api/2024-10/shop.json",
            headers=sh_headers(token), timeout=15, verify=False)
        if r.status_code == 200:
            return True, 200, ""
        return False, r.status_code, r.text[:200]
    except Exception as e:
        return False, 0, str(e)

def get_or_create_collection(domain, token, name):
    h = sh_headers(token)
    r = requests.get(f"https://{domain}/admin/api/2024-10/custom_collections.json?limit=250",
                     headers=h, verify=False)
    if r.status_code == 200:
        for c in r.json().get("custom_collections", []):
            if c["title"].strip().lower() == name.strip().lower():
                return c["id"]
    r2 = requests.post(f"https://{domain}/admin/api/2024-10/custom_collections.json",
                       headers=h, json={"custom_collection": {"title": name}}, verify=False)
    return r2.json()["custom_collection"]["id"] if r2.status_code == 201 else None

def add_to_collection(domain, token, product_id, collection_id):
    requests.post(f"https://{domain}/admin/api/2024-10/collects.json",
                  headers=sh_headers(token),
                  json={"collect": {"product_id": product_id, "collection_id": collection_id}},
                  verify=False)

def fetch_all_products(domain, token):
    products, url = [], f"https://{domain}/admin/api/2024-10/products.json?limit=250"
    while url:
        r = requests.get(url, headers=sh_headers(token), verify=False)
        if r.status_code == 200:
            products.extend(r.json().get("products", []))
            lh = r.headers.get("Link", "")
            url = None
            if 'rel="next"' in lh:
                for part in lh.split(","):
                    if 'rel="next"' in part:
                        url = part.split(";")[0].strip("<> ")
        elif r.status_code == 429:
            time.sleep(2)
        else:
            break
    return products
# def delete_product(domain, token, product_id):
#     r = requests.delete(
#         f"https://{domain}/admin/api/2024-10/products/{product_id}.json",
#         headers=sh_headers(token),
#         verify=False
#     )
#     return r.status_code == 200
def delete_product(domain, token, product_id):
    try:
        r = requests.delete(
            f"https://{domain}/admin/api/2024-10/products/{product_id}.json",
            headers=sh_headers(token),
            timeout=20,
            verify=False
        )

        return r.status_code in (200, 204)

    except Exception:
        return False
def build_asin_set(products):
    asins = set()
    for p in products:
        for tag in (p.get("tags") or "").split(","):
            t = tag.strip()
            if t.upper().startswith("ASIN:"):
                asins.add(t[5:].strip().upper())
    return asins

def build_sku_set(products):
    skus = set()
    for p in products:
        for v in p.get("variants", []):
            s = (v.get("sku") or "").strip().upper()
            if s:
                skus.add(s)
    return skus

# PRICING MATRIX
def profit_for(cost):
    table = [(15,10),(50,16),(100,22),(150,27),(200,33),(250,37),
             (300,45),(350,55),(400,60),(450,65),(500,70),(550,75),(600,78),(650,80)]
    for t, p in table:
        if cost <= t:
            return p
    return 100

# CSV PARSING
REQUIRED_COLS = {"ASIN", "Title", "Price", "Link"}

def parse_csv(uploaded_file):
    try:
        raw = uploaded_file.read()
        for sep in ("\t", ",", ";"):
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=sep, dtype=str)
                df.columns = [c.strip() for c in df.columns]
                if REQUIRED_COLS.issubset(set(df.columns)):
                    return df
            except:
                continue
        st.error("CSV needs: ASIN, Title, Price, Link columns.")
        return None
    except Exception as e:
        st.error(f"Read error: {e}")
        return None

def scrub(text):
    if not text: return ""
    text = re.sub(r'amazon|walmart|prime|shipped from|sold by', '', str(text), flags=re.IGNORECASE)
    text = re.sub(r'\u203a?\s*See more product details|\u203a?\s*See details', '', text, flags=re.IGNORECASE)
    return text.strip()

import subprocess
import json

# SELENIUM
def clean_uc_cache():
    p = os.path.join(os.environ.get("APPDATA", ""), "undetected_chromedriver")
    if os.path.exists(p):
        shutil.rmtree(p, ignore_errors=True)

def get_chrome_version():
    """Auto-detect installed Chrome major version."""
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get("USERNAME","")),
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, "--version"], capture_output=True, text=True, timeout=5)
                ver = result.stdout.strip()
                match = re.search(r"(\d+)\.\d+\.\d+\.\d+", ver)
                if match:
                    return int(match.group(1))
            except:
                pass
    # Fallback: try registry
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Google\Chrome\BLBeacon")
        ver, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
        return int(ver.split(".")[0])
    except:
        pass
    return None  # will let uc auto-detect

def build_driver():
    clean_uc_cache()
    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(f"--user-data-dir={Path(tempfile.mkdtemp(prefix='uc_'))}")

    chrome_ver = get_chrome_version()

    kwargs = {"options": opts, "use_subprocess": True}
    if chrome_ver:
        kwargs["version_main"] = chrome_ver

    try:
        driver = uc.Chrome(**kwargs)
        return driver
    except Exception as e1:
        # Clear stale driver files and retry without version pin
        root = Path(os.environ.get("APPDATA","")) / "undetected_chromedriver"
        for p in [root/"undetected_chromedriver.exe", root/"undetected"]:
            try:
                if p.is_file(): p.unlink()
                elif p.is_dir(): shutil.rmtree(p, ignore_errors=True)
            except: pass
        time.sleep(2)
        try:
            driver = uc.Chrome(options=opts, use_subprocess=True)
            return driver
        except Exception as e2:
            raise RuntimeError(
                f"Chrome failed to start.\n"
                f"Detected version: {chrome_ver}\n"
                f"Error: {e2}\n\n"
                f"Fix: Make sure Google Chrome is installed and up to date."
            )


def configure_amazon_marketplace(driver, base_url, zip_code, currency_code, log_fn=None):
    """Set the selected Amazon currency and delivery location before scraping."""
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
        if log_fn:
            log_fn(f"✅ Currency set to {currency_code}", "ok")
    except Exception as error:
        if log_fn:
            log_fn(f"⚠️ Currency could not be set: {str(error)[:80]}", "skip")

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
            zip_input = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.ID, "GLUXZipUpdateInput"))
            )
            zip_input.clear()
            zip_input.send_keys(zip_code)
        driver.find_element(By.ID, "GLUXZipUpdate").click()
        time.sleep(1)
        try:
            driver.find_element(By.NAME, "glowDoneButton").click()
        except Exception:
            pass
        time.sleep(2)
        if log_fn:
            log_fn(f"✅ Delivery location set to {zip_code}", "ok")
    except Exception as error:
        if log_fn:
            log_fn(f"⚠️ Location could not be set: {str(error)[:80]}", "skip")


def selected_marketplace_link(base_url, asin, csv_link):
    """Open the selected country's product page when an ASIN is available."""
    asin = str(asin or "").strip().upper()
    if re.fullmatch(r"[A-Z0-9]{10}", asin):
        return f"{base_url}/dp/{asin}"
    return csv_link

# SIDEBAR
with st.sidebar:
    st.markdown("## \U0001f6cd\ufe0f SC Uploader")
    st.divider()
    stores_df   = all_stores()
    store_names = stores_df["store_name"].tolist() if not stores_df.empty else []
    if store_names:
        selected_store_name = st.selectbox("Select Store", store_names)
        selected_store = stores_df[stores_df["store_name"] == selected_store_name].iloc[0]
        cid_preview = selected_store["client_id"] or ""
        if cid_preview:
            st.caption(f"Client ID: {cid_preview[:8]}...")
            st.caption(f"Domain: {selected_store['domain']}")
        else:
            st.warning("No Client ID saved — update in Manage Stores.")
    else:
        st.warning("No stores yet — add one in Manage Stores tab.")
        selected_store = None; selected_store_name = None
    st.divider()
    st.subheader("🌍 Amazon Marketplace")
    marketplace_name = st.selectbox(
        "Select Country", list(AMAZON_MARKETPLACES.keys())
    )
    marketplace = AMAZON_MARKETPLACES[marketplace_name]
    amazon_base_url = marketplace["url"]
    amazon_currency = marketplace["currency"]
    st.caption(
        f"Marketplace: {amazon_base_url} | "
        f"Currency: {amazon_currency} ({marketplace['symbol']})"
    )

    location_presets = LOCATION_PRESETS[amazon_base_url]
    location_choice = st.selectbox(
        "Select City", list(location_presets) + ["Custom location..."]
    )
    if location_choice == "Custom location...":
        zip_code = st.text_input("Postal/ZIP Code").strip()
    else:
        zip_code = location_presets[location_choice]
        st.caption(f"Selected code: {zip_code}")

    st.divider()
    st.subheader("\U0001f4e6 Product Settings")
    vendor_name     = st.text_input("Vendor / Brand Name", value="SC Store")
    collection_name = st.text_input("Collection Name",     value="New Arrivals")
    sku_prefix      = st.text_input("SKU Prefix",          value="CS").strip().upper()
    st.divider()
    uploaded_csv = st.file_uploader("\U0001f4c4 Upload Product CSV", type=["csv","tsv","txt"])
    st.caption("Needs: ASIN, Title, Price, Link columns")

# MAIN TABS
st.title("\U0001f6cd\ufe0f SC Shopify Master Uploader")

tab_upload, tab_audit, tab_stores_tab = st.tabs([
    "\U0001f680 Upload Products", "\U0001f50d SKU / ASIN Audit", "\u2699\ufe0f Manage Stores"
])

# TAB 1 — UPLOAD
with tab_upload:
    col_browser, col_right = st.columns([1,1])
    with col_browser:
        st.subheader("\U0001f4fa Browser Monitor")
        browser_frame = st.empty()
        browser_frame.info("Awaiting start…")
    with col_right:
        st.subheader("\U0001f4ca Progress")
        c1,c2,c3,c4 = st.columns(4)
        stat_total=c1.empty(); stat_uploaded=c2.empty()
        stat_skipped=c3.empty(); stat_errors=c4.empty()

    def render_stats(total=0,uploaded=0,skipped=0,errors=0):
        for holder,num,label,colour in [
            (stat_total,total,"Total","#5bc8ff"),(stat_uploaded,uploaded,"Uploaded","#39ff14"),
            (stat_skipped,skipped,"Skipped","#f0a500"),(stat_errors,errors,"Errors","#ff4b4b")
        ]:
            holder.markdown(f'''<div class="stat-card"><div class="stat-num" style="color:{colour}">{num}</div><div class="stat-lbl">{label}</div></div>''', unsafe_allow_html=True)

    render_stats()
    progress_bar = st.progress(0)
    log_box = st.empty()
    log_lines = []

    def log(msg, kind="info"):
        ts = time.strftime("%H:%M:%S")
        css = {"ok":"log-ok","skip":"log-skip","err":"log-err","info":"log-info"}.get(kind,"log-info")
        log_lines.insert(0, f'<span class="{css}">[{ts}] {msg}</span>')
        log_box.markdown(f'<div class="log-box">{"<br>".join(log_lines)}</div>', unsafe_allow_html=True)

    if st.button("\U0001f680 START UPLOAD"):
        if selected_store is None:
            st.error("Select a store from the sidebar first."); st.stop()
        if not uploaded_csv:
            st.error("Upload a CSV file first."); st.stop()

        domain      = selected_store["domain"].strip()
        client_id   = selected_store["client_id"].strip()
        client_secret = selected_store["client_secret"].strip()

        log(f"\U0001f510 Generating access token for {domain}…")
        log(f"   Client ID: {client_id[:8]}...", "info")

        token, err = get_oauth_token(domain, client_id, client_secret)
        if not token:
            log(f"\u274c OAuth failed: {err}", "err")
            st.error(
                f"Failed to generate access token.\n\n"
                f"Error: {err}\n\n"
                f"Make sure your Client ID and Client Secret are correct.\n"
                f"Get them from: Shopify Admin → Settings → Apps → Develop apps → your app → API credentials."
            )
            st.stop()
        log(f"\u2705 Token generated! ({token[:12]}...)", "ok")

        log(f"Checking collection '{collection_name}'…")
        coll_id = get_or_create_collection(domain, token, collection_name)
        log(f"\u2705 Collection ready (ID {coll_id})" if coll_id else "\u26a0\ufe0f No collection — uploading without it.",
            "ok" if coll_id else "skip")

        log("\U0001f50e Fetching existing products…")
        existing_products = fetch_all_products(domain, token)
        existing_asins    = build_asin_set(existing_products)
        existing_skus     = build_sku_set(existing_products)
        log(f"\U0001f4cb {len(existing_products)} products | {len(existing_asins)} ASINs | {len(existing_skus)} SKUs in store","info")

        df = parse_csv(uploaded_csv)
        if df is None: st.stop()
        total = len(df)
        uploaded = skipped = errors = 0
        render_stats(total)
        log(f"\U0001f4c4 CSV: {total} rows","info")

        log("\U0001f310 Detecting Chrome version and launching browser…")
        try:
            driver = build_driver()
        except RuntimeError as chrome_err:
            log(f"\u274c Chrome launch failed: {chrome_err}", "err")
            st.error(str(chrome_err))
            st.stop()
        wait = WebDriverWait(driver, 15)
        log("\u2705 Chrome launched successfully!", "ok")
        configure_amazon_marketplace(
            driver,
            amazon_base_url,
            zip_code,
            amazon_currency,
            log_fn=log,
        )
        api_url = f"https://{domain}/admin/api/2024-10/products.json"
        headers = sh_headers(token)

        try:
            for idx, row in df.iterrows():
                progress_bar.progress(min((idx + 1) / total, 1.0))
                asin_csv = str(row.get("ASIN", "")).strip().upper()
                title_csv = scrub(str(row.get("Title", f"Product {idx}")))
                link = str(row.get("Link", "")).strip()

                if not link or "http" not in link:
                    log(f"Row {idx + 1} — no link, skipped", "skip")
                    skipped += 1;
                    render_stats(total, uploaded, skipped, errors);
                    continue

                # ── PRE-SCRAPE duplicate check ──────────────────────────────────────
                if asin_csv and asin_csv in existing_asins:
                    log(f"⏭️ SKIP (ASIN exists) — {asin_csv} | {title_csv[:50]}", "skip")
                    skipped += 1;
                    render_stats(total, uploaded, skipped, errors);
                    continue

                # ✅ FIX: generate SKU the SAME way as later, using asin_csv
                sku_pre = (f"{sku_prefix}{asin_csv[2:]}" if len(asin_csv) > 2 else "").upper()
                if sku_pre and sku_pre in existing_skus:
                    log(f"⏭️ SKIP (SKU exists pre-check) — {sku_pre}", "skip")
                    skipped += 1;
                    render_stats(total, uploaded, skipped, errors);
                    continue

                log(f"🔍 Scraping row {idx + 1}: {title_csv[:55]}…", "info")

                link = selected_marketplace_link(
                    amazon_base_url, asin_csv, link
                )
                driver.get(link)
                time.sleep(3)

                try:
                    browser_frame.image(driver.get_screenshot_as_png(),
                                        caption=f"Row {idx+1} — {title_csv[:40]}")
                except: pass

                # ASIN from page
                asin = asin_csv  # default to CSV value
                try:
                    ap = driver.find_element(By.ID, "ASIN").get_attribute("value").strip().upper()
                    if ap: asin = ap
                except:
                    pass

                sku = (f"{sku_prefix}{asin[2:]}" if len(asin) > 2 else f"{sku_prefix}{int(time.time())}").upper()

                if asin in existing_asins:
                    log(f"⏭️ SKIP (page ASIN exists) — {asin}", "skip")
                    skipped += 1;
                    render_stats(total, uploaded, skipped, errors);
                    continue

                if sku in existing_skus:
                    log(f"⏭️ SKIP (SKU exists post-scrape) — {sku}", "skip")
                    skipped += 1;
                    render_stats(total, uploaded, skipped, errors);
                    continue

                # # IMAGES — main image first, then thumbnails
                # images = []
                # try:
                #     ms = driver.find_element(By.ID,"landingImage").get_attribute("src") or ""
                #     if ms.startswith("http"):
                #         images.append(re.sub(r'\._[A-Z0-9,_]+_\.','.',ms))
                # except: pass
                # try:
                #     for img in driver.find_elements(By.CSS_SELECTOR,"#altImages ul li img"):
                #         src = img.get_attribute("src") or ""
                #         if "/images/I/" in src:
                #             hi = re.sub(r'\._[A-Z0-9,_-]+_\.','.',src)
                #             if hi not in images: images.append(hi)
                # except: pass
                # images = [i for i in images if i.startswith("http")][:8]
                # IMAGES — real product images only, skip Amazon video thumbnails
                images = []

                # Main product image
                try:
                    ms = driver.find_element(By.ID, "landingImage").get_attribute("src") or ""

                    # Make sure it is a real Amazon image
                    if ms.startswith("http") and "/images/I/" in ms:
                        clean_ms = re.sub(r'\._[A-Z0-9,_-]+\_.', '.', ms)

                        if clean_ms not in images:
                            images.append(clean_ms)
                except:
                    pass

                # Additional product images
                try:
                    for img in driver.find_elements(By.CSS_SELECTOR, "#altImages ul li img"):

                        # Check the parent/thumbnail container
                        try:
                            parent_html = img.find_element(
                                By.XPATH, "./ancestor::li[1]"
                            ).get_attribute("outerHTML") or ""
                        except:
                            parent_html = ""

                        # Skip Amazon video thumbnails
                        video_markers = [
                            "play-icon",
                            "video",
                            "video-icon",
                            "a-icon-play",
                            "playOverlay",
                            "play-overlay",
                            "videoThumbnail"
                        ]

                        if any(marker.lower() in parent_html.lower() for marker in video_markers):
                            continue

                        src = img.get_attribute("src") or ""

                        if not src.startswith("http"):
                            continue

                        if "/images/I/" not in src:
                            continue

                        # Skip obvious video/play thumbnails
                        src_lower = src.lower()

                        if any(marker in src_lower for marker in [
                            "play-icon",
                            "video",
                            "play-overlay",
                            "play_icon"
                        ]):
                            continue

                        # Convert thumbnail URL to high-resolution image
                        hi = re.sub(r'\._[A-Z0-9,_-]+\_.', '.', src)

                        if hi not in images:
                            images.append(hi)

                except:
                    pass

                # Final safety limit
                images = [
                    i for i in images
                    if i.startswith("http")
                       and "/images/I/" in i
                ][:8]

                print(f"FINAL IMAGES: {len(images)}")
                for img_url in images:
                    print(f"IMAGE: {img_url}")

                # DESCRIPTION
                desc = ""
                try:
                    desc = scrub(driver.find_element(By.ID,"feature-bullets").get_attribute("innerHTML"))
                except: pass
                if not desc:
                    try:
                        desc = scrub(driver.find_element(By.ID,"productDescription").get_attribute("innerHTML"))
                    except: pass

                # TITLE from page
                title = title_csv
                try:
                    pt = scrub(driver.find_element(By.ID,"productTitle").text)
                    if pt: title = pt
                except: pass
                #
                # # TAGS from breadcrumbs
                # tags = ""
                # try:
                #     bc = driver.find_elements(By.CSS_SELECTOR,
                #         "#wayfinding-breadcrumbs_container li a, .a-breadcrumb li a")
                #     tp = [e.text.strip() for e in bc if e.text.strip() and "\u2039" not in e.text]
                #     tags = ", ".join(tp)
                # except: pass
                # print("AMAZON BREADCRUMBS:", tp)
                # asin_tag = f"ASIN:{asin}"
                # # SHOPIFY PRODUCT CATEGORY
                # shopify_category = None
                #
                # try:
                #     shopify_category = get_best_shopify_category(
                #         domain,
                #         token,
                #         tp
                #     )
                #
                #     if shopify_category:
                #         print(
                #             f"SHOPIFY CATEGORY: "
                #             f"{shopify_category.get('name')} | "
                #             f"{shopify_category.get('fullName')} | "
                #             f"{shopify_category.get('id')}"
                #         )
                #     else:
                #         print("SHOPIFY CATEGORY: No matching category found")
                #
                # except Exception as category_err:
                #     print(f"SHOPIFY CATEGORY ERROR: {category_err}")
                # tags = f"{tags}, {asin_tag}" if tags else asin_tag
                # TAGS from breadcrumbs
                tags = ""
                tp = []

                try:
                    bc = driver.find_elements(
                        By.CSS_SELECTOR,
                        "#wayfinding-breadcrumbs_container li a, .a-breadcrumb li a"
                    )

                    tp = [
                        e.text.strip()
                        for e in bc
                        if e.text.strip() and "\u2039" not in e.text
                    ]

                    tags = ", ".join(tp)

                except Exception as e:
                    print(f"AMAZON BREADCRUMBS ERROR: {e}")

                print("AMAZON BREADCRUMBS:", tp)

                asin_tag = f"ASIN:{asin}"

                # SHOPIFY PRODUCT CATEGORY
                shopify_category = None

                try:
                    shopify_category = get_best_shopify_category(
                        domain,
                        token,
                        tp
                    )

                    if shopify_category:
                        print(
                            f"SHOPIFY CATEGORY: "
                            f"{shopify_category.get('name')} | "
                            f"{shopify_category.get('fullName')} | "
                            f"{shopify_category.get('id')}"
                        )
                    else:
                        print("SHOPIFY CATEGORY: No matching category found")

                except Exception as category_err:
                    print(f"SHOPIFY CATEGORY ERROR: {category_err}")

                tags = f"{tags}, {asin_tag}" if tags else asin_tag
               #  # PRICING
               #  try: cost = float(re.sub(r"[^\d.]","",str(row.get("Price","0"))))
               #  except: cost = 0.0
               #  try: list_price = float(re.sub(r"[^\d.]","",str(row.get("List Price","0"))))
               #  except: list_price = 0.0
               #
               # # profit        = profit_for(cost)
               # # selling_price = round(cost + profit, 2)
               # # compare_price = round(list_price if list_price > selling_price else selling_price + 8.0, 2)
               #
               #  profit = profit_for(cost)
               #  selling_price = round(cost + profit, 2)
               #
               #  # Compare-at price 20%–40% higher than selling price
               #  compare_price = round(
               #      selling_price * random.uniform(1.20, 1.40),
               #      2
               #  )
                # Amazon Selling Price (Price column)
                try:
                    amazon_price = float(re.sub(r"[^\d.]", "", str(row.get("Price", "0"))))
                except:
                    amazon_price = 0.0

                # Inventory Cost (List Price / Typical Price)
                try:
                    inventory_cost = float(re.sub(r"[^\d.]", "", str(row.get("List Price", "0"))))
                except:
                    inventory_cost = 0.0

                # Agar List Price nahi mili to Amazon price use karo
                if inventory_cost <= 0:
                    inventory_cost = amazon_price

                # Profit inventory cost ke hisaab se
                profit = profit_for(inventory_cost)

                # Shopify Selling Price
                selling_price = round(inventory_cost + profit, 2)

                # Compare Price
                compare_price = round(
                    selling_price * random.uniform(1.20, 1.40),
                    2
                )
                # Console Log (debug)
                print(f"""
                Amazon Selling : ${amazon_price}
                Inventory Cost : ${inventory_cost}
                Profit         : ${profit}
                New Price      : ${selling_price}
                Compare        : ${compare_price}
                """)
                payload = {
                    "product": {
                        "title": title,
                        "body_html": f"<div>{desc}</div>" if desc else "",
                        "vendor": vendor_name,
                        "tags": tags,
                        "status": "active",
                        "variants": [{"price":str(selling_price),"compare_at_price":str(compare_price),
                                      "cost":str(inventory_cost),"sku":sku}],
                        **({"images":[{"src":i} for i in images]} if images else {}),
                    }
                }

                r = requests.post(api_url, headers=headers, json=payload, verify=False)

                if r.status_code == 201:
                    pid = r.json()["product"]["id"]
                    existing_asins.add(asin); existing_skus.add(sku.upper())
                    if coll_id: add_to_collection(domain,token,pid,coll_id)
                    # ── ASSIGN SHOPIFY PRODUCT CATEGORY ─────────────────────
                    if shopify_category:
                        category_ok, category_msg = assign_shopify_category(
                            domain,
                            token,
                            pid,
                            shopify_category["id"]
                        )

                        if category_ok:
                            log(f"🏷️ CATEGORY SET — {category_msg}", "ok")
                        else:
                            log(f"⚠️ CATEGORY FAILED — {category_msg}", "err")
                    else:
                        log("⚠️ No Shopify category found — product uploaded without category", "skip")
                    uploaded+=1
                    log(f"\u2705 {sku} | \u00a3{selling_price} | {len(images)} imgs | {title[:45]}","ok")
                elif r.status_code == 429:
                    log("\u23f3 Rate limited — waiting 4s…","info"); time.sleep(4)
                    r2 = requests.post(api_url,headers=headers,json=payload,verify=False)
                    if r2.status_code == 201:
                        pid=r2.json()["product"]["id"]
                        existing_asins.add(asin); existing_skus.add(sku.upper())
                        if coll_id: add_to_collection(domain,token,pid,coll_id)
                        # ── ASSIGN SHOPIFY PRODUCT CATEGORY ─────────────────────
                        if shopify_category:
                            category_ok, category_msg = assign_shopify_category(
                                domain,
                                token,
                                pid,
                                shopify_category["id"]
                            )

                            if category_ok:
                                log(f"🏷️ CATEGORY SET — {category_msg}", "ok")
                            else:
                                log(f"⚠️ CATEGORY FAILED — {category_msg}", "err")
                        else:
                            log(
                                "⚠️ No Shopify category found — product uploaded without category",
                                "skip"
                            )
                        uploaded+=1; log(f"\u2705 {sku} (retry OK)","ok")
                    else:
                        errors+=1; log(f"\u274c {sku}: {r2.text[:100]}","err")
                else:
                    errors+=1; log(f"\u274c {sku}: {r.text[:100]}","err")

                render_stats(total,uploaded,skipped,errors)
                time.sleep(0.5)

        except Exception as e:
            log(f"\U0001f4a5 Fatal: {e}","err")
        finally:
            driver.quit()
            log("\U0001f310 Browser closed.","info")

        progress_bar.progress(1.0)
        log("\u2500"*55,"info")
        log(f"\U0001f3c1 Done! Uploaded:{uploaded} | Skipped:{skipped} | Errors:{errors}","ok")
        if uploaded: st.balloons()

# TAB 2 — AUDIT
with tab_audit:
    st.subheader("\U0001f50d Scan for Duplicate SKUs / ASINs")
    if selected_store is None:
        st.warning("Select a store in the sidebar first.")
    else:
        a_col, b_col = st.columns(2)
        with a_col:
            if st.button("\U0001f680 Run Duplicate SKU Audit"):
                with st.spinner("Generating access token…"):
                    audit_token, aerr = get_oauth_token(
                        selected_store["domain"],
                        selected_store["client_id"],
                        selected_store["client_secret"])
                if not audit_token:
                    st.error(f"Auth failed: {aerr}")
                else:
                    with st.spinner("Fetching products…"):
                        prods = fetch_all_products(selected_store["domain"], audit_token)
                    # sku_map={}
                    # for p in prods:
                    #     for v in p.get("variants",[]):
                    #         s=(v.get("sku") or "").strip()
                    #         if s: sku_map.setdefault(s,[]).append({"Product Title":p.get("title"),"Variant ID":v.get("id"),"Price":v.get("price")})
                    # sku_map = {}
                    #
                    # for p in prods:
                    #     for v in p.get("variants", []):
                    #         s = (v.get("sku") or "").strip()
                    #         if s:
                    #             sku_map.setdefault(s, []).append({
                    #                 "Product ID": p.get("id"),
                    #                 "Product Title": p.get("title"),
                    #                 "Variant ID": v.get("id"),
                    #                 "Price": v.get("price"),
                    #                 "Created At": p.get("created_at")
                    #             })
                    # dupes={s:items for s,items in sku_map.items() if len(items)>1}
                    sku_map = {}
                    asin_map = {}

                    for p in prods:

                        created = p.get("created_at")
                        product_id = p.get("id")
                        title = p.get("title")
                        tags = p.get("tags", "")

                        # ---------- SKU ----------
                        for v in p.get("variants", []):

                            sku = (v.get("sku") or "").strip()

                            if sku:
                                sku_map.setdefault(sku, []).append({
                                    "Type": "SKU",
                                    "Value": sku,
                                    "Product ID": product_id,
                                    "Product Title": title,
                                    "Variant ID": v.get("id"),
                                    "Price": v.get("price"),
                                    "Created At": created
                                })

                        # ---------- ASIN ----------
                        for tag in tags.split(","):

                            tag = tag.strip()

                            if tag.upper().startswith("ASIN:"):
                                asin = tag.split(":", 1)[1].strip().upper()

                                asin_map.setdefault(asin, []).append({
                                    "Type": "ASIN",
                                    "Value": asin,
                                    "Product ID": product_id,
                                    "Product Title": title,
                                    "Variant ID": "",
                                    "Price": "",
                                    "Created At": created
                                })
                    dupes = {}
                    for key, items in sku_map.items():
                        if len(items) > 1:
                            dupes[f"SKU::{key}"] = items

                    for key, items in asin_map.items():
                        if len(items) > 1:
                            dupes[f"ASIN::{key}"] = items
                    st.session_state["dupes"]=dupes; st.session_state["total_prods"]=len(prods)
        with b_col:
            if st.button("\U0001f4ca Count ASINs & SKUs"):
                with st.spinner("Generating access token…"):
                    audit_tok2, aerr2 = get_oauth_token(
                        selected_store["domain"],
                        selected_store["client_id"],
                        selected_store["client_secret"])
                if not audit_tok2:
                    st.error(f"Auth failed: {aerr2}")
                else:
                    with st.spinner("Loading…"):
                        prods=fetch_all_products(selected_store["domain"], audit_tok2)
                        asins=build_asin_set(prods); skus=build_sku_set(prods)
                    st.info(f"**{len(prods)}** products | **{len(asins)}** ASINs | **{len(skus)}** SKUs")
        if "dupes" in st.session_state:
            dupes=st.session_state["dupes"]; total_p=st.session_state.get("total_prods","?")
            st.caption(f"Scanned **{total_p}** products")
            if not dupes:
                st.balloons(); st.success("\u2705 No duplicate SKUs — store is clean!")
            else:
                st.warning(f"\u26a0\ufe0f {len(dupes)} duplicate SKU(s)")
                rows = []

                for key, items in dupes.items():

                    for item in items:
                        rows.append({
                            "Duplicate Type": item["Type"],
                            "Duplicate Value": item["Value"],
                            **item
                        })
                df_d=pd.DataFrame(rows)
                st.dataframe(df_d)
                st.download_button("\U0001f4e5 Download CSV",df_d.to_csv(index=False).encode(),"duplicates.csv","text/csv")
                confirm = st.checkbox(
                    "I understand that duplicate products will be permanently deleted."
                )

                if confirm:

                    if st.button("🗑 Delete Duplicate Products"):

                        deleted = 0
                        failed = 0
                        kept = 0
                        deleted_products = set()
                        with st.spinner("Deleting duplicate products..."):

                            audit_token, err = get_oauth_token(
                                selected_store["domain"],
                                selected_store["client_id"],
                                selected_store["client_secret"]
                            )

                            if not audit_token:
                                st.error(err)

                            else:

                                for sku, items in dupes.items():

                                    # items.sort(key=lambda x: x["Created At"])
                                    items.sort(
                                        key=lambda x: (
                                            x.get("Created At") or "9999-12-31",
                                            x.get("Product ID")
                                        )
                                    )

                                    kept += 1

                                    for item in items[1:]:

                                        product_id = item["Product ID"]

                                        if product_id in deleted_products:
                                            continue

                                        ok = delete_product(
                                            selected_store["domain"],
                                            audit_token,
                                            product_id
                                        )

                                        if ok:
                                            deleted_products.add(product_id)
                                            deleted += 1
                                        else:
                                            failed += 1

                        st.success(
                            f"✅ Deleted: {deleted}\n\n"
                            f"✅ Kept: {kept}\n\n"
                            f"❌ Failed: {failed}"
                        )
                        st.session_state.pop("dupes", None)
                        st.rerun()

# TAB 3 — MANAGE STORES
with tab_stores_tab:
    st.subheader("\u2795 Add / Update a Store")
    st.info(
        "**How to get your credentials:**\n\n"
        "1. Shopify Admin → Settings → Apps and sales channels → Develop apps\n"
        "2. Create app → Configure Admin API scopes → enable **write_products, read_products, write_inventory**\n"
        "3. Install the app\n"
        "4. Go to **API credentials** tab\n"
        "5. Copy **Client ID** and **Client Secret** — paste both below\n\n"
        "The app will generate a fresh access token automatically each time you run it."
    )
    with st.form("store_form"):
        fc1,fc2=st.columns(2)
        f_name=fc1.text_input("Store Nickname")
        # RESTORED DOMAIN FIELD
        f_domain = fc2.text_input(
            "Domain (e.g. mystore.myshopify.com)"
        )
        fc3,fc4=st.columns(2)
        f_cid=fc3.text_input("Client ID", help="From Shopify: Settings → Apps → Develop apps → your app → API credentials")
        f_token=fc4.text_input("Client Secret", type="password", help="From the same page as Client ID")
        if st.form_submit_button("\U0001f4be Save Store"):
            if f_name and f_domain and f_cid and f_token:
                save_store(f_name,
                           f_domain.replace("https://","").replace("http://","").rstrip("/"),
                           f_cid, f_token)
                st.success(f"\u2705 Store **{f_name}** saved!")
                st.rerun()
            else:
                st.error("Nickname, Domain, Client ID, and Client Secret are all required.")
    st.divider()
    st.subheader("Saved Stores")
    stores_df=all_stores()
    if stores_df.empty:
        st.info("No stores saved yet.")
    else:
        for _,row in stores_df.iterrows():
            with st.expander(f"\U0001f3ea {row['store_name']} — {row['domain']}"):
                st.code(f"Domain : {row['domain']}", language=None)
                if row["client_id"]: st.code(f"Client ID: {row['client_id']}", language=None)
                st.caption("Access token hidden for security.")
                if st.button(f"\U0001f5d1\ufe0f Delete {row['store_name']}", key=f"del_{row['id']}"):
                    delete_store(int(row["id"])); st.rerun()
