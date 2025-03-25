import tkinter as tk
from tkinter import filedialog
from django.core.management.base import BaseCommand
from movies.models import Movie  # Update this import based on your app name

# Function to select file
def select_file(root):
    file_path = filedialog.askopenfilename(title="Select a File")
    if file_path:
        with open(file_path, "r") as file:
            data = file.read()
            print("File content loaded successfully!")  # Process the file content as needed
    root.quit()  # Close the GUI after the file is selected

class Command(BaseCommand):
    help = "A description of what this command does"

    def handle(self, *args, **kwargs):
        # Logic for your Django management command
        print("Running management command...")

        # Tkinter part: Initialize the Tkinter window for file selection
        root = tk.Tk()
        root.title("File Input GUI")
        root.geometry("300x100")

        # Create the button and assign the select_file function to it
        tk.Button(root, text="Select File", command=lambda: select_file(root)).pack(pady=20)

        # Start the Tkinter event loop
        root.mainloop()
