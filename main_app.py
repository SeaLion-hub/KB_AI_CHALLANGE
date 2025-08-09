# CHANGELOG:
# - st.set_page_config()를 import 직후 최상단으로 이동 (크래시 방지)
# - @st.cache_resource 정의를 set_page_config 이후로 재배치
# - safe_navigate_to_page()에 절대경로 검증 + st.switch_page 호환성 체크 추가
# - 모든 f-string HTML 출력에 sanitize_html_text() 일관 적용
# - 경로/데이터 로드 실패 시 사용자 친화적 에러 메시지 개선
# - st.experimental_rerun() 폴백으로 레거시 Streamlit 버전 지원

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
import pytz
import re

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# ================================
# [STREAMLIT CONFIG - 최우선 설정]
# ================================
st.set_page_config(
    page_title="KB Reflex - AI 투자 심리 코칭",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================================
# [IMPORTS]
# ================================
from db.principles_db import get_investment_principles, get_principle_details
from utils.ui_components import apply_toss_css
from ml.mirror_coaching import MirrorCoaching
from db.central_data_manager import get_data_manager, get_user_profile, get_user_trading_history

# ================================
# [CONSTANTS & CONFIGURATION]
# ================================

# 페이지 네비게이션 매핑 테이블
PAGE_NAVIGATION = {
    "dashboard": "pages/1_Dashboard.py",
    "review": "pages/2_Trade_Review.py", 
    "coaching": "pages/3_AI_Coaching.py",
    "charter": "pages/4_Investment_Charter.py"
}

# 감정태그 색상 팔레트 (안전한 색상만)
EMOTION_PALETTE = {
    "#욕심": "#FEF3C7",      # 연한 노랑
    "#확신": "#DBEAFE",      # 연한 파랑
    "#흥분": "#FECACA",      # 연한 빨강
    "#불안": "#F3E8FF",      # 연한 보라
    "#후회": "#E5E7EB",      # 회색
    "#공포": "#FEE2E2",      # 연한 빨강
    "#냉정": "#ECFDF5",      # 연한 초록
    "기본": "#F8FAFC"        # 중립색 (기본값)
}

# 시간대 설정 (Asia/Seoul)
KST = pytz.timezone('Asia/Seoul')

# 세션 상태 키 정의
class SessionKeys:
    """세션 상태 키 표준화"""
    USER = "REFLEX_USER"
    ONBOARDING_STAGE = "REFLEX_ONBOARDING_STAGE"  # "principles" | "trade_selection" | None
    MIRROR_INSIGHTS = "REFLEX_MIRROR_INSIGHTS"
    SELECTED_TRADE = "REFLEX_SELECTED_TRADE"
    SURVEY_DONE = "REFLEX_SURVEY_DONE"
    RECOMMENDED_PRINCIPLE = "REFLEX_RECOMMENDED_PRINCIPLE"
    SELECTED_PRINCIPLE = "REFLEX_SELECTED_PRINCIPLE"
    TRANSITION_STATE = "REFLEX_TRANSITION_STATE"
    PENDING_PAGE = "REFLEX_PENDING_PAGE"  # 레거시 네비게이션용

# ================================
# [CACHED RESOURCES - set_page_config 이후 정의]
# ================================

@st.cache_resource
def get_mirror_coach() -> MirrorCoaching:
    """MirrorCoaching 싱글턴 인스턴스 (캐시됨)"""
    try:
        return MirrorCoaching()
    except Exception as e:
        st.error(f"❌ AI 거울 코칭 시스템 초기화 실패: {str(e)}")
        # 더미 객체 반환으로 앱 크래시 방지
        class DummyMirrorCoach:
            def initialize_for_user(self, username): return {}
            def generate_insights_for_trade(self, trade, username): return {}
        return DummyMirrorCoach()

# ================================
# [UTILITY FUNCTIONS]
# ================================

def sanitize_html_text(text: str) -> str:
    """HTML 안전장치: 기본적인 텍스트 살균"""
    if not isinstance(text, str):
        return str(text)
    
    # < > 문자 제거, 줄바꿈만 허용
    sanitized = re.sub(r'[<>]', '', text)
    # 줄바꿈을 <br>로 변환
    sanitized = sanitized.replace('\n', '<br>')
    return sanitized

def get_emotion_color(emotion_tag: str) -> str:
    """감정태그에서 안전한 색상 반환"""
    return EMOTION_PALETTE.get(emotion_tag, EMOTION_PALETTE["기본"])

def format_kst_datetime(dt: datetime) -> str:
    """Asia/Seoul 시간대로 날짜 포맷팅"""
    try:
        if dt.tzinfo is None:
            dt = KST.localize(dt)
        else:
            dt = dt.astimezone(KST)
        return dt.strftime('%Y.%m.%d %H:%M')
    except Exception:
        return "날짜 불명"

def clear_reflex_session_state():
    """REFLEX_ 접두어 세션 상태 전체 삭제 유틸"""
    keys_to_delete = [key for key in st.session_state.keys() if key.startswith("REFLEX_")]
    for key in keys_to_delete:
        del st.session_state[key]

def safe_navigate_to_page(page_key: str):
    """안전한 페이지 네비게이션 (절대경로 검증 + 호환성 체크)"""
    if page_key not in PAGE_NAVIGATION:
        st.warning(f"⚠️ 알 수 없는 페이지: {sanitize_html_text(page_key)}")
        return
    
    page_rel = PAGE_NAVIGATION[page_key]
    page_abs = project_root / page_rel
    
    # 절대경로로 파일 존재 검증
    if not page_abs.exists():
        st.warning(f"📄 페이지 준비 중입니다: {sanitize_html_text(page_key.title())}")
        st.info(f"💡 찾는 경로: {page_abs}")
        return
    
    # st.switch_page 호환성 체크
    if hasattr(st, "switch_page"):
        try:
            st.switch_page(page_rel)  # 기존 상대경로 문자열 사용
        except Exception as e:
            st.error(f"❌ 페이지 이동 실패: {str(e)}")
            st.session_state[SessionKeys.PENDING_PAGE] = page_key
            st.rerun()
    else:
        # 레거시 Streamlit 버전 대체 동작
        st.warning("⚠️ 구버전 Streamlit에서는 페이지 이동이 제한됩니다.")
        st.session_state[SessionKeys.PENDING_PAGE] = page_key
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            st.rerun()

# ================================
# [SESSION STATE MANAGEMENT]
# ================================

def init_session_state():
    """세션 상태 일원화 초기화"""
    session_defaults = {
        SessionKeys.USER: None,
        SessionKeys.ONBOARDING_STAGE: None,
        SessionKeys.MIRROR_INSIGHTS: {},
        SessionKeys.SELECTED_TRADE: None,
        SessionKeys.SURVEY_DONE: False,
        SessionKeys.RECOMMENDED_PRINCIPLE: None,
        SessionKeys.SELECTED_PRINCIPLE: None,
        SessionKeys.TRANSITION_STATE: None,
        SessionKeys.PENDING_PAGE: None
    }
    
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# 초기화
apply_toss_css()
init_session_state()

# ================================
# [ENHANCED AUTH MANAGER]
# ================================

class EnhancedAuthManager:
    """향상된 사용자 인증 및 세션 관리 클래스"""
    
    def __init__(self):
        try:
            self.data_manager = get_data_manager()
            self.mirror_coach = get_mirror_coach()  # 캐시된 싱글턴 사용
        except Exception as e:
            st.error(f"❌ 시스템 초기화 실패: {str(e)}")
            self.data_manager = None
            self.mirror_coach = None
    
    def show_elegant_user_selector(self):
        """세련된 사용자 선택기"""
        st.markdown(f'''
        <div style="min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="background: white; border-radius: 24px; padding: 3rem; box-shadow: 0 25px 50px rgba(0,0,0,0.15); max-width: 900px; width: 100%;">
                <div style="text-align: center; margin-bottom: 3rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">🧠</div>
                    <h1 style="font-size: 2.5rem; font-weight: 800; color: var(--text-primary); margin-bottom: 1rem; letter-spacing: -1px;">
                        KB Reflex
                    </h1>
                    <p style="font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 0;">
                        AI 기반 투자 심리 코칭 플랫폼
                    </p>
                    <p style="font-size: 1rem; color: var(--text-light); margin-top: 0.5rem;">
                        과거의 거래를 성장의 자산으로 바꾸는 '투자 복기' 서비스
                    </p>
                </div>
        ''', unsafe_allow_html=True)
        
        st.markdown("### 👤 사용자를 선택하세요")
        
        # 데이터 매니저 안전성 체크
        if not self.data_manager:
            st.error("❌ 데이터 시스템에 연결할 수 없습니다. 페이지를 새로고침해주세요.")
            return
        
        # 중앙 데이터 매니저에서 사용자 정보 로드
        try:
            users = self.data_manager.get_all_users(refresh=False)
        except Exception as e:
            st.error(f"❌ 사용자 데이터 로드 실패: {sanitize_html_text(str(e))}")
            st.info("💡 기본 사용자 데이터를 생성하려면 페이지를 새로고침해주세요.")
            return
        
        if not users:
            st.warning("⚠️ 등록된 사용자가 없습니다.")
            st.info("💡 시스템이 기본 사용자를 생성 중입니다. 잠시 후 다시 시도해주세요.")
            return
        
        # 사용자 수에 따라 동적으로 컬럼 생성
        if len(users) <= 3:
            cols = st.columns(len(users))
        else:
            cols = st.columns(3)
        
        for i, user in enumerate(users):
            col_index = i % len(cols)
            with cols[col_index]:
                self._render_user_card(user, i)
        
        # 하단 정보
        st.markdown('''
            </div>
        </div>
        
        <style>
        .user-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            border-color: var(--primary-blue);
        }
        </style>
        ''', unsafe_allow_html=True)
    
    def _render_user_card(self, user, index):
        """사용자 카드 렌더링 (안전한 텍스트 처리)"""
        # 안전한 텍스트 처리
        safe_username = sanitize_html_text(user.username)
        safe_description = sanitize_html_text(user.description)
        safe_subtitle = sanitize_html_text(user.subtitle)
        safe_badge = sanitize_html_text(user.badge)
        safe_icon = sanitize_html_text(user.icon)
        
        st.markdown(f'''
        <div class="user-card" style="
            background: white;
            border: 2px solid {user.color}20;
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            height: 320px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
        ">
            <div style="position: absolute; top: 1rem; right: 1rem; background: {user.color}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
                {safe_badge}
            </div>
            <div>
                <div style="font-size: 4rem; margin-bottom: 1rem;">{safe_icon}</div>
                <h3 style="color: {user.color}; margin-bottom: 0.5rem; font-size: 1.5rem;">{safe_username}</h3>
                <p style="color: var(--text-secondary); font-size: 1rem; line-height: 1.4; margin-bottom: 1rem;">
                    {safe_description}
                </p>
                <p style="color: var(--text-light); font-size: 0.85rem; line-height: 1.3;">
                    {safe_subtitle}
                </p>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 세련된 선택 버튼
        if st.button(
            f"✨ {safe_username}으로 시작하기", 
            key=f"user_{safe_username}_{index}",
            use_container_width=True,
            type="primary",
            help=f"{safe_username}님으로 로그인합니다"
        ):
            self.elegant_login_transition(user)
    
    def elegant_login_transition(self, user_data):
        """세련된 로그인 전환 (rerun 최소화)"""
        # 세션 상태 설정
        st.session_state[SessionKeys.USER] = {
            'username': user_data.username,
            'user_type': user_data.user_type,
            'description': user_data.description,
            'icon': user_data.icon,
            'color': user_data.color,
            'login_time': datetime.now(KST)
        }
        
        # 온보딩 단계 설정 (상태 머신)
        if user_data.onboarding_type == "principles":
            st.session_state[SessionKeys.ONBOARDING_STAGE] = "principles"
        elif user_data.onboarding_type == "trade_selection":
            st.session_state[SessionKeys.ONBOARDING_STAGE] = "trade_selection"  
        else:
            st.session_state[SessionKeys.ONBOARDING_STAGE] = None
        
        # CSS 애니메이션으로 즉시 피드백 (sleep 제거)
        self.show_login_success_animation(user_data)
        
        # 단일 rerun
        st.rerun()
    
    def show_login_success_animation(self, user_data):
        """로그인 성공 애니메이션 (CSS 기반, 안전한 텍스트 처리)"""
        safe_username = sanitize_html_text(user_data.username)
        safe_icon = sanitize_html_text(user_data.icon)
        
        st.markdown(f'''
        <div style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
            z-index: 9999;
            text-align: center;
            min-width: 300px;
            animation: elegantFadeIn 0.8s ease-out;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">{safe_icon}</div>
            <h3 style="color: {user_data.color}; margin-bottom: 0.5rem;">환영합니다!</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                {safe_username}님으로 로그인되었습니다
            </p>
            <div style="
                width: 40px;
                height: 40px;
                border: 3px solid {user_data.color};
                border-top: 3px solid transparent;
                border-radius: 50%;
                margin: 0 auto;
                animation: spin 1s linear infinite;
            "></div>
        </div>
        
        <style>
        @keyframes elegantFadeIn {{
            0% {{ opacity: 0; transform: translate(-50%, -60%); }}
            100% {{ opacity: 1; transform: translate(-50%, -50%); }}
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        ''', unsafe_allow_html=True)
    
    def logout(self):
        """로그아웃 (REFLEX_ 키 전체 삭제)"""
        clear_reflex_session_state()
        st.rerun()
    
    def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return st.session_state.get(SessionKeys.USER) is not None
    
    def get_current_user(self):
        """현재 사용자 정보 반환"""
        return st.session_state.get(SessionKeys.USER)
    
    def show_enhanced_sidebar(self):
        """향상된 사이드바 표시 (안전한 텍스트 처리)"""
        if self.is_logged_in():
            user = self.get_current_user()
            
            # 사용자 프로필 카드 (안전한 텍스트 처리)
            safe_username = sanitize_html_text(user['username'])
            safe_description = sanitize_html_text(user['description'])
            safe_icon = sanitize_html_text(user['icon'])
            safe_user_type = sanitize_html_text(user.get('user_type', ''))
            
            st.sidebar.markdown(f'''
            <div style="
                background: linear-gradient(135deg, {user['color']}15 0%, {user['color']}25 100%);
                border: 2px solid {user['color']}40;
                border-radius: 20px;
                padding: 1.5rem;
                text-align: center;
                margin-bottom: 1.5rem;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{safe_icon}</div>
                <h3 style="margin: 0; color: var(--text-primary); font-size: 1.2rem;">{safe_username}님</h3>
                <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.85rem; line-height: 1.4;">
                    {safe_description}
                </p>
                <div style="
                    background: {user['color']};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 700;
                    margin-top: 0.75rem;
                    display: inline-block;
                ">
                    {safe_user_type.replace('_', ' ').upper()}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 사용자 전환 버튼
            if st.sidebar.button("🔄 사용자 전환", use_container_width=True, help="다른 사용자로 로그인합니다"):
                self.logout()
            
            # AI 거울 코칭 상태 표시
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🪞 AI 거울 코칭")
            
            # 거울 인사이트 표시
            mirror_insights = st.session_state.get(SessionKeys.MIRROR_INSIGHTS, {})
            if mirror_insights:
                st.sidebar.success(f"📊 {len(mirror_insights)}개의 유사 패턴 발견")
                if st.sidebar.button("💡 인사이트 보기", help="발견된 패턴을 확인합니다"):
                    self.show_mirror_insights(mirror_insights)
            else:
                st.sidebar.info("🔍 거래 패턴 분석 대기 중")
    
    def show_mirror_insights(self, insights):
        """거울 인사이트 표시 (안전한 텍스트 처리)"""
        st.sidebar.markdown("#### 🪞 발견된 패턴")
        for pattern_type, data in insights.items():
            safe_pattern = sanitize_html_text(str(pattern_type))
            safe_advice = sanitize_html_text(str(data.get('advice', '')))
            
            st.sidebar.markdown(f"**{safe_pattern}:** {data.get('count', 0)}회")
            if safe_advice:
                st.sidebar.caption(safe_advice)

# ================================
# [ONBOARDING FUNCTIONS]
# ================================

def show_enhanced_principles_onboarding():
    """향상된 투자 원칙 선택 온보딩"""
    st.markdown('''
    <div style="text-align: center; margin-bottom: 3rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
        <h1 style="font-size: 2rem; color: var(--text-primary);">
            투자 성향 분석
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            AI가 당신에게 맞는 투자 방식을 찾아드립니다
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 세션 상태 플래그로 플로우 관리 (표준화된 키 사용)
    if not st.session_state.get(SessionKeys.SURVEY_DONE, False):
        show_investment_survey()
    else:
        show_enhanced_principle_result()

def show_investment_survey():
    """투자 성향 설문조사"""
    st.markdown("### 📋 투자 성향 진단 설문")
    
    with st.form("enhanced_investment_survey"):
        st.markdown("#### 몇 가지 질문에 답해주시면 AI가 분석해드립니다:")
        
        # 진행률 표시
        st.markdown('''
        <div style="background: #f0f2f6; border-radius: 10px; height: 8px; margin-bottom: 2rem;">
            <div style="background: linear-gradient(90deg, #3182F6 0%, #667eea 100%); height: 100%; border-radius: 10px; width: 33.33%;"></div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 설문 질문들
        q1 = st.radio(
            "**Q1. 투자할 때 가장 중요하게 생각하는 것은?**",
            ["📊 안정적이고 꾸준한 수익률", "🚀 높은 성장 가능성과 기회"],
            key="enhanced_q1",
            help="투자 성향을 파악하는 첫 번째 질문입니다"
        )
        
        st.markdown("---")
        
        q2 = st.radio(
            "**Q2. 어떤 기업에 더 끌리시나요?**",
            ["🏢 오랜 역사와 안정성을 자랑하는 우량 기업", "💡 혁신적이고 미래를 바꿀 새로운 기업"],
            key="enhanced_q2",
            help="선호하는 기업 유형을 확인합니다"
        )
        
        st.markdown("---")
        
        q3 = st.radio(
            "**Q3. 투자에서 위험에 대한 당신의 철학은?**",
            ["🛡️ 손실을 최소화하는 것이 최우선", "⚡ 큰 수익을 위해서는 위험도 감수"],
            key="enhanced_q3",
            help="위험 감수 성향을 파악합니다"
        )
        
        # 완료 진행률
        st.markdown('''
        <div style="background: #f0f2f6; border-radius: 10px; height: 8px; margin: 2rem 0;">
            <div style="background: linear-gradient(90deg, #3182F6 0%, #667eea 100%); height: 100%; border-radius: 10px; width: 100%;"></div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 제출 버튼
        submitted = st.form_submit_button(
            "🎯 AI 분석 시작하기", 
            type="primary", 
            use_container_width=True,
            help="설문 결과를 바탕으로 AI가 투자 철학을 추천합니다"
        )
        
        if submitted:
            # AI 분석 시뮬레이션 (sleep 제거, 즉시 처리)
            with st.spinner("🤖 AI가 당신의 투자 성향을 분석하고 있습니다..."):
                # 가치 투자 답변 개수 계산
                value_investment_count = 0
                if "안정적이고 꾸준한" in q1:
                    value_investment_count += 1
                if "오랜 역사와 안정성" in q2:
                    value_investment_count += 1
                if "손실을 최소화" in q3:
                    value_investment_count += 1
                
                # 결과에 따른 원칙 추천
                if value_investment_count >= 2:
                    st.session_state[SessionKeys.RECOMMENDED_PRINCIPLE] = "벤저민 그레이엄"
                else:
                    st.session_state[SessionKeys.RECOMMENDED_PRINCIPLE] = "피터 린치"
                
                st.session_state[SessionKeys.SURVEY_DONE] = True
                st.rerun()

def show_enhanced_principle_result():
    """향상된 원칙 추천 결과 (안전한 텍스트 처리)"""
    recommended = st.session_state.get(SessionKeys.RECOMMENDED_PRINCIPLE)
    
    if not recommended:
        st.error("❌ 추천 결과를 불러올 수 없습니다.")
        return
    
    # 안전한 텍스트 처리
    safe_recommended = sanitize_html_text(recommended)
    
    # AI 분석 완료 표시
    st.markdown(f'''
    <div style="
        background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%);
        border: 2px solid #3182F6;
        border-radius: 24px;
        padding: 3rem;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(49, 130, 246, 0.1);
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem; animation: bounce 2s infinite;">🎉</div>
        <h2 style="color: #3182F6; margin-bottom: 1rem; font-size: 2rem;">
            AI 분석 완료!
        </h2>
        <div style="
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin: 2rem 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-size: 1.4rem;">
                당신에게 가장 적합한 투자 철학은
            </h3>
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-size: 1.8rem;
                font-weight: 700;
                margin: 1rem 0;
            ">
                {safe_recommended}
            </div>
            <p style="color: var(--text-secondary); font-size: 1rem;">
                투자 스타일입니다!
            </p>
        </div>
    </div>
    
    <style>
    @keyframes bounce {{
        0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
        40% {{ transform: translateY(-10px); }}
        60% {{ transform: translateY(-5px); }}
    }}
    </style>
    ''', unsafe_allow_html=True)
    
    # 추천된 원칙의 상세 정보
    try:
        principle_data = get_principle_details(recommended)
        if principle_data:
            show_principle_details_card(recommended, principle_data)
    except Exception as e:
        st.warning(f"⚠️ 원칙 상세 정보 로드 실패: {sanitize_html_text(str(e))}")
    
    # 다른 선택지도 보여주기
    show_alternative_principles(recommended)
    
    # 최종 확인 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            f"✨ {safe_recommended} 철학으로 시작하기", 
            key="confirm_enhanced_principle",
            type="primary",
            use_container_width=True,
            help=f"{safe_recommended} 투자 철학을 선택하고 메인으로 이동합니다"
        ):
            # 거울 코칭 초기화 (캐시된 인스턴스 사용)
            mirror_coach = get_mirror_coach()
            try:
                current_user = st.session_state.get(SessionKeys.USER, {})
                username = current_user.get('username', '이거울')
                st.session_state[SessionKeys.MIRROR_INSIGHTS] = mirror_coach.initialize_for_user(username)
            except Exception as e:
                st.warning(f"⚠️ 거울 코칭 초기화 실패: {sanitize_html_text(str(e))}")
            
            st.session_state[SessionKeys.SELECTED_PRINCIPLE] = recommended
            st.session_state[SessionKeys.ONBOARDING_STAGE] = None
            
            st.success(f"🎉 {safe_recommended} 투자 철학을 선택하셨습니다!")
            st.rerun()

def show_principle_details_card(principle_name, principle_data):
    """원칙 상세 정보 카드 (안전한 텍스트 처리)"""
    safe_name = sanitize_html_text(principle_name)
    safe_description = sanitize_html_text(principle_data.get('description', ''))
    safe_philosophy = sanitize_html_text(principle_data.get('philosophy', ''))
    safe_icon = sanitize_html_text(principle_data.get('icon', '📊'))
    
    st.markdown(f'''
    <div style="
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
            <div style="font-size: 3rem; margin-right: 1rem;">{safe_icon}</div>
            <div>
                <h3 style="margin: 0; color: var(--text-primary); font-size: 1.5rem;">{safe_name}</h3>
                <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 1rem;">
                    {safe_description}
                </p>
            </div>
        </div>
        
        <div style="
            background: #F8FAFC;
            border-left: 4px solid var(--primary-blue);
            padding: 1rem 1.5rem;
            border-radius: 0 8px 8px 0;
            margin-bottom: 1.5rem;
        ">
            <p style="margin: 0; font-style: italic; color: var(--text-primary); font-size: 1.1rem;">
                "{safe_philosophy}"
            </p>
        </div>
        
        <div>
            <h4 style="color: var(--text-primary); margin-bottom: 1rem;">🎯 핵심 원칙</h4>
            <div style="display: grid; gap: 0.75rem;">
    ''', unsafe_allow_html=True)
    
    core_principles = principle_data.get("core_principles", [])
    for principle in core_principles[:3]:
        safe_principle = sanitize_html_text(principle)
        st.markdown(f'''
        <div style="
            background: #F0F9FF;
            border: 1px solid #BFDBFE;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            color: var(--text-primary);
        ">
            • {safe_principle}
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)

def show_alternative_principles(recommended):
    """다른 투자 방식 선택지 (안전한 텍스트 처리)"""
    st.markdown("---")
    st.markdown("### 🤔 다른 투자 방식도 궁금하신가요?")
    
    try:
        principles = get_investment_principles()
        other_principles = [name for name in principles.keys() if name != recommended]
        
        col1, col2 = st.columns(2)
        
        for i, other_name in enumerate(other_principles):
            with [col1, col2][i % 2]:
                other_data = principles[other_name]
                safe_name = sanitize_html_text(other_name)
                safe_desc = sanitize_html_text(other_data.get('description', ''))[:80]
                safe_icon = sanitize_html_text(other_data.get('icon', '📊'))
                
                st.markdown(f'''
                <div style="
                    background: white;
                    border: 1px solid var(--border-color);
                    border-radius: 16px;
                    padding: 1.5rem;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    height: 200px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                " class="alternative-card">
                    <div>
                        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{safe_icon}</div>
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem; font-size: 1.1rem;">{safe_name}</h4>
                        <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.4;">
                            {safe_desc}...
                        </p>
                    </div>
                </div>
                
                <style>
                .alternative-card:hover {{
                    transform: translateY(-4px);
                    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                    border-color: var(--primary-blue);
                }}
                </style>
                ''', unsafe_allow_html=True)
                
                if st.button(
                    f"✨ {safe_name} 선택", 
                    key=f"alt_enhanced_{safe_name}_{i}", 
                    use_container_width=True,
                    help=f"{safe_name} 투자 철학으로 변경합니다"
                ):
                    st.session_state[SessionKeys.RECOMMENDED_PRINCIPLE] = other_name
                    st.rerun()
    except Exception as e:
        st.warning(f"⚠️ 대안 원칙 로드 실패: {sanitize_html_text(str(e))}")

def show_enhanced_trade_selection_onboarding():
    """향상된 거래 선택 온보딩 (안전한 텍스트 처리)"""
    user = st.session_state.get(SessionKeys.USER, {})
    username = user.get('username', '알수없음')
    safe_username = sanitize_html_text(username)
    
    st.markdown(f'''
    <div style="text-align: center; margin-bottom: 3rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
        <h1 style="font-size: 2rem; color: var(--text-primary);">
            복기할 거래 선택
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            {safe_username}님의 과거 거래를 AI가 분석하여 추천해드립니다
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 중앙 데이터 매니저에서 거래 데이터 로드
    try:
        trades_data = get_user_trading_history(username)
        
        if trades_data:
            import pandas as pd
            trades_df = pd.DataFrame(trades_data)
            trades_df['거래일시'] = pd.to_datetime(trades_df['거래일시'])
            show_recommended_trades_cards(trades_df, username)
        else:
            st.info("📊 분석할 거래 데이터가 없습니다.")
            st.markdown("💡 **안내**: 실제 서비스에서는 연결된 증권계좌의 거래 내역을 분석합니다.")
            
    except Exception as e:
        st.error(f"❌ 거래 데이터 로드 실패: {sanitize_html_text(str(e))}")
        st.info("💡 **해결방법**: 페이지를 새로고침하거나 다른 사용자로 로그인해보세요.")

def show_recommended_trades_cards(trades_data, username):
    """추천 거래 카드들 표시 (안전한 텍스트 처리)"""
    st.markdown("### 🎯 AI 추천 복기 거래")
    st.info("💡 AI가 분석한 결과, 다음 거래들의 복기가 가장 도움이 될 것 같습니다.")
    
    try:
        # 수익률 상위/하위 거래 분리
        top_trades = trades_data.nlargest(2, '수익률')
        bottom_trades = trades_data.nsmallest(2, '수익률')
        
        # 성공 거래 섹션
        if not top_trades.empty:
            st.markdown("#### 🏆 성공 거래 (학습할 점)")
            col1, col2 = st.columns(2)
            
            for i, (_, trade) in enumerate(top_trades.iterrows()):
                with [col1, col2][i % 2]:
                    show_enhanced_trade_card(trade, "success", i, username)
        
        # 실패 거래 섹션  
        if not bottom_trades.empty:
            st.markdown("#### 📉 개선 거래 (배울 점)")
            col3, col4 = st.columns(2)
            
            for i, (_, trade) in enumerate(bottom_trades.iterrows()):
                with [col3, col4][i % 2]:
                    show_enhanced_trade_card(trade, "improvement", i+2, username)
        
    except Exception as e:
        st.warning(f"⚠️ 거래 카드 렌더링 실패: {sanitize_html_text(str(e))}")
        st.info("💡 **해결방법**: 데이터를 다시 로드하려면 페이지를 새로고침하세요.")
    
    # 건너뛰기 옵션
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "⏭️ 나중에 복기하기", 
            key="skip_enhanced_onboarding", 
            use_container_width=True,
            help="복기를 건너뛰고 메인 화면으로 이동합니다"
        ):
            st.session_state[SessionKeys.ONBOARDING_STAGE] = None
            st.rerun()

def show_enhanced_trade_card(trade, card_type, index, username):
    """향상된 거래 카드 (안전한 텍스트 처리)"""
    try:
        # 안전한 텍스트 처리
        safe_stock_name = sanitize_html_text(str(trade.get('종목명', '알수없음')))
        safe_memo = sanitize_html_text(str(trade.get('메모', '')))[:60]
        emotion_tag = str(trade.get('감정태그', '#기본'))
        safe_emotion_tag = sanitize_html_text(emotion_tag)
        emotion_color = get_emotion_color(emotion_tag)
        
        profit_rate = trade.get('수익률', 0)
        profit_color = "#14AE5C" if profit_rate > 0 else "#DC2626"
        card_bg = "#F0FDF4" if card_type == "success" else "#FEF2F2"
        border_color = "#86EFAC" if card_type == "success" else "#FECACA"
        icon = "🎯" if card_type == "success" else "📚"
        
        # 날짜 처리 (KST)
        trade_date = trade.get('거래일시', datetime.now())
        if isinstance(trade_date, str):
            try:
                trade_date = datetime.fromisoformat(trade_date)
            except:
                trade_date = datetime.now()
        formatted_date = format_kst_datetime(trade_date)
        
        # 거래구분과 수량 안전 처리
        safe_trade_type = sanitize_html_text(str(trade.get('거래구분', '매수')))
        safe_quantity = str(trade.get('수량', 0))
        
        st.markdown(f'''
        <div style="
            background: {card_bg};
            border: 2px solid {border_color};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        " class="trade-card-{index}">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
                <h4 style="margin: 0; color: var(--text-primary); flex: 1;">{safe_stock_name}</h4>
                <div style="text-align: right;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: {profit_color};">
                        {profit_rate:+.1f}%
                    </div>
                </div>
            </div>
            
            <div style="margin-bottom: 1rem;">
                <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">
                    📅 {formatted_date.split()[0]} • {safe_trade_type} • {safe_quantity}주
                </div>
                <div style="
                    background: rgba(255,255,255,0.7);
                    padding: 0.75rem;
                    border-radius: 8px;
                    font-size: 0.85rem;
                    color: var(--text-secondary);
                ">
                    💭 {safe_memo}{"..." if len(safe_memo) == 60 else ""}
                </div>
            </div>
            
            <div style="
                background: {emotion_color};
                color: var(--text-primary);
                padding: 0.5rem;
                border-radius: 8px;
                text-align: center;
                font-size: 0.8rem;
                font-weight: 600;
                margin-bottom: 1rem;
            ">
                감정: {safe_emotion_tag}
            </div>
        </div>
        
        <style>
        .trade-card-{index}:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }}
        </style>
        ''', unsafe_allow_html=True)
        
        button_text = "🔍 성공 요인 분석" if card_type == "success" else "💡 개선점 찾기"
        if st.button(
            button_text, 
            key=f"select_enhanced_{card_type}_{index}", 
            use_container_width=True,
            type="primary",
            help=f"이 거래에 대한 {'성공 요인을' if card_type == 'success' else '개선점을'} 분석합니다"
        ):
            st.session_state[SessionKeys.SELECTED_TRADE] = trade.to_dict()
            st.session_state[SessionKeys.ONBOARDING_STAGE] = None
            
            # 거울 코칭 인사이트 생성 (캐시된 인스턴스 사용)
            try:
                mirror_coach = get_mirror_coach()
                insights = mirror_coach.generate_insights_for_trade(trade, username)
                st.session_state[SessionKeys.MIRROR_INSIGHTS] = insights
            except Exception as e:
                st.warning(f"⚠️ 거울 코칭 인사이트 생성 실패: {sanitize_html_text(str(e))}")
            
            st.success("✅ 거래 선택 완료! AI 분석을 시작합니다.")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 거래 카드 렌더링 실패: {sanitize_html_text(str(e))}")

# ================================
# [MAIN NAVIGATION]
# ================================

def show_enhanced_main_navigation():
    """향상된 메인 네비게이션 (안전한 텍스트 처리)"""
    user = st.session_state.get(SessionKeys.USER, {})
    safe_username = sanitize_html_text(user.get('username', '사용자'))
    safe_icon = sanitize_html_text(user.get('icon', '👤'))
    user_color = user.get('color', '#3182F6')
    
    # 환영 섹션
    st.markdown(f'''
    <div style="
        background: linear-gradient(135deg, {user_color}10 0%, {user_color}20 100%);
        border: 2px solid {user_color}40;
        border-radius: 24px;
        padding: 3rem;
        text-align: center;
        margin: 2rem 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">{safe_icon}</div>
        <h1 style="font-size: 2.5rem; color: var(--text-primary); margin-bottom: 0.5rem;">
            환영합니다, {safe_username}님! 👋
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.2rem; margin-bottom: 2rem;">
            KB Reflex와 함께 더 나은 투자 습관을 만들어보세요
        </p>
        
        <!-- 사용자별 맞춤 메시지 -->
        <div style="
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            margin-top: 2rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        ">
            {get_personalized_welcome_message(user)}
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 향상된 기능 카드들
    st.markdown("### 🚀 주요 기능")
    
    col1, col2, col3 = st.columns(3)
    
    # 대시보드 카드
    with col1:
        st.markdown('''
        <div class="feature-card" style="
            background: linear-gradient(135deg, #EBF4FF 0%, #DBEAFE 100%);
            border: 2px solid #93C5FD;
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s ease;
        ">
            <div>
                <div style="font-size: 3.5rem; margin-bottom: 1rem;">📊</div>
                <h3 style="color: var(--text-primary); margin-bottom: 1rem;">실시간 대시보드</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.4;">
                    • 실시간 포트폴리오 현황<br>
                    • AI 투자 인사이트<br>
                    • 스마트 거래 브리핑
                </p>
            </div>
            <div style="
                background: #3B82F6;
                color: white;
                padding: 0.5rem;
                border-radius: 8px;
                font-size: 0.8rem;
                font-weight: 700;
            ">
                실시간 업데이트
            </div>
        </div>
        
        <style>
        .feature-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(59, 130, 246, 0.15);
        }
        </style>
        ''', unsafe_allow_html=True)
        
        if st.button(
            "📊 대시보드 시작", 
            key="goto_enhanced_dashboard", 
            use_container_width=True, 
            type="primary",
            help="실시간 대시보드로 이동합니다"
        ):
            safe_navigate_to_page("dashboard")
    
    # 거래 복기 카드
    with col2:
        st.markdown('''
        <div class="feature-card" style="
            background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
            border: 2px solid #FACC15;
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s ease;
        ">
            <div>
                <div style="font-size: 3.5rem; margin-bottom: 1rem;">🪞</div>
                <h3 style="color: var(--text-primary); margin-bottom: 1rem;">거울 복기</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.4;">
                    • 상황 재현 복기<br>
                    • AI 패턴 분석<br>
                    • 유사 경험 매칭
                </p>
            </div>
            <div style="
                background: #F59E0B;
                color: white;
                padding: 0.5rem;
                border-radius: 8px;
                font-size: 0.8rem;
                font-weight: 700;
            ">
                핵심 기능
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button(
            "🪞 거울 복기 시작", 
            key="goto_enhanced_review", 
            use_container_width=True, 
            type="primary",
            help="거래 복기 페이지로 이동합니다"
        ):
            safe_navigate_to_page("review")
    
    # AI 코칭 카드
    with col3:
        st.markdown('''
        <div class="feature-card" style="
            background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%);
            border: 2px solid #86EFAC;
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s ease;
        ">
            <div>
                <div style="font-size: 3.5rem; margin-bottom: 1rem;">🤖</div>
                <h3 style="color: var(--text-primary); margin-bottom: 1rem;">AI 심리 코칭</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.4;">
                    • 딥러닝 심리 분석<br>
                    • 개인화된 코칭<br>
                    • 실시간 피드백
                </p>
            </div>
            <div style="
                background: #10B981;
                color: white;
                padding: 0.5rem;
                border-radius: 8px;
                font-size: 0.8rem;
                font-weight: 700;
            ">
                AI 엔진
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button(
            "🤖 AI 코칭 받기", 
            key="goto_enhanced_coaching", 
            use_container_width=True, 
            type="primary",
            help="AI 심리 코칭 페이지로 이동합니다"
        ):
            safe_navigate_to_page("coaching")
    
    # 추가 기능들
    st.markdown("---")
    st.markdown("### 🛠️ 추가 기능")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            "📜 나의 투자 헌장", 
            key="goto_enhanced_charter", 
            use_container_width=True,
            help="개인화된 투자 헌장을 확인합니다"
        ):
            safe_navigate_to_page("charter")
    
    with col2:
        if st.button(
            "⚙️ 설정 및 분석", 
            key="goto_enhanced_settings", 
            use_container_width=True,
            help="설정 페이지를 확인합니다"
        ):
            show_enhanced_settings_modal()

def get_personalized_welcome_message(user):
    """사용자별 맞춤 환영 메시지 (안전한 텍스트 처리)"""
    username = user.get('username', '알수없음')
    safe_username = sanitize_html_text(username)
    
    try:
        user_profile = get_user_profile(username)
        
        if not user_profile:
            return f'<div>환영합니다, {safe_username}님!</div>'
        
        messages = {
            '이거울': f'''
            <div style="text-align: left;">
                <h4 style="color: #3182F6; margin-bottom: 1rem;">🎯 투자 여정을 시작합니다!</h4>
                <ul style="color: var(--text-secondary); line-height: 1.6;">
                    <li>✨ AI가 추천한 투자 철학으로 시작</li>
                    <li>🎓 체계적인 학습과 실전 연습</li>
                    <li>🪞 객관적인 자기 분석 도구 활용</li>
                </ul>
            </div>
            ''',
            '박투자': f'''
            <div style="text-align: left;">
                <h4 style="color: #FF9500; margin-bottom: 1rem;">🔍 FOMO 패턴 개선 중!</h4>
                <ul style="color: var(--text-secondary); line-height: 1.6;">
                    <li>📊 1,500건 거래 데이터 분석 완료</li>
                    <li>⚡ 추격매수 패턴 집중 개선 필요</li>
                    <li>🎯 냉정한 투자 습관 형성 목표</li>
                </ul>
            </div>
            ''',
            '김국민': f'''
            <div style="text-align: left;">
                <h4 style="color: #14AE5C; margin-bottom: 1rem;">🛡️ 감정 관리 마스터링!</h4>
                <ul style="color: var(--text-secondary); line-height: 1.6;">
                    <li>📈 1,500건 거래 복기 데이터 보유</li>
                    <li>🧘‍♂️ 공포 매도 극복 프로그램 진행</li>
                    <li>📜 개인화된 투자 헌장 구축</li>
                </ul>
            </div>
            '''
        }
        
        return messages.get(username, f'<div>환영합니다, {safe_username}님!</div>')
    
    except Exception as e:
        return f'<div>환영합니다, {safe_username}님! <br><small>(메시지 로드 실패: {sanitize_html_text(str(e))})</small></div>'

def show_enhanced_settings_modal():
    """향상된 설정 모달"""
    st.info("🔧 고급 설정 기능은 준비 중입니다. 곧 만나보실 수 있습니다!")
    st.markdown("💡 **개발 예정 기능**: 알림 설정, 테마 변경, 데이터 내보내기 등")

# ================================
# [MAIN APPLICATION]
# ================================

def main():
    """메인 애플리케이션 로직 (상태 머신 기반)"""
    # 레거시 네비게이션 처리 (switch_page 호환성)
    pending_page = st.session_state.get(SessionKeys.PENDING_PAGE)
    if pending_page and hasattr(st, "switch_page"):
        try:
            page_path = PAGE_NAVIGATION.get(pending_page)
            if page_path:
                st.session_state[SessionKeys.PENDING_PAGE] = None
                st.switch_page(page_path)
        except Exception as e:
            st.error(f"❌ 페이지 이동 중 오류: {sanitize_html_text(str(e))}")
            st.session_state[SessionKeys.PENDING_PAGE] = None
    
    # 인증 매니저 초기화
    try:
        auth_manager = EnhancedAuthManager()
    except Exception as e:
        st.error(f"❌ 시스템 초기화 실패: {sanitize_html_text(str(e))}")
        st.info("💡 **해결방법**: 페이지를 새로고침하거나 브라우저 캐시를 삭제해보세요.")
        st.stop()
    
    # 향상된 사이드바 표시
    if auth_manager.is_logged_in():
        try:
            auth_manager.show_enhanced_sidebar()
        except Exception as e:
            st.sidebar.error(f"❌ 사이드바 로드 실패: {sanitize_html_text(str(e))}")
    
    # 로그인 상태에 따른 화면 분기
    if not auth_manager.is_logged_in():
        try:
            auth_manager.show_elegant_user_selector()
        except Exception as e:
            st.error(f"❌ 사용자 선택 화면 로드 실패: {sanitize_html_text(str(e))}")
            st.info("💡 **해결방법**: 데이터 파일이 손상되었을 수 있습니다. 관리자에게 문의하세요.")
    else:
        # 온보딩 상태 머신 (표준화된 키 사용)
        onboarding_stage = st.session_state.get(SessionKeys.ONBOARDING_STAGE)
        
        try:
            if onboarding_stage == "principles":
                show_enhanced_principles_onboarding()
            elif onboarding_stage == "trade_selection":
                show_enhanced_trade_selection_onboarding()
            else:
                show_enhanced_main_navigation()
        except Exception as e:
            st.error(f"❌ 화면 렌더링 실패: {sanitize_html_text(str(e))}")
            st.info("💡 **임시 해결방법**: 사용자를 전환하거나 페이지를 새로고침해보세요.")
            
            # 응급 사용자 전환 버튼
            if st.button("🔄 긴급 사용자 전환", type="secondary"):
                auth_manager.logout()

if __name__ == "__main__":
    main()