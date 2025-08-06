import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from db.user_db import UserDatabase
from api.market_api import MarketAPI
from utils.ui_components import apply_toss_css, create_metric_card
from ml.investment_charter_logic import show_charter_compliance_check

# 페이지 설정
st.set_page_config(
    page_title="KB Reflex - 거래 복기",
    page_icon="📝",
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
    
    st.sidebar.markdown("📝 **거래 복기** ← 현재 위치")
    
    if st.sidebar.button("🤖 AI 코칭", use_container_width=True):
        st.switch_page("pages/3_AI_Coaching.py")
    
    if st.sidebar.button("📜 투자 헌장", use_container_width=True):
        st.switch_page("pages/4_Investment_Charter.py")
    
    # 복기 노트 개수 표시
    if 'review_notes' in st.session_state:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 📝 작성한 복기 노트")
        st.sidebar.markdown(f"**총 {len(st.session_state.review_notes)}개** 작성됨")

def show_trade_selection():
    """거래 선택 화면"""
    user_info = st.session_state.current_user
    username = user_info['username']
    
    st.markdown(f'''
    <h1 class="main-header">📝 상황재현 복기 노트</h1>
    <p class="sub-header">{username}님의 과거 거래를 선택하여 당시 상황을 재현하고 복기해보세요</p>
    ''', unsafe_allow_html=True)
    
    # 사용자 거래 데이터 로드
    user_db = UserDatabase()
    trades_data = user_db.get_user_trades(username)
    
    if trades_data is None or len(trades_data) == 0:
        st.info(f"📊 {username}님의 거래 데이터를 찾을 수 없습니다.")
        return
    
    # 거래 데이터 전처리
    trades_data['거래일시'] = pd.to_datetime(trades_data['거래일시'])
    trades_data = trades_data.sort_values('거래일시', ascending=False)
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 수익/손실 필터
        profit_filter = st.selectbox(
            "수익/손실 필터",
            ["전체", "수익 거래만", "손실 거래만"],
            key="profit_filter"
        )
    
    with col2:
        # 감정 태그 필터
        available_emotions = ["전체"] + list(trades_data['감정태그'].unique())
        emotion_filter = st.selectbox(
            "감정 태그 필터",
            available_emotions,
            key="emotion_filter"
        )
    
    with col3:
        # 종목 필터
        available_stocks = ["전체"] + list(trades_data['종목명'].unique())
        stock_filter = st.selectbox(
            "종목 필터",
            available_stocks,
            key="stock_filter"
        )
    
    # 필터 적용
    filtered_trades = trades_data.copy()
    
    if profit_filter == "수익 거래만":
        filtered_trades = filtered_trades[filtered_trades['수익률'] > 0]
    elif profit_filter == "손실 거래만":
        filtered_trades = filtered_trades[filtered_trades['수익률'] < 0]
    
    if emotion_filter != "전체":
        filtered_trades = filtered_trades[filtered_trades['감정태그'] == emotion_filter]
    
    if stock_filter != "전체":
        filtered_trades = filtered_trades[filtered_trades['종목명'] == stock_filter]
    
    st.markdown(f"### 📋 거래 목록 ({len(filtered_trades)}건)")
    
    if len(filtered_trades) == 0:
        st.info("필터 조건에 해당하는 거래가 없습니다.")
        return
    
    # 거래 목록 표시
    for idx, trade in filtered_trades.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            profit_color = "success" if trade['수익률'] > 0 else "negative"
            st.markdown(f'''
            <div style="margin-bottom: 0.5rem;">
                <strong style="font-size: 1.1rem;">{trade['종목명']}</strong>
                <span style="color: var(--{'positive' if trade['수익률'] > 0 else 'negative'}-color); font-weight: 700; margin-left: 1rem;">
                    {trade['수익률']:+.1f}%
                </span>
            </div>
            <div style="font-size: 0.9rem; color: var(--text-secondary);">
                {trade['거래일시'].strftime('%Y년 %m월 %d일')} | {trade['거래구분']} | {trade['수량']}주
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div class="emotion-tag emotion-{trade['감정태그'].replace('#', '').lower()}" style="margin-top: 0.5rem;">
                {trade['감정태그']}
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            if len(trade['메모']) > 30:
                memo_preview = trade['메모'][:30] + "..."
            else:
                memo_preview = trade['메모']
            st.markdown(f'''
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.5rem;">
                💬 {memo_preview}
            </div>
            ''', unsafe_allow_html=True)
        
        with col4:
            if st.button("복기하기", key=f"review_{idx}", type="primary"):
                st.session_state.selected_trade_for_review = trade.to_dict()
                st.rerun()
        
        st.markdown("<hr style='margin: 1rem 0; opacity: 0.3;'>", unsafe_allow_html=True)

def show_trade_review():
    """선택된 거래의 상황재현 복기 화면"""
    if 'selected_trade_for_review' not in st.session_state or st.session_state.selected_trade_for_review is None:
        show_trade_selection()
        return
    
    trade = st.session_state.selected_trade_for_review
    
    # 뒤로가기 버튼
    if st.button("⬅️ 거래 목록으로 돌아가기", key="back_to_list"):
        st.session_state.selected_trade_for_review = None
        st.rerun()
    
    st.markdown("---")
    
    # 거래 기본 정보
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f'''
        <h1 class="main-header">📝 {trade['종목명']} 거래 복기</h1>
        <p class="sub-header">{pd.to_datetime(trade['거래일시']).strftime('%Y년 %m월 %d일')} 거래 상황을 재현합니다</p>
        ''', unsafe_allow_html=True)
    
    with col2:
        profit_class = "positive" if trade['수익률'] > 0 else "negative"
        create_metric_card("거래 결과", f"{trade['수익률']:+.1f}%", profit_class)
    
    # 거래 상세 정보 카드
    st.markdown("### 📋 거래 상세 정보")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card("거래 구분", trade['거래구분'], "")
    
    with col2:
        create_metric_card("거래 수량", f"{trade['수량']:,}주", "")
    
    with col3:
        create_metric_card("거래 가격", f"₩{trade['가격']:,}", "")
    
    with col4:
        create_metric_card("감정 상태", trade['감정태그'], "")
    
    # 당시 상황 재현
    st.markdown("### 🔍 당시 상황 재현")
    
    # Market API를 통해 과거 데이터 가져오기
    market_api = MarketAPI()
    trade_date = pd.to_datetime(trade['거래일시']).date()
    historical_info = market_api.get_historical_info(trade['종목코드'], trade_date)
    
    if historical_info:
        col1, col2 = st.columns(2)
        
        with col1:
            # 주가 정보
            st.markdown('''
            <div class="card">
                <h4 style="color: var(--text-primary); margin-bottom: 1rem;">📈 주가 정보</h4>
            ''', unsafe_allow_html=True)
            
            st.markdown(f"**종가:** ₩{historical_info['price']:,}")
            st.markdown(f"**등락률:** {historical_info['change']:+.1f}%")
            st.markdown(f"**거래량:** {historical_info['volume']:,}")
            st.markdown(f"**시가총액:** ₩{historical_info['market_cap']:,}억")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 기술적 지표
            st.markdown('''
            <div class="card" style="margin-top: 1rem;">
                <h4 style="color: var(--text-primary); margin-bottom: 1rem;">📊 주요 지표</h4>
            ''', unsafe_allow_html=True)
            
            for indicator, value in historical_info['indicators'].items():
                st.markdown(f"**{indicator}:** {value}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # 관련 뉴스
            st.markdown('''
            <div class="card">
                <h4 style="color: var(--text-primary); margin-bottom: 1rem;">📰 관련 뉴스</h4>
            ''', unsafe_allow_html=True)
            
            for i, news in enumerate(historical_info['news'], 1):
                st.markdown(f"**{i}.** {news}")
                st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 시장 분위기
            st.markdown('''
            <div class="card" style="margin-top: 1rem;">
                <h4 style="color: var(--text-primary); margin-bottom: 1rem;">🌡️ 시장 분위기</h4>
            ''', unsafe_allow_html=True)
            
            st.markdown(f"**코스피 지수:** {trade.get('코스피지수', 2400):.0f}포인트")
            st.markdown(f"**시장 감정:** {historical_info['market_sentiment']}")
            st.markdown(f"**투자자 동향:** {historical_info['investor_trend']}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("❌ 과거 데이터를 불러올 수 없습니다.")
    
    # 당시 메모
    st.markdown("### 💭 당시 작성한 메모")
    st.markdown(f'''
    <div class="card" style="background-color: #FFF7ED; border: 1px solid #FDBA74;">
        <div style="font-style: italic; color: var(--text-secondary);">
            "{trade['메모']}"
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 투자 헌장 준수 체크
    username = st.session_state.current_user['username']
    compliance_check = show_charter_compliance_check(username, trade['메모'])
    
    if compliance_check['compliance_issues'] or compliance_check['warnings']:
        st.markdown("### ⚖️ 투자 헌장 준수 체크")
        
        if compliance_check['compliance_issues']:
            for issue in compliance_check['compliance_issues']:
                st.error(issue)
        
        if compliance_check['warnings']:
            for warning in compliance_check['warnings']:
                st.warning(warning)
        
        st.info(f"💡 **권장사항:** {compliance_check['recommendation']}")
    
    # 복기 작성
    st.markdown("### ✍️ 복기 노트 작성")
    
    tab1, tab2, tab3 = st.tabs(["🧠 감정 분석", "📊 판단 근거", "💡 개선점"])
    
    with tab1:
        st.markdown("#### 당시의 감정 상태를 분석해보세요")
        
        # 감정 강도
        emotion_intensity = st.slider(
            "감정의 강도 (1: 매우 약함 ~ 10: 매우 강함)",
            min_value=1,
            max_value=10,
            value=5,
            key="emotion_intensity"
        )
        
        # 추가 감정
        additional_emotions = st.multiselect(
            "당시 느꼈던 다른 감정들을 선택하세요",
            ["불안", "흥분", "공포", "욕심", "후회", "확신", "조급함", "만족"],
            key="additional_emotions"
        )
        
        # 감정에 대한 설명
        emotion_description = st.text_area(
            "당시의 감정 상태를 구체적으로 설명해주세요",
            height=100,
            placeholder="예: 주가가 계속 오르는 것을 보면서 놓치면 안 된다는 생각이 강했다...",
            key="emotion_description"
        )
    
    with tab2:
        st.markdown("#### 거래 결정의 판단 근거를 분석해보세요")
        
        # 판단 근거 선택
        decision_factors = st.multiselect(
            "거래 결정에 영향을 준 요소들을 선택하세요",
            ["기술적 분석", "기본적 분석", "뉴스/정보", "타인 추천", "직감", "과거 경험", "시장 분위기"],
            key="decision_factors"
        )
        
        # 정보 출처
        info_sources = st.multiselect(
            "정보를 얻은 출처를 선택하세요",
            ["증권사 리포트", "뉴스", "유튜브", "블로그", "커뮤니티", "지인", "직접 분석"],
            key="info_sources"
        )
        
        # 판단 근거 설명
        decision_reasoning = st.text_area(
            "거래 결정의 판단 근거를 구체적으로 설명해주세요",
            height=100,
            placeholder="예: 기술적으로 상승 추세가 확실해 보였고, 유튜버의 추천도 있었다...",
            key="decision_reasoning"
        )
    
    with tab3:
        st.markdown("#### 이번 거래에서 얻은 교훈과 개선점을 적어보세요")
        
        # 만족도
        satisfaction = st.slider(
            "이번 거래에 대한 만족도 (1: 매우 불만족 ~ 10: 매우 만족)",
            min_value=1,
            max_value=10,
            value=5,
            key="satisfaction"
        )
        
        # 개선점
        improvements = st.text_area(
            "다음에는 어떻게 하면 더 좋은 결과를 얻을 수 있을까요?",
            height=100,
            placeholder="예: 더 신중한 분석 후 매수 타이밍을 잡아야겠다...",
            key="improvements"
        )
        
        # 교훈
        lessons_learned = st.text_area(
            "이번 거래를 통해 얻은 교훈이 있다면 적어주세요",
            height=100,
            placeholder="예: 감정적 판단보다는 데이터에 기반한 객관적 분석이 중요하다...",
            key="lessons_learned"
        )
        
        # 새로운 투자 원칙 추가
        new_rule = st.text_input(
            "이 경험을 바탕으로 새로운 투자 원칙을 만들어보세요",
            placeholder="예: 급등한 종목은 하루 더 지켜본 후 매수하기",
            key="new_investment_rule"
        )
    
    # 복기 노트 저장
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("💾 복기 노트 저장", type="primary", use_container_width=True):
            # 세션에 복기 노트 저장 (실제 구현에서는 데이터베이스에 저장)
            if 'review_notes' not in st.session_state:
                st.session_state.review_notes = []
            
            review_note = {
                'timestamp': datetime.now(),
                'trade': trade,
                'emotion_intensity': st.session_state.get('emotion_intensity', 5),
                'additional_emotions': st.session_state.get('additional_emotions', []),
                'emotion_description': st.session_state.get('emotion_description', ''),
                'decision_factors': st.session_state.get('decision_factors', []),
                'info_sources': st.session_state.get('info_sources', []),
                'decision_reasoning': st.session_state.get('decision_reasoning', ''),
                'satisfaction': st.session_state.get('satisfaction', 5),
                'improvements': st.session_state.get('improvements', ''),
                'lessons_learned': st.session_state.get('lessons_learned', ''),
                'new_rule': st.session_state.get('new_investment_rule', '')
            }
            
            st.session_state.review_notes.append(review_note)
            
            # 새로운 투자 원칙이 있으면 헌장에 추가
            if st.session_state.get('new_investment_rule', '').strip():
                try:
                    from ml.investment_charter_logic import InvestmentCharter
                    charter = InvestmentCharter(username)
                    charter.add_personal_rule(st.session_state.new_investment_rule, "복기에서 학습")
                    st.success("✅ 복기 노트가 저장되고 새로운 투자 원칙이 헌장에 추가되었습니다!")
                except:
                    st.success("✅ 복기 노트가 저장되었습니다!")
            else:
                st.success("✅ 복기 노트가 저장되었습니다!")
            
            st.balloons()
    
    with col2:
        if st.button("🤖 AI 분석 요청", type="secondary", use_container_width=True):
            # AI 분석 페이지로 이동하면서 현재 거래 정보 전달
            st.session_state.ai_analysis_trade = trade
            st.switch_page("pages/3_AI_Coaching.py")

def main():
    """메인 함수"""
    # 사이드바에 사용자 정보 및 네비게이션 표시
    show_user_switcher_sidebar()
    
    # 메인 콘텐츠 표시
    show_trade_review()

if __name__ == "__main__":
    main()