import os
import time
import sys


def scan_directory(path: str) -> None:
    """Scan a directory recursively and print each file path and size."""
    file_count = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                size = os.path.getsize(file_path)
            except OSError:
                size = -1
            print(f"{file_path} - {size} bytes")
            file_count += 1
    print(f"Durchlauf abgeschlossen. {file_count} Dateien gefunden.")


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else '/scanmedia'
    run = 1
    while True:
        print(f"Starte neuen Durchgang Nr: {run}")
        scan_directory(path)
        run += 1
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Beendet durch Benutzer")
