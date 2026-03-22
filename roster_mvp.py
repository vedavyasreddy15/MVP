import streamlit as st
import pandas as pd
import google.generativeai as genai
import hashlib
import re
import altair as alt
from PIL import Image
import PyPDF2

# -----------------------------------------------------------------------------
# PAGE CONFIG & CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Roster MVP", layout="wide", page_icon="🏆")

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
    genai.configure(api_key=api_key.strip())
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if file_type == 'pdf':
        reader = PyPDF2.PdfReader(uploaded_file)
        raw_text = "\n".join([page.extract_text() for page in reader.pages])
        prompt = "Extract only the names of the cricket players from this text. Ignore roles (batsman, bowler, etc.), numbers, or team names. Return a clean, comma-separated list of player names.\n\nText:\n" + raw_text
        response = model.generate_content(prompt)
        return response.text
    else:
        image = Image.open(uploaded_file)
        prompt = "Extract only the names of the cricket players from this image. Ignore roles (batsman, bowler, wicketkeeper, bench, etc.), numbers, emojis, or team names. Return a clean, comma-separated list of player names."
        response = model.generate_content([prompt, image])
        return response.text

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
    st.write("")
    st.write("")
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
st.write("Build rosters, extract players via AI, and compare matchup scores automatically.")

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
        col_name, col_upload = st.columns([1, 2])
        with col_name:
            new_name = st.text_input(f"Team {i+1} Name", value=state["name"], key=f"name_{team_key}")
            state["name"] = new_name
        with col_upload:
            roster_file = st.file_uploader(f"Upload Roster Image/PDF", type=["pdf", "jpg", "jpeg", "png"], key=f"file_{team_key}")
        
        st.divider()
        
        # Process New Uploads
        if roster_file is not None:
            # Only process if it's a new file to save API calls
            if roster_file.name != state["processed_file"]:
                if not st.session_state.api_key_val:
                    st.warning("⚠️ API Key required in sidebar for AI extraction.")
                else:
                    with st.spinner("🤖 AI is analyzing the roster..."):
                        try:
                            extracted_text = extract_text_with_gemini(st.session_state.api_key_val, roster_file)
                            state["raw_text"] = extracted_text
                            state["processed_file"] = roster_file.name
                            
                            # Matching Logic
                            search_text = extracted_text.lower()
                            matched = []
                            # 1. Full Match
                            for player in db.keys():
                                pattern = r'\b' + re.escape(player) + r'\b'
                                if re.search(pattern, search_text):
                                    matched.append(player)
                                    search_text = re.sub(pattern, ' ', search_text)
                            # 2. Surname Match
                            for player in db.keys():
                                if player in matched: continue
                                parts = player.split()
                                if len(parts) > 1 and len(parts[-1]) >= 3:
                                    pattern = r'\b' + re.escape(parts[-1]) + r'\b'
                                    if re.search(pattern, search_text):
                                        matched.append(player)
                                        search_text = re.sub(pattern, ' ', search_text)
                            
                            state["extracted_players"] = list(set(matched))
                            state["selected_players"] = list(set(matched)) # Auto-select matches
                            st.rerun() # Force UI update with new data
                        except Exception as e:
                            st.error(f"Extraction Failed: {e}")

        # Display Interface (Only if a file has been processed)
        if state["processed_file"]:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"### {state['name']} Roster")
                # Bind the multiselect to the session state so it doesn't clear
                selected = st.multiselect(
                    "Verify / Edit Players",
                    options=list(db.keys()),
                    default=state["selected_players"],
                    key=f"multi_{team_key}",
                    format_func=lambda x: x.title()
                )
                # Update state if user manually changes selection
                if selected != state["selected_players"]:
                    state["selected_players"] = selected
                
                # Fast Clear/Reset buttons
                c1, c2 = st.columns(2)
                if c1.button("❌ Clear All", key=f"clear_{team_key}"):
                    state["selected_players"] = []
                    st.rerun()
                if c2.button("🔄 Reset to AI Match", key=f"reset_{team_key}"):
                    state["selected_players"] = state["extracted_players"].copy()
                    st.rerun()
            
            with col2:
                # Calculate and display points
                total_pts = sum(get_points(p, db) for p in state["selected_players"])
                team_scores[state["name"]] = total_pts
                
                st.metric(label="Total Team Points", value=round(total_pts, 1))
                
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