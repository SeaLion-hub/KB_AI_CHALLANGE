#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 유사도 기반 과거 경험 검색 엔진
과거 복기 기록에서 현재 투자 계획과 유사한 상황을 찾아 "거울 코칭" 제공
"""

from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
from typing import List, Dict, Optional


class SimilaritySearch:
    """
    유사도 기반 검색 엔진 클래스
    
    과거 복기 노트들 중에서 현재 투자 계획과 가장 유사한 경험을 찾아
    사용자에게 자신의 과거 경험을 바탕으로 한 조언을 제공합니다.
    """
    
    def __init__(self, review_notes: List[Dict], model_name: str = 'jhgan/ko-sroberta-multitask'):
        """
        유사도 검색 엔진 초기화
        
        Args:
            review_notes (List[Dict]): 과거 복기 노트들의 리스트
            model_name (str): 사용할 한국어 문장 임베딩 모델명
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"🔍 유사도 검색 엔진 초기화 중... (Device: {self.device})")
        
        try:
            # 한국어 특화 문장 임베딩 모델 로드
            self.model = SentenceTransformer(model_name, device=self.device)
            print(f"✅ 문장 임베딩 모델 로드 완료: {model_name}")
        except Exception as e:
            print(f"❌ 모델 로드 실패: {str(e)}")
            # 폴백 모델 사용
            self.model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
            print("⚠️ 영어 모델로 대체 사용 중")
        
        self.review_notes = review_notes
        
        # 과거 복기 노트들의 판단 근거 텍스트 추출
        self.corpus = []
        for note in self.review_notes:
            # 판단 근거 텍스트를 우선 사용, 없으면 감정 설명 사용
            reasoning = note.get('decision_reasoning', '')
            emotion_desc = note.get('emotion_description', '')
            
            # 두 텍스트를 결합하여 더 풍부한 컨텍스트 제공
            combined_text = f"{reasoning} {emotion_desc}".strip()
            self.corpus.append(combined_text)
        
        # 코퍼스 임베딩 사전 계산
        self.corpus_embeddings = self._encode_corpus()
        
        print(f"📚 총 {len(self.corpus)}개의 과거 경험 임베딩 완료")
    
    def _encode_corpus(self) -> torch.Tensor:
        """
        코퍼스(과거 경험들)의 임베딩을 사전 계산
        
        Returns:
            torch.Tensor: 사전 계산된 임베딩 텐서
        """
        if not self.corpus:
            return torch.tensor([], device=self.device)
        
        try:
            # 모든 과거 경험들을 벡터로 변환
            embeddings = self.model.encode(
                self.corpus, 
                convert_to_tensor=True, 
                device=self.device,
                show_progress_bar=False
            )
            return embeddings
        except Exception as e:
            print(f"❌ 임베딩 계산 실패: {str(e)}")
            return torch.tensor([], device=self.device)
    
    def find_most_similar(self, query: str, top_k: int = 1, similarity_threshold: float = 0.3) -> Optional[Dict]:
        """
        현재 투자 계획과 가장 유사한 과거 경험 찾기
        
        Args:
            query (str): 현재 투자 계획/생각
            top_k (int): 반환할 상위 결과 개수
            similarity_threshold (float): 유사도 임계값 (0.3 이하면 유사하지 않다고 판단)
        
        Returns:
            Optional[Dict]: 가장 유사한 과거 경험 또는 None
        """
        if not self.corpus or len(self.corpus_embeddings) == 0:
            print("⚠️ 검색할 과거 경험이 없습니다.")
            return None
        
        if not query.strip():
            print("⚠️ 검색 쿼리가 비어있습니다.")
            return None
        
        try:
            # 현재 쿼리를 벡터로 변환
            query_embedding = self.model.encode(
                query, 
                convert_to_tensor=True, 
                device=self.device
            )
            
            # 코사인 유사도 계산
            cos_scores = util.pytorch_cos_sim(query_embedding, self.corpus_embeddings)[0]
            
            # 상위 k개 결과 추출
            top_results = torch.topk(cos_scores, k=min(top_k, len(self.corpus)))
            
            # 가장 높은 유사도 점수 확인
            best_score = top_results[0][0].item()
            best_index = top_results[1][0].item()
            
            print(f"🎯 최고 유사도: {best_score:.3f} (임계값: {similarity_threshold})")
            
            # 임계값 이하면 유사하지 않다고 판단
            if best_score < similarity_threshold:
                print("📊 유사도가 임계값 이하입니다. 유사한 경험이 없다고 판단됩니다.")
                return None
            
            # 가장 유사한 과거 경험 반환
            best_match = self.review_notes[best_index].copy()
            best_match['similarity_score'] = best_score
            best_match['matched_text'] = self.corpus[best_index]
            
            print(f"✅ 유사한 과거 경험 발견! (유사도: {best_score:.3f})")
            
            return best_match
            
        except Exception as e:
            print(f"❌ 유사도 검색 중 오류 발생: {str(e)}")
            return None
    
    def find_multiple_similar(self, query: str, top_k: int = 3, similarity_threshold: float = 0.25) -> List[Dict]:
        """
        현재 투자 계획과 유사한 여러 과거 경험들 찾기
        
        Args:
            query (str): 현재 투자 계획/생각
            top_k (int): 반환할 상위 결과 개수
            similarity_threshold (float): 유사도 임계값
        
        Returns:
            List[Dict]: 유사한 과거 경험들의 리스트
        """
        if not self.corpus or len(self.corpus_embeddings) == 0:
            return []
        
        if not query.strip():
            return []
        
        try:
            query_embedding = self.model.encode(
                query, 
                convert_to_tensor=True, 
                device=self.device
            )
            
            cos_scores = util.pytorch_cos_sim(query_embedding, self.corpus_embeddings)[0]
            top_results = torch.topk(cos_scores, k=min(top_k, len(self.corpus)))
            
            similar_experiences = []
            
            for score, idx in zip(top_results[0], top_results[1]):
                if score.item() >= similarity_threshold:
                    experience = self.review_notes[idx.item()].copy()
                    experience['similarity_score'] = score.item()
                    experience['matched_text'] = self.corpus[idx.item()]
                    similar_experiences.append(experience)
            
            print(f"🔍 {len(similar_experiences)}개의 유사한 경험 발견")
            return similar_experiences
            
        except Exception as e:
            print(f"❌ 다중 유사도 검색 중 오류 발생: {str(e)}")
            return []
    
    def get_pattern_based_experiences(self, target_pattern: str) -> List[Dict]:
        """
        특정 AI 분석 패턴을 가진 과거 경험들 찾기
        
        Args:
            target_pattern (str): 찾고자 하는 패턴 (예: "추격매수", "공포")
        
        Returns:
            List[Dict]: 해당 패턴을 가진 과거 경험들
        """
        pattern_experiences = []
        
        for note in self.review_notes:
            ai_analysis = note.get('ai_analysis', {})
            if ai_analysis.get('pattern') == target_pattern:
                pattern_experiences.append(note)
        
        print(f"📈 '{target_pattern}' 패턴의 과거 경험 {len(pattern_experiences)}개 발견")
        return pattern_experiences
    
    def get_corpus_statistics(self) -> Dict:
        """
        검색 코퍼스의 통계 정보 반환
        
        Returns:
            Dict: 통계 정보
        """
        if not self.review_notes:
            return {'total_notes': 0, 'avg_text_length': 0, 'patterns': {}}
        
        total_notes = len(self.review_notes)
        text_lengths = [len(text) for text in self.corpus if text]
        avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        
        # 패턴별 분포
        pattern_counts = {}
        for note in self.review_notes:
            ai_analysis = note.get('ai_analysis', {})
            pattern = ai_analysis.get('pattern', '미분류')
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        return {
            'total_notes': total_notes,
            'avg_text_length': round(avg_length, 1),
            'patterns': pattern_counts,
            'device': str(self.device),
            'model_ready': len(self.corpus_embeddings) > 0
        }


# 편의성을 위한 헬퍼 함수들
def create_search_engine_from_session(session_state) -> Optional[SimilaritySearch]:
    """
    세션 상태에서 검색 엔진 생성
    
    Args:
        session_state: Streamlit 세션 상태
    
    Returns:
        Optional[SimilaritySearch]: 검색 엔진 인스턴스 또는 None
    """
    review_notes = session_state.get('review_notes', [])
    
    if not review_notes:
        return None
    
    try:
        return SimilaritySearch(review_notes)
    except Exception as e:
        print(f"❌ 검색 엔진 생성 실패: {str(e)}")
        return None


def format_similarity_result(result: Dict) -> str:
    """
    유사도 검색 결과를 사용자 친화적인 텍스트로 포맷팅
    
    Args:
        result (Dict): 검색 결과
    
    Returns:
        str: 포맷팅된 텍스트
    """
    if not result:
        return "유사한 과거 경험이 없습니다."
    
    trade = result.get('trade', {})
    ai_analysis = result.get('ai_analysis', {})
    similarity = result.get('similarity_score', 0)
    
    return f"""
    📊 유사도: {similarity:.1%}
    📅 날짜: {trade.get('거래일시', 'N/A')}
    🏢 종목: {trade.get('종목명', 'N/A')}
    📈 결과: {trade.get('수익률', 'N/A')}%
    🧠 패턴: {ai_analysis.get('pattern', 'N/A')}
    """