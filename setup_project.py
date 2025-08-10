# setup_project.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 프로젝트 초기 설정 스크립트
KB AI CHALLENGE 2024

이 스크립트는 프로젝트 실행에 필요한 모든 설정 파일과 폴더를 자동 생성합니다.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def create_directory_structure():
    """프로젝트 디렉토리 구조 생성"""
    
    directories = [
        "config",
        "data", 
        "core",
        "components"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 디렉토리 생성: {directory}/")

def create_config_files():
    """모든 설정 파일 생성"""
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # 1. UI 컬러 설정
    ui_colors = {
        "brand": {
            "yellow": "#FFDD00",
            "yellow_dark": "#FFB800",
            "yellow_light": "#FFF2A0"
        },
        "base": {
            "black": "#000000",
            "white": "#FFFFFF",
            "gray_dark": "#333333",
            "gray": "#666666",
            "gray_light": "#E5E5E5",
            "gray_bg": "#F8F9FA"
        },
        "status": {
            "success": "#28A745",
            "danger": "#DC3545",
            "warning": "#FFC107",
            "info": "#17A2B8"
        },
        "investment": {
            "profit": "#FF6B6B",
            "loss": "#4ECDC4"
        }
    }
    
    save_config_file("ui_colors.json", ui_colors)
    
    # 2. UI 설정
    ui_settings = {
        "typography": {
            "primary_font": "'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif",
            "header_font_size": "3rem",
            "subheader_font_size": "1.4rem",
            "body_font_size": "1rem",
            "small_font_size": "0.8rem"
        },
        "spacing": {
            "card_padding": "1.5rem",
            "section_margin": "2rem",
            "component_gap": "1rem"
        },
        "borders": {
            "border_radius": "12px",
            "card_border_radius": "16px",
            "button_border_radius": "8px",
            "border_width": "2px"
        },
        "shadows": {
            "card_shadow": "0 4px 12px rgba(0,0,0,0.1)",
            "hover_shadow": "0 8px 24px rgba(255,221,0,0.2)",
            "button_shadow": "0 2px 4px rgba(0,0,0,0.1)"
        },
        "animations": {
            "transition_duration": "0.3s",
            "hover_transform": "translateY(-4px)",
            "button_hover_transform": "translateY(-2px)"
        }
    }
    
    save_config_file("ui_settings.json", ui_settings)
    
    # 3. AI 코칭 설정
    ai_coaching = {
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
            },
            "lack_of_basis": {
                "keywords": ["느낌", "감", "그냥", "왠지", "추측"],
                "warning": "명확한 근거 없는 투자는 위험합니다.",
                "advice": "투자 전 충분한 분석이 필요합니다."
            }
        },
        "coaching_templates": {
            "risk_warning": {
                "high": "⚠️ 높은 위험도가 감지되었습니다. 신중한 검토가 필요합니다.",
                "medium": "💡 보통 수준의 위험이 있습니다. 추가 고려사항을 확인해보세요.",
                "low": "✅ 상대적으로 안전한 수준입니다."
            },
            "emotion_guidance": {
                "불안": "불안한 마음은 이해하지만, 객관적 데이터를 먼저 확인해보세요.",
                "욕심": "욕심은 투자의 적입니다. 목표 수익률을 정하고 지키는 것이 중요합니다.",
                "확신": "확신은 좋지만 과신은 금물입니다. 리스크 관리를 잊지 마세요.",
                "FOMO": "FOMO는 가장 위험한 투자 동기입니다. 냉정을 되찾고 다시 생각해보세요."
            }
        },
        "reflection_questions": {
            "general": [
                "이 투자 결정의 가장 명확한 근거는 무엇인가요?",
                "감정이 아닌 데이터로만 판단한다면 어떤 결론인가요?",
                "최악의 경우를 고려했을 때 감당 가능한 투자인가요?",
                "이 투자가 전체 포트폴리오에서 차지하는 비중은 적절한가요?"
            ],
            "emotional": [
                "지금 이 감정이 투자 판단에 영향을 주고 있지는 않나요?",
                "냉정한 상태였다면 같은 결정을 내렸을까요?",
                "감정을 배제하고 다시 생각해본다면 어떨까요?"
            ],
            "risk_based": [
                "이 투자로 인한 최대 손실은 얼마까지 감당할 수 있나요?",
                "리스크 대비 기대 수익이 합리적인가요?",
                "분산투자 관점에서 이 투자는 어떤 의미인가요?"
            ]
        }
    }
    
    save_config_file("ai_coaching.json", ai_coaching)
    
    # 4. 투자 원칙 설정
    investment_principles = {
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
            },
            "timeline": "6개월 이상 장기 투자 권장",
            "max_single_stock": 20
        },
        "principle_templates": {
            "high_loss_rate": [
                "손절 기준을 명확히 하고 반드시 지키기",
                "투자 전 충분한 분석과 근거 마련하기",
                "감정적 판단보다는 데이터 기반 의사결정하기"
            ],
            "emotional_trader": [
                "목표 수익률 달성 시 일부 매도 규칙 만들기",
                "FOMO나 욕심이 들 때는 하루 더 생각하기",
                "투자 일기를 써서 감정 패턴 파악하기"
            ],
            "overtrading": [
                "과도한 거래 줄이고 장기 투자 고려하기",
                "월 거래 횟수 제한 두기",
                "매매 수수료와 세금 고려하여 신중하게 거래하기"
            ],
            "concentration_risk": [
                "포트폴리오 다양화로 위험 분산하기",
                "단일 종목 비중을 20% 이하로 제한하기",
                "섹터별 분산투자 고려하기"
            ]
        },
        "risk_management": {
            "position_sizing": {
                "conservative": 5,
                "moderate": 10,
                "aggressive": 20
            },
            "stop_loss_rules": {
                "growth_stocks": -15,
                "value_stocks": -20,
                "speculative": -10
            },
            "profit_taking": {
                "first_target": 20,
                "second_target": 50,
                "trailing_stop": 10
            }
        }
    }
    
    save_config_file("investment_principles.json", investment_principles)
    
    print("✅ 모든 설정 파일 생성 완료!")

def save_config_file(filename: str, data: dict):
    """설정 파일 저장"""
    config_path = Path("config") / filename
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"📝 {filename} 생성 완료")

def create_readme():
    """README.md 파일 생성"""
    
    readme_content = """# KB Reflex - AI 투자 복기 코칭 시스템

## 🚀 빠른 시작

1. **환경 설정**
   ```bash
   pip install -r requirements.txt
   ```

2. **프로젝트 초기화**
   ```bash
   python setup_project.py
   ```

3. **애플리케이션 실행**
   ```bash
   streamlit run main_app.py
   ```

## 🎯 주요 기능

- 📊 **투자 복기 기반 AI 코칭**
- 📈 **개인화된 투자 통계 분석**
- 💡 **맞춤형 투자 원칙 제안**
- 🏛️ **KB 브랜드 UI 디자인**

## 📂 프로젝트 구조

```
KB_REFLEX/
├── main_app.py              # 메인 애플리케이션
├── core/                    # 핵심 엔진
├── components/              # UI 컴포넌트
├── config/                  # 설정 파일들
└── data/                   # 생성된 데이터
```

## ⚙️ 설정 커스터마이징

모든 설정은 `config/` 폴더의 JSON 파일에서 수정 가능:

- `ui_colors.json`: 브랜드 컬러
- `ai_coaching.json`: AI 코칭 로직
- `investment_principles.json`: 투자 원칙
- 기타 설정 파일들...

## 🔧 개발자 가이드

자세한 개발 가이드는 프로젝트 문서를 참조하세요.

## 📄 라이선스

KB AI CHALLENGE 2024
"""
    
    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📄 README.md 생성 완료")

def create_gitignore():
    """.gitignore 파일 생성"""
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Streamlit
.streamlit/

# Data files (auto-generated)
data/generated_*.json
data/cache_*.json

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Environment
.env
.venv
env/
venv/
"""
    
    with open(".gitignore", 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("📄 .gitignore 생성 완료")

def main():
    """메인 설정 스크립트"""
    
    print("🚀 KB Reflex 프로젝트 초기화를 시작합니다...")
    print("=" * 50)
    
    try:
        # 1. 디렉토리 구조 생성
        print("\n📁 디렉토리 구조 생성 중...")
        create_directory_structure()
        
        # 2. 설정 파일 생성
        print("\n⚙️ 설정 파일 생성 중...")
        create_config_files()
        
        # 3. README 생성
        print("\n📖 문서 파일 생성 중...")
        create_readme()
        create_gitignore()
        
        print("\n" + "=" * 50)
        print("🎉 KB Reflex 프로젝트 초기화가 완료되었습니다!")
        print("\n다음 단계:")
        print("1. pip install -r requirements.txt")
        print("2. streamlit run main_app.py")
        print("\n📁 생성된 파일들:")
        print("- config/ (설정 파일들)")
        print("- README.md")
        print("- .gitignore")
        
        # 설정 파일 목록 표시
        config_files = list(Path("config").glob("*.json"))
        for config_file in config_files:
            print(f"- config/{config_file.name}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

# install_and_run.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 원클릭 설치 및 실행 스크립트
KB AI CHALLENGE 2024

이 스크립트는 모든 설정을 자동으로 수행하고 애플리케이션을 실행합니다.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """필요한 패키지 설치"""
    print("📦 필요한 패키지들을 설치합니다...")
    
    requirements = [
        "streamlit>=1.28.0",
        "pandas>=2.0.0", 
        "numpy>=1.24.0",
        "plotly>=5.15.0"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} 설치 완료")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} 설치 실패: {e}")
            return False
    
    return True

def setup_project():
    """프로젝트 초기화"""
    print("⚙️ 프로젝트를 초기화합니다...")
    
    try:
        # setup_project.py의 main 함수 실행
        from setup_project import main as setup_main
        return setup_main()
    except ImportError:
        print("❌ setup_project.py를 찾을 수 없습니다.")
        return False

def run_streamlit():
    """Streamlit 애플리케이션 실행"""
    print("🚀 KB Reflex를 실행합니다...")
    
    if not Path("main_app.py").exists():
        print("❌ main_app.py를 찾을 수 없습니다.")
        return False
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "main_app.py"])
        return True
    except KeyboardInterrupt:
        print("\n👋 KB Reflex를 종료합니다.")
        return True
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🏛️ KB Reflex - AI 투자 복기 코칭 시스템")
    print("=" * 50)
    
    # 1. 패키지 설치
    if not install_requirements():
        print("❌ 패키지 설치 실패")
        return
    
    # 2. 프로젝트 설정
    if not setup_project():
        print("❌ 프로젝트 설정 실패") 
        return
    
    # 3. 애플리케이션 실행
    print("\n🎉 설치가 완료되었습니다!")
    print("브라우저에서 http://localhost:8501 로 접속하세요.")
    
    input("\n엔터 키를 눌러 KB Reflex를 시작하세요...")
    run_streamlit()

if __name__ == "__main__":
    main()