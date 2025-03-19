import os
import re
import tkinter as tk
from tkinter import Listbox, Label, Entry, Button, Frame, Scrollbar, Canvas, simpledialog, Text, messagebox, Toplevel, PhotoImage
from PIL import Image, ImageTk, ImageGrab, ImageEnhance
import pytesseract  # Import pytesseract
import subprocess
import pyperclip
import shutil # Import shutil

# Path to database folder
BASE_DIR = r"F:\database"  # Replace with your actual path
SCREENSHOTS_DIR = r"F:\screenshots" # Replace with your screenshot path


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

class ImageGallery:
    def __init__(self, root):
        self.root = root
        self.root.title("Seascape Image Viewer")
        self.root.geometry("1200x800")

        # Theme Colors (Water & Sea Inspired)
        self.bg_color = '#003049'  # Deep Sea Blue
        self.fg_color = '#FCBF49'  # Sand Yellow
        self.accent_color = '#D62828' # Coral Red
        self.button_bg = '#4169E1'  # Royal Blue
        self.button_fg = 'white'
        self.listbox_bg = '#87CEEB'  # Sky Blue
        self.listbox_fg = '#003049'  # Deep Sea Blue

        self.root.configure(bg=self.bg_color)

        # Top Frame
        self.top_frame = Frame(root, bg=self.bg_color, borderwidth=2, relief=tk.GROOVE)
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Search Entry
        self.search_var = tk.StringVar()
        self.search_entry = Entry(self.top_frame, textvariable=self.search_var, font=("Arial", 14), bg='white', fg='black', insertbackground='black')  # Light Entry
        self.search_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Create Folder Input and Button (In Top Frame)
        self.new_folder_var = tk.StringVar()
        self.new_folder_entry = Entry(self.top_frame, textvariable=self.new_folder_var, font=("Arial", 14), bg='white', fg='black', insertbackground='black')
        self.new_folder_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")  # Below Search Entry

        button_style = {'bg': self.button_bg, 'fg': self.button_fg, 'font': ("Arial", 12), 'borderwidth': 2, 'relief': tk.RAISED, 'padx':5, 'pady':5}
        Button(self.top_frame, text="Create Folder", command=self.create_new_folder, **button_style).grid(row=1, column=1, padx=5, pady=5, sticky="ew") # beside new_folder_entry


        # Folder Listbox Frame
        self.folder_frame = Frame(self.top_frame, bg=self.bg_color)
        self.folder_frame.grid(row=0, column=2, rowspan=2, padx=5, pady=5, sticky="nsew")  # Make it span 2 rows


        # Folder Listbox
        self.folder_listbox = Listbox(self.folder_frame, bg=self.listbox_bg, fg=self.listbox_fg, font=("Arial", 12), height=5, borderwidth=2, relief=tk.SUNKEN)
        self.folder_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.folder_scrollbar = Scrollbar(self.folder_frame, orient=tk.VERTICAL)
        self.folder_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.folder_listbox.config(yscrollcommand=self.folder_scrollbar.set)
        self.folder_scrollbar.config(command=self.folder_listbox.yview)

        # Remove double click, use single click to load images
        #self.folder_listbox.bind("<Double-Button-1>", self.load_images)
        self.folder_listbox.bind("<ButtonRelease-1>", self.load_images) # load image on single click

        self.folder_listbox.bind("<<ListboxSelect>>", self.on_folder_select)  # Bind single click

        # Configure column weights for top_frame
        self.top_frame.columnconfigure(0, weight=1)  # Search entry column
        self.top_frame.columnconfigure(1, weight=1)  # create button column
        self.top_frame.columnconfigure(2, weight=2)  # Folder listbox column - takes more space

        # Navigation Frame
        self.nav_frame = Frame(root, bg=self.bg_color, borderwidth=2, relief=tk.GROOVE)
        self.nav_frame.pack(fill=tk.X, pady=10, padx=10)

        # Button Styling
        button_style = {'bg': self.button_bg, 'fg': self.button_fg, 'font': ("Arial", 12), 'borderwidth': 2, 'relief': tk.RAISED, 'padx':5, 'pady':5}

        Button(self.nav_frame, text="Previous", command=self.prev_image, **button_style).pack(side=tk.LEFT, padx=5)
        Button(self.nav_frame, text="Next", command=self.next_image, **button_style).pack(side=tk.LEFT, padx=5)
        Button(self.nav_frame, text="Edit in Paint", command=self.edit_image, **button_style).pack(side=tk.RIGHT, padx=5)
        Button(self.nav_frame, text="Go to Image", command=self.go_to_image, **button_style).pack(side=tk.LEFT, padx=5)  # Added "Go to Image" button
        self.ocr_button = Button(self.nav_frame, text="Extract Text (OCR)", command=self.open_ocr_popup, **button_style)
        self.ocr_button.pack(side=tk.LEFT, padx=5)  # OCR Button
        self.tag_button = Button(self.nav_frame, text="Edit Tags", command=self.open_tag_editor, **button_style)
        self.tag_button.pack(side=tk.LEFT, padx=5)
        self.notes_button = Button(self.nav_frame, text="Notes", command=self.open_notes_editor, **button_style)
        self.notes_button.pack(side=tk.LEFT, padx=5)
        self.gallery_button = Button(self.nav_frame, text="Gallery", command=self.toggle_gallery, **button_style)
        self.gallery_button.pack(side=tk.LEFT, padx=5)
        Button(self.nav_frame, text="Open in Explorer", command=self.open_in_explorer, **button_style).pack(side=tk.LEFT, padx=5)
        Button(self.nav_frame, text="Copy Path", command=self.copy_path_to_clipboard, **button_style).pack(side=tk.LEFT, padx=5)


        # Info Labels
        label_style = {'bg': self.bg_color, 'fg': self.fg_color, 'font': ("Arial", 12)}
        self.image_count_label = Label(self.nav_frame, text="T: 0", **label_style)
        self.image_count_label.pack(side=tk.LEFT, padx=5)

        self.selected_image_label = Label(self.nav_frame, text="s: 0/0", **label_style)
        self.selected_image_label.pack(side=tk.LEFT, padx=5)

        # Image Canvas
        self.image_canvas = Canvas(root, bg=self.bg_color, highlightthickness=0, borderwidth=2, relief=tk.SOLID)
        self.image_canvas.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Bind Mousewheel
        self.image_canvas.bind("<MouseWheel>", self.zoom_with_scroll)  # Standard Windows
        self.image_canvas.bind("<Button-4>", self.zoom_with_scroll)  # Linux
        self.image_canvas.bind("<Button-5>", self.zoom_with_scroll)  # Linux

        #Bind mouse events for bounding box selection
        self.image_canvas.bind("<ButtonPress-1>", self.start_selection)
        self.image_canvas.bind("<B1-Motion>", self.update_selection)
        self.image_canvas.bind("<ButtonRelease-1>", self.end_selection)

        # Image Data
        self.image_paths = []
        self.current_index = 0
        self.current_image = None
        self.original_image = None
        self.canvas_image_id = None
        self.zoom_level = 1.0
        self.mouse_x = 0
        self.mouse_y = 0
        self.selection_start_x = None
        self.selection_start_y = None
        self.selection_end_x = None
        self.selection_end_y = None
        self.selection_rectangle = None
        self.current_tags = []  # Store tags for the current image
        self.tag_window = None  # Add this line
        self.ocr_window = None  # Add this line
        self.ocr_text_widget = None
        self.notes_window = None # Line add
        self.gallery_window = None # add this line
        self.gallery_images = [] # Add this line
        self.gallery_index = 0 # Add this line
        self.thumbnail_size = (128, 128) # Define thumbnail size

        # Bind Motion to Canvas
        self.image_canvas.bind("<Motion>", self.update_mouse_position)

        # Load Folders
        self.load_folders()

        # Key Bindings
        root.bind("<Left>", self.prev_image)
        root.bind("<Right>", self.next_image)
        root.bind("<Control-e>", self.edit_image)

        self.search_entry.bind("<KeyRelease>", self.update_folder_list)

    def load_folders(self):
        if os.path.exists(BASE_DIR):
            self.all_folders = sorted([f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))], key=natural_sort_key)
            self.update_folder_list()

    def update_folder_list(self, event=None):
        search_text = self.search_var.get().lower()
        search_words = search_text.split()
        self.folder_listbox.delete(0, tk.END)
        for folder in self.all_folders:
            folder_lower = folder.lower()
            match = True
            for word in search_words:
                if word not in folder_lower:
                    # Check if the tag exist in the folder, if so the tag exist in the image
                    folder_path = os.path.join(BASE_DIR, folder, "tags.txt")
                    if os.path.exists(folder_path):
                        with open(folder_path, "r") as f:
                            tags = f.read().splitlines()
                            if word not in tags:
                                match = False
                                break
                    else:
                        match = False
                        break
            if match:
                self.folder_listbox.insert(tk.END, folder)

    def filter_folders(self, event):
        query = self.search_var.get().lower()
        self.folders = sorted([f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f)) and query in f.lower()], key=natural_sort_key)
        self.update_folder_list()

    def load_images(self, event=None):
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            return

        selected_folder = self.folder_listbox.get(selected_folder_index)
        folder_path = os.path.join(BASE_DIR, selected_folder)
        self.image_paths = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('png', 'jpg', 'jpeg'))], key=natural_sort_key)

        if self.image_paths:
            self.current_index = 0
            self.update_image_count()
            self.show_image()
            self.load_tags()
            self.load_notes()
            self.folder_listbox.selection_set(selected_folder_index)
            # After load the images need to call method load_gallery_images
            self.load_gallery_images(folder_path)
        else:
            # Handle empty folder case
            self.clear_image()
            self.update_image_count()
            self.folder_listbox.selection_set(selected_folder_index) # Ensure folder remains selected.
            messagebox.showinfo("Info", "This folder is empty.") # Display a message.
            self.gallery_images = []
            self.load_gallery_images(folder_path) # Still want to load, but will be empty


    def show_image(self):
        if self.image_paths:
            try:
                image_path = self.image_paths[self.current_index]
                self.original_image = Image.open(image_path)
                self.zoom_level = 1.0
                self.update_zoom()
                self.update_selected_image_label()
                self.reset_selection() #reset selection
            except Exception as e:
                print(f"Error displaying image: {e}")
                self.clear_image()

    def clear_image(self):
        if self.canvas_image_id:
            self.image_canvas.delete(self.canvas_image_id)
            self.canvas_image_id = None

        self.current_image = None
        self.original_image = None

    def next_image(self, event=None):
        if self.image_paths:
            self.current_index = (self.current_index + 1) % len(self.image_paths)
            self.show_image()
            self.load_tags()
            self.load_notes()

    def prev_image(self, event=None):
        if self.image_paths:
            self.current_index = (self.current_index - 1) % len(self.image_paths)
            self.show_image()
            self.load_tags()
            self.load_notes()

    def go_to_image(self):
        if not self.image_paths:
            return

        num_images = len(self.image_paths)
        input_value = simpledialog.askinteger("Go to Image", f"Enter image number (1-{num_images}):",
                                            parent=self.root,
                                            minvalue=1, maxvalue=num_images)
        if input_value is not None:
            target_index = input_value - 1
            if 0 <= target_index < num_images:
                self.current_index = target_index
                self.show_image()
                self.load_tags()
                self.load_notes()

    def edit_image(self, event=None):
        if self.image_paths:
            try:
                os.system(f'mspaint "{self.image_paths[self.current_index]}"')
            except Exception as e:
                print(f"Error opening image in Paint: {e}")

    def update_image_count(self):
        total_images = len(self.image_paths)
        self.image_count_label.config(text=f"T: {total_images}")
        self.update_selected_image_label()

    def update_selected_image_label(self):
        if self.image_paths:
            self.selected_image_label.config(text=f"s: {self.current_index + 1}/{len(self.image_paths)}")
        else:
            self.selected_image_label.config(text="s: 0/0")

    def update_zoom(self, event=None):
        if self.original_image:
            try:
                # Calculate new dimensions
                width = int(self.original_image.width * self.zoom_level)
                height = int(self.original_image.height * self.zoom_level)

                # Resize the image
                resized_image = self.original_image.resize((width, height), Image.LANCZOS)

                # Convert to PhotoImage
                self.current_image = ImageTk.PhotoImage(resized_image)

                # Calculate offset for zoom position
                x_offset = int(self.mouse_x * (self.zoom_level - 1))
                y_offset = int(self.mouse_y * (self.zoom_level - 1))

                # Display on Canvas: delete previous, create new
                if self.canvas_image_id:
                    self.image_canvas.delete(self.canvas_image_id)

                self.canvas_image_id = self.image_canvas.create_image(
                    self.image_canvas.winfo_width() // 2 - x_offset,  # Center horizontally
                    self.image_canvas.winfo_height() // 2 - y_offset, # Center vertically
                    anchor=tk.CENTER,
                    image=self.current_image
                )


            except Exception as e:
                print(f"Error zooming image: {e}")

    def zoom_with_scroll(self, event):
        if event.num == 4 or event.delta > 0:
            self.zoom_level += 0.1
            self.update_zoom()
        elif event.num == 5 or event.delta < 0:
            self.zoom_level -= 0.1
            self.update_zoom()

    def update_mouse_position(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def start_selection(self, event):
        self.selection_start_x = self.image_canvas.canvasx(event.x)
        self.selection_start_y = self.image_canvas.canvasy(event.y)
        #Remove old rectangle
        if self.selection_rectangle:
             self.image_canvas.delete(self.selection_rectangle)
             self.selection_rectangle = None

    def update_selection(self, event):
        cur_x = self.image_canvas.canvasx(event.x)
        cur_y = self.image_canvas.canvasy(event.y)

        if self.selection_start_x and self.selection_start_y:
            #Remove old rectangle
            if self.selection_rectangle:
                 self.image_canvas.delete(self.selection_rectangle)

            self.selection_rectangle = self.image_canvas.create_rectangle(
                self.selection_start_x, self.selection_start_y, cur_x, cur_y,
                outline="red", width=2
            )

    def end_selection(self, event):
        self.selection_end_x = self.image_canvas.canvasx(event.x)
        self.selection_end_y = self.image_canvas.canvasy(event.y)

    def reset_selection(self):
        """Reset selection variables and remove selection rectangle"""
        self.selection_start_x = None
        self.selection_start_y = None
        self.selection_end_x = None
        self.selection_end_y = None
        if self.selection_rectangle:
            self.image_canvas.delete(self.selection_rectangle)
            self.selection_rectangle = None

    def enhance_image(self, image):
        """Enhance the image for better OCR results"""
        # Convert to grayscale
        enhanced_image = image.convert('L')

        # Increase contrast
        enhancer = ImageEnhance.Contrast(enhanced_image)
        enhanced_image = enhancer.enhance(2) # Increase contrast by a factor of 2

        # Sharpen the image
        enhancer = ImageEnhance.Sharpness(enhanced_image)
        enhanced_image = enhancer.enhance(2)  # Increase sharpness

        return enhanced_image

    def open_tag_editor(self):
        """Opens a popup window to edit tags."""
        if self.tag_window and tk.Toplevel.winfo_exists(self.tag_window):
            self.tag_window.focus()  # If window exists, bring it to front
            return

        self.tag_window = Toplevel(self.root)
        self.tag_window.title("Edit Tags")
        self.tag_window.geometry("400x300")

        self.tag_text = Text(self.tag_window, bg='white', fg='black', font=("Arial", 12))
        self.tag_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tag_scrollbar = Scrollbar(self.tag_window, orient=tk.VERTICAL)
        self.tag_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tag_text.config(yscrollcommand=self.tag_scrollbar.set)
        self.tag_scrollbar.config(command=self.tag_text.yview)

        self.tag_text.bind("<KeyRelease>", self.auto_save_tags)  # Bind auto-save

        # Load tags into the text area when the window opens
        self.load_tags_into_text()

        self.tag_window.protocol("WM_DELETE_WINDOW", self.on_tag_window_close)

    def load_tags_into_text(self):
        """Loads the current tags into the tag editor's text area."""
        self.tag_text.delete("1.0", tk.END)
        self.tag_text.insert("1.0", "\n".join(self.current_tags))


    def auto_save_tags(self, event=None):
        """Saves the tags to file automatically."""
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            return

        selected_folder = self.folder_listbox.get(selected_folder_index)
        folder_path = os.path.join(BASE_DIR, selected_folder)
        tags_file_path = os.path.join(folder_path, "tags.txt")

        if self.tag_window and tk.Toplevel.winfo_exists(self.tag_window):
             tags = self.tag_text.get("1.0", tk.END).strip()
        else:
            return #don't save if there is no window
        try:
            with open(tags_file_path, "w") as f:
                f.write(tags)
            self.current_tags = [tag.strip() for tag in tags.splitlines() if tag.strip()]
        except Exception as e:
            print(f"Error saving tags automatically: {e}")


    def load_tags(self):
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            return

        selected_folder = self.folder_listbox.get(selected_folder_index)
        folder_path = os.path.join(BASE_DIR, selected_folder)
        tags_file_path = os.path.join(folder_path, "tags.txt")

        self.current_tags = []  # Clear existing tags
        if os.path.exists(tags_file_path):
            try:
                with open(tags_file_path, "r") as f:
                    tags = f.read().strip()
                    self.current_tags = [tag.strip() for tag in tags.splitlines() if tag.strip()]
            except Exception as e:
                print(f"Error loading tags: {e}")

        if self.tag_window and tk.Toplevel.winfo_exists(self.tag_window):
            self.load_tags_into_text()  # Load tags into editor if it's open

    def on_tag_window_close(self):
        """Handles closing of the tag editor window."""
        self.tag_window.destroy()
        self.tag_window = None

    def on_folder_select(self, event=None):
        """Loads the tags when a folder is selected in the listbox."""
        self.load_tags()  # Call load_tags directly
        self.load_notes() # Call load_notes directly

    def open_ocr_popup(self):
        """Opens a popup window to display OCR text and performs the OCR."""
        if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
            self.ocr_window.focus()  # If window exists, bring it to front
            self.perform_ocr() # Perform OCR again to refresh
            return

        self.ocr_window = Toplevel(self.root)
        self.ocr_window.title("Extracted Text (OCR)")
        self.ocr_window.geometry("600x400")  # Adjust size as needed

        self.ocr_text_widget = Text(self.ocr_window, bg='white', fg='black', font=("Arial", 12))
        self.ocr_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.ocr_scrollbar = Scrollbar(self.ocr_window, orient=tk.VERTICAL)
        self.ocr_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ocr_text_widget.config(yscrollcommand=self.ocr_scrollbar.set)
        self.ocr_scrollbar.config(command=self.ocr_text_widget.yview)

        self.perform_ocr()  # Perform OCR and display the text

        self.ocr_window.protocol("WM_DELETE_WINDOW", self.on_ocr_window_close)


    def perform_ocr(self):
        """Performs the OCR and displays the extracted text in the popup window."""
        if not self.original_image:
            if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
                self.ocr_text_widget.delete("1.0", tk.END) #Clear text
            return

        if not self.selection_start_x or not self.selection_start_y or not self.selection_end_x or not self.selection_end_y:
            if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
                self.ocr_text_widget.delete("1.0", tk.END) #Clear text
            return

        x0 = min(self.selection_start_x, self.selection_end_x)
        y0 = min(self.selection_start_y, self.selection_end_y)
        x1 = max(self.selection_start_x, self.selection_end_x)
        y1 = max(self.selection_start_y, self.selection_end_y)

        try:
            x_root = self.root.winfo_rootx() + self.image_canvas.winfo_x()
            y_root = self.root.winfo_rooty() + self.image_canvas.winfo_y()

            bbox_screen = (x_root + x0, y_root + y0, x_root + x1, y_root + y1)
            cropped_image = ImageGrab.grab(bbox=bbox_screen)

            enhanced_image = self.enhance_image(cropped_image)

            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Replace with your Tesseract path
            text = pytesseract.image_to_string(enhanced_image)

            if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
                self.ocr_text_widget.delete("1.0", tk.END)
                self.ocr_text_widget.insert("1.0", text)


        except Exception as e:
            print(f"OCR Error: {e}")
            if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
                self.ocr_text_widget.delete("1.0", tk.END) #Clear text


    def on_ocr_window_close(self):
        """Handles closing of the OCR window."""
        self.ocr_window.destroy()
        self.ocr_window = None

    def open_notes_editor(self):
        """Opens a popup window to edit notes.  This window persists on top, and binds keys."""
        if self.notes_window and tk.Toplevel.winfo_exists(self.notes_window):
            self.notes_window.focus()  # If window exists, bring it to front
            return

        self.notes_window = Toplevel(self.root)
        self.notes_window.title("Edit Notes")
        self.notes_window.geometry("400x300")

        # Make the notes window stay on top
        self.notes_window.attributes('-topmost', True)

        self.notes_text = Text(self.notes_window, bg='white', fg='black', font=("Arial", 12))
        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.notes_scrollbar = Scrollbar(self.notes_window, orient=tk.VERTICAL)
        self.notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.notes_text.config(yscrollcommand=self.notes_scrollbar.set)
        self.notes_scrollbar.config(command=self.notes_text.yview)

        self.notes_text.bind("<KeyRelease>", self.auto_save_notes)  # Bind auto-save

        # Load notes into the text area when the window opens
        self.load_notes_into_text()

        self.notes_window.protocol("WM_DELETE_WINDOW", self.on_notes_window_close) # Allow the window to be closed.

        # Bind arrow keys to the notes window
        self.notes_window.bind("<Left>", self.prev_image)  #Bind arrow keys
        self.notes_window.bind("<Right>", self.next_image)

    def load_notes_into_text(self):
        """Loads the current notes into the notes editor's text area."""
        if not self.notes_window or not tk.Toplevel.winfo_exists(self.notes_window):
            return #Do nothing if the window isn't open.

        self.notes_text.delete("1.0", tk.END) #clear widget
        folder_index = self.folder_listbox.curselection()
        if folder_index:
             selected_folder = self.folder_listbox.get(folder_index)
             folder_path = os.path.join(BASE_DIR, selected_folder)
             notes_file_path = os.path.join(folder_path, "notes.txt")
             if os.path.exists(notes_file_path):
                 try:
                    with open(notes_file_path, "r") as f:
                        notes = f.read()
                    self.notes_text.insert("1.0", notes)
                 except Exception as e:
                    print(f"Error loading notes: {e}")


    def auto_save_notes(self, event=None):
        """Saves the notes to file automatically."""
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            return

        selected_folder = self.folder_listbox.get(selected_folder_index)
        folder_path = os.path.join(BASE_DIR, selected_folder)
        notes_file_path = os.path.join(folder_path, "notes.txt")

        if self.notes_window and tk.Toplevel.winfo_exists(self.notes_window):
             notes = self.notes_text.get("1.0", tk.END).strip()
        else:
            return #don't save if there is no window

        try:
            with open(notes_file_path, "w") as f:
                f.write(notes)
        except Exception as e:
            print(f"Error saving notes automatically: {e}")

    def load_notes(self):
        """Load notes from file."""

        folder_index = self.folder_listbox.curselection()
        if folder_index:
            selected_folder = self.folder_listbox.get(folder_index)
            folder_path = os.path.join(BASE_DIR, selected_folder)
            notes_file_path = os.path.join(folder_path, "notes.txt")

            if os.path.exists(notes_file_path):
                try:
                    with open(notes_file_path, "r") as f:
                        notes = f.read().strip()
                except Exception as e:
                    print(f"Error loading notes: {e}")

            if self.notes_window and tk.Toplevel.winfo_exists(self.notes_window):
                self.load_notes_into_text()  # Load notes into editor if it's open


    def on_notes_window_close(self):
        """Handles closing of the notes window."""
        self.notes_window.destroy()
        self.notes_window = None

    def load_gallery_images(self, folder_path):
        try:
            self.gallery_images = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('png', 'jpg', 'jpeg'))], key=natural_sort_key)
        except Exception as e:
            print(f"Error loading gallery images: {e}")
            self.gallery_images = []

    def toggle_gallery(self):
        if self.gallery_window and tk.Toplevel.winfo_exists(self.gallery_window):
            # The gallery is already open.  Just close it
            self.gallery_window.destroy()
            self.gallery_window = None

            #Re-show active image in the main GUI
            self.show_image()
        else:
             self.open_gallery() # Open it

    def open_gallery(self):
        if self.gallery_window and tk.Toplevel.winfo_exists(self.gallery_window):
            self.gallery_window.focus()
            return

        if not self.gallery_images:
            #messagebox.showinfo("Info","No images in gallery!") # display
            return # do nothing

        self.gallery_window = Toplevel(self.root)
        self.gallery_window.title("Image Gallery")

        # Using a Canvas to hold the thumbnails
        self.gallery_canvas = Canvas(self.gallery_window, bg=self.bg_color)
        self.gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.gallery_scrollbar_y = Scrollbar(self.gallery_window, orient=tk.VERTICAL, command=self.gallery_canvas.yview)
        self.gallery_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.gallery_canvas.configure(yscrollcommand=self.gallery_scrollbar_y.set)
        self.gallery_canvas.bind("<Configure>", self.configure_gallery_canvas)

        self.gallery_frame = Frame(self.gallery_canvas, bg=self.bg_color)
        self.gallery_canvas.create_window((0, 0), window=self.gallery_frame, anchor="nw")

        self.populate_gallery() # Populate the gallery

        self.gallery_window.protocol("WM_DELETE_WINDOW", self.on_gallery_window_close)

        # Add Mousewheel event binding
        self.gallery_canvas.bind("<MouseWheel>", self.scroll_gallery)  # Windows
        self.gallery_canvas.bind("<Button-4>", self.scroll_gallery)  # Linux
        self.gallery_canvas.bind("<Button-5>", self.scroll_gallery)  # Linux


    def scroll_gallery(self, event):
        """Handles mousewheel scrolling in the gallery."""
        if event.num == 4 or event.delta > 0:
            self.gallery_canvas.yview_scroll(-1, "units")  # Scroll up
        elif event.num == 5 or event.delta < 0:
            self.gallery_canvas.yview_scroll(1, "units")  # Scroll down
        else: #windows
             self.gallery_canvas.yview_scroll(int(-1*(event.delta/120)), "units") # scroll
             #event.delta is platform dependent.  This is for windows.

    def configure_gallery_canvas(self, event):
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))

    def populate_gallery(self):
        """Populates the gallery with thumbnail images."""

        #Clear existing widgets in frame.
        for widget in self.gallery_frame.winfo_children():
             widget.destroy()

        num_columns = 4  # Adjust as desired
        row = 0
        col = 0

        for i, image_name in enumerate(self.gallery_images):
            image_path = os.path.join(os.path.dirname(self.image_paths[0]), image_name) # Use dirname to be safe
            try:
                img = Image.open(image_path)
                img.thumbnail(self.thumbnail_size)
                photo = ImageTk.PhotoImage(img)

                button = Button(self.gallery_frame, image=photo, borderwidth=0, command=lambda index=i: self.on_gallery_image_select_index(index))
                button.image = photo  # Keep a reference to the image
                button.grid(row=row, column=col, padx=5, pady=5)
                col += 1
                if col >= num_columns:
                    col = 0
                    row += 1
            except Exception as e:
                print(f"Error loading thumbnail: {e}")

    def on_gallery_image_select_index(self, index):
        """Handles gallery image selection based on index."""
        try:
            self.gallery_index = index
            self.current_index = self.image_paths.index(os.path.join(os.path.dirname(self.image_paths[0]), self.gallery_images[self.gallery_index]))
            self.show_image()
            self.load_tags()
            self.load_notes()
            self.toggle_gallery() #close the gallery.
        except Exception as e:
            print(f"Error gallery image selection: {e}")

    def on_gallery_image_select(self, event):
        selected_index = self.gallery_listbox.curselection()
        if selected_index:
            self.gallery_index = selected_index[0]
            self.current_index = self.image_paths.index(os.path.join(os.path.dirname(self.image_paths[0]), self.gallery_images[self.gallery_index]))
            self.show_image()
            self.load_tags()
            self.load_notes()
            self.toggle_gallery() #close the gallery.

    def on_gallery_window_close(self):
        """Handles closing of the gallery window."""
        self.gallery_window.destroy()
        self.gallery_window = None
        self.show_image()

    def open_in_explorer(self):
        """Opens the selected folder in the file explorer."""
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            #messagebox.showinfo("Info", "No folder selected.")
            return

        selected_folder = self.folder_listbox.get(selected_folder_index)
        folder_path = os.path.join(BASE_DIR, selected_folder)

        if os.path.exists(folder_path):
            try:
                subprocess.Popen(['explorer', folder_path])
            except Exception as e:
                #messagebox.showerror("Error", f"Could not open folder: {e}")
                pass
        else:
            #messagebox.showerror("Error", "Folder does not exist.")
            pass

    def create_new_folder(self):
        """Creates a new folder in the base directory."""
        new_folder_name = self.new_folder_entry.get().strip()
        if not new_folder_name:
            #messagebox.showinfo("Info", "Please enter a folder name.")
            return

        new_folder_path = os.path.join(BASE_DIR, new_folder_name)

        try:
            os.makedirs(new_folder_path, exist_ok=False)  # exist_ok=False to prevent overwriting
            #messagebox.showinfo("Success", f"Folder '{new_folder_name}' created successfully.")
            self.load_folders()  # Refresh folder list
            self.new_folder_entry.delete(0, tk.END) # Clear the entry field
            self.move_screenshots(new_folder_path) # Move the screenshots
        except FileExistsError:
            #messagebox.showerror("Error", "Folder with that name already exists.")
            pass
        except Exception as e:
            #messagebox.showerror("Error", f"Could not create folder: {e}")
            pass

    def move_screenshots(self, dest_folder):
        """Moves all images from the screenshots directory to the destination folder."""
        if not os.path.exists(SCREENSHOTS_DIR):
            #messagebox.showinfo("Info", "Screenshots directory does not exist.")
            return

        image_files = [f for f in os.listdir(SCREENSHOTS_DIR) if f.lower().endswith(('png', 'jpg', 'jpeg'))]

        if not image_files:
            #messagebox.showinfo("Info", "No screenshots to move.")
            return

        try:
            for image_file in image_files:
                source_path = os.path.join(SCREENSHOTS_DIR, image_file)
                dest_path = os.path.join(dest_folder, image_file)
                shutil.move(source_path, dest_path)
            #messagebox.showinfo("Success", f"Moved {len(image_files)} screenshots to '{dest_folder}'.")
            self.load_folders()  # Refresh folder list
        except Exception as e:
            #messagebox.showerror("Error", f"Error moving screenshots: {e}")
            pass



    def copy_path_to_clipboard(self):
        """Copies the path of the selected folder to the clipboard."""
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            #messagebox.showinfo("Info", "No folder selected.")
            return

        selected_folder = self.folder_listbox.get(selected_folder_index)
        folder_path = os.path.join(BASE_DIR, selected_folder)

        if os.path.exists(folder_path):
            try:
                pyperclip.copy(folder_path)
                #messagebox.showinfo("Success", "Folder path copied to clipboard.")
                pass
            except Exception as e:
                #messagebox.showerror("Error", f"Could not copy path to clipboard: {e}")
                pass
        else:
            #messagebox.showerror("Error", "Folder does not exist.")
            pass

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGallery(root)
    app.open_notes_editor()  # Open the notes editor *immediately*

    root.mainloop()
