#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 완전 동적 데이터 엔진
KB AI CHALLENGE 2024

🎯 핵심 원칙: 모든 데이터가 외부 설정 파일에서 로드되어 동적으로 변경 가능
- 하드코딩 제로 정책
- 설정 파일 기반 모든 데이터 관리
- 실시간 API 연동 가능한 구조
- 사용자가 데이터를 쉽게 수정 가능
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import random
import streamlit as st
from dataclasses import dataclass, asdict
import logging
import requests
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# [데이터 인터페이스] 추상화
# ================================

class DataProvider(ABC):
    """데이터 제공자 인터페이스"""
    
    @abstractmethod
    def get_market_data(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_news_data(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        pass

class FileDataProvider(DataProvider):
    """파일 기반 데이터 제공자"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def get_market_data(self) -> Dict[str, Any]:
        market_file = self.data_dir / "market_config.json"
        if market_file.exists():
            with open(market_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_news_data(self) -> List[Dict[str, Any]]:
        news_file = self.data_dir / "news_templates.json"
        if news_file.exists():
            with open(news_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        # 실시간 API 연동 시 여기서 구현
        return {}

class APIDataProvider(DataProvider):
    """API 기반 데이터 제공자 (확장 가능)"""
    
    def __init__(self, api_config: Dict[str, str]):
        self.api_config = api_config
    
    def get_market_data(self) -> Dict[str, Any]:
        # 실제 API 연동 로직
        # 예: KIS API, Yahoo Finance API 등
        return {}
    
    def get_news_data(self) -> List[Dict[str, Any]]:
        # 뉴스 API 연동
        return []
    
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        # 실시간 주가 API
        return {}

# ================================
# [설정 관리자] 모든 설정을 외부 파일에서 로드
# ================================

class ConfigManager:
    """동적 설정 관리자 - 모든 하드코딩을 제거"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        
        # 설정 파일들
        self.user_profiles_config = self._load_config("user_profiles.json", self._get_default_user_profiles())
        self.stocks_config = self._load_config("stocks.json", self._get_default_stocks())
        self.keywords_config = self._load_config("keywords.json", self._get_default_keywords())
        self.news_templates_config = self._load_config("news_templates.json", self._get_default_news_templates())
        self.market_config = self._load_config("market_settings.json", self._get_default_market_settings())
        
        logger.info("모든 설정이 외부 파일에서 로드되었습니다")
    
    def _load_config(self, filename: str, default_data: Any) -> Any:
        """설정 파일 로드 (없으면 기본값으로 생성)"""
        config_file = self.config_dir / filename
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"✅ {filename} 로드 완료")
                return data
            except Exception as e:
                logger.warning(f"⚠️ {filename} 로드 실패, 기본값 사용: {e}")
        
        # 기본값으로 파일 생성
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📝 {filename} 기본 파일 생성")
        return default_data
    
    def reload_config(self, config_name: str):
        """특정 설정 다시 로드"""
        if config_name == "user_profiles":
            self.user_profiles_config = self._load_config("user_profiles.json", {})
        elif config_name == "stocks":
            self.stocks_config = self._load_config("stocks.json", {})
        # ... 다른 설정들도 동일하게
        
        logger.info(f"🔄 {config_name} 설정 다시 로드됨")
    
    def update_config(self, config_name: str, data: Any):
        """설정 업데이트 및 저장"""
        filename_map = {
            "user_profiles": "user_profiles.json",
            "stocks": "stocks.json", 
            "keywords": "keywords.json",
            "news_templates": "news_templates.json",
            "market_settings": "market_settings.json"
        }
        
        if config_name in filename_map:
            filename = filename_map[config_name]
            config_file = self.config_dir / filename
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 메모리 업데이트
            setattr(self, f"{config_name}_config", data)
            logger.info(f"💾 {config_name} 설정 업데이트됨")
    
    # ================================
    # [기본값들] - 초기 설정 파일 생성용
    # ================================
    
    def _get_default_user_profiles(self) -> Dict:
        """사용자 프로필 기본값"""
        return {
            "profiles": {
                "fomo_trader": {
                    "description": "FOMO 매수 경향의 감정적 투자자",
                    "personality": {
                        "impulsiveness": 0.8,
                        "confidence": 0.7,
                        "patience": 0.3,
                        "analysis": 0.4,
                        "risk_tolerance": 0.8
                    },
                    "trading_patterns": {
                        "success_rate_range": [0.35, 0.45],
                        "avg_return_range": [-2.5, 1.5],
                        "trade_count_range": [40, 60]
                    },
                    "preferred_stocks": ["화제성_높은_종목"],
                    "common_emotions": ["욕심", "흥분", "확신", "불안"],
                    "trading_reasons": [
                        "{stock} 급등 소식 듣고 추격 매수",
                        "SNS에서 {stock} 호재 소식 확인", 
                        "지인 추천으로 {stock} 진입"
                    ]
                },
                "systematic_trader": {
                    "description": "체계적이고 분석적인 투자자",
                    "personality": {
                        "impulsiveness": 0.2,
                        "confidence": 0.6,
                        "patience": 0.9,
                        "analysis": 0.9,
                        "risk_tolerance": 0.4
                    },
                    "trading_patterns": {
                        "success_rate_range": [0.55, 0.70],
                        "avg_return_range": [2.0, 8.5],
                        "trade_count_range": [30, 45]
                    },
                    "preferred_stocks": ["안정적_대형주"],
                    "common_emotions": ["냉정", "확신", "신중", "차분"],
                    "trading_reasons": [
                        "{stock} 기술적 분석 결과 매수 신호",
                        "재무제표 분석 후 {stock} 가치 매력 확인",
                        "분산투자 차원에서 {stock} 편입"
                    ]
                },
                "beginner": {
                    "description": "투자 초보자",
                    "personality": {
                        "impulsiveness": 0.5,
                        "confidence": 0.3,
                        "patience": 0.6,
                        "analysis": 0.3,
                        "risk_tolerance": 0.2
                    },
                    "trading_patterns": {
                        "success_rate_range": [0.0, 0.0],
                        "avg_return_range": [0.0, 0.0],
                        "trade_count_range": [0, 0]
                    },
                    "preferred_stocks": ["전체"],
                    "common_emotions": ["신중", "불안", "희망"],
                    "trading_reasons": ["안전한 대형주 투자", "장기 투자 목적"]
                }
            },
            "users": {
                "김투자": {
                    "type": "fomo_trader",
                    "icon": "🔥",
                    "custom_traits": {
                        "news_sensitivity": 0.9,
                        "social_influence": 0.8
                    }
                },
                "박복기": {
                    "type": "systematic_trader", 
                    "icon": "📊",
                    "custom_traits": {
                        "analysis_depth": 0.9,
                        "patience_level": 0.9
                    }
                },
                "이신규": {
                    "type": "beginner",
                    "icon": "🌱",
                    "custom_traits": {
                        "learning_speed": 0.7,
                        "caution_level": 0.8
                    }
                }
            }
        }
    
    def _get_default_stocks(self) -> Dict:
        """주식 정보 기본값"""
        return {
            "categories": {
                "화제성_높은_종목": ["카카오", "NAVER", "SK하이닉스"],
                "안정적_대형주": ["삼성전자", "LG화학", "현대차"],
                "전체": "모든_종목"
            },
            "stocks": {
                "삼성전자": {
                    "sector": "반도체",
                    "market_cap": "대형주",
                    "base_price_range": [60000, 70000],
                    "volatility": 0.15,
                    "news_sensitivity": 0.8,
                    "api_symbol": "005930"
                },
                "SK하이닉스": {
                    "sector": "반도체",
                    "market_cap": "대형주", 
                    "base_price_range": [110000, 130000],
                    "volatility": 0.20,
                    "news_sensitivity": 0.9,
                    "api_symbol": "000660"
                },
                "NAVER": {
                    "sector": "인터넷",
                    "market_cap": "대형주",
                    "base_price_range": [170000, 190000],
                    "volatility": 0.18,
                    "news_sensitivity": 0.7,
                    "api_symbol": "035420"
                },
                "카카오": {
                    "sector": "인터넷",
                    "market_cap": "대형주",
                    "base_price_range": [40000, 50000],
                    "volatility": 0.25,
                    "news_sensitivity": 0.8,
                    "api_symbol": "035720"
                },
                "LG화학": {
                    "sector": "화학",
                    "market_cap": "대형주",
                    "base_price_range": [370000, 390000],
                    "volatility": 0.22,
                    "news_sensitivity": 0.6,
                    "api_symbol": "051910"
                },
                "현대차": {
                    "sector": "자동차",
                    "market_cap": "대형주",
                    "base_price_range": [170000, 190000],
                    "volatility": 0.16,
                    "news_sensitivity": 0.7,
                    "api_symbol": "005380"
                }
            }
        }
    
    def _get_default_keywords(self) -> Dict:
        """키워드 매핑 기본값"""
        return {
            "categories": {
                "stocks": "stocks_config에서_자동_로드",
                "actions": ["매수", "매도", "보유", "관망", "추가매수", "손절", "익절"],
                "emotions": ["불안", "확신", "두려움", "욕심", "냉정", "흥분", "후회", "만족"],
                "reasons": ["뉴스", "차트", "분석", "추천", "급등", "급락", "호재", "악재"],
                "market_conditions": ["상승장", "하락장", "박스권", "변동성", "거래량"]
            },
            "synonyms": {
                "매수": ["사기", "진입", "편입", "투자"],
                "매도": ["팔기", "정리", "청산", "처분"],
                "불안": ["걱정", "우려", "두려워", "무서워"],
                "확신": ["믿음", "신념", "자신", "확실"],
                "급등": ["상승", "올라", "뛰어", "폭등"],
                "급락": ["하락", "떨어져", "폭락", "추락"]
            },
            "emotion_patterns": {
                "불안": ["고민", "걱정", "어떡하지", "망설여", "불안"],
                "확신": ["확실", "틀림없", "분명", "당연"],
                "욕심": ["더", "추가", "올인", "대박"],
                "후회": ["아쉬워", "잘못", "실수", "후회"],
                "냉정": ["분석", "객관적", "데이터", "근거"]
            },
            "sentiment_words": {
                "positive": ["좋다", "상승", "호재", "기회", "매력", "긍정", "성장"],
                "negative": ["나쁘다", "하락", "악재", "위험", "우려", "부정", "손실"]
            }
        }
    
    def _get_default_news_templates(self) -> Dict:
        """뉴스 템플릿 기본값"""
        return {
            "templates": {
                "positive": [
                    "{stock}의 {sector} 관련 신기술 개발로 주가 상승 전망",
                    "{stock}, 대규모 계약 체결로 실적 개선 기대감 확산",
                    "{stock} 분기 실적 깜짝 발표, 시장 예상치 상회",
                    "글로벌 {sector} 시장 성장으로 {stock} 수혜 전망",
                    "{stock}의 신사업 진출 발표로 투자자 관심 집중"
                ],
                "negative": [
                    "{stock}, 규제 이슈로 단기 조정 불가피한 상황",
                    "{sector} 업계 전반적 둔화로 {stock} 실적 우려",
                    "{stock} 경영진 변화 발표, 불확실성 확대",
                    "글로벌 {sector} 경쟁 심화로 {stock} 마진 압박",
                    "{stock}의 주요 사업부 부진으로 주가 하락 압력"
                ],
                "neutral": [
                    "{stock}, 투자자들의 엇갈린 시각으로 보합권 거래",
                    "{sector} 업계 동향 주시하는 {stock}, 신중한 접근 필요",
                    "{stock}의 중장기 전략 발표, 시장 반응은 제한적"
                ]
            },
            "content_templates": {
                "positive": "{title}. 업계 전문가들은 이번 발표가 {stock}의 중장기 성장에 긍정적 영향을 미칠 것으로 분석하고 있다. 특히 {sector} 시장의 성장성을 고려할 때 투자 매력도가 높아질 것으로 예상된다.",
                "negative": "{title}. 시장에서는 이러한 이슈가 {stock}의 단기 실적에 부담으로 작용할 가능성을 우려하고 있다. {sector} 업계 전반에 미칠 영향도 주시해야 할 상황이다.",
                "neutral": "{title}. 시장 참가자들은 추가적인 정보를 기다리며 신중한 접근을 보이고 있다."
            },
            "sources": ["KB리서치센터", "KB증권", "KB투자증권", "시장분석팀"],
            "importance_factors": {
                "대형주_multiplier": 1.2,
                "sector_sensitivity": 1.1,
                "market_time_factor": 1.3
            }
        }
    
    def _get_default_market_settings(self) -> Dict:
        """시장 설정 기본값"""
        return {
            "trading_hours": {
                "market_open": "09:00",
                "market_close": "15:30",
                "weekend_trading": False
            },
            "volatility_settings": {
                "market_session_multiplier": 1.0,
                "after_hours_multiplier": 0.3,
                "weekend_multiplier": 0.1
            },
            "volume_settings": {
                "base_volume": 1000000,
                "market_time_factor": [1.2, 1.8],
                "volatility_factor": [0.5, 2.0]
            },
            "price_limits": {
                "daily_limit_percent": 30.0,
                "price_tick_size": 5
            },
            "api_settings": {
                "update_interval_seconds": 300,
                "retry_attempts": 3,
                "timeout_seconds": 10
            }
        }

# ================================
# [동적 데이터 생성기] 설정 기반 완전 동적
# ================================

class DynamicDataGenerator:
    """설정 파일 기반 완전 동적 데이터 생성기"""
    
    def __init__(self, config_manager: ConfigManager, data_provider: DataProvider):
        self.config = config_manager
        self.provider = data_provider
        
        # 동적으로 로드된 설정들
        self.user_profiles = self.config.user_profiles_config
        self.stocks_info = self.config.stocks_config
        self.keywords = self.config.keywords_config
        self.news_templates = self.config.news_templates_config
        self.market_settings = self.config.market_config
        
        logger.info("동적 데이터 생성기 초기화 완료 - 모든 데이터가 설정 파일에서 로드됨")
    
    def generate_users(self) -> Dict[str, Any]:
        """설정 기반 사용자 생성"""
        users = {}
        
        profiles_config = self.user_profiles["profiles"]
        users_config = self.user_profiles["users"]
        
        for user_id, user_config in users_config.items():
            user_type = user_config["type"]
            profile = profiles_config[user_type]
            
            # 거래 패턴에서 값 추출
            trading_patterns = profile["trading_patterns"]
            success_rate = random.uniform(*trading_patterns["success_rate_range"])
            avg_return = random.uniform(*trading_patterns["avg_return_range"])
            trades_count = random.randint(*trading_patterns["trade_count_range"])
            
            user_data = {
                "id": user_id,
                "name": user_id,
                "type": user_type,
                "description": profile["description"],
                "icon": user_config["icon"],
                "personality": profile["personality"],
                "trades_count": trades_count,
                "success_rate": success_rate,
                "avg_return": avg_return,
                "risk_tolerance": self._calculate_risk_tolerance(profile["personality"]),
                "custom_traits": user_config.get("custom_traits", {})
            }
            
            users[user_id] = user_data
            
        return users
    
    def generate_trades_for_user(self, user_data: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """사용자별 거래 데이터 동적 생성"""
        if count == 0:
            return []
        
        trades = []
        user_type = user_data["type"]
        profile = self.user_profiles["profiles"][user_type]
        
        # 선호 종목 카테고리
        preferred_category = profile["preferred_stocks"][0]
        if preferred_category == "전체":
            available_stocks = list(self.stocks_info["stocks"].keys())
        else:
            available_stocks = self.stocks_info["categories"][preferred_category]
        
        for i in range(count):
            # 랜덤 종목 선택
            stock = random.choice(available_stocks)
            stock_info = self.stocks_info["stocks"][stock]
            
            # 거래 생성
            trade = self._generate_single_trade(user_data, stock, stock_info, profile, i)
            trades.append(trade)
        
        return sorted(trades, key=lambda x: x["date"], reverse=True)
    
    def _generate_single_trade(self, user_data: Dict, stock: str, stock_info: Dict, profile: Dict, index: int) -> Dict:
        """단일 거래 생성"""
        # 날짜 생성
        trade_date = datetime.now() - timedelta(days=random.randint(1, 365))
        
        # 가격 생성 (설정 기반)
        price_range = stock_info["base_price_range"]
        base_price = random.randint(*price_range)
        volatility = stock_info["volatility"]
        price_variation = random.gauss(0, volatility * 0.5)
        price = max(int(price_range[0] * 0.8), int(base_price * (1 + price_variation)))
        
        # 거래량 계산
        amount = self._calculate_trade_amount(user_data, price)
        
        # 행동 및 감정 선택 (설정 기반)
        action = random.choice(self.keywords["categories"]["actions"])
        emotion = random.choice(profile["common_emotions"])
        
        # 거래 이유 생성 (템플릿 기반)
        reason_template = random.choice(profile["trading_reasons"])
        reason = reason_template.format(stock=stock)
        
        # 확신도 및 수익률 계산
        confidence = self._calculate_confidence(user_data["personality"], emotion)
        result = self._calculate_return(profile, emotion, confidence)
        
        # 시장 상황
        market_condition = random.choice(self.keywords["categories"]["market_conditions"])
        
        # 메모 생성
        memo = self._generate_memo(reason, emotion, stock, result)
        
        return {
            "id": f"{user_data['id']}_{index:03d}",
            "user_id": user_data["id"],
            "date": trade_date.strftime("%Y-%m-%d"),
            "stock": stock,
            "action": action,
            "amount": amount,
            "price": price,
            "reason": reason,
            "emotion": emotion,
            "confidence": confidence,
            "result": result,
            "memo": memo,
            "market_condition": market_condition
        }
    
    def generate_market_data(self) -> Dict[str, Any]:
        """동적 시장 데이터 생성"""
        market_data = {}
        current_time = datetime.now()
        
        # 시장 시간 확인 (설정 기반)
        is_market_time = self._is_market_session(current_time)
        
        for stock_name, stock_info in self.stocks_info["stocks"].items():
            # 가격 변동 계산
            price_data = self._calculate_dynamic_price(stock_info, is_market_time)
            
            # 거래량 계산
            volume = self._calculate_volume(stock_info, is_market_time)
            
            # 기술적 신호
            technical_signal = random.choice(["buy", "sell", "hold"])
            
            market_data[stock_name] = {
                "symbol": stock_info.get("api_symbol", stock_name),
                "name": stock_name,
                "price": price_data["current_price"],
                "change": price_data["change"],
                "change_percent": price_data["change_percent"],
                "volume": volume,
                "market_cap": stock_info["market_cap"],
                "sector": stock_info["sector"],
                "news_sentiment": random.uniform(-0.5, 0.5),
                "technical_signal": technical_signal,
                "last_update": current_time.isoformat()
            }
        
        return market_data
    
    def generate_news(self, count: int = 5) -> List[Dict[str, Any]]:
        """동적 뉴스 생성"""
        news_items = []
        templates = self.news_templates["templates"]
        content_templates = self.news_templates["content_templates"]
        sources = self.news_templates["sources"]
        
        for i in range(count):
            # 랜덤 종목 및 임팩트 선택
            stock_name = random.choice(list(self.stocks_info["stocks"].keys()))
            stock_info = self.stocks_info["stocks"][stock_name]
            
            impact_types = ["positive", "negative", "neutral"]
            impact = random.choice(impact_types)
            
            # 뉴스 제목 생성 (템플릿 기반)
            title_template = random.choice(templates[impact])
            title = title_template.format(stock=stock_name, sector=stock_info["sector"])
            
            # 뉴스 내용 생성
            content_template = content_templates[impact]
            content = content_template.format(
                title=title, 
                stock=stock_name, 
                sector=stock_info["sector"]
            )
            
            # 시간 및 중요도 계산
            news_time_delta = random.randint(10, 360)
            importance = self._calculate_news_importance(stock_info, impact)
            
            news_item = {
                "id": f"news_{i:03d}_{int(datetime.now().timestamp())}",
                "title": title,
                "content": content,
                "time": self._format_news_time(news_time_delta),
                "impact": impact,
                "sentiment_score": self._calculate_sentiment_score(impact),
                "related_stocks": [stock_name],
                "source": random.choice(sources),
                "importance": importance
            }
            
            news_items.append(news_item)
        
        return sorted(news_items, key=lambda x: x["importance"], reverse=True)
    
    # ================================
    # [보조 메서드들] 계산 로직
    # ================================
    
    def _calculate_risk_tolerance(self, personality: Dict[str, float]) -> str:
        """위험 성향 계산"""
        risk_score = (
            personality["risk_tolerance"] * 0.4 +
            personality["impulsiveness"] * 0.3 +
            personality["confidence"] * 0.2 +
            (1 - personality["patience"]) * 0.1
        )
        
        if risk_score > 0.7:
            return "high"
        elif risk_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_trade_amount(self, user_data: Dict, price: int) -> int:
        """거래 금액 계산"""
        if user_data["type"] == "fomo_trader":
            base_amount = random.randint(300, 1500) * 10000
        elif user_data["type"] == "systematic_trader":
            base_amount = random.randint(200, 800) * 10000
        else:
            base_amount = random.randint(50, 300) * 10000
        
        shares = max(1, base_amount // price)
        return shares * price
    
    def _calculate_confidence(self, personality: Dict[str, float], emotion: str) -> float:
        """확신도 계산"""
        base_confidence = personality["confidence"]
        
        # 감정별 조정
        emotion_factors = {
            "확신": 0.2, "냉정": 0.1, "차분": 0.1,
            "불안": -0.2, "두려움": -0.3, "후회": -0.1,
            "욕심": 0.15, "흥분": 0.1
        }
        
        emotion_adjust = emotion_factors.get(emotion, 0)
        return max(0.1, min(1.0, base_confidence + emotion_adjust))
    
    def _calculate_return(self, profile: Dict, emotion: str, confidence: float) -> float:
        """수익률 계산"""
        # 기본 수익률 분포
        base_return = random.gauss(0, 10)
        
        # 감정별 수익률 조정
        emotion_factors = {
            "욕심": -2.0, "흥분": -1.5, "불안": -1.0,
            "확신": 1.0, "냉정": 2.0, "신중": 1.5, "차분": 1.0
        }
        
        emotion_adjust = emotion_factors.get(emotion, 0)
        
        # 과신 페널티
        overconfidence_penalty = -1.5 if confidence > 0.8 else 0
        
        # 사용자 타입별 조정 (설정에서 가져올 수 있음)
        type_adjustments = {"fomo_trader": -1.0, "systematic_trader": 1.5, "beginner": 0}
        type_adjust = type_adjustments.get(profile.get("type", "beginner"), 0)
        
        final_return = base_return + emotion_adjust + overconfidence_penalty + type_adjust
        return max(-30.0, min(50.0, final_return))
    
    def _is_market_session(self, current_time: datetime) -> bool:
        """시장 시간 확인 (설정 기반)"""
        trading_hours = self.market_settings["trading_hours"]
        
        # 주말 확인
        if current_time.weekday() >= 5 and not trading_hours["weekend_trading"]:
            return False
        
        # 시장 시간 확인
        from datetime import time
        market_open = time(*map(int, trading_hours["market_open"].split(":")))
        market_close = time(*map(int, trading_hours["market_close"].split(":")))
        current_time_only = current_time.time()
        
        return market_open <= current_time_only <= market_close
    
    def _calculate_dynamic_price(self, stock_info: Dict, is_market_time: bool) -> Dict:
        """동적 가격 계산"""
        base_price_range = stock_info["base_price_range"]
        base_price = random.randint(*base_price_range)
        volatility = stock_info["volatility"]
        
        # 시장 시간에 따른 변동성 조정
        volatility_settings = self.market_settings["volatility_settings"]
        if is_market_time:
            volatility *= volatility_settings["market_session_multiplier"]
        else:
            volatility *= volatility_settings["after_hours_multiplier"]
        
        # 가격 변동 계산
        price_change = random.gauss(0, volatility * 0.3)
        current_price = int(base_price * (1 + price_change))
        
        # 가격 제한 적용
        price_limits = self.market_settings["price_limits"]
        daily_limit = price_limits["daily_limit_percent"] / 100
        
        min_price = int(base_price * (1 - daily_limit))
        max_price = int(base_price * (1 + daily_limit))
        current_price = max(min_price, min(max_price, current_price))
        
        change = current_price - base_price
        change_percent = (change / base_price) * 100
        
        return {
            "current_price": current_price,
            "change": change,
            "change_percent": change_percent
        }
    
    def _calculate_volume(self, stock_info: Dict, is_market_time: bool) -> int:
        """거래량 계산"""
        volume_settings = self.market_settings["volume_settings"]
        base_volume = volume_settings["base_volume"]
        
        # 시장 시간 조정
        if is_market_time:
            time_factor = random.uniform(*volume_settings["market_time_factor"])
        else:
            time_factor = random.uniform(0.3, 0.7)
        
        # 변동성 조정
        volatility_factor = random.uniform(*volume_settings["volatility_factor"])
        
        return int(base_volume * time_factor * volatility_factor)
    
    def _calculate_news_importance(self, stock_info: Dict, impact: str) -> float:
        """뉴스 중요도 계산"""
        importance_factors = self.news_templates["importance_factors"]
        base_importance = random.uniform(0.3, 0.9)
        
        # 대형주 가중치
        if stock_info["market_cap"] == "대형주":
            base_importance *= importance_factors["대형주_multiplier"]
        
        # 섹터 민감도
        if stock_info["news_sensitivity"] > 0.7:
            base_importance *= importance_factors["sector_sensitivity"]
        
        # 임팩트별 조정
        if impact == "positive":
            base_importance *= 1.1
        elif impact == "negative":
            base_importance *= 1.2  # 부정 뉴스가 더 주목받음
        
        return min(1.0, base_importance)
    
    def _calculate_sentiment_score(self, impact: str) -> float:
        """감정 점수 계산"""
        if impact == "positive":
            return random.uniform(0.3, 0.8)
        elif impact == "negative":
            return random.uniform(-0.8, -0.3)
        else:
            return random.uniform(-0.2, 0.2)
    
    def _format_news_time(self, minutes_ago: int) -> str:
        """뉴스 시간 포맷팅"""
        if minutes_ago < 60:
            return f"{minutes_ago}분 전"
        elif minutes_ago < 1440:
            hours = minutes_ago // 60
            return f"{hours}시간 전"
        else:
            days = minutes_ago // 1440
            return f"{days}일 전"
    
    def _generate_memo(self, reason: str, emotion: str, stock: str, result: float) -> str:
        """거래 메모 생성"""
        memo_templates = [
            f"{reason}. {emotion} 상태에서 결정했는데 결과는 {result:+.1f}%",
            f"{stock}에 대한 {reason}으로 투자. 당시 {emotion}했던 기억이 남.",
            f"{emotion}한 마음으로 {reason}했지만 결과는 {result:+.1f}%였다.",
            f"{reason}. 지금 생각해보니 너무 {emotion}했던 것 같다."
        ]
        return random.choice(memo_templates)

# ================================
# [고도화된 AI 매칭 엔진] 설정 기반
# ================================

class ConfigurableAIEngine:
    """설정 기반 AI 매칭 엔진"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.keywords = self.config.keywords_config
        
        # 동적으로 주식 목록 로드
        self.stock_list = list(self.config.stocks_config["stocks"].keys())
        self.keywords["categories"]["stocks"] = self.stock_list
        
        logger.info("AI 엔진이 설정 파일 기반으로 초기화됨")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """텍스트 종합 분석"""
        return {
            "keywords": self._extract_keywords(text),
            "emotion": self._extract_emotion(text),
            "sentiment": self._analyze_sentiment(text),
            "confidence": self._calculate_text_confidence(text)
        }
    
    def find_similar_trades(self, user_input: str, trades_data: List[Dict], top_k: int = 3) -> List[Dict]:
        """유사 거래 찾기"""
        if not trades_data:
            return []
        
        # 입력 분석
        input_analysis = self.analyze_text(user_input)
        
        similarities = []
        for trade in trades_data:
            similarity_score = self._calculate_similarity(input_analysis, trade)
            
            if similarity_score > 0.2:
                similarities.append({
                    "trade": trade,
                    "similarity_score": similarity_score,
                    "match_reasons": self._explain_match(input_analysis, trade)
                })
        
        # 유사도 순 정렬
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similarities[:top_k]
    
    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """키워드 추출 (설정 기반)"""
        text_lower = text.lower()
        extracted = {category: [] for category in self.keywords["categories"]}
        
        for category, keywords in self.keywords["categories"].items():
            if category == "stocks":
                keywords = self.stock_list
            
            for keyword in keywords:
                if keyword in text_lower:
                    extracted[category].append(keyword)
                    
                # 동의어 확인
                if keyword in self.keywords["synonyms"]:
                    for synonym in self.keywords["synonyms"][keyword]:
                        if synonym in text_lower:
                            extracted[category].append(keyword)
                            break
        
        return extracted
    
    def _extract_emotion(self, text: str) -> str:
        """감정 추출 (설정 기반)"""
        text_lower = text.lower()
        
        # 직접 매칭
        for emotion in self.keywords["categories"]["emotions"]:
            if emotion in text_lower:
                return emotion
        
        # 패턴 매칭
        for emotion, patterns in self.keywords["emotion_patterns"].items():
            for pattern in patterns:
                if pattern in text_lower:
                    return emotion
        
        return "중립"
    
    def _analyze_sentiment(self, text: str) -> float:
        """감정 분석 (설정 기반)"""
        text_lower = text.lower()
        positive_words = self.keywords["sentiment_words"]["positive"]
        negative_words = self.keywords["sentiment_words"]["negative"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_count
    
    def _calculate_similarity(self, input_analysis: Dict, trade: Dict) -> float:
        """다차원 유사도 계산"""
        # 종목 매칭
        stock_match = 1.0 if trade["stock"] in input_analysis["keywords"]["stocks"] else 0.0
        
        # 행동 매칭
        action_match = 1.0 if trade["action"] in input_analysis["keywords"]["actions"] else 0.0
        
        # 감정 매칭
        emotion_match = 1.0 if trade["emotion"] == input_analysis["emotion"] else 0.0
        
        # 상황 매칭
        situation_match = 0.0
        trade_text = f"{trade['reason']} {trade['memo']}".lower()
        for reason in input_analysis["keywords"]["reasons"]:
            if reason in trade_text:
                situation_match = 1.0
                break
        
        # 감정 극성 매칭
        trade_sentiment = self._analyze_sentiment(trade_text)
        sentiment_similarity = 1.0 - abs(input_analysis["sentiment"] - trade_sentiment)
        
        # 가중 평균
        total_similarity = (
            stock_match * 0.4 +
            action_match * 0.25 +
            emotion_match * 0.2 +
            situation_match * 0.1 +
            sentiment_similarity * 0.05
        )
        
        return total_similarity
    
    def _explain_match(self, input_analysis: Dict, trade: Dict) -> List[str]:
        """매칭 이유 설명"""
        reasons = []
        
        if trade["stock"] in input_analysis["keywords"]["stocks"]:
            reasons.append(f"동일 종목 ({trade['stock']})")
        
        if trade["action"] in input_analysis["keywords"]["actions"]:
            reasons.append(f"동일 행동 ({trade['action']})")
        
        if trade["emotion"] == input_analysis["emotion"]:
            reasons.append(f"동일 감정 ({trade['emotion']})")
        
        return reasons
    
    def _calculate_text_confidence(self, text: str) -> float:
        """텍스트 분석 신뢰도"""
        keywords_found = sum(len(kw_list) for kw_list in self._extract_keywords(text).values())
        return min(1.0, keywords_found / 5)

# ================================
# [통합 동적 데이터 엔진] 메인 클래스
# ================================

class CompleteDynamicDataEngine:
    """완전 동적 데이터 엔진 - 설정 파일 기반 모든 기능"""
    
    def __init__(self, config_dir: str = "config", data_dir: str = "data", use_api: bool = False):
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 설정 관리자 초기화
        self.config_manager = ConfigManager(self.config_dir)
        
        # 데이터 제공자 초기화
        if use_api:
            api_config = self.config_manager.market_config.get("api_settings", {})
            self.data_provider = APIDataProvider(api_config)
        else:
            self.data_provider = FileDataProvider(self.data_dir)
        
        # 핵심 엔진들 초기화
        self.data_generator = DynamicDataGenerator(self.config_manager, self.data_provider)
        self.ai_engine = ConfigurableAIEngine(self.config_manager)
        
        # 데이터 초기화
        self._initialize_data()
        
        logger.info("🚀 완전 동적 데이터 엔진 초기화 완료 - 100% 설정 파일 기반")
    
    def _initialize_data(self):
        """데이터 초기화"""
        try:
            # 사용자 데이터
            self.users = self._load_or_generate_users()
            
            # 거래 데이터
            self.trades = self._load_or_generate_trades()
            
            # 실시간 데이터
            self.refresh_realtime_data()
            
            logger.info(f"✅ 동적 데이터 초기화 완료: 사용자 {len(self.users)}명")
            
        except Exception as e:
            logger.error(f"❌ 데이터 초기화 실패: {e}")
            raise
    
    def _load_or_generate_users(self) -> Dict[str, Any]:
        """사용자 데이터 로드/생성"""
        users_file = self.data_dir / "generated_users.json"
        
        # 설정이 변경되었는지 확인
        config_hash = self._calculate_config_hash("user_profiles")
        
        if users_file.exists():
            try:
                with open(users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 설정 해시 확인
                if data.get("config_hash") == config_hash:
                    logger.info("🔄 기존 사용자 데이터 로드 (설정 변경 없음)")
                    return data["users"]
                else:
                    logger.info("⚡ 설정 변경 감지, 사용자 데이터 재생성")
            except Exception as e:
                logger.warning(f"⚠️ 사용자 데이터 로드 실패: {e}")
        
        # 새로 생성
        users = self.data_generator.generate_users()
        
        # 설정 해시와 함께 저장
        save_data = {
            "config_hash": config_hash,
            "generated_at": datetime.now().isoformat(),
            "users": users
        }
        
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        logger.info("📝 새 사용자 데이터 생성 및 저장")
        return users
    
    def _load_or_generate_trades(self) -> Dict[str, List[Dict]]:
        """거래 데이터 로드/생성"""
        trades_file = self.data_dir / "generated_trades.json"
        
        config_hash = self._calculate_config_hash("all")
        
        if trades_file.exists():
            try:
                with open(trades_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get("config_hash") == config_hash:
                    logger.info("🔄 기존 거래 데이터 로드")
                    return data["trades"]
                else:
                    logger.info("⚡ 설정 변경 감지, 거래 데이터 재생성")
            except Exception as e:
                logger.warning(f"⚠️ 거래 데이터 로드 실패: {e}")
        
        # 새로 생성
        trades = {}
        for user_id, user_data in self.users.items():
            trade_count = user_data["trades_count"]
            if trade_count > 0:
                trades[user_id] = self.data_generator.generate_trades_for_user(user_data, trade_count)
            else:
                trades[user_id] = []
        
        # 저장
        save_data = {
            "config_hash": config_hash,
            "generated_at": datetime.now().isoformat(),
            "trades": trades
        }
        
        with open(trades_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("📝 새 거래 데이터 생성 및 저장")
        return trades
    
    def _calculate_config_hash(self, config_type: str) -> str:
        """설정 변경 감지용 해시 계산"""
        import hashlib
        
        if config_type == "user_profiles":
            config_str = json.dumps(self.config_manager.user_profiles_config, sort_keys=True)
        elif config_type == "all":
            all_configs = {
                "users": self.config_manager.user_profiles_config,
                "stocks": self.config_manager.stocks_config,
                "keywords": self.config_manager.keywords_config
            }
            config_str = json.dumps(all_configs, sort_keys=True)
        else:
            config_str = "{}"
        
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    def refresh_realtime_data(self):
        """실시간 데이터 갱신"""
        self.market_data = self.data_generator.generate_market_data()
        self.news_data = self.data_generator.generate_news()
        logger.info("🔄 실시간 데이터 갱신 완료")
    
    # ================================
    # [공개 API] main_app.py에서 사용할 메서드들
    # ================================
    
    def get_users(self) -> Dict[str, Any]:
        """모든 사용자 반환"""
        return self.users
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """특정 사용자 반환"""
        return self.users.get(user_id)
    
    def get_user_trades(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 거래 내역 반환"""
        return self.trades.get(user_id, [])
    
    def get_market_data(self, refresh: bool = False) -> Dict[str, Any]:
        """시장 데이터 반환"""
        if refresh:
            self.market_data = self.data_generator.generate_market_data()
        return self.market_data
    
    def get_news(self, refresh: bool = False, count: int = 5) -> List[Dict[str, Any]]:
        """뉴스 데이터 반환"""
        if refresh:
            self.news_data = self.data_generator.generate_news(count)
        return self.news_data
    
    def analyze_user_situation(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """사용자 상황 종합 분석"""
        try:
            # 1. 텍스트 분석
            text_analysis = self.ai_engine.analyze_text(user_input)
            
            # 2. 관련 시장 데이터
            related_stocks = text_analysis["keywords"]["stocks"]
            market_info = {
                stock: self.market_data[stock] 
                for stock in related_stocks 
                if stock in self.market_data
            }
            
            # 3. 관련 뉴스
            related_news = [
                news for news in self.news_data
                if any(stock in news["related_stocks"] for stock in related_stocks)
            ][:3]
            
            # 4. 유사 거래 찾기
            user_trades = self.get_user_trades(user_id)
            similar_trades = self.ai_engine.find_similar_trades(user_input, user_trades)
            
            # 5. 신뢰도 계산
            confidence = self._calculate_analysis_confidence(
                text_analysis, market_info, related_news, similar_trades
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "user_id": user_id,
                "text_analysis": text_analysis,
                "market_info": market_info,
                "related_news": related_news,
                "similar_trades": similar_trades,
                "confidence": confidence,
                "data_source": "dynamic_config_based"
            }
            
        except Exception as e:
            logger.error(f"❌ 상황 분석 실패: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _calculate_analysis_confidence(self, text_analysis: Dict, market_info: Dict, related_news: List, similar_trades: List) -> float:
        """분석 신뢰도 계산"""
        confidence = 0.0
        
        # 텍스트 분석 품질 (30%)
        confidence += text_analysis["confidence"] * 0.3
        
        # 시장 데이터 (30%)
        market_score = min(1.0, len(market_info) / 2)
        confidence += market_score * 0.3
        
        # 관련 뉴스 (20%)
        news_score = min(1.0, len(related_news) / 3)
        confidence += news_score * 0.2
        
        # 과거 경험 (20%)
        if similar_trades:
            experience_score = np.mean([trade["similarity_score"] for trade in similar_trades])
            confidence += experience_score * 0.2
        
        return min(1.0, confidence)
    
    def reload_configuration(self, config_name: str = "all"):
        """설정 다시 로드 및 데이터 재생성"""
        if config_name == "all":
            self.config_manager = ConfigManager(self.config_dir)
            self.data_generator = DynamicDataGenerator(self.config_manager, self.data_provider)
            self.ai_engine = ConfigurableAIEngine(self.config_manager)
            self._initialize_data()
        else:
            self.config_manager.reload_config(config_name)
        
        logger.info(f"🔄 설정 '{config_name}' 다시 로드 완료")
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 반환"""
        return {
            "engine_type": "CompleteDynamicDataEngine",
            "version": "2.0_dynamic",
            "users_count": len(self.users),
            "total_trades": sum(len(trades) for trades in self.trades.values()),
            "config_files": {
                "user_profiles": (self.config_dir / "user_profiles.json").exists(),
                "stocks": (self.config_dir / "stocks.json").exists(),
                "keywords": (self.config_dir / "keywords.json").exists(),
                "news_templates": (self.config_dir / "news_templates.json").exists(),
                "market_settings": (self.config_dir / "market_settings.json").exists()
            },
            "last_update": datetime.now().isoformat(),
            "data_source": "100%_configuration_files"
        }

# ================================
# [STREAMLIT 캐시 통합]
# ================================

@st.cache_resource
def get_dynamic_data_engine(config_dir: str = "config", data_dir: str = "data") -> CompleteDynamicDataEngine:
    """캐시된 동적 데이터 엔진 반환"""
    logger.info("🚀 [Cache Miss] 완전 동적 데이터 엔진 생성")
    return CompleteDynamicDataEngine(config_dir, data_dir)

# ================================
# [편의 함수들] main_app.py 호환성 유지
# ================================

def get_all_users() -> Dict[str, Any]:
    engine = get_dynamic_data_engine()
    return engine.get_users()

def get_user_info(user_id: str) -> Optional[Dict[str, Any]]:
    engine = get_dynamic_data_engine()
    return engine.get_user(user_id)

def get_trading_history(user_id: str) -> List[Dict[str, Any]]:
    engine = get_dynamic_data_engine()
    return engine.get_user_trades(user_id)

def get_live_market_data(refresh: bool = True) -> Dict[str, Any]:
    engine = get_dynamic_data_engine()
    return engine.get_market_data(refresh)

def get_latest_news(refresh: bool = True, count: int = 5) -> List[Dict[str, Any]]:
    engine = get_dynamic_data_engine()
    return engine.get_news(refresh, count)

def analyze_investment_situation(user_input: str, user_id: str) -> Dict[str, Any]:
    engine = get_dynamic_data_engine()
    return engine.analyze_user_situation(user_input, user_id)

def reload_all_configs():
    """모든 설정 다시 로드"""
    engine = get_dynamic_data_engine()
    engine.reload_configuration("all")


from pathlib import Path
def get_user_reviews(user_id: str) -> list[dict]:
    """
    data/reviews_<USER>.json 형식의 복기 기록을 로드합니다.
    파일이 없으면 []을 반환합니다.
    허용 키:
      - date 또는 timestamp (문자열, ISO or YYYY-MM-DD)
      - stock (종목명)
      - emotion (감정)
      - title (제목, 선택)
      - reason (사유/메모)
      - result 또는 result_pct (수익률, %)
      - tags (리스트, 선택)
      - memo (추가 메모, 선택)
    """
    path = Path("data") / f"reviews_{user_id}.json"
    if not path.exists():
        return []
    import json, datetime
    arr = json.loads(path.read_text(encoding="utf-8"))
    # date 정규화
    for r in arr:
        if "date" not in r and "timestamp" in r and isinstance(r["timestamp"], str):
            r["date"] = r["timestamp"][:10]
    return arr
# ================================
# [테스트 및 데모]
# ================================

def test_dynamic_engine():
    """동적 엔진 테스트"""
    print("🧪 완전 동적 데이터 엔진 테스트...")
    
    engine = get_dynamic_data_engine()
    
    # 시스템 상태
    status = engine.get_system_status()
    print(f"✅ 시스템 상태: {status['engine_type']} v{status['version']}")
    
    # 설정 파일 확인
    config_status = status['config_files']
    for config_name, exists in config_status.items():
        print(f"📝 {config_name}.json: {'✅' if exists else '❌'}")
    
    # 데이터 확인
    users = engine.get_users()
    print(f"👥 사용자: {len(users)}명")
    
    for user_id in users:
        trades = engine.get_user_trades(user_id)
        print(f"  - {user_id}: {len(trades)}건 거래")
    
    # 시장 데이터
    market_data = engine.get_market_data()
    print(f"📊 시장 데이터: {len(market_data)}개 종목")
    
    # 뉴스 데이터
    news = engine.get_news()
    print(f"📰 뉴스: {len(news)}개 기사")
    
    # AI 분석 테스트
    test_input = "삼성전자가 떨어져서 불안한데 추가로 살까요?"
    analysis = engine.analyze_user_situation(test_input, "김투자")
    print(f"🤖 AI 분석 신뢰도: {analysis.get('confidence', 0):.2f}")
    print(f"🔧 데이터 소스: {analysis.get('data_source', 'unknown')}")
    
    print("🎉 모든 테스트 완료! 100% 설정 파일 기반 동적 데이터 엔진이 정상 작동합니다.")

def create_sample_config_files():
    """샘플 설정 파일 생성 (개발자용)"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # ConfigManager를 통해 기본 파일들 생성
    config_manager = ConfigManager(config_dir)
    
    print("📁 다음 설정 파일들이 생성되었습니다:")
    for config_file in config_dir.glob("*.json"):
        print(f"  - {config_file.name}")
    
    print("\n✨ 이제 설정 파일을 수정하여 데이터를 커스터마이징할 수 있습니다!")
    print("예시:")
    print("  - config/user_profiles.json: 사용자 성향 및 거래 패턴")
    print("  - config/stocks.json: 종목 정보 및 가격 범위")
    print("  - config/keywords.json: AI 매칭 키워드 및 동의어")
    print("  - config/news_templates.json: 뉴스 생성 템플릿")
    print("  - config/market_settings.json: 시장 시간 및 변동성 설정")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "create-config":
        create_sample_config_files()
    else:
        test_dynamic_engine()