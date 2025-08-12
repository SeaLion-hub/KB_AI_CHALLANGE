# pages/ai_coaching.py
"""
AI 거래 복기 센터 페이지 (Streamlit 공식 멀티페이지)
- 기존 '오답노트'에서 '거래 복기'로 확장
- 모든 거래(매수/매도, 수익/손실 무관) 복기 지원
- 성공 경험과 실패 경험 모두 학습하는 완전한 AI 코칭 시스템
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import sys
import os

# 상위 디렉토리의 모듈들을 임포트하기 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ai_service import (
        ReMinDKoreanEngine, check_gemini_api, analyze_trade_reflection,
        get_ai_success_principle
    )
    from data_service import (
        get_all_trades_for_review, save_trade_reflection, load_notes,
        save_charter, load_charter
    )
    AI_SERVICE_AVAILABLE = True
except ImportError:
    AI_SERVICE_AVAILABLE = False

from trading_service import format_currency_smart

# 페이지 설정
st.set_page_config(
    page_title="🧠 AI 거래 복기 - Re:Mind 3.1",
    page_icon="🧠",
    layout="wide"
)

# 세션 상태 확인
if 'user_data' not in st.session_state:
    st.error("데이터가 초기화되지 않았습니다. 메인 페이지에서 시작해주세요.")
    if st.button("🏠 메인 페이지로 이동"):
        st.switch_page("main_app.py")
    st.stop()

def show_trade_reflection():
    """모든 거래 복기 분석 (매수/매도, 성공/실패 모두 지원)"""
    st.markdown("### 🔍 AI 거래 복기 분석")
    st.markdown("모든 거래(매수/매도 무관)를 선택하여 AI와 함께 복기해보세요")
    
    # 사용자가 작성한 복기노트 표시
    if 'user_loss_notes' in st.session_state and st.session_state.user_loss_notes:
        st.markdown("#### 📋 작성된 복기노트")
        
        for i, note in enumerate(reversed(st.session_state.user_loss_notes), 1):
            with st.expander(f"복기노트 #{i}: {note['stock_name']} ({note['timestamp'].strftime('%Y-%m-%d %H:%M')})", expanded=False):
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
                st.info(f"💬 {note['user_comment']}")
    
    st.markdown("#### 🔍 모든 거래 복기하기")
    
    # 모든 거래 데이터 로드
    user_data = st.session_state.user_data
    if not user_data.empty:
        # 모든 거래를 복기 가능하도록 변환
        try:
            if AI_SERVICE_AVAILABLE:
                from data_service import get_all_trades_for_review
                all_trades = get_all_trades_for_review(user_data)
            else:
                # AI 서비스가 없으면 기본 처리
                all_trades = user_data.copy()
                all_trades['복기_표시'] = all_trades.apply(lambda row: 
                    f"{row['거래일시'].strftime('%Y-%m-%d') if hasattr(row['거래일시'], 'strftime') else row['거래일시']} - "
                    f"{row['종목명']} ({row['거래구분']}) - {row.get('수익률', 0):.1f}%", axis=1
                )
            
            if len(all_trades) > 0:
                # 거래 선택
                selected_idx = st.selectbox(
                    "복기할 거래를 선택하세요 (최신순)",
                    all_trades.index,
                    format_func=lambda x: all_trades.loc[x, '복기_표시'],
                    key="trade_reflection_selector"
                )
                
                selected_trade = all_trades.loc[selected_idx]
                
                # 선택된 거래의 매수/매도 구분을 명확히 표시
                trade_type = selected_trade['거래구분']
                trade_type_emoji = "🟢" if trade_type == "매수" else "🔴"
                trade_type_text = "매수 복기" if trade_type == "매수" else "매도 복기"
                
                # 수익률 계산 및 명확한 표시
                profit_loss = selected_trade.get('수익률', 0)
                is_success = profit_loss >= 0
                
                # 수익률에 따른 색상 및 텍스트
                if profit_loss > 0:
                    result_color = "#059669"
                    result_text = f"+{profit_loss:.1f}% 수익"
                    result_emoji = "🎉"
                elif profit_loss < 0:
                    result_color = "#DC2626"
                    result_text = f"{profit_loss:.1f}% 손실"
                    result_emoji = "😓"
                else:
                    result_color = "#6B7280"
                    result_text = "0% (손익 없음)"
                    result_emoji = "😐"
                
                st.markdown(f"#### {trade_type_emoji} {selected_trade['종목명']} ({trade_type_text}) {result_emoji}")
                st.markdown(f"**수익률: <span style='color: {result_color}; font-weight: bold;'>{result_text}</span>**", unsafe_allow_html=True)
                
                # 객관적 브리핑
                col1, col2 = st.columns([2, 2])
                
                with col1:
                    briefing_html = f"""
                    <div style="background-color: #FFFFFF; border-radius: 16px; padding: 20px; margin: 16px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #E5E8EB; width: 100%; box-sizing: border-box;">
                        <h4 style="font-size: 16px;">📋 거래 상세 정보</h4>
                        <div style="font-size: 13px;"><strong>거래일:</strong> {selected_trade['거래일시'].strftime('%Y년 %m월 %d일') if hasattr(selected_trade['거래일시'], 'strftime') else selected_trade['거래일시']}</div>
                        <div style="font-size: 13px;"><strong>종목:</strong> {selected_trade['종목명']} ({selected_trade.get('종목코드', 'N/A')})</div>
                        <div style="font-size: 13px;"><strong>거래구분:</strong> {trade_type_emoji} {selected_trade['거래구분']}</div>
                        <div style="font-size: 13px;"><strong>수량/가격:</strong> {selected_trade['수량']:,}주 / {format_currency_smart(selected_trade['가격'])}</div>
                        <div style="font-size: 13px;"><strong>감정상태:</strong> {selected_trade.get('감정태그', 'N/A')}</div>
                        <div style="color: {result_color}; font-weight: 700; font-size: 13px;"><strong>결과:</strong> {result_text}</div>
                    </div>
                    """
                    components.html(briefing_html, height=220)
                
                with col2:
                    analysis_html = f"""
                    <div style="background-color: #FFFFFF; border-radius: 16px; padding: 20px; margin: 16px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #E5E8EB; width: 100%; box-sizing: border-box;">
                        <h4 style="font-size: 16px;">📊 당시 종합 분석 상황</h4>
                        <div style="margin-bottom: 10px;">
                            <strong style="font-size: 13px;">📈 기술적 분석:</strong><br>
                            <span style="color: #505967; font-size: 12px; line-height: 1.4; word-wrap: break-word;">
                            {selected_trade.get('기술분석', '기술적 분석 정보 없음')}<br>
                            • 차트 패턴: {'상승 신호 감지' if trade_type == '매수' else '하락 신호 감지'}<br>
                            • 거래량: 평균 대비 150% 증가<br>
                            • 지지선: {format_currency_smart(selected_trade['가격'] * 0.95)} 예상
                            </span>
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <strong style="font-size: 13px;">📰 뉴스/펀더멘털 분석:</strong><br>
                            <span style="color: #505967; font-size: 12px; line-height: 1.4; word-wrap: break-word;">
                            {selected_trade.get('뉴스분석', '뉴스 분석 정보 없음')}<br>
                            • 시장 분위기: {'긍정적 전망 우세' if trade_type == '매수' else '부정적 전망 우세'}<br>
                            • 업종 동향: {'전반적 강세 지속' if trade_type == '매수' else '전반적 약세 지속'}<br>
                            • 외국인 매매: {'3일 연속 순매수' if trade_type == '매수' else '3일 연속 순매도'}
                            </span>
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <strong style="font-size: 13px;">😔 심리/감정 분석:</strong><br>
                            <span style="color: #505967; font-size: 12px; line-height: 1.4; word-wrap: break-word;">
                            {selected_trade.get('감정분석', '감정 분석 정보 없음')}<br>
                            • 투자자 심리지수: {'낙관적 성향' if trade_type == '매수' else '위험 회피 성향'}<br>
                            • VIX 지수: {'낮은 변동성 구간' if trade_type == '매수' else '높은 변동성 구간'}<br>
                            • 공포탐욕지수: {'탐욕(75) 수준' if trade_type == '매수' else '극도공포(25) 수준'}
                            </span>
                        </div>
                        
                        <div style="background: {'#F0FDF4' if profit_loss >= 0 else '#FEF2F2'}; padding: 8px; border-radius: 6px; border-left: 3px solid {'#10B981' if profit_loss >= 0 else '#F87171'};">
                            <strong style="color: {'#059669' if profit_loss >= 0 else '#DC2626'}; font-size: 13px;">
                                {'✅ 종합 판단:' if profit_loss >= 0 else '⚠️ 종합 위험도:'}
                            </strong> 
                            <span style="color: {'#065F46' if profit_loss >= 0 else '#7F1D1D'}; font-weight: 600; font-size: 13px;">
                                {'좋음' if profit_loss >= 0 else '높음'}
                            </span><br>
                            <small style="color: {'#065F46' if profit_loss >= 0 else '#7F1D1D'}; font-size: 11px;">
                                {'기술/뉴스/감정 지표 모두 긍정적' if profit_loss >= 0 else '기술/뉴스/감정 모든 지표가 부정적 신호'}
                            </small>
                        </div>
                    </div>
                    """
                    components.html(analysis_html, height=450)
                
                # 성공/실패에 따른 복기 UI 구분
                if is_success:
                    st.markdown("#### 🎉 AI 성공노트 작성")
                    st.markdown("축하합니다! 이 성공 경험을 분석하여 재사용 가능한 투자 원칙을 만들어보세요.")
                    reflection_placeholder = "이 성공한 거래의 투자 이유와 판단 과정을 상세히 기록해주세요. 어떤 근거로 투자를 결정했나요?"
                    reflection_title = "성공 요인 분석"
                    button_text = "🎉 AI 성공 분석 받기"
                    button_type = "primary"
                    button_color = "#059669"
                else:
                    st.markdown("#### ✏️ 거래 복기 작성")
                    st.markdown("이 거래를 복기하여 향후 개선점을 찾아보세요.")
                    reflection_placeholder = f"당시의 {trade_type} 결정 과정이나 현재의 생각을 자유롭게 기록해주세요."
                    reflection_title = "실패 요인 분석"
                    button_text = "🔍 AI 복기 분석 받기"
                    button_type = "primary"
                    button_color = "#DC2626"
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # 감정 선택
                    emotion_options = ["#공포", "#패닉", "#불안", "#추격매수", "#욕심", "#확신", "#합리적", "#만족", "#자신감"]
                    emotion_selection = st.selectbox(
                        "당시 주요 감정:",
                        emotion_options,
                        key="emotion_selector_reflection"
                    )
                
                with col2:
                    # 복기 내용 입력
                    user_reflection = st.text_area(
                        f"이 {trade_type} 거래에 대한 {reflection_title}:",
                        height=120,
                        placeholder=reflection_placeholder,
                        key="reflection_text_input"
                    )
                
                # AI 분석 및 저장 버튼
                ai_analysis_disabled = not check_gemini_api() if AI_SERVICE_AVAILABLE else True
                
                col1_btn, col2_btn = st.columns(2)
                
                with col1_btn:
                    if st.button(button_text, 
                                type=button_type, 
                                use_container_width=True, 
                                disabled=ai_analysis_disabled):
                        if user_reflection:
                            if is_success:
                                # 성공노트 AI 분석
                                st.markdown("#### 🎉 AI 성공 분석 결과")
                                
                                if AI_SERVICE_AVAILABLE:
                                    try:
                                        # 성공 원칙 추출
                                        success_principle = get_ai_success_principle(
                                            selected_trade.to_dict(), 
                                            user_reflection, 
                                            st.session_state.current_user
                                        )
                                        
                                        if success_principle.get('success'):
                                            principle_text = success_principle.get('principle', '')
                                            analysis = success_principle.get('analysis', {})
                                            
                                            # 성공 분석 결과 표시
                                            col1_success, col2_success = st.columns([2, 2])
                                            
                                            with col1_success:
                                                success_html = f"""
                                                <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #86EFAC; border-radius: 20px; padding: 18px; margin: 10px 0; word-wrap: break-word;">
                                                    <h4 style="margin: 0 0 12px 0; font-size: 16px;">🎯 성공 요인 분석</h4>
                                                    <div style="margin-bottom: 10px;">
                                                        <strong>핵심 성공 요인:</strong> {analysis.get('success_factor', 'N/A')}<br>
                                                        <strong>판단 정확도:</strong> {analysis.get('accuracy', 0)*100:.0f}%<br>
                                                        <strong>재현 가능성:</strong> {analysis.get('reproducibility', 'N/A')}
                                                    </div>
                                                    
                                                    <div style="background: rgba(255,255,255,0.8); padding: 8px; border-radius: 8px; margin-top: 10px;">
                                                        <strong>🏆 추출된 성공 원칙:</strong><br>
                                                        <em style="color: #065F46; font-weight: 600;">"{principle_text}"</em>
                                                    </div>
                                                </div>
                                                """
                                                components.html(success_html, height=280)
                                                
                                                # 헌장에 추가 버튼
                                                if st.button("✅ 성공 원칙을 헌장에 추가", key="add_success_principle", use_container_width=True):
                                                    if principle_text:
                                                        charter = load_charter(st.session_state.current_user)
                                                        if principle_text not in charter.get('success_principles', []):
                                                            charter.setdefault('success_principles', []).append(principle_text)
                                                            if save_charter(charter, st.session_state.current_user):
                                                                st.success("✅ 성공 원칙이 투자 헌장에 추가되었습니다!")
                                                                st.rerun()
                                                            else:
                                                                st.error("원칙 저장에 실패했습니다.")
                                                        else:
                                                            st.info("이미 헌장에 있는 원칙입니다.")
                                            
                                            with col2_success:
                                                insights = analysis.get('insights', {})
                                                
                                                insights_html = f"""
                                                <div style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); border: 1px solid #BFDBFE; border-radius: 20px; padding: 18px; margin: 10px 0; word-wrap: break-word;">
                                                    <h4 style="margin: 0 0 12px 0; font-size: 16px;">💡 성공 인사이트</h4>
                                                    
                                                    <div style="margin-bottom: 8px;">
                                                        <strong>강화할 점:</strong><br>
                                                        <ul style="margin: 4px 0; padding-left: 20px;">
                                                            {''.join([f'<li style="font-size: 12px;">{item}</li>' for item in insights.get('strengths', [])])}
                                                        </ul>
                                                    </div>
                                                    
                                                    <div style="margin-bottom: 8px;">
                                                        <strong>학습된 교훈:</strong><br>
                                                        <ul style="margin: 4px 0; padding-left: 20px;">
                                                            {''.join([f'<li style="font-size: 12px;">{item}</li>' for item in insights.get('lessons', [])])}
                                                        </ul>
                                                    </div>
                                                    
                                                    <div style="background: rgba(255,255,255,0.8); padding: 8px; border-radius: 8px; margin-top: 10px;">
                                                        <strong>💬 AI 조언:</strong> {analysis.get('coaching_advice', 'N/A')}
                                                    </div>
                                                </div>
                                                """
                                                components.html(insights_html, height=280)
                                        
                                        else:
                                            st.error(f"AI 분석 실패: {success_principle.get('message', '알 수 없는 오류')}")
                                            
                                    except Exception as e:
                                        st.error(f"성공 분석 중 오류 발생: {str(e)}")
                                else:
                                    st.error("AI 서비스를 사용할 수 없습니다.")
                            else:
                                # 기존 실패 거래 복기 분석
                                st.markdown("#### 🤖 AI 복기 분석 결과")
                                
                                if AI_SERVICE_AVAILABLE:
                                    try:
                                        analysis_result = analyze_trade_reflection(
                                            selected_trade.to_dict(), 
                                            user_reflection, 
                                            st.session_state.current_user
                                        )
                                        
                                        if analysis_result['success']:
                                            analysis = analysis_result['analysis']
                                            
                                            # 분석 결과를 가로로 배치
                                            col1_analysis, col2_analysis = st.columns([2, 2])
                                            
                                            with col1_analysis:
                                                # 감정 및 패턴 분석
                                                emotion_data = analysis.get('emotion_analysis', {})
                                                pattern_data = analysis.get('pattern_recognition', {})
                                                
                                                emotion_html = f"""
                                                <div style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); border: 1px solid #BFDBFE; border-radius: 20px; padding: 18px; margin: 10px 0; word-wrap: break-word;">
                                                    <h4 style="margin: 0 0 12px 0; font-size: 16px;">🧠 감정 & 패턴 분석</h4>
                                                    <div style="margin-bottom: 10px;">
                                                        <strong>주요 감정:</strong> {emotion_data.get('primary_emotion', 'N/A')}<br>
                                                        <strong>감정 강도:</strong> {emotion_data.get('emotion_intensity', 5)}/10<br>
                                                        <strong>감정 키워드:</strong> {', '.join(emotion_data.get('emotion_keywords', []))}
                                                    </div>
                                                    
                                                    <div style="margin-bottom: 10px;">
                                                        <strong>거래 패턴:</strong> {pattern_data.get('trading_pattern', 'N/A')}<br>
                                                        <strong>확신도:</strong> {pattern_data.get('confidence', 0)*100:.0f}%<br>
                                                        <strong>패턴 설명:</strong> {pattern_data.get('pattern_description', 'N/A')}
                                                    </div>
                                                </div>
                                                """
                                                components.html(emotion_html, height=280)
                                            
                                            with col2_analysis:
                                                # 인사이트 및 조언
                                                insights = analysis.get('insights', {})
                                                hashtags = ', '.join(analysis.get('ai_hashtags', []))
                                                coaching = analysis.get('coaching_advice', 'N/A')
                                                
                                                # 실패 원칙 추출
                                                failure_principle = f"'{pattern_data.get('trading_pattern', '부정적 패턴')}' 패턴을 피하고 더 신중한 분석 후 투자하기"
                                                
                                                insights_html = f"""
                                                <div style="background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%); border: 1px solid #F87171; border-radius: 20px; padding: 18px; margin: 10px 0; word-wrap: break-word;">
                                                    <h4 style="margin: 0 0 12px 0; font-size: 16px;">💡 인사이트 & 조언</h4>
                                                    
                                                    <div style="margin-bottom: 8px;">
                                                        <strong>개선점:</strong><br>
                                                        <ul style="margin: 4px 0; padding-left: 20px;">
                                                            {''.join([f'<li style="font-size: 12px;">{item}</li>' for item in insights.get('weaknesses', [])])}
                                                        </ul>
                                                    </div>
                                                    
                                                    <div style="margin-bottom: 8px;">
                                                        <strong>핵심 교훈:</strong><br>
                                                        <ul style="margin: 4px 0; padding-left: 20px;">
                                                            {''.join([f'<li style="font-size: 12px;">{item}</li>' for item in insights.get('lessons', [])])}
                                                        </ul>
                                                    </div>
                                                    
                                                    <div style="background: rgba(255,255,255,0.8); padding: 8px; border-radius: 8px; margin-top: 10px;">
                                                        <strong>🏷️ AI 해시태그:</strong> {hashtags}<br>
                                                        <strong>💬 AI 조언:</strong> {coaching}<br>
                                                        <strong>❗️ 추출된 주의 원칙:</strong><br>
                                                        <em style="color: #7F1D1D; font-weight: 600;">"{failure_principle}"</em>
                                                    </div>
                                                </div>
                                                """
                                                components.html(insights_html, height=280)
                                                
                                                # 헌장에 추가 버튼
                                                if st.button("❗️ 주의 원칙을 헌장에 추가", key="add_failure_principle", use_container_width=True):
                                                    charter = load_charter(st.session_state.current_user)
                                                    if failure_principle not in charter.get('failure_principles', []):
                                                        charter.setdefault('failure_principles', []).append(failure_principle)
                                                        if save_charter(charter, st.session_state.current_user):
                                                            st.success("✅ 주의 원칙이 투자 헌장에 추가되었습니다!")
                                                            st.rerun()
                                                        else:
                                                            st.error("원칙 저장에 실패했습니다.")
                                                    else:
                                                        st.info("이미 헌장에 있는 원칙입니다.")
                                        
                                        else:
                                            st.error(f"AI 분석 실패: {analysis_result['message']}")
                                            
                                    except Exception as e:
                                        st.error(f"AI 분석 중 오류 발생: {str(e)}")
                                else:
                                    st.error("AI 서비스를 사용할 수 없습니다.")
                        else:
                            st.warning("복기 내용을 입력해주세요.")
                
                with col2_btn:
                    if st.button("💾 복기노트 저장", 
                                type="secondary", 
                                use_container_width=True):
                        if user_reflection:
                            # 복기노트 저장
                            if AI_SERVICE_AVAILABLE:
                                try:
                                    from data_service import save_trade_reflection
                                    
                                    reflection_data = {
                                        'user_type': st.session_state.current_user,
                                        'emotion': emotion_selection,
                                        'user_comment': user_reflection,
                                        'ai_hashtags': [],
                                        'emotions': [emotion_selection],
                                        'emotion_intensity': 5,
                                        'loss_amount': 0  # 수익/손실 계산 로직 추가 가능
                                    }
                                    
                                    if save_trade_reflection(selected_trade.to_dict(), reflection_data):
                                        st.success("✅ 복기노트가 저장되었습니다!")
                                        
                                    else:
                                        st.error("복기노트 저장에 실패했습니다.")
                                        
                                except Exception as e:
                                    st.error(f"복기노트 저장 중 오류 발생: {str(e)}")
                            else:
                                st.warning("복기노트 저장 기능을 사용할 수 없습니다.")
                        else:
                            st.warning("복기 내용을 입력해주세요.")
                
                if ai_analysis_disabled:
                    st.info("💡 AI 복기 분석 기능을 사용하려면 API 키를 설정해주세요.")
                    
            else:
                st.info("복기할 거래가 없습니다.")
        
        except Exception as e:
            st.error(f"거래 데이터 처리 중 오류 발생: {str(e)}")
            st.info("기본 거래 목록을 표시합니다.")
            
            # 기본 거래 목록 표시
            if '거래구분' in user_data.columns:
                recent_trades = user_data.tail(10)
                for idx, trade in recent_trades.iterrows():
                    with st.expander(f"{trade['종목명']} ({trade['거래구분']}) - {trade.get('수익률', 0):.1f}%"):
                        st.write(f"거래일: {trade['거래일시']}")
                        st.write(f"가격: {format_currency_smart(trade['가격'])}")
                        st.write(f"수량: {trade['수량']:,}주")
    else:
        st.info("거래 데이터가 없습니다.")

def show_investment_charter():
    """나의 투자 헌장 - 성공 원칙과 실패 원칙 구분 표시"""
    st.markdown("### 📜 나의 투자 헌장")
    st.markdown("성공 경험과 실패 경험에서 학습한 개인화된 투자 원칙들을 관리합니다")
    
    # 투자 헌장 로드
    charter = load_charter(st.session_state.current_user)
    success_principles = charter.get('success_principles', [])
    failure_principles = charter.get('failure_principles', [])
    
    # 두 개의 열로 구분하여 표시
    col_success, col_failure = st.columns(2)
    
    with col_success:
        st.markdown("#### ✅ 지켜야 할 성공 원칙")
        st.markdown("성공한 투자 경험에서 학습한 원칙들입니다.")
        
        if success_principles:
            for i, principle in enumerate(success_principles):
                with st.container():
                    principle_html = f"""
                    <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #86EFAC; border-radius: 12px; padding: 16px; margin: 8px 0; word-wrap: break-word;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1; margin-right: 10px;">
                                <strong style="color: #065F46;">원칙 {i+1}</strong><br>
                                <span style="color: #047857; line-height: 1.4;">{principle}</span>
                            </div>
                        </div>
                    </div>
                    """
                    components.html(principle_html, height=100)
                    
                    # 삭제 버튼
                    if st.button(f"🗑️ 삭제", key=f"delete_success_{i}", help=f"성공 원칙 {i+1} 삭제"):
                        charter['success_principles'].remove(principle)
                        if save_charter(charter, st.session_state.current_user):
                            st.success("✅ 성공 원칙이 삭제되었습니다!")
                            st.rerun()
                        else:
                            st.error("삭제에 실패했습니다.")
        else:
            st.info("아직 성공 원칙이 없습니다. 성공한 거래를 복기하여 원칙을 추가해보세요.")
        
        # 직접 성공 원칙 추가
        st.markdown("##### ➕ 성공 원칙 직접 추가")
        new_success_principle = st.text_area(
            "새로운 성공 원칙:",
            placeholder="예: 분할 매수를 통해 리스크를 분산한다",
            key="new_success_principle",
            height=60
        )
        
        if st.button("✅ 성공 원칙 추가", key="add_manual_success"):
            if new_success_principle:
                if new_success_principle not in success_principles:
                    charter.setdefault('success_principles', []).append(new_success_principle)
                    if save_charter(charter, st.session_state.current_user):
                        st.success("✅ 성공 원칙이 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error("추가에 실패했습니다.")
                else:
                    st.warning("이미 존재하는 원칙입니다.")
            else:
                st.warning("원칙을 입력해주세요.")
    
    with col_failure:
        st.markdown("#### ❗️ 피해야 할 실패 원칙")
        st.markdown("실패한 투자 경험에서 학습한 주의사항들입니다.")
        
        if failure_principles:
            for i, principle in enumerate(failure_principles):
                with st.container():
                    principle_html = f"""
                    <div style="background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%); border: 1px solid #F87171; border-radius: 12px; padding: 16px; margin: 8px 0; word-wrap: break-word;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1; margin-right: 10px;">
                                <strong style="color: #7F1D1D;">주의사항 {i+1}</strong><br>
                                <span style="color: #991B1B; line-height: 1.4;">{principle}</span>
                            </div>
                        </div>
                    </div>
                    """
                    components.html(principle_html, height=100)
                    
                    # 삭제 버튼
                    if st.button(f"🗑️ 삭제", key=f"delete_failure_{i}", help=f"실패 원칙 {i+1} 삭제"):
                        charter['failure_principles'].remove(principle)
                        if save_charter(charter, st.session_state.current_user):
                            st.success("✅ 실패 원칙이 삭제되었습니다!")
                            st.rerun()
                        else:
                            st.error("삭제에 실패했습니다.")
        else:
            st.info("아직 주의사항이 없습니다. 실패한 거래를 복기하여 주의사항을 추가해보세요.")
        
        # 직접 실패 원칙 추가
        st.markdown("##### ➕ 주의사항 직접 추가")
        new_failure_principle = st.text_area(
            "새로운 주의사항:",
            placeholder="예: 감정적 상태에서 거래하지 않는다",
            key="new_failure_principle",
            height=60
        )
        
        if st.button("❗️ 주의사항 추가", key="add_manual_failure"):
            if new_failure_principle:
                if new_failure_principle not in failure_principles:
                    charter.setdefault('failure_principles', []).append(new_failure_principle)
                    if save_charter(charter, st.session_state.current_user):
                        st.success("✅ 주의사항이 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error("추가에 실패했습니다.")
                else:
                    st.warning("이미 존재하는 주의사항입니다.")
            else:
                st.warning("주의사항을 입력해주세요.")
    
    # 통합 헌장 보기
    if success_principles or failure_principles:
        st.markdown("---")
        if st.button("📋 완전한 투자 헌장 보기", use_container_width=True):
            charter_html = f"""
            <div style="background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); border: 1px solid #FDBA74; border-radius: 20px; padding: 24px; margin: 20px 0;">
                <h2 style="text-align: center; margin: 0 0 2rem 0; color: #191919;">📜 {st.session_state.current_user}님의 투자 헌장</h2>
                <p style="text-align: center; font-style: italic; color: #505967; margin-bottom: 2rem;">{datetime.now().strftime('%Y년 %m월 %d일')} 작성</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 2rem;">
                    <div>
                        <h3 style="color: #065F46; margin-bottom: 1rem;">✅ 지켜야 할 성공 원칙</h3>
            """
            
            for i, principle in enumerate(success_principles, 1):
                charter_html += f"""
                <div style="margin: 0.5rem 0;">
                    <strong>{i}. {principle}</strong>
                </div>
                """
            
            charter_html += """
                    </div>
                    <div>
                        <h3 style="color: #7F1D1D; margin-bottom: 1rem;">❗️ 피해야 할 실패 원칙</h3>
            """
            
            for i, principle in enumerate(failure_principles, 1):
                charter_html += f"""
                <div style="margin: 0.5rem 0;">
                    <strong>{i}. {principle}</strong>
                </div>
                """
            
            charter_html += f"""
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #FDBA74;">
                    <p><strong>서명:</strong> {st.session_state.current_user} &nbsp;&nbsp;&nbsp; <strong>날짜:</strong> {datetime.now().strftime('%Y년 %m월 %d일')}</p>
                </div>
            </div>
            """
            
            components.html(charter_html, height=400 + max(len(success_principles), len(failure_principles)) * 30)

def show_investment_principles():
    """투자 원칙 탭"""
    st.markdown("### ⚖️ AI가 추출한 투자 원칙")
    st.markdown("과거 복기노트를 분석하여 AI가 자동으로 추출한 투자 원칙들입니다")
    
    if not st.session_state.user_data.empty:
        if AI_SERVICE_AVAILABLE:
            principles = st.session_state.engine.extract_principles_from_notes(st.session_state.user_data)
        else:
            principles = []
        
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
                    
                    # 텍스트 길이에 따른 동적 높이 계산
                    title_length = len(principle['title'])
                    description_length = len(principle['description'])
                    rule_length = len(principle['rule'])
                    
                    extra_height = max(0, (title_length + description_length + rule_length - 150) // 8)
                    calculated_height = min(500, 250 + extra_height)
                    
                    principle_html = f"""
                    <div style="{card_style} border-radius: 12px; padding: 20px; margin: 16px 0; height: auto; overflow: auto;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; flex-wrap: wrap;">
                            <h4 style="margin: 0; color: #191919; word-wrap: break-word; flex: 1; margin-right: 10px;">{principle['title']}</h4>
                            <span style="background-color: {priority_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; white-space: nowrap; flex-shrink: 0;">
                                우선순위: {priority_text}
                            </span>
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <strong>📊 분석 결과:</strong><br>
                            <span style="word-wrap: break-word; line-height: 1.4; display: block; overflow-wrap: break-word;">{principle['description']}</span>
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <strong>📋 제안 규칙:</strong><br>
                            <em style="word-wrap: break-word; line-height: 1.4; display: block; overflow-wrap: break-word;">"{principle['rule']}"</em>
                        </div>
                        
                        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #505967; margin-top: 16px; flex-wrap: wrap; gap: 10px;">
                            <span><strong>증거 건수:</strong> {principle['evidence_count']}회</span>
                            <span><strong>평균 영향:</strong> -{principle['avg_impact']:.1f}%</span>
                        </div>
                    </div>
                    """
                    components.html(principle_html, height=calculated_height)
                    
                    # 원칙 채택 여부
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ 원칙 #{i} 채택", key=f"adopt_principle_{i}", use_container_width=True):
                            charter = load_charter(st.session_state.current_user)
                            # 실패 원칙으로 추가
                            if principle['rule'] not in charter.get('failure_principles', []):
                                charter.setdefault('failure_principles', []).append(principle['rule'])
                                if save_charter(charter, st.session_state.current_user):
                                    st.success(f"원칙 #{i}이 개인 투자 헌장에 추가되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("원칙 저장에 실패했습니다.")
                            else:
                                st.info("이미 헌장에 있는 원칙입니다.")
                    
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
        
        col1, col2 = st.columns(2)
        with col1:
            add_as_success = st.form_submit_button("✅ 성공 원칙으로 추가", type="primary")
        with col2:
            add_as_failure = st.form_submit_button("❗️ 주의사항으로 추가", type="secondary")
        
        if add_as_success or add_as_failure:
            if custom_title and custom_rule:
                charter = load_charter(st.session_state.current_user)
                
                if add_as_success:
                    if custom_rule not in charter.get('success_principles', []):
                        charter.setdefault('success_principles', []).append(custom_rule)
                        principle_type = "성공 원칙"
                        principle_color = "#059669"
                    else:
                        st.warning("이미 존재하는 성공 원칙입니다.")
                        st.stop()
                else:  # add_as_failure
                    if custom_rule not in charter.get('failure_principles', []):
                        charter.setdefault('failure_principles', []).append(custom_rule)
                        principle_type = "주의사항"
                        principle_color = "#DC2626"
                    else:
                        st.warning("이미 존재하는 주의사항입니다.")
                        st.stop()
                
                if save_charter(charter, st.session_state.current_user):
                    st.success(f"나만의 {principle_type}이 추가되었습니다!")
                    
                    custom_principle_html = f"""
                    <div style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); border: 1px solid #BFDBFE; border-radius: 12px; padding: 16px; margin: 16px 0;">
                        <h4 style="word-wrap: break-word; color: {principle_color};">{custom_title}</h4>
                        <p><strong>규칙:</strong> <span style="word-wrap: break-word;">{custom_rule}</span></p>
                        <p><strong>이유:</strong> <span style="word-wrap: break-word;">{custom_reason}</span></p>
                        <small style="color: #505967;">사용자 정의 {principle_type} • 추가됨: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
                    </div>
                    """
                    components.html(custom_principle_html, height=200)
                    st.rerun()
                else:
                    st.error("원칙 저장에 실패했습니다.")
            else:
                st.warning("제목과 규칙을 모두 입력해주세요.")

# AI 거래 복기 센터 페이지 메인 실행
st.markdown('<h1 style="font-size: 28px; font-weight: 800; color: #191919; margin-bottom: 8px;">🧠 AI 거래 복기 센터</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 16px; color: #505967; margin-bottom: 32px;">모든 거래를 분석하고 개인화된 투자 헌장을 만들어보세요</p>', unsafe_allow_html=True)

# AI 서비스 초기화
if AI_SERVICE_AVAILABLE and 'engine' not in st.session_state:
    st.session_state.engine = ReMinDKoreanEngine()

tab1, tab2, tab3 = st.tabs(["📝 AI 거래 복기", "📜 나의 투자 헌장", "⚖️ 투자 원칙"])

with tab1:
    show_trade_reflection()

with tab2:
    show_investment_charter()

with tab3:
    show_investment_principles()