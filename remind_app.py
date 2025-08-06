import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="Re:Mind 3.1 - AI 투자 심리 분석",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Toss-inspired CSS 스타일
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    :root {
        --bg-color: #F2F4F6;
        --sidebar-bg: #FFFFFF;
        --card-bg: #FFFFFF;
        --primary-blue: #3182F6;
        --text-primary: #191919;
        --text-secondary: #505967;
        --text-light: #8B95A1;
        --border-color: #E5E8EB;
        --positive-color: #D91A2A;
        --negative-color: #1262D7;
        --success-color: #14AE5C;
        --warning-color: #FF9500;
    }

    * {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }

    .stApp {
        background-color: var(--bg-color);
    }

    .css-1d391kg {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .metric-card {
        background-color: var(--card-bg);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid var(--border-color);
        text-align: center;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .metric-label {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-light);
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
    }

    .metric-value.positive {
        color: var(--positive-color);
    }

    .metric-value.negative {
        color: var(--negative-color);
    }

    .card {
        background-color: var(--card-bg);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid var(--border-color);
    }

    .card-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 16px;
    }

    .stButton > button {
        background-color: var(--primary-blue);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        height: 48px;
        font-size: 15px;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #2563EB;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(49, 130, 246, 0.3);
    }

    .buy-button {
        background-color: var(--positive-color) !important;
    }

    .sell-button {
        background-color: var(--negative-color) !important;
    }

    .stSelectbox > div > div {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        height: 48px;
    }

    .stTextInput > div > div > input {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        height: 48px;
        font-size: 15px;
    }

    .stNumberInput > div > div > input {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        height: 48px;
        font-size: 15px;
    }

    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color);
    }

    .main-header {
        font-size: 28px;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 8px;
    }

    .sub-header {
        font-size: 16px;
        color: var(--text-secondary);
        margin-bottom: 32px;
    }

    .ai-coaching-card {
        background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%);
        border: 1px solid #BFDBFE;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
    }

    .ai-coaching-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--primary-blue);
        margin-bottom: 12px;
    }

    .ai-coaching-content {
        font-size: 15px;
        color: var(--text-secondary);
        line-height: 1.6;
    }

    .trade-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-bottom: 1px solid var(--border-color);
    }

    .trade-item:last-child {
        border-bottom: none;
    }

    .trade-info {
        display: flex;
        flex-direction: column;
    }

    .trade-stock-name {
        font-weight: 700;
        color: var(--text-primary);
        font-size: 16px;
    }

    .trade-details {
        font-size: 13px;
        color: var(--text-light);
        margin-top: 4px;
    }

    .trade-amount {
        font-weight: 700;
        font-size: 16px;
    }

    .trade-amount.buy {
        color: var(--positive-color);
    }

    .trade-amount.sell {
        color: var(--negative-color);
    }

    .live-indicator {
        display: inline-flex;
        align-items: center;
        font-size: 14px;
        color: var(--success-color);
        font-weight: 600;
    }

    .live-dot {
        width: 8px;
        height: 8px;
        background-color: var(--success-color);
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    .emotion-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }

    .emotion-fear {
        background-color: #FEF2F2;
        color: #DC2626;
    }

    .emotion-fomo {
        background-color: #FFF7ED;
        color: #EA580C;
    }

    .emotion-rational {
        background-color: #F0FDF4;
        color: #16A34A;
    }

    .charter-rule {
        background-color: #F8FAFC;
        border-left: 4px solid var(--primary-blue);
        padding: 16px;
        margin: 12px 0;
        border-radius: 0 8px 8px 0;
    }

    .charter-rule-title {
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 8px;
    }

    .charter-rule-description {
        font-size: 14px;
        color: var(--text-secondary);
        line-height: 1.5;
    }

    .price-update {
        animation: price-pulse 1s ease-in-out;
    }

    @keyframes price-pulse {
        0% { background-color: rgba(49, 130, 246, 0.1); }
        50% { background-color: rgba(49, 130, 246, 0.3); }
        100% { background-color: rgba(49, 130, 246, 0.1); }
    }

    .loss-alert {
        background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
        border: 2px solid #F87171;
        border-radius: 16px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    }

    .loss-alert-title {
        font-size: 18px;
        font-weight: 700;
        color: #DC2626;
        margin-bottom: 12px;
    }

    .loss-alert-content {
        font-size: 14px;
        color: #7F1D1D;
        margin-bottom: 16px;
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

def load_user_data(user_type):
    """사용자 유형에 따른 데이터 로드"""
    return generate_sample_data(user_type)

def generate_sample_data(user_type):
    """샘플 데이터 생성"""
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
        {'종목명': 'KB금융', '종목코드': '105560'}
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
    
    # 메모 템플릿
    memo_templates = {
        '#공포': [f"{{종목명}} 폭락해서 무서워서 손절", f"너무 무서워서 {{종목명}} 전량 매도"],
        '#추격매수': [f"{{종목명}} 급등해서 놓치기 아까워서 매수", f"어제 {{종목명}} 상한가 갔는데 추격매수"],
        '#욕심': [f"{{종목명}} 대박날 것 같아서 추가 매수", f"{{종목명}} 더 오를 것 같아서 풀매수"],
        '#합리적': [f"{{종목명}} 기술적 분석상 매수 타이밍", f"펀더멘털 분석 후 {{종목명}} 매수"]
    }
    
    # 기본 메모 설정
    for emotion in emotions_config.keys():
        if emotion not in memo_templates:
            memo_templates[emotion] = [f"{emotion} 상태에서 {{종목명}} 거래"]
    
    # 데이터 생성
    trades = []
    start_date = datetime(2024, 1, 1)
    
    for i in range(100):
        trade_date = start_date + timedelta(days=np.random.randint(0, 240))
        stock = np.random.choice(korean_stocks)
        
        # 감정 선택 (빈도 기반)
        emotions = list(emotions_config.keys())
        frequencies = [config['freq'] for config in emotions_config.values()]
        emotion = np.random.choice(emotions, p=frequencies)
        
        # 수익률 생성
        config = emotions_config[emotion]
        return_pct = np.random.normal(config['base_return'], config['volatility'])
        
        # 메모 생성
        memo_template = np.random.choice(memo_templates[emotion])
        memo = memo_template.format(종목명=stock['종목명'])
        
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

def initialize_session_state():
    """세션 상태 초기화"""
    if 'cash' not in st.session_state:
        st.session_state.cash = 50_000_000
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}
    if 'history' not in st.session_state:
        st.session_state.history = pd.DataFrame(columns=['거래일시', '종목명', '거래구분', '수량', '가격', '금액'])
    if 'market_data' not in st.session_state:
        # 시장 데이터 초기화
        st.session_state.market_data = {
            '삼성전자': {'price': 75000, 'change': 2.1, 'news': '3분기 실적 개선 전망'},
            '카카오': {'price': 45000, 'change': -1.5, 'news': '카카오페이 IPO 계획 발표'},
            'NAVER': {'price': 180000, 'change': 0.8, 'news': '클라우드 사업 확장'},
            'LG에너지솔루션': {'price': 420000, 'change': 3.2, 'news': '북미 배터리 공장 증설'},
            '하이브': {'price': 155000, 'change': -2.8, 'news': 'BTS 멤버 입대 영향 우려'},
            'SK하이닉스': {'price': 125000, 'change': 1.7, 'news': '메모리 반도체 수급 개선'},
            '현대차': {'price': 190000, 'change': 0.3, 'news': '전기차 판매량 증가'},
            'KB금융': {'price': 78000, 'change': -0.5, 'news': '금리 인상 기대감'}
        }
    if 'user_data' not in st.session_state:
        st.session_state.user_data = load_user_data("김국민")
    if 'engine' not in st.session_state:
        st.session_state.engine = ReMinDKoreanEngine()
    if 'chart_data' not in st.session_state:
        # 실시간 차트 데이터 초기화
        base_value = st.session_state.cash
        st.session_state.chart_data = {
            'time': [datetime.now() - timedelta(minutes=i*2) for i in range(30, 0, -1)],
            'value': [base_value + np.random.normal(0, 100000) for _ in range(30)]
        }
    # 새로 추가된 세션 상태
    if 'last_price_update' not in st.session_state:
        st.session_state.last_price_update = datetime.now()
    if 'show_loss_modal' not in st.session_state:
        st.session_state.show_loss_modal = False
    if 'loss_info' not in st.session_state:
        st.session_state.loss_info = {}
    if 'show_charge_modal' not in st.session_state:
        st.session_state.show_charge_modal = False
    if 'show_loss_analysis' not in st.session_state:
        st.session_state.show_loss_analysis = False
    if 'user_loss_notes' not in st.session_state:
        st.session_state.user_loss_notes = []

def update_prices():
    """실시간 가격 업데이트 (1초마다)"""
    current_time = datetime.now()
    if (current_time - st.session_state.last_price_update).seconds >= 1:
        for stock_name in st.session_state.market_data:
            # ±2% 범위 내에서 랜덤 변동
            change = np.random.normal(0, 0.02)
            new_price = max(1000, int(st.session_state.market_data[stock_name]['price'] * (1 + change)))
            st.session_state.market_data[stock_name]['price'] = new_price
            st.session_state.market_data[stock_name]['change'] = np.random.normal(0, 3)
        
        st.session_state.last_price_update = current_time

def create_live_chart():
    """실시간 차트 생성"""
    # 새로운 데이터 포인트 추가
    current_time = datetime.now()
    portfolio_value = st.session_state.cash + sum([
        holdings['shares'] * st.session_state.market_data.get(stock, {'price': 50000})['price']
        for stock, holdings in st.session_state.portfolio.items()
    ])
    
    # 약간의 랜덤 변동 추가
    portfolio_value += np.random.normal(0, 50000)
    
    st.session_state.chart_data['time'].append(current_time)
    st.session_state.chart_data['value'].append(portfolio_value)
    
    # 최근 30개 데이터만 유지
    if len(st.session_state.chart_data['time']) > 30:
        st.session_state.chart_data['time'] = st.session_state.chart_data['time'][-30:]
        st.session_state.chart_data['value'] = st.session_state.chart_data['value'][-30:]
    
    # 차트 생성
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=st.session_state.chart_data['time'],
        y=st.session_state.chart_data['value'],
        mode='lines',
        name='포트폴리오 가치',
        line=dict(color='#3182F6', width=3),
        fill='tonexty',
        fillcolor='rgba(49, 130, 246, 0.1)'
    ))
    
    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="자산 가치 (원)",
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Pretendard", color="#191919"),
        margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(
            tickformat=',.0f',
            gridcolor='rgba(229, 232, 235, 0.5)'
        ),
        xaxis=dict(
            gridcolor='rgba(229, 232, 235, 0.5)'
        )
    )
    
    return fig

def show_charge_modal():
    """자산 충전 모달"""
    st.markdown("### 💰 자산 충전")
    st.write("원하는 금액을 입력하여 가상 자산을 충전할 수 있습니다.")
    
    charge_amount = st.number_input(
        "충전할 금액 (원)",
        min_value=10000,
        max_value=100000000,
        value=1000000,
        step=100000,
        format="%d"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💳 충전하기", key="confirm_charge", use_container_width=True):
            st.session_state.cash += charge_amount
            st.success(f"✅ ₩{charge_amount:,}원이 충전되었습니다!")
            st.balloons()
            st.session_state.show_charge_modal = False
            time.sleep(2)
            st.rerun()
    
    with col2:
        if st.button("❌ 취소", key="cancel_charge", use_container_width=True):
            st.session_state.show_charge_modal = False
            st.rerun()

def show_loss_modal(loss_info):
    """손실 발생 시 오답노트 작성 유도 모달"""
    st.markdown(f'''
    <div class="loss-alert">
        <div class="loss-alert-title">📉 손실이 발생했습니다</div>
        <div class="loss-alert-content">
            <strong>{loss_info['stock_name']}</strong> {loss_info['quantity']}주 매도에서<br>
            <strong>₩{loss_info['loss_amount']:,.0f}원 ({loss_info['loss_percentage']:.1f}%)</strong> 손실이 발생했습니다.<br><br>
            매수가: <strong>₩{loss_info['buy_price']:,.0f}</strong> → 매도가: <strong>₩{loss_info['sell_price']:,.0f}</strong>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("### 🤔 오답노트를 작성할까요?")
    st.write("손실 거래를 분석하여 향후 더 나은 투자 결정을 내릴 수 있도록 도와드립니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 네, 오답노트를 작성하겠습니다", key="create_loss_note", use_container_width=True):
            st.session_state.show_loss_analysis = True
            st.session_state.show_loss_modal = False
            st.rerun()
    
    with col2:
        if st.button("❌ 아니요, 다음에 하겠습니다", key="skip_loss_note", use_container_width=True):
            st.info("💡 언제든지 AI 코칭 센터에서 과거 거래를 분석할 수 있습니다.")
            st.session_state.show_loss_modal = False
            st.session_state.loss_info = {}
            time.sleep(1)
            st.rerun()

def show_loss_analysis(loss_info):
    """손실 발생 시 상세 분석 탭"""
    st.markdown(f'''
    <div class="loss-alert">
        <div class="loss-alert-title">📊 손실 거래 상세 분석</div>
        <div class="loss-alert-content">
            <strong>{loss_info['stock_name']}</strong> {loss_info['quantity']}주 매도 분석<br>
            손실: <strong>₩{loss_info['loss_amount']:,.0f}원 ({loss_info['loss_percentage']:.1f}%)</strong>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 분석 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📈 기술 분석", "📰 뉴스", "😔 감정", "💬 Comment"])
    
    with tab1:
        st.markdown("#### 📈 기술 분석")
        st.markdown(f"""
        **{loss_info['stock_name']} 기술적 분석 요약:**
        - 매수가: ₩{loss_info['buy_price']:,.0f}
        - 매도가: ₩{loss_info['sell_price']:,.0f}
        - 손실률: {loss_info['loss_percentage']:.1f}%
        
        **분석 포인트:**
        - 지지선 이탈로 인한 추가 하락 위험이 있었음
        - 거래량 급증과 함께 매도 압력 증가
        - RSI 지표상 과매도 구간 진입
        """)
    
    with tab2:
        st.markdown("#### 📰 뉴스 분석")
        news_items = [
            f"{loss_info['stock_name']} 실적 전망 하향 조정",
            "업종 전반 투자심리 위축",
            "외국인 투자자 매도세 지속",
            "시장 변동성 확대 우려"
        ]
        
        for i, news in enumerate(news_items, 1):
            st.markdown(f"**{i}.** {news}")
    
    with tab3:
        st.markdown("#### 😔 감정 분석")
        emotions = ["불안", "공포", "후회", "조급함"]
        selected_emotions = st.multiselect(
            "당시 느꼈던 감정을 선택하세요:",
            emotions,
            default=["불안", "후회"]
        )
        
        emotion_intensity = st.slider(
            "감정의 강도 (1-10)",
            min_value=1,
            max_value=10,
            value=7
        )
    
    with tab4:
        st.markdown("#### 💬 Comment")
        user_comment = st.text_area(
            "이번 거래에 대한 생각을 자유롭게 적어주세요:",
            height=150,
            placeholder="예: 너무 성급하게 손절했나 싶다. 뉴스만 보고 판단한 것 같아서 아쉽다...",
            key="loss_comment"
        )
        
        if st.button("📝 오답노트 완성하기", type="primary", use_container_width=True):
            if user_comment.strip():
                # AI 해시태그 생성
                analysis = st.session_state.engine.analyze_emotion_text(user_comment, st.session_state.current_user)
                
                # 오답노트 저장
                loss_note = {
                    'timestamp': datetime.now(),
                    'stock_name': loss_info['stock_name'],
                    'loss_amount': loss_info['loss_amount'],
                    'loss_percentage': loss_info['loss_percentage'],
                    'buy_price': loss_info['buy_price'],
                    'sell_price': loss_info['sell_price'],
                    'quantity': loss_info['quantity'],
                    'user_comment': user_comment,
                    'ai_hashtags': [f"#{analysis['pattern']}", f"#{analysis['keywords'][0] if analysis['keywords'] else '감정거래'}"],
                    'emotions': selected_emotions,
                    'emotion_intensity': emotion_intensity
                }
                
                st.session_state.user_loss_notes.append(loss_note)
                
                st.success("✅ 오답노트가 AI 코칭 센터에 추가되었습니다!")
                st.balloons()
                
                st.session_state.show_loss_analysis = False
                st.session_state.show_loss_modal = False
                st.session_state.loss_info = {}
                
                time.sleep(2)
                st.rerun()
            else:
                st.warning("코멘트를 입력해주세요.")
    
    # 뒤로가기 버튼
    if st.button("⬅️ 뒤로가기", key="back_from_analysis"):
        st.session_state.show_loss_analysis = False
        st.session_state.show_loss_modal = True

def execute_trade(stock_name, trade_type, quantity, price):
    """거래 실행 함수"""
    total_amount = quantity * price
    
    if trade_type == "매수":
        if st.session_state.cash >= total_amount:
            st.session_state.cash -= total_amount
            
            if stock_name in st.session_state.portfolio:
                # 기존 보유 종목의 평균 단가 계산
                existing_shares = st.session_state.portfolio[stock_name]['shares']
                existing_avg_price = st.session_state.portfolio[stock_name]['avg_price']
                new_avg_price = (existing_shares * existing_avg_price + quantity * price) / (existing_shares + quantity)
                
                st.session_state.portfolio[stock_name]['shares'] += quantity
                st.session_state.portfolio[stock_name]['avg_price'] = new_avg_price
            else:
                st.session_state.portfolio[stock_name] = {
                    'shares': quantity,
                    'avg_price': price
                }
            
            # 거래 내역 추가
            new_trade = pd.DataFrame({
                '거래일시': [datetime.now()],
                '종목명': [stock_name],
                '거래구분': [trade_type],
                '수량': [quantity],
                '가격': [price],
                '금액': [total_amount]
            })
            st.session_state.history = pd.concat([st.session_state.history, new_trade], ignore_index=True)
            
            return True, f"✅ {stock_name} {quantity}주를 {price:,}원에 매수했습니다.", None
        else:
            return False, "❌ 현금이 부족합니다.", None
    
    elif trade_type == "매도":
        if stock_name in st.session_state.portfolio and st.session_state.portfolio[stock_name]['shares'] >= quantity:
            avg_buy_price = st.session_state.portfolio[stock_name]['avg_price']
            st.session_state.cash += total_amount
            st.session_state.portfolio[stock_name]['shares'] -= quantity
            
            if st.session_state.portfolio[stock_name]['shares'] == 0:
                del st.session_state.portfolio[stock_name]
            
            # 거래 내역 추가
            new_trade = pd.DataFrame({
                '거래일시': [datetime.now()],
                '종목명': [stock_name],
                '거래구분': [trade_type],
                '수량': [quantity],
                '가격': [price],
                '금액': [total_amount]
            })
            st.session_state.history = pd.concat([st.session_state.history, new_trade], ignore_index=True)
            
            # 손실 체크 (매도가 < 평균 매수가)
            if price < avg_buy_price:
                loss_amount = (avg_buy_price - price) * quantity
                loss_percentage = ((price - avg_buy_price) / avg_buy_price) * 100
                
                return True, f"✅ {stock_name} {quantity}주를 {price:,}원에 매도했습니다.", {
                    'stock_name': stock_name,
                    'loss_amount': loss_amount,
                    'loss_percentage': loss_percentage,
                    'buy_price': avg_buy_price,
                    'sell_price': price,
                    'quantity': quantity
                }
            
            return True, f"✅ {stock_name} {quantity}주를 {price:,}원에 매도했습니다.", None
        else:
            return False, "❌ 보유 수량이 부족합니다.", None
    
    return False, "❌ 알 수 없는 오류가 발생했습니다.", None

def generate_ai_coaching_tip(user_data, user_type):
    """오늘의 AI 코칭 팁 생성"""
    recent_trades = user_data.tail(5)
    
    if len(recent_trades) == 0:
        return "📊 거래 데이터를 축적하여 개인화된 코칭을 받아보세요."
    
    # 최근 거래 패턴 분석
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

def main():
    initialize_session_state()
    update_prices()  # 실시간 가격 업데이트
    
    # 사이드바 네비게이션
    with st.sidebar:
        st.markdown("### 🧠 Re:Mind")
        st.markdown("AI 투자 심리 분석 플랫폼")
        st.markdown("---")
        
        # 사용자 선택 (키보드 입력 방지)
        user_type = st.selectbox(
            "사용자 선택",
            ["김국민 (공포매도형)", "박투자 (추격매수형)"],
            key="user_selector_main"
        )
        
        # 사용자 타입 업데이트
        if "김국민" in user_type:
            current_user = "김국민"
        else:
            current_user = "박투자"
        
        if current_user != getattr(st.session_state, 'current_user', None):
            st.session_state.current_user = current_user
            st.session_state.user_data = load_user_data(current_user)
        
        st.markdown("---")
        
        # 페이지 선택 (키보드 입력 방지)
        page = st.selectbox(
            "페이지 선택",
            ["메인 대시보드", "종목 상세 및 거래", "AI 코칭 센터", "포트폴리오"],
            key="page_selector_main"
        )
        
        # 실시간 잔고 표시 (사이드바에 추가)
        st.markdown("---")
        st.markdown("### 💰 현재 잔고")
        st.markdown(f"**현금:** ₩{st.session_state.cash:,}")
        
        total_stock_value = sum([
            holdings['shares'] * st.session_state.market_data.get(stock, {'price': 50000})['price']
            for stock, holdings in st.session_state.portfolio.items()
        ])
        st.markdown(f"**주식:** ₩{total_stock_value:,}")
        st.markdown(f"**총자산:** ₩{st.session_state.cash + total_stock_value:,}")
        
        # 충전 버튼 추가
        if st.button("💳 자산 충전", key="charge_button", use_container_width=True):
            st.session_state.show_charge_modal = True
            st.rerun()
        
        # 최근 거래 내역 (사이드바에 추가)
        if not st.session_state.history.empty:
            st.markdown("### 📊 최근 거래")
            recent_trades = st.session_state.history.tail(5).iloc[::-1]  # 최근 5개, 역순
            for _, trade in recent_trades.iterrows():
                trade_color = "🔴" if trade['거래구분'] == "매수" else "🔵"
                st.markdown(f"{trade_color} {trade['종목명']} {trade['수량']}주")
                st.caption(f"{trade['거래일시'].strftime('%H:%M:%S')} | ₩{trade['가격']:,}")
    
    # 메인 컨텐츠
    if st.session_state.show_charge_modal:
        show_charge_modal()
    elif page == "메인 대시보드":
        show_main_dashboard()
    elif page == "종목 상세 및 거래":
        show_stock_trading()
    elif page == "AI 코칭 센터":
        show_ai_coaching()
    elif page == "포트폴리오":
        show_portfolio()

def show_main_dashboard():
    """메인 대시보드 표시"""
    st.markdown(f'<h1 class="main-header">{st.session_state.current_user}님의 투자 대시보드</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">실시간 포트폴리오 현황과 AI 투자 인사이트를 확인하세요</p>', unsafe_allow_html=True)
    
    # 포트폴리오 요약 메트릭
    total_stock_value = sum([
        holdings['shares'] * st.session_state.market_data.get(stock, {'price': 50000})['price']
        for stock, holdings in st.session_state.portfolio.items()
    ])
    total_assets = st.session_state.cash + total_stock_value
    total_return = ((total_assets - 50_000_000) / 50_000_000) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">총 자산</div>
            <div class="metric-value">₩ {total_assets:,.0f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">보유 주식</div>
            <div class="metric-value">₩ {total_stock_value:,.0f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">보유 현금</div>
            <div class="metric-value">₩ {st.session_state.cash:,.0f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        return_class = "positive" if total_return >= 0 else "negative"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">총 수익률</div>
            <div class="metric-value {return_class}">{total_return:+.2f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # 실시간 자산 트렌드 차트
    st.markdown("### 📈 실시간 자산 트렌드")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        chart_container = st.empty()
    
    with col2:
        st.markdown('<div class="live-indicator"><div class="live-dot"></div>실시간 업데이트</div>', unsafe_allow_html=True)
        if st.button("🔄 차트 업데이트", key="update_chart"):
            pass  # 차트는 자동으로 업데이트됨
    
    # 실시간 차트 업데이트
    with chart_container.container():
        fig = create_live_chart()
        st.plotly_chart(fig, use_container_width=True)
    
    # 오늘의 AI 코칭 카드
    st.markdown("### 🤖 오늘의 AI 코칭")
    ai_tip = generate_ai_coaching_tip(st.session_state.user_data, st.session_state.current_user)
    
    st.markdown(f'''
    <div class="ai-coaching-card">
        <div class="ai-coaching-title">개인화된 투자 인사이트</div>
        <div class="ai-coaching-content">{ai_tip}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 자동 새로고침 (2초마다, 모달이 열려있지 않을 때만)
    if not st.session_state.show_charge_modal and not st.session_state.show_loss_modal and not st.session_state.show_loss_analysis:
        time.sleep(2)
        st.rerun()

def show_stock_trading():
    """종목 상세 및 거래 페이지"""
    st.markdown('<h1 class="main-header">종목 상세 및 거래</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">실시간 시세 확인 및 모의 거래를 진행하세요</p>', unsafe_allow_html=True)
    
    # 손실 상세 분석 표시
    if st.session_state.show_loss_analysis and st.session_state.loss_info:
        show_loss_analysis(st.session_state.loss_info)
        return
    
    # 손실 모달 표시
    if st.session_state.show_loss_modal and st.session_state.loss_info:
        show_loss_modal(st.session_state.loss_info)
        return
    
    # 종목 선택 (키보드 입력 방지)
    selected_stock = st.selectbox(
        "거래할 종목을 선택하세요",
        list(st.session_state.market_data.keys()),
        key="stock_selector_main"
    )
    
    if selected_stock:
        stock_data = st.session_state.market_data[selected_stock]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 종목 정보 카드
            st.markdown("### 📊 종목 정보")
            
            change_class = "positive" if stock_data['change'] >= 0 else "negative"
            change_symbol = "+" if stock_data['change'] >= 0 else ""
            
            st.markdown(f'''
            <div class="card price-update">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h2 style="margin: 0; color: var(--text-primary);">{selected_stock}</h2>
                    <div style="text-align: right;">
                        <div style="font-size: 24px; font-weight: 700; color: var(--text-primary);">₩ {stock_data['price']:,}</div>
                        <div style="font-size: 14px; font-weight: 600; color: var(--{'positive-color' if stock_data['change'] >= 0 else 'negative-color'});">
                            {change_symbol}{stock_data['change']:.1f}%
                        </div>
                    </div>
                </div>
                <div style="background-color: #F8FAFC; padding: 12px; border-radius: 8px;">
                    <strong>📰 관련 뉴스:</strong> {stock_data['news']}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 가격 차트 (더미 데이터)
            st.markdown("### 📈 가격 차트")
            
            # 더미 차트 데이터 생성
            dates = pd.date_range(start='2024-01-01', end='2024-08-05', freq='D')
            base_price = stock_data['price']
            prices = []
            current_price_sim = base_price * 0.8  # 80%에서 시작
            
            for _ in dates:
                change = np.random.normal(0, 0.02)  # 2% 표준편차
                current_price_sim *= (1 + change)
                prices.append(current_price_sim)
            
            # 마지막 가격을 현재 가격으로 조정
            prices[-1] = base_price
            
            chart_fig = go.Figure()
            chart_fig.add_trace(go.Scatter(
                x=dates,
                y=prices,
                mode='lines',
                name=selected_stock,
                line=dict(color='#3182F6', width=2)
            ))
            
            chart_fig.update_layout(
                height=300,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Pretendard", color="#191919"),
                margin=dict(l=0, r=0, t=0, b=0),
                yaxis=dict(
                    tickformat=',.0f',
                    gridcolor='rgba(229, 232, 235, 0.5)'
                ),
                xaxis=dict(
                    gridcolor='rgba(229, 232, 235, 0.5)'
                )
            )
            
            st.plotly_chart(chart_fig, use_container_width=True)
        
        with col2:
            # 거래 인터페이스
            st.markdown("### 💰 거래 실행")
            
            # 거래 구분을 form 밖으로 이동 (실시간 반응을 위해)
            trade_type = st.selectbox("거래 구분", ["매수", "매도"], key="trade_type_selector")
            
            with st.form("trading_form"):
                quantity = st.number_input("수량", min_value=1, value=10, step=1)
                price = st.number_input("가격", min_value=1000, value=stock_data['price'], step=1000)
                
                total_amount = quantity * price
                st.markdown(f"**총 거래금액: ₩ {total_amount:,}**")
                
                # 거래 타입에 따라 버튼 스타일 변경 (실시간)
                if trade_type == "매수":
                    submit_button = st.form_submit_button("🔴 매수 실행", use_container_width=True, type="primary")
                else:
                    submit_button = st.form_submit_button("🔵 매도 실행", use_container_width=True, type="secondary")
                
                if submit_button:
                    success, message, loss_info = execute_trade(selected_stock, trade_type, quantity, price)
                    if success:
                        st.success(message)
                        
                        # 손실 발생 시 오답노트 유도
                        if loss_info:
                            st.session_state.show_loss_modal = True
                            st.session_state.loss_info = loss_info
                            st.rerun()
                        else:
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error(message)
            
            # 현재 보유 현황
            st.markdown("### 💼 현재 보유 현황")
            
            if selected_stock in st.session_state.portfolio:
                holdings = st.session_state.portfolio[selected_stock]
                current_value = holdings['shares'] * stock_data['price']
                invested_value = holdings['shares'] * holdings['avg_price']
                pnl = current_value - invested_value
                pnl_pct = (pnl / invested_value) * 100
                
                pnl_class = "positive" if pnl >= 0 else "negative"
                
                st.markdown(f'''
                <div class="card">
                    <div><strong>보유 수량:</strong> {holdings['shares']:,}주</div>
                    <div><strong>평균 단가:</strong> ₩ {holdings['avg_price']:,}</div>
                    <div><strong>현재 가치:</strong> ₩ {current_value:,}</div>
                    <div style="color: var(--{pnl_class}-color); font-weight: 700;">
                        <strong>평가손익:</strong> ₩ {pnl:,} ({pnl_pct:+.1f}%)
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("현재 보유하지 않은 종목입니다.")
    
    # 1초마다 자동 새로고침 (조건부)
    if not st.session_state.show_loss_modal and not st.session_state.show_loss_analysis:
        time.sleep(1)
        st.rerun()

def show_ai_coaching():
    """AI 코칭 센터 페이지"""
    st.markdown('<h1 class="main-header">AI 코칭 센터</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">과거 거래를 분석하고 개인화된 투자 헌장을 만들어보세요</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 AI 오답노트", "📜 나의 투자 헌장"])
    
    with tab1:
        st.markdown("### 🔍 AI 오답노트 분석")
        
        # 사용자가 작성한 오답노트 표시
        if st.session_state.user_loss_notes:
            st.markdown("#### 📋 작성된 오답노트")
            
            for i, note in enumerate(reversed(st.session_state.user_loss_notes), 1):
                with st.expander(f"오답노트 #{i}: {note['stock_name']} ({note['timestamp'].strftime('%Y-%m-%d %H:%M')})", expanded=False):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown(f"**📊 거래 정보**")
                        st.markdown(f"- 종목: {note['stock_name']}")
                        st.markdown(f"- 수량: {note['quantity']}주")
                        st.markdown(f"- 매수가: ₩{note['buy_price']:,.0f}")
                        st.markdown(f"- 매도가: ₩{note['sell_price']:,.0f}")
                        st.markdown(f"- 손실: ₩{note['loss_amount']:,.0f} ({note['loss_percentage']:.1f}%)")
                    
                    with col2:
                        st.markdown(f"**🤖 AI 분석**")
                        st.markdown(f"- 해시태그: {' '.join(note['ai_hashtags'])}")
                        st.markdown(f"- 감정 상태: {', '.join(note['emotions'])}")
                        st.markdown(f"- 감정 강도: {note['emotion_intensity']}/10")
                    
                    st.markdown(f"**💬 사용자 코멘트**")
                    st.markdown(f'"{note['user_comment']}"')
                    
                    st.markdown("---")
        
        st.markdown("#### 🔍 과거 손실 거래 분석")
        st.markdown("과거 데이터에서 손실 거래를 선택하여 AI와 함께 분석해보세요")
        
        # 손실 거래 필터링 (기존 코드)
        user_data = st.session_state.user_data
        losing_trades = user_data[user_data['수익률'] < 0].copy()
        
        if len(losing_trades) > 0:
            losing_trades['거래일시'] = pd.to_datetime(losing_trades['거래일시'])
            losing_trades = losing_trades.sort_values('거래일시', ascending=False)
            
            # 거래 선택
            selected_idx = st.selectbox(
                "분석할 손실 거래를 선택하세요",
                losing_trades.index,
                format_func=lambda x: f"{losing_trades.loc[x, '거래일시'].strftime('%Y-%m-%d')} - {losing_trades.loc[x, '종목명']} ({losing_trades.loc[x, '수익률']:.1f}%)",
                key="post_mortem_selector"
            )
            
            selected_trade = losing_trades.loc[selected_idx]
            
            # 객관적 브리핑
            st.markdown("#### 🤖 AI 객관적 브리핑")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f'''
                <div class="card">
                    <h4>📋 거래 상세 정보</h4>
                    <div><strong>거래일:</strong> {selected_trade['거래일시'].strftime('%Y년 %m월 %d일')}</div>
                    <div><strong>종목:</strong> {selected_trade['종목명']} ({selected_trade['종목코드']})</div>
                    <div><strong>거래:</strong> {selected_trade['거래구분']}</div>
                    <div><strong>수량/가격:</strong> {selected_trade['수량']}주 / ₩{selected_trade['가격']:,}</div>
                    <div><strong>감정상태:</strong> <span class="emotion-tag">{selected_trade['감정태그']}</span></div>
                    <div style="color: var(--negative-color); font-weight: 700;"><strong>결과:</strong> {selected_trade['수익률']:.1f}% 손실</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                # 시장 상황 정보
                kospi_change = np.random.normal(-1.0, 2.0)
                
                st.markdown(f'''
                <div class="card">
                    <h4>📊 당시 시장 상황</h4>
                    <div><strong>코스피 지수:</strong> {selected_trade['코스피지수']:.0f}포인트</div>
                    <div><strong>시장 변동:</strong> <span style="color: var(--{'positive' if kospi_change >= 0 else 'negative'}-color);">{kospi_change:+.1f}%</span></div>
                    <div style="margin-top: 12px; padding: 8px; background-color: #F8FAFC; border-radius: 6px; font-size: 14px;">
                        <strong>📰 시장 분위기:</strong> 글로벌 경제 불확실성으로 인한 변동성 확대
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 사용자 자기반성
            st.markdown("#### ✏️ 사용자 자기반성")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                emotion_selection = st.selectbox(
                    "당시 주요 감정:",
                    ["#공포", "#패닉", "#불안", "#추격매수", "#욕심", "#확신", "#합리적"],
                    key="emotion_selector"
                )
            
            with col2:
                user_reflection = st.text_area(
                    "이 거래에 대한 생각을 기록해주세요:",
                    height=120,
                    placeholder="당시의 결정 과정이나 현재의 생각을 자유롭게 기록해주세요.",
                    key="reflection_text"
                )
            
            # AI 분석 버튼
            if st.button("🔍 AI 증거 기반 분석 받기", type="primary", use_container_width=True):
                if user_reflection:
                    st.markdown("#### 🤖 AI 증거 기반 분석")
                    
                    # AI 분석 실행
                    analysis = st.session_state.engine.analyze_emotion_text(user_reflection, st.session_state.current_user)
                    
                    # 증거 제시
                    st.markdown(f'''
                    <div class="card" style="background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%); border: 1px solid #BFDBFE;">
                        <h4>🔍 발견된 증거</h4>
                        <ul>
                            <li><strong>감정 키워드:</strong> 귀하의 메모에서 '{', '.join(analysis['keywords']) if analysis['keywords'] else '특별한 키워드 없음'}' 등이 발견되었습니다.</li>
                            <li><strong>패턴 분석:</strong> 이 거래는 '{analysis['pattern']}' 패턴과 {analysis['confidence']*100:.0f}% 일치합니다.</li>
                            <li><strong>시장 대비 성과:</strong> 이 거래의 수익률({selected_trade['수익률']:.1f}%)은 시장 평균({kospi_change:.1f}%)보다 저조했습니다.</li>
                        </ul>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # AI 가이드
                    st.markdown(f'''
                    <div class="card" style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #86EFAC;">
                        <h4>💡 AI 자기반성 가이드</h4>
                        <p>이러한 증거들을 종합해 볼 때, 이 거래가 '{analysis['pattern']}' 패턴일 가능성을 고려해볼 수 있습니다. 
                        향후 유사한 상황에서는 감정적인 판단을 피하고, 24시간의 냉각기간을 갖는 것을 고려해보세요.</p>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.warning("분석을 위해 생각을 입력해주세요.")
        else:
            st.info("분석할 손실 거래가 없습니다.")
    
    with tab2:
        st.markdown("### 📜 나의 투자 헌장")
        st.markdown("거래 데이터를 기반으로 개인화된 투자 규칙을 생성합니다")
        
        if st.button("🎯 투자 헌장 생성하기", type="primary", use_container_width=True):
            charter_rules = st.session_state.engine.generate_investment_charter_rules(
                st.session_state.user_data, st.session_state.current_user
            )
            
            if charter_rules:
                st.markdown(f"#### 🎯 {st.session_state.current_user}님만의 개인화된 규칙")
                
                approved_rules = []
                
                for i, rule in enumerate(charter_rules):
                    with st.expander(f"규칙 {i+1}: {rule['rule']}", expanded=True):
                        st.markdown(f'''
                        <div class="charter-rule">
                            <div class="charter-rule-title">{rule['rule']}</div>
                            <div class="charter-rule-description">
                                <strong>📊 근거:</strong> {rule['rationale']}<br>
                                <strong>📈 데이터:</strong> {rule['evidence']}<br>
                                <strong>📂 분류:</strong> {rule['category']}
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        if st.checkbox(f"이 규칙을 승인합니다", key=f"approve_rule_{i}"):
                            approved_rules.append(rule)
                
                # 승인된 규칙으로 최종 헌장 생성
                if approved_rules:
                    st.markdown("#### ✅ 승인된 투자 헌장")
                    
                    st.markdown(f'''
                    <div class="card" style="background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); border: 1px solid #FDBA74;">
                        <h2 style="text-align: center; margin: 0 0 2rem 0; color: var(--text-primary);">📜 {st.session_state.current_user}님의 투자 헌장</h2>
                        <p style="text-align: center; font-style: italic; color: var(--text-secondary); margin-bottom: 2rem;">2024년 8월 5일 작성</p>
                        
                        <h3 style="color: var(--text-primary); margin-bottom: 1rem;">🎯 핵심 원칙</h3>
                    ''', unsafe_allow_html=True)
                    
                    for i, rule in enumerate(approved_rules, 1):
                        st.markdown(f'''
                        <div style="margin: 1rem 0;">
                            <strong>{i}. {rule['rule']}</strong><br>
                            <em style="color: var(--text-secondary);">→ {rule['rationale']} ({rule['evidence']})</em>
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    st.markdown(f'''
                        <div style="text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #FDBA74;">
                            <p><strong>서명:</strong> {st.session_state.current_user} &nbsp;&nbsp;&nbsp; <strong>날짜:</strong> 2024년 8월 5일</p>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.info("충분한 거래 데이터가 없어 투자 헌장을 생성할 수 없습니다.")

def show_portfolio():
    """포트폴리오 페이지"""
    st.markdown('<h1 class="main-header">포트폴리오</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">현재 보유 종목과 전체 거래 내역을 확인하세요</p>', unsafe_allow_html=True)
    
    # 현재 보유 종목
    st.markdown("### 💼 현재 보유 종목")
    
    if st.session_state.portfolio:
        portfolio_data = []
        
        for stock_name, holdings in st.session_state.portfolio.items():
            current_price = st.session_state.market_data.get(stock_name, {'price': 50000})['price']
            current_value = holdings['shares'] * current_price
            invested_value = holdings['shares'] * holdings['avg_price']
            pnl = current_value - invested_value
            pnl_pct = (pnl / invested_value) * 100 if invested_value > 0 else 0
            
            portfolio_data.append({
                '종목명': stock_name,
                '보유수량': f"{holdings['shares']:,}주",
                '평균매수가': f"₩ {holdings['avg_price']:,}",
                '현재가': f"₩ {current_price:,}",
                '평가금액': f"₩ {current_value:,}",
                '평가손익': f"₩ {pnl:,} ({pnl_pct:+.1f}%)"
            })
        
        portfolio_df = pd.DataFrame(portfolio_data)
        st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
    else:
        st.info("현재 보유 중인 종목이 없습니다.")
    
    # 전체 거래 내역
    st.markdown("### 📊 전체 거래 내역")
    
    if not st.session_state.history.empty:
        history_display = st.session_state.history.copy()
        history_display['거래일시'] = pd.to_datetime(history_display['거래일시']).dt.strftime('%Y-%m-%d %H:%M')
        history_display['가격'] = history_display['가격'].apply(lambda x: f"₩ {x:,}")
        history_display['금액'] = history_display['금액'].apply(lambda x: f"₩ {x:,}")
        
        st.dataframe(history_display, use_container_width=True, hide_index=True)
    else:
        st.info("거래 내역이 없습니다.")
    
    # 과거 거래 데이터 (사용자 데이터에서)
    st.markdown("### 📈 과거 거래 분석")
    
    user_data = st.session_state.user_data
    
    # 감정별 성과 분석
    col1, col2 = st.columns(2)
    
    with col1:
        # 감정별 평균 수익률
        emotion_performance = user_data.groupby('감정태그')['수익률'].mean().sort_values()
        
        fig_emotion = px.bar(
            x=emotion_performance.values,
            y=emotion_performance.index,
            orientation='h',
            title="감정별 평균 수익률",
            color=emotion_performance.values,
            color_continuous_scale=['red', 'yellow', 'green']
        )
        
        fig_emotion.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Pretendard", color="#191919"),
            showlegend=False,
            coloraxis_showscale=False
        )
        
        st.plotly_chart(fig_emotion, use_container_width=True)
    
    with col2:
        # 월별 거래 횟수
        user_data['거래월'] = pd.to_datetime(user_data['거래일시']).dt.to_period('M')
        monthly_trades = user_data.groupby('거래월').size()
        
        fig_monthly = px.line(
            x=monthly_trades.index.astype(str),
            y=monthly_trades.values,
            title="월별 거래 횟수",
            markers=True
        )
        
        fig_monthly.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Pretendard", color="#191919"),
            showlegend=False
        )
        
        fig_monthly.update_traces(line_color='#3182F6', marker_color='#3182F6')
        
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    # 거래 통계 요약
    st.markdown("### 📊 거래 통계 요약")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_trades = len(user_data)
    avg_return = user_data['수익률'].mean()
    win_rate = len(user_data[user_data['수익률'] > 0]) / len(user_data) * 100
    max_loss = user_data['수익률'].min()
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">총 거래 횟수</div>
            <div class="metric-value">{total_trades}회</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        return_class = "positive" if avg_return >= 0 else "negative"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">평균 수익률</div>
            <div class="metric-value {return_class}">{avg_return:+.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        win_class = "positive" if win_rate >= 50 else "negative"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">승률</div>
            <div class="metric-value {win_class}">{win_rate:.0f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">최대 손실</div>
            <div class="metric-value negative">{max_loss:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()