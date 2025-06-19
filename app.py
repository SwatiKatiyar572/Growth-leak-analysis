from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    orders_file = request.files.get("orders")
    inventory_file = request.files.get("inventory")

    if not orders_file or not inventory_file:
        return "Both files are required.", 400

    try:
        orders = pd.read_csv(orders_file)
        inventory = pd.read_csv(inventory_file)

        # 1. % of users who ordered only once
        order_counts = orders.groupby("user_id")["order_id"].count()
        one_time_users = (order_counts == 1).sum()
        total_users = order_counts.count()
        one_time_user_pct = round((one_time_users / total_users) * 100, 2)

        # 2. Combo AOV vs Regular AOV
        orders["amount"] = pd.to_numeric(orders["amount"], errors="coerce")
        combo_aov = orders[orders["is_combo"].str.lower() == "yes"]["amount"].mean()
        regular_aov = orders[orders["is_combo"].str.lower() == "no"]["amount"].mean()

        # 3. % of expired stock
        inventory["expiration_date"] = pd.to_datetime(inventory["expiration_date"], errors="coerce")
        expired = inventory[inventory["expiration_date"] < datetime.now()]
        expired_qty = expired["quantity"].sum()
        total_qty = inventory["quantity"].sum()
        expired_pct = round((expired_qty / total_qty) * 100, 2)

        # 4. Top 3 expired products
        top_expired = expired.groupby("product_id")["quantity"].sum().sort_values(ascending=False).head(3).to_dict()

        results = {
            "one_time_user_pct": one_time_user_pct,
            "combo_aov": round(combo_aov, 2),
            "regular_aov": round(regular_aov, 2),
            "expired_pct": expired_pct,
            "top_expired": top_expired
        }

        return render_template("results.html", results=results)

    except Exception as e:
        return f"Error processing files: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
