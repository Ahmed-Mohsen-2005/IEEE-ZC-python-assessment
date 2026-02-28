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

.stApp::before {
    content: " ";
    position: fixed;
    top: 0; left: 0; bottom: 0; right: 0;
    background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
    z-index: -1;
    background-size: 100% 2px, 3px 100%;
    pointer-events: none;
}

.header-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: rgba(0,0,0,0.8);
    border-bottom: 2px solid #00F5FF;
    margin-bottom: 30px;
}

.terminal-window {
    background: rgba(13, 17, 23, 0.9);
    border: 1px solid #00F5FF;
    border-radius: 5px;
    padding: 25px;
    box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.leader-card {
    background: rgba(0, 245, 255, 0.05);
    border-left: 5px solid #00F5FF;
    padding: 15px;
    margin: 10px 0;
    border-radius: 0 10px 10px 0;
    animation: slideIn 0.4s ease-out forwards;
}

div.stButton > button {
    width: 100%;
    background: transparent;
    color: #00F5FF;
    border: 1px solid #00F5FF;
    padding: 15px;
    text-transform: uppercase;
    letter-spacing: 2px;
    transition: 0.3s;
}

div.stButton > button:hover {
    background: #00F5FF;
    color: black;
    box-shadow: 0 0 20px #00F5FF;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGO HEADER ----------------
st.markdown('<div class="header-container">', unsafe_allow_html=True)
try:
    st.image("IEEE ZC.jpg", width=220)
except:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/21/IEEE_logo.png", width=220)
st.markdown("<h2 style='color:#00FF88; margin-top:10px;'>CORE SELECTION PROTOCOL</h2>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "started" not in st.session_state:
    st.session_state.update({
        "started": False, "q_index": 0, "score": 0, "correct": 0,
        "skill_map": {"Tracing": 0, "Debug": 0, "Concept": 0, "DS": 0},
        "start_time": None, "name": "", "complete": False, "data_sent": False
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
            # Convert all elements to strings to avoid serialization issues
            row = [str(x) for x in data]
            sheet.append_row(row)
            return True
        except: return False
    return False

def load_leaderboard():
    sheet = connect_sheet()
    if sheet:
        try:
            return pd.DataFrame(sheet.get_all_records())
        except: return pd.DataFrame()
    return pd.DataFrame()

# ---------------- CERTIFICATE GENERATOR ----------------
def create_certificate(name, xp):
    img = Image.new('RGB', (1000, 700), color='#050a1a')
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 980, 680], outline='#00F5FF', width=3)
    d.rectangle([30, 30, 970, 670], outline='#00F5FF', width=1)
    for i in range(0, 1000, 50):
        d.line([i, 0, i, 20], fill='#00F5FF', width=1)
    
    d.text((500, 150), "CERTIFICATE OF COGNITION", fill='#00FF88', anchor="mm")
    d.text((500, 250), "THIS IS TO CERTIFY THAT AGENT", fill='#ffffff', anchor="mm")
    d.text((500, 350), name.upper(), fill='#00F5FF', anchor="mm")
    d.text((500, 450), "HAS SUCCESSFULLY CLEARED THE PY-CORE PROTOCOL", fill='#ffffff', anchor="mm")
    d.text((500, 520), f"FINAL SCORE: {xp} XP", fill='#00FF88', anchor="mm")
    d.text((500, 620), f"VERIFIED BY IEEE ZC - {datetime.now().strftime('%Y-%m-%d')}", fill='#888888', anchor="mm")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

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
    {"type":"DS","difficulty":3,"q":"Which method adds an item at the end of a list?","options":["add()","append()","insert()","extend()"],"answer":"append()"},
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

# ---------------- LEADERBOARD COMPONENT ----------------
def show_leaderboard(limit=5):
    df = load_leaderboard()
    if not df.empty:
        df = df.sort_values(by="XP", ascending=False).head(limit)
        for i, row in enumerate(df.iterrows()):
            r = row[1]
            rank = i + 1
            color = "#FFD700" if rank == 1 else "#C0C0C0" if rank == 2 else "#CD7F32" if rank == 3 else "#00F5FF"
            st.markdown(f"""
                <div class="leader-card" style="border-left-color: {color};">
                    <div style="display: flex; justify-content: space-between;">
                        <span><b style="color:{color}">#{rank:02}</b> {r['Name']}</span>
                        <span style="color:#00FF88">{r['XP']} XP</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ---------------- NAVIGATION ----------------
if not st.session_state.started and not st.session_state.complete:
    t1, t2 = st.tabs(["PROTOCOL ENTRY", "HALL OF FAME"])
    with t1:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown("<h3 style='text-align:center;'>IDENTITY AUTHENTICATION</h3>", unsafe_allow_html=True)
            name = st.text_input("CODENAME", placeholder="Enter your name...")
            if st.button("START SEQUENCE"):
                if name:
                    st.session_state.name = name
                    st.session_state.started = True
                    st.session_state.start_time = time.time()
                    st.rerun()
                else: st.warning("Identification Required")
    with t2:
        show_leaderboard(10)

elif st.session_state.started:
    st_autorefresh(interval=1000, key="timer")
    elapsed = int(time.time() - st.session_state.start_time)
    
    st.markdown(f"<h1 style='text-align:center; color:#00FF88;'>{elapsed//60:02}:{elapsed%60:02}</h1>", unsafe_allow_html=True)
    st.progress(st.session_state.q_index / len(questions))
    
    q = questions[st.session_state.q_index]
    
    # SAFE DISPLAY FOR CODE (No f-string backslash error)
    st.markdown('<div class="terminal-window">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:#888; font-size:0.8rem; margin-bottom:10px;">>> TASK_{st.session_state.q_index+1}/{len(questions)}</div>', unsafe_allow_html=True)
    st.code(q['q'], language='python')
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    cols = st.columns(2)
    for idx, opt in enumerate(q['options']):
        with cols[idx%2]:
            if st.button(opt, key=f"ans_{idx}"):
                if opt == q['answer']:
                    st.session_state.score += 10 * q['difficulty']
                    st.session_state.correct += 1
                    st.session_state.skill_map[q['type']] += 1
                
                if st.session_state.q_index < len(questions) - 1:
                    st.session_state.q_index += 1
                else:
                    # AUTOMATIC SAVE BEFORE SWITCHING TO COMPLETE
                    acc = round(st.session_state.correct / len(questions) * 100, 2)
                    final_xp = st.session_state.score + acc
                    save_result([
                        st.session_state.name, st.session_state.score, acc, 
                        int(time.time() - st.session_state.start_time),
                        st.session_state.skill_map["Debug"], st.session_state.skill_map["Tracing"],
                        st.session_state.skill_map["Concept"], st.session_state.skill_map["DS"],
                        final_xp, "", str(datetime.now())
                    ])
                    st.session_state.complete = True
                    st.session_state.started = False
                st.rerun()

elif st.session_state.complete:
    st.markdown("<h1 style='text-align:center;'>MISSION SUMMARY</h1>", unsafe_allow_html=True)
    
    accuracy = round(st.session_state.correct / len(questions) * 100, 2)
    total_time = int(time.time() - st.session_state.start_time)
    xp = st.session_state.score + accuracy

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### AGENT: {st.session_state.name}")
        st.metric("FINAL XP", f"{xp}")
        st.metric("ACCURACY", f"{accuracy}%")
        st.write(f"⏱ Time: {total_time}s")
        st.markdown("<p style='color:#00FF88;'>✅ DATA ARCHIVED AUTOMATICALLY</p>", unsafe_allow_html=True)
        
        if xp >= 400:
            st.success("🏆 ELITE STATUS CONFIRMED")
            cert_bytes = create_certificate(st.session_state.name, xp)
            st.download_button(
                label="💾 DOWNLOAD CORE CERTIFICATE",
                data=cert_bytes,
                file_name=f"IEEE_Core_{st.session_state.name}.png",
                mime="image/png"
            )
        else:
            st.info("Score 400+ XP to unlock the Elite Certificate.")
            
        if st.button("🔁 RESTART PROTOCOL"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    with c2:
        st.markdown("### NEURAL PROFILE")
        for skill, val in st.session_state.skill_map.items():
            st.write(f"{skill}")
            st.progress(val / 7 if val < 7 else 1.0)

    st.markdown("---")
    st.markdown("<h3 style='text-align:center; color:#00F5FF;'>🏆 SECTOR RANKINGS</h3>", unsafe_allow_html=True)
    show_leaderboard(100)