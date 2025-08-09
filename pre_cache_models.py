from transformers import MarianTokenizer, MarianMTModel

def download_model(model_name):
    """지정된 모델과 토크나이저를 다운로드하여 캐시에 저장합니다."""
    try:
        print(f"🔄 모델 다운로드 시작: {model_name}")
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        tokenizer.save_pretrained(f'./{model_name.replace("/", "_")}_cache')
        model.save_pretrained(f'./{model_name.replace("/", "_")}_cache')
        print(f"✅ 모델 다운로드 및 로컬 캐시 저장 완료: {model_name}\n")
    except Exception as e:
        print(f"❌ 모델 다운로드 실패: {model_name}")
        print(f"   오류: {e}\n")

if __name__ == "__main__":
    # 데이터 증강에 필요한 번역 모델 목록
    model_list = [
        "Helsinki-NLP/opus-mt-ko-en",
        "Helsinki-NLP/opus-mt-en-ko",
    ]
    
    print("="*50)
    print("데이터 증강에 필요한 모든 모델을 미리 다운로드합니다.")
    print("="*50)
    
    for model in model_list:
        download_model(model)
        
    print("🎉 모든 모델 다운로드 시도 완료.")