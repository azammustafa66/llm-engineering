# LLM Engineering

Hands-on notebooks and scripts for learning to build with large language models.

## Setup

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies into a local .venv
uv sync

# Add your API keys
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

> Prefer `pip`? `pip install -r requirements.txt` works too.

## Contents

| Path | Description |
| --- | --- |
| [week-1/day1.ipynb](week-1/day1.ipynb) | First LLM calls: chat completions + summarizing a scraped web page. |
| [week-1/scraper.py](week-1/scraper.py) | Helper that fetches a URL and returns clean, text-only page content. |

## Running the notebooks

```bash
uv run jupyter lab
```

Then open a notebook under `week-1/` and run the cells top to bottom.

## Notes

- Secrets live in `.env`, which is git-ignored. Never commit real API keys.
- `.venv/`, `__pycache__/`, and other generated artifacts are git-ignored.
