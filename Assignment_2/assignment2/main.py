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

import click
from app import ValenceApp

# mesh_path = "D:/MBZUAI 2022-2027/MBZUAI 2024-2027/Semester 2/CV804/Exercise 1/CV804-2025-Spring-Semester-Starter-Code/assignment2/data/space_shuttle.off"
vertex_shader_path = "D:/MBZUAI 2022-2027/MBZUAI 2024-2027/Semester 2/CV804/Exercise 1/CV804-2025-Spring-Semester-Starter-Code/assignment2/shaders/basic_transformation.vert"
fragment_shader_path = "D:/MBZUAI 2022-2027/MBZUAI 2024-2027/Semester 2/CV804/Exercise 1/CV804-2025-Spring-Semester-Starter-Code/assignment2/shaders/basic_color.frag"
@click.command()
# @click.option('--mesh_path', type=str, default=mesh_path, help='Mesh path')
@click.option('--window_width', type=int, default=1360, help='Window width')
@click.option('--window_height', type=int, default=1024, help='Window height')
def main(window_width, window_height):
    app = ValenceApp(width=window_width, height=window_height, 
                     vertex_shader_path=vertex_shader_path, fragment_shader_path=fragment_shader_path)
    app.run()

if __name__ == '__main__':
    main()