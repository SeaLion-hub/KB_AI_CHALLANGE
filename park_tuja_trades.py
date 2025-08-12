import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 박투자 (FOMO Buyer) 데이터셋 생성
np.random.seed(24) # 김국민과 다른 시드 사용

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

# 박투자 감정 패턴 (FOMO 매수에 취약)
emotions_config = {
    '#공포': {'base_return': -15, 'volatility': 12, 'freq': 0.1},
    '#패닉': {'base_return': -18, 'volatility': 15, 'freq': 0.08},
    '#불안': {'base_return': -8, 'volatility': 10, 'freq': 0.12},
    '#추격매수': {'base_return': -12, 'volatility': 20, 'freq': 0.35},
    '#욕심': {'base_return': -10, 'volatility': 25, 'freq': 0.2},
    '#확신': {'base_return': 5, 'volatility': 8, 'freq': 0.1},
    '#합리적': {'base_return': 7, 'volatility': 6, 'freq': 0.05}
}

# 박투자 메모 템플릿 (FOMO 중심)
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
        "이번엔 확실하다 싶어서 {종목명} 올인",
        "{종목명} 대박날 것 같아서 풀매수",
        "주변에서 {종목명} 추천해서 욕심내서 매수",
        "{종목명} 100% 오를 것 같아서 대량 매수"
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
    "RSI 과매수 구간 진입으로 단기 조정 예상",
    "이동평균선 상향 돌파로 상승 모멘텀 확인",
    "볼린저밴드 상단 이탈로 강한 상승세 지속",
    "MACD 데드크로스 형성으로 하락 전환 우려",
    "저항선 돌파 실패로 반락 가능성 증가",
    "거래량 감소와 함께 상승 동력 약화",
    "쐐기형 패턴 완성으로 급등 후 조정 예상",
    "피보나치 확장 161.8% 도달로 과열 구간",
    "일목균형표 구름대 상단 저항 직면",
    "스토캐스틱 과매수에서 베어리시 다이버전스"
]

# 뉴스 분석 템플릿
news_analysis_templates = [
    "어닝 서프라이즈 발표로 시장 기대감 급상승",
    "정부 지원 정책 발표로 관련주 테마 부각",
    "글로벌 트렌드 변화로 성장주 선호도 증가",
    "경쟁사 부진으로 상대적 경쟁력 부각",
    "신기술 도입 지연으로 성장 둔화 우려",
    "대규모 투자 계획 발표로 미래 가치 기대",
    "해외 수주 확대로 수출 기업 수혜 기대",
    "업계 재편 가속화로 구조 조정 압력 증가",
    "친환경 정책 강화로 관련 산업 수혜 예상",
    "금리 인하 기대감으로 성장주 재평가"
]

# 감정 분석 템플릿
emotion_analysis_templates = [
    "급등 상황에서 놓칠까 봐 하는 조급한 투자 심리",
    "주변 성공 사례에 자극받아 따라 하는 심리",
    "손실 회복을 위한 무모한 도박성 투자",
    "확실한 수익을 보장받을 수 있다는 착각",
    "시장 상황 변화에 대한 과도한 낙관론",
    "전문가 의견에만 의존하는 수동적 태도",
    "단기 수익에만 집중하는 근시안적 사고",
    "체계적 분석을 통한 냉정한 투자 접근",
    "유행과 트렌드에 휩쓸리기 쉬운 성향",
    "감정적 흥분 상태에서 비합리적 판단"
]

# 데이터 생성
trades = []
start_date = datetime(2024, 1, 1)

for i in range(120):
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

# CSV 파일로 저장
df.to_csv('park_tuja_trades.csv', index=False, encoding='utf-8-sig')
print("박투자 데이터 생성 완료!")
print(f"총 거래 수: {len(df)}")
print(f"평균 수익률: {df['수익률'].mean():.1f}%")
print("감정별 분포:")
print(df['감정태그'].value_counts())