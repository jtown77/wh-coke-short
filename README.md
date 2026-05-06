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

1. Drop the new `.xlsx` into `data/`.
2. Update the `MODEL_FILE` constant in `loaders.py` if the filename changed.
3. Commit and push — Streamlit Cloud auto-redeploys.

## Structure

- `app.py` — entry, password gate, page layout
- `loaders.py` — Excel reads, all `@st.cache_data` wrapped
- `charts.py` — Plotly chart functions
- `sections.py` — Streamlit section renderers
- `data/` — model file
- `.streamlit/config.toml` — theme
- `.streamlit/secrets.toml` — password (gitignored)
