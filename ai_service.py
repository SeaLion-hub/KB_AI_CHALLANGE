# ai_service.py
import openai
import json
import streamlit as st

# OpenAI API 설정
openai.api_key = "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"

def call_openai_api(messages, model="gpt-3.5-turbo", temperature=0.7):
    """OpenAI API 호출 함수"""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI 분석 중 오류가 발생했습니다: {str(e)}")
        return None

def analyze_trade_with_ai(stock_name, trade_type, quantity, price, csv_data):
    """거래를 AI로 분석하여 과거 CSV 데이터와 비교"""
    
    # 현재 거래 정보 구성
    current_trade = {
        "종목": stock_name,
        "거래유형": trade_type,
        "수량": quantity,
        "가격": price
    }
    
    # CSV 데이터에서 유사한 패턴 찾기 (최근 20개)
    past_trades_summary = []
    recent_trades = csv_data.tail(20)  # 최근 20개 거래
    
    for _, trade in recent_trades.iterrows():
        trade_summary = {
            "종목": trade['종목명'],
            "거래구분": trade['거래구분'],
            "감정태그": trade['감정태그'],
            "수익률": trade['수익률'],
            "메모": trade['메모'],
            "기술분석": trade['기술분석'],
            "뉴스분석": trade['뉴스분석'],
            "감정분석": trade['감정분석']
        }
        past_trades_summary.append(trade_summary)
    
    # OpenAI API 프롬프트 구성
    messages = [
        {
            "role": "system",
            "content": """당신은 투자 심리 분석 전문 AI입니다. 사용자의 현재 거래 계획을 과거 복기노트와 비교분석하여 다음 3개 분야로 분석해주세요:

1. 기술적 분석: 차트 패턴, 기술적 지표 관점
2. 뉴스/펀더멘털 분석: 시장 뉴스, 기업 실적 관점  
3. 감정 분석: 투자 심리, 감정 상태 관점

각 분야별로 가장 유사한 과거 복기노트를 찾고, 유사도(0-100%)와 유사한 이유를 제시해주세요.
응답은 JSON 형태로 해주세요."""
        },
        {
            "role": "user",
            "content": f"""
현재 거래 계획:
{json.dumps(current_trade, ensure_ascii=False, indent=2)}

과거 CSV 거래 데이터:
{json.dumps(past_trades_summary, ensure_ascii=False, indent=2)}

위 정보를 바탕으로 기술/뉴스/감정 3개 분야별 분석을 해주세요.
"""
        }
    ]
    
    response = call_openai_api(messages)
    
    if response:
        try:
            # JSON 응답 파싱 시도
            analysis_result = json.loads(response)
            return analysis_result
        except:
            # JSON 파싱 실패시 텍스트로 반환
            return {"raw_response": response}
    
    return None

class ReMinDKoreanEngine:
    """한국어 투자 심리 분석 엔진"""
    
    def __init__(self):
        # 한국 투자자 행동 패턴 정의
        self.behavioral_patterns = {
            '공포매도': ['무서워', '걱정', '패닉', '폭락', '손실', '위험', '급락', '하락', '손절'],
            '추격매수': ['상한가', '급등', '놓치기', '뒤늦게', '추격', '모두가', 'FOMO', '급히', '유튜버', '추천', '커뮤니티'],
            '복수매매': ['분하다', '보복', '화나다', '억울하다', '회복', '되찾기'],
            '과신매매': ['확신', '틀림없다', '쉬운돈', '확실하다', '보장', '무조건', '대박', '올인']
        }
    
    def analyze_emotion_text(self, text, user_type):
        """한국어 감정 분석 함수"""
        if not text:
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
                emotion = row['감정태그'].replace('#', '')
                rules.append({
                    'rule': f"{emotion} 상태일 때는 투자 결정을 하지 않기",
                    'rationale': f"데이터 분석 결과, {emotion} 상태의 거래에서 평균 {abs(row['mean']):.1f}% 손실 발생",
                    'evidence': f"{int(row['count'])}회 거래 분석 결과",
                    'category': '감정 관리'
                })
        
        return rules

def generate_ai_coaching_tip(user_data, user_type):
    """오늘의 AI 코칭 팁 생성"""
    recent_trades = user_data.tail(5)
    
    if len(recent_trades) == 0:
        return "📊 거래 데이터를 축적하여 개인화된 코칭을 받아보세요."
    
    recent_emotions = recent_trades['감정태그'].value_counts()
    avg_recent_return = recent_trades['수익률'].mean()
    
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