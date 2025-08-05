import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="Re:Mind 2.0 - AI 투자 심리 분석",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 모던한 현대미술 스타일 CSS
st.markdown("""
<style>
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --secondary: #8b5cf6;
        --accent: #ec4899;
        --dark: #1e293b;
        --darker: #0f172a;
        --light: #f1f5f9;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --card-bg: rgba(30, 41, 59, 0.7);
        --card-border: rgba(255, 255, 255, 0.1);
    }
    
    * {
        font-family: 'Noto Sans KR', 'Inter', sans-serif;
    }
    
    body {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: #f1f5f9;
        background-attachment: fixed;
    }
    
    .stApp {
        background: transparent !important;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ec4899, #8b5cf6);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 1.5rem 0 0.5rem;
        letter-spacing: -0.5px;
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }
    
    .sub-header {
        text-align: center;
        font-size: 1.3rem;
        color: #cbd5e1;
        margin-bottom: 2rem;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    
    .dashboard-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #8b5cf6, #6366f1);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 1.5rem 0 1rem;
        text-align: center;
        letter-spacing: -0.5px;
    }
    
    .section-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e2e8f0;
        margin: 2.5rem 0 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary);
        position: relative;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 80px;
        height: 3px;
        background: var(--accent);
    }
    
    .card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid var(--card-border);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100%;
        text-align: center;
        padding: 1.5rem 1rem;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(79, 70, 229, 0.2));
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    .metric-title {
        font-size: 1rem;
        color: #cbd5e1;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0.2rem 0;
    }
    
    .positive {
        color: #10b981;
    }
    
    .negative {
        color: #ef4444;
    }
    
    .neutral {
        color: #60a5fa;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-block;
        text-align: center;
        text-decoration: none;
        box-shadow: 0 4px 6px rgba(99, 102, 241, 0.2);
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(99, 102, 241, 0.3);
        background: linear-gradient(135deg, var(--primary-dark), var(--primary));
    }
    
    .btn-outline {
        background: transparent;
        color: var(--primary) !important;
        border: 1px solid var(--primary);
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .btn-outline:hover {
        background: rgba(99, 102, 241, 0.1);
        transform: translateY(-2px);
    }
    
    .user-selector {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .user-option {
        padding: 1rem 2rem;
        border-radius: 12px;
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(139, 92, 246, 0.3);
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        flex: 1;
        max-width: 300px;
    }
    
    .user-option:hover {
        background: rgba(79, 70, 229, 0.2);
        transform: translateY(-3px);
    }
    
    .user-option.active {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.3));
        border: 1px solid var(--secondary);
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
    }
    
    .user-option h3 {
        margin: 0;
        font-size: 1.2rem;
        color: #e2e8f0;
    }
    
    .user-option p {
        margin: 0.5rem 0 0;
        font-size: 0.9rem;
        color: #94a3b8;
    }
    
    .tabs {
        display: flex;
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .tab {
        padding: 0.8rem 1.5rem;
        border-radius: 12px 12px 0 0;
        background: rgba(30, 41, 59, 0.5);
        cursor: pointer;
        transition: all 0.3s ease;
        border-bottom: 2px solid transparent;
    }
    
    .tab.active {
        background: var(--card-bg);
        border-bottom: 2px solid var(--accent);
        color: var(--accent);
    }
    
    .tab:hover {
        background: rgba(30, 41, 59, 0.7);
    }
    
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), transparent);
        margin: 2rem 0;
    }
    
    .glow {
        animation: glow 2s infinite alternate;
    }
    
    @keyframes glow {
        from {
            box-shadow: 0 0 5px rgba(139, 92, 246, 0.5);
        }
        to {
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.8);
        }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
        }
    }
    
    .feature-highlight {
        text-align: center;
        padding: 1.5rem;
        border-radius: 16px;
        background: rgba(236, 72, 153, 0.1);
        border: 1px solid rgba(236, 72, 153, 0.3);
        margin: 1.5rem 0;
    }
    
    .feature-highlight h3 {
        color: #ec4899;
        margin-top: 0;
    }
    
    .analysis-container {
        background: rgba(15, 23, 42, 0.7);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    .evidence-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(79, 70, 229, 0.2));
        padding: 2rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    .charter-card {
        background: linear-gradient(135deg, rgba(8, 145, 178, 0.2), rgba(14, 116, 144, 0.2));
        padding: 2rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        border: 1px solid rgba(8, 145, 178, 0.3);
    }
    
    .footer {
        text-align: center;
        padding: 3rem 0 2rem;
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    .footer p {
        margin: 0.5rem 0;
    }
    
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    table {
        background: rgba(15, 23, 42, 0.7) !important;
        color: #e2e8f0 !important;
        border-collapse: collapse;
        width: 100%;
    }
    
    thead {
        background: rgba(79, 70, 229, 0.3) !important;
    }
    
    th {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    
    tr {
        border-bottom: 1px solid rgba(148, 163, 184, 0.2) !important;
    }
    
    tr:hover {
        background: rgba(99, 102, 241, 0.1) !important;
    }
    
    .loss-row {
        background: rgba(239, 68, 68, 0.1) !important;
    }
    
    .profit-row {
        background: rgba(16, 185, 129, 0.1) !important;
    }
    
    .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
    }
    
    .stTextInput > div > div > input {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
    }
    
    .stTextArea > div > div > textarea {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 12px !important;
        background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
        border: none !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--primary-dark), var(--primary)) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    }
    
    .stExpander > div {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 16px !important;
    }
    
    .stExpander > div > div:first-child {
        background: rgba(79, 70, 229, 0.2) !important;
        border-radius: 16px 16px 0 0 !important;
    }
</style>
""", unsafe_allow_html=True)

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
                'keywords': found_keywords[:3],  # 최대 3개까지
                'description': descriptions.get(dominant_pattern, '알 수 없는 패턴')
            }
        
        # 기본값 반환
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
                
                rules.append({
                    'rule': "급락장에서는 24시간 대기 후 투자 결정하기",
                    'rationale': '감정적 판단을 방지하고 합리적 분석 시간 확보',
                    'evidence': '행동경제학 연구 결과',
                    'category': '위기 관리'
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
                
                rules.append({
                    'rule': "모든 투자는 스스로의 리서치를 기반으로 한다",
                    'rationale': '외부 추천에 의한 투자는 객관성이 떨어질 수 있음',
                    'evidence': '과거 추종 투자 패턴 분석',
                    'category': '투자 원칙'
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
    
    def analyze_future_trade(self, stock_name, trade_type, reason, user_data, user_type):
        """미래 거래 계획 분석 (Pre-Mortem)"""
        analysis = {
            'reasoning_analysis': '',
            'failure_note_analysis': '',
            'charter_analysis': '',
            'recommendation': ''
        }
        
        # 1. Reasoning Analysis (NLP-based)
        reason_analysis = self.analyze_emotion_text(reason, user_type)
        
        if reason_analysis['pattern'] == '추격매수':
            analysis['reasoning_analysis'] = f"입력하신 이유('{reason}')를 분석한 결과, 과거 '#추격매수' 실패 패턴과 높은 유사성을 보입니다."
        elif reason_analysis['pattern'] == '공포매도':
            analysis['reasoning_analysis'] = f"입력하신 이유('{reason}')를 분석한 결과, 과거 '#공포매도' 실패 패턴과 높은 유사성을 보입니다."
        elif '추천' in reason or '유튜버' in reason or '커뮤니티' in reason:
            analysis['reasoning_analysis'] = f"입력하신 이유('{reason}')를 분석한 결과, 외부 추천에 의존하는 패턴이 발견되었습니다."
        else:
            analysis['reasoning_analysis'] = f"입력하신 이유('{reason}')를 분석한 결과, 비교적 합리적인 근거가 확인되었습니다."
        
        # 2. Failure Note Analysis
        if reason_analysis['pattern'] == '추격매수':
            chase_trades = user_data[user_data['감정태그'] == '#추격매수']
            if not chase_trades.empty:
                avg_return = chase_trades['수익률'].mean()
                analysis['failure_note_analysis'] = f"과거 오답노트에 따르면, 추격매수 패턴의 거래는 평균 {avg_return:.1f}%의 저조한 성과를 기록했습니다."
        
        elif reason_analysis['pattern'] == '공포매도':
            fear_trades = user_data[user_data['감정태그'].isin(['#공포', '#패닉', '#불안'])]
            if not fear_trades.empty:
                avg_return = fear_trades['수익률'].mean()
                analysis['failure_note_analysis'] = f"과거 오답노트에 따르면, 공포매도 패턴의 거래는 평균 {avg_return:.1f}%의 저조한 성과를 기록했습니다."
        
        elif '추천' in reason or '유튜버' in reason or '커뮤니티' in reason:
            external_trades = user_data[user_data['메모'].str.contains('추천|유튜버|커뮤니티', na=False)]
            if not external_trades.empty:
                avg_return = external_trades['수익률'].mean()
                analysis['failure_note_analysis'] = f"과거 오답노트에 따르면, 외부 추천에 기반한 귀하의 거래는 평균 {avg_return:.1f}%의 저조한 성과를 기록했습니다."
        
        # 3. Investment Charter Analysis
        if user_type == "박투자" and ('추천' in reason or '유튜버' in reason or '커뮤니티' in reason):
            analysis['charter_analysis'] = "⚠️ 또한, 이 결정은 귀하의 투자 헌장 '모든 투자는 스스로의 리서치를 기반으로 한다' 규칙과 충돌할 수 있습니다."
        elif reason_analysis['pattern'] == '공포매도':
            analysis['charter_analysis'] = "⚠️ 또한, 이 결정은 귀하의 투자 헌장 '공포 상태일 때는 24시간 동안 투자 결정 보류' 규칙과 충돌할 수 있습니다."
        elif reason_analysis['pattern'] == '추격매수' and user_type == "박투자":
            analysis['charter_analysis'] = "⚠️ 또한, 이 결정은 귀하의 투자 헌장 '급등 종목을 추격 매수하기 전에 3일간의 냉각기간 갖기' 규칙과 충돌할 수 있습니다."
        
        # 4. Final Recommendation
        if reason_analysis['pattern'] in ['공포매도', '추격매수']:
            analysis['recommendation'] = "이러한 분석에 따라, 이번 투자는 과거의 실패 패턴을 반복할 위험이 있습니다. 투자를 진행하기 전에, 감정에서 벗어나 객관적인 데이터를 다시 검토해보시는 것을 강력히 권장합니다."
        elif '추천' in reason or '유튜버' in reason or '커뮤니티' in reason:
            analysis['recommendation'] = "이러한 분석에 따라, 이번 투자는 외부 의견에 과도하게 의존할 위험이 있습니다. 투자를 진행하기 전에, 스스로의 리서치를 통해 해당 종목을 분석해보시는 것을 강력히 권장합니다."
        else:
            analysis['recommendation'] = "현재 분석 결과, 이번 투자 계획은 비교적 건전한 근거를 가지고 있습니다. 다만, 투자 전에 시장 상황과 종목의 기본적 가치를 다시 한번 확인해보시는 것을 권장합니다."
        
        return analysis

def load_user_data(user_type):
    """사용자 유형에 따른 데이터 로드"""
    try:
        if user_type == "김국민":
            return pd.read_csv('kim_gukmin_trades.csv')
        else:
            return pd.read_csv('park_tuja_trades.csv')
    except:
        # 파일이 없으면 기본 샘플 데이터 생성
        return generate_sample_data(user_type)

def generate_sample_data(user_type):
    """샘플 데이터 생성 (fallback)"""
    np.random.seed(42 if user_type == "김국민" else 24)
    
    # 한국 주요 주식
    korean_stocks = [
        {'종목명': '삼성전자', '종목코드': '005930'},
        {'종목명': '카카오', '종목코드': '035720'},
        {'종목명': 'NAVER', '종목코드': '035420'},
        {'종목명': 'LG에너지솔루션', '종목코드': '373220'},
        {'종목명': '하이브', '종목코드': '352820'},
        {'종목명': 'SK하이닉스', '종목코드': '000660'},
        {'종목명': '현대차', '종목코드': '005380'},
        {'종목명': '셀트리온', '종목코드': '068270'}
    ]
    
    # 감정 태그와 성과 매핑
    if user_type == "김국민":
        emotions_config = {
            '#공포': {'base_return': -15, 'volatility': 12, 'freq': 0.3},
            '#패닉': {'base_return': -18, 'volatility': 15, 'freq': 0.2},
            '#불안': {'base_return': -8, 'volatility': 10, 'freq': 0.2},
            '#추격매수': {'base_return': -12, 'volatility': 20, 'freq': 0.1},
            '#욕심': {'base_return': -10, 'volatility': 25, 'freq': 0.08},
            '#확신': {'base_return': 5, 'volatility': 8, 'freq': 0.07},
            '#합리적': {'base_return': 7, 'volatility': 6, 'freq': 0.05}
        }
    else:  # 박투자
        emotions_config = {
            '#공포': {'base_return': -15, 'volatility': 12, 'freq': 0.1},
            '#패닉': {'base_return': -18, 'volatility': 15, 'freq': 0.08},
            '#불안': {'base_return': -8, 'volatility': 10, 'freq': 0.12},
            '#추격매수': {'base_return': -12, 'volatility': 20, 'freq': 0.35},
            '#욕심': {'base_return': -10, 'volatility': 25, 'freq': 0.2},
            '#확신': {'base_return': 5, 'volatility': 8, 'freq': 0.1},
            '#합리적': {'base_return': 7, 'volatility': 6, 'freq': 0.05}
        }
    
    # 데이터 생성
    trades = []
    start_date = datetime(2024, 1, 1)
    
    for i in range(120):  # 120개 거래 생성
        trade_date = start_date + timedelta(days=np.random.randint(0, 300))
        stock = np.random.choice(korean_stocks)
        
        # 감정 선택 (빈도 기반)
        emotions = list(emotions_config.keys())
        frequencies = [config['freq'] for config in emotions_config.values()]
        emotion = np.random.choice(emotions, p=frequencies)
        
        # 수익률 생성
        config = emotions_config[emotion]
        return_pct = np.random.normal(config['base_return'], config['volatility'])
        
        # 메모 생성
        if emotion == '#공포':
            memo = f"{stock['종목명']} 폭락해서 무서워서 손절"
        elif emotion == '#추격매수':
            memo = f"{stock['종목명']} 급등해서 놓치기 아까워서 매수"
        elif emotion == '#욕심':
            memo = f"{stock['종목명']} 대박날 것 같아서 추가 매수"
        else:
            memo = f"{stock['종목명']} 일반 거래"
        
        trade = {
            '거래일시': trade_date,
            '종목명': stock['종목명'],
            '종목코드': stock['종목코드'],
            '거래구분': np.random.choice(['매수', '매도']),
            '수량': np.random.randint(10, 500),
            '가격': np.random.randint(50000, 500000),
            '감정태그': emotion,
            '메모': memo,
            '수익률': round(return_pct, 2),
            '코스피지수': round(2400 + np.random.normal(0, 100), 2),
            '시장뉴스': ""
        }
        trades.append(trade)
    
    df = pd.DataFrame(trades)
    df = df.sort_values('거래일시').reset_index(drop=True)
    
    return df

def create_mirror_chart(selected_trade, kospi_return):
    """언바이어스드 미러 차트"""
    fig = go.Figure()
    
    # 사용자의 손실/수익
    user_return = selected_trade['수익률']
    
    # 배경 설정
    fig.add_shape(
        type="rect",
        x0=0, x1=1, y0=-25, y1=15,
        fillcolor="rgba(59, 130, 246, 0.05)",
        layer="below",
        line_width=0,
    )
    
    # 사용자 수익률 표시
    color = '#ef4444' if user_return < 0 else '#10b981'
    fig.add_trace(go.Scatter(
        x=[0.25], y=[user_return],
        mode='markers+text',
        marker=dict(size=25, color=color, symbol='circle'),
        text=[f'투자자 수익률<br>{user_return:.1f}%'], 
        textposition="bottom center",
        textfont=dict(size=14, color=color),
        name="투자자 결과"
    ))
    
    # 시장 실제 상황 표시
    fig.add_trace(go.Scatter(
        x=[0.75], y=[kospi_return],
        mode='markers+text',
        marker=dict(size=25, color='#6366f1', symbol='square'),
        text=[f'코스피 수익률<br>{kospi_return:.1f}%'], 
        textposition="bottom center",
        textfont=dict(size=14, color='#6366f1'),
        name="시장 실제 상황"
    ))
    
    # 연결선으로 차이 강조
    fig.add_shape(
        type="line",
        x0=0.25, y0=user_return,
        x1=0.75, y1=kospi_return,
        line=dict(color="#f59e0b", width=4, dash="dash"),
    )
    
    # 차이값 표시
    difference = abs(user_return - kospi_return)
    fig.add_annotation(
        x=0.5, y=(user_return + kospi_return) / 2,
        text=f"차이<br>{difference:.1f}%p",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#f59e0b",
        font=dict(size=12, color="#f59e0b"),
        bgcolor="rgba(245, 158, 11, 0.1)",
        bordercolor="#f59e0b",
        borderwidth=1
    )
    
    fig.update_layout(
        title=dict(
            text="🪞 언바이어스드 미러: 투자자 vs 시장",
            font=dict(size=20, family="Noto Sans KR"),
            x=0.5
        ),
        xaxis=dict(showticklabels=False, range=[0, 1]),
        yaxis=dict(
            title="수익률 (%)", 
            range=[min(user_return, kospi_return) - 5, max(user_return, kospi_return) + 5],
            title_font=dict(family="Noto Sans KR")
        ),
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Noto Sans KR", color="#e2e8f0")
    )
    
    return fig

def main():
    # 세션 상태 초기화
    if 'user_type' not in st.session_state:
        st.session_state.user_type = "김국민"
    if 'user_data' not in st.session_state:
        st.session_state.user_data = load_user_data(st.session_state.user_type)
    if 'engine' not in st.session_state:
        st.session_state.engine = ReMinDKoreanEngine()
    if 'charter_approved' not in st.session_state:
        st.session_state.charter_approved = False
    if 'charter_rules' not in st.session_state:
        st.session_state.charter_rules = []
    if 'selected_post_mortem' not in st.session_state:
        st.session_state.selected_post_mortem = None
    if 'user_memo' not in st.session_state:
        st.session_state.user_memo = ""
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "dashboard"
    
    # 헤더
    st.markdown('<h1 class="main-header">Re:Mind 2.0</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI 기반 투자 심리 분석 플랫폼 - 감정이 아닌 데이터로 투자하세요</p>', unsafe_allow_html=True)
    
    # 사용자 계정 선택 (모던한 카드 디자인)
    st.markdown('<div class="section-header">사용자 계정 선택</div>', unsafe_allow_html=True)

    # 두 개의 컬럼 생성
    col1, col2 = st.columns(2)

    # 김국민 선택 버튼
    with col1:
        # 버튼을 누르면 st.session_state.user_type을 '김국민'으로 변경
        if st.button("김국민 (공포매도 유형)", key="kim_gukmin", use_container_width=True):
            st.session_state.user_type = "김국민"
            # 모든 상태 초기화 후 재실행하여 대시보드 전체를 새로고침
            st.session_state.user_data = load_user_data("김국민")
            st.session_state.charter_rules = []
            st.session_state.charter_approved = False
            st.session_state.selected_post_mortem = None
            st.session_state.user_memo = ""
            st.rerun()

    # 박투자 선택 버튼
    with col2:
        # 버튼을 누르면 st.session_state.user_type을 '박투자'으로 변경
        if st.button("박투자 (추격매수 유형)", key="park_tuja", use_container_width=True):
            st.session_state.user_type = "박투자"
            # 모든 상태 초기화 후 재실행
            st.session_state.user_data = load_user_data("박투자")
            st.session_state.charter_rules = []
            st.session_state.charter_approved = False
            st.session_state.selected_post_mortem = None
            st.session_state.user_memo = ""
            st.rerun()

    # 현재 선택된 사용자에 따라 시각적 피드백 제공 (선택사항이지만 추천)
    st.info(f"현재 선택된 사용자: **{st.session_state.user_type}**. 대시보드가 {st.session_state.user_type}님의 데이터에 맞춰 개인화되었습니다.")

    # 대시보드 헤더
    st.markdown(f'<div class="dashboard-header">{st.session_state.user_type}님의 투자 대시보드</div>', unsafe_allow_html=True)

    
    col1, col2 = st.columns(2)
    with col1:
        user_option1 = st.container()
        with user_option1:
            st.markdown(f'<div class="user-option {'active' if st.session_state.user_type == "김국민" else ''}" onclick="setUserType(\'김국민\')">', unsafe_allow_html=True)
            st.markdown('<h3>김국민</h3>', unsafe_allow_html=True)
            st.markdown('<p>공포매도 유형</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        user_option2 = st.container()
        with user_option2:
            st.markdown(f'<div class="user-option {'active' if st.session_state.user_type == "박투자" else ''}" onclick="setUserType(\'박투자\')">', unsafe_allow_html=True)
            st.markdown('<h3>박투자</h3>', unsafe_allow_html=True)
            st.markdown('<p>추격매수 유형</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 대시보드 헤더
    st.markdown(f'<div class="dashboard-header">{st.session_state.user_type}님의 투자 대시보드</div>', unsafe_allow_html=True)
    
    # 데이터 로드
    data = st.session_state.user_data
    
    # 전체 성과 요약
    st.markdown('<div class="section-header">투자 성과 요약</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_trades = len(data)
    avg_return = data['수익률'].mean()
    win_rate = len(data[data['수익률'] > 0]) / len(data) * 100
    worst_loss = data['수익률'].min()
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-title">총 거래 횟수</div>
            <div class="metric-value neutral">{total_trades}회</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        if avg_return >= 0:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">평균 수익률</div>
                <div class="metric-value positive">{avg_return:.1f}%</div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">평균 수익률</div>
                <div class="metric-value negative">{avg_return:.1f}%</div>
            </div>
            ''', unsafe_allow_html=True)
    
    with col3:
        if win_rate >= 50:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">승률</div>
                <div class="metric-value positive">{win_rate:.0f}%</div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">승률</div>
                <div class="metric-value negative">{win_rate:.0f}%</div>
            </div>
            ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-title">최대 손실</div>
            <div class="metric-value negative">{worst_loss:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # 메인 기능 탭
    st.markdown('<div class="tabs">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 거래 내역", key="tab1", use_container_width=True):
            st.session_state.active_tab = "trades"
    with col2:
        if st.button("📝 오답노트 분석", key="tab2", use_container_width=True):
            st.session_state.active_tab = "analysis"
    with col3:
        if st.button("📜 투자 헌장", key="tab3", use_container_width=True):
            st.session_state.active_tab = "charter"
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 거래 내역 섹션
    if st.session_state.active_tab == "trades":
        st.markdown('<div class="section-header">거래 내역</div>', unsafe_allow_html=True)
        
        # 거래 내역 표시 with AI 오답노트 버튼
        trade_display = data.copy()
        trade_display['거래일시'] = pd.to_datetime(trade_display['거래일시']).dt.strftime('%Y-%m-%d')
        
        # AI 오답노트 컬럼 추가
        trade_display['AI 오답노트'] = trade_display.apply(
            lambda row: "오답노트 가능" if row['수익률'] < 0 else "수익거래", axis=1
        )
        
        # 표시할 컬럼 선택
        display_cols = ['거래일시', '종목명', '거래구분', '수량', '가격', '수익률', '감정태그', 'AI 오답노트']
        
        # 손실 거래 강조를 위한 스타일링
        def highlight_rows(row):
            if row['수익률'] < 0:
                return ['background-color: rgba(239, 68, 68, 0.1)'] * len(row)
            elif row['수익률'] > 0:
                return ['background-color: rgba(16, 185, 129, 0.1)'] * len(row)
            else:
                return [''] * len(row)
        
        # 데이터프레임 표시
        styled_df = trade_display[display_cols].style.apply(highlight_rows, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # 손실 거래 선택 드롭다운
        losing_trades = data[data['수익률'] < 0].copy()
        losing_trades['거래일시'] = pd.to_datetime(losing_trades['거래일시'])
        losing_trades = losing_trades.sort_values('거래일시', ascending=False)
        
        if len(losing_trades) > 0:
            st.markdown('<div class="section-header">오답노트 분석</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_trade_idx = st.selectbox(
                    "분석할 손실 거래를 선택하세요",
                    losing_trades.index,
                    format_func=lambda x: f"{losing_trades.loc[x, '거래일시'].strftime('%Y-%m-%d')} - {losing_trades.loc[x, '종목명']} ({losing_trades.loc[x, '수익률']:.1f}%)"
                )
            
            with col2:
                if st.button("📝 오답노트 작성하기", type="primary", use_container_width=True):
                    st.session_state.selected_post_mortem = selected_trade_idx
                    st.session_state.active_tab = "analysis"
                    st.rerun()
    
    # 오답노트 분석 섹션
    elif st.session_state.active_tab == "analysis":
        st.markdown('<div class="section-header">오답노트 분석</div>', unsafe_allow_html=True)
        
        if st.session_state.selected_post_mortem is not None:
            losing_trades = data[data['수익률'] < 0].copy()
            losing_trades['거래일시'] = pd.to_datetime(losing_trades['거래일시'])
            losing_trades = losing_trades.sort_values('거래일시', ascending=False)
            selected_trade = losing_trades.loc[st.session_state.selected_post_mortem]
            
            # 동적 expander 제목
            with st.expander(f"{selected_trade['종목명']} ({selected_trade['수익률']:.1f}%) 거래 심층 분석", expanded=True):
                st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
                
                # Step 1: AI의 객관적 브리핑 (Enhanced Unbiased Mirror)
                st.markdown('<h4 style="color: #e2e8f0;">🤖 AI 객관적 브리핑</h4>', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"""
                    **📋 거래 상세 정보**
                    - **거래일:** {selected_trade['거래일시'].strftime('%Y년 %m월 %d일')}
                    - **종목:** {selected_trade['종목명']} ({selected_trade['종목코드']})
                    - **거래:** {selected_trade['거래구분']}
                    - **수량/가격:** {selected_trade['수량']}주 / {selected_trade['가격']:,}원
                    - **감정상태:** {selected_trade['감정태그']}
                    - **결과:** **{selected_trade['수익률']:.1f}% 손실**
                    """)
                
                with col2:
                    # 언바이어스드 미러 차트
                    kospi_return = round(np.random.normal(-1.0, 2.0), 1)
                    mirror_chart = create_mirror_chart(selected_trade, kospi_return)
                    st.plotly_chart(mirror_chart, use_container_width=True)
                
                # 시장 상황 정보
                st.markdown('<h5 style="color: #e2e8f0;">📰 당시 시장 상황</h5>', unsafe_allow_html=True)
                
                # 시장 뉴스 표시
                if pd.notna(selected_trade['시장뉴스']) and selected_trade['시장뉴스']:
                    news_items = selected_trade['시장뉴스'].split('|')
                    for news in news_items:
                        st.info(f"📰 {news}")
                else:
                    # 더미 뉴스 생성
                    dummy_news = [
                        "[국제] 미국 연준, 금리 인상 가능성 시사",
                        "[국내] 코스피, 외국인 매도세에 하락 마감",
                        "[시장] 투자 심리 위축...테마주 일제히 약세"
                    ]
                    for news in dummy_news:
                        st.info(f"📰 {news}")
                
                # AI 시장 요약
                market_summary = (
                    f"당시 코스피 지수는 {selected_trade['코스피지수']}포인트로, "
                    f"전일 대비 {kospi_return:.1f}%의 {'상승' if kospi_return >= 0 else '하락'}했습니다. "
                    f"글로벌 경제 불확실성과 외국인 매도세가 시장에 부정적인 영향을 미쳤으며, "
                    f"투자자들의 심리는 위축된 상태였습니다."
                )
                
                st.markdown(f"""
                <div style="background: rgba(14, 165, 233, 0.1); padding: 1rem; border-radius: 10px; border-left: 4px solid #0ea5e9; margin: 1rem 0;">
                    <strong>🤖 AI 시장 요약:</strong><br>
                    {market_summary}
                </div>
                """, unsafe_allow_html=True)
                
                # Step 2: 사용자 자기반성
                st.markdown('<h5 style="color: #e2e8f0; margin-top: 2rem;">✏️ 사용자 자기반성</h5>', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    emotion_selection = st.selectbox(
                        "당시 감정 태그 선택:",
                        ["#공포", "#패닉", "#불안", "#추격매수", "#욕심", "#확신", "#합리적"],
                        index=0
                    )
                
                with col2:
                    user_memo = st.text_area(
                        "이 거래에 대한 생각을 기록해주세요:",
                        value=st.session_state.user_memo,
                        height=120,
                        placeholder="당시의 결정 과정이나 현재의 생각을 자유롭게 기록해주세요."
                    )
                    st.session_state.user_memo = user_memo
                
                # Step 3: AI 증거 기반 분석
                if st.button("🔍 AI 증거 기반 분석 받기", type="primary"):
                    if user_memo:
                        st.markdown('<h5 style="color: #e2e8f0; margin-top: 2rem;">🤖 AI 증거 기반 분석</h5>', unsafe_allow_html=True)
                        
                        # AI 분석 실행
                        analysis = st.session_state.engine.analyze_emotion_text(user_memo, st.session_state.user_type)
                        
                        # 증거 제시 (판단이 아닌 증거)
                        st.markdown("""
                        <div class="evidence-card">
                            <h4>🔍 발견된 증거</h4>
                        """, unsafe_allow_html=True)
                        
                        # 키워드 분석
                        if analysis['keywords']:
                            st.markdown(f"""
                            <p>• <strong>감정 키워드:</strong> 귀하의 메모에서 '{', '.join(analysis['keywords'])}' 등의 키워드가 발견되었습니다.</p>
                            """, unsafe_allow_html=True)
                        
                        # 과거 패턴 분석
                        pattern_trades = data[data['감정태그'].str.contains(analysis['pattern'].replace('매수', '').replace('매도', ''), na=False)]
                        if not pattern_trades.empty:
                            avg_pattern_return = pattern_trades['수익률'].mean()
                            st.markdown(f"""
                            <p>• <strong>과거 패턴 분석:</strong> 귀하의 과거 거래 중, '{analysis['pattern']}' 패턴의 평균 수익률은 <span style="color: {'#10b981' if avg_pattern_return > 0 else '#ef4444'}; font-weight: bold;">{avg_pattern_return:.1f}%</span>입니다.</p>
                            """, unsafe_allow_html=True)
                        
                        # 시장 대비 성과
                        st.markdown(f"""
                        <p>• <strong>시장 대비 성과:</strong> 이 거래의 수익률은 <strong>{selected_trade['수익률']:.1f}%</strong>로, 시장 평균({kospi_return:.1f}%)보다 {abs(selected_trade['수익률'] - kospi_return):.1f}%p {'낮았습니다' if selected_trade['수익률'] < kospi_return else '높았습니다'}.</p>
                        """, unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # AI 제안 (판단이 아닌 가이드)
                        st.markdown("""
                        <div style="background: rgba(14, 165, 233, 0.1); padding: 1.5rem; border-radius: 10px; margin-top: 1rem; border-left: 4px solid #0ea5e9;">
                            <h5>💡 AI 자기반성 가이드</h5>
                        """, unsafe_allow_html=True)
                        
                        suggestion = (
                            f"이러한 증거들을 종합해 볼 때, 이 거래가 '{analysis['pattern']}' 패턴일 가능성을 고려해볼 수 있습니다. "
                            f"이 결정이 감정적인 선택이었을 가능성에 대해 스스로 돌아볼 수 있는 기회입니다. "
                            f"향후 유사한 상황에서는 시장의 전반적인 흐름을 고려하고, "
                            f"감정적인 판단을 피하기 위해 24시간의 냉각기간을 갖는 것을 고려해보세요."
                        )
                        
                        st.markdown(f"<p>{suggestion}</p>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    else:
                        st.warning("분석을 위해 메모를 입력해주세요.")
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("분석할 거래를 선택해주세요. '거래 내역' 탭에서 손실 거래를 선택하세요.")
    
    # 투자 헌장 섹션
    elif st.session_state.active_tab == "charter":
        st.markdown('<div class="section-header">개인화된 투자 헌장</div>', unsafe_allow_html=True)
        
        # 투자 헌장 생성
        if not st.session_state.charter_rules:
            charter_rules = st.session_state.engine.generate_investment_charter_rules(
                data, st.session_state.user_type
            )
            st.session_state.charter_rules = charter_rules
        
        if st.session_state.charter_rules:
            st.markdown(f"""
            <div class="card">
                <h3>🎯 {st.session_state.user_type}님만의 개인화된 규칙</h3>
                <p>다음은 귀하의 거래 데이터를 분석하여 도출된 개인화된 투자 규칙들입니다. 각 규칙을 검토하고 승인해주세요.</p>
            </div>
            """, unsafe_allow_html=True)
            
            approved_rules = []
            
            for i, rule in enumerate(st.session_state.charter_rules):
                with st.expander(f"규칙 {i+1}: {rule['rule']}", expanded=True):
                    st.markdown(f"""
                    **📊 근거:** {rule['rationale']}  
                    **📈 데이터:** {rule['evidence']}  
                    **📂 분류:** {rule['category']}
                    """)
                    
                    approved = st.checkbox(f"이 규칙을 승인합니다", key=f"approve_rule_{i}", value=False)
                    if approved:
                        approved_rules.append(rule)
                        if not st.session_state.charter_approved:
                            st.session_state.charter_approved = True
            
            # 승인된 규칙이 있으면 완성된 헌장 표시
            if approved_rules:
                st.markdown('<div class="section-header">✅ 승인된 투자 헌장</div>', unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="charter-card">
                    <h2 style="text-align: center; margin: 0 0 2rem 0;">📜 {st.session_state.user_type}님의 투자 헌장</h2>
                    <p style="text-align: center; font-style: italic; color: #cbd5e1;">2024년 8월 5일 작성</p>
                    
                    <h3>🎯 핵심 원칙</h3>
                    <ol>
                """, unsafe_allow_html=True)
                
                for rule in approved_rules:
                    st.markdown(f"""
                        <li><strong>{rule['rule']}</strong>
                            <br><em>→ {rule['rationale']} ({rule['evidence']})</em></li>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                    </ol>
                    
                    <h3>💪 다짐</h3>
                    <p>나는 내 자신의 거래 데이터에서 도출된 이 규칙들을 따르며, 
                    감정이 아닌 데이터에 기반한 투자 결정을 내릴 것을 다짐합니다.</p>
                    
                    <div style="text-align: center; margin-top: 2rem; font-style: italic; color: #cbd5e1;">
                        서명: {st.session_state.user_type} &nbsp;&nbsp;&nbsp; 날짜: 2024년 8월 5일
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 성과 개선 예측
                st.markdown('<div class="section-header">📈 예상 성과 개선 효과</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 과거 감정적 거래 손실
                    if st.session_state.user_type == "김국민":
                        emotional_trades = data[data['감정태그'].isin(['#공포', '#패닉', '#불안'])]
                    else:
                        emotional_trades = data[data['감정태그'].isin(['#추격매수', '#욕심'])]
                    
                    historical_loss = emotional_trades['수익률'].sum()
                    
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">과거 감정적 거래 손실</div>
                        <div class="metric-value negative">{historical_loss:.1f}%</div>
                        <div class="metric-title">총 포트폴리오 영향</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col2:
                    # 예상 개선
                    projected_improvement = abs(historical_loss) * 0.75  # 75% 개선 가정
                    
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-title">헌장 준수 시 예상 개선</div>
                        <div class="metric-value positive">+{projected_improvement:.1f}%</div>
                        <div class="metric-title">연간 수익률 개선 예상</div>
                    </div>
                    ''', unsafe_allow_html=True)
        else:
            st.info("충분한 거래 데이터가 없어 투자 헌장을 생성할 수 없습니다.")
    
    # Pre-Mortem 사전 검토 (AI 투자 계획 검토받기)
    st.markdown('<div class="section-header">🔮 AI 투자 계획 검토받기</div>', unsafe_allow_html=True)
    
    with st.expander("💡 사전 투자 검토 (Pre-Mortem)", expanded=False):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        st.markdown('<h4>📝 투자 계획 입력</h4>', unsafe_allow_html=True)
        
        # 투자 계획 입력 폼
        col1, col2 = st.columns([1, 1])
        
        with col1:
            stock_name = st.text_input("종목명", placeholder="예: 삼성전자")
            trade_type = st.selectbox("거래구분", ["매수", "매도"])
        
        with col2:
            reason = st.text_area(
                "투자를 결심한 이유",
                placeholder="투자 결정을 하게 된 이유를 자세히 설명해주세요.",
                height=120
            )
        
        # AI 검토 버튼
        if st.button("🔍 AI 다각적 검토받기", type="primary", use_container_width=True):
            if stock_name and reason:
                # AI 분석 실행
                analysis = st.session_state.engine.analyze_future_trade(
                    stock_name, trade_type, reason, data, st.session_state.user_type
                )
                
                st.markdown('<h4 style="color: #e2e8f0; margin-top: 1.5rem;">🤖 AI 다각적 검토 보고서</h4>', unsafe_allow_html=True)
                
                # 1. 사유 분석
                st.markdown("""
                <div class="card">
                    <h5>🧠 사유 분석</h5>
                """, unsafe_allow_html=True)
                st.markdown(f"<p>{analysis['reasoning_analysis']}</p>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 2. 과거 실패 노트 분석
                if analysis['failure_note_analysis']:
                    st.markdown("""
                    <div class="card" style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3);">
                        <h5>📉 과거 실패 노트 분석</h5>
                    """, unsafe_allow_html=True)
                    st.markdown(f"<p>{analysis['failure_note_analysis']}</p>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # 3. 투자 헌장 분석
                if analysis['charter_analysis']:
                    st.markdown("""
                    <div class="card" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3);">
                        <h5>📜 투자 헌장 분석</h5>
                    """, unsafe_allow_html=True)
                    st.markdown(f"<p>{analysis['charter_analysis']}</p>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # 4. 최종 권고사항
                st.markdown("""
                <div class="card" style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3);">
                    <h5>💡 AI 최종 권고사항</h5>
                """, unsafe_allow_html=True)
                st.markdown(f"<p>{analysis['recommendation']}</p>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.warning("종목명과 투자 이유를 모두 입력해주세요.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 푸터
    st.markdown("""
    <div class="footer">
        <p>🧠 Re:Mind 2.0 - AI 기반 투자 심리 분석 플랫폼</p>
        <p>감정이 아닌 데이터로, 실패가 아닌 학습으로 더 나은 투자자가 되어보세요.</p>
        <p>© 2024 Re:Mind Labs. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)

# 자바스크립트로 사용자 선택 처리
st.markdown("""
<script>
    function setUserType(userType) {
        Streamlit.setComponentValue(userType);
    }
</script>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()