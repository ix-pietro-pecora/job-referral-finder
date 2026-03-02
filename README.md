# Job Referral Finder

Find open roles at companies where you have connections — so you can ask for a referral at the right time.

**[Live demo →](https://your-app.streamlit.app)** *(update after deploy)*

## The Problem

Getting a referral requires you or your contact to constantly watch their company's job board. Most people miss the right moment. This tool does the watching for you.

## How It Works

1. Enter the role you're targeting (e.g. "Product Manager")
2. Enter companies where you know someone
3. The app checks their job boards and uses AI to filter relevant roles
4. Optionally upload your resume for personalized match scores

## Features

- Checks Greenhouse and Lever job boards automatically (covers most tech companies)
- Claude AI filters roles by relevance — no noise
- Resume upload → match score + talking points for your referral ask
- Works with 20+ pre-seeded companies, plus auto-detection for others

## Run Locally

```bash
git clone https://github.com/yourusername/job-referral-finder
cd job-referral-finder

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Add your Anthropic API key to .env

streamlit run app.py
```

## Deploy

This app is designed for [Streamlit Community Cloud](https://streamlit.io/cloud) (free):

1. Push to GitHub
2. Go to share.streamlit.io → New app → select this repo
3. Add `ANTHROPIC_API_KEY` in the Secrets section
4. Deploy

## Adding More Companies

Edit `discovery/known_companies.json`:

```json
{
  "yourcompany": { "ats": "greenhouse", "slug": "yourcompany" }
}
```

Find a company's slug by checking `boards.greenhouse.io/{slug}` or `jobs.lever.co/{slug}`.

## Roadmap

- [ ] Workday support
- [ ] Weekly email digest via GitHub Actions
- [ ] Auto-draft referral LinkedIn DM
- [ ] Save search history

## Stack

- [Streamlit](https://streamlit.io) — UI
- [Anthropic Claude](https://anthropic.com) — job matching and resume scoring
- [Greenhouse API](https://developers.greenhouse.io) — job data
- [Lever API](https://hire.lever.co/developer/postings) — job data
- [pdfplumber](https://github.com/jsvine/pdfplumber) — resume parsing
