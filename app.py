import streamlit as st
import time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import random

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="IEEE ZC | Python Core Selection",
                   page_icon="⚡", layout="wide")

# ---------------- PARTICLE BACKGROUND & STYLING ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Orbitron:wght@400;900&display=swap');

.stApp { background:black; color:#00F5FF; font-family:'Fira Code', monospace; overflow:hidden; }

/* PARTICLE BACKGROUND */
#particles-js { position:fixed; width:100%; height:100%; z-index:-1; }

/* LOGO */
.logo { display:block; margin-left:auto; margin-right:auto; width:120px; border-radius:50%; border:3px solid #00F5FF; box-shadow:0 0 20px #00F5FF; }

/* TERMINAL */
.terminal-window {background:#0d1117;border:2px solid #00F5FF;border-radius:10px;padding:20px;box-shadow:0 0 25px rgba(0,245,255,0.3);margin-bottom:20px;}
.terminal-header {background:#161b22;padding:5px 15px;margin:-20px -20px 15px -20px;border-bottom:1px solid #00F5FF;border-radius:8px 8px 0 0;color:#8892b0;font-size:0.8rem;}
.terminal-body {color:#00FF88;white-space:pre-wrap; font-size:1.4rem;}
.cursor {display:inline-block;width:10px;height:20px;background:#00FF88;animation:blink 1s infinite;}
@keyframes blink {0%,100%{opacity:0}50%{opacity:1}}

/* LEADERBOARD CARDS */
.leader-card {background: linear-gradient(90deg, rgba(0,245,255,0.1), transparent); border-left:4px solid #00F5FF; padding:12px 20px; margin:5px 0; border-radius:0 10px 10px 0; display:flex; justify-content:space-between; align-items:center; transition:0.3s;}
.leader-card:hover {background: rgba(0,255,136,0.15); transform:scale(1.02);}
.rank-1 { border-left-color:#FFD700; background:rgba(255,215,0,0.15); animation: neonGlow 1.5s infinite alternate;}
.rank-2 { border-left-color:#C0C0C0; background:rgba(192,192,192,0.1); }
.rank-3 { border-left-color:#cd7f32; background:rgba(205,127,50,0.1); }
@keyframes neonGlow { 0% { box-shadow:0 0 10px #FFD700; } 100% { box-shadow:0 0 30px #FFD700; } }

/* ANSWER BUTTONS */
.answer-option {border:2px solid #00F5FF; padding:12px; border-radius:8px; margin:6px 0; cursor:pointer; transition:0.3s; font-size:1.3rem; text-align:center; font-weight:bold; background:black;}
.answer-option:hover {background:#00FF88;color:black; transform:scale(1.05); box-shadow:0 0 15px #00FF88;}

/* PROGRESS BARS */
.progress-bar {background:#00FF88; height:20px; border-radius:10px; transition:width 1s;}
.progress-bg {background:#111; height:20px; border-radius:10px; margin-bottom:10px;}
</style>

<div id="particles-js"></div>
<script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
<script>
particlesJS("particles-js", {
  "particles": {
    "number":{"value":120,"density":{"enable":true,"value_area":800}},
    "color":{"value":"#00F5FF"},
    "shape":{"type":"circle"},
    "opacity":{"value":0.3},
    "size":{"value":3,"random":true},
    "line_linked":{"enable":true,"distance":120,"color":"#00F5FF","opacity":0.2,"width":1},
    "move":{"enable":true,"speed":3}
  }
});
</script>
""", unsafe_allow_html=True)

# ---------------- GOOGLE SHEETS ----------------
@st.cache_resource
def connect_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
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

# ---------------- SESSION ----------------
if "started" not in st.session_state:
    st.session_state.update({
        "started":False, "q_index":0, "score":0, "correct":0,
        "skill_map":{"Tracing":0,"Debug":0,"Concept":0,"DS":0},
        "start_time":None, "name":"", "complete":False
    })

# ---------------- QUESTIONS ----------------
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


# ---------------- HELPER ----------------
def terminal_print(code, title="Python 3.10 Interpreter"):
    st.markdown(f"""
    <div class="terminal-window">
        <div class="terminal-header">● ● ● {title}</div>
        <div class="terminal-body"><code>{code}</code><span class="cursor"></span></div>
    </div>
    """, unsafe_allow_html=True)

# ---------------- LANDING PAGE ----------------
if not st.session_state.started and not st.session_state.complete:
    st.image("IEEE ZC.jpg", width=120, use_container_width =False, output_format="PNG", caption=None)
    st.markdown("<h1 style='text-align:center;font-family:Orbitron;'>IEEE ZC: CORE SELECTION</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([1,1])
    with col1:
        name_input = st.text_input("Enter Your Name", placeholder="Agent Name...")
        if st.button("START PROTOCOL"):
            if name_input:
                st.session_state.name = name_input
                st.session_state.started = True
                st.session_state.start_time = time.time()
                st.rerun()
            else:
                st.warning("Identity Required")
    with col2:
        st.markdown("### 🏆 TOP 5 LEADERBOARD")
        df = load_leaderboard()
        if not df.empty:
            df = df.sort_values(by="Score", ascending=False).head(5)
            for i,row in df.iterrows():
                cls = "rank-1" if i==0 else "rank-2" if i==1 else "rank-3" if i==2 else ""
                st.markdown(f"""<div class="leader-card {cls}">
                    <span><b>{row['Name']}</b></span>
                    <span style="color:#00FF88">{row['Score']} XP</span>
                </div>""", unsafe_allow_html=True)

# ---------------- QUIZ PAGE ----------------
elif st.session_state.started and not st.session_state.complete:
    st_autorefresh(interval=1000, key="timer_refresh")
    elapsed = int(time.time() - st.session_state.start_time)
    st.markdown(f"**CANDIDATE:** {st.session_state.name}  ⏱ {elapsed//60:02}:{elapsed%60:02}")
    q = questions[st.session_state.q_index]
    terminal_print(q['q'], title=f"TASK {st.session_state.q_index + 1}/25")
    for opt in q["options"]:
        if st.button(opt, key=f"opt_{opt}"):
            if opt == q["answer"]:
                st.session_state.score += 10*q["difficulty"]
                st.session_state.correct += 1
                st.session_state.skill_map[q["type"]] += 1
            if st.session_state.q_index < 24:
                st.session_state.q_index += 1
            else:
                st.session_state.complete = True
                st.session_state.started = False
            st.rerun()

# ---------------- RESULT PAGE ----------------
elif st.session_state.complete:
    st.image("IEEE ZC.jpg", width=120, use_container_width =False)
    st.markdown("<h1 style='text-align:center'>PROTOCOL SUMMARY</h1>", unsafe_allow_html=True)
    total_time = int(time.time() - st.session_state.start_time)
    accuracy = round(st.session_state.correct/25*100,2)
    xp = st.session_state.score + accuracy

    # XP Meter
    st.markdown("### XP METER")
    st.markdown(f"""
    <div class="progress-bg">
        <div class="progress-bar" style="width:{xp/3}%;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Skill bars
    st.markdown("### SKILL MAPPING")
    for skill,value in st.session_state.skill_map.items():
        st.markdown(f"{skill}: {value}")
        st.markdown(f"""
        <div class="progress-bg">
            <div class="progress-bar" style="width:{value*10}%;"></div>
        </div>
        """, unsafe_allow_html=True)

    # Full Leaderboard
    st.markdown("### 🏆 FULL LEADERBOARD")
    df = load_leaderboard()
    if not df.empty:
        df = df.sort_values(by="Score", ascending=False)
        for i,row in df.iterrows():
            cls = "rank-1" if i==0 else "rank-2" if i==1 else "rank-3" if i==2 else ""
            st.markdown(f"""<div class="leader-card {cls}">
                <span><b>{row['Name']}</b></span>
                <span>Score: {row['Score']} | Acc: {row['Accuracy']}% | Debug:{row['Debug']} Tracing:{row['Tracing']} Concept:{row['Concept']} DS:{row['DS']} | XP: {row['XP']}</span>
            </div>""", unsafe_allow_html=True)

    # Save to Google Sheets
    save_result([
        st.session_state.name, st.session_state.score, accuracy, total_time,
        st.session_state.skill_map["Debug"], st.session_state.skill_map["Tracing"],
        st.session_state.skill_map["Concept"], st.session_state.skill_map["DS"],
        xp, "", str(datetime.now())
    ])

    if st.button("RESTART"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()