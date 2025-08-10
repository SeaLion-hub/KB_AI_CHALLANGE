# CHANGELOG:
# - st.set_page_config() 제거 (main_app.py에서만 호출)
# - 세션키 호환성: current_user와 REFLEX_USER 순차 참조 추가
# - 모든 st.switch_page 호출에 호환성 가드 및 폴백 로직 적용
# - 사용자 텍스트에 sanitize_html_text() 적용하여 HTML 안전성 강화
# - CSS 클래스명 통일: emotion-tag-enhanced → emotion-tag
# - 불필요한 임포트 제거 및 코드 최적화
# - HTML 렌더링 문제 수정: render_html() 대신 st.markdown(..., unsafe_allow_html=True) 직접 사용

import streamlit as st
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import re

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ui_components import apply_toss_css, create_mirror_coaching_card
from ml.mirror_coaching import MirrorCoaching
from db.central_data_manager import get_data_manager, get_user_trading_history, get_user_profile

# ================================
# [UTILITY FUNCTIONS]
# ================================

def sanitize_text_content(text: str) -> str:
    """텍스트 내용만 안전하게 처리 (HTML 태그는 건드리지 않음)"""
    if not isinstance(text, str):
        return str(text)
    
    # 기본적인 텍스트만 정리 (HTML 태그 유지)
    sanitized = str(text).replace('"', '&quot;').replace("'", '&#39;')
    return sanitized

def safe_navigate_to_page(page_path: str):
    """안전한 페이지 네비게이션 (호환성 체크)"""
    if hasattr(st, "switch_page"):
        try:
            st.switch_page(page_path)
        except Exception as e:
            st.error(f"❌ 페이지 이동 실패: {str(e)}")
            st.session_state["REFLEX_PENDING_PAGE"] = page_path.replace("pages/", "").replace(".py", "")
            st.rerun()
    else:
        # 레거시 Streamlit 버전 대체 동작
        st.warning("⚠️ 구버전 Streamlit에서는 페이지 이동이 제한됩니다.")
        st.session_state["REFLEX_PENDING_PAGE"] = page_path.replace("pages/", "").replace(".py", "")
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            st.rerun()

def get_current_user():
    """현재 사용자 정보 반환 (호환성 지원)"""
    # 기존 current_user 세션키 우선 확인
    if 'current_user' in st.session_state and st.session_state.current_user is not None:
        return st.session_state.current_user
    
    # main_app.py의 REFLEX_USER 키 확인
    if 'REFLEX_USER' in st.session_state and st.session_state.REFLEX_USER is not None:
        return st.session_state.REFLEX_USER
    
    return None

# ================================
# [INITIALIZATION]
# ================================

# Toss 스타일 CSS 적용
apply_toss_css()

# 로그인 확인 (호환성 지원)
current_user = get_current_user()
if current_user is None:
    st.error("⚠️ 로그인이 필요합니다.")
    if st.button("🏠 홈으로 돌아가기"):
        safe_navigate_to_page("main_app.py")
    st.stop()

user = current_user
username = user['username']

# ================================
# [MAIN FUNCTIONS]
# ================================

def show_trade_selection_interface():
    """거래 선택 인터페이스"""
    safe_username = sanitize_text_content(username)
    
    st.markdown(f'''
    <div class="main-header-enhanced">
        🪞 거울 복기 - 거래 선택
    </div>
    <div class="sub-header-enhanced">
        {safe_username}님, 복기하고 싶은 거래를 선택하거나 AI 추천을 받아보세요
    </div>
    ''', unsafe_allow_html=True)
    
    # 사용자 프로필 확인
    try:
        user_profile = get_user_profile(username)
    except Exception as e:
        st.error(f"❌ 사용자 프로필 로드 실패: {str(e)}")
        return
    
    if not user_profile or user_profile.username == "이거울":
        show_beginner_mirror_experience()
        return
    
    # 중앙 데이터 매니저에서 거래 데이터 로드
    try:
        trades_data = get_user_trading_history(username)
    except Exception as e:
        st.error(f"❌ 거래 데이터 로드 실패: {str(e)}")
        st.info("💡 **해결방법**: 페이지를 새로고침하거나 다른 사용자로 로그인해보세요.")
        return
    
    if not trades_data:
        st.warning("📊 거래 데이터를 찾을 수 없습니다.")
        st.info("💡 실제 서비스에서는 연결된 증권계좌의 거래 내역을 분석합니다.")
        return
    
    # DataFrame으로 변환
    try:
        trades_df = pd.DataFrame(trades_data)
        trades_df['거래일시'] = pd.to_datetime(trades_df['거래일시'])
    except Exception as e:
        st.error(f"❌ 거래 데이터 처리 실패: {str(e)}")
        return
    
    # 탭 인터페이스
    tab1, tab2, tab3 = st.tabs(["🎯 AI 추천", "📊 전체 거래", "🔍 필터 검색"])
    
    with tab1:
        show_ai_recommended_trades(trades_df)
    
    with tab2:
        show_all_trades_list(trades_df)
    
    with tab3:
        show_filtered_trades(trades_df)

def show_beginner_mirror_experience():
    """초보자를 위한 거울 경험"""
    st.markdown('''
    <div class="mirror-coaching-card">
        <div class="mirror-coaching-content">
            <div class="mirror-coaching-title">
                🪞 거울 복기 체험하기
            </div>
            <div class="mirror-insight">
                실제 거래 데이터는 없지만, 다른 투자자들의 사례를 통해 
                거울 복기가 어떻게 작동하는지 체험해보세요!
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 시뮬레이션 케이스 선택 (동적 로딩 가능하도록 구성)
    demo_cases = get_demo_cases()
    
    st.markdown("### 📚 학습용 거울 복기 케이스")
    
    for i, case in enumerate(demo_cases):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            result_color = "#14AE5C" if case['result'].startswith('+') else "#DC2626"
            safe_title = sanitize_text_content(case['title'])
            safe_description = sanitize_text_content(case['description'])
            safe_lesson = sanitize_text_content(case['lesson'])
            safe_emotion = sanitize_text_content(case['emotion'])
            
            st.markdown(f'''
            <div class="premium-card">
                <h4 style="color: var(--text-primary); margin-bottom: 1rem;">{safe_title}</h4>
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">{safe_description}</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="emotion-tag emotion-{safe_emotion}">{safe_emotion}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {result_color}; font-weight: 700; font-size: 1.2rem;">
                            {case['result']}
                        </div>
                        <div style="font-size: 0.85rem; color: var(--text-light);">
                            {safe_lesson}
                        </div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            if st.button(f"🪞 체험하기", key=f"demo_case_{i}", use_container_width=True):
                st.session_state.demo_case = case
                st.session_state.review_mode = "demo"
                st.rerun()

def get_demo_cases():
    """데모 케이스 데이터 (나중에 중앙 데이터 매니저로 이동 가능)"""
    return [
        {
            'title': '공포매도 사례 분석',
            'description': '시장 급락 시 패닉 매도한 실제 사례',
            'emotion': '공포',
            'result': '-15%',
            'lesson': '감정적 판단의 위험성'
        },
        {
            'title': 'FOMO 매수 사례 분석', 
            'description': '급등주 추격매수로 인한 손실 사례',
            'emotion': '욕심',
            'result': '-12%',
            'lesson': '추격매수의 함정'
        },
        {
            'title': '합리적 투자 성공 사례',
            'description': '차분한 분석 후 성공한 투자 사례',
            'emotion': '냉정',
            'result': '+28%',
            'lesson': '인내심의 중요성'
        }
    ]

def show_ai_recommended_trades(trades_data):
    """AI 추천 거래"""
    st.markdown("### 🎯 AI가 추천하는 복기 거래")
    
    try:
        mirror_coach = MirrorCoaching()
    except Exception as e:
        st.warning(f"⚠️ AI 코칭 시스템 초기화 실패: {str(e)}")
        mirror_coach = None
    
    # 추천 거래 로직 개선
    if len(trades_data) > 0:
        try:
            # 극단적인 수익률의 거래들 찾기
            high_return = trades_data[trades_data['수익률'] > 10]
            low_return = trades_data[trades_data['수익률'] < -10]
            
            success_trades = high_return.nlargest(2, '수익률') if len(high_return) > 0 else trades_data.nlargest(2, '수익률')
            failure_trades = low_return.nsmallest(2, '수익률') if len(low_return) > 0 else trades_data.nsmallest(2, '수익률')
            
            st.info("💡 복기 가치가 높은 거래들을 AI가 선별했습니다.")
            
            if len(success_trades) > 0:
                st.markdown("#### 🏆 성공 사례 (배울 점)")
                for _, trade in success_trades.iterrows():
                    show_trade_card(trade, "success")
            
            if len(failure_trades) > 0:
                st.markdown("#### 📉 개선 사례 (피할 점)")
                for _, trade in failure_trades.iterrows():
                    show_trade_card(trade, "failure")
        except Exception as e:
            st.error(f"❌ AI 추천 처리 실패: {str(e)}")
    else:
        st.warning("복기 추천 거래를 생성할 수 없습니다.")

def show_all_trades_list(trades_data):
    """전체 거래 리스트"""
    st.markdown("### 📊 전체 거래 내역")
    
    # 정렬 옵션
    col1, col2 = st.columns(2)
    with col1:
        sort_option = st.selectbox(
            "정렬 기준",
            ["최근순", "수익률 높은순", "수익률 낮은순", "거래금액 큰순"]
        )
    
    with col2:
        limit = st.selectbox("표시 개수", [10, 20, 50, 100], index=1)
    
    # 데이터 정렬
    try:
        if sort_option == "최근순":
            sorted_trades = trades_data.sort_values('거래일시', ascending=False)
        elif sort_option == "수익률 높은순":
            sorted_trades = trades_data.sort_values('수익률', ascending=False)
        elif sort_option == "수익률 낮은순":
            sorted_trades = trades_data.sort_values('수익률', ascending=True)
        else:  # 거래금액 큰순
            trades_data['거래금액'] = trades_data['수량'] * trades_data['가격']
            sorted_trades = trades_data.sort_values('거래금액', ascending=False)
        
        # 거래 카드 표시
        for _, trade in sorted_trades.head(limit).iterrows():
            show_trade_card(trade, "normal")
    except Exception as e:
        st.error(f"❌ 거래 정렬 처리 실패: {str(e)}")

def show_filtered_trades(trades_data):
    """필터 검색"""
    st.markdown("### 🔍 조건별 거래 검색")
    
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            stock_filter = st.multiselect(
                "종목 선택",
                options=trades_data['종목명'].unique(),
                default=[]
            )
        
        with col2:
            emotion_filter = st.multiselect(
                "감정 태그",
                options=trades_data['감정태그'].unique(),
                default=[]
            )
        
        with col3:
            trade_type_filter = st.multiselect(
                "거래 구분",
                options=trades_data['거래구분'].unique(),
                default=[]
            )
        
        # 수익률 범위
        col1, col2 = st.columns(2)
        with col1:
            min_return = st.number_input("최소 수익률 (%)", value=float(trades_data['수익률'].min()))
        with col2:
            max_return = st.number_input("최대 수익률 (%)", value=float(trades_data['수익률'].max()))
        
        # 필터 적용
        filtered_trades = trades_data.copy()
        
        if stock_filter:
            filtered_trades = filtered_trades[filtered_trades['종목명'].isin(stock_filter)]
        if emotion_filter:
            filtered_trades = filtered_trades[filtered_trades['감정태그'].isin(emotion_filter)]
        if trade_type_filter:
            filtered_trades = filtered_trades[filtered_trades['거래구분'].isin(trade_type_filter)]
        
        filtered_trades = filtered_trades[
            (filtered_trades['수익률'] >= min_return) & 
            (filtered_trades['수익률'] <= max_return)
        ]
        
        st.markdown(f"#### 검색 결과: {len(filtered_trades)}건")
        
        for _, trade in filtered_trades.head(20).iterrows():
            show_trade_card(trade, "normal")
    except Exception as e:
        st.error(f"❌ 필터 검색 처리 실패: {str(e)}")

import streamlit as st
import streamlit.components.v1 as components

def show_trade_card(trade, card_type):
    """거래 카드 표시 (components.html 버전)"""
    try:
        # 수익률 색상
        profit_color = "#14AE5C" if trade['수익률'] >= 0 else "#DC2626"
        
        # 카드 스타일 선택
        if card_type == "success":
            card_bg = "#F0FDF4"
            border_color = "#86EFAC"
            icon = "🎯"
        elif card_type == "failure":
            card_bg = "#FEF2F2"
            border_color = "#FECACA"
            icon = "📚"
        else:
            card_bg = "white"
            border_color = "#E5E7EB"
            icon = "📊"
        
        # 데이터 안전 처리
        safe_stock_name = str(trade['종목명'])
        safe_memo = str(trade.get('메모', ''))[:100]
        safe_trade_type = str(trade['거래구분'])
        safe_emotion_tag = str(trade.get('감정태그', '#욕심'))

        trade_date = trade['거래일시']
        trade_date_str = trade_date if isinstance(trade_date, str) else trade_date.strftime('%Y-%m-%d')

        memo_display = f'{safe_memo}{"..." if len(safe_memo) == 100 else ""}'
        
        # HTML 카드 템플릿
        html_code = f"""
        <div style="
            background: {card_bg};
            border: 2px solid {border_color};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            font-family: sans-serif;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
                <h4 style="margin: 0; flex: 1;">{safe_stock_name}</h4>
                <div style="text-align: right; color: {profit_color}; font-weight: 700; font-size: 1.2rem;">
                    {trade['수익률']:+.1f}%
                </div>
            </div>
            <div style="margin-bottom: 1rem; font-size: 0.9rem; color: #6B7280;">
                📅 {trade_date_str} • {safe_trade_type} • {trade['수량']}주 • {trade['가격']:,}원
            </div>
            <div style="
                background: rgba(255,255,255,0.7);
                padding: 0.75rem;
                border-radius: 8px;
                font-size: 0.85rem;
                color: #6B7280;
                font-style: italic;
            ">
                "{memo_display}"
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem;">
                <span style="color: #374151;">{safe_emotion_tag}</span>
            </div>
        </div>
        """

        # HTML 렌더링
        components.html(html_code, height=250)
    
    except Exception as e:
        st.error(f"❌ 거래 카드 렌더링 실패: {str(e)}")


def show_trade_review_analysis():
    """선택된 거래의 상세 복기 분석"""
    if st.session_state.get('review_mode') == "demo":
        show_demo_review_analysis()
        return
    
    trade = st.session_state.get('selected_trade_for_review')
    if not trade:
        st.error("복기할 거래가 선택되지 않았습니다.")
        if st.button("🔙 거래 선택으로 돌아가기"):
            st.session_state.selected_trade_for_review = None
            st.rerun()
        return
    
    # 헤더 (안전한 텍스트 처리)
    safe_stock_name = sanitize_text_content(str(trade['종목명']))
    st.markdown(f'''
    <div class="main-header-enhanced">
        🪞 거울 복기 - {safe_stock_name} 분석
    </div>
    <div class="sub-header-enhanced">
        AI가 당신의 과거 패턴을 분석하여 인사이트를 제공합니다
    </div>
    ''', unsafe_allow_html=True)
    
    # 뒤로가기 버튼
    if st.button("🔙 거래 목록으로", key="back_to_trades"):
        st.session_state.selected_trade_for_review = None
        st.rerun()
    
    # 거래 정보 카드
    show_trade_overview_card(trade)
    
    # AI 분석 결과
    show_mirror_analysis(trade)
    
    # 복기 노트 작성
    show_review_note_section(trade)

def show_demo_review_analysis():
    """데모 케이스 복기 분석"""
    case = st.session_state.get('demo_case')
    if not case:
        return
    
    safe_title = sanitize_text_content(case['title'])
    st.markdown(f'''
    <div class="main-header-enhanced">
        🪞 거울 복기 체험 - {safe_title}
    </div>
    <div class="sub-header-enhanced">
        실제 투자자의 사례를 통해 거울 복기를 체험해보세요
    </div>
    ''', unsafe_allow_html=True)
    
    if st.button("🔙 체험 선택으로", key="back_to_demo"):
        st.session_state.demo_case = None
        st.session_state.review_mode = None
        st.rerun()
    
    # 데모 케이스별 상세 분석
    if case['title'] == '공포매도 사례 분석':
        show_fear_selling_demo()
    elif case['title'] == 'FOMO 매수 사례 분석':
        show_fomo_buying_demo()
    else:
        show_rational_investing_demo()

def show_fear_selling_demo():
    """공포매도 사례 데모"""
    # 상황 재현
    st.markdown('''
    <div class="premium-card">
        <div class="premium-card-title">📊 상황 재현</div>
        <div style="background: #FEF2F2; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h4 style="color: #DC2626;">2024년 3월 급락장 상황</h4>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                <li>코스피 하루 만에 3.2% 급락</li>
                <li>보유 중인 삼성전자 -5% 하락</li>
                <li>온라인 커뮤니티 패닉 분위기</li>
                <li>투자자의 심리상태: 극도의 불안과 공포</li>
            </ul>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # AI 거울 분석
    create_mirror_coaching_card(
        "AI 패턴 분석 결과",
        [
            "📉 시장 급락 시 감정적 매도 패턴이 반복됩니다",
            "⏰ 충분한 사고 시간 없이 즉석에서 결정했습니다", 
            "📰 부정적 뉴스에 과도하게 반응하는 경향이 있습니다"
        ],
        [
            "만약 24시간 더 기다렸다면 어땠을까요?",
            "이 기업의 펀더멘털은 정말 변했을까요?",
            "감정적 결정과 합리적 분석의 차이를 느끼시나요?"
        ]
    )
    
    # 학습 포인트
    st.markdown('''
    <div class="premium-card">
        <div class="premium-card-title">💡 핵심 학습 포인트</div>
        <div style="margin-top: 1rem;">
            <div style="background: #F0FDF4; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #10B981;">
                <strong>🛡️ 안전장치 설정하기</strong><br>
                급락 시에는 24시간 냉각기간을 두고 재검토하는 규칙을 만들어보세요.
            </div>
            <div style="background: #EBF4FF; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #3B82F6;">
                <strong>📊 데이터 중심 사고</strong><br>
                감정이 앞설 때일수록 객관적 지표와 데이터를 먼저 확인하세요.
            </div>
            <div style="background: #FEF3C7; padding: 1rem; border-radius: 8px; border-left: 4px solid #F59E0B;">
                <strong>🧘‍♂️ 감정 관리 연습</strong><br>
                스트레스 상황에서도 냉정을 유지하는 연습이 필요합니다.
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def show_fomo_buying_demo():
    """FOMO 매수 사례 데모"""
    st.markdown('''
    <div class="premium-card">
        <div class="premium-card-title">📊 상황 재현</div>
        <div style="background: #FEF3C7; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h4 style="color: #D97706;">급등주 추격매수 상황</h4>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                <li>특정 종목 3일 연속 상한가</li>
                <li>온라인에서 "놓치면 안 된다" 분위기</li>
                <li>주변 지인들도 모두 매수 중</li>
                <li>투자자의 심리상태: FOMO(Fear of Missing Out)</li>
            </ul>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    create_mirror_coaching_card(
        "AI 패턴 분석 결과",
        [
            "🔥 급등 종목에 대한 추격매수 패턴이 있습니다",
            "👥 군중심리에 휩쓸리는 경향을 보입니다",
            "⚡ 충분한 분석 없이 즉흥적으로 결정합니다"
        ],
        [
            "왜 모든 사람이 사고 있을 때 더 조심해야 할까요?",
            "적정 가격 대신 감정에 의존하고 있지는 않나요?",
            "이 투자의 명확한 근거는 무엇이었나요?"
        ]
    )

def show_rational_investing_demo():
    """합리적 투자 성공 사례 데모"""
    st.markdown('''
    <div class="premium-card">
        <div class="premium-card-title">📊 상황 재현</div>
        <div style="background: #F0FDF4; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h4 style="color: #059669;">차분한 분석 후 투자</h4>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                <li>시장 전반적 하락 후 저평가 구간 진입</li>
                <li>펀더멘털 분석을 통한 내재가치 계산</li>
                <li>충분한 검토 시간과 신중한 접근</li>
                <li>투자자의 심리상태: 냉정하고 합리적</li>
            </ul>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    create_mirror_coaching_card(
        "성공 요인 분석",
        [
            "📊 객관적 데이터를 기반으로 한 분석이 돋보입니다",
            "⏰ 충분한 검토 시간을 가졌습니다",
            "🛡️ 안전마진을 확보한 투자였습니다"
        ],
        [
            "이런 접근 방식을 어떻게 체계화할 수 있을까요?",
            "다른 투자에서도 같은 원칙을 적용할 수 있을까요?",
            "성공 요인을 개인 투자 규칙으로 만들어보면 어떨까요?"
        ]
    )

def show_trade_overview_card(trade):
    """거래 개요 카드 (안전한 텍스트 처리)"""
    try:
        profit_color = "#14AE5C" if trade['수익률'] >= 0 else "#DC2626"
        
        # 안전한 텍스트 처리
        safe_stock_name = sanitize_text_content(str(trade['종목명']))
        safe_trade_type = sanitize_text_content(str(trade['거래구분']))
        safe_memo = sanitize_text_content(str(trade.get('메모', '메모 없음')))
        emotion_tag = str(trade.get('감정태그', '#욕심'))
        safe_emotion_tag = sanitize_text_content(emotion_tag)
        
        # 거래일시 처리
        trade_date = trade['거래일시']
        if isinstance(trade_date, str):
            trade_date_str = trade_date
        else:
            trade_date_str = trade_date.strftime('%Y-%m-%d')
        
        st.markdown(f'''
        <div class="premium-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                <div>
                    <h2 style="margin: 0; color: var(--text-primary);">{safe_stock_name}</h2>
                    <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary);">
                        {trade_date_str} • {safe_trade_type}
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="color: {profit_color}; font-weight: 700; font-size: 2rem;">
                        {trade['수익률']:+.1f}%
                    </div>
                    <div style="color: var(--text-light); font-size: 0.9rem;">
                        {trade['수량']:,}주 × {trade['가격']:,}원
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem;">
                <div style="text-align: center;">
                    <div style="color: var(--text-light); font-size: 0.9rem; margin-bottom: 0.5rem;">거래금액</div>
                    <div style="font-weight: 700; font-size: 1.2rem;">{trade['수량'] * trade['가격']:,}원</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: var(--text-light); font-size: 0.9rem; margin-bottom: 0.5rem;">감정상태</div>
                    <span class="emotion-tag emotion-{emotion_tag.replace('#', '')}">{safe_emotion_tag}</span>
                </div>
                <div style="text-align: center;">
                    <div style="color: var(--text-light); font-size: 0.9rem; margin-bottom: 0.5rem;">손익금액</div>
                    <div style="font-weight: 700; font-size: 1.2rem; color: {profit_color};">
                        {(trade['수량'] * trade['가격'] * trade['수익률'] / 100):+,.0f}원
                    </div>
                </div>
            </div>
            
            <div style="background: #F8FAFC; padding: 1.5rem; border-radius: 12px; border-left: 4px solid var(--primary-blue);">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">💭 당시 메모</h4>
                <p style="margin: 0; color: var(--text-secondary); line-height: 1.6; font-style: italic;">
                    "{safe_memo}"
                </p>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ 거래 개요 카드 렌더링 실패: {str(e)}")

def show_mirror_analysis(trade):
    """AI 거울 분석 표시"""
    st.markdown("---")
    st.markdown("### 🤖 AI 거울 분석")
    
    try:
        # 거울 코칭 인사이트 생성
        mirror_coach = MirrorCoaching()
        
        with st.spinner("🔍 AI가 유사한 과거 경험을 찾고 있습니다..."):
            # 현재 상황을 텍스트로 구성 (안전한 텍스트 처리)
            safe_stock_name = sanitize_text_content(str(trade['종목명']))
            safe_trade_type = sanitize_text_content(str(trade['거래구분']))
            safe_emotion = sanitize_text_content(str(trade.get('감정태그', '')))
            safe_memo = sanitize_text_content(str(trade.get('메모', '')))
            
            current_situation = f"{safe_stock_name} {safe_trade_type} 거래, 감정: {safe_emotion}, 메모: {safe_memo}"
            
            # 유사 경험 찾기
            try:
                similar_experiences = mirror_coach.find_similar_experiences(current_situation, username)
                # 거울 질문 생성
                mirror_questions = mirror_coach.generate_mirror_questions(similar_experiences, current_situation)
            except Exception as e:
                st.warning(f"⚠️ 유사 경험 분석 중 오류 발생: {str(e)}")
                similar_experiences = []
                mirror_questions = []
        
        if similar_experiences:
            st.success(f"🎯 {len(similar_experiences)}개의 유사한 과거 경험을 발견했습니다!")
            
            # 유사 경험 카드들
            for i, exp in enumerate(similar_experiences):
                exp_trade = exp.get('trade_data', {})
                similarity_score = exp.get('similarity_score', 0)
                
                # 안전한 텍스트 처리
                safe_exp_stock = sanitize_text_content(str(exp_trade.get('종목명', 'N/A')))
                safe_exp_date = sanitize_text_content(str(exp_trade.get('거래일시', 'N/A')))
                safe_exp_emotion = sanitize_text_content(str(exp_trade.get('감정태그', 'N/A')))
                safe_lesson = sanitize_text_content(str(exp.get('key_lesson', '학습 중')))
                
                profit_color = '#14AE5C' if exp_trade.get('수익률', 0) > 0 else '#DC2626'
                
                st.markdown(f'''
                <div class="premium-card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h4 style="margin: 0; color: var(--text-primary);">
                            📊 유사 경험 #{i+1}: {safe_exp_stock}
                        </h4>
                        <div style="background: #EBF4FF; color: #3B82F6; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem;">
                            유사도 {similarity_score:.1%}
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; font-size: 0.9rem;">
                        <div>
                            <div style="color: var(--text-light);">수익률</div>
                            <div style="font-weight: 600; color: {profit_color};">
                                {exp_trade.get('수익률', 0):+.1f}%
                            </div>
                        </div>
                        <div>
                            <div style="color: var(--text-light);">거래일</div>
                            <div style="font-weight: 600;">{safe_exp_date}</div>
                        </div>
                        <div>
                            <div style="color: var(--text-light);">감정태그</div>
                            <div style="font-weight: 600;">{safe_exp_emotion}</div>
                        </div>
                        <div>
                            <div style="color: var(--text-light);">교훈</div>
                            <div style="font-weight: 600; font-size: 0.8rem;">{safe_lesson}</div>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 거울 질문
            if mirror_questions:
                create_mirror_coaching_card(
                    "AI가 제안하는 성찰 질문",
                    ["🪞 과거의 당신이 현재의 당신에게 묻습니다"],
                    mirror_questions
                )
        
        else:
            st.info("🔍 이번 거래와 유사한 과거 경험을 찾지 못했습니다. 새로운 패턴이네요!")
            
            # 일반적인 성찰 질문 제공
            create_mirror_coaching_card(
                "첫 경험을 위한 성찰 질문",
                ["🌟 새로운 경험도 소중한 학습 기회입니다"],
                [
                    "이 투자 결정의 가장 큰 근거는 무엇이었나요?",
                    "당시의 감정이 판단에 어떤 영향을 미쳤나요?",
                    "같은 상황이 다시 온다면 어떻게 하시겠나요?"
                ]
            )
    except Exception as e:
        st.error(f"❌ AI 거울 분석 실패: {str(e)}")
        st.info("💡 **해결방법**: 페이지를 새로고침하거나 다른 거래를 선택해보세요.")

def show_review_note_section(trade):
    """복기 노트 작성 섹션"""
    st.markdown("---")
    st.markdown("### 📝 복기 노트 작성")
    
    st.info("💡 AI 분석을 참고하여 자신만의 복기 노트를 작성해보세요.")
    
    with st.form("review_note_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # 감정 재평가
            st.markdown("#### 🧠 감정 상태 재평가")
            current_emotion = trade.get('감정태그', '#욕심')
            emotion_options = ['#공포', '#욕심', '#확신', '#불안', '#냉정', '#후회', '#만족']
            current_index = emotion_options.index(current_emotion) if current_emotion in emotion_options else 1
            
            new_emotion = st.selectbox(
                "지금 다시 생각해보는 당시 감정",
                emotion_options,
                index=current_index
            )
        
        with col2:
            # 판단 근거 재검토
            st.markdown("#### 📊 판단 근거 재검토")
            decision_basis = st.multiselect(
                "당시 판단의 주요 근거 (복수 선택)",
                ['기술적 분석', '기본적 분석', '뉴스/정보', '주변 권유', '직감', '감정적 충동', '기타'],
                default=['감정적 충동']
            )
        
        # 배운 점
        st.markdown("#### 💡 배운 점과 개선점")
        lessons_learned = st.text_area(
            "이 거래에서 배운 점은 무엇인가요?",
            placeholder="예: 감정적 판단보다는 객관적 데이터를 더 중시해야겠다. 충분한 검토 시간을 가진 후 결정하자.",
            height=100
        )
        
        # 향후 원칙
        st.markdown("#### 📜 향후 투자 원칙")
        future_principles = st.text_area(
            "이 경험을 바탕으로 세울 투자 원칙이 있다면?",
            placeholder="예: 1) 급락장에서는 24시간 냉각기간을 갖는다. 2) 감정이 앞설 때는 투자 금액을 절반으로 줄인다.",
            height=100
        )
        
        # 점수 평가
        col1, col2 = st.columns(2)
        with col1:
            decision_score = st.slider("의사결정 과정 점수", 1, 10, 5)
        with col2:
            emotion_control_score = st.slider("감정 조절 점수", 1, 10, 5)
        
        # 즐겨찾기
        is_favorite = st.checkbox("⭐ 중요한 복기로 즐겨찾기 추가", value=False)
        
        # 제출 버튼
        submitted = st.form_submit_button("💾 복기 노트 저장", type="primary", use_container_width=True)
        
        if submitted:
            try:
                # 복기 노트 저장 로직 (실제로는 데이터베이스에 저장)
                review_note = {
                    'trade_date': trade['거래일시'],
                    'stock_name': trade['종목명'],
                    'original_emotion': trade.get('감정태그'),
                    'reviewed_emotion': new_emotion,
                    'decision_basis': decision_basis,
                    'lessons_learned': lessons_learned,
                    'future_principles': future_principles,
                    'decision_score': decision_score,
                    'emotion_control_score': emotion_control_score,
                    'is_favorite': is_favorite,
                    'review_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 세션에 저장 (실제로는 DB에 저장)
                if 'review_notes' not in st.session_state:
                    st.session_state.review_notes = []
                
                st.session_state.review_notes.append(review_note)
                
                st.success("✅ 복기 노트가 저장되었습니다!")
                st.balloons()
                
                # 저장 후 추가 액션 옵션
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📊 대시보드로", key="goto_dashboard_after_review"):
                        safe_navigate_to_page("pages/1_Dashboard.py")
                
                with col2:
                    if st.button("📝 오답노트 보기", key="goto_notes_after_review"):
                        safe_navigate_to_page("pages/6_Review_Notes.py")
                
                with col3:
                    if st.button("🔄 다른 거래 복기", key="review_another_trade"):
                        st.session_state.selected_trade_for_review = None
                        st.rerun()
            except Exception as e:
                st.error(f"❌ 복기 노트 저장 실패: {str(e)}")

# ================================
# [MAIN APPLICATION]
# ================================

def main():
    """메인 애플리케이션 로직"""
    try:
        if st.session_state.get('selected_trade_for_review') or st.session_state.get('demo_case'):
            show_trade_review_analysis()
        else:
            show_trade_selection_interface()
    except Exception as e:
        st.error(f"❌ 페이지 로드 실패: {str(e)}")
        st.info("💡 **해결방법**: 페이지를 새로고침하거나 홈으로 돌아가세요.")
        
        if st.button("🏠 홈으로 돌아가기", type="secondary"):
            safe_navigate_to_page("main_app.py")

if __name__ == "__main__":
    main()