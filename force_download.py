import os
from huggingface_hub import snapshot_download

# 다운로드 시 저장될 캐시 폴더를 명시적으로 지정 (선택사항이지만 안정성을 높임)
cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
os.makedirs(cache_dir, exist_ok=True)

# 문제가 되는 모델 ID
model_id = "Helsinki-NLP/opus-mt-en-ko"

print("="*60)
print(f"'{model_id}' 모델의 강제 다운로드를 시작합니다...")
print(f"저장될 캐시 위치: {cache_dir}")
print("="*60)

try:
    # 이 함수는 모델 저장소의 모든 파일을 지정된 캐시 폴더로 다운로드합니다.
    # Transformers가 요구하는 정확한 폴더 구조를 자동으로 만들어줍니다.
    snapshot_download(
        repo_id=model_id,
        cache_dir=cache_dir
    )
    print(f"✅ 모델 다운로드 및 캐시 저장 완료!")
    
except Exception as e:
    print(f"❌ 다운로드 중 심각한 오류가 발생했습니다: {e}")
    print("\n[문제 해결 가이드]")
    print("1. 인터넷 연결 및 방화벽 설정을 확인해주세요.")
    print("2. 터미널에서 'huggingface-cli login' 명령어로 HuggingFace에 로그인하면 해결될 수 있습니다.")