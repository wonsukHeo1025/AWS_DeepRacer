# DeepRacer Vehicle API

- 본 저장소는 DeepRacer 차량의 API를 [(주)에이아이캐슬](https://aicastle.io) 에서 재구성 한 것입니다.

## 설치
- 필수
    ```bash
    pip install aicastle[deepracer-vehicle] ipykernel
    ```

- 선택
    - `pip install openai`
    - `pip install ollama`

## 사용법

| 파일명 | 설명 |
| --- | --- |
| [00_initialize.ipynb](./00_initialize.ipynb) | 파일을 통해 API를 사용하기 위한 초기 설정을 진행합니다. |
| [01_Vehicle_API_Tutorial.ipynb](./01_Vehicle_API_Tutorial.ipynb) | 파일을 통해 차량의 API를 사용하는 방법을 설명합니다. |
| [02_Image_Classification.ipynb](./02_Image_Classification.ipynb) | 로컬에서 수집된 데이터로 이미지 분류 모델을 학습하는 방법을 설명합니다. |
| [03_GPT.ipynb](./03_GPT.ipynb) | GPT 모델을 사용하여 차량을 제어하는 방법을 설명합니다. |
| [04_Llama.ipynb](./04_Llama.ipynb) | LLAMA 모델을 사용하여 차량을 제어하는 방법을 설명합니다. |
