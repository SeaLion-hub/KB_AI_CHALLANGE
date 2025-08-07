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
# 1. AI 분석을 위한 import 추가
from ml.predictor import SentimentPredictor

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

# 2. AI 모델 로드를 위한 캐시 함수 추가
@st.cache_resource
def get_predictor():
    """SentimentPredictor를 캐시하여 한 번만 로드합니다."""
    try:
        return SentimentPredictor(model_path='./sentiment_model')
    except Exception as e:
        st.error(f"AI 분석 모델 로딩에 실패했습니다: {e}")
        return None

def show_charter_compliance_check(username: str, memo: str) -> dict:
    """
    투자 헌장 준수 체크 함수 (분리된 함수)
    
    Args:
        username: 사용자명
        memo: 거래 메모
    
    Returns:
        dict: 준수 체크 결과
    """
    compliance_issues = []
    warnings = []
    recommendation = ""
    
    # 선택된 투자 원칙 확인
    selected_principle = st.session_state.get('selected_principle')
    
    if not selected_principle:
        return {
            'compliance_issues': [],
            'warnings': ["💡 투자 원칙을 설정하면 더 정확한 검증을 받을 수 있습니다."],
            'recommendation': "투자 헌장 페이지에서 투자 원칙을 선택해보세요."
        }
    
    memo_lower = memo.lower()
    
    # 공통 위험 패턴 체크
    if any(word in memo_lower for word in ['급히', '서둘러', '패닉', '무서워서']):
        compliance_issues.append("⚠️ 감정적 급한 판단으로 보입니다.")
    
    if any(word in memo_lower for word in ['추천받고', '유튜버', '친구가', '커뮤니티']):
        warnings.append("🤔 타인의 추천에 의존한 투자는 위험할 수 있습니다.")
    
    if any(word in memo_lower for word in ['확실', '100%', '대박', '올인']):
        compliance_issues.append("🚨 과도한 확신이나 올인 투자는 위험합니다.")
    
    # 원칙별 특별 체크
    if selected_principle == "워런 버핏":
        if not any(word in memo_lower for word in ['분석', '펀더멘털', '기업', '가치']):
            warnings.append("🎯 워런 버핏의 원칙: 철저한 기업 분석을 했나요?")
        
        if any(word in memo_lower for word in ['단기', '빨리']):
            compliance_issues.append("⏰ 워런 버핏 원칙 위배: 장기 투자 관점을 유지하세요.")
        
        recommendation = "기업의 내재가치를 분석하고 장기적 관점에서 투자하세요."
    
    elif selected_principle == "피터 린치":
        if not any(word in memo_lower for word in ['성장', '실적', '매출', '실생활']):
            warnings.append("🔍 피터 린치의 원칙: 성장 스토리를 파악했나요?")
        
        recommendation = "일상에서 경험한 기업의 성장 가능성을 분석해보세요."
    
    elif selected_principle == "벤저민 그레이엄":
        if not any(word in memo_lower for word in ['밸류에이션', '저평가', '안전마진', '재무제표']):
            warnings.append("⚖️ 벤저민 그레이엄의 원칙: 안전 마진을 확보했나요?")
        
        recommendation = "내재가치 대비 충분한 할인가에서 매수했는지 확인하세요."
    
    if not compliance_issues and not warnings:
        recommendation = "✅ 투자 원칙에 잘 부합하는 거래입니다!"
    
    return {
        'compliance_issues': compliance_issues,
        'warnings': warnings,
        'recommendation': recommendation
    }

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
        
        # 판단 근거 설명 (1. 세션 상태와 명시적으로 연결)
        st.session_state.decision_reasoning = st.text_area(
            "거래 결정의 판단 근거를 구체적으로 설명해주세요",
            height=100,
            placeholder="예: 기술적으로 상승 추세가 확실해 보였고, 유튜버의 추천도 있었다...",
            value=st.session_state.get('decision_reasoning', ''),
            key="decision_reasoning_input"
        )
        
        # 3. AI 분석 기능 추가
        if st.button("🤖 AI로 투자 패턴 분석하기", key="analyze_pattern"):
            predictor = get_predictor()
            if predictor and st.session_state.get('decision_reasoning', '').strip():
                # AI 분석 실행 및 결과 저장
                with st.spinner("AI가 투자 패턴을 분석 중입니다..."):
                    result = predictor.predict(st.session_state.decision_reasoning)
                    st.session_state.analysis_result = result
            elif not st.session_state.get('decision_reasoning', '').strip():
                st.warning("분석할 내용을 먼저 입력해주세요.")
            else:
                # get_predictor()가 None을 반환한 경우 (모델 로드 실패)
                st.error("AI 분석 기능을 사용할 수 없습니다. 모델 로드 상태를 확인하세요.")
        
        # 세션 상태에 분석 결과가 있으면 표시
        if 'analysis_result' in st.session_state and st.session_state.analysis_result:
            result = st.session_state.analysis_result
            pattern = result.get('pattern', 'N/A')
            confidence = result.get('confidence', 0)
            description = result.get('description', '')
            
            st.markdown("---")
            st.markdown("#### 🧠 AI 분석 결과")
            st.info(f"**감지된 패턴:** '{pattern}' (신뢰도: {confidence:.1%})")
            st.write(f"**패턴 설명:** {description}")
            
            # 추가적인 분석 결과 표시
            if 'all_probabilities' in result:
                st.markdown("**기타 가능한 패턴들:**")
                for pat, prob in sorted(result['all_probabilities'].items(), 
                                      key=lambda x: x[1], reverse=True)[:3]:
                    if pat != pattern:
                        st.write(f"- {pat}: {prob:.1%}")
            
            # 3. AI 추천 템플릿 섹션 추가
            st.markdown("#### ✍️ AI 추천 템플릿")
            st.markdown("감지된 패턴을 바탕으로 한 템플릿을 클릭하면 텍스트 영역에 추가됩니다.")
            
            # 4. 패턴별 템플릿 매핑 딕셔너리
            pattern_templates = {
                "추격매수": [
                    "급등하는 것을 보고 더 오를 것 같아서 따라 들어갔습니다.",
                    "이번 기회를 놓치면 후회할 것 같다는 생각에 매수했습니다.",
                    "다른 사람들이 모두 매수한다고 해서 뒤늦게 합류했습니다."
                ],
                "공포": [
                    "주가가 계속 하락해서 더 큰 손실을 보기 전에 매도했습니다.",
                    "시장의 공포 분위기에 휩쓸려 일단 현금화했습니다.",
                    "뉴스에서 악재가 나와서 무서워서 급하게 매도했습니다."
                ],
                "냉정": [
                    "사전에 계획한 분석과 원칙에 따라 거래를 실행했습니다.",
                    "기술적/기본적 지표가 설정한 기준에 도달하여 거래했습니다.",
                    "감정적 요인을 배제하고 데이터를 바탕으로 판단했습니다."
                ],
                "욕심": [
                    "이미 수익이 났지만 더 큰 수익을 위해 추가 매수했습니다.",
                    "쉽게 돈을 벌 수 있을 것 같아서 물량을 늘렸습니다.",
                    "100% 확실하다는 생각에 올인에 가깝게 투자했습니다."
                ],
                "과신": [
                    "내 분석이 완벽하다고 생각해서 확신을 갖고 매수했습니다.",
                    "과거 성공 경험을 바탕으로 이번에도 틀릴 리 없다고 생각했습니다.",
                    "위험을 과소평가하고 큰 금액을 투자했습니다."
                ],
                "손실회피": [
                    "손실을 확정하기 싫어서 계속 보유했습니다.",
                    "평단 낮추기를 위해 추가 매수를 했습니다.",
                    "손절하기 아까워서 더 기다려보기로 했습니다."
                ],
                "확증편향": [
                    "내 생각을 뒷받침하는 정보만 찾아서 확신을 가졌습니다.",
                    "반대 의견은 무시하고 호재만 믿고 투자했습니다.",
                    "원하는 결론에 맞는 분석만 골라서 참고했습니다."
                ],
                "군중심리": [
                    "모든 사람들이 사라고 해서 따라서 매수했습니다.",
                    "커뮤니티 분위기를 타고 동참했습니다.",
                    "유명한 사람의 추천을 그대로 따라했습니다."
                ],
                "패닉": [
                    "급작스러운 하락에 당황해서 일단 매도했습니다.",
                    "시장이 붕괴될 것 같은 공포에 모든 것을 정리했습니다.",
                    "뉴스를 보고 패닉 상태에서 성급하게 결정했습니다."
                ],
                "불안": [
                    "계속 보유하기 불안해서 일부만 매도했습니다.",
                    "변동성이 너무 커서 비중을 줄였습니다.",
                    "확실하지 않은 상황에서 안전하게 일부 정리했습니다."
                ]
            }
            
            # 5. 감지된 패턴에 해당하는 템플릿 가져오기
            templates = pattern_templates.get(pattern, [])
            
            if templates:
                # 6. 최대 3개의 템플릿을 버튼으로 표시
                cols = st.columns(min(3, len(templates)))
                
                for i, template in enumerate(templates[:3]):
                    with cols[i]:
                        # 템플릿을 짧게 표시 (첫 20글자)
                        short_template = template[:20] + "..." if len(template) > 20 else template
                        
                        # 7. 템플릿 버튼 클릭 시 텍스트 추가
                        if st.button(short_template, key=f"template_{i}", use_container_width=True):
                            current_text = st.session_state.get('decision_reasoning', '')
                            
                            # 기존 텍스트가 있으면 공백 추가 후 템플릿 추가
                            if current_text.strip():
                                new_text = current_text + " " + template
                            else:
                                new_text = template
                            
                            # 세션 상태 업데이트
                            st.session_state.decision_reasoning = new_text
                            st.success(f"템플릿이 추가되었습니다!")
                            st.rerun()
                        
                        # 전체 템플릿 내용을 작은 글씨로 표시
                        st.caption(template)
            else:
                st.info("이 패턴에 대한 템플릿이 준비되어 있지 않습니다.")
            
            # 2. AI 원칙 추천 버튼 추가
            if st.button("💡 AI로부터 원칙 추천받기", key="suggest_principle"):
                # 3a. 패턴별 원칙 매핑 딕셔너리
                pattern_to_principle = {
                    "추격매수": "급등하는 종목은 바로 매수하지 않고, 최소 1시간 이상 지켜본다.",
                    "공포": "시장이 급락할 때는, 매도 전에 내가 설정한 손절 기준에 부합하는지 먼저 확인한다.",
                    "과신": "높은 수익이 예상되더라도, 한 종목에 전체 자산의 20% 이상을 투자하지 않는다.",
                    "손실회피": "매수 가격에 얽매이지 않고, -15% 등 명확한 손절 원칙을 기계적으로 지킨다.",
                    "욕심": "단기 수익에 현혹되지 말고, 투자 전 목표 수익률과 기간을 명확히 설정한다.",
                    "확증편향": "투자 결정 전, 반대 의견과 위험 요소를 의무적으로 3가지 이상 검토한다.",
                    "군중심리": "타인의 추천에 의존하지 말고, 나만의 분석 기준과 체크리스트를 만든다.",
                    "패닉": "감정이 격해질 때는 24시간 냉정 기간을 두고, 그 후에 재검토한다.",
                    "불안": "불안할 때는 투자 금액을 절반으로 줄이고, 분할 매수/매도를 고려한다.",
                    "냉정": "현재의 합리적 투자 접근법을 계속 유지하되, 정기적으로 전략을 점검한다."
                }
                
                # 3b. 감지된 패턴 가져오기
                detected_pattern = result.get('pattern', '')
                
                # 3c. 매핑에서 해당하는 원칙 찾기
                suggested_principle = pattern_to_principle.get(detected_pattern, 
                    "감지된 패턴을 바탕으로 개인만의 투자 원칙을 세워보세요.")
                
                # 3d. 세션 상태에 저장
                st.session_state.suggested_rule = suggested_principle
                
                st.success(f"💡 '{detected_pattern}' 패턴에 기반한 투자 원칙이 아래 텍스트 상자에 자동으로 입력되었습니다!")
    
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
            "이번 거래에서 배운 점은 무엇인가요?",
            height=100,
            placeholder="예: 감정에 휘둘리지 않고 냉정하게 판단해야겠다...",
            key="lessons_learned"
        )