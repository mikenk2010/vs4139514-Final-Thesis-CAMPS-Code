#!/bin/bash
# CAMPS seminar demo launcher (macOS: double-click this file, or `bash run_demo.command`).
# Starts the Streamlit app on http://localhost:8501 with Tab 1 (archived results) ready.
cd "$(dirname "$0")"

if [ -d .venv ]; then
  source .venv/bin/activate
fi

python3 -c "import streamlit, plotly, yaml, pandas" 2>/dev/null || {
  echo "Installing demo dependencies (streamlit, plotly, pyyaml, pandas)..."
  python3 -m pip install -q streamlit plotly pyyaml pandas scipy scikit-learn
}

[ -f results/demo_summary.json ] || python3 src/make_demo_summary.py
python3 src/build_showcase.py && open demo/showcase.html   # full-screen showcase (arrow keys; F = fullscreen)

echo
echo "Showcase opened in the browser (arrow keys to advance, M = switch model, F = fullscreen)."
echo "CAMPS explorer/live app starting at http://localhost:8501"
echo "Tab 1: featured case A, model GPT-4o  ->  Western 5 / SEA 7 / Neutral 7, BDS 0.94"
echo "Press Ctrl+C in this window to stop."
echo
exec python3 -m streamlit run src/demo_app.py --server.headless false --browser.gatherUsageStats false
