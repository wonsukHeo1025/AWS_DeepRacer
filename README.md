![image.png](attachment:d934ea8f-e028-42cf-9877-d80fc2883431:image.png)

![IMG_0679.jpeg](attachment:c9263dd1-c3f9-4444-be41-e62c8e38a5d8:IMG_0679.jpeg)

![IMG_0806.jpeg](attachment:aa136496-9803-42b2-a97f-e1682d4c834d:IMG_0806.jpeg)

2024.12 ~ 2025.02 (3개월)

## 대회 개요

AWS DeepRacer를 활용한 인공지능 강화학습 기반의 자율주행 자동차 대회

- 목표
    - AWS DeepRacer 환경에서 최적의 보상 함수와 경로 추적 로직 설계
    - 오프라인 RC카에도 적용해 실제 자율주행 검증
- 역할: 스피드 트랙 보상 함수 설계, 웨이포인트 기반 경로 추적 로직 구현, 실제 차량 적용(하드웨어 제어) 총괄

## 프로젝트 소개 영상

<모의 주행 테스트 영상>

[모의 주행 영상.mp4](attachment:89bce07d-1de9-42a4-b1bd-cc7b550840f8:모의_주행_영상.mp4)

## 주요 기능

### ✅ 최적의 웨이포인트와 액션 스페이스 추출

1. 웨이포인트 추출 및 최적 경로 설정
- AWS DeepRacer에서 제공하는 .npy 트랙 데이터를 불러와 중앙선, 내측, 외측 웨이포인트를 추출
- Shapely 라이브러리를 통해 트랙 변환
    
    LineString 사용하여 트랙 경계를 다각형 형태로 변환
    
    LinearRing을 통해 트랙이 Closed Loop 인지 확인
    
- 트랙 폭 조정 및 최적 웨이포인트 생성
    
    트랙 폭을 PERC_WIDTH = 0.8로 조정하여 차량이 안정적으로 주행할 수 있도록 웨이포인트 조정
    
    내부 및 외부 경계를 재설정 한 후 최적화된 주행 경로 확보
    
    ```python
    import glob
    import numpy as np
    from shapely.geometry import Point, Polygon, LineString
    import matplotlib.pyplot as plt
    
    # 트랙 데이터 로드
    waypoints = np.load(numpy_file_path)
    
    # 중앙선, 내측, 외측 웨이포인트 추출
    center_line = waypoints[:,0:2]
    inner_border = waypoints[:,2:4]
    outer_border = waypoints[:,4:6]
    
    # Shapely를 이용한 트랙 변환
    l_center_line = LineString(center_line)
    l_inner_border = LineString(inner_border)
    l_outer_border = LineString(outer_border)
    road_poly = Polygon(np.vstack((outer_border, np.flipud(inner_border))))
    print("Is loop/ring? ", l_center_line.is_ring)
    ```
    
    ![image.png](attachment:4eb16eb1-50b5-4a3f-8bb4-f5efdfa02873:image.png)
    
         < 생성된 웨이포인트 결과물 사진 >
    
- 트랙 폭 조정 및 최적 경로 계산

```python
def dist_2_points(x1, x2, y1, y2):
    return ((x1-x2)**2 + (y1-y2)**2)**0.5

def x_perc_width(waypoint, perc_width):
    center_x, center_y, inner_x, inner_y, outer_x, outer_y = waypoint
    width = dist_2_points(inner_x, outer_x, inner_y, outer_y)
    delta_x = outer_x-inner_x
    delta_y = outer_y-inner_y
    inner_x_new = inner_x + delta_x/2 * (1-perc_width)
    outer_x_new = outer_x - delta_x/2 * (1-perc_width)
    inner_y_new = inner_y + delta_y/2 * (1-perc_width)
    outer_y_new = outer_y - delta_y/2 * (1-perc_width)
    return [center_x, center_y, inner_x_new, inner_y_new, outer_x_new, outer_y_new]

PERC_WIDTH = 0.8
waypoints_new = [x_perc_width(waypoint, perc_width=PERC_WIDTH) for waypoint in waypoints]
waypoints_new = np.asarray(waypoints_new)
```

→ 각 웨이포인트의 내측과 외측을 보정하여 새로운 웨이포인트 생성

![image.png](attachment:94dd01bb-cbdc-40d5-95c6-9def673cbf80:image.png)

      < 생성된 웨이포인트 사진 >

![image.png](attachment:7f5a42a4-173d-44dc-ad39-ff51942efac2:image.png)

2. 액션스페이스 추출

- 트랙의 각 웨이포인트에서 **곡률을 계산**하여 차량의 최적 속도를 설정

```python
# 곡률을 계산하는 함수
def circle_radius(coords):
    x1, y1, x2, y2, x3, y3 = [i for sub in coords for i in sub]
    a = x1*(y2-y3) - y1*(x2-x3) + x2*y3 - x3*y2
    b = (x1**2+y1**2)*(y3-y2) + (x2**2+y2**2)*(y1-y3) + (x3**2+y3**2)*(y2-y1)
    c = (x1**2+y1**2)*(x2-x3) + (x2**2+y2**2)*(x3-x1) + (x3**2+y3**2)*(x1-x2)
    d = (x1**2+y1**2)*(x3*y2-x2*y3) + (x2**2+y2**2) * (x1*y3-x3*y1) + (x3**2+y3**2)*(x2*y1-x1*y2)
    
    try:
        r = abs((b**2+c**2-4*a*d) / abs(4*a**2)) ** 0.5
    except:
        r = 999  # 직선 구간의 경우 곡률이 무한대
    return r
    
# 곡률을 기반으로 최적 속도 계산
def optimal_velocity(track, min_speed, max_speed, look_ahead_points):
    radius = [circle_radius([track[i-1], track[i], track[(i+1) % len(track)]]) for i in range(len(track))]
    v_min_r = min(radius)**0.5
    constant_multiple = min_speed / v_min_r
    max_velocity = [(constant_multiple * i**0.5) for i in radius]
    velocity = [min(v, max_speed) for v in max_velocity]
    return velocity
```

- K-Means 클러스터링 적용 → 불필요한 액션스페이스 제거, 조합 최적화

```python
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import MiniBatchKMeans

# 액션 스페이스 정규화 및 클러스터링
X = all_actions[['velocity', 'steering']]
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)
model = MiniBatchKMeans(n_clusters=21).fit(X_scaled)
X_centroids = scaler.inverse_transform(model.cluster_centers_)

# 최적화된 액션 스페이스 저장
action_space = pd.DataFrame(X_centroids, columns=['velocity', 'steering'])
print(action_space)
```

![image.png](attachment:f107d35d-1c76-4fa8-bf03-634fe38757ea:image.png)

< 최종 추출된 액션 스페이스 >

### ✅ 최적의 Reward [Function.py](http://Function.py) 작성

- 차량이 현재 위치에서 목표로 해야 할 웨이포인트를 찾고, 그에 따라 조향각을 조정하도록 설정

```python
import math

def dist(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

def polar(x, y):
    r = (x ** 2 + y ** 2) ** .5
    theta = math.degrees(math.atan2(y, x))
    return r, theta

def angle_mod_360(angle):
    angle = angle % 360
    return angle if angle <= 180 else angle - 360

def get_target_point(params, waypoints):
    car = [params['x'], params['y']]
    distances = [dist(p, car) for p in waypoints]
    min_dist = min(distances)
    i_closest = distances.index(min_dist)
    return waypoints[(i_closest + 5) % len(waypoints)]  # 5개 앞의 웨이포인트를 목표로 설정
```

- 차량이 최적 조향각을 유지하도록 보상 점수를 부여하는 함수 구현

```python
def get_target_steering_degree(params, waypoints):
    tx, ty = get_target_point(params, waypoints)
    dx, dy = tx - params['x'], ty - params['y']
    _, target_angle = polar(dx, dy)
    return angle_mod_360(target_angle - params['heading'])

def score_steer_to_point_ahead(params, waypoints):
    best_steering_angle = get_target_steering_degree(params, waypoints)
    error = (params['steering_angle'] - best_steering_angle) / 60.0
    return max(1.0 - abs(error), 0.01)  # 최소 보상 0.01
```

- 차량이 올바른 속도를 유지하면서 목표 경로를 따르도록 보상 시스템을 통합

```python
def reward_function(params):
    return float(score_steer_to_point_ahead(params, waypoints))
```

### ✅ 하드웨어 적용 및 실험

- 여러 모델을 만들어서 파라미터와 보상함수 실험

![image.png](attachment:c9ee2b88-f0d5-4934-a150-d9bdc2e37c6e:image.png)

- AWS S3에 저장한 model.pb 모델을 다운로드하고 차량 내부로 다운로드

```python
import boto3
import os

s3 = boto3.client('s3')
BUCKET_NAME = 'my-deepracer-models'
MODEL_NAME = 'deepracer-speed-model.pb'

# 모델 다운로드
s3.download_file(BUCKET_NAME, MODEL_NAME, f'/opt/aws/deepracer/artifacts/{MODEL_NAME}')
```

- deepracer-vehicle-api를 통해 모델을 load, 적용

```python
import deepracer_vehicle_api as dv

vehicle = dv.DeepRacerVehicleAPI()
vehicle.load_model(f'/opt/aws/deepracer/artifacts/{MODEL_NAME}')
```

- 차량 영점 조절을 위한 캘리브레이션

![image.png](attachment:1341943c-8a9f-4e18-95e4-87d9150a3f7c:image.png)

- deepracer-vehicle-api를 통한 원격 제어

```python
# 차량 초기화
vehicle = dv.DeepRacerVehicleAPI()

# 속도 및 조향 설정
vehicle.set_throttle(0.5)  # 50% 속도
vehicle.set_steering_angle(-15)  # 좌측으로 15도 조향
```

- deepracer-vehicle-api를 통한 모델 실행

![image.png](attachment:6db577fe-7e1a-499f-b95d-ecfcd04802d6:image.png)

## 아키텍처 구조

![image.png](attachment:b27e1686-0351-4bbf-97e5-1bdd625f9cdb:image.png)

## **담당역할: Fast Track 및 하드웨어 담당**

- Fast Track 웨이포인트, 액션 스페이스, reward function 작성
- 차량 제어 담당

## **프로젝트 성과**

- 2024 AWS DeepRacer 챔피언십 리그 장려상
