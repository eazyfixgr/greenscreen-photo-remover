import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
from pathlib import Path
import threading


class GreenScreenRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Green Screen Remover")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        self.input_folder = ""
        self.output_folder = ""
        self.threshold = 100
        self.remove_watermark = tk.BooleanVar(value=False)

        # Preview state
        self.image_files = []
        self.current_image_index = 0
        self.current_processed_img = None
        self.current_display_img = None

        # Watermark selection state (percentages of image)
        self.watermark_region = {
            'x1': 0.75,  # 75% from left
            'y1': 0.75,  # 75% from top
            'x2': 1.0,   # 100% from left
            'y2': 1.0    # 100% from top
        }

        # Canvas drag state
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.resize_handle = None

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Label(
            self.root,
            text="🎨 Green Screen Remover & Auto Crop",
            font=("Arial", 16, "bold"),
            bg="#4CAF50",
            fg="white",
            pady=10
        )
        header.pack(fill=tk.X)

        # Main container (horizontal layout)
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left panel (controls)
        left_panel = ttk.Frame(main_container, padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        # Right panel (preview)
        right_panel = ttk.Frame(main_container, padding="10")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # === LEFT PANEL CONTROLS ===

        # Input folder selection
        input_frame = ttk.LabelFrame(left_panel, text="Φάκελος Εισόδου", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.input_label = ttk.Label(input_frame, text="Δεν έχει επιλεγεί", foreground="gray", wraplength=350)
        self.input_label.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(input_frame, text="Επιλογή Φακέλου", command=self.select_input_folder).pack(fill=tk.X)

        # Output folder selection
        output_frame = ttk.LabelFrame(left_panel, text="Φάκελος Εξόδου", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))

        self.output_label = ttk.Label(output_frame, text="Δεν έχει επιλεγεί", foreground="gray", wraplength=350)
        self.output_label.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(output_frame, text="Επιλογή Φακέλου", command=self.select_output_folder).pack(fill=tk.X)

        # Threshold slider
        threshold_frame = ttk.LabelFrame(left_panel, text="Ευαισθησία Green Screen", padding="10")
        threshold_frame.pack(fill=tk.X, pady=(0, 10))

        self.threshold_value = tk.IntVar(value=100)
        threshold_slider = ttk.Scale(
            threshold_frame,
            from_=50,
            to=150,
            orient=tk.HORIZONTAL,
            variable=self.threshold_value,
            command=self.on_threshold_change
        )
        threshold_slider.pack(fill=tk.X, pady=(0, 5))

        self.threshold_label = ttk.Label(threshold_frame, text=f"Τιμή: {self.threshold_value.get()}")
        self.threshold_label.pack()

        # Watermark removal checkbox
        watermark_frame = ttk.LabelFrame(left_panel, text="Επιλογές", padding="10")
        watermark_frame.pack(fill=tk.X, pady=(0, 10))

        watermark_check = ttk.Checkbutton(
            watermark_frame,
            text="Watermark Removal",
            variable=self.remove_watermark,
            command=self.on_watermark_toggle
        )
        watermark_check.pack(anchor=tk.W)

        info_label = ttk.Label(
            watermark_frame,
            text="Σύρε το κόκκινο κουτί στην προεπισκόπηση\nγια να επιλέξεις την περιοχή του watermark",
            font=("Arial", 8),
            foreground="gray"
        )
        info_label.pack(anchor=tk.W, pady=(5, 0))

        # Process button
        self.process_button = ttk.Button(
            left_panel,
            text="⚡ Επεξεργασία Όλων",
            command=self.process_all_images,
            state=tk.DISABLED
        )
        self.process_button.pack(pady=15, fill=tk.X, ipady=10)

        # Progress bar
        self.progress = ttk.Progressbar(left_panel, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # Status label
        self.status_label = ttk.Label(left_panel, text="Έτοιμο", foreground="blue", wraplength=350)
        self.status_label.pack()

        # === RIGHT PANEL PREVIEW ===

        preview_header = ttk.Label(right_panel, text="Προεπισκόπηση", font=("Arial", 12, "bold"))
        preview_header.pack(pady=(0, 10))

        # Preview canvas container
        preview_canvas_frame = ttk.Frame(right_panel, relief=tk.SUNKEN, borderwidth=2)
        preview_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.preview_canvas = tk.Canvas(
            preview_canvas_frame,
            bg="#f0f0f0",
            highlightthickness=0
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # Bind canvas events for watermark selection
        self.preview_canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.preview_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Navigation frame (with counter in the middle)
        nav_frame = ttk.Frame(right_panel)
        nav_frame.pack(fill=tk.X)

        self.prev_button = ttk.Button(nav_frame, text="← Προηγούμενη", command=self.prev_image, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 10))

        self.counter_label = ttk.Label(nav_frame, text="0/0", font=("Arial", 11, "bold"))
        self.counter_label.pack(side=tk.LEFT, expand=True)

        self.next_button = ttk.Button(nav_frame, text="Επόμενη →", command=self.next_image, state=tk.DISABLED)
        self.next_button.pack(side=tk.RIGHT, padx=(10, 0))

        # Image filename below navigation
        self.filename_label = ttk.Label(right_panel, text="", font=("Arial", 9), foreground="gray")
        self.filename_label.pack(pady=(5, 0))

    def select_input_folder(self):
        folder = filedialog.askdirectory(title="Επιλέξτε φάκελο με εικόνες")
        if folder:
            self.input_folder = folder
            self.input_label.config(text=folder, foreground="black")
            self.load_images()
            self.check_ready()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Επιλέξτε φάκελο εξόδου")
        if folder:
            self.output_folder = folder
            self.output_label.config(text=folder, foreground="black")
            self.check_ready()

    def load_images(self):
        """Load all images from input folder"""
        if not self.input_folder:
            return

        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        self.image_files = [
            f for f in os.listdir(self.input_folder)
            if f.lower().endswith(image_extensions)
        ]

        self.image_files.sort()

        if self.image_files:
            self.current_image_index = 0
            self.update_preview()
            self.prev_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
        else:
            self.preview_canvas.delete("all")
            self.counter_label.config(text="0/0")
            self.filename_label.config(text="")

    def prev_image(self):
        if self.image_files and self.current_image_index > 0:
            self.current_image_index -= 1
            self.update_preview()

    def next_image(self):
        if self.image_files and self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.update_preview()

    def on_threshold_change(self, value):
        self.threshold_label.config(text=f"Τιμή: {int(float(value))}")
        self.update_preview()

    def on_watermark_toggle(self):
        self.update_preview()

    def update_preview(self):
        """Update the preview with current image and settings"""
        if not self.image_files:
            return

        filename = self.image_files[self.current_image_index]
        image_path = os.path.join(self.input_folder, filename)

        # Update counter and filename
        self.counter_label.config(text=f"{self.current_image_index + 1}/{len(self.image_files)}")
        self.filename_label.config(text=filename)

        try:
            # Process the image
            threshold = self.threshold_value.get()
            processed_img = self.remove_green_screen(
                image_path,
                threshold,
                self.remove_watermark.get()
            )

            self.current_processed_img = processed_img

            # Get canvas size
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            # If canvas not yet rendered, use default size
            if canvas_width <= 1:
                canvas_width = 500
                canvas_height = 500

            # Resize for preview to fit canvas
            display_img = processed_img.copy()
            display_img.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)

            self.current_display_img = display_img

            # Create a checkerboard background
            bg_img = self.create_checkerboard(display_img.width, display_img.height)
            bg_img.paste(display_img, (0, 0), display_img)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(bg_img)

            # Clear canvas and display image
            self.preview_canvas.delete("all")

            # Center the image
            x_offset = (canvas_width - display_img.width) // 2
            y_offset = (canvas_height - display_img.height) // 2

            self.preview_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=photo, tags="preview_image")
            self.preview_canvas.image = photo  # Keep reference
            self.preview_canvas.image_offset = (x_offset, y_offset)
            self.preview_canvas.image_size = (display_img.width, display_img.height)

            # Draw watermark selection box if enabled
            if self.remove_watermark.get():
                self.draw_watermark_box()

        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                250, 250,
                text=f"Σφάλμα: {str(e)}",
                fill="red",
                font=("Arial", 10)
            )
            print(f"Preview error: {e}")

    def draw_watermark_box(self):
        """Draw the watermark selection box on canvas"""
        if not hasattr(self.preview_canvas, 'image_size'):
            return

        x_offset, y_offset = self.preview_canvas.image_offset
        img_width, img_height = self.preview_canvas.image_size

        # Calculate box coordinates
        x1 = x_offset + int(img_width * self.watermark_region['x1'])
        y1 = y_offset + int(img_height * self.watermark_region['y1'])
        x2 = x_offset + int(img_width * self.watermark_region['x2'])
        y2 = y_offset + int(img_height * self.watermark_region['y2'])

        # Draw semi-transparent rectangle
        self.preview_canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="red",
            width=2,
            tags="watermark_box"
        )

        # Draw fill with transparency effect (using stipple)
        self.preview_canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="red",
            stipple="gray50",
            tags="watermark_box"
        )

        # Draw resize handle (bottom-right corner)
        handle_size = 8
        self.preview_canvas.create_rectangle(
            x2 - handle_size, y2 - handle_size, x2, y2,
            fill="white",
            outline="red",
            width=2,
            tags="resize_handle"
        )

    def on_canvas_click(self, event):
        """Handle canvas click for dragging watermark box"""
        if not self.remove_watermark.get():
            return

        if not hasattr(self.preview_canvas, 'image_size'):
            return

        # Check if clicking on resize handle
        items = self.preview_canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        for item in items:
            if "resize_handle" in self.preview_canvas.gettags(item):
                self.drag_data["item"] = "resize"
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                return

        # Check if clicking on watermark box
        for item in items:
            if "watermark_box" in self.preview_canvas.gettags(item):
                self.drag_data["item"] = "move"
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                return

        self.drag_data["item"] = None

    def on_canvas_drag(self, event):
        """Handle dragging of watermark box"""
        if self.drag_data["item"] is None:
            return

        if not hasattr(self.preview_canvas, 'image_size'):
            return

        x_offset, y_offset = self.preview_canvas.image_offset
        img_width, img_height = self.preview_canvas.image_size

        # Calculate delta
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]

        if self.drag_data["item"] == "move":
            # Move the box
            dx_percent = dx / img_width
            dy_percent = dy / img_height

            # Update region
            new_x1 = max(0, min(1, self.watermark_region['x1'] + dx_percent))
            new_y1 = max(0, min(1, self.watermark_region['y1'] + dy_percent))
            new_x2 = max(0, min(1, self.watermark_region['x2'] + dx_percent))
            new_y2 = max(0, min(1, self.watermark_region['y2'] + dy_percent))

            # Ensure box stays within bounds
            width = new_x2 - new_x1
            height = new_y2 - new_y1

            if new_x2 > 1:
                new_x2 = 1
                new_x1 = 1 - width
            if new_y2 > 1:
                new_y2 = 1
                new_y1 = 1 - height
            if new_x1 < 0:
                new_x1 = 0
                new_x2 = width
            if new_y1 < 0:
                new_y1 = 0
                new_y2 = height

            self.watermark_region['x1'] = new_x1
            self.watermark_region['y1'] = new_y1
            self.watermark_region['x2'] = new_x2
            self.watermark_region['y2'] = new_y2

        elif self.drag_data["item"] == "resize":
            # Resize the box
            dx_percent = dx / img_width
            dy_percent = dy / img_height

            new_x2 = max(self.watermark_region['x1'] + 0.05, min(1, self.watermark_region['x2'] + dx_percent))
            new_y2 = max(self.watermark_region['y1'] + 0.05, min(1, self.watermark_region['y2'] + dy_percent))

            self.watermark_region['x2'] = new_x2
            self.watermark_region['y2'] = new_y2

        # Update drag position
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

        # Redraw
        self.preview_canvas.delete("watermark_box", "resize_handle")
        self.draw_watermark_box()

    def on_canvas_release(self, event):
        """Handle release of mouse button"""
        self.drag_data["item"] = None

    def create_checkerboard(self, width, height, square_size=10):
        """Create a checkerboard pattern to show transparency"""
        img = Image.new('RGB', (width, height), 'white')
        pixels = img.load()

        for i in range(width):
            for j in range(height):
                if (i // square_size + j // square_size) % 2 == 0:
                    pixels[i, j] = (200, 200, 200)
                else:
                    pixels[i, j] = (255, 255, 255)

        return img

    def remove_green_screen(self, image_path, threshold, remove_watermark=False):
        """Remove green screen and optionally remove watermark"""
        img = Image.open(image_path).convert("RGBA")
        width, height = img.size
        data = img.getdata()

        new_data = []
        for idx, item in enumerate(data):
            r, g, b, a = item
            x = idx % width
            y = idx // width

            # Remove watermark based on user-defined region
            if remove_watermark:
                x_percent = x / width
                y_percent = y / height

                if (self.watermark_region['x1'] <= x_percent <= self.watermark_region['x2'] and
                    self.watermark_region['y1'] <= y_percent <= self.watermark_region['y2']):
                    new_data.append((255, 255, 255, 0))
                    continue

            # Check if pixel is green (high G value, low R and B)
            if g > r + threshold and g > b + threshold:
                # Make it transparent
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        img.putdata(new_data)

        # Auto-crop: find bounding box of non-transparent pixels
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

        return img

    def check_ready(self):
        if self.input_folder and self.output_folder and self.image_files:
            self.process_button.config(state=tk.NORMAL)
        else:
            self.process_button.config(state=tk.DISABLED)

    def process_all_images(self):
        if not self.input_folder or not self.output_folder:
            messagebox.showerror("Σφάλμα", "Παρακαλώ επιλέξτε φακέλους εισόδου και εξόδου")
            return

        if not self.image_files:
            messagebox.showwarning("Προειδοποίηση", "Δεν βρέθηκαν εικόνες")
            return

        # Disable buttons during processing
        self.process_button.config(state=tk.DISABLED)
        self.prev_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)

        # Run processing in a separate thread
        thread = threading.Thread(target=self._process_images_thread)
        thread.start()

    def _process_images_thread(self):
        try:
            total_files = len(self.image_files)
            threshold = self.threshold_value.get()
            remove_wm = self.remove_watermark.get()

            for idx, filename in enumerate(self.image_files):
                # Update status
                self.root.after(0, lambda f=filename: self.status_label.config(
                    text=f"Επεξεργασία: {f}",
                    foreground="orange"
                ))

                # Update progress
                progress_value = ((idx + 1) / total_files) * 100
                self.root.after(0, lambda v=progress_value: self.progress.config(value=v))

                # Process image
                input_path = os.path.join(self.input_folder, filename)
                output_filename = Path(filename).stem + "_no_bg.png"
                output_path = os.path.join(self.output_folder, output_filename)

                try:
                    processed_img = self.remove_green_screen(input_path, threshold, remove_wm)
                    processed_img.save(output_path, "PNG")

                except Exception as e:
                    print(f"Error processing {filename}: {e}")

            # Complete
            self.root.after(0, lambda: self.progress.config(value=100))
            self.root.after(0, lambda: self.status_label.config(
                text=f"✓ Ολοκληρώθηκε! Επεξεργάστηκαν {total_files} εικόνες",
                foreground="green"
            ))
            self.root.after(0, lambda: messagebox.showinfo(
                "Επιτυχία",
                f"Επεξεργάστηκαν με επιτυχία {total_files} εικόνες!"
            ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Σφάλμα",
                f"Προέκυψε σφάλμα: {str(e)}"
            ))

        finally:
            self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.prev_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.next_button.config(state=tk.NORMAL))


def main():
    root = tk.Tk()
    app = GreenScreenRemover(root)
    root.mainloop()


if __name__ == "__main__":
    main()
