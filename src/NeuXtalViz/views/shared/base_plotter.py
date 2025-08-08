import numpy as np
import pyvista as pv


class BasePlotter:
    def __init__(self, pv_plotter):
        self.pv_plotter = pv_plotter
        self.camera_position = None
        self.pv_plotter.enable_parallel_projection()

    def change_projection(self, enable):
        """
        Enable or disable parallel projection.

        """
        if enable:
            self.pv_plotter.enable_parallel_projection()
        else:
            self.pv_plotter.disable_parallel_projection()

    def reset_view(self, negative=False):
        """
        Reset the view.

        """

        self.pv_plotter.reset_camera()
        self.pv_plotter.view_isometric(negative=negative)
        self.camera_position = self.pv_plotter.camera_position

    def reset_camera(self):
        """
        Reset the camera.

        """

        self.pv_plotter.reset_camera()

    def clear_scene(self):
        self.pv_plotter.clear_plane_widgets()
        self.pv_plotter.clear_actors()

        if self.camera_position is not None:
            self.camera_position = self.pv_plotter.camera_position

    def reset_scene(self):
        if self.camera_position is not None:
            self.pv_plotter.camera_position = self.camera_position
        else:
            self.reset_view()

    def save_screenshot(self, filename):
        """
        Save plotter screenshot.

        Parameters
        ----------
        filename : str
            Filename with *.png extension.

        """
        if filename:
            self.pv_plotter.screenshot(filename)

    def show_axes(self, data):
        T, reciprocal_lattice, show_axes = data

        if not show_axes:
            self.pv_plotter.hide_axes()
        elif T is not None:
            t = pv._vtk.vtkMatrix4x4()
            for i in range(3):
                for j in range(3):
                    t.SetElement(i, j, T[i, j])
            if reciprocal_lattice:
                actor = self.pv_plotter.add_axes(xlabel="a*", ylabel="b*", zlabel="c*")
            else:
                actor = self.pv_plotter.add_axes(xlabel="a", ylabel="b", zlabel="c")
            actor.SetUserMatrix(t)

    def view_vector(self, vecs):
        """
        Set the camera according to given vector(s).

        Parameters
        ----------
        vecs : list of 2 or single 3 element 1d array-like
            Camera direction and optional upward vector.

        """

        if len(vecs) == 2:
            vec = np.cross(vecs[0], vecs[1])
            self.pv_plotter.view_vector(vecs[0], vec)
        else:
            self.pv_plotter.view_vector(vecs)

    def view_up_vector(self, vec):
        """
        Set the camera according to given vector(s).

        Parameters
        ----------
        vec : 3 element 1d array-like
            Camera up direction and optional upward vector.

        """

        self.pv_plotter.set_viewup(vec)

    def view_xy(self):
        """
        View :math:`xy`-plane.

        """

        self.pv_plotter.view_xy()

    def view_yz(self):
        """
        View :math:`yz`-plane.

        """

        self.pv_plotter.view_yz()

    def view_zx(self):
        """
        View :math:`zx`-plane.

        """

        self.pv_plotter.view_zx()

    def view_yx(self):
        """
        View :math:`yx`-plane.

        """

        self.pv_plotter.view_yx()

    def view_zy(self):
        """
        View :math:`zy`-plane.

        """

        self.pv_plotter.view_zy()

    def view_xz(self):
        """
        View :math:`xz`-plane.

        """

        self.pv_plotter.view_xz()

    def set_position(self, pos):
        """
        Set the position.

        Parameters
        ----------
        pos : 3-element 1d array-like
            Coordinate position.

        """

        self.pv_plotter.set_position(pos, reset=True)
