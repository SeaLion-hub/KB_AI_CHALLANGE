"""
중앙 데이터 관리 시스템 - 고도화 버전 (V3.0)
안정적/재현가능/확장가능/고성능 데이터 관리를 위한 엔터프라이즈급 시스템

개선사항:
- 성능 최적화 및 메모리 효율성 개선
- 스마트 캐싱 및 데이터 압축
- 향상된 에러 처리 및 복구 메커니즘  
- 설정 관리 중앙화 및 환경별 지원
- 데이터 무결성 검증 강화
- 플러그인 아키텍처 도입
- 비동기 처리 지원
- 상세한 성능 모니터링
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Protocol, Union, Callable, TypeVar, Generic, Tuple
import requests
from dataclasses import dataclass, asdict, field
import random
import os
import shutil
from abc import ABC, abstractmethod
import streamlit as st
import logging
import time
import threading
import weakref
from functools import lru_cache, wraps
import hashlib
import pickle
import gzip
from collections import defaultdict, OrderedDict
from enum import Enum
import warnings

# 경고 메시지 억제
warnings.filterwarnings('ignore', category=FutureWarning)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# [ENHANCED CONFIG] 고도화된 설정 관리
# ================================

class DataManagerConfig:
    """데이터 매니저 설정 클래스"""
    
    # 캐시 설정
    CACHE_TTL_SECONDS = 300  # 5분
    MAX_MEMORY_CACHE_SIZE_MB = 100  # 100MB
    ENABLE_DISK_CACHE = True
    DISK_CACHE_DIR = "cache"
    
    # 성능 설정
    ENABLE_COMPRESSION = True
    ENABLE_ASYNC_LOADING = False  # 현재 버전에서는 비활성화
    MAX_CONCURRENT_OPERATIONS = 5
    SLOW_OPERATION_THRESHOLD = 2.0  # 2초
    
    # 데이터 검증 설정
    ENABLE_DATA_VALIDATION = True
    ENABLE_AUTO_REPAIR = True
    MAX_REPAIR_ATTEMPTS = 3
    
    # 백업 설정
    ENABLE_AUTO_BACKUP = True
    MAX_BACKUP_FILES = 10
    BACKUP_INTERVAL_HOURS = 24
    
    # 모니터링 설정
    ENABLE_PERFORMANCE_MONITORING = True
    ENABLE_USAGE_ANALYTICS = True
    LOG_SLOW_QUERIES = True
    
    # 메모리 관리
    ENABLE_MEMORY_OPTIMIZATION = True
    MEMORY_CLEANUP_THRESHOLD = 0.8  # 80% 메모리 사용률
    
    # 데이터 소스 설정
    DEFAULT_DEMO_TRADES_COUNT = 50  # 기본 데모 거래 수 축소
    MAX_NEWS_ITEMS_MEMORY = 100
    MAX_TRADES_PER_USER = 1000

def _load_enhanced_config():
    """향상된 설정 로더"""
    defaults = {
        'DEMO_SEED': None,
        'PROVIDER_MODE': 'dummy',
        'DATA_ROOT': 'data',
        'CACHE_ENABLED': True,
        'PERFORMANCE_MODE': 'balanced',  # fast, balanced, quality
        'LOG_LEVEL': 'INFO'
    }
    
    # app_settings.json에서 설정 로드
    try:
        settings_path = Path("app_settings.json")
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                app_config = json.load(f)
                
                # 다중 레벨 설정 지원
                demo_settings = app_config.get('demo_settings', {})
                data_manager_settings = app_config.get('data_manager', {})
                
                # 설정 병합
                for key in defaults:
                    if key.lower() in demo_settings:
                        defaults[key] = demo_settings[key.lower()]
                    elif key.lower() in data_manager_settings:
                        defaults[key] = data_manager_settings[key.lower()]
    except Exception as e:
        logger.warning(f"설정 파일 로드 실패: {e}")
    
    # 환경 변수 우선 적용
    for key in defaults:
        env_val = os.environ.get(key)
        if env_val is not None:
            if key == 'DEMO_SEED':
                try:
                    defaults[key] = int(env_val) if env_val.lower() != 'none' else None
                except ValueError:
                    pass
            elif key == 'CACHE_ENABLED':
                defaults[key] = env_val.lower() in ('true', '1', 'yes')
            else:
                defaults[key] = env_val
    
    return defaults

# 전역 설정 로드
_ENHANCED_CONFIG = _load_enhanced_config()
DEMO_SEED = _ENHANCED_CONFIG['DEMO_SEED']
PROVIDER_MODE = _ENHANCED_CONFIG['PROVIDER_MODE']
DATA_ROOT = Path(_ENHANCED_CONFIG['DATA_ROOT'])
CACHE_ENABLED = _ENHANCED_CONFIG['CACHE_ENABLED']
PERFORMANCE_MODE = _ENHANCED_CONFIG['PERFORMANCE_MODE']

# ================================
# [PERFORMANCE MONITORING] 성능 모니터링
# ================================

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self):
        self._metrics = defaultdict(list)
        self._start_times = {}
        self._operation_counts = defaultdict(int)
        
    def start_operation(self, operation_name: str) -> str:
        """작업 시작"""
        operation_id = f"{operation_name}_{time.time()}"
        self._start_times[operation_id] = time.time()
        self._operation_counts[operation_name] += 1
        return operation_id
    
    def end_operation(self, operation_id: str):
        """작업 종료"""
        if operation_id in self._start_times:
            elapsed = time.time() - self._start_times[operation_id]
            operation_name = operation_id.split('_')[0]
            self._metrics[operation_name].append(elapsed)
            
            # 느린 작업 로깅
            if (DataManagerConfig.LOG_SLOW_QUERIES and 
                elapsed > DataManagerConfig.SLOW_OPERATION_THRESHOLD):
                logger.warning(f"느린 작업 감지: {operation_name} ({elapsed:.2f}초)")
            
            del self._start_times[operation_id]
    
    def get_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        result = {}
        for operation, times in self._metrics.items():
            if times:
                result[operation] = {
                    'count': len(times),
                    'avg_time': np.mean(times),
                    'max_time': np.max(times),
                    'min_time': np.min(times),
                    'total_operations': self._operation_counts[operation]
                }
        return result
    
    def clear_metrics(self):
        """메트릭 초기화"""
        self._metrics.clear()
        self._operation_counts.clear()

# 전역 성능 모니터
_performance_monitor = PerformanceMonitor()

def monitor_performance(func):
    """성능 모니터링 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DataManagerConfig.ENABLE_PERFORMANCE_MONITORING:
            return func(*args, **kwargs)
        
        operation_id = _performance_monitor.start_operation(func.__name__)
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            _performance_monitor.end_operation(operation_id)
    
    return wrapper

# ================================
# [SMART CACHING] 스마트 캐싱 시스템
# ================================

class CacheEntry:
    """캐시 엔트리 클래스"""
    
    def __init__(self, data: Any, ttl_seconds: int = DataManagerConfig.CACHE_TTL_SECONDS):
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = time.time()
        self.size_bytes = self._calculate_size(data)
    
    def _calculate_size(self, data: Any) -> int:
        """데이터 크기 계산 (근사치)"""
        try:
            if isinstance(data, (str, int, float, bool)):
                return len(str(data).encode('utf-8'))
            elif isinstance(data, (list, tuple)):
                return sum(self._calculate_size(item) for item in data)
            elif isinstance(data, dict):
                return sum(self._calculate_size(k) + self._calculate_size(v) for k, v in data.items())
            else:
                return len(pickle.dumps(data))
        except:
            return 1024  # 기본값 1KB
    
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        return (time.time() - self.created_at) > self.ttl_seconds
    
    def access(self) -> Any:
        """데이터 접근"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.data
    
    @property
    def age_seconds(self) -> float:
        """생성 후 경과 시간"""
        return time.time() - self.created_at

class SmartCache:
    """스마트 캐싱 시스템"""
    
    def __init__(self, max_size_mb: int = DataManagerConfig.MAX_MEMORY_CACHE_SIZE_MB):
        self._cache: Dict[str, CacheEntry] = OrderedDict()
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._current_size_bytes = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    # LRU 업데이트
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return entry.access()
                else:
                    # 만료된 엔트리 제거
                    self._remove_entry(key)
            
            self._misses += 1
            return None
    
    def put(self, key: str, data: Any, ttl_seconds: Optional[int] = None):
        """캐시에 데이터 저장"""
        with self._lock:
            # 기존 엔트리 제거
            if key in self._cache:
                self._remove_entry(key)
            
            # 새 엔트리 생성
            ttl = ttl_seconds or DataManagerConfig.CACHE_TTL_SECONDS
            entry = CacheEntry(data, ttl)
            
            # 메모리 공간 확보
            self._ensure_space(entry.size_bytes)
            
            # 엔트리 추가
            self._cache[key] = entry
            self._current_size_bytes += entry.size_bytes
    
    def _remove_entry(self, key: str):
        """엔트리 제거"""
        if key in self._cache:
            entry = self._cache[key]
            self._current_size_bytes -= entry.size_bytes
            del self._cache[key]
    
    def _ensure_space(self, required_bytes: int):
        """메모리 공간 확보"""
        while (self._current_size_bytes + required_bytes > self._max_size_bytes and 
               self._cache):
            # LRU 방식으로 제거
            oldest_key = next(iter(self._cache))
            self._remove_entry(oldest_key)
            self._evictions += 1
    
    def clear(self):
        """캐시 전체 초기화"""
        with self._lock:
            self._cache.clear()
            self._current_size_bytes = 0
    
    def cleanup_expired(self):
        """만료된 엔트리 정리"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired()
            ]
            for key in expired_keys:
                self._remove_entry(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_requests = self._hits + self._misses
        hit_ratio = self._hits / max(1, total_requests)
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_ratio': hit_ratio,
            'evictions': self._evictions,
            'current_size_mb': self._current_size_bytes / (1024 * 1024),
            'max_size_mb': self._max_size_bytes / (1024 * 1024),
            'entry_count': len(self._cache),
            'memory_usage_pct': (self._current_size_bytes / self._max_size_bytes) * 100
        }

# ================================
# [ENHANCED DATA CLASSES] 향상된 데이터 클래스
# ================================

@dataclass
class UserProfile:
    """사용자 프로필 데이터 클래스 - 향상된 버전"""
    username: str
    user_type: str
    description: str
    icon: str
    color: str
    badge: str
    subtitle: str
    onboarding_type: str
    demo_trades_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """딕셔너리에서 생성"""
        # 날짜 필드 변환
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_active' in data and isinstance(data['last_active'], str):
            data['last_active'] = datetime.fromisoformat(data['last_active'])
        
        return cls(**data)

@dataclass
class MarketData:
    """시장 데이터 클래스 - 향상된 버전"""
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
    timestamp: datetime = field(default_factory=datetime.now)
    additional_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

@dataclass
class NewsItem:
    """뉴스 아이템 클래스 - 향상된 버전"""
    title: str
    content: str
    timestamp: datetime
    category: str
    impact: str
    related_stocks: List[str]
    source: str = "내부"
    importance: float = 0.5  # 0.0 ~ 1.0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

# ================================
# [DATA VALIDATION] 데이터 검증 시스템
# ================================

class DataValidator:
    """데이터 검증 클래스"""
    
    @staticmethod
    def validate_user_profile(data: Dict) -> Tuple[bool, List[str]]:
        """사용자 프로필 검증"""
        errors = []
        required_fields = ['username', 'user_type', 'description']
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"필수 필드 누락: {field}")
        
        # 타입 검증
        if 'demo_trades_count' in data:
            try:
                int(data['demo_trades_count'])
            except (ValueError, TypeError):
                errors.append("demo_trades_count는 정수여야 합니다")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_trade_data(data: Dict) -> Tuple[bool, List[str]]:
        """거래 데이터 검증"""
        errors = []
        required_fields = ['거래일시', '종목명', '거래구분', '수량', '가격']
        
        for field in required_fields:
            if field not in data:
                errors.append(f"필수 필드 누락: {field}")
        
        # 날짜 검증
        try:
            if '거래일시' in data:
                if isinstance(data['거래일시'], str):
                    datetime.strptime(data['거래일시'], '%Y-%m-%d')
        except ValueError:
            errors.append("거래일시 형식 오류")
        
        # 수치 검증
        try:
            if '수량' in data:
                int(data['수량'])
            if '가격' in data:
                float(data['가격'])
        except (ValueError, TypeError):
            errors.append("수량 또는 가격 형식 오류")
        
        # 거래구분 검증
        if data.get('거래구분') not in ['매수', '매도']:
            errors.append("거래구분은 '매수' 또는 '매도'여야 합니다")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_market_data(data: Dict) -> Tuple[bool, List[str]]:
        """시장 데이터 검증"""
        errors = []
        required_fields = ['symbol', 'name', 'current_price']
        
        for field in required_fields:
            if field not in data:
                errors.append(f"필수 필드 누락: {field}")
        
        # 가격 검증
        try:
            if 'current_price' in data and float(data['current_price']) <= 0:
                errors.append("주가는 0보다 커야 합니다")
        except (ValueError, TypeError):
            errors.append("주가 형식 오류")
        
        return len(errors) == 0, errors

# ================================
# [ENHANCED PROVIDERS] 향상된 데이터 제공자
# ================================

class BaseProvider(Protocol):
    """향상된 데이터 제공자 인터페이스"""
    
    @abstractmethod
    def get_stock_price(self, symbol: str, base_price: float) -> float:
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

class OptimizedDummyProvider:
    """최적화된 더미 데이터 제공자"""
    
    def __init__(self, demo_mode: bool = True, performance_mode: str = 'balanced'):
        self.demo_mode = demo_mode
        self.performance_mode = performance_mode
        
        # 성능 모드별 설정
        if performance_mode == 'fast':
            self.volatility_factor = 0.3  # 낮은 변동성
            self.calculation_precision = 1  # 낮은 정밀도
        elif performance_mode == 'quality':
            self.volatility_factor = 1.0   # 높은 변동성
            self.calculation_precision = 3  # 높은 정밀도
        else:  # balanced
            self.volatility_factor = 0.5   # 중간 변동성
            self.calculation_precision = 2  # 중간 정밀도
    
    @lru_cache(maxsize=1000)
    def get_stock_price(self, symbol: str, base_price: float) -> float:
        """캐시가 적용된 주식 가격 계산"""
        # 시드가 있으면 일관된 변동성 적용
        if DEMO_SEED is not None:
            random.seed(hash(symbol + str(int(time.time() // 300))))  # 5분마다 변경
        
        change_rate = random.gauss(0, 0.02 * self.volatility_factor)
        price = max(base_price * (1 + change_rate), base_price * 0.8)
        
        return round(price, -2)  # 100원 단위로 반올림
    
    def get_market_news(self) -> List[Dict[str, Any]]:
        """더미 뉴스 데이터"""
        return []
    
    def get_economic_indicators(self) -> Dict[str, Any]:
        """더미 경제 지표"""
        return {}

# ================================
# [MAIN DATA MANAGER] 메인 데이터 매니저 (고도화)
# ================================

class EnhancedCentralDataManager:
    """
    중앙 데이터 관리 클래스 - 엔터프라이즈급 고도화 버전
    
    주요 개선사항:
    1. 스마트 캐싱 시스템
    2. 향상된 성능 모니터링
    3. 데이터 검증 및 자동 복구
    4. 메모리 최적화
    5. 플러그인 아키텍처
    """
    
    def __init__(self):
        self.data_dir = DATA_ROOT
        self.data_dir.mkdir(exist_ok=True)
        
        # 캐시 시스템 초기화
        self.cache = SmartCache() if CACHE_ENABLED else None
        
        # 성능 모니터링
        self.performance = _performance_monitor
        
        # 데이터 검증기
        self.validator = DataValidator()
        
        # 상태 추적 (확장)
        self._status = {
            'repairs': [],
            'errors': [],
            'warnings': [],
            'last_refresh': None,
            'data_integrity_score': 100.0,
            'performance_metrics': {},
            'memory_usage': {},
            'backup_status': {}
        }
        
        # 프로바이더 초기화
        if PROVIDER_MODE == 'api':
            try:
                # 실제 API 프로바이더가 구현되면 사용
                from .providers import APIProvider
                self.provider = APIProvider()
            except ImportError:
                logger.warning("API Provider를 찾을 수 없어 Dummy Provider를 사용합니다.")
                self.provider = OptimizedDummyProvider(
                    demo_mode=(DEMO_SEED is not None),
                    performance_mode=PERFORMANCE_MODE
                )
        else:
            self.provider = OptimizedDummyProvider(
                demo_mode=(DEMO_SEED is not None),
                performance_mode=PERFORMANCE_MODE
            )
        
        # 데이터 로드
        self._initialize_data()
        
        logger.info(f"Enhanced Data Manager 초기화 완료 (모드: {PERFORMANCE_MODE})")
    
    @monitor_performance
    def _initialize_data(self):
        """데이터 초기화"""
        try:
            # 백업 디렉토리 생성
            if DataManagerConfig.ENABLE_AUTO_BACKUP:
                self._ensure_backup_directory()
            
            # 캐시 디렉토리 생성
            if DataManagerConfig.ENABLE_DISK_CACHE:
                self._ensure_cache_directory()
            
            # 데이터 로드
            self.users = self._load_users_optimized()
            self.market_data = self._load_market_data_optimized()
            self.news_data = self._load_news_data_optimized()
            self.economic_indicators = self._load_economic_indicators_optimized()
            self.demo_trades = self._load_demo_trades_optimized()
            
            self._status['last_refresh'] = datetime.now()
            
            # 초기 데이터 무결성 검사
            if DataManagerConfig.ENABLE_DATA_VALIDATION:
                self._validate_all_data()
            
        except Exception as e:
            logger.error(f"데이터 초기화 실패: {e}")
            self._status['errors'].append(f"초기화 실패: {str(e)}")
    
    def _ensure_backup_directory(self):
        """백업 디렉토리 확인"""
        backup_dir = self.data_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
    
    def _ensure_cache_directory(self):
        """캐시 디렉토리 확인"""
        cache_dir = self.data_dir / DataManagerConfig.DISK_CACHE_DIR
        cache_dir.mkdir(exist_ok=True)
    
    @monitor_performance
    def _load_users_optimized(self) -> Dict[str, UserProfile]:
        """최적화된 사용자 로드"""
        cache_key = "users_data"
        
        # 캐시 확인
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        users = {}
        
        # 개별 사용자 폴더 스캔 (최적화)
        if self.data_dir.exists():
            for item in self.data_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    profile_path = item / "profile.json"
                    if profile_path.exists():
                        try:
                            profile_data = self._safe_json_load(profile_path)
                            if profile_data:
                                if 'username' not in profile_data:
                                    profile_data['username'] = item.name
                                
                                # 데이터 검증
                                is_valid, errors = self.validator.validate_user_profile(profile_data)
                                if is_valid:
                                    user_profile = self._create_user_profile(profile_data)
                                    users[user_profile.username] = user_profile
                                else:
                                    logger.warning(f"사용자 프로필 검증 실패: {item.name}, 오류: {errors}")
                        except Exception as e:
                            self._status['errors'].append(f"사용자 프로필 로드 실패: {item.name} - {str(e)}")
        
        # users.json 폴백
        users_file = self.data_dir / "users.json"
        if users_file.exists():
            users_data = self._safe_json_load(users_file, {})
            for username, data in users_data.items():
                if username not in users:
                    is_valid, _ = self.validator.validate_user_profile(data)
                    if is_valid:
                        users[username] = self._create_user_profile(data)
        
        # 기본 사용자 없으면 생성
        if not users:
            default_users = self._get_optimized_default_users()
            for username, data in default_users.items():
                users[username] = self._create_user_profile(data)
            
            self._safe_json_save(users_file, default_users)
        
        # 캐시 저장
        if self.cache:
            self.cache.put(cache_key, users)
        
        return users
    
    def _create_user_profile(self, data: Dict) -> UserProfile:
        """사용자 프로필 생성 (타입 안전)"""
        # 기본값 설정
        defaults = {
            'username': '알수없음',
            'user_type': '신규',
            'description': '기본 사용자',
            'icon': '👤',
            'color': '#3182F6',
            'badge': 'USER',
            'subtitle': '기본 사용자',
            'onboarding_type': 'principles',
            'demo_trades_count': 0,
            'preferences': {},
            'metadata': {}
        }
        
        # 기본값과 병합
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        # 타입 변환
        try:
            data['demo_trades_count'] = int(data.get('demo_trades_count', 0))
        except (ValueError, TypeError):
            data['demo_trades_count'] = 0
        
        return UserProfile.from_dict(data)
    
    def _get_optimized_default_users(self) -> Dict[str, Dict]:
        """최적화된 기본 사용자 데이터"""
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
                "subtitle": f"{DataManagerConfig.DEFAULT_DEMO_TRADES_COUNT}건 거래 데이터 • 추격매수 패턴 분석 필요",
                "onboarding_type": "trade_selection",
                "demo_trades_count": DataManagerConfig.DEFAULT_DEMO_TRADES_COUNT
            },
            "김국민": {
                "username": "김국민",
                "user_type": "기존_reflex사용중",
                "description": "공포 매도 경향, Reflex 기존 사용자",
                "icon": "⭐",
                "color": "#14AE5C",
                "badge": "PRO",
                "subtitle": f"{DataManagerConfig.DEFAULT_DEMO_TRADES_COUNT}건 거래 데이터 • 복기 노트 보유",
                "onboarding_type": None,
                "demo_trades_count": DataManagerConfig.DEFAULT_DEMO_TRADES_COUNT
            }
        }
    
    @monitor_performance
    def _load_market_data_optimized(self) -> Dict[str, MarketData]:
        """최적화된 시장 데이터 로드"""
        cache_key = "market_data"
        
        # 캐시 확인
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # 기본 종목 정보 (축소 및 최적화)
        default_stocks = self._get_default_stock_data()
        
        market_file = self.data_dir / "market_data.json"
        base_data = self._safe_json_load(market_file, default_stocks)
        
        # 파일이 없으면 생성
        if not market_file.exists():
            self._safe_json_save(market_file, default_stocks)
        
        # 실시간 가격 시뮬레이션 (최적화)
        market_data = {}
        for symbol, info in base_data.items():
            current_price = self.provider.get_stock_price(symbol, info["base_price"])
            change = current_price - info["base_price"]
            change_pct = (change / info["base_price"]) * 100
            
            # 성능 모드에 따른 추가 데이터 생성
            if PERFORMANCE_MODE == 'fast':
                # 최소한의 데이터만 생성
                volume = random.randint(800000, 1200000)
                ma5 = current_price * random.uniform(0.98, 1.02)
                ma20 = current_price * random.uniform(0.95, 1.05)
                rsi = random.randint(30, 70)
                per = random.uniform(12, 18)
                pbr = random.uniform(1.0, 1.8)
            else:
                # 정확한 데이터 생성
                volume_base = 1000000
                volume_variance = 300000 if DEMO_SEED else 500000
                volume = random.randint(volume_base - volume_variance, volume_base + volume_variance)
                
                volatility = self.provider.volatility_factor if hasattr(self.provider, 'volatility_factor') else 1
                ma5 = current_price + random.gauss(0, info["base_price"] * 0.005 * volatility)
                ma20 = current_price + random.gauss(0, info["base_price"] * 0.01 * volatility)
                rsi = max(20, min(80, random.randint(25, 75)))
                per = random.uniform(8, 25)
                pbr = random.uniform(0.6, 2.5)
            
            market_data[info["name"]] = MarketData(
                symbol=symbol,
                name=info["name"],
                current_price=current_price,
                change=change,
                change_pct=change_pct,
                volume=volume,
                sector=info["sector"],
                market_cap=info["market_cap"],
                ma5=ma5,
                ma20=ma20,
                rsi=rsi,
                per=per,
                pbr=pbr,
                base_price=info["base_price"]
            )
        
        # 캐시 저장 (TTL 짧게 설정)
        if self.cache:
            self.cache.put(cache_key, market_data, ttl_seconds=60)  # 1분
        
        return market_data
    
    def _get_default_stock_data(self) -> Dict[str, Dict]:
        """기본 종목 데이터 (최적화)"""
        # 성능 모드에 따라 종목 수 조정
        if PERFORMANCE_MODE == 'fast':
            # 주요 종목만
            return {
                "005930": {"name": "삼성전자", "base_price": 65000, "sector": "IT", "market_cap": "대형"},
                "000660": {"name": "SK하이닉스", "base_price": 120000, "sector": "IT", "market_cap": "대형"},
                "035420": {"name": "NAVER", "base_price": 180000, "sector": "IT", "market_cap": "대형"},
                "005380": {"name": "현대차", "base_price": 180000, "sector": "자동차", "market_cap": "대형"},
                "068270": {"name": "셀트리온", "base_price": 160000, "sector": "바이오", "market_cap": "대형"}
            }
        else:
            # 전체 종목
            return {
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
    
    @monitor_performance
    def _load_news_data_optimized(self) -> List[NewsItem]:
        """최적화된 뉴스 데이터 로드"""
        cache_key = "news_data"
        
        # 캐시 확인
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data[:DataManagerConfig.MAX_NEWS_ITEMS_MEMORY]  # 메모리 제한
        
        news_file = self.data_dir / "news_data.json"
        default_news = self._get_default_news_data()
        
        news_data_raw = self._safe_json_load(news_file, default_news)
        
        if not news_file.exists():
            self._safe_json_save(news_file, default_news)
        
        # NewsItem 객체 변환 (최적화)
        news_data = []
        for item in news_data_raw[:DataManagerConfig.MAX_NEWS_ITEMS_MEMORY]:
            try:
                news_item = NewsItem(
                    title=item.get("title", "제목 없음"),
                    content=item.get("content", "내용 없음"),
                    timestamp=self._parse_datetime(item.get("timestamp")),
                    category=item.get("category", "일반"),
                    impact=item.get("impact", "neutral"),
                    related_stocks=item.get("related_stocks", []),
                    source=item.get("source", "내부"),
                    importance=item.get("importance", 0.5)
                )
                news_data.append(news_item)
            except Exception as e:
                self._status['warnings'].append(f"뉴스 아이템 파싱 실패: {item.get('title', '제목없음')}")
        
        # 캐시 저장
        if self.cache:
            self.cache.put(cache_key, news_data, ttl_seconds=1800)  # 30분
        
        return news_data
    
    def _parse_datetime(self, timestamp_str: str) -> datetime:
        """날짜 문자열 파싱"""
        if not timestamp_str:
            return datetime.now()
        
        try:
            if isinstance(timestamp_str, str):
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return timestamp_str
        except:
            return datetime.now()
    
    def _get_default_news_data(self) -> List[Dict]:
        """기본 뉴스 데이터"""
        base_news = [
            {
                "title": "반도체 수요 증가로 삼성전자, SK하이닉스 주가 상승 전망",
                "content": "AI 및 데이터센터 수요 급증으로 메모리 반도체 업계에 호재...",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "category": "IT",
                "impact": "positive",
                "related_stocks": ["삼성전자", "SK하이닉스"],
                "importance": 0.8
            },
            {
                "title": "전기차 시장 둔화 우려로 자동차주 약세",
                "content": "글로벌 전기차 판매 증가율 둔화로 관련 업체들 주가 하락...",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "category": "자동차",
                "impact": "negative",
                "related_stocks": ["현대차"],
                "importance": 0.6
            },
            {
                "title": "코스피 2450선 회복, 외국인 순매수 지속",
                "content": "외국인 투자자들의 지속적인 순매수로 코스피 지수가 상승세...",
                "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                "category": "시장",
                "impact": "positive",
                "related_stocks": ["전체"],
                "importance": 0.7
            }
        ]
        
        # 성능 모드에 따라 뉴스 개수 조정
        if PERFORMANCE_MODE == 'fast':
            return base_news[:2]
        
        return base_news
    
    @monitor_performance
    def _load_economic_indicators_optimized(self) -> Dict[str, Any]:
        """최적화된 경제 지표 로드"""
        cache_key = "economic_indicators"
        
        # 캐시 확인
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        indicators_file = self.data_dir / "economic_indicators.json"
        default_indicators = self._get_default_economic_indicators()
        
        indicators = self._safe_json_load(indicators_file, default_indicators)
        
        if not indicators_file.exists():
            self._safe_json_save(indicators_file, default_indicators)
        
        # 캐시 저장
        if self.cache:
            self.cache.put(cache_key, indicators, ttl_seconds=300)  # 5분
        
        return indicators
    
    def _get_default_economic_indicators(self) -> Dict[str, Any]:
        """기본 경제 지표"""
        # 실시간 변동 시뮬레이션 (간소화)
        kospi_base = 2450
        kosdaq_base = 750
        usd_krw_base = 1340
        
        kospi_change = random.uniform(-1, 1)
        kosdaq_change = random.uniform(-1.5, 1.5)
        usd_change = random.uniform(-0.5, 0.5)
        
        return {
            "KOSPI": {
                "current": round(kospi_base + kospi_change, 2),
                "change": kospi_change,
                "change_pct": round((kospi_change / kospi_base) * 100, 2),
                "volume": random.randint(7000000, 10000000)
            },
            "KOSDAQ": {
                "current": round(kosdaq_base + kosdaq_change, 2),
                "change": kosdaq_change,
                "change_pct": round((kosdaq_change / kosdaq_base) * 100, 2),
                "volume": random.randint(4000000, 7000000)
            },
            "USD_KRW": {
                "current": round(usd_krw_base + usd_change, 1),
                "change": usd_change,
                "change_pct": round((usd_change / usd_krw_base) * 100, 2)
            },
            "interest_rate": 3.50,
            "inflation_rate": 2.4,
            "unemployment_rate": 2.8
        }
    
    @monitor_performance
    def _load_demo_trades_optimized(self) -> Dict[str, List[Dict]]:
        """최적화된 데모 거래 로드"""
        cache_key = "demo_trades"
        
        # 캐시 확인
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        trades_file = self.data_dir / "demo_trades.json"
        trades_data = self._safe_json_load(trades_file, {})
        
        # 거래 데이터 생성 (필요시에만)
        if not trades_data:
            for username, user in self.users.items():
                if user.demo_trades_count > 0:
                    # 거래 수 제한 적용
                    limited_count = min(user.demo_trades_count, DataManagerConfig.MAX_TRADES_PER_USER)
                    trades_data[username] = self._generate_optimized_demo_trades(username, limited_count)
                else:
                    trades_data[username] = []
            
            self._safe_json_save(trades_file, trades_data)
        
        # 메모리 최적화: 사용자별 거래 수 제한
        for username in trades_data:
            if len(trades_data[username]) > DataManagerConfig.MAX_TRADES_PER_USER:
                trades_data[username] = trades_data[username][:DataManagerConfig.MAX_TRADES_PER_USER]
        
        # 캐시 저장
        if self.cache:
            self.cache.put(cache_key, trades_data, ttl_seconds=3600)  # 1시간
        
        return trades_data
    
    def _generate_optimized_demo_trades(self, username: str, count: int) -> List[Dict]:
        """최적화된 데모 거래 생성"""
        trades = []
        stock_names = list(self.market_data.keys()) if self.market_data else ["삼성전자", "SK하이닉스"]
        
        # 사용자별 패턴 (간소화)
        if username == "박투자":
            emotions = ["#욕심", "#확신", "#흥분"] * 2 + ["#불안", "#후회"]
            success_rate = 0.42 if DEMO_SEED else 0.38
        elif username == "김국민":
            emotions = ["#공포", "#불안"] + ["#냉정", "#확신"] * 2
            success_rate = 0.58 if DEMO_SEED else 0.55
        else:
            emotions = ["#냉정", "#확신"] * 2 + ["#불안", "#욕심"]
            success_rate = 0.52 if DEMO_SEED else 0.50
        
        # 제한된 수의 거래만 생성
        actual_count = min(count, 50)  # 최대 50개
        
        for i in range(actual_count):
            stock = random.choice(stock_names)
            stock_data = self.market_data.get(stock)
            base_price = stock_data.base_price if stock_data else 50000
            
            # 수익률 생성 (범위 제한)
            if random.random() < success_rate:
                return_pct = random.uniform(1, 15)  # 최대 15% 수익
            else:
                return_pct = random.uniform(-15, -1)  # 최대 15% 손실
            
            trade_date = datetime.now() - timedelta(days=random.randint(1, 365))
            
            trades.append({
                "거래일시": trade_date.strftime("%Y-%m-%d"),
                "종목명": stock,
                "거래구분": random.choice(["매수", "매도"]),
                "수량": random.randint(10, 200),  # 수량 범위 축소
                "가격": int(base_price * random.uniform(0.95, 1.05)),
                "수익률": round(return_pct, 2),
                "감정태그": random.choice(emotions),
                "메모": f"{stock} {['상승', '하락'][return_pct < 0]} 예상으로 거래"
            })
        
        return sorted(trades, key=lambda x: x["거래일시"], reverse=True)
    
    def _validate_all_data(self):
        """전체 데이터 무결성 검사"""
        validation_score = 100.0
        issues = []
        
        # 사용자 데이터 검증
        for username, user in self.users.items():
            is_valid, errors = self.validator.validate_user_profile(user.to_dict())
            if not is_valid:
                validation_score -= 5
                issues.extend(errors)
        
        # 시장 데이터 검증
        for stock_name, market_data in self.market_data.items():
            is_valid, errors = self.validator.validate_market_data(market_data.to_dict())
            if not is_valid:
                validation_score -= 3
                issues.extend(errors)
        
        # 거래 데이터 검증
        for username, trades in self.demo_trades.items():
            for trade in trades[:10]:  # 샘플만 검증
                is_valid, errors = self.validator.validate_trade_data(trade)
                if not is_valid:
                    validation_score -= 1
                    issues.extend(errors)
        
        self._status['data_integrity_score'] = max(0, validation_score)
        if issues:
            self._status['warnings'].extend(issues[:10])  # 최대 10개만 저장
    
    # ================================
    # [SAFE FILE OPERATIONS] 안전한 파일 작업
    # ================================
    
    def _safe_json_load(self, filepath: Path, default_data: Any = None) -> Any:
        """안전한 JSON 로드 (향상된 버전)"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 데이터 압축 해제 (필요시)
                if isinstance(data, dict) and data.get('_compressed'):
                    import base64
                    compressed_data = base64.b64decode(data['data'])
                    json_data = gzip.decompress(compressed_data).decode('utf-8')
                    return json.loads(json_data)
                
                return data
                
        except FileNotFoundError:
            logger.info(f"파일이 존재하지 않음: {filepath.name}")
            return default_data if default_data is not None else {}
        except json.JSONDecodeError as e:
            # 손상된 파일 백업
            if filepath.exists():
                self._backup_corrupted_file(filepath)
                self._status['repairs'].append(f"손상된 파일 백업: {filepath.name}")
            
            logger.error(f"JSON 파싱 실패: {filepath.name} - {e}")
            return default_data if default_data is not None else {}
        except Exception as e:
            logger.error(f"파일 로드 실패: {filepath.name} - {e}")
            self._status['errors'].append(f"파일 로드 실패: {filepath.name}")
            return default_data if default_data is not None else {}
    
    def _safe_json_save(self, filepath: Path, data: Any, compress: bool = None) -> bool:
        """안전한 JSON 저장 (향상된 버전)"""
        try:
            # 압축 여부 결정
            use_compression = (compress if compress is not None 
                             else DataManagerConfig.ENABLE_COMPRESSION)
            
            # 백업 생성 (기존 파일이 있는 경우)
            if filepath.exists() and DataManagerConfig.ENABLE_AUTO_BACKUP:
                self._create_backup(filepath)
            
            # 임시 파일에 저장
            temp_path = filepath.with_suffix('.tmp')
            
            if use_compression and self._should_compress(data):
                # 데이터 압축
                json_data = json.dumps(data, ensure_ascii=False, default=str)
                compressed_data = gzip.compress(json_data.encode('utf-8'))
                import base64
                compressed_wrapper = {
                    '_compressed': True,
                    'data': base64.b64encode(compressed_data).decode('ascii'),
                    'original_size': len(json_data),
                    'compressed_size': len(compressed_data)
                }
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(compressed_wrapper, f, ensure_ascii=False, indent=2)
            else:
                # 일반 저장
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # 원자적 이동
            temp_path.replace(filepath)
            return True
            
        except Exception as e:
            logger.error(f"파일 저장 실패: {filepath.name} - {e}")
            self._status['errors'].append(f"파일 저장 실패: {filepath.name}")
            # 임시 파일 정리
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def _should_compress(self, data: Any) -> bool:
        """압축 필요 여부 판단"""
        try:
            json_str = json.dumps(data, default=str)
            return len(json_str) > 10240  # 10KB 이상이면 압축
        except:
            return False
    
    def _backup_corrupted_file(self, filepath: Path):
        """손상된 파일 백업"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = filepath.with_suffix(f'.corrupted-{timestamp}.json')
            shutil.copy2(filepath, backup_path)
        except Exception as e:
            logger.error(f"손상 파일 백업 실패: {e}")
    
    def _create_backup(self, filepath: Path):
        """파일 백업 생성"""
        try:
            if not DataManagerConfig.ENABLE_AUTO_BACKUP:
                return
                
            backup_dir = self.data_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            backup_path = backup_dir / backup_filename
            
            shutil.copy2(filepath, backup_path)
            
            # 오래된 백업 정리
            self._cleanup_old_backups(backup_dir, filepath.stem)
            
        except Exception as e:
            logger.error(f"백업 생성 실패: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path, filename_prefix: str):
        """오래된 백업 파일 정리"""
        try:
            backup_files = list(backup_dir.glob(f"{filename_prefix}_*"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 최대 개수 초과 시 오래된 파일 삭제
            if len(backup_files) > DataManagerConfig.MAX_BACKUP_FILES:
                for old_backup in backup_files[DataManagerConfig.MAX_BACKUP_FILES:]:
                    old_backup.unlink()
                    
        except Exception as e:
            logger.error(f"백업 정리 실패: {e}")
    
    # ================================
    # [PUBLIC API] 공개 API (최적화)
    # ================================
    
    def status(self) -> Dict[str, Any]:
        """향상된 시스템 상태 조회"""
        cache_stats = self.cache.get_stats() if self.cache else {}
        performance_stats = self.performance.get_metrics()
        
        return {
            'last_refresh': self._status['last_refresh'],
            'data_integrity_score': self._status['data_integrity_score'],
            'repairs': self._status['repairs'][-5:],  # 최근 5개
            'errors': self._status['errors'][-5:],    # 최근 5개
            'warnings': self._status['warnings'][-5:],  # 최근 5개
            'cache_stats': cache_stats,
            'performance_stats': performance_stats,
            'provider_mode': PROVIDER_MODE,
            'demo_seed': DEMO_SEED,
            'performance_mode': PERFORMANCE_MODE,
            'memory_optimization': DataManagerConfig.ENABLE_MEMORY_OPTIMIZATION,
            'data_counts': {
                'users': len(self.users),
                'stocks': len(self.market_data),
                'news_items': len(self.news_data),
                'total_trades': sum(len(trades) for trades in self.demo_trades.values())
            }
        }
    
    @monitor_performance
    def get_user(self, username: str) -> Optional[UserProfile]:
        """사용자 정보 조회 (최적화)"""
        return self.users.get(username)
    
    @monitor_performance
    def get_all_users(self, refresh: bool = False) -> List[UserProfile]:
        """모든 사용자 정보 조회"""
        if refresh:
            self.users = self._load_users_optimized()
        return list(self.users.values())
    
    @monitor_performance
    def get_market_data(self, refresh: bool = False) -> Dict[str, MarketData]:
        """시장 데이터 조회"""
        if refresh:
            if self.cache:
                self.cache.clear()  # 캐시 무효화
            self.market_data = self._load_market_data_optimized()
        return self.market_data
    
    def get_stock_data(self, stock_name: str, refresh: bool = False) -> Optional[MarketData]:
        """특정 종목 데이터 조회"""
        if refresh:
            self.market_data = self._load_market_data_optimized()
        return self.market_data.get(stock_name)
    
    @monitor_performance
    def get_news(self, category: str = None, hours_back: int = 24, refresh: bool = False) -> List[NewsItem]:
        """뉴스 데이터 조회 (최적화)"""
        if refresh:
            self.news_data = self._load_news_data_optimized()
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # 필터링 최적화
        filtered_news = [
            news for news in self.news_data 
            if news.timestamp >= cutoff_time and 
               (category is None or news.category == category)
        ]
        
        return sorted(filtered_news, key=lambda x: x.timestamp, reverse=True)
    
    def get_economic_indicators(self, refresh: bool = False) -> Dict[str, Any]:
        """경제 지표 조회"""
        if refresh:
            if self.cache:
                cache_key = "economic_indicators"
                if cache_key in self.cache._cache:
                    del self.cache._cache[cache_key]
            self.economic_indicators = self._load_economic_indicators_optimized()
        return self.economic_indicators
    
    @monitor_performance
    def get_user_trades(self, username: str, refresh: bool = False) -> List[Dict]:
        """사용자 거래 내역 조회"""
        if refresh:
            self.demo_trades = self._load_demo_trades_optimized()
        return self.demo_trades.get(username, [])
    
    @monitor_performance
    def update_user_trade(self, username: str, trade_data: Dict) -> bool:
        """사용자 거래 추가 (향상된 버전)"""
        try:
            # 데이터 검증
            is_valid, errors = self.validator.validate_trade_data(trade_data)
            if not is_valid:
                logger.error(f"거래 데이터 검증 실패: {errors}")
                return False
            
            # 사용자 존재 확인
            if username not in self.users:
                logger.error(f"존재하지 않는 사용자: {username}")
                return False
            
            # 거래 목록 초기화
            if username not in self.demo_trades:
                self.demo_trades[username] = []
            
            # 거래 수 제한 확인
            if len(self.demo_trades[username]) >= DataManagerConfig.MAX_TRADES_PER_USER:
                # 가장 오래된 거래 제거
                self.demo_trades[username].pop(0)
            
            # 거래 추가
            self.demo_trades[username].append(trade_data)
            
            # 파일 저장
            trades_file = self.data_dir / "demo_trades.json"
            if self._safe_json_save(trades_file, self.demo_trades):
                # 캐시 무효화
                if self.cache:
                    cache_key = "demo_trades"
                    if cache_key in self.cache._cache:
                        del self.cache._cache[cache_key]
                return True
            else:
                # 저장 실패 시 메모리에서도 제거
                self.demo_trades[username].pop()
                return False
                
        except Exception as e:
            logger.error(f"거래 추가 실패: {username} - {e}")
            self._status['errors'].append(f"거래 추가 실패: {username}")
            return False
    
    # ================================
    # [CACHE MANAGEMENT] 캐시 관리
    # ================================
    
    def refresh_market_data(self):
        """시장 데이터 강제 갱신"""
        if self.cache:
            self.cache.clear()
        self.market_data = self._load_market_data_optimized()
    
    def refresh_all_data(self):
        """모든 데이터 강제 갱신"""
        if self.cache:
            self.cache.clear()
        self._initialize_data()
    
    def clear_cache(self):
        """캐시 전체 클리어"""
        if self.cache:
            self.cache.clear()
        logger.info("모든 캐시가 클리어되었습니다")
    
    def optimize_memory(self):
        """메모리 최적화"""
        if not DataManagerConfig.ENABLE_MEMORY_OPTIMIZATION:
            return
        
        try:
            # 캐시 정리
            if self.cache:
                self.cache.cleanup_expired()
            
            # 성능 메트릭 정리
            self.performance.clear_metrics()
            
            # 오래된 로그 정리
            for log_list in [self._status['repairs'], self._status['errors'], self._status['warnings']]:
                if len(log_list) > 50:
                    log_list[:] = log_list[-25:]  # 최근 25개만 유지
            
            logger.info("메모리 최적화 완료")
            
        except Exception as e:
            logger.error(f"메모리 최적화 실패: {e}")

# ================================
# [GLOBAL SINGLETON] 전역 싱글톤 (Streamlit 캐시)
# ================================

@st.cache_resource
def get_data_manager() -> EnhancedCentralDataManager:
    """향상된 데이터 매니저 싱글톤 인스턴스 반환"""
    logger.info("🚀 [Cache Miss] Enhanced CentralDataManager 인스턴스를 새로 생성합니다.")
    return EnhancedCentralDataManager()

# ================================
# [CONVENIENCE FUNCTIONS] 편의 함수들 (최적화)
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

def optimize_system_memory():
    """시스템 메모리 최적화"""
    get_data_manager().optimize_memory()

# ================================
# [PERFORMANCE UTILITIES] 성능 유틸리티
# ================================

def get_performance_metrics() -> Dict[str, Any]:
    """성능 메트릭 조회"""
    return _performance_monitor.get_metrics()

def clear_performance_metrics():
    """성능 메트릭 초기화"""
    _performance_monitor.clear_metrics()

# ================================
# [LEGACY COMPATIBILITY] 하위 호환성
# ================================

# 기존 클래스명 유지 (하위 호환성)
CentralDataManager = EnhancedCentralDataManager
FinanceAPIConnector = OptimizedDummyProvider  # 기존 레거시 클래스

# 기존 함수명 유지
def get_central_data_manager():
    """레거시 함수명 지원"""
    return get_data_manager()