import subprocess
import time
import webbrowser
import os

# Get the absolute path to the project root (where this script lives)
ROOT = os.path.dirname(os.path.abspath(__file__))
print(f"🌍 Project root directory: {ROOT}")
print("🚀 Starting Open Tracker Server...")
tracker_script = os.path.join(ROOT, "server", "open_tracker.py")
tracker_process = subprocess.Popen(["python", tracker_script])
time.sleep(2)  # Give the tracker time to boot

# Ask for username
username = input("Enter your username: ").strip()

print("🧠 Running Full Campaign Workflow...")
campaign_script = os.path.join(ROOT, "backend", "run_campaign.py")
campaign_result = subprocess.run(["python", campaign_script, username])

print("📊 Launching Dashboard...")
dashboard_script = os.path.join(ROOT, "dashboard", "Home.py")
# webbrowser.open("http://localhost:8501")
dashboard_process = subprocess.Popen(["streamlit", "run", dashboard_script])

print("\n✅ System running. Close this terminal to stop all services.")
try:
    tracker_process.wait()
    dashboard_process.wait()
except KeyboardInterrupt:
    print("🛑 Shutting down...")
    tracker_process.terminate()
    dashboard_process.terminate()
