# pages/stock_trading.py
"""
종목 상세 및 거래 페이지 (Streamlit 공식 멀티페이지)
- 거래 실행 후 즉시 복기 가능하도록 버튼 추가
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import time
import sys
import os

# 상위 디렉토리의 모듈들을 임포트하기 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_service import execute_trade, add_trade_to_history, calculate_expected_pnl, format_currency_smart
from ai_service import check_gemini_api
from ui_components import render_expected_pnl, show_ai_trade_review, show_loss_modal, show_loss_analysis

# 페이지 설정
st.set_page_config(
    page_title="📈 종목 거래 - Re:Mind 3.1",
    page_icon="📈",
    layout="wide"
)

# 세션 상태 확인
if 'market_data' not in st.session_state:
    st.error("데이터가 초기화되지 않았습니다. 메인 페이지에서 시작해주세요.")
    if st.button("🏠 메인 페이지로 이동"):
        st.switch_page("main_app.py")
    st.stop()

# AI 검토 또는 손실 모달이 아닐 경우에만 페이지 내용 표시
if not st.session_state.get('show_ai_review', False) and not st.session_state.get('show_loss_modal', False) and not st.session_state.get('show_loss_analysis', False):
    st.markdown('<h1 style="font-size: 28px; font-weight: 800; color: #191919; margin-bottom: 8px;">📈 종목 상세 및 거래</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 16px; color: #505967; margin-bottom: 32px;">실시간 시세 확인 및 모의 거래를 진행하세요</p>', unsafe_allow_html=True)

    # 실시간 업데이트를 위한 자동 새로고침 설정
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True

    # 자동 새로고침 토글
    col_refresh1, col_refresh2 = st.columns([1, 4])
    with col_refresh1:
        auto_refresh = st.checkbox("🔄 실시간 업데이트", value=st.session_state.auto_refresh, key="auto_refresh_toggle")
        st.session_state.auto_refresh = auto_refresh

    # 종목 선택
    selected_stock = st.selectbox(
        "거래할 종목을 선택하세요",
        list(st.session_state.market_data.keys()),
        key="stock_selector_trading"
    )

    if selected_stock:
        # 실시간 데이터 업데이트 (시뮬레이션)
        if st.session_state.auto_refresh:
            # ±5% 범위의 가격 변동으로 실시간 업데이트 시뮬레이션
            if 'last_update_time' not in st.session_state or time.time() - st.session_state.last_update_time > 2:
                for stock_name in st.session_state.market_data:
                    old_price = st.session_state.market_data[stock_name]['price']
                    # ±5% 범위의 가격 변동
                    price_change = np.random.uniform(-0.05, 0.05)  # -5% ~ +5%
                    new_price = int(old_price * (1 + price_change))
                    # 최소 가격 보장 (1,000원 이상)
                    new_price = max(new_price, 1000)
                    st.session_state.market_data[stock_name]['price'] = new_price
                    # 등락률도 실제 변동률로 업데이트
                    actual_change = ((new_price - old_price) / old_price) * 100
                    st.session_state.market_data[stock_name]['change'] = actual_change

                st.session_state.last_update_time = time.time()

        stock_data = st.session_state.market_data[selected_stock]

        col1, col2 = st.columns([2, 1])

        with col1:
            # 종목 정보 카드
            st.markdown("### 📊 종목 정보")
            change_symbol = "+" if stock_data['change'] >= 0 else ""
            change_color = "#D91A2A" if stock_data['change'] >= 0 else "#1262D7"

            # 실시간 업데이트 표시
            current_time = datetime.now().strftime("%H:%M:%S")

            st.markdown(f'''
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h2 style="margin: 0; color: #191919;">{selected_stock}</h2>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: 700; color: #191919;">{format_currency_smart(stock_data['price'])}</div>
                        <div style="font-size: 14px; font-weight: 600; color: {change_color};">
                            {change_symbol}{stock_data['change']:.1f}%
                        </div>
                        <div style="font-size: 12px; color: #8B95A1;">업데이트: {current_time}</div>
                    </div>
                </div>
                <div style="background-color: #F8FAFC; padding: 12px; border-radius: 8px;">
                    <strong>📰 관련 뉴스:</strong> {stock_data['news']}
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # 실시간 가격 차트 (최근 30일 데이터)
            st.markdown("### 📈 실시간 가격 차트")

            # 차트 데이터 생성 또는 업데이트
            chart_key = f"chart_data_{selected_stock}"
            if chart_key not in st.session_state:
                # 초기 차트 데이터 생성
                dates = pd.date_range(start=datetime.now().date() - pd.Timedelta(days=29),
                                     end=datetime.now().date(), freq='D')
                base_price = stock_data['price']

                # 30일간의 가격 데이터 생성
                prices = []
                current_price = base_price * 0.95  # 30일 전 가격을 현재 가격의 95%로 설정

                for i in range(len(dates)):
                    daily_change = np.random.normal(0, 0.02)
                    current_price = current_price * (1 + daily_change)
                    prices.append(current_price)

                # 마지막 가격을 현재 가격으로 조정
                prices[-1] = stock_data['price']

                st.session_state[chart_key] = pd.DataFrame({
                    'Date': dates,
                    'Price': prices
                })
            else:
                # 기존 차트 데이터 업데이트 (실시간)
                chart_data = st.session_state[chart_key].copy()
                chart_data.iloc[-1, chart_data.columns.get_loc('Price')] = stock_data['price']
                st.session_state[chart_key] = chart_data

            # 차트 렌더링
            fig = px.line(st.session_state[chart_key], x='Date', y='Price',
                          title=f'{selected_stock} 최근 30일 가격 추이')
            fig.update_traces(line_color='#3182F6', line_width=2)
            fig.update_layout(
                height=300, showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Pretendard", color="#191919"),
                margin=dict(l=0, r=0, t=20, b=0),
                yaxis=dict(tickformat=',.0f', gridcolor='rgba(229, 232, 235, 0.5)'),
                xaxis=dict(gridcolor='rgba(229, 232, 235, 0.5)'),
                title=dict(font=dict(size=16), x=0, xanchor='left')
            )
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{selected_stock}_{current_time}")

        with col2:
            st.markdown("### 💰 거래 실행")

            # 거래 타입 선택
            trade_type = st.selectbox("거래 구분", ["매수", "매도"], key="trade_type_selector")

            # 실시간 예상 손익 계산 및 표시
            placeholder_quantity = st.session_state.get('temp_quantity', 10)

            # 수량 입력을 위한 임시 컨테이너
            quantity_container = st.container()

            with quantity_container:
                temp_quantity = st.number_input("수량 (미리보기)", min_value=1, value=10, step=1,
                                              key="temp_quantity_preview", help="실시간 예상 손익 확인용")

            # 실시간 예상 손익 표시
            if trade_type == "매도":
                expected_pnl = calculate_expected_pnl(selected_stock, trade_type, temp_quantity,
                                                    stock_data['price'], st.session_state.portfolio)
                if expected_pnl:
                    render_expected_pnl(expected_pnl)

            # 거래 폼
            with st.form("trading_form"):
                quantity = st.number_input("수량", min_value=1, value=temp_quantity, step=1, key="form_quantity")
                price = st.number_input("가격", min_value=1000, value=stock_data['price'], step=1000)

                total_amount = quantity * price
                st.markdown(f"**총 거래금액: {format_currency_smart(total_amount)}**")

                col1_form, col2_form = st.columns(2)

                with col1_form:
                    if trade_type == "매수":
                        submit_button = st.form_submit_button("🔴 매수 실행", use_container_width=True, type="primary")
                    else:
                        submit_button = st.form_submit_button("🔵 매도 실행", use_container_width=True, type="secondary")

                with col2_form:
                    ai_review_button = st.form_submit_button("🤖 AI에게 검토받기", use_container_width=True,
                                                           disabled=not check_gemini_api())

                if submit_button:
                    success, message, loss_info, portfolio, cash = execute_trade(
                        selected_stock, trade_type, quantity, price,
                        st.session_state.portfolio, st.session_state.cash
                    )
                    if success:
                        st.session_state.portfolio = portfolio
                        st.session_state.cash = cash
                        st.session_state.history = add_trade_to_history(
                            st.session_state.history, selected_stock, trade_type, quantity, price
                        )
                        
                        # 거래 성공 메시지 표시
                        st.success(message)
                        
                        # ✅ 새로 추가: 거래 완료 후 복기 버튼
                        st.markdown("---")
                        st.markdown("### 🧠 거래 복기하기")
                        st.info("💡 방금 전 거래를 바로 복기해보세요! AI와 함께 거래 결정을 분석할 수 있습니다.")
                        
                        col1_reflect, col2_reflect = st.columns(2)
                        
                        with col1_reflect:
                            if st.button("📝 지금 복기하기", key="reflect_now", use_container_width=True, type="primary"):
                                # 방금 거래한 정보를 세션에 저장
                                st.session_state.last_trade_for_reflection = {
                                    'stock_name': selected_stock,
                                    'trade_type': trade_type,
                                    'quantity': quantity,
                                    'price': price,
                                    'timestamp': datetime.now()
                                }
                                # AI 코칭 페이지로 이동
                                st.switch_page("pages/ai_coaching.py")
                        
                        with col2_reflect:
                            if st.button("⏰ 나중에 복기하기", key="reflect_later", use_container_width=True):
                                st.info("복기는 언제든지 'AI 거래 복기' 페이지에서 할 수 있습니다.")
                        
                        # 손실 발생 시 모달 처리
                        if loss_info:
                            st.session_state.show_loss_modal = True
                            st.session_state.loss_info = loss_info
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

                if ai_review_button:
                    st.session_state.show_ai_review = True
                    st.session_state.pending_trade = {
                        'stock_name': selected_stock,
                        'trade_type': trade_type,
                        'quantity': quantity,
                        'price': price
                    }
                    st.rerun()

            # 실시간 보유 현황 표시
            st.markdown("### 💼 현재 보유 현황")
            holdings_container = st.container()

            with holdings_container:
                if selected_stock in st.session_state.get('portfolio', {}):
                    holdings = st.session_state.portfolio[selected_stock]
                    current_value = holdings['shares'] * stock_data['price']  # 실시간 가격 반영
                    invested_value = holdings['shares'] * holdings['avg_price']
                    pnl = current_value - invested_value
                    pnl_pct = (pnl / invested_value) * 100 if invested_value != 0 else 0
                    pnl_color = "#D91A2A" if pnl >= 0 else "#1262D7"

                    st.markdown(f'''
                    <div class="card">
                        <div><strong>보유 수량:</strong> {holdings['shares']:,}주</div>
                        <div><strong>평균 단가:</strong> {format_currency_smart(holdings['avg_price'])}</div>
                        <div><strong>현재 가치:</strong> {format_currency_smart(current_value)}</div>
                        <div style="color: {pnl_color}; font-weight: 700;">
                            <strong>평가손익:</strong> {format_currency_smart(abs(pnl))} ({pnl_pct:+.1f}%)
                        </div>
                        <div style="font-size: 12px; color: #8B95A1; margin-top: 8px;">
                            실시간 업데이트: {current_time}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.info("현재 보유하지 않은 종목입니다.")

# 모달 처리
if st.session_state.get('show_ai_review', False):
    show_ai_trade_review()
elif st.session_state.get('show_loss_modal', False) and st.session_state.get('loss_info', {}):
    show_loss_modal(st.session_state.loss_info)
elif st.session_state.get('show_loss_analysis', False) and st.session_state.get('loss_info', {}):
    show_loss_analysis(st.session_state.loss_info)

# 실시간 업데이트를 위한 자동 새로고침
if st.session_state.auto_refresh:
    # 모달 창이 아닐 때만 새로고침
    if not any([
        st.session_state.get('show_ai_review', False),
        st.session_state.get('show_loss_modal', False),
        st.session_state.get('show_loss_analysis', False)
    ]):
        time.sleep(2)
        st.rerun()