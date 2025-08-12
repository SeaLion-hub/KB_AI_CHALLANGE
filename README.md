# KB 금융 AI 챌린지: AI 투자 성장 플랫폼 '리플렉트(Reflect)'

## 1. 프로젝트 개요

**리플렉트(Reflect)**는 단순한 모의 투자 앱을 넘어, **투자자의 건강한 성장**에 초점을 맞춘 AI 기반 투자 성장 플랫폼입니다. 투자자가 겪는 가장 큰 어려움인 '심리적 편향'과 '반복되는 실수'를 AI 기술을 통해 극복하고, 자신의 투자 스타일을 스스로 발전시켜 나갈 수 있도록 돕는 것을 목표로 합니다.

핵심 컨셉은 **'실패로부터 배우고, 성공을 내재화하는'** 경험을 제공하는 것입니다.

## 2. 핵심 기능

-   **📈 실시간 모의 거래**: 사용자는 실제와 유사한 환경에서 주식 거래를 시뮬레이션하며 자신의 투자 전략을 테스트할 수 있습니다.
-   **📝 AI 오답노트 (AI Post-Mortem)**: 손실이 발생한 거래에 대해 사용자가 자신의 생각과 감정을 기록하면, AI가 과거 모든 데이터를 분석하여 **객관적인 데이터에 기반한 심층 분석 리포트**를 제공합니다.
-   **📜 나의 투자 헌장 (My Investment Charter)**: 'AI 오답노트'와 '성공 노트'에서 얻은 교훈을 바탕으로, AI가 사용자만의 **개인화된 투자 원칙** 초안을 생성해 줍니다. 사용자는 이를 바탕으로 자신만의 투자 철학을 정립할 수 있습니다.
-   **📊 동적 포트폴리오**: 모든 거래 내역과 현재 보유 자산, 수익률 현황을 실시간으로 추적하고 시각화하여 보여줍니다.

## 3. 시스템 아키텍처

-   **Frontend**: Streamlit
-   **Backend**: Python
-   **AI Engine**: Google Gemini API
-   **Data Storage**: CSV
-   **주요 모듈**:
    -   `main_app.py`: 앱의 진입점 및 기본 설정
    -   `pages/`: 각 기능 페이지 (트레이딩, 포트폴리오, AI 코칭)
    -   `ai_service.py`: Gemini API와 연동하여 모든 AI 분석 기능을 수행
    -   `trading_service.py`: 모의 거래 실행 및 계좌 상태 관리
    -   `data_service.py`: 사용자 데이터(거래, 노트, 헌장) 로딩 및 저장
    -   `ui_components.py`: 반복적으로 사용되는 UI 컴포넌트 관리

## 4. 실행 방법

1.  **프로젝트 다운로드 및 압축 해제**

2.  **가상 환경 생성 및 활성화 (권장)**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    venv\Scripts\activate     # Windows
    ```

3.  **필요 라이브러리 설치**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Gemini API 키 설정**
    -   프로젝트 폴더 내에 `.streamlit/secrets.toml` 파일을 생성합니다.
    -   아래와 같이 Gemini API 키를 입력하고 저장합니다.
        ```toml
        GEMINI_API_KEY = "YOUR_API_KEY_HERE"
        ```

5.  **애플리케이션 실행**
    ```bash
    streamlit run main_app.py
    ```