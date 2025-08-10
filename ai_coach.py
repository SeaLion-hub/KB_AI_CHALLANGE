#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - AI 코칭 엔진 (mirror_coaching 간소화 버전)
KB AI CHALLENGE 2024

🎯 핵심 기능:
1. 투자 복기 기반 패턴 매칭
2. 감정 상태 분석 및 코칭
3. 개인화된 투자 원칙 제안
4. 위험도 평가 및 경고
5. 설정 파일 기반 완전 동적 시스템
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re
import logging
from dataclasses import dataclass
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# [설정 기반 AI 코칭 시스템]
# ================================

@dataclass
class CoachingResult:
    """AI 코칭 결과 데이터 클래스"""
    analysis: str
    advice: List[str]
    warnings: List[str]
    questions: List[str]
    confidence: float
    risk_level: str
    emotion_state: Dict[str, Any]
    similar_trades: List[Dict[str, Any]]

class ConfigurableAICoach:
    """설정 파일 기반 AI 코칭 엔진"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # 설정 파일들 로드
        self._load_coaching_configs()
        
        logger.info("AI 코칭 엔진 초기화 완료 - 설정 파일 기반")
    
    def _load_coaching_configs(self):
        """코칭 관련 설정 파일들 로드"""
        
        # AI 코칭 설정
        self.coaching_config = self._load_config_file(
            "ai_coaching.json",
            self._get_default_coaching_config()
        )
        
        # 투자 원칙 설정
        self.principles_config = self._load_config_file(
            "investment_principles.json", 
            self._get_default_principles_config()
        )
        
        # 키워드 매핑 설정 (기존 data_engine과 연동)
        self.keywords_config = self._load_config_file(
            "keywords.json",
            self._get_default_keywords_config()
        )
    
    def _load_config_file(self, filename: str, default_data: Any) -> Any:
        """설정 파일 로드 (없으면 기본값으로 생성)"""
        config_file = self.config_dir / filename
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"설정 파일 로드 실패 {filename}: {e}")
        
        # 기본값으로 파일 생성
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"기본 설정 파일 생성: {filename}")
        return default_data
    
    def analyze_investment_situation(self, user_input: str, user_data: Dict, 
                                   user_trades: List[Dict], market_data: Dict, 
                                   news_data: List[Dict]) -> CoachingResult:
        """투자 상황 종합 분석 및 코칭"""
        
        try:
            # 1. 텍스트 분석
            text_analysis = self._analyze_input_text(user_input)
            
            # 2. 감정 상태 분석
            emotion_state = self._analyze_emotion_state(user_input, text_analysis)
            
            # 3. 위험도 평가
            risk_assessment = self._assess_investment_risk(
                user_input, text_analysis, emotion_state, market_data
            )
            
            # 4. 과거 거래 패턴 매칭
            similar_trades = self._find_similar_trades(
                user_input, text_analysis, user_trades
            )
            
            # 5. 투자 원칙 위반 체크
            principle_violations = self._check_principle_violations(
                user_input, text_analysis, user_data
            )
            
            # 6. 종합 코칭 생성
            coaching_result = self._generate_comprehensive_coaching(
                user_input, text_analysis, emotion_state, risk_assessment,
                similar_trades, principle_violations, market_data, news_data
            )
            
            logger.info(f"AI 코칭 분석 완료 - 신뢰도: {coaching_result.confidence:.2f}")
            return coaching_result
            
        except Exception as e:
            logger.error(f"AI 코칭 분석 오류: {e}")
            return self._create_error_coaching_result(str(e))
    
    def suggest_personalized_principles(self, user_data: Dict, 
                                      user_trades: List[Dict]) -> Dict[str, Any]:
        """개인화된 투자 원칙 제안"""
        
        if not user_trades:
            return self._get_beginner_principles()
        
        # 거래 패턴 분석
        trading_patterns = self._analyze_trading_patterns(user_trades)
        
        # 성과 분석
        performance_analysis = self._analyze_investment_performance(user_trades)
        
        # 감정 패턴 분석
        emotion_patterns = self._analyze_historical_emotions(user_trades)
        
        # 개인화된 원칙 생성
        personalized_principles = self._generate_personalized_principles(
            trading_patterns, performance_analysis, emotion_patterns, user_data
        )
        
        return personalized_principles
    
    # ================================
    # [텍스트 분석 엔진]
    # ================================
    
    def _analyze_input_text(self, text: str) -> Dict[str, Any]:
        """사용자 입력 텍스트 종합 분석"""
        
        # 키워드 추출
        keywords = self._extract_keywords(text)
        
        # 감정 키워드 추출
        emotion_keywords = self._extract_emotion_keywords(text)
        
        # 금액 패턴 추출
        amount_info = self._extract_amount_patterns(text)
        
        # 행동 의도 분석
        action_intent = self._analyze_action_intent(text, keywords)
        
        # 확신도 분석
        confidence_level = self._analyze_confidence_level(text)
        
        return {
            "keywords": keywords,
            "emotion_keywords": emotion_keywords,
            "amount_info": amount_info,
            "action_intent": action_intent,
            "confidence_level": confidence_level,
            "text_length": len(text),
            "question_count": text.count('?') + text.count('？')
        }
    
    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """키워드 추출 (설정 기반)"""
        keywords = {
            "stocks": [],
            "actions": [],
            "emotions": [],
            "reasons": [],
            "risk_patterns": []
        }
        
        text_lower = text.lower()
        
        # 주식 관련 키워드 (동적으로 확장 가능)
        stock_patterns = [
            "삼성전자", "SK하이닉스", "NAVER", "카카오", "LG화학", "현대차",
            "TSLA", "AAPL", "MSFT", "NVDA"
        ]
        
        for stock in stock_patterns:
            if stock.lower() in text_lower:
                keywords["stocks"].append(stock)
        
        # 행동 키워드
        action_keywords = self.keywords_config.get("categories", {}).get("actions", [])
        for action in action_keywords:
            if action in text_lower:
                keywords["actions"].append(action)
        
        # 감정 키워드
        emotion_keywords = self.keywords_config.get("categories", {}).get("emotions", [])
        for emotion in emotion_keywords:
            if emotion in text_lower:
                keywords["emotions"].append(emotion)
        
        # 위험 패턴 키워드
        risk_patterns = self.coaching_config.get("risk_patterns", {})
        for risk_level, patterns in risk_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    keywords["risk_patterns"].append({"pattern": pattern, "level": risk_level})
        
        return keywords
    
    def _extract_emotion_keywords(self, text: str) -> Dict[str, float]:
        """감정 키워드 추출 및 강도 계산"""
        emotions = self.coaching_config.get("emotions", {})
        emotion_scores = {}
        
        text_lower = text.lower()
        
        for emotion_type, emotion_list in emotions.items():
            score = 0
            for emotion in emotion_list:
                if emotion in text_lower:
                    score += text_lower.count(emotion)
            
            if score > 0:
                emotion_scores[emotion_type] = min(1.0, score / 3)  # 정규화
        
        return emotion_scores
    
    def _extract_amount_patterns(self, text: str) -> Dict[str, Any]:
        """금액 패턴 추출"""
        amount_info = {"amounts": [], "total_estimated": 0}
        
        # 한국어 금액 패턴
        patterns = [
            (r'(\d+)만원?', 10000),
            (r'(\d+)억원?', 100000000),
            (r'(\d+,?\d*)원', 1),
            (r'(\d+)천만?원?', 10000000)
        ]
        
        total_amount = 0
        
        for pattern, multiplier in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    amount = int(match.replace(',', '')) * multiplier
                    amount_info["amounts"].append(amount)
                    total_amount += amount
                except ValueError:
                    continue
        
        amount_info["total_estimated"] = total_amount
        amount_info["investment_size"] = self._categorize_investment_size(total_amount)
        
        return amount_info
    
    def _analyze_action_intent(self, text: str, keywords: Dict) -> Dict[str, Any]:
        """행동 의도 분석"""
        intent_scores = {
            "buy": 0,
            "sell": 0,
            "hold": 0,
            "research": 0
        }
        
        # 매수 의도
        buy_indicators = ["사고", "매수", "진입", "추가", "올인"]
        for indicator in buy_indicators:
            if indicator in text:
                intent_scores["buy"] += 1
        
        # 매도 의도  
        sell_indicators = ["팔고", "매도", "정리", "손절", "익절"]
        for indicator in sell_indicators:
            if indicator in text:
                intent_scores["sell"] += 1
        
        # 보유 의도
        hold_indicators = ["보유", "기다려", "관망"]
        for indicator in hold_indicators:
            if indicator in text:
                intent_scores["hold"] += 1
        
        # 연구 의도
        research_indicators = ["분석", "어떻게", "어떨까", "조언"]
        for indicator in research_indicators:
            if indicator in text:
                intent_scores["research"] += 1
        
        # 가장 높은 점수의 의도 선택
        primary_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[primary_intent] / max(1, sum(intent_scores.values()))
        
        return {
            "primary_intent": primary_intent,
            "confidence": confidence,
            "all_scores": intent_scores
        }
    
    # ================================
    # [감정 분석 엔진]
    # ================================
    
    def _analyze_emotion_state(self, text: str, text_analysis: Dict) -> Dict[str, Any]:
        """감정 상태 종합 분석"""
        
        emotion_keywords = text_analysis["emotion_keywords"]
        
        if not emotion_keywords:
            return {
                "primary_emotion": "중립",
                "intensity": 0.5,
                "confidence": 0.3,
                "emotional_risk": "낮음"
            }
        
        # 주요 감정 결정
        primary_emotion_type = max(emotion_keywords, key=emotion_keywords.get)
        intensity = emotion_keywords[primary_emotion_type]
        
        # 감정별 위험도 평가
        emotion_risk_map = {
            "negative": "높음",
            "positive": "보통", 
            "neutral": "낮음"
        }
        
        emotional_risk = emotion_risk_map.get(primary_emotion_type, "보통")
        
        # 감정 안정성 계산
        emotion_stability = 1.0 - (intensity * 0.7)  # 강한 감정일수록 불안정
        
        return {
            "primary_emotion": primary_emotion_type,
            "intensity": intensity,
            "confidence": min(1.0, sum(emotion_keywords.values())),
            "emotional_risk": emotional_risk,
            "stability": emotion_stability,
            "all_emotions": emotion_keywords
        }
    
    # ================================
    # [위험도 평가 엔진]
    # ================================
    
    def _assess_investment_risk(self, user_input: str, text_analysis: Dict, 
                               emotion_state: Dict, market_data: Dict) -> Dict[str, Any]:
        """투자 위험도 종합 평가"""
        
        risk_score = 0.3  # 기본 위험도
        risk_factors = []
        
        # 1. 감정 기반 위험도
        emotion_risk = self._calculate_emotion_risk(emotion_state)
        risk_score += emotion_risk["score"]
        risk_factors.extend(emotion_risk["factors"])
        
        # 2. 텍스트 패턴 기반 위험도
        pattern_risk = self._calculate_pattern_risk(text_analysis)
        risk_score += pattern_risk["score"]
        risk_factors.extend(pattern_risk["factors"])
        
        # 3. 시장 상황 기반 위험도
        market_risk = self._calculate_market_risk(text_analysis["keywords"], market_data)
        risk_score += market_risk["score"]
        risk_factors.extend(market_risk["factors"])
        
        # 4. 투자 규모 기반 위험도
        amount_risk = self._calculate_amount_risk(text_analysis["amount_info"])
        risk_score += amount_risk["score"]
        risk_factors.extend(amount_risk["factors"])
        
        # 위험도 정규화 및 레벨 결정
        risk_score = min(1.0, max(0.0, risk_score))
        
        if risk_score > 0.7:
            risk_level = "높음"
            risk_color = "danger"
        elif risk_score > 0.4:
            risk_level = "보통"
            risk_color = "warning"
        else:
            risk_level = "낮음"
            risk_color = "success"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level)
        }
    
    def _calculate_emotion_risk(self, emotion_state: Dict) -> Dict[str, Any]:
        """감정 기반 위험도 계산"""
        risk_score = 0.0
        risk_factors = []
        
        emotion_type = emotion_state["primary_emotion"]
        intensity = emotion_state["intensity"]
        
        # 감정별 위험도 매핑
        emotion_risk_weights = {
            "negative": 0.4,  # 불안, 두려움 등
            "positive": 0.1,  # 확신 등 (과신 위험)
            "neutral": 0.0
        }
        
        base_risk = emotion_risk_weights.get(emotion_type, 0.2)
        emotion_risk = base_risk * intensity
        
        risk_score += emotion_risk
        
        if emotion_risk > 0.3:
            risk_factors.append(f"감정적 불안정 ({emotion_type})")
        
        if emotion_state["stability"] < 0.5:
            risk_score += 0.2
            risk_factors.append("감정 변동성 높음")
        
        return {"score": risk_score, "factors": risk_factors}
    
    def _calculate_pattern_risk(self, text_analysis: Dict) -> Dict[str, Any]:
        """텍스트 패턴 기반 위험도 계산"""
        risk_score = 0.0
        risk_factors = []
        
        # 위험 패턴 체크
        risk_patterns = text_analysis["keywords"]["risk_patterns"]
        for pattern_info in risk_patterns:
            pattern = pattern_info["pattern"]
            level = pattern_info["level"]
            
            if level == "high_risk":
                risk_score += 0.3
                risk_factors.append(f"고위험 패턴: {pattern}")
            elif level == "medium_risk":
                risk_score += 0.2
                risk_factors.append(f"중위험 패턴: {pattern}")
        
        # 확신도가 너무 높거나 낮은 경우
        confidence = text_analysis["confidence_level"]
        if confidence > 0.9:
            risk_score += 0.2
            risk_factors.append("과도한 확신")
        elif confidence < 0.3:
            risk_score += 0.1
            risk_factors.append("불확실한 의사결정")
        
        return {"score": risk_score, "factors": risk_factors}
    
    def _calculate_market_risk(self, keywords: Dict, market_data: Dict) -> Dict[str, Any]:
        """시장 상황 기반 위험도 계산"""
        risk_score = 0.0
        risk_factors = []
        
        mentioned_stocks = keywords["stocks"]
        
        for stock in mentioned_stocks:
            if stock in market_data:
                stock_data = market_data[stock]
                volatility = abs(stock_data.get("change_percent", 0))
                
                if volatility > 10:  # 10% 이상 변동
                    risk_score += 0.3
                    risk_factors.append(f"{stock} 높은 변동성 ({volatility:.1f}%)")
                elif volatility > 5:  # 5% 이상 변동
                    risk_score += 0.1
                    risk_factors.append(f"{stock} 보통 변동성")
        
        return {"score": risk_score, "factors": risk_factors}
    
    # ================================
    # [유사 거래 매칭 엔진]
    # ================================
    
    def _find_similar_trades(self, user_input: str, text_analysis: Dict, 
                           user_trades: List[Dict]) -> List[Dict[str, Any]]:
        """과거 거래와의 유사도 매칭 (개선된 알고리즘)"""
        
        if not user_trades:
            return []
        
        similarities = []
        
        for trade in user_trades:
            similarity_score = self._calculate_trade_similarity(
                text_analysis, trade
            )
            
            if similarity_score > 0.2:  # 최소 유사도 threshold
                similarities.append({
                    **trade,
                    "similarity_score": similarity_score,
                    "match_factors": self._get_similarity_factors(text_analysis, trade)
                })
        
        # 유사도 순으로 정렬
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similarities[:5]  # 상위 5개만 반환
    
    def _calculate_trade_similarity(self, text_analysis: Dict, trade: Dict) -> float:
        """거래 유사도 계산 (다차원 분석)"""
        
        similarity_score = 0.0
        
        # 1. 종목 매칭 (40%)
        mentioned_stocks = text_analysis["keywords"]["stocks"]
        if trade["stock"] in mentioned_stocks:
            similarity_score += 0.4
        
        # 2. 행동 의도 매칭 (25%)
        action_intent = text_analysis["action_intent"]["primary_intent"]
        trade_action = trade.get("action", "")
        
        action_mapping = {
            "buy": ["매수", "진입"],
            "sell": ["매도", "정리", "손절", "익절"],
            "hold": ["보유", "관망"]
        }
        
        if action_intent in action_mapping:
            if any(action in trade_action for action in action_mapping[action_intent]):
                similarity_score += 0.25
        
        # 3. 감정 매칭 (20%)
        current_emotions = text_analysis["emotion_keywords"]
        trade_emotion = trade.get("emotion", "")
        
        for emotion_type in current_emotions:
            if emotion_type in trade_emotion.lower():
                similarity_score += 0.2
                break
        
        # 4. 투자 규모 매칭 (10%)
        current_amount = text_analysis["amount_info"]["total_estimated"]
        trade_amount = trade.get("amount", 0)
        
        if current_amount > 0 and trade_amount > 0:
            amount_ratio = min(current_amount, trade_amount) / max(current_amount, trade_amount)
            if amount_ratio > 0.5:  # 50% 이상 비슷한 규모
                similarity_score += 0.1
        
        # 5. 시간적 근접성 (5%)
        try:
            trade_date = datetime.strptime(trade["date"], "%Y-%m-%d")
            days_ago = (datetime.now() - trade_date).days
            if days_ago < 90:  # 3개월 이내
                time_weight = max(0, 1 - days_ago / 90) * 0.05
                similarity_score += time_weight
        except:
            pass
        
        return similarity_score
    
    def _get_similarity_factors(self, text_analysis: Dict, trade: Dict) -> List[str]:
        """유사도 요인 설명"""
        factors = []
        
        # 종목 매칭
        if trade["stock"] in text_analysis["keywords"]["stocks"]:
            factors.append(f"동일 종목 ({trade['stock']})")
        
        # 행동 매칭
        action_intent = text_analysis["action_intent"]["primary_intent"]
        if action_intent in trade.get("action", "").lower():
            factors.append(f"유사한 행동 ({action_intent})")
        
        # 감정 매칭
        for emotion in text_analysis["emotion_keywords"]:
            if emotion in trade.get("emotion", "").lower():
                factors.append(f"유사한 감정 ({emotion})")
                break
        
        # 결과 기반 학습 포인트
        if trade.get("result", 0) > 10:
            factors.append("과거 성공 사례")
        elif trade.get("result", 0) < -10:
            factors.append("과거 실패 사례")
        
        return factors
    
    # ================================
    # [종합 코칭 생성기]
    # ================================
    
    def _generate_comprehensive_coaching(self, user_input: str, text_analysis: Dict,
                                       emotion_state: Dict, risk_assessment: Dict,
                                       similar_trades: List[Dict], principle_violations: List[Dict],
                                       market_data: Dict, news_data: List[Dict]) -> CoachingResult:
        """종합 코칭 결과 생성"""
        
        # 상황 분석 메시지
        analysis = self._generate_situation_analysis(
            text_analysis, emotion_state, risk_assessment
        )
        
        # 구체적 조언
        advice = self._generate_specific_advice(
            similar_trades, risk_assessment, principle_violations
        )
        
        # 경고 메시지
        warnings = self._generate_warnings(
            risk_assessment, principle_violations, emotion_state
        )
        
        # 성찰 질문
        questions = self._generate_reflection_questions(
            text_analysis, emotion_state, similar_trades
        )
        
        # 신뢰도 계산
        confidence = self._calculate_coaching_confidence(
            similar_trades, emotion_state, text_analysis
        )
        
        return CoachingResult(
            analysis=analysis,
            advice=advice,
            warnings=warnings,
            questions=questions,
            confidence=confidence,
            risk_level=risk_assessment["risk_level"],
            emotion_state=emotion_state,
            similar_trades=similar_trades
        )
    
    def _generate_situation_analysis(self, text_analysis: Dict, emotion_state: Dict,
                                   risk_assessment: Dict) -> str:
        """상황 분석 메시지 생성"""
        
        analysis_parts = []
        
        # 기본 상황 요약
        stocks = text_analysis["keywords"]["stocks"]
        actions = text_analysis["keywords"]["actions"]
        
        if stocks:
            analysis_parts.append(f"{', '.join(stocks)}에 대한 투자 고민을 하고 계시네요.")
        
        if actions:
            analysis_parts.append(f"주요 고려 행동: {', '.join(actions)}")
        
        # 감정 상태 분석
        emotion = emotion_state["primary_emotion"]
        intensity = emotion_state["intensity"]
        
        if intensity > 0.6:
            analysis_parts.append(f"현재 {emotion} 감정이 강하게 감지됩니다.")
        elif intensity > 0.3:
            analysis_parts.append(f"{emotion} 감정이 어느 정도 영향을 주고 있는 것 같습니다.")
        
        # 위험도 평가
        risk_level = risk_assessment["risk_level"]
        analysis_parts.append(f"전체적인 투자 위험도는 '{risk_level}' 수준으로 평가됩니다.")
        
        return " ".join(analysis_parts)
    
    def _generate_specific_advice(self, similar_trades: List[Dict], 
                                risk_assessment: Dict, principle_violations: List[Dict]) -> List[str]:
        """구체적 조언 생성"""
        advice = []
        
        # 과거 거래 기반 조언
        if similar_trades:
            best_trade = similar_trades[0]
            if best_trade.get("result", 0) > 0:
                advice.append(
                    f"✅ 과거 '{best_trade['stock']}' 거래에서 {best_trade['result']:+.1f}% 수익을 얻으셨습니다. "
                    f"당시 성공 요인: {best_trade.get('reason', '명확한 분석')}"
                )
            else:
                advice.append(
                    f"⚠️ 과거 '{best_trade['stock']}' 거래에서 {best_trade['result']:+.1f}% 손실이 있었습니다. "
                    f"당시를 돌이켜보면: {best_trade.get('reason', '감정적 판단')}"
                )
        
        # 위험도 기반 조언
        risk_level = risk_assessment["risk_level"]
        if risk_level == "높음":
            advice.append("🚨 높은 위험이 감지되었습니다. 투자 규모를 줄이거나 더 신중한 검토를 권장합니다.")
        elif risk_level == "보통":
            advice.append("💡 적정 수준의 위험입니다. 추가적인 분석과 함께 신중하게 진행하세요.")
        
        # 원칙 위반 기반 조언
        if principle_violations:
            for violation in principle_violations:
                advice.append(f"📋 {violation['advice']}")
        
        return advice
    
    def _generate_warnings(self, risk_assessment: Dict, principle_violations: List[Dict],
                         emotion_state: Dict) -> List[str]:
        """경고 메시지 생성"""
        warnings = []
        
        # 고위험 경고
        if risk_assessment["risk_level"] == "높음":
            warnings.extend([
                "🚨 높은 위험도가 감지되었습니다",
                "📉 손실 가능성을 충분히 고려하세요",
                "💰 투자 금액을 줄이는 것을 고려해보세요"
            ])
        
        # 감정적 위험 경고
        if emotion_state["emotional_risk"] == "높음":
            warnings.append("😵 감정적 상태가 투자 판단에 영향을 줄 수 있습니다")
        
        # 원칙 위반 경고
        for violation in principle_violations:
            if violation["warning_level"] == "높음":
                warnings.append(f"⚠️ {violation['warning']}")
        
        return warnings
    
    def _generate_reflection_questions(self, text_analysis: Dict, emotion_state: Dict,
                                     similar_trades: List[Dict]) -> List[str]:
        """성찰 질문 생성"""
        
        questions = []
        
        # 기본 성찰 질문
        general_questions = self.coaching_config.get("reflection_questions", {}).get("general", [])
        questions.extend(general_questions[:2])  # 기본 2개
        
        # 감정 기반 질문
        if emotion_state["intensity"] > 0.5:
            emotional_questions = self.coaching_config.get("reflection_questions", {}).get("emotional", [])
            questions.extend(emotional_questions[:1])
        
        # 과거 거래 기반 질문
        if similar_trades:
            trade = similar_trades[0]
            questions.append(f"과거 {trade['stock']} 거래와 비교했을 때, 지금 상황에서 무엇이 다른가요?")
        
        # 위험 기반 질문
        risk_questions = self.coaching_config.get("reflection_questions", {}).get("risk_based", [])
        questions.extend(risk_questions[:1])
        
        return questions[:4]  # 최대 4개
    
    def _calculate_coaching_confidence(self, similar_trades: List[Dict], 
                                     emotion_state: Dict, text_analysis: Dict) -> float:
        """코칭 신뢰도 계산"""
        confidence = 0.3  # 기본 신뢰도
        
        # 유사 거래 기반 신뢰도
        if similar_trades:
            avg_similarity = np.mean([trade["similarity_score"] for trade in similar_trades])
            confidence += avg_similarity * 0.4
        
        # 텍스트 분석 품질 기반 신뢰도
        text_quality = min(1.0, len(text_analysis["keywords"]["stocks"]) / 2)
        confidence += text_quality * 0.2
        
        # 감정 분석 신뢰도
        emotion_confidence = emotion_state["confidence"]
        confidence += emotion_confidence * 0.1
        
        return min(1.0, confidence)
    
    # ================================
    # [투자 원칙 관련 메서드들]
    # ================================
    
    def _check_principle_violations(self, user_input: str, text_analysis: Dict,
                                  user_data: Dict) -> List[Dict[str, Any]]:
        """투자 원칙 위반 체크"""
        violations = []
        
        principles = self.coaching_config.get("investment_principles", {})
        
        for principle_name, principle_config in principles.items():
            keywords = principle_config["keywords"]
            warning = principle_config["warning"]
            advice = principle_config["advice"]
            
            text_lower = user_input.lower()
            
            for keyword in keywords:
                if keyword in text_lower:
                    violations.append({
                        "principle": principle_name,
                        "keyword": keyword,
                        "warning": warning,
                        "advice": advice,
                        "warning_level": "높음" if principle_name in ["emotional_investing", "overconcentration"] else "보통"
                    })
                    break  # 원칙당 하나의 위반만 기록
        
        return violations
    
    def _get_beginner_principles(self) -> Dict[str, Any]:
        """초보자용 투자 원칙"""
        return self.principles_config.get("beginner_principles", {})
    
    # ================================
    # [기본 설정 생성기들]
    # ================================
    
    def _get_default_coaching_config(self) -> Dict[str, Any]:
        """기본 AI 코칭 설정"""
        return {
            "emotions": {
                "positive": ["확신", "냉정", "차분", "만족"],
                "negative": ["불안", "두려움", "후회", "FOMO", "욕심"],
                "neutral": ["중립", "보통", "평범"]
            },
            "risk_patterns": {
                "high_risk": ["올인", "전부", "대박", "급등", "추격", "몰빵"],
                "medium_risk": ["추가매수", "더", "조금더"],
                "low_risk": ["분산", "안전", "신중", "보수적"]
            },
            "investment_principles": {
                "emotional_investing": {
                    "keywords": ["FOMO", "욕심", "흥분", "급하게", "감정적"],
                    "warning": "감정적 투자는 손실로 이어질 가능성이 높습니다.",
                    "advice": "냉정하게 한 번 더 생각해보세요."
                },
                "overconcentration": {
                    "keywords": ["올인", "전부", "몰빵", "모든걸"],
                    "warning": "과도한 집중 투자는 위험합니다.",
                    "advice": "분산투자를 통해 위험을 줄이세요."
                }
            },
            "reflection_questions": {
                "general": [
                    "이 투자 결정의 가장 명확한 근거는 무엇인가요?",
                    "감정이 아닌 데이터로만 판단한다면 어떤 결론인가요?",
                    "최악의 경우를 고려했을 때 감당 가능한 투자인가요?"
                ],
                "emotional": [
                    "지금 이 감정이 투자 판단에 영향을 주고 있지는 않나요?",
                    "냉정한 상태였다면 같은 결정을 내렸을까요?"
                ],
                "risk_based": [
                    "이 투자로 인한 최대 손실은 얼마까지 감당할 수 있나요?",
                    "리스크 대비 기대 수익이 합리적인가요?"
                ]
            }
        }
    
    def _get_default_principles_config(self) -> Dict[str, Any]:
        """기본 투자 원칙 설정"""
        return {
            "beginner_principles": {
                "basic_rules": [
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
                }
            }
        }
    
    def _get_default_keywords_config(self) -> Dict[str, Any]:
        """기본 키워드 설정"""
        return {
            "categories": {
                "actions": ["매수", "매도", "보유", "관망", "추가매수", "손절", "익절"],
                "emotions": ["불안", "확신", "두려움", "욕심", "냉정", "흥분", "후회", "만족"]
            }
        }
    
    # ================================
    # [헬퍼 메서드들]
    # ================================
    
    def _analyze_confidence_level(self, text: str) -> float:
        """텍스트에서 확신도 분석"""
        confidence_indicators = {
            "high": ["확실", "틀림없", "분명", "당연", "절대"],
            "low": ["고민", "모르겠", "애매", "확실하지", "불확실"]
        }
        
        text_lower = text.lower()
        high_count = sum(1 for word in confidence_indicators["high"] if word in text_lower)
        low_count = sum(1 for word in confidence_indicators["low"] if word in text_lower)
        
        if high_count > low_count:
            return min(1.0, 0.7 + high_count * 0.1)
        elif low_count > high_count:
            return max(0.0, 0.3 - low_count * 0.1)
        else:
            return 0.5
    
    def _categorize_investment_size(self, amount: int) -> str:
        """투자 규모 분류"""
        if amount >= 100000000:  # 1억 이상
            return "대규모"
        elif amount >= 10000000:  # 1천만 이상
            return "중규모"
        elif amount >= 1000000:   # 100만 이상
            return "소규모"
        else:
            return "소액"
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """위험도별 권장사항"""
        recommendations = {
            "높음": "투자를 재고하거나 규모를 대폭 줄이는 것을 권장합니다.",
            "보통": "추가 분석 후 신중하게 진행하세요.",
            "낮음": "적정한 위험 수준입니다."
        }
        return recommendations.get(risk_level, "신중한 검토가 필요합니다.")
    
    def _create_error_coaching_result(self, error_msg: str) -> CoachingResult:
        """오류 발생 시 기본 코칭 결과 생성"""
        return CoachingResult(
            analysis=f"분석 중 오류가 발생했습니다: {error_msg}",
            advice=["다시 시도해주세요."],
            warnings=["시스템 오류"],
            questions=["투자 전 충분한 검토를 하셨나요?"],
            confidence=0.1,
            risk_level="알 수 없음",
            emotion_state={"primary_emotion": "중립"},
            similar_trades=[]
        )
    
    # ================================
    # [투자 패턴 분석 (추가 메서드들)]
    # ================================
    
    def _analyze_trading_patterns(self, trades: List[Dict]) -> Dict[str, Any]:
        """거래 패턴 분석"""
        if not trades:
            return {}
        
        return {
            "total_trades": len(trades),
            "avg_return": np.mean([t.get("result", 0) for t in trades]),
            "success_rate": len([t for t in trades if t.get("result", 0) > 0]) / len(trades),
            "most_traded_stock": self._get_most_frequent_item([t.get("stock", "") for t in trades]),
            "most_common_emotion": self._get_most_frequent_item([t.get("emotion", "") for t in trades])
        }
    
    def _analyze_investment_performance(self, trades: List[Dict]) -> Dict[str, Any]:
        """투자 성과 분석"""
        if not trades:
            return {}
        
        returns = [t.get("result", 0) for t in trades]
        
        return {
            "total_return": sum(returns),
            "avg_return": np.mean(returns),
            "volatility": np.std(returns),
            "max_gain": max(returns),
            "max_loss": min(returns),
            "win_rate": len([r for r in returns if r > 0]) / len(returns)
        }
    
    def _analyze_historical_emotions(self, trades: List[Dict]) -> Dict[str, float]:
        """과거 감정 패턴 분석"""
        emotion_performance = {}
        
        for trade in trades:
            emotion = trade.get("emotion", "중립")
            result = trade.get("result", 0)
            
            if emotion not in emotion_performance:
                emotion_performance[emotion] = []
            emotion_performance[emotion].append(result)
        
        # 감정별 평균 수익률
        emotion_avg = {}
        for emotion, results in emotion_performance.items():
            emotion_avg[emotion] = np.mean(results)
        
        return emotion_avg
    
    def _get_most_frequent_item(self, items: List[str]) -> str:
        """가장 빈번한 항목 찾기"""
        if not items:
            return ""
        
        from collections import Counter
        counter = Counter(items)
        return counter.most_common(1)[0][0] if counter else ""
    
    def _generate_personalized_principles(self, trading_patterns: Dict, 
                                        performance_analysis: Dict, 
                                        emotion_patterns: Dict, 
                                        user_data: Dict) -> Dict[str, Any]:
        """개인화된 투자 원칙 생성"""
        
        principles = []
        
        # 성과 기반 원칙
        if performance_analysis.get("avg_return", 0) < 0:
            principles.extend([
                "손절 기준을 명확히 하고 반드시 지키기",
                "투자 전 더 충분한 분석하기"
            ])
        
        # 감정 패턴 기반 원칙
        if "욕심" in emotion_patterns or "FOMO" in emotion_patterns:
            principles.append("목표 수익률 달성 시 일부 매도하기")
        
        if "불안" in emotion_patterns:
            principles.append("투자 금액을 줄여서 심리적 부담 덜기")
        
        # 거래 빈도 기반 원칙
        if trading_patterns.get("total_trades", 0) > 20:
            principles.append("과도한 거래 줄이고 장기 투자 고려하기")
        
        return {
            "personalized_principles": principles[:5],
            "confidence_level": "높음" if len(principles) >= 3 else "보통",
            "based_on": f"{trading_patterns.get('total_trades', 0)}건의 거래 분석"
        }


# ================================
# [캐시된 인스턴스 생성]
# ================================

@st.cache_resource
def get_ai_coach(config_dir: str = "config") -> ConfigurableAICoach:
    """캐시된 AI 코치 인스턴스 반환"""
    return ConfigurableAICoach(config_dir)


# ================================
# [테스트 함수]
# ================================

def test_ai_coach():
    """AI 코치 테스트"""
    print("🧪 AI 코칭 엔진 테스트...")
    
    coach = get_ai_coach()
    
    # 테스트 입력
    test_input = "삼성전자가 5% 떨어졌는데 FOMO가 심해서 추가 매수할까 고민됩니다."
    
    # 더미 데이터
    user_data = {"name": "테스트", "type": "beginner"}
    user_trades = []
    market_data = {"삼성전자": {"price": 65000, "change_percent": -5.2}}
    news_data = []
    
    # 분석 실행
    result = coach.analyze_investment_situation(
        test_input, user_data, user_trades, market_data, news_data
    )
    
    print(f"분석 결과:")
    print(f"- 위험도: {result.risk_level}")
    print(f"- 신뢰도: {result.confidence:.2f}")
    print(f"- 조언 개수: {len(result.advice)}")
    print(f"- 경고 개수: {len(result.warnings)}")
    print(f"- 질문 개수: {len(result.questions)}")
    
    print("✅ AI 코칭 엔진 테스트 완료!")


if __name__ == "__main__":
    test_ai_coach()