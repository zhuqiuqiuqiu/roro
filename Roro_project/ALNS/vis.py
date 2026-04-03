import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def animate_full(history, layout, yard_sizes):

    num_yards = len(yard_sizes)

    #
    fig = plt.figure(figsize=(12, 6))

    # 网格布局
    gs = fig.add_gridspec(2, num_yards + 1)

    # 堆场子图
    yard_axes = []
    for i in range(num_yards):
        ax = fig.add_subplot(gs[:, i])
        yard_axes.append(ax)

    # cost曲线
    ax_cost = fig.add_subplot(gs[:, -1])

    costs = []

    colors = {
        "SUV": "blue",
        "Sedan": "green",
        "Truck": "red",
        "Van": "orange"
    }

    def update(frame):

        sol = history[frame]
        costs.append(sol.cost)

        # ===== 画堆场 =====
        for i, (yard_id, types) in enumerate(sol.yards.items()):
            ax = yard_axes[i]
            ax.clear()

            W, H = yard_sizes[yard_id]
            ax.set_xlim(0, W)
            ax.set_ylim(0, H)

            ax.set_title(f"Yard {yard_id}")
            ax.invert_yaxis()

            cost, feasible, placements = layout.evaluate(yard_id, types)

            for (x, y, w, h, t) in placements:
                rect = plt.Rectangle(
                    (x, y), w, h,
                    edgecolor='black',
                    facecolor=colors.get(t, "gray"),
                    alpha=0.7
                )
                ax.add_patch(rect)

                ax.text(
                    x + w/2,
                    y + h/2,
                    t,
                    ha='center',
                    va='center',
                    fontsize=7
                )

        # ===== 画cost曲线 =====
        ax_cost.clear()
        ax_cost.plot(costs)
        ax_cost.set_title("Cost")
        ax_cost.set_xlabel("Iter")
        ax_cost.set_ylabel("Cost")

        fig.suptitle(f"Iteration {frame} | Cost: {sol.cost:.2f}")

    ani = FuncAnimation(
        fig,
        update,
        frames=len(history),
        interval=200,
        repeat=False
    )

    plt.show()