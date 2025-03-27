'''
                                                 
   Code framework for the lecture

   "CV804: 3D Geometry Processing"

   Lecturer: Hao Li
   TAs: Phong Tran, Long Nhat Ho

   Copyright (C) 2025 by Metaverse Lab, MBZUAI
                                                                         
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
   Boston, MA 02110-1301, USA.
'''

# Importing necessary libraries for OpenGL rendering, window management, and matrix operations
from enum import Enum
import glfw
import numpy as np
from numpy.typing import NDArray
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from height_map import HeightMap
import tkinter as tk
from tkinter import filedialog


# Enum for controlling the mode of interaction with the scene
class ControlState(Enum):
    TRANSLATE = 0  # Translation of the object
    ROTATE = 1     # Rotation of the object
    IDLE = 2       # No transformation
    SCALE = 3      # Scaling of the object


# Enum for drawing modes
class DrawingMode(Enum):
    POINT = 0      # Points for object representation
    TRIANGLE = 1   # Full object as triangles
    WIREFRAME = 2  # Object in wireframe

    def next(self):
        # Returns the next drawing mode in the cycle
        members = list(type(self))
        index = (members.index(self) + 1) % len(members)
        return members[index]


# Main class for handling the height map application
class HeightMapApp:
    def __init__(self, window_width: int, window_height: int, 
                 vertex_shader_path: str, fragment_shader_path: str):
        '''
        Initialize the application and create the window.

        Args:
            window_width: Width of the window
            window_height: Height of the window
            vertex_shader_path: Path to the vertex shader file
            fragment_shader_path: Path to the fragment shader file
        '''
        # Initialize control states and transformations
        self._control_state: ControlState = ControlState.IDLE
        self._drawing_mode: DrawingMode = DrawingMode.TRIANGLE
        self._cursor_pos: NDArray[np.float32] = np.array([0., 0.], dtype=np.float32)
        self._rotate_value: NDArray[np.float32] = np.array([0., 0.], dtype=np.float32)
        self._translate_value: NDArray[np.float32] = np.array([0., 0.], dtype=np.float32)
        self._scale_value: float = 1.
        
        # Get the height map path using a file dialog
        height_map_path = self._get_map_path()

        # Initialize window, shaders, and height map
        self._create_window(window_width, window_height)
        self._height_map = HeightMap(height_map_path)
        # self._height_map_scale = 1.0
        
        # Create shaders and initialize the projection transformation
        self._shader_program = self._create_shader(vertex_shader_path, fragment_shader_path)
        self._init_projection_transform(window_width, window_height)

    def _get_map_path(self):
        """
        Opens a file dialog for the user to select the height map file.

        Returns:
            str: Path to the selected height map file
        """
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(
            title="Select Height Map File",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*")]
        )
        return file_path
    
    @staticmethod
    def _create_shader(vertex_shader_path: str, fragment_shader_path: str) -> int:
        """
        Create an OpenGL shader program.

        Args:
            vertex_shader_path: Path to the vertex shader file
            fragment_shader_path: Path to the fragment shader file

        Returns:
            int: The OpenGL shader program handle
        """
        # Read shader code from the given files
        with open(vertex_shader_path, 'r') as vs_file:
            vertex_shader_code = vs_file.read()
        with open(fragment_shader_path, 'r') as fs_file:
            fragment_shader_code = fs_file.read()

        # Compile the shaders and create the shader program
        vertex_shader = compileShader(vertex_shader_code, GL_VERTEX_SHADER)
        fragment_shader = compileShader(fragment_shader_code, GL_FRAGMENT_SHADER)
        shader_program = compileProgram(vertex_shader, fragment_shader)

        return shader_program

    def run(self):
        """Start the main rendering loop."""
        self._main_loop()

    def _init_projection_transform(self, window_width: int, window_height: int):
        """
        Initializes the projection and view matrices and sends them to the shader program.

        Args:
            window_width: Width of the window
            window_height: Height of the window
        """
        # Create a perspective projection matrix
        self._projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy=45,
            aspect=window_width / window_height,
            near=0.1,
            far=100,
            dtype=np.float32
        )

        # Create a view matrix for the camera
        self._view_transform = pyrr.matrix44.create_look_at(
            eye=np.array([0, 2, 5], dtype=np.float32),
            target=np.array([0, 0, 0], dtype=np.float32),
            up=np.array([0, 1, 0], dtype=np.float32),
            dtype=np.float32
        )

        glUseProgram(self._shader_program)

        # Send the projection and view matrices to the shader
        proj_location = glGetUniformLocation(self._shader_program, 'projection')
        glUniformMatrix4fv(proj_location, 1, GL_FALSE, self._projection_transform)

        view_location = glGetUniformLocation(self._shader_program, 'view')
        glUniformMatrix4fv(view_location, 1, GL_FALSE, self._view_transform)

    def _create_window(self, window_width: int, window_height: int):
        """
        Creates a window using GLFW and sets up OpenGL context.

        Args:
            window_width: Width of the window
            window_height: Height of the window
        """
        if not glfw.init():
            print("Failed to initialize GLFW")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        # Create the window and set OpenGL context
        self.window = glfw.create_window(window_width, window_height, "Height Map Visualization", None, None)
        if not self.window:
            print("Failed to create GLFW window")
            glfw.terminate()
            return

        glfw.make_context_current(self.window)

        # Enable depth testing and set background color
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glClearColor(0.0, 0.0, 0.0, 1.0)

        # Set GLFW callbacks for mouse and keyboard events
        glfw.set_mouse_button_callback(self.window, self._mouse_button_callback)
        glfw.set_cursor_pos_callback(self.window, self._cursor_pos_callback)
        glfw.set_scroll_callback(self.window, self._scroll_callback)
        glfw.set_key_callback(self.window, self._keyboard_callback)

    def _cursor_pos_callback(self, window: glfw._GLFWwindow, x: float, y: float):
        """
        Handles mouse cursor position changes and applies transformations accordingly.

        Args:
            window: The GLFW window instance
            x: X position of the cursor
            y: Y position of the cursor
        """
        new_cursor_pos = np.array([x, y], dtype=np.float32)
        cursor_delta = new_cursor_pos - self._cursor_pos
        self._cursor_pos = new_cursor_pos
        rotation_sensitivity = 0.025

        # Apply transformation based on control state
        match self._control_state:
            case ControlState.TRANSLATE:
                cursor_delta[1] *= -1
                self._translate_value += cursor_delta * 0.01
            case ControlState.ROTATE:
                self._rotate_value += cursor_delta * rotation_sensitivity
            case ControlState.SCALE:
                pass  # No scaling when cursor moves
            case ControlState.IDLE:
                pass

        self._update_modelview_transform()

    def _mouse_button_callback(self, window: glfw._GLFWwindow, button: int, action: int, mods: int):
        """
        Handles mouse button press/release events.

        Args:
            window: The GLFW window instance
            button: The mouse button (left or right)
            action: The action (press or release)
            mods: Modifier keys pressed
        """
        match button:
            case glfw.MOUSE_BUTTON_LEFT:
                if action == glfw.PRESS:
                    self._control_state = ControlState.ROTATE
                elif action == glfw.RELEASE:
                    self._control_state = ControlState.IDLE
            case glfw.MOUSE_BUTTON_RIGHT:
                if action == glfw.PRESS:
                    self._control_state = ControlState.TRANSLATE
                elif action == glfw.RELEASE:
                    self._control_state = ControlState.IDLE

    def _scroll_callback(self, window: glfw._GLFWwindow, xoffset: float, yoffset: float):
        """
        Handles mouse scroll events for scaling the height map.

        Args:
            window: The GLFW window instance
            xoffset: The horizontal scroll offset
            yoffset: The vertical scroll offset
        """
        self._scale_value *= (1 - yoffset * 0.01)
        self._update_modelview_transform()

    def _keyboard_callback(self, window: glfw._GLFWwindow, key, scancode, action, mods):
        """
        Handles keyboard events for changing drawing modes.

        Args:
            window: The GLFW window instance
            key: The key pressed
            scancode: The scancode of the key
            action: The action (press or release)
            mods: Modifier keys pressed
        """
        if action == glfw.PRESS:
            if key == glfw.KEY_W:
                self._drawing_mode = self._drawing_mode.next()
            if key == glfw.KEY_UP:  # Scale up when the Up arrow key is pressed
                height_map_scale = 1.1  # Increase scale by 10%
                # print(f"Height map scale increased: {height_map_scale}")
                self._height_map.apply_scale(height_map_scale)
                # Update modelview after scaling
                self._update_modelview_transform()

            elif key == glfw.KEY_DOWN:  # Scale down when the Down arrow key is pressed
                # if self._height_map_scale > 0.01:  # Ensure we don't scale too small
                height_map_scale = 0.9  # Decrease scale by 10%
                # print(f"Height map scale decreased: {height_map_scale}")
                self._height_map.apply_scale(height_map_scale)
                # Update modelview after scaling
                self._update_modelview_transform()
                # else:
                #     print("Scale is already too small to decrease further.")

    def _update_modelview_transform(self):
        """
        Updates the model transformation matrix for the height map and sends it to the shader.
        """
        # Update the model transformation with translation, rotation, and scale
        self._height_map.update_model_transform(
            self._translate_value,
            self._rotate_value,
            self._scale_value
        )

        glUseProgram(self._shader_program)

        # Send the modelview matrix to the shader
        modelview_location = glGetUniformLocation(self._shader_program, 'modelview')
        glUniformMatrix4fv(modelview_location, 1, GL_FALSE, self._height_map.get_model_transform())

    def _main_loop(self):
        """
        Main loop to draw the height map and handle user interactions.

        Steps:
            - Clear the buffers
            - Use the shader program
            - Draw the height map
            - Swap buffers and poll events
        """
        while not glfw.window_should_close(self.window):
            # Set drawing mode (point, triangle, or wireframe)
            gl_drawing_mode = GL_POINT
            match self._drawing_mode:
                case DrawingMode.TRIANGLE:
                    gl_drawing_mode = GL_FILL
                case DrawingMode.WIREFRAME:
                    gl_drawing_mode = GL_LINE
                case _:
                    gl_drawing_mode = GL_POINT
            glPolygonMode(GL_FRONT_AND_BACK, gl_drawing_mode)

            # Clear screen and depth buffer
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(self._shader_program)

            # Draw the height map
            self._height_map.draw()

            # Swap buffers and handle events
            glfw.swap_buffers(self.window)
            glfw.poll_events()

        glFinish()
        # Clean up and close the application
        self.quit()

    def quit(self):
        """Clean up resources and terminate the application."""
        self._height_map.destroy()
        glDeleteProgram(self._shader_program)
