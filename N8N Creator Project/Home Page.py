from io import BytesIO
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets as secure_secrets
import sqlite3

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="Creator Automation Portal",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


GENERAL_WORKFLOWS = [
    {
        "title": "Creator Data",
        "description": "Collect and organize creator information for your campaigns.",
        "icon": "👥",
        "accent": "violet",
        "url": None,
    },
    {
        "title": "Google Drive YouTube Upload",
        "description": "Publish YouTube content directly from your Google Drive assets.",
        "icon": "☁️",
        "accent": "blue",
        "url": None,
    },
    {
        "title": "Local Drive YouTube Upload",
        "description": "Upload local videos and prepare them for YouTube publishing.",
        "icon": "▶️",
        "accent": "rose",
        "url": None,
    },
    {
        "title": "Add Group to Existing Campaign",
        "description": "Create a new ad group inside one of your existing campaigns.",
        "icon": "➕",
        "accent": "amber",
        "url": None,
    },
    {
        "title": "Create New Campaign",
        "description": "Launch a complete new campaign using the guided automation form.",
        "icon": "🚀",
        "accent": "green",
        "url": "https://topedgetechnologies.app.n8n.cloud/form/general-app-campaign-creator",
    },
]


GAMES_WORKFLOWS = [
    {
        "title": item["title"],
        "description": item["description"].replace("campaign", "game campaign"),
        "icon": item["icon"],
        "accent": item["accent"],
        "url": None,
    }
    for item in GENERAL_WORKFLOWS
]


SHEETS = {
    "General Apps": {
        "id": "12TFHI5PoInvzmQ-EHodennayIk9CRM7zD6z35C5iZfY",
        "view_url": "https://docs.google.com/spreadsheets/d/12TFHI5PoInvzmQ-EHodennayIk9CRM7zD6z35C5iZfY/edit?usp=sharing",
    },
    "Games Apps": {
        "id": "1gXnNUghEKN5DTEdgzORmaA9UAk4A1RH__oVFZ_B5eCM",
        "view_url": "https://docs.google.com/spreadsheets/d/1gXnNUghEKN5DTEdgzORmaA9UAk4A1RH__oVFZ_B5eCM/edit?usp=sharing",
    },
}


AUTH_DB = Path(__file__).resolve().with_name("creator_portal_auth.db")
PBKDF2_ROUNDS = 200_000


def hash_value(value, salt):
    """Return a salted PBKDF2 hash for a password or recovery key."""
    return hashlib.pbkdf2_hmac(
        "sha256", value.encode("utf-8"), salt, PBKDF2_ROUNDS
    ).hex()


def password_is_valid(password):
    return (
        len(password) >= 10
        and any(character.isalpha() for character in password)
        and any(character.isdigit() for character in password)
    )


def init_auth_db():
    """Create the local user database and seed users from Streamlit secrets."""
    try:
        configured_users = st.secrets["users"]
    except Exception as error:
        raise RuntimeError(
            "Add [users.<username>] credentials to .streamlit/secrets.toml."
        ) from error

    with sqlite3.connect(AUTH_DB) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS portal_users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt BLOB NOT NULL,
                recovery_hash TEXT NOT NULL,
                recovery_salt BLOB NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for username in configured_users:
            account = configured_users[username]
            password = str(account.get("password", ""))
            recovery_key = str(account.get("recovery_key", ""))
            if not password or not recovery_key:
                raise RuntimeError(
                    f"Password or recovery_key is missing for user '{username}'."
                )
            exists = connection.execute(
                "SELECT 1 FROM portal_users WHERE username = ?", (username,)
            ).fetchone()
            if exists:
                continue
            password_salt = secure_secrets.token_bytes(16)
            recovery_salt = secure_secrets.token_bytes(16)
            connection.execute(
                """
                INSERT INTO portal_users (
                    username, display_name, password_hash, password_salt,
                    recovery_hash, recovery_salt
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    str(account.get("name", username)),
                    hash_value(password, password_salt),
                    password_salt,
                    hash_value(recovery_key, recovery_salt),
                    recovery_salt,
                ),
            )


def authenticate_user(username, password):
    with sqlite3.connect(AUTH_DB) as connection:
        account = connection.execute(
            """
            SELECT username, display_name, password_hash, password_salt
            FROM portal_users WHERE username = ?
            """,
            (username.strip(),),
        ).fetchone()
    if not account:
        return None
    supplied_hash = hash_value(password, account[3])
    return account if hmac.compare_digest(supplied_hash, account[2]) else None


def find_user_by_recovery_key(recovery_key):
    with sqlite3.connect(AUTH_DB) as connection:
        accounts = connection.execute(
            """
            SELECT username, display_name, recovery_hash, recovery_salt
            FROM portal_users
            """
        ).fetchall()
    for account in accounts:
        supplied_hash = hash_value(recovery_key, account[3])
        if hmac.compare_digest(supplied_hash, account[2]):
            return account
    return None


def update_user_password(username, new_password):
    """Update both the readable Streamlit secret and the hashed database value."""
    secrets_path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    secrets_text = secrets_path.read_text(encoding="utf-8")
    section_pattern = re.compile(
        rf"(^\[users\.{re.escape(username)}\]\s*$)(.*?)(?=^\[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    section_match = section_pattern.search(secrets_text)
    if not section_match:
        raise RuntimeError(f"User '{username}' was not found in secrets.toml.")

    section_body = section_match.group(2)
    new_password_line = f"password = {json.dumps(new_password, ensure_ascii=False)}"
    updated_body, replacements = re.subn(
        r"^password\s*=.*$",
        new_password_line,
        section_body,
        count=1,
        flags=re.MULTILINE,
    )
    if replacements != 1:
        raise RuntimeError(f"Password field for '{username}' is missing in secrets.toml.")

    updated_secrets = (
        secrets_text[: section_match.start(2)]
        + updated_body
        + secrets_text[section_match.end(2) :]
    )
    temporary_path = secrets_path.with_suffix(".toml.tmp")
    temporary_path.write_text(updated_secrets, encoding="utf-8")
    temporary_path.replace(secrets_path)

    salt = secure_secrets.token_bytes(16)
    with sqlite3.connect(AUTH_DB) as connection:
        connection.execute(
            """
            UPDATE portal_users
            SET password_hash = ?, password_salt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
            """,
            (hash_value(new_password, salt), salt, username),
        )


@st.cache_data(ttl=300, show_spinner=False)
def load_google_sheet(spreadsheet_id):
    """Load the first worksheet of a link-shared Google Sheet."""
    export_url = (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        "/export?format=csv"
    )
    response = requests.get(export_url, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" in content_type:
        raise PermissionError(
            "Google Sheet is not publicly readable. Set General access to "
            "'Anyone with the link' as Viewer."
        )

    dataframe = pd.read_csv(BytesIO(response.content))
    dataframe = dataframe.dropna(axis=0, how="all").dropna(axis=1, how="all")
    return dataframe


st.markdown(
    """
    <style>
    :root {
        --ink: #17233f;
        --muted: #64748b;
        --line: #e8edf5;
        --brand: #6557e8;
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 2%, rgba(215, 240, 255, .78), transparent 25%),
            radial-gradient(circle at 94% 7%, rgba(235, 225, 255, .72), transparent 26%),
            #f9fbff;
        color: var(--ink);
    }

    header[data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1180px; padding-top: 1.4rem; padding-bottom: 4rem; }

    .portal-nav {
        display: flex; align-items: center; justify-content: space-between;
        padding: .8rem 1rem; margin-bottom: 1.2rem;
        background: rgba(255,255,255,.78); border: 1px solid rgba(225,231,242,.9);
        border-radius: 18px; box-shadow: 0 8px 30px rgba(40,56,94,.06);
        backdrop-filter: blur(12px);
    }
    .brand { display: flex; align-items: center; gap: .7rem; color: var(--ink); font-weight: 850; }
    .brand-mark {
        width: 38px; height: 38px; display: grid; place-items: center;
        border-radius: 12px; color: white; font-size: 1.15rem;
        background: linear-gradient(135deg, #6c5ce7, #57a7ff);
        box-shadow: 0 8px 18px rgba(101,87,232,.25);
    }
    .nav-status { color: #397a58; font-size: .78rem; font-weight: 750; }
    .nav-status::before {
        content: ""; display: inline-block; width: 8px; height: 8px;
        margin-right: .45rem; border-radius: 50%; background: #43b978;
        box-shadow: 0 0 0 4px rgba(67,185,120,.12);
    }

    .hero {
        position: relative; overflow: hidden; padding: 3.2rem 3.2rem 2.9rem;
        border: 1px solid #e5eaf4; border-radius: 28px;
        background: linear-gradient(118deg, rgba(255,255,255,.98), rgba(248,246,255,.95) 58%, rgba(237,248,255,.96));
        box-shadow: 0 20px 55px rgba(42,53,90,.10);
    }
    .hero::after {
        content: "✦"; position: absolute; right: 5%; top: -35%;
        color: rgba(101,87,232,.08); font-size: 19rem; transform: rotate(15deg);
    }
    .eyebrow {
        display: inline-block; padding: .38rem .7rem; border-radius: 999px;
        color: #5b4dcc; background: #eeebff; font-size: .72rem;
        font-weight: 850; letter-spacing: .1em; text-transform: uppercase;
    }
    .hero h1 { max-width: 720px; margin: 1rem 0 .8rem; font-size: 3.15rem; line-height: 1.07; color: var(--ink); letter-spacing: -.045em; }
    .hero p { max-width: 710px; margin: 0; color: var(--muted); font-size: 1.04rem; line-height: 1.7; }
    .hero-meta { display: flex; gap: 1.2rem; margin-top: 1.5rem; color: #52617a; font-size: .8rem; font-weight: 700; }

    .section-heading { margin: 2rem 0 .15rem; color: var(--ink); font-size: 1.65rem; font-weight: 850; }
    .section-copy { color: var(--muted); font-size: .92rem; margin-bottom: .8rem; }

    div[role="radiogroup"] { gap: .55rem; }
    div[role="radiogroup"] label {
        padding: .55rem .9rem; border: 1px solid #e1e7f0; border-radius: 12px;
        background: rgba(255,255,255,.85); transition: all .18s ease;
    }
    div[role="radiogroup"] label:hover { border-color: #b8b0ff; transform: translateY(-1px); }

    .workflow-card {
        min-height: 220px; margin-top: .8rem; padding: 1.35rem;
        border: 1px solid var(--line); border-radius: 20px; background: rgba(255,255,255,.95);
        box-shadow: 0 10px 30px rgba(29,45,78,.065);
        transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
    }
    .workflow-card:hover { transform: translateY(-4px); box-shadow: 0 18px 38px rgba(29,45,78,.11); border-color: #d7dced; }
    .workflow-icon { width: 48px; height: 48px; display: grid; place-items: center; border-radius: 14px; font-size: 1.35rem; margin-bottom: 1.05rem; }
    .violet { background: #eeeaff; } .blue { background: #e7f3ff; }
    .rose { background: #ffedf2; } .amber { background: #fff3da; } .green { background: #e8f8ed; }
    .workflow-title { color: var(--ink); font-size: 1.03rem; font-weight: 850; line-height: 1.3; }
    .workflow-copy { min-height: 62px; margin-top: .55rem; color: var(--muted); font-size: .82rem; line-height: 1.55; }
    .ready-pill, .soon-pill {
        display: inline-block; margin-top: .75rem; padding: .3rem .58rem;
        border-radius: 999px; font-size: .68rem; font-weight: 850;
    }
    .ready-pill { color: #26764b; background: #e8f8ee; }
    .soon-pill { color: #7a6b3a; background: #fff6d9; }

    .stLinkButton a {
        width: 100%; margin-top: -.15rem; border: 0; border-radius: 11px;
        color: white !important; background: linear-gradient(100deg, #6557e8, #718df4);
        font-weight: 800; box-shadow: 0 8px 18px rgba(101,87,232,.20);
    }
    .stLinkButton a:hover { filter: brightness(1.04); transform: translateY(-1px); }
    .stButton button:disabled {
        width: 100%; margin-top: -.15rem; border: 1px solid #e4e8f0;
        border-radius: 11px; color: #9aa4b4; background: #f5f7fa;
    }

    .how-it-works {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem;
        margin-top: 2rem; padding: 1.1rem; border: 1px solid var(--line);
        border-radius: 20px; background: rgba(255,255,255,.78);
    }
    .step { padding: .85rem; }
    .step-no { color: #6557e8; font-size: .72rem; font-weight: 900; letter-spacing: .1em; }
    .step-title { margin-top: .3rem; color: var(--ink); font-size: .9rem; font-weight: 850; }
    .step-copy { margin-top: .25rem; color: var(--muted); font-size: .76rem; line-height: 1.5; }
    .footer { margin-top: 2.2rem; padding-top: 1.2rem; border-top: 1px solid var(--line); color: #94a3b8; text-align: center; font-size: .75rem; }
    .login-wrap {
        max-width: 470px; margin: 6vh auto 1.2rem; padding: 2rem 2rem 1.5rem;
        border: 1px solid var(--line); border-radius: 24px; background: rgba(255,255,255,.94);
        box-shadow: 0 22px 55px rgba(42,53,90,.11); text-align: center;
    }
    .login-mark {
        width: 54px; height: 54px; display: grid; place-items: center; margin: 0 auto 1rem;
        border-radius: 17px; color: white; font-size: 1.25rem; font-weight: 900;
        background: linear-gradient(135deg, #6c5ce7, #57a7ff);
    }
    .login-title { color: var(--ink); font-size: 1.55rem; font-weight: 900; }
    .login-copy { max-width: 360px; margin: .55rem auto 0; color: var(--muted); font-size: .84rem; line-height: 1.55; }
    div[data-testid="stForm"] {
        max-width: 470px; margin: 0 auto; padding: 1.4rem 1.7rem;
        border: 1px solid var(--line); border-radius: 20px; background: rgba(255,255,255,.94);
        box-shadow: 0 15px 38px rgba(42,53,90,.07);
    }
    .data-heading { margin-top: 2.1rem; color: var(--ink); font-size: 1.65rem; font-weight: 850; }
    .data-note {
        margin: .65rem 0 1rem; padding: .8rem 1rem; border: 1px solid #dce8f7;
        border-radius: 12px; color: #52617a; background: rgba(240,247,255,.78);
        font-size: .79rem;
    }
    div[data-testid="stDataFrame"] {
        overflow: hidden; border: 1px solid var(--line); border-radius: 16px;
        box-shadow: 0 10px 30px rgba(29,45,78,.055);
    }

    @media (max-width: 760px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .hero { padding: 2.2rem 1.5rem; } .hero h1 { font-size: 2.25rem; }
        .hero-meta { flex-direction: column; gap: .35rem; }
        .how-it-works { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def require_login():
    """Stop the page before private portal data loads unless a user is signed in."""
    if st.session_state.get("portal_authenticated"):
        return

    st.markdown(
        """
        <div class="login-wrap">
            <div class="login-mark">A</div>
            <div class="login-title">Creator Portal Login</div>
            <div class="login-copy">Sign in with your authorized company account to access creator data and campaign automations.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("portal_login", clear_on_submit=False):
        username = st.text_input("Username", autocomplete="username")
        password = st.text_input(
            "Password", type="password", autocomplete="current-password"
        )
        submitted = st.form_submit_button(
            "Sign in", type="primary", width="stretch"
        )

    if submitted:
        account = authenticate_user(username, password)
        if account:
            st.session_state["portal_authenticated"] = True
            st.session_state["portal_username"] = account[0]
            st.session_state["portal_display_name"] = account[1]
            st.rerun()
        else:
            st.error("Incorrect username or password.")

    forgot_left, forgot_column, forgot_right = st.columns([1, 1.25, 1])
    with forgot_column:
        forgot_label = (
            "Back to sign in"
            if st.session_state.get("show_account_recovery")
            else "Forgot username/password?"
        )
        if st.button(
            forgot_label,
            key="toggle_account_recovery",
            type="tertiary",
            width="stretch",
        ):
            st.session_state["show_account_recovery"] = not st.session_state.get(
                "show_account_recovery", False
            )
            st.rerun()

    if st.session_state.get("show_account_recovery"):
        # st.caption(
        #     "Enter the private recovery key supplied by the portal administrator. "
        #     "Your username will be shown after the password is reset."
        # )
        with st.form("portal_recovery", clear_on_submit=True):
            recovery_key = st.text_input("Recovery key", type="password")
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input("Confirm new password", type="password")
            recover_submitted = st.form_submit_button(
                "Recover account", type="primary", width="stretch"
            )

        if recover_submitted:
            account = find_user_by_recovery_key(recovery_key)
            if not account:
                st.error("Recovery key is incorrect.")
            elif new_password != confirm_password:
                st.error("New passwords do not match.")
            elif not password_is_valid(new_password):
                st.error(
                    "Password must contain at least 10 characters, one letter and one number."
                )
            else:
                try:
                    update_user_password(account[0], new_password)
                except Exception as error:
                    st.error(f"Password could not be saved: {error}")
                else:
                    st.success(
                        f"Password changed. Your username is: {account[0]}. "
                        "The database and secrets.toml have both been updated."
                    )

    st.stop()


try:
    init_auth_db()
except Exception as error:
    st.error(f"Authentication setup error: {error}")
    st.stop()

require_login()

account_space, account_column = st.columns([8, 2])
with account_column:
    if st.button("Log out", width="stretch"):
        st.session_state.pop("portal_authenticated", None)
        st.session_state.pop("portal_username", None)
        st.session_state.pop("portal_display_name", None)
        st.rerun()


st.markdown(
    f"""
    <div class="portal-nav">
        <div class="brand"><div class="brand-mark">A</div>Apps Creator Portal</div>
        <div class="nav-status">Signed in · {st.session_state['portal_display_name']}</div>
    </div>
    <section class="hero">
        <span class="eyebrow">Creator automation hub</span>
        <h1>Build, upload and launch campaigns—faster.</h1>
        <p>A single, easy-to-use workspace for creator data, YouTube uploads and campaign creation across General Apps and Games Apps.</p>
        <div class="hero-meta"><span>✓ Guided workflows</span><span>✓ Secure n8n forms</span><span>✓ No technical setup required</span></div>
    </section>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="section-heading">Choose your app type</div>', unsafe_allow_html=True)
st.markdown('<div class="section-copy">Select the category you are working with to see its available automations.</div>', unsafe_allow_html=True)

app_type = st.radio(
    "App type",
    ["General Apps", "Games Apps"],
    horizontal=True,
    label_visibility="collapsed",
)

workflows = GENERAL_WORKFLOWS if app_type == "General Apps" else GAMES_WORKFLOWS
st.markdown(f'<div class="section-heading">{app_type} workflows</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-copy">Open an available automation or check back as the remaining workflows are connected.</div>',
    unsafe_allow_html=True,
)


def render_workflow(item):
    status = '<span class="ready-pill">Ready to use</span>' if item["url"] else '<span class="soon-pill">Link coming soon</span>'
    st.markdown(
        f"""
        <div class="workflow-card">
            <div class="workflow-icon {item['accent']}">{item['icon']}</div>
            <div class="workflow-title">{item['title']}</div>
            <div class="workflow-copy">{item['description']}</div>
            {status}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if item["url"]:
        st.link_button("Open automation  →", item["url"], width="stretch")
    else:
        st.button("Coming soon", key=f"{app_type}-{item['title']}", disabled=True, width="stretch")


first_row = st.columns(3, gap="large")
for column, workflow in zip(first_row, workflows[:3]):
    with column:
        render_workflow(workflow)

second_row = st.columns(3, gap="large")
for column, workflow in zip(second_row, workflows[3:]):
    with column:
        render_workflow(workflow)


st.markdown(
    f'<div class="data-heading">{app_type} creator data</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-copy">Live data from the connected Google Sheet. Use search to quickly find any creator, campaign or record.</div>',
    unsafe_allow_html=True,
)

sheet_config = SHEETS[app_type]
data_action, source_action = st.columns([4, 1])
with data_action:
    search_text = st.text_input(
        "Search sheet data",
        placeholder="Search across all columns...",
        key=f"sheet-search-{app_type}",
    )
with source_action:
    st.write("")
    st.link_button(
        "Open Google Sheet",
        sheet_config["view_url"],
        width="stretch",
    )

try:
    with st.spinner(f"Loading {app_type} data..."):
        sheet_data = load_google_sheet(sheet_config["id"])

    if search_text.strip():
        search_mask = sheet_data.astype(str).apply(
            lambda column: column.str.contains(
                search_text.strip(), case=False, na=False, regex=False
            )
        ).any(axis=1)
        visible_data = sheet_data.loc[search_mask]
    else:
        visible_data = sheet_data

    stat_1, stat_2, stat_3 = st.columns(3)
    stat_1.metric("Total records", f"{len(sheet_data):,}")
    stat_2.metric("Visible records", f"{len(visible_data):,}")
    stat_3.metric("Data columns", f"{len(sheet_data.columns):,}")

    if visible_data.empty:
        st.info("No records match your search.")
    else:
        st.dataframe(
            visible_data,
            width="stretch",
            hide_index=True,
            height=min(620, 90 + (len(visible_data) * 35)),
        )

    st.markdown(
        '<div class="data-note">Google Sheet data is cached for 5 minutes for faster loading. Changes made in the sheet will appear automatically after the cache refreshes.</div>',
        unsafe_allow_html=True,
    )
except Exception as error:
    st.error(f"Could not load the {app_type} Google Sheet: {error}")
    st.info(
        "In Google Sheets, open Share → General access → Anyone with the link → Viewer."
    )


st.markdown(
    """
    <div class="how-it-works">
        <div class="step"><div class="step-no">STEP 01</div><div class="step-title">Choose a workflow</div><div class="step-copy">Select General Apps or Games Apps, then choose the task you want to complete.</div></div>
        <div class="step"><div class="step-no">STEP 02</div><div class="step-title">Complete the form</div><div class="step-copy">Enter the requested campaign or content information in the guided n8n form.</div></div>
        <div class="step"><div class="step-no">STEP 03</div><div class="step-title">Run the automation</div><div class="step-copy">Submit once and let the connected workflow process the request for you.</div></div>
    </div>
    <div class="footer">Top Edge Technologies · Creator Automation Portal</div>
    """,
    unsafe_allow_html=True,
)
