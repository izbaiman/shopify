import streamlit as st
import requests
import time
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shopify Duplicate SKU Finder", page_icon="🔍")

st.title("🔍 Shopify Duplicate SKU Finder")
st.markdown("Apne Shopify store se duplicate SKUs detect karein.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Shopify Credentials")
shop_url = st.sidebar.text_input("Store URL", placeholder="your-store.myshopify.com")
access_token = st.sidebar.text_input("Admin API Access Token", type="password", help="Enter Shpat...")
api_version = "2024-01"

# --- FUNCTIONS ---
def get_all_products(shop, token):
    products = []
    url = f"https://{shop}/admin/api/{api_version}/products.json?limit=250"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }

    # Progress Bar
    progress_text = "Fetching products from Shopify..."
    progress_bar = st.progress(0, text=progress_text)
    
    while url:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                products.extend(data.get('products', []))
                
                # Update progress visually
                progress_bar.empty()
                st.toast(f"Fetched {len(products)} products...")

                # Pagination
                link_header = response.headers.get('Link')
                if link_header and 'rel="next"' in link_header:
                    links = link_header.split(',')
                    for link in links:
                        if 'rel="next"' in link:
                            url = link.split(';')[0].strip('<> ')
                            break
                else:
                    url = None
            elif response.status_code == 429:
                st.warning("Rate limit hit, waiting 2 seconds...")
                time.sleep(2)
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            st.error(f"Connection Error: {e}")
            return None
            
    return products

def find_duplicate_skus(products):
    sku_map = {} 
    
    for product in products:
        title = product.get('title')
        variants = product.get('variants', [])
        
        for variant in variants:
            sku = variant.get('sku')
            if sku: 
                sku = sku.strip()
                if sku not in sku_map:
                    sku_map[sku] = []
                sku_map[sku].append({
                    "Product Name": title,
                    "Variant Title": variant.get('title'),
                    "Variant ID": variant.get('id'),
                    "Price": variant.get('price')
                })

    # Filter only duplicates and flatten for DataFrame
    duplicate_data = []
    for sku, items in sku_map.items():
        if len(items) > 1:
            for item in items:
                duplicate_data.append({
                    "SKU": sku,
                    **item
                })
    return duplicate_data

# --- MAIN LOGIC ---
if st.sidebar.button("Run Scan"):
    if not shop_url or not access_token:
        st.error("Please provide both Store URL and Access Token!")
    else:
        with st.spinner('Scanning your store... Please wait.'):
            all_products = get_all_products(shop_url, access_token)
            
            if all_products is not None:
                st.success(f"Successfully fetched {len(all_products)} products.")
                
                duplicates = find_duplicate_skus(all_products)
                
                if not duplicates:
                    st.balloons()
                    st.success("✅ No duplicate SKUs found!")
                else:
                    df = pd.DataFrame(duplicates)
                    st.warning(f"⚠️ Found {len(df['SKU'].unique())} duplicate SKUs!")
                    
                    # Display Results
                    st.dataframe(df, use_container_width=True)
                    
                    # Download Button
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name='duplicate_skus.csv',
                        mime='text/csv',
                    )

# --- INSTRUCTIONS ---
if not (shop_url and access_token):
    st.info("👈 Enter your Shopify Store URL and API Token in the sidebar to start.")
    st.image("https://cdn.shopify.com/s/files/1/0533/2089/files/shopify-admin-api-access-token.png", caption="How to get Access Token", width=400)