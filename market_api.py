import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import random

class MarketAPI:
    """과거 시점의 시장/종목 정보를 제공하는 더미 API"""
    
    def __init__(self):
        self.stock_codes = {
            '005930': '삼성전자',
            '035720': '카카오',
            '035420': 'NAVER',
            '373220': 'LG에너지솔루션',
            '352820': '하이브',
            '000660': 'SK하이닉스',
            '005380': '현대차',
            '068270': '셀트리온',
            '105560': 'KB금융'
        }
        
        # 더미 뉴스 헤드라인 풀
        self.news_pool = {
            '005930': [  # 삼성전자
                "삼성전자, 3분기 반도체 부문 실적 개선 전망",
                "삼성 갤럭시 S24 시리즈 글로벌 판매량 호조",
                "삼성전자 파운드리 사업, 대형 고객 확보",
                "반도체 업황 회복세에 삼성전자 수혜 기대",
                "삼성전자 HBM 메모리 공급 확대 계획 발표"
            ],
            '035720': [  # 카카오
                "카카오, AI 플랫폼 사업 강화 전략 발표",
                "카카오페이 해외 진출 본격화",
                "카카오톡 월간 활성 사용자 수 증가세",
                "카카오 모빌리티 IPO 추진 소식",
                "카카오엔터테인먼트 콘텐츠 사업 확대"
            ],
            '035420': [  # NAVER
                "네이버 클라우드 플랫폼 성장세 지속",
                "네이버 AI 검색 기능 대폭 개선",
                "네이버웹툰 글로벌 MAU 1억 돌파",
                "네이버 커머스 GMV 증가율 두 자리 수 기록",
                "네이버 자율주행 기술 실증 실험 성공"
            ],
            '373220': [  # LG에너지솔루션
                "LG에너지솔루션 북미 배터리 공장 증설 계획",
                "GM과의 배터리 공급 계약 확대",
                "전기차 배터리 시장 점유율 상승",
                "차세대 NCM 배터리 기술 개발 성공",
                "LG에너지솔루션 ESS 사업 확대"
            ],
            '352820': [  # 하이브
                "방탄소년단 멤버들 개별 활동 활발",
                "하이브 레이블즈 신규 아티스트 데뷔",
                "위버스 플랫폼 글로벌 사용자 증가",
                "하이브 일본 법인 실적 호조",
                "NewJeans 신곡 글로벌 차트 석권"
            ]
        }
        
        # 시장 감정 및 투자자 동향 더미 데이터
        self.market_sentiments = [
            "신중한 관망세", "낙관적 분위기", "불안감 확산", 
            "혼조세", "강세 지속", "약세 우려"
        ]
        
        self.investor_trends = [
            "외국인 순매수", "외국인 순매도", "기관 순매수",
            "기관 순매도", "개인 순매수", "개인 순매도"
        ]
    
    def get_historical_info(self, stock_code, trade_date):
        """
        특정 종목의 과거 특정 날짜 정보를 반환
        
        Args:
            stock_code (str): 종목 코드
            trade_date (date): 거래 일자
        
        Returns:
            dict: 과거 시점의 종목 정보
        """
        try:
            stock_name = self.stock_codes.get(stock_code, "알 수 없는 종목")
            
            # 시드 설정 (날짜 기반으로 일관된 데이터 생성)
            seed_value = int(trade_date.strftime('%Y%m%d')) + int(stock_code)
            np.random.seed(seed_value)
            random.seed(seed_value)
            
            # 기본 주가 정보 (더미 데이터)
            base_price = self._get_base_price(stock_code)
            price_variation = np.random.normal(0, 0.15)  # ±15% 변동
            historical_price = int(base_price * (1 + price_variation))
            historical_price = max(1000, historical_price)  # 최소 1000원
            
            # 등락률
            change_pct = np.random.normal(0, 3)  # 평균 0%, 표준편차 3%
            
            # 거래량
            base_volume = self._get_base_volume(stock_code)
            volume_variation = np.random.normal(1, 0.3)
            volume = max(100000, int(base_volume * volume_variation))
            
            # 시가총액 (더미)
            shares_outstanding = self._get_shares_outstanding(stock_code)
            market_cap = int((historical_price * shares_outstanding) / 100000000)  # 억 단위
            
            # 기술적 지표 (더미)
            indicators = {
                'RSI': round(np.random.uniform(20, 80), 1),
                'MACD': round(np.random.normal(0, 5), 2),
                'Stochastic': round(np.random.uniform(10, 90), 1),
                'Volume MA': f"{volume // 1000}K"
            }
            
            # 관련 뉴스
            news_headlines = self._get_news_headlines(stock_code, trade_date)
            
            # 시장 분위기
            market_sentiment = random.choice(self.market_sentiments)
            investor_trend = random.choice(self.investor_trends)
            
            return {
                'stock_name': stock_name,
                'stock_code': stock_code,
                'date': trade_date,
                'price': historical_price,
                'change': round(change_pct, 1),
                'volume': volume,
                'market_cap': market_cap,
                'indicators': indicators,
                'news': news_headlines,
                'market_sentiment': market_sentiment,
                'investor_trend': investor_trend
            }
            
        except Exception as e:
            print(f"Error in get_historical_info: {str(e)}")
            return None
    
    def get_current_market_data(self):
        """현재 시장 데이터 반환 (실시간 시뮬레이션용)"""
        market_data = {}
        
        for stock_code, stock_name in self.stock_codes.items():
            base_price = self._get_base_price(stock_code)
            current_change = np.random.normal(0, 2)  # ±2% 정도 변동
            
            # 더미 뉴스
            news_options = [
                f"{stock_name} 3분기 실적 전망 긍정적",
                f"{stock_name} 신규 사업 진출 계획",
                f"{stock_name} 주가 목표가 상향 조정",
                f"{stock_name} 업종 내 경쟁력 강화",
                f"{stock_name} 글로벌 시장 확대 추진"
            ]
            
            market_data[stock_name] = {
                'price': int(base_price),
                'change': round(current_change, 1),
                'news': np.random.choice(news_options)
            }
        
        return market_data
    
    def _get_base_price(self, stock_code):
        """종목별 기준 가격 반환"""
        base_prices = {
            '005930': 75000,   # 삼성전자
            '035720': 45000,   # 카카오
            '035420': 180000,  # NAVER
            '373220': 420000,  # LG에너지솔루션
            '352820': 155000,  # 하이브
            '000660': 125000,  # SK하이닉스
            '005380': 190000,  # 현대차
            '068270': 95000,   # 셀트리온
            '105560': 78000    # KB금융
        }
        return base_prices.get(stock_code, 50000)
    
    def _get_base_volume(self, stock_code):
        """종목별 기준 거래량 반환"""
        base_volumes = {
            '005930': 15000000,  # 삼성전자
            '035720': 8000000,   # 카카오
            '035420': 2000000,   # NAVER
            '373220': 1500000,   # LG에너지솔루션
            '352820': 3000000,   # 하이브
            '000660': 5000000,   # SK하이닉스
            '005380': 2500000,   # 현대차
            '068270': 1200000,   # 셀트리온
            '105560': 1800000    # KB금융
        }
        return base_volumes.get(stock_code, 1000000)
    
    def _get_shares_outstanding(self, stock_code):
        """종목별 발행주식수 반환 (더미)"""
        shares = {
            '005930': 5969782550,  # 삼성전자
            '035720': 434417010,   # 카카오
            '035420': 161480000,   # NAVER
            '373220': 191820000,   # LG에너지솔루션
            '352820': 42134293,    # 하이브
            '000660': 728002365,   # SK하이닉스
            '005380': 1417856846,  # 현대차
            '068270': 144070000,   # 셀트리온
            '105560': 682585907    # KB금융
        }
        return shares.get(stock_code, 100000000)
    
    def _get_news_headlines(self, stock_code, trade_date):
        """종목별 뉴스 헤드라인 생성"""
        if stock_code not in self.news_pool:
            stock_name = self.stock_codes.get(stock_code, "해당 종목")
            return [
                f"{stock_name} 관련 주요 뉴스 없음",
                f"{stock_name} 업종 전반 안정세",
                f"{stock_name} 시장 관심도 증가"
            ]
        
        # 날짜를 시드로 사용하여 일관된 뉴스 선택
        random.seed(int(trade_date.strftime('%Y%m%d')))
        available_news = self.news_pool[stock_code].copy()
        
        # 3-5개의 뉴스 헤드라인 선택
        num_news = random.randint(3, min(5, len(available_news)))
        selected_news = random.sample(available_news, num_news)
        
        return selected_news
    
    def get_market_indices(self, trade_date):
        """특정 날짜의 시장 지수 정보 반환"""
        # 날짜 기반 시드 설정
        np.random.seed(int(trade_date.strftime('%Y%m%d')))
        
        # 코스피 기준값 (2400 근처)
        kospi_base = 2400
        kospi_change = np.random.normal(0, 50)  # ±50포인트 변동
        kospi = round(kospi_base + kospi_change, 2)
        kospi_change_pct = round((kospi_change / kospi_base) * 100, 2)
        
        # 코스닥
        kosdaq_base = 800
        kosdaq_change = np.random.normal(0, 30)
        kosdaq = round(kosdaq_base + kosdaq_change, 2)
        kosdaq_change_pct = round((kosdaq_change / kosdaq_base) * 100, 2)
        
        return {
            'kospi': {
                'value': kospi,
                'change': kospi_change,
                'change_pct': kospi_change_pct
            },
            'kosdaq': {
                'value': kosdaq,
                'change': kosdaq_change,
                'change_pct': kosdaq_change_pct
            },
            'date': trade_date
        }
    
    def get_sector_performance(self, trade_date):
        """특정 날짜의 업종별 성과 반환"""
        sectors = [
            '반도체', '인터넷', '게임', '바이오', '자동차', 
            '금융', '화학', '철강', '조선', '건설'
        ]
        
        # 날짜 기반 시드 설정
        np.random.seed(int(trade_date.strftime('%Y%m%d')))
        
        sector_performance = {}
        for sector in sectors:
            change_pct = round(np.random.normal(0, 2.5), 2)
            sector_performance[sector] = {
                'change_pct': change_pct,
                'rank': None  # 나중에 정렬 후 순위 부여
            }
        
        # 성과순으로 정렬하여 순위 부여
        sorted_sectors = sorted(sector_performance.items(), 
                              key=lambda x: x[1]['change_pct'], 
                              reverse=True)
        
        for rank, (sector, data) in enumerate(sorted_sectors, 1):
            sector_performance[sector]['rank'] = rank
        
        return sector_performance
    
    def get_economic_indicators(self, trade_date):
        """특정 날짜 기준 경제 지표 반환"""
        # 날짜 기반 시드 설정
        np.random.seed(int(trade_date.strftime('%Y%m%d')))
        
        indicators = {
            'usd_krw': {
                'value': round(1300 + np.random.normal(0, 100), 0),
                'change': round(np.random.normal(0, 20), 1),
                'name': '달러/원 환율'
            },
            'oil_wti': {
                'value': round(80 + np.random.normal(0, 15), 1),
                'change': round(np.random.normal(0, 3), 1),
                'name': 'WTI 유가 (달러/배럴)'
            },
            'gold': {
                'value': round(2000 + np.random.normal(0, 200), 0),
                'change': round(np.random.normal(0, 30), 1),
                'name': '금 가격 (달러/온스)'
            },
            'bitcoin': {
                'value': round(45000 + np.random.normal(0, 10000), 0),
                'change': round(np.random.normal(0, 8), 1),
                'name': '비트코인 (달러)'
            }
        }
        
        return indicators
    
    def is_trading_day(self, check_date):
        """주어진 날짜가 거래일인지 확인"""
        # 주말 체크
        if check_date.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 간단한 공휴일 체크 (실제로는 더 복잡한 로직 필요)
        holidays = [
            (1, 1),   # 신정
            (3, 1),   # 삼일절  
            (5, 5),   # 어린이날
            (6, 6),   # 현충일
            (8, 15),  # 광복절
            (10, 3),  # 개천절
            (10, 9),  # 한글날
            (12, 25), # 크리스마스
        ]
        
        month_day = (check_date.month, check_date.day)
        if month_day in holidays:
            return False
        
        return True
    
    def get_previous_trading_day(self, from_date):
        """주어진 날짜로부터 이전 거래일 찾기"""
        current_date = from_date - timedelta(days=1)
        
        while not self.is_trading_day(current_date):
            current_date -= timedelta(days=1)
        
        return current_date