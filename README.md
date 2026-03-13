# 2024 AWS DeepRacer 자율주행 경진대회

## 프로젝트 영상

<주행 테스트 영상>

https://github.com/user-attachments/assets/1e4781c5-095d-48cf-8009-3d4356a5324a




## 개요

이 워크스페이스는 AWS DeepRacer 환경에서 강화학습 기반 자율주행 레이싱을 수행한 프로젝트입니다.
Reward function를 설계해 시뮬레이터에서 모델을 학습하고, 학습한 모델을 실제 차량에 업로드해 현실 환경에서 주행까지 검증했습니다.

저장소 안에는 DRfC 실행 환경, 차량 API 예제, 실험용 노트북 등이 함께 포함되어 있지만, 이 README는 제가 직접 담당한 [`drfc-aws-main/reward_function.py`](drfc-aws-main/reward_function.py)에 초점을 맞춰 정리했습니다.

## 담당 범위

제가 맡은 작업은 [`drfc-aws-main/reward_function.py`](drfc-aws-main/reward_function.py)의 설계와 튜닝이었습니다.

- 주행 보상 로직 설계
- waypoint 기반 목표 조향 방식 구현
- 시뮬레이터 학습용 reward signal 단순화 및 안정화
- 실차 주행까지 고려한 steering-oriented reward 구조 정리

## reward_function.py 소개

차량이 현재 위치에서 트랙을 따라가기 위해 앞쪽 목표 지점을 바라보도록 만들고, 실제 조향값이 그 목표 조향각에 가까울수록 더 높은 보상을 주는 구조로 이루어져 있습니다.

즉, 단순히 중심선과의 거리만 평가하는 방식이 아니라, 차량이 다음 구간을 자연스럽게 따라가도록 조향 행동 자체를 점수화하는 구조입니다.

## 코드 구조

| 함수 | 역할 |
|---|---|
| `dist(point1, point2)` | 두 점 사이의 유클리드 거리 계산 |
| `rect(r, theta)` | 극좌표를 직교좌표로 변환 |
| `polar(x, y)` | 직교좌표를 극좌표로 변환 |
| `angle_mod_360(angle)` | 각도를 `-180 ~ 180` 범위로 정규화 |
| `up_sample(waypoints, factor)` | waypoint 사이를 보간해 더 촘촘한 경로 생성 |
| `get_target_point(params)` | 차량 앞쪽에서 추종할 목표 지점 선택 |
| `get_target_steering_degree(params)` | 목표 지점을 향한 이상적인 조향각 계산 |
| `score_steer_to_point_ahead(params)` | 실제 조향과 목표 조향의 차이를 보상으로 변환 |
| `reward_function(params)` | 최종 reward 반환 |

## 동작 방식

보상 함수는 아래 흐름으로 동작합니다.

1. waypoint 경로를 업샘플링해서 더 촘촘한 추종 기준점을 만듭니다.
2. 현재 차량 위치와 가장 가까운 지점을 찾습니다.
3. 현재 위치에서 일정 반경 밖에 있는 첫 번째 지점을 "앞쪽 목표 지점"으로 잡습니다.
4. 차량 heading과 목표 지점 방향을 비교해 이상적인 조향각을 계산합니다.
5. 실제 `steering_angle`이 목표 조향각과 가까울수록 더 큰 reward를 줍니다.

점수 계산은 아래 방식을 따릅니다.

```python
error = (steering_angle - best_stearing_angle) / 60.0
score = 1.0 - abs(error)
reward = max(score, 0.01)
```

이 구조는 조향 오차가 작으면 높은 점수를, 크면 낮은 점수를 주되 reward가 지나치게 0에 가까워지지 않도록 최소값을 유지합니다.

AWS 시뮬레이터 상에서 reward function을 통해 학습이 진행되고 학습된 모델은 실제 차량에 업로드 되어 현실에서 트랙을 주행합니다.
