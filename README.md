## AWS_DeepRacer 경진대회

2024.12 ~ 2025.02 (3개월)

## 대회 개요

AWS DeepRacer를 활용한 인공지능 강화학습 기반의 자율주행 자동차 대회

- 목표
    - AWS DeepRacer 환경에서 최적의 보상 함수와 경로 추적 로직 설계
    - 오프라인 RC카에도 적용해 실제 자율주행 검증
- 역할: 스피드 트랙 보상 함수 설계, 웨이포인트 기반 경로 추적 로직 구현, 실제 차량 적용(하드웨어 제어) 총괄

## 프로젝트 소개 영상

<모의 주행 테스트 영상>



https://github.com/user-attachments/assets/1e4781c5-095d-48cf-8009-3d4356a5324a



## 주요 기능

### ✅ 최적의 웨이포인트 추출

웨이포인트 추출 및 최적 경로 설정
- AWS DeepRacer에서 제공하는 .npy 트랙 데이터를 불러와 중앙선, 내측, 외측 웨이포인트를 추출
- Shapely 라이브러리를 통해 트랙 변환
    
    LineString 사용하여 트랙 경계를 다각형 형태로 변환
    
    LinearRing을 통해 트랙이 Closed Loop 인지 확인
    
- 트랙 폭 조정 및 최적 웨이포인트 생성
    
    트랙 폭을 PERC_WIDTH = 0.8로 조정하여 차량이 안정적으로 주행할 수 있도록 웨이포인트 조정
    
    내부 및 외부 경계를 재설정 한 후 최적화된 주행 경로 확보

    ![image](https://github.com/user-attachments/assets/3d46ba89-df56-413c-b681-212124505479)

  

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

![image](https://github.com/user-attachments/assets/e38c1d25-bfd4-464d-abbb-c06358666e6d)



## 아키텍처 구조

![image](https://github.com/user-attachments/assets/e636973a-0dc4-4522-b4d2-1b8a84ec9706)


## **담당역할: Fast Track 및 하드웨어 담당**

- Fast Track 웨이포인트, 액션 스페이스, reward function 작성
- 차량 제어 담당

## **프로젝트 성과**

- 2024 AWS DeepRacer 챔피언십 리그 장려상
