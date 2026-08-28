# 🔒 WaterPy (WaterFile) — Secure Offline Watermarking Tool

A lightweight, secure, and fully offline desktop application built with Python, **CustomTkinter**, **PyMuPDF (fitz)**, and **Pillow**. Designed to protect sensitive documents (inspired by portals like *filigrane.beta.gouv.fr*), **WaterPy** runs 100% locally on your machine—guaranteeing complete privacy and confidentiality without uploading anything to external servers.

---

## 🌟 Key Features & Specifications

### 📄 Multi-Format Document Support
- **PDF Documents**: Supports multi-page PDFs with individual page rasterization.
- **Images**: Supports all standard image formats including `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, and `.tiff`.

### 🛡️ Advanced AI-Resistant Watermark Protections
Modern generative AI and OCR tools can easily remove standard digital text overlays. WaterPy prevents removal through multiple overlapping defense layers:
- **Tiled Repeating Grid**: Covers the entire document diagonally to prevent partial cropping.
- **Wavy & Curved Text**: Renders characters along dynamic sine waves to break OCR and AI bounding-box detection.
- **Variable Opacity & Color Jitter**: Randomizes opacity and color across individual letters, leaving behind destructive artifacts if AI inpainting is attempted.
- **Hollow Outline Text**: Outlines text characters without solid fill, maintaining maximum document legibility while defeating automated erasure.
- **Multiply Blend Mode**: Blends watermarks using Photoshop-style *Multiply* mode to ensure underlying black text, lines, and signatures remain crisp and legible.
- **Faint Grain & Noise Overlay**: Adds subtle Gaussian grain across the canvas, destroying the flat reference blocks that generative models rely on for reconstruction.
- **Shield & Drop Shadow Rate**: Customizable shadow layer occurrence to add depth variation.

### 🔒 PDF Flattening & Anti-Extraction Rasterization
- Standard PDF watermarks can be deleted in PDF editors. WaterPy permanently burns watermarks into the image raster layer at configurable resolutions (**100 DPI, 150 DPI, 200 DPI, or 300 DPI**).
- The resulting PDF contains **no extractable text layers, fonts, or vector objects**—making watermark removal impossible.

### 🎨 Modern & Responsive UI
- **Real-Time Live Preview**: Dynamic preview updates instantly as you adjust text, opacity, angles, spacing, or protection toggles.
- **Presets & Custom Controls**: One-click quick presets (*"Dossier Location"*, *"Confidentiel"*, etc.) alongside fine-grained controls for font size, density, angle, and colors.
- **Adaptive Dark / Light Theme**: Integrates seamlessly with your system theme via CustomTkinter.

---

## 📥 Installation & Download Guide

### 🍎 macOS Installation

> [!NOTE]
> No Python or Git installation is required on the target Mac when using pre-built binaries.

#### 1. Download the App
1. Go to the [GitHub Repository Actions Tab](https://github.com/lawrencn1/WaterPy/actions).
2. Click on the latest workflow run (e.g., **Build & Package App**).
3. Scroll down to the **Artifacts** section and click **`WaterPy-macOS`** to download `WaterPy-macOS.zip` (or download from [Releases](https://github.com/lawrencn1/WaterPy/releases) if published).

#### 2. Install
1. Double-click `WaterPy-macOS.zip` to extract **`WaterPy.app`**.
2. Drag and drop **`WaterPy.app`** into your **`Applications`** folder.

#### 3. First-Time Launch (Bypassing macOS Gatekeeper)
Because WaterPy is built independently without an expensive paid Apple Developer certificate, macOS Gatekeeper may show a warning: *"WaterPy cannot be opened because it is from an unidentified developer."*

Choose **one** of the following easy methods to open it:
- **Method A (Easiest)**: **Right-click** (or hold <kbd>Control</kbd> and click) `WaterPy.app` in Finder, select **Open**, and click **Open** in the dialog.
- **Method B (System Settings)**: Open **System Settings** > **Privacy & Security**, scroll down to the *Security* section, and click **"Open Anyway"**.
- **Method C (Terminal command)**: Open Terminal and run:
  ```bash
  xattr -cr /Applications/WaterPy.app
  ```

---

### 🪟 Windows Installation

#### 1. Download
1. Go to the [GitHub Repository Actions Tab](https://github.com/lawrencn1/WaterPy/actions).
2. Click the latest workflow run and download **`WaterPy-Windows`** (contains `WaterPy.exe`), or grab it from the [Releases](https://github.com/lawrencn1/WaterPy/releases) page.

#### 2. Run
1. Move `WaterPy.exe` to your desired folder (e.g. Desktop or Program Files).
2. Double-click `WaterPy.exe` to run.
3. If Windows SmartScreen displays *"Windows protected your PC"*:
   - Click **More info**
   - Click **Run anyway**

---

## 💻 Running & Developing from Source

If you want to run or modify the code directly on any platform:

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git (optional, for cloning)

### 2. Setup Environment
```bash
# Clone the repository
git clone https://github.com/lawrencn1/WaterPy.git
cd WaterPy

# Create and activate a virtual environment
# Windows:
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```

---

## 🔨 Packaging Locally with PyInstaller

The project includes a ready-to-use [`main.spec`](main.spec) configured for cross-platform builds.

### To build locally:
```bash
pyinstaller --noconfirm main.spec
```

- **On macOS**: Generates `dist/WaterPy.app`
- **On Windows**: Generates `dist/WaterPy.exe`

---

## 📂 Project Structure

```text
WaterPy/
├── .github/workflows/
│   └── build.yml          # Automated multi-platform CI/CD build pipeline
├── gui.py                 # Responsive CustomTkinter UI & preview renderer
├── watermark_engine.py    # Core image processing, PIL effects & PyMuPDF engine
├── main.py                # Main application entry point
├── main.spec              # PyInstaller multi-platform build specification
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore rules for builds, caches, and temp files
└── README.md              # Documentation and user guide
```

---

## 🔐 Privacy & Security Guarantee

- **Zero Network Activity**: WaterPy does not make any network requests or telemetry calls.
- **Local In-Memory / Temporary Processing**: Your documents are processed entirely in local memory and saved directly to the path you specify.
- **Irreversible Output**: Output PDFs are flattened raster layers, ensuring that original document metadata, hidden vector elements, and private content behind watermarks cannot be recovered.
