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
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr

from base_entity import BaseEntity
from spline import Spline, sloan_method


class RailwayLineEntity(BaseEntity):
    VERTEX_SHADER_PATH = './shaders/railway_line.vert'
    GEOMETRY_SHADER_PATH = './shaders/railway_line.geo'
    FRAGMENT_SHADER_PATH = './shaders/railway_line.frag'

    @staticmethod
    def _create_shader(vertex_shader_path, geometry_shader_path, fragment_shader_path):
        with open(vertex_shader_path, 'r') as f:
            vertex_shader_src = f.readlines()
        with open(geometry_shader_path, 'r') as f:
            geometry_shader_src = f.readlines()
        with open(fragment_shader_path, 'r') as f:
            fragment_shader_src = f.readlines()

        vertex_shader = compileShader(vertex_shader_src, GL_VERTEX_SHADER)
        geometry_shader = compileShader(geometry_shader_src, GL_GEOMETRY_SHADER)
        fragment_shader = compileShader(fragment_shader_src, GL_FRAGMENT_SHADER)

        shader_program = compileProgram(
            vertex_shader,
            geometry_shader,
            fragment_shader
        )

        return shader_program

    def __init__(self, points, Ts, Ns, Bs):
        super().__init__()

        self._build_vertex_data(points, Ts, Ns, Bs)

        self._shader_program = self._create_shader(
            self.VERTEX_SHADER_PATH,
            self.GEOMETRY_SHADER_PATH,
            self.FRAGMENT_SHADER_PATH
        )

    def _build_vertex_data(self, points, Ts, Ns, Bs):
        colors = np.zeros_like(points)  # Black railway
        self._vertices = np.concatenate((points, colors, Ns, Ts), axis=1).astype(np.float32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self._vertices.nbytes, self._vertices.flatten(), GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12 * np.dtype(np.float32).itemsize, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 12 * np.dtype(np.float32).itemsize, ctypes.c_void_p(12))

        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 12 * np.dtype(np.float32).itemsize, ctypes.c_void_p(24))

        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 12 * np.dtype(np.float32).itemsize, ctypes.c_void_p(36))

    def draw(self):
        glUseProgram(self._shader_program)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_LINE_STRIP, 0, self._vertices.shape[0])
        glBindVertexArray(0)

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, self.vbo)


class WoodenTieEntity(BaseEntity):
    VERTEX_SHADER_PATH = './shaders/wooden_ties.vert'
    FRAGMENT_SHADER_PATH = './shaders/wooden_ties.frag'
    
    def __init__(self, texture_path, texture_unit):
        super().__init__()
        self.texture_unit = texture_unit
        self._build_vertex_data()
        self._shader_program = self._create_shader(self.VERTEX_SHADER_PATH, self.FRAGMENT_SHADER_PATH)

    def _build_vertex_data(self):
        '''
            Build vertex data, including position, texture coordinate, and the drawing indices.
            
            Hint:
                - This entity is very similar  to the wolrd box.
        '''
        self.vertices = np.array([
            #  Position       Texture
            [-0.5, 0, -0.25, 0.0, 0.0],  # Bottom-left
            [0.5, 0, -0.25, 1.0, 0.0],   # Bottom-right
            [0.5, 0, 0.25, 1.0, 1.0],    # Top-right
            [-0.5, 0, 0.25, 0.0, 1.0]    # Top-left
        ], dtype=np.float32)

        self.indices = np.array([
            0, 1, 2,
            2, 3, 0
        ], dtype=np.uint32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Vertex Buffer Object (VBO)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        # Element Buffer Object (EBO)
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        # Position Attribute (location = 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))

        # Texture Coordinate Attribute (location = 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(3 * 4))

    def draw(self):
        '''
            Draw method.
            
            Hint:
            - Again, check the world box entity.
            - Ensure the shader program is used and the vertex array object is bound before drawing.
        '''
        glUseProgram(self._shader_program)
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(2, (self.vbo, self.ebo))


class RailwayEntity:
    def __init__(self, tie_texture_path, railway_path, texture_unit, num_steps=500):
        self._num_steps = num_steps

        with open(railway_path, 'r') as f:
            f.readline()
            points = [list(map(float, line.split(' '))) for line in f]

        points = np.array(points)
        '''
        Your code starts here. You may want to perform some transformations on the points, such as transpose or rescaling, depend on your coordinate system.
        '''
        points[:, 1] *= -1  # Inverting y-axis for correct orientation
        points *= 1.5  # Scale if necessary
        '''
        Your code ends here
        '''

        spline = Spline(points)
        points = list(map(lambda p: spline(p), np.linspace(0, 0.99, self._num_steps)))
        points = np.array(points)

        Ts, Ns, Bs = sloan_method(points)
        self._points = points
        self._Ts = Ts
        self._Ns = Ns
        self._Bs = Bs
        self._total_length = np.linalg.norm(points[1:] - points[:-1], axis=1).sum()

        self._railway_line_left = RailwayLineEntity(self._points, self._Ts, self._Ns, self._Bs)

        '''
        Your code starts here.
        Hint: Use B vectors to shift the left railway line to create the right lineway
        '''
        offset = 0.1  # Adjust this value as needed for the spacing between the railway lines
        points_shifted = self._points + offset * np.array(self._Bs)
        self._railway_line_right = RailwayLineEntity(points_shifted, self._Ts, self._Ns, self._Bs)
        '''
        Your code ends here
        '''

        self._railway_line_left.model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        self._railway_line_left.view_transform = pyrr.matrix44.create_identity(dtype=np.float32)

        self._railway_line_right.model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        self._railway_line_right.view_transform = pyrr.matrix44.create_identity(dtype=np.float32)

        self._wooden_tie = WoodenTieEntity(tie_texture_path, texture_unit)

    @property
    def total_length(self):
        return self._total_length

    def _update_projection_transform(self, projection_transform):
        self._railway_line_left.projection_transform = projection_transform
        self._railway_line_right.projection_transform = projection_transform

    def _update_view_transform(self, view_transform):
        self._railway_line_left.view_transform = view_transform
        self._railway_line_right.view_transform = view_transform

    def draw(self):
        '''
            Draw method. Your task here is to draw the wooden ties.

            Hints:
                - Uniformly spacing them along the railway.
                - Just create a single wooden tie and draw it multiple times along the railway, just like when you draw the world box.
        '''
        self._railway_line_left.draw()
        self._railway_line_right.draw()

        '''
        Your code starts here
        '''
        tie_spacing = 5.0
        num_ties = int(self._total_length // tie_spacing)

        for i in range(num_ties):
            t = i / num_ties
            position = self._points[int(t * len(self._points))]

            model_transform = pyrr.matrix44.create_from_translation(position, dtype=np.float32)
            self._wooden_tie.model_transform = model_transform
            self._wooden_tie.draw()
        '''
        Your code ends here
        '''

    def get_camera_along_railway(self, t):
        '''
        Calculate the camera extrinsics along the railway. This method is called in the app to change the view points along the railway.

        Hint:
            - You just need to calculate the eye, lookat, and up vectors and then use the pyrr create_look_at method to create the view matrix.
            - The eye can be calculate by self._points, self._Ts, and self._Bs. The eye should be between the two railway lines and a bit above them.
            - The lookat position can be calculated from the eye position and self._Ts.
            - Up vector is easy. You should figure it yourself.

        Parameters:
            - t: The normalized position on the railway.
        Returns:
            - view_matrix: The view matrix at the position t.
        '''
        assert t >= 0 and t <= 1

        # eye = np.array([0, 0, 0], dtype=np.float32)
        # lookat = np.array([0, 0, 1], dtype=np.float32)
        # up = np.array([0, 1, 0], dtype=np.float32)

        '''
        Your code starts here
        '''
        index = int(t * (len(self._points) - 1))

        eye = self._points[index] + 1.0 * self._Bs[index] + np.array([0, 2.0, 0])  # Place above track
        lookat = eye + self._Ts[index]  # Look forward along the track
        up = self._Ns[index]  # Up direction
        '''
        Your code ends here
        '''
    
        view_matrix = pyrr.matrix44.create_look_at(eye, lookat, up)
        return view_matrix

    def destroy(self):
        self._railway_line_left.destroy()
        self._railway_line_right.destroy()
        self._wooden_tie.destroy()
