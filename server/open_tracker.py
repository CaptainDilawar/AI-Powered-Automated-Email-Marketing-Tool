from flask import Flask, request, send_file
from datetime import datetime
import os

app = Flask(__name__)

# Paths to log file and tracking pixel
LOG_FILE = "../data/opens_log.csv"
PIXEL_PATH = "../static/pixel.png"

@app.route("/track_open")
def track_open():
    lead_id = request.args.get("lead_id", "unknown")
    timestamp = datetime.utcnow().isoformat()

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Append lead ID and timestamp to the log
    with open(LOG_FILE, "a") as f:
        f.write(f"{lead_id},{timestamp}\n")

    # Return a 1x1 transparent pixel
    return send_file(PIXEL_PATH, mimetype="image/png")

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Create log file with header if missing
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("lead_id,timestamp\n")

    print("📡 Open tracking server started at http://localhost:5000/track_open")
    app.run(host="0.0.0.0", port=5000)
