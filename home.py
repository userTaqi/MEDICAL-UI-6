import tkinter as tk
from PIL import Image, ImageTk
import os
import threading

def open_main_py_and_close_gui():
    # Create a new thread to run main.py
    t = threading.Thread(target=run_main_py)
    t.start()
    # Close the GUI
    root.destroy()

def run_main_py():
    # Get the directory path of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate to the directory containing main.py
    os.chdir(script_dir)
    # Run main.py using Python interpreter
    os.system("python main.py")

# Function to close the GUI
def close_gui():
    root.destroy()

# Create the main window
root = tk.Tk()
root.title("Main Application")

# Remove title bar
root.overrideredirect(True)

# Calculate half of the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
half_width = screen_width // 2
half_height = screen_height // 2

# Set the window size to half of the screen width and height
root.geometry(f"{half_width}x{half_height}+{half_width//2}+{half_height//2}")

# Load the image
image = Image.open("image.png")  # Change "your_image_file.jpg" to your image file path

# Resize the image to fit the dimensions of the window
image = image.resize((half_width, half_height))

# Convert the image to PhotoImage format
photo = ImageTk.PhotoImage(image)

# Create a label with the image
image_label = tk.Label(root, image=photo)
image_label.place(x=0, y=0)

# Customize button styles
button_style = {
    "bg": "#838B8B",  # Background color
    "fg": "white",    # Text color
    "font": ("Arial", 12),  # Font and size
    "bd": 1,          # Border width
    "activebackground": "#838B8B",  # Background color when clicked
    "activeforeground": "white"      # Text color when clicked
}

# Create a button to open main.py and close GUI
open_button = tk.Button(root, text="Get Started", command=open_main_py_and_close_gui, **button_style)
open_button.pack(side=tk.BOTTOM, padx=85, pady=10, anchor=tk.SE)  # Positioning the button at the bottom right

# Create a button to close the GUI
close_button = tk.Button(root, text="X", command=close_gui, **button_style, width=2, height=1)
close_button.pack(side=tk.RIGHT, padx=5, pady=10, anchor=tk.NE)  # Positioning the button to the right

# Run the Tkinter event loop
root.mainloop()
