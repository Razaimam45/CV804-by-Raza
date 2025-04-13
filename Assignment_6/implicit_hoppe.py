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
import numpy.typing as npt

class ImplicitHoppe:
    def __init__(self, points: npt.NDArray[np.float32], normals: npt.NDArray[np.float32]) -> None:
        self._points = points  # shape: (M,3)
        self._normals = normals  # shape: (M,3)

    def __call__(self, P: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        '''
        Calculating the signed distances of the input batched points P using the implicit Hoppe algorithm.
        The algorithm works by finding for each point in P the closest sample point (from self._points)
        and then computing the signed distance to the tangent plane defined by that sample point and its normal.
        The entire process is vectorized.

        Parameters:
            - P (NDArray[float32]): input points of shape (N,3).
        Returns:
            - dist (NDArray[float32]): signed distance values with shape (N,).
        '''

        # 1) Find the closest sample point for each point in P.
        #    We subtract sample points from each input point (broadcasting),
        #    compute the Euclidean distances, and determine the index of the smallest distance.
        #    This is computed without any Python loops.
        diff = P[:, None, :] - self._points[None, :, :]          # Shape: (N, M, 3)
        distances = np.linalg.norm(diff, axis=2)                   # Shape: (N, M)
        closest_indices = np.argmin(distances, axis=1)             # Shape: (N,)

        # 2) Compute distance to the corresponding tangent plane.
        #    For each point in P, get the corresponding closest sample point and its normal.
        #    Compute the dot product of the normal with the vector (P - closest_point)
        #    and divide by the norm of the normal.
        closest_points = self._points[closest_indices]             # Shape: (N, 3)
        closest_normals = self._normals[closest_indices]             # Shape: (N, 3)
        
        delta = P - closest_points                                 # Shape: (N, 3)
        dot_products = np.sum(closest_normals * delta, axis=1)       # Shape: (N,)
        normal_norms = np.linalg.norm(closest_normals, axis=1)       # Shape: (N,)

        # Avoid division by zero in case any normal is a zero-vector (though that should not happen)
        normal_norms = np.where(normal_norms == 0, 1, normal_norms)
        signed_distances = dot_products / normal_norms             # Shape: (N,)

        return signed_distances.astype(np.float32)


