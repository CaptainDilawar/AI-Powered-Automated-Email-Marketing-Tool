import subprocess
import time
import webbrowser
import os
import signal

from database.db import engine
from database.models import Base

# Ensure database tables exist
Base.metadata.create_all(bind=engine)
# Get the absolute path to the project root
ROOT = os.path.dirname(os.path.abspath(__file__))
print(f"🌍 Project root directory: {ROOT}")

# Start the open tracker server
print("🚀 Starting Open Tracker Server...")
tracker_script = os.path.join(ROOT, "server", "open_tracker.py")
tracker_process = subprocess.Popen(["python", tracker_script])
time.sleep(2)

# Launch Streamlit dashboard
print("📊 Launching Dashboard...")
dashboard_script = os.path.join(ROOT, "dashboard", "Home.py")
dashboard_process = subprocess.Popen(["streamlit", "run", dashboard_script])

print("\n✅ System running. Use Ctrl+C to shut down.")
try:
    tracker_process.wait()
    dashboard_process.wait()
except KeyboardInterrupt:
    print("🛑 Shutting down...")
    tracker_process.terminate()
    dashboard_process.terminate()
    time.sleep(1)
    tracker_process.kill()
    dashboard_process.kill()
    print("✅ Shutdown complete.")