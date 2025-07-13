# Uniquemedia Scanner

This repository contains a simple directory scanner written in Python. The
scanner loops endlessly, printing `Starte neuen Durchgang` with the iteration
number at the start of every scan. Files are hashed using ffmpeg's `md5` muxer
so that metadata is ignored when determining equality. When identical hashes are
found, the version containing metadata is kept if possible. A file is only
considered a duplicate when another path with the same hash exists; scanning the
same file again will no longer cause it to be moved.

## Running with Docker

Build the image:

```bash
docker build -t uniquemedia-scanner .
```

Run the scanner (replace `/path/to/scan` with the directory you want to
scan). The container expects the directory to be mounted at `/scanmedia`.
If no directory is provided, `/scanmedia` is scanned by default:

```bash
docker run --rm -v /path/to/scan:/scanmedia uniquemedia-scanner
```

The scanner will repeat indefinitely until you stop the container. Detected
duplicate files are moved to the `/double` directory so that only a single copy
remains in the scanned folder. If one of two identical files contains media
metadata while the other does not, the metadata-rich file is kept and the other
is moved. When none of the duplicates contain metadata, the file with the
shortest name is preserved.

You can exclude certain file extensions from scanning by setting the
`fileextexept` environment variable. Provide a comma-separated list of
extensions (with leading dots). The scanner reads this variable at the start of
every run and prints the excluded extensions. Quotes around the value (as used
in some compose files) are stripped automatically:

```bash
docker run --rm -v /path/to/scan:/scanmedia \
  -e fileextexept=".old,.filesync" uniquemedia-scanner
```

In this example, files ending with `.old` or `.filesync` will be ignored during
the scan.

You can control whether the scanner automatically starts new runs via the
`autoscan` environment variable. When set to `false`, the program waits for a
key press before beginning the next scan iteration. The default value is
`true`, so scans repeat without interaction.

The scanner requires `ffmpeg` (and `ffprobe`) to calculate hashes and read
metadata. If these binaries are not found at start-up, the program exits with
`ffmpeg not found`. In the Docker image, they are expected to be available at
`/ffmpeg`.

Each run writes a timestamped log file to `/log`. The log lists which files
were kept and which duplicates were moved to `/double` during that scan.

At the end of every run the scanner prints a summary like:

```
Durchlauf abgeschlossen. 12 Dateien gefunden, 2 Duplikate. 3 Dateien ausgenommen (.old) 15 Dateien gesamt!
```

The numbers indicate how many files were processed, how many duplicates were
moved, how many files were skipped due to the `fileextexept` setting and the
total number of files seen during the scan.
