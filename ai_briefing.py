import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from db.user_db import UserDatabase
from api.market_api import MarketAPI
from db.principles_db import get_principle_details

class AIBriefingService:
    """
    AI 브리핑 서비스 - 매매 추천을 하지 않고 객관적 정보만 제공
    "거울" 철학에 따라 사용자의 판단을 돕는 정보만 제공
    """
    
    def __init__(self):
        self.market_api = MarketAPI()
        self.user_db = UserDatabase()
    
    def generate_briefing(self, username: str, stock_code: str, action_type: str = "매수") -> Dict:
        """
        매매 전 AI 브리핑 생성
        
        Args:
            username: 사용자명
            stock_code: 종목코드
            action_type: 매수/매도
        
        Returns:
            Dict: 브리핑 정보
        """
        
        # 1. 현재 시장 상황 수집
        current_info = self.market_api.get_historical_info(stock_code, datetime.now().date())
        market_indices = self.market_api.get_market_indices(datetime.now().date())
        
        # 2. 사용자의 과거 거래 패턴 분석
        user_pattern = self._analyze_user_pattern(username, stock_code)
        
        # 3. 사용자의 투자 원칙과 비교
        principle_check = self._check_against_principles(username, current_info, action_type)
        
        # 4. 위험 요소 체크
        risk_factors = self._identify_risk_factors(current_info, user_pattern)
        
        briefing = {
            'timestamp': datetime.now(),
            'stock_info': current_info,
            'market_context': market_indices,
            'user_pattern_analysis': user_pattern,
            'principle_alignment': principle_check,
            'risk_assessment': risk_factors,
            'key_questions': self._generate_key_questions(action_type, risk_factors),
            'disclaimer': "⚠️ 이 브리핑은 투자 추천이 아닌 정보 제공입니다. 모든 투자 결정은 본인의 책임입니다."
        }
        
        return briefing
    
    def _analyze_user_pattern(self, username: str, stock_code: str) -> Dict:
        """사용자의 과거 거래 패턴 분석"""
        trades_data = self.user_db.get_user_trades(username)
        
        if trades_data is None or len(trades_data) == 0:
            return {
                'message': '📊 거래 데이터가 부족합니다. 신중한 첫 투자를 권장합니다.',
                'similar_trades': [],
                'emotion_pattern': None,
                'success_rate': None
            }
        
        # 동일 종목 과거 거래 찾기
        same_stock_trades = trades_data[trades_data['종목코드'] == stock_code]
        
        # 최근 감정 패턴 분석
        recent_emotions = trades_data.tail(10)['감정태그'].value_counts()
        
        # 성공률 계산
        success_rate = (trades_data['수익률'] > 0).mean() * 100
        
        return {
            'total_trades': len(trades_data),
            'same_stock_trades': len(same_stock_trades),
            'recent_emotion_pattern': recent_emotions.to_dict() if not recent_emotions.empty else {},
            'success_rate': round(success_rate, 1),
            'avg_return': round(trades_data['수익률'].mean(), 2),
            'similar_situations': self._find_similar_situations(trades_data, stock_code)
        }
    
    def _find_similar_situations(self, trades_data: pd.DataFrame, current_stock_code: str) -> List[Dict]:
        """현재 상황과 유사한 과거 거래 찾기"""
        similar_trades = []
        
        # 최근 5개 거래 중 감정 패턴이 유사한 것들 찾기
        recent_trades = trades_data.tail(10)
        
        for _, trade in recent_trades.iterrows():
            if trade['종목코드'] != current_stock_code:  # 다른 종목이지만 유사한 상황
                similar_trades.append({
                    'date': trade['거래일시'].strftime('%Y-%m-%d'),
                    'stock': trade['종목명'],
                    'emotion': trade['감정태그'],
                    'return': trade['수익률'],
                    'memo': trade['메모'][:50] + "..." if len(trade['메모']) > 50 else trade['메모']
                })
        
        return similar_trades[:3]  # 최대 3개만 반환
    
    def _check_against_principles(self, username: str, current_info: Dict, action_type: str) -> Dict:
        """사용자의 투자 원칙과 현재 상황 비교"""
        
        # 선택된 투자 원칙 가져오기
        selected_principle = st.session_state.get('selected_principle')
        
        if not selected_principle:
            return {
                'message': '💡 투자 원칙을 설정하면 더 정확한 가이드를 받을 수 있습니다.',
                'alignment_score': None,
                'warnings': []
            }
        
        principle_data = get_principle_details(selected_principle)
        if not principle_data:
            return {'message': '원칙 정보를 불러올 수 없습니다.', 'alignment_score': None, 'warnings': []}
        
        warnings = []
        alignment_score = 0
        
        # 워런 버핏 원칙 체크 예시
        if selected_principle == "워런 버핏":
            warnings.append("🤔 이 기업의 사업모델을 완전히 이해하고 계신가요?")
            
            if action_type == "매도":
                warnings.append("⏰ 장기 보유 관점에서 매도가 필요한 상황인가요?")
            
            alignment_score = 70
        
        elif selected_principle == "피터 린치":
            warnings.append("🔍 일상생활에서 이 회사 제품을 사용해본 경험이 있나요?")
            warnings.append("📈 최근 분기 실적 성장률을 확인하셨나요?")
            alignment_score = 60
            
        elif selected_principle == "벤저민 그레이엄":
            warnings.append("⚖️ 현재 가격이 내재가치 대비 충분한 안전 마진을 제공하나요?")
            warnings.append("📊 재무제표상 부채비율은 적정한가요?")
            alignment_score = 80
        
        return {
            'principle_name': selected_principle,
            'alignment_score': alignment_score,
            'warnings': warnings,
            'key_rules': principle_data.get('rules', [])[:3]  # 상위 3개 규칙만
        }
    
    def _identify_risk_factors(self, current_info: Dict, user_pattern: Dict) -> Dict:
        """현재 상황의 위험 요소 식별"""
        risk_factors = []
        risk_level = "보통"
        
        # 시장 위험 요소
        if current_info and abs(current_info.get('change', 0)) > 5:
            risk_factors.append("📈 주가 변동성이 높은 상황입니다")
            risk_level = "높음"
        
        # 사용자 패턴 위험 요소
        if user_pattern.get('recent_emotion_pattern'):
            emotions = user_pattern['recent_emotion_pattern']
            if '#공포' in emotions or '#패닉' in emotions:
                risk_factors.append("😰 최근 공포/패닉 거래 패턴이 감지되었습니다")
                risk_level = "높음"
            elif '#추격매수' in emotions or '#욕심' in emotions:
                risk_factors.append("🏃‍♂️ 최근 FOMO 매수 패턴이 감지되었습니다")
                risk_level = "높음"
        
        # 성공률 기반 위험 요소
        if user_pattern.get('success_rate', 50) < 40:
            risk_factors.append("📉 최근 거래 성공률이 낮습니다")
        
        return {
            'risk_level': risk_level,
            'factors': risk_factors,
            'recommendation': self._get_risk_recommendation(risk_level)
        }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """위험 수준별 권장 사항"""
        recommendations = {
            '낮음': "✅ 상대적으로 안정적인 상황입니다. 계획대로 진행하세요.",
            '보통': "⚠️ 신중한 접근을 권장합니다. 분할 매매를 고려해보세요.",
            '높음': "🚨 고위험 상황입니다. 24시간 후 재검토하거나 소액으로 시작하세요."
        }
        return recommendations.get(risk_level, "신중한 검토가 필요합니다.")
    
    def _generate_key_questions(self, action_type: str, risk_factors: Dict) -> List[str]:
        """사용자가 스스로에게 물어봐야 할 핵심 질문들"""
        base_questions = [
            "🎯 이 거래의 명확한 근거가 있나요?",
            "💰 손실을 감당할 수 있는 금액인가요?",
            "⏰ 감정적으로 급한 상황은 아닌가요?"
        ]
        
        if action_type == "매수":
            base_questions.extend([
                "📊 이 가격이 적정하다고 판단하는 이유는?",
                "🔍 이 회사의 사업을 이해하고 있나요?"
            ])
        else:  # 매도
            base_questions.extend([
                "📈 매도 이유가 감정적이지는 않나요?",
                "🎯 목표 수익률에 도달했나요?"
            ])
        
        if risk_factors.get('risk_level') == '높음':
            base_questions.append("🚨 지금이 아니어도 되는 거래 아닌가요?")
        
        return base_questions

def show_ai_briefing_ui(username: str, stock_code: str, stock_name: str, action_type: str = "매수"):
    """AI 브리핑 UI 표시"""
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); 
                border: 1px solid #BFDBFE; border-radius: 20px; padding: 24px; margin: 20px 0;'>
        <h3 style='color: #3182F6; margin-top: 0; display: flex; align-items: center;'>
            🤖 AI 브리핑: {stock_name} {action_type}
        </h3>
        <p style='color: #64748B; margin-bottom: 20px;'>
            매매 추천이 아닌, 판단에 도움이 될 객관적 정보를 제공합니다.
        </p>
    """, unsafe_allow_html=True)
    
    if st.button("🔍 AI 브리핑 요청", key=f"ai_briefing_{stock_code}_{action_type}", type="primary"):
        
        with st.spinner("🧠 AI가 시장 상황을 분석 중입니다..."):
            briefing_service = AIBriefingService()
            briefing = briefing_service.generate_briefing(username, stock_code, action_type)
        
        # 브리핑 결과 표시
        st.markdown("### 📊 현재 상황 분석")
        
        if briefing['stock_info']:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("현재가", f"₩{briefing['stock_info']['price']:,}")
            with col2:
                st.metric("등락률", f"{briefing['stock_info']['change']:+.1f}%")
            with col3:
                st.metric("시장상황", briefing['stock_info']['market_sentiment'])
        
        # 사용자 패턴 분석
        st.markdown("### 👤 당신의 거래 패턴")
        pattern = briefing['user_pattern_analysis']
        
        if pattern['total_trades'] > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 거래수", f"{pattern['total_trades']}건")
                st.metric("성공률", f"{pattern['success_rate']}%")
            with col2:
                st.metric("평균 수익률", f"{pattern['avg_return']:+.1f}%")
                st.metric("동일종목 거래", f"{pattern['same_stock_trades']}건")
            
            # 유사한 상황 표시
            if pattern['similar_situations']:
                st.markdown("**🔍 유사한 과거 상황:**")
                for situation in pattern['similar_situations']:
                    st.markdown(f"- **{situation['date']}** {situation['stock']} ({situation['emotion']}) → {situation['return']:+.1f}%")
        else:
            st.info(pattern['message'])
        
        # 투자 원칙 체크
        st.markdown("### 🎯 투자 원칙 체크")
        principle = briefing['principle_alignment']
        
        if principle.get('alignment_score'):
            st.metric("원칙 부합도", f"{principle['alignment_score']}/100점")
            
            if principle['warnings']:
                st.markdown("**⚠️ 체크포인트:**")
                for warning in principle['warnings']:
                    st.markdown(f"- {warning}")
            
            if principle.get('key_rules'):
                st.markdown("**📋 핵심 원칙:**")
                for rule in principle['key_rules']:
                    st.markdown(f"- {rule}")
        else:
            st.info(principle['message'])
        
        # 위험 요소
        st.markdown("### 🚨 위험 요소 분석")
        risk = briefing['risk_assessment']
        
        risk_color = {"낮음": "🟢", "보통": "🟡", "높음": "🔴"}
        st.markdown(f"**위험도:** {risk_color[risk['risk_level']]} {risk['risk_level']}")
        
        if risk['factors']:
            for factor in risk['factors']:
                st.markdown(f"- {factor}")
        
        st.info(risk['recommendation'])
        
        # 핵심 질문들
        st.markdown("### 🤔 스스로에게 물어보세요")
        
        for question in briefing['key_questions']:
            st.markdown(f"- {question}")
        
        # 면책 조항
        st.markdown("---")
        st.warning(briefing['disclaimer'])
    
    st.markdown("</div>", unsafe_allow_html=True)