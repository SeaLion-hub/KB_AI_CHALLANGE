# ui_components.py (KB 테마 적용 + 완전한 최종 버전)
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# AI 서비스에서 필요한 함수들을 안전하게 임포트
try:
    from ai_service import (
        analyze_trade_with_ai, check_gemini_api, test_gemini_connection, 
        find_similar_experiences_ai, setup_gemini_api, gemini_select_and_analyze_trades
    )
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    # AI 서비스가 없으면 더미 함수 제공
    def check_gemini_api():
        return False
    def test_gemini_connection():
        return False
    def analyze_trade_with_ai(*args, **kwargs):
        return {'similar_trades': [], 'ai_analysis': 'AI 서비스를 사용할 수 없습니다.', 'method': 'error'}
    def find_similar_experiences_ai(*args, **kwargs):
        return []
    def setup_gemini_api():
        return False
    def gemini_select_and_analyze_trades(*args, **kwargs):
        return {'method': 'error', 'analysis': 'AI 서비스를 사용할 수 없습니다.'}
    GEMINI_AVAILABLE = False

try:
    from trading_service import format_currency_smart, calculate_expected_pnl
except ImportError:
    def format_currency_smart(amount):
        return f"{amount:,}원"
    def calculate_expected_pnl(*args, **kwargs):
        return None

def apply_kb_theme():
    """KB 금융그룹 테마 적용 함수 (기존 구조를 유지한 흰색 테마 버전)"""
    css = """
    <style>
        /* KB 금융그룹 전용 폰트 및 색상 변수 --- 수정됨 --- */
        :root {
            --kb-yellow: #FFCC00;
            --kb-dark-yellow: #E6B800; /* 호버/그라데이션용 */
            --kb-black: #1c1c1c;       /* 기본 텍스트 색상 */
            --kb-white: #FFFFFF;       /* 기본 배경 */
            --kb-light-gray: #f5f5f5;  /* 보조 배경 (사이드바 등) */
            --kb-border: #e0e0e0;       /* 옅은 테두리 */
            --kb-text-secondary: #555555; /* 보조 텍스트 */
            --kb-success: #28a745;
            --kb-error: #dc3545;
            --kb-warning: #ffc107;
        }

        /* 기본 앱 배경 --- 수정됨 --- */
        [data-testid="stAppViewContainer"] {
            background-color: var(--kb-white);
            color: var(--kb-black);
        }
        [data-testid="stApp"] {
            background: transparent;
        }
        .stApp, .stApp > div { 
            color: var(--kb-black); 
        }
        
        /* 헤더 및 제목 --- 수정됨 --- */
        h1, h2, h3, h4, h5, h6 { 
            color: var(--kb-black) !important; 
            font-weight: 700;
        }
        h1 {
            border-bottom: 3px solid var(--kb-yellow);
            padding-bottom: 8px;
        }

        /* 사이드바 스타일링 --- 수정됨 --- */
        [data-testid="stSidebar"] { 
            background-color: var(--kb-light-gray);
            border-right: 1px solid var(--kb-border);
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--kb-black) !important;
        }

        /* 버튼 스타일링 --- 수정됨 --- */
        .stButton > button {
            background: var(--kb-yellow);
            color: var(--kb-black);
            font-weight: 700;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .stButton > button:hover {
            background: var(--kb-dark-yellow);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
        }
        .stButton > button:active {
            transform: translateY(0px);
        }

        /* Primary 버튼 (특별한 강조) --- 수정됨 --- */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--kb-yellow) 0%, #ffaa00 100%);
            color: var(--kb-black);
            font-weight: 800;
            box-shadow: 0 6px 20px rgba(255, 204, 0, 0.4);
        }

        /* Secondary 버튼 --- 수정됨 --- */
        .stButton > button[kind="secondary"] {
            background: var(--kb-white);
            color: var(--kb-text-secondary);
            border: 1px solid var(--kb-border);
        }

        /* 입력 필드 --- 수정됨 --- */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            background-color: var(--kb-white);
            color: var(--kb-black);
            border: 1px solid #BDBDBD;
            border-radius: 8px;
            padding: 12px;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div:focus-within {
            border-color: var(--kb-yellow);
            box-shadow: 0 0 10px rgba(255, 204, 0, 0.5);
        }

        /* 메트릭 카드 --- 수정됨 --- */
        [data-testid="stMetric"] {
            background-color: var(--kb-white);
            border: 1px solid var(--kb-border);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        [data-testid="stMetricValue"] {
            color: var(--kb-black);
            font-weight: 700;
        }

        /* 탭 스타일링 --- 수정됨 --- */
        .stTabs [data-baseweb="tab-list"] {
            background-color: var(--kb-light-gray);
            border-radius: 8px;
            padding: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            color: var(--kb-text-secondary);
            border-radius: 6px;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background: var(--kb-yellow);
            color: var(--kb-black) !important;
        }

        /* Expander 스타일링 --- 수정됨 --- */
        .streamlit-expanderHeader {
            background-color: var(--kb-light-gray);
            color: var(--kb-black);
            border: 1px solid var(--kb-border);
            border-radius: 8px;
            font-weight: 600;
        }
        .streamlit-expanderContent {
            background-color: var(--kb-white);
            border: 1px solid var(--kb-border);
            border-top: none;
        }

        /* Alert 박스 --- 수정됨 --- */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid;
            color: var(--kb-black);
        }
        .stSuccess { background-color: #e9f7ef; border-left-color: var(--kb-success); }
        .stError { background-color: #fbe9e7; border-left-color: var(--kb-error); }
        .stWarning { background-color: #fff8e1; border-left-color: var(--kb-warning); }
        .stInfo { background-color: #fffae6; border-left-color: var(--kb-yellow); }

        /* 진행률 바 (수정할 필요 없음) */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, var(--kb-yellow) 0%, var(--kb-dark-yellow) 100%);
        }

        /* 스피너 (수정할 필요 없음) */
        .stSpinner > div {
            border-top-color: var(--kb-yellow) !important;
        }

        /* 데이터프레임 테이블 --- 수정됨 --- */
        .dataframe {
            background-color: var(--kb-white);
            color: var(--kb-black);
            border: 1px solid var(--kb-border);
        }
        .dataframe th {
            background-color: var(--kb-yellow);
            color: var(--kb-black);
            font-weight: 700;
        }

        /* 커스텀 카드 스타일 --- 수정됨 --- */
        .kb-card {
            background-color: var(--kb-white);
            border: 1px solid var(--kb-border);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.07);
        }
        
        /* 커스텀 하이라이트 스타일 (수정할 필요 없음) */
        .kb-highlight {
            background: linear-gradient(135deg, var(--kb-yellow) 0%, var(--kb-dark-yellow) 100%);
            color: var(--kb-black);
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 700;
        }

        /* 애니메이션 효과 (수정할 필요 없음) */
        @keyframes kb-glow {
            0%, 100% { box-shadow: 0 0 5px var(--kb-yellow); }
            50% { box-shadow: 0 0 20px var(--kb-yellow), 0 0 30px var(--kb-yellow); }
        }
        .kb-glow {
            animation: kb-glow 2s ease-in-out infinite;
        }

        /* 반응형 디자인 (수정할 필요 없음) */
        @media (max-width: 768px) {
            .stButton > button {
                padding: 10px 16px;
                font-size: 12px;
            }
            h1 { font-size: 24px; }
            h2 { font-size: 20px; }
            h3 { font-size: 18px; }
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(css, unsafe_allow_html=True)

def render_css():
    """기존 CSS 스타일 렌더링 (KB 테마와 함께 사용)"""
    st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        * {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }

        .gemini-card {
            background: linear-gradient(135deg, #FFCC00 0%, #FFD700 50%, #FFAA00 100%);
            border-radius: 20px;
            padding: 24px;
            color: #1c1c1c;
            box-shadow: 0 8px 32px rgba(255, 204, 0, 0.4);
            border: none;
            text-align: center;
            margin-bottom: 24px;
        }

        .gemini-status-active {
            background: linear-gradient(135deg, #FFCC00 0%, #FFD700 100%);
            color: #1c1c1c;
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(255, 204, 0, 0.4);
        }

        .gemini-status-inactive {
            background: linear-gradient(135deg, #666666 0%, #888888 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(102, 102, 102, 0.3);
        }

        .ai-coaching-card {
            background: linear-gradient(135deg, #FFCC00 0%, #FFD700 50%, #FFAA00 100%);
            border-radius: 20px;
            padding: 24px;
            color: #1c1c1c;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(255, 204, 0, 0.3);
        }

        .ai-coaching-title {
            font-size: 20px;
            font-weight: 800;
            margin-bottom: 16px;
            text-align: center;
        }

        .ai-coaching-content {
            font-size: 16px;
            line-height: 1.7;
            text-align: left;
            white-space: pre-line;
        }

        .kb-powered {
            font-size: 12px;
            opacity: 0.9;
            text-align: center;
            margin-top: 12px;
        }

        .gemini-analysis-card {
            background: linear-gradient(135deg, #2c2c2c 0%, #1c1c1c 100%);
            border: 2px solid #FFCC00;
            border-radius: 20px;
            padding: 24px;
            margin: 20px 0;
        }

        .gemini-analysis-title {
            font-size: 18px;
            font-weight: 700;
            color: #FFCC00;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
        }

        .similarity-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
            margin: 4px;
        }

        .similarity-high {
            background: linear-gradient(135deg, #FFCC00 0%, #FFD700 100%);
            color: #1c1c1c;
        }

        .similarity-medium {
            background-color: #FFAA00;
            color: #1c1c1c;
        }

        .similarity-low {
            background-color: #00ff88;
            color: #1c1c1c;
        }

        .trade-review-card {
            background: linear-gradient(135deg, #2c2c2c 0%, #1c1c1c 100%);
            border: 2px solid #FFCC00;
            border-radius: 16px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 4px 12px rgba(255, 204, 0, 0.2);
        }

        .reflection-result-card {
            background: linear-gradient(135deg, #2c4a2c 0%, #1c3e1c 100%);
            border: 2px solid #00ff88;
            border-radius: 16px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 4px 12px rgba(0, 255, 136, 0.2);
        }

        .reflection-insight-card {
            background: linear-gradient(135deg, #2c2c2c 0%, #1c1c1c 100%);
            border: 1px solid #FFCC00;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
        }

        .loss-alert {
            background: linear-gradient(135deg, #4a2c2c 0%, #3e1c1c 100%);
            border: 2px solid #ff4444;
            border-radius: 16px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }

        .loss-alert-title {
            font-size: 18px;
            font-weight: 700;
            color: #ff4444;
            margin-bottom: 12px;
        }

        .loss-alert-content {
            font-size: 14px;
            color: #f0f0f0;
            margin-bottom: 16px;
        }

        .card {
            background: linear-gradient(135deg, #2c2c2c 0%, #1c1c1c 100%);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border: 1px solid #444444;
        }

        .metric-card {
            background: linear-gradient(135deg, #2c2c2c 0%, #1c1c1c 100%);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border: 2px solid #FFCC00;
            text-align: center;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .metric-label {
            font-size: 14px;
            font-weight: 600;
            color: #FFCC00;
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: #f0f0f0;
        }

        .metric-value.positive {
            color: #00ff88;
        }

        .metric-value.negative {
            color: #ff4444;
        }

        .pnl-preview {
            background: linear-gradient(135deg, #2c4a2c 0%, #1c3e1c 100%);
            border: 1px solid #00ff88;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
        }

        .pnl-preview.negative {
            background: linear-gradient(135deg, #4a2c2c 0%, #3e1c1c 100%);
            border: 1px solid #ff4444;
        }

        .emotion-tag {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }

        .emotion-fear { background: #ff4444; color: #f0f0f0; }
        .emotion-greed { background: #FFAA00; color: #1c1c1c; }
        .emotion-rational { background: #00ff88; color: #1c1c1c; }
        .emotion-anxiety { background: #FFCC00; color: #1c1c1c; }
    </style>
    """, unsafe_allow_html=True)

def render_gemini_status():
    """Gemini API 상태 표시 및 설정 UI (KB 테마 적용)"""
    if check_gemini_api():
        # 연결 테스트
        connection_ok = test_gemini_connection()
        if connection_ok:
            st.markdown("""
            <div class="gemini-status-active">
                🚀 KB AI 활성화됨 - 모든 AI 기능 사용 가능
            </div>
            """, unsafe_allow_html=True)
            return True
        else:
            st.markdown("""
            <div class="gemini-status-inactive">
                ⚠️ KB AI 연결 오류 - API 키를 확인해주세요
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="gemini-status-inactive">
            🔴 KB AI 비활성화 - 핵심 기능을 위해 설정 필요
        </div>
        """, unsafe_allow_html=True)
        
        # Gemini API 키 설정 UI (KB 스타일)
        with st.expander("🔑 KB AI 설정 (필수)", expanded=True):
            st.markdown("""
            <div class="gemini-card">
                <h3>🏦 KB AI로 투자 심리 분석</h3>
                <p>KB Re:Mind의 핵심 AI 기능을 사용하기 위해 Gemini API 키가 필요합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **KB AI 서비스 설정 방법:**
            
            1. **[Google AI Studio](https://aistudio.google.com/app/apikey)** 접속
            2. **'Create API Key'** 클릭  
            3. **새 프로젝트에서 API 키 생성**
            4. **생성된 키를 아래에 입력**
            
            ⭐ **무료로 매일 1,500회 요청 가능**
            """)
            
            api_key = st.text_input(
                "Gemini API 키 입력", 
                type="password", 
                key="gemini_api_key_input",
                placeholder="AIza..."
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 KB AI 연결하기", key="save_gemini_key", use_container_width=True):
                    if api_key and (api_key.startswith("AIza") or len(api_key) > 30):
                        st.session_state.gemini_api_key = api_key
                        st.success("✅ KB AI가 활성화되었습니다!")
                        
                    elif api_key:
                        st.error("❌ 올바른 Gemini API 키 형식이 아닙니다.")
                    else:
                        st.warning("⚠️ API 키를 입력해주세요.")
            
            with col2:
                if st.button("🧪 연결 테스트", key="test_gemini", use_container_width=True):
                    if api_key:
                        st.session_state.gemini_api_key = api_key
                        with st.spinner("KB AI 연결 테스트 중..."):
                            if test_gemini_connection():
                                st.success("✅ KB AI 연결 성공!")
                            else:
                                st.error("❌ KB AI 연결 실패")
                    else:
                        st.warning("⚠️ 먼저 API 키를 입력해주세요.")
    
    return False

def show_ai_trade_review():
    """개선된 AI 거래 검토 화면 - KB 테마 적용"""
    st.markdown("### 🤖 KB AI 거래 검토")
    
    if st.session_state.pending_trade:
        trade = st.session_state.pending_trade
        
        # 현재 거래 정보 표시 (KB 스타일)
        trade_info_html = f'''
        <div class="gemini-analysis-card">
            <div class="gemini-analysis-title">
                🏦 KB AI가 과거 유사 거래를 직접 선택하고 분석합니다
            </div>
            <div style="color: #f0f0f0;">
                <strong>종목:</strong> {trade["stock_name"]}<br>
                <strong>거래유형:</strong> {trade["trade_type"]}<br>
                <strong>수량:</strong> {trade["quantity"]:,}주<br>
                <strong>가격:</strong> {format_currency_smart(trade["price"])}<br>
                <strong>총액:</strong> {format_currency_smart(trade["quantity"] * trade["price"])}
            </div>
            <div class="kb-powered">Powered by KB AI • 자동 거래 선별 및 분석</div>
        </div>
        '''
        st.markdown(trade_info_html, unsafe_allow_html=True)
        
        # Gemini 기반 AI 분석 실행
        if not st.session_state.user_data.empty and check_gemini_api():
            with st.spinner("🏦 KB AI가 모든 과거 거래를 검토하여 가장 유사한 3개를 선택하고 있습니다..."):
                try:
                    # Gemini가 직접 거래를 선택하고 분석
                    analysis_result = gemini_select_and_analyze_trades(
                        trade, 
                        st.session_state.user_data, 
                        st.session_state.current_user
                    )
                    
                    if analysis_result["method"] == "gemini_selection" and analysis_result.get("selected_trades"):
                        # Gemini가 선택한 유사 거래들 표시
                        st.markdown("#### 📋 KB AI가 직접 선택한 가장 유사한 과거 거래 3개")
                        
                        for i, trade_data in enumerate(analysis_result["selected_trades"], 1):
                            stock_name = trade_data.get("종목명", "")
                            return_rate = trade_data.get("수익률", 0)
                            
                            with st.expander(f"🔍 선택된 거래 #{i}: {stock_name} ({return_rate:.1f}%)", expanded=True):
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    trade_date = trade_data.get("거래일시", "")
                                    trade_type = trade_data.get("거래구분", "")
                                    emotion_tag = trade_data.get("감정태그", "")
                                    
                                    return_color = "#00ff88" if return_rate >= 0 else "#ff4444"
                                    
                                    trade_card_html = f'''
                                    <div class="trade-review-card">
                                        <div style="margin-bottom: 12px;">
                                            <span class="similarity-badge similarity-high">KB AI 선택</span>
                                        </div>
                                        <div style="color: #f0f0f0;"><strong>📅 거래일:</strong> {trade_date}</div>
                                        <div style="color: #f0f0f0;"><strong>📈 종목:</strong> {stock_name}</div>
                                        <div style="color: #f0f0f0;"><strong>💰 거래:</strong> {trade_type}</div>
                                        <div style="color: #f0f0f0;"><strong>📊 수익률:</strong> 
                                            <span style="color: {return_color};">
                                                {return_rate:+.1f}%
                                            </span>
                                        </div>
                                        <div style="color: #f0f0f0;"><strong>😔 감정상태:</strong> {emotion_tag}</div>
                                    </div>
                                    '''
                                    st.markdown(trade_card_html, unsafe_allow_html=True)
                                
                                with col2:
                                    similarity_reason = trade_data.get("similarity_reason", "유사성 분석 결과")
                                    memo = trade_data.get("메모", "")
                                    gemini_summary = trade_data.get("gemini_summary", "분석 요약 없음")
                                    
                                    reason_card_html = f'''
                                    <div class="trade-review-card">
                                        <div style="color: #FFCC00;"><strong>🎯 선택 이유:</strong></div>
                                        <div style="font-style: italic; color: #f0f0f0; margin: 8px 0;">
                                            "{similarity_reason}"
                                        </div>
                                        
                                        <div style="margin-top: 12px;">
                                            <div style="color: #FFCC00;"><strong>💭 당시 메모:</strong></div>
                                            <div style="font-size: 13px; color: #aaaaaa;">
                                                "{memo}"
                                            </div>
                                        </div>
                                        
                                        <div style="margin-top: 8px;">
                                            <div style="color: #FFCC00;"><strong>🤖 KB AI 요약:</strong></div>
                                            <div style="font-size: 13px; color: #FFCC00;">
                                                {gemini_summary}
                                            </div>
                                        </div>
                                    </div>
                                    '''
                                    st.markdown(reason_card_html, unsafe_allow_html=True)
                        
                        # KB AI 종합 분석 및 조언
                        st.markdown("#### 🏦 KB AI 종합 분석 및 투자 조언")
                        
                        # 패턴 분석
                        if analysis_result.get("pattern_analysis"):
                            pattern_text = analysis_result["pattern_analysis"]
                            pattern_html = f"""
                            <div style="background: linear-gradient(135deg, #2c2c2c 0%, #1c1c1c 100%); 
                                       border: 2px solid #FFCC00; border-radius: 16px; padding: 20px; margin: 16px 0;">
                                <h4 style="color: #FFCC00; margin-bottom: 12px;">🔍 KB AI 패턴 분석</h4>
                                <div style="line-height: 1.6; color: #f0f0f0;">
                                    {pattern_text}
                                </div>
                            </div>
                            """
                            st.markdown(pattern_html, unsafe_allow_html=True)
                        
                        # 위험도 평가
                        if analysis_result.get("risk_assessment"):
                            risk_text = analysis_result["risk_assessment"]
                            risk_html = f"""
                            <div style="background: linear-gradient(135deg, #4a4a2c 0%, #3e3e1c 100%); 
                                       border: 2px solid #FFAA00; border-radius: 16px; padding: 20px; margin: 16px 0;">
                                <h4 style="color: #FFAA00; margin-bottom: 12px;">⚠️ KB AI 위험도 평가</h4>
                                <div style="line-height: 1.6; color: #f0f0f0;">
                                    {risk_text}
                                </div>
                            </div>
                            """
                            st.markdown(risk_html, unsafe_allow_html=True)
                        
                        # 구체적 권고사항
                        if analysis_result.get("recommendation"):
                            recommendation_text = analysis_result["recommendation"]
                            recommendation_html = f"""
                            <div class="ai-coaching-card">
                                <div class="ai-coaching-title">💡 KB AI 투자 권고사항</div>
                                <div class="ai-coaching-content">{recommendation_text}</div>
                                <div class="kb-powered">Powered by KB AI • 3개 유사 거래 종합 분석</div>
                            </div>
                            """
                            st.markdown(recommendation_html, unsafe_allow_html=True)
                        
                        # 대안 전략
                        if analysis_result.get("alternative_strategy"):
                            alternative_text = analysis_result["alternative_strategy"]
                            alternative_html = f"""
                            <div style="background: linear-gradient(135deg, #2c4a2c 0%, #1c3e1c 100%); 
                                       border: 2px solid #00ff88; border-radius: 16px; padding: 20px; margin: 16px 0;">
                                <h4 style="color: #00ff88; margin-bottom: 12px;">📋 KB AI 대안 전략</h4>
                                <div style="line-height: 1.6; color: #f0f0f0;">
                                    {alternative_text}
                                </div>
                            </div>
                            """
                            st.markdown(alternative_html, unsafe_allow_html=True)
                    
                    elif analysis_result["method"] == "gemini_text":
                        # JSON 파싱 실패 시 텍스트 응답 표시
                        analysis_text = analysis_result["analysis"]
                        text_html = f"""
                        <div class="ai-coaching-card">
                            <div class="ai-coaching-title">🏦 KB AI 분석 결과</div>
                            <div class="ai-coaching-content">{analysis_text}</div>
                            <div class="kb-powered">Powered by KB AI</div>
                        </div>
                        """
                        st.markdown(text_html, unsafe_allow_html=True)
                    
                    else:
                        # 오류 발생 시
                        error_msg = analysis_result.get("analysis", "알 수 없는 오류")
                        st.error(f"KB AI 분석 중 오류가 발생했습니다: {error_msg}")
                        
                except Exception as e:
                    st.error(f"KB AI 분석 중 오류가 발생했습니다: {str(e)}")
                
        else:
            st.markdown("""
            <div class="gemini-card">
                <h3>🚨 KB AI 연결 필요</h3>
                <p>거래 분석을 위해서는 KB AI API 연결이 필수입니다.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 거래 실행 또는 취소
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ KB AI 분석을 반영하여 거래 실행", 
                        key="execute_after_ai_review", 
                        use_container_width=True, 
                        type="primary"):
                
                try:
                    from trading_service import execute_trade, add_trade_to_history
                    
                    success, message, loss_info, portfolio, cash = execute_trade(
                        trade["stock_name"], 
                        trade["trade_type"], 
                        trade["quantity"], 
                        trade["price"],
                        st.session_state.portfolio,
                        st.session_state.cash
                    )
                    
                    if success:
                        st.session_state.portfolio = portfolio
                        st.session_state.cash = cash
                        st.session_state.history = add_trade_to_history(
                            st.session_state.history,
                            trade["stock_name"],
                            trade["trade_type"],
                            trade["quantity"],
                            trade["price"]
                        )
                        
                        st.success(message)
                        st.session_state.show_ai_review = False
                        st.session_state.pending_trade = None
                        
                        if loss_info:
                            st.session_state.show_loss_modal = True
                            st.session_state.loss_info = loss_info
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                except ImportError:
                    st.error("거래 서비스를 사용할 수 없습니다.")
        
        with col2:
            if st.button("❌ 거래 취소", key="cancel_after_ai_review", use_container_width=True):
                st.session_state.show_ai_review = False
                st.session_state.pending_trade = None
                st.info("거래가 취소되었습니다.")
                time.sleep(1)
                st.rerun()

def show_charge_modal():
    """자산 충전 모달 (KB 테마 적용)"""
    st.markdown("### 💰 KB 자산 충전")
    st.write("원하는 금액을 입력하여 가상 자산을 충전할 수 있습니다.")
    
    charge_amount = st.number_input(
        "충전할 금액 (원)",
        min_value=10000,
        max_value=100000000,
        value=1000000,
        step=100000,
        format="%d"
    )
    
    # KB 스타일 충전 미리보기
    preview_html = f"""
    <div class="card">
        <h4 style="color: #FFCC00;">💳 충전 미리보기</h4>
        <div style="color: #f0f0f0;">
            <strong>현재 잔고:</strong> {format_currency_smart(st.session_state.cash)}<br>
            <strong>충전 금액:</strong> <span style="color: #FFCC00;">{format_currency_smart(charge_amount)}</span><br>
            <strong>충전 후 잔고:</strong> <span style="color: #00ff88; font-weight: 700;">{format_currency_smart(st.session_state.cash + charge_amount)}</span>
        </div>
    </div>
    """
    st.markdown(preview_html, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💳 KB 충전하기", key="confirm_charge", use_container_width=True):
            st.session_state.cash += charge_amount
            st.success(f"✅ {format_currency_smart(charge_amount)}이 충전되었습니다!")
            
            st.session_state.show_charge_modal = False
            time.sleep(2)
            st.rerun()
    
    with col2:
        if st.button("❌ 취소", key="cancel_charge", use_container_width=True):
            st.session_state.show_charge_modal = False
            st.rerun()

def show_gemini_coaching_card(user_data, user_type):
    """KB AI 기반 오늘의 코칭 카드"""
    try:
        from ai_service import generate_ai_coaching_tip
        ai_tip = generate_ai_coaching_tip(user_data, user_type)
    except ImportError:
        ai_tip = "KB AI 서비스를 연결해주세요."
    
    if check_gemini_api():
        coaching_html = f'''
        <div class="ai-coaching-card">
            <div class="ai-coaching-title">
                🏦 오늘의 KB AI 투자 코칭
            </div>
            <div class="ai-coaching-content">{ai_tip}</div>
            <div class="kb-powered">Powered by KB AI • 개인화된 투자 분석</div>
        </div>
        '''
        st.markdown(coaching_html, unsafe_allow_html=True)
    else:
        waiting_html = f'''
        <div class="gemini-card">
            <h3>🚨 KB AI 코칭 대기 중</h3>
            <p>개인화된 KB AI 코칭을 받으려면 API를 연결해주세요.</p>
            <div style="font-size: 14px; margin-top: 12px; opacity: 0.9;">
                기본 조언: {ai_tip}
            </div>
        </div>
        '''
        st.markdown(waiting_html, unsafe_allow_html=True)

def show_loss_modal(loss_info):
    """손실 발생 시 모달 (KB 테마 적용)"""
    loss_html = f'''
    <div class="loss-alert">
        <div class="loss-alert-title">📉 투자 손실이 발생했습니다</div>
        <div class="loss-alert-content">
            <strong>{loss_info["stock_name"]}</strong> {loss_info["quantity"]:,}주 매도에서<br>
            <strong>{format_currency_smart(loss_info["loss_amount"])} ({loss_info["loss_percentage"]:.1f}%)</strong> 손실이 발생했습니다.
        </div>
    </div>
    '''
    st.markdown(loss_html, unsafe_allow_html=True)
    
    st.markdown("### 🏦 KB AI 복기노트를 작성할까요?")
    st.info("💡 손실 거래를 KB AI와 함께 분석하여 같은 실수를 반복하지 않도록 도움을 받을 수 있습니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧠 네, KB AI 복기노트 작성", key="create_ai_loss_note", use_container_width=True, type="primary"):
            st.session_state.show_loss_analysis = True
            st.session_state.show_loss_modal = False
            st.rerun()
    
    with col2:
        if st.button("⏰ 나중에 복기하기", key="skip_loss_note", use_container_width=True):
            st.session_state.show_loss_modal = False
            st.session_state.loss_info = {}
            st.info("복기는 언제든지 'KB AI 거래 복기' 페이지에서 할 수 있습니다.")
            time.sleep(1)
            st.rerun()

def show_loss_analysis(loss_info):
    """손실 분석 화면 (KB 테마 적용)"""
    analysis_html = f'''
    <div class="loss-alert">
        <div class="loss-alert-title">🏦 KB AI 손실 분석</div>
        <div class="loss-alert-content">
            <strong>{loss_info["stock_name"]}</strong> 손실 거래를 KB AI가 전문적으로 분석합니다
        </div>
    </div>
    '''
    st.markdown(analysis_html, unsafe_allow_html=True)
    
    if check_gemini_api():
        st.markdown("### 🏦 KB AI 손실 원인 분석")
        st.markdown("손실이 발생한 거래의 원인을 KB AI가 분석하여 향후 개선점을 제시합니다.")
        
        # 손실 거래 요약 정보 표시 (KB 스타일)
        summary_html = f"""
        <div class="trade-review-card">
            <h4 style="color: #FFCC00;">📊 손실 거래 요약</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; color: #f0f0f0;">
                <div>
                    <strong>종목:</strong> {loss_info["stock_name"]}<br>
                    <strong>수량:</strong> {loss_info["quantity"]:,}주<br>
                    <strong>매수가:</strong> {format_currency_smart(loss_info["buy_price"])}
                </div>
                <div>
                    <strong>매도가:</strong> {format_currency_smart(loss_info["sell_price"])}<br>
                    <strong>손실금액:</strong> {format_currency_smart(loss_info["loss_amount"])}<br>
                    <strong>손실률:</strong> <span style="color: #ff4444; font-weight: 700;">{loss_info["loss_percentage"]:.1f}%</span>
                </div>
            </div>
        </div>
        """
        st.markdown(summary_html, unsafe_allow_html=True)
        
        if st.button("🔍 KB AI 분석 시작", type="primary", use_container_width=True):
            try:
                from ai_service import analyze_trading_psychology
                
                loss_context = f"""
                {loss_info["stock_name"]} {loss_info["quantity"]}주를 
                {format_currency_smart(loss_info["buy_price"])}에서 매수했다가 
                {format_currency_smart(loss_info["sell_price"])}에 매도하여 
                {loss_info["loss_percentage"]:.1f}% 손실을 봤습니다.
                """
                
                with st.spinner("🏦 KB AI가 손실 원인을 분석하고 있습니다..."):
                    analysis = analyze_trading_psychology(
                        loss_context,
                        st.session_state.user_data,
                        st.session_state.current_user
                    )
                    
                    result_html = f"""
                    <div class="gemini-analysis-card">
                        <div class="gemini-analysis-title">🏦 KB AI 손실 분석 결과</div>
                        <div class="ai-coaching-content" style="color: #f0f0f0; line-height: 1.8;">
                            {analysis}
                        </div>
                        <div class="kb-powered">Powered by KB AI • 손실 패턴 분석</div>
                    </div>
                    """
                    st.markdown(result_html, unsafe_allow_html=True)
                    
                    # 추가 액션 버튼
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📝 상세 복기노트 작성", key="detailed_reflection", use_container_width=True):
                            st.info("KB AI 거래 복기 페이지로 이동하여 더 상세한 복기를 진행할 수 있습니다.")
                            st.session_state.last_trade_for_reflection = {
                                'stock_name': loss_info["stock_name"],
                                'trade_type': '매도',
                                'quantity': loss_info["quantity"],
                                'price': loss_info["sell_price"],
                                'timestamp': datetime.now()
                            }
                    
                    with col2:
                        if st.button("💾 분석 결과 저장", key="save_analysis", use_container_width=True):
                            st.success("✅ KB AI 분석 결과가 저장되었습니다!")
                            
            except ImportError:
                st.error("KB AI 서비스를 사용할 수 없습니다.")
    else:
        st.markdown("""
        <div class="gemini-card">
            <h3>🚨 KB AI 연결 필요</h3>
            <p>KB AI 손실 분석을 위해 API가 필요합니다.</p>
            <p>사이드바에서 KB AI API 키를 설정해주세요.</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("⬅️ 뒤로가기", key="back_from_loss_analysis"):
        st.session_state.show_loss_analysis = False
        st.session_state.show_loss_modal = False
        st.session_state.loss_info = {}
        st.rerun()

def render_metric_card(label, value, value_type="normal"):
    """KB 테마 메트릭 카드 렌더링"""
    if value_type == "positive":
        value_class = "positive"
    elif value_type == "negative":
        value_class = "negative"
    else:
        value_class = ""
    
    return f'''
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {value_class}">{value}</div>
    </div>
    '''

def render_expected_pnl(expected_pnl_info):
    """예상 손익 표시 (KB 테마 적용)"""
    if not expected_pnl_info:
        return
    
    pnl = expected_pnl_info["expected_pnl"]
    pnl_pct = expected_pnl_info["pnl_percentage"]
    
    pnl_class = "" if pnl >= 0 else "negative"
    pnl_sign = "+" if pnl >= 0 else ""
    color = "#00ff88" if pnl >= 0 else "#ff4444"
    
    pnl_html = f'''
    <div class="pnl-preview {pnl_class}">
        <div style="font-weight: 700; font-size: 16px; color: {color}; margin-bottom: 8px;">
            📈 KB AI 예상 손익: {pnl_sign}{format_currency_smart(abs(pnl))} ({pnl_pct:+.1f}%)
        </div>
        <div style="font-size: 14px; color: #f0f0f0;">
            평균매수가: {format_currency_smart(expected_pnl_info["avg_buy_price"])} → 
            매도가: {format_currency_smart(expected_pnl_info["sell_price"])}
        </div>
    </div>
    '''
    st.markdown(pnl_html, unsafe_allow_html=True)

def create_live_chart(chart_data):
    """KB 테마가 적용된 실시간 차트 생성"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=chart_data['time'],
        y=chart_data['value'],
        mode='lines',
        name='Price',
        line=dict(color='#FFCC00', width=3),
        fill="tonexty",
        fillcolor="rgba(255, 204, 0, 0.1)"
    ))

    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="",
        height=300,
        showlegend=False,
        plot_bgcolor='#1c1c1c',
        paper_bgcolor='#1c1c1c',
        font=dict(family="Pretendard", color="#f0f0f0"),
        margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(
            tickformat=',.0f',
            gridcolor='rgba(255, 204, 0, 0.2)',
            tickfont=dict(color='#f0f0f0')
        ),
        xaxis=dict(
            gridcolor='rgba(255, 204, 0, 0.2)',
            tickfont=dict(color='#f0f0f0')
        )
    )
    
    return fig

def show_reflection_results(analysis_result):
    """복기 분석 결과 표시 (KB 테마 적용)"""
    if not analysis_result or not analysis_result.get('success'):
        st.error("복기 분석 결과가 없습니다.")
        return
    
    analysis = analysis_result.get('analysis', {})
    
    # 감정 및 패턴 분석 카드 (KB 스타일)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        emotion_data = analysis.get('emotion_analysis', {})
        primary_emotion = emotion_data.get('primary_emotion', 'N/A')
        emotion_intensity = emotion_data.get('emotion_intensity', 5)
        emotion_keywords = emotion_data.get('emotion_keywords', [])
        
        # 감정에 따른 색상 결정 (KB 테마)
        emotion_colors = {
            '공포': '#ff4444', '패닉': '#ff4444', '불안': '#FFAA00',
            '욕심': '#FFCC00', '확신': '#00ff88', '합리적': '#00ff88'
        }
        emotion_color = emotion_colors.get(primary_emotion, '#f0f0f0')
        
        emotion_html = f"""
        <div class="reflection-insight-card">
            <h4 style="color: {emotion_color}; margin-bottom: 16px;">🧠 KB AI 감정 분석</h4>
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #f0f0f0;"><strong>주요 감정:</strong></span>
                    <span class="emotion-tag" style="background-color: {emotion_color}20; color: {emotion_color};">
                        {primary_emotion}
                    </span>
                </div>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #f0f0f0;">감정 강도:</strong> 
                <div style="background: #444444; border-radius: 10px; height: 20px; margin-top: 4px;">
                    <div style="background: {emotion_color}; height: 100%; width: {emotion_intensity * 10}%; border-radius: 10px; transition: width 0.3s;"></div>
                </div>
                <small style="color: #aaaaaa;">{emotion_intensity}/10</small>
            </div>
            <div style="color: #f0f0f0;">
                <strong>감정 키워드:</strong><br>
                {', '.join(emotion_keywords) if emotion_keywords else '키워드 없음'}
            </div>
        </div>
        """
        st.markdown(emotion_html, unsafe_allow_html=True)
    
    with col2:
        pattern_data = analysis.get('pattern_recognition', {})
        trading_pattern = pattern_data.get('trading_pattern', 'N/A')
        confidence = pattern_data.get('confidence', 0)
        pattern_description = pattern_data.get('pattern_description', 'N/A')
        
        # 패턴에 따른 색상 결정 (KB 테마)
        pattern_colors = {
            '공포매도': '#ff4444', '추격매수': '#FFAA00', 
            '복수매매': '#ff4444', '과신매매': '#FFCC00',
            '합리적투자': '#00ff88'
        }
        pattern_color = pattern_colors.get(trading_pattern, '#f0f0f0')
        
        pattern_html = f"""
        <div class="reflection-insight-card">
            <h4 style="color: {pattern_color}; margin-bottom: 16px;">🎯 KB AI 패턴 분석</h4>
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #f0f0f0;"><strong>거래 패턴:</strong></span>
                    <span class="emotion-tag" style="background-color: {pattern_color}20; color: {pattern_color};">
                        {trading_pattern}
                    </span>
                </div>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #f0f0f0;">확신도:</strong> 
                <div style="background: #444444; border-radius: 10px; height: 20px; margin-top: 4px;">
                    <div style="background: {pattern_color}; height: 100%; width: {confidence * 100}%; border-radius: 10px; transition: width 0.3s;"></div>
                </div>
                <small style="color: #aaaaaa;">{confidence * 100:.0f}%</small>
            </div>
            <div style="color: #f0f0f0;">
                <strong>패턴 설명:</strong><br>
                <small style="color: #aaaaaa; line-height: 1.4;">
                    {pattern_description}
                </small>
            </div>
        </div>
        """
        st.markdown(pattern_html, unsafe_allow_html=True)
    
    # 인사이트 및 교훈 표시 (KB 테마)
    insights = analysis.get('insights', {})
    strengths = insights.get('strengths', [])
    weaknesses = insights.get('weaknesses', [])
    lessons = insights.get('lessons', [])
    
    insight_html = f"""
    <div class="reflection-result-card">
        <h4 style="color: #00ff88; margin-bottom: 16px;">💡 KB AI 복기 인사이트 & 교훈</h4>
        
        <div style="margin-bottom: 16px;">
            <strong style="color: #00ff88;">✅ 잘한 점:</strong>
            <ul style="margin: 8px 0; padding-left: 20px; color: #f0f0f0;">
                {(''.join([f'<li style="margin: 4px 0;">{item}</li>' for item in strengths]) if strengths else '<li style="color: #aaaaaa;">특별히 잘한 점이 발견되지 않았습니다.</li>')}
            </ul>
        </div>
        
        <div style="margin-bottom: 16px;">
            <strong style="color: #ff4444;">⚠️ 개선할 점:</strong>
            <ul style="margin: 8px 0; padding-left: 20px; color: #f0f0f0;">
                {(''.join([f'<li style="margin: 4px 0;">{item}</li>' for item in weaknesses]) if weaknesses else '<li style="color: #aaaaaa;">특별히 개선할 점이 발견되지 않았습니다.</li>')}
            </ul>
        </div>
        
        <div style="margin-bottom: 16px;">
            <strong style="color: #FFCC00;">📚 핵심 교훈:</strong>
            <ul style="margin: 8px 0; padding-left: 20px; color: #f0f0f0;">
                {(''.join([f'<li style="margin: 4px 0;">{item}</li>' for item in lessons]) if lessons else '<li style="color: #aaaaaa;">특별한 교훈이 발견되지 않았습니다.</li>')}
            </ul>
        </div>
    </div>
    """
    st.markdown(insight_html, unsafe_allow_html=True)
    
    # AI 해시태그 및 조언 (KB 테마)
    ai_hashtags = analysis.get('ai_hashtags', [])
    coaching_advice = analysis.get('coaching_advice', 'N/A')
    
    advice_html = f"""
    <div class="ai-coaching-card">
        <div class="ai-coaching-title">🏦 KB AI 맞춤 조언</div>
        <div style="margin-bottom: 16px;">
            <strong>🏷️ KB AI 해시태그:</strong><br>
            {' '.join([f'<span class="emotion-tag" style="background: rgba(28, 28, 28, 0.8); color: #FFCC00; margin: 2px; border: 1px solid #FFCC00;">{tag}</span>' for tag in ai_hashtags]) if ai_hashtags else '<span style="opacity: 0.8;">해시태그 없음</span>'}
        </div>
        <div class="ai-coaching-content">
            <strong>💬 개인화된 조언:</strong><br>
            {coaching_advice}
        </div>
        <div class="kb-powered">Powered by KB AI • 복기 분석 결과</div>
    </div>
    """
    st.markdown(advice_html, unsafe_allow_html=True)

# 하위 호환성을 위한 별칭
render_api_status = render_gemini_status