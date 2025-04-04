import math
"""
waypoints2 = [
  [-1.60792, -1.51349],
  [-1.40371, -1.57758],
  [-1.18953, -1.62832],
  [-0.96345, -1.66708],
  [-0.72291, -1.69498],
  [-0.46509, -1.71309],
  [-0.18814, -1.72269],
  [0.10614, -1.72577],
  [0.41389, -1.72556],
  [0.72164, -1.72565],
  [1.02939, -1.72623],
  [1.33468, -1.72389],
  [1.62757, -1.70287],
  [1.89923, -1.6521],
  [2.14015, -1.56716],
  [2.3431, -1.44925],
  [2.50311, -1.3027],
  [2.61634, -1.13327],
  [2.67832, -0.94737],
  [2.68248, -0.75305],
  [2.61891, -0.5632],
  [2.495, -0.39134],
  [2.32253, -0.24394],
  [2.10873, -0.12508],
  [1.86278, -0.03424],
  [1.59614, 0.03523],
  [1.32288, 0.12358],
  [1.05606, 0.22651],
  [0.79533, 0.34292],
  [0.54037, 0.47188],
  [0.29092, 0.61257],
  [0.04672, 0.76416],
  [-0.19247, 0.92588],
  [-0.42591, 1.09626],
  [-0.66597, 1.25006],
  [-0.91364, 1.38066],
  [-1.16813, 1.48177],
  [-1.42661, 1.54771],
  [-1.68429, 1.57396],
  [-1.93472, 1.55736],
  [-2.17035, 1.49676],
  [-2.38317, 1.39255],
  [-2.56486, 1.24608],
  [-2.70597, 1.05887],
  [-2.8136, 0.84474],
  [-2.88637, 0.60652],
  [-2.92199, 0.34634],
  [-2.91569, 0.06585],
  [-2.86028, -0.22637],
  [-2.76456, -0.48953],
  [-2.64087, -0.71764],
  [-2.4974, -0.9134],
  [-2.33938, -1.08026],
  [-2.17, -1.22111],
  [-1.99089, -1.33783],
  [-1.80345, -1.43431],
  [-1.60792, -1.51349]
]
"""

#두 점 간의 유클리드 거리(직선 거리)를 계산
def dist(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

#극좌표를 직교 좌표로 변환
def rect(r, theta):
    x = r * math.cos(math.radians(theta))
    y = r * math.sin(math.radians(theta))
    return x, y

#직교좌표를 극좌표로 변환
def polar(x, y):
    r = (x ** 2 + y ** 2) ** .5
    theta = math.degrees(math.atan2(y,x))
    return r, theta

#입력 각도를 -180에서 +180 범위로 조정한다.
def angle_mod_360(angle):
    n = math.floor(angle/360.0)
    angle_between_0_and_360 = angle - n*360.0
    if angle_between_0_and_360 <= 180.0:
        return angle_between_0_and_360
    else:
        return angle_between_0_and_360 - 360

#웨이포인트 간격을 좁혀주는 업샘플링. waypoints를 넣고 factor는 웨이포인트 간에 추가할 개수를 의미, 더 세밀하게 경로를 따를 수 있도록 한다.
def up_sample(waypoints, factor):
    p = waypoints
    n = len(p)

    return [[i / factor * p[(j+1) % n][0] + (1 - i / factor) * p[j][0],
             i / factor * p[(j+1) % n][1] + (1 - i / factor) * p[j][1]] for j in range(n) for i in range(factor)]


def get_target_point(params):
    #업샘플링 된 웨이포인트 리스트를 가져오기
    waypoints = up_sample(params, 20)
    #차량 위치 가져오기
    car = [params['x'], params['y']]
    #distances : 차량과 업샘플링된 각 웨이포인트 사이의 거리 리스트
    distances = [dist(p, car) for p in waypoints]
    min_dist = min(distances) # 가장 가까운 웨이포인트와의 거리
    i_closest = distances.index(min_dist) # 가장 가까운 웨이포인트 인덱스
    #차량이 현재 위치에서 목표로 할 다음 경로를 추적하는 첫 번째 기준
    n = len(waypoints)
    #가장 가까운 웨이포인트를 시작으로 웨이포인트를 순서대로 재배열
    waypoints_starting_with_closest = [waypoints[(i+i_closest) % n] for i in range(n)]
    # 차량이 트랙 중앙에서 트랙 폭의 90% 안에 머물도록 유도
    r = params['track_width'] * 0.9
    # 각 웨이포인트가 반경 r 안에 있는지 여부를 나타내는 리스트
    # True는 반경 안, False는 반경 밖이다. 그럼 0.9r이면 차에서 트랙 너비를 한참 초과 하는 거 아닌가?
    is_inside = [dist(p, car) < r for p in waypoints_starting_with_closest]
    # 차량 반경 밖에 있는 첫 번째 웨이포인트의 인덱스
    i_first_outside = is_inside.index(False)
    # 차량 반경 내에 모든 웨이포인트가 포함된 경우 가장 가까운 웨이포인트 반환.
    if i_first_outside < 0: 
        return waypoints[i_closest]

    return waypoints_starting_with_closest[i_first_outside]
    # 타겟 웨이포인트를 반환하는 것이다. 궁금증 : r 값을 줄이면 바라보는 웨이포인트가 좀 더 가까워지는 것인가?

def get_target_steering_degree(params):
    #목표점 tx,ty
    tx, ty = get_target_point(params)
    car_x = params['x']
    car_y = params['y']
    #벡터방향 dx,dy
    dx = tx-car_x
    dy = ty-car_y
    heading = params['heading']

    _, target_angle = polar(dx, dy)

    steering_angle = target_angle - heading
    # 핸들 각도를 결정
    return angle_mod_360(steering_angle)

# 리워드 점수 계산
def score_steer_to_point_ahead(params):
    best_stearing_angle = get_target_steering_degree(params)
    steering_angle = params['steering_angle']

    error = (steering_angle - best_stearing_angle) / 60.0  # 60 degree is already really bad

    score = 1.0 - abs(error)

    return max(score, 0.01)  # optimizer is rumored to struggle with negative numbers and numbers too close to zero


def reward_function(params):
    return float(score_steer_to_point_ahead(params))        