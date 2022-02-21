import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from matplotlib import cm

COLORS = ["g", "b", "m", "r", "y"]


def plot_data(
    title: str, xaxis: list, yaxis: list, xlabel: str, ylabel: str, path="graphs/"
):
    print(path + title)
    plt.plot(xaxis, yaxis, COLORS[0], label=xlabel)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.savefig(f"{path+title}.png", bbox_inches="tight")
    plt.close()


def plot_3ddata(title: str, xaxis: list, yaxis: list, path="3d_graphs/"):
    print(path + title)
    plt.plot(xaxis, yaxis, COLORS[0], label="positioning")
    plt.title(title)
    plt.xlabel("Price")
    plt.ylabel("Position")
    plt.legend()
    plt.savefig(f"{path+title}.png", bbox_inches="tight")
    plt.close()


def plot3d(X, Y, Z):
    fig = plt.figure(figsize=(8, 5))
    ax = fig.gca(projection="3d")

    # Make data.
    #     X = np.arange(-5, 5, 0.25)
    #     Y = np.arange(-5, 5, 0.25)
    X, Y = np.meshgrid(X, Y)
    #     R = np.sqrt(X**2 + Y**2)
    #     Z = np.sin(R)
    print(Z.shape)
    # Plot the surface.
    surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm, linewidth=0, antialiased=False)

    # ax.plot_wireframe(X, Y, Z, rstride=5, cstride=5)
    # Customize the z axis.
    ax.set_zlim(-1.01, 1.01)
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter("%.02f"))

    # Tweaking display region and labels
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_zlim(0, 1)
    ax.set_xlabel("Emma Probability A")
    ax.set_ylabel("James Probability A")
    ax.set_zlabel("Emma Win %")

    # rotate the axes and update
    for angle in range(0, 360):
        ax.view_init(30, angle)
        plt.draw()
        #         plt.show()
        plt.pause(0.001)

    # Add a color bar which maps values to colors.


#     fig.colorbar(surf, shrink=0.5, aspect=5)

#     plt.show()
