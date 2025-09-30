import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter


def plot_statistics(ax_cov, sym, asym):
    ax_cov[0].clear()
    ax_cov[1].clear()
    ax_cov[2].clear()

    color = plt.get_cmap("tab20").colors

    width = 1 / 3

    shel, comp, mult, refl = sym

    x = np.arange(len(shel))

    ax_cov[0].bar(x, comp, width, color=color[0])
    ax_cov[1].bar(x, mult, width, color=color[2])
    ax_cov[2].bar(x, refl, width, color=color[4])

    shel, comp, mult, refl = asym

    ax_cov[0].bar(x + width, comp, width, color=color[1])
    ax_cov[1].bar(x + width, mult, width, color=color[3])
    ax_cov[2].bar(x + width, refl, width, color=color[5])

    ax_cov[0].set_ylim(0, 100)

    ax_cov[0].minorticks_on()
    ax_cov[1].minorticks_on()
    ax_cov[2].minorticks_on()

    ax_cov[2].set_xlabel("Resolution Shell [Å]")
    ax_cov[0].set_ylabel("Completeness [%]")
    ax_cov[1].set_ylabel("Redundancy")
    ax_cov[2].set_ylabel("Unique Reflections")

    ax_cov[0].set_xticks(x + width, shel)
    ax_cov[1].set_xticks(x + width, shel)
    ax_cov[2].set_xticks(x + width, shel)


def plot_instrument_alternate(
        fig_inst,
        ax_inst,
        cb_inst,
        cb_inst_alt,
        gamma_inst,
        nu_inst,
        gamma_1,
        nu_1,
        lamda_1,
        gamma_2,
        nu_2,
        lamda_2,
):
    if cb_inst is not None:
        cb_inst.remove()
        cb_inst = None

    if cb_inst_alt is not None:
        cb_inst_alt.remove()
        cb_inst_alt = None

    ax_inst.clear()
    ax_inst.invert_xaxis()

    ax_inst.scatter(
        gamma_inst, nu_inst, color="lightgray", marker="o", rasterized=True
    )

    im = ax_inst.scatter(
        gamma_1, nu_1, c=lamda_1, marker="o", cmap="GnBu", rasterized=True
    )

    im_alt = ax_inst.scatter(
        gamma_2, nu_2, c=lamda_2, marker="o", cmap="RdPu", rasterized=True
    )

    ax_inst.set_aspect(1)
    ax_inst.minorticks_on()

    ax_inst.set_xlabel(r"$\gamma$")
    ax_inst.set_ylabel(r"$\nu$")

    fmt_str_form = FormatStrFormatter(r"$%d^\circ$")

    ax_inst.xaxis.set_major_formatter(fmt_str_form)
    ax_inst.yaxis.set_major_formatter(fmt_str_form)

    if len(lamda_2) > 0:
        cb_inst_alt = fig_inst.colorbar(
            im_alt, ax=ax_inst, orientation="horizontal"
        )
        cb_inst_alt.minorticks_on()

    if len(lamda_1) > 0:
        cb_inst = fig_inst.colorbar(
            im, ax=ax_inst, orientation="horizontal"
        )
        cb_inst.minorticks_on()

    if len(lamda_2) > 0:
        cb_inst_alt.ax.set_xlabel(r"$\lambda$ [Å]")
    elif len(lamda_1) > 0:
        cb_inst.ax.set_xlabel(r"$\lambda$ [Å]")
    return cb_inst, cb_inst_alt


def plot_instrument(fig_inst, ax_inst, cb_inst, cb_inst_alt, gamma_inst, nu_inst, gamma, nu, lamda):
    if cb_inst is not None:
        cb_inst.remove()
        cb_inst = None

    if cb_inst_alt is not None:
        cb_inst_alt.remove()
        cb_inst_alt = None

    ax_inst.clear()
    ax_inst.invert_xaxis()

    ax_inst.scatter(
        gamma_inst, nu_inst, color="lightgray", marker="o", rasterized=True
    )

    im = ax_inst.scatter(
        gamma, nu, c=lamda, marker="o", rasterized=True
    )

    ax_inst.set_aspect(1)
    ax_inst.minorticks_on()

    ax_inst.set_xlabel(r"$\gamma$")
    ax_inst.set_ylabel(r"$\nu$")

    fmt_str_form = FormatStrFormatter(r"$%d^\circ$")

    ax_inst.xaxis.set_major_formatter(fmt_str_form)
    ax_inst.yaxis.set_major_formatter(fmt_str_form)
    if len(lamda) > 0:
        cb_inst = fig_inst.colorbar(
            im, ax=ax_inst, orientation="horizontal"
        )
        cb_inst.minorticks_on()
        cb_inst.ax.set_xlabel(r"$\lambda$ [Å]")
    return cb_inst, cb_inst_alt
