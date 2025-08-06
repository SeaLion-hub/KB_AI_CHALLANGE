import streamlit as st
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from db.user_db import UserDatabase
from utils.ui_components import apply_toss_css

class AuthManager:
    """사용자 인증 및 세션 관리 클래스"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """세션 상태 초기화"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'onboarding_complete' not in st.session_state:
            st.session_state.onboarding_complete = False
    
    def login(self, username: str, user_type: str) -> bool:
        """사용자 로그인 처리"""
        try:
            # 사용자 정보 설정
            st.session_state.authenticated = True
            st.session_state.user_info = {
                'username': username,
                'user_type': user_type,
                'login_time': st.session_state.get('login_time', None)
            }
            
            # 기존 사용자 중 김국민은 이미 온보딩 완료로 처리
            if user_type == "기존_reflex사용중":
                st.session_state.onboarding_complete = True
            
            return True
        except Exception as e:
            st.error(f"로그인 처리 중 오류가 발생했습니다: {str(e)}")
            return False
    
    def logout(self):
        """사용자 로그아웃"""
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.onboarding_complete = False
        
        # 관련 세션 상태 초기화
        keys_to_clear = [
            'selected_principle', 'selected_trade_for_review',
            'cash', 'portfolio', 'history', 'market_data'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self):
        """현재 로그인된 사용자 정보 반환"""
        return st.session_state.get('user_info', None)
    
    def require_login(self) -> bool:
        """로그인 필수 페이지에서 사용 - 로그인되지 않으면 메인 페이지로 리다이렉트"""
        if not self.is_logged_in():
            st.error("🔒 로그인이 필요합니다.")
            st.markdown('''
            <div style="text-align: center; margin: 2rem 0;">
                <a href="/" style="
                    display: inline-block;
                    background-color: var(--primary-blue);
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 700;
                ">🔐 로그인하러 가기</a>
            </div>
            ''', unsafe_allow_html=True)
            return False
        return True
    
    def show_user_info_sidebar(self):
        """사이드바에 사용자 정보 표시"""
        if self.is_logged_in():
            user_info = self.get_current_user()
            username = user_info['username']
            user_type = user_info['user_type']
            
            # 사용자 타입에 따른 이모지
            type_emoji = {
                "신규": "🆕",
                "기존_reflex처음": "🔄", 
                "기존_reflex사용중": "⭐"
            }
            
            type_description = {
                "신규": "신규 사용자",
                "기존_reflex처음": "KB 기존 고객",
                "기존_reflex사용중": "KB Reflex 사용자"
            }
            
            st.sidebar.markdown(f'''
            <div class="card" style="margin-bottom: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">
                        {type_emoji.get(user_type, "👤")}
                    </div>
                    <h3 style="margin: 0; color: var(--text-primary);">{username}님</h3>
                    <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.9rem;">
                        {type_description.get(user_type, user_type)}
                    </p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 로그아웃 버튼
            if st.sidebar.button("🚪 로그아웃", use_container_width=True):
                self.logout()
                st.rerun()

# 페이지 설정 (메인 앱에서 사용될 경우에만)
if __name__ == "__main__":
    st.set_page_config(
        page_title="KB Reflex - AI 투자 심리 코칭",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Toss 스타일 CSS 적용
    apply_toss_css()

    def show_login_page():
        """로그인 페이지 표시"""
        st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
        
        # 중앙 정렬을 위한 컬럼
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
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
            
            # 로그인 폼
            st.markdown('''
            <div class="card" style="max-width: 400px; margin: 0 auto;">
                <div class="card-title" style="text-align: center; margin-bottom: 2rem;">
                    로그인
                </div>
            ''', unsafe_allow_html=True)
            
            with st.form("login_form"):
                # 사용자 선택
                user_options = [
                    "이거울 (신규 사용자)",
                    "박투자 (FOMO 매수형)",
                    "김국민 (공포 매도형)"
                ]
                
                selected_user = st.selectbox(
                    "사용자를 선택하세요",
                    user_options,
                    key="user_selector"
                )
                
                # 임시 비밀번호 입력
                password = st.text_input("비밀번호", type="password", placeholder="demo123")
                
                st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
                
                login_button = st.form_submit_button(
                    "🔐 로그인",
                    use_container_width=True,
                    type="primary"
                )
                
                if login_button:
                    # 간단한 비밀번호 검증
                    if password == "demo123":
                        # 사용자 정보 추출
                        if "이거울" in selected_user:
                            username = "이거울"
                            user_type = "신규"
                        elif "박투자" in selected_user:
                            username = "박투자"
                            user_type = "기존_reflex처음"
                        else:
                            username = "김국민"
                            user_type = "기존_reflex사용중"
                        
                        # 로그인 처리
                        auth_manager = AuthManager()
                        if auth_manager.login(username, user_type):
                            st.success("✅ 로그인 성공!")
                            st.balloons()
                            
                            # 잠시 대기 후 페이지 새로고침
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ 로그인에 실패했습니다.")
                    else:
                        st.error("❌ 비밀번호가 올바르지 않습니다. (힌트: demo123)")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 데모 안내
            st.markdown('''
            <div style="text-align: center; margin-top: 2rem; padding: 1rem; background-color: #F8FAFC; border-radius: 12px;">
                <p style="color: var(--text-light); font-size: 14px; margin: 0;">
                    💡 데모 계정 비밀번호: <strong>demo123</strong><br>
                    각 사용자별로 다른 온보딩 경험을 제공합니다.
                </p>
            </div>
            ''', unsafe_allow_html=True)

    def show_onboarding():
        """사용자별 온보딩 화면"""
        user_info = st.session_state.user_info
        username = user_info['username']
        user_type = user_info['user_type']
        
        if user_type == "신규":
            show_principles_onboarding(username)
        elif user_type == "기존_reflex처음":
            show_trade_selection_onboarding(username)
        else:  # 기존_reflex사용중
            # 온보딩 건너뛰기
            st.session_state.onboarding_complete = True
            st.rerun()

    def show_principles_onboarding(username):
        """투자 원칙 선택 온보딩 (신규 사용자용)"""
        from db.principles_db import get_investment_principles
        
        st.markdown(f'''
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2rem; color: var(--text-primary); margin-bottom: 0.5rem;">
                환영합니다, {username}님! 👋
            </h1>
            <p style="color: var(--text-secondary); font-size: 1.1rem;">
                투자를 시작하기 전에, 존경하는 투자 대가의 원칙을 선택해보세요
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        principles = get_investment_principles()
        
        col1, col2, col3 = st.columns(3)
        selected_principle = None
        
        for i, (name, data) in enumerate(principles.items()):
            with [col1, col2, col3][i % 3]:
                st.markdown(f'''
                <div class="card" style="height: 300px; cursor: pointer;">
                    <div style="text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">{data['icon']}</div>
                        <h3 style="color: var(--text-primary); margin-bottom: 1rem;">{name}</h3>
                        <p style="color: var(--text-secondary); font-size: 14px; line-height: 1.5;">
                            {data['description']}
                        </p>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"{name} 선택", key=f"select_{name}", use_container_width=True):
                    selected_principle = name
        
        if selected_principle:
            st.session_state.selected_principle = selected_principle
            st.session_state.onboarding_complete = True
            st.success(f"✅ {selected_principle}의 투자 원칙을 선택하셨습니다!")
            st.balloons()
            import time
            time.sleep(2)
            st.rerun()

    def show_trade_selection_onboarding(username):
        """거래 선택 온보딩 (기존 사용자, Reflex 처음 사용)"""
        from db.user_db import UserDatabase
        
        st.markdown(f'''
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2rem; color: var(--text-primary); margin-bottom: 0.5rem;">
                다시 만나뵙네요, {username}님! 👋
            </h1>
            <p style="color: var(--text-secondary); font-size: 1.1rem;">
                과거 거래 중에서 어떤 거래부터 복기해보시겠어요?
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        # 사용자 거래 데이터 로드
        user_db = UserDatabase()
        trades_data = user_db.get_user_trades(username)
        
        if trades_data is not None and len(trades_data) > 0:
            # 수익률 상위 2개, 하위 2개 추출
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
                        st.session_state.onboarding_complete = True
                        st.success("✅ 거래를 선택했습니다!")
                        import time
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
                        st.session_state.onboarding_complete = True
                        st.success("✅ 거래를 선택했습니다!")
                        import time
                        time.sleep(1)
                        st.rerun()
        
        # 건너뛰기 옵션
        st.markdown('<div style="text-align: center; margin-top: 2rem;">', unsafe_allow_html=True)
        if st.button("나중에 선택하기", key="skip_onboarding", type="secondary"):
            st.session_state.onboarding_complete = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    def main():
        """메인 애플리케이션 로직"""
        # 인증 상태 확인
        auth_manager = AuthManager()
        
        if not auth_manager.is_logged_in():
            show_login_page()
        else:
            # 온보딩 완료 여부 확인
            if not st.session_state.get('onboarding_complete', False):
                show_onboarding()
            else:
                # 메인 애플리케이션으로 리다이렉트
                st.markdown('''
                <script>
                    window.location.href = '/Dashboard';
                </script>
                ''', unsafe_allow_html=True)
                
                # JavaScript 리다이렉트가 작동하지 않는 경우를 대비한 안내
                st.markdown(f'''
                <div style="text-align: center; margin-top: 3rem;">
                    <h2>환영합니다, {st.session_state.user_info['username']}님!</h2>
                    <p>대시보드 페이지로 이동해주세요.</p>
                    <a href="/Dashboard" style="
                        display: inline-block;
                        background-color: var(--primary-blue);
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 8px;
                        font-weight: 700;
                        margin-top: 1rem;
                    ">📊 대시보드로 이동</a>
                </div>
                ''', unsafe_allow_html=True)

    main()