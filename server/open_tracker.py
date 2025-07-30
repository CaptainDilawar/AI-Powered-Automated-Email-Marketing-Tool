from flask import Flask, request, send_file
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# --- App Setup ---
app = Flask(__name__)
PIXEL_PATH = "../static/pixel.png"

# --- Database Setup ---
from database.db import engine
from database.models import EmailContent

SessionLocal = sessionmaker(bind=engine)

@app.route("/track_open")
def track_open():
    lead_id = request.args.get("lead_id", None)
    if not lead_id:
        return send_file(PIXEL_PATH, mimetype="image/png")

    try:
        lead_id = int(lead_id)
    except ValueError:
        return send_file(PIXEL_PATH, mimetype="image/png")

    session = SessionLocal()
    email_record = session.query(EmailContent).filter_by(lead_id=lead_id).first()

    if email_record:
        if not email_record.opened:
            email_record.opened = True
            session.commit()
            print(f"✅ Marked Lead ID {lead_id} as opened.")
        else:
            print(f"ℹ️ Lead ID {lead_id} already marked as opened.")
    else:
        print(f"⚠️ No email found with Lead ID {lead_id}.")

    session.close()
    return send_file(PIXEL_PATH, mimetype="image/png")

if __name__ == "__main__":
    print("📡 Open tracking server started at http://localhost:5000/track_open")
    app.run(host="0.0.0.0", port=5000)
