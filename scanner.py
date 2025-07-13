import os
import time
import sys
import hashlib
import subprocess
import json
import shutil
from typing import Dict, List


# Locate required binaries
def find_binary(candidates: list[str]) -> str | None:
    """Return the first existing path from candidates or None."""
    for path in candidates:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    return None


FFMPEG_PATH = find_binary(["/ffmpeg", "/ffmpeg/ffmpeg", "/usr/bin/ffmpeg"])
FFPROBE_PATH = find_binary([
    "/ffmpeg/ffprobe",
    "/ffprobe",
    "/usr/bin/ffprobe",
    "/ffmpeg",
])

LOG_DIR = "/log"


# Helper to read the `fileextexept` environment variable at runtime.
def get_excluded_exts() -> list[str]:
    """Return a list of lowercase extensions that should be skipped."""
    cleaned: list[str] = []
    raw = os.environ.get("fileextexept", "")
    for ext in raw.split(','):
        ext = ext.strip().strip('"').strip("'").lower()
        if ext:
            cleaned.append(ext)
    return cleaned


def file_hash(file_path: str) -> str:
    """Return a hash of the media content, ignoring metadata when possible."""
    if FFMPEG_PATH:
        try:
            result = subprocess.run(
                [
                    FFMPEG_PATH,
                    "-v",
                    "quiet",
                    "-i",
                    file_path,
                    "-map_metadata",
                    "-1",
                    "-f",
                    "md5",
                    "-",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and "MD5=" in result.stdout:
                return result.stdout.strip().split("=", 1)[1]
        except Exception:
            pass

    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def has_metadata(file_path: str) -> bool:
    """Return True if ffprobe detects metadata in the file."""
    if not FFPROBE_PATH:
        return False
    try:
        result = subprocess.run(
            [FFPROBE_PATH, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            try:
                info = json.loads(result.stdout)
            except json.JSONDecodeError:
                return False
            if info.get("format", {}).get("tags"):
                return True
            for st in info.get("streams", []):
                if st.get("tags"):
                    return True
    except Exception:
        pass
    return False


def prefers(path1: str, meta1: bool, path2: str, meta2: bool) -> bool:
    """Return True if the first file should be kept over the second."""
    if meta1 != meta2:
        return meta1  # files with metadata outrank those without
    name1 = os.path.basename(path1)
    name2 = os.path.basename(path2)
    if len(name1) != len(name2):
        return len(name1) < len(name2)
    return False


def move_to_double(file_path: str, double_dir: str = "/double") -> str | None:
    """Move a file to the duplicate directory, avoiding name collisions.

    Returns the destination path or None on failure.
    """
    try:
        os.makedirs(double_dir, exist_ok=True)
        base_name = os.path.basename(file_path)
        dest = os.path.join(double_dir, base_name)
        counter = 1
        while os.path.exists(dest):
            dest = os.path.join(double_dir, f"{base_name}.{counter}")
            counter += 1
        shutil.move(file_path, dest)
        print(f"Moved {file_path} to {dest}")
        return dest
    except OSError as e:
        print(f"Failed to move {file_path} to {double_dir}: {e}")
        return None


def write_log(moved: Dict[str, List[str]], log_dir: str = LOG_DIR) -> None:
    """Write a log file listing moved duplicates."""
    try:
        os.makedirs(log_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_dir, f"{timestamp}.log")
        with open(log_path, "w") as f:
            if not moved:
                f.write("Keine Duplikate in diesem Durchgang.\n")
            else:
                for keep, dupes in moved.items():
                    f.write(f"Originaldatei: {keep}\n")
                    f.write("Verschobene Duplikate zu dieser Datei:\n")
                    for d in dupes:
                        f.write(f"  - {d}\n")
                    f.write("\n")
        print(f"Log geschrieben: {log_path}")
    except OSError as e:
        print(f"Fehler beim Schreiben des Logs: {e}")


def scan_directory(
    path: str,
    known: dict[str, tuple[str, bool]],
    exclude_exts: list[str],
) -> Dict[str, List[str]]:
    """Scan a directory recursively, print file info and handle duplicates."""
    file_count = 0
    dup_count = 0
    skip_count = 0
    moved: Dict[str, List[str]] = {}
    for root, dirs, files in os.walk(path):
        for name in files:
            if any(name.lower().endswith(ext) for ext in exclude_exts):
                skip_count += 1
                continue
            file_path = os.path.join(root, name)
            try:
                size = os.path.getsize(file_path)
            except OSError:
                size = -1
            digest = file_hash(file_path)
            meta = has_metadata(file_path)
            if digest:
                if digest in known:
                    other_path, other_meta = known[digest]
                    if file_path != other_path:
                        dup_count += 1
                        if prefers(file_path, meta, other_path, other_meta):
                            print(f"Duplicate found: {file_path} replaces {other_path}")
                            dest = move_to_double(other_path)
                            if dest is not None:
                                moved.setdefault(file_path, []).append(other_path)
                            known[digest] = (file_path, meta)
                        else:
                            print(f"Duplicate found: {file_path} matches {other_path}")
                            dest = move_to_double(file_path)
                            if dest is not None:
                                moved.setdefault(other_path, []).append(file_path)
                else:
                    known[digest] = (file_path, meta)
            print(f"{file_path} - {size} bytes - {digest}")
            file_count += 1
    total = file_count + skip_count
    ext_desc = ", ".join(exclude_exts) if exclude_exts else "keine"
    print(
        f"Durchlauf abgeschlossen. {file_count} Dateien gefunden, {dup_count} Duplikate. "
        f"{skip_count} Dateien ausgenommen ({ext_desc}) {total} Dateien gesamt!"
    )
    return moved


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else '/scanmedia'
    if not FFMPEG_PATH:
        print('ffmpeg not found')
        sys.exit(1)
    run = 1
    known: dict[str, tuple[str, bool]] = {}
    while True:
        exclude_exts = get_excluded_exts()
        print(f"Starte neuen Durchgang Nr: {run}")
        if exclude_exts:
            print("Ausgeschlossene Dateiendungen: " + ", ".join(exclude_exts))
        else:
            print("Ausgeschlossene Dateiendungen: keine")
        moved = scan_directory(path, known, exclude_exts)
        write_log(moved)
        run += 1
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Beendet durch Benutzer")
