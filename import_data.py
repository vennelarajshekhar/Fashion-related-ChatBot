import sqlite3
import pandas as pd

df = pd.read_excel("cit_national_ranks_cleaned.xlsx")

# 93 rows have their values shifted into the wrong columns, so drop them
good_labels = ["Best Seller", "Good Seller", "Average Seller", "Poor Seller"]
bad = (df["rank_label"].notna() & ~df["rank_label"].isin(good_labels)) | df["selling_price_INR"].isna()
df = df[~bad]

# make number columns real numbers and dates plain text
for col in ["rank_percentile", "review_count"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
for col in ["launch_on", "last_seen_date"]:
    df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")
for col in ["sku", "color", "product_color"]:
    df[col] = df[col].astype("string")

with sqlite3.connect("fashion.db") as conn:
    df.to_sql("cit_national_ranks", conn, if_exists="replace", index=False)

print("Saved", len(df), "rows")