import os
import re
import tkinter as tk
from tkinter import Listbox, Label, Entry, Button, Frame, Scrollbar, Canvas, simpledialog, Text, messagebox, Toplevel, \
    PhotoImage, Checkbutton, BooleanVar
from PIL import Image, ImageTk, ImageGrab, ImageEnhance
import pytesseract
import subprocess
import pyperclip
import shutil


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


class ImageGallery:
    def __init__(self, root):
        self.root = root
        self.root.title("Seascape Image Viewer")
        self.root.geometry("1200x800")

        self.bg_color = '#003049'
        self.fg_color = '#FCBF49'
        self.accent_color = '#D62828'
        self.button_bg = '#4169E1'
        self.button_fg = 'white'
        self.listbox_bg = '#87CEEB'
        self.listbox_fg = '#003049'

        self.root.configure(bg=self.bg_color)

        # Automatically detect base directories
        self.BASE_DIRS = [f for f in os.listdir(".") if os.path.isdir(f) and f != "__pycache__"]
        self.SCREENSHOTS_DIR = r"F:\Macros\notes\images\screenshots"

        # Top Frame
        self.top_frame = Frame(root, bg=self.bg_color, borderwidth=1, relief=tk.GROOVE, padx=5, pady=5)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)

        # Search Entry
        self.search_var = tk.StringVar()
        self.search_entry = Entry(self.top_frame, textvariable=self.search_var, font=("Arial", 14), bg='white',
                                  fg='black', insertbackground='black')
        self.search_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Checkboxes for BASE_DIRS
        self.checkbox_vars = {}
        self.checkbox_frame = Frame(self.top_frame, bg=self.bg_color, borderwidth=1, relief=tk.GROOVE, padx=5,
                                     pady=5)
        self.checkbox_frame.grid(row=2, column=0, columnspan=5, padx=5, pady=5, sticky="ew")

        row_num = 1
        col_num = 0
        for base_dir in self.BASE_DIRS:
            dir_name = os.path.basename(base_dir)
            self.checkbox_vars[dir_name] = BooleanVar(value=True)  # Set default to True
            checkbox = Checkbutton(self.checkbox_frame, text=dir_name, variable=self.checkbox_vars[dir_name],
                                   bg=self.bg_color, fg=self.fg_color, command=self.update_folder_list)
            checkbox.grid(row=row_num, column=col_num, padx=5, pady=2, sticky="w")
            col_num += 1
            if col_num > 4:
                col_num = 0
                row_num += 1

        # Create Folder Input and Button
        self.new_folder_var = tk.StringVar()
        self.new_folder_entry = Entry(self.top_frame, textvariable=self.new_folder_var, font=("Arial", 14),
                                       bg='white', fg='black', insertbackground='black')
        self.new_folder_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        button_style = {'bg': self.button_bg, 'fg': self.button_fg, 'font': ("Arial", 12), 'borderwidth': 1,
                        'relief': tk.RAISED, 'padx': 3, 'pady': 3}
        Button(self.top_frame, text="Create Folder", command=self.create_new_folder, **button_style).grid(row=1,
                                                                                                             column=1,
                                                                                                             padx=5,
                                                                                                             pady=5,
                                                                                                             sticky="ew")

        # Folder Listbox Frame
        self.folder_frame = Frame(self.top_frame, bg=self.bg_color)
        self.folder_frame.grid(row=0, column=5, rowspan=row_num, padx=5, pady=5, sticky="nsew")
        self.top_frame.columnconfigure(5, weight=2)

        # Folder Listbox
        self.folder_listbox = Listbox(self.folder_frame, bg=self.listbox_bg, fg=self.listbox_fg, font=("Arial", 12),
                                      height=5, borderwidth=1, relief=tk.SUNKEN)
        self.folder_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.folder_scrollbar = Scrollbar(self.folder_frame, orient=tk.VERTICAL)
        self.folder_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.folder_listbox.config(yscrollcommand=self.folder_scrollbar.set)
        self.folder_scrollbar.config(command=self.folder_listbox.yview)

        self.folder_listbox.bind("<ButtonRelease-1>", self.load_images)
        self.folder_listbox.bind("<<ListboxSelect>>", self.on_folder_select)

        # Navigation Frame
        self.nav_frame = Frame(root, bg=self.bg_color, borderwidth=1, relief=tk.GROOVE)
        self.nav_frame.pack(fill=tk.X, pady=5, padx=5)

        # Button Styling
        button_style = {'bg': self.button_bg, 'fg': self.button_fg, 'font': ("Arial", 12), 'borderwidth': 1,
                        'relief': tk.RAISED, 'padx': 3, 'pady': 3}

        Button(self.nav_frame, text="Previous", command=self.prev_image, **button_style).pack(side=tk.LEFT, padx=3)
        Button(self.nav_frame, text="Next", command=self.next_image, **button_style).pack(side=tk.LEFT, padx=3)
        Button(self.nav_frame, text="Edit in Paint", command=self.edit_image, **button_style).pack(side=tk.RIGHT,
                                                                                                    padx=3)
        Button(self.nav_frame, text="Go to Image", command=self.go_to_image, **button_style).pack(side=tk.LEFT,
                                                                                                     padx=3)
        self.ocr_button = Button(self.nav_frame, text="Extract Text (OCR)", command=self.open_ocr_popup,
                                 **button_style)
        self.ocr_button.pack(side=tk.LEFT, padx=3)
        self.tag_button = Button(self.nav_frame, text="Edit Tags", command=self.open_tag_editor, **button_style)
        self.tag_button.pack(side=tk.LEFT, padx=3)
        self.notes_button = Button(self.nav_frame, text="Notes", command=self.open_notes_editor, **button_style)
        self.notes_button.pack(side=tk.LEFT, padx=3)
        self.gallery_button = Button(self.nav_frame, text="Gallery", command=self.toggle_gallery, **button_style)
        self.gallery_button.pack(side=tk.LEFT, padx=3)
        Button(self.nav_frame, text="Open in Explorer", command=self.open_in_explorer, **button_style).pack(
            side=tk.LEFT, padx=3)
        Button(self.nav_frame, text="Copy Path", command=self.copy_path_to_clipboard, **button_style).pack(
            side=tk.LEFT, padx=3)

        # Info Labels
        label_style = {'bg': self.bg_color, 'fg': self.fg_color, 'font': ("Arial", 12)}
        self.image_count_label = Label(self.nav_frame, text="T: 0", **label_style)
        self.image_count_label.pack(side=tk.LEFT, padx=3)

        self.selected_image_label = Label(self.nav_frame, text="s: 0/0", **label_style)
        self.selected_image_label.pack(side=tk.LEFT, padx=3)

        # Image Canvas
        self.image_canvas = Canvas(root, bg=self.bg_color, highlightthickness=0, borderwidth=1, relief=tk.SOLID)
        self.image_canvas.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Bind resize event to canvas
        self.image_canvas.bind("<Configure>", self.resize_image)

        self.image_canvas.bind("<MouseWheel>", self.zoom_with_scroll)
        self.image_canvas.bind("<Button-4>", self.zoom_with_scroll)
        self.image_canvas.bind("<Button-5>", self.zoom_with_scroll)

        self.image_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.image_canvas.bind("<B1-Motion>", self.pan_image)
        self.image_canvas.bind("<ButtonRelease-1>", self.end_pan)

        # OCR Selection Bindings - CTRL + Left Click
        self.image_canvas.bind("<Control-ButtonPress-1>", self.start_selection)
        self.image_canvas.bind("<Control-B1-Motion>", self.update_selection)
        self.image_canvas.bind("<Control-ButtonRelease-1>", self.end_selection)

        self.image_paths = []
        self.current_index = 0
        self.current_image = None
        self.original_image = None
        self.canvas_image_id = None
        self.zoom_level = 1.0
        self.image_x = 0  # added x and y offset for the image
        self.image_y = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.pan_start_x = None
        self.pan_start_y = None

        self.selection_start_x = None
        self.selection_start_y = None
        self.selection_end_x = None
        self.selection_end_y = None
        self.selection_rectangle = None
        self.current_tags = []
        self.tag_window = None
        self.ocr_window = None
        self.ocr_text_widget = None
        self.notes_window = None
        self.gallery_window = None
        self.gallery_images = []
        self.gallery_index = 0
        self.thumbnail_size = (128, 128)

        self.image_canvas.bind("<Motion>", self.update_mouse_position)

        self.load_folders()

        root.bind("<Left>", self.prev_image)
        root.bind("<Right>", self.next_image)
        root.bind("<Control-e>", self.edit_image)
        self.notes_window = None

        self.search_entry.bind("<KeyRelease>", self.update_folder_list)

        #  Create OCR popup and show it immediately
        self.open_ocr_popup(True)

    def load_folders(self):
        self.all_folders = []
        for base_dir in self.BASE_DIRS:
            if os.path.isabs(base_dir):
                full_base_dir = base_dir
            else:
                full_base_dir = os.path.abspath(base_dir)

            if os.path.exists(full_base_dir):
                # folders = [f for f in os.listdir(full_base_dir) if
                #            os.path.isdir(os.path.join(full_base_dir, f))]
                for item in os.listdir(full_base_dir):
                    item_path = os.path.join(full_base_dir, item)
                    if os.path.isdir(item_path):
                        # Append subfolders
                        self.all_folders.append(os.path.join(os.path.basename(full_base_dir), item))

        self.all_folders = sorted(self.all_folders, key=natural_sort_key)
        self.update_folder_list()

    def update_folder_list(self, event=None):
        search_text = self.search_var.get().lower()
        search_words = search_text.split()

        self.folder_listbox.delete(0, tk.END)

        for base_dir in self.BASE_DIRS:
            dir_name = os.path.basename(base_dir)
            if not self.checkbox_vars.get(dir_name, BooleanVar(value=True)).get():
                continue  # Skip if the base directory is not checked

            for folder in self.all_folders:
                # Split the folder path into parent directory and folder name
                parent_dir, folder_name = os.path.split(folder)

                # Check if folder starts with selected dir_name
                if not folder.startswith(dir_name):
                    continue

                # Find the full folder path based on the selected name
                full_folder_path = None
                for base_dir_check in self.BASE_DIRS:
                    if os.path.basename(base_dir_check) == parent_dir:

                        # Check if base_dir_check is absolute or relative
                        if os.path.isabs(base_dir_check):
                            full_base_dir = base_dir_check
                        else:
                            full_base_dir = os.path.abspath(base_dir_check)  # Convert to absolute path

                        full_folder_path = os.path.join(full_base_dir, folder_name)
                        break

                if not full_folder_path:
                    continue

                # search in the tags.txt
                tags_file_path = os.path.join(full_folder_path, "tags.txt")

                if os.path.exists(tags_file_path):
                    with open(tags_file_path, "r") as f:
                        tags = [tag.strip().lower() for tag in f.read().splitlines() if tag.strip()]
                        # Check if every search word is present in the tags
                        tag_match = all(word in tags for word in search_words)
                else:
                    tag_match = False

                # Folder name match logic
                name_match = all(word in folder_name.lower() for word in search_words)

                # insert in the listbox
                if tag_match or name_match:
                    # Show only the folder name instead of the full path
                    self.folder_listbox.insert(tk.END, folder_name)

    def load_images(self, event=None):
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            return

        # Get the folder name from the listbox, not the full path
        selected_folder_name = self.folder_listbox.get(selected_folder_index[0])

        # Find the full folder path based on the selected name
        full_folder_path = None
        for base_dir in self.BASE_DIRS:
            if os.path.isabs(base_dir):
                full_base_dir = base_dir
            else:
                full_base_dir = os.path.abspath(base_dir)

            # Construct the potential full path
            potential_path = os.path.join(full_base_dir, selected_folder_name)

            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                full_folder_path = potential_path
                break

        if not full_folder_path:
            print(f"Error: Could not find full path for folder name {selected_folder_name}")
            return

        self.image_paths = sorted([os.path.join(full_folder_path, f) for f in os.listdir(full_folder_path) if
                                   f.lower().endswith(('png', 'jpg', 'jpeg'))], key=natural_sort_key)

        if self.image_paths:
            self.current_index = 0
            self.update_image_count()
            self.show_image()
            self.load_tags()
            self.load_notes()
            self.folder_listbox.selection_set(selected_folder_index)
            # After load the images need to call method load_gallery_images
            self.load_gallery_images(full_folder_path)
        else:
            # Handle empty folder case
            self.clear_image()
            self.update_image_count()
            self.folder_listbox.selection_set(selected_folder_index)  # Ensure folder remains selected.
            messagebox.showinfo("Info", "This folder is empty.")  # Display a message.
            self.gallery_images = []
            self.load_gallery_images(full_folder_path)  # Still want to load, but will be empty

    def show_image(self):
        if self.image_paths:
            try:
                image_path = self.image_paths[self.current_index]
                self.original_image = Image.open(image_path)
                self.zoom_level = 1.0
                self.image_x = 0  # Reset x and y offset when loading a new image
                self.image_y = 0
                self.resize_image()  # Call resize_image instead of update_zoom
                self.update_selected_image_label()
                self.reset_selection()  # reset selection
                self.perform_ocr() # trigger OCR after showing images
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

    def update_zoom(self):
        if self.original_image:
            try:
                width = int(self.original_image.width * self.zoom_level)
                height = int(self.original_image.height * self.zoom_level)
                resized_image = self.original_image.resize((width, height), Image.LANCZOS)
                self.current_image = ImageTk.PhotoImage(resized_image)

                self.update_image()

            except Exception as e:
                print(f"Error zooming image: {e}")
                messagebox.showerror("Error", f"Zoom error: {e}")

    def zoom_with_scroll(self, event):
        if self.original_image:
            zoom_factor = 1.0
            if event.num == 4 or event.delta > 0:
                zoom_factor = 1.1
            elif event.num == 5 or event.delta < 0:
                zoom_factor = 0.9
            else:
                zoom_factor = 1.0

            if zoom_factor != 1.0:
                self.zoom_level *= zoom_factor
                self.zoom_level = max(0.1, min(self.zoom_level, 10.0))
                self.update_zoom()

    def update_image(self):
        if self.current_image:
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()

            width = self.current_image.width()
            height = self.current_image.height()

            x_offset = (canvas_width - width) // 2 + self.image_x
            y_offset = (canvas_height - height) // 2 + self.image_y

            self.image_canvas.delete(self.canvas_image_id)
            self.canvas_image_id = self.image_canvas.create_image(x_offset, y_offset, anchor=tk.NW,
                                                                   image=self.current_image)
            self.image_canvas.lower(self.canvas_image_id)

    def start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan_image(self, event):
        if self.pan_start_x is not None and self.pan_start_y is not None:
            delta_x = event.x - self.pan_start_x
            delta_y = event.y - self.pan_start_y

            self.image_x += delta_x
            self.image_y += delta_y

            self.pan_start_x = event.x
            self.pan_start_y = event.y

            self.update_image()

    def end_pan(self, event):
        self.pan_start_x = None
        self.pan_start_y = None

    def update_mouse_position(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def start_selection(self, event):
        # Store starting position of selection
        self.selection_start_x = self.image_canvas.canvasx(event.x)
        self.selection_start_y = self.image_canvas.canvasy(event.y)

        # If a rectangle exists, delete it
        if self.selection_rectangle:
            self.image_canvas.delete(self.selection_rectangle)
            self.selection_rectangle = None

    def update_selection(self, event):
        # Get current position
        cur_x = self.image_canvas.canvasx(event.x)
        cur_y = self.image_canvas.canvasy(event.y)

        # Delete old rectangle if it exists
        if self.selection_rectangle:
            self.image_canvas.delete(self.selection_rectangle)

        # Draw new rectangle
        self.selection_rectangle = self.image_canvas.create_rectangle(
            self.selection_start_x, self.selection_start_y, cur_x, cur_y,
            outline="red", width=2
        )

    def end_selection(self, event):
        # Store end position of selection
        self.selection_end_x = self.image_canvas.canvasx(event.x)
        self.selection_end_y = self.image_canvas.canvasy(event.y)

        # Perform OCR immediately after selection
        self.perform_ocr()

    def reset_selection(self):
        self.selection_start_x = None
        self.selection_start_y = None
        self.selection_end_x = None
        self.selection_end_y = None
        if self.selection_rectangle:
            self.image_canvas.delete(self.selection_rectangle)
            self.selection_rectangle = None

    def enhance_image(self, image):
        enhanced_image = image.convert('L')
        enhancer = ImageEnhance.Contrast(enhanced_image)
        enhanced_image = enhancer.enhance(2)
        enhancer = ImageEnhance.Sharpness(enhanced_image)
        enhanced_image = enhancer.enhance(2)
        return enhanced_image

    def open_tag_editor(self):
        if self.tag_window and tk.Toplevel.winfo_exists(self.tag_window):
            self.tag_window.focus()
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

        self.tag_text.bind("<KeyRelease>", self.auto_save_tags)

        self.load_tags_into_text()

        self.tag_window.protocol("WM_DELETE_WINDOW", self.on_tag_window_close)

    def load_tags_into_text(self):
        self.tag_text.delete("1.0", tk.END)
        self.tag_text.insert("1.0", "\n".join(self.current_tags))

    def auto_save_tags(self, event=None):
        # Get the folder name from the listbox, not the full path
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            return

        selected_folder_name = self.folder_listbox.get(selected_folder_index[0])

        # Find the full folder path based on the selected name
        full_folder_path = None
        for base_dir in self.BASE_DIRS:
            if os.path.isabs(base_dir):
                full_base_dir = base_dir
            else:
                full_base_dir = os.path.abspath(base_dir)

            # Construct the potential full path
            potential_path = os.path.join(full_base_dir, selected_folder_name)

            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                full_folder_path = potential_path
                break

        if not full_folder_path:
            print(f"Error: Could not find full path for folder name {selected_folder_name}")
            return
        tags_file_path = os.path.join(full_folder_path, "tags.txt")

        if self.tag_window and tk.Toplevel.winfo_exists(self.tag_window):
            tags = self.tag_text.get("1.0", tk.END).strip()
        else:
            return

        try:
            with open(tags_file_path, "w") as f:
                f.write(tags)
            self.current_tags = [tag.strip() for tag in tags.splitlines() if tag.strip()]
        except Exception as e:
            print(f"Error saving tags automatically: {e}")

    def load_tags(self):
        # Get the folder name from the listbox, not the full path
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            return

        selected_folder_name = self.folder_listbox.get(selected_folder_index[0])

        # Find the full folder path based on the selected name
        full_folder_path = None
        for base_dir in self.BASE_DIRS:
            if os.path.isabs(base_dir):
                full_base_dir = base_dir
            else:
                full_base_dir = os.path.abspath(base_dir)

            # Construct the potential full path
            potential_path = os.path.join(full_base_dir, selected_folder_name)

            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                full_folder_path = potential_path
                break

        if not full_folder_path:
            print(f"Error: Could not find full path for folder name {selected_folder_name}")
            return
        tags_file_path = os.path.join(full_folder_path, "tags.txt")

        self.current_tags = []
        if os.path.exists(tags_file_path):
            try:
                with open(tags_file_path, "r") as f:
                    tags = f.read().strip()
                    self.current_tags = [tag.strip() for tag in tags.splitlines() if tag.strip()]
            except Exception as e:
                print(f"Error loading tags: {e}")

        if self.tag_window and tk.Toplevel.winfo_exists(self.tag_window):
            self.load_tags_into_text()

    def on_tag_window_close(self):
        self.tag_window.destroy()
        self.tag_window = None

    def on_folder_select(self, event=None):
        self.load_tags()
        self.load_notes()

    def open_ocr_popup(self, init_call=False):
        if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
            self.ocr_window.focus()
            return

        self.ocr_window = Toplevel(self.root)
        self.ocr_window.title("Extracted Text (OCR)")
        self.ocr_window.geometry("600x400")
        self.ocr_window.attributes('-topmost', True)  # stay on top

        self.ocr_text_widget = Text(self.ocr_window, bg='white', fg='black', font=("Arial", 12))
        self.ocr_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.ocr_scrollbar = Scrollbar(self.ocr_window, orient=tk.VERTICAL)
        self.ocr_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ocr_text_widget.config(yscrollcommand=self.ocr_scrollbar.set)
        self.ocr_scrollbar.config(command=self.ocr_text_widget.yview)

        # No longer automatically performing OCR here.  Rely on selection.
        # self.perform_ocr()

        # set this to true if we don't need to close it
        if not init_call:
            self.ocr_window.protocol("WM_DELETE_WINDOW", self.on_ocr_window_close)

    def perform_ocr(self):
        if not self.original_image:
            if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
                self.ocr_text_widget.delete("1.0", tk.END)
            return

        # Ensure there is a valid selection
        if not self.selection_start_x or not self.selection_start_y or not self.selection_end_x or not self.selection_end_y:
            if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
                self.ocr_text_widget.delete("1.0", tk.END)
            return

        x0 = min(self.selection_start_x, self.selection_end_x)
        y0 = min(self.selection_start_y, self.selection_end_y)
        x1 = max(self.selection_start_x, self.selection_end_x)
        y1 = max(self.selection_start_y, self.selection_end_y)
        try:
            # Get the absolute coordinates of the image canvas on the screen
            x_root = self.root.winfo_rootx() + self.image_canvas.winfo_x()
            y_root = self.root.winfo_rooty() + self.image_canvas.winfo_y()

            # Get canvas offset in image
            x_offset = (self.image_canvas.winfo_width() - self.original_image.width * self.zoom_level) // 2 + self.image_x
            y_offset = (self.image_canvas.winfo_height() - self.original_image.height * self.zoom_level) // 2 + self.image_y

            # Scale rectangle coordinates
            x0 = (x0 - x_offset) / self.zoom_level
            y0 =(y0 - y_offset) / self.zoom_level
            x1 = (x1 - x_offset) / self.zoom_level
            y1 = (y1 - y_offset) / self.zoom_level

            # Ensure coordinates within image bounds
            x0 = max(0, x0)
            y0 = max(0, y0)
            x1 = min(self.original_image.width, x1)
            y1 = min(self.original_image.height, y1)

            # Crop the image
            cropped_image = self.original_image.crop((x0, y0, x1, y1))

            enhanced_image = self.enhance_image(cropped_image)

            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            text = pytesseract.image_to_string(enhanced_image)

            # Update OCR window
            if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
                self.ocr_text_widget.delete("1.0", tk.END)
                self.ocr_text_widget.insert("1.0", text)

        except Exception as e:
            print(f"OCR Error: {e}")
            if self.ocr_window and tk.Toplevel.winfo_exists(self.ocr_window):
                self.ocr_text_widget.delete("1.0", tk.END)

    def on_ocr_window_close(self):
        if self.ocr_window:
            self.ocr_window.destroy()
            self.ocr_window = None

    def open_notes_editor(self):
        if self.notes_window and tk.Toplevel.winfo_exists(self.notes_window):
            self.notes_window.focus()
            return

        self.notes_window = Toplevel(self.root)
        self.notes_window.title("Edit Notes")
        self.notes_window.geometry("400x300")
        self.notes_window.attributes('-topmost', True)

        self.notes_text = Text(self.notes_window, bg='white', fg='black', font=("Arial", 12))
        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.notes_scrollbar = Scrollbar(self.notes_window, orient=tk.VERTICAL)
        self.notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.notes_text.config(yscrollcommand=self.notes_scrollbar.set)
        self.notes_scrollbar.config(command=self.notes_text.yview)

        self.notes_text.bind("<KeyRelease>", self.auto_save_notes)

        self.load_notes_into_text()

        self.notes_window.protocol("WM_DELETE_WINDOW", self.on_notes_window_close)
        self.notes_window.bind("<Left>", self.prev_image)
        self.notes_window.bind("<Right>", self.next_image)
        self.notes_text.bind("<KeyRelease>", self.auto_save_notes)

        self.load_notes_into_text()

        self.notes_window.protocol("WM_DELETE_WINDOW", self.on_notes_window_close)
        self.notes_window.bind("<Left>", self.prev_image)
        self.notes_window.bind("<Right>", self.next_image)

    def load_notes_into_text(self):
        if not self.notes_window or not tk.Toplevel.winfo_exists(self.notes_window):
            return

        self.notes_text.delete("1.0", tk.END)
        folder_index = self.folder_listbox.curselection()
        if folder_index:
            # Get the folder name from the listbox, not the full path
            selected_folder_name = self.folder_listbox.get(folder_index[0])

            # Find the full folder path based on the selected name
            full_folder_path = None
            for base_dir in self.BASE_DIRS:
                if os.path.isabs(base_dir):
                    full_base_dir = base_dir
                else:
                    full_base_dir = os.path.abspath(base_dir)

                # Construct the potential full path
                potential_path = os.path.join(full_base_dir, selected_folder_name)

                if os.path.exists(potential_path) and os.path.isdir(potential_path):
                    full_folder_path = potential_path
                    break

            if not full_folder_path:
                print(f"Error: Could not find full path for folder name {selected_folder_name}")
                return

            notes_file_path = os.path.join(full_folder_path, "notes.txt")
            if os.path.exists(notes_file_path):
                try:
                    with open(notes_file_path, "r") as f:
                        notes = f.read()
                    self.notes_text.insert("1.0", notes)
                except Exception as e:
                    print(f"Error loading notes: {e}")

    def auto_save_notes(self, event=None):
         # Get the folder name from the listbox, not the full path
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            return

        selected_folder_name = self.folder_listbox.get(selected_folder_index[0])

        # Find the full folder path based on the selected name
        full_folder_path = None
        for base_dir in self.BASE_DIRS:
            if os.path.isabs(base_dir):
                full_base_dir = base_dir
            else:
                full_base_dir = os.path.abspath(base_dir)

            # Construct the potential full path
            potential_path = os.path.join(full_base_dir, selected_folder_name)

            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                full_folder_path = potential_path
                break

        if not full_folder_path:
            print(f"Error: Could not find full path for folder name {selected_folder_name}")
            return

        notes_file_path = os.path.join(full_folder_path, "notes.txt")

        if self.notes_window and tk.Toplevel.winfo_exists(self.notes_window):
            notes = self.notes_text.get("1.0", tk.END).strip()
        else:
            return

        try:
            with open(notes_file_path, "w") as f:
                f.write(notes)
        except Exception as e:
            print(f"Error saving notes automatically: {e}")

    def load_notes(self):
        folder_index = self.folder_listbox.curselection()
        if folder_index:
            # Get the folder name from the listbox, not the full path
            selected_folder_name = self.folder_listbox.get(folder_index[0])

            # Find the full folder path based on the selected name
            full_folder_path = None
            for base_dir in self.BASE_DIRS:
                if os.path.isabs(base_dir):
                    full_base_dir = base_dir
                else:
                    full_base_dir = os.path.abspath(base_dir)

                # Construct the potential full path
                potential_path = os.path.join(full_base_dir, selected_folder_name)

                if os.path.exists(potential_path) and os.path.isdir(potential_path):
                    full_folder_path = potential_path
                    break

            if not full_folder_path:
                print(f"Error: Could not find full path for folder name {selected_folder_name}")
                return

            notes_file_path = os.path.join(full_folder_path, "notes.txt")

            if os.path.exists(notes_file_path):
                try:
                    with open(notes_file_path, "r") as f:
                        notes = f.read().strip()
                except Exception as e:
                    print(f"Error loading notes: {e}")

            if self.notes_window and tk.Toplevel.winfo_exists(self.notes_window):
                self.load_notes_into_text()

    def on_notes_window_close(self):
        self.notes_window.destroy()
        self.notes_window = None

    def load_gallery_images(self, folder_path):
        try:
            self.gallery_images = sorted([f for f in os.listdir(folder_path) if
                                           f.lower().endswith(('png', 'jpg', 'jpeg'))], key=natural_sort_key)
        except Exception as e:
            print(f"Error loading gallery images: {e}")
            self.gallery_images = []

    def toggle_gallery(self):
        if self.gallery_window and tk.Toplevel.winfo_exists(self.gallery_window):
            self.gallery_window.destroy()
            self.gallery_window = None
            self.show_image()
        else:
            self.open_gallery()

    def open_gallery(self):
        if self.gallery_window and tk.Toplevel.winfo_exists(self.gallery_window):
            self.gallery_window.focus()
            return

        if not self.gallery_images:
            # messagebox.showinfo("Info","No images in gallery!") # display
            return

        self.gallery_window = Toplevel(self.root)
        self.gallery_window.title("Image Gallery")

        self.gallery_canvas = Canvas(self.gallery_window, bg=self.bg_color)
        self.gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.gallery_scrollbar_y = Scrollbar(self.gallery_window, orient=tk.VERTICAL,
                                                command=self.gallery_canvas.yview)
        self.gallery_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.gallery_canvas.configure(yscrollcommand=self.gallery_scrollbar_y.set)
        self.gallery_canvas.bind("<Configure>", self.configure_gallery_canvas)

        self.gallery_frame = Frame(self.gallery_canvas, bg=self.bg_color)
        self.gallery_canvas.create_window((0, 0), window=self.gallery_frame, anchor="nw")

        self.populate_gallery()

        self.gallery_window.protocol("WM_DELETE_WINDOW", self.on_gallery_window_close)

        self.gallery_canvas.bind("<MouseWheel>", self.scroll_gallery)
        self.gallery_canvas.bind("<Button-4>", self.scroll_gallery)
        self.gallery_canvas.bind("<Button-5>", self.scroll_gallery)

    def scroll_gallery(self, event):
        if event.num == 4 or event.delta > 0:
            self.gallery_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.gallery_canvas.yview_scroll(1, "units")
        else:
            self.gallery_canvas.yview_scroll(int(-1 * (event.delta / 120)),
                                             "units")

    def configure_gallery_canvas(self, event):
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))

    def populate_gallery(self):
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        num_columns = 4
        row = 0
        col = 0

        for i, image_name in enumerate(self.gallery_images):
            # Get the folder name from the listbox, not the full path
            selected_folder_name = self.folder_listbox.get(self.folder_listbox.curselection()[0])

            # Find the full folder path based on the selected name
            full_folder_path = None
            for base_dir in self.BASE_DIRS:
                if os.path.isabs(base_dir):
                    full_base_dir = base_dir
                else:
                    full_base_dir = os.path.abspath(base_dir)

                # Construct the potential full path
                potential_path = os.path.join(full_base_dir, selected_folder_name)

                if os.path.exists(potential_path) and os.path.isdir(potential_path):
                    full_folder_path = potential_path
                    break

            if not full_folder_path:
                print(f"Error: Could not find full path for folder name {selected_folder_name}")
                return

            try:
                image_path = os.path.join(full_folder_path, image_name)
                img = Image.open(image_path)
                img.thumbnail(self.thumbnail_size)
                photo = ImageTk.PhotoImage(img)

                button = Button(self.gallery_frame, image=photo, borderwidth=0,
                                command=lambda index=i: self.on_gallery_image_select_index(index))
                button.image = photo
                button.grid(row=row, column=col, padx=5, pady=5)
                col += 1
                if col >= num_columns:
                    col = 0
                    row += 1
            except Exception as e:
                print(f"Error loading thumbnail: {e}")

    def on_gallery_image_select_index(self, index):
        try:
            self.gallery_index = index

            # Get the folder name from the listbox, not the full path
            selected_folder_name = self.folder_listbox.get(self.folder_listbox.curselection()[0])

            # Find the full folder path based on the selected name
            full_folder_path = None
            for base_dir in self.BASE_DIRS:
                if os.path.isabs(base_dir):
                    full_base_dir = base_dir
                else:
                    full_base_dir = os.path.abspath(base_dir)

                # Construct the potential full path
                potential_path = os.path.join(full_base_dir, selected_folder_name)

                if os.path.exists(potential_path) and os.path.isdir(potential_path):
                    full_folder_path = potential_path
                    break

            if not full_folder_path:
                print(f"Error: Could not find full path for folder name {selected_folder_name}")
                return

            image_path = os.path.join(full_folder_path, self.gallery_images[self.gallery_index])
            self.current_index = self.image_paths.index(image_path)
            self.show_image()
            self.load_tags()
            self.load_notes()
            self.toggle_gallery()
        except Exception as e:
            print(f"Error gallery image selection: {e}")

    def on_gallery_image_select(self, event):
        selected_index = self.gallery_listbox.curselection()
        if selected_index:
            self.gallery_index = selected_index[0]
            self.current_index = self.image_paths.index(
                os.path.join(os.path.dirname(self.image_paths[0]), self.gallery_images[self.gallery_index]))
            self.show_image()
            self.load_tags()
            self.load_notes()
            self.toggle_gallery()

    def on_gallery_window_close(self):
        self.gallery_window.destroy()
        self.gallery_window = None
        self.show_image()

    def open_in_explorer(self):
         # Get the folder name from the listbox, not the full path
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            # messagebox.showinfo("Info", "No folder selected.")
            return

        selected_folder_name = self.folder_listbox.get(selected_folder_index[0])

        # Find the full folder path based on the selected name
        full_folder_path = None
        for base_dir in self.BASE_DIRS:
            if os.path.isabs(base_dir):
                full_base_dir = base_dir
            else:
                full_base_dir = os.path.abspath(base_dir)

            # Construct the potential full path
            potential_path = os.path.join(full_base_dir, selected_folder_name)

            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                full_folder_path = potential_path
                break

        if not full_folder_path:
            print(f"Error: Could not find full path for folder name {selected_folder_name}")
            return

        if os.path.exists(full_folder_path):
            try:
                subprocess.Popen(['explorer', full_folder_path])
            except Exception as e:
                # messagebox.showerror("Error", f"Could not open folder: {e}")
                pass
        else:
            # messagebox.showerror("Error", "Folder does not exist.")
            pass

    def create_new_folder(self):
        new_folder_name = self.new_folder_entry.get().strip()
        if not new_folder_name:
            messagebox.showinfo("Info", "Please enter a folder name.")
            return

        checked_count = sum(var.get() for var in self.checkbox_vars.values())

        if checked_count == 0:
            messagebox.showinfo("Info", "Please select a base directory by checking one of the checkboxes.")
            return
        elif checked_count > 1:
            messagebox.showinfo("Info", "You should select only one checkbox to create a folder.")
            return

        selected_base_dir = None
        for dir_name, var in self.checkbox_vars.items():
            if var.get():
                for base_dir in self.BASE_DIRS:
                    if os.path.basename(base_dir) == dir_name:
                        selected_base_dir = base_dir
                        break
                if selected_base_dir:
                    break

        if not selected_base_dir:
            messagebox.showerror("Error", "Could not determine the selected base directory.")
            return

        # Check if selected_base_dir is absolute or relative
        if os.path.isabs(selected_base_dir):
            full_base_dir = selected_base_dir
        else:
            full_base_dir = os.path.abspath(selected_base_dir)  # Convert to absolute path

        new_folder_path = os.path.join(full_base_dir, new_folder_name)

        try:
            os.makedirs(new_folder_path, exist_ok=False)
            messagebox.showinfo("Success",
                                f"Folder '{new_folder_name}' created successfully in '{os.path.basename(full_base_dir)}'.")
            self.load_folders()
            self.new_folder_entry.delete(0, tk.END)
            self.move_screenshots(new_folder_path)
        except FileExistsError:
            messagebox.showerror("Error", "Folder with that name already exists.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not create folder: {e}")

    def move_screenshots(self, dest_folder):
        if not os.path.exists(self.SCREENSHOTS_DIR):
            messagebox.showinfo("Info", "Screenshots directory does not exist.")
            return

        image_files = [f for f in os.listdir(self.SCREENSHOTS_DIR) if
                       f.lower().endswith(('png', 'jpg', 'jpeg'))]

        if not image_files:
            messagebox.showinfo("Info", "No screenshots to move.")
            return

        try:
            for image_file in image_files:
                source_path = os.path.join(self.SCREENSHOTS_DIR, image_file)
                dest_path = os.path.join(dest_folder, image_file)
                shutil.move(source_path, dest_path)
            messagebox.showinfo("Success", f"Moved {len(image_files)} screenshots to '{dest_folder}'.")
            self.load_folders()
        except Exception as e:
            messagebox.showerror("Error", f"Error moving screenshots: {e}")

    def copy_path_to_clipboard(self):
         # Get the folder name from the listbox, not the full path
        selected_folder_index = self.folder_listbox.curselection()
        if not selected_folder_index:
            messagebox.showinfo("Info", "No folder selected.")
            return

        selected_folder_name = self.folder_listbox.get(selected_folder_index[0])

        # Find the full folder path based on the selected name
        full_folder_path = None
        for base_dir in self.BASE_DIRS:
            if os.path.isabs(base_dir):
                full_base_dir = base_dir
            else:
                full_base_dir = os.path.abspath(base_dir)

            # Construct the potential full path
            potential_path = os.path.join(full_base_dir, selected_folder_name)

            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                full_folder_path = potential_path
                break

        if not full_folder_path:
            print(f"Error: Could not find full path for folder name {selected_folder_name}")
            return

        if os.path.exists(full_folder_path):
            try:
                pyperclip.copy(full_folder_path)
                messagebox.showinfo("Success", "Folder path copied to clipboard.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not copy path to clipboard: {e}")
        else:
            messagebox.showerror("Error", "Folder does not exist.")

    def resize_image(self, event=None):
        if self.original_image:
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()

            img_width, img_height = self.original_image.size

            # Calculate aspect ratios
            canvas_ratio = canvas_width / canvas_height
            img_ratio = img_width / img_height

            if canvas_ratio > img_ratio:
                # Canvas is wider than the image, fit to height
                new_height = canvas_height
                new_width = int(new_height * img_ratio)
            else:
                # Canvas is taller than the image, fit to width
                new_width = canvas_width
                new_height = int(new_width * (1 / img_ratio))

            resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
            self.current_image = ImageTk.PhotoImage(resized_image)

            if self.canvas_image_id:
                self.image_canvas.delete(self.canvas_image_id)

            x_offset = (canvas_width - new_width) // 2 + self.image_x
            y_offset = (canvas_height - new_height) // 2 + self.image_y

            self.canvas_image_id = self.image_canvas.create_image(
                x_offset, y_offset,
                anchor=tk.NW,
                image=self.current_image
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGallery(root)
    root.mainloop()