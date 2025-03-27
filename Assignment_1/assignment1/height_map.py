'''
                                                
   Code framework for the lecture

   "CV804: 3D Geometry Processing"

   Lecturer: Hao Li
   TAs: Phong Tran, Long Nhat Ho

   Copyright (C) 2025 by  Metaverse Lab, MBZUAI
                                                                         
-----------------------------------------------------------------------------
                                                                            
                                License                                     
                                                                            
   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, 
   Boston, MA  02110-1301, USA.
'''


import cv2
import numpy as np
from numpy.typing import NDArray
from OpenGL.GL import *
import pyrr
from typing import Tuple


class HeightMap:
    def __init__(self, height_map_path):
        self._num_vertices: int = -1

        self.vao: int = 0
        self.vbo: int = 0
        self.ebo: int = 0
        self._indices: NDArray[np.uint32] = np.empty(0, dtype=np.uint32)

        self.height_map, self.texture = self._load_height_map(height_map_path)
        self._build_vertex_data(self.height_map, self.texture)

        self._init_model_transform()

    def _load_height_map(self, path: str) -> Tuple[NDArray[np.float32], NDArray[np.float32]]:
        """
        Load the height map and calculate the texture.

        Parameters:
            - path (str): Path to the height map image.
        Returns:
            - height_map (NDArray[np.float32]): The height map. It is the z-coordinate in the model space.
            - texture (NDArray[np.float32]): The RGB texture, normalized to range [0..1].
        
        Details:
        - The function reads the image from the specified path using OpenCV's `cv2.imread` function in grayscale mode. 
        - The height map is scaled to a range of [0, 1] by dividing by 255.0.
        - It computes a texture by mapping height values to colors. A simple color gradient is applied to visualize the height map, with blue representing low heights and red representing high heights.
        - The function returns both the height map (representing the z-coordinates) and the computed texture (RGB values corresponding to each height).
        """
        
        image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Image at path '{path}' could not be loaded.")

        height_map = image.astype(np.float32) / 255.0  # Normalize height to range [0, 1]

        # Calculate the texture based on the height values
        texture = np.zeros((height_map.shape[0], height_map.shape[1], 3), dtype=np.float32)
        # Define color gradient for height (example: blue for low, red for high)
        for i in range(height_map.shape[0]):
            for j in range(height_map.shape[1]):
                height = height_map[i, j]

                # Normalize the height to the range [0, 1]
                # height_normalized = np.clip(height, 0.0, 1.0)

                # Define the color components
                r = height  # Red increases with height
                g = 1.0 - abs(2 * height - 1)
                b = 1.0 - height  # Blue decreases with height
        
                # Example heatmap coloring based on height:
                # r = height  # Red increases with height
                # g = 0.0     # Green stays constant
                # b = 1.0 - height  # Blue decreases with height

                # Set the color at the pixel
                texture[i, j] = [g, r, b]

        return height_map, texture

    def apply_scale(self, scale_factor):
        """Apply the scaling factor to the height map."""
        self.height_map *= scale_factor
        # print(f"Height map scaled by factor: {scale_factor}")
        # Update the vertex positions according to the new height map scale
        H, W = self.height_map.shape
        for i in range(H):
            for j in range(W):
                idx = i * W + j
                self._vertices[idx, 2] = self.height_map[i, j]  # Update Z-coordinate (height)

        # Re-upload the updated vertex data to the GPU
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self._vertices.nbytes, self._vertices)
        
    def _build_vertex_data(self, height_map: NDArray[np.float32], texture: NDArray[np.float32]):
        """
        Build the vertex data for rendering, including:
            - Vertex Array Object (VAO)
            - Vertex Buffer Object (VBO)
            - Optionally Element Buffer Object (EBO) if you draw using glDrawElements.

        Parameters:
            - height_map (NDArray[np.float32]): Height map numpy array.
            - texture (NDArray[np.float32]): Texture numpy array.
        
        Details:
        - This function constructs the vertex data for rendering by creating positions and color values for each vertex.
        - The vertex positions are normalized to a [-1, 1] range based on the resolution of the height map (height_map.shape).
        - The colors (RGB) for each vertex are assigned based on the calculated texture.
        - The function then creates the appropriate OpenGL buffers (VAO, VBO, EBO) to store the vertex data and indices for drawing.
        - It generates indices for drawing using triangle strips, which are optimized for rendering grid-like structures like height maps.
        """
        
        H, W = height_map.shape
        self._num_vertices = H * W

        # Create vertex positions and colors
        vertices = np.zeros((H * W, 6), dtype=np.float32)  # x, y, z, r, g, b
        
        # Generate vertex positions and colors
        for i in range(H):
            for j in range(W):
                idx = i * W + j
                # Normalize coordinates to [-1, 1]
                x = (j / (W - 1)) * 2 - 1
                y = (i / (H - 1)) * 2 - 1
                z = height_map[i, j]
                r, g, b = texture[i, j]
                
                vertices[idx] = [x, y, z, r, g, b]
        self._vertices = np.array(vertices, dtype=np.float32)
        
        # Generate indices for triangle strips - one strip per row
        indices = []
        for i in range(H - 1):
            # Start a new strip for each row
            row_indices = []
            for j in range(W):
                row_indices.extend([i * W + j, (i + 1) * W + j])
            indices.extend(row_indices)
            # Add a primitive restart index
            # indices.append(0xFFFFFFFF)  # Use maximum uint32 value as primitive restart index

        # Remove the last primitive restart index
        # if indices:
        #     indices.pop()

        self._indices = np.array(indices, dtype=np.uint32)
        
        # Create and bind VAO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Create and bind VBO
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self._vertices.nbytes, self._vertices, GL_STATIC_DRAW)
        
        # Create and bind EBO
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self._indices.nbytes, self._indices, GL_STATIC_DRAW)
        
        # Set vertex attributes
        # Position attribute (x, y, z)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # Color attribute (r, g, b)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)
        
        glBindVertexArray(0)


    def _init_model_transform(self):
        self._model_transform = pyrr.matrix44.create_identity(dtype=np.float32)

    def update_model_transform(
        self,
        translation: NDArray[np.float32],
        rotation: NDArray[np.float32],
        scale: float
    ):
        """
        Update the model transformation matrix.

        Parameters:
            - translation (NDArray[np.float32]): 3D translation vector.
            - rotation (NDArray[np.float32]): 2D Rotation vector. Only rotate in yaw and pitch angles.
            - scale (float): Scale value. Assuming the scale is uniform in all three dimensions.
        
        Details:
        - The function updates the model's transformation matrix by combining translation, rotation, and scaling transformations.
        - It uses the `pyrr` library to generate matrices for translation, rotation (both yaw and pitch), and scaling.
        - The final model transformation matrix is computed by multiplying these individual matrices in the correct order.
        """
        
        # Ensure translation is a 3D vector
        translation_3d = np.array([translation[0], translation[1], 0.0], dtype=np.float32)
        
        # Create transformations
        translation_matrix = pyrr.matrix44.create_from_translation(translation_3d, dtype=np.float32)
        rotation_yaw_matrix = pyrr.matrix44.create_from_y_rotation(rotation[0], dtype=np.float32)
        rotation_pitch_matrix = pyrr.matrix44.create_from_x_rotation(rotation[1], dtype=np.float32)
        scale_matrix = pyrr.matrix44.create_from_scale([scale, scale, scale], dtype=np.float32)
        
        # Combine transformations
        self._model_transform = pyrr.matrix44.multiply(
            pyrr.matrix44.multiply(
                pyrr.matrix44.multiply(scale_matrix, rotation_yaw_matrix),
                rotation_pitch_matrix
            ),
            translation_matrix
        )


    def get_model_transform(self):
        return self._model_transform

    def draw(self):
        """
        OpenGL draw function.

        Details:
        - The function binds the VAO (Vertex Array Object) to begin drawing.
        - It uses `glDrawElements` to draw the model using the indices defined in the EBO.
        - Finally, it unbinds the VAO after drawing to clean up.
        """
        
        glBindVertexArray(self.vao)
        glEnable(GL_PRIMITIVE_RESTART)
        glPrimitiveRestartIndex(0xFFFFFFFF)
        glDrawElements(GL_TRIANGLES, len(self._indices), GL_UNSIGNED_INT, None)
        glDisable(GL_PRIMITIVE_RESTART)
        glBindVertexArray(0)

    def destroy(self):
        """
        Clean the data, including VAO, VBO, and optionally EBO.

        Details:
        - The function deletes the OpenGL resources (VAO, VBO, and EBO) to free up memory.
        - It ensures proper cleanup of resources used for rendering.
        """
        
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteBuffers(1, [self.ebo])