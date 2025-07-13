# Uniquemedia Scanner

This repository contains a simple directory scanner written in Python. The
scanner loops endlessly, printing the start of each run and listing all files
and their sizes.

## Running with Docker

Build the image:

```bash
docker build -t uniquemedia-scanner .
```

Run the scanner (replace `/path/to/scan` with the directory you want to
scan):

```bash
docker run --rm -v /path/to/scan:/data uniquemedia-scanner /data
```

The scanner will repeat indefinitely until you stop the container.
