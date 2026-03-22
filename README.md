# IPL Fantasy Calculator 🏏

Welcome to the **IPL Fantasy Calculator**! This Streamlit web application allows you to automatically calculate the total MVP points of your fantasy cricket team by simply uploading a document (PDF or Image) containing your players' names.

## Features
* **Live Web Scraping**: Automatically fetches the latest player MVP points directly from the official IPL website. No manual dataset maintenance required!
* **Optical Character Recognition (OCR)**: Upload a picture (JPG/PNG) of your handwritten or typed team list, and the app will read the names using Tesseract OCR.
* **PDF Support**: Upload a PDF document of your team roster, and the app will parse the text to extract player names.
* **Instant Calculation**: Matches extracted names with the live scraped database to calculate your team's total points.

## Core Files
* `mvp_1.py` - The main Streamlit Python application. (Acts as the `app.py`).
* `requirements.txt` - Python dependencies needed to run the app.
* `packages.txt` - System dependencies (Tesseract OCR) required by Streamlit Community Cloud for image processing.

## Local Setup

### 1. Install System Dependencies
If you want to read images locally on your own computer, you must install Tesseract OCR:
* **Windows**: Download the installer from the UB-Mannheim Tesseract wiki.
* **Mac**: Run `brew install tesseract` in your terminal.
* **Linux**: Run `sudo apt-get install tesseract-ocr`.

### 2. Install Python Dependencies
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

