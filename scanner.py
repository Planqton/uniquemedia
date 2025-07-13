import os
import time
import sys
import hashlib
import subprocess
import json
import shutil


def file_hash(file_path: str) -> str:
    """Return a hash of the media content, ignoring metadata when possible."""
    ffmpeg_paths = ["/ffmpeg", "/ffmpeg/ffmpeg", "/usr/bin/ffmpeg"]

    for bin_path in ffmpeg_paths:
        if os.path.exists(bin_path):
            try:
                result = subprocess.run(
                    [
                        bin_path,
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
    ffprobe_paths = [
        "/ffmpeg/ffprobe",
        "/ffprobe",
        "/usr/bin/ffprobe",
        "/ffmpeg",
    ]
    for bin_path in ffprobe_paths:
        if os.path.exists(bin_path):
            try:
                result = subprocess.run(
                    [bin_path, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    try:
                        info = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        continue
                    if info.get("format", {}).get("tags"):
                        return True
                    for st in info.get("streams", []):
                        if st.get("tags"):
                            return True
            except Exception:
                pass
    return False


def move_to_double(file_path: str, double_dir: str = "/double") -> None:
    """Move a file to the duplicate directory, avoiding name collisions."""
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
    except OSError as e:
        print(f"Failed to move {file_path} to {double_dir}: {e}")


def scan_directory(path: str, known: dict[str, tuple[str, bool]]) -> None:
    """Scan a directory recursively, print file info and handle duplicates."""
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
            meta = has_metadata(file_path)
            if digest:
                if digest in known:
                    other_path, other_meta = known[digest]
                    if file_path != other_path:
                        dup_count += 1
                        if meta and not other_meta:
                            print(
                                f"Duplicate found: {file_path} replaces {other_path} (metadata preference)"
                            )
                            move_to_double(other_path)
                            known[digest] = (file_path, meta)
                        else:
                            print(f"Duplicate found: {file_path} matches {other_path}")
                            move_to_double(file_path)
                else:
                    known[digest] = (file_path, meta)
            print(f"{file_path} - {size} bytes - {digest}")
            file_count += 1
    print(f"Durchlauf abgeschlossen. {file_count} Dateien gefunden, {dup_count} Duplikate.")


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else '/scanmedia'
    run = 1
    known: dict[str, tuple[str, bool]] = {}
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
