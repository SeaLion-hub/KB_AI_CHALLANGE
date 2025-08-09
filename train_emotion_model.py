#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB AI Challenge - KB Reflex 투자 심리 분석 모델 (시연용 고도화 버전)
시연 안정성과 낮은 오답 리스크에 최적화된 7클래스/4클래스 동시 학습 시스템

핵심 설계 원칙:
1. 시연 리스크 통제: 불확실성 거부 로직으로 애매한 예측 회피
2. 누수 방지: 시연 후보 문장을 직접 학습에 사용하지 않고 어휘 상관만 활용
3. 일반화 보존: 과도한 증강/편향 방지로 실제 성능 유지
4. 사용자 단위 평가: GroupKFold로 현실적 성능 측정
5. 투명한 리포팅: 모든 지표와 한계점 명시
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path
import warnings
import time
import random
import sys
import argparse
from collections import Counter, defaultdict
import pickle

# 프로젝트 루트 설정
current_file = Path(__file__)
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

warnings.filterwarnings('ignore')

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
    MarianMTModel,
    MarianTokenizer
)
from sklearn.model_selection import train_test_split, GroupKFold, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score, 
    confusion_matrix, precision_recall_fscore_support
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 중앙 데이터 관리자 import - 다양한 경로 시도
get_data_manager = None
import_paths = [
    "db.central_data_manager",
    "central_data_manager", 
    "db.central_data_manager",
    "REFLEX.db.central_data_manager",
    "sentiment_model.db.central_data_manager"
]

for import_path in import_paths:
    try:
        if import_path == "db.central_data_manager":
            from db.central_data_manager import get_data_manager
        elif import_path == "central_data_manager":
            from central_data_manager import get_data_manager
        elif import_path == "REFLEX.db.central_data_manager":
            from REFLEX.db.central_data_manager import get_data_manager
        elif import_path == "sentiment_model.db.central_data_manager":
            from sentiment_model.db.central_data_manager import get_data_manager
        else:
            # 동적 import
            import importlib
            module = importlib.import_module(import_path)
            get_data_manager = getattr(module, 'get_data_manager')
        
        print(f"✅ 중앙 데이터 관리자 로드 성공: {import_path}")
        break
    except (ImportError, AttributeError, ModuleNotFoundError) as e:
        continue

if get_data_manager is None:
    print("⚠️ 모든 경로에서 중앙 데이터 관리자를 찾을 수 없습니다.")
    print("💡 다음 위치들을 확인해주세요:")
    for path in import_paths:
        print(f"   - {path}")
    print("📁 현재 프로젝트 구조를 확인하고 올바른 경로로 수정해주세요.")
    print("🔄 Mock 데이터로 진행합니다.")

# 재현성을 위한 시드 고정
RANDOM_SEED = 42
torch.manual_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# 7클래스 → 4클래스 매핑 (시연 안정성을 위한 단순화)
LABEL_7TO4_MAPPING = {
    '공포': '부정',     # 명확한 부정 감정
    '불안': '부정',     # 명확한 부정 감정  
    '후회': '부정',     # 명확한 부정 감정
    '냉정': '중립',     # 이성적 판단
    '확신': '긍정',     # 명확한 긍정 감정
    '흥분': '긍정',     # 명확한 긍정 감정
    '욕심': '탐욕'      # 독립적인 위험 감정
}

class CBLoss(nn.Module):
    """Class-Balanced Loss for 불균형 데이터셋"""
    def __init__(self, samples_per_class, beta=0.9999, gamma=2.0):
        super(CBLoss, self).__init__()
        effective_num = 1.0 - np.power(beta, samples_per_class)
        weights = (1.0 - beta) / np.array(effective_num)
        weights = weights / np.sum(weights) * len(weights)
        self.weights = torch.tensor(weights, dtype=torch.float32)
        self.gamma = gamma
        
    def forward(self, logits, labels):
        """CB Loss 계산"""
        if logits.device != self.weights.device:
            self.weights = self.weights.to(logits.device)
        
        ce_loss = nn.CrossEntropyLoss(reduction='none')(logits, labels)
        pt = torch.exp(-ce_loss)
        focal_weight = (1 - pt) ** self.gamma
        cb_weight = self.weights[labels]
        loss = focal_weight * cb_weight * ce_loss
        return loss.mean()

class FocalLoss(nn.Module):
    """Focal Loss for 어려운 샘플 집중 학습"""
    def __init__(self, alpha=1, gamma=2, weight=None):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.weight = weight
        
    def forward(self, logits, labels):
        """Focal Loss 계산"""
        ce_loss = nn.CrossEntropyLoss(reduction='none', weight=self.weight)(logits, labels)
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        return focal_loss.mean()

class CustomTrainer(Trainer):
    """커스텀 손실 함수를 지원하는 트레이너"""
    def __init__(self, loss_type='weighted_ce', class_weights=None, samples_per_class=None, **kwargs):
        super().__init__(**kwargs)
        self.loss_type = loss_type
        self.class_weights = class_weights
        self.samples_per_class = samples_per_class
        
        # 손실 함수 초기화
        if loss_type == 'focal':
            self.loss_fn = FocalLoss(weight=class_weights)
        elif loss_type == 'cbloss' and samples_per_class is not None:
            self.loss_fn = CBLoss(samples_per_class)
        else:  # weighted_ce
            self.loss_fn = None  # 기본 CrossEntropyLoss 사용
    
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        """커스텀 손실 계산 - 새로운 transformers 버전 호환"""
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        
        if self.loss_fn is not None:
            loss = self.loss_fn(logits, labels)
        else:
            # 기본 weighted CrossEntropyLoss
            if self.class_weights is not None:
                if self.class_weights.device != logits.device:
                    self.class_weights = self.class_weights.to(logits.device)
                loss_fn = nn.CrossEntropyLoss(weight=self.class_weights)
            else:
                loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits, labels)
        
        return (loss, outputs) if return_outputs else loss

class DemoAwareAugmentation:
    """시연 안정성을 위한 보수적 데이터 증강 (누수 방지)"""
    
    def __init__(self, demo_csv_path: Optional[str] = None):
        self.demo_csv_path = demo_csv_path
        self.demo_texts = []
        self.demo_vocab_weights = {}
        self.translation_available = False
        
        # 시연 후보 문장 로드 (누수 방지: 직접 학습에 사용하지 않음)
        if demo_csv_path and os.path.exists(demo_csv_path):
            self._load_demo_candidates()
            self._compute_vocab_weights()
        
        # 번역 모델 초기화 시도
        self._setup_translation()
        
        print(f"🎯 시연 인식 증강기 초기화 완료")
        print(f"   - 시연 후보: {len(self.demo_texts)}개")
        print(f"   - 번역 기능: {'✅' if self.translation_available else '❌'}")
        print(f"   - 누수 방지: 시연 문장 직접 학습 금지")
    
    def _load_demo_candidates(self):
        """시연 후보 문장 로드 (학습 데이터로 절대 사용하지 않음)"""
        try:
            demo_df = pd.read_csv(self.demo_csv_path)
            if 'text' in demo_df.columns:
                self.demo_texts = demo_df['text'].dropna().tolist()
                print(f"📄 시연 후보 로드: {len(self.demo_texts)}개 문장")
            else:
                print(f"⚠️ 시연 CSV에 'text' 컬럼이 없습니다: {list(demo_df.columns)}")
        except Exception as e:
            print(f"❌ 시연 후보 로드 실패: {e}")
    
    def _compute_vocab_weights(self):
        """시연 후보와의 어휘 상관도 계산 (TF-IDF 기반)"""
        if not self.demo_texts:
            return
        
        try:
            # 간단한 TF-IDF 벡터화
            vectorizer = TfidfVectorizer(max_features=1000, stop_words=None, lowercase=True)
            demo_vectors = vectorizer.fit_transform(self.demo_texts)
            vocab = vectorizer.get_feature_names_out()
            
            # 어휘별 가중치 계산 (빈도 기반)
            feature_weights = np.mean(demo_vectors.toarray(), axis=0)
            self.demo_vocab_weights = dict(zip(vocab, feature_weights))
            
            print(f"🔍 어휘 상관도 계산 완료: {len(self.demo_vocab_weights)}개 토큰")
            
        except Exception as e:
            print(f"⚠️ 어휘 가중치 계산 실패: {e}")
    
    def _setup_translation(self):
        """번역 모델 설정 (Back Translation용)"""
        try:
            self.ko_to_en_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-ko-en")
            self.ko_to_en_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-ko-en")
            self.en_to_ko_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ko")
            self.en_to_ko_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-ko")
            self.translation_available = True
            print("✅ 번역 모델 로드 완료")
        except Exception as e:
            print(f"⚠️ 번역 모델 로드 실패: {str(e)[:100]}... (증강 기능 제한)")
    
    def _get_demo_similarity_weight(self, text: str) -> float:
        """시연 후보와의 유사도 기반 가중치 계산 (누수 없는 방식)"""
        if not self.demo_vocab_weights:
            return 1.0
        
        # 텍스트의 토큰들이 시연 어휘와 얼마나 겹치는지 계산
        tokens = text.lower().split()
        overlap_score = sum(self.demo_vocab_weights.get(token, 0) for token in tokens)
        
        # 보수적 가중치: 1.0~1.2 범위로 제한 (과도한 편향 방지)
        return min(1.2, 1.0 + overlap_score * 0.1)
    
    def back_translate(self, text: str) -> str:
        """Back Translation: 한국어 → 영어 → 한국어"""
        if not self.translation_available:
            return text
        
        try:
            # 한국어 → 영어
            inputs = self.ko_to_en_tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            outputs = self.ko_to_en_model.generate(**inputs, max_length=128, do_sample=True, temperature=0.7)
            english = self.ko_to_en_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 영어 → 한국어
            inputs = self.en_to_ko_tokenizer(english, return_tensors="pt", truncation=True, max_length=128)
            outputs = self.en_to_ko_model.generate(**inputs, max_length=128, do_sample=True, temperature=0.7)
            back_korean = self.en_to_ko_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return back_korean.strip() if back_korean.strip() != text else text
            
        except Exception:
            return text
    
    def synonym_replace(self, text: str) -> str:
        """투자 관련 동의어 교체"""
        synonyms = {
            '매수': ['구매', '매입', '취득'],
            '매도': ['판매', '매각', '처분'],
            '급등': ['상승', '폭등', '오름'],
            '급락': ['하락', '폭락', '떨어짐'],
            '불안': ['걱정', '우려', '두려움'],
            '확신': ['믿음', '신념', '자신감'],
            '손절': ['손해매도', '손실정리', '컷로스'],
            '물타기': ['추가매수', '평단가낮추기'],
            '존버': ['장기보유', '홀딩'],
            '대박': ['큰수익', '고수익']
        }
        
        words = text.split()
        result = []
        
        for word in words:
            # 30% 확률로 동의어 교체 (보수적)
            if random.random() < 0.3:
                for original, replacements in synonyms.items():
                    if original in word:
                        replacement = random.choice(replacements)
                        word = word.replace(original, replacement)
                        break
            result.append(word)
        
        return ' '.join(result)
    
    def insert_filler(self, text: str) -> str:
        """자연스러운 부가어 삽입"""
        fillers = ['정말로', '사실', '실제로', '그런데', '아무래도', '확실히', '당연히']
        words = text.split()
        
        if len(words) >= 3 and random.random() < 0.2:  # 20% 확률
            pos = random.randint(1, len(words) - 1)
            filler = random.choice(fillers)
            words.insert(pos, filler)
        
        return ' '.join(words)
    
    def augment_with_demo_awareness(self, texts: List[str], labels: List[str], 
                                  augment_ratio: float = 1.2, minority_only: bool = True) -> Tuple[List[str], List[str]]:
        """시연 인식 증강 (누수 방지하면서 안정성 향상)"""
        
        print(f"🔄 시연 인식 데이터 증강 시작")
        print(f"   - 증강 비율: {augment_ratio:.1f}x (보수적 상한)")
        print(f"   - 소수 클래스만: {minority_only}")
        print(f"   - 누수 방지: 시연 문장 직접 사용 금지")
        
        augmented_texts = texts.copy()
        augmented_labels = labels.copy()
        
        # 라벨별 개수 계산
        label_counts = Counter(labels)
        total_original = len(texts)
        target_total = int(total_original * augment_ratio)
        
        print(f"📊 원본 분포: {dict(label_counts)}")
        
        for label, count in label_counts.items():
            # 소수 클래스만 증강하는 경우
            if minority_only:
                median_count = np.median(list(label_counts.values()))
                if count >= median_count:
                    continue
            
            # 목표 개수 계산 (과도하게 늘리지 않음)
            target_count = min(count * 2, int(count * augment_ratio))  # 최대 2배
            need_count = target_count - count
            
            if need_count <= 0:
                continue
            
            # 해당 라벨의 텍스트들
            label_texts = [text for text, lbl in zip(texts, labels) if lbl == label]
            generated = 0
            
            for _ in range(need_count * 3):  # 여유분으로 3배 시도
                if generated >= need_count:
                    break
                
                # 원본 텍스트 선택
                source_text = random.choice(label_texts)
                
                # 시연 유사도 기반 가중 샘플링 (누수 없이)
                demo_weight = self._get_demo_similarity_weight(source_text)
                if random.random() > demo_weight / 1.2:  # 가중치 적용
                    continue
                
                # 증강 방법 선택
                methods = ['synonym', 'filler']
                if self.translation_available:
                    methods.append('back_translate')
                
                method = random.choice(methods)
                
                # 증강 실행
                if method == 'back_translate':
                    aug_text = self.back_translate(source_text)
                elif method == 'synonym':
                    aug_text = self.synonym_replace(source_text)
                else:  # filler
                    aug_text = self.insert_filler(source_text)
                
                # 유효성 검사 (누수 방지)
                if self._is_valid_augmented_text(aug_text, source_text):
                    augmented_texts.append(aug_text)
                    augmented_labels.append(label)
                    generated += 1
            
            print(f"   {label}: {count} → {count + generated} (+{generated})")
        
        print(f"✅ 증강 완료: {len(augmented_texts)}개 ({len(augmented_texts) - total_original:+d})")
        
        return augmented_texts, augmented_labels
    
    def _is_valid_augmented_text(self, aug_text: str, original_text: str) -> bool:
        """증강 텍스트 유효성 검사 (누수 방지)"""
        # 1. 최소 길이 체크
        if len(aug_text.strip()) < 5:
            return False
        
        # 2. 원본과 동일한지 체크
        if aug_text.strip() == original_text.strip():
            return False
        
        # 3. 시연 후보와 동일/매우 유사한지 체크 (누수 방지)
        for demo_text in self.demo_texts:
            if aug_text.strip() == demo_text.strip():
                return False
            # 90% 이상 겹치면 거부
            if self._text_similarity(aug_text, demo_text) > 0.9:
                return False
        
        # 4. 금지어 체크
        banned_words = ['테스트', 'test', '샘플', 'sample']
        if any(word in aug_text.lower() for word in banned_words):
            return False
        
        return True
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """간단한 텍스트 유사도 계산"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)

class InvestmentEmotionDataset(Dataset):
    """투자 감정 분석 데이터셋"""
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 192):
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

def load_data_from_central_manager() -> pd.DataFrame:
    """중앙 데이터 관리자에서 데이터 로드"""
    if get_data_manager is None:
        # Mock 데이터 생성 (테스트용) - 더 현실적인 데이터
        print("📊 Mock 데이터 생성 중...")
        mock_data = []
        emotions = ['공포', '냉정', '불안', '욕심', '확신', '후회', '흥분']
        
        # 더 다양하고 현실적인 투자 메모 템플릿
        memo_templates = {
            '공포': [
                "코스피가 너무 떨어져서 무서워서 전량 매도했어요",
                "폭락장에서 패닉매도 해버렸습니다",
                "손실이 무서워서 급하게 손절했어요",
                "하락장이 두려워서 모든 포지션 정리",
                "공포감에 휩쓸려서 저가에 팔았습니다"
            ],
            '냉정': [
                "기술적 분석 결과 적정 매수 타이밍으로 판단됨",
                "펀더멘털 분석 후 냉정하게 매수 결정",
                "차트 분석 결과에 따라 매도했습니다",
                "재무제표 검토 후 합리적 판단으로 매수",
                "시장 상황을 분석한 결과 매도 타이밍"
            ],
            '불안': [
                "손실이 너무 커서 불안해서 일부 매도했습니다",
                "계속 떨어질까봐 불안해서 팔았어요",
                "불안감 때문에 반절만 매도했습니다",
                "하락이 지속될까 걱정되어 일부 매도",
                "앞으로가 불안해서 포지션 줄였어요"
            ],
            '욕심': [
                "다들 사라고 해서 욕심내서 추가 매수했어요",
                "더 오를 것 같아서 욕심부려 물타기",
                "대박날 것 같아서 욕심내서 올인",
                "욕심이 나서 빚내서 추가 매수",
                "큰 수익을 위해 욕심부려서 레버리지"
            ],
            '확신': [
                "완벽한 분석 후 확신을 가지고 매수했습니다",
                "이 종목은 확실하다고 생각해서 매수",
                "분명히 오를 거라는 확신으로 매수",
                "확실한 정보를 바탕으로 매수 결정",
                "100% 확신을 가지고 대량 매수"
            ],
            '후회': [
                "너무 일찍 판 것 같아서 후회됩니다",
                "더 기다렸어야 했는데 후회스러워요",
                "성급하게 팔아서 후회하고 있습니다",
                "좀 더 참았으면 좋았을 텐데 후회됨",
                "타이밍을 잘못 잡아서 후회스럽습니다"
            ],
            '흥분': [
                "급등 소식에 흥분해서 대량 매수했어요",
                "상한가 뉴스에 흥분해서 추가 매수",
                "대박 소식에 흥분해서 올인했습니다",
                "급등에 흥분해서 이성을 잃고 매수",
                "좋은 뉴스에 흥분해서 즉시 매수"
            ]
        }
        
        # 사용자별 다양한 패턴 생성
        user_count = 72  # 사용자 수
        records_per_emotion = 72  # 감정별 레코드 수
        
        for emotion in emotions:
            templates = memo_templates[emotion]
            for i in range(records_per_emotion):
                user_id = (i % user_count) + 1
                template_idx = i % len(templates)
                base_memo = templates[template_idx]
                
                # 약간의 변형 추가
                variations = [
                    f"{base_memo}",
                    f"{base_memo} (변형_{i})",
                    f"정말 {base_memo}",
                    f"결국 {base_memo}",
                    f"사실 {base_memo}"
                ]
                
                memo = variations[i % len(variations)]
                
                mock_data.append({
                    'username': f'user_{user_id}',
                    '메모': memo,
                    '감정태그': emotion
                })
        
        print(f"✅ Mock 데이터 생성 완료: {len(mock_data)}개 레코드")
        print(f"👥 가상 사용자: {user_count}명")
        return pd.DataFrame(mock_data)
    
    print("🔗 중앙 데이터 관리자 연결 시도 중...")
    try:
        data_manager = get_data_manager()
        all_users = data_manager.get_all_users()
        print(f"👥 총 {len(all_users)}명의 사용자 발견")
        
        all_trades = []
        for user in all_users:
            user_trades = data_manager.get_user_trades(user.username)
            if user_trades:
                for trade in user_trades:
                    trade['username'] = user.username  # 사용자 정보 추가
                all_trades.extend(user_trades)
        
        if not all_trades:
            raise ValueError("로드할 수 있는 거래 데이터가 없습니다.")
        
        df = pd.DataFrame(all_trades)
        print(f"✅ 실제 데이터 로드 완료: {len(df)}개 레코드")
        return df
        
    except Exception as e:
        print(f"❌ 중앙 데이터 로드 실패: {e}")
        print("🔄 Mock 데이터로 fallback...")
        return load_data_from_central_manager()  # Mock 데이터로 재귀 호출

def create_7_to_4_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """7클래스를 4클래스로 매핑"""
    df = df.copy()
    df['감정태그_4cls'] = df['감정태그'].map(LABEL_7TO4_MAPPING)
    
    # 매핑되지 않은 라벨 처리
    unmapped = df[df['감정태그_4cls'].isna()]
    if len(unmapped) > 0:
        print(f"⚠️ 매핑되지 않은 라벨: {unmapped['감정태그'].unique()}")
        df = df.dropna(subset=['감정태그_4cls'])
    
    return df

def compute_class_weights(labels: List[str]) -> torch.Tensor:
    """클래스 불균형 보정을 위한 가중치 계산"""
    label_counts = Counter(labels)
    total = len(labels)
    num_classes = len(label_counts)
    
    weights = []
    for i in range(num_classes):
        # sklearn의 'balanced' 전략과 동일
        weight = total / (num_classes * label_counts[list(label_counts.keys())[i]])
        weights.append(weight)
    
    return torch.FloatTensor(weights)

def create_oof_predictions(df: pd.DataFrame, class_type: str = '7cls', 
                          model_name: str = "beomi/KcELECTRA-base",
                          loss_type: str = 'weighted_ce',
                          augment_ratio: float = 1.2,
                          minority_only: bool = True,
                          demo_csv: Optional[str] = None,
                          n_folds: int = 5) -> Dict[str, Any]:
    """사용자 단위 GroupKFold로 OOF 예측 생성"""
    
    print(f"🔄 {class_type} OOF 예측 생성 시작 (GroupKFold {n_folds}-Fold)")
    
    # 라벨 컬럼 선택
    label_col = '감정태그' if class_type == '7cls' else '감정태그_4cls'
    
    # 라벨 인코딩
    label_encoder = LabelEncoder()
    df['label_encoded'] = label_encoder.fit_transform(df[label_col])
    
    label_to_id = {label: idx for idx, label in enumerate(label_encoder.classes_)}
    id_to_label = {idx: label for label, idx in label_to_id.items()}
    
    # GroupKFold 설정 (사용자 단위 분할)
    gkf = GroupKFold(n_splits=n_folds)
    groups = df['username'].values
    
    oof_predictions = np.zeros(len(df))
    oof_probabilities = np.zeros((len(df), len(label_to_id)))
    fold_scores = []
    
    # 각 Fold별 학습
    for fold, (train_idx, val_idx) in enumerate(gkf.split(df, df['label_encoded'], groups)):
        print(f"\n📊 Fold {fold + 1}/{n_folds}")
        
        train_df = df.iloc[train_idx].copy()
        val_df = df.iloc[val_idx].copy()
        
        print(f"   훈련: {len(train_df)}개 ({len(train_df['username'].unique())}명)")
        print(f"   검증: {len(val_df)}개 ({len(val_df['username'].unique())}명)")
        
        # 데이터 증강 (훈련 데이터만)
        augmenter = DemoAwareAugmentation(demo_csv)
        train_texts, train_labels = augmenter.augment_with_demo_awareness(
            train_df['메모'].tolist(),
            train_df[label_col].tolist(),
            augment_ratio=augment_ratio,
            minority_only=minority_only
        )
        
        # 증강된 라벨 인코딩
        train_labels_encoded = [label_to_id[label] for label in train_labels]
        val_labels_encoded = val_df['label_encoded'].tolist()
        
        # 모델 초기화
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=len(label_to_id),
            hidden_dropout_prob=0.2,
            attention_probs_dropout_prob=0.2
        )
        
        # 데이터셋 생성
        train_dataset = InvestmentEmotionDataset(train_texts, train_labels_encoded, tokenizer)
        val_dataset = InvestmentEmotionDataset(val_df['메모'].tolist(), val_labels_encoded, tokenizer)
        
        # 클래스 가중치 계산
        class_weights = compute_class_weights(train_labels)
        samples_per_class = [train_labels.count(label) for label in label_encoder.classes_]
        
        # 훈련 설정
        output_dir = f"./temp_fold_{fold}"
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,  # Fold별로는 짧게
            per_device_train_batch_size=8,
            per_device_eval_batch_size=16,
            warmup_ratio=0.1,
            weight_decay=0.01,
            learning_rate=2e-5,
            logging_steps=50,
            eval_strategy="no",  # Fold 내에서는 검증 없이
            save_strategy="no",
            remove_unused_columns=False,
            dataloader_num_workers=0,
            fp16=torch.cuda.is_available(),
            report_to=None,
        )
        
        # 트레이너 초기화
        trainer = CustomTrainer(
            loss_type=loss_type,
            class_weights=class_weights,
            samples_per_class=samples_per_class,
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=tokenizer,
        )
        
        # 훈련
        trainer.train()
        
        # 검증 예측
        predictions = trainer.predict(val_dataset)
        val_pred_probs = torch.softmax(torch.from_numpy(predictions.predictions), dim=-1).numpy()
        val_pred_labels = np.argmax(val_pred_probs, axis=1)
        
        # OOF 저장
        oof_predictions[val_idx] = val_pred_labels
        oof_probabilities[val_idx] = val_pred_probs
        
        # Fold 성능 계산
        fold_acc = accuracy_score(val_labels_encoded, val_pred_labels)
        fold_f1_macro = f1_score(val_labels_encoded, val_pred_labels, average='macro')
        fold_f1_weighted = f1_score(val_labels_encoded, val_pred_labels, average='weighted')
        
        fold_scores.append({
            'fold': fold + 1,
            'accuracy': fold_acc,
            'f1_macro': fold_f1_macro,
            'f1_weighted': fold_f1_weighted
        })
        
        print(f"   Fold {fold + 1} 성능: Acc={fold_acc:.4f}, F1_macro={fold_f1_macro:.4f}")
        
        # 임시 폴더 정리
        import shutil
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
    
    # 전체 OOF 성능 계산
    oof_acc = accuracy_score(df['label_encoded'], oof_predictions)
    oof_f1_macro = f1_score(df['label_encoded'], oof_predictions, average='macro')
    oof_f1_weighted = f1_score(df['label_encoded'], oof_predictions, average='weighted')
    
    print(f"\n🎯 {class_type} OOF 최종 성능:")
    print(f"   정확도: {oof_acc:.4f}")
    print(f"   F1 Macro: {oof_f1_macro:.4f}")
    print(f"   F1 Weighted: {oof_f1_weighted:.4f}")
    
    return {
        'predictions': oof_predictions,
        'probabilities': oof_probabilities,
        'fold_scores': fold_scores,
        'overall_scores': {
            'accuracy': oof_acc,
            'f1_macro': oof_f1_macro,
            'f1_weighted': oof_f1_weighted
        },
        'label_to_id': label_to_id,
        'id_to_label': id_to_label,
        'true_labels': df['label_encoded'].values
    }

def create_holdout_model(df: pd.DataFrame, class_type: str = '4cls',
                        model_name: str = "beomi/KcELECTRA-base",
                        loss_type: str = 'weighted_ce',
                        augment_ratio: float = 1.2,
                        minority_only: bool = True,
                        demo_csv: Optional[str] = None,
                        output_dir: str = "./sentiment_model") -> Dict[str, Any]:
    """시연용 4클래스 모델 생성 (Holdout 방식)"""
    
    print(f"🎯 {class_type} 시연용 모델 생성 (Holdout)")
    
    # 라벨 컬럼 선택
    label_col = '감정태그' if class_type == '7cls' else '감정태그_4cls'
    
    # 라벨 인코딩
    label_encoder = LabelEncoder()
    df['label_encoded'] = label_encoder.fit_transform(df[label_col])
    
    label_to_id = {label: idx for idx, label in enumerate(label_encoder.classes_)}
    id_to_label = {idx: label for label, idx in label_to_id.items()}
    
    # 훈련/검증 분할 (stratified)
    train_df, val_df = train_test_split(
        df, test_size=0.15, random_state=RANDOM_SEED,
        stratify=df['label_encoded']
    )
    
    print(f"📊 데이터 분할: 훈련 {len(train_df)}, 검증 {len(val_df)}")
    
    # 데이터 증강
    augmenter = DemoAwareAugmentation(demo_csv)
    train_texts, train_labels = augmenter.augment_with_demo_awareness(
        train_df['메모'].tolist(),
        train_df[label_col].tolist(),
        augment_ratio=augment_ratio,
        minority_only=minority_only
    )
    
    # 라벨 인코딩
    train_labels_encoded = [label_to_id[label] for label in train_labels]
    val_labels_encoded = val_df['label_encoded'].tolist()
    
    # 모델 초기화
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(label_to_id),
        hidden_dropout_prob=0.2,
        attention_probs_dropout_prob=0.2
    )
    
    # 데이터셋 생성
    train_dataset = InvestmentEmotionDataset(train_texts, train_labels_encoded, tokenizer)
    val_dataset = InvestmentEmotionDataset(val_df['메모'].tolist(), val_labels_encoded, tokenizer)
    
    # 클래스 가중치 계산
    class_weights = compute_class_weights(train_labels)
    samples_per_class = [train_labels.count(label) for label in label_encoder.classes_]
    
    # 훈련 설정
    model_output_dir = os.path.join(output_dir, class_type)
    os.makedirs(model_output_dir, exist_ok=True)
    
    training_args = TrainingArguments(
        output_dir=model_output_dir,
        num_train_epochs=6,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        warmup_ratio=0.1,
        weight_decay=0.01,
        learning_rate=2e-5,
        logging_steps=50,
        eval_strategy="steps",
        eval_steps=100,
        save_strategy="steps",
        save_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="f1_weighted",
        greater_is_better=True,
        save_total_limit=2,
        remove_unused_columns=False,
        dataloader_num_workers=0,
        fp16=torch.cuda.is_available(),
        gradient_accumulation_steps=2,
        label_smoothing_factor=0.05,
        report_to=None,
    )
    
    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        accuracy = accuracy_score(labels, predictions)
        f1_macro = f1_score(labels, predictions, average='macro')
        f1_weighted = f1_score(labels, predictions, average='weighted')
        
        return {
            'accuracy': accuracy,
            'f1_macro': f1_macro,
            'f1_weighted': f1_weighted
        }
    
    # 트레이너 초기화
    trainer = CustomTrainer(
        loss_type=loss_type,
        class_weights=class_weights,
        samples_per_class=samples_per_class,
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )
    
    # 훈련
    print("🏃‍♂️ 모델 훈련 시작...")
    trainer.train()
    
    # 최종 평가
    eval_results = trainer.evaluate()
    print(f"✅ 최종 성능:")
    print(f"   정확도: {eval_results['eval_accuracy']:.4f}")
    print(f"   F1 Macro: {eval_results['eval_f1_macro']:.4f}")
    print(f"   F1 Weighted: {eval_results['eval_f1_weighted']:.4f}")
    
    # 모델 저장
    trainer.save_model()
    tokenizer.save_pretrained(model_output_dir)
    
    # 모델 정보 저장
    model_info = {
        'class_type': class_type,
        'model_name': model_name,
        'loss_type': loss_type,
        'label_to_id': label_to_id,
        'id_to_label': {str(k): v for k, v in id_to_label.items()},
        'num_labels': len(label_to_id),
        'training_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'augment_ratio': augment_ratio,
        'minority_only': minority_only,
        'performance': {
            'accuracy': eval_results['eval_accuracy'],
            'f1_macro': eval_results['eval_f1_macro'],
            'f1_weighted': eval_results['eval_f1_weighted']
        },
        'data_stats': {
            'train_size': len(train_texts),
            'val_size': len(val_df),
            'original_train_size': len(train_df)
        }
    }
    
    with open(os.path.join(model_output_dir, 'model_info.json'), 'w', encoding='utf-8') as f:
        json.dump(model_info, f, ensure_ascii=False, indent=2)
    
    # 검증 예측
    val_predictions = trainer.predict(val_dataset)
    val_pred_probs = torch.softmax(torch.from_numpy(val_predictions.predictions), dim=-1).numpy()
    val_pred_labels = np.argmax(val_pred_probs, axis=1)
    
    return {
        'model': model,
        'tokenizer': tokenizer,
        'predictions': val_pred_labels,
        'probabilities': val_pred_probs,
        'true_labels': val_labels_encoded,
        'label_to_id': label_to_id,
        'id_to_label': id_to_label,
        'performance': model_info['performance'],
        'output_dir': model_output_dir
    }

def create_visualizations(results: Dict[str, Any], output_dir: str, class_type: str,
                         reject_threshold: float = 0.45):
    """성능 시각화 및 리포트 생성"""
    
    print(f"📊 {class_type} 시각화 생성 중...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 기본 변수 설정
    predictions = results['predictions']
    probabilities = results['probabilities']
    true_labels = results['true_labels']
    id_to_label = results['id_to_label']
    
    # 1. Confusion Matrix
    plt.figure(figsize=(10, 8))
    cm = confusion_matrix(true_labels, predictions)
    
    labels = [id_to_label[i] for i in range(len(id_to_label))]
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=labels, yticklabels=labels)
    plt.title(f'{class_type} Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{class_type}_confusion_matrix.png'), dpi=300)
    plt.close()
    
    # 2. 라벨별 F1 Score
    f1_scores = f1_score(true_labels, predictions, average=None)
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, f1_scores, alpha=0.7)
    plt.title(f'{class_type} F1 Scores by Label')
    plt.ylabel('F1 Score')
    plt.xticks(rotation=45)
    
    # 막대 위에 값 표시
    for bar, score in zip(bars, f1_scores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{score:.3f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{class_type}_f1_by_label.png'), dpi=300)
    plt.close()
    
    # 3. 신뢰도 분포
    max_probs = np.max(probabilities, axis=1)
    
    plt.figure(figsize=(10, 6))
    plt.hist(max_probs, bins=50, alpha=0.7, edgecolor='black')
    plt.axvline(reject_threshold, color='red', linestyle='--', 
                label=f'Reject Threshold ({reject_threshold})')
    plt.title(f'{class_type} Confidence Distribution')
    plt.xlabel('Max Probability')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{class_type}_confidence_dist.png'), dpi=300)
    plt.close()
    
    # 4. 임계값별 정확도-커버리지 곡선
    thresholds = np.arange(0.1, 1.0, 0.05)
    accuracies = []
    coverages = []
    
    for threshold in thresholds:
        # 임계값 이상의 예측만 고려
        confident_mask = max_probs >= threshold
        if np.sum(confident_mask) == 0:
            accuracies.append(0)
            coverages.append(0)
            continue
        
        confident_preds = predictions[confident_mask]
        confident_true = true_labels[confident_mask]
        
        acc = accuracy_score(confident_true, confident_preds)
        cov = np.mean(confident_mask)
        
        accuracies.append(acc)
        coverages.append(cov)
    
    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, accuracies, 'b-', label='Accuracy', linewidth=2)
    plt.plot(thresholds, coverages, 'r-', label='Coverage', linewidth=2)
    plt.axvline(reject_threshold, color='green', linestyle='--', 
                label=f'Selected Threshold ({reject_threshold})')
    
    plt.title(f'{class_type} Accuracy-Coverage Trade-off')
    plt.xlabel('Confidence Threshold')
    plt.ylabel('Score')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{class_type}_threshold_curve.png'), dpi=300)
    plt.close()
    
    # 5. 성능 메트릭 JSON 저장
    rejection_rate = np.mean(max_probs < reject_threshold)
    confident_mask = max_probs >= reject_threshold
    
    if np.sum(confident_mask) > 0:
        confident_acc = accuracy_score(true_labels[confident_mask], predictions[confident_mask])
        confident_f1 = f1_score(true_labels[confident_mask], predictions[confident_mask], average='weighted')
    else:
        confident_acc = 0.0
        confident_f1 = 0.0
    
    metrics = {
        'overall_performance': {
            'accuracy': float(accuracy_score(true_labels, predictions)),
            'f1_macro': float(f1_score(true_labels, predictions, average='macro')),
            'f1_weighted': float(f1_score(true_labels, predictions, average='weighted'))
        },
        'confidence_analysis': {
            'reject_threshold': reject_threshold,
            'rejection_rate': float(rejection_rate),
            'coverage': float(1 - rejection_rate),
            'confident_accuracy': float(confident_acc),
            'confident_f1_weighted': float(confident_f1)
        },
        'label_wise_f1': {
            id_to_label[i]: float(score) 
            for i, score in enumerate(f1_scores)
        },
        'confusion_matrix': cm.tolist()
    }
    
    with open(os.path.join(output_dir, f'{class_type}_metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {class_type} 시각화 완료: {output_dir}")
    
    return metrics

def predict_with_model(text: str, model_dir: str, reject_threshold: float = 0.45) -> Dict[str, Any]:
    """단일 텍스트 예측 (보류 기능 포함)"""
    
    # 모델 정보 로드
    with open(os.path.join(model_dir, 'model_info.json'), 'r', encoding='utf-8') as f:
        model_info = json.load(f)
    
    id_to_label = {int(k): v for k, v in model_info['id_to_label'].items()}
    
    # 모델 로드
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.eval()
    
    # 예측
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=192)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probabilities = torch.softmax(outputs.logits, dim=-1).squeeze().numpy()
        predicted_id = np.argmax(probabilities)
        max_prob = np.max(probabilities)
    
    # 보류 판단
    if max_prob < reject_threshold:
        predicted_label = "보류"
        confidence = max_prob
        all_probs = {id_to_label[i]: float(prob) for i, prob in enumerate(probabilities)}
    else:
        predicted_label = id_to_label[predicted_id]
        confidence = max_prob
        all_probs = {id_to_label[i]: float(prob) for i, prob in enumerate(probabilities)}
    
    return {
        'text': text,
        'predicted_label': predicted_label,
        'confidence': float(confidence),
        'all_probabilities': all_probs,
        'rejected': max_prob < reject_threshold,
        'reject_threshold': reject_threshold
    }

def batch_predict(csv_path: str, model_dir: str, reject_threshold: float = 0.45) -> str:
    """배치 예측 (CSV 입력/출력)"""
    
    # 입력 CSV 로드
    df = pd.read_csv(csv_path)
    if 'text' not in df.columns:
        raise ValueError("CSV 파일에 'text' 컬럼이 필요합니다.")
    
    results = []
    for _, row in df.iterrows():
        result = predict_with_model(row['text'], model_dir, reject_threshold)
        results.append(result)
    
    # 결과 DataFrame 생성
    result_df = pd.DataFrame([
        {
            'text': r['text'],
            'predicted_label': r['predicted_label'],
            'confidence': r['confidence'],
            'rejected': r['rejected']
        }
        for r in results
    ])
    
    # 출력 파일명 생성
    output_path = csv_path.replace('.csv', '_predictions.csv')
    result_df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"✅ 배치 예측 완료: {output_path}")
    print(f"   전체: {len(result_df)}개")
    print(f"   보류: {result_df['rejected'].sum()}개 ({result_df['rejected'].mean():.1%})")
    
    return output_path

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='KB Reflex 투자 심리 분석 모델 (시연용)')
    
    # 기본 옵션
    parser.add_argument('--model_name', type=str, default='beomi/KcELECTRA-base',
                       help='사용할 백본 모델 (기본: beomi/KcELECTRA-base)')
    parser.add_argument('--output_dir', type=str, default='./sentiment_model',
                       help='모델 저장 디렉토리')
    
    # 훈련 옵션
    parser.add_argument('--train_4cls', action='store_true',
                       help='4클래스 모델도 함께 훈련')
    parser.add_argument('--loss_type', type=str, default='weighted_ce',
                       choices=['weighted_ce', 'focal', 'cbloss'],
                       help='손실 함수 타입')
    parser.add_argument('--augment_ratio', type=float, default=1.2,
                       help='데이터 증강 비율 (최대 1.4 권장)')
    parser.add_argument('--minority_only', action='store_true', default=True,
                       help='소수 클래스만 증강')
    parser.add_argument('--demo_csv', type=str, default=None,
                       help='시연 후보 문장 CSV 파일 경로')
    parser.add_argument('--reject_threshold', type=float, default=0.45,
                       help='불확실성 거부 임계값 (기본: 0.45)')
    
    # 추론 옵션
    parser.add_argument('--predict', type=str, default=None,
                       help='단일 텍스트 예측')
    parser.add_argument('--batch_predict', type=str, default=None,
                       help='배치 예측 CSV 파일 경로')
    parser.add_argument('--model_path', type=str, default=None,
                       help='추론에 사용할 모델 경로')
    
    args = parser.parse_args()
    
    # 시드 고정
    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    
    # 추론 모드
    if args.predict or args.batch_predict:
        if not args.model_path:
            model_path = os.path.join(args.output_dir, '4cls')  # 기본적으로 4클래스 모델 사용
            if not os.path.exists(model_path):
                model_path = os.path.join(args.output_dir, '7cls')
        else:
            model_path = args.model_path
        
        if not os.path.exists(model_path):
            print(f"❌ 모델을 찾을 수 없습니다: {model_path}")
            return
        
        if args.predict:
            result = predict_with_model(args.predict, model_path, args.reject_threshold)
            print(f"\n🎯 예측 결과:")
            print(f"   텍스트: {result['text']}")
            print(f"   예측: {result['predicted_label']}")
            print(f"   신뢰도: {result['confidence']:.3f}")
            print(f"   보류 여부: {result['rejected']}")
            if not result['rejected']:
                print(f"   전체 확률:")
                for label, prob in sorted(result['all_probabilities'].items(), 
                                        key=lambda x: x[1], reverse=True):
                    print(f"     {label}: {prob:.3f}")
        
        if args.batch_predict:
            output_path = batch_predict(args.batch_predict, model_path, args.reject_threshold)
            print(f"✅ 배치 예측 결과: {output_path}")
        
        return
    
    # 훈련 모드
    print("🚀 KB Reflex 투자 심리 분석 모델 훈련 시작 (시연용 고도화 버전)")
    print("=" * 80)
    print(f"⚙️ 설정:")
    print(f"   모델: {args.model_name}")
    print(f"   손실함수: {args.loss_type}")
    print(f"   증강비율: {args.augment_ratio}")
    print(f"   시연CSV: {args.demo_csv}")
    print(f"   거부임계값: {args.reject_threshold}")
    print(f"   4클래스 훈련: {args.train_4cls}")
    print("=" * 80)
    
    try:
        # 1. 데이터 로드
        print("\n📊 데이터 로드 중...")
        df = load_data_from_central_manager()
        
        # 필수 컬럼 확인
        required_columns = ['메모', '감정태그']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")
        
        # username 컬럼이 없으면 생성
        if 'username' not in df.columns:
            df['username'] = 'user_' + (df.index // 10 + 1).astype(str)  # 10개씩 묶어서 사용자 할당
            print("⚠️ username 컬럼이 없어서 자동 생성했습니다.")
        
        # 데이터 정제
        initial_len = len(df)
        df = df.dropna(subset=['메모', '감정태그'])
        df = df[df['메모'].str.strip() != '']
        df = df[df['감정태그'].str.strip() != '']
        df['감정태그'] = df['감정태그'].str.replace('#', '', regex=False)
        
        print(f"📊 데이터 정제 완료: {initial_len} → {len(df)}개")
        
        # 7클래스 분포 확인
        print(f"🏷️ 7클래스 분포:")
        for emotion, count in df['감정태그'].value_counts().items():
            print(f"   {emotion}: {count}개")
        
        # 4클래스 매핑
        df = create_7_to_4_mapping(df)
        print(f"🏷️ 4클래스 분포:")
        for emotion, count in df['감정태그_4cls'].value_counts().items():
            print(f"   {emotion}: {count}개")
        
        # 2. 7클래스 OOF 평가
        print(f"\n🔄 7클래스 GroupKFold OOF 평가...")
        oof_7cls = create_oof_predictions(
            df, class_type='7cls',
            model_name=args.model_name,
            loss_type=args.loss_type,
            augment_ratio=args.augment_ratio,
            minority_only=args.minority_only,
            demo_csv=args.demo_csv
        )
        
        # 7클래스 시각화
        output_7cls = os.path.join(args.output_dir, '7cls')
        create_visualizations(oof_7cls, output_7cls, '7cls', args.reject_threshold)
        
        # 3. 4클래스 모델 훈련 (선택사항)
        if args.train_4cls:
            print(f"\n🎯 4클래스 시연용 모델 훈련...")
            
            # OOF 평가
            oof_4cls = create_oof_predictions(
                df, class_type='4cls',
                model_name=args.model_name,
                loss_type=args.loss_type,
                augment_ratio=args.augment_ratio,
                minority_only=args.minority_only,
                demo_csv=args.demo_csv
            )
            
            # Holdout 모델 생성 (실제 배포용)
            holdout_4cls = create_holdout_model(
                df, class_type='4cls',
                model_name=args.model_name,
                loss_type=args.loss_type,
                augment_ratio=args.augment_ratio,
                minority_only=args.minority_only,
                demo_csv=args.demo_csv,
                output_dir=args.output_dir
            )
            
            # 4클래스 시각화 (OOF 기준)
            output_4cls = os.path.join(args.output_dir, '4cls')
            create_visualizations(oof_4cls, output_4cls, '4cls_oof', args.reject_threshold)
            
            # Holdout 시각화
            create_visualizations(holdout_4cls, output_4cls, '4cls_holdout', args.reject_threshold)
        
        # 4. 최종 리포트
        print(f"\n🎉 훈련 완료!")
        print("=" * 80)
        print(f"📈 7클래스 OOF 성능:")
        print(f"   정확도: {oof_7cls['overall_scores']['accuracy']:.4f}")
        print(f"   F1 Macro: {oof_7cls['overall_scores']['f1_macro']:.4f}")
        print(f"   F1 Weighted: {oof_7cls['overall_scores']['f1_weighted']:.4f}")
        
        if args.train_4cls:
            print(f"📈 4클래스 OOF 성능:")
            print(f"   정확도: {oof_4cls['overall_scores']['accuracy']:.4f}")
            print(f"   F1 Macro: {oof_4cls['overall_scores']['f1_macro']:.4f}")
            print(f"   F1 Weighted: {oof_4cls['overall_scores']['f1_weighted']:.4f}")
            
            print(f"📈 4클래스 Holdout 성능:")
            print(f"   정확도: {holdout_4cls['performance']['accuracy']:.4f}")
            print(f"   F1 Macro: {holdout_4cls['performance']['f1_macro']:.4f}")
            print(f"   F1 Weighted: {holdout_4cls['performance']['f1_weighted']:.4f}")
        
        print(f"\n📁 저장 위치:")
        print(f"   7클래스: {output_7cls}")
        if args.train_4cls:
            print(f"   4클래스: {output_4cls}")
        
        print(f"\n🧪 모델 테스트:")
        if args.train_4cls:
            test_texts = [
                "코스피가 너무 떨어져서 무서워서 전량 매도했어요",
                "기술적 분석 결과 적정 매수 타이밍으로 판단됨",
                "모든 사람들이 사라고 해서 따라서 추가 매수했어요"
            ]
            
            for text in test_texts:
                result = predict_with_model(text, holdout_4cls['output_dir'], args.reject_threshold)
                print(f"📝 '{text[:30]}...'")
                print(f"🎯 예측: {result['predicted_label']} (신뢰도: {result['confidence']:.3f})")
        
        print("=" * 80)
        print("✅ 모든 과정이 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()