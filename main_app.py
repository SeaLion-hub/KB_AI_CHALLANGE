import streamlit as st
import sys
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from db.user_db import UserDatabase
from db.principles_db import get_investment_principles, get_principle_details
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
            'cash', 'portfolio', 'history', 'market_data', 'chart_data',
            'survey_completed', 'recommended_principle'
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
    """투자 원칙 선택 온보딩 (설문조사 포함)"""
    st.markdown('''
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 2rem; color: var(--text-primary);">
            투자 성향 분석 🎯
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            간단한 질문으로 당신에게 맞는 투자 방식을 찾아보세요
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 1. 세션 상태 플래그로 플로우 관리
    if not st.session_state.get('survey_completed', False):
        # 2. 설문조사 표시
        st.markdown("### 📋 투자 성향 진단 설문")
        
        # 2b. 폼 생성 및 질문들
        with st.form("investment_survey"):
            st.markdown("#### 다음 질문들에 답해주세요:")
            
            # Q1
            q1 = st.radio(
                "**Q1. 투자를 할 때 더 중요하게 생각하는 것은 무엇인가요?**",
                ["안정적인 수익률 (가치 투자)", "높은 성장 가능성 (성장 투자)"],
                key="q1"
            )
            
            st.markdown("---")
            
            # Q2
            q2 = st.radio(
                "**Q2. 당신이 더 잘 이해할 수 있는 기업은 어디인가요?**",
                ["오랜 기간 검증된 우량 기업 (가치 투자)", "우리 일상을 바꾸는 새로운 기업 (성장 투자)"],
                key="q2"
            )
            
            st.markdown("---")
            
            # Q3
            q3 = st.radio(
                "**Q3. 위험에 대한 당신의 생각은 어떤가요?**",
                ["손실 가능성을 최소화하는 것이 가장 중요하다. (가치 투자)", "큰 수익을 위해 어느 정도의 위험은 감수할 수 있다. (성장 투자)"],
                key="q3"
            )
            
            # 2c. 제출 버튼
            submitted = st.form_submit_button("내 투자 성향 분석하기", type="primary", use_container_width=True)
            
            # 2d. 폼 제출 시 성향 계산
            if submitted:
                # 가치 투자 답변 개수 계산
                value_investment_count = 0
                if "가치 투자" in q1:
                    value_investment_count += 1
                if "가치 투자" in q2:
                    value_investment_count += 1
                if "가치 투자" in q3:
                    value_investment_count += 1
                
                # 2e. 결과에 따른 원칙 추천
                if value_investment_count >= 2:  # 가치 투자 답변이 더 많음
                    st.session_state.recommended_principle = "벤저민 그레이엄"
                else:  # 성장 투자 답변이 더 많음
                    st.session_state.recommended_principle = "피터 린치"
                
                # 2f. 설문 완료 플래그 설정 후 리런
                st.session_state.survey_completed = True
                st.rerun()
    
    else:
        # 3. 설문 완료 후 추천 결과 표시
        recommended = st.session_state.recommended_principle
        
        # 3b. 추천 결과를 눈에 띄게 표시
        st.markdown(f'''
        <div style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); 
                    border: 2px solid #3182F6; border-radius: 20px; padding: 30px; 
                    text-align: center; margin: 2rem 0;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎉</div>
            <h2 style="color: #3182F6; margin-bottom: 1rem; font-size: 1.8rem;">
                분석 완료!
            </h2>
            <h3 style="color: var(--text-primary); margin-bottom: 1.5rem; font-size: 1.4rem;">
                AI가 당신의 성향을 분석한 결과,<br>
                <strong style="color: #3182F6; font-size: 1.6rem;">'{recommended}'</strong>의<br>
                투자 방식이 가장 적합해 보입니다!
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        # 추천된 원칙의 상세 정보 표시
        principle_data = get_principle_details(recommended)
        if principle_data:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f'''
                <div style="text-align: center; padding: 2rem; background-color: var(--card-bg); 
                           border-radius: 15px; margin-bottom: 1rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">{principle_data['icon']}</div>
                    <h3 style="color: var(--text-primary); margin: 0;">{recommended}</h3>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**투자 철학:**")
                st.info(f'"{principle_data["philosophy"]}"')
                
                st.markdown(f"**특징:**")
                st.write(principle_data["description"])
                
                st.markdown(f"**핵심 원칙:**")
                for principle in principle_data["core_principles"][:3]:
                    st.markdown(f"• {principle}")
        
        # 다른 선택지도 보여주기
        st.markdown("---")
        st.markdown("### 🤔 다른 투자 방식도 궁금하신가요?")
        
        principles = get_investment_principles()
        other_principles = [name for name in principles.keys() if name != recommended]
        
        col1, col2 = st.columns(2)
        
        for i, other_name in enumerate(other_principles):
            with [col1, col2][i % 2]:
                other_data = principles[other_name]
                st.markdown(f'''
                <div class="card" style="height: 200px; cursor: pointer;">
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{other_data['icon']}</div>
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">{other_name}</h4>
                        <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.4;">
                            {other_data['description'][:80]}...
                        </p>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"{other_name} 선택하기", key=f"alt_{other_name}", use_container_width=True):
                    st.session_state.recommended_principle = other_name
                    st.rerun()
        
        # 3c. 최종 확인 버튼
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(
                "이 원칙으로 투자 여정 시작하기", 
                key="confirm_principle",
                type="primary",
                use_container_width=True
            ):
                # 3d. 원래 로직 실행
                st.session_state.selected_principle = recommended
                st.session_state.onboarding_needed = None
                st.success(f"✅ {recommended}의 투자 원칙을 선택하셨습니다!")
                st.balloons()
                time.sleep(2)
                st.rerun()
        
        # 설문 다시하기 옵션
        st.markdown('<div style="text-align: center; margin-top: 1rem;">', unsafe_allow_html=True)
        if st.button("🔄 설문 다시하기", key="retake_survey"):
            st.session_state.survey_completed = False
            if 'recommended_principle' in st.session_state:
                del st.session_state.recommended_principle
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

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