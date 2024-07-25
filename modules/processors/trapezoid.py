from scipy.spatial import ConvexHull
from math import atan, sin, cos, sqrt
from typing import List


def non_zero(x):
    if x == 0:
        x = 0.00001
    return x


def find_deviation(prev, vert, next):
    delta_prev_x = next[0] - prev[0]
    delta_vert_x = next[0] - vert[0]
    delta_prev_y = non_zero(next[1] - prev[1])
    delta_vert_y = non_zero(next[1] - vert[1])

    angle_a = atan(delta_vert_x / delta_vert_y)
    angle_b = atan(delta_prev_x / delta_prev_y)
    angle_o = angle_b - angle_a
    x = sqrt((delta_vert_x**2) + (delta_vert_y**2))

    return abs(sin(angle_o) * x)


def remove_least_deviation(vertices: List):
    padded = [vertices[-1]] + [v for v in vertices] + [vertices[0]]

    deviations = []
    for i in range(1, len(vertices) + 1):
        deviations.append((i - 1, find_deviation(padded[i - 1], padded[i], padded[i + 1])))

    min_dev = min(deviations, key=lambda e: e[1])
    vertices.pop(min_dev[0])

    return vertices


# Function to find minimum area trapezoid
def find_best_fit_trapezoid(points):
    # Calculate convex hull
    hull = ConvexHull(points)
    hull_vertices = [points[vertex] for vertex in hull.vertices]

    while len(hull_vertices) > 4:
        remove_least_deviation(hull_vertices)

    return hull_vertices
