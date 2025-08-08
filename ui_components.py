# ui_components.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from ai_service import analyze_trade_with_ai, check_api_key
from trading_service import format_currency_smart, calculate_expected_pnl

def render_css():
    """CSS 스타일 렌더링"""
    st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        :root {
            --bg-color: #F2F4F6;
            --sidebar-bg: #FFFFFF;
            --card-bg: #FFFFFF;
            --primary-blue: #3182F6;
            --text-primary: #191919;
            --text-secondary: #505967;
            --text-light: #8B95A1;
            --border-color: #E5E8EB;
            --positive-color: #D91A2A;
            --negative-color: #1262D7;
            --success-color: #14AE5C;
            --warning-color: #FF9500;
        }

        * {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }

        .metric-card {
            background-color: var(--card-bg);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
            text-align: center;
            from datetime import datetime, timedelta
            import time
            from ai_service import analyze_trade_with_ai, check_api_key
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .metric-label {
            font-size: 14px;
            font-weight: 600;
                "render_api_status"
            color: var(--text-light);
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .metric-value.positive {
            color: var(--positive-color);
        }

        .metric-value.negative {
            color: var(--negative-color);
        }

        .card {
            background-color: var(--card-bg);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
        }

        .ai-analysis-card {
            background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%);
            border: 2px solid #3182F6;
            border-radius: 20px;
            padding: 24px;
            margin: 20px 0;
        }

        .ai-analysis-title {
            font-size: 18px;
            font-weight: 700;
            color: var(--primary-blue);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
        }

        .similarity-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
            margin: 4px;
        }

        .similarity-high {
            background-color: #FEE2E2;
            color: #DC2626;
        }

        .similarity-medium {
            background-color: #FEF3C7;
            color: #D97706;
        }

        .similarity-low {
            background-color: #D1FAE5;
            color: #059669;
        }

        .loss-alert {
            background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
            border: 2px solid #F87171;
            border-radius: 16px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }

        .loss-alert-title {
            font-size: 18px;
            font-weight: 700;
            color: #DC2626;
            margin-bottom: 12px;
        }

        .loss-alert-content {
            font-size: 14px;
            color: #7F1D1D;
            margin-bottom: 16px;
        }

        .pnl-preview {
            background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
            border: 1px solid #86EFAC;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
        }

        .pnl-preview.negative {
            background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
            border: 1px solid #F87171;
        }

        .live-indicator {
            display: inline-flex;
            align-items: center;
            font-size: 14px;
            color: var(--success-color);
            font-weight: 600;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success-color);
            border-radius: 50%;
            margin-right: 6px;
            animation: pulse 2s infinite;
        }

        .api-status {
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 16px;
        }

        .api-status.active {
            background-color: #D1FAE5;
            color: #059669;
        }

        .api-status.inactive {
            background-color: #FEE2E2;
            color: #DC2626;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
    """, unsafe_allow_html=True)

def render_api_status():
    """API 키 상태 표시"""
    if check_api_key():
        st.markdown("""
        <div style="background-color: #D1FAE5; color: #059669; padding: 8px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 16px; text-align: center;">
            🟢 AI 기능 활성화됨
        </div>
        """, unsafe_allow_html=True)
        return True
    else:
        st.markdown("""
        <div style="background-color: #FEE2E2; color: #DC2626; padding: 8px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 16px; text-align: center;">
            🔴 AI 기능 비활성화
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🔑 API 키 설정 방법", expanded=False):
            st.markdown("""
            **OpenAI API 키 설정이 필요합니다:**
            
            1. [OpenAI 웹사이트](https://platform.openai.com/api-keys)에서 API 키 생성
            2. 아래 입력창에 API 키 입력
            3. AI 분석 기능 활용
            
            ⚠️ **주의:** API 키는 안전하게 보관하세요!
            """)
            
            api_key = st.text_input(
                "OpenAI API 키 입력", 
                type="password", 
                key="api_key_input",
                placeholder="sk-proj-..."
            )
            
            if st.button("💾 API 키 저장", key="save_api_key", use_container_width=True):
                if api_key and api_key.startswith("sk-"):
                    st.session_state.openai_api_key = api_key
                    st.success("✅ API 키가 저장되었습니다!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                elif api_key:
                    st.error("❌ 올바른 OpenAI API 키 형식이 아닙니다. 'sk-'로 시작해야 합니다.")
                else:
                    st.warning("⚠️ API 키를 입력해주세요.")
        return False

def render_metric_card(label, value, value_type="normal"):
    """메트릭 카드 렌더링"""
    if value_type == "positive":
        value_class = "positive"
    elif value_type == "negative":
        value_class = "negative"
    else:
        value_class = ""
    
    return f'''
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {value_class}">{value}</div>
    </div>
    '''

def render_expected_pnl(expected_pnl_info):
    """예상 손익 표시"""
    if not expected_pnl_info:
        return
    
    pnl = expected_pnl_info['expected_pnl']
    pnl_pct = expected_pnl_info['pnl_percentage']
    
    pnl_class = "" if pnl >= 0 else "negative"
    pnl_sign = "+" if pnl >= 0 else ""
    color = "#059669" if pnl >= 0 else "#DC2626"
    
    st.markdown(f'''
    <div class="pnl-preview {pnl_class}">
        <div style="font-weight: 700; font-size: 16px; color: {color}; margin-bottom: 8px;">
            📈 예상 손익: {pnl_sign}{format_currency_smart(abs(pnl))} ({pnl_pct:+.1f}%)
        </div>
        <div style="font-size: 14px; color: #505967;">
            평균매수가: {format_currency_smart(expected_pnl_info['avg_buy_price'])} → 
            매도가: {format_currency_smart(expected_pnl_info['sell_price'])}
        </div>
    </div>
    ''', unsafe_allow_html=True)

def create_live_chart(chart_data):
    """실시간 차트 생성"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=chart_data['time'],
        y=chart_data['value'],
        mode='lines',
        name='포트폴리오 가치',
        line=dict(color='#3182F6', width=3),
        fill='tonexty',
        fillcolor='rgba(49, 130, 246, 0.1)'
    ))
    
    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="자산 가치 (원)",
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
    
    return fig

def show_charge_modal():
    """자산 충전 모달"""
    st.markdown("### 💰 자산 충전")
    st.write("원하는 금액을 입력하여 가상 자산을 충전할 수 있습니다.")
    
    charge_amount = st.number_input(
        "충전할 금액 (원)",
        min_value=10000,
        max_value=100000000,
        value=1000000,
        step=100000,
        format="%d"
    )
    
    st.markdown(f"**충전 후 잔고**: {format_currency_smart(st.session_state.cash + charge_amount)}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💳 충전하기", key="confirm_charge", use_container_width=True):
            st.session_state.cash += charge_amount
            st.success(f"✅ {format_currency_smart(charge_amount)}이 충전되었습니다!")
            st.balloons()
            st.session_state.show_charge_modal = False
            time.sleep(2)
            st.rerun()
    
    with col2:
        if st.button("❌ 취소", key="cancel_charge", use_container_width=True):
            st.session_state.show_charge_modal = False
            st.rerun()

def show_ai_trade_review():
    """AI 거래 검토 화면"""
    st.markdown("### 🤖 AI 거래 검토")
    
    if st.session_state.pending_trade:
        trade = st.session_state.pending_trade
        
        st.markdown(f'''
        <div class="ai-analysis-card">
            <div class="ai-analysis-title">
                🔍 거래 분석 중...
            </div>
            <div>
                <strong>종목:</strong> {trade['stock_name']}<br>
                <strong>거래유형:</strong> {trade['trade_type']}<br>
                <strong>수량:</strong> {trade['quantity']:,}주<br>
                <strong>가격:</strong> {format_currency_smart(trade['price'])}<br>
                <strong>총액:</strong> {format_currency_smart(trade['quantity'] * trade['price'])}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 예상 손익 표시 (매도인 경우)
        if trade['trade_type'] == "매도":
            expected_pnl = calculate_expected_pnl(
                trade['stock_name'], 
                trade['trade_type'], 
                trade['quantity'], 
                trade['price'], 
                st.session_state.portfolio
            )
            if expected_pnl:
                render_expected_pnl(expected_pnl)
        
        if not st.session_state.user_data.empty:
            with st.spinner("AI가 과거 CSV 거래 데이터와 비교 분석 중..."):
                # AI 분석 실행 (CSV 데이터 사용)
                analysis_result = analyze_trade_with_ai(
                    trade['stock_name'], 
                    trade['trade_type'], 
                    trade['quantity'], 
                    trade['price'],
                    st.session_state.user_data
                )
                
                if analysis_result and 'similar_trades' in analysis_result:
                    similar_trades = analysis_result['similar_trades']
                    
                    if similar_trades:
                        st.markdown("### 📊 유사한 과거 거래 발견")
                        
                        # 상위 5개 유사 거래 표시
                        for i, similar in enumerate(similar_trades[:5], 1):
                            trade_data = similar['trade']
                            similarity = similar['similarity'] * 100
                            
                            # 유사도 등급 결정
                            if similarity >= 70:
                                similarity_class = "similarity-high"
                                similarity_text = "높음"
                            elif similarity >= 50:
                                similarity_class = "similarity-medium"  
                                similarity_text = "보통"
                            else:
                                similarity_class = "similarity-low"
                                similarity_text = "낮음"
                            
                            result_color = "#DC2626" if similar['result'] < 0 else "#059669"
                            
                            result_color = "#DC2626" if similar['result'] < 0 else "#059669"
                            
                            st.markdown(f"""
                            <div style="background-color: #FFFFFF; border-radius: 16px; padding: 20px; margin: 16px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #E5E8EB;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <h4 style="margin: 0; color: #191919;">유사 거래 #{i}</h4>
                                    <span class="similarity-badge {similarity_class}">유사도 {similarity:.0f}% ({similarity_text})</span>
                                </div>
                                
                                <div style="margin-bottom: 12px;">
                                    <strong>📅 거래일:</strong> {similar['date']}<br>
                                    <strong>📊 종목:</strong> {trade_data.get('종목명', 'N/A')} ({trade_data.get('거래구분', 'N/A')})<br>
                                    <strong>💫 감정상태:</strong> {trade_data.get('감정태그', 'N/A')}<br>
                                    <strong style="color: {result_color};">💰 결과:</strong> <span style="color: {result_color};">{similar['result']:+.1f}%</span>
                                </div>
                                
                                <div style="background-color: #F8FAFC; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                                    <strong>🔍 유사한 이유:</strong> {', '.join(similar['reasons'])}
                                </div>
                                
                                <div style="font-size: 14px; color: #505967;">
                                    <strong>📝 당시 메모:</strong> "{trade_data.get('메모', 'N/A')}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # AI 종합 분석 (API 키가 있는 경우)
                        if 'ai_analysis' in analysis_result and analysis_result['ai_analysis']:
                            st.markdown("### 🤖 AI 종합 분석")
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); border: 2px solid #3182F6; border-radius: 20px; padding: 24px; margin: 20px 0;">
                                <div style="font-size: 18px; font-weight: 700; color: #3182F6; margin-bottom: 16px; display: flex; align-items: center;">
                                    💡 AI 조언
                                </div>
                                <div style="line-height: 1.6; color: #505967;">{analysis_result['ai_analysis']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("💡 유사한 과거 거래를 찾을 수 없습니다.")
                else:
                    st.error("AI 분석 중 오류가 발생했습니다.")
        else:
            st.info("💡 CSV 데이터를 기반으로 과거 거래 패턴과 비교 분석합니다.")
        
        # 거래 실행 또는 취소
        col1, col2 = st.columns(2)
        
        with col1:
            button_disabled = not check_api_key() and not st.session_state.user_data.empty
            if st.button("✅ 분석 결과를 반영하여 거래 실행", 
                        key="execute_after_review", 
                        use_container_width=True, 
                        type="primary",
                        disabled=False):  # 항상 실행 가능하도록
                
                from trading_service import execute_trade, add_trade_to_history
                
                success, message, loss_info, portfolio, cash = execute_trade(
                    trade['stock_name'], 
                    trade['trade_type'], 
                    trade['quantity'], 
                    trade['price'],
                    st.session_state.portfolio,
                    st.session_state.cash
                )
                
                if success:
                    st.session_state.portfolio = portfolio
                    st.session_state.cash = cash
                    st.session_state.history = add_trade_to_history(
                        st.session_state.history,
                        trade['stock_name'],
                        trade['trade_type'],
                        trade['quantity'],
                        trade['price']
                    )
                    
                    st.success(message)
                    st.session_state.show_ai_review = False
                    st.session_state.pending_trade = None
                    
                    if loss_info:
                        st.session_state.show_loss_modal = True
                        st.session_state.loss_info = loss_info
                    
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            if st.button("❌ 거래 취소", key="cancel_after_review", use_container_width=True):
                st.session_state.show_ai_review = False
                st.session_state.pending_trade = None
                st.info("거래가 취소되었습니다.")
                time.sleep(1)
                st.rerun()

def show_loss_modal(loss_info):
    """손실 발생 시 오답노트 작성 유도 모달"""
    st.markdown(f'''
    <div class="loss-alert">
        <div class="loss-alert-title">📉 손실이 발생했습니다</div>
        <div class="loss-alert-content">
            <strong>{loss_info['stock_name']}</strong> {loss_info['quantity']:,}주 매도에서<br>
            <strong>{format_currency_smart(loss_info['loss_amount'])} ({loss_info['loss_percentage']:.1f}%)</strong> 손실이 발생했습니다.<br><br>
            매수가: <strong>{format_currency_smart(loss_info['buy_price'])}</strong> → 
            매도가: <strong>{format_currency_smart(loss_info['sell_price'])}</strong>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("### 🤔 오답노트를 작성할까요?")
    st.write("손실 거래를 분석하여 향후 더 나은 투자 결정을 내릴 수 있도록 도와드립니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 네, 오답노트를 작성하겠습니다", key="create_loss_note", use_container_width=True):
            st.session_state.show_loss_analysis = True
            st.session_state.show_loss_modal = False
            st.rerun()
    
    with col2:
        if st.button("❌ 아니요, 다음에 하겠습니다", key="skip_loss_note", use_container_width=True):
            st.info("💡 언제든지 AI 코칭 센터에서 과거 거래를 분석할 수 있습니다.")
            st.session_state.show_loss_modal = False
            st.session_state.loss_info = {}
            time.sleep(1)
            st.rerun()

def show_loss_analysis(loss_info):
    """손실 발생 시 상세 분석 탭"""
    st.markdown(f'''
    <div class="loss-alert">
        <div class="loss-alert-title">📊 손실 거래 상세 분석</div>
        <div class="loss-alert-content">
            <strong>{loss_info['stock_name']}</strong> {loss_info['quantity']:,}주 매도 분석<br>
            손실: <strong>{format_currency_smart(loss_info['loss_amount'])} ({loss_info['loss_percentage']:.1f}%)</strong>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 분석 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📈 기술 분석", "📰 뉴스", "😔 감정", "💬 Comment"])
    
    with tab1:
        st.markdown("#### 📈 기술 분석")
        st.markdown(f"""
        **{loss_info['stock_name']} 기술적 분석 요약:**
        - 매수가: {format_currency_smart(loss_info['buy_price'])}
        - 매도가: {format_currency_smart(loss_info['sell_price'])}
        - 손실률: {loss_info['loss_percentage']:.1f}%
        
        **분석 포인트:**
        - 지지선 이탈로 인한 추가 하락 위험이 있었음
        - 거래량 급증과 함께 매도 압력 증가
        - RSI 지표상 과매도 구간 진입
        """)
    
    with tab2:
        st.markdown("#### 📰 뉴스 분석")
        news_items = [
            f"{loss_info['stock_name']} 실적 전망 하향 조정",
            "업종 전반 투자심리 위축",
            "외국인 투자자 매도세 지속",
            "시장 변동성 확대 우려"
        ]
        
        for i, news in enumerate(news_items, 1):
            st.markdown(f"**{i}.** {news}")
    
    with tab3:
        st.markdown("#### 😔 감정 분석")
        emotions = ["불안", "공포", "후회", "조급함"]
        selected_emotions = st.multiselect(
            "당시 느꼈던 감정을 선택하세요:",
            emotions,
            default=["불안", "후회"]
        )
        
        emotion_intensity = st.slider(
            "감정의 강도 (1-10)",
            min_value=1,
            max_value=10,
            value=7
        )
    
    with tab4:
        st.markdown("#### 💬 Comment")
        user_comment = st.text_area(
            "이번 거래에 대한 생각을 자유롭게 적어주세요:",
            height=150,
            placeholder="예: 너무 성급하게 손절했나 싶다. 뉴스만 보고 판단한 것 같아서 아쉽다...",
            key="loss_comment"
        )
        
        if st.button("📝 오답노트 완성하기", type="primary", use_container_width=True):
            if user_comment.strip():
                from ai_service import ReMinDKoreanEngine
                engine = ReMinDKoreanEngine()
                analysis = engine.analyze_emotion_text(user_comment, st.session_state.current_user)
                
                loss_note = {
                    'timestamp': datetime.now(),
                    'stock_name': loss_info['stock_name'],
                    'loss_amount': loss_info['loss_amount'],
                    'loss_percentage': loss_info['loss_percentage'],
                    'buy_price': loss_info['buy_price'],
                    'sell_price': loss_info['sell_price'],
                    'quantity': loss_info['quantity'],
                    'user_comment': user_comment,
                    'ai_hashtags': [f"#{analysis['pattern']}", f"#{analysis['keywords'][0] if analysis['keywords'] else '감정거래'}"],
                    'emotions': selected_emotions,
                    'emotion_intensity': emotion_intensity
                }
                
                st.session_state.user_loss_notes.append(loss_note)
                
                st.success("✅ 오답노트가 AI 코칭 센터에 추가되었습니다!")
                st.balloons()
                
                st.session_state.show_loss_analysis = False
                st.session_state.show_loss_modal = False
                st.session_state.loss_info = {}
                
                time.sleep(2)
                st.rerun()
            else:
                st.warning("코멘트를 입력해주세요.")
    
    if st.button("⬅️ 뒤로가기", key="back_from_analysis"):
        st.session_state.show_loss_analysis = False
        st.session_state.show_loss_modal = True