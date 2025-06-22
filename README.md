# flask-chatbot-api

# Flask Chatbot API

This project implements a chatbot API using Flask, integrating generative AI capabilities with support for emotion detection.

## Features

- **Chatbot Interface:** Provides responses to user queries through a simple chat interface.
- **Emotion Detection:** Identifies emotions from text for better user interaction.
- **Session Management:** Retains the latest chat sessions.
- **MongoDB Integration:** Stores user data and chat histories.
- **Google GenAI Integration:** Uses advanced AI for text generation.

## Project Structure

- **app.py:** Main Flask application file containing routes and core logic.
- **emotion/emotion_detect.py:** Script for detecting emotions from user inputs.
- **models/vector_store.pkl:** Pre-trained embeddings or vector data.
- **static/css/styles.css:** CSS styles for the frontend.
- **static/js/scripts.js:** JavaScript functionality for the frontend.
- **templates/index.html:** HTML template for the web interface.

## Dependencies

The project requires the following Python libraries:
- Flask (>=2.3.2)
- Flask-CORS (>=3.0.10)
- pandas (>=2.2.2)
- numpy (>=1.26.4)
- pymongo (>=4.13.2)
- python-dotenv (>=1.0.1)
- Google GenAI

To install dependencies, use:
```bash
pip install -r requirements.txt
