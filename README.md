# 🔒 WaterFile - Secure Offline Watermarking Tool

A lightweight, secure, and fully offline desktop application written in Python using **CustomTkinter** and **PyMuPDF (fitz)**. This application mimics the French government's document securement portal (*filigrane.beta.gouv.fr*) but runs entirely locally on your machine, ensuring complete privacy for your sensitive documents.

---

## ✨ Features

- **Multi-Format Support**: Secure both PDF files and standard images (`.png`, `.jpg`, `.jpeg`).
- **Tiled Diagonal Watermarks**: Applies a staggered repeating diagonal grid of semi-transparent watermark text to prevent cropping or clean extraction.
- **🛡️ Advanced AI-Resistant Features**:
  - **Wavy & Curved Text**: Draws character-by-character along a dynamically scaled sine wave, disrupting AI and OCR bounding-box recognition.
  - **Variable Opacity & Colors**: Randomly fluctuates the color and opacity of individual letters around your target value, leaving behind messy "ghosting" artifacts if AI tools attempt inpainting.
  - **Faint Static Noise Overlay**: Sprinkles a subtle Gaussian noise/grain mask over the final document, breaking the clean reference pixel blocks that generative AIs need to reconstruction-fill.
  - **Hollow Outline Text (New)**: Draws character stroke borders but leaves the inner shape fully transparent, maintaining extreme legibility on dense diagrams while remaining fully AI-resistant.
  - **Pillow-Based Multiply Blend Mode (New)**: Composites the watermark PNG using the Photoshop-style **Multiply** blend mode, ensuring black lines, text, and vector graphics on the page remain perfectly pitch black and never get washed out.
  - **Shield Occurrence rate (New)**: Adjust the percentage of lines that receive the blurred drop shadow via a slider in the GUI.
- **Security-First PDF Flattening (Rasterization)**: 
  - Watermarking vectors in standard PDFs can be easily removed by editing tools.
  - **WaterFile** prevents this by rendering each watermarked page into a high-quality rasterized image (at 100, 150, or 200 DPI) and reassembling them into a new flat PDF.
  - **The resulting PDF contains zero extractable text layers or vector objects**, meaning the watermark cannot be selected, edited, or removed.
- **Real-Time Live Preview**: Instantly updates a scaled, responsive preview of the first page of the document as you edit your text, opacity, rotation, or AI-protection toggles.
- **Modern UI**: Clean, responsive, and dark/light mode adaptable interface with native widgets, sliders, and progress bars.
- **100% Offline**: No network connections are made; your files never leave your computer.

---

## 🛠️ Code Architecture

The project is structured in a clean, modular fashion:
- [main.py](file:///X:/WaterPy/main.py): The main entry point to launch the application.
- [gui.py](file:///X:/WaterPy/gui.py): The responsive GUI codebase built using `customtkinter`. It handles the thread pool, resizing logic, and state.
- [watermark_engine.py](file:///X:/WaterPy/watermark_engine.py): The core processing module containing PIL/Pillow image compositions, PyMuPDF page rendering, and PDF assembly.

---

## 🚀 Running the App Locally

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Install Dependencies
Install the required packages from [requirements.txt](file:///X:/WaterPy/requirements.txt):
```bash
pip install -r requirements.txt
```

### 3. Start the Application
Run the launcher:
```bash
python main.py
```

---

## 📦 Packaging to Standalone Windows `.exe`

To package this application into a single standalone Windows executable that runs without opening an attached console window, use the following **PyInstaller** command:

```powershell
pyinstaller --onefile --noconsole --collect-all customtkinter main.py
```

### Explanation of Command Flags:
- `--onefile` (`-F`): Bundles all python scripts and dependencies into a single, portable executable file (`main.exe` inside the `dist/` directory).
- `--noconsole` (`-w`): Prevents the Windows Command Prompt (console window) from opening behind the graphical interface when running the app.
- `--collect-all customtkinter`: **CRITICAL!** Instructs PyInstaller to search for and collect all metadata, themes (JSON files), fonts, and assets embedded in the `customtkinter` package directory so the GUI renders properly with all styles.

*Optional*: If you have a custom icon file (e.g., `app_icon.ico`), you can compile it with:
```powershell
pyinstaller --onefile --noconsole --collect-all customtkinter --icon=app_icon.ico main.py
```
