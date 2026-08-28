import os
import io
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import fitz  # PyMuPDF

def get_font(font_size: int, bold: bool = True) -> ImageFont.ImageFont:
    """
    Safely load a font. Tries Arial Bold/DejaVuSans-Bold if bold is requested,
    otherwise standard Arial/DejaVuSans.
    """
    font_paths = []
    if bold:
        font_paths.extend([
            "arialbd.ttf",                                       # Windows Arial Bold
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS Arial Bold
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # Linux DejaVuSans Bold
            "DejaVuSans-Bold.ttf",
            "LiberationSans-Bold.ttf"
        ])
    
    font_paths.extend([
        "arial.ttf",                                         # Windows Arial
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",     # Linux DejaVuSans
        "/System/Library/Fonts/Supplemental/Arial.ttf",       # macOS Arial
        "Arial.ttf",
        "DejaVuSans.ttf"
    ])
    
    for path in font_paths:
        try:
            return ImageFont.truetype(path, font_size)
        except IOError:
            continue
    return ImageFont.load_default()

def add_noise(image: Image.Image, intensity: float = 0.05) -> Image.Image:
    """
    Applies Gaussian noise grain overlay to both RGB and RGBA images.
    Uses PIL's native C implementation for high performance (numpy-free).
    """
    orig_mode = image.mode
    if image.mode != "RGB" and image.mode != "RGBA":
        image = image.convert("RGB")
        orig_mode = "RGB"
    
    try:
        # Generate 8-bit noise image via native C function
        noise_img = Image.effect_noise(image.size, sigma=15)
        
        # Convert L-mode noise to RGB
        noise_rgb = Image.merge("RGB", (noise_img, noise_img, noise_img))
        
        # Blend the noise layer lightly over the original image
        blended = Image.blend(image.convert("RGB"), noise_rgb, alpha=intensity)
        
        if orig_mode == "RGBA":
            return blended.convert("RGBA")
        return blended
    except Exception:
        # Fallback to returning unmodified image
        return image

def draw_shield(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: tuple):
    """
    Draws a simple geometric shield shape outline at center (cx, cy).
    """
    s = size
    points = [
        (cx - s, cy - s),             # Top-left corner
        (cx + s, cy - s),             # Top-right corner
        (cx + s, cy),                 # Right edge midpoint
        (cx, cy + int(s * 1.35)),     # Bottom point
        (cx - s, cy)                  # Left edge midpoint
    ]
    draw.polygon(points, outline=color, width=2)

def generate_chaos_layer(
    width: int, 
    height: int, 
    text: str, 
    opacity: float = 0.50,  # Default to 50% opacity
    angle: float = 30,
    wavy: bool = True,
    var_opacity: bool = True,
    shield_rate: float = 0.25,
    hollow_text: bool = False
) -> Image.Image:
    """
    Generates a full-page transparent PNG (the Decoy & Shield Chaos Layer) matching (width, height).
    - Alternates lines: Red, Gray, Shield (Gray + Blur shadow), Gray.
    - Red lines have the same transparency as gray lines.
    - Exactly ONE line (near the center) is drawn perfectly straight (no wavy sine wave).
    - Shield occurrence rate is adjustable (0.0 to 1.0) and distributed evenly.
    - Supports hollow outline text with proportional stroke width.
    """
    if not text:
        return Image.new("RGBA", (width, height), (0, 0, 0, 0))
        
    # S = diagonal size of target area to allow rotation without edge clipping
    S = int(math.hypot(width, height))
    
    # Create square scratch canvas for rotation
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    
    # Base font size proportional to the page width
    font_size = max(12, int(min(width, height) * 0.035))
    font = get_font(font_size, bold=True)
    
    # Measure character widths for precise positioning
    char_widths = []
    text_w = 0
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    sample_bbox = temp_draw.textbbox((0, 0), "A", font=font)
    char_h = sample_bbox[3] - sample_bbox[1]
    
    for char in text:
        char_bbox = temp_draw.textbbox((0, 0), char, font=font)
        cw = char_bbox[2] - char_bbox[0]
        if cw == 0:
            cw = font.getbbox(" ")[2] - font.getbbox(" ")[0]
        char_widths.append(cw)
        text_w += cw
        
    amplitude = max(3, int(font_size * 0.22)) if wavy else 0
    wavelength = max(60, font_size * 8)
    freq = 2 * math.pi / wavelength
    
    # Spacing step between rows (reduced density layout)
    row_step = int(font_size * 4.2)
    y_rows = list(range(font_size, S - font_size, row_step))
    num_rows = len(y_rows)
    
    if num_rows == 0:
        return Image.new("RGBA", (width, height), (0, 0, 0, 0))
        
    # Identify center row index
    center_idx = num_rows // 2
    
    # Stroke width calculation if hollow text is selected
    stroke_w = max(1, int(font_size * 0.075)) if hollow_text else 0
    
    # 1. DRAW SHADOW PASS: Draw a blurred drop shadow matching the text letters
    if shield_rate > 0.0 and num_rows > 0:
        shield_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        shield_draw = ImageDraw.Draw(shield_layer)
        has_shields = False
        
        # Calculate shadow opacity relative to user-selected opacity
        # Shadows are slightly darker for better edge contrast
        shadow_alpha = min(150, max(40, int(255 * opacity * 0.85)))
        shadow_color = (40, 40, 40, shadow_alpha)  # Darker gray shadow
        
        for row_idx, y_row in enumerate(y_rows):
            is_red_line = (row_idx % 4 == 0)
            is_shield_row = (int((row_idx + 1) * shield_rate) > int(row_idx * shield_rate)) and not is_red_line
            
            if is_shield_row:
                has_shields = True
                is_straight_line = (row_idx == center_idx)
                row_offset = (row_idx % 2) * (text_w // 2)
                curr_x = -font_size * 4 - row_offset
                
                # Draw the shadow text (offset by +2px down and right)
                while curr_x < S + font_size * 2:
                    for idx, char in enumerate(text):
                        cw = char_widths[idx]
                        y_offset = 0
                        if wavy and not is_straight_line:
                            y_offset = amplitude * math.sin(curr_x * freq)
                            
                        # Draw shadow letter
                        if hollow_text:
                            # Shadow is hollow outline too
                            shield_draw.text(
                                (curr_x + 2, y_row + y_offset + 2), 
                                char, 
                                font=font, 
                                fill=(40, 40, 40, 0),
                                stroke_width=stroke_w,
                                stroke_fill=shadow_color
                            )
                        else:
                            shield_draw.text(
                                (curr_x + 2, y_row + y_offset + 2), 
                                char, 
                                font=font, 
                                fill=shadow_color
                            )
                        curr_x += cw
                        
                        if curr_x >= S + font_size * 2:
                            break
                            
                    space_w = font.getbbox(" ")[2] - font.getbbox(" ")[0]
                    curr_x += space_w * 6
                    
        if has_shields:
            # Apply Gaussian Blur to turn duplicate text letters into a soft drop shadow
            blurred_shield = shield_layer.filter(ImageFilter.GaussianBlur(radius=4))
            canvas = Image.alpha_composite(canvas, blurred_shield)
        
    # Draw drawing context on main canvas
    draw = ImageDraw.Draw(canvas)
    
    # 2. DRAW SHARP FOREGROUND TEXT PASS
    for row_idx, y_row in enumerate(y_rows):
        is_red_line = (row_idx % 4 == 0)
        is_straight_line = (row_idx == center_idx)
        
        # Stagger starting positions
        row_offset = (row_idx % 2) * (text_w // 2)
        curr_x = -font_size * 4 - row_offset
        
        while curr_x < S + font_size * 2:
            for idx, char in enumerate(text):
                cw = char_widths[idx]
                
                # Apply Sine Wave Y Offset
                y_offset = 0
                if wavy and not is_straight_line:
                    y_offset = amplitude * math.sin(curr_x * freq)
                    
                # Opacity is shared between gray and red text lines
                if var_opacity:
                    op = min(0.75, max(0.25, opacity + random.uniform(-0.08, 0.08)))
                    alpha = int(255 * op)
                else:
                    alpha = int(255 * opacity)
                    
                if is_red_line:
                    r, g, b = 255, 0, 0
                else:
                    r, g, b = 128, 128, 128
                    if var_opacity:
                        r = min(255, max(0, r + random.randint(-15, 15)))
                        g = min(255, max(0, g + random.randint(-15, 15)))
                        b = min(255, max(0, b + random.randint(-15, 15)))
                        
                # Style font: solid fill or hollow outline
                if hollow_text:
                    fill_color = (r, g, b, 0) # Transparent fill inside
                    char_stroke_w = stroke_w
                    char_stroke_fill = (r, g, b, alpha)
                else:
                    fill_color = (r, g, b, alpha)
                    char_stroke_w = 0
                    char_stroke_fill = None
                    
                draw.text(
                    (curr_x, y_row + y_offset), 
                    char, 
                    font=font, 
                    fill=fill_color,
                    stroke_width=char_stroke_w,
                    stroke_fill=char_stroke_fill
                )
                curr_x += cw
                
                if curr_x >= S + font_size * 2:
                    break
                    
            # Space between repetitions
            space_w = font.getbbox(" ")[2] - font.getbbox(" ")[0]
            curr_x += space_w * 6
            
    # 3. Rotate the canvas
    rotated_canvas = canvas.rotate(angle, resample=Image.BICUBIC, expand=False)
    
    # 4. Crop rotated canvas to center (width, height)
    left = (S - width) // 2
    top = (S - height) // 2
    right = left + width
    bottom = top + height
    
    return rotated_canvas.crop((left, top, right, bottom))

def apply_watermark(
    image: Image.Image, 
    text: str, 
    opacity: float = 0.50, 
    angle: float = 30,
    wavy: bool = True,
    var_opacity: bool = True,
    noise_grain: bool = True,
    shield_rate: float = 0.25,
    hollow_text: bool = False
) -> Image.Image:
    """
    Applies the Chaos Layer watermark to a PIL Image (used for live previewing).
    Keeps the preview perfectly synchronized with the saved file output.
    """
    if not text:
        return image.copy()

    # Convert base to RGB for multiplication
    rgb_img = image.convert("RGB")
    w, h = rgb_img.size
    
    chaos_layer = generate_chaos_layer(
        w, h, text, opacity=opacity, angle=angle,
        wavy=wavy, var_opacity=var_opacity, shield_rate=shield_rate, hollow_text=hollow_text
    )
    
    # Create white canvas and paste chaos layer onto it
    watermark_canvas = Image.new("RGB", (w, h), (255, 255, 255))
    watermark_canvas.paste(chaos_layer, mask=chaos_layer.split()[3])
    
    # Multiply watermark over base image (Multiply blend mode)
    watermarked = ImageChops.multiply(rgb_img, watermark_canvas)
    
    if noise_grain:
        watermarked = add_noise(watermarked, intensity=0.05)
        
    # Clean up
    chaos_layer.close()
    watermark_canvas.close()
    
    # Convert back to original image mode if necessary
    if image.mode != "RGB":
        return watermarked.convert(image.mode)
    return watermarked

def process_image_file(
    input_path: str, 
    output_path: str, 
    text: str, 
    opacity: float = 0.50, 
    angle: float = 30,
    wavy: bool = True,
    var_opacity: bool = True,
    noise_grain: bool = True,
    shield_rate: float = 0.25,
    hollow_text: bool = False
):
    """
    Composites the Chaos Layer over the original image and saves it as a flat RGB image.
    Uses Pillow's ImageChops.multiply for advanced blend modes.
    """
    with Image.open(input_path) as img:
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
            
        # Convert base to RGB for multiplication
        rgb_img = img.convert("RGB")
        w, h = rgb_img.size
        
        # Generate Chaos Layer PNG matching the image size
        chaos_layer = generate_chaos_layer(
            w, h, text, opacity=opacity, angle=angle,
            wavy=wavy, var_opacity=var_opacity, shield_rate=shield_rate, hollow_text=hollow_text
        )
        
        # Create white canvas and paste chaos layer onto it
        watermark_canvas = Image.new("RGB", (w, h), (255, 255, 255))
        watermark_canvas.paste(chaos_layer, mask=chaos_layer.split()[3])
        
        # Multiply watermark over the original image
        watermarked = ImageChops.multiply(rgb_img, watermark_canvas)
        
        ext = os.path.splitext(output_path.lower())[1]
        if ext in [".jpg", ".jpeg"]:
            # Apply static noise grain overlay
            if noise_grain:
                watermarked = add_noise(watermarked, intensity=0.05)
            watermarked.save(output_path, "JPEG", quality=90)
        else:
            # Save as PNG
            if noise_grain:
                watermarked = add_noise(watermarked, intensity=0.05)
            watermarked.save(output_path, format="PNG")
            
        # Clean up
        chaos_layer.close()
        watermark_canvas.close()
        watermarked.close()

def get_pdf_page_image(pdf_path: str, page_num: int, dpi: int = 150) -> Image.Image:
    """
    Renders a specific page of a PDF as a PIL Image.
    Forces PIL to load image bytes immediately to prevent lazy loading errors.
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    pix = page.get_pixmap(dpi=dpi)
    img_data = pix.tobytes("png")
    doc.close()
    
    img = Image.open(io.BytesIO(img_data))
    img.load()  # Force immediate byte reading into memory
    return img

def get_pdf_page_count(pdf_path: str) -> int:
    """
    Returns the total number of pages in a PDF document.
    """
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count

def process_pdf_file(
    input_path: str, 
    output_path: str, 
    text: str, 
    opacity: float = 0.50, 
    angle: float = 30, 
    dpi: int = 150, 
    wavy: bool = True,
    var_opacity: bool = True,
    noise_grain: bool = True,
    shield_rate: float = 0.25,
    hollow_text: bool = False,
    progress_callback=None
):
    """
    Watermarks every page of a PDF and flat-rasterizes it.
    Uses Pillow's ImageChops.multiply to recreate fitz.PDF_BM_Multiply,
    ensuring black text/diagram lines stay black on all systems.
    Incremental page writing and memory release prevent OOM on large files.
    """
    doc = fitz.open(input_path)
    page_count = len(doc)
    
    # Create empty target PDF document
    out_doc = fitz.open()
    
    try:
        for i in range(page_count):
            if progress_callback:
                progress_callback(i + 1, page_count)
            
            # 1. Render page to image at specified DPI
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi)
            img_data = pix.tobytes("png")
            page_img = Image.open(io.BytesIO(img_data)).convert("RGB")
            
            # 2. Generate Chaos Layer matching page dimensions
            w, h = page_img.size
            chaos_layer = generate_chaos_layer(
                w, h, text, opacity=opacity, angle=angle,
                wavy=wavy, var_opacity=var_opacity, shield_rate=shield_rate,
                hollow_text=hollow_text
            )
            
            # 3. Create white canvas and paste chaos layer onto it
            watermark_canvas = Image.new("RGB", (w, h), (255, 255, 255))
            watermark_canvas.paste(chaos_layer, mask=chaos_layer.split()[3])
            
            # 4. Multiply watermark canvas with the rendered page image (keeps black lines black)
            watermarked_img = ImageChops.multiply(page_img, watermark_canvas)
            
            # 5. Apply subtle static noise layer over the final flattened image
            if noise_grain:
                watermarked_img = add_noise(watermarked_img, intensity=0.05)
                
            # Convert to compressed JPEG bytes for PDF insertion (greatly reduces file size)
            img_byte_arr = io.BytesIO()
            watermarked_img.save(img_byte_arr, format="JPEG", quality=90)
            img_bytes = img_byte_arr.getvalue()
            
            # 6. Insert page into target PDF using page dimensions
            w_pts = page.rect.width
            h_pts = page.rect.height
            out_page = out_doc.new_page(width=w_pts, height=h_pts)
            
            rect = fitz.Rect(0, 0, w_pts, h_pts)
            out_page.insert_image(rect, stream=img_bytes)
            
            # Clean up PIL image handles immediately to free RAM
            page_img.close()
            chaos_layer.close()
            watermark_canvas.close()
            watermarked_img.close()
            
        # 7. Write PDF using garbage collection and deflation compression
        out_doc.save(output_path, garbage=3, deflate=True)
    finally:
        out_doc.close()
        doc.close()
