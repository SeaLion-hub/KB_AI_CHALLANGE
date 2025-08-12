# main_app.py (KB 테마 적용 + Streamlit 공식 멀티페이지 사용)
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings

warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="Re:Mind 3.1 - KB AI 투자 심리 분석",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 모든 모듈을 직접 임포트
try:
    # 데이터 서비스
    from data_service import (load_user_data_from_csv, initialize_market_data, update_prices,
                             add_dummy_trading_history, get_loss_trade_scenarios)

    # 거래 서비스
    from trading_service import execute_trade, add_trade_to_history, calculate_portfolio_value, format_currency_smart

    # AI 서비스
    from ai_service import ReMinDKoreanEngine, generate_ai_coaching_tip, check_gemini_api, test_gemini_connection

    # UI 컴포넌트 (KB 테마 포함)
    from ui_components import (render_css, render_gemini_status, show_charge_modal, show_ai_trade_review,
                              show_loss_modal, show_loss_analysis, show_gemini_coaching_card,
                              render_metric_card, create_live_chart, apply_kb_theme)

except ImportError as e:
    st.error(f"🚨 필수 모듈 import 오류: {e}")
    st.error("다음을 확인해주세요:")
    st.error("1. 모든 .py 파일이 같은 디렉토리에 있는지")
    st.error("2. `pip install google-generativeai scikit-learn` 실행했는지")
    st.stop()

# KB 테마 적용 (앱 전체에 일관된 스타일 적용)
apply_kb_theme()

def initialize_session_state():
    """세션 상태 초기화"""
    if 'cash' not in st.session_state:
        st.session_state.cash = 50_000_000
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}
    if 'history' not in st.session_state:
        st.session_state.history = pd.DataFrame(columns=['거래일시', '종목명', '거래구분', '수량', '가격', '금액'])
    if 'market_data' not in st.session_state:
        st.session_state.market_data = initialize_market_data()
    if 'user_data' not in st.session_state:
        st.session_state.user_data = load_user_data_from_csv("김국민")
    if 'engine' not in st.session_state:
        st.session_state.engine = ReMinDKoreanEngine()
    if 'chart_data' not in st.session_state:
        base_value = st.session_state.cash
        st.session_state.chart_data = {
            'time': [datetime.now() - timedelta(minutes=i*2) for i in range(30, 0, -1)],
            'value': [base_value + np.random.normal(0, 100000) for _ in range(30)]
        }
    if 'last_price_update' not in st.session_state:
        st.session_state.last_price_update = datetime.now()
    if 'show_loss_modal' not in st.session_state:
        st.session_state.show_loss_modal = False
    if 'loss_info' not in st.session_state:
        st.session_state.loss_info = {}
    if 'show_charge_modal' not in st.session_state:
        st.session_state.show_charge_modal = False
    if 'show_loss_analysis' not in st.session_state:
        st.session_state.show_loss_analysis = False
    if 'user_loss_notes' not in st.session_state:
        st.session_state.user_loss_notes = []
    if 'show_ai_review' not in st.session_state:
        st.session_state.show_ai_review = False
    if 'pending_trade' not in st.session_state:
        st.session_state.pending_trade = None
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "김국민"

    # 더미 거래 데이터 추가 (한 번만 실행)
    if 'dummy_data_loaded' not in st.session_state:
        add_dummy_trading_history()

        # AI 코칭용 손실 노트도 미리 생성
        loss_scenarios = get_loss_trade_scenarios()
        for scenario in loss_scenarios:
            loss_note = {
                'timestamp': scenario['date'],
                'stock_name': scenario['stock_name'],
                'loss_amount': scenario['loss_amount'],
                'loss_percentage': scenario['loss_percentage'],
                'buy_price': scenario['buy_price'],
                'sell_price': scenario['sell_price'],
                'quantity': scenario['quantity'],
                'user_comment': scenario['memo'],
                'ai_hashtags': [scenario['emotion'], '#손실거래'],
                'emotions': ['후회', '불안'],
                'emotion_intensity': 7,
                'gemini_insight': f"이 거래는 {scenario['emotion']} 상태에서 이루어진 전형적인 감정적 거래입니다."
            }
            st.session_state.user_loss_notes.append(loss_note)

        st.session_state.dummy_data_loaded = True

def render_sidebar():
    """사이드바 렌더링 (Streamlit 공식 멀티페이지 사용)"""
    with st.sidebar:
        # KB 브랜드 로고 섹션
        st.markdown("""
        <div style="text-align: center; padding: 20px 0; background: linear-gradient(135deg, #FFCC00 0%, #FFD700 100%); 
                   border-radius: 12px; margin-bottom: 20px; color: #1c1c1c;">
            <h2 style="margin: 0; font-weight: 800; color: #1c1c1c;">🏦 KB Re:Mind 3.1</h2>
            <p style="margin: 5px 0 0 0; font-size: 14px; font-weight: 600; color: #333;">AI 투자 심리 분석 플랫폼</p>
        </div>
        """, unsafe_allow_html=True)

        # Streamlit 공식 페이지 네비게이션
        st.markdown("### 📍 페이지 이동")
        st.markdown("사이드바에서 페이지를 선택하세요 ↑")

        st.markdown("---")

        # Gemini API 상태 표시
        gemini_connected = render_gemini_status()

        # 사용자 선택
        user_type = st.selectbox(
            "👤 사용자 선택",
            ["김국민 (공포매도형)", "박투자 (추격매수형)"],
            key="user_selector_main"
        )

        current_user = "김국민" if "김국민" in user_type else "박투자"

        if current_user != st.session_state.current_user:
            st.session_state.current_user = current_user
            st.session_state.user_data = load_user_data_from_csv(current_user)
            
        # AI 기능 상태 표시
        if gemini_connected:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FFCC00 0%, #FFD700 100%);
                       color: #1c1c1c; padding: 12px; border-radius: 12px; text-align: center; margin-bottom: 16px;">
                <strong>🚀 KB AI 기능 활성화</strong><br>
                <small>• 거래 패턴 분석<br>• 개인화된 코칭<br>• 심리 상태 진단</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #666666 0%, #888888 100%);
                       color: white; padding: 12px; border-radius: 12px; text-align: center; margin-bottom: 16px;">
                <strong>⚠️ AI 기능 대기 중</strong><br>
                <small>Gemini API 연결 필요</small>
            </div>
            """, unsafe_allow_html=True)

        # 잔고 표시
        st.markdown("### 💰 현재 잔고")
        total_stock_value = calculate_portfolio_value(st.session_state.portfolio, st.session_state.market_data)

        # KB 스타일 잔고 카드
        balance_html = f"""
        <div style="background: linear-gradient(135deg, #2c2c2c 0%, #1c1c1c 100%); 
                   border: 2px solid #FFCC00; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <div style="color: #FFCC00; font-weight: 700; margin-bottom: 8px;">현금</div>
            <div style="color: #f0f0f0; font-size: 16px; font-weight: 600;">{format_currency_smart(st.session_state.cash)}</div>
            
            <div style="color: #FFCC00; font-weight: 700; margin: 12px 0 8px 0;">보유 주식</div>
            <div style="color: #f0f0f0; font-size: 16px; font-weight: 600;">{format_currency_smart(total_stock_value)}</div>
            
            <div style="color: #FFCC00; font-weight: 700; margin: 12px 0 8px 0;">총 자산</div>
            <div style="color: #FFCC00; font-size: 18px; font-weight: 700;">{format_currency_smart(st.session_state.cash + total_stock_value)}</div>
        </div>
        """
        st.markdown(balance_html, unsafe_allow_html=True)

        if st.button("💳 자산 충전", key="charge_button", use_container_width=True):
            st.session_state.show_charge_modal = True
            st.rerun()

        # 최근 거래
        if not st.session_state.history.empty:
            st.markdown("### 📊 최근 거래")
            recent_trades = st.session_state.history.tail(3).iloc[::-1]
            for _, trade in recent_trades.iterrows():
                emoji = "🔴" if trade['거래구분'] == "매수" else "🔵"
                trade_html = f"""
                <div style="background: #2c2c2c; border-left: 3px solid #FFCC00; 
                           padding: 8px 12px; margin: 4px 0; border-radius: 0 8px 8px 0;">
                    <div style="color: #FFCC00; font-weight: 600;">{emoji} {trade['종목명']} {trade['수량']:,}주</div>
                    <div style="color: #f0f0f0; font-size: 12px;">
                        {trade['거래일시'].strftime('%H:%M:%S')} | {format_currency_smart(trade['가격'])}
                    </div>
                </div>
                """
                st.markdown(trade_html, unsafe_allow_html=True)

        # Gemini AI 퀵 분석
        if gemini_connected:
            st.markdown("---")
            st.markdown("### 🤖 KB AI 퀵 체크")

            if st.button("💡 지금 거래해도 될까?", key="quick_ai_check", use_container_width=True):
                from ai_service import analyze_trading_psychology

                quick_context = f"{current_user}님이 지금 거래를 고민하고 있습니다."

                with st.spinner("KB AI 분석 중..."):
                    quick_advice = analyze_trading_psychology(
                        quick_context,
                        st.session_state.user_data,
                        current_user
                    )

                    # 간단한 요약만 표시
                    if '위험' in quick_advice or '높음' in quick_advice:
                        st.error("⚠️ 현재 거래 위험도가 높습니다")
                    elif '좋음' in quick_advice or '낮음' in quick_advice:
                        st.success("✅ 현재 거래하기 좋은 상태입니다")
                    else:
                        st.info("💡 신중하게 접근하세요")

def show_main_dashboard():
    """메인 대시보드 표시"""
    # KB 스타일 헤더
    header_html = f"""
    <div style="background: linear-gradient(135deg, #FFCC00 0%, #FFD700 100%); 
               padding: 24px; border-radius: 16px; margin-bottom: 24px; text-align: center;">
        <h1 style="margin: 0; color: #1c1c1c; font-size: 32px; font-weight: 800;">
            🏦 {st.session_state.current_user}님의 KB AI 대시보드
        </h1>
        <p style="margin: 8px 0 0 0; color: #333; font-size: 16px; font-weight: 600;">
            KB 금융그룹과 함께하는 스마트 투자 관리
        </p>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    total_stock_value = calculate_portfolio_value(st.session_state.portfolio, st.session_state.market_data)
    total_assets = st.session_state.cash + total_stock_value
    total_return = ((total_assets - 50_000_000) / 50_000_000) * 100

    # KB 스타일 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    metrics_data = [
        ("총 자산", format_currency_smart(total_assets), "#FFCC00"),
        ("보유 주식", format_currency_smart(total_stock_value), "#f0f0f0"),
        ("보유 현금", format_currency_smart(st.session_state.cash), "#f0f0f0"),
        ("총 수익률", f"{total_return:+.2f}%", "#00ff88" if total_return >= 0 else "#ff4444")
    ]
    
    for col, (label, value, color) in zip([col1, col2, col3, col4], metrics_data):
        with col:
            metric_html = f"""
            <div style="background: linear-gradient(135deg, #2c2c2c 0%, #1c1c1c 100%); 
                       border: 2px solid #FFCC00; border-radius: 12px; padding: 20px; 
                       text-align: center; height: 120px; display: flex; 
                       flex-direction: column; justify-content: center;">
                <div style="color: #FFCC00; font-size: 14px; font-weight: 600; margin-bottom: 8px;">
                    {label}
                </div>
                <div style="color: {color}; font-size: 24px; font-weight: 700;">
                    {value}
                </div>
            </div>
            """
            st.markdown(metric_html, unsafe_allow_html=True)

    # Gemini AI 코칭 카드 (KB 스타일)
    show_gemini_coaching_card(st.session_state.user_data, st.session_state.current_user)

def main():
    initialize_session_state()
    render_css()

    # 실시간 가격 업데이트
    current_time = datetime.now()
    if (current_time - st.session_state.last_price_update).seconds >= 2:
        st.session_state.market_data = update_prices(st.session_state.market_data)
        st.session_state.last_price_update = current_time

    # 사이드바 렌더링
    render_sidebar()

    # 모달 처리 (자산 충전 모달만 남김)
    if st.session_state.get('show_charge_modal', False):
        show_charge_modal()
    else:
        show_main_dashboard()

    # 자동 새로고침 (모달 창이 열려있지 않을 때만)
    if not any([
        st.session_state.get('show_charge_modal', False),
        st.session_state.get('show_loss_modal', False),
        st.session_state.get('show_loss_analysis', False),
        st.session_state.get('show_ai_review', False)
    ]):
        time.sleep(2)
        st.rerun()

if __name__ == "__main__":
    main()