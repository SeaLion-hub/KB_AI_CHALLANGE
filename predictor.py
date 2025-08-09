#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 투자 심리 분석 예측 모듈
실시간 투자 심리 패턴 분류를 위한 BERT 기반 예측 엔진
"""

import os
import json
import torch
import numpy as np
from typing import Dict, Optional
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F


class SentimentPredictor:
    """
    훈련된 BERT 모델을 사용하여 투자 심리 패턴을 예측하는 클래스
    
    이 클래스는 사용자의 투자 메모 텍스트를 분석하여 다음과 같은 심리 패턴을 분류합니다:
    - 공포매도, 추격매수, 과신, 손실회피 등
    """
    
    def __init__(self, model_path: str):
        """
        예측 모델 초기화
        
        Args:
            model_path (str): 훈련된 모델이 저장된 디렉토리 경로
        """
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        print(f"🤖 KB Reflex AI 엔진 로딩 중... (Device: {self.device})")
        
        # 모델 정보 로드
        self._load_model_info()
        
        # 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # 모델 로드
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()  # 평가 모드로 설정
        
        print(f"✅ AI 엔진 로드 완료 (클래스 수: {len(self.id_to_label)})")
        
        # 각 감정 패턴에 대한 설명 정의
        self._define_pattern_descriptions()
    
    def _load_model_info(self):
        """모델 정보 및 라벨 매핑 로드"""
        model_info_path = os.path.join(self.model_path, 'model_info.json')
        
        if not os.path.exists(model_info_path):
            raise FileNotFoundError(f"모델 정보 파일을 찾을 수 없습니다: {model_info_path}")
        
        with open(model_info_path, 'r', encoding='utf-8') as f:
            model_info = json.load(f)
        
        # 문자열 키를 정수로 변환
        self.id_to_label = {int(k): v for k, v in model_info['id_to_label'].items()}
        self.label_to_id = model_info['label_to_id']
        self.num_labels = model_info['num_labels']
    
    def _define_pattern_descriptions(self):
        """각 투자 심리 패턴에 대한 설명 정의"""
        self.pattern_descriptions = {
            '공포': '시장 하락이나 손실에 대한 두려움으로 인한 급작스러운 매도 행동입니다. 감정적 결정으로 이어질 수 있어 주의가 필요합니다.',
            '추격매수': '주가 상승을 보고 기회를 놓칠까 두려워 서둘러 매수하는 FOMO(Fear of Missing Out) 심리입니다.',
            '과신': '과거의 성공 경험을 바탕으로 과도한 자신감을 보이는 패턴입니다. 위험 관리에 소홀해질 수 있습니다.',
            '손실회피': '손실을 확정하기 싫어하여 손절을 지연시키거나 피하려는 심리입니다.',
            '확증편향': '자신의 판단을 뒷받침하는 정보만 선택적으로 수집하려는 경향입니다.',
            '군중심리': '다른 투자자들의 행동을 따라하려는 경향으로, 독립적 사고가 부족할 때 나타납니다.',
            '냉정': '감정에 휘둘리지 않고 합리적으로 투자 결정을 내리는 이상적인 상태입니다.'
        }
    
    def _get_pattern_description(self, pattern: str) -> str:
        """패턴에 대한 설명 반환"""
        return self.pattern_descriptions.get(pattern, '분석된 투자 심리 패턴입니다.')
    
    def _get_confidence_level(self, confidence: float) -> str:
        """신뢰도 레벨 텍스트 반환"""
        if confidence >= 0.9:
            return "매우 높음"
        elif confidence >= 0.7:
            return "높음"
        elif confidence >= 0.5:
            return "보통"
        else:
            return "낮음"
    
    def predict(self, text: str) -> Dict:
        """
        입력 텍스트의 투자 심리 패턴 예측
        
        Args:
            text (str): 분석할 투자 메모 텍스트
            
        Returns:
            Dict: 예측 결과 딕셔너리
                - pattern (str): 예측된 심리 패턴
                - confidence (float): 예측 신뢰도 (0-1)
                - confidence_level (str): 신뢰도 레벨 ("높음", "보통", "낮음")
                - description (str): 패턴에 대한 설명
                - all_probabilities (dict): 모든 클래스별 확률
        """
        if not text or not text.strip():
            return {
                'pattern': '분석불가',
                'confidence': 0.0,
                'confidence_level': '없음',
                'description': '분석할 텍스트가 없습니다.',
                'all_probabilities': {}
            }
        
        try:
            # 텍스트 토크나이징
            inputs = self.tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=128,
                return_tensors='pt'
            )
            
            # GPU가 사용 가능한 경우 입력 텐서를 GPU로 이동
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 모델 추론
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # 소프트맥스를 적용하여 확률 계산
            probabilities = F.softmax(logits, dim=-1)
            probabilities = probabilities.cpu().numpy()[0]  # CPU로 이동 후 numpy 배열로 변환
            
            # 가장 높은 확률의 클래스 찾기
            predicted_class_id = np.argmax(probabilities)
            predicted_pattern = self.id_to_label[predicted_class_id]
            confidence = float(probabilities[predicted_class_id])
            
            # 모든 클래스별 확률 딕셔너리 생성
            all_probabilities = {
                self.id_to_label[i]: float(prob) 
                for i, prob in enumerate(probabilities)
            }
            
            # 결과 딕셔너리 생성
            result = {
                'pattern': predicted_pattern,
                'confidence': round(confidence, 3),
                'confidence_level': self._get_confidence_level(confidence),
                'description': self._get_pattern_description(predicted_pattern),
                'all_probabilities': all_probabilities
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 예측 중 오류 발생: {str(e)}")
            return {
                'pattern': '오류',
                'confidence': 0.0,
                'confidence_level': '없음',
                'description': f'분석 중 오류가 발생했습니다: {str(e)}',
                'all_probabilities': {}
            }
    
    def predict_batch(self, texts: list) -> list:
        """
        여러 텍스트를 배치로 예측
        
        Args:
            texts (list): 분석할 텍스트 리스트
            
        Returns:
            list: 각 텍스트에 대한 예측 결과 리스트
        """
        results = []
        for text in texts:
            result = self.predict(text)
            results.append(result)
        return results
    
    def get_model_info(self) -> Dict:
        """
        모델 정보 반환
        
        Returns:
            Dict: 모델 정보 딕셔너리
        """
        return {
            'model_path': self.model_path,
            'device': str(self.device),
            'num_labels': self.num_labels,
            'label_to_id': self.label_to_id,
            'id_to_label': self.id_to_label,
            'available_patterns': list(self.pattern_descriptions.keys())
        }