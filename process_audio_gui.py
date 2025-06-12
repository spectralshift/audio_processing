import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import sys
import os

from process_audio import process_directory


class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, string):
        self.widget.insert(tk.END, string)
        self.widget.see(tk.END)
        self.widget.update()

    def flush(self):
        pass


def run_processing(path, verbose, text_widget):
    redirector = TextRedirector(text_widget)
    original_stdout = sys.stdout
    sys.stdout = redirector
    try:
        process_directory(path, verbose=verbose)
    finally:
        sys.stdout = original_stdout
        messagebox.showinfo("Finished", "Processing complete.")


def main():
    root = tk.Tk()
    root.title("Process Audio")

    path_var = tk.StringVar()
    verbose_var = tk.BooleanVar(value=False)

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill=tk.X)

    path_entry = tk.Entry(frame, textvariable=path_var, width=40)
    path_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def browse():
        directory = filedialog.askdirectory()
        if directory:
            path_var.set(directory)

    browse_btn = tk.Button(frame, text="Browse", command=browse)
    browse_btn.pack(side=tk.LEFT, padx=5)

    verbose_cb = tk.Checkbutton(root, text="Verbose", variable=verbose_var)
    verbose_cb.pack(anchor="w", padx=10)

    output = scrolledtext.ScrolledText(root, width=80, height=20)
    output.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    def start():
        path = path_var.get()
        if not path:
            messagebox.showerror("Error", "Please select a directory.")
            return
        output.delete(1.0, tk.END)
        run_processing(path, verbose_var.get(), output)

    start_btn = tk.Button(root, text="Start", command=start)
    start_btn.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
