import os
import sys
import subprocess
import webbrowser
import time
from threading import Timer

def open_browser():
    url = "http://127.0.0.1:5000"
    print(f"\n[Portal] Opening Placement Eligibility Portal at {url}")
    webbrowser.open(url)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'database.db')
    
    print("=" * 60)
    print("      PREPELIGIBLE // Placement Eligibility Checker Portal")
    print("=" * 60)
    
    # 1. Check database initialization
    if not os.path.exists(db_path):
        print("[Database] Database file not found. Running initialization...")
        db_init_script = os.path.join(current_dir, 'db_init.py')
        try:
            subprocess.run([sys.executable, db_init_script], check=True)
            print("[Database] Initialization complete.")
        except subprocess.CalledProcessError as e:
            print(f"[Error] Failed to initialize database: {e}")
            sys.exit(1)
    else:
        print("[Database] SQLite database.db detected.")

    # 2. Schedule browser opening in a separate thread after server starts
    print("[Portal] Starting background browser scheduler...")
    Timer(1.5, open_browser).start()

    # 3. Start Flask app
    print("[Server] Launching Flask development server...")
    app_script = os.path.join(current_dir, 'app.py')
    try:
        # Run Flask server (it will block and show server output)
        subprocess.run([sys.executable, app_script], check=True)
    except KeyboardInterrupt:
        print("\n[Server] Shutting down server. Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"[Error] Flask server failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
