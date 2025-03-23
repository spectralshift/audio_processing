import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import threading
import multiprocessing
import simpleaudio as sa
from pydub import AudioSegment

def playback_function(snippet):
    try:
        play_obj = sa.play_buffer(
            snippet.raw_data,
            num_channels=snippet.channels,
            bytes_per_sample=snippet.sample_width,
            sample_rate=snippet.frame_rate
        )
        play_obj.wait_done()
    except Exception as e:
        print("Error during audio playback in process:", e)

class AnnotationApp:
    def __init__(self, master):
        self.master = master
        master.title("Annotation Helper")

        # Initialize variables for paths and data.
        self.base_dir = None
        self.audio_file = None
        self.json_file = None
        self.annotations = []
        self.current_index = 0

        # Create the menu frame with three main buttons.
        self.menu_frame = tk.Frame(master)
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)

        self.load_button = tk.Button(self.menu_frame, text="Load Directory", command=self.load_directory)
        self.load_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_button = tk.Button(self.menu_frame, text="Save Annotations", command=self.save_annotations, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.quit_button = tk.Button(self.menu_frame, text="Quit", command=self.quit_app)
        self.quit_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Frame for annotation details (transcript, audio play, navigation).
        self.annotation_frame = tk.Frame(master)
        self.annotation_frame.pack(fill=tk.BOTH, expand=True)

        # Transcript Text Box.
        self.text_label = tk.Label(self.annotation_frame, text="Transcript:")
        self.text_label.pack(anchor="w", padx=5)
        self.text_box = tk.Text(self.annotation_frame, height=5, wrap="word")
        self.text_box.pack(fill=tk.X, padx=5, pady=5)
        self.text_box.config(state=tk.DISABLED)

        # Play Audio Button.
        self.play_button = tk.Button(self.annotation_frame, text="Play Audio", command=self.play_audio, state=tk.DISABLED)
        self.play_button.pack(padx=5, pady=5)

        # === New Rating Buttons ===
        self.rating_frame = tk.Frame(self.annotation_frame)
        self.rating_frame.pack(pady=5)
        # Button for "good" rating: green check mark.
        self.good_button = tk.Button(self.rating_frame, text="✅", command=lambda: self.set_rating("good"), bg="light green")
        self.good_button.pack(side=tk.LEFT, padx=5)
        # Button for "ok" rating: yellow check mark.
        self.ok_button = tk.Button(self.rating_frame, text="✔️", command=lambda: self.set_rating("ok"), bg="light yellow")
        self.ok_button.pack(side=tk.LEFT, padx=5)
        # Button for "bad" rating: red X.
        self.bad_button = tk.Button(self.rating_frame, text="❌", command=lambda: self.set_rating("bad"), bg="tomato")
        self.bad_button.pack(side=tk.LEFT, padx=5)
        # ============================

        # Navigation Controls Frame.
        self.nav_frame = tk.Frame(self.annotation_frame)
        self.nav_frame.pack(pady=5)

        self.prev_button = tk.Button(self.nav_frame, text="<< Previous", command=self.prev_record, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(self.nav_frame, text="Next >>", command=self.next_record, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)

        self.jump_label = tk.Label(self.nav_frame, text="Go to record:")
        self.jump_label.pack(side=tk.LEFT, padx=5)

        self.jump_entry = tk.Entry(self.nav_frame, width=5)
        self.jump_entry.pack(side=tk.LEFT, padx=5)
        self.jump_entry.bind("<Return>", self.jump_to_record)

        self.record_label = tk.Label(self.nav_frame, text="Record: 0 / 0")
        self.record_label.pack(side=tk.LEFT, padx=5)

    def load_directory(self):
        directory = filedialog.askdirectory()
        if not directory:
            return
        self.base_dir = directory

        # Look for a JSON file named 'annotations.json'
        json_path = os.path.join(directory, "annotations.json")
        if not os.path.exists(json_path):
            messagebox.showerror("Error", "annotations.json not found in the selected directory.")
            return
        self.json_file = json_path

        # Look for an audio file with a common audio extension (.wav, .mp3, .mp4)
        audio_file = None
        for file in os.listdir(directory):
            if file.lower().endswith((".wav", ".mp3", ".mp4")):
                audio_file = os.path.join(directory, file)
                break
        if not audio_file:
            messagebox.showerror("Error", "No audio file (.wav, .mp3, .mp4) found in the selected directory.")
            return
        self.audio_file = audio_file

        # Load the JSON file.
        try:
            with open(self.json_file, "r") as f:
                self.annotations = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON file: {str(e)}")
            return

        # === Add new key 'rating' with default 'unrated' if not already present ===
        for record in self.annotations:
            if 'rating' not in record:
                record['rating'] = 'unrated'
        # ========================================================================

        try:
            self.audio_data = AudioSegment.from_file(self.audio_file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio file: {str(e)}")
            return

        if not self.annotations:
            messagebox.showinfo("Info", "No annotations found in the JSON file.")
            return

        self.current_index = 0
        self.display_record()

        # Enable UI elements now that the directory is loaded.
        self.save_button.config(state=tk.NORMAL)
        self.play_button.config(state=tk.NORMAL)
        self.prev_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.NORMAL)
        self.text_box.config(state=tk.NORMAL)

    def display_record(self):
        if not self.annotations:
            return

        record = self.annotations[self.current_index]
        # Update the transcript text box.
        self.text_box.config(state=tk.NORMAL)
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, record.get("text", ""))
        self.text_box.config(state=tk.NORMAL)

        # Update the record navigation label.
        total = len(self.annotations)
        self.record_label.config(text=f"Record: {self.current_index + 1} / {total}")

    def save_current_record(self):
        # Save the current transcript text into the annotations list.
        if not self.annotations:
            return
        new_text = self.text_box.get("1.0", tk.END).strip()
        self.annotations[self.current_index]["text"] = new_text

    def set_rating(self, rating):
        if not self.annotations:
            return
        self.annotations[self.current_index]['rating'] = rating
        #messagebox.showinfo("Rating", f"Set rating to '{rating}' for the current record.")

    def prev_record(self):
        self.save_current_record()
        if self.current_index > 0:
            self.current_index -= 1
            self.display_record()
        else:
            messagebox.showinfo("Info", "Already at the first record.")

    def next_record(self):
        self.save_current_record()
        if self.current_index < len(self.annotations) - 1:
            self.current_index += 1
            self.display_record()
        else:
            messagebox.showinfo("Info", "Already at the last record.")

    def jump_to_record(self, event):
        self.save_current_record()
        try:
            index = int(self.jump_entry.get()) - 1
            if 0 <= index < len(self.annotations):
                self.current_index = index
                self.display_record()
            else:
                messagebox.showerror("Error", "Invalid record number.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")

    def play_audio(self):
        if not self.annotations or not hasattr(self, 'audio_data'):
            return

        record = self.annotations[self.current_index]
        start_ms = record.get("start", 0) * 1000
        end_ms = record.get("end", 0) * 1000

        if start_ms >= end_ms:
            messagebox.showerror("Error", "Invalid time interval in annotation.")
            return

        # Slice the preloaded audio data.
        snippet = self.audio_data[start_ms:end_ms]
        
        p = multiprocessing.Process(target=playback_function, args=(snippet,))
        p.start()

    def save_annotations(self):
        # Save the current transcript text into the annotations list.
        self.save_current_record()
        # Split the annotations by rating.
        base, ext = os.path.splitext(self.json_file)
        ratings = ["good", "ok", "bad", "unrated"]
        files_created = []
        for rating in ratings:
            filtered = [record for record in self.annotations if record.get("rating", "unrated") == rating]
            if filtered:
                filename = f"{base}_{rating}{ext}"
                try:
                    with open(filename, "w") as f:
                        json.dump(filtered, f, indent=2)
                    files_created.append(os.path.basename(filename))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file {filename}: {str(e)}")
                    return
        if files_created:
            messagebox.showinfo("Success", f"Annotations saved successfully in: {', '.join(files_created)}")
        else:
            messagebox.showinfo("Success", "No annotations to save for any rating.")

    def quit_app(self):
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationApp(root)
    root.mainloop()
