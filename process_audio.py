import os
import sys
import json
import shutil
import subprocess
import re

# Global minimum duration threshold in seconds
MIN_DURATION = 0.75

def validate_json_data(data, json_filename):
    """
    Validates that the JSON data is a list of dictionaries and that
    each dictionary has the required keys: "text", "start", "end", and "rating".
    """
    if not isinstance(data, list):
        print(f"Error: JSON file '{json_filename}' is not a list of segments.")
        return False
    for seg in data:
        if not isinstance(seg, dict):
            print(f"Error: JSON file '{json_filename}' contains a non-dictionary segment.")
            return False
        for key in ['text', 'start', 'end', 'rating']:
            if key not in seg:
                print(f"Error: JSON file '{json_filename}' is missing key '{key}' in one of the segments.")
                return False
        try:
            float(seg['start'])
            float(seg['end'])
        except (ValueError, TypeError):
            print(f"Error: JSON file '{json_filename}' has non-numeric start or end values in a segment.")
            return False
    return True

def process_json_file(audio_path, json_path, verbose=False):
    """
    Processes a single JSON file with the provided audio file:
    - Validates the JSON file.
    - Creates an output directory named after the JSON file (without extension).
    - For each segment that meets MIN_DURATION, extracts the audio using ffmpeg.
    - Creates a metadata JSON file with keys "text" and "audio_file" for each snippet.
    - Logs the steps (checking, processing, outputting, closing).
    """
    json_base = os.path.splitext(os.path.basename(json_path))[0]
    print(f"Checking JSON file: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON file '{json_path}': {e}")
        return

    if not validate_json_data(data, json_path):
        print(f"Skipping file '{json_path}' due to invalid structure.")
        return

    # Create output directory for this JSON file (delete if exists)
    out_dir = os.path.join(os.path.dirname(json_path), json_base)
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    print(f"Created output directory: {out_dir}")

    # Filter valid segments based on duration
    valid_segments = []
    for idx, segment in enumerate(data):
        try:
            start = float(segment['start'])
            end = float(segment['end'])
        except (ValueError, TypeError):
            print(f"Skipping segment {idx+1} in '{json_path}' due to invalid start/end values.")
            continue

        # Validate basic boundaries for start and end
        if start < 0 or end <= start:
            print(
                f"Skipping segment {idx+1} in '{json_path}': invalid time range (start={start}, end={end})."
            )
            continue

        duration = end - start
        if duration < MIN_DURATION:
            print(
                f"Skipping segment {idx+1} in '{json_path}': duration {duration:.2f}s is less than MIN_DURATION ({MIN_DURATION}s)."
            )
            continue
        valid_segments.append(segment)

    if not valid_segments:
        print(f"No valid segments found in '{json_path}'.")
        return

    audio_base = os.path.splitext(os.path.basename(audio_path))[0]
    print(f"Processing JSON file '{json_path}' with {len(valid_segments)} valid segment(s).")

    # List to hold metadata for each processed segment.
    metadata = []

    for idx, segment in enumerate(valid_segments):
        start_time = float(segment['start'])
        end_time = float(segment['end'])
        duration = end_time - start_time

        # Filename based on the audio file base and sequential numbering (starting at 1)
        output_filename = f"{audio_base}_{idx+1:04d}.wav"
        output_file = os.path.join(out_dir, output_filename)

        cmd = [
            "ffmpeg",
            "-y",                   # Overwrite output files if they exist.
            "-i", audio_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-ar", "24000",         # Set the audio sampling rate to 24 kHz.
            "-ac", "1",             # Convert audio to mono.
            "-sample_fmt", "s16",   # Set the sample format to 16-bit.
            output_file             # Make sure this has a .wav extension.
        ]
        print(f"Processing segment {idx+1}: extracting to '{output_filename}'")
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Output segment saved: {output_file}")
            # Append metadata: original text and generated audio file name.
            metadata.append({
                "text": segment["text"],
                "audio_file": output_filename
            })
        except subprocess.CalledProcessError as e:
            print(f"Error processing segment {idx+1} in '{json_path}': {e}")
            if e.stderr:
                stderr_text = e.stderr.decode("utf-8", errors="replace").strip()
                if stderr_text:
                    print(stderr_text)
            if verbose and e.stdout:
                stdout_text = e.stdout.decode("utf-8", errors="replace").strip()
                if stdout_text:
                    print(stdout_text)

    # Save the metadata JSON file in the same directory as the audio files.
    metadata_path = os.path.join(out_dir, "metadata.json")
    try:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata JSON saved: {metadata_path}")
    except Exception as e:
        print(f"Error saving metadata JSON file '{metadata_path}': {e}")

    print(f"Finished processing JSON file '{json_path}'.\nClosing file.")

def main():
    """
    Main function:
    - Expects a subfolder argument.
    - Validates that exactly one audio file exists in the folder.
    - Processes all JSON files in the folder sequentially.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Split audio based on a JSON annotation file.")
    parser.add_argument("subfolder", help="Subfolder containing the audio and JSON files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    subfolder = args.subfolder
    verbose = args.verbose
    parent_dir = os.getcwd()
    process_dir = os.path.join(parent_dir, subfolder)

    if not os.path.isdir(process_dir):
        print(f"Error: The folder '{process_dir}' does not exist.")
        sys.exit(1)

    files = os.listdir(process_dir)

    # Valid audio file extensions
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4', '.aac']
    audio_files = [
        os.path.join(process_dir, file)
        for file in files
        if os.path.isfile(os.path.join(process_dir, file)) and os.path.splitext(file)[1].lower() in audio_extensions
    ]

    if len(audio_files) != 1:
        print(f"Error: There must be exactly one audio file in the directory. Found {len(audio_files)}.")
        sys.exit(1)

    audio_path = audio_files[0]
    print(f"Found audio file: {audio_path}")

    # Process all JSON files in the directory
    json_files = [
        os.path.join(process_dir, file)
        for file in files
        if os.path.isfile(os.path.join(process_dir, file)) and os.path.splitext(file)[1].lower() == '.json'
    ]
    if not json_files:
        print("Error: No JSON files found in the directory.")
        sys.exit(1)

    print(f"Found {len(json_files)} JSON file(s) to process.")

    for json_file in json_files:
        process_json_file(audio_path, json_file, verbose=verbose)

if __name__ == "__main__":
    main()
