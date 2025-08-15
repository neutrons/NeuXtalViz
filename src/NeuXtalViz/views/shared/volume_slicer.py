from matplotlib.transforms import Affine2D
import numpy as np
import pyvista as pv

from NeuXtalViz.view_models.volume_slicer import VolumeSlicerViewModel


class VolumeSlicerPlotter:
    def __init__(
        self,
        view_model: VolumeSlicerViewModel,
        pv_plotter,
        fig_slice,
        slice_callback,
        fig_cut,
        cut_callback,
    ):
        self.view_model = view_model
        self.pv_plotter = pv_plotter

        self.fig_slice = fig_slice
        self.slice_callback = slice_callback
        self.ax_slice = self.fig_slice.subplots(1, 1)
        self.cb = None

        self.cut_callback = cut_callback
        self.fig_cut = fig_cut
        self.ax_cut = self.fig_cut.subplots(1, 1)

    def __format_axis_coord(self, x, y):
        x, y, _ = np.dot(self.T_inv, [x, y, 1])
        return "x={:.3f}, y={:.3f}".format(x, y)

    def add_cut(self, result):
        cut_dict, show, line_cut, scale, thick = result

        x = cut_dict["x"]
        y = cut_dict["y"]
        e = cut_dict["e"]

        val = cut_dict["value"]

        label = cut_dict["label"]
        title = cut_dict["title"]

        lines = self.ax_slice.get_lines()
        for line in lines:
            line.remove()

        xlim = self.xlim
        ylim = self.ylim

        delta = 0 if thick is None else thick / 2

        if line_cut == "Axis 2":
            l0 = [val - delta, val - delta], ylim
            l1 = [val + delta, val + delta], ylim
            direction = "vertical"
        else:
            l0 = xlim, [val - delta, val - delta]
            l1 = xlim, [val + delta, val + delta]
            direction = "horizontal"

        self.l = show

        self.ax_slice.plot(*l0, "w--", lw=1, alpha=self.l, transform=self.transform)
        self.ax_slice.plot(*l1, "w--", lw=1, alpha=self.l, transform=self.transform)

        self.ax_cut.clear()

        self.ax_cut.errorbar(x, y, e)
        self.ax_cut.set_xlabel(label)
        self.ax_cut.set_yscale(scale)
        self.ax_cut.set_title(title)
        self.ax_cut.minorticks_on()

        self.ax_cut.xaxis.get_major_locator().set_params(integer=True)

        self.cut_callback()
        self.slice_callback()

        self.linecut = {
            "is_dragging": False,
            "line_cut": (xlim, ylim, delta, direction),
        }

        self.fig_slice.canvas.mpl_connect("button_press_event", self.on_press)
        self.fig_slice.canvas.mpl_connect("button_release_event", self.on_release)
        self.fig_slice.canvas.mpl_connect("motion_notify_event", self.on_motion)

    def add_histo(self, result):
        """
        Plots the volume slicer.
        """
        histo_dict, normal, norm, value, opacity, log_scale, cmap = result

        self.clear_scene()

        origin = norm
        origin[origin.index(1)] = value

        signal = histo_dict["signal"]
        labels = histo_dict["labels"]

        min_lim = histo_dict["min_lim"]
        max_lim = histo_dict["max_lim"]
        spacing = histo_dict["spacing"]

        P = histo_dict["projection"]
        T = histo_dict["transform"]
        S = histo_dict["scales"]

        grid = pv.ImageData()
        grid.dimensions = np.array(signal.shape) + 1

        grid.origin = min_lim
        grid.spacing = spacing

        min_bnd = min_lim * S
        max_bnd = max_lim * S

        bounds = np.array([[min_bnd[i], max_bnd[i]] for i in [0, 1, 2]])
        limits = np.array([[min_lim[i], max_lim[i]] for i in [0, 1, 2]])

        a = pv._vtk.vtkMatrix3x3()
        b = pv._vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                a.SetElement(i, j, T[i, j])
                b.SetElement(i, j, P[i, j])

        grid.cell_data["scalars"] = signal.flatten(order="F")

        normal /= np.linalg.norm(normal)

        origin = np.dot(P, origin)

        clim = [np.nanmin(signal), np.nanmax(signal)]

        if not np.all(np.isfinite(clim)):
            clim = [0.1, 10]

        self.clip = self.pv_plotter.add_volume_clip_plane(
            grid,
            opacity=opacity,
            log_scale=log_scale,
            clim=clim,
            normal=normal,
            origin=origin,
            origin_translation=False,
            show_scalar_bar=False,
            normal_rotation=False,
            cmap=cmap,
            user_matrix=b,
        )

        prop = self.clip.GetOutlineProperty()
        prop.SetOpacity(0)

        prop = self.clip.GetEdgesProperty()
        prop.SetOpacity(0)

        actor = self.pv_plotter.show_grid(
            xtitle=labels[0],
            ytitle=labels[1],
            ztitle=labels[2],
            font_size=8,
            minor_ticks=True,
        )

        actor.SetAxisBaseForX(*T[:, 0])
        actor.SetAxisBaseForY(*T[:, 1])
        actor.SetAxisBaseForZ(*T[:, 2])

        actor.bounds = bounds.ravel()
        actor.SetXAxisRange(limits[0])
        actor.SetYAxisRange(limits[1])
        actor.SetZAxisRange(limits[2])

        axis0_args = *limits[0], actor.n_xlabels, actor.x_label_format
        axis1_args = *limits[1], actor.n_ylabels, actor.y_label_format
        axis2_args = *limits[2], actor.n_zlabels, actor.z_label_format

        axis0_label = pv.plotting.cube_axes_actor.make_axis_labels(*axis0_args)
        axis1_label = pv.plotting.cube_axes_actor.make_axis_labels(*axis1_args)
        axis2_label = pv.plotting.cube_axes_actor.make_axis_labels(*axis2_args)

        actor.SetAxisLabels(0, axis0_label)
        actor.SetAxisLabels(1, axis1_label)
        actor.SetAxisLabels(2, axis2_label)

        self.reset_view()

        self.clip.AddObserver("InteractionEvent", self.view_model.interaction_callback)

    def add_slice(self, result):
        slice_dict, cmap, scale = result

        x = slice_dict["x"]
        y = slice_dict["y"]

        labels = slice_dict["labels"]
        title = slice_dict["title"]
        signal = slice_dict["signal"]

        vmin = np.nanmin(signal)
        vmax = np.nanmax(signal)

        if np.isclose(vmax, vmin) or not np.isfinite([vmin, vmax]).all():
            vmin, vmax = (0.1, 1) if scale == "log" else (0, 1)

        T = slice_dict["transform"]
        aspect = slice_dict["aspect"]

        self.T_inv = np.linalg.inv(T)

        self.ax_slice.format_coord = self.__format_axis_coord

        transform = Affine2D(T) + self.ax_slice.transData
        self.transform = transform

        self.xlim = np.array([x.min(), x.max()])
        self.ylim = np.array([y.min(), y.max()])

        if self.cb is not None:
            self.cb.remove()

        self.ax_slice.clear()
        im = self.ax_slice.pcolormesh(
            x,
            y,
            signal,
            norm=scale,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            shading="flat",
            rasterized=True,
            transform=transform,
        )

        self.im = im
        vmin, vmax = self.im.norm.vmin, self.im.norm.vmax

        self.view_model.set_slice_field("vlims", [vmin, vmax])
        self.view_model.set_slice_field("vmin", vmin)
        self.view_model.set_slice_field("vmin_slider", 0)
        self.view_model.set_slice_field("vmax", vmax)
        self.view_model.set_slice_field("vmax_slider", 100)

        self.view_model.set_slice_field("xmin", self.xlim[0])
        self.view_model.set_slice_field("xmax", self.xlim[1])

        self.view_model.set_slice_field("ymin", self.ylim[0])
        self.view_model.set_slice_field("ymax", self.ylim[1])

        self.ax_slice.set_aspect(aspect)
        self.ax_slice.set_xlabel(labels[0])
        self.ax_slice.set_ylabel(labels[1])
        self.ax_slice.set_title(title)
        self.ax_slice.minorticks_on()

        self.ax_slice.xaxis.get_major_locator().set_params(integer=True)
        self.ax_slice.yaxis.get_major_locator().set_params(integer=True)

        self.cb = self.fig_slice.colorbar(self.im, ax=self.ax_slice)
        self.cb.minorticks_on()

        self.slice_callback()

    def clear_scene(self):
        """
        Clear all actors.
        """
        self.pv_plotter.clear_actors()
        self.pv_plotter.clear_plane_widgets()

    def on_press(self, event):
        if (
            event.inaxes == self.ax_slice
            and self.fig_slice.canvas.toolbar.mode == ""
            and self.l
        ):
            self.linecut["is_dragging"] = True

    def on_release(self, event):
        if self.linecut["is_dragging"]:
            self.linecut["is_dragging"] = False

            self.view_model.update_cut()

    def on_motion(self, event):
        if self.linecut["is_dragging"] and event.inaxes == self.ax_slice:
            lines = self.ax_slice.get_lines()
            for line in lines:
                line.remove()

            xlim, ylim, delta, direction = self.linecut["line_cut"]

            x, y, _ = np.dot(self.T_inv, [event.xdata, event.ydata, 1])

            if direction == "vertical":
                l0 = [x - delta, x - delta], ylim
                l1 = [x + delta, x + delta], ylim
                self.view_model.set_cut_field("value", x, skip_update=True)
            else:
                l0 = xlim, [y - delta, y - delta]
                l1 = xlim, [y + delta, y + delta]
                self.view_model.set_cut_field("value", y, skip_update=True)

            self.ax_slice.plot(*l0, "w--", linewidth=1, transform=self.transform)

            self.ax_slice.plot(*l1, "w--", linewidth=1, transform=self.transform)

            self.slice_callback()

    def reset_view(self):
        """
        Reset the view.
        """

        self.pv_plotter.reset_camera()
        self.pv_plotter.view_isometric()

    def set_cut_lim(self, lim):
        if self.cb is not None:
            self.ax_cut.set_xlim(*lim)

            self.cut_callback()

    def set_slice_lim(self, lims):
        xlim, ylim = lims

        if self.cb is not None:
            xmin, xmax = xlim
            ymin, ymax = ylim
            T = np.linalg.inv(self.T_inv)
            xmin, ymin, _ = np.dot(T, [xmin, ymin, 1])
            xmax, ymax, _ = np.dot(T, [xmax, ymax, 1])
            self.ax_slice.set_xlim(xmin, xmax)
            self.ax_slice.set_ylim(ymin, ymax)

            self.slice_callback()

    def update_colorbar_vlims(self, vlims):
        vmin, vmax = vlims

        if self.cb is not None:
            self.im.set_clim(vmin=vmin, vmax=vmax)
            self.cb.update_normal(self.im)
            self.cb.minorticks_on()

            self.slice_callback()

    def update_lines(self, alpha):
        lines = self.ax_slice.get_lines()
        for line in lines:
            line.set_alpha(alpha)

        self.slice_callback()
