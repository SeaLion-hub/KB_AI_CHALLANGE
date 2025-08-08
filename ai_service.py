# ai_service.py
__all__ = [
    "check_api_key",
    "call_openai_api", 
    "find_similar_trades",
    "analyze_trade_with_ai",
    "ReMinDKoreanEngine",
    "generate_ai_coaching_tip"
]

import json
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


def check_api_key():
    """API 키 확인"""
    return hasattr(st.session_state, 'openai_api_key') and bool(st.session_state.openai_api_key)
# Import 오류 방지를 위한 try-except 구문
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    # OpenAI 없어도 경고하지 않음 (선

def call_openai_api(messages, model="gpt-3.5-turbo", temperature=0.7):
    """OpenAI API 호출 함수 (v1.0+ 호환)"""
    if not check_api_key():
        return "API 키가 설정되지 않았거나 OpenAI 라이브러리를 사용할 수 없습니다."
    
    if not OPENAI_AVAILABLE:
        return "OpenAI 라이브러리가 설치되지 않았습니다."
    
    try:
        client = OpenAI(api_key=st.session_state.openai_api_key)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

def find_similar_trades(current_trade, csv_data, similarity_threshold=0.3):
    """유사한 거래들을 모두 찾아서 반환"""
    similar_trades = []
    
    if csv_data.empty:
        return similar_trades
    
    current_stock = current_trade['종목']
    current_type = current_trade['거래유형']
    
    for _, trade in csv_data.iterrows():
        similarity_score = 0
        similarity_reasons = []
        
        # 종목명 유사도 (가중치 30%)
        if str(trade.get('종목명', '')) == current_stock:
            similarity_score += 0.3
            similarity_reasons.append(f"동일 종목 ({current_stock})")
        
        # 거래 구분 유사도 (가중치 20%)
        if str(trade.get('거래구분', '')) == current_type:
            similarity_score += 0.2
            similarity_reasons.append(f"동일 거래유형 ({current_type})")
        
        # 감정태그 유사도 (가중치 25%)
        emotion_tag = trade.get('감정태그', '')
        if emotion_tag:
            negative_emotions = ['#공포', '#패닉', '#불안', '#추격매수', '#욕심']
            if str(emotion_tag) in negative_emotions:
                similarity_score += 0.25
                similarity_reasons.append(f"감정패턴 유사 ({emotion_tag})")
        
        # 기술분석 키워드 유사도 (가중치 15%)
        tech_analysis = trade.get('기술분석', '')
        if tech_analysis:
            tech_keywords = ['과매도', '과매수', '지지선', '저항선', '돌파', '반등', '하락', '상승']
            if any(keyword in str(tech_analysis) for keyword in tech_keywords):
                similarity_score += 0.15
                similarity_reasons.append("기술적 패턴 유사")
        
        # 뉴스분석 키워드 유사도 (가중치 10%)
        news_analysis = trade.get('뉴스분석', '')
        if news_analysis:
            news_keywords = ['실적', '발표', '기대', '우려', '호재', '악재']
            if any(keyword in str(news_analysis) for keyword in news_keywords):
                similarity_score += 0.1
                similarity_reasons.append("뉴스 상황 유사")
        
        # 임계값 이상인 경우만 추가
        if similarity_score >= similarity_threshold:
            similar_trades.append({
                'trade': trade.to_dict(),
                'similarity': similarity_score,
                'reasons': similarity_reasons,
                'date': str(trade.get('거래일시', '날짜 정보 없음')),
                'result': float(trade.get('수익률', 0))
            })
    
    # 유사도 순으로 정렬
    similar_trades.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_trades

def analyze_trade_with_ai(stock_name, trade_type, quantity, price, csv_data):
    """거래를 AI로 분석하여 과거 CSV 데이터와 비교"""
    
    # 현재 거래 정보 구성
    current_trade = {
        "종목": stock_name,
        "거래유형": trade_type,
        "수량": quantity,
        "가격": price
    }
    
    # 유사한 거래들 찾기
    similar_trades = find_similar_trades(current_trade, csv_data)
    
    if not similar_trades:
        return {
            'message': '유사한 과거 거래를 찾을 수 없습니다.',
            'similar_trades': []
        }
    
    # API 키가 있으면 AI 분석도 수행
    ai_analysis = None
    if check_api_key():
        # 상위 5개 거래로 AI 분석
        top_trades = similar_trades[:5]
        trades_summary = []
        
        for similar in top_trades:
            trade = similar['trade']
            trade_summary = {
                "거래일": str(trade.get('거래일시', '날짜 정보 없음')),
                "종목": str(trade.get('종목명', '')),
                "거래구분": str(trade.get('거래구분', '')),
                "감정태그": str(trade.get('감정태그', '')),
                "수익률": float(trade.get('수익률', 0)),
                "유사도": f"{similar['similarity']*100:.1f}%"
            }
            trades_summary.append(trade_summary)
        
        messages = [
            {
                "role": "system",
                "content": """당신은 투자 심리 분석 전문 AI입니다. 현재 거래와 유사한 과거 거래들을 분석하여 간단한 조언을 해주세요."""
            },
            {
                "role": "user", 
                "content": f"""
현재 거래: {json.dumps(current_trade, ensure_ascii=False)}
유사한 과거 거래들: {json.dumps(trades_summary, ensure_ascii=False)}

위 정보를 바탕으로 간단한 투자 조언을 해주세요.
"""
            }
        ]
        
        ai_analysis = call_openai_api(messages)
    
    return {
        'similar_trades': similar_trades,
        'ai_analysis': ai_analysis
    }

class ReMinDKoreanEngine:
    """한국어 투자 심리 분석 엔진"""
    
    def __init__(self):
        # 한국 투자자 행동 패턴 정의
        self.behavioral_patterns = {
            '공포매도': ['무서워', '걱정', '패닉', '폭락', '손실', '위험', '급락', '하락', '손절'],
            '추격매수': ['상한가', '급등', '놓치기', '뒤늦게', '추격', '모두가', 'FOMO', 'fomo', '급히', '유튜버', '추천', '커뮤니티'],
            '복수매매': ['분하다', '보복', '화나다', '억울하다', '회복', '되찾기'],
            '과신매매': ['확신', '틀림없다', '쉬운돈', '확실하다', '보장', '무조건', '대박', '올인']
        }
    
    def analyze_emotion_text(self, text, user_type):
        """한국어 감정 분석 함수"""
        if not text or not isinstance(text, str):
            return {
                'pattern': '중립', 
                'confidence': 0.5, 
                'keywords': [],
                'description': '감정 패턴을 분석할 수 없습니다.'
            }
        
        text_lower = text.lower()
        
        # 키워드 매칭
        found_keywords = []
        patterns_found = {}
        
        for pattern, keywords in self.behavioral_patterns.items():
            pattern_keywords = [kw for kw in keywords if kw in text_lower]
            if pattern_keywords:
                patterns_found[pattern] = len(pattern_keywords)
                found_keywords.extend(pattern_keywords)
        
        # 가장 많이 매칭된 패턴 선택
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
        rules = []
        
        if user_data.empty:
            return rules
        
        try:
            # 감정별 성과 분석
            emotion_performance = user_data.groupby('감정태그')['수익률'].agg(['mean', 'count']).reset_index()
            emotion_performance = emotion_performance[emotion_performance['count'] >= 3]
            
            # 사용자 유형에 따라 다른 규칙 생성
            if user_type == "김국민":
                # 김국민은 공포매도 관련 규칙 추가
                fear_emotions = ['#공포', '#패닉', '#불안']
                fear_trades = emotion_performance[emotion_performance['감정태그'].isin(fear_emotions)]
                
                if not fear_trades.empty and fear_trades['mean'].mean() < -5:
                    rules.append({
                        'rule': "공포 상태(#공포, #패닉, #불안)일 때는 24시간 동안 투자 결정 보류",
                        'rationale': f"데이터 분석 결과, 공포 상태의 거래에서 평균 {abs(fear_trades['mean'].mean()):.1f}% 손실 발생",
                        'evidence': f"{int(fear_trades['count'].sum())}회 거래 분석 결과",
                        'category': '감정 관리'
                    })
            else:
                # 박투자는 추격매수 관련 규칙 추가
                chase_emotions = ['#추격매수', '#욕심']
                chase_trades = emotion_performance[emotion_performance['감정태그'].isin(chase_emotions)]
                
                if not chase_trades.empty and chase_trades['mean'].mean() < -5:
                    rules.append({
                        'rule': "급등 종목을 추격 매수하기 전에 3일간의 냉각기간 갖기",
                        'rationale': f"데이터 분석 결과, 추격매수의 평균 수익률은 {chase_trades['mean'].mean():.1f}%로 저조함",
                        'evidence': f"{int(chase_trades['count'].sum())}회 거래 분석 결과",
                        'category': '투자 전략'
                    })
            
            # 일반적인 규칙들
            for _, row in emotion_performance.iterrows():
                if row['mean'] < -8 and row['count'] >= 3:
                    emotion = str(row['감정태그']).replace('#', '')
                    rules.append({
                        'rule': f"{emotion} 상태일 때는 투자 결정을 하지 않기",
                        'rationale': f"데이터 분석 결과, {emotion} 상태의 거래에서 평균 {abs(row['mean']):.1f}% 손실 발생",
                        'evidence': f"{int(row['count'])}회 거래 분석 결과",
                        'category': '감정 관리'
                    })
        
        except Exception as e:
            st.error(f"투자 헌장 규칙 생성 중 오류 발생: {e}")
            return []
        
        return rules

    def extract_principles_from_notes(self, user_data):
        """오답노트에서 투자 원칙 추출"""
        principles = []
        
        if user_data.empty:
            return principles
        
        try:
            # 손실 거래 분석
            losing_trades = user_data[user_data['수익률'] < -10]  # 10% 이상 손실
            
            if len(losing_trades) > 0:
                # 감정별 손실 패턴 분석
                emotion_losses = losing_trades.groupby('감정태그')['수익률'].agg(['mean', 'count'])
                
                for emotion, data in emotion_losses.iterrows():
                    if data['count'] >= 2:  # 2회 이상 반복된 패턴
                        avg_loss = abs(data['mean'])
                        count = int(data['count'])
                        
                        principle = {
                            'title': f"{emotion} 감정 상태 거래 금지",
                            'description': f"{emotion} 상태에서 {count}회 거래하여 평균 {avg_loss:.1f}% 손실 발생",
                            'rule': f"{emotion} 감정이 감지되면 24시간 거래 금지",
                            'evidence_count': count,
                            'avg_impact': avg_loss
                        }
                        principles.append(principle)
            
            # 시간대별 패턴 분석 (컬럼이 존재하는 경우에만)
            if '거래일시' in user_data.columns:
                try:
                    user_data_copy = user_data.copy()
                    user_data_copy['거래시간'] = pd.to_datetime(user_data_copy['거래일시']).dt.hour
                    hourly_performance = user_data_copy.groupby('거래시간')['수익률'].mean()
                    
                    worst_hours = hourly_performance[hourly_performance < -5].index.tolist()
                    if worst_hours:
                        principle = {
                            'title': f"특정 시간대 거래 자제",
                            'description': f"{worst_hours}시 거래에서 손실률이 높음",
                            'rule': f"{worst_hours}시에는 거래 자제하고 한번 더 생각하기",
                            'evidence_count': len(worst_hours),
                            'avg_impact': abs(hourly_performance[hourly_performance < -5].mean())
                        }
                        principles.append(principle)
                except Exception:
                    # 시간대 분석에서 오류 발생 시 무시
                    pass
        
        except Exception as e:
            st.error(f"투자 원칙 추출 중 오류 발생: {e}")
            return []
        
        return principles

def generate_ai_coaching_tip(user_data, user_type):
    """오늘의 AI 코칭 팁 생성"""
    try:
        if user_data.empty:
            return "📊 거래 데이터를 축적하여 개인화된 코칭을 받아보세요."
        
        recent_trades = user_data.tail(5)
        
        # 빈 데이터프레임인 경우 처리
        if recent_trades.empty:
            return "📊 거래 데이터를 축적하여 개인화된 코칭을 받아보세요."
        
        # 감정태그가 존재하는지 확인
        if '감정태그' not in recent_trades.columns:
            return "📊 거래 데이터에 감정 정보가 없습니다. 더 자세한 데이터를 입력해주세요."
        
        recent_emotions = recent_trades['감정태그'].value_counts()
        
        # 수익률 컬럼이 존재하는지 확인
        if '수익률' in recent_trades.columns:
            avg_recent_return = recent_trades['수익률'].mean()
        else:
            avg_recent_return = 0
        
        if user_type == "김국민":
            if '#공포' in recent_emotions.index or '#패닉' in recent_emotions.index:
                return "⚠️ 최근 공포/패닉 거래가 감지되었습니다. 오늘은 시장을 관찰하고 24시간 후 재검토하세요."
            elif avg_recent_return < -5:
                return "💡 최근 수익률이 저조합니다. 감정적 판단보다는 데이터 기반 분석에 집중해보세요."
            else:
                return "✅ 최근 거래 패턴이 안정적입니다. 현재의 신중한 접근을 유지하세요."
        else:  # 박투자
            if '#추격매수' in recent_emotions.index or '#욕심' in recent_emotions.index:
                return "⚠️ 최근 추격매수 패턴이 감지되었습니다. 오늘은 FOMO를 경계하고 냉정한 판단을 하세요."
            elif avg_recent_return < -5:
                return "💡 최근 수익률이 저조합니다. 외부 추천보다는 본인만의 투자 원칙을 세워보세요."
            else:
                return "✅ 최근 거래가 개선되고 있습니다. 현재의 신중한 접근을 계속 유지하세요."
    
    except Exception as e:
        return f"💡 AI 코칭 팁 생성 중 오류가 발생했습니다: {str(e)}"