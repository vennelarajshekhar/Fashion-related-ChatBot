# Fashion Dataset Chat Agent (local starter)

## Files
- `app.py`: Streamlit chatbot with dataset scope check, SQL planning, SQL validation, and evidence-grounded answers.
- `import_data.py`: imports the existing Excel file into SQLite.
- `requirements.txt`: Python dependencies.
- `.env.example`: template for your API key.

## Before running
Keep your existing Excel file here:
`data/cit_national_ranks_cleaned.xlsx`

Copy `.env.example` to `.env`, then add your actual OpenAI API key.
Never share or commit `.env`.

## Install dependencies
Open the terminal in this folder and run:
`python -m pip install -r requirements.txt`

## Import dataset
Run:
`python import_data.py`

Expected dataset size for this project: 8,108 records and 28 columns.

## Start the app
Run:
`python -m streamlit run app.py`

Streamlit will print a local URL, usually `http://localhost:8501`.
Open it in your browser.

## Test
1. `How many records are in the dataset?`
2. `What brands are present in the dataset?`
3. `Show the top 10 products by popularity.`
4. `Tell me a joke.` (should be rejected)
5. `What is the population of Bengaluru?` (should be rejected unless supported by the dataset)

The exact answer depends on the actual values and columns in the Excel dataset.

## Safety notes
- The database is opened in SQLite read-only mode by the chatbot.
- Only one SELECT statement is accepted.
- SQL references to other tables or unknown columns are rejected.
- Scope checking and answer generation use the OpenAI API, so a valid API key and internet access are required.
- This is a starter implementation, not a complete security boundary for an internet-facing production service. Review and test before deploying.
