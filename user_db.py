import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import os

class UserDatabase:
    """사용자별 거래 데이터를 로드하고 관리하는 클래스"""
    
    def __init__(self):
        self.data_path = Path(__file__).parent.parent / "data"
        self.ensure_data_directory()
        self.generate_csv_files_if_not_exist()
    
    def ensure_data_directory(self):
        """data 디렉토리 생성"""
        self.data_path.mkdir(exist_ok=True)
    
    def generate_csv_files_if_not_exist(self):
        """CSV 파일이 없으면 생성"""
        kim_file = self.data_path / "kim_gukmin_trades.csv"
        park_file = self.data_path / "park_tuja_trades.csv"
        
        if not kim_file.exists():
            self.generate_kim_gukmin_data()
        
        if not park_file.exists():
            self.generate_park_tuja_data()
    
    def get_user_trades(self, username):
        """
        사용자별 거래 데이터 반환
        
        Args:
            username (str): 사용자명 (김국민, 박투자)
        
        Returns:
            pd.DataFrame: 거래 데이터 또는 None
        """
        try:
            if username == "김국민":
                file_path = self.data_path / "kim_gukmin_trades.csv"
            elif username == "박투자":
                file_path = self.data_path / "park_tuja_trades.csv"
            else:
                return None  # 이거울은 거래 데이터 없음
            
            if file_path.exists():
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                df['거래일시'] = pd.to_datetime(df['거래일시'])
                return df
            else:
                print(f"파일을 찾을 수 없습니다: {file_path}")
                return None
                
        except Exception as e:
            print(f"데이터 로드 중 오류 발생: {str(e)}")
            return None
    
    def get_user_summary(self, username):
        """
        사용자의 거래 요약 통계 반환
        
        Args:
            username (str): 사용자명
        
        Returns:
            dict: 요약 통계
        """
        trades_data = self.get_user_trades(username)
        
        if trades_data is None or len(trades_data) == 0:
            return None
        
        summary = {
            'total_trades': len(trades_data),
            'avg_return': trades_data['수익률'].mean(),
            'total_return': trades_data['수익률'].sum(),
            'win_rate': (trades_data['수익률'] > 0).mean() * 100,
            'max_gain': trades_data['수익률'].max(),
            'max_loss': trades_data['수익률'].min(),
            'most_common_emotion': trades_data['감정태그'].mode().iloc[0] if len(trades_data) > 0 else None,
            'date_range': {
                'start': trades_data['거래일시'].min(),
                'end': trades_data['거래일시'].max()
            }
        }
        
        return summary
    
    def generate_kim_gukmin_data(self):
        """김국민 거래 데이터 생성 (공포매도형)"""
        print("김국민 데이터 생성 중...")
        
        np.random.seed(42)
        
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
        
        # 김국민의 감정 패턴 (공포매도 성향)
        emotions_config = {
            '#공포': {'base_return': -15, 'volatility': 12, 'freq': 0.3},
            '#패닉': {'base_return': -18, 'volatility': 15, 'freq': 0.2},
            '#불안': {'base_return': -8, 'volatility': 10, 'freq': 0.2},
            '#추격매수': {'base_return': -12, 'volatility': 20, 'freq': 0.1},
            '#욕심': {'base_return': -10, 'volatility': 25, 'freq': 0.08},
            '#확신': {'base_return': 5, 'volatility': 8, 'freq': 0.07},
            '#합리적': {'base_return': 7, 'volatility': 6, 'freq': 0.05}
        }
        
        # 메모 템플릿
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
                '시장뉴스': ""
            }
            trades.append(trade)
        
        df = pd.DataFrame(trades)
        df = df.sort_values('거래일시').reset_index(drop=True)
        
        # CSV 저장
        file_path = self.data_path / "kim_gukmin_trades.csv"
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        print(f"김국민 데이터 생성 완료! ({len(df)}건)")
        print(f"평균 수익률: {df['수익률'].mean():.1f}%")
    
    def generate_park_tuja_data(self):
        """박투자 거래 데이터 생성 (FOMO 매수형)"""
        print("박투자 데이터 생성 중...")
        
        np.random.seed(24)
        
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
        
        # 박투자의 감정 패턴 (FOMO 매수 성향)
        emotions_config = {
            '#공포': {'base_return': -15, 'volatility': 12, 'freq': 0.1},
            '#패닉': {'base_return': -18, 'volatility': 15, 'freq': 0.08},
            '#불안': {'base_return': -8, 'volatility': 10, 'freq': 0.12},
            '#추격매수': {'base_return': -12, 'volatility': 20, 'freq': 0.35},  # 높은 빈도
            '#욕심': {'base_return': -10, 'volatility': 25, 'freq': 0.2},      # 높은 빈도
            '#확신': {'base_return': 5, 'volatility': 8, 'freq': 0.1},
            '#합리적': {'base_return': 7, 'volatility': 6, 'freq': 0.05}
        }
        
        # 메모 템플릿 (FOMO 중심)
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
                '시장뉴스': ""
            }
            trades.append(trade)
        
        df = pd.DataFrame(trades)
        df = df.sort_values('거래일시').reset_index(drop=True)
        
        # CSV 저장
        file_path = self.data_path / "park_tuja_trades.csv"
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        print(f"박투자 데이터 생성 완료! ({len(df)}건)")
        print(f"평균 수익률: {df['수익률'].mean():.1f}%")
    
    def get_top_bottom_trades(self, username, top_n=2, bottom_n=2):
        """
        사용자의 수익률 상/하위 거래 반환
        
        Args:
            username (str): 사용자명
            top_n (int): 상위 n개
            bottom_n (int): 하위 n개
        
        Returns:
            tuple: (상위 거래, 하위 거래)
        """
        trades_data = self.get_user_trades(username)
        
        if trades_data is None or len(trades_data) == 0:
            return None, None
        
        top_trades = trades_data.nlargest(top_n, '수익률')
        bottom_trades = trades_data.nsmallest(bottom_n, '수익률')
        
        return top_trades, bottom_trades
    
    def save_review_note(self, username, trade_id, review_data):
        """
        복기 노트 저장 (향후 구현)
        
        Args:
            username (str): 사용자명
            trade_id (str): 거래 ID
            review_data (dict): 복기 내용
        """
        # 실제 구현에서는 데이터베이스에 저장
        print(f"복기 노트 저장: {username} - {trade_id}")
        return True
    
    def get_review_notes(self, username):
        """
        사용자의 복기 노트 목록 반환 (향후 구현)
        
        Args:
            username (str): 사용자명
        
        Returns:
            list: 복기 노트 목록
        """
        # 실제 구현에서는 데이터베이스에서 조회
        return []
    
    def get_user_statistics(self, username):
        """
        사용자의 상세 통계 반환
        
        Args:
            username (str): 사용자명
        
        Returns:
            dict: 상세 통계
        """
        trades_data = self.get_user_trades(username)
        
        if trades_data is None or len(trades_data) == 0:
            return None
        
        # 월별 통계
        trades_data['month'] = trades_data['거래일시'].dt.to_period('M')
        monthly_stats = trades_data.groupby('month').agg({
            '수익률': ['mean', 'sum', 'count'],
            '감정태그': lambda x: x.mode().iloc[0] if len(x) > 0 else None
        }).round(2)
        
        # 감정별 상세 통계
        emotion_stats = trades_data.groupby('감정태그').agg({
            '수익률': ['mean', 'std', 'min', 'max', 'count'],
            '거래구분': lambda x: (x == '매수').mean() * 100  # 매수 비율
        }).round(2)
        
        # 종목별 통계
        stock_stats = trades_data.groupby('종목명').agg({
            '수익률': ['mean', 'sum', 'count'],
            '감정태그': lambda x: x.mode().iloc[0] if len(x) > 0 else None
        }).round(2)
        
        return {
            'monthly_stats': monthly_stats,
            'emotion_stats': emotion_stats,
            'stock_stats': stock_stats,
            'overall_stats': self.get_user_summary(username)
        }
    # 이 파일을 직접 실행했을 때만 아래 코드가 작동하도록 하는 실행 스위치입니다.
if __name__ == "__main__":
    db = UserDatabase()
    print("✅ 모든 사용자 데이터 파일 생성이 성공적으로 완료되었습니다.")