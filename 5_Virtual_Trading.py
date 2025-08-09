import streamlit as st
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from pathlib import Path
from main_app import SessionKeys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ui_components import apply_toss_css, create_mirror_coaching_card
from db.central_data_manager import (
    get_data_manager, get_market_data, get_user_profile,
    get_user_trading_history, add_user_trade
)

# 페이지 설정
st.set_page_config(
    page_title="KB Reflex - 거래하기",
    page_icon="🛒",
    layout="wide"
)

# Toss 스타일 CSS 적용
apply_toss_css()

# 로그인 확인
if st.session_state.get(SessionKeys.USER) is None:
    st.error("⚠️ 로그인이 필요합니다.")
    if st.button("🏠 홈으로 돌아가기"):
        st.switch_page("main_app.py")
    st.stop()

user = st.session_state[SessionKeys.USER]
username = user['username']

# 포트폴리오 초기화
def initialize_portfolio(username: str, initial_capital=50_000_000):
    """
    거래 기록을 기반으로 포트폴리오를 동적으로 계산합니다.
    이로써 대시보드와 모의 거래 화면의 데이터가 항상 일치하게 됩니다.
    """
    if 'portfolio' not in st.session_state:
        trades_list = get_user_trading_history(username)
        cash = initial_capital
        holdings = {}  # {'종목명': {'shares': 수량, 'avg_price': 평단가}}
        history = []   # 포트폴리오 내부 거래 히스토리

        if trades_list:
            trades_df = pd.DataFrame(trades_list).sort_values(by='거래일시')
            for _, trade in trades_df.iterrows():
                trade_cost = trade['수량'] * trade['가격']
                stock_name = trade['종목명']

                if trade['거래구분'] == '매수':
                    cash -= trade_cost
                    if stock_name in holdings:
                        total_cost = (holdings[stock_name]['avg_price'] * holdings[stock_name]['shares']) + trade_cost
                        total_shares = holdings[stock_name]['shares'] + trade['수량']
                        holdings[stock_name]['avg_price'] = total_cost / total_shares if total_shares > 0 else 0
                        holdings[stock_name]['shares'] = total_shares
                    else:
                        holdings[stock_name] = {'shares': trade['수량'], 'avg_price': trade['가격']}
                elif trade['거래구분'] == '매도':
                    cash += trade_cost
                    if stock_name in holdings:
                        holdings[stock_name]['shares'] -= trade['수량']
                        if holdings[stock_name]['shares'] <= 0:
                            del holdings[stock_name]

                # (선택) 과거 거래를 포트폴리오 history 형식으로 적재
                try:
                    ts = pd.to_datetime(trade['거래일시']).to_pydatetime()
                except Exception:
                    ts = datetime.now()
                history.append({
                    'timestamp': ts,
                    'stock_name': stock_name,
                    'action': 'buy' if trade['거래구분'] == '매수' else 'sell',
                    'shares': int(trade['수량']),
                    'price': float(trade['가격']),
                    'total_amount': float(trade_cost),
                    'emotion': trade.get('감정태그', ''),
                    'memo': trade.get('메모', ''),
                    'confidence': trade.get('확신도', 5),
                    'portfolio_value_after': None
                })

        # ✅ history를 같은 딕셔너리 안에 넣어줍니다
        st.session_state.portfolio = {'cash': cash, 'holdings': holdings, 'history': history}
        # 레거시 접근을 쓰는 코드가 있다면 참고용으로 남겨둠
        st.session_state.history = trades_list

def show_market_overview():
    """시장 현황 개요"""
    st.markdown(f'''
    <div class="main-header-enhanced">
        🛒 {username}님의 가상 거래
    </div>
    <div class="sub-header-enhanced">
        실전과 동일한 환경에서 연습하고 AI 코칭을 받아보세요
    </div>
    ''', unsafe_allow_html=True)
    
    # 라이브 인디케이터
    st.markdown('''
    <div class="live-indicator-enhanced" style="margin-bottom: 2rem;">
        <div class="live-dot-enhanced"></div>
        실시간 시뮬레이션
    </div>
    ''', unsafe_allow_html=True)
    
    # 중앙 데이터 매니저에서 시장 데이터 로드
    market_data = get_market_data(refresh=True)
    
    # 시장 지수 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 경제 지표에서 KOSPI 정보 가져오기
        data_manager = get_data_manager()
        economic_data = data_manager.get_economic_indicators()
        kospi_data = economic_data.get('KOSPI', {})
        
        from utils.ui_components import create_enhanced_metric_card
        create_enhanced_metric_card(
            "KOSPI 지수",
            f"{kospi_data.get('current', 2450):,.0f}",
            f"{kospi_data.get('change_pct', 0):+.2f}%",
            "positive" if kospi_data.get('change_pct', 0) > 0 else "negative"
        )
    
    with col2:
        # 포트폴리오 가치 계산
        portfolio = st.session_state.portfolio
        total_value = portfolio['cash']
        for stock, holding in portfolio['holdings'].items():
            if stock in market_data:
                total_value += holding['shares'] * market_data[stock].current_price
        
        total_return = (total_value - 50000000) / 50000000 * 100
        create_enhanced_metric_card(
            "내 자산",
            f"{total_value:,.0f}원",
            f"{total_return:+.1f}%",
            "positive" if total_return > 0 else "negative"
        )
    
    with col3:
        create_enhanced_metric_card(
            "보유 현금",
            f"{portfolio['cash']:,.0f}원",
            f"{(portfolio['cash']/total_value*100) if total_value else 0:.1f}%"
        )
    
    with col4:
        create_enhanced_metric_card(
            "보유 종목",
            f"{len(portfolio['holdings'])}개",
            "분산 투자" if len(portfolio['holdings']) > 3 else "집중 투자"
        )

def show_stock_list():
    """종목 리스트"""
    st.markdown("### 📈 종목 현황")
    
    # 중앙 데이터 매니저에서 시장 데이터 로드
    market_data = get_market_data(refresh=True)
    
    # 섹터 필터
    col1, col2, col3 = st.columns(3)
    with col1:
        # 모든 섹터 추출
        sectors = list(set([data.sector for data in market_data.values()]))
        sector_filter = st.selectbox(
            "섹터 필터",
            ["전체"] + sectors
        )
    
    with col2:
        sort_option = st.selectbox(
            "정렬 기준",
            ["등락률 높은순", "등락률 낮은순", "거래량 많은순", "가격 높은순", "가격 낮은순"]
        )
    
    with col3:
        st.markdown("#### 🔍 빠른 검색")
        search_query = st.text_input("종목명 검색", placeholder="예: 삼성전자")
    
    # 데이터 필터링 및 정렬
    filtered_data = {}
    for stock, data in market_data.items():
        # 섹터 필터
        if sector_filter != "전체" and data.sector != sector_filter:
            continue
        # 검색 필터
        if search_query and search_query not in stock:
            continue
        filtered_data[stock] = data
    
    # 정렬
    if sort_option == "등락률 높은순":
        filtered_data = dict(sorted(filtered_data.items(), key=lambda x: x[1].change_pct, reverse=True))
    elif sort_option == "등락률 낮은순":
        filtered_data = dict(sorted(filtered_data.items(), key=lambda x: x[1].change_pct))
    elif sort_option == "거래량 많은순":
        filtered_data = dict(sorted(filtered_data.items(), key=lambda x: x[1].volume, reverse=True))
    elif sort_option == "가격 높은순":
        filtered_data = dict(sorted(filtered_data.items(), key=lambda x: x[1].current_price, reverse=True))
    else:  # 가격 낮은순
        filtered_data = dict(sorted(filtered_data.items(), key=lambda x: x[1].current_price))
    
    # 종목 카드 표시
    for stock, data in filtered_data.items():
        show_stock_card(stock, data)

def show_stock_card(stock_name, stock_data):
    """개별 종목 카드"""
    change_color = "#14AE5C" if stock_data.change_pct > 0 else "#DC2626"
    portfolio = st.session_state.portfolio
    
    # 보유 여부 확인
    holding_info = portfolio['holdings'].get(stock_name, {})
    is_holding = len(holding_info) > 0

    # 🔧 중첩 f-string이 Ellipsis를 유발할 수 있어 분리
    holding_html = ""
    if is_holding:
        pnl_pct = ((stock_data.current_price - holding_info['avg_price']) / holding_info['avg_price'] * 100) if holding_info['avg_price'] else 0
        holding_html = f"""
        <div style="background: #F0F9FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
            <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.5rem;">📊 보유 현황</div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; font-size: 0.85rem;">
                <div>
                    <div style="color: var(--text-light);">보유수량</div>
                    <div style="font-weight: 600;">{holding_info['shares']:,}주</div>
                </div>
                <div>
                    <div style="color: var(--text-light);">평균단가</div>
                    <div style="font-weight: 600;">{holding_info['avg_price']:,}원</div>
                </div>
                <div>
                    <div style="color: var(--text-light);">손익률</div>
                    <div style="font-weight: 600; color: {change_color};">
                        {pnl_pct:+.1f}%
                    </div>
                </div>
            </div>
        </div>
        """
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f'''
        <div class="premium-card" style="margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <h4 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                        {stock_name}
                        {('<span style="background: #EBF4FF; color: #3B82F6; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.7rem;">보유중</span>' if is_holding else '')}
                    </h4>
                    <div style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 0.5rem;">
                        {stock_data.sector} • PER {stock_data.per:.1f} • PBR {stock_data.pbr:.2f}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary);">
                        {stock_data.current_price:,.0f}원
                    </div>
                    <div style="color: {change_color}; font-weight: 600; font-size: 1rem;">
                        {stock_data.change:+,.0f}원 ({stock_data.change_pct:+.2f}%)
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; font-size: 0.85rem;">
                <div>
                    <div style="color: var(--text-light);">거래량</div>
                    <div style="font-weight: 600;">{stock_data.volume:,}</div>
                </div>
                <div>
                    <div style="color: var(--text-light);">5일 평균</div>
                    <div style="font-weight: 600;">{stock_data.ma5:,.0f}원</div>
                </div>
                <div>
                    <div style="color: var(--text-light);">20일 평균</div>
                    <div style="font-weight: 600;">{stock_data.ma20:,.0f}원</div>
                </div>
                <div>
                    <div style="color: var(--text-light);">RSI</div>
                    <div style="font-weight: 600; color: {'#DC2626' if stock_data.rsi > 70 else '#14AE5C' if stock_data.rsi < 30 else 'var(--text-primary)'};">
                        {stock_data.rsi:.0f}
                    </div>
                </div>
            </div>

            {holding_html}
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        # 매수/매도 버튼
        if st.button(f"🛒 매수", key=f"buy_{stock_name}", use_container_width=True, type="primary"):
            st.session_state.selected_stock = stock_name
            st.session_state.selected_action = "buy"
            st.session_state.stock_data = stock_data
            st.rerun()
        
        if is_holding:
            if st.button(f"💰 매도", key=f"sell_{stock_name}", use_container_width=True):
                st.session_state.selected_stock = stock_name
                st.session_state.selected_action = "sell"
                st.session_state.stock_data = stock_data
                st.rerun()
        
        # AI 코칭 버튼
        if st.button(f"🤖 AI 코칭", key=f"ai_coach_{stock_name}", use_container_width=True):
            show_ai_coaching_for_stock(stock_name, stock_data)

def show_trading_modal():
    """거래 모달"""
    if 'selected_stock' not in st.session_state:
        return
    
    stock_name = st.session_state.selected_stock
    action = st.session_state.selected_action
    stock_data = st.session_state.stock_data
    portfolio = st.session_state.portfolio
    
    # 모달 스타일 헤더
    action_text = "매수" if action == "buy" else "매도"
    action_color = "#14AE5C" if action == "buy" else "#DC2626"
    action_icon = "🛒" if action == "buy" else "💰"
    
    st.markdown(f'''
    <div class="modal-overlay">
        <div class="modal-content">
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">{action_icon}</div>
                <h2 style="color: {action_color}; margin-bottom: 0.5rem;">{stock_name} {action_text}</h2>
                <div style="color: var(--text-secondary);">현재가: {stock_data.current_price:,}원</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 거래 폼
    with st.form(f"trading_form_{stock_name}_{action}"):
        st.markdown(f"### {action_icon} {stock_name} {action_text}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 거래 정보")
            st.info(f"현재가: {stock_data.current_price:,}원")
            
            if action == "buy":
                max_shares = int(portfolio['cash'] * 0.9 / stock_data.current_price) if stock_data.current_price else 0
                max_shares = max(max_shares, 0)
                shares = st.number_input(
                    f"매수 수량 (최대 {max_shares:,}주)",
                    min_value=1,
                    max_value=max_shares if max_shares > 0 else 1,
                    value=min(100, max_shares) if max_shares > 0 else 1,
                    step=10
                )
            else:  # sell
                holding = portfolio['holdings'][stock_name]
                shares = st.number_input(
                    f"매도 수량 (보유: {holding['shares']:,}주)",
                    min_value=1,
                    max_value=holding['shares'],
                    value=holding['shares'],
                    step=10
                )
        
        with col2:
            st.markdown("#### 💰 거래 금액")
            total_amount = shares * stock_data.current_price
            st.metric("총 거래대금", f"{total_amount:,}원")
            
            if action == "buy":
                st.metric("거래 후 현금", f"{portfolio['cash'] - total_amount:,}원")
            else:
                st.metric("거래 후 현금", f"{portfolio['cash'] + total_amount:,}원")
        
        # 감정 및 메모 입력
        st.markdown("#### 🧠 투자 심리 기록")
        col1, col2 = st.columns(2)
        
        with col1:
            emotion = st.selectbox(
                "현재 감정 상태",
                ["#확신", "#불안", "#욕심", "#냉정", "#공포", "#흥분", "#후회"]
            )
        
        with col2:
            confidence = st.slider("투자 확신도", 1, 10, 5)
        
        memo = st.text_area(
            "거래 메모 (판단 근거, 기대하는 점 등)",
            placeholder="예: 기술적 분석 결과 상승 신호 포착. RSI 30 근처에서 반등 기대.",
            height=80
        )
        
        # 제출 버튼
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                f"{action_icon} {action_text} 실행",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            execute_trade(stock_name, action, shares, stock_data.current_price, emotion, memo, confidence)

def execute_trade(stock_name, action, shares, price, emotion, memo, confidence):
    """거래 실행"""
    portfolio = st.session_state.portfolio
    total_amount = shares * price
    
    try:
        if action == "buy":
            # 매수 처리
            if portfolio['cash'] < total_amount:
                st.error("현금이 부족합니다!")
                return
            
            portfolio['cash'] -= total_amount
            
            if stock_name in portfolio['holdings']:
                # 기존 보유 종목 추가 매수
                old_shares = portfolio['holdings'][stock_name]['shares']
                old_avg_price = portfolio['holdings'][stock_name]['avg_price']
                
                new_total_shares = old_shares + shares
                new_avg_price = ((old_shares * old_avg_price) + (shares * price)) / new_total_shares if new_total_shares else price
                
                portfolio['holdings'][stock_name] = {
                    'shares': new_total_shares,
                    'avg_price': new_avg_price
                }
            else:
                # 신규 매수
                portfolio['holdings'][stock_name] = {
                    'shares': shares,
                    'avg_price': price
                }
        
        else:  # sell
            # 매도 처리
            if stock_name not in portfolio['holdings'] or portfolio['holdings'][stock_name]['shares'] < shares:
                st.error("보유 수량이 부족합니다!")
                return
            
            portfolio['cash'] += total_amount
            portfolio['holdings'][stock_name]['shares'] -= shares
            
            # 모든 주식 매도 시 제거
            if portfolio['holdings'][stock_name]['shares'] == 0:
                del portfolio['holdings'][stock_name]
        
        # 거래 기록 저장
        trade_record = {
            'timestamp': datetime.now(),
            'stock_name': stock_name,
            'action': action,
            'shares': shares,
            'price': price,
            'total_amount': total_amount,
            'emotion': emotion,
            'memo': memo,
            'confidence': confidence,
            'portfolio_value_after': calculate_portfolio_value()
        }
        
        # ✅ 항상 존재하도록 initialize에서 보장했지만, 방어 코드 한 줄
        if 'history' not in portfolio:
            portfolio['history'] = []
        portfolio['history'].append(trade_record)
        
        # 중앙 데이터 매니저에 거래 저장 (이거울: 시뮬레이션)
        user_profile = get_user_profile(username)
        if user_profile and user_profile.username == "이거울":
            return_pct = np.random.normal(0, 10)  # 임시 수익률
            
            trade_data = {
                "거래일시": datetime.now().strftime("%Y-%m-%d"),
                "종목명": stock_name,
                "거래구분": "매수" if action == "buy" else "매도",
                "수량": shares,
                "가격": price,
                "수익률": return_pct,
                "감정태그": emotion,
                "메모": memo
            }
            add_user_trade(username, trade_data)
        
        # 성공 메시지
        action_text = "매수" if action == "buy" else "매도"
        st.success(f"✅ {stock_name} {shares:,}주 {action_text} 완료!")
        st.balloons()
        
        # 세션 상태 정리
        for key in ("selected_stock", "selected_action", "stock_data"):
            if key in st.session_state:
                del st.session_state[key]
        
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"거래 실행 중 오류 발생: {str(e)}")

def calculate_portfolio_value():
    """포트폴리오 총 가치 계산"""
    portfolio = st.session_state.portfolio
    market_data = get_market_data()
    
    total_value = portfolio['cash']
    for stock, holding in portfolio['holdings'].items():
        if stock in market_data:
            total_value += holding['shares'] * market_data[stock].current_price
    
    return total_value

def show_ai_coaching_for_stock(stock_name, stock_data):
    """종목별 AI 코칭"""
    st.markdown("---")
    st.markdown(f"### 🤖 {stock_name} AI 투자 코칭")
    
    user_profile = get_user_profile(username)
    
    # 과거 거래 패턴 분석
    if user_profile and user_profile.username != "이거울":
        trades_data = get_user_trading_history(username)
        
        if trades_data:
            trades_df = pd.DataFrame(trades_data)
            stock_trades = trades_df[trades_df['종목명'] == stock_name]
            
            if len(stock_trades) > 0:
                avg_return = stock_trades['수익률'].mean()
                win_rate = (stock_trades['수익률'] > 0).mean() * 100
                most_common_emotion = stock_trades['감정태그'].mode().iloc[0] if len(stock_trades) > 0 else "N/A"
                
                create_mirror_coaching_card(
                    f"{stock_name} 과거 거래 패턴",
                    [
                        f"📊 총 {len(stock_trades)}회 거래, 평균 수익률 {avg_return:.1f}%",
                        f"🎯 승률 {win_rate:.1f}%, 주요 감정: {most_common_emotion}",
                        f"💡 이 종목에 대한 당신만의 패턴이 있습니다"
                    ],
                    [
                        "과거 거래에서 반복되는 패턴이 있나요?",
                        "이번 거래는 과거와 어떻게 다른가요?",
                        "감정적 판단보다 객관적 근거가 충분한가요?"
                    ]
                )
            else:
                create_mirror_coaching_card(
                    f"{stock_name} 첫 거래 가이드",
                    [
                        "🌟 이 종목은 처음 거래하는 종목입니다",
                        f"📈 현재 RSI {stock_data.rsi:.0f}, PER {stock_data.per:.1f}",
                        "🤔 신중한 접근이 필요합니다"
                    ],
                    [
                        "이 종목을 선택한 명확한 이유가 있나요?",
                        "적정 투자 비중을 정했나요?",
                        "손절/익절 계획이 있나요?"
                    ]
                )
    else:
        # 이거울용 일반적인 코칭
        rsi_status = "과매수" if stock_data.rsi > 70 else "과매도" if stock_data.rsi < 30 else "중립"
        
        create_mirror_coaching_card(
            f"{stock_name} 투자 가이드",
            [
                f"📊 기술적 분석: RSI {stock_data.rsi:.0f} ({rsi_status})",
                f"💰 밸류에이션: PER {stock_data.per:.1f}, PBR {stock_data.pbr:.2f}",
                f"📈 추세: 현재가 vs 20일 평균 {((stock_data.current_price - stock_data.ma20) / stock_data.ma20 * 100):+.1f}%"
            ],
            [
                "이 지표들이 당신의 투자 결정에 어떤 의미인가요?",
                "단기 거래인가요, 장기 투자인가요?",
                "전체 포트폴리오에서 적정한 비중일까요?"
            ]
        )

def show_portfolio_summary():
    """포트폴리오 요약"""
    st.markdown("---")
    st.markdown("### 💼 내 포트폴리오")
    
    portfolio = st.session_state.portfolio
    market_data = get_market_data()
    
    if not portfolio['holdings']:
        st.info("💡 아직 보유한 종목이 없습니다. 첫 투자를 시작해보세요!")
        return
    
    total_investment = 0
    total_current_value = 0
    
    for stock, holding in portfolio['holdings'].items():
        if stock in market_data:
            investment = holding['shares'] * holding['avg_price']
            current_value = holding['shares'] * market_data[stock].current_price
            profit_loss = current_value - investment
            profit_loss_pct = (profit_loss / investment) * 100 if investment else 0
            
            total_investment += investment
            total_current_value += current_value
            
            color = "#14AE5C" if profit_loss > 0 else "#DC2626"
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{stock}**")
                st.caption(f"{holding['shares']:,}주 • 평균 {holding['avg_price']:,}원")
            
            with col2:
                st.markdown(f"**{current_value:,}원**")
                st.caption(f"현재 {market_data[stock].current_price:,}원")
            
            with col3:
                st.markdown(f"<span style='color: {color}; font-weight: 600;'>{profit_loss:+,.0f}원</span>", unsafe_allow_html=True)
                st.caption(f"{profit_loss_pct:+.1f}%")
    
    # 전체 수익률
    if total_investment > 0:
        total_profit_loss = total_current_value - total_investment
        total_profit_loss_pct = (total_profit_loss / total_investment) * 100
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("투자원금", f"{total_investment:,}원")
        
        with col2:
            st.metric("평가금액", f"{total_current_value:,}원")
        
        with col3:
            st.metric("손익", f"{total_profit_loss:+,.0f}원", f"{total_profit_loss_pct:+.1f}%")

def show_trading_history():
    """거래 내역"""
    st.markdown("---")
    st.markdown("### 📋 최근 거래 내역")
    
    portfolio = st.session_state.portfolio
    history = portfolio.get('history', [])
    
    if not history:
        st.info("💡 아직 거래 내역이 없습니다.")
        return
    
    # 최근 10개 거래만 표시
    recent_trades = sorted(history, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    for trade in recent_trades:
        action_color = "#14AE5C" if trade['action'] == "buy" else "#DC2626"
        action_icon = "🛒" if trade['action'] == "buy" else "💰"
        action_text = "매수" if trade['action'] == "buy" else "매도"
        
        st.markdown(f'''
        <div class="trade-item-enhanced">
            <div class="trade-header">
                <div class="trade-stock-name">
                    {action_icon} {trade['stock_name']} {action_text}
                </div>
                <div style="color: {action_color}; font-weight: 700;">
                    {trade['shares']:,}주 × {trade['price']:,}원
                </div>
            </div>
            <div class="trade-details">
                📅 {trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} • 총액 {trade['total_amount']:,}원
            </div>
            <div style="margin: 0.5rem 0;">
                <span class="emotion-tag-enhanced emotion-{trade['emotion'].replace('#', '')}">{trade['emotion']}</span>
                <span style="margin-left: 1rem; font-size: 0.85rem; color: var(--text-light);">
                    확신도: {trade['confidence']}/10
                </span>
            </div>
            <div class="trade-memo">
                💭 {trade['memo']}
            </div>
        </div>
        ''', unsafe_allow_html=True)

# 메인 로직
def main():
    # ✅ username 전달해서 TypeError 방지
    initialize_portfolio(username)
    
    # 거래 모달 표시 (우선순위)
    if 'selected_stock' in st.session_state and 'selected_action' in st.session_state:
        show_trading_modal()
        return
    
    # 메인 화면
    show_market_overview()
    show_stock_list()
    show_portfolio_summary()
    show_trading_history()
    
    # 자동 새로고침 옵션
    if st.checkbox("🔄 실시간 업데이트 (10초)", value=True):
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()
