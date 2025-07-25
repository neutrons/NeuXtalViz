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
        self.pv_plotter.enable_block_picking(
            callback=self.highlight, side="right"
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
