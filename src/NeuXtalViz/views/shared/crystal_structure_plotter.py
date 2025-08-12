import matplotlib
import numpy as np
import pyvista as pv

from NeuXtalViz.config.atoms import colors, radii


class CrystalStructurePlotter:
    def __init__(self, pv_plotter, callback):
        self.pv_plotter = pv_plotter
        self.callback = callback

    def highlight(self, index, dataset):
        color = self.mapper.block_attr[index].color

        if color == "pink":
            color = None
        else:
            color = "pink"

        self.mapper.block_attr[index].color = color

        ind = self.indexing[index - 1]

        if color == "pink":
            self.callback(ind)

    def reset_view(self):
        """
        Reset the view.

        """

        self.pv_plotter.reset_camera()
        self.pv_plotter.view_isometric()

    def add_atoms(self, atom_dict):
        self.pv_plotter.clear_actors()

        T = np.eye(4)

        geoms, cmap, self.indexing = [], [], {}

        sphere = pv.Icosphere(radius=1, nsub=2)

        atm_ind = 0

        for i_atm, atom in enumerate(atom_dict.keys()):
            color = colors[atom]
            radius = radii[atom][0]

            coordinates, opacities, indices = atom_dict[atom]

            for coord, occ, ind in zip(coordinates, opacities, indices):
                T[0, 0] = T[1, 1] = T[2, 2] = radius
                T[:3, 3] = coord
                atm = sphere.copy().transform(T)
                atm["scalars"] = np.full(sphere.n_cells, i_atm + 1.0)
                geoms.append(atm)
                self.indexing[atm_ind] = ind
                atm_ind += 1

            cmap.append(color)

        cmap = matplotlib.colors.ListedColormap(cmap)

        multiblock = pv.MultiBlock(geoms)

        _, mapper = self.pv_plotter.add_composite(
            multiblock, cmap=cmap, smooth_shading=True, show_scalar_bar=False
        )

        self.mapper = mapper

        self.pv_plotter.enable_block_picking(callback=self.highlight, side="left")
        self.pv_plotter.enable_block_picking(callback=self.highlight, side="right")

        self.reset_view()

    def add_histo(self, histo_dict, normal, norm, value, opacity, log_scale, cmap):
        self.pv_plotter.clear_actors()
        self.pv_plotter.clear_plane_widgets()

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

        self.clip.AddObserver("InteractionEvent", self.callback)

    def add_sample(self, sample_mesh):
        self.pv_plotter.clear_actors()

        triangles = []
        for triangle in sample_mesh:
            triangles.append(pv.Triangle(triangle))

        multiblock = pv.MultiBlock(triangles)

        _, mapper = self.pv_plotter.add_composite(multiblock, smooth_shading=True)

        self.pv_plotter.add_legend_scale(
            corner_offset_factor=2,
            bottom_border_offset=50,
            top_border_offset=50,
            left_border_offset=100,
            right_border_offset=100,
            legend_visibility=True,
            xy_label_mode=False,
        )

        self.reset_view()

    def draw_cell(self, A):
        T = np.eye(4)
        T[:3, :3] = A

        mesh = pv.Box(bounds=(0, 1, 0, 1, 0, 1), level=0, quads=True)
        mesh.transform(T, inplace=True)

        self.pv_plotter.add_mesh(
            mesh, color="k", style="wireframe", render_lines_as_tubes=True
        )
