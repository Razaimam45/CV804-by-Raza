# Rigid Surface Registration

![Examples](./assets_results\gifs\bunny_p2p_gif.gif)
![Examples](./assets_results\gifs\bunny_p2surface_gif.gif)
![Examples](./assets_results\gifs\bee_p2p_gif.gif)
![Examples](./assets_results\gifs\goblet_p2surface_gif.gif)
![Examples](./assets_results\gifs\dragon_p2surface_gif.gif)
![Examples](./assets_results\gifs\asu_p2surface_gif.gif)

## Overview
This project implements an **interactive rigid surface registration application** for aligning multiple 3D meshes. It supports **point-to-point** and **point-to-plane** distance minimization techniques.

### Features
- **Mesh Registration**: Align source meshes to a target mesh using rigid transformations.
- **Interactive Initialization**: Users can manually adjust the source mesh before automatic registration.
- **Real-time Visualization**: View sampled points and registration results dynamically.
- **Multiple Mesh Support**: Process and align multiple 3D meshes sequentially.

## Installation
Ensure that you have a working Python environment with `numpy`, `scipy`, `trimesh`, and `glfw`. If you have already set up the environment from previous assignments, you can reuse it.

To install dependencies, run:
```sh
pip install -r requirements.txt
```

## Usage
Run the application with the following command:
```sh
python main.py --output_file save_path path_to_mesh_1 path_to_mesh_2 ... path_to_mesh_n
```
### Arguments:
- `save_path`: Path to save registered points (e.g., `results/output.txt`)
- `path_to_mesh_i`: Paths to the input meshes (at least 2 meshes required)

Example:
```sh
python main.py --output_file results/output.txt data/bunny_1.obj data/bunny_2.obj
```

## Implementation Details
This project implements two surface registration techniques:

### **1. Sampling Points (Preprocessing)**
- Uniformly sample points from the source mesh.
- Find the closest corresponding points on the target mesh using a **KD-tree**.
- Implemented in `RegistrationViewerApp.subsample()`.

### **2. Pair Filtering (Noise Reduction)**
- **Distance Thresholding:** Removes pairs too far apart.
- **Normal Compatibility:** Removes pairs where normals differ significantly (>60 degrees).
- **Border Handling:** Removes pairs near mesh borders.
- Implemented in `RegistrationViewerApp.calculate_correspondences()`.

### **3. Point-to-Point Registration**
- Finds the optimal rigid transformation to minimize point distances.
- Uses small-angle approximations to linearize rotation.
- Solves for rotation `R` and translation `t` using least squares.
- Implemented in `Registration.register_point2point()`.

### **4. Point-to-Plane Registration**
- Minimizes the distance between points and their corresponding **tangent planes**.
- Linearizes the rotation and solves using least squares.
- Implemented in `Registration.register_point2surface()`.

## Controls
| Key | Action |
|------|-----------------------------|
| `r` | Run point-to-point registration |
| `SPACE` | Run point-to-plane registration |
| `SHIFT + Mouse` | Manually rotate the source mesh |
| `n` | Load the next mesh |

## File Structure
```
RigidSurfaceRegistration/
├── main.py                 # Entry point
├── registration.py         # Registration algorithms
├── transformation.py       # Rigid transformations
├── closest_point.py        # KD-tree for closest point matching
├── viewer.py               # OpenGL viewer
├── data/                   # Input mesh files
├── Models/                 # Additional low point mesh files
├── resources/              # Example images
└── assets_results/         # Output registered meshes and assets
```

## Acknowledgments
This project is part of CV804 course on **rigid surface registration** and **iterative closest point (ICP) algorithms**. The methodology follows industry standards for 3D surface alignment.