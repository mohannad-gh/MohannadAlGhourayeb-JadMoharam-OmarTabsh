# Start Omar Tabsh's three services together (Ctrl+C stops all of them)
# Omar Tabsh - 202400798
#
#   python -m scripts.run_tabsh_services
#
# Audit Logging (5005) starts first because the other services send events to it.

import subprocess
import sys
import time

SERVICES = [
    ("Security Audit Logging", "services.audit_logging.app", 5005),
    ("Threat Intelligence", "services.threat_intelligence.app", 5004),
    ("Security Reports", "services.security_reports.app", 5006),
]


def main():
    processes = []
    try:
        for name, module, port in SERVICES:
            processes.append(subprocess.Popen([sys.executable, "-m", module]))
            print(f"Started {name} service on http://127.0.0.1:{port}")
            time.sleep(1)
        print("All services running. Press Ctrl+C to stop.")
        while all(process.poll() is None for process in processes):
            time.sleep(1)
        print("A service stopped unexpectedly, shutting down the others.")
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    main()
