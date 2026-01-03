# Astro-Horizon Customizer (Beta)
### For N.I.N.A. Custom Horizons & Stellarium Landscape Polygons

> [!WARNING]
> **Beta Software:** This tool is currently in active development. Please verify your exported data before using it in critical astronomy sessions.

A specialized utility designed for astrophotographers to create accurate horizon profiles. By warping 360° panoramas into a **Polar Projection**, it allows for precise tracing of trees, buildings, and terrain to generate horizon files for **N.I.N.A.** and **Stellarium**.

### Source Image Example (360° Equirectangular)
![360 Panorama Example](images/background.png)
*Source: Example image from **360 Photo Cam** for iOS.*

> [!IMPORTANT]
> **Image Preparation:** > 1. **Capture:** Use apps like **360 Photo Cam** (iOS) or **Google Street View/GCam** (Android).
> 2. **Alignment:** Ensure your panorama is centered on **True North**. The vertical center line of your image must be 0° Azimuth.

## 🚀 Key Features

* **Polar Transformation:** Center = Zenith (+90°), Edge = Nadir (-90°).
* **Horizon Baseline:** 0° elevation is mapped precisely to the **50% radius** mark.
* **True North Orientation:** 0° Azimuth (North) points straight **down** from the center.
* **Angular Progression Lock:** Enforces a **Clockwise-only** trace to ensure data integrity.
* **Dynamic Vector Tracking:** Real-time guides for both angle and elevation.

## 📸 Visual Workflow

| 1. Interface | 2. Loaded Image |
| :---: | :---: |
| ![Empty Interface](images/i1.png) | ![Loaded Image](images/i2.png) |

| 3. Tracing Points | 4. Finished Path |
| :---: | :---: |
| ![Adding Points](images/i3.png) | ![Finished Path](images/i4.png) |

## 🛠 Installation

### From Source
1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/Th0MmyS/stellarium_ilg.git](https://github.com/Th0MmyS/stellarium_ilg.git)
    cd stellarium_ilg
    ```
2.  **Install dependencies:**
    ```bash
    pip install opencv-python numpy Pillow
    ```
3.  **Run the app:**
    ```bash
    python main.py
    ```

### From Standalone Executable
Go to the **releases** section on the right side of this GitHub page to download the standalone `.exe` (Windows). 

## 📖 How to Use

1.  **Load Image:** Select your 360° equirectangular panorama (must be North-centered).
2.  **Zoom:** Use the slider for fine details. 
3.  **Trace:** Click along your horizon features. The tool enforces **Clockwise** movement.
4.  **Undo:** Press `Z` to remove the last point.

## 💾 Exporting Data

You can retrieve your horizon data in two ways:

1.  **Automated Export:** Click the **Export (Q)** button or press the `Q` key. This automatically generates `path_results.txt` and `horizon_script.txt` in the application folder, containing your points sorted numerically by angle.
2.  **Manual Copy:** The **Sidebar** displays a live, sorted list of your coordinates. You can manually select the text within this box and copy-paste it directly into your own text editors or configuration files.

## 📊 Coordinate System



| Parameter | Logic |
| :--- | :--- |
| **Angle (X)** | 0° to 359° (Clockwise, 0 = Bottom/North) |
| **Elevation (Y)** | -90° (Outer Edge) → 0° (Mid-Radius) → +90° (Center) |

## 🔭 Final Results Example

The exported data can be used to create custom horizons for astronomy software:

| N.I.N.A. Horizon | Stellarium Horizon |
| :---: | :---: |
| ![NINA Example](images/nina.png) | ![Stellarium Example](images/stellarium.png) |

## 🛠 Developer: Building the Executable
**Windows:**
```powershell
python -m PyInstaller --noconsole --onefile main.py