from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# 设置中文显示和负号显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 1️⃣ 读取 Excel / CSV
df = pd.read_csv("final_vehicle_layout.csv")

# 如果是 Excel
# df = pd.read_excel("final_vehicle_layout.xlsx")

# 车型颜色
color_map = {
    "suv": "#1f77b4",

}

# 2️⃣ 直接给定堆场尺寸
# 你可以用一个字典为每个堆场指定不同的尺寸
yard_sizes = {
    0: {"width": 20, "length": 30},
    1: {"width": 15, "length": 40},

    # 你可以继续为每个堆场增加尺寸
}

# 3️⃣ 按堆场绘制图形，堆场的尺寸从字典获取
for yard_id, yard_df in df.groupby("yard_i"):

    # 获取当前堆场的尺寸（从字典中获取）
    yard_width = yard_sizes[yard_id]["width"]
    yard_length = yard_sizes[yard_id]["length"]

    # 创建一个新的图形对象，设置图像大小
    fig, ax = plt.subplots(figsize=(12, 8))

    # 画堆场边界
    ax.add_patch(
        Rectangle(
            (0, 0),
            yard_width,
            yard_length,
            fill=False,
            edgecolor="black",
            linewidth=2
        )
    )

    # 4️⃣ 画每一辆车
    for _, row in yard_df.iterrows():
        xl = row["X_left"]
        yl = row["Y_left"]
        xr = row["X_right"]
        yr = row["Y_right"]

        width = xr - xl
        height = yr - yl

        # 创建每辆车的矩形
        rect = Rectangle(
            (xl, yl),
            width,
            height,
            facecolor=color_map.get(row["vehicle_type_j"], "gray"),
            edgecolor="black",
            alpha=0.75
        )
        ax.add_patch(rect)

        # 标注每辆车，去掉注释行如果不需要显示
        # ax.text(
        #     xl + width / 2,
        #     yl + height / 2,
        #     f'{row["vehicle_type_j"]}-{int(row["vehicle_q"])}',
        #     ha="center",
        #     va="center",
        #     fontsize=8,
        #     color="white"
        # )

    # 设置堆场的坐标轴范围
    ax.set_xlim(0, yard_width)
    ax.set_ylim(0, yard_length)

    # 设置图像的纵横比为相等，保持堆场比例
    ax.set_aspect("equal")

    # 设置标题和坐标轴标签
    ax.set_title(f"堆场 {yard_id} 车辆排布图", fontsize=14)
    ax.set_xlabel("Width")
    ax.set_ylabel("Length")
    ax.grid(True, linestyle="--", alpha=0.4)

    # 保存图像到文件，堆场 ID 会被用于区分文件名
    plt.savefig(

        f"yard_{yard_id}_layout3-两堆场两车型-主.png",
        dpi=600,  # 设置高分辨率
        bbox_inches="tight",  # 去除白边
        pad_inches=0.02  # 极小的边距
    )

    # 关闭当前图形对象，避免内存占用
    plt.close()
