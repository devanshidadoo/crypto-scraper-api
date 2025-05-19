# app.py
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper import process_url
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper import process_url



app = Flask(__name__)

CORS(app)
# You can tune this
executor = ThreadPoolExecutor(max_workers=5)

@app.route("/process", methods=["POST"])
def process_batch():
    data = request.get_json(force=True)
    urls = data.get("urls", [])
    if not isinstance(urls, list) or not urls:
        return jsonify({"error": "Please provide a non‐empty list of URLs"}), 400

    # submit all URLs to your existing process_url()
    futures = {executor.submit(process_url, url): url for url in urls}
    results = []
    for fut in as_completed(futures):
        results.append(fut.result())

    return jsonify({"results": results})

if __name__ == "__main__":
    # use host="0.0.0.0" if you want external access
    app.run(port=8000, debug=True)
