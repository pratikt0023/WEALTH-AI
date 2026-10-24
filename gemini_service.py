import os
from typing import Any

def _demo_advice(context: dict[str, Any]) -> dict[str, Any]:
    income = max(0.0, float(context.get("income", 0) or 0))
    other_income = max(0.0, float(context.get("otherIncome", 0) or 0))
    expenses = context.get("expenses") or {}
    total_expenses = sum(max(0.0, float(v or 0)) for v in expenses.values())
    total_income = income + other_income
    balance = total_income - total_expenses
    rate = (balance / total_income * 100) if total_income else 0
    tips = []
    if total_income <= 0:
        tips.append("Enter your monthly income to get a more useful budget.")
    elif balance < 0:
        tips.append("Your listed expenses exceed income. Start by reviewing flexible categories and essential bills.")
    elif rate < 10:
        tips.append("Try setting aside a small automatic amount on payday, then gradually increase it.")
    else:
        tips.append("Your current budget shows a positive balance. Consider assigning it to a clear savings goal.")
    largest = sorted(
        ((str(k), max(0.0, float(v or 0))) for k, v in expenses.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    if largest and total_expenses:
        category, amount = largest[0]
        tips.append(f"Review '{category}' first because it is your largest listed expense ({amount:,.0f} per month).")
    goal = context.get("financialGoal")
    if goal:
        tips.append(f"Keep your goal visible: {goal}. Compare progress each month rather than making sudden changes.")
    tips.append("These are general educational suggestions; verify important decisions against your real circumstances.")
    return {
        "mode": "demo",
        "summary": f"Your estimated monthly balance is {balance:,.2f}. Your estimated savings rate is {rate:.1f}%.",
        "suggestions": tips,
        "budget": {
            "income": round(total_income, 2),
            "expenses": round(total_expenses, 2),
            "balance": round(balance, 2),
            "savingsRate": round(rate, 1),
        },
    }

def generate_advice(context: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return _demo_advice(context)
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = (
            "You are a careful personal budgeting educator. Provide general educational budgeting "
            "insights, not investment/tax/legal advice. Do not guarantee outcomes. Be concise and "
            "practical. Treat all amounts as user-supplied monthly figures. Context JSON: "
            f"{context}. Return a concise summary followed by 3-5 actionable suggestions."
        )
        response = client.models.generate_content(model=model, contents=prompt)
        text = (getattr(response, "text", None) or "").strip()
        if not text:
            return _demo_advice(context)
        return {"mode": "gemini", "summary": text, "suggestions": [], "budget": _demo_advice(context)["budget"]}
    except Exception:
        # Avoid exposing internal provider errors or secrets to clients.
        result = _demo_advice(context)
        result["mode"] = "demo-fallback"
        return result

def answer_question(question: str, context: dict[str, Any]) -> dict[str, str]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            prompt = (
                "Answer as a budgeting educator in simple language. Do not provide specific "
                "investment, tax, or legal advice; do not guarantee results. Keep it under 180 words. "
                f"Budget context: {context}\nUser question: {question}"
            )
            response = client.models.generate_content(model=model, contents=prompt)
            answer = (getattr(response, "text", None) or "").strip()
            if answer:
                return {"answer": answer, "mode": "gemini"}
        except Exception:
            pass
    return {
        "answer": (
            "Demo answer: start by comparing monthly income with essential and flexible expenses. "
            "Choose one realistic savings target, review your spending weekly, and adjust the plan "
            "based on actual results. Add a Gemini API key on the backend for personalized AI responses. "
            "This is educational information, not professional financial advice."
        ),
        "mode": "demo",
    }
