import streamlit as st
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from pathlib import Path
from textwrap import dedent

# --- 프로젝트 루트 경로 설정 ---
try:
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root))
    
    from utils.ui_components import apply_toss_css, create_mirror_coaching_card, create_enhanced_metric_card
    from ml.mirror_coaching import MirrorCoaching
    from db.central_data_manager import get_data_manager, get_user_trading_history, get_user_profile
except (ImportError, NameError):
    # Streamlit Cloud나 유사 환경에서 실행될 때를 대비한 Fallback
    st.warning("필요한 모듈(db, utils, ml)을 찾을 수 없습니다. 일부 기능이 제한될 수 있습니다.")
    # 임시로 더미 클래스와 함수를 만들어 앱의 흐름을 유지합니다.
    class UserDatabase:
        def get_user_trades(self, username): return pd.DataFrame()
    class MirrorCoaching:
        def find_similar_experiences(self, situation, username): return []
        def generate_mirror_questions(self, experiences, situation): return []
    def apply_toss_css(): pass
    def create_mirror_coaching_card(title, content, questions): st.info(title)
    def create_enhanced_metric_card(title, value, subtitle, tone="neutral"): st.metric(label=title, value=value, delta=subtitle)

# --- 유틸리티 함수: HTML 렌더링 ---
def render_html(html_string):
    """
    Dedent 처리된 HTML 문자열을 st.markdown으로 안전하게 렌더링합니다.
    """
    st.markdown(dedent(html_string), unsafe_allow_html=True)

# --- 페이지 설정 ---
st.set_page_config(
    page_title="KB Reflex - AI 심리 코칭",
    page_icon="🤖",
    layout="wide"
)

# Toss 스타일 CSS 적용
apply_toss_css()

# ================================
# 🔐 통일된 로그인 가드 (REFLEX_USER)
# ================================
REFLEX_USER_KEY = "REFLEX_USER"

def require_login():
    """main_app.py와 동일한 세션 키로 로그인 상태 확인"""
    user = st.session_state.get(REFLEX_USER_KEY)
    if not user:
        st.error("⚠️ 로그인이 필요합니다.")
        if st.button("🏠 홈으로 돌아가기"):
            try:
                st.switch_page("main_app.py")
            except Exception:
                st.rerun()
        st.stop()
    return user

# 로그인 보장 + 현재 사용자
user = require_login()
username = user.get("username", "사용자")

# --- AI 코칭 세션 상태 초기화 ---
if 'coaching_session' not in st.session_state:
    st.session_state.coaching_session = {
        'current_situation': '',
        'emotion_state': '',
        'coaching_history': [],
        'session_start': datetime.now()
    }
if 'ai_coaching_goals' not in st.session_state:
    st.session_state.ai_coaching_goals = []
if 'editing_goal_index' not in st.session_state:
    st.session_state.editing_goal_index = None

# --- 메인 대시보드 함수 ---
def show_coaching_dashboard():
    """AI 코칭 대시보드"""
    render_html(f'''
        <div class="main-header-enhanced">
            🤖 {username}님의 AI 심리 코칭
        </div>
        <div class="sub-header-enhanced">
            실시간으로 투자 심리를 분석하고 개인화된 코칭을 받아보세요
        </div>
    ''')

    show_coaching_status()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 실시간 코칭",
        "📊 심리 패턴 분석",
        "🧘‍♂️ 감정 관리",
        "📈 성장 추적"
    ])

    with tab1:
        show_realtime_coaching()
    with tab2:
        show_psychology_analysis()
    with tab3:
        show_emotion_management()
    with tab4:
        show_growth_tracking()

# --- 컴포넌트 함수들 ---
def show_coaching_status():
    """코칭 상태 표시"""
    session = st.session_state.coaching_session
    session_duration = datetime.now() - session['session_start']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        create_enhanced_metric_card(
            "세션 시간", f"{session_duration.seconds // 60}분", "진행 중", tone="neutral"
        )
    with col2:
        create_enhanced_metric_card(
            "코칭 횟수", f"{len(session['coaching_history'])}회", "이번 세션", tone="neutral"
        )
    with col3:
        recent_emotion = session.get('emotion_state', '분석 중')
        create_enhanced_metric_card(
            "현재 감정", recent_emotion, "AI 분석 결과", tone="info"
        )
    with col4:
        confidence = np.random.randint(85, 98)
        create_enhanced_metric_card(
            "AI 신뢰도", f"{confidence}%", "분석 정확도", tone="positive"
        )

def show_realtime_coaching():
    """실시간 코칭"""
    st.markdown("### 🎯 현재 상황 기반 AI 코칭")
    with st.form("current_situation_form"):
        st.markdown("#### 💭 지금 어떤 생각을 하고 계신가요?")
        col1, col2 = st.columns([2, 1])
        with col1:
            current_situation = st.text_area(
                "현재 투자 상황이나 고민을 자유롭게 적어보세요",
                placeholder="예: 삼성전자가 5% 떨어졌는데 더 살까 말까 고민되고...",
                height=100,
                value=st.session_state.coaching_session.get('current_situation', '')
            )
        with col2:
            st.markdown("#### 🧠 현재 감정 상태")
            emotion_options = ["😟 불안함", "😰 두려움", "🤑 욕심", "😡 분노", "😌 냉정함", "😵‍💫 혼란", "😊 만족", "😤 초조함"]
            selected_emotion = st.selectbox("지금 느끼는 감정을 선택해주세요", emotion_options, index=0)
            urgency = st.slider("얼마나 급한 상황인가요?", 1, 10, 5, help="1: 여유로움 ~ 10: 매우 급함")
        
        submitted = st.form_submit_button("🤖 AI 코칭 받기", type="primary", use_container_width=True)
        if submitted and current_situation.strip():
            get_ai_coaching_response(current_situation, selected_emotion, urgency)

def get_ai_coaching_response(situation, emotion, urgency):
    """AI 코칭 응답 생성"""
    with st.spinner("🤖 AI가 당신의 상황을 분석하고 있습니다..."):
        time.sleep(2)
        mirror_coach = MirrorCoaching()
        similar_experiences, mirror_questions = [], []

        # 사용자 프로필 확인
        user_profile = get_user_profile(username)
        
        if user_profile and user_profile.username != "이거울":
            try:
                similar_experiences = mirror_coach.find_similar_experiences(situation, username)
                mirror_questions = mirror_coach.generate_mirror_questions(similar_experiences, situation)
            except Exception as e:
                st.warning(f"유사 경험 분석 중 오류 발생: {str(e)}")

        advice = generate_emotion_based_advice(emotion, urgency, similar_experiences)
        coaching_record = {
            'timestamp': datetime.now(), 
            'situation': situation, 
            'emotion': emotion, 
            'urgency': urgency, 
            'advice': advice, 
            'similar_count': len(similar_experiences)
        }
        
        st.session_state.coaching_session['coaching_history'].append(coaching_record)
        st.session_state.coaching_session['current_situation'] = situation
        st.session_state.coaching_session['emotion_state'] = emotion
        
        show_coaching_result(advice, similar_experiences, mirror_questions, urgency)

def generate_emotion_based_advice(emotion, urgency, similar_experiences):
    """감정 기반 맞춤형 조언 생성"""
    base_emotion = emotion.split(' ')[1] if ' ' in emotion else emotion
    advice_templates = {
        "불안함": {
            "title": "불안감 해소 가이드", 
            "immediate": [
                "🫁 먼저 깊게 숨을 쉬고 5분간 현재 상황을 객관적으로 정리해보세요",
                "📊 감정이 아닌 데이터로 판단해보세요 (차트, 재무제표, 뉴스 팩트)",
                "⏰ 지금 당장 결정하지 말고 24시간 여유를 두고 재검토하세요"
            ], 
            "long_term": [
                "불안감이 들 때마다 기록하고 패턴을 파악해보세요",
                "투자 전 체크리스트를 만들어 감정적 판단을 방지하세요",
                "소액으로 연습하며 경험을 쌓아가세요"
            ]
        },
        "두려움": {
            "title": "공포 극복 전략", 
            "immediate": [
                "🛡️ 현재 손실 한도선을 미리 정하고 그 범위 내에서 행동하세요",
                "📈 과거 시장 회복 사례들을 찾아보세요 (역사는 반복됩니다)",
                "💰 투자금의 일부만 위험에 노출시키고 나머지는 안전자산에 보관하세요"
            ], 
            "long_term": [
                "두려움의 원인을 구체적으로 분석해보세요",
                "위험 관리 계획을 수립하고 철저히 지키세요",
                "성공했던 투자 경험을 기록하고 자신감을 키우세요"
            ]
        },
        "욕심": {
            "title": "욕심 컨트롤 방법", 
            "immediate": [
                "🎯 원래 계획했던 목표 수익률을 다시 확인해보세요",
                "📉 욕심 때문에 실패했던 과거 경험을 떠올려보세요",
                "💡 '더 벌 수 있다'는 생각보다 '지금까지 번 것을 지키자'에 집중하세요"
            ], 
            "long_term": [
                "목표 수익률 달성 시 자동으로 일부 매도하는 규칙을 만드세요",
                "욕심으로 인한 손실 사례를 정리해 교훈으로 활용하세요",
                "분산투자로 한 번에 큰 수익을 노리지 않도록 하세요"
            ]
        },
        "냉정함": {
            "title": "냉정한 판단 유지법", 
            "immediate": [
                "✅ 지금의 차분한 상태가 최적의 판단 시점입니다",
                "📋 체크리스트를 활용해 빠뜨린 고려사항이 없는지 확인하세요",
                "🎯 장기적 관점에서 이 결정이 어떤 의미인지 생각해보세요"
            ], 
            "long_term": [
                "현재의 냉정한 분석 과정을 기록해두세요",
                "감정적일 때 참고할 수 있는 판단 기준을 만들어두세요",
                "냉정한 상태에서의 성공 사례를 축적하세요"
            ]
        },
        "default": {
            "title": "균형잡힌 투자 접근법", 
            "immediate": [
                "🧠 현재 상황을 객관적으로 분석해보세요",
                "📊 데이터와 감정을 분리해서 생각해보세요",
                "⚖️ 위험과 수익의 균형을 다시 한 번 점검하세요"
            ], 
            "long_term": [
                "지속적인 학습과 경험 축적에 집중하세요",
                "자신만의 투자 원칙을 정립하고 지켜나가세요",
                "시장의 변화에 유연하게 대응할 수 있는 능력을 기르세요"
            ]
        }
    }
    return advice_templates.get(base_emotion, advice_templates["default"])

def show_coaching_result(advice, similar_experiences, mirror_questions, urgency):
    """코칭 결과 표시"""
    st.markdown("---")
    st.markdown("### 🎯 AI 코칭 결과")

    if urgency >= 8: 
        st.error(f"🚨 높은 긴급도({urgency}/10) 감지! 신중한 접근이 필요합니다.")
    elif urgency >= 6: 
        st.warning(f"⚠️ 중간 긴급도({urgency}/10) - 충분한 검토 시간을 가지세요.")
    else: 
        st.info(f"✅ 안정적 상황({urgency}/10) - 차분한 분석이 가능한 상태입니다.")

    create_mirror_coaching_card(
        f"🎯 {advice['title']} - 지금 당장 해야 할 것",
        advice['immediate'],
        mirror_questions[:3] if mirror_questions else [
            "이 결정을 24시간 후에도 같은 마음으로 할 수 있나요?",
            "감정을 제거하고 순수하게 데이터만 본다면?",
            "가장 존경하는 투자자라면 어떻게 할까요?"
        ]
    )
    
    st.markdown("#### 📈 장기적 개선 방안")
    for tip in advice['long_term']: 
        st.markdown(f"• {tip}")

    if similar_experiences:
        st.markdown("---")
        st.markdown("#### 🪞 과거 유사 경험")
        st.success(f"📊 {len(similar_experiences)}개의 유사한 상황을 발견했습니다!")
        for i, exp in enumerate(similar_experiences[:2]):
            trade_data = exp.get('trade_data', {})
            similarity = exp.get('similarity_score', 0)
            with st.expander(f"유사 경험 {i+1}: {trade_data.get('종목명', 'N/A')} ({similarity:.1%} 유사)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**거래일**: {trade_data.get('거래일시', 'N/A')}")
                    st.write(f"**수익률**: {trade_data.get('수익률', 0):+.1f}%")
                    st.write(f"**감정태그**: {trade_data.get('감정태그', 'N/A')}")
                with col2:
                    st.write(f"**거래구분**: {trade_data.get('거래구분', 'N/A')}")
                    st.write(f"**수량**: {trade_data.get('수량', 0):,}주")
                    st.write(f"**교훈**: {exp.get('key_lesson', '학습 중')}")

def show_psychology_analysis():
    """심리 패턴 분석"""
    st.markdown("### 📊 투자 심리 패턴 분석")
    
    # 사용자 프로필 확인
    user_profile = get_user_profile(username)
    
    if not user_profile or user_profile.username == "이거울":
        show_beginner_psychology_guide()
        return

    # 중앙 데이터 매니저에서 거래 데이터 로드
    trades_data = get_user_trading_history(username)

    if not trades_data:
        st.warning("분석할 거래 데이터가 부족합니다.")
        return
    
    # DataFrame으로 변환
    trades_df = pd.DataFrame(trades_data)
    
    show_emotion_performance_analysis(trades_df)
    show_temporal_pattern_analysis(trades_df)
    show_cognitive_bias_diagnosis(trades_df)

def show_beginner_psychology_guide():
    """초보자용 심리 가이드"""
    st.info("📚 투자 초보자를 위한 심리적 함정과 대처법을 알려드립니다!")
    biases = [
        {
            'name': '손실 회피 편향', 
            'description': '같은 크기의 이익보다 손실을 2배 이상 크게 느끼는 심리', 
            'example': '10만원 손실이 10만원 수익보다 훨씬 아프게 느껴짐', 
            'solution': '사전에 손절선을 정하고 감정적 판단을 방지'
        },
        {
            'name': '확증 편향', 
            'description': '자신의 믿음을 뒷받침하는 정보만 찾고 신뢰하는 경향', 
            'example': '매수한 종목의 긍정적 뉴스만 찾아보게 됨', 
            'solution': '반대 의견도 적극적으로 찾아보고 검토하기'
        },
        {
            'name': '군집 사고', 
            'description': '다른 사람들이 하는 것을 따라 하려는 충동', 
            'example': '주변에서 모두 사는 주식을 덩달아 매수', 
            'solution': '독립적 분석과 개인 투자 원칙 고수'
        }
    ]
    for bias in biases:
        render_html(f'''
            <div class="premium-card">
                <h4 style="color: var(--text-primary); margin-bottom: 1rem;">⚠️ {bias['name']}</h4>
                <div style="margin-bottom: 1rem;"><strong>설명:</strong> {bias['description']}</div>
                <div style="margin-bottom: 1rem; background: #FEF3C7; padding: 0.75rem; border-radius: 8px;"><strong>예시:</strong> {bias['example']}</div>
                <div style="background: #F0FDF4; padding: 0.75rem; border-radius: 8px;"><strong>💡 대처법:</strong> {bias['solution']}</div>
            </div>
        ''')

def show_emotion_performance_analysis(trades_data):
    """감정별 성과 분석"""
    st.markdown("#### 🧠 감정별 투자 성과")
    try:
        emotion_analysis = trades_data.groupby('감정태그').agg({'수익률': ['mean', 'count', 'std']}).round(2)
        emotion_analysis.columns = ['평균수익률', '거래횟수', '변동성']
        emotion_analysis = emotion_analysis.sort_values('평균수익률', ascending=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🏆 성과가 좋은 감정 상태")
            for emotion, data in emotion_analysis.head(3).iterrows():
                render_html(f'''
                <div style="background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem;">
                    <div style="font-weight: 700; color: #059669; margin-bottom: 0.5rem;">{emotion}</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">평균 수익률: <strong>{data['평균수익률']:+.1f}%</strong> | 거래 횟수: <strong>{int(data['거래횟수'])}회</strong></div>
                </div>''')
        with col2:
            st.markdown("##### 📉 주의가 필요한 감정 상태")
            for emotion, data in emotion_analysis.tail(3).iterrows():
                render_html(f'''
                <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem;">
                    <div style="font-weight: 700; color: #DC2626; margin-bottom: 0.5rem;">{emotion}</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">평균 수익률: <strong>{data['평균수익률']:+.1f}%</strong> | 거래 횟수: <strong>{int(data['거래횟수'])}회</strong></div>
                </div>''')
    except Exception as e:
        st.error(f"감정별 분석 중 오류 발생: {str(e)}")

def show_temporal_pattern_analysis(trades_data):
    """시간별 패턴 분석"""
    st.markdown("#### ⏰ 시간대별 투자 패턴")
    try:
        trades_copy = trades_data.copy()
        trades_copy['거래시간'] = pd.to_datetime(trades_copy['거래일시'])
        trades_copy['시간대'] = trades_copy['거래시간'].dt.hour
        trades_copy['요일'] = trades_copy['거래시간'].dt.day_name()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🕐 시간대별 평균 수익률")
            hourly_perf = trades_copy.groupby('시간대')['수익률'].mean()
            if not hourly_perf.empty:
                st.success(f"✅ 최고 성과 시간: {hourly_perf.idxmax()}시 ({hourly_perf.max():+.1f}%)")
                st.error(f"❌ 최저 성과 시간: {hourly_perf.idxmin()}시 ({hourly_perf.min():+.1f}%)")
        with col2:
            st.markdown("##### 📅 요일별 평균 수익률")
            daily_perf = trades_copy.groupby('요일')['수익률'].mean().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).dropna()
            if not daily_perf.empty:
                st.success(f"✅ 최고 성과 요일: {daily_perf.idxmax()} ({daily_perf.max():+.1f}%)")
                st.error(f"❌ 최저 성과 요일: {daily_perf.idxmin()} ({daily_perf.min():+.1f}%)")
    except Exception as e:
        st.error(f"시간 패턴 분석 중 오류 발생: {str(e)}")

def show_cognitive_bias_diagnosis(trades_data):
    """인지적 편향 진단"""
    st.markdown("#### 🧩 인지적 편향 진단")
    try:
        loss_trade_ratio = (trades_data['수익률'] < 0).mean() * 100
        stock_counts = trades_data['종목명'].value_counts()
        repeated_stock_ratio = (stock_counts > 1).sum() / len(stock_counts) * 100 if len(stock_counts) > 0 else 0
        
        biases = []
        if loss_trade_ratio > 60:
            biases.append({
                'name': '손실 회피 편향', 
                'severity': '높음', 
                'description': f'손실 거래 비율이 {loss_trade_ratio:.1f}%로 높습니다.', 
                'advice': '손절선을 미리 정하고 감정적 판단을 줄이세요.'
            })
        if repeated_stock_ratio > 30:
            biases.append({
                'name': '확증 편향', 
                'severity': '중간', 
                'description': f'전체 종목의 {repeated_stock_ratio:.1f}%를 반복 투자했습니다.', 
                'advice': '다양한 종목과 섹터로 분산 투자를 고려하세요.'
            })

        if not biases:
            st.success("🎉 현재 큰 인지적 편향은 발견되지 않았습니다!")
        else:
            for bias in biases:
                severity_color = "#EF4444" if bias['severity'] == '높음' else "#F59E0B"
                render_html(f'''
                <div style="background: white; border: 2px solid {severity_color}; border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;">
                    <h4 style="color: {severity_color}; margin-bottom: 1rem;">⚠️ {bias['name']} ({bias['severity']})</h4>
                    <div style="margin-bottom: 1rem; color: var(--text-secondary);">{bias['description']}</div>
                    <div style="background: {severity_color}10; padding: 1rem; border-radius: 8px; color: var(--text-primary);">
                        💡 <strong>개선 방안:</strong> {bias['advice']}
                    </div>
                </div>''')
    except Exception as e:
        st.error(f"편향 진단 중 오류 발생: {str(e)}")

def show_emotion_management():
    """감정 관리 도구"""
    st.markdown("### 🧘‍♂️ 실시간 감정 관리")
    with st.form("emotion_checkin"):
        st.markdown("#### 🌡️ 현재 감정 온도 체크")
        col1, col2 = st.columns(2)
        with col1:
            fear = st.slider("두려움 정도", 0, 10, 5)
            greed = st.slider("욕심 정도", 0, 10, 5)
            confidence = st.slider("확신 정도", 0, 10, 5)
        with col2:
            stress = st.slider("스트레스 정도", 0, 10, 5)
            patience = st.slider("참을성 정도", 0, 10, 5)
            clarity = st.slider("판단 명확성", 0, 10, 5)
        
        if st.form_submit_button("📊 감정 상태 분석", type="primary"):
            analyze_current_emotion(fear, greed, confidence, stress, patience, clarity)

def analyze_current_emotion(fear, greed, confidence, stress, patience, clarity):
    """현재 감정 상태 분석"""
    st.markdown("---")
    st.markdown("#### 📊 감정 분석 결과")
    
    balance = (patience + clarity - stress - abs(fear - 5) - abs(greed - 5))
    if balance > 5:
        st.success("✅ 균형잡힌 감정 상태입니다. 투자 결정하기 좋은 시점이네요!")
        icon, advice = "✅", []
    elif balance > 0:
        st.warning("⚠️ 약간의 감정적 불균형이 있습니다. 신중하게 접근하세요.")
        icon, advice = "⚠️", []
    else:
        st.error("🚨 감정적으로 불안정한 상태입니다. 투자 결정을 미루는 것이 좋겠습니다.")
        icon, advice = "🚨", []

    if fear > 7: advice.append("🛡️ 높은 두려움 수치입니다. 위험 관리 계획을 재점검하세요.")
    if greed > 7: advice.append("🎯 욕심이 높은 상태입니다. 목표 수익률을 다시 확인하세요.")
    if stress > 7: advice.append("😮‍💨 스트레스가 높습니다. 잠시 휴식을 취하고 마음을 가라앉히세요.")
    if patience < 4: advice.append("⏰ 조급함이 느껴집니다. 충분한 검토 시간을 가지세요.")
    if clarity < 4: advice.append("🤔 판단이 흐릿한 상태입니다. 더 많은 정보를 수집해보세요.")
    if not advice: advice.append("🎉 전반적으로 안정적인 감정 상태를 유지하고 있습니다!")
    
    create_mirror_coaching_card(
        f"{icon} 감정 상태별 맞춤 조언", advice,
        ["지금 이 감정 상태에서 투자 결정을 해도 괜찮을까요?", "감정을 더 안정시키기 위해 무엇을 할 수 있을까요?", "객관적인 관점에서 현재 상황을 어떻게 평가하시나요?"]
    )
    show_emotion_stabilization_techniques(fear, greed, stress)

def show_emotion_stabilization_techniques(fear, greed, stress):
    """감정 안정화 기법 제안"""
    st.markdown("#### 🧘‍♂️ 감정 안정화 기법")
    techniques = []
    if fear > 6: 
        techniques.append({
            'name': '두려움 극복 호흡법', 
            'description': '4-7-8 호흡법으로 불안감을 줄여보세요', 
            'steps': ['4초간 숨 들이마시기', '7초간 숨 참기', '8초간 숨 내쉬기', '3-5회 반복']
        })
    if greed > 6: 
        techniques.append({
            'name': '욕심 조절 명상', 
            'description': '현재 가진 것에 대한 감사 명상', 
            'steps': ['편안한 자세로 앉기', '현재 보유 자산 생각하기', '그것에 대한 감사함 느끼기', '5분간 지속']
        })
    if stress > 6: 
        techniques.append({
            'name': '스트레스 해소 운동', 
            'description': '간단한 스트레칭으로 긴장 완화', 
            'steps': ['목과 어깨 돌리기', '깊은 숨쉬기', '손목과 발목 돌리기', '전신 스트레칭']
        })
    if not techniques: 
        techniques.append({
            'name': '균형 유지 명상', 
            'description': '현재의 안정적 상태를 유지하는 명상', 
            'steps': ['편안한 자세 취하기', '호흡에 집중하기', '현재 순간에 머물기', '평정심 유지하기']
        })

    for tech in techniques:
        with st.expander(f"🧘‍♂️ {tech['name']}"):
            st.write(tech['description'])
            st.markdown("**실행 방법:**")
            for i, step in enumerate(tech['steps'], 1): 
                st.write(f"{i}. {step}")

def show_growth_tracking():
    """성장 추적"""
    st.markdown("### 📈 AI 코칭 성장 추적")
    history = st.session_state.coaching_session.get('coaching_history', [])
    if not history:
        st.info("📊 아직 코칭 이력이 없습니다. 실시간 코칭을 받아보세요!")
        return
    show_coaching_progress(history)
    show_emotion_trend(history)
    show_learning_goals()

def show_coaching_progress(history):
    """코칭 진행 상황"""
    st.markdown("#### 📊 코칭 진행 현황")
    recent_sessions = history[-5:]
    col1, col2, col3 = st.columns(3)
    with col1:
        create_enhanced_metric_card("총 코칭 세션", f"{len(history)}회", "누적 기록", "neutral")
    with col2:
        recent_urgency = np.mean([s['urgency'] for s in recent_sessions]) if recent_sessions else 0
        urgency_trend = "안정" if recent_urgency < 5 else "주의" if recent_urgency < 7 else "긴급"
        create_enhanced_metric_card("평균 긴급도", f"{recent_urgency:.1f}/10", urgency_trend, "info")
    with col3:
        match_rate = np.mean([min(s['similar_count'], 3) for s in recent_sessions]) * 33.3 if recent_sessions else 0
        create_enhanced_metric_card("경험 매칭률", f"{match_rate:.0f}%", "AI 분석 정확도", "positive")

def show_emotion_trend(history):
    """감정 변화 추이"""
    st.markdown("#### 🧠 감정 패턴 변화")
    if len(history) < 6:
        st.info("코칭 기록이 6회 이상 쌓이면 감정 변화 추이를 분석해 드립니다.")
        return

    get_base_emotion = lambda s: (s.split(' ')[1] if ' ' in s else s)
    early_emotions = pd.Series([get_base_emotion(s['emotion']) for s in history[:3]]).value_counts()
    recent_emotions = pd.Series([get_base_emotion(s['emotion']) for s in history[-3:]]).value_counts()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 🔄 초기 주요 감정")
        st.write(early_emotions)
    with col2:
        st.markdown("##### ⭐ 최근 주요 감정")
        st.write(recent_emotions)

    neg_emotions = {'불안함', '두려움', '분노', '혼란', '초조함'}
    early_neg = sum(count for emotion, count in early_emotions.items() if emotion in neg_emotions)
    recent_neg = sum(count for emotion, count in recent_emotions.items() if emotion in neg_emotions)

    if recent_neg < early_neg: 
        st.success("🎉 부정적 감정이 감소하고 있습니다! 좋은 발전이에요.")
    elif recent_neg > early_neg: 
        st.warning("⚠️ 최근 감정적 스트레스가 증가했습니다. 감정 관리에 더 신경써보세요.")
    else: 
        st.info("📊 감정 패턴이 안정적으로 유지되고 있습니다.")

def show_learning_goals():
    """학습 목표 설정"""
    st.markdown("#### 🎯 개인 성장 목표 설정")
    current_goals = st.session_state.ai_coaching_goals

    with st.expander("📝 새로운 학습 목표 추가", expanded=not current_goals):
        with st.form("add_learning_goal"):
            goal_opts = ["감정적 투자 줄이기", "데이터 기반 의사결정 늘리기", "손절/익절 규칙 지키기", "분산투자 실천하기", "장기적 관점 유지하기", "FOMO 매수 줄이기", "공포매도 방지하기", "투자 일지 꾸준히 쓰기"]
            selected_goal = st.selectbox("달성하고 싶은 목표를 선택하세요", goal_opts)
            target_period = st.selectbox("목표 달성 기간", ["1개월", "3개월", "6개월", "1년"])
            specific_plan = st.text_area("구체적인 실행 계획", placeholder="예: 매주 복기 노트 2개 이상 작성하기")

            if st.form_submit_button("🎯 목표 추가", type="primary"):
                new_goal = {
                    'goal': selected_goal, 
                    'period': target_period, 
                    'plan': specific_plan, 
                    'created_date': datetime.now().strftime('%Y-%m-%d'), 
                    'progress': 0, 
                    'status': '진행중'
                }
                st.session_state.ai_coaching_goals.append(new_goal)
                st.success("🎉 새로운 학습 목표가 추가되었습니다!")
                st.rerun()

    if current_goals:
        st.markdown("##### 📋 현재 진행 중인 목표")
        for i, goal in enumerate(current_goals):
            color = "#10B981" if goal['progress'] >= 80 else "#F59E0B" if goal['progress'] >= 50 else "#EF4444"
            render_html(f'''
            <div style="background: white; border: 2px solid {color}; border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: var(--text-primary);">{goal['goal']}</h4>
                    <div style="background:{color}; color:white; padding:0.25rem 0.75rem; border-radius:12px; font-size:0.8rem; font-weight:700;">{goal['progress']}% 완료</div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">📅 목표 기간: {goal['period']} | 시작일: {goal['created_date']}</div>
                    <div style="color: var(--text-primary); line-height: 1.4;">📝 실행 계획: {goal['plan']}</div>
                </div>
                <div style="background: #F1F5F9; border-radius: 8px; height: 8px; overflow: hidden; margin-bottom: 1rem;">
                    <div style="background:{color}; height:100%; width:{goal['progress']}%; transition: width 0.3s ease;"></div>
                </div>
            </div>''')

            c1, c2, c3 = st.columns(3)
            if c1.button("📈 진행도 +10%", key=f"prog_{i}"):
                goal['progress'] = min(100, goal['progress'] + 10)
                if goal['progress'] == 100: 
                    goal['status'] = '완료'
                    st.balloons()
                st.rerun()
            if c2.button("📝 계획 수정", key=f"edit_{i}"): 
                st.session_state.editing_goal_index = i
                st.rerun()
            if c3.button("🗑️ 목표 삭제", key=f"del_{i}"): 
                st.session_state.ai_coaching_goals.pop(i)
                st.success("목표가 삭제되었습니다.")
                st.rerun()

    if st.session_state.editing_goal_index is not None:
        show_edit_goal_modal()

def show_edit_goal_modal():
    """목표 수정 모달"""
    index = st.session_state.editing_goal_index
    goal = st.session_state.ai_coaching_goals[index]
    
    st.markdown("---")
    st.markdown("### ✏️ 목표 수정")
    with st.form("edit_goal_form"):
        new_plan = st.text_area("실행 계획 수정", value=goal['plan'], height=100)
        new_progress = st.slider("현재 진행도", 0, 100, goal['progress'])
        
        c1, c2 = st.columns(2)
        if c1.form_submit_button("💾 저장", type="primary"):
            goal['plan'], goal['progress'] = new_plan, new_progress
            st.session_state.editing_goal_index = None
            st.success("목표가 수정되었습니다!")
            st.rerun()
        if c2.form_submit_button("❌ 취소"):
            st.session_state.editing_goal_index = None
            st.rerun()

def show_coaching_history():
    """코칭 이력"""
    st.markdown("---")
    st.markdown("### 📜 코칭 이력")
    history = st.session_state.coaching_session.get('coaching_history', [])
    if not history:
        st.info("아직 코칭 이력이 없습니다.")
        return
    
    recent_history = sorted(history, key=lambda x: x['timestamp'], reverse=True)[:5]
    for i, session in enumerate(recent_history):
        with st.expander(f"💬 {session['timestamp'].strftime('%Y-%m-%d %H:%M')} | {session['emotion']} | 긴급도 {session['urgency']}/10", expanded=(i==0)):
            st.markdown(f"**상황:** {session['situation']}")
            st.markdown(f"**AI 조언:** {session['advice']['title']}")
            if session['similar_count'] > 0: 
                st.success(f"🔍 {session['similar_count']}개의 유사 경험을 찾았습니다.")
            else: 
                st.info("🆕 새로운 패턴의 상황이었습니다.")

# --- 메인 실행 ---
def main():
    show_coaching_dashboard()
    show_coaching_history()

if __name__ == "__main__":
    main()
