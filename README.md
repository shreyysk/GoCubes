## File: `README.md`
**Location**: `rubik-ultimate/README.md`

```markdown
# Rubik Ultimate Solver 🎲

A comprehensive Rubik's Cube solver combining webcam scanning, 3D visualization, and multiple solving algorithms.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## ✨ Features

### 🎥 Webcam Scanning
- Real-time cube detection with OpenCV
- Automatic color recognition using CIEDE2000 algorithm
- Color calibration mode for different lighting conditions
- Manual color correction interface

### 🧮 Multiple Solving Algorithms
- **Kociemba Algorithm**: Fast two-phase solver
- **Thistlethwaite Algorithm**: Four-phase group theory approach
- Solution optimization and move reduction
- Step-by-step solution breakdown

### 🎨 Visualization
- **3D Cube View**: Interactive OpenGL rendering
- **2D Flat View**: Traditional net representation
- Smooth animation of moves
- Solution playback with next/previous controls

### 🌍 Additional Features
- Multi-language support (EN, ES, FR, DE, ZH)
- Random scramble generator
- Solution export/import
- Performance metrics and statistics
- Dark/Light theme support

## 📋 Requirements

- Python 3.8 or higher
- Webcam (for scanning feature)
- OpenGL compatible graphics card
- 4GB RAM minimum

## 🚀 Installation

### Method 1: Using pip (Recommended)

```bash
# Create virtual environment
python -m venv env

# Activate virtual environment
# On Windows:
env\Scripts\activate
# On macOS/Linux:
source env/bin/activate

# Install the package
pip install -r requirements.txt
python setup.py install
```

### Method 2: From source

```bash
# Clone the repository
git clone https://github.com/yourusername/rubik-ultimate.git
cd rubik-ultimate

# Create and activate virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run directly
python src/main.py
```

## 📖 Usage

### GUI Mode (Default)

```bash
# Launch the application
rubik-ultimate

# Or directly with Python
python src/main.py
```

### Command Line Mode

```bash
# Solve a specific scramble
rubik-cli "R U R' U' R' F R2 U' R' U' R U R' F'"

# Generate random scramble and solve
rubik-cli --random 25

# Use webcam scanning
rubik-cli --scan

# Show solution breakdown by subgroups
rubik-cli "F U F' U'" --group
```

## 🎮 Controls

### Webcam Scanning Mode
- **Space**: Capture face
- **C**: Toggle calibration mode
- **R**: Reset scan
- **Enter**: Process scanned cube

### 3D Visualization
- **Left Click + Drag**: Rotate view
- **Right Click + Drag**: Pan view
- **Mouse Wheel**: Zoom in/out
- **Arrow Keys**: Step through solution
- **Space**: Play/Pause animation
- **R**: Reset view

### Keyboard Shortcuts
- **Ctrl+N**: New scan
- **Ctrl+O**: Open scramble file
- **Ctrl+S**: Save solution
- **Ctrl+Q**: Quit
- **F1**: Show help
- **F11**: Toggle fullscreen

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
  "scanner": {
    "camera_index": 0,
    "detection_threshold": 30,
    "color_distance_algorithm": "CIEDE2000"
  },
  "solver": {
    "default_algorithm": "kociemba",
    "max_depth": 25,
    "use_pruning_tables": true
  },
  "visualization": {
    "animation_speed": 500,
    "cube_size": 300,
    "show_labels": true
  },
  "general": {
    "language": "en",
    "theme": "dark",
    "auto_save_solutions": true
  }
}
```

## 🏗️ Project Structure

```
rubik-ultimate/
├── src/               # Source code
│   ├── scanner/       # Webcam and color detection
│   ├── solver/        # Solving algorithms
│   ├── visualizer/    # 2D/3D visualization
│   └── utils/         # Utilities and helpers
├── assets/            # Resources (fonts, icons, styles)
├── translations/      # Language files
├── tests/            # Unit tests
└── examples/         # Example scrambles and demos
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test module
pytest tests/test_solver.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📊 Performance

| Algorithm | Average Solve Time | Move Count |
|-----------|-------------------|------------|
| Kociemba  | 0.02s            | 20-25      |
| Thistlethwaite | 0.15s       | 30-45      |

## 🐛 Known Issues

- Color detection may vary under different lighting conditions
- Some webcams may have compatibility issues with OpenCV
- 3D rendering requires OpenGL 3.3+ support

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original QBR project for webcam scanning concepts
- Kociemba algorithm implementation
- Thistlethwaite group theory approach
- OpenCV and PyQt5 communities

## 📧 Contact

- Project Link: [https://github.com/yourusername/rubik-ultimate](https://github.com/yourusername/rubik-ultimate)
- Issues: [https://github.com/yourusername/rubik-ultimate/issues](https://github.com/yourusername/rubik-ultimate/issues)

## 🚦 Roadmap

- [ ] Add more solving algorithms (CFOP, Roux)
- [ ] Implement pattern recognition
- [ ] Add solver statistics and analytics
- [ ] Mobile app version
- [ ] Cloud-based solving service
- [ ] VR/AR support
- [ ] Machine learning for better color detection
- [ ] Bluetooth cube integration

---

Made with ❤️ by the Rubik Ultimate Team
```

