# File: run_flask.py

import os
import logging
import atexit
from flask import Flask, jsonify
from flask_cors import CORS

from app.api.v1.endpoints.chat_flask import chat_bp
from app.core.engine import get_chat_engine
from app.core.tools.api_property_search import _fetch_all_data
from app.core.async_worker import async_worker

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app.register_blueprint(chat_bp, url_prefix='/api/v1')

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "100Gaj Flask API is running"
    })

with app.app_context():
    logging.info("Application starting up...")
    get_chat_engine()
    _fetch_all_data()
    logging.info("Startup complete. Models and data are loaded.")

atexit.register(lambda: async_worker.stop())

if __name__ == '__main__':
    # Disabling the reloader is important for the background thread to work predictably.
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)