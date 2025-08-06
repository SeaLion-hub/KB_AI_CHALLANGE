#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB AI Challenge - 투자 심리 분석 모델 훈련 스크립트 (경로 수정 버전)
KB Reflex: AI 투자 심리 코칭 플랫폼
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

# 재현 가능한 결과를 위한 시드 설정
torch.manual_seed(42)
np.random.seed(42)

class InvestmentEmotionDataset(Dataset):
    """투자 메모와 감정 태그를 처리하는 PyTorch 데이터셋 클래스"""
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self) -> int:
        return len(self.texts)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def find_csv_files():
    """CSV 파일 위치 자동 탐지"""
    possible_locations = [
        # 현재 디렉토리
        ["kim_gukmin_trades.csv", "park_tuja_trades.csv"],
        # data 폴더
        ["data/kim_gukmin_trades.csv", "data/park_tuja_trades.csv"],
        # 절대 경로로 data 폴더 확인
        [str(Path("data/kim_gukmin_trades.csv").resolve()), 
         str(Path("data/park_tuja_trades.csv").resolve())],
    ]
    
    for file_list in possible_locations:
        if all(os.path.exists(file) for file in file_list):
            print(f"✅ CSV 파일 발견: {os.path.dirname(file_list[0]) or '현재 디렉토리'}")
            return file_list
    
    return None

def create_data_if_missing():
    """데이터가 없으면 자동 생성"""
    print("📊 CSV 파일이 없어서 자동 생성합니다...")
    
    try:
        # 현재 스크립트 위치 기준으로 프로젝트 루트 찾기
        current_file = Path(__file__)
        project_root = current_file.parent
        
        # sys.path에 프로젝트 루트 추가
        import sys
        sys.path.insert(0, str(project_root))
        
        from db.user_db import UserDatabase
        db = UserDatabase()
        
        # 생성된 파일 경로 반환
        data_dir = project_root / "data"
        return [
            str(data_dir / "kim_gukmin_trades.csv"),
            str(data_dir / "park_tuja_trades.csv")
        ]
        
    except Exception as e:
        print(f"❌ 자동 데이터 생성 실패: {e}")
        print("💡 수동으로 'python db/user_db.py'를 실행해주세요.")
        return None

def load_and_combine_data(file_paths: List[str]) -> pd.DataFrame:
    """여러 CSV 파일을 로드하고 하나의 DataFrame으로 통합"""
    print("📊 데이터 로딩 중...")
    dataframes = []
    
    for file_path in file_paths:
        try:
            # 다양한 인코딩 시도
            encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is not None:
                print(f"✅ {file_path} 로드 완료: {len(df)}개 레코드")
                dataframes.append(df)
            else:
                print(f"❌ {file_path} 인코딩 오류")
                
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            continue
        except Exception as e:
            print(f"❌ {file_path} 로드 실패: {str(e)}")
            continue
    
    if not dataframes:
        raise ValueError("로드할 수 있는 데이터 파일이 없습니다.")
    
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(f"🔄 데이터 통합 완료: 총 {len(combined_df)}개 레코드")
    
    return combined_df

def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int], Dict[int, str]]:
    """데이터 전처리 및 라벨 인코딩"""
    print("🔧 데이터 전처리 중...")
    
    # 필수 컬럼 확인
    required_columns = ['메모', '감정태그']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ 필수 컬럼이 없습니다: {missing_columns}")
        print(f"💡 사용 가능한 컬럼: {list(df.columns)}")
        raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")
    
    # 결측값 제거
    initial_len = len(df)
    df = df.dropna(subset=['메모', '감정태그'])
    print(f"📝 결측값 제거: {initial_len} -> {len(df)}개 레코드")
    
    # 빈 문자열 제거
    df = df[df['메모'].str.strip() != '']
    df = df[df['감정태그'].str.strip() != '']
    print(f"📝 빈 값 제거 후: {len(df)}개 레코드")
    
    # 감정태그에서 # 기호 제거 (있는 경우)
    df['감정태그'] = df['감정태그'].str.replace('#', '', regex=False)
    
    # 라벨 인코딩
    label_encoder = LabelEncoder()
    df['label_encoded'] = label_encoder.fit_transform(df['감정태그'])
    
    # 매핑 딕셔너리 생성
    label_to_id = {label: idx for idx, label in enumerate(label_encoder.classes_)}
    id_to_label = {idx: label for label, idx in label_to_id.items()}
    
    print(f"🏷️  감정 라벨 매핑:")
    for label, idx in label_to_id.items():
        count = len(df[df['감정태그'] == label])
        print(f"   {idx}: {label} ({count}개)")
    
    return df, label_to_id, id_to_label

def create_train_val_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """훈련/검증 데이터셋 분할"""
    print("✂️  데이터 분할 중...")
    
    train_df, val_df = train_test_split(
        df, 
        test_size=test_size, 
        random_state=random_state,
        stratify=df['label_encoded']
    )
    
    print(f"📊 훈련 데이터: {len(train_df)}개")
    print(f"📊 검증 데이터: {len(val_df)}개")
    
    return train_df, val_df

def initialize_model_and_tokenizer(model_name: str, num_labels: int) -> Tuple[Any, Any]:
    """모델과 토크나이저 초기화"""
    print(f"🤖 모델 초기화 중: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels
    )
    
    print(f"✅ 모델 로드 완료 (라벨 수: {num_labels})")
    return model, tokenizer

def compute_metrics(eval_pred) -> Dict[str, float]:
    """평가 메트릭 계산"""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    accuracy = accuracy_score(labels, predictions)
    
    return {'accuracy': accuracy}

def save_model_info(output_dir: str, label_to_id: Dict[str, int], id_to_label: Dict[int, str]):
    """모델 정보 및 라벨 매핑 저장"""
    model_info = {
        'label_to_id': label_to_id,
        'id_to_label': {str(k): v for k, v in id_to_label.items()},
        'num_labels': len(label_to_id),
        'model_type': 'BERT-based emotion classifier for investment psychology'
    }
    
    info_path = os.path.join(output_dir, 'model_info.json')
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(model_info, f, ensure_ascii=False, indent=2)
    
    print(f"💾 모델 정보 저장: {info_path}")

def main():
    """메인 훈련 파이프라인"""
    print("🚀 KB Reflex 투자 심리 분석 모델 훈련 시작")
    print("=" * 60)
    
    # 설정값
    MODEL_NAME = "klue/bert-base"
    OUTPUT_DIR = "./sentiment_model"
    
    try:
        # 1. CSV 파일 찾기 또는 생성
        CSV_FILES = find_csv_files()
        
        if CSV_FILES is None:
            CSV_FILES = create_data_if_missing()
            if CSV_FILES is None:
                raise FileNotFoundError("CSV 파일을 찾거나 생성할 수 없습니다.")
        
        # 2. 데이터 로딩 및 전처리
        df = load_and_combine_data(CSV_FILES)
        df, label_to_id, id_to_label = preprocess_data(df)
        
        # 3. 데이터 분할
        train_df, val_df = create_train_val_split(df)
        
        # 4. 모델 및 토크나이저 초기화
        model, tokenizer = initialize_model_and_tokenizer(MODEL_NAME, len(label_to_id))
        
        # 5. 데이터셋 생성
        print("🎯 PyTorch 데이터셋 생성 중...")
        train_dataset = InvestmentEmotionDataset(
            texts=train_df['메모'].tolist(),
            labels=train_df['label_encoded'].tolist(),
            tokenizer=tokenizer
        )
        
        val_dataset = InvestmentEmotionDataset(
            texts=val_df['메모'].tolist(),
            labels=val_df['label_encoded'].tolist(),
            tokenizer=tokenizer
        )
        
        # 6. 훈련 설정 (버전 호환성)
        try:
            training_args = TrainingArguments(
                output_dir=OUTPUT_DIR,
                num_train_epochs=3,
                per_device_train_batch_size=16,
                per_device_eval_batch_size=64,
                warmup_steps=100,
                weight_decay=0.01,
                eval_strategy="steps",
                save_strategy="steps",
                eval_steps=50,
                save_steps=50,
                logging_steps=50,
                load_best_model_at_end=True,
                metric_for_best_model="accuracy",
                greater_is_better=True,
                save_total_limit=2,
                remove_unused_columns=False,
            )
        except TypeError:
            # 구 버전 호환성
            print("⚠️  구 버전 transformers 감지, 호환성 모드...")
            training_args = TrainingArguments(
                output_dir=OUTPUT_DIR,
                num_train_epochs=3,
                per_device_train_batch_size=16,
                per_device_eval_batch_size=64,
                warmup_steps=100,
                weight_decay=0.01,
                evaluation_strategy="steps",
                save_strategy="steps",
                eval_steps=50,
                save_steps=50,
                logging_steps=50,
                load_best_model_at_end=True,
                metric_for_best_model="accuracy",
                greater_is_better=True,
                save_total_limit=2,
                remove_unused_columns=False,
            )
        
        # 7. 트레이너 초기화
        print("🏃‍♂️ 트레이너 초기화 중...")
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=tokenizer,
            compute_metrics=compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
        )
        
        # 8. 모델 훈련
        print("🎓 모델 훈련 시작...")
        print("=" * 60)
        trainer.train()
        
        # 9. 최종 평가
        print("📊 최종 평가 중...")
        eval_results = trainer.evaluate()
        print(f"✅ 최종 검증 정확도: {eval_results['eval_accuracy']:.4f}")
        
        # 10. 모델 저장
        print("💾 모델 저장 중...")
        trainer.save_model()
        tokenizer.save_pretrained(OUTPUT_DIR)
        
        # 11. 모델 정보 저장
        save_model_info(OUTPUT_DIR, label_to_id, id_to_label)
        
        # 12. 상세 분류 보고서 생성
        print("📋 분류 성능 보고서 생성 중...")
        predictions = trainer.predict(val_dataset)
        y_pred = np.argmax(predictions.predictions, axis=1)
        y_true = val_df['label_encoded'].tolist()
        
        print("\n📊 상세 분류 보고서:")
        print("=" * 60)
        target_names = [id_to_label[i] for i in range(len(id_to_label))]
        print(classification_report(y_true, y_pred, target_names=target_names))
        
        print("\n🎉 훈련 완료!")
        print(f"📁 모델 저장 위치: {OUTPUT_DIR}")
        print("=" * 60)
        
        # 13. 간단한 테스트
        print("\n🧪 모델 테스트:")
        test_texts = [
            "코스피가 너무 떨어져서 무서워서 전량 매도했어요",
            "유튜버 추천받고 급하게 매수했습니다",
            "기술적 분석 결과 적정 매수 타이밍으로 판단됨"
        ]
        
        for test_text in test_texts:
            inputs = tokenizer(test_text, return_tensors="pt", truncation=True, max_length=128)
            with torch.no_grad():
                outputs = model(**inputs)
                predicted_id = torch.argmax(outputs.logits, dim=-1).item()
                predicted_emotion = id_to_label[predicted_id]
                confidence = torch.softmax(outputs.logits, dim=-1).max().item()
            
            print(f"📝 '{test_text[:30]}...'")
            print(f"🎯 예측: {predicted_emotion} (신뢰도: {confidence:.3f})")
            print()
        
    except Exception as e:
        print(f"❌ 훈련 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()