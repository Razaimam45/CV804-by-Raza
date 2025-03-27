'''
                                                
   Code framework for the lecture

   "CV804: 3D Geometry Processing"

   Lecturer: Hao Li
   TAs: Phong Tran, Long Nhat Ho, Ekaterina Radionova

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


from OpenGL.GL import *
import numpy as np
import pyrr

from base_entity import BaseEntity


class BoxFaceEntity(BaseEntity):
    VERTEX_SHADER_PATH = './shaders/box_face.vert'
    FRAGMENT_SHADER_PATH = './shaders/box_face.frag'

    def __init__(self, texture_path, texture_unit):
        super().__init__()

        self.texture_unit = texture_unit
        self._build_vertex_data()
        self._shader_program = self._create_shader(self.VERTEX_SHADER_PATH, self.FRAGMENT_SHADER_PATH)

        # Pass texture to fragment shader
        self.texture = self._load_texture(texture_path, texture_unit)
        glUseProgram(self._shader_program)
        glUniform1i(glGetUniformLocation(self._shader_program, "texture0"), texture_unit)

    def _build_vertex_data(self):
        '''
            This method builds the vertex data required for rendering a single face of the world box. It includes the following steps:
            1. Create the vertices: Defines the vertices of two triangles that form a square. Each vertex contains 6 values: 
            - xyz coordinates of the vertex
            - st coordinates of the texture
            - An extra placeholder value
            2. Create the drawing indices: Defines the order in which the vertices should be drawn. Uses GL_TRIANGLES with 6 values.
            3. Create VAO (Vertex Array Object): Stores the vertex attribute configuration and the vertex buffer objects associated with it.
            4. Create VBO (Vertex Buffer Object): Stores the vertex data in GPU memory.
            5. Create EBO (Element Buffer Object): Stores the indices in GPU memory.
            The method also sets up the vertex attribute pointers for position and texture coordinates, and binds the buffers appropriately.
        '''
        '''
            Build vertex data, including position, texture coordinate, and the drawing indices.
            
            Hint:
                - Step 1: Create the vertices. It should be the vertices of 2 triangles that combined into a square. Each tuple in the vertices should contain 6 values: xyz coordinate of the vertex and st coordinate of the texture
                - Step 2: Create the drawing indices. If you use GL_TRIANGLES, it has 6 values. On the other hand, if you use GL_TRIANGLE_STRIP, it only has 4 values.
                - Step 3: Create VAO.
                - Step 4: Create VBO.
                - Step 5: Create EBO using the created indices.
        '''

        self.vertices = np.array([
            # Position          # Tex Coords   # Extra value (placeholder)
            -0.5, -0.5, 0.0,    0.0, 0.0,     0.0,
            0.5, -0.5, 0.0,    1.0, 0.0,     0.0,
            0.5,  0.5, 0.0,    1.0, 1.0,     0.0,
            -0.5,  0.5, 0.0,    0.0, 1.0,     0.0
        ], dtype=np.float32)

        self._indices = np.array([
            0, 1, 2,
            2, 3, 0
        ], dtype=np.uint32)

        # Step 3: Create VAO
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)

        glBindVertexArray(self.vao)

        # Step 4: Create VBO
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        # Step 5: Create EBO using the created indices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self._indices.nbytes, self._indices, GL_STATIC_DRAW)

        # Position attribute (xyz: 3 values)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * self.vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Texture coord attribute (st: 2 values)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 6 * self.vertices.itemsize, ctypes.c_void_p(3 * self.vertices.itemsize))
        glEnableVertexAttribArray(1)

        # Bind back to default (clean-up)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)


    def draw(self):
        glUseProgram(self._shader_program)
        glBindVertexArray(self.vao)
        glActiveTexture(GL_TEXTURE0 + self.texture_unit)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glDrawElements(GL_TRIANGLES, len(self._indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(2, (self.vbo, self.ebo))


class WorldBoxEntity:
    def __init__(self, sky_texture_path: str, ground_texture_path: str, texture_unit: int):
        """
        Initializes the WorldBoxEntity with sky and ground textures and calculates the model transforms for the world faces.

        Args:
            sky_texture_path (str): The file path to the sky texture.
            ground_texture_path (str): The file path to the ground texture.
            texture_unit (int): The texture unit to be used for binding textures.

        Attributes:
            _sky_face (BoxFaceEntity): The entity representing the sky face.
            _ground (BoxFaceEntity): The entity representing the ground face.
            _front_transform (numpy.ndarray): The transformation matrix for the front face.
            _back_transform (numpy.ndarray): The transformation matrix for the back face.
            _left_transform (numpy.ndarray): The transformation matrix for the left face.
            _right_transform (numpy.ndarray): The transformation matrix for the right face.
            _top_transform (numpy.ndarray): The transformation matrix for the top face.
            _bottom_transform (numpy.ndarray): The transformation matrix for the bottom face.
        """
        super().__init__()
        '''
            This code already created the sky and the ground. The world is implemented by a closed box for simplicity. 
            The sky is composite of the top, left, right, front, back box faces. The ground is the bottom face.

            This code is already load the sky and the ground entities. There are only two faces for the sky and the ground. 
            You need to draw the sky face 5 times by calculating the below model transforms to transform the sky face into front, back, left, right, and top positions. Please read the draw function for more details.
        '''

        self._sky_face = BoxFaceEntity(sky_texture_path, texture_unit + 0)
        self._sky_face.model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        self._sky_face.view_transform = pyrr.matrix44.create_identity(dtype=np.float32)

        self._ground = BoxFaceEntity(ground_texture_path, texture_unit + 1)
        self._ground.model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        self._ground.view_transform = pyrr.matrix44.create_identity(dtype=np.float32)

        '''
        Your code starts from here. Need to replace these matrices.
        '''
        # Calculate transformations for each face of the box
        # Front face (Z = 10)
        self._front_transform = pyrr.matrix44.create_from_translation([0, 0, 10], dtype=np.float32)

        # Back face (Z = -10, rotated 180° around Y)
        back_rotation = pyrr.matrix44.create_from_y_rotation(np.pi, dtype=np.float32)
        back_translation = pyrr.matrix44.create_from_translation([0, 0, -10], dtype=np.float32)
        self._back_transform = pyrr.matrix44.multiply(back_rotation, back_translation)

        # Left face (X = -10, rotated 90° around Y)
        left_rotation = pyrr.matrix44.create_from_y_rotation(np.pi/2, dtype=np.float32)
        left_translation = pyrr.matrix44.create_from_translation([-10, 0, 0], dtype=np.float32)
        self._left_transform = pyrr.matrix44.multiply(left_rotation, left_translation)

        # Right face (X = 10, rotated -90° around Y)
        right_rotation = pyrr.matrix44.create_from_y_rotation(-np.pi/2, dtype=np.float32)
        right_translation = pyrr.matrix44.create_from_translation([10, 0, 0], dtype=np.float32)
        self._right_transform = pyrr.matrix44.multiply(right_rotation, right_translation)

        # Top face (Y = 10, rotated -90° around X)
        top_rotation = pyrr.matrix44.create_from_x_rotation(-np.pi/2, dtype=np.float32)
        top_translation = pyrr.matrix44.create_from_translation([0, 10, 0], dtype=np.float32)
        self._top_transform = pyrr.matrix44.multiply(top_rotation, top_translation)

        # Bottom face (Y = -10, rotated 90° around X)
        bottom_rotation = pyrr.matrix44.create_from_x_rotation(np.pi/2, dtype=np.float32)
        bottom_translation = pyrr.matrix44.create_from_translation([0, -10, 0], dtype=np.float32)
        self._bottom_transform = pyrr.matrix44.multiply(bottom_rotation, bottom_translation)

        '''
        Your code ends here.
        '''

    def _update_projection_transform(self, projection_transform):
        self._sky_face.projection_transform = projection_transform
        self._ground.projection_transform = projection_transform

    def _update_view_transform(self, view_transform):
        self._sky_face.view_transform = view_transform
        self._ground.view_transform = view_transform

    def draw(self):
        # Sky front
        self._sky_face.model_transform = self._front_transform
        self._sky_face.draw()

        # Sky back
        self._sky_face.model_transform = self._back_transform
        self._sky_face.draw()

        # Sky left
        self._sky_face.model_transform = self._left_transform
        self._sky_face.draw()
        
        # Sky right
        self._sky_face.model_transform = self._right_transform
        self._sky_face.draw()

        # Sky top
        self._sky_face.model_transform = self._top_transform
        self._sky_face.draw()

        # Ground
        self._ground.model_transform = self._bottom_transform
        self._ground.draw()

    def destroy(self):
        self._sky_face.destroy()
        self._ground.destroy()
