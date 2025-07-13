import os
import time
import sys
import hashlib


def file_hash(file_path: str) -> str:
    """Return SHA-256 hash of a file's contents."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def scan_directory(path: str, known: dict[str, str]) -> None:
    """Scan a directory recursively, print file info and detect duplicates."""
    file_count = 0
    dup_count = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                size = os.path.getsize(file_path)
            except OSError:
                size = -1
            digest = file_hash(file_path)
            if digest:
                if digest in known:
                    dup_count += 1
                    print(f"Duplicate found: {file_path} matches {known[digest]}")
                else:
                    known[digest] = file_path
            print(f"{file_path} - {size} bytes - {digest}")
            file_count += 1
    print(f"Durchlauf abgeschlossen. {file_count} Dateien gefunden, {dup_count} Duplikate.")


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else '/scanmedia'
    run = 1
    known: dict[str, str] = {}
    while True:
        print(f"Starte neuen Durchgang Nr: {run}")
        scan_directory(path, known)
        run += 1
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Beendet durch Benutzer")
