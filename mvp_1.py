import streamlit as st

st.set_page_config(page_title="MVP", layout="wide", page_icon="🏆")

from PIL import Image
import PyPDF2
import re
import pandas as pd
import google.generativeai as genai
import hashlib
import altair as alt

def get_points(player_name, db):
    normalized_name = player_name.strip().lower()
    return db.get(normalized_name, 0.0)

# Custom CSS for a fancier look
st.markdown("""
    <style>
    /* Navy Blue & Beige Theme */
    .stApp {
        background-color: #0A192F !important;
        background-image: radial-gradient(at top center, #112A46, #0A192F) !important;
    }
    /* Frosted Glass Effect for the Main Block */
    .block-container {
        background: rgba(10, 25, 47, 0.7);
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(229, 211, 179, 0.2);
        padding: 2rem;
        margin-top: 2rem;
    }
    /* Frosted Glass Effect for the Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 25, 47, 0.5) !important;
        backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(229, 211, 179, 0.2) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: transparent !important;
    }
    /* Input boxes & dropdowns */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, ul[role="listbox"] {
        background-color: #112A46 !important;
        border: 1px solid #E5D3B3 !important;
    }
    div[data-baseweb="input"] *, div[data-baseweb="select"] *, ul[role="listbox"] * {
        color: #FFFFFF !important;
    }
    /* Fix File Uploader Backgrounds (Drag Drop Box & Uploaded File Box) */
    [data-testid="stFileUploadDropzone"] {
        background-color: #112A46 !important;
        border: 1px dashed #E5D3B3 !important;
    }
    [data-testid="stFileUploadDropzone"] *, [data-testid="stFileUploadDropzone"] span, [data-testid="stFileUploadDropzone"] small, [data-testid="stFileUploadDropzone"] div {
        color: #FFFFFF !important;
    }
    [data-testid="stUploadedFile"] {
        background-color: #0A192F !important;
        border: 1px solid #E5D3B3 !important;
    }
    [data-testid="stUploadedFile"] *, [data-testid="stUploadedFile"] span, [data-testid="stUploadedFile"] small, [data-testid="stUploadedFile"] div {
        color: #FFFFFF !important;
    }
    /* Fix Info / Warning / Alert Boxes */
    [data-testid="stAlert"] {
        background-color: #112A46 !important;
        border-left: 4px solid #E5D3B3 !important;
    }
    /* Unified readable text */
    h1, h2, h3, p, span, label, li, small {
        color: #FFFFFF !important;
    }
    .big-font { font-size: 22px !important; color: #E5D3B3 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏆 MVP")
st.markdown("<p class='big-font'>Build your rosters, extract players automatically, and compare team scores!</p>", unsafe_allow_html=True)

st.sidebar.header("1. 🐙 Load Main Database")

db = {}
df = None

octo_file = st.sidebar.file_uploader("Upload Octoparse File", type=["csv", "xlsx", "xls"])
if octo_file is not None:
    try:
        if octo_file.name.lower().endswith('.csv'):
            df = pd.read_csv(octo_file)
        else:
            df = pd.read_excel(octo_file)
    except Exception as e:
        st.sidebar.error(f"❌ Could not read file properly: {e}.")

if df is not None:
    try:
        with st.sidebar.expander("📊 Preview Database Data"):
            st.dataframe(df.head(10))
            
        columns = df.columns.tolist()
        st.sidebar.write("### Map Your Columns")
        
        name_col = st.sidebar.selectbox("Player Names Column?", options=columns, index=0)
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        default_pt_idx = columns.index(num_cols[0]) if num_cols else (1 if len(columns) > 1 else 0)
        point_col = st.sidebar.selectbox("Points Column?", options=columns, index=default_pt_idx)
            
        for index, row in df.iterrows():
            try:
                db[str(row[name_col]).lower().strip()] = float(row[point_col])
            except (ValueError, TypeError):
                continue
        st.sidebar.success(f"✅ Successfully loaded {len(db)} players!")
    except Exception as e:
        st.sidebar.error(f"❌ Error processing data columns: {e}.")

st.divider()

if "api_locked" not in st.session_state:
    st.session_state.api_locked = False
if "api_key_val" not in st.session_state:
    st.session_state.api_key_val = ""

# Hashing the password directly in memory so "2026" is never written in plain text
EXPECTED_HASH = hashlib.sha256(bytes([50, 48, 50, 54])).hexdigest() 

col_api, col_lock = st.sidebar.columns([4, 1])
with col_api:
    gemini_api_key = st.text_input(
        "API", 
        type="password", 
        disabled=st.session_state.api_locked, 
        value=st.session_state.api_key_val
    )
    if not st.session_state.api_locked:
        st.session_state.api_key_val = gemini_api_key
with col_lock:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) # Aligns lock icon with input box
    lock_icon = "🔒" if st.session_state.api_locked else "🔓"
    if st.button(lock_icon):
        st.session_state.show_passcode = not st.session_state.get("show_passcode", False)

if st.session_state.get("show_passcode", False):
    pass_input = st.sidebar.text_input("Passcode", type="password")
    if st.sidebar.button("Submit"):
        if hashlib.sha256(pass_input.encode()).hexdigest() == EXPECTED_HASH:
            st.session_state.api_locked = not st.session_state.api_locked
            st.session_state.show_passcode = False
            st.rerun()
        else:
            st.sidebar.error("Incorrect Passcode!")

if not db:
    st.info("� **Please upload your Octoparse database file in the sidebar first to proceed.**")
else:
    st.subheader("2. 🏏 Set Up Your Teams")
    
    # Dynamically select number of teams
    num_teams = st.number_input("How many teams are competing?", min_value=1, max_value=10, value=2, step=1)
    
    # Create beautiful tabs for each team
    tabs = st.tabs([f"Team {i+1}" for i in range(num_teams)])
    
    # Dictionary to keep track of final points for the leaderboard chart
    team_scores = {}
    
    if "team_data" not in st.session_state:
        st.session_state.team_data = {}
        
    for i, tab in enumerate(tabs):
        with tab:
            team_key = f"team_{i}"
            if team_key not in st.session_state.team_data:
                st.session_state.team_data[team_key] = {"last_file": None, "raw_text": None, "extracted_names": []}
            
            team_state = st.session_state.team_data[team_key]
            
            col_name, col_upload = st.columns([1, 2], gap="large")
            with col_name:
                team_name = st.text_input(f"✏️ Edit Team {i+1} Name", value=f"Team {i+1}", key=f"name_{team_key}")
            with col_upload:
                uploaded_file = st.file_uploader(f"Upload Roster Image/PDF", type=["pdf", "jpg", "jpeg", "png"], key=f"file_{team_key}")
            
            if uploaded_file is not None:
                file_type = uploaded_file.name.split('.')[-1].lower()
                
                # Create a 2-column layout: Left side for image preview, Right side for calculation
                col_left, col_right = st.columns([1, 2], gap="large")
                
                with col_left:
                    if file_type in ['jpg', 'jpeg', 'png']:
                        st.image(uploaded_file, caption=f"{team_name} Roster", use_container_width=True)
                    elif file_type == 'pdf':
                        st.info("📄 PDF Document loaded.")
                        
                with col_right:
                    # Process file if it's new
                    if team_state["last_file"] != uploaded_file.name:
                        if not st.session_state.api_key_val:
                            st.warning(f"⚠️ Please enter your API Key in the sidebar to enable AI Extraction.")
                        else:
                            try:
                                genai.configure(api_key=st.session_state.api_key_val.strip())
                                
                                # Dynamically check which models your specific Google account/region has access to
                                available_models = [m.name for m in genai.list_models()]
                                if 'models/gemini-2.5-flash' in available_models:
                                    model_name = 'gemini-2.5-flash'
                                elif 'models/gemini-2.0-flash' in available_models:
                                    model_name = 'gemini-2.0-flash'
                                elif file_type == 'pdf':
                                    model_name = 'gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else 'gemini-pro'
                                else:
                                    model_name = 'gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else 'gemini-1.5-flash'
                                    
                                model = genai.GenerativeModel(model_name)
                                text = ""
                                with st.spinner(f"🤖 AI ({model_name}) is analyzing the roster for {team_name}..."):
                                    if file_type == 'pdf':
                                        reader = PyPDF2.PdfReader(uploaded_file)
                                        raw_text = ""
                                        for page in reader.pages:
                                            raw_text += page.extract_text() + "\n"
                                        
                                        prompt = "Extract only the names of the cricket players from this text. Ignore roles (batsman, bowler, etc.), numbers, or team names. Return a clean, comma-separated list of player names.\n\nText:\n" + raw_text
                                        response = model.generate_content(prompt)
                                        text = response.text
                                    elif file_type in ['jpg', 'jpeg', 'png']:
                                        image = Image.open(uploaded_file)
                                        prompt = "Extract only the names of the cricket players from this image. Ignore roles (batsman, bowler, wicketkeeper, bench, etc.), numbers, emojis, or team names. Return a clean, comma-separated list of player names."
                                        response = model.generate_content([prompt, image])
                                        text = response.text
                                        
                                if text:
                                    team_state["raw_text"] = text
                                    search_text = text.lower()
                                    extracted_names = []
                                    
                                    # Pass 1: Strict Exact Full Name Matching
                                    for player in db.keys():
                                        pattern = r'\b' + re.escape(player) + r'\b'
                                        if re.search(pattern, search_text):
                                            extracted_names.append(player)
                                            search_text = re.sub(pattern, ' ', search_text)
                                            
                                    # Pass 2: Surname Matching
                                    for player in db.keys():
                                        if player in extracted_names:
                                            continue
                                        parts = player.split()
                                        if len(parts) > 1:
                                            surname = parts[-1]
                                            if len(surname) >= 3:
                                                pattern = r'\b' + re.escape(surname) + r'\b'
                                                if re.search(pattern, search_text):
                                                    extracted_names.append(player)
                                                    search_text = re.sub(pattern, ' ', search_text)
                                    
                                    team_state["extracted_names"] = list(set(extracted_names))
                                    st.session_state[f"multi_{team_key}"] = team_state["extracted_names"].copy()
                                    team_state["last_file"] = uploaded_file.name
                            except Exception as e:
                                st.error(f"Gemini API Error: {e}")
                            
                    if team_state["raw_text"] is not None:
                        with st.expander("👀 View Raw Extracted Text"):
                            st.text(team_state["raw_text"])
                            
                        st.markdown(f"### 🏏 Verify **{team_name}**")
                        
                        colA, colB = st.columns(2)
                        with colA:
                            if st.button("❌ Deselect All Players", key=f"clear_{team_key}"):
                                st.session_state[f"multi_{team_key}"] = []
                        with colB:
                            if st.button("🔄 Reset Extracted", key=f"reset_{team_key}"):
                                st.session_state[f"multi_{team_key}"] = team_state["extracted_names"].copy()
                                
                        # Initialize empty list if key not set
                        if f"multi_{team_key}" not in st.session_state:
                            st.session_state[f"multi_{team_key}"] = []
                            
                        selected_players = st.multiselect(
                            "Select Players:",
                            options=list(db.keys()), 
                            key=f"multi_{team_key}",
                            format_func=lambda x: x.title()
                        )
                        
                        total_points = sum([get_points(name, db) for name in selected_players])
                        team_scores[team_name] = total_points
                        
                        # Display the beautiful points metric
                        st.metric(label="🏆 Total Team Points", value=round(total_points, 1))
                        
                        with st.expander("Player Breakdown"):
                            for name in selected_players:
                                pts = get_points(name, db)
                                st.write(f"**{name.title()}**: {pts} pts")
                                
    st.divider()
    
    # Render the Leaderboard section if at least one team has a score
    if any(score > 0 for score in team_scores.values()):
        st.subheader("📊 Matchup Leaderboard")
        
        chart_data = pd.DataFrame(list(team_scores.items()), columns=['Team Name', 'Total Points'])
        
        base_chart = alt.Chart(chart_data).encode(
            x=alt.X('Team Name', sort=None, title="Teams"),
            y=alt.Y('Total Points', title="Points")
        )
        
        bars = base_chart.mark_bar(color='#E5D3B3', size=60, cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        
        text = base_chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,
            fontSize=16,
            color='white',
            fontWeight='bold'
        ).encode(text='Total Points')
        
        st.altair_chart(bars + text, use_container_width=True)
