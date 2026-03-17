from datetime import datetime
from tkinter.font import names
from gurobipy import *
#参数区
######---------------------------------------- 求解案例一
# 每个堆场的长度
L_i_list = [30,40 ]
#每个堆场的宽度
W_i_list = [20,15]



#######---------------------------------------求解案例二
# #每个堆场的宽度
# W_i_list = [9, 13, 10]
# # 每个堆场的长度
# L_i_list = [30, 40, 20]
# M 的取值
M = max(max(W_i_list), max(L_i_list))
#各个车型的名字
numer_j = ['suv', 'volvo']         ###  注意修改
#每种车型的长度
l_j = [5 , 4.8]
#每种车型的宽度20
w_j = [2.2, 2]
#每种车型的数量
n_j = [6, 7]
#堆场索引
I = list(range(len(W_i_list)))
#车型de索引
J = list(range(len(numer_j)))
#每个堆场长度的字典
L = {i:L_i_list[i] for i in I}
#每个堆场宽度的字典
W = {i:W_i_list[i] for i in I}
#每个堆场面积的字典
A = {i:L_i_list[i]*W_i_list[i] for i in I}
#每个车型长度的字典
l_j = {j:l_j[j] for j in J }
#每个车型宽度的字典
w_j = {j:w_j[j] for j in J }
#每个车型面积的字典
a = {j:l_j[j]*w_j[j] for j in J}
#每个车型的数量
n = {j:n_j[j] for j in J}
#定义k
K = {j: range(n[j]) for j in J}   #字典
#j车型第q辆车
Vehicles = []
for j in J :
    for q in range(n[j]):
        Vehicles.append((j,q))
#jq,mk车辆数量
Pairs = [(j,q,m,k) for (j,q) in Vehicles for(m,k) in Vehicles if (j,q)!=(m,k)]

# print(f'Pairs_length:{len(Pairs)}')
# 2256个

                                        #变量区
m = Model('roro')
#定义决策变量
#0-1变量，堆场i是否被使用（1使用，0不使用）
v_i = m.addVars(I,vtype=GRB.BINARY, name='v_i')
#0-1变量，i堆场是否分配了j车型（1是，0否）
y_ij = m.addVars(I,J,vtype=GRB.BINARY, name='y_ij')

#定义决策变量
x = {}
for i in I:
    for j in J:
        for q in K[j]:
            x[i,j,q] = m.addVar(vtype=GRB.BINARY,
                                name=f"x_{i}_{j}_{q}")

#0-1变量，i堆场j车型的q辆车放置（竖直为0，横放为1）
# r_ijq = m.addVars(I, J, K, vtype=GRB.BINARY, name="r")
r_ijq = m.addVars(I, Vehicles, vtype=GRB.BINARY, name="r")

#0-1变量，左右上下的定位变量
# l = m.addVars(I, J, K, J, K, vtype=GRB.BINARY, name="l")
# b = m.addVars(I, J, K, J, K, vtype=GRB.BINARY, name="b")
l = m.addVars(I, Vehicles, Vehicles, vtype=GRB.BINARY, name="l")
b = m.addVars(I, Vehicles, Vehicles, vtype=GRB.BINARY, name="b")



#坐标

Xl, Yl, Xr, Yr = {}, {}, {}, {}
for i in I:
    for j in J:
        for q in K[j]:
            Xl[i,j,q] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"Xl_{i}_{j}_{q}")
            Yl[i,j,q] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"Yl_{i}_{j}_{q}")
            Xr[i,j,q] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"Xr_{i}_{j}_{q}")
            Yr[i,j,q] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"Yr_{i}_{j}_{q}")



#定义辅助变量
z_j =m.addVars(J,vtype=GRB.CONTINUOUS,lb=0,name='z_j')
u_i = m.addVars(I,vtype=GRB.CONTINUOUS,lb=0,ub=1,name='u_i')
u_min = m.addVar(vtype=GRB.CONTINUOUS,lb=0, ub=1 ,name='u_min')
                                         #更新参数
m.update()

                                         #目标函数区
# # 定义 主目标函数
# m.setObjective(sum(z_j for j in J),GRB.MINIMIZE)
# 定义 次目标函数
# m.setObjective(u_min, GRB.MAXIMIZE)



                                         #约束区
# 约束一：每种车型j放置堆场数 超过1 的部分
for j in J:
    m.addConstr(
        z_j[j]+1 >= quicksum(y_ij[i,j] for i in I),
        name='每种车型j放置堆场数超过1的部分'
    )
for j in J:
    m.addConstr(
        z_j[j]+1 <= quicksum(y_ij[i,j] for i in I),
        name='每种车型j放置堆场数超过1的部分'
    )


# 约束二：车辆均被分配到堆场中
for j in J:
    for q in K[j]:  #每一个车型的每一辆车都被分配到堆场中
        m.addConstr(
            quicksum(x[i,j,q]  for i in I) ==1,
            name='车辆均被分配到堆场中'
        )
#约束三：堆场上放置的车辆总面积要小于等于堆场面积
for i in I:
    m.addConstr(
        quicksum(
            a[j] * quicksum(x[i,j,q] for q in K[j])
        for j in J) <= A[i],
        name='堆场上放置的车辆总面积要小于等于堆场面积'
    )
#约束四：堆场放置车型与某车辆是否放置在堆场上的关联约束
for i in I:
    for j in J:
        m.addConstr(
            quicksum(x[i,j,q] for q in K[j]) >= y_ij[i,j],
            name='堆场放置车型与某车辆是否放置在堆场上的关联约束'
        )
#约束四‘：堆场上放置车辆与堆场放置车型的关联约束2
for i in I:
    for j in J:
        m.addConstr(
            quicksum(x[i,j,q] for q in K[j]) <=y_ij[i,j] * M,
            name='堆场上放置车辆与堆场放置车型的关联约束2'
        )
#约束五：被使用堆场的最小面积利用率与所有被使用堆场的面积利用率的关联约束
for i in I:
    m.addConstr(
        u_min <= u_i[i] + (1-v_i[i]),
        name='被使用堆场的最小面积利用率与所有被使用堆场的面积利用率的关联约束'
    )
#约束六：该堆场的利用率小于等于堆场是否被使用的0-1变量
for i in I:
    m.addConstr(
        u_i[i] <= v_i[i],
        name='该堆场的利用率小于等于堆场是否被使用的0-1变量'
    )
#约束七：堆场是否被使用与是否有车辆被停放到该堆场的关联约束1
for i in I:
    m.addConstr(
        v_i[i] <= quicksum(
            quicksum(x[i,j,q] for q in K[j])
        for j in J
        ),
        name ='堆场是否被使用与是否有车辆被停放到该堆场的关联约束1'
    )
#约束八：堆场是否被使用与是否有车辆被停放到该堆场的关联约束2
for i in I:
    m.addConstr(
        quicksum(
            quicksum(x[i,j,q] for q in K[j])
            for j in J) <= v_i[i] * M ,
        name = '堆场是否被使用与是否有车辆被停放到该堆场的关联约束2'
    )
#约束九：定义堆场i的利用率的公式
for i in I:
    m.addConstr(
        u_i[i]*A[i] == quicksum(
            a[j] * quicksum(x[i,j,q] for q in K[j])
        for j in J),
        name='堆场的利用率定义公式'
    )
#利用率这里的≥，应该是改成＝

#约束十：对车型坐标的约束
for i in I:
    for j in J:
        for q in K[j]:
            m.addConstr(Xr[i,j,q] <= W[i] + M*(1-x[i,j,q]),name='每辆车的右X坐标小于等于堆场宽度')
for i in I:
    for j in J:
        for q in K[j]:
            m.addConstr(Yr[i,j,q] <= L[i] + M*(1-x[i,j,q]),name='每辆车的右Y坐标小于等于堆场高度/长度')
# for i in I:
#     for j in J:
#         for q in K[j]:
#             m.addConstr(
#                 Xr[i,j,q] >= Xl[i,j,q] + (1-r_ijq[i,j,q])*w_j[j] + r_ijq[i,j,q]*l_j[j] - M*(1-x[i,j,q])
#             )
# for i in I:
#     for j in J:
#         for q in K[j]:
#             m.addConstr(
#                 Xr[i,j,q] <= Xl[i,j,q] + (1-r_ijq[i,j,q])*w_j[j] + r_ijq[i,j,q]*l_j[j] + M*(1-x[i,j,q])
#             )
# for i in I:
#     for j in J:
#         for q in K[j]:
#             m.addConstr(
#                 Yr[i,j,q] >= Yl[i,j,q] + (1-r_ijq[i,j,q])*l_j[j] + r_ijq[i,j,q]*w_j[j] - M*(1-x[i,j,q])
#             )
# for i in I:
#     for j in J:
#         for q in K[j]:
#             m.addConstr(
#                 Yr[i,j,q] <= Yl[i,j,q] + (1-r_ijq[i,j,q])*l_j[j] + r_ijq[i,j,q]*w_j[j] + M*(1-x[i,j,q])
#             )
#约束十一：对车辆的重叠约束
# for i in I:
#     for j in J:
#         for q in K[j]:
#             for j2 in J:
#                 for k in K[j2]:
#                     if (j==j2) and (q==k):
#                         continue
#
#                     m.addConstr(Xr[i, j, q] <= Xl[i, m, k] + M * (1 - l[i, j, q, m, k]))
#                     m.addConstr(Xr[i, m, k] <= Xl[i, j, q] + M * (1 - l[i, m, k, j, q]))
#                     m.addConstr(Yr[i, j, q] <= Yl[i, m, k] + M * (1 - b[i, j, q, m, k]))
#                     m.addConstr(Yr[i, m, k] <= Yl[i, j, q] + M * (1 - b[i, m, k, j, q]))
#
#                     m.addConstr(
#                         l[i,j,q,m,k] + l[i,m,k,j,q] + b[i,j,q,m,k] + b[i,m,k,j,q]
#                         >= x[i,j,q] + x[i,m,k] -1
#                     )
Vehicles = [(j,q) for j in J for q in K[j]]
for i in I:
    for idx1 in range(len(Vehicles)):
        j,q = Vehicles[idx1]
        for idx2 in range(idx1+1, len(Vehicles)):
            p,k = Vehicles[idx2]
            # A 在 B 左
            m.addConstr(
                Xr[i,j,q] <= Xl[i,p,k] + M*(1-l[i,j,q,p,k]),
                name='A在B坐标左边的防重叠约束'
            )
            # B 在 A 左
            m.addConstr(
                Xr[i,p,k] <= Xl[i,j,q] + M*(1-l[i,p,k,j,q]),
                name='B在A坐标左边的防重叠约束'
            )
            # A 在 B 下
            m.addConstr(
                Yr[i,j,q] <= Yl[i,p,k] + M*(1-b[i,j,q,p,k]),
                name='A在B坐标下边的防重叠约束'
            )
            # B 在 A 下
            m.addConstr(
                Yr[i,p,k] <= Yl[i,j,q] + M*(1-b[i,p,k,j,q]),
                name='B在A坐标下边的防重叠约束'
            )
            # OR 约束
            m.addConstr(
                l[i,j,q,p,k] + l[i,p,k,j,q]
              + b[i,j,q,p,k] + b[i,p,k,j,q]
              >= x[i,j,q] + x[i,p,k] - 1 ,
                name='防重叠0-1变量的控制约束'
            )
#约束十二：当车辆转向后的坐标
for i in I:
    for j in J:
        for q in K[j]:
            m.addConstr(
                Xr[i,j,q]
                == Xl[i,j,q]
                + (1 - r_ijq[i,j,q]) * w_j[j]
                + r_ijq[i,j,q] * l_j[j],
                name="车辆转向后X坐标转换约束"
            )
            m.addConstr(
                Yr[i,j,q]
                == Yl[i,j,q]
                + (1 - r_ijq[i,j,q]) * l_j[j]
                + r_ijq[i,j,q] * w_j[j],
                name="车辆转向后Y坐标转换约束"
            )
#####################              求解
# ------------------------------------------        求解：主目标
#////2026.1.7 demo：增加车辆排布紧凑目标函数
obj_demo = quicksum(Yl[i,j,q] for i in I for j in J for q in K[j])

#如上为紧凑目标函数部分
#----------------------------------   求解：归一化参数
# m.setObjective(quicksum(z_j[j] for j in J) , GRB.MINIMIZE)
# m.setObjective(obj_demo , GRB.MINIMIZE)

#求解组合目标函数：  每种车型使用的堆场数量 少
obj_demo2= quicksum(z_j[j] for j in J)

### -------------------------------------    主目标函数
m.setObjective(obj_demo2 , GRB.MINIMIZE)
# ------------------------------------------   修改后的主目标+紧凑目标
# m.setObjective(obj_demo2 + obj_demo, GRB.MINIMIZE)

m.write("roro_model_demo_2026_1_13.lp")
print('已经完成模型结构的打印')

#------------------------   计算求解时间
star_time = datetime.now()
print(f'开始求解时间：{star_time}')
m.optimize()
if m.status != GRB.OPTIMAL:
    raise RuntimeError("第一阶段未找到最优解")

Z_star = int(round(m.ObjVal))
print("主目标最优值 Z* =", Z_star)
# -----------------------------------------         求解：次目标
m.addConstr(
    quicksum(z_j[j] for j in J) <= Z_star,
    name="primary_fixed"
)


### 次目标函数 + 紧凑目标   因为目标是max，所有为 -obj_demo
m.setObjective(u_min - obj_demo, GRB.MAXIMIZE)

### -------------  次目标函数
# m.setObjective(u_min, GRB.MAXIMIZE)

m.optimize()
if m.status != GRB.OPTIMAL:
    raise RuntimeError("第二阶段未找到最优解")
print("最小利用率 u_min =", u_min.X)
end_time = datetime.now()
print(f'结束求解时间：{end_time}')
####----------------------------------------------     打印最后的变量求解值
import csv
with open("final_vehicle_layout.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "yard_i", "vehicle_type_j", "vehicle_q",
        "rotated_r",
        "X_left", "Y_left", "X_right", "Y_right",
        "length", "width"
    ])

    for i in I:
        for j in J:
            for q in K[j]:
                if x[i, j, q].X > 0.5:
                    r = int(round(r_ijq[i, j, q].X))

                    # 计算旋转后的尺寸
                    if r == 0:   # 竖放
                        length = l_j[j]
                        width  = w_j[j]
                    else:        # 横放
                        length = w_j[j]
                        width  = l_j[j]

                    writer.writerow([
                        i, numer_j[j], q,
                        r,
                        round(Xl[i,j,q].X, 3),
                        round(Yl[i,j,q].X, 3),
                        round(Xr[i,j,q].X, 3),
                        round(Yr[i,j,q].X, 3),
                        round(length, 3),
                        round(width, 3)
                    ])

print("✅ 已输出最终车辆排布：final_vehicle_layout.csv")
### ------------------------------------------------    打印完整的求解报告
m.write("solution.sol")

