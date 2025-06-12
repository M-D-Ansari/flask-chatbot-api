from flask_cors import CORS

from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import numpy as np
import pickle
import json
import os
from datetime import datetime
from google.genai import types, Client
from google.api_core import retry
import re
CORS(app)

app = Flask(__name__)
app.secret_key = "MySecretKey1194"

client = Client(api_key="AIzaSyC_Rxw2816l5IU0N3c7sZFoLnhsi3qOEiA")

SESSIONS_FILE = "session.json"

def load_sessions():
    if not os.path.exists(SESSIONS_FILE) or os.path.getsize(SESSIONS_FILE) == 0:
        return {"sessions": []}
    with open(SESSIONS_FILE, "r") as f:
        return json.load(f)

def save_sessions(data):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def create_new_session(user_name):
    return {
        "session_id": datetime.now().isoformat(),
        "user_name": user_name,
        "messages": []
    }

def get_session_by_id(session_id, sessions_data):
    for s in sessions_data.get("sessions", []):
        if s["session_id"] == session_id:
            return s
    return None

with open("models/vector_store.pkl", "rb") as f:
    formatted_df = pickle.load(f)

def is_retriable(e):
    return hasattr(e, "code") and e.code in {429, 500, 503}

@retry.Retry(predicate=is_retriable, timeout=300.0)
def embed_fn(text: str) -> list[float]:
    response = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text,
        config=types.EmbedContentConfig(task_type="classification")
    )
    return response.embeddings[0].values

def retrieve_similar_responses(query, top_k=3):
    query_vec = np.array(embed_fn(query))
    similarities = []

    for _, row in formatted_df.iterrows():
        sim_score = np.dot(query_vec, np.array(row["embedding"]))
        similarities.append({
            "user": row["user"],
            "therapist": row["therapist"],
            "score": sim_score
        })

    return sorted(similarities, key=lambda x: x["score"], reverse=True)[:top_k]

def extract_name(message):
    match = re.search(r"my name is ([a-zA-Z]+)", message, re.IGNORECASE)
    return match.group(1) if match else None

def mental_health_rag_response(query):
    extracted_name = extract_name(query)
    if extracted_name:
        session['user_name'] = extracted_name.capitalize()

    remembered_name = session.get("user_name", "Guest")
    session_id = session.get("session_id", None)

    sessions_data = load_sessions()

    current_session = get_session_by_id(session_id, sessions_data) if session_id else None

    history = ""
    if current_session and "messages" in current_session:
        for msg in current_session["messages"]:
            role = "User" if msg["sender"] == "user" else "Therapist"
            history += f"{role}: {msg['text']}\n"

    top_matches = retrieve_similar_responses(query, top_k=3)
    context = "\n".join([
        f"User: {item['user']}\nTherapist: {item['therapist']}"
        for item in top_matches
    ])

    prompt = f"""
You are Thera, a kind and empathetic mental health therapist.

Your job is to respond to the user’s latest message while:
- remembering the user's name from earlier if provided,
- referencing accurate past conversation from history,
- using relevant context examples.
- Dont reply topics which are not related to mental health and decline politely.
- If the user has not provided a name, use "Guest".
- If the user has provided a name, use it in your response.
- Do not mention the user's name in your response if it is not provided.
- Recommend helpful resources or coping strategies when appropriate.
- Keep responses concise and focused on the user's needs.
- Always be supportive and non-judgmental.
- When needed you can suggest the user general medication or therapy options, but do not prescribe specific treatments.
- Try to avoid repeating the same suggestions or responses.



Remembered name: {remembered_name}

Chat history:
{history}

Relevant examples:
{context}

Latest message from user:
{query}

Reply ONLY in the following JSON format:

{{
  "response": "Therapist's message",
  "suggestions": ["suggestion 1", "suggestion 2"]
}}
"""

    try:
        gemini_response = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt
        )
        raw_output = gemini_response.candidates[0].content.parts[0].text.strip()

        if raw_output.startswith("```"):
            raw_output = raw_output.strip("`").strip()
            if raw_output.lower().startswith("json"):
                raw_output = raw_output[4:].strip()

        parsed = json.loads(raw_output)
        return parsed

    except json.JSONDecodeError:
        print("❌ JSON parse error. Raw output:", raw_output)
        return {
            "response": "I'm having trouble understanding that. Could you rephrase?",
            "suggestions": ["Say it differently", "Try asking in another way"]
        }

    except Exception as e:
        print("❌ Gemini error:", e)
        return {
            "response": "Something went wrong. Please try again shortly.",
            "suggestions": ["Try refreshing the page", "Give it another try later"]
        }

@app.route("/")
def index():
    session.clear()

    user_name = "Guest"

    sessions_data = load_sessions()
    new_session = create_new_session(user_name)
    sessions_data["sessions"].append(new_session)
    session["session_id"] = new_session["session_id"]
    session["user_name"] = user_name

    save_sessions(sessions_data)

    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("query", "")
    if not user_input:
        return jsonify({"error": "Empty query"}), 400

    response_data = mental_health_rag_response(user_input)

    user_name = session.get("user_name", "Guest")
    session_id = session.get("session_id")

    sessions_data = load_sessions()

    if session_id:
        current_session = get_session_by_id(session_id, sessions_data)
    else:
        current_session = None

    if not current_session or len(current_session["messages"]) > 50:
        current_session = create_new_session(user_name)
        sessions_data["sessions"].append(current_session)
        session["session_id"] = current_session["session_id"]

    current_session["messages"].append({"sender": "user", "text": user_input})
    current_session["messages"].append({"sender": "bot", "text": response_data["response"]})

    save_sessions(sessions_data)
    return jsonify(response_data)

def get_latest_session():
    sessions_data = load_sessions()
    if sessions_data["sessions"]:
        return sessions_data["sessions"][-1]
    return None

@app.route("/latest_session", methods=["GET"])
def latest_session():
    session_data = get_latest_session()
    return jsonify(session_data if session_data else {"messages": []})

if __name__ == "__main__":
    app.run(debug=True)
