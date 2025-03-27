import matplotlib.pyplot as plt
import numpy as np

def save_height_map(array, save_path="example.png"):
    """
    Save a height map as an image using matplotlib.

    Parameters:
        - height_map (np.ndarray): The height map to save (values should be in range [0, 1]).
        - save_path (str): The file path to save the image.
    """
    plt.figure(figsize=(5, 5))
    plt.imshow(array, cmap='gray', vmin=0, vmax=1)
    plt.axis('off')  # Hide axes
    plt.tight_layout(pad=0)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()
