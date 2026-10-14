import json
import os
import sqlite3

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
DB_PATH = "fashion.db"
TABLE = "cit_national_ranks"
MODEL = "gpt-4o-mini"  # use "gpt-4o" if answers are wrong

NOTES = """Column notes:
- rank_absolute: lower number = better rank. rank_percentile: higher = better.
- rank_label is one of: Best Seller, Good Seller, Average Seller, Poor Seller.
- discount is a percentage (0-100).
- selling_price_USD / selling_price_INR are the real prices, mrp_* are list prices.
- category_id, department_id, channel_id are numbers only (no names exist).
- rating, rating_count, review_count are often NULL.
- launch_on and last_seen_date are text like 2026-09-03.
- Several rows can be the same product in different colors.
- There is no style/fabric/length column. Words like High Neck, Mini, Maxi, Satin, Linen,
  Strapless, Floral are inside product_name, so search them with product_name LIKE '%high neck%'.
- Searching products by color: check both color and product_color with LIKE."""


def connect():
    # read-only, so the model can never change the data
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def get_schema():
    with connect() as conn:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({TABLE})")]
        brands = [r[0] for r in conn.execute(f"SELECT DISTINCT brand FROM {TABLE}")]
        colors = [r[0] for r in conn.execute(f"SELECT DISTINCT color FROM {TABLE} WHERE color IS NOT NULL")]
    return f"Table: {TABLE}\nColumns: {cols}\nBrands: {brands}\nColors: {colors}\n{NOTES}"


def ask(client, system, history, user, as_json=True):
    kwargs = {"response_format": {"type": "json_object"}} if as_json else {}
    # system prompt + last 10 chat messages (user/assistant) + the new question
    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": user}]
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
        **kwargs,
    )
    text = resp.choices[0].message.content
    return json.loads(text) if as_json else text


def check_question_scope(client, schema, history, question):
    system = schema + """\n\nYou check if a question can be answered from a fashion product table.
Return JSON: {"allowed": true or false, "reason": "short reason"}
Searching products by words in product_name (style, fabric, length like "high neck",
"mini", "satin") is ALLOWED, because product_name contains those words.
Allow anything that can be answered by counting, filtering, sorting or averaging the
columns (brands, prices, discounts, ranks, popularity, ratings, colors, dates, products),
questions about the columns themselves, and follow-ups to the chat history.
Reject only unrelated questions (jokes, general knowledge) or things the table
cannot contain (sales revenue, stock levels, customers). If unsure, allow."""
    result = ask(client, system, history, question)
    return result.get("allowed", False), result.get("reason", "")


def plan_queries(client, schema, history, question):
    system = schema + f"""\n\nYou write SQLite queries for the table {TABLE}.
Return JSON: {{"queries": [{{"purpose": "...", "sql": "..."}}]}}
Rules:
- 1 to 3 SELECT queries, only on {TABLE}, only real column names.
- No SELECT *. Pick the columns needed. Include product_name and brand for products.
- Whenever you return products, ALSO include feature_image and pdp_url (the app shows them as pictures and links).
- Use LIMIT 20 for lists.
- For style/fabric/length words (high neck, mini, satin...) use product_name LIKE '%word%'.
  If the user gives two words like "high neck", also try the hyphen form: product_name LIKE '%high neck%' OR product_name LIKE '%high-neck%'.
- For highest/lowest/best questions, skip NULLs (WHERE col IS NOT NULL) and return a few top rows.
- If a price has no currency, return both USD and INR.
- Use the exact brand spelling from the schema.
- If the question is a follow-up (e.g. "show me below 10,000", "what about Zara?"),
  KEEP the filters from the earlier questions (like color or dress type) and add the new one.
  The earlier SQL is shown in the chat history."""
    result = ask(client, system, history, question)
    return result.get("queries", [])[:3]


def run_query(sql):
    sql = sql.strip().rstrip(";")
    if not sql.lower().startswith(("select", "with")) or ";" in sql:
        raise ValueError("Only a single SELECT query is allowed.")
    with connect() as conn:
        cur = conn.execute(sql)
        rows = cur.fetchmany(50)
        columns = [d[0] for d in cur.description]
    return {"columns": columns, "rows": rows}


def final_answer(client, history, question, results):
    system = """Answer the question using ONLY the SQL results given.
Give the direct answer first, then short details. Say USD or INR for prices.
If the results are empty, say the dataset does not have that information.
Product pictures and links are shown by the app under your answer, so do not write URLs."""
    user = f"{question}\n\nSQL results:\n{json.dumps(results, default=str)}"
    return ask(client, system, history, user, as_json=False)


def get_products(results):
    """Rows that have an image or link, to show as pictures (max 8, no duplicates)."""
    items, seen = [], set()
    for r in results:
        for row in r["result"]["rows"]:
            d = dict(zip(r["result"]["columns"], row))
            key = d.get("pdp_url") or d.get("feature_image")
            if key and key not in seen:
                seen.add(key)
                items.append(d)
    return items[:8]


def show_products(items):
    cols = st.columns(4)
    for i, d in enumerate(items):
        with cols[i % 4]:
            if d.get("feature_image"):
                st.image(d["feature_image"])
            st.caption(f"{d.get('product_name', '')} - {d.get('brand', '')}")
            if d.get("pdp_url"):
                st.markdown(f"[View product]({d['pdp_url']})")


def without_urls(results):
    """Remove long URLs before sending results to the model (saves tokens)."""
    short = []
    for r in results:
        keep = [i for i, c in enumerate(r["result"]["columns"]) if c not in ("feature_image", "pdp_url")]
        short.append({
            "purpose": r["purpose"],
            "sql": r["sql"],
            "result": {
                "columns": [r["result"]["columns"][i] for i in keep],
                "rows": [[row[i] for i in keep] for row in r["result"]["rows"]],
            },
        })
    return short


# ---------------- Streamlit UI ----------------
st.title("👗 Fashion Dataset Chat Agent")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Add OPENAI_API_KEY to your .env file.")
    st.stop()

client = OpenAI(api_key=api_key)
schema = get_schema()

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("products"):
            show_products(m["products"])

question = st.chat_input("Ask a question about the dataset...")

if question:
    with st.chat_message("user"):
        st.markdown(question)

    # last 10 messages as chat history, with the SQL each answer used
    history = []
    for m in st.session_state.messages[-10:]:
        text = m["content"]
        if m.get("sql"):
            text += "\n(SQL used: " + " | ".join(m["sql"]) + ")"
        history.append({"role": m["role"], "content": text})
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        try:
            sqls, products = [], []
            allowed, reason = check_question_scope(client, schema, history, question)
            if not allowed:
                answer = f"I can only answer questions about this dataset. ({reason})"
            else:
                results = []
                for q in plan_queries(client, schema, history, question):
                    results.append({"purpose": q["purpose"], "sql": q["sql"], "result": run_query(q["sql"])})
                sqls = [r["sql"] for r in results]
                answer = final_answer(client, history, question, without_urls(results))
                products = get_products(results)
                with st.expander("SQL used"):
                    for r in results:
                        st.code(r["sql"], language="sql")
        except Exception as e:
            answer = f"Something went wrong: {e}"
        st.markdown(answer)
        if products:
            show_products(products)
    st.session_state.messages.append({"role": "assistant", "content": answer, "sql": sqls, "products": products})