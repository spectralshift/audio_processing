# Audio Processing

A few small utilities for turning raw recordings into training data.

## Dependencies

- Python 3.8+.
- Packages from `requirements.txt`.
- `ffmpeg` available on your `PATH` for audio extraction.

Install the Python packages with:

```bash
pip install -r requirements.txt
```

## Workflow

1. **Prepare the audio** – start with a single audio file (or extract the audio track from a video).
2. **Transcribe** – generate a word‑level JSON transcript (for example with ElevenLabs) and remove unneeded metadata.
3. **Build sentence annotations** – run `process_elevenlabs_annotations.py` on the raw JSON to combine words into complete sentences for one speaker. Run with `input.json output.json` for CLI usage or without arguments to open the GUI.
4. **Annotate and rate** – place the resulting JSON and the audio file in one folder as `annotations.json` and run `annotate.py`. Listen to each segment, edit the text if necessary and mark it as `good`, `ok` or `bad`. Saving creates files such as `annotations_good.json` and `annotations_bad.json`.
5. **Split the audio** – copy the audio file and the JSON file you want to use (e.g. `annotations_good.json`) into a new folder and run `process_audio.py <folder>` or use `process_audio_gui.py`. Each JSON file is processed and the audio is cut into numbered `.wav` files (24 kHz mono). A `metadata.json` describing the clips is written in a subdirectory named after the JSON file.

## Script summary

- **process_elevenlabs_annotations.py** – Converts ElevenLabs output to sentence‑level annotations.
  - *Input:* raw ElevenLabs JSON.
  - *Output:* list of `{"text", "start", "end"}` for a single speaker.
  - Run `python process_elevenlabs_annotations.py input.json output.json` or launch without arguments to use the GUI.
- **annotate.py** – GUI for reviewing each sentence.
  - *Input:* folder containing an audio file and `annotations.json`.
  - *Output:* `annotations_good.json`, `annotations_ok.json`, `annotations_bad.json` and `annotations_unrated.json`.
- **process_audio.py** – CLI tool that splits an audio file according to annotation JSON files.
  - *Input:* folder with one audio file and one or more JSON files.
  - *Output:* for every JSON file, a subdirectory with clipped `.wav` files and `metadata.json`.
- **process_audio_gui.py** – simple Tkinter front‑end for `process_audio.py`.

## Example data

The `tests` directory contains sample audio and annotations. The file `sample_invalid.json` demonstrates how `process_audio.py` reports segments with negative start times or end times before the start. Only valid segments are exported.

