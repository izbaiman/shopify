# import requests
# import time

# SHOP_NAME = "thetailstore-2.myshopify.com"
# ACCESS_TOKEN = "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" 
# API_VERSION = "2024-01"

# def get_all_products(shop, token):
#     products = []
#     url = f"https://{shop}/admin/api/{API_VERSION}/products.json?limit=250"
    
#     headers = {
#         "X-Shopify-Access-Token": token,
#         "Content-Type": "application/json"
#     }

#     while url:
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             data = response.json()
#             products.extend(data.get('products', []))
            
#             # Handle Pagination (Shopify uses Link headers)
#             link_header = response.headers.get('Link')
#             if link_header and 'rel="next"' in link_header:
#                 # Extract the next page URL
#                 links = link_header.split(',')
#                 for link in links:
#                     if 'rel="next"' in link:
#                         url = link.split(';')[0].strip('<> ')
#                         break
#             else:
#                 url = None
#         elif response.status_code == 429:
#             print("Rate limit hit, sleeping for 2 seconds...")
#             time.sleep(2)
#         else:
#             print(f"Error: {response.status_code}, {response.text}")
#             break
            
#     return products

# def find_duplicate_skus(products):
#     sku_map = {} # { "SKU_CODE": [List of Product Titles] }
    
#     for product in products:
#         title = product.get('title')
#         variants = product.get('variants', [])
        
#         for variant in variants:
#             sku = variant.get('sku')
            
#             if sku: # Ignore empty SKUs
#                 sku = sku.strip()
#                 if sku not in sku_map:
#                     sku_map[sku] = []
#                 sku_map[sku].append({
#                     "product": title,
#                     "variant": variant.get('title'),
#                     "id": variant.get('id')
#                 })

#     # Filter only duplicates
#     duplicates = {sku: info for sku, info in sku_map.items() if len(info) > 1}
#     return duplicates

# # === EXECUTION ===
# print(f"🚀 Fetching products from {SHOP_NAME}...")
# all_products = get_all_products(SHOP_NAME, ACCESS_TOKEN)
# print(f"📦 Total products fetched: {len(all_products)}")

# duplicates = find_duplicate_skus(all_products)

# if not duplicates:
#     print("✅ No duplicate SKUs found!")
# else:
#     print(f"⚠️ Found {len(duplicates)} duplicate SKUs:\n")
#     for sku, items in duplicates.items():
#         print(f"SKU: {sku}")
#         for item in items:
#             print(f"  - {item['product']} ({item['variant']}) | ID: {item['id']}")
#         print("-" * 30)



import streamlit as st
import requests
import pandas as pd
import time

# --- Page Configuration ---
st.set_page_config(page_title="Shopify SKU Checker", page_icon="🔍")

st.title("🔍 Shopify Duplicate SKU Finder")
st.info("Apne Shopify store ke credentials niche enter karein aur 'Find Duplicates' par click karein.")

# --- User Inputs (Runtime) ---
col1, col2 = st.columns(2)

with col1:
    shop_input = st.text_input(
        "Shop Domain", 
        placeholder="your-store.myshopify.com",
        help="Example: thetailstore-2.myshopify.com"
    )

with col2:
    token_input = st.text_input(
        "Admin Access Token", 
        type="password", 
        placeholder="shpat_xxxxxxx...",
        help="Shopify Admin API Access Token yahan paste karein."
    )

# --- Backend Functions ---

def get_all_products(shop, token):
    # Clean the shop domain in case user pastes full URL
    shop = shop.replace("https://", "").replace("http://", "").split("/")[0]
    
    products = []
    api_version = "2024-01"
    url = f"https://{shop}/admin/api/{api_version}/products.json?limit=250"
    
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }

    try:
        # Initializing progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        while url:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                new_products = data.get('products', [])
                products.extend(new_products)
                
                status_text.text(f"Fetched {len(products)} products...")
                
                # Shopify Pagination
                link_header = response.headers.get('Link')
                if link_header and 'rel="next"' in link_header:
                    links = link_header.split(',')
                    for link in links:
                        if 'rel="next"' in link:
                            url = link.split(';')[0].strip('<> ')
                            break
                else:
                    url = None
            elif response.status_code == 401:
                st.error("❌ Invalid Access Token! Please check your credentials.")
                return None
            elif response.status_code == 404:
                st.error("❌ Shop Domain not found. Use 'your-store.myshopify.com' format.")
                return None
            elif response.status_code == 429:
                time.sleep(2) # Rate limit handling
            else:
                st.error(f"Error: {response.status_code}")
                return None
        
        progress_bar.empty()
        status_text.empty()
        return products

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

def find_duplicates(products):
    sku_map = {}
    for product in products:
        title = product.get('title')
        handle = product.get('handle') # For clickable link
        variants = product.get('variants', [])
        
        for variant in variants:
            sku = variant.get('sku')
            if sku and sku.strip():
                sku = sku.strip()
                if sku not in sku_map:
                    sku_map[sku] = []
                sku_map[sku].append({
                    "Product Name": title,
                    "Variant": variant.get('title'),
                    "Price": variant.get('price'),
                    "SKU": sku
                })
    
    # Filter only those that appear more than once
    duplicate_list = []
    for sku, items in sku_map.items():
        if len(items) > 1:
            duplicate_list.extend(items)
    
    return duplicate_list

# --- Main Logic ---

if st.button("🚀 Find Duplicates"):
    if not shop_input or not token_input:
        st.warning("⚠️ Please provide both Shop Domain and Access Token.")
    else:
        with st.spinner("Connecting to Shopify..."):
            all_products = get_all_products(shop_input, token_input)
        
        if all_products is not None:
            duplicates = find_duplicates(all_products)
            
            # Summary Metrics
            st.divider()
            m1, m2 = st.columns(2)
            m1.metric("Total Products", len(all_products))
            m2.metric("Duplicate Entries Found", len(duplicates))

            if duplicates:
                df = pd.DataFrame(duplicates)
                
                # Re-ordering columns for better view
                df = df[["SKU", "Product Name", "Variant", "Price"]]
                
                st.subheader("📋 Duplicate SKU List")
                st.dataframe(df, use_container_width=True)
                
                # Export to CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download List as CSV",
                    data=csv,
                    file_name=f"duplicates_{shop_input}.csv",
                    mime='text/csv'
                )
            else:
                st.success("🎉 No duplicate SKUs found! Your store is clean.")

# Sidebar Instructions
with st.sidebar:
    st.header("Instructions")
    st.markdown("""
    1. **Shop Domain:** `mystore.myshopify.com` format mein likhein.
    2. **Access Token:** Shopify Admin > Settings > App and sales channels > Develop Apps se generate karein.
    3. Is app ko use karne ke liye `read_products` permission honi chahiye.
    """)