import streamlit as st
import time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import random
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os

# --- CONFIG & THEME ---
st.set_page_config(page_title="IEEE ZC | Python Core", page_icon="⚡", layout="wide")

# ---------------- ADVANCED CYBER-UI STYLING ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;500&family=Rajdhani:wght@500;700&display=swap');

.stApp {
    background: linear-gradient(135deg, #000000 0%, #050a1a 100%);
    color: #00F5FF;
    font-family: 'Rajdhani', sans-serif;
}

/* CRT Scanline & Background Glow */
.stApp::before {
    content: " ";
    position: fixed; top: 0; left: 0; bottom: 0; right: 0;
    background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 255, 0, 0.06));
    z-index: -1;
    background-size: 100% 2px, 3px 100%;
    pointer-events: none;
}

@keyframes float {
    0% { transform: translateY(0px); } 
    50% { transform: translateY(-15px); } 
    100% { transform: translateY(0px); }
}

.logo-container { display: flex; justify-content: center; margin-bottom: 20px; }
.logo-img {
    width: 180px; border-radius: 50%;
    animation: float 4s ease-in-out infinite;
    box-shadow: 0 0 25px rgba(0, 245, 255, 0.4);
}

.header-container {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 20px; background: rgba(0,0,0,0.8); border-bottom: 2px solid #00F5FF; margin-bottom: 30px;
}

/* Question Terminal Rectangle */
.terminal-window {
    background: rgba(13, 17, 23, 0.95);
    border: 2px solid #00F5FF;
    border-radius: 8px;
    padding: 25px;
    box-shadow: 0 0 30px rgba(0, 245, 255, 0.15);
    margin-bottom: 15px;
}

.timer-text {
    font-size: 5.5rem; font-weight: 900; color: #00FF88;
    text-align: center; margin: 10px 0;
    text-shadow: 0 0 30px rgba(0, 255, 136, 0.6);
    font-family: 'Fira Code', monospace;
}

.leader-card {
    background: rgba(0, 245, 255, 0.03); border-left: 5px solid #00F5FF;
    padding: 18px; margin: 12px 0; border-radius: 4px;
    transition: 0.3s ease-in-out;
}

.leader-card:hover {
    background: rgba(0, 245, 255, 0.12);
    transform: scale(1.01);
}

div.stButton > button {
    width: 100%; background: rgba(0, 245, 255, 0.05); color: #00F5FF; 
    border: 1px solid #00F5FF; padding: 18px; text-transform: uppercase; 
    letter-spacing: 2px; transition: 0.25s; font-weight: bold;
}

div.stButton > button:hover {
    background: #00F5FF !important; color: black !important; 
    box-shadow: 0 0 25px #00F5FF;
}

div.stButton > button:active, div.stButton > button:focus {
    outline: none !important; border: 1px solid #00F5FF !important; color: #00F5FF !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGO HELPER (BASE64) ----------------
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return None

img_tag = ""
if os.path.exists("IEEE ZC.jpg"):
    img_b64 = get_img_as_base64("IEEE ZC.jpg")
    if img_b64:
        img_tag = f'<div class="logo-container"><img src="data:image/jpeg;base64,{img_b64}" class="logo-img"></div>'
else:
    img_tag = '<div class="logo-container"><div style="text-align:center; font-size:40px; color:#00F5FF;">IEEE ZC 🦅</div></div>'

# ---------------- STATIC HEADER ----------------
st.markdown('<div class="header-container">', unsafe_allow_html=True)
st.markdown(img_tag, unsafe_allow_html=True)
st.markdown("<h2 style='color:#00FF88; margin-top:10px; letter-spacing:3px;'>CORE SELECTION PROTOCOL</h2>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "started" not in st.session_state:
    st.session_state.update({
        "started": False, "q_index": 0, "score": 0, "correct": 0,
        "skill_map": {"Tracing": 0, "Debug": 0, "Concept": 0, "DS": 0},
        "start_time": None, "name": "", "complete": False
    })

# ---------------- GOOGLE SHEETS ----------------
@st.cache_resource
def connect_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url(st.secrets["private_sheet_url"]).sheet1
    except: return None

def save_result(data):
    sheet = connect_sheet()
    if sheet:
        try:
            row = [str(x) for x in data]
            sheet.append_row(row)
            return True
        except: return False
    return False

def load_leaderboard():
    sheet = connect_sheet()
    if sheet:
        try: return pd.DataFrame(sheet.get_all_records())
        except: return pd.DataFrame()
    return pd.DataFrame()

# ---------------- QUESTIONS ----------------
questions = [
    {"type":"Concept","difficulty":2,"q":"Which of the following results in a float in Python 3?","options":["10 // 3","5 + 2","12 / 4","int('10')"],"answer":"12 / 4"},
    {"type":"Tracing","difficulty":2,"q":"x = 7\ny = 2\nprint(x % y ** y)","options":["1","3","0.5","4"],"answer":"3"},
    {"type":"Concept","difficulty":2,"q":"Which statement about Python variables is TRUE?","options":["Variables must be declared with a type","Immutable variables cannot be changed after assignment","Variable names can start with a number","Strings are mutable"],"answer":"Immutable variables cannot be changed after assignment"},
    {"type":"Tracing","difficulty":2,"q":"a = True\nb = False\nc = True\nprint(a or b and not c)","options":["True","False","Error","None"],"answer":"True"},
    {"type":"Debug","difficulty":2,"q":"x = 10\nif x > 5:\n    if x < 10:\n        print('A')\n    else:\n        print('B')\nelse:\n    print('C')","options":["A","B","C","None"],"answer":"B"},
    {"type":"Tracing","difficulty":2,"q":"# Short-circuit logic\nprint(0 or 'Hello')","options":["0","'Hello'","True","False"],"answer":"'Hello'"},
    {"type":"Tracing","difficulty":2,"q":"for i in range(1, 10, 3):\n    print(i, end=' ')\n# What is the output?","options":["1 4 7","1 4 7 10","1 2 3","3 6 9"],"answer":"1 4 7"},
    {"type":"Tracing","difficulty":2,"q":"i = 1\nwhile i < 10:\n    i *= 2\nprint(i)","options":["8","10","16","32"],"answer":"16"},
    {"type":"Tracing","difficulty":3,"q":"res = 0\nfor i in range(2):\n    for j in range(2):\n        res += (i + j)\nprint(res)","options":["2","4","6","8"],"answer":"4"},
    {"type":"Tracing","difficulty":2,"q":"s = 'ZewailCity'\nprint(s[2:5])","options":["'ewa'","'wai'","'wail'","'Zew'"],"answer":"'wai'"},
    {"type":"Tracing","difficulty":2,"q":"s = 'Python'\nprint(s[::-1])","options":["'nohtyP'","'Python'","'P'","Error"],"answer":"'nohtyP'"},
    {"type":"DS","difficulty":2,"q":"x = [1, 2, 3]\ny = x\nx.append(4)\nprint(len(y))","options":["3","4","Error","None"],"answer":"4"},
    {"type":"Tracing","difficulty":3,"q":"vals = [10, 20, 30, 40]\nvals[1:3] = [0]\nprint(vals)","options":["[10, 0, 40]","[10, 0, 30, 40]","[0, 20, 30, 40]","Error"],"answer":"[10, 0, 40]"},
    {"type":"Tracing","difficulty":3,"q":"def func(a, b=5):\n    return a * b\nprint(func(b=2, a=3))","options":["15","6","10","Error"],"answer":"6"},
    {"type":"Debug","difficulty":3,"q":"n = 10\ndef change():\n    n = 20\nchange()\nprint(n)","options":["10","20","Error","None"],"answer":"10"},
    {"type":"Concept","difficulty":2,"q":"What does the 'return' keyword do in a function?","options":["Exits the program","Sends a value back and exits the function","Restarts the loop","Prints a value to the console"],"answer":"Sends a value back and exits the function"},
    {"type":"Tracing","difficulty":2,"q":"d = {'x': 1, 'y': 2}\nprint(d.get('z', 0))","options":["None","Error","0","'z'"],"answer":"0"},
    {"type":"Concept","difficulty":3,"q":"Which of the following cannot be used as a Dictionary key?","options":["String","Integer","Tuple","List"],"answer":"List"},
    {"type":"Tracing","difficulty":2,"q":"s = {1, 2, 2, 3}\nprint(len(s))","options":["4","3","2","Error"],"answer":"3"},
    {"type":"Tracing","difficulty":2,"q":"t = (1, 2)\nt[0] = 5\nprint(t)","options":["(5, 2)","(1, 2)","Error","None"],"answer":"Error"},
    {"type":"Tracing","difficulty":3,"q":"matrix = [[1, 2], [3, 4]]\nprint(matrix[1][0])","options":["1","2","3","4"],"answer":"3"},
    {"type":"Tracing","difficulty":3,"q":"res = [x for x in range(5) if x % 2 != 0]\nprint(res)","options":["[1, 3]","[0, 2, 4]","[1, 2, 3, 4]","[1, 3, 5]"],"answer":"[1, 3]"},
    {"type":"Concept","difficulty":2,"q":"Which mode is used to add data to the end of an existing file?","options":["'r'","'w'","'a'","'x'"],"answer":"'a'"},
    {"type":"Tracing","difficulty":2,"q":"name = 'Agent'\nprint(f'Hello {name}')","options":["Hello {name}","Hello Agent","Error","'Hello Agent'"],"answer":"Hello Agent"},
    {"type":"Concept","difficulty":3,"q":"What happens if you open a non-existent file in 'r' mode?","options":["A new file is created","Nothing happens","FileNotFoundError is raised","The program hangs"],"answer":"FileNotFoundError is raised"}
]

# ---------------- NAVIGATION ----------------
if not st.session_state.started and not st.session_state.complete:
    t1, t2 = st.tabs(["PROTOCOL ENTRY", "HALL OF FAME"])
    with t1:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown("<h3 style='text-align:center;'>IDENTITY AUTHENTICATION</h3>", unsafe_allow_html=True)
            name = st.text_input("CODENAME", placeholder="Enter Agent Name...")
            if st.button("INITIALIZE SEQUENCE"):
                if name:
                    st.session_state.name = name
                    st.session_state.started = True
                    st.session_state.start_time = time.time()
                    st.rerun()
                else: st.warning("Identification Required")
    with t2:
        df = load_leaderboard()
        if not df.empty:
            df = df.sort_values(by="XP", ascending=False).head(15)
            for i, r in enumerate(df.iterrows()):
                st.markdown(f'<div class="leader-card">#{i+1:02} {r[1]["Name"]} — {r[1]["XP"]} XP</div>', unsafe_allow_html=True)

elif st.session_state.started:
    st_autorefresh(interval=1000, key="timer_pulse")
    elapsed = int(time.time() - st.session_state.start_time)
    
    # UI: Timer and Progress
    st.markdown(f"<div class='timer-text'>{elapsed//60:02}:{elapsed%60:02}</div>", unsafe_allow_html=True)
    st.progress(st.session_state.q_index / len(questions))
    
    q = questions[st.session_state.q_index]
    
    # UI: Terminal Window for Question
    st.markdown(f"""
    <div class="terminal-window" style="padding-top: 10px;">
        <div style="color: #888; font-size: 0.8rem; margin-bottom: 15px; font-family: 'Fira Code', monospace;">
            >> TASK_{st.session_state.q_index + 1}/{len(questions)}
        </div>
        <div style="background: rgba(0,0,0,0.4); padding: 20px; border-radius: 5px; border: 1px solid rgba(0, 245, 255, 0.1);">
            <pre style="margin: 0; color: #00FF88; font-family: 'Fira Code', monospace; font-size: 1.2rem; line-height: 1.5; white-space: pre-wrap;"><code>{q['q']}</code></pre>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("") 
    
    # Answer Logic
    cols = st.columns(2)
    for idx, opt in enumerate(q['options']):
        with cols[idx % 2]:
            if st.button(opt, key=f"ans_{st.session_state.q_index}_{idx}"):
                # 1. Update Internal Stats
                if opt == q['answer']:
                    st.session_state.score += 10 * q['difficulty']
                    st.session_state.correct += 1
                    st.session_state.skill_map[q['type']] += 1
                
                # 2. Check if there are more questions
                if st.session_state.q_index < len(questions) - 1:
                    st.session_state.q_index += 1
                    st.rerun()
                else:
                    # 3. MISSION COMPLETE: Prepare and Save Data
                    acc = round(st.session_state.correct / len(questions) * 100, 2)
                    total_time = int(time.time() - st.session_state.start_time)
                    final_xp = st.session_state.score + acc
                    
                    # Row Sequence: Name, Score, Accuracy, Time, Debug, Tracing, Concept, DS, XP, Timestamp
                    result_payload = [
                        st.session_state.name,                     
                        st.session_state.score,                    
                        acc,                                       
                        total_time,                                
                        st.session_state.skill_map.get("Debug", 0),   
                        st.session_state.skill_map.get("Tracing", 0), 
                        st.session_state.skill_map.get("Concept", 0), 
                        st.session_state.skill_map.get("DS", 0),      
                        final_xp,                                  
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    
                    with st.spinner("SYNCHRONIZING WITH CENTRAL DATABASE..."):
                        success = save_result(result_payload)
                        if success:
                            st.toast("Protocol Data Synchronized!", icon="✅")
                        else:
                            st.error("Data Sync Failed. Check Connection.")
                    
                    # 4. Update State to show Final Screen
                    st.session_state.complete = True
                    st.session_state.started = False
                    st.rerun()

elif st.session_state.complete:
    st.markdown("<h1 style='text-align:center; color:#00FF88; text-shadow:0 0 15px #00FF88;'>MISSION ACCOMPLISHED</h1>", unsafe_allow_html=True)
    
    accuracy = round(st.session_state.correct / len(questions) * 100, 2)
    xp = st.session_state.score + accuracy

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### AGENT: {st.session_state.name}")
        st.metric("FINAL XP", f"{xp}")
        st.metric("ACCURACY", f"{accuracy}%")
        if st.button("🔁 RESTART PROTOCOL"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    with c2:
        st.markdown("### NEURAL PROFICIENCY")
        for skill, val in st.session_state.skill_map.items():
            st.write(f"{skill}")
            st.progress(val / 7 if val < 7 else 1.0)

    st.divider()
    st.markdown("<h3 style='text-align:center; color:#00F5FF;'>🏆 GLOBAL SECTOR RANKINGS</h3>", unsafe_allow_html=True)
    
    df_final = load_leaderboard()
    if not df_final.empty:
        df_final = df_final.sort_values(by="XP", ascending=False).head(100)
        for i, row in enumerate(df_final.iterrows()):
            r = row[1]
            rank = i + 1
            rank_color = "#FFD700" if rank == 1 else "#C0C0C0" if rank == 2 else "#CD7F32" if rank == 3 else "#00F5FF"
            st.markdown(f"""
                <div class="leader-card" style="border-left-color: {rank_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span><b style="color:{rank_color}; font-size:1.2rem; margin-right:15px;">#{rank:02}</b> {r['Name']}</span>
                        <span style="color:#00FF88; font-family: 'Fira Code'; font-weight: bold;">{r['XP']} XP</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)