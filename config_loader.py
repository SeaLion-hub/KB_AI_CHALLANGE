import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import streamlit as st

class ConfigLoader:
    """설정 및 데이터 자동 로딩 클래스"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(__file__).parent.parent / config_dir
        self.config_dir.mkdir(exist_ok=True)
        self._cache = {}
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """JSON 파일 로드 (캐싱 포함)"""
        if filename in self._cache:
            return self._cache[filename]
        
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            # 기본 설정 파일이 없으면 생성
            self._create_default_config(filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[filename] = data
                return data
        except Exception as e:
            st.error(f"설정 파일 로드 오류 ({filename}): {str(e)}")
            return {}
    
    def _create_default_config(self, filename: str):
        """기본 설정 파일 생성"""
        default_configs = {
            "users_config.json": self._get_default_users_config(),
            "message_templates.json": self._get_default_message_templates(),
            "app_settings.json": self._get_default_app_settings()
        }
        
        if filename in default_configs:
            file_path = self.config_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_configs[filename], f, ensure_ascii=False, indent=2)
    
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
                    "trading_count": 0
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
                    "trading_count": 1500
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
                    "trading_count": 1500
                }
            ],
            "user_types": {
                "신규": {
                    "emoji": "🆕",
                    "description": "신규 사용자",
                    "color": "#3182F6"
                },
                "기존_reflex처음": {
                    "emoji": "🔄",
                    "description": "KB 기존 고객",
                    "color": "#FF9500"
                },
                "기존_reflex사용중": {
                    "emoji": "⭐",
                    "description": "KB Reflex 사용자",
                    "color": "#14AE5C"
                }
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
                    ]
                },
                "박투자": {
                    "title": "🔍 FOMO 패턴 개선 중!",
                    "color": "#FF9500",
                    "items": [
                        "📊 {trading_count}건 거래 데이터 분석 완료",
                        "⚡ 추격매수 패턴 집중 개선 필요",
                        "🎯 냉정한 투자 습관 형성 목표"
                    ]
                },
                "김국민": {
                    "title": "🛡️ 감정 관리 마스터링!",
                    "color": "#14AE5C",
                    "items": [
                        "📈 {trading_count}건 거래 복기 데이터 보유",
                        "🧘‍♂️ 공포 매도 극복 프로그램 진행",
                        "📜 개인화된 투자 헌장 구축"
                    ]
                }
            },
            "survey_questions": [
                {
                    "id": "q1",
                    "question": "**Q1. 투자할 때 가장 중요하게 생각하는 것은?**",
                    "options": [
                        {
                            "text": "📊 안정적이고 꾸준한 수익률",
                            "value": "stable",
                            "weight": 1
                        },
                        {
                            "text": "🚀 높은 성장 가능성과 기회",
                            "value": "growth",
                            "weight": 0
                        }
                    ]
                },
                {
                    "id": "q2",
                    "question": "**Q2. 어떤 기업에 더 끌리시나요?**",
                    "options": [
                        {
                            "text": "🏢 오랜 역사와 안정성을 자랑하는 우량 기업",
                            "value": "stable",
                            "weight": 1
                        },
                        {
                            "text": "💡 혁신적이고 미래를 바꿀 새로운 기업",
                            "value": "growth",
                            "weight": 0
                        }
                    ]
                },
                {
                    "id": "q3",
                    "question": "**Q3. 투자에서 위험에 대한 당신의 철학은?**",
                    "options": [
                        {
                            "text": "🛡️ 손실을 최소화하는 것이 최우선",
                            "value": "conservative",
                            "weight": 1
                        },
                        {
                            "text": "⚡ 큰 수익을 위해서는 위험도 감수",
                            "value": "aggressive",
                            "weight": 0
                        }
                    ]
                }
            ],
            "principle_recommendations": {
                "conservative": "벤저민 그레이엄",
                "growth": "피터 린치"
            }
        }
    
    def _get_default_app_settings(self) -> Dict[str, Any]:
        """기본 앱 설정"""
        return {
            "app": {
                "title": "KB Reflex - AI 투자 심리 코칭",
                "icon": "🧠",
                "layout": "wide",
                "demo_password": "demo123"
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
                    "page": "pages/1_Dashboard.py"
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
                    "page": "pages/2_Trade_Review.py"
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
                    "page": "pages/3_AI_Coaching.py"
                }
            ]
        }
    
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
    
    def get_welcome_message(self, username: str, **kwargs) -> str:
        """사용자별 환영 메시지 생성"""
        templates = self._load_json("message_templates.json")
        welcome_messages = templates.get("welcome_messages", {})
        
        if username not in welcome_messages:
            return ""
        
        message_data = welcome_messages[username]
        title = message_data.get("title", "")
        color = message_data.get("color", "#3182F6")
        items = message_data.get("items", [])
        
        # 템플릿 변수 치환
        formatted_items = []
        for item in items:
            formatted_item = item.format(**kwargs)
            formatted_items.append(formatted_item)
        
        # HTML 생성
        items_html = "".join([f"<li>{item}</li>" for item in formatted_items])
        
        return f'''
        <div style="text-align: left;">
            <h4 style="color: {color}; margin-bottom: 1rem;">{title}</h4>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                {items_html}
            </ul>
        </div>
        '''
    
    def get_survey_questions(self) -> List[Dict[str, Any]]:
        """설문 질문 목록 조회"""
        templates = self._load_json("message_templates.json")
        return templates.get("survey_questions", [])
    
    def get_principle_recommendation(self, score_type: str) -> str:
        """점수 타입에 따른 투자 원칙 추천"""
        templates = self._load_json("message_templates.json")
        recommendations = templates.get("principle_recommendations", {})
        return recommendations.get(score_type, "피터 린치")
    
    def get_app_settings(self) -> Dict[str, Any]:
        """앱 설정 조회"""
        return self._load_json("app_settings.json")
    
    def get_features(self) -> List[Dict[str, Any]]:
        """기능 목록 조회"""
        settings = self.get_app_settings()
        return settings.get("features", [])
    
    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """새 사용자 추가"""
        try:
            config = self._load_json("users_config.json")
            config["users"].append(user_data)
            
            file_path = self.config_dir / "users_config.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._cache.pop("users_config.json", None)
            return True
        except Exception as e:
            st.error(f"사용자 추가 오류: {str(e)}")
            return False
    
    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """사용자 정보 업데이트"""
        try:
            config = self._load_json("users_config.json")
            users = config["users"]
            
            for i, user in enumerate(users):
                if user["username"] == username:
                    users[i].update(user_data)
                    break
            else:
                return False  # 사용자를 찾지 못함
            
            file_path = self.config_dir / "users_config.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._cache.pop("users_config.json", None)
            return True
        except Exception as e:
            st.error(f"사용자 업데이트 오류: {str(e)}")
            return False
    
    def reload_cache(self):
        """캐시 새로고침"""
        self._cache.clear()


# 전역 인스턴스
config_loader = ConfigLoader()
