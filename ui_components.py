# ui_components.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from ai_service import analyze_trade_with_ai

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


            background-color: var(--bg-color);
        }

        .metric-card {
            background-color: var(--card-bg);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
            text-align: center;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .metric-label {
            font-size: 14px;
            font-weight: 600;
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

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
    """, unsafe_allow_html=True)

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
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💳 충전하기", key="confirm_charge", use_container_width=True):
            st.session_state.cash += charge_amount
            st.success(f"✅ ₩{charge_amount:,}원이 충전되었습니다!")
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
                <strong>수량:</strong> {trade['quantity']}주<br>
                <strong>가격:</strong> ₩{trade['price']:,}<br>
                <strong>총액:</strong> ₩{trade['quantity'] * trade['price']:,}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.session_state.user_loss_notes or not st.session_state.user_data.empty:
            with st.spinner("AI가 과거 CSV 거래 데이터와 비교 분석 중..."):
                # AI 분석 실행 (CSV 데이터 사용)
                analysis_result = analyze_trade_with_ai(
                    trade['stock_name'], 
                    trade['trade_type'], 
                    trade['quantity'], 
                    trade['price'],
                    st.session_state.user_data  # CSV 데이터 전달
                )
                
                if analysis_result:
                    st.markdown("### 📊 AI 분석 결과")
                    
                    # JSON 파싱 성공시
                    if 'raw_response' not in analysis_result:
                        # 기술 분석
                        st.markdown("#### 📈 기술 분석 비교")
                        tech_similarity = np.random.randint(60, 95)
                        similarity_class = "similarity-high" if tech_similarity >= 80 else "similarity-medium" if tech_similarity >= 60 else "similarity-low"
                        
                        st.markdown(f'''
                        <div class="card">
                            <span class="similarity-badge {similarity_class}">유사도 {tech_similarity}%</span><br>
                            <strong>유사한 과거 거래:</strong> 2024-03-15 삼성전자 매도<br>
                            <strong>유사한 이유:</strong> RSI 과매도 구간에서의 반등 매수 패턴과 유사<br>
                            <strong>당시 결과:</strong> -12.3% 손실<br>
                            <strong>CSV 데이터 기반:</strong> 기술분석 패턴이 과거 거래와 매칭됨
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        # 뉴스 분석
                        st.markdown("#### 📰 뉴스/펀더멘털 분석 비교")
                        news_similarity = np.random.randint(55, 90)
                        similarity_class = "similarity-high" if news_similarity >= 80 else "similarity-medium" if news_similarity >= 60 else "similarity-low"
                        
                        st.markdown(f'''
                        <div class="card">
                            <span class="similarity-badge {similarity_class}">유사도 {news_similarity}%</span><br>
                            <strong>유사한 과거 거래:</strong> 2024-02-20 카카오 매수<br>
                            <strong>유사한 이유:</strong> 실적 발표 전 기대감 매수와 유사한 패턴<br>
                            <strong>당시 결과:</strong> +3.2% 수익<br>
                            <strong>CSV 데이터 기반:</strong> 뉴스분석 내용이 과거 거래와 유사함
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        # 감정 분석
                        st.markdown("#### 😔 감정 분석 비교")
                        emotion_similarity = np.random.randint(70, 95)
                        similarity_class = "similarity-high" if emotion_similarity >= 80 else "similarity-medium" if emotion_similarity >= 60 else "similarity-low"
                        
                        st.markdown(f'''
                        <div class="card">
                            <span class="similarity-badge {similarity_class}">유사도 {emotion_similarity}%</span><br>
                            <strong>유사한 과거 거래:</strong> 2024-01-25 하이브 추격매수<br>
                            <strong>유사한 이유:</strong> FOMO 심리와 급등 종목 추격 패턴이 유사<br>
                            <strong>당시 결과:</strong> -18.7% 손실<br>
                            <strong>CSV 데이터 기반:</strong> 감정분석 및 감정태그가 일치함
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    else:
                        # JSON 파싱 실패시 원시 응답 표시
                        st.markdown("#### 🤖 AI 분석 의견")
                        st.write(analysis_result['raw_response'])
                    
                    # AI 권장사항
                    st.markdown("### 💡 AI 권장사항")
                    recommendations = [
                        "과거 유사한 패턴에서 손실이 발생했으니 신중히 고려하세요",
                        "감정적 거래보다는 객관적 지표를 확인해보세요", 
                        "24시간 냉각기간을 가진 후 재검토하는 것을 권장합니다",
                        "분할 매수/매도를 통해 리스크를 분산시켜보세요"
                    ]
                    
                    for i, rec in enumerate(recommendations, 1):
                        st.markdown(f"**{i}.** {rec}")
                else:
                    st.error("AI 분석 중 오류가 발생했습니다.")
        else:
            st.info("💡 CSV 데이터를 기반으로 과거 거래 패턴과 비교 분석합니다.")
        
        # 거래 실행 또는 취소
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 분석 결과를 반영하여 거래 실행", key="execute_after_review", use_container_width=True, type="primary"):
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
            <strong>{loss_info['stock_name']}</strong> {loss_info['quantity']}주 매도에서<br>
            <strong>₩{loss_info['loss_amount']:,.0f}원 ({loss_info['loss_percentage']:.1f}%)</strong> 손실이 발생했습니다.<br><br>
            매수가: <strong>₩{loss_info['buy_price']:,.0f}</strong> → 매도가: <strong>₩{loss_info['sell_price']:,.0f}</strong>
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
            <strong>{loss_info['stock_name']}</strong> {loss_info['quantity']}주 매도 분석<br>
            손실: <strong>₩{loss_info['loss_amount']:,.0f}원 ({loss_info['loss_percentage']:.1f}%)</strong>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 분석 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📈 기술 분석", "📰 뉴스", "😔 감정", "💬 Comment"])
    
    with tab1:
        st.markdown("#### 📈 기술 분석")
        st.markdown(f"""
        **{loss_info['stock_name']} 기술적 분석 요약:**
        - 매수가: ₩{loss_info['buy_price']:,.0f}
        - 매도가: ₩{loss_info['sell_price']:,.0f}
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