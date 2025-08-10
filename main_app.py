#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - AI 투자 복기 코칭 (완전 개선 버전)
KB AI CHALLENGE 2024 - 프로토타입

핵심 기능:
1. 투자 복기 → AI 분석 → 개인화된 코칭
2. 실시간 데이터 기반 동적 응답
3. 과거 거래 패턴 매칭을 통한 복기
4. 투자 원칙 제안 및 통계 분석
5. 완전한 동적 데이터 시스템
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import random
import plotly.express as px
import plotly.graph_objects as go

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 임시 데이터 매니저 (core.data_engine이 없는 경우)
class TempDataManager:
    def __init__(self):
        # 임시 사용자 데이터
        self.users = {
            "김투자": {
                "icon": "😰",
                "description": "감정적 투자자 - FOMO와 욕심에 흔들리는 타입",
                "trades_count": 15,
                "personality": "emotional"
            },
            "박복기": {
                "icon": "🤓",
                "description": "체계적 투자자 - 데이터와 분석을 중시하는 타입",
                "trades_count": 23,
                "personality": "analytical"
            },
            "이신규": {
                "icon": "🌱",
                "description": "투자 초보자 - 기본부터 차근차근 배우는 타입",
                "trades_count": 0,
                "personality": "beginner"
            }
        }
        
        # 임시 시장 데이터
        self.market_data = {
            "삼성전자": {"price": 75200, "change": -2.3, "change_percent": -2.3, "volume": 1500000, "market_cap": "450조원", "sector": "기술"},
            "SK하이닉스": {"price": 142000, "change": 3.7, "change_percent": 3.7, "volume": 890000, "market_cap": "103조원", "sector": "반도체"},
            "NAVER": {"price": 183500, "change": -0.8, "change_percent": -0.8, "volume": 450000, "market_cap": "30조원", "sector": "IT서비스"},
            "카카오": {"price": 58900, "change": 1.2, "change_percent": 1.2, "volume": 750000, "market_cap": "25조원", "sector": "인터넷"}
        }
        
        # 임시 거래 데이터
        self.trades = {
            "김투자": [
                {"date": "2024-07-15", "stock": "삼성전자", "result": -8.2, "emotion": "욕심", "reason": "FOMO로 급등 후 매수"},
                {"date": "2024-07-20", "stock": "SK하이닉스", "result": 5.3, "emotion": "불안", "reason": "반도체 상승세 따라가기"},
                {"date": "2024-08-01", "stock": "NAVER", "result": -3.1, "emotion": "욕심", "reason": "AI 테마 기대감"},
                {"date": "2024-08-05", "stock": "카카오", "result": 2.1, "emotion": "냉정", "reason": "차트 분석 후 매수"}
            ],
            "박복기": [
                {"date": "2024-06-20", "stock": "NAVER", "result": 8.9, "emotion": "확신", "reason": "실적 분석 후 매수"},
                {"date": "2024-07-10", "stock": "삼성전자", "result": 4.5, "emotion": "냉정", "reason": "기술적 분석 기반"},
                {"date": "2024-07-25", "stock": "SK하이닉스", "result": -2.3, "emotion": "확신", "reason": "펀더멘털 기반 투자"},
                {"date": "2024-08-02", "stock": "카카오", "result": 6.7, "emotion": "냉정", "reason": "밸류에이션 매력"}
            ]
        }
        
        # 임시 뉴스 데이터
        self.news_data = [
            {
                "title": "삼성전자, AI 반도체 시장 점유율 확대",
                "content": "삼성전자가 AI 전용 반도체 시장에서의 점유율을 크게 늘렸다는 분석이 나왔습니다.",
                "time": "2시간 전",
                "impact": "긍정적",
                "importance": "높음",
                "source": "한국경제",
                "related_stocks": ["삼성전자", "SK하이닉스"]
            },
            {
                "title": "NAVER, 글로벌 AI 서비스 확장 발표",
                "content": "네이버가 자체 개발한 AI 모델을 기반으로 한 글로벌 서비스 확장 계획을 발표했습니다.",
                "time": "4시간 전",
                "impact": "긍정적",
                "importance": "중간",
                "source": "연합뉴스",
                "related_stocks": ["NAVER"]
            }
        ]
    
    def get_user_trades(self, user_id):
        return self.trades.get(user_id, [])
    
    def get_user(self, user_id):
        return self.users.get(user_id, {})

try:
    from core.data_engine import get_dynamic_data_engine, get_user_reviews 
except ImportError:
    # core.data_engine이 없는 경우 임시 데이터 사용
    def get_dynamic_data_engine():
        return TempDataManager()
    def get_user_reviews(user_id: str):  # ← 추가: 없는 경우 안전한 대체
        return []

# ================================
# [STREAMLIT CONFIG]
# ================================
st.set_page_config(
    page_title="KB Reflex - AI 투자 복기 코칭",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# KB 스타일 (간단한 버전)
def apply_kb_theme():
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .kb-header {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .kb-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #FFD700;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .kb-info {
        background: linear-gradient(135deg, #E8F4FD 0%, #BDDBFA 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #FFD700;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #FFD700;
        text-align: center;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def kb_header(title, subtitle, icon):
    st.markdown(f"""
    <div class="kb-header">
        <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
        <h1 style="font-size: 3rem; font-weight: 800; margin: 0 0 1rem 0; 
                   text-shadow: 2px 2px 4px rgba(0,0,0,0.1); letter-spacing: -1px;">
            {title}
        </h1>
        <p style="font-size: 1.4rem; margin: 0; opacity: 0.9; font-weight: 500;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)

def kb_metric_card(title, value, delta, delta_type, icon):
    delta_color = "#28A745" if delta_type == "success" else "#DC3545" if delta_type == "danger" else "#6C757D"
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <h4 style="margin: 0.5rem 0; color: #333;">{title}</h4>
        <div style="font-size: 1.5rem; font-weight: bold; margin: 0.5rem 0;">{value}</div>
        <div style="color: {delta_color}; font-size: 0.9rem;">{delta}</div>
    </div>
    """, unsafe_allow_html=True)

def kb_alert(message, alert_type, title=""):
    colors = {
        "success": "#D4EDDA",
        "warning": "#FFF3CD", 
        "danger": "#F8D7DA",
        "info": "#D1ECF1"
    }
    bg_color = colors.get(alert_type, "#F8F9FA")
    
    if title:
        st.markdown(f"""
        <div style="background: {bg_color}; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <h5 style="margin: 0 0 0.5rem 0;">{title}</h5>
            <p style="margin: 0;">{message}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: {bg_color}; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <p style="margin: 0;">{message}</p>
        </div>
        """, unsafe_allow_html=True)

apply_kb_theme()

# 전역 데이터 매니저
@st.cache_resource  
def get_data_manager():
    return get_dynamic_data_engine()

# ================================
# [개선된 AI 코칭 엔진]
# ================================
class EnhancedAICoach:
    """개선된 AI 코칭 엔진 - 더 정교한 분석과 조언"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def analyze_situation(self, user_input, selected_user):
        """사용자 입력 상황 종합 분석"""
        
        # 1. 기본 키워드 분석
        keywords = self._extract_keywords(user_input)
        
        # 2. 감정 상태 분석
        emotion_analysis = self._analyze_emotion_state(user_input)
        
        # 3. 관련 뉴스 및 시장 데이터
        related_news = self._find_related_news(keywords)
        market_info = self._get_market_info(keywords)
        
        # 4. 과거 거래 패턴 매칭
        similar_trades = self._find_similar_trades_enhanced(user_input, selected_user)
        
        # 5. 투자 원칙 위반 체크
        principle_violations = self._check_investment_principles(user_input, selected_user)
        
        # 6. 위험도 평가
        risk_assessment = self._assess_investment_risk(user_input, market_info, emotion_analysis)
        
        # 7. 종합 AI 코칭 생성
        coaching = self._generate_enhanced_coaching(
            user_input, similar_trades, market_info, related_news, 
            emotion_analysis, principle_violations, risk_assessment
        )
        
        return {
            "keywords": keywords,
            "emotion_analysis": emotion_analysis,
            "related_news": related_news,
            "market_info": market_info,
            "similar_trades": similar_trades,
            "principle_violations": principle_violations,
            "risk_assessment": risk_assessment,
            "coaching": coaching
        }
    
    def suggest_investment_principles(self, user_trades, user_data):
        """사용자 거래 패턴 기반 투자 원칙 제안"""
        if not user_trades:
            return self._get_beginner_principles()
        
        # 거래 패턴 분석
        pattern_analysis = self._analyze_trading_patterns(user_trades)
        
        # 감정 패턴 분석
        emotion_patterns = self._analyze_emotion_patterns(user_trades)
        
        # 맞춤형 원칙 생성
        principles = self._generate_personalized_principles(
            pattern_analysis, emotion_patterns, user_data
        )
        
        return principles
    
    def _extract_keywords(self, text):
        """키워드 추출"""
        keywords = []
        
        # 종목명 체크
        stocks = list(self.data_manager.market_data.keys())
        actions = ["매수", "매도", "보유", "관망", "추가매수", "손절", "익절"]
        emotions = ["불안", "확신", "두려움", "욕심", "냉정", "흥분", "후회", "만족", "FOMO"]
        
        text_lower = text.lower()
        
        for stock in stocks:
            if stock in text:
                keywords.append(("종목", stock))
        
        for action in actions:
            if action in text_lower:
                keywords.append(("행동", action))
                
        for emotion in emotions:
            if emotion in text_lower:
                keywords.append(("감정", emotion))
        
        return keywords
    
    def _analyze_emotion_state(self, text):
        """감정 상태 분석"""
        emotions = {
            "불안": ["불안", "걱정", "두려워", "무서워", "떨려"],
            "욕심": ["욕심", "더", "추가", "올인", "대박", "FOMO"],
            "후회": ["후회", "아쉬워", "잘못", "실수"],
            "확신": ["확실", "틀림없", "분명", "당연", "확신"],
            "냉정": ["냉정", "객관적", "데이터", "분석", "근거"]
        }
        
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, words in emotions.items():
            score = sum(1 for word in words if word in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if not emotion_scores:
            return {"primary_emotion": "중립", "intensity": 0.5, "confidence": 0.3}
        
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        intensity = min(1.0, emotion_scores[primary_emotion] / 3)
        confidence = min(1.0, sum(emotion_scores.values()) / 5)
        
        return {
            "primary_emotion": primary_emotion,
            "intensity": intensity,
            "confidence": confidence,
            "all_emotions": emotion_scores
        }
    
    def _find_similar_trades_enhanced(self, user_input, selected_user):
        """과거 유사 거래 찾기"""
        if selected_user == "이신규":
            return []
        
        user_trades = self.data_manager.get_user_trades(selected_user)
        if not user_trades:
            return []
        
        # 간단한 유사도 계산
        similarities = []
        
        for trade in user_trades:
            similarity_score = 0.6 + random.uniform(-0.3, 0.3)  # 임시 유사도
            
            if similarity_score > 0.2:
                similarities.append({
                    **trade,
                    "similarity": similarity_score,
                    "match_factors": ["감정 패턴", "종목 유사성"]
                })
        
        return sorted(similarities, key=lambda x: x["similarity"], reverse=True)[:3]
    
    def _check_investment_principles(self, user_input, selected_user):
        """투자 원칙 위반 체크"""
        violations = []
        
        # 기본 투자 원칙들
        principles = {
            "감정적_투자": ["FOMO", "욕심", "흥분", "급하게"],
            "과도한_집중": ["올인", "전부", "몰빵"],
            "손절_지연": ["더 떨어질까", "조금만 더", "회복될 때까지"],
            "근거_부족": ["느낌", "감", "그냥", "왠지"]
        }
        
        text_lower = user_input.lower()
        
        for principle, keywords in principles.items():
            for keyword in keywords:
                if keyword in text_lower:
                    violations.append({
                        "principle": principle,
                        "keyword": keyword,
                        "warning_level": "높음" if principle in ["감정적_투자", "과도한_집중"] else "중간"
                    })
        
        return violations
    
    def _assess_investment_risk(self, user_input, market_info, emotion_analysis):
        """투자 위험도 평가"""
        risk_score = 0.5  # 기본 중간 위험
        risk_factors = []
        
        # 감정 기반 위험도
        if emotion_analysis["primary_emotion"] in ["욕심", "FOMO", "흥분"]:
            risk_score += 0.3
            risk_factors.append("감정적 판단 위험")
        
        # 시장 상황 기반 위험도
        if market_info:
            for stock, data in market_info.items():
                if abs(data["change"]) > 5:  # 5% 이상 변동
                    risk_score += 0.2
                    risk_factors.append(f"{stock} 높은 변동성")
        
        # 텍스트 패턴 기반 위험도
        high_risk_patterns = ["올인", "전부", "대박", "급등", "추격"]
        for pattern in high_risk_patterns:
            if pattern in user_input:
                risk_score += 0.2
                risk_factors.append(f"위험 패턴: {pattern}")
        
        risk_score = min(1.0, risk_score)
        
        # 위험도 레벨 결정
        if risk_score > 0.7:
            risk_level = "높음"
        elif risk_score > 0.4:
            risk_level = "보통"
        else:
            risk_level = "낮음"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors
        }
    
    def _generate_enhanced_coaching(self, user_input, similar_trades, market_info, 
                                  related_news, emotion_analysis, principle_violations, risk_assessment):
        """AI 코칭 메시지 생성"""
        
        # 상황 분석
        analysis = f"현재 투자 상황을 분석한 결과, {emotion_analysis['primary_emotion']} 감정 상태가 감지되었습니다."
        
        # 구체적 조언
        advice = []
        if similar_trades:
            best_trade = max(similar_trades, key=lambda x: x["result"])
            advice.append(f"과거 {best_trade['stock']} 투자에서 {best_trade['result']:+.1f}% 수익을 얻은 경험을 참고하세요.")
        
        if risk_assessment["risk_level"] == "높음":
            advice.append("현재 높은 위험도가 감지되어 신중한 접근을 권장합니다.")
        
        # 경고 및 주의사항
        warnings = []
        for violation in principle_violations:
            warnings.append(f"{violation['principle']} 위반이 감지되었습니다.")
        
        # 성찰 질문
        questions = [
            "이 투자 결정이 감정에 의한 것은 아닌가요?",
            "과거 비슷한 상황에서 어떤 결과를 얻었나요?",
            "투자 원칙을 지키고 있는지 다시 한번 점검해보세요."
        ]
        
        # 신뢰도 계산
        confidence = 0.7 if similar_trades else 0.5
        
        return {
            "analysis": analysis,
            "advice": advice,
            "warnings": warnings,
            "questions": questions,
            "confidence": confidence,
            "coaching_type": "enhanced"
        }
    
    def _get_beginner_principles(self):
        """초보자용 기본 투자 원칙"""
        return {
            "basic_principles": [
                "분산투자로 위험 분산하기",
                "투자는 여유자금으로만 하기", 
                "감정적 판단 피하기",
                "손절 기준 미리 정하기",
                "충분한 공부 후 투자하기"
            ],
            "recommended_allocation": {
                "안전자산": 60,
                "성장주": 30,
                "고위험자산": 10
            },
            "investment_timeline": "6개월 이상 장기 투자 권장"
        }
    
    def _analyze_trading_patterns(self, trades):
        """거래 패턴 분석"""
        if not trades:
            return {}
        
        # 거래 빈도
        trade_frequency = len(trades)
        
        # 수익 거래 비율
        profitable_trades = [t for t in trades if t["result"] > 0]
        success_rate = len(profitable_trades) / len(trades) if trades else 0
        
        # 평균 수익률
        avg_return = sum(t["result"] for t in trades) / len(trades)
        
        # 가장 많이 거래한 종목
        stock_counts = {}
        for trade in trades:
            stock_counts[trade["stock"]] = stock_counts.get(trade["stock"], 0) + 1
        
        favorite_stock = max(stock_counts, key=stock_counts.get) if stock_counts else None
        
        return {
            "trade_frequency": trade_frequency,
            "success_rate": success_rate,
            "avg_return": avg_return,
            "favorite_stock": favorite_stock,
            "stock_diversity": len(stock_counts)
        }
    
    def _analyze_emotion_patterns(self, trades):
        """감정 패턴 분석"""
        emotion_counts = {}
        for trade in trades:
            emotion = trade["emotion"]
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        return emotion_counts
    
    def _generate_personalized_principles(self, pattern_analysis, emotion_patterns, user_data):
        """개인화된 투자 원칙 생성"""
        principles = []
        
        # 수익률 기반 원칙
        if pattern_analysis.get("avg_return", 0) < 0:
            principles.append("손절 기준을 명확히 하고 지키기")
            principles.append("투자 전 충분한 분석하기")
        
        # 감정 패턴 기반 원칙
        if "욕심" in emotion_patterns:
            principles.append("목표 수익률 달성 시 일부 매도하기")
        
        if "불안" in emotion_patterns:
            principles.append("투자 금액을 줄여서 심리적 부담 덜기")
        
        # 거래 빈도 기반 원칙
        if pattern_analysis.get("trade_frequency", 0) > 20:
            principles.append("과도한 거래 줄이고 장기 투자 고려하기")
        
        # 다양성 기반 원칙
        if pattern_analysis.get("stock_diversity", 0) < 3:
            principles.append("포트폴리오 다양화로 위험 분산하기")
        
        return {
            "personalized_principles": principles[:5],  # 최대 5개
            "confidence_level": "높음" if len(principles) >= 3 else "보통",
            "based_on": f"{pattern_analysis.get('trade_frequency', 0)}건의 거래 분석"
        }
    
    def _find_related_news(self, keywords):
        """관련 뉴스 찾기"""
        news = self.data_manager.news_data
        related = []
        
        for news_item in news:
            for keyword_type, keyword in keywords:
                if keyword_type == "종목":
                    if keyword in news_item.get("related_stocks", []):
                        related.append(news_item)
                elif keyword in news_item["title"] or keyword in news_item["content"]:
                    related.append(news_item)
        
        return related[:3]
    
    def _get_market_info(self, keywords):
        """시장 정보 조회"""
        market_data = self.data_manager.market_data
        info = {}
        
        for keyword_type, keyword in keywords:
            if keyword_type == "종목" and keyword in market_data:
                info[keyword] = market_data[keyword]
        
        return info

# ================================
# [통계 분석 엔진]
# ================================
class StatisticsEngine:
    """투자 통계 분석 엔진"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def generate_user_statistics(self, user_id):
        """사용자별 종합 통계 생성"""
        user_trades = self.data_manager.get_user_trades(user_id)
        
        if not user_trades:
            return self._empty_statistics()
        
        # 기본 통계
        basic_stats = self._calculate_basic_stats(user_trades)
        
        # 수익률 분석 (수정됨)
        performance_stats = self._calculate_performance_stats(user_trades)
        
        # 감정 패턴 분석
        emotion_stats = self._calculate_emotion_stats(user_trades)
        
        # 종목별 분석 (수정됨)
        stock_stats = self._calculate_stock_stats(user_trades)
        
        # 시간별 패턴 (수정됨)
        time_stats = self._calculate_time_patterns(user_trades)
        
        return {
            "basic_stats": basic_stats,
            "performance_stats": performance_stats,
            "emotion_stats": emotion_stats,
            "stock_stats": stock_stats,
            "time_stats": time_stats
        }
    
    def _calculate_basic_stats(self, trades):
        """기본 통계 계산"""
        total_trades = len(trades)
        profitable_trades = [t for t in trades if t["result"] > 0]
        
        return {
            "total_trades": total_trades,
            "profitable_trades": len(profitable_trades),
            "success_rate": len(profitable_trades) / total_trades * 100 if total_trades > 0 else 0,
            "avg_return": sum(t["result"] for t in trades) / total_trades if total_trades > 0 else 0,
            "best_trade": max(trades, key=lambda x: x["result"])["result"] if trades else 0,
            "worst_trade": min(trades, key=lambda x: x["result"])["result"] if trades else 0
        }
    
    def _calculate_performance_stats(self, trades):
        """수익률 분석 (누락된 메서드)"""
        if not trades:
            return {}
        
        returns = [t["result"] for t in trades]
        
        return {
            "total_return": sum(returns),
            "avg_return": sum(returns) / len(returns),
            "max_return": max(returns),
            "min_return": min(returns),
            "volatility": self._calculate_volatility(returns),
            "sharpe_ratio": self._calculate_sharpe_ratio(returns)
        }
    
    def _calculate_emotion_stats(self, trades):
        """감정 패턴 통계"""
        emotion_counts = {}
        emotion_performance = {}
        
        for trade in trades:
            emotion = trade["emotion"]
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            if emotion not in emotion_performance:
                emotion_performance[emotion] = []
            emotion_performance[emotion].append(trade["result"])
        
        # 감정별 평균 수익률
        emotion_avg_returns = {}
        for emotion, returns in emotion_performance.items():
            emotion_avg_returns[emotion] = sum(returns) / len(returns)
        
        return {
            "emotion_counts": emotion_counts,
            "emotion_avg_returns": emotion_avg_returns,
            "most_frequent_emotion": max(emotion_counts, key=emotion_counts.get) if emotion_counts else "없음",
            "best_performing_emotion": max(emotion_avg_returns, key=emotion_avg_returns.get) if emotion_avg_returns else "없음"
        }
    
    def _calculate_stock_stats(self, trades):
        """종목별 분석 (누락된 메서드)"""
        stock_performance = {}
        
        for trade in trades:
            stock = trade["stock"]
            if stock not in stock_performance:
                stock_performance[stock] = []
            stock_performance[stock].append(trade["result"])
        
        stock_stats = {}
        for stock, returns in stock_performance.items():
            stock_stats[stock] = {
                "total_trades": len(returns),
                "avg_return": sum(returns) / len(returns),
                "total_return": sum(returns),
                "success_rate": len([r for r in returns if r > 0]) / len(returns) * 100
            }
        
        return stock_stats
    
    def _calculate_time_patterns(self, trades):
        """시간별 패턴 (누락된 메서드)"""
        # 월별 패턴 분석
        monthly_performance = {}
        
        for trade in trades:
            # 간단한 월 추출 (실제로는 datetime 파싱 필요)
            month = trade["date"][:7]  # YYYY-MM 형식
            if month not in monthly_performance:
                monthly_performance[month] = []
            monthly_performance[month].append(trade["result"])
        
        monthly_stats = {}
        for month, returns in monthly_performance.items():
            monthly_stats[month] = {
                "total_trades": len(returns),
                "avg_return": sum(returns) / len(returns),
                "total_return": sum(returns)
            }
        
        return {
            "monthly_performance": monthly_stats,
            "best_month": max(monthly_stats, key=lambda x: monthly_stats[x]["avg_return"]) if monthly_stats else None,
            "worst_month": min(monthly_stats, key=lambda x: monthly_stats[x]["avg_return"]) if monthly_stats else None
        }
    
    def _calculate_volatility(self, returns):
        """변동성 계산"""
        if len(returns) < 2:
            return 0
        
        avg = sum(returns) / len(returns)
        variance = sum((r - avg) ** 2 for r in returns) / (len(returns) - 1)
        return variance ** 0.5
    
    def _calculate_sharpe_ratio(self, returns):
        """샤프 비율 계산 (간단 버전)"""
        if not returns:
            return 0
        
        avg_return = sum(returns) / len(returns)
        volatility = self._calculate_volatility(returns)
        
        return avg_return / volatility if volatility > 0 else 0
    
    def _empty_statistics(self):
        """빈 통계 반환 (신규 사용자용)"""
        return {
            "basic_stats": {"total_trades": 0, "success_rate": 0, "avg_return": 0},
            "performance_stats": {},
            "emotion_stats": {"emotion_counts": {}, "most_frequent_emotion": "없음"},
            "stock_stats": {},
            "time_stats": {}
        }

# ================================
# [메인 UI 컴포넌트들]
# ================================

def show_user_selector():
    """사용자 선택 화면"""
    st.markdown("### 👤 사용자 선택")
    
    data_manager = get_data_manager()
    users = data_manager.users
    
    cols = st.columns(len(users))
    
    for i, (username, user_data) in enumerate(users.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="kb-card">
                <div style="text-align: center; font-size: 3rem; margin-bottom: 1rem;">
                    {user_data['icon']}
                </div>
                <h4 style="text-align: center; margin-bottom: 1rem;">{username}</h4>
                <p style="text-align: center; color: #666; font-size: 0.9rem; margin-bottom: 1rem;">
                    {user_data['description']}
                </p>
                <div style="text-align: center; font-size: 0.8rem; color: #999;">
                    거래 데이터: {user_data['trades_count']}건
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"👤 {username}으로 시작", key=f"user_{username}", use_container_width=True):
                st.session_state.selected_user = username
                st.session_state.user_data = user_data
                st.rerun()

def show_market_status():
    """실시간 시장 현황"""
    st.markdown("### 📊 실시간 시장 현황")
    
    data_manager = get_data_manager()
    market_data = data_manager.market_data
    
    cols = st.columns(len(market_data))
    
    for i, (stock, data) in enumerate(market_data.items()):
        with cols[i]:
            change_color = "danger" if data["change"] < 0 else "success"
            change_icon = "📉" if data["change"] < 0 else "📈"
            
            kb_metric_card(
                title=stock,
                value=f"{data['price']:,}원",
                delta=f"{change_icon} {data['change']:+.1f}%",
                delta_type=change_color,
                icon="💰"
            )

def show_main_demo():
    """메인 데모 화면"""
    selected_user = st.session_state.selected_user
    user_data = st.session_state.user_data
    
    # 사용자 환영 메시지
    st.markdown(f"""
    <div class="kb-info">
        <h3>👋 {selected_user}님, 환영합니다!</h3>
        <p>{user_data['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 탭으로 기능 분리
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI 코칭", "📊 내 투자 통계", "💡 투자 원칙", "📈 시장 현황"])
    
    with tab1:
        show_ai_coaching_tab(selected_user)
    
    with tab2:
        show_statistics_tab(selected_user)
    
    with tab3:
        show_investment_principles_tab(selected_user)
    
    with tab4:
        show_market_status()

def show_ai_coaching_tab(selected_user):
    """AI 코칭 탭"""
    st.markdown("### 🤖 AI 투자 코칭")
    st.markdown("**현재 투자 고민이나 상황을 자유롭게 입력해주세요:**")
    
    # 예시 템플릿 제공
    example_inputs = {
        "삼성전자 추가 매수": "삼성전자가 5% 떨어졌는데 추가 매수할까 고민됩니다. AI 반도체 관련 뉴스는 긍정적인 것 같은데...",
        "카카오 손절 타이밍": "카카오를 -10%에 보유하고 있는데 규제 뉴스 때문에 더 떨어질까봐 불안합니다. 손절해야 할까요?",
        "NAVER 익절 고민": "NAVER가 15% 올랐는데 더 오를 것 같기도 하고... 익절 타이밍을 못 잡겠어요.",
        "FOMO 매수 고민": "SK하이닉스가 급등하고 있어서 빨리 사야할 것 같은데, 너무 늦은 건 아닐까요?"
    }
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_area(
            "투자 상황 입력",
            height=120,
            placeholder="예: 삼성전자가 5% 떨어졌는데 추가 매수할까 고민됩니다...",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("**💡 예시 템플릿**")
        for title, template in example_inputs.items():
            if st.button(title, key=f"template_{title}", use_container_width=True):
                st.session_state.template_input = template
                st.rerun()
    
    # 템플릿 선택 시 입력창에 반영
    if "template_input" in st.session_state:
        user_input = st.session_state.template_input
        del st.session_state.template_input
    
    # 분석 버튼
    if st.button("🚀 AI 분석 시작", type="primary", use_container_width=True):
        if user_input.strip():
            analyze_user_situation_enhanced(user_input, selected_user)
        else:
            kb_alert("투자 상황을 입력해주세요!", "warning")

def show_statistics_tab(selected_user):
    """통계 탭"""
    st.markdown("### 📊 내 투자 통계")
    
    data_manager = get_data_manager()
    stats_engine = StatisticsEngine(data_manager)
    user_stats = stats_engine.generate_user_statistics(selected_user)
    
    if user_stats["basic_stats"]["total_trades"] == 0:
        kb_alert("아직 거래 데이터가 없습니다. 첫 번째 거래를 기록해보세요!", "info")
        return
    
    # 기본 통계
    st.markdown("#### 📈 기본 투자 성과")
    col1, col2, col3, col4 = st.columns(4)
    
    basic = user_stats["basic_stats"]
    
    with col1:
        kb_metric_card("총 거래", f"{basic['total_trades']}건", "", "normal", "💼")
    
    with col2:
        success_rate = basic['success_rate']
        delta_type = "success" if success_rate > 50 else "danger"
        kb_metric_card("성공률", f"{success_rate:.1f}%", "", delta_type, "🎯")
    
    with col3:
        avg_return = basic['avg_return']
        delta_type = "success" if avg_return > 0 else "danger"
        kb_metric_card("평균 수익률", f"{avg_return:+.1f}%", "", delta_type, "📊")
    
    with col4:
        best_trade = basic['best_trade']
        kb_metric_card("최고 수익", f"{best_trade:+.1f}%", "", "success", "🏆")
    
    # 감정별 투자 성과
    st.markdown("#### 🎭 감정별 투자 성과")
    emotion_stats = user_stats["emotion_stats"]
    
    if emotion_stats["emotion_counts"]:
        # 감정별 거래 횟수 차트
        col1, col2 = st.columns(2)
        
        with col1:
            fig_count = px.bar(
                x=list(emotion_stats["emotion_counts"].keys()),
                y=list(emotion_stats["emotion_counts"].values()),
                title="감정별 거래 횟수",
                color=list(emotion_stats["emotion_counts"].values()),
                color_continuous_scale="RdYlBu_r"
            )
            fig_count.update_layout(height=400)
            st.plotly_chart(fig_count, use_container_width=True)
        
        with col2:
            # 감정별 평균 수익률
            emotions = list(emotion_stats["emotion_avg_returns"].keys())
            returns = list(emotion_stats["emotion_avg_returns"].values())
            
            fig_returns = px.bar(
                x=emotions,
                y=returns,
                title="감정별 평균 수익률",
                color=returns,
                color_continuous_scale="RdYlGn"
            )
            fig_returns.update_layout(height=400)
            st.plotly_chart(fig_returns, use_container_width=True)
        
        # 감정 분석 인사이트
        st.markdown("#### 🧠 감정 분석 인사이트")
        most_frequent = emotion_stats["most_frequent_emotion"]
        best_performing = emotion_stats["best_performing_emotion"]
        
        insights = []
        if most_frequent in ["욕심", "흥분", "FOMO"]:
            insights.append("⚠️ 감정적 투자 경향이 높습니다. 더 냉정한 판단이 필요합니다.")
        
        if best_performing in ["냉정", "확신"]:
            insights.append("✅ 이성적 판단을 할 때 더 좋은 성과를 보입니다.")
        
        if most_frequent != best_performing:
            insights.append(f"💡 '{best_performing}' 상태일 때 투자 성과가 좋습니다. 이 감정 상태를 더 자주 유지해보세요.")
        
        for insight in insights:
            st.markdown(f"- {insight}")

def show_investment_principles_tab(selected_user):
    """투자 원칙 탭"""
    st.markdown("### 💡 개인화된 투자 원칙")
    
    data_manager = get_data_manager()
    ai_coach = EnhancedAICoach(data_manager)
    
    user_trades = data_manager.get_user_trades(selected_user)
    user_data = data_manager.get_user(selected_user)
    
    principles = ai_coach.suggest_investment_principles(user_trades, user_data)
    
    if selected_user == "이신규" or not user_trades:
        st.markdown("#### 🌱 초보 투자자를 위한 기본 원칙")
        basic_principles = principles["basic_principles"]
        
        for i, principle in enumerate(basic_principles, 1):
            st.markdown(f"{i}. **{principle}**")
        
        st.markdown("#### 📊 권장 자산 배분")
        allocation = principles["recommended_allocation"]
        
        fig = px.pie(
            values=list(allocation.values()),
            names=list(allocation.keys()),
            title="초보자 권장 포트폴리오"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        kb_alert(f"투자 기간: {principles['investment_timeline']}", "info")
    
    else:
        st.markdown(f"#### 🎯 {selected_user}님 맞춤형 투자 원칙")
        st.markdown(f"*{principles['based_on']}을 바탕으로 생성됨*")
        
        personalized = principles["personalized_principles"]
        
        for i, principle in enumerate(personalized, 1):
            st.markdown(f"{i}. **{principle}**")
        
        confidence = principles["confidence_level"]
        confidence_color = "success" if confidence == "높음" else "warning"
        kb_alert(f"원칙 신뢰도: {confidence}", confidence_color)
        
        # 원칙 준수 체크리스트
        st.markdown("#### ✅ 투자 전 체크리스트")
        with st.form("investment_checklist"):
            st.markdown("다음 원칙들을 확인해보세요:")
            
            checks = {}
            for i, principle in enumerate(personalized):
                checks[f"check_{i}"] = st.checkbox(principle)
            
            if st.form_submit_button("체크 완료", use_container_width=True):
                checked_count = sum(checks.values())
                total_count = len(checks)
                
                if checked_count == total_count:
                    kb_alert("모든 원칙을 확인했습니다! 현명한 투자하세요! 🎉", "success")
                elif checked_count >= total_count * 0.7:
                    kb_alert("대부분의 원칙을 확인했습니다. 조금 더 신중하게 검토해보세요.", "warning")
                else:
                    kb_alert("더 많은 원칙들을 검토해보시기 바랍니다.", "danger")

def analyze_user_situation_enhanced(user_input, selected_user):
    """개선된 사용자 상황 분석 및 코칭"""
    
    # AI 분석 시작
    with st.spinner("🤖 AI가 상황을 종합 분석하고 있습니다..."):
        data_manager = get_data_manager()
        ai_coach = EnhancedAICoach(data_manager)
        
        result = ai_coach.analyze_situation(user_input, selected_user)
    
    st.markdown("---")
    st.markdown("## 🎯 AI 종합 분석 결과")
    
    # 위험도 평가 (상단에 크게 표시)
    risk_assessment = result["risk_assessment"]
    risk_level = risk_assessment["risk_level"]
    risk_colors = {"낮음": "success", "보통": "warning", "높음": "danger"}
    
    kb_alert(f"🚨 투자 위험도: {risk_level} (점수: {risk_assessment['risk_score']:.2f}/1.0)", 
             risk_colors[risk_level])
    
    # 감정 분석
    emotion_analysis = result["emotion_analysis"]
    if emotion_analysis["confidence"] > 0.5:
        emotion_msg = f"감지된 감정: {emotion_analysis['primary_emotion']} (강도: {emotion_analysis['intensity']:.1f})"
        if emotion_analysis['primary_emotion'] in ['욕심', 'FOMO', '흥분']:
            kb_alert(emotion_msg, "warning")
        else:
            kb_alert(emotion_msg, "info")
    
    # 투자 원칙 위반 체크
    violations = result["principle_violations"]
    if violations:
        st.markdown("### ⚠️ 투자 원칙 위반 경고")
        for violation in violations:
            warning_level = violation["warning_level"]
            alert_type = "danger" if warning_level == "높음" else "warning"
            kb_alert(f"'{violation['keyword']}' - {violation['principle']} 위반 (위험도: {warning_level})", alert_type)
    
    # 핵심 정보 표시
    col1, col2 = st.columns(2)
    
    with col1:
        # 관련 뉴스
        if result["related_news"]:
            st.markdown("#### 📰 관련 뉴스")
            for news in result["related_news"]:
                st.markdown(f"""
                <div class="kb-card">
                    <h5>{news["title"]}</h5>
                    <p style="font-size: 0.9rem;">{news["content"]}</p>
                    <div style="font-size: 0.8rem; color: #666;">
                        {news["time"]} | {news["source"]} | 영향도: {news["impact"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # 시장 정보
        if result["market_info"]:
            st.markdown("#### 📊 관련 종목 현황")
            for stock, data in result["market_info"].items():
                change_color = "#DC3545" if data["change"] < 0 else "#28A745"
                st.markdown(f"""
                <div class="kb-card">
                    <h5>💰 {stock}</h5>
                    <div style="font-size: 1.2rem; font-weight: bold;">
                        {data['price']:,}원 
                        <span style="color: {change_color};">
                            ({data['change']:+.1f}%)
                        </span>
                    </div>
                    <div style="font-size: 0.8rem; color: #666;">
                        거래량: {data['volume']:,} | 시가총액: {data['market_cap']} | 섹터: {data['sector']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        # 과거 거래 패턴
        if result["similar_trades"]:
            st.markdown("#### 🪞 유사한 과거 경험")
            for trade in result["similar_trades"]:
                result_color = "#28A745" if trade["result"] > 0 else "#DC3545"
                
                st.markdown(f"""
                <div class="kb-card">
                    <h5>📈 {trade['stock']} ({trade['date']})</h5>
                    <p style="font-size: 0.9rem;"><strong>결과:</strong> 
                        <span style="color: {result_color}; font-weight: bold;">
                            {trade['result']:+.1f}%
                        </span>
                    </p>
                    <p style="font-size: 0.85rem; color: #666;">
                        <strong>당시 판단:</strong> {trade['reason']}<br>
                        <strong>감정 상태:</strong> {trade['emotion']}<br>
                        <strong>유사도:</strong> {trade['similarity']:.0%}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("#### 🆕 새로운 패턴")
            kb_alert("과거 유사한 거래 경험이 없습니다. 더욱 신중한 접근을 권장합니다.", "info")
    
    # AI 코칭 조언
    coaching = result["coaching"]
    st.markdown("### 🤖 AI 코칭 조언")
    
    confidence = coaching["confidence"]
    confidence_text = "높음" if confidence > 0.7 else "보통" if confidence > 0.4 else "낮음"
    
    st.markdown(f"""
    <div class="kb-info">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h4 style="margin: 0;">💡 맞춤형 조언</h4>
            <div style="background: {'#28A745' if confidence > 0.7 else '#FFC107' if confidence > 0.4 else '#DC3545'}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem;">
                신뢰도: {confidence_text} ({confidence:.0%})
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 상황 분석
    st.markdown("**📋 상황 분석:**")
    st.info(coaching["analysis"])
    
    # 구체적 조언
    if coaching["advice"]:
        st.markdown("**💡 구체적 조언:**")
        for advice in coaching["advice"]:
            st.markdown(f"• {advice}")
    
    # 경고사항
    if coaching.get("warnings"):
        st.markdown("**⚠️ 주의사항:**")
        for warning in coaching["warnings"]:
            st.markdown(f"• {warning}")
    
    # 성찰 질문
    st.markdown("### 🤔 성찰 질문")
    st.markdown("AI가 제안하는 자기 성찰 질문입니다:")
    
    for i, question in enumerate(coaching["questions"], 1):
        with st.expander(f"질문 {i}: {question}"):
            user_answer = st.text_area(
                "답변을 적어보세요", 
                key=f"answer_{i}",
                height=80,
                placeholder="이 질문에 대한 솔직한 답변을 적어보세요..."
            )
            if user_answer:
                st.success("✅ 답변이 기록되었습니다. 이런 성찰이 더 나은 투자 결정으로 이어집니다!")

# ================================
# [메인 애플리케이션]
# ================================

def main():
    """메인 애플리케이션"""
    
    # KB 헤더 표시
    kb_header("KB Reflex", "AI 기반 투자 복기 코칭 시스템", "🏛️")
    
    # 세션 상태 초기화
    if "selected_user" not in st.session_state:
        st.session_state.selected_user = None
    
    # 사용자가 선택되지 않았으면 선택 화면
    if not st.session_state.selected_user:
        show_user_selector()
    else:
        # 메인 데모 화면
        show_main_demo()
        
        # 사용자 변경 버튼
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 다른 사용자로 체험하기", use_container_width=True):
                # 세션 상태 초기화
                for key in list(st.session_state.keys()):
                    if key.startswith(('selected_user', 'user_data', 'template_input')):
                        del st.session_state[key]
                st.rerun()

# ================================
# [실행]
# ================================
if __name__ == "__main__":
    main()