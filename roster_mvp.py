import streamlit as st
import pandas as pd
from google import genai
import hashlib
import re
import altair as alt
from PIL import Image
import PyPDF2

# -----------------------------------------------------------------------------
# PAGE CONFIG & CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Roster MVP", layout="wide", page_icon="🏆")

# Lightweight, modern CSS that won't break Streamlit's native components
st.markdown("""
    <style>
    .big-font { 
        font-size: 1.2rem; 
        color: #475569; 
        margin-bottom: 2rem;
    }
    div[data-testid="stMetricValue"] {
        color: #d97706 !important; /* Darker Gold for better contrast on white */
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(uploaded_file):
    """Caches the dataset so it doesn't reload on every single click."""
    if uploaded_file.name.lower().endswith('.csv'):
        return pd.read_csv(uploaded_file)
    else:
        return pd.read_excel(uploaded_file)

def get_points(player_name, db_dict):
    normalized_name = str(player_name).strip().lower()
    return db_dict.get(normalized_name, 0.0)

def extract_text_with_gemini(api_key, uploaded_file):
    """Handles the Gemini API extraction logic cleanly outside the main loop."""
    client = genai.Client(api_key=api_key.strip())
    available_models = [m.name for m in client.models.list()]
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    # Model selection fallback
    if 'models/gemini-2.5-flash' in available_models or 'gemini-2.5-flash' in available_models:
        model_name = 'gemini-2.5-flash'
    elif 'models/gemini-2.0-flash' in available_models or 'gemini-2.0-flash' in available_models:
        model_name = 'gemini-2.0-flash'
    else:
        model_name = 'gemini-1.5-flash'
        
    if file_type == 'pdf':
        reader = PyPDF2.PdfReader(uploaded_file)
        raw_text = "\n".join([page.extract_text() for page in reader.pages])
        prompt = "Extract only the names of the cricket players from this text. Ignore roles (batsman, bowler, etc.), numbers, or team names. Return a clean, comma-separated list of player names.\n\nText:\n" + raw_text
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    else:
        image = Image.open(uploaded_file)
        prompt = "Extract only the names of the cricket players from this image. Ignore roles (batsman, bowler, wicketkeeper, bench, etc.), numbers, emojis, or team names. Return a clean, comma-separated list of player names."
        response = client.models.generate_content(model=model_name, contents=[image, prompt])
        return response.text

# Callbacks to safely update multiselect widgets without throwing Streamlit exceptions
def clear_team_selection(t_key):
    st.session_state[t_key]["selected_players"] = []
    if f"multi_{t_key}" in st.session_state:
        st.session_state[f"multi_{t_key}"] = []

def reset_team_selection(t_key):
    st.session_state[t_key]["selected_players"] = st.session_state[t_key]["extracted_players"].copy()
    if f"multi_{t_key}" in st.session_state:
        st.session_state[f"multi_{t_key}"] = st.session_state[t_key]["extracted_players"].copy()

# -----------------------------------------------------------------------------
# SIDEBAR: SETUP & AUTH
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ Setup Menu")

# --- API Key Management ---
st.sidebar.subheader("1. API Configuration")
if "api_locked" not in st.session_state:
    st.session_state.api_locked = False
if "api_key_val" not in st.session_state:
    st.session_state.api_key_val = ""

EXPECTED_HASH = hashlib.sha256(b"2026").hexdigest()

col_api, col_lock = st.sidebar.columns([4, 1])
with col_api:
    gemini_api_key = st.text_input(
        "Gemini API Key", 
        type="password", 
        disabled=st.session_state.api_locked, 
        value=st.session_state.api_key_val
    )
    if not st.session_state.api_locked:
        st.session_state.api_key_val = gemini_api_key
with col_lock:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🔒" if st.session_state.api_locked else "🔓"):
        st.session_state.show_passcode = not st.session_state.get("show_passcode", False)

if st.session_state.get("show_passcode", False):
    pass_input = st.sidebar.text_input("Enter Passcode to toggle lock", type="password")
    if st.sidebar.button("Submit Passcode"):
        if hashlib.sha256(pass_input.encode()).hexdigest() == EXPECTED_HASH:
            st.session_state.api_locked = not st.session_state.api_locked
            st.session_state.show_passcode = False
            st.rerun()
        else:
            st.sidebar.error("Incorrect Passcode!")

st.sidebar.divider()

# --- Database Loading ---
st.sidebar.subheader("2. Load Database")
db = {}

db_method = st.sidebar.radio("Input Method", ["Paste Text", "Upload File"], horizontal=True)

if db_method == "Paste Text":
    pasted_text = st.sidebar.text_area(
        "Paste Player Data", 
        height=200, 
        placeholder="Paste directly from the IPL website or Excel!"
    )
    if pasted_text.strip():
        clean_lines = [line.strip() for line in pasted_text.split('\n')]
        clean_text = "\n".join(clean_lines)
        
        # 1. Try to match the official BCCI website copy-paste format (Name -> Team -> Points)
        web_matches = re.findall(r'^([A-Za-z\s\-\'\.]+)\n([A-Z]{2,4})\n(\d+\.?\d*)', clean_text, re.MULTILINE)
        
        if web_matches:
            for name_str, team_str, pt_str in web_matches:
                name = name_str.strip().lower()
                try:
                    if name: db[name] = float(pt_str)
                except ValueError:
                    continue
        else:
            # 2. Fallback to standard line-by-line (Excel/Sheets format)
            for line in clean_lines:
                if not line: continue
                
                if '\t' in line:
                    parts = line.split('\t')
                    name_str, pt_str = parts[0], parts[-1]
                else:
                    match = re.search(r'^(.*?)\s+([-+]?\d*\.?\d+)\s*$', line)
                    if match:
                        name_str, pt_str = match.group(1), match.group(2)
                    else:
                        continue
                
                name = str(name_str).strip().lower()
                if not re.search(r'[a-z]', name): # Ensure it's a name to avoid parsing bad rows
                    continue
                    
                try:
                    if name: db[name] = float(pt_str)
                except ValueError:
                    continue
        
        if db:
            st.sidebar.success(f"✅ Loaded {len(db)} players from text.")
        else:
            st.sidebar.warning("⚠️ Could not read format. Ensure it is 'Name Points'.")
else:
    octo_file = st.sidebar.file_uploader("Upload Octoparse File", type=["csv", "xlsx", "xls"])
    
    if octo_file:
        try:
            df = load_data(octo_file)
            with st.sidebar.expander("📊 Preview Data"):
                st.dataframe(df.head(5))
                
            columns = df.columns.tolist()
            name_col = st.sidebar.selectbox("Player Names Column", options=columns, index=0)
            
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            default_pt_idx = columns.index(num_cols[0]) if num_cols else 0
            point_col = st.sidebar.selectbox("Points Column", options=columns, index=default_pt_idx)
                
            # Build dictionary cleanly
            for _, row in df.iterrows():
                try:
                    db[str(row[name_col]).lower().strip()] = float(row[point_col])
                except (ValueError, TypeError):
                    continue
            st.sidebar.success(f"✅ Loaded {len(db)} players.")
        except Exception as e:
            st.sidebar.error(f"Error loading data: {e}")

# -----------------------------------------------------------------------------
# MAIN DASHBOARD
# -----------------------------------------------------------------------------
st.title("🏆 Roster MVP")
st.markdown("<div class='big-font'>Build rosters, extract players via AI, and compare matchup scores automatically.</div>", unsafe_allow_html=True)

if not db:
    st.info("👈 **Please upload your player database in the sidebar to get started.**")
    st.stop() # Halt execution until DB is loaded to save UI clutter

# --- Team Setup ---
num_teams = st.number_input("Number of Teams in Matchup", min_value=1, max_value=10, value=2, step=1)
tabs = st.tabs([f"Team {i+1}" for i in range(num_teams)])
team_scores = {}

for i, tab in enumerate(tabs):
    with tab:
        team_key = f"team_{i}"
        
        # Initialize team state if it doesn't exist
        if team_key not in st.session_state:
            st.session_state[team_key] = {
                "name": f"Team {i+1}",
                "processed_file": None,
                "raw_text": "",
                "extracted_players": [],
                "selected_players": []
            }
        
        state = st.session_state[team_key]
        
        # Header Row
        col_name, col_input = st.columns([1, 2])
        with col_name:
            new_name = st.text_input(f"Team {i+1} Name", value=state["name"], key=f"name_{team_key}")
            state["name"] = new_name
            
            if st.button("🔄 Re-analyze Roster", key=f"reanalyze_{team_key}"):
                state["processed_file"] = None
                
        with col_input:
            input_method = st.radio("Roster Input Method", ["Upload File", "Paste Text"], key=f"method_{team_key}", horizontal=True)
            
            roster_file = None
            roster_text = ""
            current_input_id = None
            
            if input_method == "Upload File":
                roster_file = st.file_uploader(f"Upload Roster Image/PDF", type=["pdf", "jpg", "jpeg", "png"], key=f"file_{team_key}")
                if roster_file is not None:
                    current_input_id = roster_file.name
            else:
                roster_text = st.text_area("Paste Roster Names", height=100, key=f"text_{team_key}", placeholder="Paste player names here...")
                if roster_text.strip():
                    current_input_id = hashlib.md5(roster_text.encode()).hexdigest()
        
        st.divider()
        
        # Process New Uploads
        if current_input_id is not None:
            if current_input_id != state["processed_file"]:
                should_process = False
                extracted_text = ""
                
                if input_method == "Upload File":
                    if not st.session_state.api_key_val:
                        st.warning("⚠️ API Key required in sidebar for AI extraction.")
                    else:
                        with st.spinner("🤖 AI is analyzing the roster..."):
                            try:
                                extracted_text = extract_text_with_gemini(st.session_state.api_key_val, roster_file)
                                should_process = True
                            except Exception as e:
                                st.error(f"Extraction Failed: {e}")
                else:
                    extracted_text = roster_text
                    should_process = True
                    
                if should_process:
                    state["raw_text"] = extracted_text
                    state["processed_file"] = current_input_id
                    
                    search_text = extracted_text.lower()
                    matched_with_idx = []
                    sorted_players = sorted(db.keys(), key=len, reverse=True)
                    
                    # 1. Exact Full Match
                    for player in sorted_players:
                        pattern = r'\b' + re.escape(player) + r'\b'
                        for m in re.finditer(pattern, search_text):
                            matched_with_idx.append((m.start(), player))
                        search_text = re.sub(pattern, lambda x: ' ' * len(x.group()), search_text)
                            
                    # 2. Surname Match
                    for player in sorted_players:
                        parts = player.split()
                        if len(parts) > 1 and len(parts[-1]) >= 3:
                            surname = parts[-1]
                            pattern = r'\b' + re.escape(surname) + r'\b'
                            for m in re.finditer(pattern, search_text):
                                matched_with_idx.append((m.start(), player))
                            search_text = re.sub(pattern, lambda x: ' ' * len(x.group()), search_text)
                                
                    matched_with_idx.sort(key=lambda x: x[0])
                    
                    matched = []
                    for _, player in matched_with_idx:
                        if player not in matched:
                            matched.append(player)
                    
                    state["extracted_players"] = matched
                    state["selected_players"] = matched.copy() 
                    st.session_state[f"multi_{team_key}"] = state["selected_players"].copy() 
                    st.rerun() 

        # Display Interface (Always visible)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"### {state['name']} Roster")
            selected = st.multiselect(
                "Verify / Edit Players",
                options=list(db.keys()),
                default=state["selected_players"],
                key=f"multi_{team_key}",
                format_func=lambda x: x.title()
            )
            if selected != state["selected_players"]:
                state["selected_players"] = selected
                
            st.info(f"**Players Selected:** {len(state['selected_players'])}")
            
            c1, c2 = st.columns(2)
            c1.button("❌ Clear All", key=f"clear_{team_key}", on_click=clear_team_selection, args=(team_key,))
            if state["processed_file"]:
                c2.button("🔄 Reset to Match", key=f"reset_{team_key}", on_click=reset_team_selection, args=(team_key,))
        
        with col2:
            total_pts = sum(get_points(p, db) for p in state["selected_players"])
            team_scores[state["name"]] = total_pts
            
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #334155;">
                <h4 style='color: #94a3b8; margin:0;'>Total Team Points</h4>
                <h1 style='color: #eab308; margin:0; font-size: 3rem;'>{round(total_pts, 1)}</h1>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("See Player Breakdown"):
                for p in state["selected_players"]:
                    st.write(f"**{p.title()}**: {get_points(p, db)} pts")

# -----------------------------------------------------------------------------
# LEADERBOARD SECTION
# -----------------------------------------------------------------------------
if any(score > 0 for score in team_scores.values()):
    st.divider()
    st.subheader("📊 Matchup Leaderboard")
    
    chart_data = pd.DataFrame(list(team_scores.items()), columns=['Team Name', 'Total Points'])
    
    chart = alt.Chart(chart_data).mark_bar(
        color='#3b82f6', 
        cornerRadiusTopLeft=8, 
        cornerRadiusTopRight=8
    ).encode(
        x=alt.X('Team Name', sort='-y', axis=alt.Axis(labelAngle=0, title="")),
        y=alt.Y('Total Points', title="Points"),
        tooltip=['Team Name', 'Total Points']
    ).properties(height=400)
    
    # Add text labels on top of bars
    text = chart.mark_text(
        align='center', baseline='bottom', dy=-5, color='white', fontSize=14, fontWeight='bold'
    ).encode(text=alt.Text('Total Points:Q', format='.1f'))
    
    st.altair_chart(chart + text, use_container_width=True)