# File Counter

This project provides a simple Docker container that counts all files in a
mounted directory. It expects the host directory to be mounted at
`/scanmedia` inside the container.

## Usage

1. Build the image:
   ```
   docker build -t file-counter .
   ```

2. Run the container with your directory mounted at `/scanmedia`:
   ```
   docker run --rm -v C:/epifixer:/scanmedia file-counter
   ```

The container will output the total number of files found in the mounted
folder and all of its subfolders.
