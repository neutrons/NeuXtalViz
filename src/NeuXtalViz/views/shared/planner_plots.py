import matplotlib.pyplot as plt
import numpy as np

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
