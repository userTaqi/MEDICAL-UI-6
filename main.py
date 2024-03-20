import sys
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import threading
import shutil
import atexit
import tkinter.ttk as ttk
import os
from tkinter import IntVar
import detect
import anonymize

# Define the lock file path
LOCK_FILE = "main.lock"

# Function to check if the lock file exists
def check_lock():
    return os.path.exists(LOCK_FILE)

# Function to create the lock file
def create_lock():
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

# Function to delete the lock file
def delete_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

# Check if another instance of the application is running
if check_lock():
    print("Another instance is already running.")
    sys.exit(1)

# Create the lock file
create_lock()

class MedicalImageAnonymizationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultrasound Anonymization Tool")
        self.root.state('zoomed')  # Maximize the window
        self.uploaded_folder_path = None  # Initialize the variable to store the folder path

        # Create frames with specified background colors
        uploaded_images_frame = tk.Frame(root, bd=1, relief=tk.SOLID)
        top_buttons_frame = tk.Frame(root, bd=1, relief=tk.SOLID, bg="gray17")
        large_canvases_frame = tk.Frame(root, bd=1, relief=tk.SOLID)
        bottom_bar_frame = tk.Frame(root, bd=1, height=20, relief=tk.SOLID, bg="gray15")

        uploaded_images_frame.grid(row=2, column=1, sticky="nsew")
        top_buttons_frame.grid(row=1, column=1, columnspan=2, sticky="nsew")
        large_canvases_frame.grid(row=2, column=2, sticky="nsew")
        bottom_bar_frame.grid(row=3, column=1, columnspan=2, sticky="nsew")

        # Use grid_rowconfigure and grid_columnconfigure to make frames fill the available space
        root.grid_rowconfigure(1, weight=1)
        root.grid_rowconfigure(2, weight=1)
        root.grid_rowconfigure(3, weight=1)
        root.grid_columnconfigure(2, weight=1)

        save_button = tk.Button(top_buttons_frame, font='Helvetica 11 bold', fg="white", background="gray30",
                                text="Save", command=self.save_anonymized_images, relief="flat", borderwidth=0, width=6)
        save_button.pack(side=tk.RIGHT, padx=10)

        # Add a button to top_buttons_frame to enable/disable large_image_canvas1
        toggle_canvas_button = tk.Button(top_buttons_frame, font='Helvetica 11 bold', fg="white", background="gray30",
                                         text="Show/Hide Original", command=self.toggle_large_canvas1, relief="flat",
                                         borderwidth=0, width=20)
        toggle_canvas_button.pack(side=tk.RIGHT, padx=7)

        anonymize_button = tk.Button(top_buttons_frame, font='Helvetica 11 bold', fg="white", background="gray30",
                                     text="Anonymize Images", command=self.anonymize_images, relief="flat",
                                     borderwidth=0,
                                     width=20)
        anonymize_button.pack(side=tk.RIGHT, padx=10)

        detect_button = tk.Button(top_buttons_frame, font='Helvetica 11 bold', fg="white", background="gray30",
                                  text="Detect Images", command=self.detect_images, relief="flat", borderwidth=0,
                                  width=19)
        detect_button.pack(side=tk.RIGHT, padx=10)

        upload_button = tk.Button(top_buttons_frame, font='Helvetica 11 bold', fg="white", background="gray30",
                                  text="Upload Images", command=self.upload_images, relief="flat", borderwidth=0,
                                  width=17)
        upload_button.pack(side=tk.RIGHT, padx=10)

        program_label = tk.Label(top_buttons_frame, font='Helvetica 17 bold', fg="white", background="gray17",
                                 text="Ultrasound Anonymization Tool")
        program_label.pack(side=tk.LEFT, padx=10)

        # Create a hover effect function
        def on_hover(event):
            event.widget['background'] = 'gray40'

        # Create a leave effect function
        def on_leave(event):
            event.widget['background'] = 'gray30'

        # Create a progress bar and center it using place
        self.progress_bar = ttk.Progressbar(bottom_bar_frame, mode='determinate', length=200)

        # Add a StringVar for progress text
        self.progress_text_var = tk.StringVar()
        self.progress_text_var.set("")  # Initial text

        # Create a label to display progress text
        self.progress_label = ttk.Label(bottom_bar_frame, textvariable=self.progress_text_var, background="gray15",
                                        foreground="white")

        # create style for scroll bar
        style = ttk.Style()
        style.theme_use('alt')
        style.configure("Vertical.TScrollbar", background="white", arrowcolor="black")

        # Create a canvas to display images
        self.image_canvas = tk.Canvas(uploaded_images_frame, width=243, height=600, relief=tk.SOLID,
                                      highlightthickness=0, bg="gray25")
        self.image_canvas.pack(side=tk.RIGHT, fill=tk.Y)

        self.label00 = tk.Label(text="upload to view images", font=('Helvetica', 12), fg="gray50",
                                bg="gray25")
        self.label00.place(in_=self.image_canvas, anchor="center", relx=0.5, rely=0.5, y=0)

        # Apply hover effect to buttons
        for button in [upload_button, detect_button, anonymize_button, toggle_canvas_button, save_button]:
            button.bind('<Enter>', on_hover)
            button.bind('<Leave>', on_leave)

        # Create a vertical scrollbar with the custom style
        self.scrollbar = ttk.Scrollbar(uploaded_images_frame, command=self.image_canvas.yview)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.image_canvas.config(yscrollcommand=self.scrollbar.set)

        # Bind mouse enter and leave events to the canvas for scrolling
        self.image_canvas.bind("<Enter>", self.on_canvas_enter)
        self.image_canvas.bind("<Leave>", self.on_canvas_leave)

        # Create a canvas to display images BIG
        self.large_image_canvas1 = tk.Canvas(large_canvases_frame, width=225, height=900, relief=tk.SUNKEN,
                                             highlightthickness=0, bg="gray30", bd=1)
        self.large_image_canvas1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.large_image_canvas1.bind("<Button-1>", self.show_large_image)

        self.large_image_canvas3 = tk.Canvas(large_canvases_frame, width=225, height=900, relief=tk.SUNKEN,
                                             highlightthickness=0, bg="gray30", bd=1)
        self.large_image_canvas3.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.large_image_canvas3.bind("<Button-1>", self.show_large_image)

        self.large_image_canvas2 = tk.Canvas(large_canvases_frame, width=225, height=900, relief=tk.SUNKEN,
                                             highlightthickness=0, bg="gray30", bd=1)
        self.large_image_canvas2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.large_image_canvas2.bind("<Button-1>", self.show_large_image)

        # Create labels above large canvases
        self.label1 = tk.Label(large_canvases_frame, text="Original Image", font=('Helvetica', 12), fg="white",
                               bg="gray30")
        self.label1.place(in_=self.large_image_canvas1, anchor="n", relx=0.5, rely=0, y=15)

        self.label2 = tk.Label(large_canvases_frame, text="Detected Image", font=('Helvetica', 12), fg="white",
                               bg="gray30")
        self.label2.place(in_=self.large_image_canvas2, anchor="n", relx=0.5, rely=0, y=15)

        self.label3 = tk.Label(large_canvases_frame, text="Anonymized Image", font=('Helvetica', 12), fg="white",
                               bg="gray30")
        self.label3.place(in_=self.large_image_canvas3, anchor="n", relx=0.5, rely=0, y=15)

        # Keep track of the last-clicked image
        self.last_clicked_image = None

        # Add a variable to track the state of large_image_canvas1
        self.large_canvas1_enabled = IntVar()
        self.large_canvas1_enabled.set(1)  # Set to 1 for enabled, 0 for disabled

        # Bind arrow keys for scrolling in the image canvas
        self.image_canvas.bind("<Up>", self.on_arrow_key)
        self.image_canvas.bind("<Down>", self.on_arrow_key)
        self.image_canvas.focus_set()

    ###################################################################################################################
    def toggle_large_canvas1(self):
        if self.large_canvas1_enabled.get():
            # Disable large_image_canvas1
            self.large_image_canvas1.pack_forget()
            self.large_canvas1_enabled.set(0)
            self.update_large_canvases()  # Update canvases when disabling canvas1
        else:
            # Enable large_image_canvas1
            self.large_image_canvas1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.large_canvas1_enabled.set(1)
            self.update_large_canvases()

    ###############################################################################################
    def on_canvas_enter(self, event):
        self.image_canvas.bind("<MouseWheel>", self.on_mousewheel)

    def on_canvas_leave(self, event):
        self.image_canvas.unbind("<MouseWheel>")

    def on_arrow_key(self, event):
        if event.keysym == "Up":
            self.image_canvas.yview_scroll(-1, "units")
        elif event.keysym == "Down":
            self.image_canvas.yview_scroll(1, "units")

    def on_mousewheel(self, event):
        self.image_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    ###################################################################################################################

    def save_anonymized_images(self):
        if not self.uploaded_folder_path:
            print("Please anonymize images first.")
            return

        # Ask user to select the destination folder for saving anonymized images
        save_folder = filedialog.askdirectory(title="Select Destination Folder")
        if not save_folder:
            return  # User canceled the operation

        # Use threading to run the save_anonymized_images_script in the background
        save_thread = threading.Thread(target=self.save_anonymized_images_script, args=(save_folder,))
        save_thread.start()

    def save_anonymized_images_script(self, save_folder):
        # Copy anonymized images to the selected destination folder
        anonymized_folder_path = os.path.join(self.uploaded_folder_path, 'temp_anonymized')
        if os.path.exists(anonymized_folder_path):
            for file_name in os.listdir(anonymized_folder_path):
                file_path = os.path.join(anonymized_folder_path, file_name)
                if os.path.isfile(file_path):
                    destination_path = os.path.join(save_folder, file_name)
                    shutil.copy(file_path, destination_path)
            print("Anonymized images saved successfully.")
        else:
            print("Anonymized images folder not found.")

    ###################################################################################################################
    def upload_images(self):
        self.cleanup()
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            self.uploaded_folder_path = folder_path  # Save the folder path
            # Use threading to run the display_images method in the background
            display_thread = threading.Thread(target=self.display_images, args=(folder_path,))
            display_thread.start()
            self.label00.place_forget()

    ###################################################################################################################
    def detect_images(self):
        if not self.uploaded_folder_path:
            print("Please upload images first.")
            return

        # Initialize progress bar
        self.progress_bar['value'] = 0
        self.progress_bar.update()

        # Use threading to run the text detection script in the background
        detection_thread = threading.Thread(target=self.run_text_detection_script, args=(self.uploaded_folder_path,))
        detection_thread.start()

    def run_text_detection_script(self, folder_path):
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        self.progress_label.pack(side=tk.RIGHT)
        self.progress_bar.pack(side=tk.RIGHT)
        self.progress_text_var.set("0%")

        total_images = len(image_files)
        self.progress_bar["maximum"] = total_images

        for index, image_file in enumerate(image_files, start=1):
            try:
                detect.run_detection(os.path.join(folder_path, image_file))  # Call the detection function
                print(f"Text detection script completed successfully for image: {image_file}")
            except Exception as e:
                print(f"Error running text detection script for image {image_file}: {e}")

            self.progress_text_var.set(f"{index}/{total_images}")
            self.progress_bar["value"] = index
            self.progress_bar.update()

        # Reset progress bar after completion
        self.progress_text_var.set("Detection Done")
        self.progress_bar["value"] = total_images
        self.update_large_canvases()
        self.progress_label.pack_forget()
        self.progress_bar.pack_forget()

    ###################################################################################################################
    def anonymize_images(self):
        if not self.uploaded_folder_path:  # modify this to detected images path
            print("Please detect images first.")
            return

        # Initialize progress bar
        self.progress_bar['value'] = 0
        self.progress_bar.update()

        # Use threading to run the anonymization script in the background
        anonymization_thread = threading.Thread(target=self.run_anonymization_script, args=(self.uploaded_folder_path,))
        anonymization_thread.start()

    def run_anonymization_script(self, folder_path):
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        self.progress_label.pack(side=tk.RIGHT)
        self.progress_bar.pack(side=tk.RIGHT)
        self.progress_text_var.set("0%")
        self.progress_bar['value'] = 0

        total_images = len(image_files)
        self.progress_bar["maximum"] = total_images

        for index, image_file in enumerate(image_files, start=1):
            try:
                anonymize.run_anonymization(os.path.join(folder_path, image_file),
                                            os.path.join(folder_path, 'temp_detected',
                                                         f'mask_{image_file}'))  # Call the detection function
                print(f"Text anonymization script completed successfully for image: {image_file}")
            except Exception as e:
                print(f"Error running text anonymization script for image {image_file}: {e}")

            self.progress_text_var.set(f"{index}/{total_images}")
            self.progress_bar["value"] = index
            self.progress_bar.update()

        # Reset progress bar after completion
        self.progress_text_var.set("Detection Done")
        self.progress_bar["value"] = total_images
        self.update_large_canvases()
        self.progress_label.pack_forget()
        self.progress_bar.pack_forget()

    ###################################################################################################################
    def display_images(self, folder_path):
        self.image_canvas.delete("all")  # Clear existing images on the canvas

        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

        square_size = 120
        border_color = "grey"

        row, col = 0, 0
        for image_file in image_files:
            image_path = os.path.join(folder_path, image_file)
            img = Image.open(image_path)
            img.thumbnail((100, 100))  # Resize image if needed
            photo = ImageTk.PhotoImage(img)

            square_x, square_y = col * square_size, row * square_size

            self.image_canvas.create_rectangle(square_x, square_y, square_x + square_size, square_y + square_size,
                                               outline=border_color, width=1)

            center_x, center_y = square_x + square_size // 2, square_y + square_size // 2

            tag = image_file
            self.image_canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=photo, tags=(tag,))

            col += 1
            if col == 2:
                col = 0
                row += 1

            self.image_canvas.image_references = getattr(self.image_canvas, 'image_references', []) + [photo]
            self.image_canvas.tag_bind(tag, "<Button-1>", self.show_large_image)

        self.image_canvas.config(scrollregion=self.image_canvas.bbox("all"))
        self.scrollbar.update()

    def show_large_image(self, event):
        # Check if the event occurred on self.image_canvas
        if event.widget == self.image_canvas:
            x, y = self.image_canvas.canvasx(event.x), self.image_canvas.canvasy(event.y)
            item = self.image_canvas.find_closest(x, y)

            if item:
                tags = self.image_canvas.gettags(item)
                if tags:
                    image_file = tags[0]
                    bbox = self.image_canvas.bbox(item)

                    self.image_canvas.delete("highlight_rectangle")
                    self.last_clicked_image = item
                    highlight_rectangle = self.image_canvas.create_rectangle(
                        bbox, outline="red", width=2, tags="highlight_rectangle"
                    )

                    original_img = Image.open(os.path.join(self.uploaded_folder_path, image_file))
                    original_img.thumbnail((530, 530))  # Resize image if needed
                    original_photo = ImageTk.PhotoImage(original_img)

                    self.large_image_canvas1.delete("all")
                    self.large_image_canvas2.delete("all")
                    self.large_image_canvas3.delete("all")
                    self.large_image_canvas1.create_image(self.large_image_canvas1.winfo_width() / 2,
                                                          self.large_image_canvas1.winfo_height() / 2, anchor=tk.CENTER,
                                                          image=original_photo)
                    self.large_image_canvas1.original_photo_reference = original_photo

                    original_image_name = tags[0]

                    # Update canvas2 with masked image
                    masked_image_name = f"boxes_{original_image_name}"
                    masked_image_path = os.path.join(self.uploaded_folder_path, 'temp_detected', masked_image_name)
                    if os.path.exists(masked_image_path):
                        masked_img = Image.open(masked_image_path)
                        masked_img.thumbnail((530, 530))
                        masked_photo = ImageTk.PhotoImage(masked_img)

                        # Update canvas2 after calling update_idletasks()
                        self.large_image_canvas2.delete("all")
                        self.large_image_canvas2.update_idletasks()
                        self.large_image_canvas2.create_image(self.large_image_canvas2.winfo_width() / 2,
                                                              self.large_image_canvas2.winfo_height() / 2,
                                                              anchor=tk.CENTER, image=masked_photo)
                        self.large_image_canvas2.masked_photo_reference = masked_photo

                    # Update canvas3 with anonymized image
                    anonymized_image_name = f"anonymized_{original_image_name}"
                    anonymized_image_path = os.path.join(self.uploaded_folder_path, 'temp_anonymized',
                                                         anonymized_image_name)
                    if os.path.exists(anonymized_image_path):
                        anonymized_img = Image.open(anonymized_image_path)
                        anonymized_img.thumbnail((530, 530))
                        anonymized_photo = ImageTk.PhotoImage(anonymized_img)

                        # Update canvas3 after calling update_idletasks()
                        self.large_image_canvas3.delete("all")
                        self.large_image_canvas3.update_idletasks()
                        self.large_image_canvas3.create_image(self.large_image_canvas3.winfo_width() / 2,
                                                              self.large_image_canvas3.winfo_height() / 2,
                                                              anchor=tk.CENTER, image=anonymized_photo)
                        self.large_image_canvas3.anonymized_photo_reference = anonymized_photo

    def update_large_canvases(self):
        # Get the currently selected image
        selected_item = self.last_clicked_image
        if selected_item:
            tags = self.image_canvas.gettags(selected_item)
            if tags:
                original_image_name = tags[0]

                # Update canvas1 with original image
                original_image_path = os.path.join(self.uploaded_folder_path, original_image_name)
                if os.path.exists(original_image_path):
                    original_img = Image.open(original_image_path)
                    self.large_image_canvas1.update_idletasks()
                    original_img.thumbnail(
                        (self.large_image_canvas1.winfo_width() / 1.05, self.large_image_canvas1.winfo_height() / 1.05))
                    original_photo = ImageTk.PhotoImage(original_img)

                    # Update canvas1 after calling update_idletasks()
                    self.large_image_canvas1.delete("all")
                    self.large_image_canvas1.update_idletasks()
                    self.large_image_canvas1.create_image(self.large_image_canvas1.winfo_width() / 2,
                                                          self.large_image_canvas1.winfo_height() / 2,
                                                          anchor=tk.CENTER, image=original_photo)
                    self.large_image_canvas1.original_photo_reference = original_photo

                # Update canvas2 with masked image
                masked_image_name = f"boxes_{original_image_name}"
                masked_image_path = os.path.join(self.uploaded_folder_path, 'temp_detected', masked_image_name)
                if os.path.exists(masked_image_path):
                    masked_img = Image.open(masked_image_path)
                    self.large_image_canvas2.update_idletasks()
                    masked_img.thumbnail(
                        (self.large_image_canvas2.winfo_width() / 1.05, self.large_image_canvas2.winfo_height() / 1.05))
                    masked_photo = ImageTk.PhotoImage(masked_img)

                    # Update canvas2 after calling update_idletasks()
                    self.large_image_canvas2.delete("all")
                    self.large_image_canvas2.update_idletasks()
                    self.large_image_canvas2.create_image(self.large_image_canvas2.winfo_width() / 2,
                                                          self.large_image_canvas2.winfo_height() / 2,
                                                          anchor=tk.CENTER, image=masked_photo)
                    self.large_image_canvas2.masked_photo_reference = masked_photo

                # Update canvas3 with anonymized image
                anonymized_image_name = f"anonymized_{original_image_name}"
                anonymized_image_path = os.path.join(self.uploaded_folder_path, 'temp_anonymized',
                                                     anonymized_image_name)
                if os.path.exists(anonymized_image_path):
                    anonymized_img = Image.open(anonymized_image_path)
                    self.large_image_canvas3.update_idletasks()
                    anonymized_img.thumbnail(
                        (self.large_image_canvas2.winfo_width() / 1.05, self.large_image_canvas2.winfo_height() / 1.05))
                    anonymized_photo = ImageTk.PhotoImage(anonymized_img)

                    # Update canvas3 after calling update_idletasks()
                    self.large_image_canvas3.delete("all")
                    self.large_image_canvas3.update_idletasks()
                    self.large_image_canvas3.create_image(self.large_image_canvas3.winfo_width() / 2,
                                                          self.large_image_canvas3.winfo_height() / 2,
                                                          anchor=tk.CENTER, image=anonymized_photo)
                    self.large_image_canvas3.anonymized_photo_reference = anonymized_photo

    ###################################################################################################################
    def update_progress(self, processed_images, total_images):
        progress_value = processed_images / total_images * 100
        self.progress_bar['value'] = progress_value
        self.progress_text_var.set(f" {progress_value:.0f}%")
        self.progress_bar.update()

    def cleanup(self):
        # Check if uploaded_folder_path is provided
        if not self.uploaded_folder_path:
            print("Error: No path provided for cleanup.")
            return

        # This function will be called when the program exits
        detected_images_path = os.path.join(self.uploaded_folder_path, 'temp_detected')
        anonymized_images_path = os.path.join(self.uploaded_folder_path, 'temp_anonymized')

        # Check if the 'temp_detected' directory exists, and delete it
        if os.path.exists(detected_images_path):
            shutil.rmtree(detected_images_path)

        # Check if the 'temp_anonymized' directory exists, and delete it
        if os.path.exists(anonymized_images_path):
            shutil.rmtree(anonymized_images_path)

        # sys.exit()


if __name__ == "__main__":
    root = tk.Tk()
    app = MedicalImageAnonymizationTool(root)
    atexit.register(app.cleanup)
    atexit.register(delete_lock)
    root.mainloop()