# Fashion Dataset Chat Agent

A Streamlit chatbot that answers questions about the supplied fashion-product dataset. The app is designed to ground responses in the records retrieved from the local database and refuse questions unrelated to the dataset.

## Project Overview

The application uses an LLM to:
1. Check whether a question is related to the fashion dataset.
2. Generate read-only SQL queries to retrieve relevant records.
3. Explain the returned database results in natural language.
4. Display product cards with images and product-page links when those fields are available.

**LLM:** OpenAI `gpt-4o-mini`

## Tech Stack

- Python
- Streamlit
- OpenAI API (`gpt-4o-mini`)
- SQLite
- pandas
- `python-dotenv`
- `sqlglot`
- `openpyxl`

## Dataset

- **Source file expected:** `data/cit_national_ranks_cleaned.xlsx`
- **Database file generated locally:** `fashion.db`
- **Table:** `cit_national_ranks`
- **Expected dataset size:** 8,108 records and 28 columns (verify after importing your copy).

Known columns include `_id`, `channel_id`, `locale_id`, `sku`, `color`, `product_color`, `category_id`, `department_id`, `product_id`, `brand`, `product_name`, `rank_absolute`, `rank_percentile`, `rank_label`, `niche_score`, `popularity`, `discount`, `rating`, `rating_count`, `review_count`, `launch_on`, `last_seen_date`, `pdp_url`, `feature_image`, `mrp_USD`, `mrp_INR`, `selling_price_USD`, and `selling_price_INR`.

> The Excel dataset and `fashion.db` may not be included in the repository. Obtain the dataset from the project owner or another authorized source. Do not commit private or restricted data.

## Requirements

- Git
- Python (Python 3.11 or 3.12 recommended)
- A valid OpenAI API key
- The authorized source Excel dataset

## Setup (Windows PowerShell)

### 1. Clone the repository

```powershell
git clone https://github.com/vennelarajshekhar/Fashion-related-ChatBot.git
cd Fashion-related-ChatBot
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, follow your organization's approved Python setup instructions or use the virtual environment's Python executable directly.

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the API key

Create a local `.env` file from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set your own key:

```dotenv
OPENAI_API_KEY=your_actual_openai_api_key
```

If the application also expects a `DATABASE_URL`, configure it according to the current code. For the SQLite database described here, the value may be:

```dotenv
DATABASE_URL=sqlite:///fashion.db
```

Do not commit `.env`, publish the API key, or include it in screenshots. Each developer should use their own authorized API key.

### 5. Add the dataset

Place the authorized Excel file at:

```text
data/cit_national_ranks_cleaned.xlsx
```

Keep the path and filename consistent with the import script. If the dataset was not provided with the repository, ask the project owner for access.

### 6. Create the SQLite database

Run the import script, if it is present in the repository:

```powershell
python import_data.py
```

This should create `fashion.db` and populate the `cit_national_ranks` table. Confirm the output reports the expected record and column counts. If your repository uses a different import-script name, check the project files and use the actual script.

### 7. Run the chatbot

```powershell
python -m streamlit run app.py
```

Open the local URL printed in the terminal, usually `http://localhost:8501`.

## Example Questions to Test

### Dataset-related questions

- How many records are in the dataset?
- Which brands are present?
- Show the top 10 products by popularity.
- Which products have the highest ratings?
- Show products in a particular color.
- What are the prices of products from a specific brand?

The answer depends on the values available in the dataset and the current implementation.

### Out-of-scope questions

- Tell me a joke.
- What is the population of Bengaluru?
- Explain a general topic unrelated to the dataset.

These should be refused rather than answered using general knowledge.

## Guardrails and Limitations

- Responses should be grounded in database query results.
- Unrelated questions should be rejected by the scope check.
- The chatbot's database connection is intended to be read-only.
- Generated SQL should be restricted to safe read-only queries and the expected table/columns.
- LLM-based guardrails can make mistakes. Test borderline questions and inspect SQL/results when an answer looks incorrect.
- This is a project/demo implementation, not a complete production security boundary. Perform a security review before exposing it publicly.

## Troubleshooting

| Problem | What to check |
|---|---|
| Missing or invalid API key | Confirm `.env` exists in the project root and `OPENAI_API_KEY` is valid. Restart Streamlit after editing it. |
| Excel file not found | Confirm the file is at `data/cit_national_ranks_cleaned.xlsx`. |
| Database not found | Run `python import_data.py` after placing the Excel file. |
| Missing Python package | Activate the virtual environment and run `python -m pip install -r requirements.txt`. |
| Streamlit command not found | Use `python -m streamlit run app.py`. |
| Incorrect answer | Check the generated SQL, returned rows, column names, and missing values. |

## Security

Ensure `.gitignore` excludes at least:

```gitignore
.env
fashion.db
.venv/
venv/
__pycache__/
*.pyc
```

If an API key was ever committed or exposed, revoke/rotate it. Removing it from the latest commit does not remove it from Git history.

## Quick Start

1. Clone the repository.
2. Install `requirements.txt`.
3. Create `.env` with your own OpenAI API key.
4. Obtain the authorized Excel dataset.
5. Run `python import_data.py`.
6. Run `python -m streamlit run app.py`.
7. Test dataset-related questions and out-of-scope refusals.
