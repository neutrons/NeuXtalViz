import numpy as np
import pyvista as pv

from NeuXtalViz.view_models.ub_tools import UBViewModel


class UBPlotter:
    def __init__(self, view_model: UBViewModel, pv_plotter: pv.Plotter):
        self.view_model = view_model
        self.pv_plotter = pv_plotter
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
