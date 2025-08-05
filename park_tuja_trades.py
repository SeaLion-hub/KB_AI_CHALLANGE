import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate Park Tuja (FOMO Buyer) dataset
np.random.seed(24)

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

# Park Tuja's emotional pattern (prone to FOMO buying)
emotions_config = {
    '#공포': {'base_return': -15, 'volatility': 12, 'freq': 0.1},
    '#패닉': {'base_return': -18, 'volatility': 15, 'freq': 0.08},
    '#불안': {'base_return': -8, 'volatility': 10, 'freq': 0.12},
    '#추격매수': {'base_return': -12, 'volatility': 20, 'freq': 0.35},  # Much higher frequency
    '#욕심': {'base_return': -10, 'volatility': 25, 'freq': 0.2},      # Higher frequency
    '#확신': {'base_return': 5, 'volatility': 8, 'freq': 0.1},
    '#합리적': {'base_return': 7, 'volatility': 6, 'freq': 0.05}
}

# Memo templates for Park Tuja (focused on FOMO)
memo_templates = {
    '#공포': [
        "코스피 폭락하니까 {종목명} 급히 손절했음",
        "너무 무서워서 {종목명} 전량 매도, 더 떨어지기 전에"
    ],
    '#패닉': [
        "패닉장이다... {종목명} 지금 당장 다 팔아야 함",
        "{종목명} 폭락, 더 이상 못 견디겠어서 전량 매도"
    ],
    '#불안': [
        "마음이 불안해서 {종목명} 절반만 매도",
        "{종목명} 계속 가지고 있기 불안해서 일부 매도"
    ],
    '#추격매수': [
        "어제 {종목명} 상한가 갔는데 오늘이라도 타야겠어서 추격매수",
        "{종목명} 급등 중, 놓치기 아까워서 일단 매수",
        "모두가 {종목명} 산다고 해서 뒤늦게 합류",
        "{종목명} 뉴스 터지고 급등해서 서둘러 매수했음",
        "유튜버가 {종목명} 추천해서 급히 매수",
        "{종목명} 커뮤니티에서 난리나서 FOMO 매수",
        "친구가 {종목명}로 돈 벌었다고 해서 따라 매수",
        "{종목명} 상승장 놓치기 싫어서 추격 매수",
        "주식방에서 {종목명} 대박 예상한다고 해서 매수"
    ],
    '#욕심': [
        "{종목명} 이미 올랐지만 더 오를 것 같아서 추가 매수",
        "쉬운 돈이다 싶어서 {종목명} 물량 늘림",
        "{종목명} 대박날 것 같아서 풀매수",
        "이번엔 확실하다 싶어서 {종목명} 올인",
        "{종목명} 100% 오를 것 같아서 대량 매수",
        "주변에서 {종목명} 추천해서 욕심내서 매수"
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

# Market news templates for FOMO trades
market_news_templates = [
    "[기업] {종목명} 신제품 출시 발표로 급등|[시장] 해당 업종 전반 강세|[증권] 목표주가 상향 조정 러시",
    "[경제] 정부 지원책 발표로 관련주 부각|[시장] 개인투자자 매수세 급증|[증권] 외국인 순매수 전환",
    "[기업] 어닝 서프라이즈 발표 후 급등|[시장] 동종업계 동반 상승|[증권] 증권사 매수 추천 확산",
    "[정치] 관련 규제 완화 기대감|[시장] 테마주 급등 랠리|[증권] 기관 매수 물량 유입",
    "[국제] 글로벌 동종업체 호실적|[시장] 수급 불균형으로 급등|[증권] 공매도 잔량 급감"
]

# Generate data
trades = []
start_date = datetime(2024, 1, 1)

for i in range(120):
    trade_date = start_date + timedelta(days=np.random.randint(0, 300))
    stock = np.random.choice(korean_stocks)
    
    # Select emotion based on frequency (Park Tuja has more FOMO)
    emotions = list(emotions_config.keys())
    frequencies = [config['freq'] for config in emotions_config.values()]
    emotion = np.random.choice(emotions, p=frequencies)
    
    # Generate return
    config = emotions_config[emotion]
    return_pct = np.random.normal(config['base_return'], config['volatility'])
    
    # Generate memo
    memo_template = np.random.choice(memo_templates[emotion])
    memo = memo_template.format(종목명=stock['종목명'])
    
    # Add market news for key FOMO trades
    market_news = ""
    if emotion in ['#추격매수', '#욕심'] and return_pct < -10:
        market_news_template = np.random.choice(market_news_templates)
        market_news = market_news_template.format(종목명=stock['종목명'])
    
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
df.to_csv('park_tuja_trades.csv', index=False, encoding='utf-8-sig')
print("박투자 데이터 생성 완료!")
print(f"총 거래 수: {len(df)}")
print(f"평균 수익률: {df['수익률'].mean():.1f}%")
print("감정별 분포:")
print(df['감정태그'].value_counts())