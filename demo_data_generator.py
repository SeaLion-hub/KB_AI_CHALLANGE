#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 데모 데이터 생성기 및 CLI 도구
KB AI CHALLENGE 2024

공모전 시연을 위한 최적화된 데모 데이터를 생성합니다.
"""

import json
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import sys

class DemoDataGenerator:
    """공모전 시연용 데모 데이터 생성기"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
    
    def generate_realistic_demo_scenarios(self):
        """현실적인 데모 시나리오 생성"""
        
        scenarios = {
            "김투자_FOMO_시나리오": {
                "user_type": "fomo_trader",
                "scenario_description": "FOMO 매수 후 후회하는 감정적 투자자",
                "recent_trades": [
                    {
                        "date": "2024-08-05",
                        "stock": "삼성전자",
                        "action": "매수",
                        "amount": 2000000,
                        "price": 68000,
                        "reason": "AI 반도체 급등 소식 듣고 FOMO 매수",
                        "emotion": "욕심",
                        "confidence": 0.9,
                        "result": -8.2,
                        "memo": "뉴스 보고 급하게 샀는데 바로 떨어짐. 역시 FOMO는 금물..."
                    },
                    {
                        "date": "2024-07-28",
                        "stock": "SK하이닉스",
                        "action": "매수", 
                        "amount": 1500000,
                        "price": 125000,
                        "reason": "메모리 반도체 사이클 회복 기대",
                        "emotion": "확신",
                        "confidence": 0.8,
                        "result": 12.5,
                        "memo": "차트 분석하고 신중하게 매수. 좋은 결과!"
                    },
                    {
                        "date": "2024-07-15",
                        "stock": "카카오",
                        "action": "매도",
                        "amount": 800000,
                        "price": 45000,
                        "reason": "규제 이슈로 불안해서 급매도",
                        "emotion": "불안",
                        "confidence": 0.3,
                        "result": -15.3,
                        "memo": "패닉셀... 나중에 다시 올랐는데 너무 아쉬워"
                    }
                ],
                "test_inputs": [
                    "삼성전자가 또 5% 떨어졌는데 FOMO가 심해서 추가 매수할까요?",
                    "SK하이닉스 급등하고 있어서 빨리 사야할 것 같은데 어떻게 생각하세요?",
                    "카카오 또 규제 뉴스 나왔는데 보유 중인 걸 팔아야 할까요?"
                ]
            },
            
            "박복기_체계적_시나리오": {
                "user_type": "systematic_trader",
                "scenario_description": "분석적이고 체계적인 투자자",
                "recent_trades": [
                    {
                        "date": "2024-08-01",
                        "stock": "NAVER",
                        "action": "매수",
                        "amount": 3000000,
                        "price": 180000,
                        "reason": "기술적 분석 결과 지지선에서 반등 신호 확인",
                        "emotion": "냉정",
                        "confidence": 0.7,
                        "result": 8.9,
                        "memo": "차트 패턴 분석하고 손절선 설정 후 매수. 계획대로 진행"
                    },
                    {
                        "date": "2024-07-20",
                        "stock": "LG화학",
                        "action": "매수",
                        "amount": 2500000,
                        "price": 380000,
                        "reason": "2차전지 업황 회복 + 밸류에이션 매력",
                        "emotion": "확신",
                        "confidence": 0.8,
                        "result": 6.3,
                        "memo": "펀더멘털 분석 후 중장기 관점에서 매수"
                    },
                    {
                        "date": "2024-07-10",
                        "stock": "현대차",
                        "action": "매도",
                        "amount": 1800000,
                        "price": 185000,
                        "reason": "목표가 도달로 부분 매도",
                        "emotion": "만족",
                        "confidence": 0.9,
                        "result": 15.7,
                        "memo": "계획된 수익률 달성. 원칙 지킨 결과"
                    }
                ],
                "test_inputs": [
                    "NAVER 차트 분석 결과 매수 신호가 나왔는데 어떻게 보시나요?",
                    "LG화학 실적 발표 앞두고 있는데 분석적 관점에서 조언 부탁드립니다.",
                    "현재 포트폴리오가 IT 비중이 높은데 리밸런싱이 필요할까요?"
                ]
            },
            
            "이신규_초보_시나리오": {
                "user_type": "beginner",
                "scenario_description": "투자 초보자",
                "recent_trades": [],
                "test_inputs": [
                    "처음 투자하는데 어떤 주식을 사야 할까요?",
                    "친구가 삼성전자 사라고 하는데 괜찮을까요?",
                    "100만원으로 시작하려는데 어떻게 분산투자 해야 하나요?",
                    "투자 공부는 어떻게 해야 하나요?"
                ]
            }
        }
        
        return scenarios
    
    def generate_realistic_news_data(self):
        """현실적인 뉴스 데이터 생성"""
        
        news_templates = [
            {
                "title": "삼성전자, 차세대 AI 반도체 'GPU-X' 개발 성공",
                "content": "삼성전자가 글로벌 AI 시장 공략을 위한 차세대 GPU 'GPU-X'를 성공적으로 개발했다고 발표했다. 이번 GPU는 기존 대비 성능이 40% 향상되었으며, 전력 효율성도 크게 개선되었다.",
                "time": "2시간 전",
                "impact": "positive",
                "importance": 0.9,
                "related_stocks": ["삼성전자"],
                "source": "KB리서치센터"
            },
            {
                "title": "SK하이닉스, HBM4 양산 계획 발표... 글로벌 AI 메모리 시장 선도",
                "content": "SK하이닉스가 2025년 하반기 HBM4 양산을 목표로 한다고 발표했다. 이는 경쟁사 대비 6개월 앞선 것으로, AI 메모리 시장에서의 선도적 지위를 더욱 공고히 할 것으로 전망된다.",
                "time": "4시간 전", 
                "impact": "positive",
                "importance": 0.8,
                "related_stocks": ["SK하이닉스"],
                "source": "KB증권"
            },
            {
                "title": "카카오, 개인정보보호 강화 정책 발표... 규제 리스크 해소 기대",
                "content": "카카오가 개인정보 보호 강화를 위한 종합 정책을 발표했다. 이번 정책은 최근 제기된 개인정보 관련 우려를 해소하고, 규제 당국과의 협력을 강화하는 내용을 담고 있다.",
                "time": "6시간 전",
                "impact": "positive", 
                "importance": 0.7,
                "related_stocks": ["카카오"],
                "source": "KB리서치센터"
            },
            {
                "title": "NAVER, 클라우드 사업 확장... 하이퍼스케일 데이터센터 신설",
                "content": "NAVER가 클라우드 사업 확장의 일환으로 춘천에 대규모 하이퍼스케일 데이터센터 신설 계획을 발표했다. 2026년 완공 예정인 이 데이터센터는 NAVER 클라우드 플랫폼의 경쟁력을 크게 향상시킬 전망이다.",
                "time": "1일 전",
                "impact": "positive",
                "importance": 0.8,
                "related_stocks": ["NAVER"],
                "source": "KB투자증권"
            },
            {
                "title": "금리 인하 기대감 확산... 국고채 금리 하락으로 주식시장 상승 동력",
                "content": "한국은행의 금리 인하 가능성이 높아지면서 국고채 금리가 하락하고 있다. 이에 따라 주식시장으로의 자금 유입이 예상되며, 특히 성장주에 대한 관심이 높아지고 있다.",
                "time": "3시간 전",
                "impact": "positive", 
                "importance": 0.6,
                "related_stocks": ["삼성전자", "SK하이닉스", "NAVER"],
                "source": "KB리서치센터"
            }
        ]
        
        return news_templates
    
    def generate_optimized_market_data(self):
        """공모전 시연용 최적화된 시장 데이터"""
        
        market_data = {
            "삼성전자": {
                "symbol": "005930",
                "name": "삼성전자",
                "price": 67500,
                "change": -2100,
                "change_percent": -3.01,
                "volume": 15234567,
                "market_cap": "대형주",
                "sector": "반도체",
                "news_sentiment": 0.3,
                "technical_signal": "hold",
                "last_update": datetime.now().isoformat()
            },
            "SK하이닉스": {
                "symbol": "000660", 
                "name": "SK하이닉스",
                "price": 128900,
                "change": 3400,
                "change_percent": 2.71,
                "volume": 8956432,
                "market_cap": "대형주",
                "sector": "반도체",
                "news_sentiment": 0.6,
                "technical_signal": "buy",
                "last_update": datetime.now().isoformat()
            },
            "NAVER": {
                "symbol": "035420",
                "name": "NAVER", 
                "price": 185500,
                "change": 1200,
                "change_percent": 0.65,
                "volume": 2341876,
                "market_cap": "대형주",
                "sector": "인터넷",
                "news_sentiment": 0.4,
                "technical_signal": "hold",
                "last_update": datetime.now().isoformat()
            },
            "카카오": {
                "symbol": "035720",
                "name": "카카오",
                "price": 47600,
                "change": -800,
                "change_percent": -1.65,
                "volume": 5432109,
                "market_cap": "대형주", 
                "sector": "인터넷",
                "news_sentiment": 0.2,
                "technical_signal": "sell",
                "last_update": datetime.now().isoformat()
            },
            "LG화학": {
                "symbol": "051910",
                "name": "LG화학",
                "price": 385000,
                "change": 5000,
                "change_percent": 1.32,
                "volume": 876543,
                "market_cap": "대형주",
                "sector": "화학",
                "news_sentiment": 0.1,
                "technical_signal": "hold",
                "last_update": datetime.now().isoformat()
            },
            "현대차": {
                "symbol": "005380",
                "name": "현대차",
                "price": 187500,
                "change": -1500,
                "change_percent": -0.79,
                "volume": 1234567,
                "market_cap": "대형주",
                "sector": "자동차",
                "news_sentiment": 0.0,
                "technical_signal": "hold",
                "last_update": datetime.now().isoformat()
            }
        }
        
        return market_data
    
    def save_demo_data(self):
        """데모 데이터 저장"""
        
        print("🎭 공모전 시연용 데모 데이터를 생성합니다...")
        
        # 시나리오 데이터
        scenarios = self.generate_realistic_demo_scenarios()
        demo_file = self.data_dir / "demo_scenarios.json"
        
        with open(demo_file, 'w', encoding='utf-8') as f:
            json.dump(scenarios, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 데모 시나리오 저장: {demo_file}")
        
        # 뉴스 데이터
        news_data = self.generate_realistic_news_data()
        news_file = self.data_dir / "demo_news.json"
        
        with open(news_file, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 데모 뉴스 저장: {news_file}")
        
        # 시장 데이터
        market_data = self.generate_optimized_market_data()
        market_file = self.data_dir / "demo_market.json"
        
        with open(market_file, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 데모 시장 데이터 저장: {market_file}")
        
        # 시연 가이드 생성
        self.create_demo_guide()
        
        print("\n🎉 데모 데이터 생성이 완료되었습니다!")
    
    def create_demo_guide(self):
        """시연 가이드 생성"""
        
        guide_content = """# KB Reflex 공모전 시연 가이드

## 🎯 시연 시나리오

### 1. 김투자 (감정적 투자자) 시연
**캐릭터**: FOMO 매수를 자주 하는 감정적 투자자

**시연 순서**:
1. 김투자 선택
2. 투자 통계 탭에서 감정별 성과 확인
   - "욕심" 상태일 때 손실 많음
   - "냉정" 상태일 때 수익 좋음
3. AI 코칭 탭에서 다음 입력:
   ```
   "삼성전자가 또 5% 떨어졌는데 FOMO가 심해서 추가 매수할까요?"
   ```
4. AI 분석 결과 확인:
   - 높은 위험도 경고
   - 과거 유사 거래 (삼성전자 -8.2% 손실)
   - 감정적 투자 원칙 위반 경고
   - 성찰 질문으로 냉정한 판단 유도

**핵심 메시지**: AI가 과거 경험을 바탕으로 감정적 판단을 견제

### 2. 박복기 (체계적 투자자) 시연
**캐릭터**: 분석적이고 체계적인 투자자

**시연 순서**:
1. 박복기 선택
2. 투자 통계에서 높은 성공률 확인
3. AI 코칭에서 다음 입력:
   ```
   "NAVER 차트 분석 결과 매수 신호가 나왔는데 어떻게 보시나요?"
   ```
4. AI 분석 결과 확인:
   - 낮은 위험도
   - 과거 성공 사례 (NAVER +8.9% 수익)
   - 체계적 접근법 인정
   - 손절선 설정 등 구체적 조언

**핵심 메시지**: AI가 체계적 투자자에게는 더 정교한 조언 제공

### 3. 이신규 (초보자) 시연
**캐릭터**: 투자 초보자

**시연 순서**:
1. 이신규 선택
2. 투자 원칙 탭에서 초보자 가이드 확인
3. AI 코칭에서 다음 입력:
   ```
   "처음 투자하는데 어떤 주식을 사야 할까요?"
   ```
4. AI 분석 결과 확인:
   - 초보자 맞춤 조언
   - 기본 투자 원칙 안내
   - 안전한 투자 방법 제안

**핵심 메시지**: AI가 사용자 수준에 맞는 개인화된 가이드 제공

## 🎨 시연 팁

1. **각 탭 순서대로 설명**:
   - AI 코칭 → 투자 통계 → 투자 원칙 → 시장 현황

2. **시각적 요소 강조**:
   - KB 노랑 브랜드 컬러
   - 직관적인 차트와 그래프
   - 명확한 위험도 표시

3. **개인화 포인트 강조**:
   - 사용자별 완전히 다른 분석 결과
   - 과거 거래 기반 맞춤형 조언
   - 성장 과정 추적

4. **기술적 차별점**:
   - 100% 설정 파일 기반 동적 시스템
   - 모든 데이터가 실시간 변경 가능
   - 확장성과 유연성

## 📊 예상 질문 & 답변

**Q: 실제 API와 연동되나요?**
A: 현재는 시연용이지만, 구조상 실제 API와 쉽게 연동 가능합니다.

**Q: AI 분석의 근거는 무엇인가요?**
A: 개인의 과거 거래 패턴, 감정 상태, 시장 상황을 종합 분석합니다.

**Q: 다른 서비스와의 차이점은?**
A: 투자 결과가 아닌 의사결정 과정에 집중하며, 개인 경험을 자산으로 활용합니다.

**Q: 확장 계획은?**
A: 실시간 API, 고도화된 AI 모델, 소셜 기능 등을 순차적으로 추가할 예정입니다.
"""
        
        guide_file = self.data_dir / "demo_guide.md"
        
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"📖 시연 가이드 저장: {guide_file}")

class KBReflexCLI:
    """KB Reflex CLI 도구"""
    
    def __init__(self):
        self.project_root = Path.cwd()
    
    def status(self):
        """프로젝트 상태 확인"""
        print("🏛️ KB Reflex 프로젝트 상태")
        print("=" * 40)
        
        # 디렉토리 확인
        dirs = ["config", "core", "components", "data"]
        for dir_name in dirs:
            dir_path = self.project_root / dir_name
            status = "✅" if dir_path.exists() else "❌"
            print(f"{status} {dir_name}/")
        
        # 주요 파일 확인
        files = ["main_app.py", "requirements.txt", "README.md"]
        for file_name in files:
            file_path = self.project_root / file_name
            status = "✅" if file_path.exists() else "❌"
            print(f"{status} {file_name}")
        
        # 설정 파일 확인
        config_dir = self.project_root / "config"
        if config_dir.exists():
            config_files = list(config_dir.glob("*.json"))
            print(f"\n📁 설정 파일: {len(config_files)}개")
            for config_file in config_files:
                print(f"  - {config_file.name}")
    
    def clean(self):
        """캐시 및 임시 파일 정리"""
        print("🧹 프로젝트 정리 중...")
        
        # __pycache__ 정리
        import shutil
        for pycache in self.project_root.rglob("__pycache__"):
            shutil.rmtree(pycache)
            print(f"🗑️ 삭제: {pycache}")
        
        # 생성된 데이터 파일 정리 (선택적)
        data_dir = self.project_root / "data"
        if data_dir.exists():
            generated_files = list(data_dir.glob("generated_*.json"))
            for file in generated_files:
                file.unlink()
                print(f"🗑️ 삭제: {file}")
        
        print("✅ 정리 완료")
    
    def demo(self):
        """데모 데이터 생성"""
        generator = DemoDataGenerator()
        generator.save_demo_data()
    
    def run(self):
        """애플리케이션 실행"""
        import subprocess
        try:
            print("🚀 KB Reflex 실행 중...")
            subprocess.run([sys.executable, "-m", "streamlit", "run", "main_app.py"])
        except KeyboardInterrupt:
            print("\n👋 KB Reflex 종료")
        except FileNotFoundError:
            print("❌ Streamlit이 설치되지 않았습니다.")
            print("pip install streamlit 을 실행해주세요.")

def main():
    """CLI 메인 함수"""
    parser = argparse.ArgumentParser(description="KB Reflex CLI 도구")
    
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령들")
    
    # 상태 확인
    subparsers.add_parser("status", help="프로젝트 상태 확인")
    
    # 정리
    subparsers.add_parser("clean", help="캐시 및 임시 파일 정리")
    
    # 데모 데이터 생성
    subparsers.add_parser("demo", help="데모 데이터 생성")
    
    # 애플리케이션 실행
    subparsers.add_parser("run", help="애플리케이션 실행")
    
    # 테스트 실행
    subparsers.add_parser("test", help="통합 테스트 실행")
    
    args = parser.parse_args()
    
    cli = KBReflexCLI()
    
    if args.command == "status":
        cli.status()
    elif args.command == "clean":
        cli.clean()
    elif args.command == "demo":
        cli.demo()
    elif args.command == "run":
        cli.run()
    elif args.command == "test":
        # 테스트 스크립트 실행
        try:
            from test_kb_reflex import main as test_main
            test_main()
        except ImportError:
            print("❌ 테스트 스크립트를 찾을 수 없습니다.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()