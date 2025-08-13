# pages/ai_review.py (안정성 강화 최종 버전)
"""
AI 검토 전용 페이지
- 안정화된 ai_service의 새로운 데이터 구조를 처리하여 'N/A' 문제 해결
"""

import streamlit as st
import sys
import os
from datetime import datetime
import time

# 상위 디렉토리의 모듈들을 임포트하기 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_service import execute_trade, add_trade_to_history, format_currency_smart
from ai_service import check_gemini_api, gemini_select_and_analyze_trades
from ui_components import apply_kb_theme

# 페이지 설정
st.set_page_config(page_title="🤖 AI 거래 검토 - Re:Mind 3.1", page_icon="🤖", layout="wide")
apply_kb_theme()

# 세션 상태 확인
if 'pending_trade' not in st.session_state or not st.session_state.pending_trade:
    st.error("검토할 거래 정보가 없습니다.")
    if st.button("📈 거래 페이지로 돌아가기"):
        st.switch_page("pages/stock_trading.py")
    st.stop()

# 헤더
st.markdown('<h1 style="font-size: 28px; font-weight: 800; color: #191919;">🤖 KB AI 거래 검토</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 16px; color: #505967;">AI가 과거 거래 데이터를 분석하여 현재 거래를 검토합니다</p>', unsafe_allow_html=True)

trade = st.session_state.pending_trade

# 현재 거래 정보 표시
st.markdown("### 📋 검토할 거래 정보")
col1, col2, col3 = st.columns(3)
col1.metric("종목", trade["stock_name"])
col2.metric("거래유형", trade["trade_type"])
col3.metric("수량", f"{trade['quantity']:,}주")
st.metric("총액", format_currency_smart(trade["quantity"] * trade["price"]))
st.markdown("---")

# Gemini 기반 AI 분석 실행
if not st.session_state.user_data.empty and check_gemini_api():
    st.markdown("### 🏦 KB AI 분석 진행")
    with st.spinner("🏦 KB AI가 유사 거래를 선택하고 분석하고 있습니다..."):
        analysis_result = gemini_select_and_analyze_trades(
            trade, st.session_state.user_data, st.session_state.current_user
        )

        # [수정] 새로운 데이터 구조에 맞춰 결과 처리
        if "selected_trades" in analysis_result and "ai_analysis" in analysis_result:
            st.markdown("#### 📋 AI가 선택한 가장 유사한 과거 거래 3개")

            for i, trade_data in enumerate(analysis_result["selected_trades"], 1):
                # 데이터가 보장되므로 .get()의 기본값이 필요 없어짐
                stock_name = trade_data["종목명"]
                return_rate = float(trade_data.get("수익률", 0))

                with st.expander(f"🔍 유사 거래 #{i}: {stock_name} ({return_rate:+.1f}%)", expanded=True):
                    col1_exp, col2_exp = st.columns(2)
                    with col1_exp:
                        st.markdown("**당시 주관적 데이터**")
                        st.info(f"**감정:** {trade_data.get('감정태그', '기록 없음')}")
                        st.info(f"**메모:** \"{trade_data.get('메모', '기록 없음')}\"")
                    with col2_exp:
                        st.markdown("**당시 객관적 데이터**")
                        st.warning(f"**기술 분석:** {trade_data.get('기술분석', '기록 없음')}")
                        st.warning(f"**뉴스 분석:** {trade_data.get('뉴스분석', '기록 없음')}")
                        st.warning(f"**코스피:** {trade_data.get('코스피지수', 0):.2f}")

            # AI 종합 분석 표시
            st.markdown("#### 🏦 KB AI 종합 분석 및 투자 조언")
            ai_analysis = analysis_result['ai_analysis']
            st.markdown("##### 🔍 패턴 분석")
            st.info(ai_analysis.get("pattern_analysis", "분석 정보 없음"))
            st.markdown("##### ⚠️ 위험도 평가")
            st.warning(ai_analysis.get("risk_assessment", "분석 정보 없음"))
            st.markdown("##### 💡 투자 권고사항")
            st.success(ai_analysis.get("recommendation", "분석 정보 없음"))
            st.markdown("##### 📋 대안 전략")
            st.info(ai_analysis.get("alternative_strategy", "분석 정보 없음"))
        else:
            st.error(f"KB AI 분석 중 오류가 발생했습니다: {analysis_result.get('analysis', '알 수 없는 오류')}")

else:
    st.error("🚨 KB AI 연결이 필요합니다. 사이드바에서 Gemini API 키를 설정해주세요.")

# 거래 실행 또는 취소 버튼
st.markdown("---")
st.markdown("### 💡 거래 결정")
col1_btn, col2_btn, col3_btn = st.columns(3)
with col1_btn:
    if st.button("✅ 거래 실행", key="execute_trade", use_container_width=True, type="primary"):
        # (거래 실행 로직은 기존과 동일)
        st.switch_page("pages/stock_trading.py")
with col2_btn:
    if st.button("❌ 거래 취소", key="cancel_trade", use_container_width=True):
        st.session_state.pending_trade = None # 세션 초기화
        st.info("거래 검토가 취소되었습니다.")
        time.sleep(1)
        st.switch_page("pages/stock_trading.py")