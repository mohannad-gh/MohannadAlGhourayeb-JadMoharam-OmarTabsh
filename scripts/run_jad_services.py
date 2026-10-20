"""Run Jad's three apps. Start Omar's Audit Logging separately on port 5005."""
import subprocess
import sys

MODULES = ('services.notifications.app', 'services.incidents.app', 'services.playbooks.app')


def main():
    processes = []
    try:
        for module in MODULES:
            processes.append(subprocess.Popen([sys.executable, '-m', module]))
        while True:
            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError(f'A service exited with status {process.returncode}')
            import time
            time.sleep(.5)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            process.wait(timeout=10)


if __name__ == '__main__':
    main()
