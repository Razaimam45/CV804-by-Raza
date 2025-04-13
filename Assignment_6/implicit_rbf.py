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

class ImplicitRBF:
    def __init__(self, points: npt.NDArray[np.float32], normals: npt.NDArray[np.float32]) -> None:
        # Number of sample points
        N = points.shape[0]

        # 1) Collect constraints (on-surface and off-surface).
        # Compute a small offset epsilon proportional to the bounding box diagonal.
        min_pt = np.min(points, axis=0)
        max_pt = np.max(points, axis=0)
        epsilon = 0.01 * np.linalg.norm(max_pt - min_pt)

        # On-surface constraints: f(p_i) = 0.
        pts_on = points  # shape (N,3)
        # Off-surface constraints:
        pts_pos = points + epsilon * normals  # f(p_i + epsilon * n_i) = +epsilon
        pts_neg = points - epsilon * normals  # f(p_i - epsilon * n_i) = -epsilon

        # Stack the 3 sets of constraints into a single (3N x 3) array.
        X = np.vstack((pts_on, pts_pos, pts_neg))
        # Build the right-hand side vector d of length 3N.
        d = np.hstack((
            np.zeros(N, dtype=np.float32),           # on-surface: 0
            np.full(N, epsilon, dtype=np.float32),     # positive offset: +epsilon
            -np.full(N, epsilon, dtype=np.float32)     # negative offset: -epsilon
        ))

        # 2) Setup matrix M of size (3N, N) using the RBF kernel phi(r) = r^3.
        # We compute the pairwise distances between each constraint point in X (3N,3)
        # and each center (sample point) in points (N,3) vectorized.
        diff = X[:, None, :] - points[None, :, :]      # shape: (3N, N, 3)
        r = np.linalg.norm(diff, axis=2)                # shape: (3N, N)
        M = r ** 3                                      # apply the triharmonic kernel

        # 3) Solve the (over-determined) linear system in a least squares sense.
        self._weights, residuals, rank, s = np.linalg.lstsq(M, d, rcond=None)

        # Save centers (the sample points are the centers of the RBFs) for evaluation.
        self._centers = points

    def __call__(self, P: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        '''
        Evaluate the implicit function at a batch of points P.
        The function is given by:
            f(x) = sum_j weights_j * phi(|| x - center_j ||),
        where phi(r) = r^3.
        
        Parameters:
            - P (NDArray[float32]): Input points, shape (M,3).
        Returns:
            - f (NDArray[float32]): The evaluated function values, shape (M,).
        '''
        # Compute the vectorized pairwise differences between evaluation points P and centers.
        diff = P[:, None, :] - self._centers[None, :, :]  # shape: (M, N, 3)
        # Compute Euclidean norms for each pair.
        r = np.linalg.norm(diff, axis=2)                   # shape: (M, N)
        # Apply the kernel phi(r) = r^3.
        phi = r ** 3                                       # shape: (M, N)
        # Compute the signed distance as a weighted sum of kernel responses.
        f = np.dot(phi, self._weights)                     # shape: (M,)
        return f.astype(np.float32)

