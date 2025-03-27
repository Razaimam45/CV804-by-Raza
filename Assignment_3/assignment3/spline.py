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


import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import seaborn as sns
import numpy as np
from numpy.typing import NDArray
from typing import List, Tuple


ORI_VIS_LEN = 4.0


class Spline:
    def __init__(self, points):
        assert len(points) >= 4

        points = np.array(points)

        # Padding the first and last control points
        self._points = np.zeros([points.shape[0] + 2, 3])
        self._points[1: -1, :] = points
        self._points[0] = points[0]
        self._points[-1] = points[-1]

        self._num_points = self._points.shape[0]
        self._segment_lengths = np.zeros(self._num_points - 1)
        for i in range(self._num_points - 1):
            self._segment_lengths[i] = np.sqrt(((self._points[i + 1] - self._points[i]) ** 2).sum())

        self._total_length = np.sum(self._segment_lengths)

    @staticmethod
    def _catmull_rom(points: NDArray[np.float32], t: float) -> NDArray[np.float32]:
        """
        Calculate the position of a Catmull-Rom spline for a given parameter t.
        This method assumes there are exactly 4 control points.

        Args:
            points (NDArray[np.float32]): Array of 4 control points.
            t (float): Parameter between 0 and 1.

        Returns:
            NDArray[np.float32]: The calculated position on the spline.
        """
        assert points.shape[0] == 4
        assert 0 <= t <= 1

        t2 = t * t
        t3 = t2 * t

        p0, p1, p2, p3 = points  # Extract the four control points

        # Catmull-Rom spline basis matrix coefficients
        q = (0.5 * (
            (2 * p1) +
            (-p0 + p2) * t +
            (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
            (-p0 + 3 * p1 - 3 * p2 + p3) * t3
        ))

        return q.astype(np.float32)


    def __call__(self, t: float) -> NDArray[np.float32]:
        """
        Calculate the position of a Catmull-Rom spline for a given parameter t.
        This method handles the general case with more than 4 control points.

        Args:
            t (float): Parameter between 0 and 1.

        Returns:
            NDArray[np.float32]: The calculated position on the spline.
        """
        assert 0 <= t <= 1

        # Find which segment the parameter `t` belongs to
        total_length = self._total_length * t
        accumulated_length = 0

        for i in range(self._num_points - 3):  # Only valid for interior control points
            if accumulated_length + self._segment_lengths[i] >= total_length:
                if self._segment_lengths[i] != 0:
                    local_t = (total_length - accumulated_length) / self._segment_lengths[i]
                else:
                    local_t = 0
                return self._catmull_rom(self._points[i:i + 4], local_t)
            accumulated_length += self._segment_lengths[i]

        # Fallback (numerical precision issues)
        return self._points[-2]


def sloan_method(
    points: NDArray[np.float32]
) -> Tuple[List[NDArray[np.float32]], List[NDArray[np.float32]], List[NDArray[np.float32]]]:
    """
    Calculate the TNB (Tangent, Normal, Binormal) frames for a given set of points.

    Args:
        points (NDArray[np.float32]): Array of points representing the spline.

    Returns:
        Tuple[List[NDArray[np.float32]], List[NDArray[np.float32]], List[NDArray[np.float32]]]:
        Lists of Tangent, Normal, and Binormal vectors for each point.
    """
    n = len(points)
    Ts, Ns, Bs = [], [], []

    for i in range(n - 1):
        if i == 0:
            T = points[i + 1] - points[i]
            T /= np.linalg.norm(T)  # Normalize T
            B = np.array([0, 0, 1], dtype=np.float32)  # Initial binormal (arbitrary)
            N = np.cross(B, T)
            N /= np.linalg.norm(N)  # Normalize N
            B = np.cross(T, N)  # Recompute B for orthogonality
        else:
            T = points[i + 1] - points[i]
            T /= np.linalg.norm(T)  # Normalize T
            B = np.cross(Ts[-1], N)  # Update B
            B /= np.linalg.norm(B)
            N = np.cross(B, T)  # Update N
            N /= np.linalg.norm(N)

        Ts.append(T)
        Ns.append(N)
        Bs.append(B)

    # Append last frame
    Ts.append(Ts[-1])
    Ns.append(Ns[-1])
    Bs.append(Bs[-1])

    return Ts, Ns, Bs


def animate(frame_idx, particle, orientation_lines, x_railroad, y_railroad, z_railroad, Ts, Ns, Bs):
    p = np.array([x_railroad[frame_idx], y_railroad[frame_idx], z_railroad[frame_idx]])
    T = Ts[frame_idx]
    N = Ns[frame_idx]
    B = Bs[frame_idx]

    assert np.isclose(np.linalg.norm(T), 1 + 1e-6)
    assert np.isclose(np.linalg.norm(B), 1 + 1e-6)
    assert np.isclose(np.linalg.norm(N), 1 + 1e-6)

    # Update particle's position
    particle.set_data(p[0: 1], p[1: 2])
    particle.set_3d_properties(p[2: 3])

    # Update particle's orientations
    for i, vec in enumerate([T, N, B]):
        orientation_lines[i].set_data(
            [p[0], p[0] + ORI_VIS_LEN * vec[0]],
            [p[1], p[1] + ORI_VIS_LEN * vec[1]]
        )
        orientation_lines[i].set_3d_properties([p[2], p[2] + ORI_VIS_LEN * vec[2]])

    return [particle,] + orientation_lines


if __name__ == '__main__':
    with open('assets/spline_data/goodRide.sp', 'r') as f:
        f.readline()
        points = [list(map(float, line.split(' '))) for line in f]

    spline = Spline(points)

    # Set Seaborn style
    sns.set_theme(style="whitegrid")

    # Create figure and axis
    fig = plt.figure()
    ax = plt.subplot(111, projection='3d')

    # Plot the railroad
    x_railroad, y_railroad, z_railroad = [], [], []
    for t in np.linspace(0, 0.99, 1000):  # Only go to 0.99 to avoid numerical issue
        p = spline(t)
        x_railroad.append(p[0])
        y_railroad.append(p[1])
        z_railroad.append(p[2])
    ax.plot(x_railroad, y_railroad, z_railroad)

    # Prepare the particle and the orientations
    particle, = ax.plot([x_railroad[0]], [y_railroad[0]], [z_railroad[0]], 'ro') # 'ro' creates a red circle marker

    # Generate the orientations
    [Ts, Ns, Bs] = sloan_method(np.stack((x_railroad, y_railroad, z_railroad), axis=1))

    orientation_colors = ['r', 'g', 'b']
    orientation_lines = []
    for i, ori in enumerate([Ts[0], Ns[0], Bs[0]]):
        line, = ax.plot(
            [x_railroad[0], x_railroad[0] + ORI_VIS_LEN * ori[0]],
            [y_railroad[0], y_railroad[0] + ORI_VIS_LEN * ori[1]],
            [z_railroad[0], z_railroad[0] + ORI_VIS_LEN * ori[2]],
            color=orientation_colors[i]
        )
        orientation_lines.append(line)

    # Animate the car
    num_frames = 1000
    speed = 4
    ani = FuncAnimation(
        fig,
        lambda frame: animate(
            frame, particle, orientation_lines, x_railroad, y_railroad, z_railroad, Ts, Ns, Bs
        ),
        frames=np.arange(0, num_frames - 1, 4),
        blit=False
    )

    # Show plot
    plt.show()