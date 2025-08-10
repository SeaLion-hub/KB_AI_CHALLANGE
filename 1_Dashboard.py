import streamlit as st
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ui_components import apply_toss_css, create_enhanced_metric_card, create_mirror_coaching_card, render_html
from ml.mirror_coaching import MirrorCoaching
from db.central_data_manager import get_data_manager, get_market_data, get_economic_data, get_user_trading_history, get_latest_news

# 페이지 설정
st.set_page_config(
    page_title="KB Reflex - 실시간 대시보드",
    page_icon="📊",
    layout="wide"
)

# Toss 스타일 CSS 적용
apply_toss_css()

# ─────────────────────────────────────────────────────────
# 🔐 로그인 상태 점검 (main_app.py와 같은 세션 키 사용)
# ─────────────────────────────────────────────────────────
REFLEX_USER_KEY = "REFLEX_USER"  # main_app.SessionKeys.USER 와 동일 의미

if st.session_state.get(REFLEX_USER_KEY) is None:
    st.error("⚠️ 로그인이 필요합니다.")
    if st.button("🏠 홈으로 돌아가기"):
        # 멀티페이지 구조에서 메인으로 복귀
        try:
            st.switch_page("main_app.py")
        except Exception:
            st.rerun()
    st.stop()

# 현재 사용자 정보
user = st.session_state[REFLEX_USER_KEY]
username = user.get('username', '사용자')

# render_html 함수 임시 정의 (HTML 렌더링 수정)
def render_html(html):
    st.markdown(html, unsafe_allow_html=True)

# 대시보드 초기화
@st.cache_data(ttl=30)  # 30초간 캐시
def initialize_dashboard_data(username):
    """대시보드 데이터 초기화"""
    data_manager = get_data_manager()

    if username == "이거울":
        # 시뮬레이션 데이터
        return {
            'cash': 50000000,
            'holdings': {},
            'portfolio_value': 50000000,
            'total_return': 0.0,
            'recent_trades': []
        }
    else:
        # 중앙 데이터 매니저에서 거래 데이터 로드
        trades_data = get_user_trading_history(username)

        if not trades_data:
            return {
                'cash': 50000000,
                'holdings': {},
                'portfolio_value': 50000000,
                'total_return': 0.0,
                'recent_trades': []
            }

        # DataFrame으로 변환하여 계산
        trades_df = pd.DataFrame(trades_data)
        total_invested = (trades_df['수량'] * trades_df['가격']).sum() if len(trades_df) > 0 else 0
        avg_return = trades_df['수익률'].mean() if len(trades_df) > 0 else 0

        # 포트폴리오 가치 계산
        portfolio_value = 50000000 + (total_invested * avg_return / 100)

        return {
            'cash': max(10000000, 50000000 - total_invested * 0.3),
            'holdings': {
                '삼성전자': {'shares': 100, 'avg_price': 65000},
                'SK하이닉스': {'shares': 50, 'avg_price': 120000},
                'NAVER': {'shares': 30, 'avg_price': 180000}
            },
            'portfolio_value': portfolio_value,
            'total_return': avg_return,
            'recent_trades': trades_data[-5:] if len(trades_data) > 5 else trades_data
        }

# 대시보드 메인 콘텐츠
def show_enhanced_dashboard():
    """향상된 대시보드 표시"""

    # 헤더
    render_html(f'''
    <div class="main-header-enhanced">
        📊 {username}님의 실시간 대시보드
    </div>
    <div class="sub-header-enhanced">
        AI 기반 투자 인사이트와 실시간 포트폴리오 현황을 확인하세요
    </div>
    ''')

    # 라이브 인디케이터
    render_html('''
    <div class="live-indicator-enhanced" style="margin-bottom: 2rem;">
        <div class="live-dot-enhanced"></div>
        실시간 업데이트
    </div>
    ''')

    # 중앙 데이터 매니저에서 데이터 로드
    dashboard_data = initialize_dashboard_data(username)
    market_data = get_market_data(refresh=True)
    economic_data = get_economic_data()

    # 포트폴리오 가치 계산
    current_portfolio_value = dashboard_data['cash']
    for stock, holdings in dashboard_data['holdings'].items():
        if stock in market_data:
            current_portfolio_value += holdings['shares'] * market_data[stock].current_price

    # 메트릭 카드 섹션
    st.markdown("### 📈 포트폴리오 현황")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_return_pct = (current_portfolio_value - 50000000) / 50000000 * 100
        create_enhanced_metric_card(
            "총 자산",
            f"{current_portfolio_value:,.0f}원",
            f"{total_return_pct:+.1f}%",
            "positive" if total_return_pct >= 0 else "negative"
        )

    with col2:
        kospi_data = economic_data.get('KOSPI', {})
        create_enhanced_metric_card(
            "KOSPI 지수",
            f"{kospi_data.get('current', 2450):,.0f}",
            f"{kospi_data.get('change_pct', 0):+.2f}%",
            "positive" if kospi_data.get('change_pct', 0) >= 0 else "negative"
        )

    with col3:
        create_enhanced_metric_card(
            "현금",
            f"{dashboard_data['cash']:,.0f}원",
            f"{dashboard_data['cash']/current_portfolio_value*100:.1f}%"
        )

    with col4:
        mirror_coach = MirrorCoaching()
        insights = mirror_coach.initialize_for_user(username)
        insight_count = len(insights.get('insights', {}))
        create_enhanced_metric_card(
            "AI 인사이트",
            f"{insight_count}개",
            "분석 완료"
        )

    # 차트 섹션
    col1, col2 = st.columns([2, 1])

    with col1:
        render_html('''
        <div class="premium-card">
            <div class="premium-card-title">
                📊 포트폴리오 가치 추이
            </div>
        </div>
        ''')

        # 포트폴리오 차트 생성
        chart_data = generate_portfolio_chart_data(current_portfolio_value)
        fig = create_portfolio_chart(chart_data)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        render_html('''
        <div class="premium-card">
            <div class="premium-card-title">
                🔥 실시간 HOT 종목
            </div>
        </div>
        ''')

        # HOT 종목 리스트
        hot_stocks = sorted(
            market_data.items(),
            key=lambda x: abs(x[1].change_pct),
            reverse=True
        )[:5]

        for stock_name, data in hot_stocks:
            change_color = "#14AE5C" if data.change_pct > 0 else "#DC2626"
            st.markdown(f'''
            <div style="
                background: white;
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <div style="font-weight: 700; color: var(--text-primary);">{stock_name}</div>
                    <div style="font-size: 0.85rem; color: var(--text-light);">{data.current_price:,.0f}원</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: {change_color}; font-weight: 700;">
                        {data.change_pct:+.2f}%
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-light);">
                        거래량 {data.volume:,}
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

    # 뉴스 섹션 추가
    show_market_news_section()

    # AI 거울 코칭 섹션
    if username != "이거울":
        show_mirror_coaching_section(username)
    else:
        show_beginner_coaching_section()

    # 보유 종목 상세
    if dashboard_data['holdings']:
        show_holdings_detail(dashboard_data['holdings'], market_data)

    # 최근 거래 내역
    if dashboard_data['recent_trades']:
        show_recent_trades(dashboard_data['recent_trades'])

def show_market_news_section():
    """시장 뉴스 섹션"""
    st.markdown("---")
    st.markdown("### 📰 오늘의 시장 뉴스")

    # 중앙 데이터 매니저에서 뉴스 로드
    latest_news = get_latest_news()

    if latest_news:
        for news in latest_news[:3]:  # 최신 3개 뉴스만 표시
            impact_color = {
                "positive": "#14AE5C",
                "negative": "#DC2626",
                "neutral": "#6B7280"
            }.get(news.impact, "#6B7280")

            impact_icon = {
                "positive": "📈",
                "negative": "📉",
                "neutral": "📊"
            }.get(news.impact, "📊")

            st.markdown(f'''
            <div class="premium-card" style="margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="font-size: 1.5rem; margin-right: 0.5rem;">{impact_icon}</span>
                    <div style="flex: 1;">
                        <h4 style="margin: 0; color: var(--text-primary);">{news.title}</h4>
                        <div style="color: var(--text-light); font-size: 0.85rem; margin-top: 0.25rem;">
                            {news.timestamp.strftime('%Y-%m-%d %H:%M')} • {news.category}
                        </div>
                    </div>
                    <div style="
                        background: {impact_color}15;
                        color: {impact_color};
                        padding: 0.25rem 0.75rem;
                        border-radius: 12px;
                        font-size: 0.75rem;
                        font-weight: 600;
                    ">
                        {news.impact.upper()}
                    </div>
                </div>
                <p style="color: var(--text-secondary); line-height: 1.5; margin: 0;">
                    {news.content[:100]}...
                </p>
                {f'<div style="margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-light);">관련 종목: {", ".join(news.related_stocks)}</div>' if news.related_stocks and news.related_stocks != ["전체"] else ''}
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("📰 최신 뉴스를 불러오는 중입니다...")

def generate_portfolio_chart_data(current_value):
    """포트폴리오 차트 데이터 생성"""
    dates = []
    values = []
    base_date = datetime.now() - timedelta(days=30)

    for i in range(31):
        date = base_date + timedelta(days=i)
        if i == 0:
            value = 50000000  # 초기 자본
        else:
            # 점진적 변화 시뮬레이션
            change = np.random.normal(0, current_value * 0.005)
            value = values[-1] + change

        dates.append(date)
        values.append(value)

    # 마지막 값을 현재 값으로 조정
    values[-1] = current_value

    return {'dates': dates, 'values': values}

def create_portfolio_chart(chart_data):
    """포트폴리오 차트 생성"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=chart_data['dates'],
        y=chart_data['values'],
        mode='lines',
        name='포트폴리오 가치',
        line=dict(color='#3182F6', width=3),
        fill='tonexty',
        fillcolor='rgba(49, 130, 246, 0.1)',
        hovertemplate='<b>%{y:,.0f}원</b><br>%{x}<extra></extra>'
    ))

    # 초기 자본 라인
    fig.add_hline(
        y=50000000,
        line_dash="dash",
        line_color="rgba(156, 163, 175, 0.5)",
        annotation_text="초기 자본"
    )

    fig.update_layout(
        title="",
        xaxis=dict(showgrid=True, gridcolor='rgba(229, 232, 235, 0.3)'),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(229, 232, 235, 0.3)',
            tickformat=',.0f',
            ticksuffix='원'
        ),
        height=300,
        margin=dict(l=80, r=20, t=20, b=40),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Pretendard", color="#191919")
    )

    return fig

def show_mirror_coaching_section(username):
    """거울 코칭 섹션"""
    st.markdown("---")
    st.markdown("### 🪞 AI 거울 코칭")

    mirror_coach = MirrorCoaching()

    # 중앙 데이터 매니저에서 거래 데이터 로드
    trades_data = get_user_trading_history(username)

    if trades_data and len(trades_data) > 0:
        # DataFrame으로 변환
        trades_df = pd.DataFrame(trades_data)

        # 추천 복기 거래 (최근 거래 중 수익률이 극단적인 것들)
        if len(trades_df) > 0:
            # 최근 10개 거래 중에서 극단적인 수익률 찾기
            recent_trades = trades_df.tail(10)
            extreme_trades = recent_trades[
                (recent_trades['수익률'] > 15) | (recent_trades['수익률'] < -15)
            ]

            if len(extreme_trades) > 0:
                top_trade = extreme_trades.iloc[0]

                insights = [
                    f"🎯 {top_trade['종목명']} 거래의 복기가 필요합니다",
                    f"📊 수익률: {top_trade['수익률']:+.1f}%, 감정태그: {top_trade.get('감정태그', 'N/A')}",
                    "🤔 유사한 패턴이 반복되고 있는지 확인해보세요"
                ]

                questions = [
                    "이 거래에서 가장 아쉬운 점은 무엇인가요?",
                    "같은 상황이 다시 온다면 어떻게 하시겠나요?"
                ]

                create_mirror_coaching_card(
                    "복기 추천 거래 발견!",
                    insights,
                    questions
                )

                if st.button("🪞 지금 복기하기", key="goto_review_from_dashboard"):
                    # 메인앱의 표준 세션 키도 함께 설정해 서로 호환되게 함
                    st.session_state["REFLEX_SELECTED_TRADE"] = top_trade.to_dict()
                    st.session_state["REFLEX_ONBOARDING_STAGE"] = None  # 혹시 남아있을 온보딩 제거
                    try:
                        st.switch_page("pages/2_Trade_Review.py")
                    except Exception:
                        st.rerun()
            else:
                st.info("🔍 특별히 복기할 거래를 찾고 있습니다...")
        else:
            st.info("🔍 복기할 거래를 찾고 있습니다...")
    else:
        st.info("🔍 복기할 거래를 찾고 있습니다...")

def show_beginner_coaching_section():
    """초보자용 코칭 섹션"""
    st.markdown("---")
    st.markdown("### 🎓 초보자 가이드")

    insights = [
        "✨ KB Reflex에 오신 것을 환영합니다!",
        "📚 체계적인 학습을 통해 현명한 투자자가 되어보세요",
        "🛡️ 위험 관리와 감정 조절이 성공 투자의 핵심입니다"
    ]

    questions = [
        "어떤 투자 목표를 가지고 계신가요?",
        "투자에서 가장 두려운 것은 무엇인가요?"
    ]

    create_mirror_coaching_card(
        "투자 여정을 시작해보세요!",
        insights,
        questions
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 모의 거래하기", key="goto_virtual_trading"):
            try:
                st.switch_page("pages/5_Virtual_Trading.py")
            except Exception:
                st.rerun()

    with col2:
        if st.button("📜 투자 원칙 학습", key="goto_principles"):
            try:
                st.switch_page("pages/4_Investment_Charter.py")
            except Exception:
                st.rerun()

def show_holdings_detail(holdings, market_data):
    """보유 종목 상세"""
    st.markdown("---")
    st.markdown("### 💼 보유 종목 상세")

    for stock, holding in holdings.items():
        if stock in market_data:
            stock_data = market_data[stock]
            current_price = stock_data.current_price
            total_value = holding['shares'] * current_price
            profit_loss = (current_price - holding['avg_price']) * holding['shares']
            profit_loss_pct = (current_price - holding['avg_price']) / holding['avg_price'] * 100

            color = "#14AE5C" if profit_loss >= 0 else "#DC2626"

            st.markdown(f'''
            <div class="premium-card" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: var(--text-primary);">{stock}</h4>
                    <div style="text-align: right;">
                        <div style="font-size: 1.2rem; font-weight: 700; color: {color};">
                            {profit_loss:+,.0f}원 ({profit_loss_pct:+.1f}%)
                        </div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; font-size: 0.9rem;">
                    <div>
                        <div style="color: var(--text-light);">보유수량</div>
                        <div style="font-weight: 600;">{holding['shares']:,}주</div>
                    </div>
                    <div>
                        <div style="color: var(--text-light);">평균단가</div>
                        <div style="font-weight: 600;">{holding['avg_price']:,}원</div>
                    </div>
                    <div>
                        <div style="color: var(--text-light);">현재가</div>
                        <div style="font-weight: 600;">{current_price:,.0f}원</div>
                    </div>
                    <div>
                        <div style="color: var(--text-light);">평가금액</div>
                        <div style="font-weight: 600;">{total_value:,.0f}원</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

def show_recent_trades(recent_trades):
    """최근 거래 내역"""
    st.markdown("---")
    st.markdown("### 📋 최근 거래 내역")

    for trade in recent_trades:
        profit_color = "#14AE5C" if trade['수익률'] >= 0 else "#DC2626"

        st.markdown(f'''
        <div class="trade-item-enhanced">
            <div class="trade-header">
                <div class="trade-stock-name">{trade['종목명']}</div>
                <div class="trade-return {'positive' if trade['수익률'] >= 0 else 'negative'}">
                    {trade['수익률']:+.1f}%
                </div>
            </div>
            <div class="trade-details">
                📅 {trade['거래일시']} • {trade['거래구분']} • {trade['수량']}주
            </div>
            <div class="trade-memo">
                💭 {trade.get('메모', 'N/A')[:100]}
            </div>
        </div>
        ''', unsafe_allow_html=True)

# 메인 실행
show_enhanced_dashboard()

# 자동 새로고침 (개발용)
if st.checkbox("🔄 자동 새로고침 (5초)", value=False):
    time.sleep(5)
    st.rerun()