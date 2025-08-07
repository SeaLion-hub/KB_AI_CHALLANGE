# data_service.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

def generate_sample_data(user_type):
    """기술/뉴스/감정 분석이 포함된 샘플 데이터 생성"""
    np.random.seed(42 if user_type == "김국민" else 24)
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
    technical_analysis_templates = [
        "RSI 과매도 구간 진입, 반등 신호 감지",
        "이동평균선 하향 돌파로 추가 하락 우려",
        "볼린저밴드 상단 터치 후 조정 예상",
        "MACD 골든크로스 형성으로 상승 전환",
        "지지선 이탈로 하락 가속화 가능성",
        "거래량 급증과 함께 돌파 신호",
        "삼각수렴 패턴 완성 후 방향성 주목",
        "피보나치 되돌림 61.8% 지지선 테스트"
    ]
    news_analysis_templates = [
        "분기 실적 발표 앞두고 기대감 상승",
        "정부 규제 완화 소식으로 업종 전반 호재",
        "글로벌 공급망 이슈로 원자재 가격 상승",
        "경쟁사 호실적 발표로 동반 상승 기대",
        "신제품 출시 연기로 실망감 확산",
        "대주주 지분 매각 소식으로 우려 증가",
        "해외 진출 확대 계획 발표로 성장성 부각",
        "업계 전반 수요 둔화 우려로 주가 부담"
    ]
    emotion_analysis_templates = [
        "시장 하락에 대한 과도한 공포감 지배",
        "급등에 따른 FOMO 심리로 충동적 매수",
        "손실 회복 욕구로 무리한 레버리지",
        "과도한 자신감으로 리스크 관리 소홀",
        "불확실성 증가로 불안감 확산",
        "타인 추천에 의존한 주체성 부족",
        "단기 수익 욕심으로 조급한 매매",
        "냉정한 분석 기반의 합리적 판단"
    ]
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
    else:
        emotions_config = {
            '#공포': {'base_return': -15, 'volatility': 12, 'freq': 0.1},
            '#패닉': {'base_return': -18, 'volatility': 15, 'freq': 0.08},
            '#불안': {'base_return': -8, 'volatility': 10, 'freq': 0.12},
            '#추격매수': {'base_return': -12, 'volatility': 20, 'freq': 0.35},
            '#욕심': {'base_return': -10, 'volatility': 25, 'freq': 0.2},
            '#확신': {'base_return': 5, 'volatility': 8, 'freq': 0.1},
            '#합리적': {'base_return': 7, 'volatility': 6, 'freq': 0.05}
        }
    memo_templates = {
        '#공포': [f"{{종목명}} 폭락해서 무서워서 손절", f"너무 무서워서 {{종목명}} 전량 매도"],
        '#추격매수': [f"{{종목명}} 급등해서 놓치기 아까워서 매수", f"어제 {{종목명}} 상한가 갔는데 추격매수"],
        '#욕심': [f"{{종목명}} 대박날 것 같아서 추가 매수", f"{{종목명}} 더 오를 것 같아서 풀매수"],
        '#합리적': [f"{{종목명}} 기술적 분석상 매수 타이밍", f"펀더멘털 분석 후 {{종목명}} 매수"]
    }
    for emotion in emotions_config.keys():
        if emotion not in memo_templates:
            memo_templates[emotion] = [f"{emotion} 상태에서 {{종목명}} 거래"]
    trades = []
    start_date = datetime(2024, 1, 1)
    for i in range(100):
        trade_date = start_date + timedelta(days=np.random.randint(0, 240))
        stock = np.random.choice(korean_stocks)
        emotions = list(emotions_config.keys())
        frequencies = [config['freq'] for config in emotions_config.values()]
        emotion = np.random.choice(emotions, p=frequencies)
        config = emotions_config[emotion]
        return_pct = np.random.normal(config['base_return'], config['volatility'])
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
    return df

def load_user_data_from_csv(user_type):
    """CSV 파일에서 사용자 데이터 로드"""
    try:
        if user_type == "김국민":
            df = pd.read_csv('kim_gukmin_trades.csv', encoding='utf-8-sig')
        else:
            df = pd.read_csv('park_tuja_trades.csv', encoding='utf-8-sig')
        
        # 날짜 컬럼 변환
        df['거래일시'] = pd.to_datetime(df['거래일시'])
        return df
    except FileNotFoundError:
        st.warning(f"CSV 파일을 찾을 수 없습니다. 샘플 데이터를 생성합니다.")
        return generate_sample_data(user_type)

def load_user_data_from_csv(user_type):
    """CSV 파일에서 사용자 데이터 로드, 없으면 샘플 데이터 생성"""
    try:
        if user_type == "김국민":
            df = pd.read_csv('kim_gukmin_trades.csv', encoding='utf-8-sig')
        else:
            df = pd.read_csv('park_tuja_trades.csv', encoding='utf-8-sig')
        
        # 날짜 컬럼 변환
        df['거래일시'] = pd.to_datetime(df['거래일시'])
        return df
    except FileNotFoundError:
        st.warning(f"CSV 파일을 찾을 수 없습니다. 샘플 데이터를 생성합니다.")
        return generate_sample_data(user_type)
    """기술/뉴스/감정 분석이 포함된 샘플 데이터 생성"""
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
    
    # 기술적 분석 템플릿
    technical_analysis_templates = [
        "RSI 과매도 구간 진입, 반등 신호 감지",
        "이동평균선 하향 돌파로 추가 하락 우려",
        "볼린저밴드 상단 터치 후 조정 예상",
        "MACD 골든크로스 형성으로 상승 전환",
        "지지선 이탈로 하락 가속화 가능성",
        "거래량 급증과 함께 돌파 신호",
        "삼각수렴 패턴 완성 후 방향성 주목",
        "피보나치 되돌림 61.8% 지지선 테스트"
    ]
    
    # 뉴스 분석 템플릿
    news_analysis_templates = [
        "분기 실적 발표 앞두고 기대감 상승",
        "정부 규제 완화 소식으로 업종 전반 호재",
        "글로벌 공급망 이슈로 원자재 가격 상승",
        "경쟁사 호실적 발표로 동반 상승 기대",
        "신제품 출시 연기로 실망감 확산",
        "대주주 지분 매각 소식으로 우려 증가",
        "해외 진출 확대 계획 발표로 성장성 부각",
        "업계 전반 수요 둔화 우려로 주가 부담"
    ]
    
    # 감정 분석 템플릿  
    emotion_analysis_templates = [
        "시장 하락에 대한 과도한 공포감 지배",
        "급등에 따른 FOMO 심리로 충동적 매수",
        "손실 회복 욕구로 무리한 레버리지",
        "과도한 자신감으로 리스크 관리 소홀",
        "불확실성 증가로 불안감 확산",
        "타인 추천에 의존한 주체성 부족",
        "단기 수익 욕심으로 조급한 매매",
        "냉정한 분석 기반의 합리적 판단"
    ]
    
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
            '기술분석': np.random.choice(technical_analysis_templates),
            '뉴스분석': np.random.choice(news_analysis_templates),
            '감정분석': np.random.choice(emotion_analysis_templates)
        }
        trades.append(trade)
    
    df = pd.DataFrame(trades)
    df = df.sort_values('거래일시').reset_index(drop=True)
    
    return df

def initialize_market_data():
    """시장 데이터 초기화"""
    return {
        '삼성전자': {'price': 75000, 'change': 2.1, 'news': '3분기 실적 개선 전망'},
        '카카오': {'price': 45000, 'change': -1.5, 'news': '카카오페이 IPO 계획 발표'},
        'NAVER': {'price': 180000, 'change': 0.8, 'news': '클라우드 사업 확장'},
        'LG에너지솔루션': {'price': 420000, 'change': 3.2, 'news': '북미 배터리 공장 증설'},
        '하이브': {'price': 155000, 'change': -2.8, 'news': 'BTS 멤버 입대 영향 우려'},
        'SK하이닉스': {'price': 125000, 'change': 1.7, 'news': '메모리 반도체 수급 개선'},
        '현대차': {'price': 190000, 'change': 0.3, 'news': '전기차 판매량 증가'},
        'KB금융': {'price': 78000, 'change': -0.5, 'news': '금리 인상 기대감'}
    }

def update_prices(market_data):
    """실시간 가격 업데이트"""
    for stock_name in market_data:
        # ±2% 범위 내에서 랜덤 변동
        change = np.random.normal(0, 0.02)
        new_price = max(1000, int(market_data[stock_name]['price'] * (1 + change)))
        market_data[stock_name]['price'] = new_price
        market_data[stock_name]['change'] = np.random.normal(0, 3)
    
    return market_data