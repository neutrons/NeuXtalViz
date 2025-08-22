import numpy as np
import pyvista as pv
from matplotlib.backends.backend_qtagg import FigureCanvas
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
        canvas_slice: FigureCanvas,
    ):
        self.view_model = view_model
        self.pv_plotter = pv_plotter

        self.canvas_slice = canvas_slice
        self.fig_slice = self.canvas_slice.figure
        self.ax_slice = self.fig_slice.subplots(1, 1)
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

        self.canvas_slice.draw_idle()
        self.canvas_slice.flush_events()

    def update_slice_colorbar(self, vlims):
        if self.cb_slice is not None:
            # self.set_vmin_value(vmin)
            # self.set_vmax_value(vmax)

            self.im.set_clim(vmin=vlims[0], vmax=vlims[1])
            self.cb_slice.update_normal(self.im)
            self.cb_slice.minorticks_on()

            self.canvas_slice.draw_idle()
            self.canvas_slice.flush_events()
