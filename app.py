import streamlit as st
import random
import time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go
import copy
from streamlit_autorefresh import st_autorefresh

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="IEEE ZC | Python Core Selection",
    page_icon="⚡",
    layout="wide"
)

# -------------------- CYBER UI & TERMINAL STYLING --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Orbitron:wght@400;900&display=swap');

.stApp {
    background-color: #050a10;
    color: #00F5FF;
    font-family: 'Fira Code', monospace;
}

/* TERMINAL BOX */
.terminal-window {
    background: #0d1117;
    border: 2px solid #00F5FF;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
    position: relative;
    margin-bottom: 25px;
}
.terminal-header {
    background: #161b22;
    padding: 5px 15px;
    margin: -20px -20px 15px -20px;
    border-bottom: 1px solid #00F5FF;
    border-radius: 8px 8px 0 0;
    color: #8892b0;
    font-size: 0.8rem;
}
.terminal-body {
    color: #00FF88;
    white-space: pre-wrap;
}
.cursor {
    display: inline-block;
    width: 10px;
    height: 20px;
    background: #00FF88;
    animation: blink 1s infinite;
}
@keyframes blink { 0%, 100% {opacity: 0} 50% {opacity: 1} }

/* LEADERBOARD WIDGETS */
.leader-card {
    background: linear-gradient(90deg, rgba(0,245,255,0.1), transparent);
    border-left: 4px solid #00F5FF;
    padding: 10px 20px;
    margin: 5px 0;
    border-radius: 0 10px 10px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.rank-1 { border-left-color: #FFD700; background: rgba(255,215,0,0.1); }

/* NEON BUTTONS */
div.stButton > button {
    width: 100%;
    background: transparent;
    border: 2px solid #00F5FF;
    color: #00F5FF;
    font-family: 'Orbitron', sans-serif;
    transition: 0.3s;
}
div.stButton > button:hover {
    background: #00F5FF;
    color: #050a10;
    box-shadow: 0 0 30px #00F5FF;
}

/* GLOBAL RADIOS */
div[data-testid="stMarkdownContainer"] > p { font-size: 1.1rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# -------------------- GOOGLE SHEETS --------------------
@st.cache_resource
def connect_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet_url = st.secrets["private_sheet_url"]
    return client.open_by_url(sheet_url).sheet1

def save_result(data):
    sheet = connect_sheet()
    sheet.append_row(data)

def load_leaderboard():
    try:
        sheet = connect_sheet()
        records = sheet.get_all_records()
        return pd.DataFrame(records)
    except:
        return pd.DataFrame()

# -------------------- SESSION STATE --------------------
if "started" not in st.session_state:
    st.session_state.update({
        "started": False, "q_index": 0, "score": 0, "correct": 0,
        "skill_map": {"Tracing": 0, "Debug": 0, "Concept": 0, "DS": 0},
        "start_time": None, "name": "", "complete": False
    })

# -------------------- HELPER FUNCTIONS --------------------
def terminal_print(code, title="Python 3.10 Interpreter"):
    st.markdown(f"""
    <div class="terminal-window">
        <div class="terminal-header">● ● ● {title}</div>
        <div class="terminal-body"><code>{code}</code><span class="cursor"></span></div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- MEDIUM PYTHON QUESTIONS --------------------
questions = [
    {"type":"Tracing","difficulty":3,"q":"x = [1,2,3]\ny = x\nx.append(4)\nprint(y)","options":["[1,2,3]","[1,2,3,4]","Error","None"],"answer":"[1,2,3,4]"},
    {"type":"Debug","difficulty":3,"q":"for i in range(3)\n    print(i)","options":["Error","0 1 2","1 2 3","0 1 2 3"],"answer":"Error"},
    {"type":"DS","difficulty":3,"q":"Which structure is best for FIFO?","options":["List","Set","Deque","Tuple"],"answer":"Deque"},
    {"type":"Concept","difficulty":3,"q":"Difference between tuple and list?","options":["Tuple mutable","List immutable","Tuple immutable","No difference"],"answer":"Tuple immutable"},
    {"type":"Tracing","difficulty":3,"q":"def f(a=[]):\n a.append(1)\n return a\nprint(f()); print(f())","options":["[1][1]","[1][1,1]","Error","[]"],"answer":"[1][1,1]"},
    {"type":"Debug","difficulty":3,"q":"def func():\n print(x)\nx = 5\nfunc()","options":["5","Error","None","0"],"answer":"Error"},
    {"type":"DS","difficulty":3,"q":"Time complexity of inserting at index 0 in a list?","options":["O(1)","O(log n)","O(n)","O(n^2)"],"answer":"O(n)"},
    {"type":"Concept","difficulty":3,"q":"What does 'is' check in Python?","options":["Value equality","Reference equality","Type equality","Both"],"answer":"Reference equality"},
    {"type":"Tracing","difficulty":3,"q":"print(bool([]))","options":["True","False"],"answer":"False"},
    {"type":"Debug","difficulty":3,"q":"if True print('Hi')","options":["Error","Hi","True","False"],"answer":"Error"},
    {"type":"DS","difficulty":3,"q":"Which method adds an item at the end of a list?","options":["add()","append()","insert()","extend()"],"answer":"append"},
    {"type":"Concept","difficulty":3,"q":"What is Python's GIL?","options":["Global Interpreter Lock","Graphical Interface Library","General Input List","None"],"answer":"Global Interpreter Lock"},
    {"type":"Tracing","difficulty":3,"q":"x = 5\ny = x\nx = 7\nprint(y)","options":["5","7","Error","None"],"answer":"5"},
    {"type":"Debug","difficulty":3,"q":"print('2'+2)","options":["4","'22'","Error","2+2"],"answer":"Error"},
    {"type":"DS","difficulty":3,"q":"Best DS for LIFO?","options":["Stack","Queue","Deque","List"],"answer":"Stack"},
    {"type":"Concept","difficulty":3,"q":"Difference between deep copy and shallow copy?","options":["Both same","Shallow copies objects only","Deep copies nested objects","Shallow copies everything"],"answer":"Deep copies nested objects"},
    {"type":"Tracing","difficulty":3,"q":"print(2**3**2)","options":["512","64","256","Error"],"answer":"512"},
    {"type":"Debug","difficulty":3,"q":"x = [1,2,3]\nx[3]","options":["3","Error","None","0"],"answer":"Error"},
    {"type":"DS","difficulty":3,"q":"Time complexity of dict lookup?","options":["O(1)","O(n)","O(log n)","O(n^2)"],"answer":"O(1)"},
    {"type":"Concept","difficulty":3,"q":"Mutable types in Python?","options":["List, Dict, Set","Tuple, List","All","None"],"answer":"List, Dict, Set"},
    {"type":"Tracing","difficulty":3,"q":"print([i for i in range(3)])","options":["0 1 2","[0,1,2]","Error","[1,2,3]"],"answer":"[0,1,2]"},
    {"type":"Debug","difficulty":3,"q":"x = 10\ny = 0\nprint(x/y)","options":["Error","0","10","None"],"answer":"Error"},
    {"type":"DS","difficulty":3,"q":"Which DS is unordered and mutable?","options":["List","Tuple","Dict","String"],"answer":"Dict"},
    {"type":"Concept","difficulty":3,"q":"Python functions are first-class objects?","options":["Yes","No"],"answer":"Yes"},
    {"type":"Tracing","difficulty":3,"q":"a = [1,2]\nb = a*2\nprint(b)","options":["[1,2,1,2]","[1,2,2]","Error","[1,1,2,2]"],"answer":"[1,2,1,2]"},
    {"type":"Debug","difficulty":3,"q":"print('Hello' / 2)","options":["Error","Hello2","'Hello2'","None"],"answer":"Error"}
]

# -------------------- MAIN LOGIC --------------------
def quiz_page():
    st_autorefresh(interval=1000, key="timer_refresh")  # live timer

    elapsed = int(time.time() - st.session_state.start_time)
    
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown(f"**CANDIDATE:** {st.session_state.name}")
        st.progress(st.session_state.q_index / len(questions))
    with col2:
        st.markdown(f"### ⏱ {elapsed//60:02}:{elapsed%60:02}")

    q = questions[st.session_state.q_index]
    terminal_print(q['q'], title=f"TASK {st.session_state.q_index + 1}/{len(questions)}")
    ans = st.radio("SELECT OUTPUT:", q['options'], index=None)
    
    if st.button("EXECUTE COMMAND"):
        if ans:
            if ans == q["answer"]:
                st.session_state.score += 10 * q["difficulty"]
                st.session_state.correct += 1
                st.session_state.skill_map[q["type"]] += 1
            if st.session_state.q_index < len(questions)-1:
                st.session_state.q_index += 1
            else:
                st.session_state.complete = True
                st.session_state.started = False
            st.rerun()

# --- LANDING PAGE ---
if not st.session_state.started and not st.session_state.complete:
    st.markdown("<h1 style='text-align:center; font-family:Orbitron;'>IEEE ZC: CORE SELECTION</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("### 🛠 IDENTITY VERIFICATION")
        name_input = st.text_input("Enter Legal Name", placeholder="Agent Name...")
        if st.button("INITIATE PROTOCOL"):
            if name_input:
                st.session_state.name = name_input
                st.session_state.started = True
                st.session_state.start_time = time.time()
                st.rerun()
            else:
                st.warning("Identity Required.")
    with col2:
        st.markdown("### 🏆 GLOBAL LEADERBOARD")
        df_lb = load_leaderboard()
        if df_lb.empty:
            st.info("No leaderboard data yet.")
        else:
            df_lb = df_lb.sort_values(by="Score", ascending=False)
            for i,row in df_lb.head(5).iterrows():
                cls = "rank-1" if i==0 else ""
                st.markdown(f"""<div class="leader-card {cls}">
                    <span><b>{row['Name']}</b></span>
                    <span style="color:#00FF88">{row['Score']} XP</span>
                </div>""", unsafe_allow_html=True)

# --- QUIZ PAGE ---
elif st.session_state.started and not st.session_state.complete:
    quiz_page()

# --- RESULTS PAGE ---
elif st.session_state.complete:
    st.markdown("<h1 style='text-align:center;'>PROTOCOL SUMMARY</h1>", unsafe_allow_html=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(st.session_state.skill_map.values()),
        theta=list(st.session_state.skill_map.keys()),
        fill='toself', line_color='#00F5FF'
    ))
    fig.update_layout(
        template="plotly_dark",
        polar=dict(radialaxis=dict(visible=False)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    total_time = int(time.time() - st.session_state.start_time)
    accuracy = round(st.session_state.correct / len(questions) * 100,2)
    xp = st.session_state.score + accuracy
    
    save_result([
        st.session_state.name, st.session_state.score, accuracy,
        total_time,
        st.session_state.skill_map["Debug"],
        st.session_state.skill_map["Tracing"],
        st.session_state.skill_map["Concept"],
        st.session_state.skill_map["DS"],
        xp,
        ",".join([k for k,v in st.session_state.skill_map.items() if v>0]),
        str(datetime.now())
    ])
    
    st.metric("FINAL XP", xp)
    st.markdown(f"Accuracy: {accuracy}%")
    st.markdown(f"Time Taken: {total_time}s")
    
    if st.button("RE-ENTRY PROTOCOL"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()