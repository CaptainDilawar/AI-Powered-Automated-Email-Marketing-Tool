# Import necessary modules from Flask, datetime, and os
from flask import Flask, request, send_file
from datetime import datetime
import os

# Initialize the Flask application
app = Flask(__name__)

# Define the log file name for storing open tracking data
LOG_FILE = "opens_log.csv"

# Route to track email opens via a tracking pixel
@app.route("/track_open")
def track_open():
    # Get the lead_id from the query parameters, default to 'unknown' if not provided
    lead_id = request.args.get("lead_id", "unknown")
    # Get the current UTC timestamp in ISO format
    timestamp = datetime.utcnow().isoformat()

    # Append the lead_id and timestamp to the log file
    with open(LOG_FILE, "a") as f:
        f.write(f"{lead_id},{timestamp}\n")

    # Return a 1x1 transparent PNG pixel to the client
    return send_file("pixel.png", mimetype="image/png")

# Main entry point for running the Flask app
if __name__ == "__main__":
    # If the log file does not exist, create it and write the header
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("lead_id,timestamp\n")
    # Start the Flask server on all interfaces, port 5000
    app.run(host="0.0.0.0", port=5000)
