A super simple set of personal python files for an audio training pipeline.

## Dependencies

Install the Python packages in `requirements.txt`. The audio utilities also
rely on `ffmpeg` being installed and available on your `PATH`.

1 - You have a video or audio clip. If video, strip audio. Now you have an audio file.

2 - Do the basic annotation. Recommended in ElevenLabs using speech to text (stt)

3 - Now you have the annotation file, and the audio file. Take the annotation and remove excess details (see example)

4 - Run 'process_elevenlabs_annotations.py', selecting the speaker you want to extract and form full sentences from; saves to a new file.

5 - You now have a file of sentences from one speaker; take this file and the video and place into one directory. Rename JSON to annotation.json

6 - Run the annotate.py file. Check and rate each snippet. 

  - Guidance: Good = can be used now, OK = needs processing (eg: background), Bad = unusable (eg: wrong person, incoherence, unsuitable)
    
7 - Copy the audio and the annotation file you wish to process (eg: good only) and place it into a new folder.
    
8 - Run the `process_audio.py` script on the new folder or use the GUI with `process_audio_gui.py`. Both split the file into the chunks in the annotation file.

### GUI Usage

Launch the graphical interface with:

```
python process_audio_gui.py
```

Use **Browse** to select the folder that contains your audio file and JSON annotations. Enable **Verbose** for additional output and press **Start** to begin processing. Progress messages appear in the text box at the bottom of the window.


![Alt text](workflow.png)

## Sample JSON

The file `tests/sample_invalid.json` demonstrates how `process_audio.py` skips segments
with invalid start or end values. When you run the script with this file, it
prints warnings for:

- a segment with a negative start time
- a segment where the end time is less than or equal to the start time

Only the valid segment in the file will be processed.
