"""
Research AI — Streamlit UI for the Multi-Agent Research System (MAS).

Drop this file into your `MAS` folder (next to agents.py, pipeline.py, tools.py)
and run it with:

    streamlit run app.py

It calls the exact same building blocks as pipeline.py (build_search_agent,
build_reader_agent, writer_chain, critic_chain) — this file only handles
presentation.
"""

import re
import html
from datetime import datetime

import streamlit as st

import os



for key, value in st.secrets.items():
    os.environ[str(key)] = str(value)

from agents import (
    build_reader_agent,
    build_search_agent,
    writer_chain,
    critic_chain,
)

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(page_title="Research AI", page_icon="◆", layout="wide")

# --------------------------------------------------------------------------
# Style: a control room for four agents, not a SaaS dashboard template.
# Deep blue-black ground, cyan signal for progress, warm amber for review
# flags, Space Grotesk for display type, JetBrains Mono for anything that's
# actually a status readout or raw data.
# --------------------------------------------------------------------------
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

.stApp { background: #0B0D13; color: #DDE2EC; }
.block-container { max-width: 780px; padding-top: 2.6rem; }

/* ---------- Header ---------- */
.hud-top {
    display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 0.4rem;
}
.hud-top .brand { font-weight: 700; font-size: 1.55rem; letter-spacing: -0.01em; color: #F2F4F8; }
.hud-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: #5D6478;
    display: flex; align-items: center; gap: 0.4rem;
}
.hud-status .light {
    width: 7px; height: 7px; border-radius: 50%;
    background: #3A4155; display: inline-block;
}
.hud-status.live .light {
    background: #57E6D9;
    box-shadow: 0 0 8px 1px rgba(87,230,217,0.75);
}
.tagline { color: #838BA0; font-size: 0.97rem; margin: 0.9rem 0 2.1rem 0; max-width: 56ch; }

/* ---------- Command input ---------- */
.cmd-row { display: flex; align-items: center; gap: 0.6rem; }
.cmd-caret { font-family: 'JetBrains Mono', monospace; color: #57E6D9; font-size: 1.1rem; }
div[data-testid="stTextInput"] input {
    background: #12151E;
    border: 1px solid #232838;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.98rem;
    padding: 0.65rem 0.9rem;
    color: #EAEDF4;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #57E6D9;
    box-shadow: 0 0 0 1px rgba(87,230,217,0.35);
}
div[data-testid="stTextInput"] input::placeholder { color: #4C5266; }

.stButton > button, .stFormSubmitButton > button {
    background: #57E6D9;
    color: #06171A;
    border: none;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 0.62rem 1.4rem;
}
.stButton > button:hover, .stFormSubmitButton > button:hover { background: #7FF0E6; color: #06171A; }

/* ---------- Signal path (pipeline timeline) ---------- */
.signal { margin: 1.9rem 0 2.3rem 0; }
.sig-step { display: flex; align-items: flex-start; gap: 1rem; position: relative; padding-bottom: 1.15rem; }
.sig-step:not(:last-child)::before {
    content: ""; position: absolute; left: 8px; top: 22px;
    width: 1px; height: calc(100% - 8px); background: #232838;
}
.sig-step.done:not(:last-child)::before { background: #235049; }
.sig-node {
    width: 17px; height: 17px; border-radius: 50%; margin-top: 2px; flex-shrink: 0;
    border: 1.5px solid #2C3245; background: #12151E;
    display: flex; align-items: center; justify-content: center;
}
.sig-node::after { content: ""; width: 6px; height: 6px; border-radius: 50%; background: transparent; }
.sig-step.done .sig-node { border-color: #57E6D9; }
.sig-step.done .sig-node::after { background: #57E6D9; }
.sig-step.active .sig-node { border-color: #FFB169; box-shadow: 0 0 10px 1px rgba(255,177,105,0.45); }
.sig-step.active .sig-node::after { background: #FFB169; }
.sig-label { font-family: 'JetBrains Mono', monospace; font-size: 0.92rem; color: #EAEDF4; }
.sig-step.pending .sig-label { color: #565D72; }
.sig-note { font-size: 0.87rem; color: #7B8299; margin-top: 0.15rem; }

/* ---------- Report panel ---------- */
.panel {
    background: #10131B;
    border: 1px solid #232838;
    border-radius: 10px;
    padding: 1.9rem 2.1rem;
}
.panel-tag {
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    color: #57E6D9; margin-bottom: 0.9rem; display: block;
}
.report-body { line-height: 1.75; font-size: 1.02rem; color: #DDE2EC; }
.report-body p { margin-bottom: 1rem; }

/* ---------- Review panel (critic) ---------- */
.review-panel {
    border-left: 2.5px solid #FFB169;
    background: #14151B;
    border-radius: 0 8px 8px 0;
    padding: 1.1rem 1.4rem;
    margin: 1.5rem 0;
}
.review-tag { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FFB169; display: block; margin-bottom: 0.5rem; }
.review-panel p { color: #C7CCDB; line-height: 1.65; margin: 0; }

/* ---------- Raw log (search / scrape output) ---------- */
.log-box {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.81rem;
    background: #0D0F16;
    border: 1px solid #1D2130;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    color: #97E8DC;
    line-height: 1.55;
    max-height: 320px;
    overflow-y: auto;
    white-space: pre-wrap;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] { background: #0D0F16; border-right: 1px solid #1D2130; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown { color: #9AA1B5; }
section[data-testid="stSidebar"] h3 { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #7B8299; }

/* Run-log entries: quiet list rows, not solid CTA buttons — the generic
   button style (dark text on bright cyan) doesn't work repeated many times,
   so give these their own look with a clearly readable light label. */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: #12151E !important;
    color: #DDE2EC !important;
    border: 1px solid #232838 !important;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 400;
    font-size: 0.82rem;
    text-align: left;
    justify-content: flex-start;
    padding: 0.5rem 0.8rem;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background: #1A1E2B !important;
    border-color: #57E6D9 !important;
    color: #F2F4F8 !important;
}

hr { border-color: #1D2130; }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "current" not in st.session_state:
    st.session_state.current = None
if "running" not in st.session_state:
    st.session_state.running = False
if "run_counter" not in st.session_state:
    st.session_state.run_counter = 0

# --------------------------------------------------------------------------
# Sidebar — run log
# --------------------------------------------------------------------------
with st.sidebar:
    run_count = len(st.session_state.history)
    st.markdown(f"### Run log · {run_count}")
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            label = f"#{item['run_id']} · {item['topic'][:32]}"
            if st.button(label, key=f"hist_{item['run_id']}", use_container_width=True):
                st.session_state.current = item
                st.rerun()
        st.markdown("---")
        if st.button("Clear log", use_container_width=True):
            st.session_state.history = []
            st.session_state.current = None
            st.rerun()
    else:
        st.caption("No runs yet.")

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
status_class = "live" if st.session_state.running else ""
st.markdown(
    f"""
    <div class="hud-top">
        <div class="brand">Research AI</div>
        <div class="hud-status {status_class}"><span class="light"></span>{'running' if st.session_state.running else 'idle'}</div>
    </div>
    <div class="tagline">Four agents on one line: one searches, one reads, one writes, one checks the work.</div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------
with st.form("topic_form"):
    c1, c2 = st.columns([8, 1.4])
    with c1:
        topic = st.text_input("Topic", placeholder="topic to investigate", label_visibility="collapsed")
    with c2:
        submitted = st.form_submit_button("Run", use_container_width=True)

# --------------------------------------------------------------------------
# Signal path (pipeline progress)
# --------------------------------------------------------------------------
STEPS = [
    ("search", "scanning for recent, reliable sources"),
    ("read", "pulling full content from the best match"),
    ("draft", "composing the report from what came back"),
    ("review", "flagging gaps or issues in the draft"),
]


def render_signal(active_index: int, placeholder) -> None:
    rows = []
    for i, (label, note) in enumerate(STEPS):
        if active_index == -1:
            state = "pending"
        elif i < active_index:
            state = "done"
        elif i == active_index:
            state = "active"
        else:
            state = "pending"
        rows.append(
            f'<div class="sig-step {state}"><div class="sig-node"></div>'
            f'<div><div class="sig-label">{label}</div><div class="sig-note">{note}</div></div></div>'
        )
    placeholder.markdown(f'<div class="signal">{"".join(rows)}</div>', unsafe_allow_html=True)


def as_text(value) -> str:
    if hasattr(value, "content"):
        return value.content
    return str(value)


def report_to_html(report_text: str) -> str:
    escaped = html.escape(report_text.strip())
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", escaped) if p.strip()]
    return "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs)


# --------------------------------------------------------------------------
# Run pipeline
# --------------------------------------------------------------------------
if submitted:
    if not topic or not topic.strip():
        st.warning("Enter a topic first.")
    else:
        topic = topic.strip()
        st.session_state.running = True
        signal_slot = st.empty()
        state = {}
        try:
            render_signal(0, signal_slot)
            search_agent = build_search_agent()
            search_result = search_agent.invoke(
                {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]}
            )
            state["search_results"] = search_result["messages"][-1].content

            render_signal(1, signal_slot)
            reader_agent = build_reader_agent()
            reader_result = reader_agent.invoke(
                {
                    "messages": [
                        (
                            "user",
                            f"Based on the following search results about '{topic}', "
                            f"pick the most relevant URL and scrape it for deeper content.\n\n"
                            f"Search Results:\n{state['search_results'][:800]}",
                        )
                    ]
                }
            )
            state["scraped_content"] = reader_result["messages"][-1].content

            render_signal(2, signal_slot)
            research_combined = (
                f"SEARCH RESULTS : \n {state['search_results']} \n\n"
                f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
            )
            state["report"] = writer_chain.invoke({"topic": topic, "research": research_combined})

            render_signal(3, signal_slot)
            state["feedback"] = critic_chain.invoke({"report": state["report"]})

            render_signal(4, signal_slot)

            st.session_state.run_counter += 1
            record = {
                "run_id": st.session_state.run_counter,
                "topic": topic,
                "timestamp": datetime.now().strftime("%b %d, %H:%M"),
                "state": state,
            }
            st.session_state.history.append(record)
            st.session_state.current = record
            st.session_state.running = False
            st.rerun()  # refresh so the sidebar run log reflects this run immediately
        except Exception as e:
            st.session_state.running = False
            st.error(f"Pipeline stopped: {e}")

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
record = st.session_state.current
if record:
    state = record["state"]
    st.markdown("---")
    st.markdown(
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;color:#565D72;">'
        f'{record["timestamp"]}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {record['topic']}")

    st.markdown(
        f'<div class="panel"><span class="panel-tag">report</span>'
        f'<div class="report-body">{report_to_html(as_text(state.get("report", "")))}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="review-panel"><span class="review-tag">review</span>'
        f'<p>{html.escape(as_text(state.get("feedback", "")))}</p></div>',
        unsafe_allow_html=True,
    )

    st.download_button(
        "Download report",
        data=as_text(state.get("report", "")),
        file_name=f"{record['topic'][:40].replace(' ', '_')}.md",
        mime="text/markdown",
    )

    with st.expander("search — raw results"):
        st.markdown(
            f'<div class="log-box">{html.escape(as_text(state.get("search_results", "")))}</div>',
            unsafe_allow_html=True,
        )
    with st.expander("read — scraped content"):
        st.markdown(
            f'<div class="log-box">{html.escape(as_text(state.get("scraped_content", "")))}</div>',
            unsafe_allow_html=True,
        )
else:
    st.caption("No output yet — run a topic above.")