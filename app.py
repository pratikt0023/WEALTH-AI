import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from gemini_service import generate_advice, answer_question

load_dotenv()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
allowed_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
CORS(app, resources={r"/api/*": {"origins": [allowed_origin, "http://127.0.0.1:5173"]}})

def clean_context(data):
    data = data if isinstance(data, dict) else {}
    expenses_in = data.get("expenses") if isinstance(data.get("expenses"), dict) else {}
    expenses = {}
    for key, value in expenses_in.items():
        try:
            amount = float(value)
            if amount >= 0 and amount < 1_000_000_000:
                expenses[str(key)[:60]] = amount
        except (TypeError, ValueError):
            continue
    def number(key):
        try:
            value = float(data.get(key, 0) or 0)
            return value if 0 <= value < 1_000_000_000 else 0
        except (TypeError, ValueError):
            return 0
    return {
        "income": number("income"),
        "otherIncome": number("otherIncome"),
        "expenses": expenses,
        "financialGoal": str(data.get("financialGoal", "Build savings"))[:200],
        "targetAmount": number("targetAmount"),
        "currentSavings": number("currentSavings"),
        "targetDate": str(data.get("targetDate", ""))[:30],
        "riskPreference": str(data.get("riskPreference", "Balanced"))[:40],
        "notes": str(data.get("notes", ""))[:500],
    }

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "WEALTH AI API"})

@app.post("/api/financial-advice")
def financial_advice():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON request body."}), 400
    return jsonify(generate_advice(clean_context(data)))

@app.post("/api/ask")
def ask():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON request body."}), 400
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400
    if len(question) > 1000:
        return jsonify({"error": "Question must be 1000 characters or fewer."}), 400
    return jsonify(answer_question(question, clean_context(data.get("context", {}))))

@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Request too large."}), 413

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
