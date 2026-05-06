# wh-coke-short

Wolf Hill internal pitch site — Coca-Cola Consolidated (COKE) short thesis. Streamlit app, password-gated.

## Local setup

```powershell
cd "C:\Users\JoshuaLehrman\Wolf Hill Capital Management LLC\Shared - Documents\Josh\COKE\Site"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`. Enter the password from `.streamlit/secrets.toml`.

## Deploy (Streamlit Community Cloud)

1. Push repo to GitHub (public).
2. Connect on `share.streamlit.io`.
3. In the app settings, paste contents of `.streamlit/secrets.toml` into the Secrets field.
4. Deploy. The live URL is password-gated.

## Updating the model

**Local dev:** the app reads from the live model at
`...\COKE\Models\WH COKE Model v04.29.2026.xlsx` directly. Save in Excel → reload the
browser → Base scenario reflects new numbers automatically (mtime-keyed cache).

**Bull/Bear scenarios** are captured separately because openpyxl can't recalculate
formulas. After you change Bull/Bear assumptions in the model:

1. Click the **↻ Refresh** button next to the scenario selector, OR
2. From CLI: `python regenerate_scenarios.py`

That uses Excel COM (win32com) to flip `Summary!D4` to "1 - Bull" / "3 - Bear",
recalculate, capture the Summary outputs, and write them to `data/scenarios.json`.
Excel closes without saving — model file is never modified.

**Deployed to Streamlit Cloud:** uses the bundled copy in `data/`. To push updated
numbers, copy the live model into `data/`, commit, push.

## Structure

- `app.py` — entry, password gate, page layout
- `loaders.py` — Excel reads, all `@st.cache_data` wrapped
- `charts.py` — Plotly chart functions
- `sections.py` — Streamlit section renderers
- `data/` — model file
- `.streamlit/config.toml` — theme
- `.streamlit/secrets.toml` — password (gitignored)
