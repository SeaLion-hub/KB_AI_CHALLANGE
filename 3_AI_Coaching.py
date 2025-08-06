#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - AI 투자 심리 코칭 페이지
실시간 딥러닝 기반 투자 심리 분석 및 개인화된 코칭 제공
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import sys
from pathlib import Path
import numpy as np

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 페이지 설정
st.set_page_config(page_title="AI 투자 심리 코칭", page_icon="🧠", layout="wide")

# 인증 확인
if 'current_user' not in st.session_state or st.session_state.current_user is None:
    st.error("🔒 로그인이 필요합니다.")
    if st.button("🏠 메인 페이지로 이동"):
        st.switch_page("main_app.py")
    st.stop()

def show_user_switcher_sidebar():
    """사이드바에 사용자 전환 및 네비게이션 표시"""
    user = st.session_state.current_user
    
    st.sidebar.markdown(f'''
    <div class="card" style="margin-bottom: 1rem; text-align: center;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">
            {user['icon']}
        </div>
        <h3 style="margin: 0; color: var(--text-primary);">{user['username']}님</h3>
        <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.9rem;">
            {user['description']}
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 사용자 전환 버튼
    if st.sidebar.button("🔄 다른 사용자로 전환", use_container_width=True):
        # 세션 상태 초기화
        keys_to_clear = ['current_user', 'onboarding_needed', 'selected_principle', 'selected_trade_for_review',
                        'cash', 'portfolio', 'history', 'market_data', 'chart_data']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.switch_page("main_app.py")
    
    # 네비게이션
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 네비게이션")
    
    if st.sidebar.button("📊 대시보드", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
    
    if st.sidebar.button("📝 거래 복기", use_container_width=True):
        st.switch_page("pages/2_Trade_Review.py")
    
    st.sidebar.markdown("🤖 **AI 코칭** ← 현재 위치")
    
    if st.sidebar.button("📜 투자 헌장", use_container_width=True):
        st.switch_page("pages/4_Investment_Charter.py")

@st.cache_resource
def load_sentiment_model():
    """
    투자 심리 분석 모델 로드 (캐시 적용)
    앱 실행 시 한 번만 로드되어 성능 최적화
    """
    try:
        from ml.predictor import SentimentPredictor
        predictor = SentimentPredictor(model_path='./sentiment_model')
        return predictor
    except Exception as e:
        st.error(f"❌ AI 모델 로드 실패: {str(e)}")
        st.error("⚠️ 먼저 train_emotion_model.py를 실행하여 모델을 훈련해주세요.")
        
        # 더미 예측기 반환
        class DummyPredictor:
            def predict(self, text):
                return {
                    'pattern': '공포',
                    'confidence': 0.75,
                    'confidence_level': '높음',
                    'description': '시장 하락에 대한 두려움이 감지되었습니다.',
                    'all_probabilities': {
                        '공포': 0.75,
                        '추격매수': 0.15,
                        '냉정': 0.10
                    }
                }
            
            def get_model_info(self):
                return {
                    'model_path': './sentiment_model',
                    'device': 'cpu',
                    'num_labels': 3,
                    'available_patterns': ['공포', '추격매수', '냉정']
                }
        
        return DummyPredictor()

def get_coaching_advice(pattern: str, confidence: float) -> dict:
    """
    투자 심리 패턴에 따른 맞춤형 코칭 조언 제공
    
    Args:
        pattern (str): 분석된 심리 패턴
        confidence (float): 예측 신뢰도
        
    Returns:
        dict: 코칭 조언 딕셔너리
    """
    coaching_data = {
        '공포': {
            'advice': "😰 공포에 휘둘린 매도는 장기적으로 손실을 가져올 수 있습니다.",
            'action_plan': [
                "🎯 미리 설정한 손절선을 준수하세요",
                "📊 펀더멘털 분석을 다시 검토해보세요",
                "⏰ 감정이 격해질 때는 24시간 후 재검토하세요",
                "📚 성공한 투자자들의 위기 극복 사례를 학습하세요"
            ],
            'risk_level': '높음',
            'color': '#FF6B6B'
        },
        '추격매수': {
            'advice': "🏃‍♂️ FOMO에 의한 추격매수는 고점 매수 위험이 높습니다.",
            'action_plan': [
                "📈 기술적 분석으로 적정 매수 시점을 찾으세요",
                "💰 분할 매수를 통해 평균 단가를 낮추세요",
                "⏳ 급등 후에는 최소 1-2일 관망하세요",
                "🎪 시장 과열 신호를 체크하세요"
            ],
            'risk_level': '높음',
            'color': '#FF9F43'
        },
        '과신': {
            'advice': "😎 과도한 자신감은 위험 관리를 소홀히 만들 수 있습니다.",
            'action_plan': [
                "🔍 투자 결정의 객관적 근거를 재검토하세요",
                "📊 포트폴리오의 위험 분산을 확인하세요",
                "👥 다른 투자자들의 의견도 들어보세요",
                "📖 과거 실패 사례를 되돌아보세요"
            ],
            'risk_level': '중간',
            'color': '#FFA726'
        },
        '손실회피': {
            'advice': "😣 손실 확정을 미루면 더 큰 손실로 이어질 수 있습니다.",
            'action_plan': [
                "✂️ 명확한 손절 기준을 설정하세요",
                "💡 손실도 투자의 일부임을 받아들이세요",
                "🔄 다른 기회로 손실을 만회할 계획을 세우세요",
                "📝 손절 후 원인 분석을 통해 학습하세요"
            ],
            'risk_level': '높음',
            'color': '#EF5350'
        },
        '확증편향': {
            'advice': "🔍 한쪽 정보만 보는 것은 잘못된 판단으로 이어집니다.",
            'action_plan': [
                "📰 다양한 관점의 분석 보고서를 읽으세요",
                "❓ 반대 의견에도 귀 기울여보세요",
                "🔬 객관적 데이터를 중심으로 판단하세요",
                "👥 투자 커뮤니티에서 다양한 의견을 수집하세요"
            ],
            'risk_level': '중간',
            'color': '#AB47BC'
        },
        '군중심리': {
            'advice': "👥 남들 따라하기는 독립적 사고력을 약화시킵니다.",
            'action_plan': [
                "🎯 나만의 투자 철학을 정립하세요",
                "📊 독립적인 분석 역량을 키우세요",
                "🚫 SNS나 커뮤니티 정보에 과도하게 의존하지 마세요",
                "💭 투자 전 스스로에게 '왜?'라고 질문하세요"
            ],
            'risk_level': '중간',
            'color': '#5C6BC0'
        },
        '냉정': {
            'advice': "✅ 훌륭한 투자 마인드셋을 유지하고 계십니다!",
            'action_plan': [
                "📈 현재의 합리적 접근법을 계속 유지하세요",
                "📚 지속적인 학습으로 역량을 강화하세요",
                "🎯 장기적 관점에서 투자하세요",
                "🔄 정기적으로 투자 전략을 점검하세요"
            ],
            'risk_level': '낮음',
            'color': '#66BB6A'
        }
    }
    
    return coaching_data.get(pattern, {
        'advice': "🤔 특이한 투자 패턴이 감지되었습니다.",
        'action_plan': ["📊 투자 전략을 재검토해보세요"],
        'risk_level': '보통',
        'color': '#78909C'
    })

def create_confidence_gauge(confidence: float):
    """신뢰도 게이지 차트 생성"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "분석 신뢰도"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def create_probability_chart(probabilities: dict):
    """모든 심리 패턴별 확률 차트 생성"""
    patterns = list(probabilities.keys())
    probs = [probabilities[pattern] * 100 for pattern in patterns]
    
    # 색상 매핑
    color_map = {
        '공포': '#FF6B6B',
        '추격매수': '#FF9F43', 
        '냉정': '#66BB6A',
        '과신': '#FFA726'
    }
    colors = [color_map.get(pattern, '#78909C') for pattern in patterns]
    
    fig = go.Figure(data=[
        go.Bar(
            x=patterns, 
            y=probs, 
            text=[f"{p:.1f}%" for p in probs],
            textposition='auto',
            marker_color=colors
        )
    ])
    
    fig.update_layout(
        title="모든 심리 패턴별 분석 확률",
        xaxis_title="투자 심리 패턴",
        yaxis_title="확률 (%)",
        height=400,
        showlegend=False
    )
    return fig

def analyze_historical_patterns():
    """사용자의 과거 심리 패턴 분석"""
    username = st.session_state.current_user['username']
    
    # 더미 데이터 (실제로는 DB에서 가져옴)
    if username == "김국민":
        pattern_history = {
            '공포': 35,
            '패닉': 20,
            '불안': 25,
            '냉정': 15,
            '확신': 5
        }
    elif username == "박투자":
        pattern_history = {
            '추격매수': 40,
            '욕심': 25,
            'FOMO': 20,
            '냉정': 10,
            '후회': 5
        }
    else:  # 이거울
        pattern_history = {
            '신중': 50,
            '학습': 30,
            '확신': 20
        }
    
    return pattern_history

def show_pattern_evolution():
    """심리 패턴 변화 추이 차트"""
    st.markdown("### 📈 심리 패턴 변화 추이")
    
    # 더미 데이터 생성
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
    patterns = ['공포', '추격매수', '냉정']
    
    fig = go.Figure()
    
    for pattern in patterns:
        # 패턴별 더미 데이터 생성
        if pattern == '공포':
            values = [30 + 20 * np.sin(i/10) + np.random.normal(0, 5) for i in range(len(dates))]
        elif pattern == '추격매수':
            values = [25 + 15 * np.cos(i/8) + np.random.normal(0, 3) for i in range(len(dates))]
        else:  # 냉정
            values = [20 + 10 * np.sin(i/12) + 15 + np.random.normal(0, 2) for i in range(len(dates))]
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=pattern,
            line=dict(width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title="월별 심리 패턴 빈도 변화",
        xaxis_title="날짜",
        yaxis_title="빈도 (%)",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    """메인 애플리케이션"""
    from utils.ui_components import apply_toss_css
    apply_toss_css()
    
    # 사이드바에 사용자 정보 및 네비게이션 표시
    show_user_switcher_sidebar()
    
    # 헤더
    st.title("🧠 AI 투자 심리 코칭")
    st.markdown("### 딥러닝 기반 실시간 투자 심리 분석 및 개인화된 코칭")
    
    # AI 모델 로드
    with st.spinner("🤖 AI 엔진 로딩 중..."):
        predictor = load_sentiment_model()
    
    # 모델 정보 표시
    with st.expander("🔍 AI 엔진 정보"):
        model_info = predictor.get_model_info()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("분석 가능 패턴", model_info['num_labels'])
        with col2:
            st.metric("실행 환경", model_info['device'])
        with col3:
            st.metric("모델 상태", "✅ 로드 완료")
        
        st.write("**분석 가능한 투자 심리 패턴:**")
        st.write(", ".join(model_info['available_patterns']))
    
    # 특별 거래 분석 (거래 복기에서 넘어온 경우)
    if 'ai_analysis_trade' in st.session_state:
        trade = st.session_state.ai_analysis_trade
        
        st.markdown("---")
        st.markdown(f"### 🎯 선택된 거래 분석: {trade['종목명']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("거래일", pd.to_datetime(trade['거래일시']).strftime('%Y-%m-%d'))
        with col2:
            st.metric("수익률", f"{trade['수익률']:+.1f}%")
        with col3:
            st.metric("감정태그", trade['감정태그'])
        
        # 당시 메모 AI 분석
        if st.button("🔍 당시 메모 AI 분석", type="primary"):
            with st.spinner("🧠 AI가 당시 심리를 분석 중입니다..."):
                result = predictor.predict(trade['메모'])
            
            if result['pattern'] != '오류':
                coaching = get_coaching_advice(result['pattern'], result['confidence'])
                
                st.markdown(f"""
                <div style='padding: 20px; border-radius: 10px; background-color: {coaching['color']}20; border-left: 5px solid {coaching['color']};'>
                    <h3 style='color: {coaching['color']}; margin-top: 0;'>📊 AI 분석 결과</h3>
                    <h2 style='color: {coaching['color']};'>💠 {result['pattern']}</h2>
                    <p><strong>신뢰도:</strong> {result['confidence']:.1%} ({result['confidence_level']})</p>
                    <p><strong>당시 메모:</strong> "{trade['메모']}"</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### 🎯 맞춤형 코칭 조언")
                st.warning(coaching['advice'])
                
                st.markdown("### 📋 개선 방안")
                for i, action in enumerate(coaching['action_plan'], 1):
                    st.markdown(f"{i}. {action}")
        
        # 분석 완료 후 세션에서 제거
        if st.button("✅ 분석 완료"):
            del st.session_state.ai_analysis_trade
            st.rerun()
    
    st.divider()
    
    # 메인 분석 섹션
    st.subheader("💭 투자 메모 실시간 분석")
    
    # 입력 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        user_input = st.text_area(
            "투자할 때의 생각이나 감정을 자유롭게 적어보세요:",
            placeholder="예: '코스피가 너무 떨어져서 무서워서 전량 매도했어요...'",
            height=100,
            key="main_analysis_input"
        )
    
    with col2:
        st.info("💡 **분석 팁**\n- 솔직한 감정 표현\n- 구체적인 상황 서술\n- 투자 이유나 동기 포함")
    
    # 분석 버튼
    if st.button("🔍 AI 심리 분석 시작", type="primary", use_container_width=True):
        if user_input.strip():
            # 분석 실행
            with st.spinner("🧠 AI가 당신의 투자 심리를 분석 중입니다..."):
                result = predictor.predict(user_input)
            
            if result['pattern'] != '오류':
                st.success("✅ 분석 완료!")
                
                # 결과 표시 영역
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # 주요 결과
                    coaching = get_coaching_advice(result['pattern'], result['confidence'])
                    
                    st.markdown(f"""
                    <div style='padding: 20px; border-radius: 10px; background-color: {coaching['color']}20; border-left: 5px solid {coaching['color']};'>
                        <h3 style='color: {coaching['color']}; margin-top: 0;'>📊 분석 결과</h3>
                        <h2 style='color: {coaching['color']};'>💠 {result['pattern']}</h2>
                        <p><strong>신뢰도:</strong> {result['confidence']:.1%} ({result['confidence_level']})</p>
                        <p><strong>위험도:</strong> {coaching['risk_level']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 패턴 설명
                    st.markdown("### 📝 심리 패턴 설명")
                    st.info(result['description'])
                
                with col2:
                    # 신뢰도 게이지
                    st.plotly_chart(create_confidence_gauge(result['confidence']), 
                                  use_container_width=True)
                
                # 코칭 조언
                st.markdown("### 🎯 맞춤형 코칭 조언")
                st.warning(coaching['advice'])
                
                st.markdown("### 📋 실행 계획")
                for i, action in enumerate(coaching['action_plan'], 1):
                    st.markdown(f"{i}. {action}")
                
                # 상세 분석 결과
                with st.expander("📈 상세 분석 결과 보기"):
                    st.plotly_chart(create_probability_chart(result['all_probabilities']), 
                                  use_container_width=True)
                    
                    st.markdown("### 📊 모든 패턴별 확률")
                    prob_df = pd.DataFrame([
                        {'심리 패턴': pattern, '확률': f"{prob:.1%}"}
                        for pattern, prob in sorted(result['all_probabilities'].items(), 
                                                  key=lambda x: x[1], reverse=True)
                    ])
                    st.dataframe(prob_df, use_container_width=True, hide_index=True)
                
            else:
                st.error(f"❌ {result['description']}")
        else:
            st.warning("📝 분석할 텍스트를 입력해주세요.")
    
    st.divider()
    
    # 개인화된 분석 섹션
    st.subheader("📊 나만의 투자 심리 분석")
    
    # 탭으로 구성
    tab1, tab2, tab3 = st.tabs(["📈 심리 패턴 추이", "🎯 개인화 인사이트", "💡 분석 예시"])
    
    with tab1:
        import numpy as np
        show_pattern_evolution()
        
        # 패턴별 통계
        st.markdown("### 📊 내 심리 패턴 분포")
        pattern_history = analyze_historical_patterns()
        
        # 도넛 차트
        fig = go.Figure(data=[go.Pie(
            labels=list(pattern_history.keys()),
            values=list(pattern_history.values()),
            hole=.3
        )])
        
        fig.update_layout(
            title="투자 심리 패턴 분포",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### 🎯 개인화된 투자 인사이트")
        
        username = st.session_state.current_user['username']
        
        if username == "김국민":
            st.markdown("""
            #### 📊 김국민님의 투자 성향 분석
            
            **주요 특징:**
            - 🚨 **공포매도 성향**: 시장 하락 시 감정적 매도 빈도가 높습니다
            - 😰 **손실 회피**: 손실을 확정하기를 꺼려하는 경향이 있습니다
            - 📉 **변동성 민감**: 시장 변동성에 과민하게 반응합니다
            
            **개선 방안:**
            - 📋 사전에 손절선을 명확히 설정하고 준수하세요
            - 🧘‍♂️ 감정적 결정을 피하기 위한 쿨링오프 시간을 갖으세요
            - 📊 장기적 관점에서 투자 성과를 평가하세요
            """)
        elif username == "박투자":
            st.markdown("""
            #### 📊 박투자님의 투자 성향 분석
            
            **주요 특징:**
            - 🏃‍♂️ **FOMO 매수**: 상승장에서 추격매수 성향이 강합니다
            - 🤑 **과도한 욕심**: 수익 기회를 놓칠까 봐 성급한 판단을 합니다
            - 👥 **외부 의존**: 타인의 추천에 크게 의존하는 경향이 있습니다
            
            **개선 방안:**
            - ⏰ 급등 종목은 하루 더 지켜본 후 판단하세요
            - 💰 분할 매수로 평균 단가를 관리하세요
            - 🎯 본인만의 투자 원칙을 수립하고 지키세요
            """)
        else:  # 이거울
            st.markdown("""
            #### 📊 이거울님의 투자 여정 시작
            
            **현재 상태:**
            - 🆕 **신규 투자자**: 투자 경험이 부족하지만 학습 의욕이 높습니다
            - 📚 **학습형**: 체계적으로 공부하며 접근하려는 자세가 보입니다
            - 🎯 **원칙 추구**: 명확한 투자 원칙을 찾고 있습니다
            
            **추천 방향:**
            - 📖 선택한 투자 대가의 원칙을 깊이 학습하세요
            - 💰 소액부터 시작하여 경험을 쌓아보세요
            - 📝 모든 거래에 대해 복기 습관을 기르세요
            """)
    
    with tab3:
        st.markdown("### 💡 분석 예시")
        
        example_texts = [
            "코스피가 너무 많이 떨어져서 무서워서 모든 주식을 팔아버렸어요",
            "유튜버가 추천한 주식이 급등해서 바로 올인했습니다", 
            "이번에는 확실해 보여서 대출까지 받아서 투자했어요",
            "손실이 너무 커져서 손절을 못하겠어요",
            "모든 지표를 분석한 결과 매수 타이밍이라고 판단됩니다"
        ]
        
        col1, col2 = st.columns(2)
        
        for i, example in enumerate(example_texts):
            with col1 if i % 2 == 0 else col2:
                st.markdown(f'''
                <div class="card" style="margin-bottom: 1rem;">
                    <p style="font-size: 14px; margin-bottom: 1rem;"><strong>예시 {i+1}:</strong></p>
                    <p style="font-style: italic; color: var(--text-secondary); margin-bottom: 1rem;">"{example}"</p>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"분석하기", key=f"example_{i}", use_container_width=True):
                    # 예시 분석 실행
                    with st.spinner("분석 중..."):
                        example_result = predictor.predict(example)
                    
                    st.write(f"**분석 결과:** {example_result['pattern']} (신뢰도: {example_result['confidence']:.1%})")
                    st.write(f"**설명:** {example_result['description']}")
    
    # 푸터
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🏆 KB AI Challenge - KB Reflex Team</p>
        <p>💡 AI 기반 투자 심리 분석으로 더 나은 투자 습관을 만들어보세요</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()