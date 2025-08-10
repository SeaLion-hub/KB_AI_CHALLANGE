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
import time

def print_banner():
    """KB Reflex 배너 출력"""
    banner = """
🏛️ ========================================== 🏛️
    KB Reflex - AI 투자 복기 코칭 시스템
    KB AI CHALLENGE 2024 출품작
🏛️ ========================================== 🏛️
"""
    print(banner)

def check_python_version():
    """Python 버전 확인"""
    print("🔍 Python 버전 확인 중...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8 이상이 필요합니다. 현재 버전: {version.major}.{version.minor}")
        print("Python을 업그레이드한 후 다시 시도해주세요.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} 확인 완료")
    return True

def install_requirements():
    """필요한 패키지 설치"""
    print("\n📦 필요한 패키지들을 설치합니다...")
    
    requirements = [
        "streamlit>=1.28.0",
        "pandas>=2.0.0", 
        "numpy>=1.24.0",
        "plotly>=5.15.0"
    ]
    
    for i, package in enumerate(requirements, 1):
        try:
            print(f"  [{i}/{len(requirements)}] {package} 설치 중...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"  ✅ {package} 설치 완료")
            else:
                print(f"  ⚠️ {package} 설치 중 경고 (계속 진행)")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ {package} 설치 시간 초과 (계속 진행)")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ {package} 설치 실패: {e}")
            print("  💡 수동으로 설치해주세요: pip install", package)
    
    print("✅ 패키지 설치 단계 완료")
    return True

def setup_project():
    """프로젝트 초기화"""
    print("\n⚙️ 프로젝트를 초기화합니다...")
    
    try:
        # setup_project.py가 있는지 확인
        if Path("setup_project.py").exists():
            print("  📄 setup_project.py 실행 중...")
            result = subprocess.run([sys.executable, "setup_project.py"], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("  ✅ 프로젝트 초기화 완료")
                return True
            else:
                print("  ⚠️ setup_project.py 실행 중 오류, 기본 설정으로 진행")
        
        # setup_project.py가 없거나 실패한 경우 기본 설정
        return create_basic_setup()
        
    except Exception as e:
        print(f"  ❌ 프로젝트 초기화 실패: {e}")
        print("  💡 기본 설정으로 진행합니다...")
        return create_basic_setup()

def create_basic_setup():
    """기본 프로젝트 설정"""
    print("  📁 기본 디렉토리 구조 생성 중...")
    
    # 필수 디렉토리 생성
    directories = ["config", "data", "core", "components"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"    📂 {directory}/ 생성")
    
    # 기본 __init__.py 파일 생성
    for directory in ["core", "components"]:
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# KB Reflex Module\n")
    
    print("  ✅ 기본 설정 완료")
    return True

def generate_demo_data():
    """데모 데이터 생성"""
    print("\n🎭 데모 데이터를 생성합니다...")
    
    try:
        if Path("demo_data_generator.py").exists():
            print("  📊 demo_data_generator.py 실행 중...")
            result = subprocess.run([
                sys.executable, "demo_data_generator.py", "demo"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("  ✅ 데모 데이터 생성 완료")
            else:
                print("  ⚠️ 데모 데이터 생성 실패, 기본 데이터로 진행")
        else:
            print("  💡 demo_data_generator.py가 없어 기본 데이터로 진행")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 데모 데이터 생성 실패: {e}")
        print("  💡 기본 데이터로 계속 진행합니다...")
        return True

def check_main_app():
    """main_app.py 파일 확인"""
    print("\n🔍 메인 애플리케이션 파일 확인 중...")
    
    if not Path("main_app.py").exists():
        print("❌ main_app.py 파일을 찾을 수 없습니다!")
        print("💡 다음 사항을 확인해주세요:")
        print("  1. 현재 디렉토리가 KB_Reflex 프로젝트 폴더인지 확인")
        print("  2. main_app.py 파일이 존재하는지 확인")
        print("  3. 파일 권한이 올바른지 확인")
        return False
    
    print("✅ main_app.py 파일 확인 완료")
    return True

def run_streamlit():
    """Streamlit 애플리케이션 실행"""
    print("\n🚀 KB Reflex를 실행합니다...")
    print("📱 브라우저에서 http://localhost:8501 로 자동 접속됩니다.")
    print("🛑 종료하려면 Ctrl+C를 누르세요.")
    print("\n" + "="*50)
    
    try:
        # Streamlit 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "main_app.py",
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
        return True
        
    except KeyboardInterrupt:
        print("\n\n👋 KB Reflex를 종료합니다. 감사합니다!")
        return True
        
    except FileNotFoundError:
        print("\n❌ Streamlit이 설치되지 않았습니다.")
        print("💡 다음 명령어를 실행해주세요:")
        print("   pip install streamlit")
        return False
        
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        print("💡 수동으로 실행해보세요:")
        print("   streamlit run main_app.py")
        return False

def show_success_message():
    """성공 메시지 출력"""
    success_msg = """
🎉 =================== 설치 완료! =================== 🎉

✅ KB Reflex가 성공적으로 설치되었습니다!

📱 브라우저에서 다음 주소로 접속하세요:
   👉 http://localhost:8501

🎭 공모전 시연 가이드:
   1. 김투자 (감정적 투자자) → FOMO 상황 입력
   2. 박복기 (체계적 투자자) → 분석적 질문 입력  
   3. 이신규 (초보 투자자) → 기본 질문 입력

💡 문제가 발생하면:
   - python test_kb_reflex.py (테스트 실행)
   - python demo_data_generator.py status (상태 확인)

🏛️ KB AI Challenge 2024 화이팅! 🏆

===============================================
"""
    print(success_msg)

def main():
    """메인 실행 함수"""
    print_banner()
    
    # 실행 단계들
    steps = [
        ("Python 버전 확인", check_python_version),
        ("패키지 설치", install_requirements), 
        ("프로젝트 초기화", setup_project),
        ("데모 데이터 생성", generate_demo_data),
        ("메인 앱 확인", check_main_app)
    ]
    
    print("🔄 KB Reflex 설치를 시작합니다...\n")
    
    # 각 단계 실행
    for step_name, step_func in steps:
        try:
            if not step_func():
                print(f"\n❌ {step_name} 단계에서 문제가 발생했습니다.")
                print("💡 수동으로 해결한 후 다시 시도해주세요.")
                return False
        except Exception as e:
            print(f"\n❌ {step_name} 중 예외 발생: {e}")
            print("💡 계속 진행합니다...")
    
    # 설치 완료 메시지
    show_success_message()
    
    # 사용자에게 실행 여부 확인
    try:
        user_input = input("지금 KB Reflex를 실행하시겠습니까? (y/n): ").lower().strip()
        
        if user_input in ['y', 'yes', '']:
            return run_streamlit()
        else:
            print("\n👍 설치가 완료되었습니다!")
            print("🚀 나중에 실행하려면: streamlit run main_app.py")
            return True
            
    except KeyboardInterrupt:
        print("\n\n👋 설치를 종료합니다.")
        return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 설치가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        print("💡 수동 설치를 시도해주세요:")
        print("   1. pip install streamlit pandas numpy plotly")
        print("   2. python setup_project.py")  
        print("   3. streamlit run main_app.py")
        sys.exit(1)