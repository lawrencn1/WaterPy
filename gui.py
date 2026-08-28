import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

# Import our upgraded watermarking engine
import watermark_engine

# Set appearance mode and color theme
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

class WatermarkApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("WaterFile")
        self.geometry("1200x700")
        self.minimum_size = (550, 600)
        self.minsize(550, 600)

        # State variables
        self.input_file_path = None
        self.file_type = None  # "pdf" or "image"
        self.preview_base_image = None  # Original resized image (unwatermarked)
        self.last_width = 0
        self.last_height = 0
        self.is_processing = False

        # Configure layout grid (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Left panel: fixed width controls
        self.grid_columnconfigure(1, weight=1)  # Right panel: dynamic preview

        self.setup_left_panel()
        self.setup_right_panel()

        # Bind window resize to dynamically scale the preview
        self.preview_container.bind("<Configure>", self.on_preview_resize)

    def setup_left_panel(self):
        """Creates the controls side of the UI."""
        # Create a container for the entire left side
        self.left_container = ctk.CTkFrame(self, width=450, corner_radius=0)
        self.left_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.left_container.grid_rowconfigure(0, weight=1)
        self.left_container.grid_rowconfigure(1, weight=0)
        self.left_container.grid_columnconfigure(0, weight=1)

        # Scrollable frame for controls (inside left container)
        self.left_panel = ctk.CTkScrollableFrame(self.left_container, width=450, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.left_panel.grid_columnconfigure(0, weight=1)

        # ---- HEADER ----
        # Header removed as per user request



        # ---- SECTION 1: FILE SELECTION ----
        self.file_frame = ctk.CTkFrame(self.left_panel)
        self.file_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        self.file_frame.grid_columnconfigure(0, weight=1)

        self.file_title = ctk.CTkLabel(
            self.file_frame, 
            text="Select Document", 
            font=ctk.CTkFont(weight="bold")
        )
        self.file_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.select_btn = ctk.CTkButton(
            self.file_frame, 
            text="Open PDF or Image", 
            command=self.select_file,
            height=35
        )
        self.select_btn.grid(row=1, column=0, sticky="ew", padx=15, pady=10)

        self.file_info_label = ctk.CTkLabel(
            self.file_frame, 
            text="No file loaded\nSupports PDF, PNG, JPG, JPEG", 
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.file_info_label.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 15))

        # ---- SECTION 2: WATERMARK TEXT ----
        self.watermark_frame = ctk.CTkFrame(self.left_panel)
        self.watermark_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=10)
        self.watermark_frame.grid_columnconfigure(0, weight=1)

        self.watermark_title = ctk.CTkLabel(
            self.watermark_frame, 
            text="Watermark Text", 
            font=ctk.CTkFont(weight="bold")
        )
        self.watermark_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.text_entry_var = tk.StringVar(value="Usage exclusif pour")
        self.text_entry_var.trace_add("write", lambda *args: self.update_preview())
        self.text_entry = ctk.CTkEntry(
            self.watermark_frame, 
            textvariable=self.text_entry_var,
            placeholder_text="Enter watermark text..."
        )
        self.text_entry.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))

        # ---- SECTION 3: STYLING OPTIONS ----
        self.options_frame = ctk.CTkFrame(self.left_panel)
        self.options_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=10)
        self.options_frame.grid_columnconfigure(0, weight=1)

        self.options_title = ctk.CTkLabel(
            self.options_frame, 
            text="Configuration", 
            font=ctk.CTkFont(weight="bold")
        )
        self.options_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        # Opacity Slider
        self.opacity_label = ctk.CTkLabel(self.options_frame, text="Opacity: 50%")
        self.opacity_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.opacity_slider = ctk.CTkSlider(
            self.options_frame, 
            from_=0.05, to=0.80, 
            number_of_steps=15,
            command=self.on_opacity_change
        )
        self.opacity_slider.set(0.50)  # Default to 50% opacity
        self.opacity_slider.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Rotation Angle Slider
        self.angle_label = ctk.CTkLabel(self.options_frame, text="Angle: 30°")
        self.angle_label.grid(row=3, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.angle_slider = ctk.CTkSlider(
            self.options_frame, 
            from_=-90, to=90, 
            number_of_steps=36,
            command=self.on_angle_change
        )
        self.angle_slider.set(30)
        self.angle_slider.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 10))

        # PDF Export DPI Settings
        self.dpi_label = ctk.CTkLabel(self.options_frame, text="PDF Quality (Rasterization DPI):")
        self.dpi_label.grid(row=5, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.dpi_menu = ctk.CTkSegmentedButton(
            self.options_frame,
            values=["200 DPI (Standard)", "250 DPI (High)", "300 DPI (Print)"],
            command=self.on_dpi_change
        )
        self.dpi_menu.set("200 DPI (Standard)")
        self.dpi_menu.grid(row=6, column=0, sticky="ew", padx=15, pady=(5, 15))

        # Wavy Text Checkbox
        self.wavy_var = ctk.BooleanVar(value=True)
        self.wavy_cb = ctk.CTkCheckBox(
            self.options_frame,
            text="Wavy/Curved Text (Sine Wave)",
            variable=self.wavy_var,
            command=self.update_preview,
            font=ctk.CTkFont(size=12)
        )
        self.wavy_cb.grid(row=7, column=0, sticky="w", padx=15, pady=5)

        # Variable Opacity Checkbox
        self.var_opacity_var = ctk.BooleanVar(value=True)
        self.var_opacity_cb = ctk.CTkCheckBox(
            self.options_frame,
            text="Variable Opacity & Colors",
            variable=self.var_opacity_var,
            command=self.update_preview,
            font=ctk.CTkFont(size=12)
        )
        self.var_opacity_cb.grid(row=8, column=0, sticky="w", padx=15, pady=5)

        # Shield Occurrence Slider
        self.shield_rate_label = ctk.CTkLabel(self.options_frame, text="Shield Occurrence: 40%", font=ctk.CTkFont(size=12))
        self.shield_rate_label.grid(row=9, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.shield_rate_slider = ctk.CTkSlider(
            self.options_frame,
            from_=0.0, to=1.0,
            number_of_steps=100,
            command=self.on_shield_rate_change
        )
        self.shield_rate_slider.set(0.40)  # Default: 40% of lines get shields
        self.shield_rate_slider.grid(row=10, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Static Noise Checkbox
        self.noise_grain_var = ctk.BooleanVar(value=True)
        self.noise_grain_cb = ctk.CTkCheckBox(
            self.options_frame,
            text="Faint Static Noise Overlay",
            variable=self.noise_grain_var,
            command=self.update_preview,
            font=ctk.CTkFont(size=12)
        )
        self.noise_grain_cb.grid(row=11, column=0, sticky="w", padx=15, pady=(5, 15))

        # ---- SECTION 4: ACTION / EXPORT ----
        self.action_frame = ctk.CTkFrame(self.left_container)
        self.action_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        self.action_frame.grid_columnconfigure(0, weight=1)

        self.action_title = ctk.CTkLabel(
            self.action_frame, 
            text="Export Secured File", 
            font=ctk.CTkFont(weight="bold")
        )
        self.action_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.save_btn = ctk.CTkButton(
            self.action_frame, 
            text="Save Secured File", 
            fg_color="#2da44e",  # Green color for safety/success
            hover_color="#2c974b",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            command=self.save_file,
            state="disabled"
        )
        self.save_btn.grid(row=1, column=0, sticky="ew", padx=15, pady=10)

        # Progress elements
        self.progress_bar = ctk.CTkProgressBar(self.action_frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 5))
        self.progress_bar.grid_remove()  # Hide initially

        self.status_label = ctk.CTkLabel(
            self.action_frame, 
            text="", 
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.status_label.grid_remove()

    def setup_right_panel(self):
        """Creates the preview side of the UI."""
        self.right_panel = ctk.CTkFrame(self, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.right_panel.grid_rowconfigure(0, weight=0)  # Title
        self.right_panel.grid_rowconfigure(1, weight=1)  # Preview box
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.preview_header = ctk.CTkLabel(
            self.right_panel, 
            text="Document Preview (First Page)", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.preview_header.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        # Preview Container
        self.preview_container = ctk.CTkFrame(self.right_panel, fg_color=("white", "#1e1e1e"), border_width=1, border_color=("gray75", "gray25"))
        self.preview_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.preview_container.grid_rowconfigure(0, weight=1)
        self.preview_container.grid_columnconfigure(0, weight=1)

        # Placeholder label when no document is loaded
        self.placeholder_label = ctk.CTkLabel(
            self.preview_container,
            text="No document loaded.\n\nClick 'Open PDF or Image' to load a file\nand view a secure, live preview.",
            justify="center",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.placeholder_label.grid(row=0, column=0, sticky="nsew")

        # Preview Display Widget (Label containing the CTkImage)
        self.preview_display = ctk.CTkLabel(self.preview_container, text="")
        # Keep hidden until a file is loaded
        self.preview_display.grid_remove()

    # ---- EVENT HANDLERS ----

    def on_opacity_change(self, val):
        self.opacity_label.configure(text=f"Opacity: {int(float(val) * 100)}%")
        self.update_preview()

    def on_angle_change(self, val):
        self.angle_label.configure(text=f"Angle: {int(float(val))}°")
        self.update_preview()

    def on_dpi_change(self, val):
        pass

    def on_shield_rate_change(self, val):
        self.shield_rate_label.configure(text=f"Shield Occurrence: {int(float(val) * 100)}%")
        self.update_preview()

    def get_selected_dpi(self) -> int:
        val = self.dpi_menu.get()
        if "300" in val:
            return 300
        elif "250" in val:
            return 250
        else:
            return 200

    def select_file(self):
        """Prompt user to open an image or PDF file."""
        file_types = [
            ("Supported Documents", "*.pdf *.png *.jpg *.jpeg *.PNG *.JPG *.JPEG"),
            ("PDF Files (*.pdf)", "*.pdf"),
            ("Image Files (*.png, *.jpg, *.jpeg)", "*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG"),
        ]
        
        path = filedialog.askopenfilename(title="Select Document", filetypes=file_types)
        if not path:
            return

        self.input_file_path = path
        ext = os.path.splitext(path.lower())[1]

        # Update file info card
        filename = os.path.basename(path)
        file_size_kb = os.path.getsize(path) / 1024
        
        if ext == ".pdf":
            self.file_type = "pdf"
            try:
                pages = watermark_engine.get_pdf_page_count(path)
                self.file_info_label.configure(
                    text=f"📄 {filename}\nType: PDF Document\nPages: {pages}\nSize: {file_size_kb:.1f} KB",
                    text_color=("black", "white")
                )
                self.dpi_label.grid()
                self.dpi_menu.grid()
            except Exception as e:
                messagebox.showerror("Error Reading PDF", f"Failed to load PDF file:\n{str(e)}")
                return
        else:
            self.file_type = "image"
            self.file_info_label.configure(
                text=f"🖼️ {filename}\nType: Image\nSize: {file_size_kb:.1f} KB",
                text_color=("black", "white")
            )
            # Hide DPI options for standard images
            self.dpi_label.grid_remove()
            self.dpi_menu.grid_remove()

        # Enable save button
        self.save_btn.configure(state="normal")
        self.load_preview_base_image()

    def load_preview_base_image(self):
        """
        Loads the unwatermarked first page of the file, resizes it to fit 
        a standard bounding box, and caches it to make live updating extremely fast.
        """
        if not self.input_file_path:
            return

        try:
            # Show a temporary rendering status
            self.placeholder_label.grid_remove()
            self.preview_display.grid()
            self.preview_display.configure(text="Rendering preview... Please wait.", image=None)
            self.update_idletasks()

            # Load the base image depending on file type
            if self.file_type == "pdf":
                # Render page 1 at 120 DPI for preview cache
                self.preview_base_image = watermark_engine.get_pdf_page_image(self.input_file_path, 0, dpi=120)
            else:
                self.preview_base_image = Image.open(self.input_file_path)
                # Handle EXIF orientation
                try:
                    from PIL import ImageOps
                    self.preview_base_image = ImageOps.exif_transpose(self.preview_base_image)
                except Exception:
                    pass

            self.update_preview()
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to generate document preview:\n{str(e)}")
            self.placeholder_label.grid()
            self.preview_display.grid_remove()

    def on_preview_resize(self, event):
        """Triggers preview update when the panel size changes, adapting page sizing."""
        if not self.preview_base_image:
            return
            
        # Add a deadband threshold to prevent feedback loops/lag
        if abs(event.width - self.last_width) > 15 or abs(event.height - self.last_height) > 15:
            self.last_width = event.width
            self.last_height = event.height
            self.update_preview()

    def update_preview(self):
        """Applies the current watermark parameters to the cached base image and displays it."""
        if not self.preview_base_image:
            return

        text = self.text_entry_var.get()
        opacity = self.opacity_slider.get()
        angle = self.angle_slider.get()
        wavy = self.wavy_var.get()
        var_opacity = self.var_opacity_var.get()
        noise_grain = self.noise_grain_var.get()
        shield_rate = self.shield_rate_slider.get()

        # Compute display boundaries based on current preview frame size
        # Subtract padding to keep the image centered nicely
        pad_x = 40
        pad_y = 40
        avail_w = max(100, self.preview_container.winfo_width() - pad_x)
        avail_h = max(100, self.preview_container.winfo_height() - pad_y)

        # 1. Scale the base image to fit preview frame dimensions
        orig_w, orig_h = self.preview_base_image.size
        scale = min(avail_w / orig_w, avail_h / orig_h)
        fit_w = int(orig_w * scale)
        fit_h = int(orig_h * scale)

        if fit_w <= 0 or fit_h <= 0:
            return

        # Resize the base image
        scaled_base = self.preview_base_image.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

        # 2. Apply the watermark to the scaled image
        watermarked_preview = watermark_engine.apply_watermark(
            scaled_base, text, opacity=opacity, angle=angle,
            wavy=wavy, var_opacity=var_opacity, noise_grain=noise_grain,
            shield_rate=shield_rate, hollow_text=False
        )

        # 3. Create CustomTkinter CTkImage to display
        ctk_img = ctk.CTkImage(
            light_image=watermarked_preview,
            dark_image=watermarked_preview,
            size=(fit_w, fit_h)
        )

        # Update preview label
        self.preview_display.configure(text="", image=ctk_img)
        self.preview_display.image = ctk_img  # Maintain strong reference to prevent GC

    def save_file(self):
        """Starts the file export process in a background thread."""
        if not self.input_file_path or self.is_processing:
            return

        # Prepare initial save path suggestion
        dir_name = os.path.dirname(self.input_file_path)
        base_name = os.path.basename(self.input_file_path)
        name_part, ext_part = os.path.splitext(base_name)
        suggested_name = f"{name_part}_filigrane{ext_part}"

        if self.file_type == "pdf":
            file_types = [("PDF Document (*.pdf)", "*.pdf")]
            default_ext = ".pdf"
        else:
            file_types = [
                ("PNG Image (*.png)", "*.png"),
                ("JPEG Image (*.jpg, *.jpeg)", "*.jpg *.jpeg"),
            ]
            default_ext = ext_part

        output_path = filedialog.asksaveasfilename(
            title="Save Secured File",
            initialdir=dir_name,
            initialfile=suggested_name,
            filetypes=file_types,
            defaultextension=default_ext
        )

        if not output_path:
            return

        # Update UI to processing state
        self.is_processing = True
        self.save_btn.configure(state="disabled")
        self.select_btn.configure(state="disabled")
        self.text_entry.configure(state="disabled")
        self.wavy_cb.configure(state="disabled")
        self.var_opacity_cb.configure(state="disabled")
        self.shield_rate_slider.configure(state="disabled")
        self.noise_grain_cb.configure(state="disabled")
        
        self.progress_bar.grid()
        self.progress_bar.set(0.0)
        self.status_label.grid()
        self.status_label.configure(text="Preparing document...")

        # Run process in a separate thread so GUI remains responsive
        text = self.text_entry_var.get()
        opacity = self.opacity_slider.get()
        angle = self.angle_slider.get()
        dpi = self.get_selected_dpi()
        wavy = self.wavy_var.get()
        var_opacity = self.var_opacity_var.get()
        noise_grain = self.noise_grain_var.get()
        shield_rate = self.shield_rate_slider.get()

        threading.Thread(
            target=self.export_worker,
            args=(output_path, text, opacity, angle, dpi, wavy, var_opacity, noise_grain, shield_rate, False),
            daemon=True
        ).start()

    def export_worker(self, output_path: str, text: str, opacity: float, angle: float, dpi: int, wavy: bool, var_opacity: bool, noise_grain: bool, shield_rate: float, hollow_text: bool):
        """Export worker function running on a background thread."""
        try:
            if self.file_type == "pdf":
                def progress_cb(current, total):
                    percent = current / total
                    self.after(0, lambda: self.progress_bar.set(percent))
                    self.after(0, lambda: self.status_label.configure(text=f"Securing & Flattening page {current} of {total}..."))
                
                watermark_engine.process_pdf_file(
                    self.input_file_path,
                    output_path,
                    text,
                    opacity=opacity,
                    angle=angle,
                    dpi=dpi,
                    wavy=wavy,
                    var_opacity=var_opacity,
                    noise_grain=noise_grain,
                    shield_rate=shield_rate,
                    hollow_text=hollow_text,
                    progress_callback=progress_cb
                )
            else:
                self.after(0, lambda: self.progress_bar.set(0.5))
                self.after(0, lambda: self.status_label.configure(text="Saving watermarked image..."))
                
                watermark_engine.process_image_file(
                    self.input_file_path,
                    output_path,
                    text,
                    opacity=opacity,
                    angle=angle,
                    wavy=wavy,
                    var_opacity=var_opacity,
                    noise_grain=noise_grain,
                    shield_rate=shield_rate,
                    hollow_text=hollow_text
                )
                self.after(0, lambda: self.progress_bar.set(1.0))

            # Success notification
            self.after(0, lambda: self.on_export_success(output_path))
        except Exception as e:
            self.after(0, lambda: self.on_export_failure(str(e)))

    def on_export_success(self, path):
        self.is_processing = False
        self.save_btn.configure(state="normal")
        self.select_btn.configure(state="normal")
        self.text_entry.configure(state="normal")
        self.wavy_cb.configure(state="normal")
        self.var_opacity_cb.configure(state="normal")
        self.shield_rate_slider.configure(state="normal")
        self.noise_grain_cb.configure(state="normal")
        self.progress_bar.grid_remove()
        
        self.status_label.grid()
        self.status_label.configure(text=f"✅ Export Complete: {os.path.basename(path)}", text_color="#2da44e")
        self.after(5000, self._hide_status)

    def _hide_status(self):
        self.status_label.grid_remove()
        self.status_label.configure(text_color="gray")

    def on_export_failure(self, error_msg):
        self.is_processing = False
        self.save_btn.configure(state="normal")
        self.select_btn.configure(state="normal")
        self.text_entry.configure(state="normal")
        self.wavy_cb.configure(state="normal")
        self.var_opacity_cb.configure(state="normal")
        self.shield_rate_slider.configure(state="normal")
        self.noise_grain_cb.configure(state="normal")
        self.progress_bar.grid_remove()
        self.status_label.grid_remove()
        
        messagebox.showerror(
            "Export Failed", 
            f"An error occurred during saving:\n{error_msg}"
        )

# Standard main block to allow running gui.py directly
if __name__ == "__main__":
    app = WatermarkApp()
    app.mainloop()
