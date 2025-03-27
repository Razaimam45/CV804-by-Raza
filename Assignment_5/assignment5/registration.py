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

import numpy as np
from transformation import Transformation

class Registration:
    def register_point2point(self, src, target):
        """
        Task 3: Implement point-to-point registration.
        Solves for a small rotation (α, β, γ) and translation (tx, ty, tz)
        such that p + skew([α,β,γ]) p + t ≈ q.
        
        """
        n = len(src)
        A = np.zeros((n * 3, 6))  # 3 equations per point, 6 unknowns
        b = np.zeros(n * 3)       # Residuals for x, y, z per point

        for i, (p, q) in enumerate(zip(src, target)):
            # p = [p_x, p_y, p_z], q = [q_x, q_y, q_z]
            p_x, p_y, p_z = p
            q_x, q_y, q_z = q

            base = 3 * i

            # Row 0 (x-equation):  0*α + p_z*β + (-p_y)*γ + 1*t_x + 0*t_y + 0*t_z = q_x - p_x
            A[base + 0, :] = [0,      p_z,   -p_y,  1, 0, 0]
            b[base + 0]    = q_x - p_x

            # Row 1 (y-equation): -p_z*α + 0*β + p_x*γ + 0*t_x + 1*t_y + 0*t_z = q_y - p_y
            A[base + 1, :] = [-p_z,   0,      p_x,   0, 1, 0]
            b[base + 1]    = q_y - p_y

            # Row 2 (z-equation):  p_y*α + (-p_x)*β + 0*γ + 0*t_x + 0*t_y + 1*t_z = q_z - p_z
            A[base + 2, :] = [p_y,   -p_x,    0,     0, 0, 1]
            b[base + 2]    = q_z - p_z

        # Solve the least-squares system A x = b
        x = np.linalg.lstsq(A, b, rcond=None)[0]
        # x[0:3] are the rotation parameters (α, β, γ)
        # x[3:6] are the translation components (tx, ty, tz)
        return Transformation.from_angles_and_translation(x[:3], x[3:])


    def register_point2surface(self, src, target, target_normals):
        """
        Task 4: Implement point-to-plane registration.
        For each source point p, target point q, and target normal n,
        we set up one equation:
        n[0]*(q[0]-p[0]) + n[1]*(q[1]-p[1]) + n[2]*(q[2]-p[2]) = 
        (n[2]*p[1]-n[1]*p[2])*α + (n[0]*p[2]-n[2]*p[0])*β + (n[1]*p[0]-n[0]*p[1])*γ +
        n[0]*t_x + n[1]*t_y + n[2]*t_z.
        We build a linear system A x = b, where x = [α, β, γ, t_x, t_y, t_z].
        """
        n_pts = len(src)
        A = np.zeros((n_pts, 6))  # One equation per correspondence
        b = np.zeros(n_pts)       # Right-hand side

        for i, (p, q, n_vec) in enumerate(zip(src, target, target_normals)):
            # Unpack the source point p and target normal n
            p_x, p_y, p_z = p
            n_x, n_y, n_z = n_vec

            # Set up the rotation part:
            # A[6*i+0] = n[2]*p[1] - n[1]*p[2]
            # A[6*i+1] = n[0]*p[2] - n[2]*p[0]
            # A[6*i+2] = n[1]*p[0] - n[0]*p[1]
            A[i, 0] = n_z * p_y - n_y * p_z
            A[i, 1] = n_x * p_z - n_z * p_x
            A[i, 2] = n_y * p_x - n_x * p_y

            # Set up the translation part using the normal components directly.
            A[i, 3:6] = n_vec  # [n_x, n_y, n_z]

            # Set up the residual (projection of (q-p) onto the normal)
            b[i] = n_x * (q[0] - p_x) + n_y * (q[1] - p_y) + n_z * (q[2] - p_z)

        # Solve the overdetermined system A x = b using least squares.
        x = np.linalg.lstsq(A, b, rcond=None)[0]
        # x[:3] contains the rotation parameters (α, β, γ)
        # x[3:] contains the translation (t_x, t_y, t_z)
        return Transformation.from_angles_and_translation(x[:3], x[3:])

