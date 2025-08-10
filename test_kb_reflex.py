#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 통합 테스트 및 검증 스크립트
KB AI CHALLENGE 2024

프로젝트의 모든 기능이 정상 작동하는지 검증합니다.
"""

import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class TestLogger:
    """테스트 로거"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []
    
    def test_passed(self, test_name: str):
        """테스트 통과"""
        print(f"✅ {test_name}")
        self.tests_passed += 1
    
    def test_failed(self, test_name: str, error: str):
        """테스트 실패"""
        print(f"❌ {test_name}: {error}")
        self.tests_failed += 1
        self.errors.append(f"{test_name}: {error}")
    
    def summary(self):
        """테스트 요약"""
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        print(f"총 테스트: {total}개")
        print(f"통과: {self.tests_passed}개")
        print(f"실패: {self.tests_failed}개")
        print(f"성공률: {success_rate:.1f}%")
        
        if self.errors:
            print("\n❌ 실패한 테스트들:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.tests_failed == 0

class KBReflexTester:
    """KB Reflex 통합 테스터"""
    
    def __init__(self):
        self.logger = TestLogger()
        self.project_root = Path.cwd()
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 KB Reflex 통합 테스트를 시작합니다...")
        print("=" * 50)
        
        # 1. 프로젝트 구조 테스트
        self.test_project_structure()
        
        # 2. 설정 파일 테스트
        self.test_config_files()
        
        # 3. 핵심 모듈 테스트
        self.test_core_modules()
        
        # 4. UI 컴포넌트 테스트
        self.test_ui_components()
        
        # 5. 데이터 엔진 테스트
        self.test_data_engine()
        
        # 6. AI 코칭 엔진 테스트
        self.test_ai_coach()
        
        # 7. 메인 앱 임포트 테스트
        self.test_main_app_import()
        
        # 결과 요약
        return self.logger.summary()
    
    def test_project_structure(self):
        """프로젝트 구조 테스트"""
        print("\n📁 프로젝트 구조 검증 중...")
        
        required_files = [
            "main_app.py",
            "core/data_engine.py",
            "core/ai_coach.py",
            "components/kb_style.py",
            "components/widgets.py"
        ]
        
        required_dirs = [
            "config",
            "core",
            "components"
        ]
        
        # 필수 파일 확인
        for file_path in required_files:
            if (self.project_root / file_path).exists():
                self.logger.test_passed(f"필수 파일 존재: {file_path}")
            else:
                self.logger.test_failed(f"필수 파일 누락: {file_path}", "파일이 존재하지 않음")
        
        # 필수 디렉토리 확인
        for dir_path in required_dirs:
            if (self.project_root / dir_path).is_dir():
                self.logger.test_passed(f"필수 디렉토리 존재: {dir_path}/")
            else:
                self.logger.test_failed(f"필수 디렉토리 누락: {dir_path}/", "디렉토리가 존재하지 않음")
    
    def test_config_files(self):
        """설정 파일 테스트"""
        print("\n⚙️ 설정 파일 검증 중...")
        
        required_configs = [
            "ui_colors.json",
            "ui_settings.json", 
            "ai_coaching.json",
            "investment_principles.json"
        ]
        
        config_dir = self.project_root / "config"
        
        if not config_dir.exists():
            self.logger.test_failed("설정 디렉토리", "config/ 디렉토리가 존재하지 않음")
            return
        
        for config_file in required_configs:
            config_path = config_dir / config_file
            
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    if config_data:
                        self.logger.test_passed(f"설정 파일 유효: {config_file}")
                    else:
                        self.logger.test_failed(f"설정 파일 비어있음: {config_file}", "데이터가 없음")
                
                except json.JSONDecodeError as e:
                    self.logger.test_failed(f"설정 파일 JSON 오류: {config_file}", str(e))
                except Exception as e:
                    self.logger.test_failed(f"설정 파일 읽기 실패: {config_file}", str(e))
            else:
                self.logger.test_failed(f"설정 파일 누락: {config_file}", "파일이 존재하지 않음")
    
    def test_core_modules(self):
        """핵심 모듈 테스트"""
        print("\n🧠 핵심 모듈 검증 중...")
        
        # 데이터 엔진 임포트 테스트
        try:
            sys.path.append(str(self.project_root))
            from core.data_engine import get_dynamic_data_engine, CompleteDynamicDataEngine
            self.logger.test_passed("데이터 엔진 임포트")
            
            # 데이터 엔진 인스턴스 생성 테스트
            try:
                engine = CompleteDynamicDataEngine()
                self.logger.test_passed("데이터 엔진 인스턴스 생성")
                
                # 기본 기능 테스트
                users = engine.get_users()
                if users and len(users) > 0:
                    self.logger.test_passed("사용자 데이터 생성")
                else:
                    self.logger.test_failed("사용자 데이터 생성", "사용자 데이터가 없음")
                
                market_data = engine.get_market_data()
                if market_data and len(market_data) > 0:
                    self.logger.test_passed("시장 데이터 생성")
                else:
                    self.logger.test_failed("시장 데이터 생성", "시장 데이터가 없음")
                
            except Exception as e:
                self.logger.test_failed("데이터 엔진 기능", str(e))
        
        except ImportError as e:
            self.logger.test_failed("데이터 엔진 임포트", str(e))
        
        # AI 코칭 엔진 임포트 테스트
        try:
            from core.ai_coach import ConfigurableAICoach, CoachingResult
            self.logger.test_passed("AI 코칭 엔진 임포트")
            
            # AI 코칭 엔진 인스턴스 생성 테스트
            try:
                coach = ConfigurableAICoach()
                self.logger.test_passed("AI 코칭 엔진 인스턴스 생성")
            except Exception as e:
                self.logger.test_failed("AI 코칭 엔진 기능", str(e))
        
        except ImportError as e:
            self.logger.test_failed("AI 코칭 엔진 임포트", str(e))
    
    def test_ui_components(self):
        """UI 컴포넌트 테스트"""
        print("\n🎨 UI 컴포넌트 검증 중...")
        
        # KB 스타일 임포트 테스트
        try:
            from components.kb_style import (
                KBColors, apply_kb_theme, kb_header, 
                kb_metric_card, kb_news_card, kb_investment_status_card
            )
            self.logger.test_passed("KB 스타일 컴포넌트 임포트")
            
            # 컬러 시스템 테스트
            try:
                colors = KBColors()
                if hasattr(colors, 'YELLOW') and colors.YELLOW:
                    self.logger.test_passed("KB 컬러 시스템 초기화")
                else:
                    self.logger.test_failed("KB 컬러 시스템", "컬러 설정이 로드되지 않음")
            except Exception as e:
                self.logger.test_failed("KB 컬러 시스템", str(e))
        
        except ImportError as e:
            self.logger.test_failed("KB 스타일 컴포넌트 임포트", str(e))
        
        # 위젯 임포트 테스트
        try:
            from components.widgets import (
                render_performance_overview,
                render_emotion_analysis_chart,
                render_trade_history_table
            )
            self.logger.test_passed("위젯 컴포넌트 임포트")
        
        except ImportError as e:
            self.logger.test_failed("위젯 컴포넌트 임포트", str(e))
    
    def test_data_engine(self):
        """데이터 엔진 기능 테스트"""
        print("\n📊 데이터 엔진 기능 검증 중...")
        
        try:
            from core.data_engine import get_dynamic_data_engine
            
            engine = get_dynamic_data_engine()
            
            # 사용자 관련 기능
            users = engine.get_users()
            if users:
                user_id = list(users.keys())[0]
                
                # 사용자 정보 조회
                user_info = engine.get_user(user_id)
                if user_info:
                    self.logger.test_passed("사용자 정보 조회")
                else:
                    self.logger.test_failed("사용자 정보 조회", "사용자 정보를 찾을 수 없음")
                
                # 거래 내역 조회
                trades = engine.get_user_trades(user_id)
                self.logger.test_passed(f"거래 내역 조회 ({len(trades)}건)")
                
                # 통계 생성 (새로 추가된 메서드)
                try:
                    stats = engine.get_user_statistics(user_id)
                    if stats and "basic_stats" in stats:
                        self.logger.test_passed("사용자 통계 생성")
                    else:
                        self.logger.test_failed("사용자 통계 생성", "통계 데이터가 올바르지 않음")
                except AttributeError:
                    self.logger.test_failed("사용자 통계 생성", "get_user_statistics 메서드가 없음")
            
            # 시장 데이터
            market_data = engine.get_market_data(refresh=True)
            if market_data:
                self.logger.test_passed("시장 데이터 갱신")
            else:
                self.logger.test_failed("시장 데이터 갱신", "시장 데이터가 없음")
            
            # 뉴스 데이터
            news = engine.get_news(refresh=True)
            if news:
                self.logger.test_passed("뉴스 데이터 생성")
            else:
                self.logger.test_failed("뉴스 데이터 생성", "뉴스 데이터가 없음")
            
            # 시스템 상태
            status = engine.get_system_status()
            if status and "engine_type" in status:
                self.logger.test_passed("시스템 상태 조회")
            else:
                self.logger.test_failed("시스템 상태 조회", "상태 정보가 올바르지 않음")
        
        except Exception as e:
            self.logger.test_failed("데이터 엔진 기능 테스트", str(e))
    
    def test_ai_coach(self):
        """AI 코칭 엔진 기능 테스트"""
        print("\n🤖 AI 코칭 엔진 기능 검증 중...")
        
        try:
            from core.ai_coach import ConfigurableAICoach
            from core.data_engine import get_dynamic_data_engine
            
            coach = ConfigurableAICoach()
            data_engine = get_dynamic_data_engine()
            
            # 테스트 데이터 준비
            test_input = "삼성전자가 5% 떨어졌는데 FOMO가 심해서 추가 매수할까 고민됩니다."
            users = data_engine.get_users()
            
            if users:
                user_id = list(users.keys())[0]
                user_data = data_engine.get_user(user_id)
                user_trades = data_engine.get_user_trades(user_id)
                market_data = data_engine.get_market_data()
                news_data = data_engine.get_news()
                
                # AI 분석 실행
                try:
                    result = coach.analyze_investment_situation(
                        test_input, user_data, user_trades, market_data, news_data
                    )
                    
                    if hasattr(result, 'analysis') and result.analysis:
                        self.logger.test_passed("AI 상황 분석")
                    else:
                        self.logger.test_failed("AI 상황 분석", "분석 결과가 올바르지 않음")
                    
                    if hasattr(result, 'risk_level') and result.risk_level:
                        self.logger.test_passed("위험도 평가")
                    else:
                        self.logger.test_failed("위험도 평가", "위험도 평가 결과가 없음")
                    
                    if hasattr(result, 'confidence') and 0 <= result.confidence <= 1:
                        self.logger.test_passed("신뢰도 계산")
                    else:
                        self.logger.test_failed("신뢰도 계산", "신뢰도 값이 올바르지 않음")
                
                except Exception as e:
                    self.logger.test_failed("AI 코칭 분석", str(e))
                
                # 투자 원칙 제안 테스트
                try:
                    principles = coach.suggest_personalized_principles(user_data, user_trades)
                    
                    if principles and "personalized_principles" in principles:
                        self.logger.test_passed("투자 원칙 제안")
                    else:
                        self.logger.test_failed("투자 원칙 제안", "원칙 제안 결과가 올바르지 않음")
                
                except Exception as e:
                    self.logger.test_failed("투자 원칙 제안", str(e))
        
        except Exception as e:
            self.logger.test_failed("AI 코칭 엔진 초기화", str(e))
    
    def test_main_app_import(self):
        """메인 앱 임포트 테스트"""
        print("\n🚀 메인 앱 임포트 검증 중...")
        
        try:
            # Streamlit 없이도 메인 모듈이 임포트되는지 확인
            import importlib.util
            
            spec = importlib.util.spec_from_file_location("main_app", "main_app.py")
            if spec is None:
                self.logger.test_failed("메인 앱 스펙", "main_app.py 스펙을 로드할 수 없음")
                return
            
            self.logger.test_passed("메인 앱 파일 검증")
            
            # 주요 함수들이 정의되어 있는지 확인 (문자열 검색)
            with open("main_app.py", 'r', encoding='utf-8') as f:
                content = f.read()
                
                required_functions = [
                    "def main():",
                    "def show_user_selector():",
                    "def show_main_demo():",
                    "def analyze_user_situation_enhanced("
                ]
                
                for func in required_functions:
                    if func in content:
                        self.logger.test_passed(f"필수 함수 정의: {func.split('(')[0].replace('def ', '')}")
                    else:
                        self.logger.test_failed(f"함수 누락: {func.split('(')[0].replace('def ', '')}", "함수가 정의되지 않음")
        
        except Exception as e:
            self.logger.test_failed("메인 앱 검증", str(e))

def create_test_report(test_success: bool, errors: List[str]):
    """테스트 리포트 생성"""
    
    report = {
        "test_time": datetime.now().isoformat(),
        "test_success": test_success,
        "errors": errors,
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform
        }
    }
    
    report_path = Path("test_report.json")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 테스트 리포트가 저장되었습니다: {report_path}")

def main():
    """메인 테스트 실행"""
    print("🏛️ KB Reflex - 통합 테스트 시스템")
    print(f"⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = KBReflexTester()
    
    try:
        success = tester.run_all_tests()
        
        # 테스트 리포트 생성
        create_test_report(success, tester.logger.errors)
        
        if success:
            print("\n🎉 모든 테스트가 성공했습니다!")
            print("KB Reflex가 정상적으로 설정되었습니다.")
            print("\n다음 단계:")
            print("1. streamlit run main_app.py")
            print("2. 브라우저에서 http://localhost:8501 접속")
        else:
            print("\n⚠️ 일부 테스트가 실패했습니다.")
            print("실패한 항목들을 확인하고 수정해주세요.")
            
            # 실행 가능 여부 판단
            critical_failures = [
                error for error in tester.logger.errors 
                if any(critical in error.lower() for critical in ["임포트", "파일 누락", "디렉토리 누락"])
            ]
            
            if not critical_failures:
                print("\n💡 중요한 오류는 없으므로 앱 실행은 가능할 것 같습니다.")
        
        return success
    
    except KeyboardInterrupt:
        print("\n❌ 테스트가 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 예외 발생: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)