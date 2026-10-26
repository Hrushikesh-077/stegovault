# StegoVault - Data Hiding in Image Using Steganography
Vel Tech - 10214CS601 Minor Project-I

LSB steganography with optional AES-256 password protection, quality metrics
(MSE/PSNR), a Streamlit web UI and a command-line tool.

## Setup (Windows)
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

## Run the web app
    streamlit run app.py          (opens http://localhost:8501)

## Command line
    python cli.py embed cover.png out.png "my secret" -p mypassword
    python cli.py extract out.png -p mypassword

## Tests
    pip install pytest
    pytest

## Files
- stego.py - core engine (embed / extract / AES / MSE+PSNR)
- app.py   - Streamlit UI (OpenCV used for PSNR check + change heat-map)
- cli.py   - terminal interface
- tests/   - automated tests
