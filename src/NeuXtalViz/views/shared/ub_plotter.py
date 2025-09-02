import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter
from matplotlib.transforms import Affine2D
from mpl_toolkits.axisartist import Axes, GridHelperCurveLinear
from mpl_toolkits.axisartist.grid_finder import (
    ExtremeFinderSimple,
    MaxNLocator,
)

from NeuXtalViz.view_models.ub_tools import UBViewModel


class UBPlotter:
    def __init__(
        self,
        view_model: UBViewModel,
        pv_plotter: pv.Plotter,
        fig_slice: Figure,
        fig_inst: Figure,
        fig_scan: Figure,
        fig_clust: Figure,
    ):
        self.view_model = view_model
        self.pv_plotter = pv_plotter

        self.fig_slice = fig_slice
        self.ax_slice = self.fig_slice.subplots(1, 1)
        self.fig_inst = fig_inst
        self.ax_inst = self.fig_inst.subplots(1, 1)
        self.fig_scan = fig_scan
        self.ax_scan = self.fig_scan.subplots(1, 1)
        self.fig_clust = fig_clust
        self.ax_clust = self.fig_clust.subplots(3, 1, sharex=True, sharey=True)

        self.ax_xint = None
        self.ax_yint = None
        self.cb_slice = None
        self.cb_inst = None

        self.camera_position = None
        self.last_highlight = None
        self.mapper = None

    def add_Q_viz(self, Q_dict):
        self.clear_scene()

        signal = Q_dict.get("signal")
        spacing = Q_dict.get("spacing")
        min_lim = Q_dict.get("min_lim")
        max_lim = Q_dict.get("max_lim")

        grid = pv.ImageData(spacing=spacing, dimensions=signal.shape, origin=min_lim)

        grid["scalars"] = signal.T.flatten()

        # cmax = np.nanmax(signal)

        _ = self.pv_plotter.add_volume(
            grid,
            opacity="linear",
            show_scalar_bar=False,
            cmap="binary",
            # clim=[0.0001*cmax, cmax],
            # log_scale=True,
            # shade=True,
            culling=True,
        )

        transforms = Q_dict.get("transforms")
        intensities = Q_dict.get("intensities")
        indexings = Q_dict.get("indexings")
        numbers = Q_dict.get("numbers")

        params = [transforms, intensities, indexings, numbers]

        integrate = np.any(intensities)

        mesh = pv.Line(
            pointa=(min_lim[0], 0, 0), pointb=(max_lim[0], 0, 0), resolution=1
        )

        self.pv_plotter.add_mesh(
            mesh, color="k", style="wireframe", render_lines_as_tubes=True
        )

        mesh = pv.Line(
            pointa=(0, min_lim[1], 0), pointb=(0, max_lim[1], 0), resolution=1
        )

        self.pv_plotter.add_mesh(
            mesh, color="k", style="wireframe", render_lines_as_tubes=True
        )

        mesh = pv.Line(
            pointa=(0, 0, min_lim[2]), pointb=(0, 0, max_lim[2]), resolution=1
        )

        self.pv_plotter.add_mesh(
            mesh, color="k", style="wireframe", render_lines_as_tubes=True
        )

        if all([elem is not None for elem in params]) and len(numbers) > 0:
            sphere = pv.Icosphere(radius=1, nsub=0)

            geoms, self.indexing = [], {}
            for i, (T, I, ind, no) in enumerate(zip(*params)):
                ellipsoid = sphere.copy().transform(T)
                color = I if integrate else ind
                ellipsoid["scalars"] = np.full(sphere.n_cells, color)
                geoms.append(ellipsoid)
                self.indexing[i] = i

            multiblock = pv.MultiBlock(geoms)

            mu = np.nanmean(intensities)
            sigma = np.nanstd(intensities)

            cmap = "turbo" if integrate else ["lightblue", "lightgreen"]
            n_colors = 256 if integrate else 2
            clim = [mu - 3 * sigma, mu + 3 * sigma] if integrate else [0, 1]

            _, mapper = self.pv_plotter.add_composite(
                multiblock,
                scalars="scalars",
                color=None,
                log_scale=False,
                style="wireframe",
                cmap=cmap,
                clim=clim,
                n_colors=n_colors,
                show_scalar_bar=False,
                smooth_shading=True,
            )

            self.mapper = mapper

            self.pv_plotter.enable_block_picking(callback=self.highlight, side="left")
            self.pv_plotter.enable_block_picking(callback=self.highlight, side="right")

            self.last_highlight = None

        self.reset_scene()

    def highlight(self, index, dataset):
        if self.mapper is None:
            return

        if self.last_highlight is not None:
            self.mapper.block_attr[self.last_highlight].color = None
        if self.last_highlight == index:
            self.last_highlight = None
            return

        self.mapper.block_attr[index].color = "pink"
        self.last_highlight = index

        ind = self.indexing[index - 1]

        self.view_model.highlight_peaks(ind)

    def highlight_peak(self, index):
        if self.mapper is None:
            return

        if self.last_highlight is not None:
            self.mapper.block_attr[self.last_highlight].color = None

        self.mapper.block_attr[index].color = "pink"
        self.last_highlight = index

    def clear_scene(self):
        """
        Clear all actors.
        """
        self.pv_plotter.clear_actors()
        self.pv_plotter.clear_plane_widgets()

        if self.camera_position is not None:
            self.camera_position = self.pv_plotter.camera_position

    def reset_scene(self):
        if self.camera_position is not None:
            self.pv_plotter.camera_position = self.camera_position
        else:
            self.reset_view()

    def reset_view(self, negative=False):
        """
        Reset the view.
        """
        self.pv_plotter.reset_camera()
        self.pv_plotter.view_isometric(negative=negative)
        self.camera_position = self.pv_plotter.camera_position

    def __format_axis_coord(self, x, y):
        x, y, _ = np.dot(self.T_inv, [x, y, 1])
        return "x={:.3f}, y={:.3f}".format(x, y)

    def update_slice(self, slice_dict, cmap, scale):
        x = slice_dict["x"]
        y = slice_dict["y"]

        labels = slice_dict["labels"]
        title = slice_dict["title"]
        signal = slice_dict["signal"]
        clip = slice_dict["clip"]

        vmin = np.nanmin(clip)
        vmax = np.nanmax(clip)

        if scale == "log" and np.isclose(vmin, 0):
            vmin = np.nanmin(signal[signal > 0])

        if np.isclose(vmax, vmin) or not np.isfinite([vmin, vmax]).all():
            vmin, vmax = (0.1, 1) if scale == "log" else (0, 1)

        T = slice_dict["transform"]
        aspect = slice_dict["aspect"]

        transform = Affine2D(T)

        self.T_inv = np.linalg.inv(T)

        self.ax_slice.format_coord = self.__format_axis_coord

        self.ax_slice.remove()

        if self.cb_slice is not None:
            self.cb_slice.remove()
            self.cb_slice = None

        # if self.ax_xint:
        #     self.ax_xint.remove()
        # if self.ax_yint:
        #     self.ax_yint.remove()

        extreme_finder = ExtremeFinderSimple(20, 20)

        grid_locator1 = MaxNLocator(nbins=10)
        grid_locator2 = MaxNLocator(nbins=10)

        grid_locator1.set_params(integer=True)
        grid_locator2.set_params(integer=True)

        grid_helper = GridHelperCurveLinear(
            transform,
            extreme_finder=extreme_finder,
            grid_locator1=grid_locator1,
            grid_locator2=grid_locator2,
        )

        self.ax_slice = self.fig_slice.add_subplot(
            1, 1, 1, axes_class=Axes, grid_helper=grid_helper
        )

        # self.ax_slice.set_xlabel(labels[0])
        # self.ax_slice.set_ylabel(labels[1])
        self.ax_slice.set_aspect(aspect)

        # divider = make_axes_locatable(self.ax_slice)

        # self.ax_yint = divider.append_axes('right',
        #                                    '10%',
        #                                    pad=0.15,
        #                                    sharey=self.ax_slice)

        # self.ax_xint = divider.append_axes('top',
        #                                    '10%',
        #                                    pad=0.15,
        #                                    sharex=self.ax_slice)

        trans = transform + self.ax_slice.transData

        im = self.ax_slice.pcolormesh(
            x,
            y,
            clip,
            norm=scale,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            shading="flat",
            transform=trans,
            rasterized=True,
        )

        self.ax_slice.set_xlabel(labels[0])
        self.ax_slice.set_ylabel(labels[1])

        # self.ax_slice.set_xticks([])
        # self.ax_slice.set_yticks([])

        # xlim = self.ax_slice.get_xlim()
        # ylim = self.ax_slice.get_ylim()

        # ascale = (ylim[1] - ylim[0]) / (xlim[1] - xlim[0]) * aspect

        # xstart = 1+0.05 if ascale > 1 else 1+0.05*ascale
        # ystart = 1+0.05 if ascale < 1 else 1+0.05*ascale

        # xwidth = 0.1 if ascale < 1 else 0.1 * ascale
        # ywidth = 0.1 if ascale > 1 else 0.1 / ascale

        # self.ax_xint = self.ax_slice.inset_axes(
        #     [0, 0 - ywidth, 1, ywidth], sharex=self.ax_slice
        # )

        # self.ax_yint = self.ax_slice.inset_axes(
        #     [0 - xwidth, 0, xwidth, 1], sharey=self.ax_slice
        # )

        # xint = signal.sum(axis=0)
        # yint = signal.sum(axis=1)
        # sigx = np.sqrt(xint)
        # sigy = np.sqrt(yint)

        # self.ax_xint.errorbar(
        #     0.5 * (x[1:] + x[:-1]),
        #     xint,
        #     yerr=sigx,
        #     fmt=".",
        #     linestyle="-",
        #     color="C0",
        # )

        # self.ax_yint.errorbar(
        #     yint,
        #     0.5 * (y[1:] + y[:-1]),
        #     xerr=sigy,
        #     fmt=".",
        #     linestyle="-",
        #     color="C1",
        # )

        # self.ax_xint.minorticks_on()
        # self.ax_yint.minorticks_on()

        # self.ax_xint.xaxis.get_major_locator().set_params(integer=True)
        # self.ax_yint.yaxis.get_major_locator().set_params(integer=True)

        # self.ax_xint.set_xlabel(labels[0])
        # self.ax_yint.set_ylabel(labels[1])

        # self.ax_xint.yaxis.tick_right()
        # self.ax_yint.xaxis.tick_top()

        # self.ax_xint.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
        # self.ax_yint.ticklabel_format(style="sci", axis="x", scilimits=(0, 0))

        # self.ax_xint.grid(True)
        # self.ax_yint.grid(True)

        # self.ax_xint.set_xticks([])
        # self.ax_yint.set_yticks([])

        self.im = im
        self.view_model.set_slice_field("vlims", [self.im.norm.vmin, self.im.norm.vmax])

        self.ax_slice.set_title(title)
        self.ax_slice.grid(True)

        # ax = [self.ax_slice, self.ax_xint, self.ax_yint]

        # cax = self.ax_yint.inset_axes([1.1, 0, 0.25, 1])

        self.cb_slice = self.fig_slice.colorbar(self.im, ax=self.ax_slice)
        self.cb_slice.minorticks_on()

        # self.fig_slice.tight_layout()

        self.fig_slice.canvas.draw_idle()
        self.fig_slice.canvas.flush_events()

    def update_slice_colorbar(self, vlims):
        if self.cb_slice is not None:
            # self.set_vmin_value(vmin)
            # self.set_vmax_value(vmax)

            self.im.set_clim(vmin=vlims[0], vmax=vlims[1])
            self.cb_slice.update_normal(self.im)
            self.cb_slice.minorticks_on()

            self.fig_slice.canvas.draw_idle()
            self.fig_slice.canvas.flush_events()

    def update_instrument_view(self, inst_view, norm="linear"):
        gamma = inst_view["gamma"]
        nu = inst_view["nu"]
        counts = inst_view["counts"]

        if self.cb_inst is not None:
            self.cb_inst.remove()
            self.cb_inst = None

        self.ax_inst.clear()
        self.ax_inst.invert_xaxis()

        self.im = self.ax_inst.scatter(
            gamma,
            nu,
            c=counts,
            s=1,
            marker="o",
            norm=norm,
            vmin=0,
            vmax=np.percentile(counts, 95),
            rasterized=True,
        )

        self.ax_inst.set_aspect(1)
        self.ax_inst.minorticks_on()

        self.ax_inst.set_xlabel(r"$\gamma$")
        self.ax_inst.set_ylabel(r"$\nu$")

        fmt_str_form = FormatStrFormatter(r"$%d^\circ$")

        self.ax_inst.xaxis.set_major_formatter(fmt_str_form)
        self.ax_inst.yaxis.set_major_formatter(fmt_str_form)

        # self.cb_inst = self.fig_inst.colorbar(self.im, ax=self.ax_inst)
        # self.cb_inst.minorticks_on()

        self.fig_inst.canvas.draw_idle()
        self.fig_inst.canvas.flush_events()

    def update_roi_view(self, roi_view):
        horz = roi_view["horz"]
        vert = roi_view["vert"]
        horz_roi = roi_view["horz_roi"]
        vert_roi = roi_view["vert_roi"]

        for line in self.ax_inst.lines:
            line.remove()

        self.ax_inst.axvline(x=horz - horz_roi, color="k", linestyle="--")
        self.ax_inst.axvline(x=horz + horz_roi, color="k", linestyle="--")

        self.ax_inst.axhline(y=vert - vert_roi, color="k", linestyle="--")
        self.ax_inst.axhline(y=vert + vert_roi, color="k", linestyle="--")

        self.fig_inst.canvas.draw_idle()
        self.fig_inst.canvas.flush_events()

        self.inst_roi = {"roi": (horz_roi, vert_roi)}

        self.fig_inst.canvas.mpl_connect("button_press_event", self.on_press_inst)

    def update_scan_view(self, roi_view):
        x = roi_view["x"]
        y = roi_view["y"]
        val = roi_view["val"]
        label = roi_view["label"]

        self.ax_scan.clear()

        self.ax_scan.errorbar(x, y, yerr=np.sqrt(y), fmt="o", color="C0")
        self.ax_scan.plot(x, y, color="C1")
        # self.ax_scan.set_yscale('log')
        self.line_scan = self.ax_scan.axvline(x=val, color="k", linestyle="--")
        self.ax_scan.minorticks_on()

        if label == "wavelength":
            xlabel = r"$\lambda$ [Å]"
        else:
            xlabel = r"$\vartheta$ [°]"

        self.ax_scan.set_xlabel(xlabel)

        self.fig_scan.canvas.draw_idle()
        self.fig_scan.canvas.flush_events()

        self.fig_scan.canvas.mpl_connect("button_press_event", self.on_press_scan)

    def on_press_scan(self, event):
        if event.inaxes == self.ax_scan and self.fig_scan.canvas.toolbar.mode == "":
            val = event.xdata

            self.diffraction_line.blockSignals(True)

            self.set_diffraction(val)

            self.diffraction_line.blockSignals(False)

            self.line_scan.set_xdata([val])

            self.fig_scan.canvas.draw_idle()
            self.fig_scan.canvas.flush_events()

            self.scan_ready.emit()

    def on_press_inst(self, event):
        if event.inaxes == self.ax_inst and self.fig_inst.canvas.toolbar.mode == "":
            for line in self.ax_inst.lines:
                line.remove()

            horz_roi, vert_roi = self.inst_roi["roi"]

            horz, vert = event.xdata, event.ydata

            self.horizontal_line.blockSignals(True)
            self.vertical_line.blockSignals(True)

            self.set_horizontal(horz)
            self.set_vertical(vert)

            self.horizontal_line.blockSignals(False)
            self.vertical_line.blockSignals(False)

            self.ax_inst.axvline(x=horz - horz_roi, color="k", linestyle="--")
            self.ax_inst.axvline(x=horz + horz_roi, color="k", linestyle="--")

            self.ax_inst.axhline(y=vert - vert_roi, color="k", linestyle="--")
            self.ax_inst.axhline(y=vert + vert_roi, color="k", linestyle="--")

            self.fig_inst.canvas.draw_idle()
            self.fig_inst.canvas.flush_events()

            self.roi_ready.emit()

    def add_cluster_peaks(self, peak_dict):
        self.pv_plotter.clear_actors()

        for i in range(3):
            self.ax_clust[i].clear()

        bins = np.linspace(-1.025, 1.025, 42)

        coordinates = np.array(peak_dict["coordinates"])
        clusters = np.array(peak_dict["clusters"])

        vectors = peak_dict["translation"]
        T = peak_dict["transform"]
        T_inv = peak_dict["inverse"]

        translations = np.array(
            np.meshgrid([-1, 0, 1], [-1, 0, 1], [-1, 0, 1])
        ).T.reshape(-1, 3)

        offsets = np.dot(translations, vectors)

        multiblock = pv.MultiBlock()

        for uni in np.unique(clusters):
            coords = coordinates[clusters == uni]
            coords = (coords[:, np.newaxis, :] + offsets).reshape(-1, 3)
            delta = (T_inv @ coords.T).T
            mask = (np.abs(delta) < 1).all(axis=1)
            coords = coords[mask]
            delta = delta[mask]
            points = pv.PolyData(coords)
            if uni >= 0:
                color = "C{}".format(uni)
                multiblock[color] = points
                if uni > 0:
                    h, _ = np.histogram(delta[:, 0], bins=bins)
                    k, _ = np.histogram(delta[:, 1], bins=bins)
                    l, _ = np.histogram(delta[:, 2], bins=bins)
                    self.ax_clust[0].stairs(h, bins, color=color)
                    self.ax_clust[1].stairs(k, bins, color=color)
                    self.ax_clust[2].stairs(l, bins, color=color)
            else:
                self.pv_plotter.add_mesh(
                    points,
                    color="k",
                    smooth_shading=True,
                    point_size=5,
                    render_points_as_spheres=True,
                )

        for i in range(3):
            self.ax_clust[i].minorticks_on()
            self.ax_clust[i].set_yscale("log")

        self.ax_clust[0].set_xlabel("$[h00]$")
        self.ax_clust[1].set_xlabel("$[0k0]$")
        self.ax_clust[2].set_xlabel("$[00l]$")

        self.fig_clust.canvas.draw_idle()
        self.fig_clust.canvas.flush_events()

        _, mapper = self.pv_plotter.add_composite(
            multiblock,
            multi_colors=True,
            smooth_shading=True,
            point_size=10,
            render_points_as_spheres=True,
        )

        prop_cycle = plt.rcParams["axes.prop_cycle"]

        cmap = prop_cycle.by_key()["color"]

        colors = []
        for i in range(1, len(mapper.block_attr)):
            colors.append(cmap[i - 1])
            mapper.block_attr[i].color = cmap[i - 1]

        legend = [["C{}".format(i), color] for i, color in enumerate(colors)]

        A = np.eye(4)
        A[:3, :3] = T

        mesh = pv.Box(bounds=(-1, 1, -1, 1, -1, 1), level=0, quads=True)
        mesh.transform(A, inplace=True)

        self.pv_plotter.add_mesh(
            mesh, color="k", style="wireframe", render_lines_as_tubes=True
        )

        for point in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]:
            mesh = pv.Line(pointa=-np.array(point), pointb=point, resolution=1)
            mesh.transform(A, inplace=True)

            self.pv_plotter.add_mesh(
                mesh, color="k", style="wireframe", render_lines_as_tubes=True
            )

        pointsa = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        pointsb = [(-1, 1), (1, 1), (1, -1), (-1, -1)]

        for i in range(4):
            a, b = pointsa[i], pointsb[i]

            mesh = pv.Line(pointa=(a[0], a[1], 0), pointb=(b[0], b[1], 0), resolution=1)

            mesh.transform(A, inplace=True)

            self.pv_plotter.add_mesh(
                mesh, color="k", style="wireframe", render_lines_as_tubes=True
            )

            mesh = pv.Line(pointa=(a[0], 0, a[1]), pointb=(b[0], 0, b[1]), resolution=1)

            mesh.transform(A, inplace=True)

            self.pv_plotter.add_mesh(
                mesh, color="k", style="wireframe", render_lines_as_tubes=True
            )

            mesh = pv.Line(pointa=(0, a[0], a[1]), pointb=(0, b[0], b[1]), resolution=1)

            mesh.transform(A, inplace=True)

            self.pv_plotter.add_mesh(
                mesh, color="k", style="wireframe", render_lines_as_tubes=True
            )

        self.pv_plotter.add_legend(legend, loc="lower right", bcolor="w", face=None)

        self.pv_plotter.enable_depth_peeling()

        self.reset_view()
