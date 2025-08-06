import streamlit as st
import sys
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from db.user_db import UserDatabase
from db.principles_db import get_investment_principles
from utils.ui_components import apply_toss_css

# 페이지 설정
st.set_page_config(
    page_title="KB Reflex - AI 투자 심리 코칭",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Toss 스타일 CSS 적용
apply_toss_css()

class SimpleAuthManager:
    """간소화된 사용자 인증 및 세션 관리 클래스"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """세션 상태 초기화"""
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
    
    def show_user_selector(self):
        """구글 로그인 스타일의 사용자 선택기"""
        st.markdown('''
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="font-size: 3rem; font-weight: 800; color: var(--primary-blue); margin-bottom: 1rem;">
                🧠 KB Reflex
            </h1>
            <h2 style="font-size: 1.5rem; color: var(--text-secondary); font-weight: 400; margin-bottom: 3rem;">
                AI 투자 심리 코칭 플랫폼
            </h2>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown("### 👤 사용자를 선택하세요")
        
        # 사용자 프로필 카드들
        users = [
            {
                'username': '이거울',
                'type': '신규',
                'description': '투자를 처음 시작하는 신규 사용자',
                'icon': '🆕',
                'color': '#3182F6'
            },
            {
                'username': '박투자', 
                'type': '기존_reflex처음',
                'description': 'FOMO 매수 경향이 있는 기존 고객',
                'icon': '🔄',
                'color': '#FF9500'
            },
            {
                'username': '김국민',
                'type': '기존_reflex사용중', 
                'description': '공포 매도 경향, Reflex 기존 사용자',
                'icon': '⭐',
                'color': '#14AE5C'
            }
        ]
        
        col1, col2, col3 = st.columns(3)
        
        for i, user in enumerate(users):
            with [col1, col2, col3][i]:
                st.markdown(f'''
                <div class="card" style="height: 200px; text-align: center; cursor: pointer; border: 2px solid {user['color']}20; transition: all 0.3s ease;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">{user['icon']}</div>
                    <h3 style="color: {user['color']}; margin-bottom: 0.5rem;">{user['username']}</h3>
                    <p style="color: var(--text-secondary); font-size: 14px; line-height: 1.4;">
                        {user['description']}
                    </p>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(
                    f"{user['username']}으로 시작하기", 
                    key=f"user_{user['username']}",
                    use_container_width=True,
                    type="primary"
                ):
                    self.login_user(user)
                    st.rerun()
    
    def login_user(self, user_data):
        """사용자 로그인 처리"""
        st.session_state.current_user = {
            'username': user_data['username'],
            'user_type': user_data['type'],
            'description': user_data['description'],
            'icon': user_data['icon'],
            'login_time': datetime.now()
        }
        
        # 사용자별 초기 설정
        if user_data['type'] == "신규":
            st.session_state.onboarding_needed = "principles"
        elif user_data['type'] == "기존_reflex처음":
            st.session_state.onboarding_needed = "trade_selection"  
        else:
            st.session_state.onboarding_needed = None
        
        st.success(f"✅ {user_data['username']}님으로 로그인되었습니다!")
        st.balloons()
    
    def logout(self):
        """로그아웃"""
        st.session_state.current_user = None
        st.session_state.onboarding_needed = None
        
        # 관련 세션 상태 초기화
        keys_to_clear = [
            'selected_principle', 'selected_trade_for_review',
            'cash', 'portfolio', 'history', 'market_data', 'chart_data'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return st.session_state.current_user is not None
    
    def get_current_user(self):
        """현재 사용자 정보 반환"""
        return st.session_state.current_user
    
    def show_user_switcher_sidebar(self):
        """사이드바에 사용자 전환기 표시"""
        if self.is_logged_in():
            user = self.get_current_user()
            
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
                self.logout()
                st.rerun()

def show_principles_onboarding():
    """투자 원칙 선택 온보딩"""
    st.markdown('''
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 2rem; color: var(--text-primary);">
            투자 대가의 원칙을 선택하세요 🎯
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            선택한 원칙이 당신의 투자 여정을 안내합니다
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    principles = get_investment_principles()
    
    col1, col2, col3 = st.columns(3)
    
    for i, (name, data) in enumerate(principles.items()):
        with [col1, col2, col3][i % 3]:
            st.markdown(f'''
            <div class="card" style="height: 350px; cursor: pointer;">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">{data['icon']}</div>
                    <h3 style="color: var(--text-primary); margin-bottom: 1rem;">{name}</h3>
                    <p style="color: var(--text-secondary); font-size: 14px; line-height: 1.5; margin-bottom: 1rem;">
                        {data['description']}
                    </p>
                    <div style="background-color: #F8FAFC; padding: 12px; border-radius: 8px; margin-bottom: 1rem;">
                        <p style="font-style: italic; font-size: 13px; color: var(--text-light); margin: 0;">
                            "{data['philosophy'][:60]}..."
                        </p>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            if st.button(
                f"{name} 선택하기",
                key=f"principle_{name}",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.selected_principle = name
                st.session_state.onboarding_needed = None
                st.success(f"✅ {name}의 투자 원칙을 선택하셨습니다!")
                st.balloons()
                time.sleep(2)
                st.rerun()

def show_trade_selection_onboarding():
    """거래 선택 온보딩"""
    user = st.session_state.current_user
    username = user['username']
    
    st.markdown(f'''
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 2rem; color: var(--text-primary);">
            복기할 거래를 선택하세요 📊
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            {username}님의 과거 거래를 분석해보겠습니다
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 사용자 거래 데이터 로드
    user_db = UserDatabase()
    trades_data = user_db.get_user_trades(username)
    
    if trades_data is not None and len(trades_data) > 0:
        # 수익률 상위/하위 거래 표시
        top_trades = trades_data.nlargest(2, '수익률')
        bottom_trades = trades_data.nsmallest(2, '수익률')
        
        st.markdown("### 🏆 수익률 상위 거래")
        col1, col2 = st.columns(2)
        
        for i, (_, trade) in enumerate(top_trades.iterrows()):
            with [col1, col2][i]:
                st.markdown(f'''
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: var(--text-primary);">{trade['종목명']}</h4>
                            <p style="margin: 5px 0; color: var(--text-secondary); font-size: 14px;">
                                {trade['거래일시'].strftime('%Y-%m-%d')} | {trade['거래구분']}
                            </p>
                            <p style="margin: 5px 0; color: var(--text-light); font-size: 13px;">
                                💬 {trade['메모'][:30]}...
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 18px; font-weight: 700; color: var(--success-color);">
                                +{trade['수익률']:.1f}%
                            </div>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"이 거래 복기하기", key=f"select_top_{i}", use_container_width=True):
                    st.session_state.selected_trade_for_review = trade.to_dict()
                    st.session_state.onboarding_needed = None
                    st.success("✅ 거래를 선택했습니다!")
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("### 📉 수익률 하위 거래")
        col3, col4 = st.columns(2)
        
        for i, (_, trade) in enumerate(bottom_trades.iterrows()):
            with [col3, col4][i]:
                st.markdown(f'''
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: var(--text-primary);">{trade['종목명']}</h4>
                            <p style="margin: 5px 0; color: var(--text-secondary); font-size: 14px;">
                                {trade['거래일시'].strftime('%Y-%m-%d')} | {trade['거래구분']}
                            </p>
                            <p style="margin: 5px 0; color: var(--text-light); font-size: 13px;">
                                💬 {trade['메모'][:30]}...
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 18px; font-weight: 700; color: var(--negative-color);">
                                {trade['수익률']:.1f}%
                            </div>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"이 거래 복기하기", key=f"select_bottom_{i}", use_container_width=True):
                    st.session_state.selected_trade_for_review = trade.to_dict()
                    st.session_state.onboarding_needed = None
                    st.success("✅ 거래를 선택했습니다!")
                    time.sleep(1)
                    st.rerun()
    
    # 건너뛰기 옵션
    st.markdown('<div style="text-align: center; margin-top: 2rem;">', unsafe_allow_html=True)
    if st.button("나중에 선택하기", key="skip_onboarding", type="secondary"):
        st.session_state.onboarding_needed = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_main_navigation():
    """메인 애플리케이션 네비게이션"""
    user = st.session_state.current_user
    
    st.markdown(f'''
    <div style="text-align: center; margin: 3rem 0;">
        <h1 style="font-size: 2.5rem; color: var(--text-primary); margin-bottom: 0.5rem;">
            환영합니다, {user['username']}님! 👋
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.2rem;">
            KB Reflex와 함께 더 나은 투자 습관을 만들어보세요
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 메인 기능 카드들
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('''
        <div class="card" style="height: 200px; text-align: center; cursor: pointer;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">대시보드</h3>
            <p style="color: var(--text-secondary); font-size: 14px;">
                실시간 포트폴리오 현황과<br>AI 투자 인사이트 확인
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button("📊 대시보드 보기", key="goto_dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Dashboard.py")
    
    with col2:
        st.markdown('''
        <div class="card" style="height: 200px; text-align: center; cursor: pointer;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📝</div>
            <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">거래 복기</h3>
            <p style="color: var(--text-secondary); font-size: 14px;">
                과거 거래 상황을 재현하고<br>객관적으로 분석하기
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button("📝 거래 복기하기", key="goto_review", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Trade_Review.py")
    
    with col3:
        st.markdown('''
        <div class="card" style="height: 200px; text-align: center; cursor: pointer;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
            <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">AI 코칭</h3>
            <p style="color: var(--text-secondary); font-size: 14px;">
                딥러닝 기반 실시간<br>투자 심리 분석 및 코칭
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button("🤖 AI 코칭 받기", key="goto_coaching", use_container_width=True, type="primary"):
            st.switch_page("pages/3_AI_Coaching.py")
    
    # 추가 기능들
    st.markdown("---")
    st.markdown("### 🛠️ 추가 기능")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📜 나의 투자 헌장", key="goto_charter", use_container_width=True):
            st.switch_page("pages/4_Investment_Charter.py")
    
    with col2:
        if st.button("⚙️ 설정", key="goto_settings", use_container_width=True):
            st.info("설정 페이지는 준비 중입니다.")

def main():
    """메인 애플리케이션 로직"""
    auth_manager = SimpleAuthManager()
    
    # 사이드바에 사용자 전환기 표시 (로그인된 경우)
    if auth_manager.is_logged_in():
        auth_manager.show_user_switcher_sidebar()
    
    if not auth_manager.is_logged_in():
        # 로그인 페이지 표시
        auth_manager.show_user_selector()
    else:
        # 온보딩 필요 여부 확인
        onboarding_needed = st.session_state.get('onboarding_needed')
        
        if onboarding_needed == "principles":
            show_principles_onboarding()
        elif onboarding_needed == "trade_selection":
            show_trade_selection_onboarding() 
        else:
            # 메인 네비게이션 표시
            show_main_navigation()

if __name__ == "__main__":
    main()