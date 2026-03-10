# 2024 AWS DeepRacer 자율주행 경진대회

## 개요

이 저장소는 AWS DeepRacer 경진대회 워크스페이스 중 제가 직접 담당한 `reward_function.py` 설계와 튜닝 과정을 정리한 포트폴리오 문서입니다.

프로젝트 전체에는 클라우드 학습 인프라, 차량 API, 하드웨어 실험, 경로 최적화 실험이 함께 포함되어 있지만, 제 담당 범위는 오직 [`drfc-aws-main/reward_function.py`](drfc-aws-main/reward_function.py) 설계였습니다.

중요한 점은 다음과 같습니다.

- 최적 경로 생성, A* 경로 탐색, 레이싱 라인 계산은 제 담당이 아니었습니다.
- 저는 팀원이 만든 최적 레이싱 라인 결과와 AWS 기본 Object Avoidance 구조를 받아, 이를 실제 대회용 보상함수로 통합하고 튜닝하는 역할을 맡았습니다.
- 최종적으로 장애물 회피와 안정적인 라인 추종을 동시에 만족하는 보상함수를 설계했고, 해당 세팅으로 장려상을 수상했습니다.

실험 로그 기준 최고 기록은 `00:11.5`였고, 실차 기준 `set_speed = 65`에서 안정적으로 주행했으며 실제 랩타임은 대략 12초대였습니다.

## 담당 범위

| 영역 | 파일 | 구현한 내용 |
|---|---|---|
| Reward Function Design | [`drfc-aws-main/reward_function.py`](drfc-aws-main/reward_function.py) | Object Avoidance 대회용 최종 보상함수 설계, 레이싱 라인 추종 보상과 장애물 회피 보상의 통합, 장애물별 좌우 위치 유도 로직 설계, reward weight 및 조건 튜닝 |

## 담당 범위 제외

아래 항목들은 프로젝트에는 포함되어 있지만 제 직접 담당 범위는 아니었습니다.

- A* 기반 경로 최적화 및 레이싱 라인 생성
- 트랙 `.npy` 분석 및 최적 waypoint 산출


## 역할 분담

역할 분담을 명확히 하기 위해, 보상함수와 외부 입력을 구분해서 설명합니다.

- `racing_track` 좌표 자체는 팀원이 생성한 최적 경로 결과입니다.
- 저는 그 좌표를 직접 생성한 것이 아니라, 보상함수 안에서 어떻게 점수화할지 설계했습니다.
- 즉, 제 역할은 경로를 만드는 것이 아니라 그 경로를 얼마나 잘 따라가고, 장애물을 얼마나 안정적으로 피하는지를 reward로 정의하는 것이었습니다.

## reward_function.py 설계 목표

제가 설계한 보상함수는 AWS DeepRacer Object Avoidance 환경에서 아래 목표를 동시에 만족하도록 구성되었습니다.

- 팀원이 만든 최적 레이싱 라인을 안정적으로 따라가도록 유도
- obstacle 상황에서 단순 감속이 아니라 충돌 가능성이 낮은 좌우 위치를 보상으로 유도
- 차량이 라인에서 멀어지거나 heading이 크게 틀어졌을 때 과감하게 패널티 부여
- 속도와 라인 추종 사이의 균형을 맞춰 실제 차량에서도 재현 가능하도록 유도

## reward_function.py 상세 설명

현재 [`drfc-aws-main/reward_function.py`](drfc-aws-main/reward_function.py)는 크게 6개의 층으로 구성됩니다.

### 1. 기하 계산 보조 함수

보상함수 앞부분에는 거리, 선분과의 거리, 방향 차이 계산을 위한 helper function이 들어 있습니다.

- 두 점 사이 유클리드 거리 계산
- 차량과 레이싱 라인 사이의 수직거리 계산
- 차량 heading과 레이싱 라인 진행 방향 차이 계산
- 장애물과 차량의 거리 계산

이 부분은 reward의 기반이 되는 측정 계층입니다.

### 2. 레이싱 라인 입력

보상함수 내부에는 `racing_track = [[x, y, optimal_speed, heading], ...]` 형태의 좌표 배열이 들어 있습니다.

- `x, y`: 기준 레이싱 라인 위치
- `optimal_speed`: 해당 구간에서 목표 속도
- `heading`: 해당 구간의 진행 방향 정보

이 배열은 제가 생성한 경로가 아니라, 팀원이 만든 최적 경로 결과를 reward에 반영하기 위해 사용한 입력 데이터입니다.

### 3. 기본 보상과 진행률 보상

보상은 먼저 기본값 `1.0`에서 시작하고, 여기에 `progress / 100.0`을 더합니다.

- 완주 전에도 progress가 오를수록 조금씩 보상이 증가
- 초반 학습에서 아무것도 못 배우는 상태를 줄이고, 전진 자체에 대한 최소한의 학습 신호를 주기 위한 구성

즉, 이 보상은 “일단 앞으로 가는 것” 자체를 전혀 무시하지 않도록 만든 안전장치입니다.

### 4. 레이싱 라인 추종 보상

레이싱 라인 보상은 차량이 현재 어느 정도 정확하게 최적 라인을 따라가고 있는지를 계산합니다.

- 현재 차량과 가장 가까운 레이싱 라인 포인트 2개를 찾음
- 그 두 점이 이루는 선분과 차량 위치 사이의 거리를 계산
- 차량이 레이싱 라인에 가까울수록 더 큰 보상을 부여

현재 코드에서는 아래 형태로 반영됩니다.

```python
reward += max(1e-3, 1.0 - (distance_line / (track_width * 0.5))) * 1.3
```

이 항목의 목적은 차가 중앙선 근처가 아니라 최적 주행 라인 근처를 유지하게 만드는 것입니다.

### 5. 최적 속도 보상

레이싱 라인 각 포인트에는 목표 속도가 함께 들어 있습니다. 보상함수는 현재 차량 속도와 이 목표 속도의 차이를 비교해 속도 보상을 추가합니다.

```python
reward += max(1e-3, 1.0 - (speed_diff / optimal_speed)) * 1.8
```

이 항목의 핵심은 단순히 빠르게 달리게 만드는 것이 아닙니다.

- 직선 구간에서는 빠른 속도 유지
- 곡선이나 회피 구간에서는 과속 억제
- 레이싱 라인 설계에서 의도한 속도 프로파일을 학습에 반영

즉, “빠를수록 좋다”가 아니라 “구간에 맞는 속도를 택할수록 좋다”는 구조입니다.

### 6. 방향 패널티와 오프트랙 패널티

차량이 레이싱 라인을 지나가더라도 heading이 지나치게 틀어져 있으면 안정적인 주행으로 보기 어렵습니다. 이를 위해 방향 차이 패널티가 들어 있습니다.

- 차량 방향과 레이싱 라인 진행 방향 차이가 `45도`를 넘으면 전체 reward에 `0.7`을 곱함

또한 안전성과 학습 명확성을 위해 하드 패널티도 둡니다.

- 바퀴가 트랙 밖으로 나가면 즉시 `1e-3`
- `distance_from_center >= track_width / 2`이면 즉시 `1e-3`

이 부분은 “회복 가능한 실수”와 “즉시 실패로 봐야 하는 상태”를 구분하기 위한 장치입니다.

### 7. 장애물 회피 보상

Object Avoidance 환경에서는 레이싱 라인만 따라가면 성능이 나오지 않았습니다. 그래서 보상함수 안에서 장애물 정보를 별도로 읽어 회피 보상을 추가했습니다.

사용하는 주요 입력은 다음과 같습니다.

- `objects_location`
- `closest_objects`
- `objects_left_of_center`
- `is_left_of_center`

먼저 차량과 다음 장애물 사이의 거리를 계산한 뒤, 현재 차량이 장애물과 같은 차선에 있는지를 판정합니다.

- 같은 차선이면 거리 구간에 따라 보상을 줄이거나 페널티를 줌
- 다른 차선이면 충돌 가능성이 낮으므로 보상을 더 크게 줌

현재 코드는 같은 차선일 때 다음처럼 거리별로 보상을 조정합니다.

- `0.5 <= distance < 0.8`: `avoid_reward = 0.5`
- `0.3 <= distance < 0.5`: `avoid_reward = 0.01`
- `distance < 0.3`: `avoid_reward = 1e-3`
- 충분히 멀면 `avoid_reward = 1.0`

이 구조는 obstacle을 “보면 피하라”가 아니라 “같은 차선에 가까이 붙을수록 손해”로 학습시키기 위한 것입니다.

### 8. 장애물별 좌우 위치 유도 보상

이 보상함수의 핵심 차별점은 planner처럼 차선을 계산하는 것이 아니라, 특정 장애물 인덱스에서 어느 쪽 위치가 유리한지를 reward로 직접 유도한다는 점입니다.

현재 코드 기준으로는 다음 규칙을 둡니다.

- 0번 장애물: 오른쪽 위치 선호
- 1번 장애물: 왼쪽 위치 선호
- 2번 장애물: 오른쪽 위치 선호

이를 위해 `is_left_of_center` 값을 사용해 차량이 현재 왼쪽에 있는지 오른쪽에 있는지를 확인하고, 장애물 인덱스별로 보상을 다르게 부여합니다.

```python
obstacle_reward = (
    3.5 * avoid_reward
    + 2.0 * rewardRight0
    + 2.0 * rewardLeft1
    + 2.0 * rewardRight2
)
reward += obstacle_reward
```

이 구조 덕분에 차량은 단순히 장애물을 늦게 피하는 것이 아니라, 더 일찍 유리한 쪽 위치로 이동하도록 학습할 수 있었습니다.

## reward_function.py가 실제로 해결한 문제

실험 과정에서 확인한 핵심 문제와, 보상함수 수준에서 어떻게 대응했는지는 아래와 같습니다.

| 문제 | 단순한 접근 | 실제 한계 | 최종 reward에서의 대응 |
|---|---|---|---|
| 레이싱 라인만 따라감 | 최적 라인 근접 보상만 사용 | object 환경에서 장애물 충돌 빈발 | obstacle distance + same-lane 판정 추가 |
| 장애물을 너무 늦게 회피함 | 충돌 직전 패널티만 부여 | 회피 시작 시점이 늦음 | 장애물별 좌우 위치 유도 보상 추가 |
| 과속으로 회피 실패 | 빠를수록 보상 | 곡선/장애물 구간 제어 불안정 | 구간별 optimal speed 보상 사용 |
| 라인은 맞는데 heading이 틀어짐 | 거리만 보상 | zig-zag와 흔들림 발생 | direction difference 패널티 추가 |
| 학습이 쉽게 과적합됨 | 학습 시간만 증가 | 특정 장애물 패턴만 학습 | reward weight와 조건을 반복 조정 |

## 실험 로그 기반 개선 과정

엑셀로 관리한 실험 기록을 기준으로, 최종 보상함수는 여러 실패를 거쳐 수렴한 결과였습니다.

| 단계 | 모델 | reward 관점의 실험 포인트 | 관찰 | 결론 |
|---|---|---|---|---|
| 초기 시도 | `hw01-obj` | `r = 0.9`, continuous action space | Object Avoidance 환경에서 안정성이 부족 | reward 신호가 충분히 명확하지 않았음 |
| 1차 개선 | `hw02-obj`, `hw02-obj-clone` | discrete action space로 전환 | completion은 높아졌지만 1번 장애물 통과 실패 | 레이싱 라인 보상만으로는 부족 |
| 중간 개선 | `hw03-obj` ~ `hw09-obj` | discount factor 조정, `r = 0.5`, 속도/조향 세분화 | 라인 추종은 좋아졌지만 object 환경 대응이 불완전 | 회피 보상을 reward 안에 직접 넣어야 함 |
| 최종 통합 | `integrated1` | 팀원 경로 결과 + OA 보상 변형 + 장애물별 좌우 위치 유도 보상 | `set_speed = 65`에서 안정적 주행, best lap `00:11.5` | 최종 제출 및 수상 모델 |
| 과적합 검증 | `integrated1-clone-clone` | 동일 구조 장시간 학습 (`9h`) | 첫 번째 장애물 왼쪽 틈으로 파고드는 과적합 발생 | 무작정 오래 학습시키는 것은 역효과 가능 |

## 실험에서 얻은 인사이트

- Object Avoidance 환경에서는 레이싱 라인 추종 reward만으로는 충분하지 않았다.
- reward 안에서 장애물 거리, 같은 차선 여부, 장애물별 좌우 위치 선호를 직접 분리해 주는 것이 훨씬 효과적이었다.
- planner 없이도 좌우 위치 선호를 reward로 유도하는 방식이 구현과 튜닝 면에서 단순하고 강력했다.
- 학습 시간을 늘리는 것보다 reward 구조를 더 명확하게 만드는 것이 성능에 더 큰 영향을 줬다.
- 장시간 clone 학습은 개선이 아니라 특정 obstacle 패턴에 대한 과적합을 일으킬 수 있었다.

## 최종 검증 환경

최종 reward function을 검증할 때 사용한 대표 설정은 아래와 같습니다.

| 항목 | 값 |
|---|---|
| 환경 | AWS DeepRacer Object Avoidance |
| 최종 모델 | `integrated1` |
| Action Space | discrete `21` actions |
| Learning Rate | `0.0003` |
| Discount Factor | `0.9` |
| Training Time | `4.5h` |
| 최고 기록 | `00:11.5` |
| 실차 기준 | `set_speed = 65`, 약 `12초대` |

## 액션 스페이스 요약

아래 action space는 최종 reward function을 검증할 때 사용한 학습 설정입니다.

- action 개수: `21`
- steering 범위: `-30.0 ~ 30.0`
- speed 범위: `1.3 ~ 3.7544`

<details>
<summary>사용한 action space 전체 보기</summary>

```python
from aicastle.deepracer.drfc.aws import drfc
drfc.set_model_metadata({
    "action_space": [
        {"steering_angle": 6.6347, "speed": 2.3099},
        {"steering_angle": 3.8378, "speed": 3.7494},
        {"steering_angle": 12.5795, "speed": 1.6743},
        {"steering_angle": 0.0256, "speed": 3.1353},
        {"steering_angle": 0.7976, "speed": 1.3572},
        {"steering_angle": -1.2044, "speed": 2.2898},
        {"steering_angle": 1.8639, "speed": 2.7392},
        {"steering_angle": 11.7137, "speed": 1.3335},
        {"steering_angle": 4.2553, "speed": 1.6776},
        {"steering_angle": 23.2229, "speed": 1.3321},
        {"steering_angle": -11.6405, "speed": 2.2051},
        {"steering_angle": 17.4536, "speed": 2.2852},
        {"steering_angle": 9.5605, "speed": 1.9713},
        {"steering_angle": -0.8296, "speed": 1.9318},
        {"steering_angle": 14.3511, "speed": 2.8269},
        {"steering_angle": -11.2569, "speed": 2.7161},
        {"steering_angle": 22.1874, "speed": 1.7366},
        {"steering_angle": -9.8472, "speed": 3.7544},
        {"steering_angle": -8.0276, "speed": 1.6672},
        {"steering_angle": 30.0, "speed": 1.3},
        {"steering_angle": -30.0, "speed": 1.3},
    ],
})
```

</details>

## 관련 파일

| 파일 | 의미 |
|---|---|
| [`drfc-aws-main/reward_function.py`](drfc-aws-main/reward_function.py) | 제가 직접 설계한 최종 보상함수 |
| [`drfc-aws-main/02_Setup.ipynb`](drfc-aws-main/02_Setup.ipynb) | reward를 학습 설정에 연결하는 참고 파일 |
| [`aws_obj/obj_astar_reward.ipynb`](aws_obj/obj_astar_reward.ipynb) | 팀 차원의 경로 최적화 실험 흔적이 남아 있는 파일이지만, 제 직접 담당 범위는 아님 |

## 기술 스택

- AWS DeepRacer
- DeepRacer for Cloud (DRfC)
- Python
- Reinforcement Learning Reward Design

## 결과

- 2024 AWS DeepRacer 챔피언십 리그 장려상
- 최종 제출 모델 `integrated1` 선정
- 최고 기록 `00:11.5` 확인
- `set_speed = 65`에서 안정적 주행 확인
- 실주행 기준 대략 12초대 랩타임 확보

## 요약

이 프로젝트에서 저는 AWS DeepRacer 워크스페이스 전체 중 오직 `reward_function.py` 설계와 튜닝만 담당했습니다.

- 팀원이 만든 최적 레이싱 라인 결과를 reward에 통합
- AWS 기본 Object Avoidance 구조를 대회용으로 변형
- 장애물 거리, 같은 차선 여부, 장애물별 좌우 위치 선호를 보상으로 설계
- reward weight와 조건을 반복 조정해 실제 주행 안정성과 기록을 확보

## 프로젝트 영상

<주행 테스트 영상>

https://github.com/user-attachments/assets/1e4781c5-095d-48cf-8009-3d4356a5324a


