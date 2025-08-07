import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from db.user_db import UserDatabase
from utils.ui_components import apply_toss_css, create_metric_card, create_live_chart
from api.market_api import MarketAPI
from ml.ai_briefing import show_ai_briefing_ui

# 페이지 설정
st.set_page_config(
    page_title="KB Reflex - 대시보드",
    page_icon="📊",
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

def initialize_dashboard_session():
    """대시보드 세션 상태 초기화"""
    if 'cash' not in st.session_state:
        st.session_state.cash = 50_000_000
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}
    if 'history' not in st.session_state:
        st.session_state.history = pd.DataFrame(columns=['거래일시', '종목명', '거래구분', '수량', '가격', '금액'])
    if 'market_data' not in st.session_state:
        # Market API를 통한 시장 데이터 초기화
        market_api = MarketAPI()
        st.session_state.market_data = market_api.get_current_market_data()
    if 'chart_data' not in st.session_state:
        # 실시간 차트 데이터 초기화
        base_value = st.session_state.cash
        st.session_state.chart_data = {
            'time': [datetime.now() - timedelta(minutes=i*2) for i in range(30, 0, -1)],
            'value': [base_value + np.random.normal(0, 100000) for _ in range(30)]
        }
    if 'last_price_update' not in st.session_state:
        st.session_state.last_price_update = datetime.now()

def update_prices():
    """실시간 가격 업데이트 (3초마다)"""
    current_time = datetime.now()
    if (current_time - st.session_state.last_price_update).seconds >= 3:
        for stock_name in st.session_state.market_data:
            # ±2% 범위 내에서 랜덤 변동
            change = np.random.normal(0, 0.02)
            new_price = max(1000, int(st.session_state.market_data[stock_name]['price'] * (1 + change)))
            st.session_state.market_data[stock_name]['price'] = new_price
            st.session_state.market_data[stock_name]['change'] = np.random.normal(0, 3)
        
        st.session_state.last_price_update = current_time

def execute_trade(stock_name, action, quantity, price):
    """거래 실행"""
    total_amount = quantity * price
    
    if action == "매수":
        if st.session_state.cash >= total_amount:
            st.session_state.cash -= total_amount
            
            # 포트폴리오 업데이트
            if stock_name in st.session_state.portfolio:
                # 기존 보유 종목의 평균 단가 계산
                existing_shares = st.session_state.portfolio[stock_name]['shares']
                existing_avg_price = st.session_state.portfolio[stock_name]['avg_price']
                
                new_total_shares = existing_shares + quantity
                new_avg_price = ((existing_shares * existing_avg_price) + (quantity * price)) / new_total_shares
                
                st.session_state.portfolio[stock_name] = {
                    'shares': new_total_shares,
                    'avg_price': int(new_avg_price)
                }
            else:
                st.session_state.portfolio[stock_name] = {
                    'shares': quantity,
                    'avg_price': price
                }
            
            # 거래 기록 추가
            new_trade = pd.DataFrame([{
                '거래일시': datetime.now(),
                '종목명': stock_name,
                '거래구분': action,
                '수량': quantity,
                '가격': price,
                '금액': total_amount
            }])
            st.session_state.history = pd.concat([st.session_state.history, new_trade], ignore_index=True)
            
            st.success(f"✅ {stock_name} {quantity}주 매수 완료! (₩{total_amount:,})")
            return True
        else:
            st.error("❌ 보유 현금이 부족합니다.")
            return False
    
    elif action == "매도":
        if stock_name in st.session_state.portfolio and st.session_state.portfolio[stock_name]['shares'] >= quantity:
            st.session_state.cash += total_amount
            
            # 포트폴리오 업데이트
            st.session_state.portfolio[stock_name]['shares'] -= quantity
            
            # 모든 주식을 매도한 경우 포트폴리오에서 제거
            if st.session_state.portfolio[stock_name]['shares'] == 0:
                del st.session_state.portfolio[stock_name]
            
            # 거래 기록 추가
            new_trade = pd.DataFrame([{
                '거래일시': datetime.now(),
                '종목명': stock_name,
                '거래구분': action,
                '수량': quantity,
                '가격': price,
                '금액': total_amount
            }])
            st.session_state.history = pd.concat([st.session_state.history, new_trade], ignore_index=True)
            
            st.success(f"✅ {stock_name} {quantity}주 매도 완료! (₩{total_amount:,})")
            return True
        else:
            st.error("❌ 보유 주식이 부족합니다.")
            return False

def generate_ai_coaching_tip(user_data, username):
    """오늘의 AI 코칭 팁 생성"""
    if user_data is None or len(user_data) == 0:
        return "📊 거래 데이터를 축적하여 개인화된 코칭을 받아보세요."
    
    recent_trades = user_data.tail(5)
    
    # 최근 거래 패턴 분석
    recent_emotions = recent_trades['감정태그'].value_counts()
    avg_recent_return = recent_trades['수익률'].mean()
    
    if username == "김국민":
        if '#공포' in recent_emotions.index or '#패닉' in recent_emotions.index:
            return "⚠️ 최근 공포/패닉 거래가 감지되었습니다. 오늘은 시장을 관찰하고 24시간 후 재검토하세요."
        elif avg_recent_return < -5:
            return "💡 최근 수익률이 저조합니다. 감정적 판단보다는 데이터 기반 분석에 집중해보세요."
        else:
            return "✅ 최근 거래 패턴이 안정적입니다. 현재의 신중한 접근을 유지하세요."
    elif username == "박투자":
        if '#추격매수' in recent_emotions.index or '#욕심' in recent_emotions.index:
            return "⚠️ 최근 추격매수 패턴이 감지되었습니다. 오늘은 FOMO를 경계하고 냉정한 판단을 하세요."
        elif avg_recent_return < -5:
            return "💡 최근 수익률이 저조합니다. 외부 추천보다는 본인만의 투자 원칙을 세워보세요."
        else:
            return "✅ 최근 거래가 개선되고 있습니다. 현재의 신중한 접근을 계속 유지하세요."
    else:  # 이거울
        if st.session_state.get('selected_principle'):
            return f"📚 선택하신 '{st.session_state.selected_principle}'의 원칙을 바탕으로 첫 투자를 계획해보세요."
        else:
            return "🌟 새로운 투자 여정의 시작입니다. 신중한 분석과 원칙을 바탕으로 시작해보세요."

def show_trading_interface():
    """거래 인터페이스"""
    st.markdown("### 💰 모의 거래")
    
    # 종목 선택
    available_stocks = list(st.session_state.market_data.keys())
    selected_stock = st.selectbox("거래할 종목 선택", available_stocks)
    
    if selected_stock:
        current_price = st.session_state.market_data[selected_stock]['price']
        current_change = st.session_state.market_data[selected_stock]['change']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("현재가", f"₩{current_price:,}")
        with col2:
            change_color = "normal" if current_change >= 0 else "inverse"
            st.metric("등락률", f"{current_change:+.1f}%", delta=f"{current_change:+.1f}%")
        with col3:
            # 보유 수량 표시
            held_shares = st.session_state.portfolio.get(selected_stock, {}).get('shares', 0)
            st.metric("보유 수량", f"{held_shares:,}주")
        
        # AI 브리핑 버튼
        username = st.session_state.current_user['username']
        
        col1, col2 = st.columns(2)
        with col1:
            action_type = st.selectbox("거래 구분", ["매수", "매도"])
        with col2:
            quantity = st.number_input("수량", min_value=1, max_value=10000, value=10)
        
        # AI 브리핑 표시
        if st.checkbox("🤖 AI 브리핑 보기"):
            show_ai_briefing_ui(username, "005930", selected_stock, action_type)  # 임시 종목코드
        
        # 거래 실행 버튼
        total_amount = quantity * current_price
        
        col1, col2 = st.columns(2)
        
        with col1:
            if action_type == "매수":
                if st.button(f"🔴 {selected_stock} 매수", type="primary", use_container_width=True):
                    if execute_trade(selected_stock, "매수", quantity, current_price):
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                st.caption(f"필요 금액: ₩{total_amount:,}")
        
        with col2:
            if action_type == "매도":
                if st.button(f"🔵 {selected_stock} 매도", type="secondary", use_container_width=True):
                    if execute_trade(selected_stock, "매도", quantity, current_price):
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                st.caption(f"예상 수익: ₩{total_amount:,}")

def show_dashboard():
    """메인 대시보드 표시"""
    user_info = st.session_state.current_user
    username = user_info['username']
    user_type = user_info['user_type']
    
    # 대시보드 헤더
    st.markdown(f'''
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <div>
            <h1 class="main-header">{username}님의 투자 대시보드</h1>
            <p class="sub-header">실시간 포트폴리오 현황과 AI 투자 인사이트를 확인하세요</p>
        </div>
        <div class="live-indicator">
            <div class="live-dot"></div>
            실시간 업데이트
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 포트폴리오 요약 메트릭
    total_stock_value = sum([
        holdings['shares'] * st.session_state.market_data.get(stock, {'price': 50000})['price']
        for stock, holdings in st.session_state.portfolio.items()
    ])
    total_assets = st.session_state.cash + total_stock_value
    total_return = ((total_assets - 50_000_000) / 50_000_000) * 100
    
    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card("총 자산", f"₩ {total_assets:,.0f}", "")
    
    with col2:
        create_metric_card("보유 주식", f"₩ {total_stock_value:,.0f}", "")
    
    with col3:
        create_metric_card("보유 현금", f"₩ {st.session_state.cash:,.0f}", "")
    
    with col4:
        return_class = "positive" if total_return >= 0 else "negative"
        create_metric_card("총 수익률", f"{total_return:+.2f}%", return_class)
    
    # 실시간 자산 트렌드 차트
    st.markdown("### 📈 실시간 자산 트렌드")
    col1, col2 = st.columns([4, 1])
    
    with col1:
        chart_container = st.empty()
    
    with col2:
        if st.button("🔄 차트 업데이트", key="update_chart"):
            pass  # 차트는 자동으로 업데이트됨
    
    # 실시간 차트 생성 및 표시
    with chart_container.container():
        fig = create_live_chart(st.session_state.chart_data, st.session_state.cash, st.session_state.portfolio, st.session_state.market_data)
        st.plotly_chart(fig, use_container_width=True)
    
    # 사용자 데이터 로드 (AI 코칭용)
    user_db = UserDatabase()
    user_trades_data = None
    
    if username in ["김국민", "박투자"]:
        user_trades_data = user_db.get_user_trades(username)
    
    # 오늘의 AI 코칭 카드
    st.markdown("### 🤖 오늘의 AI 코칭")
    ai_tip = generate_ai_coaching_tip(user_trades_data, username)
    
    st.markdown(f'''
    <div class="ai-coaching-card">
        <div class="ai-coaching-title">개인화된 투자 인사이트</div>
        <div class="ai-coaching-content">{ai_tip}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 거래 인터페이스와 포트폴리오 표시
    col1, col2 = st.columns([1, 1])
    
    with col1:
        show_trading_interface()
    
    with col2:
        # 현재 보유 종목 (있는 경우에만 표시)
        if st.session_state.portfolio:
            st.markdown("### 💼 현재 보유 종목")
            
            portfolio_data = []
            for stock_name, holdings in st.session_state.portfolio.items():
                current_price = st.session_state.market_data.get(stock_name, {'price': 50000})['price']
                current_change = st.session_state.market_data.get(stock_name, {'change': 0})['change']
                current_value = holdings['shares'] * current_price
                invested_value = holdings['shares'] * holdings['avg_price']
                pnl = current_value - invested_value
                pnl_pct = (pnl / invested_value) * 100 if invested_value > 0 else 0
                
                portfolio_data.append({
                    '종목명': stock_name,
                    '보유수량': f"{holdings['shares']:,}주",
                    '평균매수가': f"₩{holdings['avg_price']:,}",
                    '현재가': f"₩{current_price:,}",
                    '등락률': f"{current_change:+.1f}%",
                    '평가금액': f"₩{current_value:,}",
                    '평가손익': f"₩{pnl:,} ({pnl_pct:+.1f}%)"
                })
            
            portfolio_df = pd.DataFrame(portfolio_data)
            st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
        else:
            st.info("💡 아직 보유 종목이 없습니다. 첫 투자를 시작해보세요!")
    
    # 최근 거래 내역 (있는 경우에만 표시)
    if not st.session_state.history.empty:
        st.markdown("### 📊 최근 거래 내역")
        recent_trades = st.session_state.history.tail(5).iloc[::-1]  # 최근 5개, 역순
        
        for _, trade in recent_trades.iterrows():
            trade_color = "🔴" if trade['거래구분'] == "매수" else "🔵"
            st.markdown(f'''
            <div class="trade-item">
                <div class="trade-info">
                    <div class="trade-stock-name">{trade_color} {trade['종목명']}</div>
                    <div class="trade-details">{trade['거래일시'].strftime('%Y-%m-%d %H:%M:%S')} | {trade['수량']}주</div>
                </div>
                <div class="trade-amount {'buy' if trade['거래구분'] == '매수' else 'sell'}">
                    ₩{trade['금액']:,}
                </div>
            </div>
            ''', unsafe_allow_html=True)

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
    
    st.sidebar.markdown("📊 **대시보드** ← 현재 위치")
    
    if st.sidebar.button("📝 거래 복기", use_container_width=True):
        st.switch_page("pages/2_Trade_Review.py")
    
    if st.sidebar.button("🤖 AI 코칭", use_container_width=True):
        st.switch_page("pages/3_AI_Coaching.py")
    
    if st.sidebar.button("📜 투자 헌장", use_container_width=True):
        st.switch_page("pages/4_Investment_Charter.py")
    
    # 사이드바에 실시간 잔고 표시
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 현재 잔고")
    st.sidebar.markdown(f"**현금:** ₩{st.session_state.cash:,}")
    
    total_stock_value = sum([
        holdings['shares'] * st.session_state.market_data.get(stock, {'price': 50000})['price']
        for stock, holdings in st.session_state.portfolio.items()
    ])
    st.sidebar.markdown(f"**주식:** ₩{total_stock_value:,}")
    st.sidebar.markdown(f"**총자산:** ₩{st.session_state.cash + total_stock_value:,}")

def main():
    """메인 함수"""
    initialize_dashboard_session()
    update_prices()
    
    # 사이드바에 사용자 정보 및 네비게이션 표시
    show_user_switcher_sidebar()
    
    # 메인 대시보드 표시
    show_dashboard()
    
    # 자동 새로고침 (5초마다)
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()