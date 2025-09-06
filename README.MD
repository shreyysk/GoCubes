
-----

# 🎲 Go Cubes - Rubik's Cube Scanner & Solver

Go Cubes is a Python application that uses your computer's webcam to scan a physical 3x3 Rubik's Cube, automatically detect its state, and provide a step-by-step solution. It features a powerful graphical editor to correct any scanning errors and an animated 3D visualizer to display the solution.

## ✨ Features

  * **Camera-Based Scanning**: Uses OpenCV to detect the cube's faces and identify the color of each sticker in real-time.
  * **Color Calibration**: Includes a standalone script to calibrate color detection for your specific cube and lighting conditions, ensuring high accuracy.
  * **Hybrid Manual Editor**: If the scan fails or produces an impossible state, a powerful GUI launches automatically:
      * **2D Unfolded Net**: An easy-to-use interface to see all six faces at once and repaint incorrect stickers with a single click.
      * **Live 3D Preview**: A parallel 3D model (Pygame/OpenGL) updates in real-time as you edit the 2D net, so you can see the cube from all angles.
      * **Real-Time Validation**: The editor continuously checks for color count errors, impossible edge pieces (e.g., White-Yellow), and duplicate pieces, guiding you to a solvable state.
  * **3D Solution Visualizer**: Once a valid cube state is found, the application displays the solution on an animated 3D model, allowing you to follow the moves step by step.
  * **Robust Controls**: All windows can be closed via the command line (`Ctrl+C`), and the application provides a restart option upon failure, creating a smooth user experience.

-----

## ⚙️ Installation

### **Requirements**

You'll need Python 3 installed. The project depends on several libraries which can be installed via pip.

1.  Create a `requirements.txt` file with the following content:

    ```txt
    opencv-python
    numpy
    pygame
    PyOpenGL
    rubik-solver
    ```

2.  Install the required packages by running this command in your terminal:

    ```bash
    pip install -r requirements.txt
    ```

-----

## 🚀 Usage

All commands should be run from the root directory of the project.

### **1. Color Calibration (Recommended First Step)**

To ensure the camera accurately detects your cube's colors, run the calibration script first. A `resources/colors.json` file will be created with your settings.

```bash
python main.py -c
```

Follow the on-screen instructions: show each color to the camera, click on it, and press 'w' or Enter to save.

### **2. Scanning and Solving**

This is the main function. Hold each of the six faces of the cube up to the camera and wait for the program to detect it.

```bash
python main.py
```

### **3. Manual Editor**

If you want to skip the camera scan and enter the cube's state manually, you can launch the hybrid editor directly.

```bash
python main.py -m
```

### **4. Keyboard Shortcuts**

  * **During Scanning/Calibration**:
      * `q` or `Esc`: Quit the program.
      * `Backspace`: Go back to scan the previous face.
  * **In the Hybrid Editor**:
      * `Esc`: Close the editor window.
  * **In the 3D Solution Visualizer**:
      * `Enter` or `Right Arrow`: Show the next move.
      * `Backspace` or `Left Arrow`: Go to the previous move.
      * `q` or `Esc`: Close the visualizer.
  * **In the Terminal**:
      * `Ctrl+C`: Gracefully closes any active window (scanning, editor, or visualizer).

-----

## 📂 File Descriptions

  * `main.py`: The main entry point for the application. Handles the scanning loop, validation, and restart logic.
  * `hybrid_editor.py`: The GUI for manually correcting the cube state, featuring the 2D net and live 3D preview.
  * `PyCube.py`: The 3D visualization module for displaying the solution steps.
  * `calibrate.py`: A script for calibrating color detection values.
  * `helpers.py`: Contains helper functions for advanced color distance calculations (CIEDE2000) and cube validation data.
  * `geometry.py`: Defines the vertices, faces, and color schemes for the 3D models.
  * `draw.py`: A helper module to draw the 2D cube state overlay on the camera feed during scanning.
  * `predict.py`: Contains the logic for predicting the closest color match for a sticker.
  * `quat.py`: A utility for quaternion mathematics used for smooth 3D rotations.
  * `debug.py`: A standalone script for analyzing cube states without needing a camera.
  * `resources/colors.json`: (Generated) The file where custom color calibration data is saved.

  steps

  
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
python src\main.py



# First time: Calibrate colors for your lighting
python src\main.py --c