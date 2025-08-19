import matplotlib
import numpy as np
import pyvista as pv

from NeuXtalViz.config.atoms import colors, radii


class PlannerPlotter:
    def __init__(self, pv_plotter):
        self.pv_plotter = pv_plotter

    def reset_view(self):
        """
        Reset the view.

        """

        self.pv_plotter.reset_camera()
        self.pv_plotter.view_isometric()

    def add_peaks(self, peak_dict):
        self.pv_plotter.clear_actors()

        coords = np.array(peak_dict["coords"])
        colors = np.array(peak_dict["colors"])
        # sizes = np.array(peak_dict['sizes'])

        points = pv.PolyData(coords)
        points["colors"] = colors
        # points['sizes'] = 5*sizes

        self.pv_plotter.add_mesh(
            points,
            scalars="colors",
            rgb=True,
            smooth_shading=True,
            point_size=10,
            render_points_as_spheres=True,
        )

        self.pv_plotter.enable_depth_peeling()

        coords = np.array(peak_dict["axis_coords"])
        colors = np.array(peak_dict["axis_colors"])

        for i in range(3):
            arrow = pv.Arrow([0, 0, 0], coords[i], scale="auto")
            self.pv_plotter.add_mesh(arrow, color=colors[i], smooth_shading=True)

        radius = 0.2 * np.sqrt(np.min(np.sum(coords**2, axis=1)))
        sphere = pv.Sphere(radius=radius)

        self.pv_plotter.add_mesh(sphere, color="w", smooth_shading=True)

        Q_max = 2 * np.pi / peak_dict["axis_limit"]

        mesh = pv.Line(
            pointa=(-Q_max, 0, 0), pointb=(Q_max, 0, 0), resolution=1
        )

        self.pv_plotter.add_mesh(
            mesh, color="k", style="wireframe", render_lines_as_tubes=True
        )

        mesh = pv.Line(
            pointa=(0, -Q_max, 0), pointb=(0, Q_max, 0), resolution=1
        )

        self.pv_plotter.add_mesh(
            mesh, color="k", style="wireframe", render_lines_as_tubes=True
        )

        mesh = pv.Line(
            pointa=(0, 0, -Q_max), pointb=(0, 0, Q_max), resolution=1
        )

        self.pv_plotter.add_mesh(
            mesh, color="k", style="wireframe", render_lines_as_tubes=True
        )

        self.reset_view()