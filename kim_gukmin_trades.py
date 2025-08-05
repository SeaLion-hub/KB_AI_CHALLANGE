import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate Kim Gukmin (Panic Seller) dataset
np.random.seed(42)

# Korean stocks
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

# Kim Gukmin's emotional pattern (prone to panic selling)
emotions_config = {
    '#공포': {'base_return': -15, 'volatility': 12, 'freq': 0.3},
    '#패닉': {'base_return': -18, 'volatility': 15, 'freq': 0.2},
    '#불안': {'base_return': -8, 'volatility': 10, 'freq': 0.2},
    '#추격매수': {'base_return': -12, 'volatility': 20, 'freq': 0.1},
    '#욕심': {'base_return': -10, 'volatility': 25, 'freq': 0.08},
    '#확신': {'base_return': 5, 'volatility': 8, 'freq': 0.07},
    '#합리적': {'base_return': 7, 'volatility': 6, 'freq': 0.05}
}

# Memo templates for Kim Gukmin
memo_templates = {
    '#공포': [
        "코스피 폭락하니까 {종목명} 급히 손절했음",
        "너무 무서워서 {종목명} 전량 매도, 더 떨어지기 전에",
        "시장 상황이 심상치 않아 {종목명} 손절매로 처리",
        "급락장이라 {종목명} 물량 정리했음",
        "{종목명} 계속 빠지면 큰일날 것 같아서 손절"
    ],
    '#패닉': [
        "패닉장이다... {종목명} 지금 당장 다 팔아야 함",
        "{종목명} 폭락, 더 이상 못 견디겠어서 전량 매도",
        "시장 붕괴될 것 같아 {종목명} 긴급 매도",
        "하한가 갈 것 같아 {종목명} 패닉 매도"
    ],
    '#불안': [
        "마음이 불안해서 {종목명} 절반만 매도",
        "{종목명} 계속 가지고 있기 불안해서 일부 매도",
        "변동성이 너무 커서 {종목명} 비중 줄임"
    ],
    '#추격매수': [
        "어제 {종목명} 상한가 갔는데 오늘이라도 타야겠어서 추격매수",
        "{종목명} 급등 중, 놓치기 아까워서 일단 매수"
    ],
    '#욕심': [
        "{종목명} 이미 올랐지만 더 오를 것 같아서 추가 매수",
        "{종목명} 대박날 것 같아서 풀매수"
    ],
    '#확신': [
        "{종목명} 기술적 분석상 매수 타이밍으로 판단",
        "펀더멘털 분석 결과 {종목명} 저평가, 전략적 매수"
    ],
    '#합리적': [
        "{종목명} 밸류에이션 적정 수준에서 매수",
        "분할 매수 전략으로 {종목명} 추가 매수"
    ]
}

# Market news templates for key trades
market_news_templates = [
    "[경제] 미 연준 금리 인상 우려로 증시 급락|[국제] 글로벌 인플레이션 심화 우려|[시장] 외국인 대량 매도세 지속",
    "[정치] 정부 부동산 정책 발표로 시장 불안|[경제] 원/달러 환율 급등으로 수입 부담 증가|[기업] 대형 IPO 물량 출회로 유동성 부족",
    "[국제] 중국 경제성장률 둔화 우려|[시장] 개인투자자 패닉셀링 확산|[경제] 물가상승률 목표치 초과로 긴축 정책 우려",
    "[기업] 주요 기업 실적 부진 발표|[시장] 코스피 2400선 붕괴 우려|[경제] 수출 둔화로 경기침체 우려",
    "[국제] 미중 무역갈등 재점화|[정치] 정치적 불확실성 증가|[시장] 기관투자자 매도 우세"
]

# Generate data
trades = []
start_date = datetime(2024, 1, 1)

for i in range(120):
    trade_date = start_date + timedelta(days=np.random.randint(0, 300))
    stock = np.random.choice(korean_stocks)
    
    # Select emotion based on frequency
    emotions = list(emotions_config.keys())
    frequencies = [config['freq'] for config in emotions_config.values()]
    emotion = np.random.choice(emotions, p=frequencies)
    
    # Generate return
    config = emotions_config[emotion]
    return_pct = np.random.normal(config['base_return'], config['volatility'])
    
    # Generate memo
    memo_template = np.random.choice(memo_templates[emotion])
    memo = memo_template.format(종목명=stock['종목명'])
    
    # Add market news for key panic selling trades
    market_news = ""
    if emotion in ['#공포', '#패닉'] and return_pct < -15:
        market_news = np.random.choice(market_news_templates)
    
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
        '시장뉴스': market_news
    }
    trades.append(trade)

df = pd.DataFrame(trades)
df = df.sort_values('거래일시').reset_index(drop=True)

# Save to CSV
df.to_csv('kim_gukmin_trades.csv', index=False, encoding='utf-8-sig')
print("김국민 데이터 생성 완료!")
print(f"총 거래 수: {len(df)}")
print(f"평균 수익률: {df['수익률'].mean():.1f}%")
print("감정별 분포:")
print(df['감정태그'].value_counts())