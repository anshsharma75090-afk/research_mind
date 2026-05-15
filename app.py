
"""
ResearchMind — Modern Chat UI
Run: streamlit run chat_app.py
Requires: pipeline.py in the same folder
"""

import contextlib
import html
import io
import re
import time
import uuid

import streamlit as st

from pipeline import run_research_pipeline


# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchMind",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── helpers ──────────────────────────────────────────────────────────────────
def run_pipeline(topic: str):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        state = run_research_pipeline(topic)
    return state, buf.getvalue()


def extract_score(feedback: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", feedback)
    if m:
        return m.group(1) + "/10"
    m = re.search(r"score[:\s]+(\d+(?:\.\d+)?)", feedback, re.I)
    return (m.group(1) + "/10") if m else "—"


def parse_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\]\"']+", text)
    return [u.rstrip(".,") for u in dict.fromkeys(urls)][:6]

def linkify_text(text: str) -> str:
    parts = []
    last_index = 0
    for match in re.finditer(r"https?://[^\s)>\]\\\"']+", text):
        url = match.group(0).rstrip(".,")
        end = match.end()
        trail = match.group(0)[len(url):]
        parts.append(html.escape(text[last_index:match.start()]))
        parts.append(
            f'<a href="{html.escape(url)}" target="_blank" rel="noreferrer noopener">'
            f'{html.escape(url)}</a>'
        )
        parts.append(html.escape(trail))
        last_index = end
    parts.append(html.escape(text[last_index:]))
    return "".join(parts)

def ts() -> str:
    return time.strftime("%I:%M %p")


# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">

    <style>
    /* ── tokens ── */
    :root {
        --bg:   #09090f;
        --s1:   #0e0f1a;
        --s2:   #14151f;
        --s3:   #1a1b28;
        --b1:   rgba(255,255,255,0.06);
        --b2:   rgba(255,255,255,0.11);
        --ink:  #ecedf5;
        --ink2: #8b8fa8;
        --ink3: #4e5169;
        --a:    #7c6aff;
        --a2:   #a897ff;
        --g:    #3ffcb8;
        --r:    #ff5757;
        --gold: #f0c060;
        --rad:  10px;
    }

    html, body, .stApp {
        background: var(--bg) !important;
        color: var(--ink) !important;
        font-family: 'Geist', sans-serif !important;
    }

    /* hide streamlit chrome */
    [data-testid="stSidebar"] > div:first-child { background: var(--s1) !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    footer { display: none !important; }
    #MainMenu { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }

    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* ── sidebar ── */
    [data-testid="stSidebar"] {
        border-right: 1px solid var(--b1) !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 0 !important;
    }

    /* ── section labels ── */
    .sb-label {
        font-family: 'Geist Mono', monospace;
        font-size: 10px;
        letter-spacing: .12em;
        text-transform: uppercase;
        color: var(--ink3);
        padding: 12px 16px 4px;
    }

    /* ── history items ── */
    .hist-item {
        display: flex;
        align-items: center;
        gap: 9px;
        padding: 9px 14px;
        margin: 1px 6px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 12.5px;
        color: var(--ink2);
        transition: background .12s, color .12s;
    }
    .hist-item:hover { background: var(--s2); color: var(--ink); }
    .hist-item.active { background: rgba(124,106,255,.12); color: var(--a2); }
    .hist-title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .hist-meta { font-size: 10px; color: var(--ink3); font-family: 'Geist Mono', monospace; }

    /* ── new chat btn ── */
    .new-btn {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 12px 10px 8px;
        padding: 9px 12px;
        border-radius: 8px;
        border: 1px solid var(--b2);
        background: transparent;
        color: var(--ink2);
        font-size: 12.5px;
        font-family: 'Geist', sans-serif;
        cursor: pointer;
        width: calc(100% - 20px);
        transition: all .15s;
    }
    .new-btn:hover { background: var(--s2); color: var(--ink); border-color: var(--a); }

    /* ── user card ── */
    .user-card {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 14px;
        border-top: 1px solid var(--b1);
        cursor: pointer;
    }
    .avatar {
        width: 30px; height: 30px;
        border-radius: 99px;
        background: linear-gradient(135deg,var(--a),var(--g));
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 600; color: #0a0a0f; flex-shrink: 0;
    }
    .user-name { font-size: 12.5px; font-weight: 500; }
    .user-role { font-size: 10.5px; color: var(--ink3); }

    /* ── topbar ── */
    .topbar {
        height: 52px;
        border-bottom: 1px solid var(--b1);
        display: flex;
        align-items: center;
        padding: 0 20px;
        gap: 10px;
        background: var(--s1);
    }
    .topbar-title { flex: 1; font-size: 13.5px; font-weight: 500; }
    .model-pill {
        display: flex;
        align-items: center;
        gap: 6px;
        background: var(--s2);
        border: 1px solid var(--b1);
        border-radius: 7px;
        padding: 5px 10px;
        font-size: 11.5px;
        color: var(--ink2);
    }
    .tb-icon {
        width: 30px; height: 30px;
        border-radius: 7px;
        border: 1px solid var(--b1);
        background: transparent;
        color: var(--ink2);
        display: flex; align-items: center; justify-content: center;
        font-size: 14px;
        cursor: pointer;
        transition: background .12s, color .12s;
    }
    .tb-icon:hover { background: var(--s2); color: var(--ink); }

    /* ── message bubbles ── */
    .msg-wrap { max-width: 740px; margin: 0 auto; padding: 28px 24px; }

    .msg { display: flex; gap: 12px; margin-bottom: 22px; }
    .msg.user { flex-direction: row-reverse; }

    .msg-av {
        width: 32px; height: 32px; border-radius: 99px; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 600; margin-top: 2px;
    }
    .msg.user  .msg-av { background: linear-gradient(135deg,var(--a),#b06aff); color: #fff; }
    .msg.ai    .msg-av { background: var(--s3); border: 1px solid var(--b2); color: var(--a2); font-size: 14px; }

    .msg-bubble { min-width: 0; }
    .msg.user   .msg-bubble { display: flex; flex-direction: column; align-items: flex-end; max-width: 82%; }
    .msg.ai     .msg-bubble { flex: 1; }

    .msg-text {
        font-size: 13.5px; line-height: 1.75;
        padding: 11px 15px; border-radius: 12px;
    }
    .msg.user .msg-text {
        background: rgba(124,106,255,.17);
        border: 1px solid rgba(124,106,255,.22);
        border-bottom-right-radius: 4px;
        color: var(--ink);
    }
    .msg.ai .msg-text {
        background: var(--s2);
        border: 1px solid var(--b1);
        border-bottom-left-radius: 4px;
        color: #d8daea;
    }

    .msg-meta {
        font-size: 10.5px; color: var(--ink3); margin-top: 5px;
        display: flex; align-items: center; gap: 6px;
        font-family: 'Geist Mono', monospace;
    }
    .msg.user .msg-meta { justify-content: flex-end; }

    /* ── source cards ── */
    .sources { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin-top: 10px; }
    .src-card {
        background: var(--s3); border: 1px solid var(--b1);
        border-radius: 8px; padding: 9px 11px;
        font-size: 11.5px; display: flex; gap: 8px; align-items: flex-start;
    }
    .src-icon {
        width: 22px; height: 22px; border-radius: 5px;
        background: rgba(124,106,255,.14);
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; flex-shrink: 0;
    }
    .src-title { font-size: 11.5px; font-weight: 500; color: var(--ink); margin-bottom: 2px; }
    .src-url   { font-size: 10px; color: var(--ink3); }
    .src-url a { color: var(--ink3); text-decoration: none; }
    .src-url a:hover { color: var(--a); }
    .full-report-text a { color: var(--a); text-decoration: underline; }

    /* ── tags ── */
    .tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
    .tag {
        font-size: 10.5px; padding: 3px 9px; border-radius: 99px;
        background: rgba(124,106,255,.1); border: 1px solid rgba(124,106,255,.2);
        color: var(--a2); font-family: 'Geist Mono', monospace;
    }

    /* ── score badge ── */
    .score-badge {
        display: inline-flex; align-items: center; justify-content: center;
        padding: 3px 10px; border-radius: 99px;
        background: rgba(63,252,184,.1); border: 1px solid rgba(63,252,184,.25);
        color: var(--g); font-family: 'Geist Mono', monospace;
        font-size: 11px; font-weight: 600;
    }

    /* ── metrics row ── */
    .metrics { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
    .metric-pill {
        background: var(--s3); border: 1px solid var(--b1); border-radius: 8px;
        padding: 7px 12px; font-size: 11.5px;
    }
    .metric-pill .ml { color: var(--ink3); font-size: 10px; font-family:'Geist Mono',monospace; }
    .metric-pill .mv { color: var(--ink); font-weight: 500; font-size: 13.5px; }

    /* ── typing ── */
    .typing { display: flex; align-items: center; gap: 5px; padding: 11px 15px; width: fit-content; }
    .dot { width: 6px; height: 6px; border-radius: 99px; background: var(--ink3); }

    /* ── input bar ── */
    .stTextInput > div > div > input {
        background: var(--s2) !important;
        border: 1px solid var(--b2) !important;
        border-radius: 10px !important;
        color: var(--ink) !important;
        font-family: 'Geist', sans-serif !important;
        font-size: 13.5px !important;
        min-height: 48px !important;
        padding: 0 14px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--a) !important;
        box-shadow: 0 0 0 3px rgba(124,106,255,.14) !important;
    }
    .stTextInput label { display: none !important; }

    /* ── buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, var(--a), #9b89ff) !important;
        border: none !important;
        color: #fff !important;
        font-family: 'Geist', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 9px !important;
        min-height: 44px !important;
        box-shadow: 0 6px 20px rgba(124,106,255,.3) !important;
        transition: opacity .15s !important;
    }
    .stButton > button:hover { opacity: .88 !important; }

    .stButton.secondary > button {
        background: var(--s2) !important;
        border: 1px solid var(--b2) !important;
        color: var(--ink2) !important;
        box-shadow: none !important;
    }

    /* ── checkboxes / toggles ── */
    .stCheckbox label { color: var(--ink2) !important; font-size: 12.5px !important; }
    .stCheckbox [data-testid="stCheckbox"] { gap: 7px !important; }

    /* ── selectbox ── */
    .stSelectbox > div > div {
        background: var(--s2) !important;
        border: 1px solid var(--b1) !important;
        border-radius: 8px !important;
        color: var(--ink) !important;
    }
    .stSelectbox label { color: var(--ink3) !important; font-size: 10.5px !important; font-family: 'Geist Mono', monospace !important; letter-spacing: .08em !important; text-transform: uppercase !important; }

    /* ── info / warning ── */
    .stAlert { border-radius: 9px !important; }

    /* ── status bar ── */
    .full-report-card {
        background: rgba(16,18,35,0.98);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 24px 26px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.28);
        margin-bottom: 16px;
    }

    .full-report-heading {
        font-size: 30px;
        font-weight: 700;
        color: var(--a);
        letter-spacing: 0.01em;
        margin-bottom: 16px;
    }

    .full-report-text {
        font-size: 20px;
        line-height: 1.85;
        color: #eef0ff;
        white-space: pre-wrap;
    }

    .full-report-text strong,
    .full-report-text b {
        color: var(--gold);
    }

    .status-bar {
        display: flex; align-items: center; gap: 12px;
        padding: 6px 20px;
        border-top: 1px solid var(--b1);
        background: var(--s1);
        font-size: 10.5px; color: var(--ink3);
        font-family: 'Geist Mono', monospace;
    }
    .status-dot {
        width: 6px; height: 6px; border-radius: 99px;
        background: var(--g); box-shadow: 0 0 5px var(--g);
    }

    /* ── suggestion pills ── */
    .sug-pill {
        display: inline-block;
        background: var(--s2); border: 1px solid var(--b1); border-radius: 99px;
        padding: 5px 13px; font-size: 11.5px; color: var(--ink2);
        cursor: pointer; margin: 3px; transition: all .12s;
    }
    .sug-pill:hover { border-color: var(--a); color: var(--a2); background: rgba(124,106,255,.08); }

    /* ── welcome card ── */
    .welcome {
        text-align: center;
        padding: 60px 24px 30px;
        max-width: 520px;
        margin: 0 auto;
    }
    .welcome-icon {
        width: 56px; height: 56px; border-radius: 14px;
        background: linear-gradient(135deg,var(--a),#b06aff);
        display: flex; align-items: center; justify-content: center;
        font-size: 24px; color: #fff; margin: 0 auto 18px;
    }
    .welcome-title { font-size: 20px; font-weight: 600; letter-spacing: -.02em; margin-bottom: 8px; }
    .welcome-sub { font-size: 13px; color: var(--ink2); line-height: 1.65; margin-bottom: 24px; }
    .eg-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .eg-card {
        background: var(--s2); border: 1px solid var(--b1); border-radius: 10px;
        padding: 13px; font-size: 12px; color: var(--ink2); text-align: left;
        cursor: pointer; transition: all .15s;
    }
    .eg-card:hover { border-color: var(--a); color: var(--ink); background: rgba(124,106,255,.08); }
    .eg-card strong { display: block; color: var(--ink); margin-bottom: 4px; font-size: 12.5px; }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: none; }
    }
    .animate-in { animation: fadeUp .25s ease both; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "chats": {},           # {chat_id: {title, messages: [...]}}
        "active_chat": None,
        "run_count": 0,
        "deep_mode": False,
        "model": "Claude Sonnet 4.5",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


def new_chat():
    cid = str(uuid.uuid4())[:8]
    st.session_state.chats[cid] = {"title": "New research", "messages": []}
    st.session_state.active_chat = cid
    return cid


def active_messages():
    cid = st.session_state.active_chat
    if cid and cid in st.session_state.chats:
        return st.session_state.chats[cid]["messages"]
    return []


def add_message(role: str, content: dict):
    cid = st.session_state.active_chat
    if cid:
        st.session_state.chats[cid]["messages"].append({"role": role, "content": content, "ts": ts()})


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown(
        """
        <div style="padding:16px 14px 12px;border-bottom:1px solid var(--b1);display:flex;align-items:center;gap:9px">
            <div style="width:28px;height:28px;border-radius:7px;background:linear-gradient(135deg,var(--a),#b06aff);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:#fff;flex-shrink:0">RM</div>
            <span style="font-size:13px;font-weight:600">ResearchMind</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # New chat
    if st.button("＋  New research", use_container_width=True, key="new_chat_btn"):
        new_chat()
        st.rerun()

    st.markdown('<div class="sb-label">Chats</div>', unsafe_allow_html=True)

    # History list
    chats = st.session_state.chats
    for cid, chat in reversed(list(chats.items())):
        is_active = cid == st.session_state.active_chat
        cls = "hist-item active" if is_active else "hist-item"
        msgs = chat["messages"]
        last = msgs[-1]["ts"] if msgs else ""
        if st.button(
            f"{'◉' if is_active else '○'}  {chat['title']}",
            key=f"chat_{cid}",
            use_container_width=True,
        ):
            st.session_state.active_chat = cid
            st.rerun()

    st.markdown('<div class="sb-label" style="margin-top:12px">Settings</div>', unsafe_allow_html=True)

    model = st.selectbox(
        "Model",
        [
            "Claude Sonnet 4.5",
            "Claude Opus 4",
            "Claude Haiku 4.5",
            "── Mistral ──",
            "Mistral Large 2",
            "Mistral Small 3",
            "Mixtral 8x22B",
        ],
        index=0,
        key="model_select",
        label_visibility="visible",
    )
    st.session_state.model = model

    deep = st.checkbox("Deep research mode", value=st.session_state.deep_mode, key="deep_toggle")
    st.session_state.deep_mode = deep

    # Stats
    total = sum(len(c["messages"]) for c in chats.values())
    runs = st.session_state.run_count
    st.markdown(
        f"""
        <div style="margin-top:12px;padding:10px 4px;">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--ink3);font-family:'Geist Mono',monospace;margin-bottom:6px">
                <span>Pipeline runs</span><span style="color:var(--a2)">{runs}</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--ink3);font-family:'Geist Mono',monospace">
                <span>Total messages</span><span style="color:var(--a2)">{total}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # User
    st.markdown(
        """
        <div class="user-card" style="margin-top:auto">
            <div class="avatar">AB</div>
            <div>
                <div class="user-name">Abs</div>
                <div class="user-role">Intern · Mohali</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── MAIN AREA ─────────────────────────────────────────────────────────────────

# Ensure an active chat
if not st.session_state.active_chat:
    new_chat()

cid = st.session_state.active_chat
chat = st.session_state.chats[cid]
messages = chat["messages"]

# Topbar
title_display = html.escape(chat["title"])
st.markdown(
    f"""
    <div class="topbar">
        <span class="topbar-title">{title_display}</span>
        <div class="model-pill">
            <i class="ti ti-cpu" style="font-size:12px;color:var(--a2)"></i>
            {html.escape(st.session_state.model)}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Messages ──────────────────────────────────────────────────────────────────
if not messages:
    # Welcome / empty state
    st.markdown(
        """
        <div class="welcome animate-in">
            <div class="welcome-icon">⚡</div>
            <div class="welcome-title">ResearchMind</div>
            <div class="welcome-sub">
                Ask any research question. Four AI agents — Search, Reader, Writer, Critic —
                collaborate to deliver a sourced, structured report.
            </div>
            <div class="eg-grid">
                <div class="eg-card"><strong>AI agents in 2026</strong>Trends, players, real-world use cases</div>
                <div class="eg-card"><strong>Quantum computing</strong>State of the art and market outlook</div>
                <div class="eg-card"><strong>Climate AI tools</strong>How ML is changing climate science</div>
                <div class="eg-card"><strong>Biotech breakthroughs</strong>Gene editing, drug discovery, more</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Render all messages
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        t = msg.get("ts", "")

        if role == "user":
            text = html.escape(content.get("text", ""))
            st.markdown(
                f"""
                <div class="msg user animate-in">
                    <div class="msg-av">A</div>
                    <div class="msg-bubble">
                        <div class="msg-text">{text}</div>
                        <div class="msg-meta">✓ {t}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif role == "assistant":
            report  = content.get("report", "")
            feedback = content.get("feedback", "")
            logs    = content.get("logs", "")
            error   = content.get("error", "")
            score   = extract_score(feedback) if feedback else "—"
            words   = len(report.split()) if report else 0
            urls    = parse_urls(report)

            if error:
                st.markdown(
                    f"""
                    <div class="msg ai animate-in">
                        <div class="msg-av">⚡</div>
                        <div class="msg-bubble" style="flex:1">
                            <div class="msg-text" style="border-color:rgba(255,87,87,.3)">
                                <strong style="color:var(--r)">Pipeline error</strong><br>
                                <span style="font-size:12.5px">{html.escape(error)}</span>
                            </div>
                            <div class="msg-meta">⚡ ResearchMind · {t}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                # Build source cards HTML
                src_html = ""
                if urls:
                    cards = ""
                    for url in urls[:4]:
                        domain = re.sub(r"https?://(?:www\.)?", "", url).split("/")[0]
                        cards += f"""
                        <div class="src-card">
                            <div class="src-icon"><i class="ti ti-world" style="font-size:12px;color:var(--a2)"></i></div>
                            <div>
                                <div class="src-title">{html.escape(domain)}</div>
                                <div class="src-url"><a href="{html.escape(url)}" target="_blank" rel="noreferrer noopener">{html.escape(url[:55])}{'…' if len(url)>55 else ''}</a></div>
                            </div>
                        </div>"""
                    src_html = f'<div class="sources" style="margin-top:12px">{cards}</div>'

                # Metrics
                metrics_html = f"""
                <div class="metrics">
                    <div class="metric-pill"><div class="ml">Words</div><div class="mv">{words:,}</div></div>
                    <div class="metric-pill"><div class="ml">Sources</div><div class="mv">{len(urls)}</div></div>
                    <div class="metric-pill"><div class="ml">Score</div><div class="mv"><span class="score-badge">{html.escape(score)}</span></div></div>
                </div>"""

                st.markdown(
                    f"""
                    <div class="msg ai animate-in">
                        <div class="msg-av">⚡</div>
                        <div class="msg-bubble" style="flex:1">
                            <div class="msg-text">
                                <strong style="color:var(--ink);font-size:14px">Research Report Ready</strong>
                                {metrics_html}
                                {src_html}
                            </div>
                            <div class="msg-meta">⚡ ResearchMind · {t}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Full report in expander — auto-open for the latest message
                is_latest = (msg == messages[-1])
                with st.expander("📋 View full report", expanded=is_latest):
                    if report:
                        report_html = (
                            '<div class="full-report-card">'
                            '<div class="full-report-heading">Full report</div>'
                            f'<div class="full-report-text">{linkify_text(report).replace(chr(10), "<br>")}</div>'
                            '</div>'
                        )
                        st.markdown(report_html, unsafe_allow_html=True)
                        st.download_button(
                            "⬇ Download .md",
                            data=report,
                            file_name=f"{chat['title'].replace(' ','_').lower()}_report.md",
                            mime="text/markdown",
                            key=f"dl_{t}_{len(report)}",
                        )
                    else:
                        st.markdown("_No report generated._")

                if feedback:
                    with st.expander("🎯 Critic feedback", expanded=False):
                        st.markdown(feedback)

                if logs:
                    with st.expander("🪵 Pipeline logs", expanded=False):
                        st.code(logs, language="text")


# ── Suggestion chips (display only, no fill) ──────────────────────────────────
suggestions = [
    "AI agents 2026",
    "Quantum computing market",
    "Climate AI tools",
    "LLM benchmarks",
    "Biotech breakthroughs",
    "Robotics trends",
]

st.markdown("<br>", unsafe_allow_html=True)
chips_html = "".join(f'<span class="sug-pill">{s}</span>' for s in suggestions)
st.markdown(f'<div style="padding:0 0 8px">{chips_html}</div>', unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────────────────────
# Use a counter in key to force a fresh empty input after each send
input_key = f"user_input_{st.session_state.get('input_counter', 0)}"

input_col, btn_col = st.columns([6, 1])

with input_col:
    user_input = st.text_input(
        "msg",
        value="",
        placeholder="Ask ResearchMind anything… (e.g. AI agent trends 2026)",
        key=input_key,
        label_visibility="collapsed",
    )

with btn_col:
    send = st.button("⚡ Send", use_container_width=True, key="send_btn")


# ── Process send ──────────────────────────────────────────────────────────────
if send and user_input.strip():
    query = user_input.strip()

    # Update chat title if first message
    if not messages:
        short = query[:38] + ("…" if len(query) > 38 else "")
        st.session_state.chats[cid]["title"] = short

    add_message("user", {"text": query})

    # Bump counter so input widget re-renders empty next run
    st.session_state["input_counter"] = st.session_state.get("input_counter", 0) + 1

    # Show spinner while running
    with st.spinner("Four agents working — search → read → write → critique…"):
        try:
            state, logs = run_pipeline(query)
            st.session_state.run_count += 1
            add_message(
                "assistant",
                {
                    "report":   state.get("report", ""),
                    "feedback": state.get("feedback", ""),
                    "logs":     logs,
                    "error":    "",
                },
            )
        except Exception as exc:
            add_message("assistant", {"report": "", "feedback": "", "logs": "", "error": str(exc)})

    st.rerun()


# ── Status bar ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="status-bar">
        <div class="status-dot"></div>
        <span>4 agents online</span>
        <span style="margin-left:auto;display:flex;gap:12px">
            <span>Session · #{cid[:6]}</span>
            <span>·</span>
            <span>{len(messages)} messages</span>
            <span>·</span>
            <span>{st.session_state.run_count} runs</span>
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)