"""Single entry point for the three Amazon / Shopify tools."""

import streamlit as st


# Do not call st.set_page_config here. Each existing tool owns its own page
# configuration, and Streamlit runs only the page selected in this navigation.
page = st.navigation(
    [
        st.Page("combined_pages/home.py", title="Home", icon="🏠", default=True),
        st.Page("Product_simplifier.py", title="Product Simplifier", icon="🔎"),
        st.Page("lister.py", title="Shopify Lister", icon="🛍️"),
        st.Page("testing.py", title="Price & Stock Sync", icon="🔄"),
    ],
    position="sidebar",
)

page.run()
