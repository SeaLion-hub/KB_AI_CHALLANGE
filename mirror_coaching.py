#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 거울 코칭 시스템 (AI Challenge 핵심 기능) - 개선 버전
과거 경험을 현재 상황과 매칭하여 "거울"처럼 반성할 수 있게 도와주는 AI 시스템

개선사항:
- SentenceTransformer 모델 캐싱 최적화
- 메모리 사용량 최적화
- 에러 처리 강화
- 설정 분리 및 확장성 개선
- 성능 모니터링 추가
"""
import streamlit as st  
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import re
from pathlib import Path
import sys
import logging
import time
from functools import lru_cache
import warnings

# 경고 메시지 억제
warnings.filterwarnings('ignore', category=FutureWarning)

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 통합된 데이터 소스 import
from db.central_data_manager import get_user_trading_history

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# [CONFIG] 설정 관리
# ================================

class MirrorCoachingConfig:
    """거울 코칭 시스템 설정 클래스"""
    
    # 모델 설정
    MODEL_NAME = 'jhgan/ko-sroberta-multitask'
    MODEL_CACHE_TTL = 3600  # 1시간
    
    # 유사도 설정
    MIN_SIMILARITY_THRESHOLD = 0.3
    DEFAULT_TOP_K = 3
    MAX_TOP_K = 10
    
    # 텍스트 처리 설정
    MAX_TEXT_LENGTH = 500
    MIN_TEXT_LENGTH = 5
    
    # 한국어 불용어
    KOREAN_STOPWORDS = {
        '그리고', '하지만', '그런데', '그래서', '그것', '이것', '저것',
        '있다', '없다', '되다', '하다', '있는', '없는', '된다', '그런',
        '이런', '저런', '그리고는', '하지만은', '그런데도'
    }
    
    # 감정 키워드 매핑
    EMOTION_KEYWORDS = {
        '공포': ['무서워', '두려워', '불안', '걱정', '패닉', '폭락', '급락'],
        '욕심': ['욕심', '더', '추가', '풀매수', '올인', '대박', '잭팟'],
        '후회': ['후회', '아쉬워', '잘못', '실수', '놓쳤', '아까워'],
        '확신': ['확신', '확실', '틀림없', '분명', '100%', '당연'],
        '냉정': ['분석', '판단', '근거', '데이터', '객관적', '이성적']
    }
    
    # 성능 모니터링
    ENABLE_PERFORMANCE_MONITORING = True
    SLOW_OPERATION_THRESHOLD = 2.0  # 2초 이상 걸리는 작업 로깅

# ================================
# [OPTIMIZED MODEL LOADING] 모델 로딩 최적화
# ================================

class ModelManager:
    """SentenceTransformer 모델 관리 클래스"""
    
    _instance = None
    _model = None
    _last_loaded = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def model(self):
        """모델 인스턴스 반환 (지연 로딩)"""
        current_time = time.time()
        
        # 모델이 없거나 캐시가 만료된 경우 로드
        if (self._model is None or 
            self._last_loaded is None or 
            current_time - self._last_loaded > MirrorCoachingConfig.MODEL_CACHE_TTL):
            
            self._load_model()
        
        return self._model
    
    def _load_model(self):
        """모델 로드"""
        try:
            start_time = time.time()
            logger.info(f"SentenceTransformer 모델 로딩 시작: {MirrorCoachingConfig.MODEL_NAME}")
            
            # SentenceTransformer 지연 import (모듈 로드 속도 개선)
            from sentence_transformers import SentenceTransformer
            
            self._model = SentenceTransformer(MirrorCoachingConfig.MODEL_NAME)
            self._last_loaded = time.time()
            
            load_time = time.time() - start_time
            logger.info(f"모델 로딩 완료 ({load_time:.2f}초)")
            
            if MirrorCoachingConfig.ENABLE_PERFORMANCE_MONITORING and load_time > MirrorCoachingConfig.SLOW_OPERATION_THRESHOLD:
                logger.warning(f"모델 로딩이 예상보다 오래 걸렸습니다: {load_time:.2f}초")
                
        except Exception as e:
            logger.error(f"모델 로딩 실패: {str(e)}")
            raise RuntimeError(f"SentenceTransformer 모델을 로드할 수 없습니다: {str(e)}")
    
    def clear_cache(self):
        """모델 캐시 클리어"""
        self._model = None
        self._last_loaded = None
        logger.info("모델 캐시가 클리어되었습니다")

# 글로벌 모델 매니저 인스턴스
model_manager = ModelManager()

@st.cache_resource
def get_sentence_transformer_model():
    """SentenceTransformer 모델을 로드하고 캐시합니다."""
    logger.info("🚀 [Cache Miss] SentenceTransformer 모델을 새로 로드합니다.")
    return model_manager.model

# ================================
# [PERFORMANCE MONITOR] 성능 모니터링
# ================================

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            
            if MirrorCoachingConfig.ENABLE_PERFORMANCE_MONITORING:
                if elapsed > MirrorCoachingConfig.SLOW_OPERATION_THRESHOLD:
                    logger.warning(f"느린 작업 감지: {self.operation_name} ({elapsed:.2f}초)")
                else:
                    logger.debug(f"작업 완료: {self.operation_name} ({elapsed:.2f}초)")

# ================================
# [ENHANCED TEXT PROCESSING] 텍스트 처리 개선
# ================================

class TextProcessor:
    """텍스트 전처리 클래스"""
    
    @staticmethod
    @lru_cache(maxsize=1000)  # 자주 사용되는 텍스트 캐싱
    def clean_text(text: str) -> str:
        """텍스트 전처리 (캐싱 적용)"""
        if not isinstance(text, str) or not text.strip():
            return ""
        
        # 길이 제한
        if len(text) > MirrorCoachingConfig.MAX_TEXT_LENGTH:
            text = text[:MirrorCoachingConfig.MAX_TEXT_LENGTH]
        
        # 기본 정제
        text = text.lower().strip()
        
        # 특수문자 제거 (한글, 영문, 숫자, 공백만 유지)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 중복 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 불용어 제거
        words = text.split()
        words = [word for word in words if word not in MirrorCoachingConfig.KOREAN_STOPWORDS]
        
        result = ' '.join(words)
        
        # 최소 길이 확인
        if len(result.strip()) < MirrorCoachingConfig.MIN_TEXT_LENGTH:
            return ""
        
        return result
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
        """키워드 추출"""
        cleaned = TextProcessor.clean_text(text)
        if not cleaned:
            return []
        
        words = cleaned.split()
        # 길이가 2 이상인 단어들을 키워드로 추출
        keywords = [word for word in words if len(word) >= 2]
        
        # 빈도수 기반 정렬 (실제로는 TF-IDF 등을 사용할 수 있음)
        from collections import Counter
        word_counts = Counter(keywords)
        
        return [word for word, count in word_counts.most_common(max_keywords)]

# ================================
# [MAIN COACHING CLASS] 메인 코칭 클래스
# ================================

class MirrorCoaching:
    """
    거울 코칭 시스템 - 개선 버전
    
    개선사항:
    1. 성능 최적화 및 메모리 효율성 개선
    2. 에러 처리 강화
    3. 캐싱 전략 개선
    4. 설정 관리 분리
    """
    
    def __init__(self):
        """초기화"""
        self.text_processor = TextProcessor()
        self._cache = {}  # 내부 캐시
        logger.info("MirrorCoaching 시스템 초기화 완료")
    
    def _convert_to_dataframe(self, trades_list: List[Dict]) -> pd.DataFrame:
        """거래 데이터 리스트를 DataFrame으로 변환 (에러 처리 강화)"""
        if not trades_list:
            return pd.DataFrame()
        
        try:
            df = pd.DataFrame(trades_list)
            
            # 날짜 컬럼 처리
            if '거래일시' in df.columns:
                df['거래일시'] = pd.to_datetime(df['거래일시'], errors='coerce')
                # 유효하지 않은 날짜 제거
                df = df.dropna(subset=['거래일시'])
            
            # 필수 컬럼 확인 및 기본값 설정
            required_columns = {
                '메모': '',
                '수익률': 0.0,
                '감정태그': '',
                '종목명': '알수없음'
            }
            
            for col, default_val in required_columns.items():
                if col not in df.columns:
                    df[col] = default_val
                else:
                    df[col] = df[col].fillna(default_val)
            
            return df
            
        except Exception as e:
            logger.error(f"DataFrame 변환 중 오류: {str(e)}")
            return pd.DataFrame()
    
    def initialize_for_user(self, username: str) -> Dict:
        """사용자 초기화 및 기본 인사이트 생성 (성능 개선)"""
        try:
            with PerformanceMonitor(f"사용자 초기화: {username}"):
                # 캐시 확인
                cache_key = f"user_init_{username}"
                if cache_key in self._cache:
                    cached_result = self._cache[cache_key]
                    if (datetime.now() - cached_result['timestamp']).seconds < 300:  # 5분 캐시
                        logger.debug(f"캐시에서 사용자 데이터 반환: {username}")
                        return cached_result['data']
                
                # 통합된 데이터 소스에서 거래 데이터 가져오기
                trades_list = get_user_trading_history(username)
                trades_data = self._convert_to_dataframe(trades_list)
                
                if trades_data.empty:
                    result = {
                        'status': 'no_data',
                        'message': f'{username}님의 거래 데이터가 없습니다.',
                        'insights': {},
                        'performance_info': {
                            'total_trades': 0,
                            'processing_time': 0
                        }
                    }
                else:
                    # 기본 패턴 분석
                    base_insights = self._analyze_base_patterns(trades_data)
                    
                    result = {
                        'status': 'initialized',
                        'message': f'{username}님의 거래 패턴 분석 완료',
                        'insights': base_insights,
                        'total_trades': len(trades_data),
                        'performance_info': {
                            'total_trades': len(trades_data),
                            'processing_time': time.time()
                        }
                    }
                
                # 결과 캐싱
                self._cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                return result
                
        except Exception as e:
            logger.error(f"사용자 초기화 중 오류: {str(e)}")
            return {
                'status': 'error',
                'message': f'초기화 중 오류: {str(e)}',
                'insights': {}
            }
    
    def find_similar_experiences(
        self, 
        current_situation: str, 
        username: str, 
        top_k: int = None
    ) -> List[Dict]:
        """
        현재 상황과 유사한 과거 경험 찾기 (성능 최적화)
        
        Args:
            current_situation: 현재 투자 상황/생각
            username: 사용자명
            top_k: 반환할 유사 경험 개수 (기본값: config에서 설정)
        
        Returns:
            유사한 과거 경험 리스트
        """
        if top_k is None:
            top_k = MirrorCoachingConfig.DEFAULT_TOP_K
        
        top_k = min(top_k, MirrorCoachingConfig.MAX_TOP_K)  # 최대값 제한
        
        try:
            with PerformanceMonitor(f"유사 경험 탐색: {username}"):
                # 입력 검증
                cleaned_current = self.text_processor.clean_text(current_situation)
                if not cleaned_current:
                    logger.warning("현재 상황 텍스트가 유효하지 않습니다")
                    return []
                
                # 통합된 데이터 소스에서 거래 데이터 가져오기
                trades_list = get_user_trading_history(username)
                trades_data = self._convert_to_dataframe(trades_list)
                
                if trades_data.empty:
                    return []
                
                # 메모 텍스트 전처리 (벡터화)
                past_memos = trades_data['메모'].astype(str).tolist()
                cleaned_memos = [self.text_processor.clean_text(memo) for memo in past_memos]
                
                # 빈 메모 필터링
                valid_indices = [i for i, memo in enumerate(cleaned_memos) if memo.strip()]
                valid_memos = [cleaned_memos[i] for i in valid_indices]
                
                if not valid_memos:
                    logger.info(f"유효한 메모가 없습니다: {username}")
                    return []
                
                # 모델 로드 및 임베딩 생성
                model = get_sentence_transformer_model()
                
                # 배치 처리로 성능 개선
                try:
                    current_embedding = model.encode([cleaned_current], show_progress_bar=False)
                    past_embeddings = model.encode(valid_memos, show_progress_bar=False)
                except Exception as e:
                    logger.error(f"임베딩 생성 중 오류: {str(e)}")
                    return []
                
                # 코사인 유사도 계산
                import sentence_transformers.util
                similarities = sentence_transformers.util.pytorch_cos_sim(
                    current_embedding, past_embeddings
                )[0]
                
                # NumPy 배열로 변환하여 정렬
                similarities_np = similarities.cpu().numpy()
                
                # 유사도 순으로 정렬하고 상위 k개 선택
                top_indices = np.argsort(similarities_np)[::-1][:top_k]
                
                similar_experiences = []
                for idx in top_indices:
                    similarity_score = float(similarities_np[idx])
                    if similarity_score > MirrorCoachingConfig.MIN_SIMILARITY_THRESHOLD:
                        original_idx = valid_indices[idx]
                        trade_info = trades_data.iloc[original_idx]
                        
                        similar_experiences.append({
                            'trade_data': trade_info.to_dict(),
                            'similarity_score': similarity_score,
                            'insight_type': self._determine_insight_type(trade_info),
                            'key_lesson': self._extract_key_lesson(trade_info),
                            'keywords': self.text_processor.extract_keywords(trade_info.get('메모', ''))
                        })
                
                logger.info(f"유사 경험 {len(similar_experiences)}개 발견: {username}")
                return similar_experiences
                
        except Exception as e:
            logger.error(f"유사 경험 탐색 중 오류: {str(e)}")
            return []
    
    def generate_hybrid_coaching(self, current_trade: dict, similar_experiences: list) -> dict:
        """
        하이브리드 데이터 주입형 코칭 메시지 생성 (개선 버전)
        """
        try:
            with PerformanceMonitor("코칭 메시지 생성"):
                # 1. 유사 경험이 없는 경우 - 개선된 기본 메시지
                if not similar_experiences:
                    return {
                        "analysis": "새로운 패턴의 거래가 감지되었습니다.",
                        "message": "이번 거래는 당신만의 투자 원칙을 만들어갈 좋은 기회입니다. 신중하게 접근해보세요.",
                        "question": "이번 결정에 가장 큰 영향을 미친 단 하나의 요인은 무엇인가요?",
                        "confidence": "low",
                        "suggestion": "거래 후 복기를 통해 패턴을 축적해보세요."
                    }
                
                # 2. 가장 유사한 과거 거래 데이터 추출
                best_match = similar_experiences[0]
                past_trade = best_match['trade_data']
                similarity_score = best_match['similarity_score']
                
                # 3. 신뢰도 기반 메시지 조정
                confidence_level = "high" if similarity_score > 0.7 else "medium" if similarity_score > 0.5 else "low"
                
                # 4. 성과 기반 템플릿 선택
                if past_trade.get('수익률', 0) >= 0:
                    # 성공 경험 기반 템플릿
                    analysis = (
                        f"현재 '{current_trade.get('종목명', '해당 종목')}'에 대한 고민은 "
                        f"과거 '{past_trade.get('종목명', 'N/A')}'에서 성공했던 경험과 "
                        f"{similarity_score:.0%} 유사합니다."
                    )
                    
                    message = (
                        f"과거 해당 거래에서 '{past_trade.get('메모', '특별한 판단')}' 라는 판단으로 "
                        f"{past_trade.get('수익률', 0):.1f}%의 수익을 얻으셨습니다. "
                        f"성공 요인을 현재 상황에 적용할 수 있을지 검토해보세요."
                    )
                    
                    question = "과거의 성공 경험과 비교했을 때, 현재 상황에서 놓치고 있는 요소는 무엇인가요?"
                    
                else:
                    # 실패 경험 기반 템플릿
                    analysis = (
                        f"현재 상황은 과거 '{past_trade.get('종목명', 'N/A')}' 거래에서 "
                        f"손실을 경험했던 상황과 {similarity_score:.0%} 유사합니다."
                    )
                    
                    message = (
                        f"과거 '{past_trade.get('메모', '당시의 판단')}' 라고 판단했던 거래는 "
                        f"{abs(past_trade.get('수익률', 0)):.1f}%의 손실로 이어졌습니다. "
                        f"같은 실수를 반복하지 않기 위해 신중한 검토가 필요합니다."
                    )
                    
                    question = "과거의 실수를 반복하지 않기 위해 지금 당장 다르게 행동해야 할 것은 무엇일까요?"
                
                # 5. 추가 인사이트 제공
                suggestion = self._generate_coaching_suggestion(similar_experiences, confidence_level)
                
                return {
                    "analysis": analysis,
                    "message": message,
                    "question": question,
                    "confidence": confidence_level,
                    "similarity_score": similarity_score,
                    "suggestion": suggestion,
                    "related_emotions": [exp['trade_data'].get('감정태그', '') for exp in similar_experiences[:3]]
                }
                
        except Exception as e:
            logger.error(f"코칭 메시지 생성 중 오류: {str(e)}")
            return {
                "analysis": "시스템 오류로 분석을 완료할 수 없습니다.",
                "message": "잠시 후 다시 시도해보세요.",
                "question": "현재 상황을 객관적으로 판단해보세요.",
                "confidence": "error"
            }
    
    def _generate_coaching_suggestion(self, similar_experiences: List[Dict], confidence_level: str) -> str:
        """코칭 제안 생성"""
        if confidence_level == "high":
            return "과거 경험과 매우 유사한 패턴입니다. 과거의 교훈을 적극 활용하세요."
        elif confidence_level == "medium":
            return "과거 경험을 참고하되, 현재 상황의 차이점도 함께 고려하세요."
        else:
            return "과거 경험이 제한적입니다. 보수적인 접근을 권장합니다."
    
    def generate_mirror_questions(
        self, 
        similar_experiences: List[Dict],
        current_situation: str,
        max_questions: int = 5
    ) -> List[str]:
        """
        거울 질문 생성 - 개선된 버전
        """
        try:
            questions = []
            
            if not similar_experiences:
                # 기본 질문 세트 (신규 사용자용)
                questions.extend([
                    "🤔 이번 투자 결정의 가장 명확한 근거는 무엇인가요?",
                    "⚖️ 이 투자의 위험과 기회를 어떻게 평가하시나요?",
                    "🎯 6개월 후의 당신에게 이 결정을 어떻게 설명하시겠나요?",
                    "💰 최악의 경우 손실을 감당할 수 있는 금액인가요?",
                    "🧭 이 거래가 당신의 투자 원칙에 부합하나요?"
                ])
                return questions[:max_questions]
            
            # 과거 경험 기반 맞춤형 질문
            success_count = sum(1 for exp in similar_experiences if exp['trade_data'].get('수익률', 0) > 0)
            failure_count = len(similar_experiences) - success_count
            
            # 성공/실패 비율에 따른 질문 조정
            for i, exp in enumerate(similar_experiences[:2]):  # 상위 2개 경험만 사용
                trade = exp['trade_data']
                similarity = exp['similarity_score']
                
                if trade.get('수익률', 0) < 0:  # 손실 경험
                    questions.append(
                        f"📉 과거 {trade.get('종목명', 'N/A')} 거래에서 "
                        f"{abs(trade.get('수익률', 0)):.1f}% 손실을 경험하셨습니다. "
                        f"그때와 지금의 가장 큰 차이점은 무엇인가요? (유사도: {similarity:.0%})"
                    )
                    
                    emotion = trade.get('감정태그', '')
                    if emotion in ['#공포', '#패닉', '#불안']:
                        questions.append(f"😰 과거 {emotion} 상태에서의 결정을 어떻게 개선할 수 있을까요?")
                        
                else:  # 수익 경험
                    questions.append(
                        f"📈 과거 {trade.get('종목명', 'N/A')} 거래에서 "
                        f"{trade.get('수익률', 0):.1f}% 수익을 내신 성공 요인을 "
                        f"이번에도 적용할 수 있을까요? (유사도: {similarity:.0%})"
                    )
            
            # 감정 패턴 기반 질문
            emotion_pattern = self._detect_dominant_emotion(similar_experiences)
            if emotion_pattern:
                questions.append(
                    f"🧠 최근 '{emotion_pattern}' 패턴이 반복되고 있습니다. "
                    f"이번엔 어떻게 다르게 접근하시겠나요?"
                )
            
            # 기본 성찰 질문 추가
            base_questions = [
                "⏰ 이 투자 결정을 24시간 후에도 같은 마음으로 할 수 있나요?",
                "📊 객관적 데이터와 주관적 느낌 중 어느 쪽에 더 의존하고 있나요?",
                "🎪 만약 이 투자가 실패한다면, 가장 큰 원인은 무엇일 것 같나요?",
                "🪞 지금의 결정을 가장 친한 친구에게도 권할 수 있나요?"
            ]
            
            # 성공/실패 비율에 따라 추가 질문 선택
            if failure_count > success_count:
                base_questions.insert(0, "🚨 과거 실패 패턴이 많이 감지됩니다. 정말 지금이 적절한 타이밍인가요?")
            
            questions.extend(base_questions)
            
            return questions[:max_questions]
            
        except Exception as e:
            logger.error(f"거울 질문 생성 중 오류: {str(e)}")
            return [
                "🤔 현재 상황을 객관적으로 판단해보세요.",
                "⚖️ 위험과 기회를 균형있게 고려하고 있나요?",
                "🎯 이 결정의 명확한 근거가 있나요?"
            ]
    
    def _detect_dominant_emotion(self, similar_experiences: List[Dict]) -> str:
        """지배적 감정 패턴 감지 (개선된 버전)"""
        if not similar_experiences:
            return ""
        
        emotions = []
        for exp in similar_experiences:
            emotion = exp['trade_data'].get('감정태그', '')
            if emotion:
                emotions.append(emotion)
        
        if not emotions:
            return ""
        
        # 빈도수 계산
        from collections import Counter
        emotion_counts = Counter(emotions)
        
        # 가장 빈번한 감정 반환 (동점일 경우 첫 번째)
        if emotion_counts:
            most_common = emotion_counts.most_common(1)[0]
            if most_common[1] >= 2:  # 최소 2번 이상 나타난 감정만
                return most_common[0]
        
        return ""
    
    def create_mirror_report(
        self, 
        username: str, 
        current_situation: str,
        similar_experiences: List[Dict] = None
    ) -> Dict:
        """종합 거울 리포트 생성 (개선된 버전)"""
        try:
            with PerformanceMonitor(f"거울 리포트 생성: {username}"):
                report = {
                    'timestamp': datetime.now(),
                    'username': username,
                    'current_situation': current_situation,
                    'mirror_analysis': {},
                    'performance_info': {}
                }
                
                # 유사 경험이 제공되지 않았다면 찾기
                if similar_experiences is None:
                    similar_experiences = self.find_similar_experiences(current_situation, username)
                
                if similar_experiences:
                    report['mirror_analysis']['similar_count'] = len(similar_experiences)
                    report['mirror_analysis']['experiences'] = similar_experiences
                    
                    # 패턴 요약
                    success_count = sum(1 for exp in similar_experiences if exp['trade_data'].get('수익률', 0) > 0)
                    failure_count = len(similar_experiences) - success_count
                    
                    report['mirror_analysis']['pattern_summary'] = {
                        'success_cases': success_count,
                        'failure_cases': failure_count,
                        'dominant_emotion': self._detect_dominant_emotion(similar_experiences),
                        'avg_similarity': np.mean([exp['similarity_score'] for exp in similar_experiences])
                    }
                    
                    # 거울 질문 생성
                    report['mirror_questions'] = self.generate_mirror_questions(
                        similar_experiences, current_situation
                    )
                    
                    # 핵심 인사이트
                    report['key_insights'] = self._generate_key_insights(similar_experiences)
                    
                    # 위험도 평가
                    report['risk_assessment'] = self._assess_risk_level(similar_experiences)
                    
                else:
                    report['mirror_analysis']['message'] = "유사한 과거 경험을 찾을 수 없습니다."
                    report['mirror_questions'] = self.generate_mirror_questions([], current_situation)
                    report['key_insights'] = ["새로운 패턴의 거래입니다. 신중한 접근을 권장합니다."]
                    report['risk_assessment'] = {'level': 'unknown', 'score': 50}
                
                # 성능 정보 추가
                report['performance_info'] = {
                    'similar_experiences_count': len(similar_experiences),
                    'processing_timestamp': datetime.now(),
                    'cache_status': 'processed'
                }
                
                return report
                
        except Exception as e:
            logger.error(f"거울 리포트 생성 중 오류: {str(e)}")
            return {
                'timestamp': datetime.now(),
                'username': username,
                'error': f"리포트 생성 중 오류: {str(e)}",
                'mirror_questions': ["현재 상황을 객관적으로 판단해보세요."]
            }
    
    def _assess_risk_level(self, similar_experiences: List[Dict]) -> Dict:
        """위험도 평가"""
        if not similar_experiences:
            return {'level': 'unknown', 'score': 50, 'reason': '과거 데이터 부족'}
        
        # 손실 거래 비율 계산
        loss_count = sum(1 for exp in similar_experiences if exp['trade_data'].get('수익률', 0) < 0)
        loss_ratio = loss_count / len(similar_experiences)
        
        # 평균 손실률 계산
        losses = [exp['trade_data'].get('수익률', 0) for exp in similar_experiences if exp['trade_data'].get('수익률', 0) < 0]
        avg_loss = np.mean(losses) if losses else 0
        
        # 위험 점수 계산 (0-100)
        risk_score = 50  # 기본값
        risk_score += loss_ratio * 30  # 손실 비율 가중치
        if avg_loss < -10:
            risk_score += 20  # 큰 손실 경험 시 추가 위험
        
        # 감정 패턴 위험도
        risky_emotions = ['#공포', '#패닉', '#욕심', '#추격매수']
        emotion_risk = sum(1 for exp in similar_experiences if exp['trade_data'].get('감정태그', '') in risky_emotions)
        risk_score += (emotion_risk / len(similar_experiences)) * 20
        
        risk_score = min(100, max(0, risk_score))
        
        # 위험 등급 결정
        if risk_score >= 80:
            level = 'very_high'
        elif risk_score >= 65:
            level = 'high'
        elif risk_score >= 35:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'level': level,
            'score': round(risk_score, 1),
            'loss_ratio': round(loss_ratio * 100, 1),
            'avg_loss': round(avg_loss, 2) if avg_loss != 0 else 0,
            'reason': f"과거 유사 상황에서 {loss_ratio:.0%}의 손실 확률"
        }
    
    # ================================
    # [HELPER METHODS] 기존 메소드들 (최적화)
    # ================================
    
    def _analyze_base_patterns(self, trades_data: pd.DataFrame) -> Dict:
        """기본 거래 패턴 분석 (메모리 최적화)"""
        try:
            patterns = {}
            
            # 데이터가 너무 적으면 간단한 분석만
            if len(trades_data) < 5:
                return {
                    'message': '분석하기에 거래 데이터가 부족합니다.',
                    'trade_count': len(trades_data)
                }
            
            # 1. 감정별 성과 분석 (상위 5개만)
            if '감정태그' in trades_data.columns and '수익률' in trades_data.columns:
                emotion_performance = trades_data.groupby('감정태그')['수익률'].agg(['mean', 'count']).round(2)
                emotion_performance = emotion_performance.nlargest(5, 'count')  # 상위 5개만
                patterns['emotion_performance'] = emotion_performance.to_dict('index')
            
            # 2. 월별 거래 패턴 (최근 12개월만)
            if '거래일시' in trades_data.columns:
                trades_data['month'] = pd.to_datetime(trades_data['거래일시']).dt.month
                monthly_pattern = trades_data.groupby('month')['수익률'].agg(['mean', 'count']).round(2)
                patterns['monthly_pattern'] = monthly_pattern.to_dict('index')
            
            # 3. 종목별 성과 (상위 10개만)
            if '종목명' in trades_data.columns:
                stock_performance = trades_data.groupby('종목명')['수익률'].agg(['mean', 'count']).round(2)
                stock_performance = stock_performance.nlargest(10, 'count')  # 상위 10개만
                patterns['stock_performance'] = stock_performance.to_dict('index')
            
            # 4. 전체 통계
            patterns['overall_stats'] = {
                'total_trades': len(trades_data),
                'win_rate': round((trades_data['수익률'] > 0).mean() * 100, 1),
                'avg_return': round(trades_data['수익률'].mean(), 2),
                'best_return': round(trades_data['수익률'].max(), 2),
                'worst_return': round(trades_data['수익률'].min(), 2)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"기본 패턴 분석 중 오류: {str(e)}")
            return {'error': f'패턴 분석 실패: {str(e)}'}
    
    def _determine_insight_type(self, trade_info: pd.Series) -> str:
        """인사이트 유형 결정"""
        try:
            return_pct = trade_info.get('수익률', 0)
            emotion = trade_info.get('감정태그', '')
            
            if return_pct > 10:
                return "success_pattern"
            elif return_pct < -10:
                return "failure_pattern" 
            elif emotion in ['#공포', '#패닉']:
                return "emotional_pattern"
            else:
                return "neutral_pattern"
        except Exception:
            return "unknown_pattern"
    
    def _extract_key_lesson(self, trade_info: pd.Series) -> str:
        """핵심 교훈 추출"""
        try:
            emotion = trade_info.get('감정태그', '')
            return_pct = trade_info.get('수익률', 0)
            
            if return_pct > 15:
                return f"성공 요인: {emotion} 상태에서도 좋은 결과"
            elif return_pct < -15:
                return f"주의 사항: {emotion} 감정이 손실로 이어짐"
            else:
                return f"평범한 결과: {emotion} 감정의 영향 분석 필요"
        except Exception:
            return "교훈 추출 실패"
    
    def _generate_key_insights(self, similar_experiences: List[Dict]) -> List[str]:
        """핵심 인사이트 생성 (개선된 버전)"""
        try:
            insights = []
            
            if not similar_experiences:
                return ["과거 유사 경험이 부족합니다. 신중한 접근을 권장합니다."]
            
            # 수익률 기반 인사이트
            returns = [exp['trade_data'].get('수익률', 0) for exp in similar_experiences]
            avg_return = np.mean(returns)
            
            if avg_return > 5:
                insights.append(f"🎯 유사한 상황에서 평균 {avg_return:.1f}%의 수익을 기록했습니다.")
            elif avg_return < -5:
                insights.append(f"⚠️ 유사한 상황에서 평균 {abs(avg_return):.1f}%의 손실이 발생했습니다.")
            else:
                insights.append("📊 유사한 상황에서 보통의 결과를 보였습니다.")
            
            # 감정 패턴 인사이트
            dominant_emotion = self._detect_dominant_emotion(similar_experiences)
            if dominant_emotion:
                insights.append(f"🧠 과거 유사 상황에서 주로 '{dominant_emotion}' 감정이 나타났습니다.")
            
            # 유사도 기반 신뢰도
            avg_similarity = np.mean([exp['similarity_score'] for exp in similar_experiences])
            if avg_similarity > 0.7:
                insights.append(f"🔍 매우 유사한 패턴입니다 (평균 유사도: {avg_similarity:.0%})")
            elif avg_similarity < 0.4:
                insights.append("⚠️ 과거 경험과의 유사도가 낮습니다. 신중한 접근이 필요합니다.")
            
            return insights[:3]  # 최대 3개까지
            
        except Exception as e:
            logger.error(f"인사이트 생성 중 오류: {str(e)}")
            return ["인사이트 생성 중 오류가 발생했습니다."]
    
    def clear_cache(self):
        """캐시 클리어"""
        self._cache.clear()
        model_manager.clear_cache()
        # LRU 캐시도 클리어
        self.text_processor.clean_text.cache_clear()
        logger.info("모든 캐시가 클리어되었습니다")
    
    def get_cache_info(self) -> Dict:
        """캐시 정보 조회"""
        return {
            'internal_cache_size': len(self._cache),
            'text_processor_cache': self.text_processor.clean_text.cache_info()._asdict(),
            'model_cache_status': 'loaded' if model_manager._model else 'not_loaded'
        }