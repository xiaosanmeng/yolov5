"""
1.车头时距的基本概念是指在同一车道上行驶的车辆队列中，前后两辆车的前端通过同一地点的时间差。
2.车头间距，又称为空间车头间距，是指同一车道上行驶的车辆之间，前车车尾与后车车头之间的实际距离。
3.排队长度指路口进口道各转向的排队长度；定义为从路口信号灯转为绿灯时刻，该路口进口道各转向车流排队最后一辆车距离路口停车线的距离。
4.速度，车辆通过有信号灯控制路口时的行车速度。
视频默认30fps，通过frame_id可以计算得到视频的时长
"""

import math
import numpy as np
import cv2
from PIL import Image
from track.trajectory_clustering import draw_lines
from matplotlib.path import Path


# 计算两点之间的距离
def calculate_distance(point1, point2):
    """
    计算两个像素点之间的欧几里得距离。

    参数:
    point1 (tuple): 第一个点的坐标，格式为(x1, y1)。
    point2 (tuple): 第二个点的坐标，格式为(x2, y2)。

    返回:
    float: 两点之间的距离。
    """
    x1, y1 = point1
    x2, y2 = point2
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance


# 通过多边形得到掩码矩阵
def get_mask(h, w, mask_pt: list):
    # 创建图像
    img = np.zeros((h, w), np.uint8)
    # 遍历每一根多段线
    for pl in mask_pt:
        pl = np.array(pl)
        pl[:, 0] = np.round(pl[:, 0] * w)  # x
        pl[:, 1] = np.round(pl[:, 1] * h)  # y

        # 绘制多边形
        cv2.polylines(img, [np.array(pl, dtype=np.int32)], True, 1)
        # 获取掩码
        img = cv2.fillPoly(img, [np.array(pl, dtype=np.int32)], 1)

    # cv2.imshow('Mask Image', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return img


# 计算检测框的中点（作为车辆的位置）
def calculate_midpoint(info_list):
    x_center = (float(info_list['x1']) + float(info_list['x2'])) / 2
    y_center = (float(info_list['y1']) + float(info_list['y2'])) / 2
    return [int(x_center), int(y_center)]


# 辅助函数：判断点是否在mask内
def is_point_in_mask(point, mask):
    # 实现点在多边形内的判断逻辑
    x1, y1 = point
    result = mask[y1, x1]
    # print(result)
    return result


# 计算车头时距
# 车头时距的基本概念是指在同一车道上行驶的车辆队列中，”前后两辆车“的”前端“通过同一地点的时间差（使用出口道的停止线）。
def calculate_headway_times(info_list, length_per_pixel, exit_mask):
    # 需要知道前一辆车的位置在哪
    # 基于汽车id来分
    car_dict = {}
    # 先把所有位于出口道的车辆信息，放入一个新列表中
    for track_info in info_list:
        center_x, center_y = calculate_midpoint(track_info)
        if is_point_in_mask((center_x, center_y), exit_mask):
            # 基于轨迹类型对获取每个id的在路口区域的轨迹
            if track_info['id'] not in car_dict:
                car_dict[track_info['id']] = [track_info]
            else:
                car_dict[track_info['id']].append(track_info)
    return None


# 车头间距
# 车头间距，又称为空间车头间距，是指同一车道上行驶的车辆之间（进入出口道），”前车车头“与”后车车头“之间的实际距离。
def calculate_headway_distances(info_list, length_per_pixel):
    # 需要知道前一辆车的位置在哪
    pass


# 排队长度
# 排队长度指路口进口道各转向的排队长度；定义为从路口信号灯转为绿灯时刻，该路口进口道各转向车流排队最后一辆车距离路口停止线的距离。
# 直接算每根线的直线距离吧，然后选一根最短的
def calculate_queue_length(info_list, length_per_pixel):
    # 需要判断车辆在什么情况处于排队状态
    # 需要知道停止线的位置
    pass


# 速度
# 速度可以通过计算车辆在连续两帧之间的移动距离除以时间差来计算。（用起点终点）
# 计算路口围合区域的平均速度
def calculate_speed(info_list, length_per_pixel, mask):
    # 默认帧率
    fps = 30
    # 初始化存储起点终点与速度的字典
    start_dic = {}
    end_dic = {}
    distance_dic = {}
    speed_dic = {}
    average_dic = {}

    for info in info_list:
        # 得到车辆所在位置对应的点
        mid_point = calculate_midpoint(info)
        # 先判断是否在十字路口围合区域内
        if mask[mid_point[1]][mid_point[0]] == 1:
            # 如果该id不在起点字典中，则为第一次出现，新建一个存储起点坐标
            if info['id'] not in start_dic:
                start_dic[info['id']] = [mid_point]
                # 存储时间
                start_dic[info['id']].append(info['frame'])
                # 存储类别
                start_dic[info['id']].append(info['track_cls'])
            # 如果该id已存在起点字典中，则计算终点坐标与行驶距离
            else:
                # print('----------------------------')
                # print(info['id'])
                if info['id'] not in distance_dic:
                    distance_dic[info['id']] = calculate_distance(start_dic[info['id']][0], mid_point)
                else:
                    # print(distance_dic[info['id']], calculate_distance(end_dic[info['id']][0], mid_point))
                    distance_dic[info['id']] += calculate_distance(end_dic[info['id']][0], mid_point)
                end_dic[info['id']] = [mid_point]
                end_dic[info['id']].append(info['frame'])
                # print(distance_dic[info['id']])
    # print(start_dic)
    # print(end_dic)

    # 判断起点与终点的个数是否相同，不相同则把出意外的点删掉
    if len(start_dic) != len(end_dic):
        # print('起点终点长度不相等：', len(start_dic), len(end_dic))
        del_list = []
        for car_id in start_dic:
            if car_id not in end_dic:
                del_list.append(car_id)
        for key in del_list:
            del start_dic[key]

    # 计算起点与终点的距离
    for car_id in start_dic:
        distance = distance_dic[car_id] * length_per_pixel
        # 取帧数计算时间
        time = (end_dic[car_id][1] - start_dic[car_id][1]) / fps
        speed = distance / time * 3.6
        # 如果类别信息是否已存储
        if start_dic[car_id][2] not in speed_dic:
            speed_dic[start_dic[car_id][2]] = [speed]
        else:
            speed_dic[start_dic[car_id][2]].append(speed)

    for key, values in speed_dic.items():
        # 计算每组数据的平均值
        average_value = sum(values) / len(values)
        # 将结果存储在新的字典中
        average_dic[key] = average_value
    # # 计算平均速度(m/s)
    # average_speed = sum(speed_list) / len(speed_list)
    print('average_speed', average_dic)

    return average_dic


# ---------------第一组测试数据---------------
# 读取的txt数据
txt_path = r'example\1.txt'
# 底图图片
image_path = r'example\1.jpg'
# 超参
threshold = 0.125
min_cars = 5

# 画面尺寸
# w, h = (1920, 1080)

mask = []  # 车道区域
scale_line = [[0.4934539794921875, 0.2621527777777778], [0.5608367919921875, 0.265625]]  # 比例尺线
scale_length = 4 * 3.5  # 比例尺的实际尺寸，以m为单位
entrance_areas = [[[0.4446258544921875, 0.2708333333333333], [0.4631805419921875, 0.2934027777777778],
                   [0.4905242919921875, 0.2604166666666667], [0.5618133544921875, 0.2621527777777778],
                   [0.5657196044921875, 0.001736111111111111], [0.4856414794921875, 0.001736111111111111],
                   [0.4622039794921875, 0.203125]],
                  [[0.0012664794921875, 0.5503472222222222], [0.4114227294921875, 0.5451388888888888],
                   [0.4163055419921875, 0.6927083333333334], [0.4006805419921875, 0.7239583333333334],
                   [0.3840789794921875, 0.7534722222222222], [0.3186492919921875, 0.7291666666666666],
                   [0.0950164794921875, 0.7413194444444444], [0.0032196044921875, 0.7361111111111112]],
                  [[0.5129852294921875, 0.8003472222222222], [0.5862274169921875, 0.8020833333333334],
                   [0.6086883544921875, 0.7986111111111112], [0.6233367919921875, 0.8315972222222222],
                   [0.6096649169921875, 0.8819444444444444], [0.6018524169921875, 0.953125],
                   [0.6038055419921875, 0.9930555555555556], [0.5120086669921875, 0.9930555555555556]],
                  [[0.6448211669921875, 0.3975694444444444], [0.6565399169921875, 0.3576388888888889],
                   [0.6721649169921875, 0.3333333333333333], [0.9993133544921875, 0.3611111111111111],
                   [0.9983367919921875, 0.5138888888888888], [0.9534149169921875, 0.5190972222222222],
                   [0.6516571044921875, 0.5243055555555556]]]  # 进口道区域
exit_areas = [[[0.4436492919921875, 0.2630208333333333], [0.4592742919921875, 0.2942708333333333],
               [0.4163055419921875, 0.3637152777777778], [0.4065399169921875, 0.3880208333333333],
               [0.4065399169921875, 0.5199652777777778], [0.0012664794921875, 0.5217013888888888],
               [0.0041961669921875, 0.3602430555555556], [0.3498992919921875, 0.3602430555555556],
               [0.3918914794921875, 0.3376736111111111], [0.4260711669921875, 0.2994791666666667]],
              [[0.5598602294921875, 0.2595486111111111], [0.5940399169921875, 0.2578125],
               [0.6116180419921875, 0.2873263888888889], [0.6418914794921875, 0.3480902777777778],
               [0.6575164794921875, 0.3619791666666667], [0.6692352294921875, 0.3324652777777778],
               [0.6526336669921875, 0.3098958333333333], [0.6301727294921875, 0.2647569444444444],
               [0.6086883544921875, 0.20572916666666666], [0.5969696044921875, 0.12760416666666666],
               [0.5911102294921875, 0.04600694444444445], [0.5911102294921875, -0.0008680555555555555],
               [0.5618133544921875, 0.0008680555555555555]],
              [[0.6409149169921875, 0.5512152777777778], [0.6399383544921875, 0.6727430555555556],
               [0.6760711669921875, 0.6779513888888888], [0.6790008544921875, 0.6935763888888888],
               [0.6428680419921875, 0.7352430555555556], [0.6233367919921875, 0.7595486111111112],
               [0.6086883544921875, 0.7960069444444444], [0.6252899169921875, 0.8289930555555556],
               [0.6506805419921875, 0.7769097222222222], [0.6770477294921875, 0.7352430555555556],
               [0.7336883544921875, 0.7126736111111112], [0.8176727294921875, 0.7126736111111112],
               [0.9963836669921875, 0.7039930555555556], [0.9954071044921875, 0.5442708333333334]],
              [[0.4006805419921875, 0.7248263888888888], [0.3811492919921875, 0.7560763888888888],
               [0.4163055419921875, 0.8064236111111112], [0.4358367919921875, 0.8324652777777778],
               [0.4456024169921875, 0.8862847222222222], [0.4543914794921875, 0.9626736111111112],
               [0.4543914794921875, 0.9921875], [0.5110321044921875, 0.9939236111111112],
               [0.5110321044921875, 0.8828125], [0.5129852294921875, 0.8237847222222222],
               [0.4758758544921875, 0.8203125], [0.4700164794921875, 0.8307291666666666],
               [0.4582977294921875, 0.8255208333333334], [0.4397430419921875, 0.7786458333333334],
               [0.4163055419921875, 0.7387152777777778]]]
stop_lines = [
    [[0.4456024169921875, 0.2690972222222222], [0.4582977294921875, 0.296875],
     [0.4934539794921875, 0.2638888888888889], [0.5579071044921875, 0.2621527777777778]],
    [[0.6731414794921875, 0.3333333333333333], [0.6575164794921875, 0.359375],
     [0.6448211669921875, 0.3975694444444444], [0.6526336669921875, 0.5190972222222222]],
    [[0.6243133544921875, 0.8315972222222222], [0.6086883544921875, 0.8020833333333334],
     [0.5139617919921875, 0.7986111111111112]],
    [[0.3791961669921875, 0.75], [0.3977508544921875, 0.7239583333333334],
     [0.4133758544921875, 0.6944444444444444], [0.4094696044921875, 0.5434027777777778]]]  # 停止线位置
intersection_area = [[[0.4436492919921875, 0.2647569444444444], [0.4573211669921875, 0.2960069444444444],
                      [0.4895477294921875, 0.2682291666666667], [0.5959930419921875, 0.2612847222222222],
                      [0.6155242919921875, 0.2994791666666667], [0.6370086669921875, 0.2751736111111111],
                      [0.6741180419921875, 0.3307291666666667], [0.6565399169921875, 0.3567708333333333],
                      [0.6545867919921875, 0.6727430555555556], [0.6399383544921875, 0.7404513888888888],
                      [0.6536102294921875, 0.7630208333333334], [0.6262664794921875, 0.8272569444444444],
                      [0.6096649169921875, 0.8029513888888888], [0.4680633544921875, 0.8064236111111112],
                      [0.4446258544921875, 0.7942708333333334], [0.4280242919921875, 0.8098958333333334],
                      [0.3821258544921875, 0.7526041666666666], [0.3997039794921875, 0.7248263888888888],
                      [0.4133758544921875, 0.6970486111111112], [0.4065399169921875, 0.3932291666666667],
                      [0.4231414794921875, 0.3515625], [0.4075164794921875, 0.3116319444444444]]]

# ---------------第二组测试数据---------------
# 读取的txt数据
txt_path = r'example\5.txt'
# 底图图片
image_path = r'example\5.jpg'
# 超参
threshold = 0.125
min_cars = 5

# 画面尺寸
# w, h = (3810, 2160)

mask = []  # 车道区域
scale_line = [[0.4407196044921875, 0.2517361111111111], [0.5139617919921875, 0.2534722222222222]]  # 比例尺线
scale_length = 5 * 3.5  # 比例尺的实际尺寸，以m为单位
entrance_areas = [[[0.4368133544921875, 0], [0.4368133544921875, 0.2482638888888889],
                   [0.5149383544921875, 0.25], [0.5129852294921875, 0]],
                  [[0.6838836669921875, 0.4565972222222222], [0.6838836669921875, 0.5677083333333334],
                   [0.9973602294921875, 0.5763888888888888], [0.9963836669921875, 0.4739583333333333]],
                  [[0.5276336669921875, 0.8125], [0.6125946044921875, 0.828125],
                   [0.6155242919921875, 0.9930555555555556], [0.5276336669921875, 0.9965277777777778]],
                  [[0.0002899169921875, 0.5347222222222222], [0.1321258544921875, 0.5225694444444444],
                   [0.3791961669921875, 0.5434027777777778], [0.3762664794921875, 0.6527777777777778],
                   [0.0017547607421875, 0.6145833333333334]]]  # 进口道区域
exit_areas = [[[0.5198211669921875, 0.8098958333333334], [0.4514617919921875, 0.7977430555555556],
               [0.4524383544921875, 0.9956597222222222], [0.5256805419921875, 0.9973958333333334]],
              [[0.6848602294921875, 0.5824652777777778], [0.6790008544921875, 0.6796875],
               [0.9954071044921875, 0.7057291666666666], [0.9963836669921875, 0.6085069444444444]],
              [[0.5247039794921875, 0.2526041666666667], [0.5989227294921875, 0.24913194444444445],
               [0.5959930419921875, 0.0008680555555555555], [0.5188446044921875, 0.0008680555555555555]],
              [[0.0012664794921875, 0.4105902777777778], [0.3850555419921875, 0.4296875],
               [0.3791961669921875, 0.5303819444444444], [-0.0006866455078125, 0.5026041666666666]]]
stop_lines = [[[0.4407196044921875, 0.2517361111111111], [0.5139617919921875, 0.2534722222222222]],
              [[0.6858367919921875, 0.421875], [0.6838836669921875, 0.5677083333333334]],
              [[0.6223602294921875, 0.8263888888888888], [0.5256805419921875, 0.8107638888888888]],
              [[0.3752899169921875, 0.6805555555555556], [0.3782196044921875, 0.5486111111111112]]]  # 停止线位置
intersection_area = [[[0.4407196044921875, 0.2543402777777778], [0.3801727294921875, 0.3862847222222222],
                      [0.3752899169921875, 0.6935763888888888], [0.4280242919921875, 0.7960069444444444],
                      [0.6311492919921875, 0.8272569444444444], [0.6838836669921875, 0.7421875],
                      [0.6848602294921875, 0.3845486111111111], [0.6096649169921875, 0.2560763888888889]]]

# ==================================================================
# ============================数据处理===============================
# ==================================================================

# # 读取result_txt的数据，进行后续处理
# with open(txt_path, 'r') as f:
#     lines = f.readlines()
# # 新建一个轨迹列表把这些数据储存起来
# tracks = []
# 遍历txt每一行数据
# for line in lines:
#     info_list = line.replace('\n', '').split('/')
#     # 获取属性里的每一个值
#     frame, id, x1, y1, x2, y2, conf, cls, track_cls, start_vector, end_vector = info_list
#     # 修改内部参数的属性并赋值道track中
#     track_info_dict = {'frame': int(frame), 'id': int(id), 'x1': int(x1), 'y1': int(y1), 'x2': int(x2), 'y2': int(y2),
#                        'conf': float(conf), 'cls': int(cls), 'track_cls': int(track_cls),
#                        'start_vector': eval(start_vector), 'end_vector': eval(end_vector)}
#     tracks.append(track_info_dict)
# print(tracks)

# 读取图片
img_pil = Image.open(image_path)
img_cv2 = np.array(img_pil)
img_base = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2BGR)
# 宽高从这里拿
h, w = img_base.shape[:2]

# 执行绘图算法，并获取info_list
count_result, front_colors, info_list = draw_lines(img_base, txt_path, threshold=0.125, min_cars=5)
print('info_list第一条数据展示：', info_list[0])
# print(info_list)

# -----------------------------------------------
# Step1：去归一化，并转为numpy格式，方便计算，获取length_per_pixel
scale_line = np.array(scale_line) * np.array((w, h))
print('scale_line', scale_line)
if len(scale_line) != 0 and scale_length:
    distance = calculate_distance(scale_line[0], scale_line[1])
    # 计算得到一个像素代表的实际真实长度（以m为单位）
    length_per_pixel = scale_length / distance
    print(length_per_pixel)

# intersection_mask = get_mask(h, w, intersection_area)
# speed = calculate_speed(info_list, length_per_pixel, intersection_mask)
# 出口道
exit_mask = get_mask(h, w, exit_areas)
calculate_headway_times(info_list, length_per_pixel, exit_mask)
