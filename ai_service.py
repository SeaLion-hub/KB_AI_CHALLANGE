# ai_service.py - AI 분석 엔진 (최종 정리)
"""
Re:Mind 3.1 - Gemini AI 기반 투자 심리 분석 서비스
핵심 기능: 투자자의 과거 거래 패턴을 AI가 분석하여 맞춤형 조언 제공
"""

import json
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import List, Dict, Any, Optional
import pickle
import hashlib

# === Gemini API 연동 및 기본 설정 ===
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# === API 연결 관리 함수들 ===
def check_gemini_api():
    """Gemini API 연결 상태 확인"""
    return GEMINI_AVAILABLE and hasattr(st.session_state, 'gemini_api_key') and bool(st.session_state.gemini_api_key)

def setup_gemini_api():
    """Gemini API 초기화"""
    if not GEMINI_AVAILABLE:
        return False
    if hasattr(st.session_state, 'gemini_api_key') and st.session_state.gemini_api_key:
        try:
            genai.configure(api_key=st.session_state.gemini_api_key)
            return True
        except Exception as e:
            st.error(f"Gemini API 설정 오류: {str(e)}")
            return False
    return False

def test_gemini_connection():
    """API 연결 테스트"""
    if not check_gemini_api() or not setup_gemini_api():
        return False
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("안녕하세요. 연결 테스트입니다.")
        return bool(response.text)
    except Exception as e:
        st.error(f"Gemini 연결 테스트 실패: {str(e)}")
        return False

# === 핵심 기능 1: 성공 거래 원칙 추출 ===
def get_ai_success_principle(trade_data: dict, success_note: str, user_type: str) -> dict:
    """성공 거래에서 재사용 가능한 투자 원칙을 AI가 추출"""
    if not check_gemini_api() or not setup_gemini_api():
        return {'success': False, 'message': 'Gemini API가 연결되지 않았습니다.'}
    
    try:
        # 거래 정보 요약
        trade_info = f"""
        - 종목: {trade_data.get('종목명', '')}, 거래구분: {trade_data.get('거래구분', '')}
        - 수익률: +{trade_data.get('수익률', 0):.1f}%"""
        
        # 사용자 유형별 맞춤 분석 방향 설정
        focus = "보수적 투자자의 성공 경험을 바탕으로 신중하고 안정적인 투자 원칙을" if user_type == "김국민" else "적극적 투자자의 성공 경험을 바탕으로 기회 포착과 리스크 관리를 균형 잡은 투자 원칙을"
        
        # AI 분석 요청 프롬프트
        prompt = f"""
        당신은 전문 투자 분석가입니다. {user_type} 투자자의 성공한 거래 경험을 분석하여 재사용 가능한 투자 원칙을 추출해주세요.
        {trade_info}
        사용자의 성공노트: "{success_note}"
        {focus} 다음 형식의 JSON으로 분석해주세요:
        {{
            "principle": "다른 투자에도 적용 가능한 일반화된 성공 원칙 한 문장",
            "analysis": {{
                "success_factor": "이 거래가 성공한 핵심 요인",
                "reproducibility": "이 성공 패턴의 재현 가능성 (높음/보통/낮음)",
                "insights": {{"strengths": ["잘한 점들"], "lessons": ["다른 투자에 적용할 수 있는 교훈들"]}},
                "coaching_advice": "향후 투자 조언 (3-4문장)"
            }}
        }}"""
        
        # Gemini AI 호출
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # JSON 파싱
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        analysis_result = json.loads(response_text)
        
        return {
            'success': True, 
            'principle': analysis_result.get('principle', ''), 
            'analysis': analysis_result.get('analysis', {}), 
            'raw_response': response.text
        }
    except Exception as e:
        return {'success': False, 'message': f'성공 원칙 추출 중 오류가 발생했습니다: {str(e)}'}

# === 핵심 기능 2: 유사 거래 선별 및 AI 분석 ===
# ai_service.py 파일의 gemini_select_and_analyze_trades 함수를 이 코드로 완전히 교체하세요.

def gemini_select_and_analyze_trades(current_trade: dict, user_data: pd.DataFrame, user_type: str) -> dict:
    """ [최종 수정] 데이터 준비 과정을 포함하고, 코사인 유사도로 '선택' 후 AI로 '분석'하여 오류를 해결한 함수 """
    if not check_gemini_api() or not setup_gemini_api():
        return {'method': 'error', 'analysis': 'Gemini API가 연결되지 않았습니다.'}
    if user_data.empty:
        return {'method': 'error', 'analysis': '분석할 과거 거래 데이터가 없습니다.'}

    try:
        # --- [해결책 1] AI 분석 전, 과거 거래 데이터에 임베딩을 준비하는 과정 추가 ---
        # 이 함수는 임베딩이 없으면 생성하고, 이미 있으면 그대로 사용하므로 안전합니다.
        st.info("AI 분석을 위해 과거 거래 데이터를 준비합니다...")
        processed_user_data = preprocess_embeddings_cache(user_data, user_type)
        st.info("데이터 준비 완료. 유사 거래를 분석합니다.")


        # --- 1. 선택 (Selection using Cosine Similarity) ---
        current_trade_text = generate_text_for_embedding(pd.Series(current_trade))
        # 준비된 데이터를 사용하여 유사 거래를 찾습니다.
        similar_trades_info = find_similar_experiences_ai(current_trade_text, processed_user_data, top_k=3)

        if not similar_trades_info:
            return {'method': 'error', 'analysis': '유사한 과거 거래를 찾지 못했습니다.'}

        # original_index는 preprocess_embeddings_cache를 거쳐도 유지됩니다.
        selected_indices = [trade['trade_data']['original_index'] for trade in similar_trades_info]
        selected_trades_df = processed_user_data.loc[selected_indices]

        # --- 2. 분석 (Analysis using Gemini AI) ---

        # [해결책 2] AI에게 분석을 요청하기 전, 불필요한 'embedding' 컬럼을 확실하게 제거합니다.
        selected_trades_for_analysis = selected_trades_df.copy()
        if 'embedding' in selected_trades_for_analysis.columns:
            selected_trades_for_analysis = selected_trades_for_analysis.drop(columns=['embedding'])
        
        selected_trades_json = selected_trades_for_analysis.to_json(orient='records', indent=2, force_ascii=False)

        prompt = f"""
        당신은 전문 투자 분석가입니다. {user_type} 투자자의 '현재 거래 계획'과 아래 제시된 '가장 유사한 과거 거래 3개'의 완전한 데이터를 비교 분석해주세요.

        [현재 거래 계획]
        {current_trade_text}

        [가장 유사한 과거 거래 3개 (JSON 형식)]
        {selected_trades_json}

        [분석 지시]
        제시된 3개의 유사 거래 데이터만을 바탕으로 다음 항목들을 분석하여 JSON 형식으로 응답해주세요.
        {{
            "pattern_analysis": "선택된 3개 거래의 공통적인 성공/실패 패턴 요약",
            "risk_assessment": "과거 패턴을 바탕으로 한 현재 거래의 위험도 평가 (높음/보통/낮음) 및 근거",
            "recommendation": "위험도와 패턴을 종합하여 내리는 최종 권고사항",
            "alternative_strategy": "현재 거래에 대한 대안 전략 제안"
        }}
        """
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        
        ai_analysis_json = json.loads(response_text)

        return {
            'method': 'cosine_selection_and_gemini_analysis',
            'selected_trades': selected_trades_df.to_dict(orient='records'),
            'ai_analysis': ai_analysis_json
        }
    except Exception as e:
        return {'method': 'error', 'analysis': f'AI 분석 중 오류가 발생했습니다: {str(e)}'}
# === 핵심 기능 3: 거래 복기 분석 ===
def analyze_trade_reflection(trade_data: dict, reflection_text: str, user_type: str) -> dict:
    """매수/매도 모든 거래의 복기 분석 (성공/실패 무관)"""
    if not check_gemini_api() or not setup_gemini_api():
        return {'success': False, 'message': 'Gemini API가 연결되지 않았습니다.'}
    
    try:
        # 거래 정보 요약
        trade_type = trade_data.get('거래구분', '')
        trade_info = f"""
        거래 정보:
        - 종목: {trade_data.get('종목명', '')}, 거래구분: {trade_type}
        - 수익률: {trade_data.get('수익률', 0):.1f}%"""
        
        # 사용자 유형별 분석 관점 설정
        focus = "보수적 투자 관점에서" if user_type == "김국민" else "FOMO 매수 패턴과 적극적 투자 관점에서"
        
        # AI 복기 분석 요청
        prompt = f"""
        당신은 전문 투자 심리 분석가입니다. {user_type} 투자자의 거래 복기를 분석해주세요.
        {trade_info}
        사용자의 복기 내용: "{reflection_text}"
        {focus} 다음 형식의 JSON으로 분석해주세요:
        {{
            "emotion_analysis": {{ "primary_emotion": "주요 감정", "emotion_intensity": 5, "emotion_keywords": [] }},
            "pattern_recognition": {{ "trading_pattern": "거래 패턴 분류", "confidence": 0.8, "pattern_description": "패턴 설명" }},
            "insights": {{ "strengths": ["잘한 점"], "weaknesses": ["개선점"], "lessons": ["핵심 교훈"] }},
            "ai_hashtags": ["#해시태그"],
            "coaching_advice": "개인화된 조언"
        }}"""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        analysis_result = json.loads(response_text)
        
        return {'success': True, 'analysis': analysis_result, 'raw_response': response.text}
    except Exception as e:
        return {'success': False, 'message': f'분석 중 오류가 발생했습니다: {str(e)}'}

# === 임베딩 및 유사도 계산 함수들 ===
def create_embedding(text: str) -> Optional[List[float]]:
    """텍스트를 Gemini 임베딩으로 벡터화"""
    if not check_gemini_api() or not setup_gemini_api():
        return None
    
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=[text],
            task_type="semantic_similarity"
        )
        return result['embedding'][0] if result['embedding'] else None
    except Exception as e:
        st.error(f"임베딩 생성 오류: {str(e)}")
        return None

def create_embeddings_batch(texts: List[str], batch_size: int = 100) -> Optional[List[List[float]]]:
    """텍스트 목록을 배치 처리로 임베딩 생성"""
    if not texts or not check_gemini_api() or not setup_gemini_api():
        return None
    
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=batch_texts,
                task_type="semantic_similarity"
            )
            if result and 'embedding' in result:
                all_embeddings.extend(result['embedding'])
        except Exception as e:
            st.error(f"배치 임베딩 생성 오류: {str(e)}")
            all_embeddings.extend([None] * len(batch_texts))
    
    return all_embeddings if all_embeddings else None

def generate_text_for_embedding(trade_row: pd.Series) -> str:
    """거래 데이터를 임베딩용 텍스트로 변환"""
    parts = []
    
    # 필수 정보 추출
    if '종목명' in trade_row and pd.notna(trade_row['종목명']):
        parts.append(f"종목: {trade_row['종목명']}")
    if '거래구분' in trade_row and pd.notna(trade_row['거래구분']):
        parts.append(f"거래: {trade_row['거래구분']}")
    if '감정태그' in trade_row and pd.notna(trade_row['감정태그']):
        parts.append(f"감정: {trade_row['감정태그']}")
    if '메모' in trade_row and pd.notna(trade_row['메모']):
        memo = str(trade_row['메모']).strip()
        if memo:
            parts.append(f"메모: {memo}")
    
    # 분석 정보 추가
    for col in ['기술분석', '뉴스분석', '감정분석']:
        if col in trade_row and pd.notna(trade_row[col]):
            content = str(trade_row[col]).strip()
            if content:
                parts.append(f"{col}: {content}")
    
    # 수익률 정보
    if '수익률' in trade_row and pd.notna(trade_row['수익률']):
        profit = float(trade_row['수익률'])
        if profit > 0:
            parts.append(f"수익: +{profit:.1f}%")
        elif profit < 0:
            parts.append(f"손실: {profit:.1f}%")
    
    return " | ".join(parts) if parts else "거래 정보 없음"

# ai_service.py 파일의 기존 preprocess_embeddings_cache 함수를 이 코드로 교체하세요.

@st.cache_data(ttl=3600, show_spinner=False)  # 1시간 캐시
def preprocess_embeddings_cache(user_data: pd.DataFrame, user_id: str) -> pd.DataFrame:
    """
    [Robust Version] 거래 데이터에 대한 임베딩을 미리 생성하고 캐시하며, 인덱스 정렬을 보장합니다.
    """
    if user_data.empty:
        return user_data

    # 원본 데이터프레임 수정을 피하기 위해 복사본으로 작업합니다.
    df = user_data.copy()
    # 나중에 원래 인덱스를 참조할 수 있도록 보존합니다.
    if 'original_index' not in df.columns:
        df['original_index'] = df.index

    if 'embedding' not in df.columns:
        df['embedding'] = None

    # 임베딩이 필요한 행을 찾습니다 (null이거나, 리스트가 아니거나, 빈 리스트인 경우).
    needs_embedding_mask = df['embedding'].apply(lambda x: not isinstance(x, list) or len(x) == 0)
    needs_embedding = df[needs_embedding_mask]

    if needs_embedding.empty:
        return df

    if check_gemini_api():
        progress_container = st.container()
        with progress_container:
            st.info(f"💾 AI 분석 준비 중: {len(needs_embedding)}개 거래 데이터의 임베딩을 생성합니다...")
            progress_bar = st.progress(0)
            st.session_state.embedding_progress = progress_bar

        texts_to_embed = [generate_text_for_embedding(row) for _, row in needs_embedding.iterrows()]

        embeddings = create_embeddings_batch(texts_to_embed)

        # [핵심 수정] 생성된 임베딩의 길이와 필요한 임베딩의 길이가 같은지 확인합니다.
        if embeddings and len(embeddings) == len(needs_embedding):
            # [오류 해결] 임베딩 리스트로 pandas Series를 생성합니다.
            # 이렇게 하면 새로운 데이터의 인덱스가 업데이트하려는 데이터프레임의 인덱스와 완벽하게 정렬됩니다.
            embedding_series = pd.Series(embeddings, index=needs_embedding.index)

            # Series를 'embedding' 열에 할당합니다. 이 방식이 리스트를 직접 할당하는 것보다 안전합니다.
            df.loc[needs_embedding.index, 'embedding'] = embedding_series
            progress_container.success(f"✅ {len(needs_embedding)}개 임베딩 생성 완료!")
        else:
            # create_embeddings_batch가 None을 반환하거나 길이가 다른 리스트를 반환하는 경우를 처리합니다.
            error_message = (f"❌ 임베딩 생성에 실패했습니다. API 연결을 확인하거나 일부 데이터에 문제가 있을 수 있습니다. "
                           f"(생성된 임베딩 수: {len(embeddings if embeddings else [])}, 필요한 수: {len(needs_embedding)})")
            progress_container.error(error_message)


        if 'embedding_progress' in st.session_state:
            del st.session_state.embedding_progress

    return df

def calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """두 임베딩 간의 코사인 유사도 계산"""
    try:
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        
        dot_product = np.dot(vec1, vec2.T)[0, 0]
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    except Exception:
        return 0.0

def find_similar_experiences_ai(current_situation: str, user_data: pd.DataFrame, top_k: int = 5) -> List[Dict]:
    """현재 상황과 유사한 과거 거래 경험을 AI 임베딩으로 찾기"""
    if user_data.empty or not check_gemini_api():
        return []
    
    # 현재 상황 임베딩 생성
    current_embedding = create_embedding(current_situation)
    if not current_embedding:
        return []
    
    # 유효한 임베딩이 있는 과거 거래만 필터링
    valid_trades = user_data[
        user_data['embedding'].notna() & 
        user_data['embedding'].apply(lambda x: isinstance(x, list) and len(x) > 0)
    ]
    
    if valid_trades.empty:
        return []
    
    # 유사도 계산 및 정렬
    similar_experiences = []
    for idx, trade in valid_trades.iterrows():
        trade_embedding = trade['embedding']
        similarity = calculate_cosine_similarity(current_embedding, trade_embedding)
        
        if similarity > 0.2:  # 유사도 임계값
            trade_dict = trade.to_dict()
            trade_dict['original_index'] = idx  # 원본 인덱스 보존
            
            similar_experiences.append({
                'trade_data': trade_dict,
                'similarity': similarity,
                'date': str(trade.get('거래일시', '날짜 정보 없음')),
                'result': float(trade.get('수익률', 0))
            })
    
    # 유사도 순으로 정렬하여 상위 k개 반환
    similar_experiences.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_experiences[:top_k]

# === 개인화된 코칭 및 분석 함수들 ===
def generate_personalized_coaching(current_situation: str, similar_experiences: List[Dict], user_type: str) -> str:
    """유사 경험을 바탕으로 개인화된 AI 코칭 메시지 생성"""
    if not check_gemini_api() or not setup_gemini_api():
        return "⚠️ Gemini API 키가 설정되지 않았습니다."
    
    try:
        # 유사 경험을 텍스트로 변환
        experiences_text = ""
        for i, exp in enumerate(similar_experiences[:3], 1):
            trade = exp['trade_data']
            experiences_text += f"""
            경험 {i} (유사도: {exp['similarity']*100:.1f}%):
            - 종목: {trade.get('종목명', '')}
            - 거래: {trade.get('거래구분', '')}
            - 수익률: {trade.get('수익률', 0)}%
            - 감정상태: {trade.get('감정태그', '')}
            - 당시 메모: "{trade.get('메모', '')}"
            """
        
        # 사용자 유형별 코칭 방향 설정
        if user_type == "김국민":
            persona_context = "공포매도 성향이 강한 보수적 투자자"
            coaching_focus = "감정적 판단을 피하고 데이터 기반의 냉정한 분석을 통한 투자 결정"
        else:  # 박투자
            persona_context = "FOMO(Fear of Missing Out) 성향이 강한 적극적 투자자"
            coaching_focus = "충동적 매수를 피하고 신중한 분석을 통한 투자 결정"
        
        # AI 코칭 요청
        prompt = f"""
        당신은 한국의 전문 투자 심리 코치입니다. {persona_context}인 투자자에게 조언을 제공해야 합니다.
        
        현재 투자 상황:
        {current_situation}
        
        이 투자자의 과거 유사 경험들:
        {experiences_text}
        
        위 정보를 바탕으로 다음 형식으로 조언해주세요:
        
        ## 🔍 패턴 분석
        과거 유사 거래들의 공통점과 결과를 2-3문장으로 분석
        
        ## ❓ 자기 성찰 질문
        현재 결정을 내리기 전 스스로에게 물어봐야 할 3가지 핵심 질문
        
        ## 💡 구체적 조언
        {coaching_focus}를 위한 3-4가지 실행 가능한 조언
        
        ## 🎯 24시간 액션 플랜
        오늘 당장 실행할 수 있는 1-2가지 구체적 행동
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        return f"AI 코칭 생성 중 오류가 발생했습니다: {str(e)}"

def analyze_trading_pattern_with_ai(user_data: pd.DataFrame, user_type: str) -> Dict[str, Any]:
    """전체 거래 패턴을 AI로 종합 분석"""
    if user_data.empty or not check_gemini_api():
        return {}
    
    try:
        # 거래 데이터 통계 계산
        total_trades = len(user_data)
        avg_return = user_data['수익률'].mean()
        losing_trades = user_data[user_data['수익률'] < 0]
        winning_trades = user_data[user_data['수익률'] > 0]
        emotion_distribution = user_data['감정태그'].value_counts().to_dict()
        emotion_performance = user_data.groupby('감정태그')['수익률'].agg(['mean', 'count']).round(2)
        
        # 최근 거래 패턴 분석
        recent_trades = user_data.tail(10)
        recent_context = ""
        for _, trade in recent_trades.iterrows():
            recent_context += f"""
            - {trade.get('거래일시', '')}: {trade.get('종목명', '')} ({trade.get('거래구분', '')})
              감정: {trade.get('감정태그', '')}, 수익률: {trade.get('수익률', 0)}%
              메모: "{trade.get('메모', '')}"
            """
        
        # AI 패턴 분석 요청
        prompt = f"""
        당신은 한국의 전문 투자 분석가입니다. {user_type} 투자자의 거래 패턴을 종합 분석해주세요.
        
        ## 거래 데이터 요약
        - 총 거래 횟수: {total_trades}회
        - 평균 수익률: {avg_return:.1f}%
        - 수익 거래: {len(winning_trades)}회 ({len(winning_trades)/total_trades*100:.1f}%)
        - 손실 거래: {len(losing_trades)}회 ({len(losing_trades)/total_trades*100:.1f}%)
        - 감정별 거래 분포: {emotion_distribution}
        
        ## 감정별 성과 분석
        {emotion_performance.to_string()}
        
        ## 최근 10개 거래 패턴
        {recent_context}
        
        다음 형식으로 상세 분석해주세요:
        
        ### 🎯 핵심 투자 패턴
        - 주요 강점 2가지
        - 주요 약점 2가지
        - 특이한 패턴이나 습관
        
        ### 📊 감정별 성과 분석
        - 가장 수익성이 높은 감정 상태
        - 가장 위험한 감정 상태
        - 감정 관리 개선점
        
        ### ⚠️ 위험 신호 감지
        - 거래 중단을 고려해야 하는 3가지 신호
        - 각 신호에 대한 구체적 기준
        
        ### 💎 개선 전략
        - 즉시 적용 가능한 3가지 개선책
        - 중장기 목표 2가지
        
        ### 📋 맞춤형 투자 원칙
        - 이 투자자에게 특히 중요한 3가지 규칙
        - 각 규칙의 근거
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return {
            'analysis': response.text,
            'total_trades': total_trades,
            'avg_return': avg_return,
            'win_rate': len(winning_trades)/total_trades*100,
            'loss_rate': len(losing_trades)/total_trades*100,
            'emotion_distribution': emotion_distribution,
            'emotion_performance': emotion_performance.to_dict()
        }
        
    except Exception as e:
        return {'error': f"패턴 분석 중 오류: {str(e)}"}

def generate_investment_charter(user_data: pd.DataFrame, user_type: str) -> str:
    """개인화된 투자 헌장 생성"""
    if user_data.empty or not check_gemini_api():
        return "투자 헌장을 생성하기 위해서는 충분한 거래 데이터와 Gemini API가 필요합니다."
    
    try:
        pattern_analysis = analyze_trading_pattern_with_ai(user_data, user_type)
        if 'error' in pattern_analysis:
            return f"헌장 생성 중 오류: {pattern_analysis['error']}"
        
        # 손실이 큰 감정 패턴 식별
        losing_emotions = user_data[user_data['수익률'] < -5].groupby('감정태그')['수익률'].agg(['mean', 'count'])
        
        prompt = f"""
        당신은 투자 헌장 작성 전문가입니다. {user_type} 투자자를 위한 개인화된 투자 헌장을 작성해주세요.
        
        투자자 프로필:
        - 총 거래: {pattern_analysis.get('total_trades', 0)}회
        - 평균 수익률: {pattern_analysis.get('avg_return', 0):.1f}%
        - 승률: {pattern_analysis.get('win_rate', 0):.1f}%
        
        주요 위험 감정:
        {losing_emotions.to_string() if not losing_emotions.empty else "특별한 위험 패턴 없음"}
        
        다음 형식으로 투자 헌장을 작성해주세요:
        
        # 📜 {user_type}님의 개인 투자 헌장
        
        ## 🎯 투자 철학
        나의 투자 스타일과 목표를 명확히 선언
        
        ## ⚖️ 핵심 원칙 (5가지)
        1. 감정 관리 원칙
        2. 리스크 관리 원칙  
        3. 거래 실행 원칙
        4. 정보 수집 원칙
        5. 성과 평가 원칙
        
        ## 🚫 절대 금지 사항 (3가지)
        이 투자자가 절대 하지 말아야 할 행동들
        
        ## ⏰ 거래 중단 기준
        언제 투자를 멈추고 냉정해야 하는지
        
        ## 📊 정기 점검 계획
        언제, 어떻게 이 헌장을 검토할 것인지
        
        ## ✍️ 서명
        작성일: {datetime.now().strftime('%Y년 %m월 %d일')}
        투자자: {user_type}
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        return f"투자 헌장 생성 중 오류: {str(e)}"

def analyze_trading_psychology(user_input: str, user_data: pd.DataFrame, user_type: str) -> str:
    """현재 거래 심리 상태 분석"""
    if not check_gemini_api():
        return "심리 분석을 위해 Gemini API가 필요합니다."
    
    try:
        # 최근 거래 패턴 분석
        recent_emotions = user_data.tail(10)['감정태그'].value_counts().to_dict() if not user_data.empty else {}
        recent_returns = user_data.tail(5)['수익률'].tolist() if not user_data.empty else []
        
        prompt = f"""
        당신은 투자 심리 전문가입니다. {user_type} 투자자의 현재 심리 상태를 분석해주세요.
        
        투자자의 현재 생각/고민:
        "{user_input}"
        
        최근 거래에서의 감정 패턴:
        {recent_emotions}
        
        최근 5회 거래 수익률:
        {recent_returns}
        
        다음 형식으로 분석해주세요:
        
        ## 🧠 현재 심리 상태 진단
        - 주요 감정: (불안/욕심/공포/자신감 등)
        - 위험도: (낮음/보통/높음/매우높음)
        - 판단력 상태: 분석
        
        ## 🔍 심리적 편향 체크
        - 인지편향 여부 (확증편향, 손실회피편향 등)
        - 감정적 의사결정 위험도
        
        ## 💊 처방전
        - 즉시 실행할 멘탈 관리법 2가지
        - 24시간 내 피해야 할 행동 3가지
        - 장기적 심리 훈련 방법 1가지
        
        ## 🎯 다음 거래 권장사항
        현재 심리 상태를 고려한 구체적 행동 지침
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        return f"심리 분석 중 오류: {str(e)}"

# === 기존 거래 분석 함수들 (하위 호환성 유지) ===
def find_similar_trades(current_trade, csv_data, similarity_threshold=0.3):
    """기존 유사 거래 찾기 함수 (임베딩 우선, 키워드 매칭 폴백)"""
    if csv_data.empty:
        return []
    
    # 임베딩 기반 분석 시도
    if 'embedding' in csv_data.columns and check_gemini_api():
        current_situation = f"""
        종목: {current_trade.get('종목', '')}
        거래구분: {current_trade.get('거래유형', '')}
        수량: {current_trade.get('수량', '')}주
        가격: {current_trade.get('가격', '')}원
        """
        
        similar_experiences = find_similar_experiences_ai(current_situation, csv_data, top_k=5)
        if similar_experiences:
            return similar_experiences
    
    # 기본 키워드 매칭 방식 (폴백)
    similar_trades = []
    current_stock = current_trade.get('종목', '')
    current_type = current_trade.get('거래유형', '')
    
    for _, trade in csv_data.iterrows():
        similarity_score = 0
        similarity_reasons = []
        
        # 종목명 유사도
        if str(trade.get('종목명', '')) == current_stock:
            similarity_score += 0.4
            similarity_reasons.append(f"동일 종목 ({current_stock})")
        
        # 거래 구분 유사도
        if str(trade.get('거래구분', '')) == current_type:
            similarity_score += 0.3
            similarity_reasons.append(f"동일 거래유형 ({current_type})")
        
        # 감정 패턴 유사도
        emotion_tag = trade.get('감정태그', '')
        if emotion_tag and any(keyword in emotion_tag for keyword in ['#공포', '#패닉', '#추격매수', '#욕심']):
            similarity_score += 0.3
            similarity_reasons.append(f"위험 감정패턴 ({emotion_tag})")
        
        if similarity_score >= similarity_threshold:
            similar_trades.append({
                'trade_data': trade.to_dict(),
                'similarity': similarity_score,
                'reasons': similarity_reasons,
                'date': str(trade.get('거래일시', '날짜 정보 없음')),
                'result': float(trade.get('수익률', 0))
            })
    
    similar_trades.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_trades[:5]

def analyze_trade_with_ai(stock_name, trade_type, quantity, price, csv_data):
    """통합 거래 분석 함수 (임베딩 우선, 기본 분석 폴백)"""
    current_trade = {
        "종목": stock_name,
        "거래유형": trade_type,
        "수량": quantity,
        "가격": price
    }
    
    current_situation = f"""
    종목: {stock_name}
    거래구분: {trade_type}
    수량: {quantity}주
    가격: {price:,}원
    """
    
    # 임베딩 기반 빠른 분석
    if 'embedding' in csv_data.columns and check_gemini_api():
        similar_trades = find_similar_experiences_ai(current_situation, csv_data)
        if similar_trades:
            ai_analysis = generate_personalized_coaching(
                current_situation, 
                similar_trades, 
                st.session_state.get('current_user', '김국민')
            )
            return {
                'similar_trades': similar_trades,
                'ai_analysis': ai_analysis,
                'method': 'optimized_gemini_ai'
            }
    
    # 기본 방식 (폴백)
    similar_trades = find_similar_trades(current_trade, csv_data)
    
    return {
        'similar_trades': similar_trades,
        'ai_analysis': "임베딩 데이터를 준비하면 더 정확한 AI 분석을 받을 수 있습니다.",
        'method': 'basic'
    }

# === 투자 심리 분석 엔진 클래스 ===
class ReMinDKoreanEngine:
    """한국어 투자 심리 분석 엔진 (Gemini 기반)"""
    
    def __init__(self):
        # 행동 패턴 키워드 정의
        self.behavioral_patterns = {
            '공포매도': ['무서워', '걱정', '패닉', '폭락', '손실', '위험', '급락', '하락', '손절'],
            '추격매수': ['상한가', '급등', '놓치기', '뒤늦게', '추격', '모두가', 'FOMO', 'fomo', '급히', '유튜버', '추천', '커뮤니티'],
            '복수매매': ['분하다', '보복', '화나다', '억울하다', '회복', '되찾기'],
            '과신매매': ['확신', '틀림없다', '쉬운돈', '확실하다', '보장', '무조건', '대박', '올인']
        }
        self._emotion_cache = {}  # 감정 분석 캐시
    
    def analyze_emotion_text_batch(self, texts: List[str], user_type: str) -> List[Dict]:
        """배치 단위 감정 분석"""
        if not texts:
            return []
        
        results = []
        
        # Gemini 배치 분석 시도 (5개 이상일 때)
        if check_gemini_api() and len(texts) > 5:
            try:
                batch_prompt = f"""
                다음 {len(texts)}개의 텍스트들에서 각각의 투자 감정 패턴을 분석해주세요.
                """
                
                for i, text in enumerate(texts, 1):
                    batch_prompt += f"{i}. {text}\n"
                
                batch_prompt += """
                각 텍스트에 대해 다음 JSON 형식으로 결과를 배열로 반환해주세요:
                [
                    {
                        "id": 1,
                        "pattern": "공포매도/추격매수/복수매매/과신매매/합리적투자 중 하나",
                        "confidence": 0.0~1.0 사이 값,
                        "keywords": ["감지된", "키워드"],
                        "description": "패턴 설명"
                    }
                ]
                """
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(batch_prompt)
                
                try:
                    batch_results = json.loads(response.text)
                    if isinstance(batch_results, list) and len(batch_results) == len(texts):
                        return batch_results
                except:
                    pass
                    
            except Exception as e:
                st.warning(f"배치 감정 분석 오류: {e}")
        
        # 개별 처리 (폴백)
        for text in texts:
            results.append(self.analyze_emotion_text(text, user_type))
        
        return results
    
    def analyze_emotion_text(self, text, user_type):
        """단일 텍스트 감정 분석 (캐시 적용)"""
        if not text or not isinstance(text, str):
            return {
                'pattern': '중립', 
                'confidence': 0.5, 
                'keywords': [],
                'description': '감정 패턴을 분석할 수 없습니다.'
            }
        
        # 캐시 확인
        cache_key = hashlib.md5(f"{text}_{user_type}".encode()).hexdigest()
        if cache_key in self._emotion_cache:
            return self._emotion_cache[cache_key]
        
        result = self._analyze_emotion_internal(text, user_type)
        
        # 캐시 저장 (최대 1000개)
        if len(self._emotion_cache) < 1000:
            self._emotion_cache[cache_key] = result
        
        return result
    
    def _analyze_emotion_internal(self, text, user_type):
        """내부 감정 분석 로직 (Gemini 우선, 키워드 분석 폴백)"""
        # Gemini 분석 시도
        if check_gemini_api():
            try:
                prompt = f"""
                다음 텍스트에서 투자 감정 패턴을 분석해주세요:
                "{text}"
                
                분석 결과를 다음 JSON 형식으로 반환해주세요:
                {{
                    "pattern": "공포매도/추격매수/복수매매/과신매매/합리적투자 중 하나",
                    "confidence": 0.0~1.0 사이 값,
                    "keywords": ["감지된", "키워드", "목록"],
                    "description": "패턴에 대한 설명"
                }}
                """
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                try:
                    result = json.loads(response.text)
                    return result
                except:
                    pass
            except Exception:
                pass
        
        # 기본 키워드 분석 (폴백)
        text_lower = text.lower()
        found_keywords = []
        patterns_found = {}
        
        for pattern, keywords in self.behavioral_patterns.items():
            pattern_keywords = [kw for kw in keywords if kw in text_lower]
            if pattern_keywords:
                patterns_found[pattern] = len(pattern_keywords)
                found_keywords.extend(pattern_keywords)
        
        if patterns_found:
            dominant_pattern = max(patterns_found, key=patterns_found.get)
            confidence = min(0.9, 0.6 + (patterns_found[dominant_pattern] * 0.1))
            
            descriptions = {
                '공포매도': '시장 하락에 대한 두려움으로 인한 패닉 매도 패턴',
                '추격매수': 'FOMO(Fear of Missing Out)에 의한 고점 매수 패턴',
                '복수매매': '손실 회복을 위한 감정적 복수 거래 패턴',
                '과신매매': '과도한 자신감으로 인한 무리한 투자 패턴'
            }
            
            return {
                'pattern': dominant_pattern,
                'confidence': confidence,
                'keywords': found_keywords[:3],
                'description': descriptions.get(dominant_pattern, '알 수 없는 패턴')
            }
        
        return {
            'pattern': '합리적투자',
            'confidence': 0.60,
            'keywords': [],
            'description': '데이터 기반의 합리적 투자 패턴'
        }
    
    def generate_investment_charter_rules(self, user_data, user_type):
        """개인화된 투자 헌장 규칙 생성"""
        if user_data.empty:
            return []
        
        rules = []
        
        # 감정별 수익률 분석으로 규칙 생성
        if '감정태그' in user_data.columns and '수익률' in user_data.columns:
            emotion_performance = user_data.groupby('감정태그')['수익률'].mean()
            
            # 손실이 큰 감정 패턴에 대한 규칙 생성
            for emotion, avg_return in emotion_performance.items():
                if avg_return < -5:  # 평균 -5% 이하인 경우
                    if emotion in ['#공포', '#패닉']:
                        rules.append({
                            'rule': f'{emotion} 상태일 때는 24시간 거래 금지',
                            'rationale': f'과거 데이터상 {emotion} 상태에서 평균 {avg_return:.1f}% 손실',
                            'evidence': f'{len(user_data[user_data["감정태그"] == emotion])}회 거래 분석',
                            'category': '감정 관리'
                        })
                    elif emotion in ['#추격매수', '#욕심']:
                        rules.append({
                            'rule': '급등주 추격매수 시 투자금액을 10만원 이하로 제한',
                            'rationale': f'추격매수에서 평균 {avg_return:.1f}% 손실 발생',
                            'evidence': f'{len(user_data[user_data["감정태그"] == emotion])}회 거래 분석',
                            'category': 'FOMO 방지'
                        })
        
        return rules[:5]  # 최대 5개 규칙
    
    def extract_principles_from_notes(self, user_data):
        """복기노트에서 투자 원칙 추출"""
        if user_data.empty or '메모' not in user_data.columns:
            return []
        
        principles = []
        
        # 손실 거래 분석
        losing_trades = user_data[user_data['수익률'] < 0]
        
        if len(losing_trades) > 5:
            # 감정별 손실 패턴 분석
            emotion_losses = losing_trades.groupby('감정태그').agg({
                '수익률': ['mean', 'count']
            }).round(2)
            
            for emotion in emotion_losses.index:
                avg_loss = emotion_losses.loc[emotion, ('수익률', 'mean')]
                count = emotion_losses.loc[emotion, ('수익률', 'count')]
                
                if count >= 3 and avg_loss < -5:
                    principles.append({
                        'title': f'{emotion} 상태에서의 거래 제한',
                        'description': f'과거 {count}회 거래에서 평균 {avg_loss:.1f}% 손실 발생',
                        'rule': f'{emotion} 감정 상태일 때는 투자 결정을 24시간 연기한다',
                        'evidence_count': int(count),
                        'avg_impact': abs(avg_loss)
                    })
        
        # 종목별 패턴 분석
        if '종목명' in user_data.columns:
            stock_losses = losing_trades.groupby('종목명').agg({
                '수익률': ['mean', 'count']
            }).round(2)
            
            for stock in stock_losses.index:
                avg_loss = stock_losses.loc[stock, ('수익률', 'mean')]
                count = stock_losses.loc[stock, ('수익률', 'count')]
                
                if count >= 3 and avg_loss < -10:
                    principles.append({
                        'title': f'{stock} 종목 거래 주의',
                        'description': f'{stock}에서 {count}회 거래로 평균 {avg_loss:.1f}% 손실',
                        'rule': f'{stock} 거래 시 투자금액을 평소의 50%로 제한한다',
                        'evidence_count': int(count),
                        'avg_impact': abs(avg_loss)
                    })
        
        # 기본 원칙들 추가 (데이터 부족 시)
        if len(principles) < 3:
            principles.extend([
                {
                    'title': '거래 시간대 제한',
                    'description': '충동적 거래를 방지하기 위한 시간 관리',
                    'rule': '시장 개장 첫 30분과 마감 30분에는 거래하지 않는다',
                    'evidence_count': 0,
                    'avg_impact': 0
                },
                {
                    'title': '분할 매수 원칙',
                    'description': '리스크 분산을 위한 투자 전략',
                    'rule': '한 번에 전체 투자 예정 금액의 30%를 초과하여 매수하지 않는다',
                    'evidence_count': 0,
                    'avg_impact': 0
                }
            ])
        
        return principles[:5]

# === 유틸리티 함수들 ===
def generate_ai_coaching_tip(user_data, user_type):
    """일일 AI 코칭 팁 생성"""
    try:
        if user_data.empty:
            return "📊 거래 데이터를 축적하여 개인화된 AI 코칭을 받아보세요."
        
        # 임베딩 기반 빠른 패턴 분석
        if 'embedding' in user_data.columns and check_gemini_api():
            recent_trades = user_data.tail(10)
            recent_emotions = recent_trades['감정태그'].value_counts().to_dict()
            recent_returns = recent_trades['수익률'].tolist()
            avg_recent_return = recent_trades['수익률'].mean()
            
            total_trades = len(user_data)
            overall_return = user_data['수익률'].mean()
            win_rate = len(user_data[user_data['수익률'] > 0]) / len(user_data) * 100
            
            prompt = f"""
            당신은 {user_type} 투자자의 전담 AI 코치입니다. 오늘의 핵심 투자 조언을 간결하게 제공해주세요.
            
            투자자 현황:
            - 총 거래: {total_trades}회
            - 전체 평균 수익률: {overall_return:.1f}%
            - 승률: {win_rate:.1f}%
            - 최근 10회 거래 평균: {avg_recent_return:.1f}%
            
            최근 감정 패턴: {recent_emotions}
            최근 수익률 추이: {recent_returns}
            
            다음 형식으로 오늘의 핵심 조언 1개를 제공해주세요:
            🎯 [오늘의 핵심 메시지 - 한 문장]
            📊 [데이터 근거 - 간단히]
            💡 [구체적 행동 지침 - 실행 가능한 내용]
            
            답변은 50자 이내의 간결하고 임팩트 있는 메시지로 작성해주세요.
            """
            
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                st.warning(f"Gemini 코칭 생성 오류: {e}")
        
        # 기본 로직 (폴백)
        recent_trades = user_data.tail(5)
        if recent_trades.empty:
            return "📊 거래 데이터를 축적하여 개인화된 코칭을 받아보세요."
        
        if '감정태그' not in recent_trades.columns:
            return "📊 거래 데이터에 감정 정보가 없습니다."
        
        recent_emotions = recent_trades['감정태그'].value_counts()
        avg_recent_return = recent_trades['수익률'].mean() if '수익률' in recent_trades.columns else 0
        
        # 사용자 유형별 맞춤 조언
        if user_type == "김국민":
            if '#공포' in recent_emotions.index or '#패닉' in recent_emotions.index:
                return "⚠️ 최근 공포/패닉 거래가 감지되었습니다. 오늘은 시장을 관찰하고 24시간 후 재검토하세요."
            elif avg_recent_return < -5:
                return "💡 최근 수익률이 저조합니다. 감정적 판단보다는 데이터 기반 분석에 집중해보세요."
            else:
                return "✅ 최근 거래 패턴이 안정적입니다. 현재의 신중한 접근을 유지하세요."
        else:  # 박투자
            if '#추격매수' in recent_emotions.index or '#욕심' in recent_emotions.index:
                return "⚠️ 최근 FOMO 거래가 감지되었습니다. 오늘은 충동을 억제하고 냉정한 판단을 하세요."
            elif avg_recent_return < -5:
                return "💡 최근 수익률이 저조합니다. 외부 추천보다는 본인만의 투자 원칙을 세워보세요."
            else:
                return "✅ 최근 거래가 개선되고 있습니다. 현재의 신중한 접근을 계속 유지하세요."
    
    except Exception as e:
        return f"💡 AI 코칭 팁 생성 중 오류가 발생했습니다: {str(e)}"

# === 하위 호환성을 위한 더미 함수들 ===
def check_api_key():
    """하위 호환성을 위한 함수"""
    return check_gemini_api()

def call_openai_api(prompt, user_type="김국민"):
    """더미 함수 - 사용하지 않음"""
    return "이 기능은 Gemini API를 사용합니다. check_gemini_api()를 확인해주세요."

def get_performance_metrics() -> Dict[str, Any]:
    """시스템 성능 메트릭 반환"""
    metrics = {
        'gemini_available': GEMINI_AVAILABLE,
        'sklearn_available': SKLEARN_AVAILABLE,
        'api_configured': check_gemini_api(),
        'cache_size': len(getattr(ReMinDKoreanEngine(), '_emotion_cache', {})),
        'embedding_model': 'text-embedding-004'
    }
    return metrics