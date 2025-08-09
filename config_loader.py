"""
설정 및 데이터 자동 로딩 모듈 - 고도화 버전 (V2.0)
안정적이고 확장 가능한 설정 관리 시스템

개선사항:
- 에러 처리 강화
- 캐싱 시스템 개선
- 타입 안전성 향상
- 동적 설정 로딩
- 백업/복원 기능
- 설정 검증
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import streamlit as st
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """설정 검증 오류"""
    pass

class ConfigLoader:
    """설정 및 데이터 자동 로딩 클래스"""
    
    def __init__(self, config_dir: str = "config", enable_backup: bool = True):
        """
        ConfigLoader 초기화
        
        Args:
            config_dir: 설정 파일 디렉토리
            enable_backup: 백업 기능 활성화 여부
        """
        self.config_dir = Path(__file__).parent.parent / config_dir
        self.backup_dir = self.config_dir / "backups"
        self.enable_backup = enable_backup
        self._cache = {}
        self._cache_timestamps = {}
        
        # 디렉토리 생성
        self.config_dir.mkdir(exist_ok=True)
        if self.enable_backup:
            self.backup_dir.mkdir(exist_ok=True)
        
        logger.info(f"ConfigLoader 초기화 완료: {self.config_dir}")
    
    def _backup_config(self, filename: str) -> bool:
        """설정 파일 백업"""
        if not self.enable_backup:
            return True
            
        try:
            source_path = self.config_dir / filename
            if not source_path.exists():
                return True
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{filename.stem}_{timestamp}{filename.suffix}"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(source_path, backup_path)
            
            # 오래된 백업 파일 정리 (최근 10개만 유지)
            self._cleanup_old_backups(filename)
            
            logger.debug(f"백업 완료: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"백업 실패 ({filename}): {str(e)}")
            return False
    
    def _cleanup_old_backups(self, filename: str, keep_count: int = 10):
        """오래된 백업 파일 정리"""
        try:
            pattern = f"{Path(filename).stem}_*{Path(filename).suffix}"
            backup_files = list(self.backup_dir.glob(pattern))
            
            # 수정 시간 기준 정렬
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 오래된 파일들 삭제
            for old_file in backup_files[keep_count:]:
                old_file.unlink()
                logger.debug(f"오래된 백업 삭제: {old_file.name}")
                
        except Exception as e:
            logger.error(f"백업 정리 실패: {str(e)}")
    
    def _is_cache_valid(self, filename: str) -> bool:
        """캐시 유효성 검사"""
        if filename not in self._cache:
            return False
            
        file_path = self.config_dir / filename
        if not file_path.exists():
            return False
            
        file_mtime = file_path.stat().st_mtime
        cache_time = self._cache_timestamps.get(filename, 0)
        
        return file_mtime <= cache_time
    
    def _load_json(self, filename: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        JSON 파일 로드 (캐싱 포함)
        
        Args:
            filename: 파일명
            force_reload: 강제 재로딩 여부
        """
        # 캐시 확인
        if not force_reload and self._is_cache_valid(filename):
            logger.debug(f"캐시에서 로드: {filename}")
            return self._cache[filename]
        
        file_path = self.config_dir / filename
        
        # 기본 설정 파일이 없으면 생성
        if not file_path.exists():
            logger.info(f"기본 설정 파일 생성: {filename}")
            self._create_default_config(filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 데이터 검증
                self._validate_config(filename, data)
                
                # 캐시 업데이트
                self._cache[filename] = data
                self._cache_timestamps[filename] = datetime.now().timestamp()
                
                logger.debug(f"파일 로드 완료: {filename}")
                return data
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류 ({filename}): {str(e)}")
            st.error(f"설정 파일 형식 오류: {filename}")
            return self._get_fallback_config(filename)
            
        except Exception as e:
            logger.error(f"설정 파일 로드 오류 ({filename}): {str(e)}")
            st.error(f"설정 파일 로드 실패: {filename}")
            return self._get_fallback_config(filename)
    
    def _validate_config(self, filename: str, data: Dict[str, Any]) -> None:
        """설정 데이터 검증"""
        try:
            if filename == "users_config.json":
                self._validate_users_config(data)
            elif filename == "message_templates.json":
                self._validate_message_templates(data)
            elif filename == "app_settings.json":
                self._validate_app_settings(data)
                
        except ConfigValidationError as e:
            logger.warning(f"설정 검증 실패 ({filename}): {str(e)}")
            # 검증 실패 시 경고만 출력하고 계속 진행
    
    def _validate_users_config(self, data: Dict[str, Any]) -> None:
        """사용자 설정 검증"""
        if "users" not in data or not isinstance(data["users"], list):
            raise ConfigValidationError("users 필드가 없거나 리스트가 아닙니다")
        
        required_user_fields = ["username", "type", "description"]
        for i, user in enumerate(data["users"]):
            for field in required_user_fields:
                if field not in user:
                    raise ConfigValidationError(f"사용자 {i}: {field} 필드가 누락되었습니다")
    
    def _validate_message_templates(self, data: Dict[str, Any]) -> None:
        """메시지 템플릿 검증"""
        if "survey_questions" in data:
            if not isinstance(data["survey_questions"], list):
                raise ConfigValidationError("survey_questions는 리스트여야 합니다")
    
    def _validate_app_settings(self, data: Dict[str, Any]) -> None:
        """앱 설정 검증"""
        if "app" not in data:
            raise ConfigValidationError("app 설정이 누락되었습니다")
    
    def _get_fallback_config(self, filename: str) -> Dict[str, Any]:
        """폴백 설정 반환"""
        fallback_configs = {
            "users_config.json": {"users": [], "user_types": {}},
            "message_templates.json": {"welcome_messages": {}, "survey_questions": []},
            "app_settings.json": {"app": {"title": "KB Reflex"}, "features": []}
        }
        return fallback_configs.get(filename, {})
    
    def _create_default_config(self, filename: str) -> bool:
        """기본 설정 파일 생성"""
        try:
            default_configs = {
                "users_config.json": self._get_default_users_config(),
                "message_templates.json": self._get_default_message_templates(),
                "app_settings.json": self._get_default_app_settings(),
                "trading_data.json": self._get_default_trading_data(),
                "ui_preferences.json": self._get_default_ui_preferences()
            }
            
            if filename not in default_configs:
                logger.warning(f"알 수 없는 설정 파일: {filename}")
                return False
            
            file_path = self.config_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_configs[filename], f, ensure_ascii=False, indent=2)
            
            logger.info(f"기본 설정 파일 생성 완료: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"기본 설정 파일 생성 실패 ({filename}): {str(e)}")
            return False
    
    def _get_default_users_config(self) -> Dict[str, Any]:
        """기본 사용자 설정"""
        return {
            "users": [
                {
                    "username": "이거울",
                    "type": "신규",
                    "description": "투자를 처음 시작하는 신규 사용자",
                    "subtitle": "거래 데이터 없음 • 투자 원칙 학습 필요",
                    "icon": "🆕",
                    "color": "#3182F6",
                    "badge": "NEW",
                    "onboarding_type": "principles",
                    "has_trading_data": False,
                    "trading_count": 0,
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "preferences": {
                        "notification_enabled": True,
                        "auto_analysis": True,
                        "privacy_mode": False
                    }
                },
                {
                    "username": "박투자",
                    "type": "기존_reflex처음",
                    "description": "FOMO 매수 경향이 있는 기존 고객",
                    "subtitle": "1,500건 거래 데이터 • 추격매수 패턴 분석 필요",
                    "icon": "🔄",
                    "color": "#FF9500",
                    "badge": "ACTIVE",
                    "onboarding_type": "trade_selection",
                    "has_trading_data": True,
                    "trading_count": 1500,
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "preferences": {
                        "notification_enabled": True,
                        "auto_analysis": True,
                        "privacy_mode": False
                    }
                },
                {
                    "username": "김국민",
                    "type": "기존_reflex사용중",
                    "description": "공포 매도 경향, Reflex 기존 사용자",
                    "subtitle": "1,500건 거래 데이터 • 복기 노트 보유",
                    "icon": "⭐",
                    "color": "#14AE5C",
                    "badge": "PRO",
                    "onboarding_type": None,
                    "has_trading_data": True,
                    "trading_count": 1500,
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "preferences": {
                        "notification_enabled": True,
                        "auto_analysis": True,
                        "privacy_mode": True
                    }
                }
            ],
            "user_types": {
                "신규": {
                    "emoji": "🆕",
                    "description": "신규 사용자",
                    "color": "#3182F6",
                    "features": ["onboarding", "basic_education", "simple_interface"],
                    "limits": {"daily_trades": 10, "portfolio_size": 5}
                },
                "기존_reflex처음": {
                    "emoji": "🔄",
                    "description": "KB 기존 고객",
                    "color": "#FF9500",
                    "features": ["advanced_analysis", "pattern_detection", "risk_alerts"],
                    "limits": {"daily_trades": 50, "portfolio_size": 20}
                },
                "기존_reflex사용중": {
                    "emoji": "⭐",
                    "description": "KB Reflex 사용자",
                    "color": "#14AE5C",
                    "features": ["full_access", "custom_insights", "priority_support"],
                    "limits": {"daily_trades": 100, "portfolio_size": 50}
                }
            },
            "metadata": {
                "version": "2.0",
                "last_updated": datetime.now().isoformat(),
                "total_users": 3
            }
        }
    
    def _get_default_message_templates(self) -> Dict[str, Any]:
        """기본 메시지 템플릿"""
        return {
            "welcome_messages": {
                "이거울": {
                    "title": "🎯 투자 여정을 시작합니다!",
                    "color": "#3182F6",
                    "items": [
                        "✨ AI가 추천한 투자 철학으로 시작",
                        "🎓 체계적인 학습과 실전 연습",
                        "🪞 객관적인 자기 분석 도구 활용"
                    ],
                    "next_steps": [
                        "투자 성향 분석 설문 완료",
                        "개인 맞춤 투자 원칙 설정",
                        "모의 투자로 실전 연습"
                    ]
                },
                "박투자": {
                    "title": "🔍 FOMO 패턴 개선 중!",
                    "color": "#FF9500",
                    "items": [
                        "📊 {trading_count}건 거래 데이터 분석 완료",
                        "⚡ 추격매수 패턴 집중 개선 필요",
                        "🎯 냉정한 투자 습관 형성 목표"
                    ],
                    "next_steps": [
                        "최근 거래 패턴 분석",
                        "감정 트리거 식별",
                        "개선 전략 수립"
                    ]
                },
                "김국민": {
                    "title": "🛡️ 감정 관리 마스터링!",
                    "color": "#14AE5C",
                    "items": [
                        "📈 {trading_count}건 거래 복기 데이터 보유",
                        "🧘‍♂️ 공포 매도 극복 프로그램 진행",
                        "📜 개인화된 투자 헌장 구축"
                    ],
                    "next_steps": [
                        "심화 분석 리포트 확인",
                        "투자 헌장 업데이트",
                        "멘토링 세션 참여"
                    ]
                }
            },
            "survey_questions": [
                {
                    "id": "q1",
                    "category": "risk_preference",
                    "question": "**Q1. 투자할 때 가장 중요하게 생각하는 것은?**",
                    "description": "당신의 투자 우선순위를 알려주세요",
                    "options": [
                        {
                            "text": "📊 안정적이고 꾸준한 수익률",
                            "value": "stable",
                            "weight": 1,
                            "description": "리스크를 최소화하며 꾸준한 성장을 추구"
                        },
                        {
                            "text": "🚀 높은 성장 가능성과 기회",
                            "value": "growth",
                            "weight": 0,
                            "description": "높은 수익을 위해 적극적인 투자 추구"
                        }
                    ]
                },
                {
                    "id": "q2",
                    "category": "company_preference",
                    "question": "**Q2. 어떤 기업에 더 끌리시나요?**",
                    "description": "선호하는 기업 스타일을 선택하세요",
                    "options": [
                        {
                            "text": "🏢 오랜 역사와 안정성을 자랑하는 우량 기업",
                            "value": "stable",
                            "weight": 1,
                            "description": "검증된 비즈니스 모델과 안정성"
                        },
                        {
                            "text": "💡 혁신적이고 미래를 바꿀 새로운 기업",
                            "value": "growth",
                            "weight": 0,
                            "description": "혁신과 성장 잠재력"
                        }
                    ]
                },
                {
                    "id": "q3",
                    "category": "risk_tolerance",
                    "question": "**Q3. 투자에서 위험에 대한 당신의 철학은?**",
                    "description": "리스크 관리에 대한 접근 방식을 선택하세요",
                    "options": [
                        {
                            "text": "🛡️ 손실을 최소화하는 것이 최우선",
                            "value": "conservative",
                            "weight": 1,
                            "description": "방어적 투자로 자산 보호 우선"
                        },
                        {
                            "text": "⚡ 큰 수익을 위해서는 위험도 감수",
                            "value": "aggressive",
                            "weight": 0,
                            "description": "적극적 투자로 높은 수익 추구"
                        }
                    ]
                },
                {
                    "id": "q4",
                    "category": "investment_horizon",
                    "question": "**Q4. 투자 기간은 얼마나 생각하고 계신가요?**",
                    "description": "투자 목표 기간을 설정해주세요",
                    "options": [
                        {
                            "text": "📅 단기 (1년 이내)",
                            "value": "short_term",
                            "weight": 0,
                            "description": "빠른 수익 실현 목표"
                        },
                        {
                            "text": "🗓️ 장기 (5년 이상)",
                            "value": "long_term",
                            "weight": 1,
                            "description": "장기적 자산 증식 목표"
                        }
                    ]
                }
            ],
            "principle_recommendations": {
                "conservative": {
                    "name": "벤저민 그레이엄",
                    "style": "가치투자",
                    "description": "안전마진을 중시하는 보수적 투자",
                    "key_principles": [
                        "내재가치 대비 저평가된 기업 발굴",
                        "안전마진 확보로 손실 위험 최소화",
                        "장기적 관점의 인내심 있는 투자"
                    ]
                },
                "growth": {
                    "name": "피터 린치",
                    "style": "성장투자",
                    "description": "성장 잠재력이 높은 기업에 투자",
                    "key_principles": [
                        "이해할 수 있는 사업에만 투자",
                        "성장성과 수익성을 동시에 고려",
                        "시장 트렌드와 소비자 변화에 주목"
                    ]
                }
            },
            "notification_templates": {
                "trade_alert": "🚨 {symbol} 거래 알림: {message}",
                "pattern_detected": "🔍 패턴 감지: {pattern_type} - {description}",
                "coaching_suggestion": "💡 코칭 제안: {suggestion}"
            },
            "metadata": {
                "version": "2.0",
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _get_default_app_settings(self) -> Dict[str, Any]:
        """기본 앱 설정"""
        return {
            "app": {
                "title": "KB Reflex - AI 투자 심리 코칭",
                "icon": "🧠",
                "layout": "wide",
                "demo_password": "demo123",
                "version": "2.0",
                "environment": "production",
                "debug": False,
                "max_file_size": "10MB",
                "session_timeout": 3600
            },
            "features": [
                {
                    "id": "dashboard",
                    "name": "실시간 대시보드",
                    "icon": "📊",
                    "description": "• 실시간 포트폴리오 현황<br>• AI 투자 인사이트<br>• 스마트 거래 브리핑",
                    "background": "linear-gradient(135deg, #EBF4FF 0%, #DBEAFE 100%)",
                    "border": "#93C5FD",
                    "button_color": "#3B82F6",
                    "badge": "실시간 업데이트",
                    "page": "pages/1_Dashboard.py",
                    "enabled": True,
                    "beta": False
                },
                {
                    "id": "review",
                    "name": "거울 복기",
                    "icon": "🪞",
                    "description": "• 상황 재현 복기<br>• AI 패턴 분석<br>• 유사 경험 매칭",
                    "background": "linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)",
                    "border": "#FACC15",
                    "button_color": "#F59E0B",
                    "badge": "핵심 기능",
                    "page": "pages/2_Trade_Review.py",
                    "enabled": True,
                    "beta": False
                },
                {
                    "id": "coaching",
                    "name": "AI 심리 코칭",
                    "icon": "🤖",
                    "description": "• 딥러닝 심리 분석<br>• 개인화된 코칭<br>• 실시간 피드백",
                    "background": "linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%)",
                    "border": "#86EFAC",
                    "button_color": "#10B981",
                    "badge": "AI 엔진",
                    "page": "pages/3_AI_Coaching.py",
                    "enabled": True,
                    "beta": False
                },
                {
                    "id": "analytics",
                    "name": "고급 분석",
                    "icon": "📈",
                    "description": "• 심화 데이터 분석<br>• 예측 모델링<br>• 커스텀 리포트",
                    "background": "linear-gradient(135deg, #F3E8FF 0%, #DDD6FE 100%)",
                    "border": "#C4B5FD",
                    "button_color": "#8B5CF6",
                    "badge": "프리미엄",
                    "page": "pages/4_Analytics.py",
                    "enabled": False,
                    "beta": True
                }
            ],
            "ui_settings": {
                "theme": "light",
                "sidebar_width": 280,
                "chart_height": 400,
                "animation_duration": 300,
                "auto_refresh_interval": 30
            },
            "api_settings": {
                "timeout": 30,
                "retry_count": 3,
                "cache_ttl": 300
            },
            "metadata": {
                "version": "2.0",
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _get_default_trading_data(self) -> Dict[str, Any]:
        """기본 거래 데이터 설정"""
        return {
            "sample_trades": [
                {
                    "id": "trade_001",
                    "symbol": "삼성전자",
                    "date": "2024-08-01",
                    "type": "매수",
                    "price": 78000,
                    "quantity": 10,
                    "emotion": "냉정",
                    "confidence": 8,
                    "result": "수익",
                    "return_rate": 5.2
                },
                {
                    "id": "trade_002",
                    "symbol": "SK하이닉스",
                    "date": "2024-08-05",
                    "type": "매도",
                    "price": 145000,
                    "quantity": 5,
                    "emotion": "불안",
                    "confidence": 4,
                    "result": "손실",
                    "return_rate": -3.1
                }
            ],
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _get_default_ui_preferences(self) -> Dict[str, Any]:
        """기본 UI 선호 설정"""
        return {
            "color_scheme": "toss",
            "font_size": "medium",
            "compact_mode": False,
            "show_animations": True,
            "auto_save": True,
            "notifications": {
                "email": True,
                "push": False,
                "sound": True
            },
            "privacy": {
                "analytics": True,
                "personalization": True,
                "data_sharing": False
            },
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            }
        }
    
    # ========================================
    # Public Methods - 사용자 관련
    # ========================================
    
    def get_users(self) -> List[Dict[str, Any]]:
        """모든 사용자 정보 조회"""
        config = self._load_json("users_config.json")
        return config.get("users", [])
    
    def get_user_by_name(self, username: str) -> Optional[Dict[str, Any]]:
        """사용자명으로 사용자 정보 조회"""
        users = self.get_users()
        return next((user for user in users if user["username"] == username), None)
    
    def get_user_types(self) -> Dict[str, Any]:
        """사용자 타입 설정 조회"""
        config = self._load_json("users_config.json")
        return config.get("user_types", {})
    
    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """새 사용자 추가"""
        try:
            # 필수 필드 검증
            required_fields = ["username", "type", "description"]
            for field in required_fields:
                if field not in user_data:
                    raise ValueError(f"필수 필드 누락: {field}")
            
            # 중복 사용자 검사
            if self.get_user_by_name(user_data["username"]):
                raise ValueError(f"이미 존재하는 사용자: {user_data['username']}")
            
            # 타임스탬프 추가
            user_data["created_at"] = datetime.now().isoformat()
            user_data["last_login"] = None
            
            # 기본값 설정
            user_data.setdefault("preferences", {
                "notification_enabled": True,
                "auto_analysis": True,
                "privacy_mode": False
            })
            
            # 백업 생성
            self._backup_config("users_config.json")
            
            # 설정 업데이트
            config = self._load_json("users_config.json")
            config["users"].append(user_data)
            config["metadata"]["total_users"] = len(config["users"])
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 파일 저장
            file_path = self.config_dir / "users_config.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._cache.pop("users_config.json", None)
            
            logger.info(f"사용자 추가 완료: {user_data['username']}")
            return True
            
        except Exception as e:
            logger.error(f"사용자 추가 오류: {str(e)}")
            st.error(f"사용자 추가 실패: {str(e)}")
            return False
    
    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """사용자 정보 업데이트"""
        try:
            # 백업 생성
            self._backup_config("users_config.json")
            
            config = self._load_json("users_config.json")
            users = config["users"]
            
            for i, user in enumerate(users):
                if user["username"] == username:
                    # 업데이트할 데이터 병합
                    users[i].update(user_data)
                    users[i]["last_updated"] = datetime.now().isoformat()
                    break
            else:
                raise ValueError(f"사용자를 찾을 수 없음: {username}")
            
            # 메타데이터 업데이트
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 파일 저장
            file_path = self.config_dir / "users_config.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._cache.pop("users_config.json", None)
            
            logger.info(f"사용자 업데이트 완료: {username}")
            return True
            
        except Exception as e:
            logger.error(f"사용자 업데이트 오류: {str(e)}")
            st.error(f"사용자 업데이트 실패: {str(e)}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """사용자 삭제"""
        try:
            # 백업 생성
            self._backup_config("users_config.json")
            
            config = self._load_json("users_config.json")
            users = config["users"]
            
            original_count = len(users)
            config["users"] = [user for user in users if user["username"] != username]
            
            if len(config["users"]) == original_count:
                raise ValueError(f"삭제할 사용자를 찾을 수 없음: {username}")
            
            # 메타데이터 업데이트
            config["metadata"]["total_users"] = len(config["users"])
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 파일 저장
            file_path = self.config_dir / "users_config.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._cache.pop("users_config.json", None)
            
            logger.info(f"사용자 삭제 완료: {username}")
            return True
            
        except Exception as e:
            logger.error(f"사용자 삭제 오류: {str(e)}")
            st.error(f"사용자 삭제 실패: {str(e)}")
            return False
    
    def update_user_login(self, username: str) -> bool:
        """사용자 로그인 시간 업데이트"""
        try:
            user_data = {"last_login": datetime.now().isoformat()}
            return self.update_user(username, user_data)
        except Exception as e:
            logger.error(f"로그인 시간 업데이트 오류: {str(e)}")
            return False
    
    # ========================================
    # Public Methods - 메시지 및 템플릿
    # ========================================
    
    def get_welcome_message(self, username: str, **kwargs) -> str:
        """사용자별 환영 메시지 생성"""
        try:
            templates = self._load_json("message_templates.json")
            welcome_messages = templates.get("welcome_messages", {})
            
            if username not in welcome_messages:
                return self._get_default_welcome_message(username)
            
            message_data = welcome_messages[username]
            title = message_data.get("title", "")
            color = message_data.get("color", "#3182F6")
            items = message_data.get("items", [])
            next_steps = message_data.get("next_steps", [])
            
            # 템플릿 변수 치환
            formatted_items = []
            for item in items:
                try:
                    formatted_item = item.format(**kwargs)
                    formatted_items.append(formatted_item)
                except KeyError as e:
                    logger.warning(f"템플릿 변수 누락: {e}")
                    formatted_items.append(item)
            
            # HTML 생성
            items_html = "".join([f"<li style='margin-bottom: 0.5rem;'>{item}</li>" for item in formatted_items])
            
            next_steps_html = ""
            if next_steps:
                next_steps_items = "".join([f"<li style='margin-bottom: 0.5rem;'>{step}</li>" for step in next_steps])
                next_steps_html = f'''
                <div style="margin-top: 1.5rem;">
                    <h5 style="color: {color}; margin-bottom: 0.75rem;">다음 단계</h5>
                    <ul style="color: var(--text-secondary); line-height: 1.6; font-size: 0.9rem;">
                        {next_steps_items}
                    </ul>
                </div>
                '''
            
            return f'''
            <div style="text-align: left;">
                <h4 style="color: {color}; margin-bottom: 1rem;">{title}</h4>
                <ul style="color: var(--text-secondary); line-height: 1.6;">
                    {items_html}
                </ul>
                {next_steps_html}
            </div>
            '''
            
        except Exception as e:
            logger.error(f"환영 메시지 생성 오류: {str(e)}")
            return self._get_default_welcome_message(username)
    
    def _get_default_welcome_message(self, username: str) -> str:
        """기본 환영 메시지"""
        return f'''
        <div style="text-align: left;">
            <h4 style="color: #3182F6; margin-bottom: 1rem;">👋 환영합니다, {username}님!</h4>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                <li>KB Reflex와 함께 스마트한 투자를 시작하세요</li>
                <li>AI 기반 투자 심리 분석 서비스</li>
                <li>개인화된 투자 코칭 제공</li>
            </ul>
        </div>
        '''
    
    def get_survey_questions(self) -> List[Dict[str, Any]]:
        """설문 질문 목록 조회"""
        templates = self._load_json("message_templates.json")
        return templates.get("survey_questions", [])
    
    def get_principle_recommendation(self, score_type: str) -> Dict[str, Any]:
        """점수 타입에 따른 투자 원칙 추천"""
        templates = self._load_json("message_templates.json")
        recommendations = templates.get("principle_recommendations", {})
        
        default_recommendation = {
            "name": "피터 린치",
            "style": "성장투자",
            "description": "성장 잠재력이 높은 기업에 투자",
            "key_principles": ["이해할 수 있는 사업에만 투자"]
        }
        
        return recommendations.get(score_type, default_recommendation)
    
    def get_notification_template(self, template_type: str, **kwargs) -> str:
        """알림 템플릿 조회"""
        try:
            templates = self._load_json("message_templates.json")
            notification_templates = templates.get("notification_templates", {})
            
            if template_type not in notification_templates:
                return f"알림: {kwargs.get('message', '내용 없음')}"
            
            template = notification_templates[template_type]
            return template.format(**kwargs)
            
        except Exception as e:
            logger.error(f"알림 템플릿 조회 오류: {str(e)}")
            return f"알림: {kwargs.get('message', '내용 없음')}"
    
    # ========================================
    # Public Methods - 앱 설정
    # ========================================
    
    def get_app_settings(self) -> Dict[str, Any]:
        """앱 설정 조회"""
        return self._load_json("app_settings.json")
    
    def get_features(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """기능 목록 조회"""
        settings = self.get_app_settings()
        features = settings.get("features", [])
        
        if enabled_only:
            features = [f for f in features if f.get("enabled", True)]
        
        return features
    
    def get_feature_by_id(self, feature_id: str) -> Optional[Dict[str, Any]]:
        """ID로 기능 조회"""
        features = self.get_features()
        return next((f for f in features if f["id"] == feature_id), None)
    
    def update_app_settings(self, settings_data: Dict[str, Any]) -> bool:
        """앱 설정 업데이트"""
        try:
            # 백업 생성
            self._backup_config("app_settings.json")
            
            config = self.get_app_settings()
            config.update(settings_data)
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 파일 저장
            file_path = self.config_dir / "app_settings.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._cache.pop("app_settings.json", None)
            
            logger.info("앱 설정 업데이트 완료")
            return True
            
        except Exception as e:
            logger.error(f"앱 설정 업데이트 오류: {str(e)}")
            return False
    
    # ========================================
    # Public Methods - 거래 데이터
    # ========================================
    
    def get_trading_data(self) -> Dict[str, Any]:
        """거래 데이터 조회"""
        return self._load_json("trading_data.json")
    
    def add_trade_record(self, trade_data: Dict[str, Any]) -> bool:
        """거래 기록 추가"""
        try:
            # 필수 필드 검증
            required_fields = ["symbol", "date", "type", "price", "quantity"]
            for field in required_fields:
                if field not in trade_data:
                    raise ValueError(f"필수 필드 누락: {field}")
            
            # ID 자동 생성
            if "id" not in trade_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                trade_data["id"] = f"trade_{timestamp}"
            
            # 타임스탬프 추가
            trade_data["created_at"] = datetime.now().isoformat()
            
            # 백업 생성
            self._backup_config("trading_data.json")
            
            # 데이터 업데이트
            config = self.get_trading_data()
            if "sample_trades" not in config:
                config["sample_trades"] = []
            
            config["sample_trades"].append(trade_data)
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 파일 저장
            file_path = self.config_dir / "trading_data.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._cache.pop("trading_data.json", None)
            
            logger.info(f"거래 기록 추가 완료: {trade_data['id']}")
            return True
            
        except Exception as e:
            logger.error(f"거래 기록 추가 오류: {str(e)}")
            return False
    
    # ========================================
    # Public Methods - UI 선호 설정
    # ========================================
    
    def get_ui_preferences(self) -> Dict[str, Any]:
        """UI 선호 설정 조회"""
        return self._load_json("ui_preferences.json")
    
    def update_ui_preferences(self, preferences_data: Dict[str, Any]) -> bool:
        """UI 선호 설정 업데이트"""
        try:
            config = self.get_ui_preferences()
            config.update(preferences_data)
            config["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 파일 저장
            file_path = self.config_dir / "ui_preferences.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._cache.pop("ui_preferences.json", None)
            
            logger.info("UI 선호 설정 업데이트 완료")
            return True
            
        except Exception as e:
            logger.error(f"UI 선호 설정 업데이트 오류: {str(e)}")
            return False
    
    # ========================================
    # Public Methods - 유틸리티
    # ========================================
    
    def reload_cache(self, filename: Optional[str] = None):
        """캐시 새로고침"""
        if filename:
            self._cache.pop(filename, None)
            self._cache_timestamps.pop(filename, None)
            logger.info(f"캐시 새로고침: {filename}")
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("전체 캐시 새로고침")
    
    def get_config_status(self) -> Dict[str, Any]:
        """설정 파일 상태 조회"""
        config_files = [
            "users_config.json",
            "message_templates.json", 
            "app_settings.json",
            "trading_data.json",
            "ui_preferences.json"
        ]
        
        status = {
            "config_dir": str(self.config_dir),
            "backup_enabled": self.enable_backup,
            "files": {}
        }
        
        for filename in config_files:
            file_path = self.config_dir / filename
            status["files"][filename] = {
                "exists": file_path.exists(),
                "size": file_path.stat().st_size if file_path.exists() else 0,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if file_path.exists() else None,
                "cached": filename in self._cache
            }
        
        return status
    
    def export_config(self, export_path: Optional[str] = None) -> str:
        """설정 내보내기"""
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = self.config_dir / f"config_export_{timestamp}.json"
            else:
                export_path = Path(export_path)
            
            # 모든 설정 수집
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0"
                },
                "users_config": self._load_json("users_config.json"),
                "message_templates": self._load_json("message_templates.json"),
                "app_settings": self._load_json("app_settings.json"),
                "trading_data": self._load_json("trading_data.json"),
                "ui_preferences": self._load_json("ui_preferences.json")
            }
            
            # 내보내기 파일 저장
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"설정 내보내기 완료: {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"설정 내보내기 오류: {str(e)}")
            raise
    
    def import_config(self, import_path: str, merge: bool = True) -> bool:
        """설정 가져오기"""
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없음: {import_path}")
            
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 버전 확인
            if "export_info" not in import_data:
                logger.warning("내보내기 정보가 없는 파일")
            
            # 백업 생성
            if self.enable_backup:
                for config_file in ["users_config.json", "message_templates.json", "app_settings.json"]:
                    self._backup_config(config_file)
            
            # 설정 복원
            config_mappings = {
                "users_config": "users_config.json",
                "message_templates": "message_templates.json",
                "app_settings": "app_settings.json",
                "trading_data": "trading_data.json",
                "ui_preferences": "ui_preferences.json"
            }
            
            for key, filename in config_mappings.items():
                if key in import_data:
                    if merge and filename in ["users_config.json"]:
                        # 사용자 데이터는 병합
                        current_config = self._load_json(filename)
                        import_config = import_data[key]
                        
                        # 사용자 병합 로직
                        if "users" in import_config:
                            existing_usernames = {user["username"] for user in current_config.get("users", [])}
                            for user in import_config["users"]:
                                if user["username"] not in existing_usernames:
                                    current_config.setdefault("users", []).append(user)
                        
                        # 파일 저장
                        file_path = self.config_dir / filename
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(current_config, f, ensure_ascii=False, indent=2)
                    else:
                        # 전체 교체
                        file_path = self.config_dir / filename
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(import_data[key], f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self.reload_cache()
            
            logger.info(f"설정 가져오기 완료: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"설정 가져오기 오류: {str(e)}")
            st.error(f"설정 가져오기 실패: {str(e)}")
            return False
    
    def reset_config(self, config_type: Optional[str] = None) -> bool:
        """설정 초기화"""
        try:
            if config_type:
                # 특정 설정만 초기화
                if self.enable_backup:
                    self._backup_config(config_type)
                
                self._create_default_config(config_type)
                self.reload_cache(config_type)
                
                logger.info(f"설정 초기화 완료: {config_type}")
            else:
                # 전체 설정 초기화
                config_files = ["users_config.json", "message_templates.json", "app_settings.json"]
                
                for filename in config_files:
                    if self.enable_backup:
                        self._backup_config(filename)
                    self._create_default_config(filename)
                
                self.reload_cache()
                logger.info("전체 설정 초기화 완료")
            
            return True
            
        except Exception as e:
            logger.error(f"설정 초기화 오류: {str(e)}")
            return False
    
    def get_version_info(self) -> Dict[str, str]:
        """버전 정보 조회"""
        return {
            "config_loader_version": "2.0",
            "last_updated": "2024-08-10",
            "python_version": str(sys.version_info[:3]) if 'sys' in globals() else "unknown",
            "config_dir": str(self.config_dir)
        }


# ========================================
# 유틸리티 함수들
# ========================================

def validate_json_file(file_path: Union[str, Path]) -> bool:
    """JSON 파일 유효성 검사"""
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
        
    except (json.JSONDecodeError, Exception):
        return False

def merge_configs(base_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
    """설정 딕셔너리 병합"""
    merged = base_config.copy()
    
    for key, value in new_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged

def sanitize_filename(filename: str) -> str:
    """파일명 정제"""
    import re
    # 위험한 문자 제거
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 연속된 언더스코어 제거
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')


# ========================================
# 전역 인스턴스
# ========================================

# 전역 설정 로더 인스턴스
config_loader = ConfigLoader()

# 초기화 확인
if __name__ == "__main__":
    print("ConfigLoader V2.0 - 테스트 모드")
    print(f"설정 디렉토리: {config_loader.config_dir}")
    print(f"백업 기능: {'활성화' if config_loader.enable_backup else '비활성화'}")
    
    # 기본 테스트
    try:
        users = config_loader.get_users()
        print(f"등록된 사용자 수: {len(users)}")
        
        features = config_loader.get_features()
        print(f"사용 가능한 기능 수: {len(features)}")
        
        status = config_loader.get_config_status()
        print("설정 파일 상태:")
        for filename, info in status["files"].items():
            print(f"  {filename}: {'✅' if info['exists'] else '❌'}")
        
    except Exception as e:
        print(f"테스트 실행 중 오류: {e}")

# 시스템 임포트 (버전 정보용)
import sys