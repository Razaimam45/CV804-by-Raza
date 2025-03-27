//=============================================================================
//                                                
//   Code framework for the lecture
//
//   "CV804: 3D Geometry Processing"
//
//   Lecturer: Hao Li
//   TAs: Phong Tran, Long Nhat Ho, Ekaterina Radionova
//
//   Copyright (C) 2025 Metaverse Lab
//                                                                         
//-----------------------------------------------------------------------------
//                                                                            
//                                License                                     
//                                                                            
//   This program is free software; you can redistribute it and/or
//   modify it under the terms of the GNU General Public License
//   as published by the Free Software Foundation; either version 2
//   of the License, or (at your option) any later version.
//   
//   This program is distributed in the hope that it will be useful,
//   but WITHOUT ANY WARRANTY; without even the implied warranty of
//   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//   GNU General Public License for more details.
//   
//   You should have received a copy of the GNU General Public License
//   along with this program; if not, write to the Free Software
//   Foundation, Inc., 51 Franklin Street, Fifth Floor, 
//   Boston, MA  02110-1301, USA.
//                                                                            
//=============================================================================
//=============================================================================

#version 330 core

layout(location = 0) in vec3 aPos;     // Vertex position
layout(location = 1) in vec3 aNormal;  // Vertex normal
layout(location = 2) in vec2 aTexCoord; // Texture coordinates

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 FragPos;   // Fragment position
out vec3 Normal;    // Normal vector for lighting
out vec2 TexCoord;  // Texture coordinates

void main()
{
    FragPos = vec3(model * vec4(aPos, 1.0));  
    Normal = mat3(transpose(inverse(model))) * aNormal;  
    TexCoord = aTexCoord;

    gl_Position = projection * view * vec4(FragPos, 1.0);
}