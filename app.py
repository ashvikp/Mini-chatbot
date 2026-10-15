
import os

from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({
            "reply": "The AI API key is not configured yet."
        }), 500

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])

    # Keep the input small and accept only valid chat messages.
    if not isinstance(messages, list) or not messages:
        return jsonify({"reply": "Please enter a message."}), 400

    history = []
    for item in messages[-12:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")

        if role not in ("user", "assistant"):
            continue
        if not isinstance(content, str):
            continue
        if len(content) > 4000:
            continue

        history.append({"role": role, "content": content})

    if not history or history[-1]["role"] != "user":
        return jsonify({"reply": "Please send a valid message."}), 400

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MiniGPT, a friendly and helpful AI "
                        "assistant. Explain things clearly and simply."
                    )
                },
                *history
            ]
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply or "I couldn't generate a reply."})

    except Exception:
        app.logger.exception("AI request failed")
        return jsonify({
            "reply": "Sorry, something went wrong. Check the server logs."
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
