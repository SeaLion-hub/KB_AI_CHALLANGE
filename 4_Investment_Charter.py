import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ui_components import apply_toss_css
from ml.investment_charter_logic import InvestmentCharter
from ml.investment_charter import show_investment_charter_ui

# 페이지 설정
st.set_page_config(
    page_title="KB Reflex - 투자 헌장",
    page_icon="📜",
    layout="wide"
)

# CSS 적용
apply_toss_css()

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
    
    if st.sidebar.button("🤖 AI 코칭", use_container_width=True):
        st.switch_page("pages/3_AI_Coaching.py")
    
    st.sidebar.markdown("📜 **투자 헌장** ← 현재 위치")

def main():
    """메인 함수"""
    # 사이드바에 사용자 정보 및 네비게이션 표시
    show_user_switcher_sidebar()
    
    # 메인 콘텐츠
    username = st.session_state.current_user['username']
    show_investment_charter_ui(username)

if __name__ == "__main__":
    main()