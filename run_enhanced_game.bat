@echo off
cd /d "%~dp0"
echo Starting Texas Hold'em GTO Trainer (Enhanced UI)...
python -m streamlit run texas_holdem_enhanced_ui.py --server.port 8501 --theme.base dark
pause