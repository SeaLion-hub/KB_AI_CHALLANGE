"""
AI 브리핑 서비스 - 개선 버전
매매 추천을 하지 않고 객관적 정보만 제공하는 고도화된 AI 브리핑 시스템

개선사항:
- 성능 최적화 및 캐싱 강화
- 위험 평가 알고리즘 개선
- 설정 관리 중앙화
- 에러 처리 및 복구 기능 강화
- 메모리 사용량 최적화
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import sys
from pathlib import Path
import logging
import time
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum
import warnings

# 경고 메시지 억제
warnings.filterwarnings('ignore', category=FutureWarning)

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from db.central_data_manager import get_data_manager, MarketData
from db.principles_db import get_principle_details

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# [CONFIG] 설정 관리
# ================================

class BriefingConfig:
    """AI 브리핑 시스템 설정"""
    
    # 캐시 설정
    CACHE_TTL_SECONDS = 300  # 5분
    MAX_CACHE_SIZE = 100
    
    # 위험 평가 설정
    RISK_THRESHOLDS = {
        'volatility_high': 5.0,      # 5% 이상 변동성
        'volatility_medium': 3.0,    # 3% 이상 변동성
        'rsi_overbought': 70,        # RSI 과매수
        'rsi_oversold': 30,          # RSI 과매도
        'rsi_extreme_high': 80,      # RSI 극과매수
        'rsi_extreme_low': 20,       # RSI 극과매도
        'success_rate_low': 30,      # 낮은 성공률
        'success_rate_very_low': 40, # 매우 낮은 성공률
    }
    
    # 성능 모니터링
    ENABLE_PERFORMANCE_MONITORING = True
    SLOW_OPERATION_THRESHOLD = 1.5  # 1.5초 이상 걸리는 작업 로깅
    
    # 데이터 제한
    MAX_SIMILAR_TRADES = 10
    MAX_NEWS_ITEMS = 5
    MAX_QUESTIONS = 8
    
    # 투자 원칙별 가중치
    PRINCIPLE_WEIGHTS = {
        '워런 버핏': {'per_weight': 0.3, 'pbr_weight': 0.2, 'stability_weight': 0.5},
        '피터 린치': {'growth_weight': 0.4, 'sector_weight': 0.3, 'momentum_weight': 0.3},
        '벤저민 그레이엄': {'value_weight': 0.5, 'safety_weight': 0.3, 'diversification_weight': 0.2}
    }

class RiskLevel(Enum):
    """위험 수준 열거형"""
    VERY_LOW = "매우 낮음"
    LOW = "낮음"
    MEDIUM = "보통"
    HIGH = "높음"
    VERY_HIGH = "매우 높음"
    UNKNOWN = "알 수 없음"

@dataclass
class BriefingCache:
    """브리핑 캐시 데이터 클래스"""
    data: Dict
    timestamp: datetime
    username: str
    stock_code: str
    
    def is_expired(self) -> bool:
        """캐시 만료 여부 확인"""
        return (datetime.now() - self.timestamp).total_seconds() > BriefingConfig.CACHE_TTL_SECONDS

# ================================
# [PERFORMANCE MONITOR] 성능 모니터링
# ================================

class BriefingPerformanceMonitor:
    """AI 브리핑 성능 모니터링"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            
            if BriefingConfig.ENABLE_PERFORMANCE_MONITORING:
                if elapsed > BriefingConfig.SLOW_OPERATION_THRESHOLD:
                    logger.warning(f"느린 브리핑 작업: {self.operation_name} ({elapsed:.2f}초)")
                else:
                    logger.debug(f"브리핑 작업 완료: {self.operation_name} ({elapsed:.2f}초)")

# ================================
# [ENHANCED RISK ASSESSMENT] 향상된 위험 평가
# ================================

class RiskAssessmentEngine:
    """향상된 위험 평가 엔진"""
    
    @staticmethod
    def calculate_market_risk(current_info: Optional[Dict]) -> Dict:
        """시장 위험도 계산"""
        if not current_info:
            return {'score': 50, 'factors': [], 'level': RiskLevel.UNKNOWN}
        
        risk_score = 0
        risk_factors = []
        
        # 1. 변동성 위험
        change_pct = abs(current_info.get('change_pct', 0))
        if change_pct > BriefingConfig.RISK_THRESHOLDS['volatility_high']:
            risk_score += 25
            risk_factors.append(f"📈 높은 변동성: {change_pct:.1f}%")
        elif change_pct > BriefingConfig.RISK_THRESHOLDS['volatility_medium']:
            risk_score += 15
            risk_factors.append(f"📊 중간 변동성: {change_pct:.1f}%")
        
        # 2. RSI 기반 위험
        rsi = current_info.get('rsi', 50)
        if rsi > BriefingConfig.RISK_THRESHOLDS['rsi_extreme_high']:
            risk_score += 20
            risk_factors.append(f"🚨 RSI 극과매수: {rsi:.1f}")
        elif rsi > BriefingConfig.RISK_THRESHOLDS['rsi_overbought']:
            risk_score += 10
            risk_factors.append(f"⚠️ RSI 과매수: {rsi:.1f}")
        elif rsi < BriefingConfig.RISK_THRESHOLDS['rsi_extreme_low']:
            risk_score += 15
            risk_factors.append(f"🚨 RSI 극과매도: {rsi:.1f}")
        elif rsi < BriefingConfig.RISK_THRESHOLDS['rsi_oversold']:
            risk_score += 5
            risk_factors.append(f"💡 RSI 과매도: {rsi:.1f}")
        
        # 3. 밸류에이션 위험
        per = current_info.get('per', 15)
        pbr = current_info.get('pbr', 1.5)
        
        if per > 30:
            risk_score += 15
            risk_factors.append(f"📊 높은 PER: {per:.1f}배")
        elif per < 5:
            risk_score += 10
            risk_factors.append(f"⚠️ 매우 낮은 PER: {per:.1f}배 (기업 위험 가능성)")
        
        if pbr > 3.0:
            risk_score += 10
            risk_factors.append(f"📊 높은 PBR: {pbr:.1f}배")
        
        # 위험 수준 결정
        if risk_score >= 60:
            level = RiskLevel.VERY_HIGH
        elif risk_score >= 45:
            level = RiskLevel.HIGH
        elif risk_score >= 25:
            level = RiskLevel.MEDIUM
        elif risk_score >= 10:
            level = RiskLevel.LOW
        else:
            level = RiskLevel.VERY_LOW
        
        return {
            'score': min(100, risk_score),
            'factors': risk_factors,
            'level': level,
            'components': {
                'volatility_risk': change_pct,
                'momentum_risk': rsi,
                'valuation_risk': (per + pbr) / 2
            }
        }
    
    @staticmethod
    def calculate_user_pattern_risk(user_pattern: Dict) -> Dict:
        """사용자 패턴 위험도 계산"""
        risk_score = 0
        risk_factors = []
        
        # 1. 성공률 기반 위험
        success_rate = user_pattern.get('success_rate')
        if success_rate is not None:
            if success_rate < BriefingConfig.RISK_THRESHOLDS['success_rate_low']:
                risk_score += 25
                risk_factors.append(f"📉 낮은 성공률: {success_rate:.1f}%")
            elif success_rate < BriefingConfig.RISK_THRESHOLDS['success_rate_very_low']:
                risk_score += 15
                risk_factors.append(f"📉 보통 이하 성공률: {success_rate:.1f}%")
        
        # 2. 감정 패턴 위험
        recent_emotions = user_pattern.get('recent_emotion_pattern', {})
        risky_emotions = ['#공포', '#패닉', '#후회', '#욕심', '#추격매수']
        
        risky_emotion_count = sum(count for emotion, count in recent_emotions.items() 
                                 if emotion in risky_emotions)
        total_emotions = sum(recent_emotions.values()) if recent_emotions else 0
        
        if total_emotions > 0:
            risky_ratio = risky_emotion_count / total_emotions
            if risky_ratio > 0.6:
                risk_score += 20
                risk_factors.append("😰 위험한 감정 거래 패턴 빈번")
            elif risky_ratio > 0.3:
                risk_score += 10
                risk_factors.append("🤔 감정적 거래 패턴 감지")
        
        # 3. 거래 빈도 위험
        last_trade = user_pattern.get('last_trade_date')
        if last_trade:
            try:
                if isinstance(last_trade, str):
                    last_trade_date = datetime.strptime(last_trade, '%Y-%m-%d')
                else:
                    last_trade_date = last_trade
                
                days_since_last = (datetime.now() - last_trade_date).days
                if days_since_last < 1:
                    risk_score += 20
                    risk_factors.append("⚡ 연속 거래 위험 (당일 재거래)")
                elif days_since_last < 3:
                    risk_score += 10
                    risk_factors.append("🔄 빈번한 거래 패턴")
            except (ValueError, TypeError):
                pass
        
        return {
            'score': min(100, risk_score),
            'factors': risk_factors,
            'pattern_analysis': {
                'success_rate': success_rate,
                'risky_emotion_ratio': risky_ratio if 'risky_ratio' in locals() else 0,
                'recent_activity': days_since_last if 'days_since_last' in locals() else None
            }
        }

# ================================
# [ENHANCED PRINCIPLE CHECKER] 향상된 원칙 체크
# ================================

class PrincipleChecker:
    """투자 원칙 체크 엔진"""
    
    @staticmethod
    def check_buffett_alignment(current_info: Dict, action_type: str) -> Dict:
        """워런 버핏 원칙 체크"""
        warnings = []
        score = 50
        
        warnings.extend([
            "🤔 이 기업의 사업모델을 완전히 이해하고 있나요?",
            "🏰 기업의 경제적 해자(Economic Moat)를 확인하셨나요?",
            "📈 지속적인 수익 성장 능력이 있나요?"
        ])
        
        if action_type == "매도":
            warnings.append("⏰ 장기 보유 관점에서 정말 매도가 필요한가요?")
        
        # PER/PBR 기반 점수 조정
        per = current_info.get('per', 20)
        pbr = current_info.get('pbr', 2.0)
        
        if per < 15 and pbr < 1.5:
            score += 25
        elif per < 20 and pbr < 2.0:
            score += 15
        elif per > 25 or pbr > 3.0:
            score -= 15
        
        return {
            'score': max(30, min(90, score)),
            'warnings': warnings,
            'key_metrics': {'per': per, 'pbr': pbr}
        }
    
    @staticmethod
    def check_lynch_alignment(current_info: Dict, action_type: str) -> Dict:
        """피터 린치 원칙 체크"""
        warnings = []
        score = 50
        
        warnings.extend([
            "🔍 일상에서 이 회사 제품/서비스를 경험해보셨나요?",
            "📈 최근 분기 실적 성장률을 확인하셨나요?",
            "🚀 이 업종의 성장 가능성은 어떻게 평가하시나요?"
        ])
        
        # 성장 섹터 가점
        growth_sectors = ['IT', '바이오', '전자', '게임']
        if current_info.get('sector') in growth_sectors:
            score += 15
            warnings.append("💡 성장 섹터입니다. PEG 비율을 확인해보세요.")
        
        # PER 기반 조정
        per = current_info.get('per', 15)
        if 10 <= per <= 20:
            score += 10
        elif per > 30:
            score -= 10
        
        return {
            'score': max(40, min(85, score)),
            'warnings': warnings,
            'growth_indicators': {'sector': current_info.get('sector'), 'per': per}
        }
    
    @staticmethod
    def check_graham_alignment(current_info: Dict, action_type: str) -> Dict:
        """벤저민 그레이엄 원칙 체크"""
        warnings = []
        score = 50
        
        warnings.extend([
            "⚖️ 현재 가격이 내재가치 대비 충분한 안전 마진을 제공하나요?",
            "📊 기업의 재무 건전성을 확인하셨나요?",
            "🛡️ 분산 투자 관점에서 포트폴리오를 검토하셨나요?"
        ])
        
        # 밸류 지표 기반 점수 조정
        pbr = current_info.get('pbr', 2.0)
        per = current_info.get('per', 15)
        
        if pbr < 1.0:
            score += 30
        elif pbr < 1.5:
            score += 20
        elif pbr > 2.5:
            score -= 15
        
        if per < 10:
            score += 15
        elif per > 20:
            score -= 10
        
        return {
            'score': max(35, min(95, score)),
            'warnings': warnings,
            'value_metrics': {'pbr': pbr, 'per': per, 'safety_margin': pbr < 1.5 and per < 15}
        }

# ================================
# [MAIN BRIEFING SERVICE] 메인 브리핑 서비스
# ================================

class AIBriefingService:
    """
    AI 브리핑 서비스 - 개선 버전
    
    개선사항:
    1. 캐싱 시스템 강화
    2. 위험 평가 알고리즘 개선
    3. 성능 모니터링 추가
    4. 에러 처리 강화
    """
    
    def __init__(self):
        self.data_manager = get_data_manager()
        self.risk_engine = RiskAssessmentEngine()
        self.principle_checker = PrincipleChecker()
        self._cache = {}  # 브리핑 캐시
        logger.info("AI 브리핑 서비스 초기화 완료")
    
    def _get_cache_key(self, username: str, stock_code: str, action_type: str) -> str:
        """캐시 키 생성"""
        return f"{username}_{stock_code}_{action_type}"
    
    def _get_cached_briefing(self, cache_key: str) -> Optional[Dict]:
        """캐시된 브리핑 조회"""
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            if not cached_item.is_expired():
                logger.debug(f"캐시에서 브리핑 반환: {cache_key}")
                return cached_item.data
            else:
                # 만료된 캐시 제거
                del self._cache[cache_key]
        return None
    
    def _cache_briefing(self, cache_key: str, briefing_data: Dict, username: str, stock_code: str):
        """브리핑 캐시 저장"""
        # 캐시 크기 제한
        if len(self._cache) >= BriefingConfig.MAX_CACHE_SIZE:
            # 가장 오래된 캐시 항목 제거
            oldest_key = min(self._cache.keys(), 
                           key=lambda k: self._cache[k].timestamp)
            del self._cache[oldest_key]
        
        self._cache[cache_key] = BriefingCache(
            data=briefing_data,
            timestamp=datetime.now(),
            username=username,
            stock_code=stock_code
        )
    
    def generate_briefing(self, username: str, stock_code: str, action_type: str = "매수") -> Dict:
        """
        매매 전 AI 브리핑 생성 - 개선 버전
        """
        try:
            with BriefingPerformanceMonitor(f"브리핑 생성: {username}-{stock_code}"):
                # 캐시 확인
                cache_key = self._get_cache_key(username, stock_code, action_type)
                cached_result = self._get_cached_briefing(cache_key)
                if cached_result:
                    cached_result['from_cache'] = True
                    return cached_result
                
                # 1. 현재 시장 상황 수집
                current_info = self._get_current_stock_info(stock_code)
                market_indices = self.data_manager.get_economic_indicators()
                
                # 2. 사용자의 과거 거래 패턴 분석
                user_pattern = self._analyze_user_pattern(username, stock_code)
                
                # 3. 사용자의 투자 원칙과 비교
                principle_check = self._check_against_principles(username, current_info, action_type)
                
                # 4. 향상된 위험 요소 체크
                risk_factors = self._enhanced_risk_assessment(current_info, user_pattern)
                
                # 5. 시장 맥락 정보
                market_context = self._get_market_context(stock_code)
                
                # 6. 개선된 핵심 질문 생성
                key_questions = self._generate_enhanced_questions(action_type, risk_factors, principle_check)
                
                briefing = {
                    'timestamp': datetime.now(),
                    'version': '2.0',  # 개선 버전 표시
                    'stock_info': current_info,
                    'market_context': market_context,
                    'market_indices': market_indices,
                    'user_pattern_analysis': user_pattern,
                    'principle_alignment': principle_check,
                    'risk_assessment': risk_factors,
                    'key_questions': key_questions,
                    'performance_metrics': {
                        'analysis_depth': 'enhanced',
                        'confidence_level': self._calculate_confidence_level(current_info, user_pattern),
                        'data_quality': self._assess_data_quality(current_info, user_pattern)
                    },
                    'disclaimer': "⚠️ 이 브리핑은 투자 추천이 아닌 정보 제공입니다. 모든 투자 결정은 본인의 책임입니다.",
                    'from_cache': False
                }
                
                # 결과 캐싱
                self._cache_briefing(cache_key, briefing, username, stock_code)
                
                return briefing
                
        except Exception as e:
            logger.error(f"브리핑 생성 중 오류: {str(e)}")
            return {
                'error': f'브리핑 생성 실패: {str(e)}',
                'timestamp': datetime.now(),
                'fallback_questions': [
                    "🤔 현재 결정의 명확한 근거가 있나요?",
                    "⚖️ 위험과 기회를 균형있게 고려했나요?",
                    "💰 손실을 감당할 수 있는 범위인가요?"
                ]
            }
    
    def _calculate_confidence_level(self, current_info: Optional[Dict], user_pattern: Dict) -> str:
        """분석 신뢰도 계산"""
        confidence_score = 0
        
        # 현재 주식 정보 완성도
        if current_info:
            required_fields = ['price', 'volume', 'rsi', 'per', 'pbr']
            available_fields = sum(1 for field in required_fields if current_info.get(field) is not None)
            confidence_score += (available_fields / len(required_fields)) * 40
        
        # 사용자 패턴 데이터 충분성
        total_trades = user_pattern.get('total_trades', 0)
        if total_trades >= 50:
            confidence_score += 30
        elif total_trades >= 20:
            confidence_score += 20
        elif total_trades >= 5:
            confidence_score += 10
        
        # 유사 거래 존재 여부
        similar_trades = user_pattern.get('same_stock_trades', 0)
        if similar_trades > 0:
            confidence_score += 30
        
        if confidence_score >= 80:
            return "high"
        elif confidence_score >= 60:
            return "medium"
        else:
            return "low"
    
    def _assess_data_quality(self, current_info: Optional[Dict], user_pattern: Dict) -> str:
        """데이터 품질 평가"""
        if not current_info:
            return "poor"
        
        # 기본 데이터 존재 여부
        has_basic_data = all(current_info.get(field) is not None 
                           for field in ['price', 'change_pct'])
        
        # 기술적 지표 존재 여부
        has_technical_data = all(current_info.get(field) is not None 
                               for field in ['rsi', 'ma5', 'ma20'])
        
        # 펀더멘털 지표 존재 여부
        has_fundamental_data = all(current_info.get(field) is not None 
                                 for field in ['per', 'pbr'])
        
        if has_basic_data and has_technical_data and has_fundamental_data:
            return "excellent"
        elif has_basic_data and (has_technical_data or has_fundamental_data):
            return "good"
        elif has_basic_data:
            return "fair"
        else:
            return "poor"
    
    def _get_current_stock_info(self, stock_identifier: str) -> Optional[Dict]:
        """
        종목 정보 조회 (최적화된 버전)
        """
        try:
            market_data = self.data_manager.get_market_data()
            
            # 종목명으로 직접 조회
            if stock_identifier in market_data:
                return self._format_stock_info(market_data[stock_identifier])
            
            # 종목코드로 조회
            for stock_name, stock_data in market_data.items():
                if stock_data.symbol == stock_identifier:
                    return self._format_stock_info(stock_data)
            
            logger.warning(f"종목 정보를 찾을 수 없음: {stock_identifier}")
            return None
            
        except Exception as e:
            logger.error(f"종목 정보 조회 중 오류: {str(e)}")
            return None
    
    def _format_stock_info(self, stock_data: MarketData) -> Dict:
        """MarketData를 딕셔너리로 변환"""
        return {
            'symbol': stock_data.symbol,
            'name': stock_data.name,
            'price': stock_data.current_price,
            'change': stock_data.change,
            'change_pct': stock_data.change_pct,
            'volume': stock_data.volume,
            'sector': stock_data.sector,
            'market_cap': stock_data.market_cap,
            'ma5': stock_data.ma5,
            'ma20': stock_data.ma20,
            'rsi': stock_data.rsi,
            'per': stock_data.per,
            'pbr': stock_data.pbr,
            'market_sentiment': self._get_market_sentiment(stock_data.change_pct)
        }
    
    @lru_cache(maxsize=100)
    def _get_market_sentiment(self, change_pct: float) -> str:
        """변동률 기반 시장 심리 판단 (캐시 적용)"""
        if change_pct > 3:
            return "매우 강세"
        elif change_pct > 1:
            return "강세"
        elif change_pct > -1:
            return "보합"
        elif change_pct > -3:
            return "약세"
        else:
            return "매우 약세"
    
    def _get_market_context(self, stock_identifier: str) -> Dict:
        """시장 맥락 정보 수집 (최적화)"""
        try:
            # 경제 지표
            economic_data = self.data_manager.get_economic_indicators()
            
            # 관련 뉴스 (제한된 개수만)
            news_data = self.data_manager.get_news(hours_back=24)
            
            # 종목명 확인
            stock_info = self._get_current_stock_info(stock_identifier)
            stock_name = stock_info['name'] if stock_info else stock_identifier
            
            # 관련 뉴스 필터링 (최대 개수 제한)
            related_news = []
            for news in news_data[:20]:  # 최대 20개까지만 확인
                if (stock_name in news.related_stocks or 
                    '전체' in news.related_stocks or
                    (stock_info and stock_info['sector'] == news.category)):
                    related_news.append({
                        'title': news.title,
                        'impact': news.impact,
                        'category': news.category,
                        'timestamp': news.timestamp
                    })
                    
                    if len(related_news) >= BriefingConfig.MAX_NEWS_ITEMS:
                        break
            
            return {
                'kospi': economic_data.get('KOSPI', {}),
                'kosdaq': economic_data.get('KOSDAQ', {}),
                'usd_krw': economic_data.get('USD_KRW', {}),
                'interest_rate': economic_data.get('interest_rate'),
                'related_news': related_news,
                'market_trend': self._analyze_overall_market_trend(economic_data)
            }
            
        except Exception as e:
            logger.error(f"시장 맥락 수집 중 오류: {str(e)}")
            return {}
    
    def _analyze_overall_market_trend(self, economic_data: Dict) -> str:
        """전체 시장 트렌드 분석 (향상된 버전)"""
        try:
            kospi_change = economic_data.get('KOSPI', {}).get('change_pct', 0)
            kosdaq_change = economic_data.get('KOSDAQ', {}).get('change_pct', 0)
            
            avg_change = (kospi_change + kosdaq_change) / 2
            
            # 더 세분화된 트렌드 분석
            if avg_change > 2:
                return "강한 상승 추세"
            elif avg_change > 1:
                return "상승 추세"
            elif avg_change > -1:
                return "횡보 추세"
            elif avg_change > -2:
                return "하락 추세"
            else:
                return "강한 하락 추세"
                
        except Exception as e:
            logger.error(f"시장 트렌드 분석 중 오류: {str(e)}")
            return "분석 불가"
    
    def _analyze_user_pattern(self, username: str, stock_identifier: str) -> Dict:
        """사용자 거래 패턴 분석 (향상된 버전)"""
        try:
            trades_data = self.data_manager.get_user_trades(username)
            
            if not trades_data:
                return {
                    'message': '📊 거래 데이터가 부족합니다. 신중한 첫 투자를 권장합니다.',
                    'total_trades': 0,
                    'data_quality': 'insufficient'
                }
            
            # DataFrame 변환 및 데이터 정제
            trades_df = pd.DataFrame(trades_data)
            trades_df = self._clean_trades_data(trades_df)
            
            # 종목명 확인
            stock_info = self._get_current_stock_info(stock_identifier)
            target_stock_name = stock_info['name'] if stock_info else stock_identifier
            
            # 분석 결과 구성
            analysis_result = {
                'total_trades': len(trades_df),
                'data_quality': 'sufficient' if len(trades_df) >= 10 else 'limited'
            }
            
            # 동일 종목 거래 분석
            same_stock_trades = trades_df[trades_df['종목명'] == target_stock_name] if '종목명' in trades_df.columns else pd.DataFrame()
            analysis_result['same_stock_trades'] = len(same_stock_trades)
            
            # 성공률 및 수익률 분석
            if '수익률' in trades_df.columns and not trades_df['수익률'].isna().all():
                analysis_result.update({
                    'success_rate': round((trades_df['수익률'] > 0).mean() * 100, 1),
                    'avg_return': round(trades_df['수익률'].mean(), 2),
                    'max_gain': round(trades_df['수익률'].max(), 2),
                    'max_loss': round(trades_df['수익률'].min(), 2)
                })
            
            # 최근 감정 패턴 분석 (최근 20건)
            recent_trades = trades_df.tail(20)
            if '감정태그' in recent_trades.columns:
                recent_emotions = recent_trades['감정태그'].value_counts().to_dict()
                analysis_result['recent_emotion_pattern'] = recent_emotions
            
            # 거래 빈도 분석
            if '거래일시' in trades_df.columns:
                trades_df['거래일시'] = pd.to_datetime(trades_df['거래일시'], errors='coerce')
                last_trade_date = trades_df['거래일시'].max()
                if pd.notna(last_trade_date):
                    analysis_result['last_trade_date'] = last_trade_date
            
            # 유사 상황 찾기 (제한된 개수만)
            analysis_result['similar_situations'] = self._find_limited_similar_situations(
                trades_df, target_stock_name, max_results=BriefingConfig.MAX_SIMILAR_TRADES
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"사용자 패턴 분석 중 오류: {str(e)}")
            return {
                'error': f'패턴 분석 실패: {str(e)}',
                'total_trades': 0,
                'data_quality': 'error'
            }
    
    def _clean_trades_data(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """거래 데이터 정제"""
        try:
            # 기본 컬럼 확인 및 기본값 설정
            if '수익률' not in trades_df.columns:
                trades_df['수익률'] = 0.0
            if '감정태그' not in trades_df.columns:
                trades_df['감정태그'] = ''
            if '메모' not in trades_df.columns:
                trades_df['메모'] = ''
                
            # 수치형 데이터 변환
            trades_df['수익률'] = pd.to_numeric(trades_df['수익률'], errors='coerce').fillna(0)
            
            # 날짜 데이터 변환
            if '거래일시' in trades_df.columns:
                trades_df['거래일시'] = pd.to_datetime(trades_df['거래일시'], errors='coerce')
                # 잘못된 날짜 제거
                trades_df = trades_df.dropna(subset=['거래일시'])
            
            return trades_df
            
        except Exception as e:
            logger.error(f"거래 데이터 정제 중 오류: {str(e)}")
            return trades_df
    
    def _find_limited_similar_situations(self, trades_df: pd.DataFrame, current_stock_name: str, max_results: int = 5) -> List[Dict]:
        """제한된 개수의 유사 상황 찾기"""
        try:
            if trades_df.empty:
                return []
            
            similar_trades = []
            recent_trades = trades_df.tail(20)  # 최근 20개만 확인
            
            for _, trade in recent_trades.iterrows():
                if len(similar_trades) >= max_results:
                    break
                    
                if trade.get('종목명') != current_stock_name:
                    trade_info = {
                        'date': trade.get('거래일시', 'N/A'),
                        'stock': trade.get('종목명', 'N/A'),
                        'emotion': trade.get('감정태그', 'N/A'),
                        'return': trade.get('수익률', 0),
                        'memo': str(trade.get('메모', ''))[:50] + "..." if len(str(trade.get('메모', ''))) > 50 else str(trade.get('메모', ''))
                    }
                    similar_trades.append(trade_info)
            
            return similar_trades
            
        except Exception as e:
            logger.error(f"유사 상황 찾기 중 오류: {str(e)}")
            return []
    
    def _check_against_principles(self, username: str, current_info: Optional[Dict], action_type: str) -> Dict:
        """투자 원칙 체크 (향상된 버전)"""
        try:
            selected_principle = st.session_state.get('selected_principle')
            
            if not selected_principle or not current_info:
                return {
                    'message': '💡 투자 원칙을 설정하고 종목 정보가 준비되면 더 정확한 가이드를 받을 수 있습니다.',
                    'alignment_score': None,
                    'warnings': [],
                    'principle_name': selected_principle
                }
            
            # 원칙별 체크 실행
            if selected_principle == "워런 버핏":
                result = self.principle_checker.check_buffett_alignment(current_info, action_type)
            elif selected_principle == "피터 린치":
                result = self.principle_checker.check_lynch_alignment(current_info, action_type)
            elif selected_principle == "벤저민 그레이엄":
                result = self.principle_checker.check_graham_alignment(current_info, action_type)
            else:
                return {
                    'message': f'알 수 없는 투자 원칙: {selected_principle}',
                    'alignment_score': 50,
                    'warnings': [],
                    'principle_name': selected_principle
                }
            
            # 공통 체크 항목 추가
            result['warnings'].extend(self._get_common_principle_checks(current_info, action_type))
            result['principle_name'] = selected_principle
            
            return result
            
        except Exception as e:
            logger.error(f"투자 원칙 체크 중 오류: {str(e)}")
            return {
                'error': f'원칙 체크 실패: {str(e)}',
                'alignment_score': 50,
                'warnings': ["시스템 오류로 원칙 체크를 완료할 수 없습니다."],
                'principle_name': st.session_state.get('selected_principle')
            }
    
    def _get_common_principle_checks(self, current_info: Dict, action_type: str) -> List[str]:
        """공통 원칙 체크 항목"""
        checks = []
        
        # 기술적 지표 기반 경고
        rsi = current_info.get('rsi', 50)
        if rsi > 70:
            checks.append(f"⚠️ RSI 과매수 구간입니다 (현재: {rsi:.1f})")
        elif rsi < 30:
            checks.append(f"💡 RSI 과매도 구간입니다 (현재: {rsi:.1f})")
        
        # 변동성 경고
        change_pct = abs(current_info.get('change_pct', 0))
        if change_pct > 5:
            checks.append(f"🌊 높은 변동성에 주의하세요 ({change_pct:.1f}%)")
        
        return checks
    
    def _enhanced_risk_assessment(self, current_info: Optional[Dict], user_pattern: Dict) -> Dict:
        """향상된 위험 요소 평가"""
        try:
            # 시장 위험 평가
            market_risk = self.risk_engine.calculate_market_risk(current_info)
            
            # 사용자 패턴 위험 평가
            pattern_risk = self.risk_engine.calculate_user_pattern_risk(user_pattern)
            
            # 종합 위험 점수 계산 (가중 평균)
            total_risk_score = (market_risk['score'] * 0.6 + pattern_risk['score'] * 0.4)
            
            # 전체 위험 요소 통합
            all_risk_factors = market_risk['factors'] + pattern_risk['factors']
            
            # 종합 위험 수준 결정
            if total_risk_score >= 70:
                overall_level = RiskLevel.VERY_HIGH
            elif total_risk_score >= 55:
                overall_level = RiskLevel.HIGH
            elif total_risk_score >= 35:
                overall_level = RiskLevel.MEDIUM
            elif total_risk_score >= 20:
                overall_level = RiskLevel.LOW
            else:
                overall_level = RiskLevel.VERY_LOW
            
            # 맞춤형 권장사항 생성
            recommendation = self._generate_risk_recommendation(overall_level, total_risk_score, market_risk, pattern_risk)
            
            return {
                'risk_level': overall_level.value,
                'risk_score': round(total_risk_score, 1),
                'factors': all_risk_factors,
                'recommendation': recommendation,
                'detailed_analysis': {
                    'market_risk': market_risk,
                    'pattern_risk': pattern_risk,
                    'combined_score': total_risk_score
                },
                'risk_breakdown': {
                    'market_component': round(market_risk['score'] * 0.6, 1),
                    'pattern_component': round(pattern_risk['score'] * 0.4, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"위험 평가 중 오류: {str(e)}")
            return {
                'risk_level': RiskLevel.UNKNOWN.value,
                'risk_score': 50,
                'factors': [f"위험 평가 오류: {str(e)}"],
                'recommendation': "시스템 오류로 위험 평가를 완료할 수 없습니다. 신중한 접근을 권장합니다."
            }
    
    def _generate_risk_recommendation(self, risk_level: RiskLevel, total_score: float, market_risk: Dict, pattern_risk: Dict) -> str:
        """위험 수준별 맞춤형 권장사항 생성"""
        base_recommendations = {
            RiskLevel.VERY_LOW: "✅ 위험도가 낮은 상황입니다. 계획에 따라 진행하되 기본적인 주의는 유지하세요.",
            RiskLevel.LOW: "🟢 상대적으로 안전한 상황입니다. 적정 규모로 투자를 고려해볼 수 있습니다.",
            RiskLevel.MEDIUM: "🟡 보통 수준의 위험이 있습니다. 분할 매매나 손절선 설정을 고려하세요.",
            RiskLevel.HIGH: "🟠 높은 위험이 감지됩니다. 소액 투자나 관망을 권장합니다.",
            RiskLevel.VERY_HIGH: "🔴 매우 높은 위험 상황입니다. 투자를 재고하거나 24시간 후 재검토하세요."
        }
        
        base_rec = base_recommendations.get(risk_level, "신중한 접근이 필요합니다.")
        
        # 상세 조언 추가
        specific_advice = []
        
        if market_risk['score'] > 50:
            specific_advice.append("📊 시장 변동성이 높은 상황입니다.")
        
        if pattern_risk['score'] > 50:
            specific_advice.append("🧠 과거 거래 패턴에서 위험 신호가 감지됩니다.")
        
        if total_score > 80:
            specific_advice.append("💡 감정적 결정을 피하고 하루 정도 시간을 두고 재검토해보세요.")
        
        if specific_advice:
            return base_rec + "\n\n" + " ".join(specific_advice)
        
        return base_rec
    
    def _generate_enhanced_questions(self, action_type: str, risk_factors: Dict, principle_check: Dict) -> List[str]:
        """향상된 핵심 질문 생성"""
        try:
            questions = []
            
            # 기본 질문
            base_questions = [
                "🎯 이 거래의 명확한 근거와 목표가 있나요?",
                "💰 최악의 경우 손실을 감당할 수 있는 금액인가요?",
                "⏰ 지금이 아니어도 되는 거래는 아닌가요?"
            ]
            
            # 매수/매도별 질문
            if action_type == "매수":
                base_questions.extend([
                    "📊 현재 가격이 적정 수준이라고 판단하는 이유는?",
                    "📈 장기적으로 이 종목을 보유할 의향이 있나요?",
                    "🔍 이 회사의 사업과 재무상태를 충분히 이해하고 있나요?"
                ])
            else:  # 매도
                base_questions.extend([
                    "📉 매도 이유가 감정적이지는 않나요?",
                    "🎯 애초 설정한 목표나 손절 기준에 도달했나요?",
                    "⏳ 조금 더 기다려볼 여지는 없나요?"
                ])
            
            questions.extend(base_questions)
            
            # 위험도별 추가 질문
            risk_level = risk_factors.get('risk_level', '보통')
            if risk_level in ['높음', '매우 높음']:
                questions.extend([
                    "🚨 높은 위험이 감지됩니다. 정말 지금 거래해야 하나요?",
                    "🤔 24시간 후에도 같은 결정을 내릴 수 있나요?",
                    "💭 가장 신뢰하는 사람에게도 이 거래를 권할 수 있나요?"
                ])
            
            # 투자 원칙 부합도 기반 질문
            alignment_score = principle_check.get('alignment_score')
            if alignment_score is not None and alignment_score < 50:
                questions.append("📋 이 거래가 선택한 투자 원칙과 부합하는지 다시 한번 확인해보세요.")
            
            # 사용자 패턴 기반 질문
            if risk_factors.get('detailed_analysis', {}).get('pattern_risk', {}).get('score', 0) > 40:
                questions.append("🪞 과거 비슷한 상황에서의 결과를 다시 한번 되돌아보세요.")
            
            return questions[:BriefingConfig.MAX_QUESTIONS]
            
        except Exception as e:
            logger.error(f"질문 생성 중 오류: {str(e)}")
            return [
                "🤔 현재 상황을 객관적으로 판단해보세요.",
                "⚖️ 위험과 기회를 균형있게 고려하고 있나요?",
                "🎯 이 결정의 명확한 근거가 있나요?"
            ]
    
    def clear_cache(self):
        """캐시 클리어"""
        self._cache.clear()
        # LRU 캐시도 클리어
        self._get_market_sentiment.cache_clear()
        logger.info("AI 브리핑 캐시가 클리어되었습니다")
    
    def get_cache_info(self) -> Dict:
        """캐시 정보 조회"""
        return {
            'briefing_cache_size': len(self._cache),
            'market_sentiment_cache': self._get_market_sentiment.cache_info()._asdict(),
            'cache_hit_ratio': len([c for c in self._cache.values() if not c.is_expired()]) / max(1, len(self._cache))
        }

# ================================
# [UI COMPONENT] UI 컴포넌트 (기존 함수 개선)
# ================================

def show_ai_briefing_ui(username: str, stock_code: str, stock_name: str, action_type: str = "매수"):
    """AI 브리핑 UI 표시 - 개선 버전"""
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); 
                border: 1px solid #BFDBFE; border-radius: 20px; padding: 24px; margin: 20px 0;'>
        <h3 style='color: #3182F6; margin-top: 0; display: flex; align-items: center;'>
            🤖 AI 브리핑 2.0: {stock_name} {action_type}
        </h3>
        <p style='color: #64748B; margin-bottom: 20px;'>
            매매 추천이 아닌, 판단에 도움이 될 객관적 정보를 제공합니다. (향상된 분석 엔진)
        </p>
    """, unsafe_allow_html=True)
    
    if st.button("🔍 AI 브리핑 요청", key=f"ai_briefing_{stock_code}_{action_type}", type="primary"):
        
        with st.spinner("🧠 고도화된 AI가 종합 분석 중입니다..."):
            try:
                briefing_service = AIBriefingService()
                briefing = briefing_service.generate_briefing(username, stock_code, action_type)
                
                # 오류 처리
                if 'error' in briefing:
                    st.error(f"⚠️ {briefing['error']}")
                    if 'fallback_questions' in briefing:
                        st.markdown("### 💭 기본 체크리스트")
                        for question in briefing['fallback_questions']:
                            st.markdown(f"- {question}")
                    return
                
                # 캐시 정보 표시 (개발/디버그용)
                if briefing.get('from_cache'):
                    st.info("💾 캐시된 데이터를 활용하여 빠르게 분석했습니다.")
                
                # 분석 품질 정보 표시
                performance_metrics = briefing.get('performance_metrics', {})
                confidence = performance_metrics.get('confidence_level', 'unknown')
                data_quality = performance_metrics.get('data_quality', 'unknown')
                
                # 신뢰도 표시
                confidence_emoji = {'high': '🟢', 'medium': '🟡', 'low': '🔴'}.get(confidence, '❓')
                quality_emoji = {'excellent': '🟢', 'good': '🟡', 'fair': '🟠', 'poor': '🔴'}.get(data_quality, '❓')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("분석 신뢰도", f"{confidence_emoji} {confidence.upper()}")
                with col2:
                    st.metric("데이터 품질", f"{quality_emoji} {data_quality.upper()}")
                
                # 기존 브리핑 표시 로직은 유지하되 향상된 데이터 활용
                _display_enhanced_briefing_content(briefing, stock_name, action_type)
                
            except Exception as e:
                st.error(f"🚨 브리핑 생성 중 예상치 못한 오류가 발생했습니다: {str(e)}")
                logger.error(f"UI 브리핑 오류: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def _display_enhanced_briefing_content(briefing: Dict, stock_name: str, action_type: str):
    """향상된 브리핑 콘텐츠 표시"""
    
    # 현재 상황 분석
    st.markdown("### 📊 현재 상황 분석")
    
    if briefing['stock_info']:
        stock_info = briefing['stock_info']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("현재가", f"₩{stock_info['price']:,.0f}")
        with col2:
            st.metric("등락률", f"{stock_info['change_pct']:+.1f}%", f"₩{stock_info['change']:+,.0f}")
        with col3:
            st.metric("거래량", f"{stock_info['volume']:,}")
        with col4:
            st.metric("시장상황", stock_info['market_sentiment'])
        
        # 기술적 지표
        col1, col2, col3 = st.columns(3)
        with col1:
            rsi = stock_info['rsi']
            rsi_color = "inverse" if rsi > 70 or rsi < 30 else "normal"
            st.metric("RSI", f"{rsi:.1f}", delta_color=rsi_color)
        with col2:
            st.metric("PER", f"{stock_info['per']:.1f}배")
        with col3:
            st.metric("PBR", f"{stock_info['pbr']:.1f}배")
    else:
        st.error(f"⚠️ '{stock_name}' 종목 정보를 찾을 수 없습니다.")
    
    # 시장 맥락 (기존 로직 유지)
    _display_market_context(briefing.get('market_context', {}))
    
    # 사용자 패턴 분석
    _display_user_pattern_analysis(briefing.get('user_pattern_analysis', {}))
    
    # 투자 원칙 체크 (기존 로직 유지하되 향상된 데이터 활용)
    _display_principle_alignment(briefing.get('principle_alignment', {}))
    
    # 향상된 위험 요소 분석
    _display_enhanced_risk_assessment(briefing.get('risk_assessment', {}))
    
    # 핵심 질문들
    _display_key_questions(briefing.get('key_questions', []))
    
    # 최종 체크리스트
    _display_final_checklist(briefing.get('risk_assessment', {}), action_type)
    
    # 면책 조항
    st.markdown("---")
    st.warning(briefing.get('disclaimer', ''))
    
    # 개선된 도움말
    _display_enhanced_help_tips()

def _display_market_context(market_context: Dict):
    """시장 맥락 표시"""
    st.markdown("### 🌐 시장 맥락")
    
    if not market_context:
        st.warning("시장 맥락 정보를 가져올 수 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        if 'kospi' in market_context and market_context['kospi']:
            kospi = market_context['kospi']
            st.metric("KOSPI", f"{kospi.get('current', 0):,.2f}", f"{kospi.get('change_pct', 0):+.2f}%")
        
        if 'usd_krw' in market_context and market_context['usd_krw']:
            usd_krw = market_context['usd_krw']
            st.metric("USD/KRW", f"{usd_krw.get('current', 0):,.1f}", f"{usd_krw.get('change_pct', 0):+.2f}%")
    
    with col2:
        if 'kosdaq' in market_context and market_context['kosdaq']:
            kosdaq = market_context['kosdaq']
            st.metric("KOSDAQ", f"{kosdaq.get('current', 0):,.2f}", f"{kosdaq.get('change_pct', 0):+.2f}%")
        
        if 'interest_rate' in market_context and market_context['interest_rate']:
            st.metric("기준금리", f"{market_context['interest_rate']:.1f}%")
    
    st.info(f"📈 전체 시장 트렌드: **{market_context.get('market_trend', 'N/A')}**")
    
    # 관련 뉴스
    if market_context.get('related_news'):
        st.markdown("**📰 관련 뉴스:**")
        for news in market_context['related_news']:
            impact_emoji = {"positive": "📈", "negative": "📉", "neutral": "📊"}.get(news['impact'], "📰")
            st.markdown(f"- {impact_emoji} {news['title']} ({news['category']})")

def _display_user_pattern_analysis(pattern: Dict):
    """사용자 패턴 분석 표시"""
    st.markdown("### 👤 당신의 거래 패턴")
    
    if pattern.get('total_trades', 0) > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 거래수", f"{pattern['total_trades']}건")
            if 'success_rate' in pattern:
                success_rate = pattern['success_rate']
                success_color = "normal" if success_rate >= 50 else "inverse"
                st.metric("성공률", f"{success_rate}%", delta_color=success_color)
        with col2:
            if 'avg_return' in pattern:
                avg_return = pattern['avg_return']
                return_color = "normal" if avg_return >= 0 else "inverse"
                st.metric("평균 수익률", f"{avg_return:+.1f}%", delta_color=return_color)
            st.metric("동일종목 거래", f"{pattern.get('same_stock_trades', 0)}건")
        
        # 데이터 품질 표시
        data_quality = pattern.get('data_quality', 'unknown')
        quality_colors = {
            'sufficient': '🟢 충분',
            'limited': '🟡 제한적', 
            'insufficient': '🔴 부족',
            'error': '⚫ 오류'
        }
        st.info(f"데이터 품질: {quality_colors.get(data_quality, '❓ 알 수 없음')}")
        
        # 최근 감정 패턴
        if pattern.get('recent_emotion_pattern'):
            st.markdown("**🎭 최근 감정 패턴:**")
            emotions = pattern['recent_emotion_pattern']
            emotion_text = ", ".join([f"{emotion}({count}회)" for emotion, count in emotions.items()])
            st.write(emotion_text)
        
        # 유사한 상황 표시
        if pattern.get('similar_situations'):
            st.markdown("**🔍 유사한 과거 상황:**")
            for situation in pattern['similar_situations']:
                return_color = "🟢" if situation.get('return', 0) > 0 else "🔴"
                st.markdown(f"- **{situation.get('date', 'N/A')}** {situation.get('stock', 'N/A')} ({situation.get('emotion', 'N/A')}) → {return_color} {situation.get('return', 0):+.1f}%")
                if situation.get('memo'):
                    st.markdown(f"  💭 *{situation['memo']}*")
    else:
        message = pattern.get('message', '거래 데이터가 없습니다.')
        st.info(message)

def _display_principle_alignment(principle: Dict):
    """투자 원칙 체크 표시"""
    st.markdown("### 🎯 투자 원칙 체크")
    
    if 'error' in principle:
        st.error(principle['error'])
        return
    
    if principle.get('alignment_score') is not None:
        score = principle['alignment_score']
        if score >= 80:
            score_color = "🟢"
            score_desc = "매우 부합"
        elif score >= 60:
            score_color = "🟡"
            score_desc = "부분 부합"
        else:
            score_color = "🔴"
            score_desc = "검토 필요"
        
        st.metric(f"{principle.get('principle_name', '투자 원칙')} 부합도", f"{score_color} {score}/100점 ({score_desc})")
        
        if principle.get('warnings'):
            st.markdown("**⚠️ 체크포인트:**")
            for warning in principle['warnings']:
                st.markdown(f"- {warning}")
        
        if principle.get('key_rules'):
            st.markdown(f"**📋 {principle['principle_name']} 핵심 원칙:**")
            for rule in principle['key_rules']:
                st.markdown(f"- {rule}")
    else:
        message = principle.get('message', '투자 원칙 정보가 없습니다.')
        st.info(message)

def _display_enhanced_risk_assessment(risk: Dict):
    """향상된 위험 요소 분석 표시"""
    st.markdown("### 🚨 종합 위험 분석")
    
    risk_colors = {
        "매우 낮음": "🟢", 
        "낮음": "🟢",
        "보통": "🟡", 
        "높음": "🟠", 
        "매우 높음": "🔴",
        "알 수 없음": "❓"
    }
    
    risk_level = risk.get('risk_level', '알 수 없음')
    risk_color = risk_colors.get(risk_level, "🟡")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("종합 위험도", f"{risk_color} {risk_level}")
    with col2:
        st.metric("위험 점수", f"{risk.get('risk_score', 50)}/100점")
    
    # 위험 요소 세부 분석
    if 'detailed_analysis' in risk:
        with st.expander("🔍 위험 분석 세부사항"):
            detailed = risk['detailed_analysis']
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📊 시장 위험**")
                market_risk = detailed.get('market_risk', {})
                st.metric("시장 위험 점수", f"{market_risk.get('score', 0):.1f}점")
                
            with col2:
                st.markdown("**🧠 패턴 위험**")
                pattern_risk = detailed.get('pattern_risk', {})
                st.metric("패턴 위험 점수", f"{pattern_risk.get('score', 0):.1f}점")
    
    # 위험 요소 목록
    if risk.get('factors'):
        st.markdown("**⚠️ 식별된 위험 요소:**")
        for factor in risk['factors']:
            st.markdown(f"- {factor}")
    else:
        st.success("✅ 특별한 위험 요소가 발견되지 않았습니다.")
    
    # 위험도별 권장사항 표시
    recommendation = risk.get('recommendation', '신중한 접근이 필요합니다.')
    if risk_level in ['높음', '매우 높음']:
        st.error(recommendation)
    elif risk_level == '보통':
        st.warning(recommendation)
    else:
        st.success(recommendation)

def _display_key_questions(questions: List[str]):
    """핵심 질문들 표시"""
    st.markdown("### 🤔 스스로에게 물어보세요")
    st.markdown("거래 전 다음 질문들을 스스로에게 해보세요:")
    
    for i, question in enumerate(questions, 1):
        st.markdown(f"**{i}.** {question}")

def _display_final_checklist(risk_assessment: Dict, action_type: str):
    """최종 체크리스트 표시"""
    st.markdown("### ✅ 최종 체크리스트")
    
    checklist_items = [
        "투자 원칙에 부합하는 거래인가요?",
        "감정적이지 않은 합리적 판단인가요?",
        "손실 허용 범위 내의 금액인가요?",
        "충분한 정보를 바탕으로 한 결정인가요?"
    ]
    
    # 위험도가 높은 경우 추가 체크리스트
    risk_level = risk_assessment.get('risk_level', '보통')
    if risk_level in ['높음', '매우 높음']:
        checklist_items.extend([
            "24시간 후에도 같은 생각일까요?",
            "가장 신뢰하는 사람에게도 이 거래를 권할까요?",
            "지금이 아니어도 되는 거래는 아닌가요?"
        ])
    
    for i, item in enumerate(checklist_items):
        st.checkbox(item, key=f"enhanced_checklist_{i}_{hash(item)}")

def _display_enhanced_help_tips():
    """개선된 도움말 표시"""
    with st.expander("💡 AI 브리핑 2.0 활용 가이드"):
        st.markdown("""
        **개선된 AI 브리핑을 효과적으로 활용하는 방법:**
        
        1. **신뢰도 확인**: 분석 신뢰도와 데이터 품질을 먼저 확인하세요.
        2. **종합 위험도 중시**: 시장 위험과 개인 패턴 위험을 종합한 평가를 참고하세요.
        3. **단계적 접근**: 위험도가 높을 때는 소액 테스트나 분할 매매를 고려하세요.
        4. **패턴 인식**: 과거 유사 상황과 현재를 비교하여 패턴을 파악하세요.
        5. **원칙 준수**: 선택한 투자 원칙과의 부합도를 지속적으로 체크하세요.
        6. **감정 관리**: 감정적 거래 패턴이 감지되면 잠시 멈춰 생각해보세요.
        7. **지속적 학습**: 거래 후 결과를 분석하여 다음 브리핑의 정확도를 높이세요.
        
        **🆕 브리핑 2.0의 새로운 기능:**
        - 향상된 위험 평가 알고리즘
        - 더 정확한 사용자 패턴 분석  
        - 투자 원칙별 맞춤 조언
        - 실시간 신뢰도 평가
        - 캐싱을 통한 빠른 응답
        """)