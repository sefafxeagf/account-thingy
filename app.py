import os
import json
import random
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from threading import Lock

app = Flask(__name__)
CORS(app)

dataDir = "data"
os.makedirs(dataDir, exist_ok=True)

delKey = "kawaiikittymeow"
lock = Lock()
database = {}


def loadData():
    for filename in os.listdir(dataDir):
        if filename.endswith(".json"):
            titleid = filename[:-5]
            try:
                with open(os.path.join(dataDir, filename), "r", encoding="utf-8") as f:
                    database[titleid] = json.load(f)
            except Exception:
                database[titleid] = []

def saveTitleId(titleid):
    filepath = os.path.join(dataDir, f"{titleid}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(database.get(titleid, []), f, indent=2)

loadData()


@app.route('/<titleid>', methods=['POST'])
def uploadJson(titleid):
    try:
        data = request.get_json(force=True)

        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            return jsonify({"error": "invalid json"}), 400
        for item in data:
            if not isinstance(item, dict):
                return jsonify({"error": "invalid json"}), 400

        with lock:
            database.setdefault(titleid, []).extend(data)
            saveTitleId(titleid)

        return jsonify({
            "message": f"{len(data)} accounts added to: {titleid}",
            "total_entries": len(database[titleid])
        }), 201

    except Exception as e:
        return jsonify({"error": f"Invalid payload: {str(e)}"}), 400

@app.route('/<titleid>', methods=['GET'])
def getJson(titleid):
    entries = database.get(titleid, [])
    if not entries:
        return jsonify({"error": "No data found for this titleid"}), 404
    return jsonify(random.choice(entries)), 200

@app.route('/<titleid>/amount', methods=['GET'])
def getamount(titleid):
    count = len(database.get(titleid, []))
    return jsonify({"titleid": titleid, "amount": count}), 200


@app.route('/<titleid>', methods=['DELETE'])
def deletetitleid(titleid):
    key = request.args.get("key")
    if key != delKey:
        return jsonify({"error": "Invalid or missing delete key"}), 403
    with lock:
        if titleid not in database:
            return jsonify({"error": "Title id not found"}), 404
        del database[titleid]
        filepath = os.path.join(dataDir, f"{titleid}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
    return jsonify({"message": f"All accounts for {titleid} were removed"}), 200


@app.route('/all', methods=['GET'])
def listall():
    return jsonify({"titleids": list(database.keys()), "total_titleids": len(database)}), 200



@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
