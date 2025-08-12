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

# 기술적 분석 템플릿
technical_analysis_templates = [
    "RSI 과매도 구간 진입, 반등 신호 감지됨",
    "이동평균선 하향 돌파로 추가 하락 우려",
    "볼린저밴드 상단 터치 후 조정 예상",
    "MACD 골든크로스 형성으로 상승 전환 기대",
    "지지선 이탈로 하락 가속화 가능성",
    "거래량 급증과 함께 돌파 신호 확인",
    "삼각수렴 패턴 완성 후 방향성 주목 필요",
    "피보나치 되돌림 61.8% 지지선 테스트 중",
    "일목균형표 구름대 아래 위치로 약세 지속",
    "스토캐스틱 과매수 구간에서 다이버전스 발생"
]

# 뉴스 분석 템플릿
news_analysis_templates = [
    "분기 실적 발표 앞두고 시장 기대감 상승",
    "정부 규제 완화 소식으로 업종 전반 호재 분위기",
    "글로벌 공급망 이슈로 원자재 가격 상승 압박",
    "경쟁사 호실적 발표로 동반 상승 기대감 확산",
    "신제품 출시 연기 소식으로 시장 실망감 증가",
    "대주주 지분 매각 계획 발표로 투자자 우려 증대",
    "해외 진출 확대 계획으로 중장기 성장성 부각",
    "업계 전반 수요 둔화 우려로 주가 하방 압력",
    "ESG 경영 강화 발표로 기관 투자자 관심 증가",
    "배당금 증액 발표로 배당 투자자들의 관심 집중"
]

# 감정 분석 템플릿
emotion_analysis_templates = [
    "시장 하락에 대한 과도한 공포감이 투자 판단을 흐림",
    "급등에 따른 FOMO 심리로 충동적 매수 결정",
    "손실 회복 욕구로 무리한 레버리지 활용",
    "과도한 자신감으로 리스크 관리 원칙 무시",
    "불확실성 증가로 불안감이 지배적 감정 상태",
    "타인 추천에만 의존하여 주체적 판단 부족",
    "단기 수익 욕심으로 조급한 매매 패턴 반복",
    "냉정한 분석 기반의 합리적 투자 판단 수행",
    "시장 변동성에 과도하게 민감한 반응 보임",
    "군중심리에 휩쓸려 독립적 사고 능력 저하"
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
        '기술분석': np.random.choice(technical_analysis_templates),
        '뉴스분석': np.random.choice(news_analysis_templates),
        '감정분석': np.random.choice(emotion_analysis_templates)
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