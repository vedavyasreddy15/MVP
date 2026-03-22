<<<<<<< HEAD
# Roster MVP 🏆 (IPL Fantasy Calculator)

Welcome to **Roster MVP**! This Streamlit web application allows you to automatically extract player rosters from images or PDFs using Google's Gemini AI, match them against your custom database, and compare matchup scores across multiple teams.

## Features
* **🤖 AI Image & PDF Extraction**: Upload a picture (JPG/PNG) or PDF of your team list. The app uses Google's Gemini AI (`gemini-1.5-flash`) to intelligently read the image, ignore roles/numbers, and extract a clean list of player names.
* **📊 Custom Database Integration**: Upload your own scraped data file (CSV or Excel, e.g., from Octoparse) to act as the master points database.
* **⚔️ Multi-Team Matchups**: Create multiple teams, process their rosters simultaneously, and instantly compare their total points.
* **📈 Interactive Leaderboards**: Automatically generates an Altair bar chart to visualize the winning teams.
* **🔒 Secure API Setup**: Built-in passcode-locked sidebar to safely store and use your Gemini API key during the session.

## Core Files
* `roster_mvp.py` - The main Streamlit Python application.
* `requirements.txt` - Python dependencies needed to run the app.

## Local Setup

### 1. Install Python Dependencies
Open your terminal/command prompt and run:
```bash
pip install -r requirements.txt
```

### 3. Run the App
Start the Streamlit development server by running:
```bash
streamlit run mvp_1.py
```

## Deployment
This app is fully configured to be deployed for free on **Streamlit Community Cloud**:
1. Upload `mvp_1.py`, `requirements.txt`, and `packages.txt` to a public GitHub repository. (Note: You can safely ignore/delete older files like `mvp_2` or duplicate requirements).
2. Go to share.streamlit.io and log in with GitHub.
3. Create a new app, link your GitHub repository, and select `mvp_1.py` as the Main file path.
4. Click **Deploy**! 

*Note: Streamlit will automatically read `packages.txt` to install the system-level Tesseract OCR, and `requirements.txt` for the Python packages.*

---
**Disclaimer**: This project relies on the live HTML structure of the official IPL stats page. If the website changes its layout or employs heavy JavaScript blocking, the web scraper may need adjustments.
=======
# Roster MVP 🏆 (IPL Fantasy Calculator)

Welcome to **Roster MVP**! This Streamlit web application allows you to automatically extract player rosters from images or PDFs using Google's Gemini AI, match them against your custom database, and compare matchup scores across multiple teams.

## Features
* **🤖 AI Image & PDF Extraction**: Upload a picture (JPG/PNG) or PDF of your team list. The app uses Google's Gemini AI (`gemini-1.5-flash`) to intelligently read the image, ignore roles/numbers, and extract a clean list of player names.
* **📊 Custom Database Integration**: Upload your own scraped data file (CSV or Excel, e.g., from Octoparse) to act as the master points database.
* **⚔️ Multi-Team Matchups**: Create multiple teams, process their rosters simultaneously, and instantly compare their total points.
* **📈 Interactive Leaderboards**: Automatically generates an Altair bar chart to visualize the winning teams.
* **🔒 Secure API Setup**: Built-in passcode-locked sidebar to safely store and use your Gemini API key during the session.

## Core Files
* `roster_mvp.py` - The main Streamlit Python application.
* `requirements.txt` - Python dependencies needed to run the app.

## Local Setup

### 1. Install Python Dependencies
Open your terminal/command prompt and run:
```bash
pip install -r requirements.txt
```

### 3. Run the App
Start the Streamlit development server by running:
```bash
streamlit run mvp_1.py
```

## Deployment
This app is fully configured to be deployed for free on **Streamlit Community Cloud**:
1. Upload `mvp_1.py`, `requirements.txt`, and `packages.txt` to a public GitHub repository. (Note: You can safely ignore/delete older files like `mvp_2` or duplicate requirements).
2. Go to share.streamlit.io and log in with GitHub.
3. Create a new app, link your GitHub repository, and select `mvp_1.py` as the Main file path.
4. Click **Deploy**! 

*Note: Streamlit will automatically read `packages.txt` to install the system-level Tesseract OCR, and `requirements.txt` for the Python packages.*

---
**Disclaimer**: This project relies on the live HTML structure of the official IPL stats page. If the website changes its layout or employs heavy JavaScript blocking, the web scraper may need adjustments.
>>>>>>> 2c9c55d39ea6ad239611d228b267afda17e2f23b
