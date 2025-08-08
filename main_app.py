# main_app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import time
import warnings

# 모듈 임포트
from data_service import load_user_data_from_csv, initialize_market_data, update_prices
from trading_service import execute_trade, add_trade_to_history, calculate_portfolio_value, get_portfolio_performance, calculate_expected_pnl, format_currency_smart
from ai_service import ReMinDKoreanEngine, generate_ai_coaching_tip, check_api_key
import sys
sys.path.append('.')
from ui_components import (render_css, render_metric_card, create_live_chart, show_charge_modal, 
                          show_ai_trade_review, show_loss_modal, show_loss_analysis, render_api_status, render_expected_pnl)

warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="Re:Mind 3.1 - AI 투자 심리 분석",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def update_chart_data():
    """차트 데이터 업데이트"""
    current_time = datetime.now()
    portfolio_value = st.session_state.cash + calculate_portfolio_value(
        st.session_state.portfolio, 
        st.session_state.market_data
    )
    
    portfolio_value += np.random.normal(0, 50000)
    
    st.session_state.chart_data['time'].append(current_time)
    st.session_state.chart_data['value'].append(portfolio_value)
    
    if len(st.session_state.chart_data['time']) > 30:
        st.session_state.chart_data['time'] = st.session_state.chart_data['time'][-30:]
        st.session_state.chart_data['value'] = st.session_state.chart_data['value'][-30:]

def main():
    initialize_session_state()
    render_css()
    
    # 실시간 가격 업데이트
    current_time = datetime.now()
    if (current_time - st.session_state.last_price_update).seconds >= 1:
        st.session_state.market_data = update_prices(st.session_state.market_data)
        st.session_state.last_price_update = current_time
    
    # 사이드바 네비게이션
    with st.sidebar:
        st.markdown("### 🧠 Re:Mind")
        st.markdown("AI 투자 심리 분석 플랫폼")
        st.markdown("---")
        
        # API 상태 표시
        api_active = render_api_status()
        
        user_type = st.selectbox(
            "사용자 선택",
            ["김국민 (공포매도형)", "박투자 (추격매수형)"],
            key="user_selector_main"
        )
        
        if "김국민" in user_type:
            current_user = "김국민"
        else:
            current_user = "박투자"
        
        if current_user != getattr(st.session_state, 'current_user', None):
            st.session_state.current_user = current_user
            st.session_state.user_data = load_user_data_from_csv(current_user)
        
        st.markdown("---")
        
        page = st.selectbox(
            "페이지 선택",
            ["메인 대시보드", "종목 상세 및 거래", "AI 코칭 센터", "포트폴리오"],
            key="page_selector_main"
        )
        
        st.markdown("---")
        st.markdown("### 💰 현재 잔고")
        st.markdown(f"**현금:** {format_currency_smart(st.session_state.cash)}")
        
        total_stock_value = calculate_portfolio_value(st.session_state.portfolio, st.session_state.market_data)
        st.markdown(f"**주식:** {format_currency_smart(total_stock_value)}")
        st.markdown(f"**총자산:** {format_currency_smart(st.session_state.cash + total_stock_value)}")
        
        if st.button("💳 자산 충전", key="charge_button", use_container_width=True):
            st.session_state.show_charge_modal = True
            st.rerun()
        
        if not st.session_state.history.empty:
            st.markdown("### 📊 최근 거래")
            recent_trades = st.session_state.history.tail(5).iloc[::-1]
            for _, trade in recent_trades.iterrows():
                trade_color = "🔴" if trade['거래구분'] == "매수" else "🔵"
                st.markdown(f"{trade_color} {trade['종목명']} {trade['수량']:,}주")
                st.caption(f"{trade['거래일시'].strftime('%H:%M:%S')} | {format_currency_smart(trade['가격'])}")
    
    # 메인 컨텐츠
    if st.session_state.show_charge_modal:
        show_charge_modal()
    elif st.session_state.show_loss_analysis and st.session_state.loss_info:
        show_loss_analysis(st.session_state.loss_info)
    elif st.session_state.show_loss_modal and st.session_state.loss_info:
        show_loss_modal(st.session_state.loss_info)
    elif st.session_state.show_ai_review and page == "종목 상세 및 거래":
        show_ai_trade_review()
    elif page == "메인 대시보드":
        show_main_dashboard()
    elif page == "종목 상세 및 거래":
        show_stock_trading()
    elif page == "AI 코칭 센터":
        show_ai_coaching()
    elif page == "포트폴리오":
        show_portfolio()

def show_main_dashboard():
    """메인 대시보드 표시"""
    st.markdown(f'<h1 style="font-size: 28px; font-weight: 800; color: #191919; margin-bottom: 8px;">{st.session_state.current_user}님의 투자 대시보드</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 16px; color: #505967; margin-bottom: 32px;">실시간 포트폴리오 현황과 AI 투자 인사이트를 확인하세요</p>', unsafe_allow_html=True)
    
    total_stock_value = calculate_portfolio_value(st.session_state.portfolio, st.session_state.market_data)
    total_assets = st.session_state.cash + total_stock_value
    total_return = ((total_assets - 50_000_000) / 50_000_000) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(render_metric_card("총 자산", format_currency_smart(total_assets)), unsafe_allow_html=True)
    
    with col2:
        st.markdown(render_metric_card("보유 주식", format_currency_smart(total_stock_value)), unsafe_allow_html=True)
    
    with col3:
        st.markdown(render_metric_card("보유 현금", format_currency_smart(st.session_state.cash)), unsafe_allow_html=True)
    
    with col4:
        value_type = "positive" if total_return >= 0 else "negative"
        st.markdown(render_metric_card("총 수익률", f"{total_return:+.2f}%", value_type), unsafe_allow_html=True)
    
    # 실시간 자산 트렌드 차트
    st.markdown("### 📈 실시간 자산 트렌드")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        update_chart_data()
        fig = create_live_chart(st.session_state.chart_data)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown('<div style="display: inline-flex; align-items: center; font-size: 14px; color: #14AE5C; font-weight: 600;"><div style="width: 8px; height: 8px; background-color: #14AE5C; border-radius: 50%; margin-right: 6px; animation: pulse 2s infinite;"></div>실시간 업데이트</div>', unsafe_allow_html=True)
        if st.button("🔄 차트 업데이트", key="update_chart"):
            pass
    
    # 오늘의 AI 코칭 카드
    st.markdown("### 🤖 오늘의 AI 코칭")
    ai_tip = generate_ai_coaching_tip(st.session_state.user_data, st.session_state.current_user)
    
    st.markdown(f'''
    <div style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); border: 1px solid #BFDBFE; border-radius: 20px; padding: 24px; margin-bottom: 24px;">
        <div style="font-size: 18px; font-weight: 700; color: #3182F6; margin-bottom: 12px;">개인화된 투자 인사이트</div>
        <div style="font-size: 15px; color: #505967; line-height: 1.6;">{ai_tip}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 자동 새로고침
    if not any([st.session_state.show_charge_modal, st.session_state.show_loss_modal, 
               st.session_state.show_loss_analysis, st.session_state.show_ai_review]):
        time.sleep(2)
        st.rerun()

def show_stock_trading():
    """종목 상세 및 거래 페이지"""
    st.markdown('<h1 style="font-size: 28px; font-weight: 800; color: #191919; margin-bottom: 8px;">종목 상세 및 거래</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 16px; color: #505967; margin-bottom: 32px;">실시간 시세 확인 및 모의 거래를 진행하세요</p>', unsafe_allow_html=True)
    
    # 종목 선택
    selected_stock = st.selectbox(
        "거래할 종목을 선택하세요",
        list(st.session_state.market_data.keys()),
        key="stock_selector_main"
    )
    
    if selected_stock:
        stock_data = st.session_state.market_data[selected_stock]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 종목 정보 카드
            st.markdown("### 📊 종목 정보")
            
            change_symbol = "+" if stock_data['change'] >= 0 else ""
            change_color = "#D91A2A" if stock_data['change'] >= 0 else "#1262D7"
            
            st.markdown(f'''
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h2 style="margin: 0; color: #191919;">{selected_stock}</h2>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: 700; color: #191919;">{format_currency_smart(stock_data['price'])}</div>
                        <div style="font-size: 14px; font-weight: 600; color: {change_color};">
                            {change_symbol}{stock_data['change']:.1f}%
                        </div>
                    </div>
                </div>
                <div style="background-color: #F8FAFC; padding: 12px; border-radius: 8px;">
                    <strong>📰 관련 뉴스:</strong> {stock_data['news']}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 가격 차트
            st.markdown("### 📈 가격 차트")
            
            # 더미 차트 데이터 생성
            dates = pd.date_range(start='2024-01-01', end='2024-08-05', freq='D')
            base_price = stock_data['price']
            prices = []
            current_price_sim = base_price * 0.8
            
            for _ in dates:
                change = np.random.normal(0, 0.02)
                current_price_sim *= (1 + change)
                prices.append(current_price_sim)
            
            prices[-1] = base_price
            
            chart_df = pd.DataFrame({
                'Date': dates,
                'Price': prices
            })
            
            fig = px.line(chart_df, x='Date', y='Price', title='')
            fig.update_traces(line_color='#3182F6', line_width=2)
            fig.update_layout(
                height=300,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Pretendard", color="#191919"),
                margin=dict(l=0, r=0, t=0, b=0),
                yaxis=dict(
                    tickformat=',.0f',
                    gridcolor='rgba(229, 232, 235, 0.5)'
                ),
                xaxis=dict(
                    gridcolor='rgba(229, 232, 235, 0.5)'
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 거래 인터페이스
            st.markdown("### 💰 거래 실행")
            
            trade_type = st.selectbox("거래 구분", ["매수", "매도"], key="trade_type_selector")
            
            with st.form("trading_form"):
                quantity = st.number_input("수량", min_value=1, value=10, step=1)
                price = st.number_input("가격", min_value=1000, value=stock_data['price'], step=1000)
                
                total_amount = quantity * price
                st.markdown(f"**총 거래금액: {format_currency_smart(total_amount)}**")
                
                # 예상 손익 표시 (매도인 경우)
                if trade_type == "매도":
                    expected_pnl = calculate_expected_pnl(selected_stock, trade_type, quantity, price, st.session_state.portfolio)
                    if expected_pnl:
                        render_expected_pnl(expected_pnl)
                
                col1_form, col2_form = st.columns(2)
                
                with col1_form:
                    if trade_type == "매수":
                        submit_button = st.form_submit_button("🔴 매수 실행", use_container_width=True, type="primary")
                    else:
                        submit_button = st.form_submit_button("🔵 매도 실행", use_container_width=True, type="secondary")
                
                with col2_form:
                    ai_review_button = st.form_submit_button("🤖 AI에게 검토받기", use_container_width=True, disabled=not check_api_key() and st.session_state.user_data.empty)
                
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
                        
                        st.success(message)
                        
                        if loss_info:
                            st.session_state.show_loss_modal = True
                            st.session_state.loss_info = loss_info
                            st.rerun()
                        else:
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error(message)
                
                if ai_review_button:
                    # AI 검토 모드로 전환
                    st.session_state.show_ai_review = True
                    st.session_state.pending_trade = {
                        'stock_name': selected_stock,
                        'trade_type': trade_type,
                        'quantity': quantity,
                        'price': price
                    }
                    st.rerun()
            
            # 현재 보유 현황
            st.markdown("### 💼 현재 보유 현황")
            
            if selected_stock in st.session_state.portfolio:
                holdings = st.session_state.portfolio[selected_stock]
                current_value = holdings['shares'] * stock_data['price']
                invested_value = holdings['shares'] * holdings['avg_price']
                pnl = current_value - invested_value
                pnl_pct = (pnl / invested_value) * 100
                
                pnl_color = "#D91A2A" if pnl >= 0 else "#1262D7"
                
                st.markdown(f'''
                <div class="card">
                    <div><strong>보유 수량:</strong> {holdings['shares']:,}주</div>
                    <div><strong>평균 단가:</strong> {format_currency_smart(holdings['avg_price'])}</div>
                    <div><strong>현재 가치:</strong> {format_currency_smart(current_value)}</div>
                    <div style="color: {pnl_color}; font-weight: 700;">
                        <strong>평가손익:</strong> {format_currency_smart(abs(pnl))} ({pnl_pct:+.1f}%)
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("현재 보유하지 않은 종목입니다.")
    
    # 자동 새로고침 (조건부)
    if not any([st.session_state.show_loss_modal, st.session_state.show_loss_analysis, st.session_state.show_ai_review]):
        time.sleep(1)
        st.rerun()

def show_ai_coaching():
    """AI 코칭 센터 페이지"""
    st.markdown('<h1 style="font-size: 28px; font-weight: 800; color: #191919; margin-bottom: 8px;">AI 코칭 센터</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 16px; color: #505967; margin-bottom: 32px;">과거 거래를 분석하고 개인화된 투자 헌장을 만들어보세요</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 AI 오답노트", "📜 나의 투자 헌장", "⚖️ 투자 원칙"])
    
    with tab1:
        show_ai_post_mortem()
    
    with tab2:
        show_investment_charter()
    
    with tab3:
        show_investment_principles()

def show_ai_post_mortem():
    """AI 오답노트 분석"""
    st.markdown("### 🔍 AI 오답노트 분석")
    
    # 사용자가 작성한 오답노트 표시
    if st.session_state.user_loss_notes:
        st.markdown("#### 📋 작성된 오답노트")
        
        for i, note in enumerate(reversed(st.session_state.user_loss_notes), 1):
            with st.expander(f"오답노트 #{i}: {note['stock_name']} ({note['timestamp'].strftime('%Y-%m-%d %H:%M')})", expanded=False):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"**📊 거래 정보**")
                    st.markdown(f"- 종목: {note['stock_name']}")
                    st.markdown(f"- 수량: {note['quantity']:,}주")
                    st.markdown(f"- 매수가: {format_currency_smart(note['buy_price'])}")
                    st.markdown(f"- 매도가: {format_currency_smart(note['sell_price'])}")
                    st.markdown(f"- 손실: {format_currency_smart(note['loss_amount'])} ({note['loss_percentage']:.1f}%)")
                
                with col2:
                    st.markdown(f"**🤖 AI 분석**")
                    st.markdown(f"- 해시태그: {' '.join(note['ai_hashtags'])}")
                    st.markdown(f"- 감정 상태: {', '.join(note['emotions'])}")
                    st.markdown(f"- 감정 강도: {note['emotion_intensity']}/10")
                
                st.markdown(f"**💬 사용자 코멘트**")
                st.markdown(f'"{note['user_comment']}"')
    
    st.markdown("#### 🔍 과거 손실 거래 분석")
    st.markdown("과거 데이터에서 손실 거래를 선택하여 AI와 함께 분석해보세요")
    
    # 손실 거래 필터링
    user_data = st.session_state.user_data
    if not user_data.empty:
        losing_trades = user_data[user_data['수익률'] < 0].copy()
        
        if len(losing_trades) > 0:
            losing_trades['거래일시'] = pd.to_datetime(losing_trades['거래일시'])
            losing_trades = losing_trades.sort_values('거래일시', ascending=False)
            
            # 거래 선택
            selected_idx = st.selectbox(
                "분석할 손실 거래를 선택하세요",
                losing_trades.index,
                format_func=lambda x: f"{losing_trades.loc[x, '거래일시'].strftime('%Y-%m-%d')} - {losing_trades.loc[x, '종목명']} ({losing_trades.loc[x, '수익률']:.1f}%)",
                key="post_mortem_selector"
            )
            
            selected_trade = losing_trades.loc[selected_idx]
            
            # 객관적 브리핑
            st.markdown("#### 🤖 AI 객관적 브리핑")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border-radius: 16px; padding: 20px; margin: 16px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #E5E8EB;">
                    <h4>📋 거래 상세 정보</h4>
                    <div><strong>거래일:</strong> {selected_trade['거래일시'].strftime('%Y년 %m월 %d일')}</div>
                    <div><strong>종목:</strong> {selected_trade['종목명']} ({selected_trade['종목코드']})</div>
                    <div><strong>거래:</strong> {selected_trade['거래구분']}</div>
                    <div><strong>수량/가격:</strong> {selected_trade['수량']:,}주 / {format_currency_smart(selected_trade['가격'])}</div>
                    <div><strong>감정상태:</strong> {selected_trade['감정태그']}</div>
                    <div style="color: #1262D7; font-weight: 700;"><strong>결과:</strong> {selected_trade['수익률']:.1f}% 손실</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border-radius: 16px; padding: 20px; margin: 16px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #E5E8EB;">
                    <h4>📊 당시 종합 분석 상황</h4>
                    <div style="margin-bottom: 12px;">
                        <strong>📈 기술적 분석:</strong><br>
                        <span style="color: #505967; font-size: 14px; line-height: 1.4;">
                        {selected_trade['기술분석']}<br>
                        • 차트 패턴: 추가 하락 신호 감지<br>
                        • 거래량: 평균 대비 150% 증가<br>
                        • 지지선: {format_currency_smart(selected_trade['가격'] * 0.95)} 예상
                        </span>
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <strong>📰 뉴스/펀더멘털 분석:</strong><br>
                        <span style="color: #505967; font-size: 14px; line-height: 1.4;">
                        {selected_trade['뉴스분석']}<br>
                        • 시장 분위기: 부정적 전망 우세<br>
                        • 업종 동향: 전반적 약세 지속<br>
                        • 외국인 매매: 3일 연속 순매도
                        </span>
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <strong>😔 심리/감정 분석:</strong><br>
                        <span style="color: #505967; font-size: 14px; line-height: 1.4;">
                        {selected_trade['감정분석']}<br>
                        • 투자자 심리지수: 위험 회피 성향<br>
                        • VIX 지수: 높은 변동성 구간<br>
                        • 공포탐욕지수: 극도공포(25) 수준
                        </span>
                    </div>
                    
                    <div style="background: #FEF2F2; padding: 8px; border-radius: 6px; border-left: 3px solid #F87171;">
                        <strong style="color: #DC2626;">⚠️ 종합 위험도:</strong> 
                        <span style="color: #7F1D1D; font-weight: 600;">높음</span><br>
                        <small style="color: #7F1D1D;">기술/뉴스/감정 모든 지표가 부정적 신호</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 사용자 자기반성
            st.markdown("#### ✏️ 사용자 자기반성")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                emotion_selection = st.selectbox(
                    "당시 주요 감정:",
                    ["#공포", "#패닉", "#불안", "#추격매수", "#욕심", "#확신", "#합리적"],
                    key="emotion_selector"
                )
            
            with col2:
                user_reflection = st.text_area(
                    "이 거래에 대한 생각을 기록해주세요:",
                    height=120,
                    placeholder="당시의 결정 과정이나 현재의 생각을 자유롭게 기록해주세요.",
                    key="reflection_text"
                )
            
            # AI 분석 버튼
            ai_analysis_disabled = not check_api_key()
            if st.button("🔍 AI 증거 기반 분석 받기", 
                        type="primary", 
                        use_container_width=True, 
                        disabled=ai_analysis_disabled):
                if user_reflection:
                    st.markdown("#### 🤖 AI 증거 기반 분석")
                    
                    # AI 분석 실행
                    analysis = st.session_state.engine.analyze_emotion_text(user_reflection, st.session_state.current_user)
                    
                    # 증거 제시
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); border: 1px solid #BFDBFE; border-radius: 20px; padding: 24px; margin: 20px 0;">
                        <h4>🔍 발견된 증거</h4>
                        <ul>
                            <li><strong>감정 키워드:</strong> 귀하의 메모에서 '{', '.join(analysis['keywords']) if analysis['keywords'] else '특별한 키워드 없음'}' 등이 발견되었습니다.</li>
                            <li><strong>패턴 분석:</strong> 이 거래는 '{analysis['pattern']}' 패턴과 {analysis['confidence']*100:.0f}% 일치합니다.</li>
                            <li><strong>기술적 요인:</strong> {selected_trade['기술분석']}</li>
                            <li><strong>뉴스 요인:</strong> {selected_trade['뉴스분석']}</li>
                            <li><strong>감정적 요인:</strong> {selected_trade['감정분석']}</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # AI 가이드
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #86EFAC; border-radius: 20px; padding: 24px; margin: 20px 0;">
                        <h4>💡 AI 자기반성 가이드</h4>
                        <p>이러한 증거들을 종합해 볼 때, 이 거래가 '{analysis['pattern']}' 패턴일 가능성을 고려해볼 수 있습니다. 
                        향후 유사한 상황에서는 감정적인 판단을 피하고, 24시간의 냉각기간을 갖는 것을 고려해보세요.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("분석을 위해 생각을 입력해주세요.")
            
            if ai_analysis_disabled:
                st.info("💡 AI 분석 기능을 사용하려면 API 키를 설정해주세요.")
        else:
            st.info("분석할 손실 거래가 없습니다.")
    else:
        st.info("거래 데이터가 없습니다.")

def show_investment_charter():
    """나의 투자 헌장"""
    st.markdown("### 📜 나의 투자 헌장")
    st.markdown("거래 데이터를 기반으로 개인화된 투자 규칙을 생성합니다")
    
    charter_disabled = not check_api_key() and st.session_state.user_data.empty
    if st.button("🎯 투자 헌장 생성하기", type="primary", use_container_width=True, disabled=charter_disabled):
        charter_rules = st.session_state.engine.generate_investment_charter_rules(
            st.session_state.user_data, st.session_state.current_user
        )
        
        if charter_rules:
            st.markdown(f"#### 🎯 {st.session_state.current_user}님만의 개인화된 규칙")
            
            approved_rules = []
            
            for i, rule in enumerate(charter_rules):
                with st.expander(f"규칙 {i+1}: {rule['rule']}", expanded=True):
                    st.markdown(f'''
                    <div style="background-color: #F8FAFC; border-left: 4px solid #3182F6; padding: 16px; margin: 12px 0; border-radius: 0 8px 8px 0;">
                        <div style="font-weight: 700; color: #191919; margin-bottom: 8px;">{rule['rule']}</div>
                        <div style="font-size: 14px; color: #505967; line-height: 1.5;">
                            <strong>📊 근거:</strong> {rule['rationale']}<br>
                            <strong>📈 데이터:</strong> {rule['evidence']}<br>
                            <strong>📂 분류:</strong> {rule['category']}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    if st.checkbox(f"이 규칙을 승인합니다", key=f"approve_rule_{i}"):
                        approved_rules.append(rule)
            
            # 승인된 규칙으로 최종 헌장 생성
            if approved_rules:
                st.markdown("#### ✅ 승인된 투자 헌장")
                
                st.markdown(f'''
                <div style="background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); border: 1px solid #FDBA74; border-radius: 20px; padding: 24px; margin: 20px 0;">
                    <h2 style="text-align: center; margin: 0 0 2rem 0; color: #191919;">📜 {st.session_state.current_user}님의 투자 헌장</h2>
                    <p style="text-align: center; font-style: italic; color: #505967; margin-bottom: 2rem;">2024년 8월 8일 작성</p>
                    
                    <h3 style="color: #191919; margin-bottom: 1rem;">🎯 핵심 원칙</h3>
                ''', unsafe_allow_html=True)
                
                for i, rule in enumerate(approved_rules, 1):
                    st.markdown(f'''
                    <div style="margin: 1rem 0;">
                        <strong>{i}. {rule['rule']}</strong><br>
                        <em style="color: #505967;">→ {rule['rationale']} ({rule['evidence']})</em>
                    </div>
                    ''', unsafe_allow_html=True)
                
                st.markdown(f'''
                    <div style="text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #FDBA74;">
                        <p><strong>서명:</strong> {st.session_state.current_user} &nbsp;&nbsp;&nbsp; <strong>날짜:</strong> 2024년 8월 8일</p>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("충분한 거래 데이터가 없어 투자 헌장을 생성할 수 없습니다.")
    
    if charter_disabled:
        st.info("💡 투자 헌장 생성 기능을 사용하려면 API 키를 설정하거나 거래 데이터가 필요합니다.")

def show_investment_principles():
    """투자 원칙 탭"""
    st.markdown("### ⚖️ AI가 추출한 투자 원칙")
    st.markdown("과거 복기노트를 분석하여 AI가 자동으로 추출한 투자 원칙들입니다")
    
    if not st.session_state.user_data.empty:
        principles = st.session_state.engine.extract_principles_from_notes(st.session_state.user_data)
        
        if principles:
            st.markdown("#### 📋 추출된 투자 원칙")
            
            for i, principle in enumerate(principles, 1):
                # 원칙의 중요도에 따른 색상 결정
                if principle['avg_impact'] > 15:
                    priority_color = "#DC2626"
                    priority_text = "높음"
                    card_style = "border: 2px solid #F87171; background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);"
                elif principle['avg_impact'] > 8:
                    priority_color = "#D97706"
                    priority_text = "보통"
                    card_style = "border: 1px solid #FDBA74; background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);"
                else:
                    priority_color = "#059669"
                    priority_text = "낮음"
                    card_style = "border: 1px solid #86EFAC; background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);"
                
                with st.expander(f"원칙 #{i}: {principle['title']}", expanded=i <= 3):
                    st.markdown(f'''
                    <div style="{card_style} border-radius: 12px; padding: 20px; margin: 16px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <h4 style="margin: 0; color: #191919;">{principle['title']}</h4>
                            <span style="background-color: {priority_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                                우선순위: {priority_text}
                            </span>
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <strong>📊 분석 결과:</strong><br>
                            {principle['description']}
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <strong>📋 제안 규칙:</strong><br>
                            <em>"{principle['rule']}"</em>
                        </div>
                        
                        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #505967;">
                            <span><strong>증거 건수:</strong> {principle['evidence_count']}회</span>
                            <span><strong>평균 영향:</strong> -{principle['avg_impact']:.1f}%</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # 원칙 채택 여부
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ 원칙 #{i} 채택", key=f"adopt_principle_{i}", use_container_width=True):
                            st.success(f"원칙 #{i}이 개인 투자 헌장에 추가되었습니다!")
                            st.balloons()
                    
                    with col2:
                        if st.button(f"❌ 원칙 #{i} 거부", key=f"reject_principle_{i}", use_container_width=True):
                            st.info(f"원칙 #{i}을 거부했습니다.")
        else:
            st.info("아직 충분한 데이터가 없어 투자 원칙을 추출할 수 없습니다. 더 많은 거래를 진행해주세요.")
    else:
        st.info("거래 데이터가 없습니다. 먼저 거래를 진행해주세요.")
    
    # 사용자 직접 원칙 추가
    st.markdown("#### ➕ 나만의 원칙 추가하기")
    
    with st.form("add_custom_principle"):
        custom_title = st.text_input("원칙 제목", placeholder="예: 감정적 상태에서 거래 금지")
        custom_rule = st.text_area("구체적 규칙", placeholder="예: 화가 나거나 흥분한 상태에서는 24시간 거래를 하지 않는다", height=100)
        custom_reason = st.text_area("설정 이유", placeholder="예: 감정적인 상태에서 손실을 많이 봤기 때문", height=100)
        
        if st.form_submit_button("원칙 추가하기", type="primary"):
            if custom_title and custom_rule:
                st.success("나만의 투자 원칙이 추가되었습니다!")
                st.markdown(f'''
                <div style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); border: 1px solid #BFDBFE; border-radius: 12px; padding: 16px; margin: 16px 0;">
                    <h4>{custom_title}</h4>
                    <p><strong>규칙:</strong> {custom_rule}</p>
                    <p><strong>이유:</strong> {custom_reason}</p>
                    <small style="color: #505967;">사용자 정의 원칙 • 추가됨: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.warning("제목과 규칙을 모두 입력해주세요.")

def show_portfolio():
    """포트폴리오 페이지"""
    st.markdown('<h1 style="font-size: 28px; font-weight: 800; color: #191919; margin-bottom: 8px;">포트폴리오</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 16px; color: #505967; margin-bottom: 32px;">현재 보유 종목과 전체 거래 내역을 확인하세요</p>', unsafe_allow_html=True)
    
    # 현재 보유 종목
    st.markdown("### 💼 현재 보유 종목")
    
    if st.session_state.portfolio:
        portfolio_df = get_portfolio_performance(st.session_state.portfolio, st.session_state.market_data)
        st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
    else:
        st.info("현재 보유 중인 종목이 없습니다.")
    
    # 전체 거래 내역
    st.markdown("### 📊 전체 거래 내역")
    
    if not st.session_state.history.empty:
        history_display = st.session_state.history.copy()
        history_display['거래일시'] = pd.to_datetime(history_display['거래일시']).dt.strftime('%Y-%m-%d %H:%M')
        history_display['가격'] = history_display['가격'].apply(lambda x: format_currency_smart(x))
        history_display['금액'] = history_display['금액'].apply(lambda x: format_currency_smart(x))
        
        st.dataframe(history_display, use_container_width=True, hide_index=True)
    else:
        st.info("거래 내역이 없습니다.")
    
    # 과거 거래 데이터 분석
    st.markdown("### 📈 과거 거래 분석")
    
    user_data = st.session_state.user_data
    
    if not user_data.empty:
        # 감정별 성과 분석
        col1, col2 = st.columns(2)
        
        with col1:
            # 감정별 평균 수익률
            emotion_performance = user_data.groupby('감정태그')['수익률'].mean().sort_values()
            
            fig_emotion = px.bar(
                x=emotion_performance.values,
                y=emotion_performance.index,
                orientation='h',
                title="감정별 평균 수익률",
                color=emotion_performance.values,
                color_continuous_scale=['red', 'yellow', 'green']
            )
            
            fig_emotion.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Pretendard", color="#191919"),
                showlegend=False,
                coloraxis_showscale=False
            )
            
            st.plotly_chart(fig_emotion, use_container_width=True)
        
        with col2:
            # 월별 거래 횟수
            user_data['거래월'] = pd.to_datetime(user_data['거래일시']).dt.to_period('M')
            monthly_trades = user_data.groupby('거래월').size()
            
            fig_monthly = px.line(
                x=monthly_trades.index.astype(str),
                y=monthly_trades.values,
                title="월별 거래 횟수",
                markers=True
            )
            
            fig_monthly.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Pretendard", color="#191919"),
                showlegend=False
            )
            
            fig_monthly.update_traces(line_color='#3182F6', marker_color='#3182F6')
            
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # 거래 통계 요약
        st.markdown("### 📊 거래 통계 요약")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_trades = len(user_data)
        avg_return = user_data['수익률'].mean()
        win_rate = len(user_data[user_data['수익률'] > 0]) / len(user_data) * 100
        max_loss = user_data['수익률'].min()
        
        with col1:
            st.markdown(render_metric_card("총 거래 횟수", f"{total_trades}회"), unsafe_allow_html=True)
        
        with col2:
            value_type = "positive" if avg_return >= 0 else "negative"
            st.markdown(render_metric_card("평균 수익률", f"{avg_return:+.1f}%", value_type), unsafe_allow_html=True)
        
        with col3:
            value_type = "positive" if win_rate >= 50 else "negative"
            st.markdown(render_metric_card("승률", f"{win_rate:.0f}%", value_type), unsafe_allow_html=True)
        
        with col4:
            st.markdown(render_metric_card("최대 손실", f"{max_loss:.1f}%", "negative"), unsafe_allow_html=True)
    else:
        st.info("분석할 거래 데이터가 없습니다.")

if __name__ == "__main__":
    main()