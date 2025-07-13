# Uniquemedia Scanner

This repository contains a simple directory scanner written in Python. The
scanner loops endlessly, printing the start of each run and listing all files,
their sizes and a SHA-256 hash of the contents. Duplicate files are detected by
comparing hashes only. When identical hashes are found, the version containing
metadata is kept if possible.

## Running with Docker

Build the image:

```bash
docker build -t uniquemedia-scanner .
```

Run the scanner (replace `/path/to/scan` with the directory you want to
scan). The container expects the directory to be mounted at `/scanmedia`:

```bash
docker run --rm -v /path/to/scan:/scanmedia uniquemedia-scanner
```

The scanner will repeat indefinitely until you stop the container. Detected
duplicate files are moved to the `/double` directory so that only a single copy
remains in the scanned folder. If one of two identical files contains media
metadata while the other does not, the metadata-rich file is kept and the other
is moved.

If you need to process media files with `ffmpeg`, the binary is available in the
container at `/ffmpeg`.
