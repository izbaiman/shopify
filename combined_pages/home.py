# import streamlit as st


# st.set_page_config(
#     page_title="Amazon & Shopify Tools",
#     page_icon="🧰",
#     layout="wide",
# )

# st.title("🧰 Amazon & Shopify Tools")
# st.caption("Choose a tool from the sidebar to begin.")

# left, middle, right = st.columns(3)

# with left:
#     st.subheader("🔎 Product Simplifier")
#     st.write("Search Amazon products by country, city, price, rating, and sales.")

# with middle:
#     st.subheader("🛍️ Shopify Lister")
#     st.write("Upload a CSV and create Shopify product listings from Amazon data.")

# with right:
#     st.subheader("🔄 Price & Stock Sync")
#     st.write("Sync Amazon prices and out-of-stock status with Shopify.")

# st.info("Your original tool files remain separate. This dashboard only provides one shared entry point.")
import streamlit as st


st.set_page_config(page_title="Amazon Intelligence Pro", page_icon="🧰", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: radial-gradient(circle at 88% 4%, #ffe2a8 0, transparent 22%), radial-gradient(circle at 8% 11%, #caefff 0, transparent 25%), #f7f9fc; }
    .block-container { max-width: 1250px; padding-top: 2.2rem; }
    section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e8edf5; }
    section[data-testid="stSidebar"]::before { content: "🛍️  Amazon & Shopify Tools"; display: block; color: #172554; font-size: 1.25rem; font-weight: 800; padding: 1.5rem 1.2rem .9rem; }
    section[data-testid="stSidebar"] a { border-radius: 10px; margin: .15rem .55rem; padding: .55rem .7rem; }
    section[data-testid="stSidebar"] a:hover { background: #f1edff; color: #6845ee; }
    .sidebar-workspace { margin: 5.5rem .75rem 0; padding: 1rem; border: 1px solid #e5e7ff; border-radius: 16px; background: linear-gradient(145deg, #f7f4ff, #eef7ff); }
    .sidebar-workspace-title { color: #172554; font-size: .82rem; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; margin-bottom: .65rem; }
    .sidebar-status { color: #166534; font-size: .82rem; font-weight: 700; }
    .status-dot { display: inline-block; width: 8px; height: 8px; margin-right: .35rem; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 3px #bbf7d0; }
    .sidebar-workspace-copy { color: #64748b; font-size: .76rem; line-height: 1.45; margin-top: .6rem; }
    .sidebar-footer { color: #64748b; font-size: .74rem; line-height: 1.6; margin: 1.4rem .9rem 0; padding-top: 1rem; border-top: 1px solid #e8edf5; }
    .sidebar-footer span { color: #94a3b8; }
    .hero { position: relative; overflow: hidden; background: linear-gradient(118deg, #111827 0%, #1d3557 58%, #0b7285 100%); color: white; padding: 2.6rem 3rem; border-radius: 24px; box-shadow: 0 18px 42px rgba(15, 23, 42, .20); margin-bottom: 1.4rem; }
    .hero::after { content: "◌  ◈  ✦"; position: absolute; right: 3rem; bottom: 1.2rem; color: rgba(255,255,255,.18); font-size: 5rem; letter-spacing: .25rem; transform: rotate(-12deg); }
    .hero-kicker { color: #8ee7f4; font-size: .78rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    .hero h1 { margin: .45rem 0 .7rem; font-size: 2.65rem; line-height: 1.1; }
    .hero p { color: #dbeafe; font-size: 1.07rem; margin: 0; max-width: 700px; }
    .section-label { color: #475569; font-size: .82rem; font-weight: 800; letter-spacing: .11em; text-transform: uppercase; margin: 1.7rem 0 .6rem; }
    .tool-card { min-height: 275px; padding: 1.45rem; background: rgba(255,255,255,.96); border: 1px solid #e2e8f0; border-radius: 18px; box-shadow: 0 8px 25px rgba(15,23,42,.08); transition: transform .18s ease, box-shadow .18s ease; }
    .tool-card:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(15,23,42,.13); }
    .tool-icon { font-size: 2.25rem; }
    .tool-title { color: #13213b; font-size: 1.28rem; font-weight: 800; margin: .55rem 0 .35rem; }
    .tool-text { color: #64748b; font-size: .95rem; line-height: 1.55; min-height: 72px; }
    .pill { display: inline-block; color: #075985; background: #e0f2fe; font-size: .74rem; font-weight: 700; padding: .28rem .58rem; border-radius: 999px; margin-top: .55rem; }
    .stButton > button { border: 0; border-radius: 9px; font-weight: 750; background: linear-gradient(100deg, #f97316, #f59e0b); color: white; }
    .stButton > button:hover { color: white; border: 0; filter: brightness(1.04); }
    div[data-testid="stMetric"] { background: rgba(255,255,255,.84); border: 1px solid #e2e8f0; padding: .75rem 1rem; border-radius: 13px; }
    .journey { display: flex; gap: 1rem; align-items: stretch; background: rgba(255,255,255,.85); border: 1px solid #e2e8f0; border-radius: 18px; padding: 1rem; }
    .journey-step { flex: 1; padding: .85rem; border-radius: 12px; background: #fafbff; border: 1px solid #edf0f6; }
    .journey-no { color: #fff; background: #6d4aff; font-weight: 800; border-radius: 50%; padding: .22rem .5rem; display: inline-block; }
    .journey-title { color: #172554; font-weight: 800; margin-top: .45rem; }
    .journey-copy { color: #64748b; font-size: .87rem; line-height: 1.45; margin-top: .25rem; }
    .quick-card { min-height: 150px; padding: 1rem; border: 1px solid #e7ecf5; border-radius: 14px; background: rgba(255,255,255,.92); box-shadow: 0 5px 18px rgba(15,23,42,.05); }
    .quick-icon { float: left; width: 40px; height: 40px; line-height: 40px; text-align: center; margin-right: .7rem; border-radius: 12px; background: #f0eaff; font-size: 1.25rem; }
    .quick-value { color: #172554; font-size: 1.5rem; font-weight: 800; }
    .quick-label { color: #64748b; font-size: .79rem; }
    .quick-change { color: #16a34a; font-size: .73rem; font-weight: 700; margin-top: .65rem; }
    .spark { color: #7c5cff; font-size: 1.7rem; letter-spacing: -.36rem; white-space: nowrap; overflow: hidden; margin-top: .25rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Fill the lower sidebar area with useful workspace context instead of leaving
# an empty column below the navigation links.
st.sidebar.markdown(
    """
    <div class="sidebar-workspace">
        <div class="sidebar-workspace-title">Workspace status</div>
        <div class="sidebar-status"><span class="status-dot"></span> Ready to work</div>
        <div class="sidebar-workspace-copy">Choose a tool above to research products, list them, or sync your catalog.</div>
    </div>
    <div class="sidebar-footer">A&S Tools<br><span>Amazon + Shopify workspace</span></div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">Unified ecommerce workspace</div>
            <h1>Amazon & Shopify Tools</h1>
            <p>Research winning products, create Shopify listings, and keep prices and stock status in sync—all from one dashboard.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption("● Local workspace ready  •  Select any tool below to begin")

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Research", "Amazon", "Country & city based")
metric_2.metric("Listing", "CSV → Shopify", "ASIN duplicate checks")
metric_3.metric("Sync", "Price & Stock", "Batch processing")
metric_4.metric("Workspace", "3 Tools", "One dashboard")

st.markdown('<div class="section-label">Choose your workflow</div>', unsafe_allow_html=True)
col_1, col_2, col_3 = st.columns(3, gap="large")

with col_1:
    st.markdown('<div class="tool-card"><div class="tool-icon">🔎</div><div class="tool-title">Product Simplifier</div><div class="tool-text">Search Amazon products by marketplace, delivery city, price range, rating, and monthly sales. Export shortlisted products for listing.</div><span class="pill">Step 1 · Product research</span></div>', unsafe_allow_html=True)
    if st.button("Open Product Simplifier →", key="open_simplifier", use_container_width=True):
        st.switch_page("Product_Simplifier.py")

with col_2:
    st.markdown('<div class="tool-card"><div class="tool-icon">🛍️</div><div class="tool-title">Shopify Lister</div><div class="tool-text">Upload your product CSV, collect Amazon product information, check ASIN/SKU duplicates, and create Shopify listings.</div><span class="pill">Step 2 · Create listings</span></div>', unsafe_allow_html=True)
    if st.button("Open Shopify Lister →", key="open_lister", use_container_width=True):
        st.switch_page("lister_with_verifier.py")

with col_3:
    st.markdown('<div class="tool-card"><div class="tool-icon">🔄</div><div class="tool-title">Price & Stock Sync</div><div class="tool-text">Read Amazon pricing and availability, then update Shopify prices and configured out-of-stock inventory locations.</div><span class="pill">Step 3 · Maintain catalog</span></div>', unsafe_allow_html=True)
    if st.button("Open Price & Stock Sync →", key="open_sync", use_container_width=True):
        st.switch_page("price_update_testing2.py")

st.markdown('<div class="section-label">Demo Quick Stats <span style="font-weight:500;color:#94a3b8;letter-spacing:0;text-transform:none;">• visual preview</span></div>', unsafe_allow_html=True)
stat_1, stat_2, stat_3 = st.columns(3, gap="large")

with stat_1:
    st.markdown('<div class="quick-card"><div class="quick-icon">📦</div><div class="quick-value">1,245</div><div class="quick-label">Products Scanned</div><div class="quick-change">+12% vs yesterday</div><div class="spark">--------------------------------------------------------------------------------------------------</div></div>', unsafe_allow_html=True)
with stat_2:
    st.markdown('<div class="quick-card"><div class="quick-icon" style="background:#eaf9ed;">🛍️</div><div class="quick-value">842</div><div class="quick-label">Products Listed</div><div class="quick-change">+8% vs yesterday</div><div class="spark" style="color:#4caf50;">--------------------------------------------------------------------------------------------------</div></div>', unsafe_allow_html=True)
with stat_3:
    st.markdown('<div class="quick-card"><div class="quick-icon" style="background:#e8f1ff;">🔄</div><div class="quick-value">96.5%</div><div class="quick-label">Sync Success Rate</div><div class="quick-change">+2.3% vs yesterday</div><div class="spark" style="color:#3b82f6;">--------------------------------------------------------------------------------------------------</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Recommended order</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="journey">
        <div class="journey-step"><span class="journey-no">1</span><div class="journey-title">Search products</div><div class="journey-copy">Use Product Simplifier to find products that match your market criteria.</div></div>
        <div class="journey-step"><span class="journey-no">2</span><div class="journey-title">List on Shopify</div><div class="journey-copy">Upload approved CSV products while checking duplicate ASINs and SKUs.</div></div>
        <div class="journey-step"><span class="journey-no">3</span><div class="journey-title">Sync catalog</div><div class="journey-copy">Keep product pricing and unavailable inventory updated from Amazon.</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
