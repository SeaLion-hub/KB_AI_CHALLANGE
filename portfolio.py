# pages/portfolio.py
"""
포트폴리오 페이지 (Streamlit 공식 멀티페이지)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# 상위 디렉토리의 모듈들을 임포트하기 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_service import get_portfolio_performance, format_currency_smart
from ui_components import render_metric_card

# 페이지 설정
st.set_page_config(
    page_title="💼 포트폴리오 - Re:Mind 3.1",
    page_icon="💼",
    layout="wide"
)

st.markdown('<h1 style="font-size: 28px; font-weight: 800; color: #191919; margin-bottom: 8px;">💼 포트폴리오</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 16px; color: #505967; margin-bottom: 32px;">현재 보유 종목과 전체 거래 내역을 확인하세요</p>', unsafe_allow_html=True)

# 세션 상태 확인
if 'portfolio' not in st.session_state:
    st.error("데이터가 초기화되지 않았습니다. 메인 페이지에서 시작해주세요.")
    if st.button("🏠 메인 페이지로 이동"):
        st.switch_page("main_app.py")
    st.stop()

# 현재 보유 종목
st.markdown("### 💼 현재 보유 종목")

if st.session_state.portfolio:
    try:
        portfolio_df = get_portfolio_performance(st.session_state.portfolio, st.session_state.market_data)
        if not portfolio_df.empty:
            st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
        else:
            st.info("포트폴리오 데이터를 불러올 수 없습니다.")
    except Exception as e:
        st.error(f"포트폴리오 데이터 오류: {e}")
        st.info("현재 보유 중인 종목이 없습니다.")
else:
    st.info("현재 보유 중인 종목이 없습니다.")

# 전체 거래 내역
st.markdown("### 📊 전체 거래 내역")

if 'history' in st.session_state and not st.session_state.history.empty:
    try:
        history_display = st.session_state.history.copy()
        history_display['거래일시'] = pd.to_datetime(history_display['거래일시']).dt.strftime('%Y-%m-%d %H:%M')
        history_display['가격'] = history_display['가격'].apply(lambda x: format_currency_smart(x))
        history_display['금액'] = history_display['금액'].apply(lambda x: format_currency_smart(x))
        
        st.dataframe(history_display, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"거래 내역 표시 오류: {e}")
else:
    st.info("거래 내역이 없습니다.")

# 과거 거래 데이터 분석
st.markdown("### 📈 과거 거래 분석")

user_data = st.session_state.get('user_data', pd.DataFrame())

if not user_data.empty:
    try:
        # 감정별 성과 분석
        col1, col2 = st.columns(2)
        
        with col1:
            # 감정별 평균 수익률
            if '감정태그' in user_data.columns and '수익률' in user_data.columns:
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
            else:
                st.info("감정별 분석을 위한 데이터가 부족합니다.")
        
        with col2:
            # 월별 거래 횟수
            if '거래일시' in user_data.columns:
                user_data_copy = user_data.copy()
                user_data_copy['거래일시'] = pd.to_datetime(user_data_copy['거래일시'])
                user_data_copy['거래월'] = user_data_copy['거래일시'].dt.to_period('M')
                monthly_trades = user_data_copy.groupby('거래월').size()
                
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
            else:
                st.info("월별 분석을 위한 데이터가 부족합니다.")
        
        # 거래 통계 요약
        st.markdown("### 📊 거래 통계 요약")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_trades = len(user_data)
        avg_return = user_data['수익률'].mean() if '수익률' in user_data.columns else 0
        win_rate = len(user_data[user_data['수익률'] > 0]) / len(user_data) * 100 if '수익률' in user_data.columns and len(user_data) > 0 else 0
        max_loss = user_data['수익률'].min() if '수익률' in user_data.columns else 0
        
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
            
    except Exception as e:
        st.error(f"거래 분석 중 오류 발생: {e}")
        st.info("기본 통계만 표시합니다.")
        
        # 기본 통계
        total_trades = len(user_data)
        st.metric("총 거래 횟수", f"{total_trades}회")
else:
    st.info("분석할 거래 데이터가 없습니다.")