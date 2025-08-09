"""
중앙 데이터 관리 시스템 (리팩터링 버전)
안정적/재현가능/확장가능한 데이터 관리를 위한 고도화된 시스템
모든 하드코딩된 데이터를 외부 데이터로 관리하며, 시드 고정, 캐싱, 동적 스캔 지원
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Protocol, Union
import requests
from dataclasses import dataclass, asdict, field
import random
import os
import shutil
from abc import ABC, abstractmethod

# ================================
# [CONFIG HOOK] 설정 로더
# ================================

def _load_config_settings():
    """환경변수 > app_settings.json의 demo_settings > 디폴트 순으로 설정 로드"""
    # 기본값
    defaults = {
        'DEMO_SEED': None,
        'PROVIDER_MODE': 'dummy',  # dummy(기본) | api(미래용)
        'DATA_ROOT': 'data'
    }
    
    # app_settings.json에서 demo_settings 읽기 시도
    try:
        settings_path = Path("app_settings.json")
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                app_config = json.load(f)
                demo_settings = app_config.get('demo_settings', {})
                for key in defaults:
                    if key.lower() in demo_settings:
                        defaults[key] = demo_settings[key.lower()]
    except Exception:
        pass  # 파일 없거나 파싱 실패 시 기본값 사용
    
    # 환경변수 우선 적용
    for key in defaults:
        env_val = os.environ.get(key)
        if env_val is not None:
            # 타입 변환
            if key == 'DEMO_SEED':
                try:
                    defaults[key] = int(env_val) if env_val.lower() != 'none' else None
                except ValueError:
                    pass
            else:
                defaults[key] = env_val
    
    return defaults

# 전역 설정 로드
_CONFIG = _load_config_settings()
DEMO_SEED = _CONFIG['DEMO_SEED']
PROVIDER_MODE = _CONFIG['PROVIDER_MODE']
DATA_ROOT = Path(_CONFIG['DATA_ROOT'])

# ================================
# [DETERMINISM] 시드 고정 (모듈 최초 초기화 시 단 한 번)
# ================================

_SEED_INITIALIZED = False

def _initialize_demo_seed():
    """데모 시드 초기화 (모듈당 단 한 번만 실행)"""
    global _SEED_INITIALIZED
    if not _SEED_INITIALIZED and DEMO_SEED is not None:
        random.seed(DEMO_SEED)
        np.random.seed(DEMO_SEED)
        _SEED_INITIALIZED = True
        print(f"[DEMO] Seed initialized: {DEMO_SEED}")

# 모듈 로드 시 시드 초기화
_initialize_demo_seed()

# ================================
# [DATA CLASSES] 
# ================================

@dataclass
class UserProfile:
    """사용자 프로필 데이터 클래스"""
    username: str
    user_type: str
    description: str
    icon: str
    color: str
    badge: str
    subtitle: str
    onboarding_type: str
    demo_trades_count: int = 0

@dataclass
class MarketData:
    """시장 데이터 클래스"""
    symbol: str
    name: str
    current_price: float
    change: float
    change_pct: float
    volume: int
    sector: str
    market_cap: str
    ma5: float
    ma20: float
    rsi: float
    per: float
    pbr: float
    base_price: float

@dataclass
class NewsItem:
    """뉴스 아이템 클래스"""
    title: str
    content: str
    timestamp: datetime
    category: str
    impact: str  # positive, negative, neutral
    related_stocks: List[str]

# ================================
# [PROVIDER INTERFACE] API 제공자 인터페이스
# ================================

class BaseProvider(Protocol):
    """금융 데이터 제공자 인터페이스"""
    
    @abstractmethod
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """주식 가격 조회"""
        pass
    
    @abstractmethod
    def get_market_news(self) -> List[Dict[str, Any]]:
        """시장 뉴스 조회"""
        pass
    
    @abstractmethod
    def get_economic_indicators(self) -> Dict[str, Any]:
        """경제 지표 조회"""
        pass

class DummyProvider:
    """더미 데이터 제공자 (현재 시뮬레이션 로직)"""
    
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        # 데모 모드에서는 변동성 줄임
        self.volatility_factor = 0.5 if demo_mode else 1.0
    
    def get_stock_price(self, symbol: str, base_price: float) -> float:
        """시뮬레이션된 주식 가격 반환"""
        # 데모 모드에서는 변동성 축소 (표준편차 절반)
        change_rate = random.gauss(0, 0.03 * self.volatility_factor)
        return max(base_price * (1 + change_rate), base_price * 0.8)
    
    def get_market_news(self) -> List[Dict[str, Any]]:
        """더미 뉴스 데이터 반환"""
        return []  # 기본 뉴스는 파일에서 로드
    
    def get_economic_indicators(self) -> Dict[str, Any]:
        """더미 경제 지표 반환"""
        return {}  # 기본 지표는 파일에서 로드

class APIProvider:
    """실제 API 데이터 제공자 (미래 확장용 - 현재는 스텁)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """실제 API를 통한 주식 가격 조회"""
        raise NotImplementedError("API Provider는 아직 구현되지 않았습니다")
    
    def get_market_news(self) -> List[Dict[str, Any]]:
        """실제 API를 통한 뉴스 조회"""
        raise NotImplementedError("API Provider는 아직 구현되지 않았습니다")
    
    def get_economic_indicators(self) -> Dict[str, Any]:
        """실제 API를 통한 경제 지표 조회"""
        raise NotImplementedError("API Provider는 아직 구현되지 않았습니다")

# ================================
# [MAIN DATA MANAGER]
# ================================

class CentralDataManager:
    """중앙 데이터 관리 클래스 (고도화 버전)"""
    
    def __init__(self):
        self.data_dir = DATA_ROOT
        self.data_dir.mkdir(exist_ok=True)
        
        # [캐시 시스템] 메모리 캐시와 파일 변경 감지
        self._cache = {}
        self._file_index = {}  # 파일별 mtime 추적
        
        # [상태 추적] 복구/에러 상태 기록
        self._status = {
            'repairs': [],      # 데이터 복구 이력
            'errors': [],       # 에러 로그
            'last_refresh': None,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # [Provider 초기화]
        if PROVIDER_MODE == 'api':
            self.provider = APIProvider()  # 현재는 NotImplementedError 발생
        else:
            # 데모 시드가 설정된 경우 데모 모드로 초기화
            self.provider = DummyProvider(demo_mode=(DEMO_SEED is not None))
        
        self._load_all_data()
    
    def _safe_path(self, username: str) -> Path:
        """경로 탈출 방지를 위한 안전한 경로 생성"""
        user_path = (self.data_dir / username).resolve()
        data_root_resolved = self.data_dir.resolve()
        
        # 경로가 DATA_ROOT 하위에 있는지 검증
        try:
            user_path.relative_to(data_root_resolved)
            return user_path
        except ValueError:
            raise ValueError(f"안전하지 않은 경로: {username}")
    
    def _get_file_mtime(self, filepath: Path) -> float:
        """파일 변경 시간 조회"""
        try:
            return filepath.stat().st_mtime if filepath.exists() else 0
        except OSError:
            return 0
    
    def _is_cache_valid(self, cache_key: str, filepath: Path) -> bool:
        """캐시 유효성 검사 (mtime 기반)"""
        if cache_key not in self._cache:
            return False
        
        current_mtime = self._get_file_mtime(filepath)
        cached_mtime = self._file_index.get(str(filepath), 0)
        
        return current_mtime == cached_mtime
    
    def _update_cache(self, cache_key: str, data: Any, filepath: Path):
        """캐시 업데이트"""
        self._cache[cache_key] = data
        self._file_index[str(filepath)] = self._get_file_mtime(filepath)
    
    def _safe_json_load(self, filepath: Path, default_data: Any = None) -> Any:
        """안전한 JSON 로드 (백업 및 복구 기능)"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # 파일이 손상된 경우 백업 생성
            if filepath.exists() and isinstance(e, json.JSONDecodeError):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = filepath.with_suffix(f'.corrupt-{timestamp}.json')
                try:
                    shutil.copy2(filepath, backup_path)
                    self._status['errors'].append(
                        f"JSON 파싱 실패: {filepath.name} -> 백업: {backup_path.name}"
                    )
                except Exception:
                    pass
            
            # 기본값 반환 및 복구 기록
            self._status['repairs'].append(
                f"파일 복구: {filepath.name} -> 기본값 사용"
            )
            return default_data if default_data is not None else {}
    
    def _safe_json_save(self, filepath: Path, data: Any) -> bool:
        """안전한 JSON 저장"""
        try:
            # 임시 파일에 먼저 저장 후 원자적 이동
            temp_path = filepath.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # 원자적 이동
            temp_path.replace(filepath)
            return True
        except Exception as e:
            self._status['errors'].append(f"파일 저장 실패: {filepath.name} - {str(e)}")
            return False
    
    def _validate_and_repair_user_data(self, data: Dict) -> UserProfile:
        """사용자 데이터 유효성 검사 및 복구"""
        # 필수 필드 기본값
        defaults = {
            'username': '알수없음',
            'user_type': '신규',
            'description': '기본 사용자',
            'icon': '👤',
            'color': '#3182F6',
            'badge': 'USER',
            'subtitle': '기본 사용자',
            'onboarding_type': 'principles',
            'demo_trades_count': 0
        }
        
        repaired = False
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
                repaired = True
        
        # 타입 검증 및 복구
        if not isinstance(data.get('demo_trades_count'), int):
            try:
                data['demo_trades_count'] = int(data.get('demo_trades_count', 0))
            except (ValueError, TypeError):
                data['demo_trades_count'] = 0
                repaired = True
        
        if repaired:
            self._status['repairs'].append(
                f"사용자 데이터 복구: {data.get('username', '알수없음')}"
            )
        
        return UserProfile(**data)
    
    def _scan_users(self) -> Dict[str, UserProfile]:
        """동적 사용자 스캔: data/{username}/profile.json 우선, users.json 폴백"""
        users = {}
        
        # 1. 개별 사용자 폴더 스캔 (우선순위)
        if self.data_dir.exists():
            for item in self.data_dir.iterdir():
                if item.is_dir():
                    profile_path = item / "profile.json"
                    if profile_path.exists():
                        try:
                            profile_data = self._safe_json_load(profile_path)
                            if profile_data:
                                # username이 없으면 폴더명 사용
                                if 'username' not in profile_data:
                                    profile_data['username'] = item.name
                                
                                user_profile = self._validate_and_repair_user_data(profile_data)
                                users[user_profile.username] = user_profile
                        except Exception as e:
                            self._status['errors'].append(
                                f"사용자 프로필 로드 실패: {item.name} - {str(e)}"
                            )
        
        # 2. users.json 폴백 (충돌 시 필드 병합)
        users_file = self.data_dir / "users.json"
        if users_file.exists():
            users_data = self._safe_json_load(users_file, {})
            
            for username, data in users_data.items():
                if username in users:
                    # 기존 사용자가 있으면 누락된 필드만 병합
                    existing_data = asdict(users[username])
                    for key, value in data.items():
                        if key not in existing_data or existing_data[key] is None:
                            existing_data[key] = value
                    users[username] = self._validate_and_repair_user_data(existing_data)
                else:
                    # 새 사용자 추가
                    users[username] = self._validate_and_repair_user_data(data)
        
        # 3. 기본 사용자가 없으면 생성
        if not users:
            default_users_data = self._get_default_users_data()
            for username, data in default_users_data.items():
                users[username] = self._validate_and_repair_user_data(data)
            
            # users.json에 저장
            self._safe_json_save(users_file, default_users_data)
        
        return users
    
    def _get_default_users_data(self) -> Dict[str, Dict]:
        """기본 사용자 데이터 반환"""
        return {
            "이거울": {
                "username": "이거울",
                "user_type": "신규",
                "description": "투자를 처음 시작하는 신규 사용자",
                "icon": "🆕",
                "color": "#3182F6",
                "badge": "NEW",
                "subtitle": "거래 데이터 없음 • 투자 원칙 학습 필요",
                "onboarding_type": "principles",
                "demo_trades_count": 0
            },
            "박투자": {
                "username": "박투자",
                "user_type": "기존_reflex처음",
                "description": "FOMO 매수 경향이 있는 기존 고객",
                "icon": "🔄",
                "color": "#FF9500",
                "badge": "ACTIVE",
                "subtitle": "1,500건 거래 데이터 • 추격매수 패턴 분석 필요",
                "onboarding_type": "trade_selection",
                "demo_trades_count": 1500
            },
            "김국민": {
                "username": "김국민",
                "user_type": "기존_reflex사용중",
                "description": "공포 매도 경향, Reflex 기존 사용자",
                "icon": "⭐",
                "color": "#14AE5C",
                "badge": "PRO",
                "subtitle": "1,500건 거래 데이터 • 복기 노트 보유",
                "onboarding_type": None,
                "demo_trades_count": 1500
            }
        }
    
    def _load_all_data(self):
        """모든 데이터 로드 (캐시 고려)"""
        self.users = self._scan_users()
        self.market_data = self._load_market_data()
        self.news_data = self._load_news_data()
        self.economic_indicators = self._load_economic_indicators()
        self.demo_trades = self._load_demo_trades()
        self._status['last_refresh'] = datetime.now()
    
    def _load_market_data(self, refresh: bool = False) -> Dict[str, MarketData]:
        """시장 데이터 로드 (캐싱 지원)"""
        market_file = self.data_dir / "market_data.json"
        cache_key = "market_data"
        
        # 캐시 유효성 검사
        if not refresh and self._is_cache_valid(cache_key, market_file):
            self._status['cache_hits'] += 1
            return self._cache[cache_key]
        
        self._status['cache_misses'] += 1
        
        # 기본 종목 정보
        default_stocks = {
            "005930": {"name": "삼성전자", "base_price": 65000, "sector": "IT", "market_cap": "대형"},
            "000660": {"name": "SK하이닉스", "base_price": 120000, "sector": "IT", "market_cap": "대형"},
            "035420": {"name": "NAVER", "base_price": 180000, "sector": "IT", "market_cap": "대형"},
            "035720": {"name": "카카오", "base_price": 45000, "sector": "IT", "market_cap": "대형"},
            "051910": {"name": "LG화학", "base_price": 380000, "sector": "화학", "market_cap": "대형"},
            "005380": {"name": "현대차", "base_price": 180000, "sector": "자동차", "market_cap": "대형"},
            "005490": {"name": "POSCO홀딩스", "base_price": 350000, "sector": "철강", "market_cap": "대형"},
            "015760": {"name": "한국전력", "base_price": 22000, "sector": "전력", "market_cap": "대형"},
            "105560": {"name": "KB금융", "base_price": 48000, "sector": "금융", "market_cap": "대형"},
            "066570": {"name": "LG전자", "base_price": 95000, "sector": "전자", "market_cap": "대형"},
            "068270": {"name": "셀트리온", "base_price": 160000, "sector": "바이오", "market_cap": "대형"},
            "017670": {"name": "SK텔레콤", "base_price": 52000, "sector": "통신", "market_cap": "대형"}
        }
        
        base_data = self._safe_json_load(market_file, default_stocks)
        
        # 파일이 없었다면 생성
        if not market_file.exists():
            self._safe_json_save(market_file, default_stocks)
        
        # 실시간 가격 시뮬레이션
        market_data = {}
        for symbol, info in base_data.items():
            current_price = self.provider.get_stock_price(symbol, info["base_price"])
            change = current_price - info["base_price"]
            change_pct = (change / info["base_price"]) * 100
            
            # 데모 모드에서는 변동성 축소
            volume_base = 1000000
            volume_variance = 500000 if DEMO_SEED is None else 200000
            
            market_data[info["name"]] = MarketData(
                symbol=symbol,
                name=info["name"],
                current_price=current_price,
                change=change,
                change_pct=change_pct,
                volume=random.randint(volume_base - volume_variance, volume_base + volume_variance),
                sector=info["sector"],
                market_cap=info["market_cap"],
                ma5=current_price + random.gauss(0, info["base_price"] * 0.005 * (self.provider.volatility_factor if hasattr(self.provider, 'volatility_factor') else 1)),
                ma20=current_price + random.gauss(0, info["base_price"] * 0.01 * (self.provider.volatility_factor if hasattr(self.provider, 'volatility_factor') else 1)),
                rsi=random.randint(25, 75),  # 데모에서는 극값 제한
                per=random.uniform(10, 20),
                pbr=random.uniform(0.8, 2.0),
                base_price=info["base_price"]
            )
        
        # 캐시 업데이트
        self._update_cache(cache_key, market_data, market_file)
        return market_data
    
    def _load_news_data(self, refresh: bool = False) -> List[NewsItem]:
        """뉴스 데이터 로드 (캐싱 지원)"""
        news_file = self.data_dir / "news_data.json"
        cache_key = "news_data"
        
        # 캐시 유효성 검사
        if not refresh and self._is_cache_valid(cache_key, news_file):
            self._status['cache_hits'] += 1
            return self._cache[cache_key]
        
        self._status['cache_misses'] += 1
        
        default_news = [
            {
                "title": "반도체 수요 증가로 삼성전자, SK하이닉스 주가 상승 전망",
                "content": "AI 및 데이터센터 수요 급증으로 메모리 반도체 업계에 호재...",
                "timestamp": "2024-08-09T09:00:00",
                "category": "IT",
                "impact": "positive",
                "related_stocks": ["삼성전자", "SK하이닉스"]
            },
            {
                "title": "전기차 시장 둔화 우려로 자동차주 약세",
                "content": "글로벌 전기차 판매 증가율 둔화로 관련 업체들 주가 하락...",
                "timestamp": "2024-08-09T10:30:00",
                "category": "자동차",
                "impact": "negative",
                "related_stocks": ["현대차"]
            },
            {
                "title": "코스피 2450선 회복, 외국인 순매수 지속",
                "content": "외국인 투자자들의 지속적인 순매수로 코스피 지수가 상승세...",
                "timestamp": "2024-08-09T11:15:00",
                "category": "시장",
                "impact": "positive",
                "related_stocks": ["전체"]
            }
        ]
        
        news_data_raw = self._safe_json_load(news_file, default_news)
        
        # 파일이 없었다면 생성
        if not news_file.exists():
            self._safe_json_save(news_file, default_news)
        
        # NewsItem 객체로 변환
        news_data = []
        for item in news_data_raw:
            try:
                news_data.append(NewsItem(
                    title=item.get("title", "제목 없음"),
                    content=item.get("content", "내용 없음"),
                    timestamp=datetime.fromisoformat(item.get("timestamp", datetime.now().isoformat())),
                    category=item.get("category", "일반"),
                    impact=item.get("impact", "neutral"),
                    related_stocks=item.get("related_stocks", [])
                ))
            except Exception as e:
                self._status['repairs'].append(f"뉴스 아이템 복구: {item.get('title', '제목없음')}")
        
        # 캐시 업데이트
        self._update_cache(cache_key, news_data, news_file)
        return news_data
    
    def _load_economic_indicators(self, refresh: bool = False) -> Dict[str, Any]:
        """경제 지표 데이터 로드 (캐싱 지원)"""
        indicators_file = self.data_dir / "economic_indicators.json"
        cache_key = "economic_indicators"
        
        # 캐시 유효성 검사
        if not refresh and self._is_cache_valid(cache_key, indicators_file):
            self._status['cache_hits'] += 1
            return self._cache[cache_key]
        
        self._status['cache_misses'] += 1
        
        default_indicators = {
            "KOSPI": {
                "current": 2450.32,
                "change": 12.45,
                "change_pct": 0.51,
                "volume": 8500000
            },
            "KOSDAQ": {
                "current": 750.25,
                "change": -3.21,
                "change_pct": -0.43,
                "volume": 5200000
            },
            "USD_KRW": {
                "current": 1340.50,
                "change": 5.20,
                "change_pct": 0.39
            },
            "interest_rate": 3.50,
            "inflation_rate": 2.4,
            "unemployment_rate": 2.8
        }
        
        indicators = self._safe_json_load(indicators_file, default_indicators)
        
        # 파일이 없었다면 생성
        if not indicators_file.exists():
            self._safe_json_save(indicators_file, default_indicators)
        
        # 캐시 업데이트
        self._update_cache(cache_key, indicators, indicators_file)
        return indicators
    
    def _load_demo_trades(self, refresh: bool = False) -> Dict[str, List[Dict]]:
        """사용자별 데모 거래 데이터 로드 (캐싱 지원)"""
        trades_file = self.data_dir / "demo_trades.json"
        cache_key = "demo_trades"
        
        # 캐시 유효성 검사
        if not refresh and self._is_cache_valid(cache_key, trades_file):
            self._status['cache_hits'] += 1
            return self._cache[cache_key]
        
        self._status['cache_misses'] += 1
        
        trades_data = self._safe_json_load(trades_file, {})
        
        # 거래 데이터가 없으면 생성
        if not trades_data:
            for username, user in self.users.items():
                if user.demo_trades_count > 0:
                    trades_data[username] = self._generate_demo_trades(username, user.demo_trades_count)
                else:
                    trades_data[username] = []
            
            self._safe_json_save(trades_file, trades_data)
        
        # 캐시 업데이트
        self._update_cache(cache_key, trades_data, trades_file)
        return trades_data
    
    def _generate_demo_trades(self, username: str, count: int) -> List[Dict]:
        """사용자별 거래 패턴에 맞는 데모 거래 생성 (시드 영향 반영)"""
        trades = []
        stocks = list(self.market_data.keys()) if self.market_data else ["삼성전자", "SK하이닉스"]
        
        # 사용자별 거래 패턴 (데모 모드에서는 극단적 패턴 완화)
        if username == "박투자":
            emotions = ["#욕심", "#확신", "#흥분"] * 3 + ["#불안", "#후회"] * 2
            success_rate = 0.4 if DEMO_SEED else 0.35  # 데모에서는 조금 더 관대
        elif username == "김국민":
            emotions = ["#공포", "#불안"] * 2 + ["#냉정", "#확신"] * 3
            success_rate = 0.6 if DEMO_SEED else 0.55
        else:
            emotions = ["#냉정", "#확신"] * 3 + ["#불안", "#욕심"] * 2
            success_rate = 0.55 if DEMO_SEED else 0.50
        
        for i in range(min(count, 100)):  # 최대 100개만 생성
            stock = random.choice(stocks)
            base_price = getattr(self.market_data.get(stock), 'base_price', 50000)
            
            # 거래 수익률 생성 (데모 모드에서는 극값 제한)
            if random.random() < success_rate:
                max_gain = 20 if DEMO_SEED else 30
                return_pct = random.uniform(1, max_gain)
            else:
                max_loss = -20 if DEMO_SEED else -30
                return_pct = random.uniform(max_loss, -1)
            
            trade_date = datetime.now() - timedelta(days=random.randint(1, 365))
            
            trades.append({
                "거래일시": trade_date.strftime("%Y-%m-%d"),
                "종목명": stock,
                "거래구분": random.choice(["매수", "매도"]),
                "수량": random.randint(10, 500),
                "가격": int(base_price * random.uniform(0.9, 1.1)),
                "수익률": round(return_pct, 2),
                "감정태그": random.choice(emotions),
                "메모": f"{stock} {['상승', '하락'][return_pct < 0]} 예상으로 거래"
            })
        
        return sorted(trades, key=lambda x: x["거래일시"], reverse=True)
    
    def _validate_trade_data(self, trade_data: Dict) -> bool:
        """거래 데이터 유효성 검사"""
        required_fields = ["거래일시", "종목명", "거래구분", "수량", "가격"]
        
        # 필수 필드 확인
        for field in required_fields:
            if field not in trade_data:
                self._status['errors'].append(f"거래 데이터 필수 필드 누락: {field}")
                return False
        
        # 날짜 형식 검증
        try:
            if isinstance(trade_data["거래일시"], str):
                datetime.strptime(trade_data["거래일시"], "%Y-%m-%d")
            elif not isinstance(trade_data["거래일시"], datetime):
                raise ValueError("날짜 형식 오류")
        except (ValueError, TypeError):
            self._status['errors'].append("거래 데이터 날짜 형식 오류")
            return False
        
        # 수치 데이터 검증
        try:
            int(trade_data["수량"])
            float(trade_data["가격"])
        except (ValueError, TypeError):
            self._status['errors'].append("거래 데이터 수치 형식 오류")
            return False
        
        # 거래구분 검증
        if trade_data["거래구분"] not in ["매수", "매도"]:
            self._status['errors'].append("거래구분 값 오류")
            return False
        
        return True
    
    # ================================
    # [PUBLIC API - 읽기 전용]
    # ================================
    
    def status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            'last_refresh': self._status['last_refresh'],
            'repairs': self._status['repairs'][-10:],  # 최근 10개만
            'errors': self._status['errors'][-10:],    # 최근 10개만
            'cache_stats': {
                'hits': self._status['cache_hits'],
                'misses': self._status['cache_misses'],
                'hit_ratio': self._status['cache_hits'] / max(1, self._status['cache_hits'] + self._status['cache_misses'])
            },
            'provider_mode': PROVIDER_MODE,
            'demo_seed': DEMO_SEED
        }
    
    def get_user(self, username: str) -> Optional[UserProfile]:
        """사용자 정보 조회"""
        return self.users.get(username)
    
    def get_all_users(self, refresh: bool = False) -> List[UserProfile]:
        """모든 사용자 정보 조회"""
        if refresh:
            self.users = self._scan_users()
        return list(self.users.values())
    
    def get_market_data(self, refresh: bool = False) -> Dict[str, MarketData]:
        """시장 데이터 조회"""
        if refresh:
            self.market_data = self._load_market_data(refresh=True)
        return self.market_data
    
    def get_stock_data(self, stock_name: str, refresh: bool = False) -> Optional[MarketData]:
        """특정 종목 데이터 조회"""
        if refresh:
            self.market_data = self._load_market_data(refresh=True)
        return self.market_data.get(stock_name)
    
    def get_news(self, category: str = None, hours_back: int = 24, refresh: bool = False) -> List[NewsItem]:
        """뉴스 데이터 조회"""
        if refresh:
            self.news_data = self._load_news_data(refresh=True)
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        filtered_news = [
            news for news in self.news_data 
            if news.timestamp >= cutoff_time
        ]
        
        if category:
            filtered_news = [
                news for news in filtered_news 
                if news.category == category
            ]
        
        return sorted(filtered_news, key=lambda x: x.timestamp, reverse=True)
    
    def get_economic_indicators(self, refresh: bool = False) -> Dict[str, Any]:
        """경제 지표 조회"""
        if refresh:
            self.economic_indicators = self._load_economic_indicators(refresh=True)
        return self.economic_indicators
    
    def get_user_trades(self, username: str, refresh: bool = False) -> List[Dict]:
        """사용자 거래 내역 조회"""
        if refresh:
            self.demo_trades = self._load_demo_trades(refresh=True)
        return self.demo_trades.get(username, [])
    
    # ================================
    # [PUBLIC API - 쓰기 전용]
    # ================================
    
    def update_user_trade(self, username: str, trade_data: Dict) -> bool:
        """
        사용자 거래 추가 (쓰기 전용)
        
        Args:
            username: 사용자명
            trade_data: 거래 데이터 (필수: 거래일시, 종목명, 거래구분, 수량, 가격)
        
        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        try:
            # 경로 안전성 검증
            self._safe_path(username)
            
            # 데이터 유효성 검사
            if not self._validate_trade_data(trade_data):
                return False
            
            # 사용자 거래 목록 초기화
            if username not in self.demo_trades:
                self.demo_trades[username] = []
            
            # 거래 데이터 추가
            self.demo_trades[username].append(trade_data)
            
            # 파일에 저장
            trades_file = self.data_dir / "demo_trades.json"
            if self._safe_json_save(trades_file, self.demo_trades):
                # 캐시 무효화
                cache_key = "demo_trades"
                if cache_key in self._cache:
                    del self._cache[cache_key]
                return True
            else:
                # 저장 실패 시 메모리에서도 제거
                self.demo_trades[username].pop()
                return False
                
        except Exception as e:
            self._status['errors'].append(f"거래 추가 실패: {username} - {str(e)}")
            return False
    
    # ================================
    # [PUBLIC API - 캐시 관리]
    # ================================
    
    def refresh_market_data(self):
        """시장 데이터 강제 갱신"""
        self.market_data = self._load_market_data(refresh=True)
    
    def refresh_news_data(self):
        """뉴스 데이터 강제 갱신"""
        self.news_data = self._load_news_data(refresh=True)
    
    def refresh_all_data(self):
        """모든 데이터 강제 갱신"""
        self._cache.clear()
        self._file_index.clear()
        self._load_all_data()
    
    def clear_cache(self):
        """캐시 클리어"""
        self._cache.clear()
        self._file_index.clear()
        self._status['cache_hits'] = 0
        self._status['cache_misses'] = 0

# ================================
# [GLOBAL SINGLETON]
# ================================

_data_manager = None

def get_data_manager() -> CentralDataManager:
    """데이터 매니저 싱글톤 인스턴스 반환"""
    global _data_manager
    if _data_manager is None:
        _data_manager = CentralDataManager()
    return _data_manager

# ================================
# [CONVENIENCE FUNCTIONS] 
# ================================

def get_user_profile(username: str) -> Optional[UserProfile]:
    """사용자 프로필 조회"""
    return get_data_manager().get_user(username)

def get_market_data(refresh: bool = False) -> Dict[str, MarketData]:
    """시장 데이터 조회"""
    return get_data_manager().get_market_data(refresh)

def get_stock_data(stock_name: str) -> Optional[MarketData]:
    """종목 데이터 조회"""
    return get_data_manager().get_stock_data(stock_name)

def get_latest_news(category: str = None) -> List[NewsItem]:
    """최신 뉴스 조회"""
    return get_data_manager().get_news(category, hours_back=24)

def get_economic_data() -> Dict[str, Any]:
    """경제 지표 조회"""
    return get_data_manager().get_economic_indicators()

def get_user_trading_history(username: str) -> List[Dict]:
    """사용자 거래 이력 조회"""
    return get_data_manager().get_user_trades(username)

def add_user_trade(username: str, trade_data: Dict) -> bool:
    """사용자 거래 추가"""
    return get_data_manager().update_user_trade(username, trade_data)

def get_system_status() -> Dict[str, Any]:
    """시스템 상태 조회"""
    return get_data_manager().status()

# ================================
# [LEGACY COMPATIBILITY]
# ================================

# 기존 FinanceAPIConnector 클래스는 하위 호환성을 위해 유지
FinanceAPIConnector = APIProvider