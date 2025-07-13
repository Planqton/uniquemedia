import os


def count_files(path):
    total = 0
    for _, _, files in os.walk(path):
        total += len(files)
    return total


def main():
    scan_path = os.environ.get("SCAN_PATH", "/scanmedia")
    if not os.path.exists(scan_path):
        print(f"Scan path '{scan_path}' does not exist.")
        return
    total = count_files(scan_path)
    print(f"Total files found: {total}")


if __name__ == "__main__":
    main()
