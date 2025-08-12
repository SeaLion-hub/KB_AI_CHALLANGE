# data_service.py (배치 처리 최적화 + 복기노트 기능 통합 + 투자 헌장 관리)
"""
Re:Mind 3.1 - 데이터 서비스 (배치 처리 최적화 + 모든 거래 복기 지원 + 성공/실패 원칙 구분 관리)
사용자 거래 데이터 및 시장 데이터 관리 + 복기노트 저장/로드 + 투자 헌장 관리
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import os
import pickle
import hashlib
import time
import json

# AI 서비스 임포트
try:
    from ai_service import (
        preprocess_embeddings_cache, 
        get_embedding_stats,
        check_gemini_api
    )
    AI_SERVICE_AVAILABLE = True
except ImportError:
    AI_SERVICE_AVAILABLE = False

__all__ = [
    "generate_sample_data",
    "load_user_data_from_csv",
    "load_user_data_with_embeddings",
    "save_user_data_to_csv",
    "save_user_data_with_embeddings",
    "get_loss_trade_scenarios",
    "add_dummy_trading_history",
    "initialize_market_data",
    "update_prices",
    "get_market_summary",
    "create_sample_csv_files",
    "validate_user_data",
    "get_user_statistics",
    "clear_embedding_cache",
    "get_embedding_stats_summary",
    # 복기노트 관련 함수들
    "save_note",
    "load_notes",
    "initialize_notes_csv",
    "get_all_trades_for_review",
    "save_trade_reflection",
    # 투자 헌장 관리 함수들 (새로 추가)
    "save_charter",
    "load_charter",
    "initialize_charter_file"
]

# 캐시 설정
CACHE_DIR = "data_cache"
EMBEDDING_CACHE_EXPIRY = 24 * 3600  # 24시간

# 파일 경로 설정
NOTES_CSV_PATH = "notes.csv"
CHARTER_JSON_PATH = "charter.json"

def ensure_cache_directory():
    """캐시 디렉토리 생성"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_key(user_id: str, data_hash: str) -> str:
    """캐시 키 생성"""
    return hashlib.md5(f"{user_id}_{data_hash}".encode()).hexdigest()

def get_data_hash(df: pd.DataFrame) -> str:
    """데이터프레임 해시 생성"""
    if df.empty:
        return "empty"
    
    # 임베딩 컬럼 제외하고 해시 계산
    df_for_hash = df.drop(columns=['embedding'], errors='ignore')
    
    # 데이터프레임을 문자열로 변환하여 해시 계산
    data_str = df_for_hash.to_string()
    return hashlib.md5(data_str.encode()).hexdigest()

# ==================== 투자 헌장 관리 함수들 (새로 추가) ====================

def initialize_charter_file():
    """투자 헌장 JSON 파일 초기화"""
    if not os.path.exists(CHARTER_JSON_PATH):
        # 기본 헌장 구조 생성
        default_charter = {
            "김국민": {
                "success_principles": [],
                "failure_principles": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            "박투자": {
                "success_principles": [],
                "failure_principles": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
        
        try:
            with open(CHARTER_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_charter, f, ensure_ascii=False, indent=2)
            st.info(f"✅ 투자 헌장 파일 {CHARTER_JSON_PATH}을 초기화했습니다.")
        except Exception as e:
            st.error(f"투자 헌장 파일 초기화 중 오류: {e}")

def save_charter(charter_data: dict, user_type: str) -> bool:
    """투자 헌장 저장 (성공 원칙과 실패 원칙 구분)"""
    try:
        initialize_charter_file()
        
        # 기존 헌장 파일 로드
        if os.path.exists(CHARTER_JSON_PATH):
            try:
                with open(CHARTER_JSON_PATH, 'r', encoding='utf-8') as f:
                    all_charters = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # 파일이 손상되었거나 없으면 새로 생성
                all_charters = {}
        else:
            all_charters = {}
        
        # 사용자별 헌장 업데이트
        if user_type not in all_charters:
            all_charters[user_type] = {
                "success_principles": [],
                "failure_principles": [],
                "created_at": datetime.now().isoformat()
            }
        
        # 헌장 데이터 검증 및 업데이트
        user_charter = all_charters[user_type]
        
        # success_principles와 failure_principles 키가 있는지 확인
        if 'success_principles' in charter_data:
            user_charter['success_principles'] = charter_data['success_principles']
        
        if 'failure_principles' in charter_data:
            user_charter['failure_principles'] = charter_data['failure_principles']
        
        # 업데이트 시간 갱신
        user_charter['updated_at'] = datetime.now().isoformat()
        
        # 파일에 저장
        with open(CHARTER_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_charters, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        st.error(f"투자 헌장 저장 중 오류: {e}")
        return False

def load_charter(user_type: str) -> dict:
    """투자 헌장 로드 (성공 원칙과 실패 원칙 구분)"""
    try:
        initialize_charter_file()
        
        if not os.path.exists(CHARTER_JSON_PATH):
            return {
                "success_principles": [],
                "failure_principles": []
            }
        
        with open(CHARTER_JSON_PATH, 'r', encoding='utf-8') as f:
            all_charters = json.load(f)
        
        # 사용자별 헌장 반환
        if user_type in all_charters:
            user_charter = all_charters[user_type]
            
            # 기본 구조 확인 및 보완
            if 'success_principles' not in user_charter:
                user_charter['success_principles'] = []
            if 'failure_principles' not in user_charter:
                user_charter['failure_principles'] = []
            
            return user_charter
        else:
            # 사용자 헌장이 없으면 빈 구조 반환
            return {
                "success_principles": [],
                "failure_principles": []
            }
        
    except Exception as e:
        st.error(f"투자 헌장 로드 중 오류: {e}")
        return {
            "success_principles": [],
            "failure_principles": []
        }

# ==================== 복기노트 관련 함수들 ====================

def initialize_notes_csv():
    """복기노트 CSV 파일 초기화 (trade_type 컬럼 포함)"""
    if not os.path.exists(NOTES_CSV_PATH):
        # 새로운 구조의 notes.csv 생성
        notes_df = pd.DataFrame(columns=[
            'note_id',           # 고유 ID
            'user_type',         # 사용자 유형 (김국민/박투자)
            'stock_name',        # 종목명
            'trade_type',        # 거래 구분 ('buy' 또는 'sell') - 새로 추가
            'quantity',          # 수량
            'buy_price',         # 매수가
            'sell_price',        # 매도가 (매수 복기시 None)
            'loss_amount',       # 손실금액 (수익시 음수)
            'loss_percentage',   # 손실률 (수익시 음수)
            'emotion',           # 감정 상태
            'user_comment',      # 사용자 코멘트
            'ai_hashtags',       # AI 해시태그 (리스트를 문자열로 저장)
            'emotions',          # 감정 목록 (리스트를 문자열로 저장)
            'emotion_intensity', # 감정 강도
            'timestamp',         # 작성 시간
            'trade_date'         # 실제 거래 날짜
        ])
        notes_df.to_csv(NOTES_CSV_PATH, index=False, encoding='utf-8-sig')
        st.info(f"✅ 복기노트 파일 {NOTES_CSV_PATH}을 초기화했습니다.")
    else:
        # 기존 파일이 있으면 구조 확인 및 업데이트
        try:
            existing_notes = pd.read_csv(NOTES_CSV_PATH, encoding='utf-8-sig')
            if 'trade_type' not in existing_notes.columns:
                # trade_type 컬럼이 없으면 추가 (기본값: 'sell' - 기존은 모두 손실 거래였으므로)
                existing_notes['trade_type'] = 'sell'
                existing_notes.to_csv(NOTES_CSV_PATH, index=False, encoding='utf-8-sig')
                st.info("✅ 복기노트 파일을 새로운 구조로 업데이트했습니다.")
        except Exception as e:
            st.warning(f"복기노트 파일 업데이트 중 오류: {e}")

def save_note(note_data: dict) -> bool:
    """복기노트 저장 (trade_type 포함)"""
    try:
        initialize_notes_csv()
        
        # 기존 노트 로드
        if os.path.exists(NOTES_CSV_PATH):
            notes_df = pd.read_csv(NOTES_CSV_PATH, encoding='utf-8-sig')
        else:
            notes_df = pd.DataFrame()
        
        # 새 노트 ID 생성
        note_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        
        # 새 노트 데이터 준비
        new_note = {
            'note_id': note_id,
            'user_type': note_data.get('user_type', '김국민'),
            'stock_name': note_data.get('stock_name', ''),
            'trade_type': note_data.get('trade_type', 'sell'),  # 'buy' 또는 'sell'
            'quantity': note_data.get('quantity', 0),
            'buy_price': note_data.get('buy_price', 0),
            'sell_price': note_data.get('sell_price', None),  # 매수 복기시 None
            'loss_amount': note_data.get('loss_amount', 0),
            'loss_percentage': note_data.get('loss_percentage', 0),
            'emotion': note_data.get('emotion', ''),
            'user_comment': note_data.get('user_comment', ''),
            'ai_hashtags': str(note_data.get('ai_hashtags', [])),  # 리스트를 문자열로 변환
            'emotions': str(note_data.get('emotions', [])),
            'emotion_intensity': note_data.get('emotion_intensity', 5),
            'timestamp': datetime.now().isoformat(),
            'trade_date': note_data.get('trade_date', datetime.now().isoformat())
        }
        
        # 새 노트를 DataFrame에 추가
        new_note_df = pd.DataFrame([new_note])
        notes_df = pd.concat([notes_df, new_note_df], ignore_index=True)
        
        # CSV 파일에 저장
        notes_df.to_csv(NOTES_CSV_PATH, index=False, encoding='utf-8-sig')
        
        return True
        
    except Exception as e:
        st.error(f"복기노트 저장 중 오류: {e}")
        return False

def load_notes(user_type: str = None) -> pd.DataFrame:
    """복기노트 로드 (사용자별 필터링 가능)"""
    try:
        initialize_notes_csv()
        
        if not os.path.exists(NOTES_CSV_PATH):
            return pd.DataFrame()
        
        notes_df = pd.read_csv(NOTES_CSV_PATH, encoding='utf-8-sig')
        
        # 사용자별 필터링
        if user_type:
            notes_df = notes_df[notes_df['user_type'] == user_type]
        
        # 시간순 정렬 (최신순)
        if 'timestamp' in notes_df.columns:
            notes_df['timestamp'] = pd.to_datetime(notes_df['timestamp'])
            notes_df = notes_df.sort_values('timestamp', ascending=False)
        
        return notes_df
        
    except Exception as e:
        st.error(f"복기노트 로드 중 오류: {e}")
        return pd.DataFrame()

def get_all_trades_for_review(user_data: pd.DataFrame) -> pd.DataFrame:
    """모든 거래를 복기 가능하도록 반환 (매수/매도 구분 포함)"""
    if user_data.empty:
        return pd.DataFrame()
    
    try:
        # 복기용 데이터 준비
        review_data = user_data.copy()
        
        # 필요한 컬럼이 있는지 확인
        required_columns = ['거래일시', '종목명', '거래구분', '수량', '가격']
        missing_columns = [col for col in required_columns if col not in review_data.columns]
        
        if missing_columns:
            st.warning(f"복기에 필요한 컬럼이 없습니다: {missing_columns}")
            return pd.DataFrame()
        
        # 거래일시를 datetime으로 변환
        if '거래일시' in review_data.columns:
            review_data['거래일시'] = pd.to_datetime(review_data['거래일시'])
        
        # 최신순으로 정렬
        review_data = review_data.sort_values('거래일시', ascending=False)
        
        # 복기용 표시 텍스트 생성
        review_data['복기_표시'] = review_data.apply(lambda row: 
            f"{row['거래일시'].strftime('%Y-%m-%d')} - {row['종목명']} "
            f"({row['거래구분']}) - {row.get('수익률', 0):.1f}%", axis=1
        )
        
        return review_data
        
    except Exception as e:
        st.error(f"거래 데이터 준비 중 오류: {e}")
        return pd.DataFrame()

def save_trade_reflection(trade_data: dict, reflection_data: dict) -> bool:
    """거래 복기 저장 (매수/매도 모두 지원)"""
    try:
        # trade_type 결정
        trade_type = 'buy' if trade_data.get('거래구분') == '매수' else 'sell'
        
        # 복기노트 데이터 구성
        note_data = {
            'user_type': reflection_data.get('user_type', '김국민'),
            'stock_name': trade_data.get('종목명', ''),
            'trade_type': trade_type,
            'quantity': trade_data.get('수량', 0),
            'buy_price': trade_data.get('가격', 0) if trade_type == 'buy' else reflection_data.get('buy_price', 0),
            'sell_price': trade_data.get('가격', 0) if trade_type == 'sell' else None,
            'loss_amount': reflection_data.get('loss_amount', 0),
            'loss_percentage': trade_data.get('수익률', 0),
            'emotion': reflection_data.get('emotion', ''),
            'user_comment': reflection_data.get('user_comment', ''),
            'ai_hashtags': reflection_data.get('ai_hashtags', []),
            'emotions': reflection_data.get('emotions', []),
            'emotion_intensity': reflection_data.get('emotion_intensity', 5),
            'trade_date': trade_data.get('거래일시', datetime.now().isoformat())
        }
        
        return save_note(note_data)
        
    except Exception as e:
        st.error(f"거래 복기 저장 중 오류: {e}")
        return False

# ==================== 기존 함수들 (그대로 유지) ====================

def generate_sample_data(user_type):
    """기술/뉴스/감정 분석이 포함된 샘플 데이터 생성 (손실 내역 포함)"""
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
    
    # 사용자 유형별 감정 설정
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
        memo_templates = {
            '#공포': [
                "코스피 폭락하니까 {종목명} 급히 손절했음",
                "너무 무서워서 {종목명} 전량 매도"
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
                "{종목명} 상승장 놓치기 싫어서 추격 매수"
            ],
            '#욕심': [
                "{종목명} 이미 올랐지만 더 오를 것 같아서 추가 매수",
                "쉬운 돈이다 싶어서 {종목명} 물량 늘림",
                "{종목명} 대박날 것 같아서 풀매수",
                "이번엔 확실하다 싶어서 {종목명} 올인"
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
    
    # 기본 메모 설정
    for emotion in emotions_config.keys():
        if emotion not in memo_templates:
            memo_templates[emotion] = [f"{emotion} 상태에서 {{종목명}} 거래"]
    
    # 데이터 생성
    trades = []
    start_date = datetime(2024, 1, 1)
    
    # 기본 거래 100개 생성
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
    
    # AI 코칭 손실 내역과 연동되는 특별한 손실 거래들 추가
    loss_scenarios = [
        {
            'stock': '카카오',
            'emotion': '#공포',
            'memo': '코스피 폭락하니까 카카오 급히 손절했음',
            'return': -15.2,
            'buy_price': 50000,
            'sell_price': 42400,
            'quantity': 100,
            'date_offset': 30
        },
        {
            'stock': '하이브',
            'emotion': '#패닉',
            'memo': '하이브 폭락, 더 이상 못 견디겠어서 전량 매도',
            'return': -22.8,
            'buy_price': 180000,
            'sell_price': 138960,
            'quantity': 50,
            'date_offset': 15
        },
        {
            'stock': 'LG에너지솔루션',
            'emotion': '#추격매수',
            'memo': '어제 LG에너지솔루션 상한가 갔는데 오늘이라도 타야겠어서 추격매수',
            'return': -18.5,
            'buy_price': 450000,
            'sell_price': 366750,
            'quantity': 30,
            'date_offset': 7
        },
        {
            'stock': 'SK하이닉스',
            'emotion': '#욕심',
            'memo': 'SK하이닉스 대박날 것 같아서 풀매수',
            'return': -12.7,
            'buy_price': 140000,
            'sell_price': 122220,
            'quantity': 80,
            'date_offset': 45
        },
        {
            'stock': '삼성전자',
            'emotion': '#불안',
            'memo': '마음이 불안해서 삼성전자 절반만 매도',
            'return': -8.3,
            'buy_price': 75000,
            'sell_price': 68775,
            'quantity': 150,
            'date_offset': 60
        }
    ]
    
    # 성공 거래 시나리오들도 추가
    success_scenarios = [
        {
            'stock': '삼성전자',
            'emotion': '#확신',
            'memo': '삼성전자 기술적 분석상 매수 타이밍으로 판단',
            'return': 12.5,
            'buy_price': 70000,
            'sell_price': 78750,
            'quantity': 100,
            'date_offset': 20
        },
        {
            'stock': 'NAVER',
            'emotion': '#합리적',
            'memo': 'NAVER 분할 매수 전략으로 추가 매수',
            'return': 8.7,
            'buy_price': 165000,
            'sell_price': 179355,
            'quantity': 50,
            'date_offset': 35
        },
        {
            'stock': 'KB금융',
            'emotion': '#확신',
            'memo': 'KB금융 펀더멘털 분석 결과 저평가, 전략적 매수',
            'return': 15.3,
            'buy_price': 65000,
            'sell_price': 74945,
            'quantity': 80,
            'date_offset': 50
        }
    ]
    
    # 특별한 손실 거래들을 매수-매도 페어로 추가
    for scenario in loss_scenarios:
        # 매수 거래
        buy_date = datetime.now() - timedelta(days=scenario['date_offset'] + 3)
        buy_trade = {
            '거래일시': buy_date,
            '종목명': scenario['stock'],
            '종목코드': '999999',  # 더미 코드
            '거래구분': '매수',
            '수량': scenario['quantity'],
            '가격': scenario['buy_price'],
            '감정태그': scenario['emotion'],
            '메모': f"{scenario['stock']} 매수 - " + scenario['memo'].replace('매도', '매수').replace('손절', '매수'),
            '수익률': 0,  # 매수 시점에는 수익률 0
            '코스피지수': round(2400 + np.random.normal(0, 50), 2),
            '기술분석': np.random.choice(technical_analysis_templates),
            '뉴스분석': np.random.choice(news_analysis_templates),
            '감정분석': np.random.choice(emotion_analysis_templates)
        }
        trades.append(buy_trade)
        
        # 매도 거래 (손실)
        sell_date = datetime.now() - timedelta(days=scenario['date_offset'])
        sell_trade = {
            '거래일시': sell_date,
            '종목명': scenario['stock'],
            '종목코드': '999999',
            '거래구분': '매도',
            '수량': scenario['quantity'],
            '가격': scenario['sell_price'],
            '감정태그': scenario['emotion'],
            '메모': scenario['memo'],
            '수익률': scenario['return'],
            '코스피지수': round(2400 + np.random.normal(0, 50), 2),
            '기술분석': "지지선 이탈로 하락 가속화 가능성",
            '뉴스분석': "부정적 뉴스로 인한 투자심리 악화",
            '감정분석': "시장 하락에 대한 과도한 공포감 지배"
        }
        trades.append(sell_trade)
    
    # 특별한 성공 거래들을 매수-매도 페어로 추가
    for scenario in success_scenarios:
        # 매수 거래
        buy_date = datetime.now() - timedelta(days=scenario['date_offset'] + 3)
        buy_trade = {
            '거래일시': buy_date,
            '종목명': scenario['stock'],
            '종목코드': '999998',  # 더미 코드
            '거래구분': '매수',
            '수량': scenario['quantity'],
            '가격': scenario['buy_price'],
            '감정태그': scenario['emotion'],
            '메모': f"{scenario['stock']} 매수 - " + scenario['memo'],
            '수익률': 0,  # 매수 시점에는 수익률 0
            '코스피지수': round(2400 + np.random.normal(0, 50), 2),
            '기술분석': "기술적 지표 상승 신호 확인",
            '뉴스분석': "긍정적 실적 전망으로 시장 기대감 상승",
            '감정분석': "냉정한 분석 기반의 합리적 판단"
        }
        trades.append(buy_trade)
        
        # 매도 거래 (수익)
        sell_date = datetime.now() - timedelta(days=scenario['date_offset'])
        sell_trade = {
            '거래일시': sell_date,
            '종목명': scenario['stock'],
            '종목코드': '999998',
            '거래구분': '매도',
            '수량': scenario['quantity'],
            '가격': scenario['sell_price'],
            '감정태그': scenario['emotion'],
            '메모': scenario['memo'].replace('매수', '목표가 도달로 매도'),
            '수익률': scenario['return'],
            '코스피지수': round(2400 + np.random.normal(0, 50), 2),
            '기술분석': "목표 수익률 달성으로 이익 실현",
            '뉴스분석': "펀더멘털 개선 확인으로 수익 확정",
            '감정분석': "계획된 투자 전략에 따른 합리적 실현"
        }
        trades.append(sell_trade)
    
    df = pd.DataFrame(trades)
    df = df.sort_values('거래일시').reset_index(drop=True)
    
    return df

def load_user_data_from_csv(user_type):
    """CSV 파일에서 사용자 데이터 로드, 없으면 샘플 데이터 생성"""
    try:
        if user_type == "김국민":
            csv_filename = 'kim_gukmin_trades.csv'
        else:
            csv_filename = 'park_tuja_trades.csv'
        
        # 파일이 존재하는지 확인
        if os.path.exists(csv_filename):
            df = pd.read_csv(csv_filename, encoding='utf-8-sig')
            # 날짜 컬럼 변환
            df['거래일시'] = pd.to_datetime(df['거래일시'])
            return df
        else:
            # 파일이 없으면 샘플 데이터 생성
            df = generate_sample_data(user_type)
            # 생성한 데이터를 CSV로 저장
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            st.info(f"✅ {csv_filename} 샘플 파일을 생성했습니다.")
            return df
            
    except Exception as e:
        st.warning(f"⚠️ CSV 파일 로드 중 오류: {e}. 샘플 데이터를 생성합니다.")
        return generate_sample_data(user_type)

# 배치 처리 최적화 함수들
@st.cache_data(ttl=3600, show_spinner=False)
def load_user_data_with_embeddings(user_type: str, force_refresh: bool = False) -> pd.DataFrame:
    """사용자 거래 기록을 불러오고 임베딩을 추가 (배치 처리 최적화)"""
    if not AI_SERVICE_AVAILABLE:
        return load_user_data_from_csv(user_type)
    
    ensure_cache_directory()
    
    # 1. 기존 CSV 데이터 로드
    df = load_user_data_from_csv(user_type)
    
    if df.empty:
        return df
    
    # 2. 강제 새로고침이 아닌 경우 캐시 확인
    if not force_refresh:
        data_hash = get_data_hash(df)
        cache_key = get_cache_key(user_type, data_hash)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
        
        cached_df = get_cached_embeddings(cache_path)
        if cached_df is not None and not cached_df.empty:
            # 캐시된 데이터가 있고 임베딩 커버리지가 충분한 경우
            if AI_SERVICE_AVAILABLE:
                stats = get_embedding_stats(cached_df)
                if stats['embedding_coverage'] >= 95:
                    return cached_df
    
    # 3. 임베딩이 필요한 경우 생성
    if check_gemini_api():
        df_with_embeddings = preprocess_embeddings_cache(df, user_type)
        
        # 4. 캐시에 저장
        data_hash = get_data_hash(df_with_embeddings)
        cache_key = get_cache_key(user_type, data_hash)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
        save_cached_embeddings(df_with_embeddings, cache_path)
        
        return df_with_embeddings
    else:
        # API가 없는 경우 기본 데이터 반환
        return df

def get_cached_embeddings(cache_path: str) -> pd.DataFrame:
    """캐시된 임베딩 데이터 로드"""
    if not os.path.exists(cache_path):
        return None
    
    try:
        # 캐시 파일 생성 시간 확인
        cache_age = time.time() - os.path.getmtime(cache_path)
        if cache_age > EMBEDDING_CACHE_EXPIRY:
            # 만료된 캐시 삭제
            os.remove(cache_path)
            return None
        
        # 캐시 로드
        with open(cache_path, 'rb') as f:
            cache_data = pickle.load(f)
        
        if isinstance(cache_data, dict) and 'dataframe' in cache_data:
            return cache_data['dataframe']
        elif isinstance(cache_data, pd.DataFrame):
            return cache_data
        else:
            return None
            
    except Exception as e:
        st.warning(f"캐시 로드 오류: {e}")
        # 손상된 캐시 파일 삭제
        try:
            os.remove(cache_path)
        except:
            pass
        return None

def save_cached_embeddings(df: pd.DataFrame, cache_path: str):
    """임베딩 데이터를 캐시에 저장"""
    try:
        ensure_cache_directory()
        
        cache_data = {
            'dataframe': df,
            'timestamp': datetime.now(),
            'embedding_stats': get_embedding_stats(df) if AI_SERVICE_AVAILABLE else {},
            'version': '1.0'
        }
        
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
            
    except Exception as e:
        st.warning(f"캐시 저장 오류: {e}")

def save_user_data_with_embeddings(df: pd.DataFrame, user_type: str) -> bool:
    """임베딩이 포함된 사용자 데이터 저장"""
    if df.empty:
        return False
    
    try:
        # 1. CSV 파일 저장 (임베딩 제외)
        csv_saved = save_user_data_to_csv(df, user_type)
        
        # 2. 임베딩 캐시 업데이트
        if AI_SERVICE_AVAILABLE and 'embedding' in df.columns:
            ensure_cache_directory()
            data_hash = get_data_hash(df)
            cache_key = get_cache_key(user_type, data_hash)
            cache_path = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
            save_cached_embeddings(df, cache_path)
        
        return csv_saved
        
    except Exception as e:
        st.error(f"데이터 저장 오류: {e}")
        return False

def clear_embedding_cache(user_type: str = None):
    """임베딩 캐시 삭제"""
    ensure_cache_directory()
    
    try:
        if user_type:
            # 특정 사용자 캐시만 삭제
            pattern = f"{user_type}_"
            deleted_count = 0
            for filename in os.listdir(CACHE_DIR):
                if filename.endswith('.pkl'):
                    # 캐시 파일 내용 확인해서 해당 사용자인지 체크
                    cache_path = os.path.join(CACHE_DIR, filename)
                    try:
                        with open(cache_path, 'rb') as f:
                            cache_data = pickle.load(f)
                        # 사용자별 구분이 어려우므로 모든 캐시 삭제로 변경
                        os.remove(cache_path)
                        deleted_count += 1
                    except:
                        pass
            st.success(f"✅ {deleted_count}개의 캐시 파일이 삭제되었습니다.")
        else:
            # 모든 캐시 삭제
            deleted_count = 0
            for filename in os.listdir(CACHE_DIR):
                if filename.endswith('.pkl'):
                    os.remove(os.path.join(CACHE_DIR, filename))
                    deleted_count += 1
            st.success(f"✅ 전체 {deleted_count}개의 캐시 파일이 삭제되었습니다.")
        
        # Streamlit 캐시도 클리어
        st.cache_data.clear()
        
    except Exception as e:
        st.error(f"캐시 삭제 오류: {e}")

def get_embedding_stats_summary(user_type: str) -> dict:
    """임베딩 통계 요약 정보"""
    if not AI_SERVICE_AVAILABLE:
        return {'status': 'ai_service_unavailable'}
    
    try:
        df = load_user_data_with_embeddings(user_type)
        return get_embedding_stats(df)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 기존 함수들 (그대로 유지)
def save_user_data_to_csv(user_data, user_type):
    """사용자 데이터를 CSV 파일로 저장"""
    try:
        if user_type == "김국민":
            filename = 'kim_gukmin_trades.csv'
        else:
            filename = 'park_tuja_trades.csv'
        
        # 임베딩 컬럼 제외하고 저장
        df_to_save = user_data.drop(columns=['embedding'], errors='ignore')
        df_to_save.to_csv(filename, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"데이터 저장 중 오류: {e}")
        return False

def get_loss_trade_scenarios():
    """AI 코칭에서 사용할 손실 거래 시나리오들"""
    return [
        {
            'stock_name': '카카오',
            'quantity': 100,
            'buy_price': 50000,
            'sell_price': 42400,
            'loss_amount': 760000,
            'loss_percentage': -15.2,
            'emotion': '#공포',
            'memo': '코스피 폭락하니까 카카오 급히 손절했음',
            'date': datetime.now() - timedelta(days=30)
        },
        {
            'stock_name': '하이브',
            'quantity': 50,
            'buy_price': 180000,
            'sell_price': 138960,
            'loss_amount': 2052000,
            'loss_percentage': -22.8,
            'emotion': '#패닉',
            'memo': '하이브 폭락, 더 이상 못 견디겠어서 전량 매도',
            'date': datetime.now() - timedelta(days=15)
        },
        {
            'stock_name': 'LG에너지솔루션',
            'quantity': 30,
            'buy_price': 450000,
            'sell_price': 366750,
            'loss_amount': 2497500,
            'loss_percentage': -18.5,
            'emotion': '#추격매수',
            'memo': '어제 LG에너지솔루션 상한가 갔는데 오늘이라도 타야겠어서 추격매수',
            'date': datetime.now() - timedelta(days=7)
        },
        {
            'stock_name': 'SK하이닉스',
            'quantity': 80,
            'buy_price': 140000,
            'sell_price': 122220,
            'loss_amount': 1422400,
            'loss_percentage': -12.7,
            'emotion': '#욕심',
            'memo': 'SK하이닉스 대박날 것 같아서 풀매수',
            'date': datetime.now() - timedelta(days=45)
        },
        {
            'stock_name': '삼성전자',
            'quantity': 150,
            'buy_price': 75000,
            'sell_price': 68775,
            'loss_amount': 933750,
            'loss_percentage': -8.3,
            'emotion': '#불안',
            'memo': '마음이 불안해서 삼성전자 절반만 매도',
            'date': datetime.now() - timedelta(days=60)
        }
    ]

def add_dummy_trading_history():
    """포트폴리오 거래 내역에 더미 데이터 추가"""
    if 'history' not in st.session_state:
        st.session_state.history = pd.DataFrame(columns=['거래일시', '종목명', '거래구분', '수량', '가격', '금액'])
    
    # 손실 거래 시나리오들을 거래 내역에 추가
    loss_scenarios = get_loss_trade_scenarios()
    
    for scenario in loss_scenarios:
        # 매수 거래 추가
        buy_trade = pd.DataFrame({
            '거래일시': [scenario['date'] - timedelta(days=3)],
            '종목명': [scenario['stock_name']],
            '거래구분': ['매수'],
            '수량': [scenario['quantity']],
            '가격': [scenario['buy_price']],
            '금액': [scenario['quantity'] * scenario['buy_price']]
        })
        
        # 매도 거래 추가 (손실)
        sell_trade = pd.DataFrame({
            '거래일시': [scenario['date']],
            '종목명': [scenario['stock_name']],
            '거래구분': ['매도'],
            '수량': [scenario['quantity']],
            '가격': [scenario['sell_price']],
            '금액': [scenario['quantity'] * scenario['sell_price']]
        })
        
        # 기존 내역에 추가 (중복 방지)
        if st.session_state.history.empty:
            st.session_state.history = pd.concat([buy_trade, sell_trade], ignore_index=True)
        else:
            # 중복 확인
            existing = st.session_state.history[
                (st.session_state.history['종목명'] == scenario['stock_name']) &
                (st.session_state.history['거래구분'] == '매도') &
                (st.session_state.history['수량'] == scenario['quantity'])
            ]
            
            if existing.empty:
                st.session_state.history = pd.concat([
                    st.session_state.history, buy_trade, sell_trade
                ], ignore_index=True)
    
    # 날짜순 정렬
    st.session_state.history = st.session_state.history.sort_values('거래일시').reset_index(drop=True)

def initialize_market_data():
    """시장 데이터 초기화"""
    return {
        '삼성전자': {
            'price': 75000, 
            'change': 2.1, 
            'news': '3분기 실적 개선 전망으로 상승세',
            'volume': 1500000
        },
        '카카오': {
            'price': 45000, 
            'change': -1.5, 
            'news': '카카오페이 IPO 계획 발표 후 혼조세',
            'volume': 890000
        },
        'NAVER': {
            'price': 180000, 
            'change': 0.8, 
            'news': '클라우드 사업 확장으로 성장 기대',
            'volume': 650000
        },
        'LG에너지솔루션': {
            'price': 420000, 
            'change': 3.2, 
            'news': '북미 배터리 공장 증설 계획 발표',
            'volume': 340000
        },
        '하이브': {
            'price': 155000, 
            'change': -2.8, 
            'news': 'BTS 멤버 입대 영향 우려로 하락',
            'volume': 780000
        },
        'SK하이닉스': {
            'price': 125000, 
            'change': 1.7, 
            'news': '메모리 반도체 수급 개선 신호',
            'volume': 920000
        },
        '현대차': {
            'price': 190000, 
            'change': 0.3, 
            'news': '전기차 판매량 증가로 실적 개선',
            'volume': 480000
        },
        'KB금융': {
            'price': 78000, 
            'change': -0.5, 
            'news': '금리 인상 기대감 속 금융주 관심',
            'volume': 1200000
        }
    }

def update_prices(market_data):
    """실시간 가격 업데이트 (변동성 시뮬레이션)"""
    updated_data = market_data.copy()
    
    for stock_name in updated_data:
        # ±2% 범위 내에서 랜덤 변동
        price_change = np.random.normal(0, 0.015)  # 1.5% 표준편차
        current_price = updated_data[stock_name]['price']
        new_price = max(1000, int(current_price * (1 + price_change)))
        
        # 가격 업데이트
        updated_data[stock_name]['price'] = new_price
        
        # 등락률 계산
        price_change_pct = ((new_price - current_price) / current_price) * 100
        updated_data[stock_name]['change'] = round(price_change_pct, 2)
        
        # 거래량 랜덤 업데이트
        volume_change = np.random.normal(0, 0.1)
        current_volume = updated_data[stock_name]['volume']
        new_volume = max(10000, int(current_volume * (1 + volume_change)))
        updated_data[stock_name]['volume'] = new_volume
    
    return updated_data

def get_market_summary():
    """시장 전체 요약 정보"""
    return {
        'kospi_index': round(2400 + np.random.normal(0, 20), 2),
        'kosdaq_index': round(850 + np.random.normal(0, 15), 2),
        'won_dollar': round(1300 + np.random.normal(0, 10), 2),
        'market_sentiment': np.random.choice(['강세', '약세', '보합', '혼조']),
        'top_gainers': ['삼성전자', 'LG에너지솔루션', 'SK하이닉스'],
        'top_losers': ['카카오', '하이브', 'KB금융'],
        'trading_volume': f"{np.random.randint(8, 15)}조원"
    }

def create_sample_csv_files():
    """샘플 CSV 파일들을 생성하는 함수"""
    try:
        # 김국민 데이터 생성 및 저장
        kim_data = generate_sample_data("김국민")
        kim_data.to_csv('kim_gukmin_trades.csv', index=False, encoding='utf-8-sig')
        
        # 박투자 데이터 생성 및 저장
        park_data = generate_sample_data("박투자")
        park_data.to_csv('park_tuja_trades.csv', index=False, encoding='utf-8-sig')
        
        return True
    except Exception as e:
        st.error(f"CSV 파일 생성 중 오류: {e}")
        return False

# 데이터 검증 함수들
def validate_user_data(df):
    """사용자 데이터 유효성 검증"""
    required_columns = ['거래일시', '종목명', '거래구분', '수량', '가격', '감정태그', '메모', '수익률']
    
    if df.empty:
        return False, "데이터가 비어있습니다."
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"필수 컬럼이 없습니다: {missing_columns}"
    
    return True, "데이터가 유효합니다."

def get_user_statistics(df):
    """사용자 데이터 통계 정보 (임베딩 정보 포함)"""
    if df.empty:
        return {}
    
    try:
        stats = {
            'total_trades': len(df),
            'avg_return': df['수익률'].mean(),
            'win_rate': len(df[df['수익률'] > 0]) / len(df) * 100,
            'total_return': df['수익률'].sum(),
            'max_profit': df['수익률'].max(),
            'max_loss': df['수익률'].min(),
            'trading_frequency': len(df) / max(1, (df['거래일시'].max() - df['거래일시'].min()).days),
            'emotion_distribution': df['감정태그'].value_counts().to_dict(),
            'stock_distribution': df['종목명'].value_counts().head(5).to_dict()
        }
        
        # 임베딩 통계 추가
        if AI_SERVICE_AVAILABLE and 'embedding' in df.columns:
            embedding_stats = get_embedding_stats(df)
            stats.update({
                'embedding_coverage': embedding_stats.get('embedding_coverage', 0),
                'embedded_trades': embedding_stats.get('embedded_trades', 0),
                'embedding_status': embedding_stats.get('status', 'unknown')
            })
        
        return stats
    except Exception as e:
        st.error(f"통계 계산 중 오류: {e}")
        return {}

# 배치 처리 상태 확인 함수
def check_batch_processing_status():
    """배치 처리 시스템 상태 확인"""
    status = {
        'ai_service_available': AI_SERVICE_AVAILABLE,
        'gemini_api_configured': check_gemini_api() if AI_SERVICE_AVAILABLE else False,
        'cache_directory_exists': os.path.exists(CACHE_DIR),
        'cache_files_count': 0,
        'charter_file_exists': os.path.exists(CHARTER_JSON_PATH),
        'notes_file_exists': os.path.exists(NOTES_CSV_PATH)
    }
    
    if status['cache_directory_exists']:
        try:
            cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.pkl')]
            status['cache_files_count'] = len(cache_files)
        except:
            status['cache_files_count'] = 0
    
    return status

# 성능 최적화 함수
def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """데이터프레임 메모리 사용량 최적화"""
    if df.empty:
        return df
    
    optimized_df = df.copy()
    
    # 숫자형 컬럼 최적화
    for col in optimized_df.select_dtypes(include=['int64']).columns:
        if optimized_df[col].min() >= 0:
            if optimized_df[col].max() < 255:
                optimized_df[col] = optimized_df[col].astype('uint8')
            elif optimized_df[col].max() < 65535:
                optimized_df[col] = optimized_df[col].astype('uint16')
            else:
                optimized_df[col] = optimized_df[col].astype('uint32')
        else:
            if optimized_df[col].min() > -128 and optimized_df[col].max() < 127:
                optimized_df[col] = optimized_df[col].astype('int8')
            elif optimized_df[col].min() > -32768 and optimized_df[col].max() < 32767:
                optimized_df[col] = optimized_df[col].astype('int16')
            else:
                optimized_df[col] = optimized_df[col].astype('int32')
    
    # float 컬럼 최적화
    for col in optimized_df.select_dtypes(include=['float64']).columns:
        optimized_df[col] = optimized_df[col].astype('float32')
    
    # 문자열 컬럼을 카테고리로 변환 (반복되는 값이 많은 경우)
    for col in optimized_df.select_dtypes(include=['object']).columns:
        if col not in ['메모', '기술분석', '뉴스분석', '감정분석']:  # 긴 텍스트 제외
            unique_ratio = optimized_df[col].nunique() / len(optimized_df)
            if unique_ratio < 0.5:  # 고유값이 50% 미만인 경우
                optimized_df[col] = optimized_df[col].astype('category')
    
    return optimized_df

# 배치 처리 관련 유틸리티
def get_cache_info():
    """캐시 정보 반환"""
    ensure_cache_directory()
    
    cache_info = {
        'cache_dir': CACHE_DIR,
        'cache_expiry_hours': EMBEDDING_CACHE_EXPIRY / 3600,
        'total_cache_files': 0,
        'total_cache_size_mb': 0,
        'cache_files': []
    }
    
    try:
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.pkl'):
                file_path = os.path.join(CACHE_DIR, filename)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                file_age_hours = (time.time() - os.path.getmtime(file_path)) / 3600
                
                cache_info['cache_files'].append({
                    'filename': filename,
                    'size_mb': round(file_size, 2),
                    'age_hours': round(file_age_hours, 1),
                    'expired': file_age_hours > (EMBEDDING_CACHE_EXPIRY / 3600)
                })
                
                cache_info['total_cache_files'] += 1
                cache_info['total_cache_size_mb'] += file_size
        
        cache_info['total_cache_size_mb'] = round(cache_info['total_cache_size_mb'], 2)
        
    except Exception as e:
        cache_info['error'] = str(e)
    
    return cache_info

def cleanup_expired_cache():
    """만료된 캐시 파일들 정리"""
    ensure_cache_directory()
    cleaned_count = 0
    
    try:
        current_time = time.time()
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.pkl'):
                file_path = os.path.join(CACHE_DIR, filename)
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > EMBEDDING_CACHE_EXPIRY:
                    os.remove(file_path)
                    cleaned_count += 1
        
        if cleaned_count > 0:
            st.info(f"✅ 만료된 캐시 파일 {cleaned_count}개를 정리했습니다.")
        
    except Exception as e:
        st.warning(f"캐시 정리 중 오류: {e}")
    
    return cleaned_count

# 투자 헌장 관련 유틸리티 함수들
def get_charter_statistics(user_type: str = None) -> dict:
    """투자 헌장 통계 정보"""
    try:
        if user_type:
            charter = load_charter(user_type)
            return {
                'user_type': user_type,
                'success_principles_count': len(charter.get('success_principles', [])),
                'failure_principles_count': len(charter.get('failure_principles', [])),
                'total_principles': len(charter.get('success_principles', [])) + len(charter.get('failure_principles', [])),
                'created_at': charter.get('created_at', ''),
                'updated_at': charter.get('updated_at', '')
            }
        else:
            # 모든 사용자 통계
            if not os.path.exists(CHARTER_JSON_PATH):
                return {'total_users': 0, 'total_principles': 0}
            
            with open(CHARTER_JSON_PATH, 'r', encoding='utf-8') as f:
                all_charters = json.load(f)
            
            total_success = sum(len(charter.get('success_principles', [])) for charter in all_charters.values())
            total_failure = sum(len(charter.get('failure_principles', [])) for charter in all_charters.values())
            
            return {
                'total_users': len(all_charters),
                'total_success_principles': total_success,
                'total_failure_principles': total_failure,
                'total_principles': total_success + total_failure,
                'users': list(all_charters.keys())
            }
    
    except Exception as e:
        st.error(f"헌장 통계 계산 중 오류: {e}")
        return {}

def export_charter_to_text(user_type: str) -> str:
    """투자 헌장을 텍스트 형태로 내보내기"""
    try:
        charter = load_charter(user_type)
        
        text_charter = f"""
📜 {user_type}님의 투자 헌장
작성일: {charter.get('created_at', datetime.now().isoformat())[:10]}
최종 수정: {charter.get('updated_at', datetime.now().isoformat())[:10]}

=== ✅ 지켜야 할 성공 원칙 ===
"""
        
        success_principles = charter.get('success_principles', [])
        if success_principles:
            for i, principle in enumerate(success_principles, 1):
                text_charter += f"{i}. {principle}\n"
        else:
            text_charter += "아직 성공 원칙이 없습니다.\n"
        
        text_charter += """
=== ❗️ 피해야 할 실패 원칙 ===
"""
        
        failure_principles = charter.get('failure_principles', [])
        if failure_principles:
            for i, principle in enumerate(failure_principles, 1):
                text_charter += f"{i}. {principle}\n"
        else:
            text_charter += "아직 실패 원칙이 없습니다.\n"
        
        text_charter += f"""
=== 서명 ===
투자자: {user_type}
날짜: {datetime.now().strftime('%Y년 %m월 %d일')}
"""
        
        return text_charter
        
    except Exception as e:
        return f"헌장 내보내기 중 오류: {str(e)}"

# 복기노트 관련 유틸리티 함수들
def get_notes_statistics(user_type: str = None) -> dict:
    """복기노트 통계 정보"""
    try:
        notes_df = load_notes(user_type)
        
        if notes_df.empty:
            return {
                'total_notes': 0,
                'success_notes': 0,
                'failure_notes': 0
            }
        
        # trade_type 컬럼이 있는지 확인
        if 'trade_type' in notes_df.columns:
            success_notes = len(notes_df[notes_df['trade_type'] == 'buy'])
            failure_notes = len(notes_df[notes_df['trade_type'] == 'sell'])
        else:
            # 기존 구조에서는 모두 실패 노트로 간주
            success_notes = 0
            failure_notes = len(notes_df)
        
        stats = {
            'total_notes': len(notes_df),
            'success_notes': success_notes,
            'failure_notes': failure_notes
        }
        
        # 감정 분포 추가
        if 'emotion' in notes_df.columns:
            emotion_counts = notes_df['emotion'].value_counts().to_dict()
            stats['emotion_distribution'] = emotion_counts
        
        # 최근 활동 추가
        if 'timestamp' in notes_df.columns:
            notes_df['timestamp'] = pd.to_datetime(notes_df['timestamp'])
            recent_notes = notes_df[notes_df['timestamp'] >= (datetime.now() - timedelta(days=30))]
            stats['recent_notes_count'] = len(recent_notes)
        
        return stats
        
    except Exception as e:
        st.error(f"복기노트 통계 계산 중 오류: {e}")
        return {}

# 데이터 무결성 검증 함수들
def validate_charter_integrity():
    """투자 헌장 데이터 무결성 검증"""
    try:
        if not os.path.exists(CHARTER_JSON_PATH):
            return True, "헌장 파일이 없습니다. 자동으로 생성됩니다."
        
        with open(CHARTER_JSON_PATH, 'r', encoding='utf-8') as f:
            all_charters = json.load(f)
        
        issues = []
        
        for user_type, charter in all_charters.items():
            if 'success_principles' not in charter:
                issues.append(f"{user_type}: success_principles 키 누락")
            if 'failure_principles' not in charter:
                issues.append(f"{user_type}: failure_principles 키 누락")
            
            # 원칙들이 리스트인지 확인
            if not isinstance(charter.get('success_principles', []), list):
                issues.append(f"{user_type}: success_principles가 리스트가 아님")
            if not isinstance(charter.get('failure_principles', []), list):
                issues.append(f"{user_type}: failure_principles가 리스트가 아님")
        
        if issues:
            return False, f"무결성 검증 실패: {', '.join(issues)}"
        else:
            return True, "헌장 데이터 무결성 검증 완료"
            
    except Exception as e:
        return False, f"헌장 무결성 검증 중 오류: {str(e)}"

def validate_notes_integrity():
    """복기노트 데이터 무결성 검증"""
    try:
        if not os.path.exists(NOTES_CSV_PATH):
            return True, "복기노트 파일이 없습니다. 자동으로 생성됩니다."
        
        notes_df = pd.read_csv(NOTES_CSV_PATH, encoding='utf-8-sig')
        
        required_columns = ['note_id', 'user_type', 'stock_name', 'user_comment', 'timestamp']
        missing_columns = [col for col in required_columns if col not in notes_df.columns]
        
        if missing_columns:
            return False, f"필수 컬럼 누락: {missing_columns}"
        
        # 중복 note_id 확인
        if notes_df['note_id'].duplicated().any():
            return False, "중복된 note_id가 발견되었습니다."
        
        # 데이터 타입 확인
        try:
            pd.to_datetime(notes_df['timestamp'])
        except:
            return False, "timestamp 컬럼의 날짜 형식이 올바르지 않습니다."
        
        return True, "복기노트 데이터 무결성 검증 완료"
        
    except Exception as e:
        return False, f"복기노트 무결성 검증 중 오류: {str(e)}"

# 시스템 상태 체크 함수
def get_system_health_check() -> dict:
    """전체 시스템 상태 체크"""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'healthy',
        'components': {}
    }
    
    # AI 서비스 상태
    health_status['components']['ai_service'] = {
        'available': AI_SERVICE_AVAILABLE,
        'gemini_configured': check_gemini_api() if AI_SERVICE_AVAILABLE else False
    }
    
    # 파일 시스템 상태
    health_status['components']['filesystem'] = {
        'cache_dir_exists': os.path.exists(CACHE_DIR),
        'charter_file_exists': os.path.exists(CHARTER_JSON_PATH),
        'notes_file_exists': os.path.exists(NOTES_CSV_PATH)
    }
    
    # 데이터 무결성 상태
    charter_valid, charter_msg = validate_charter_integrity()
    notes_valid, notes_msg = validate_notes_integrity()
    
    health_status['components']['data_integrity'] = {
        'charter_valid': charter_valid,
        'charter_message': charter_msg,
        'notes_valid': notes_valid,
        'notes_message': notes_msg
    }
    
    # 캐시 상태
    cache_info = get_cache_info()
    health_status['components']['cache'] = {
        'total_files': cache_info.get('total_cache_files', 0),
        'total_size_mb': cache_info.get('total_cache_size_mb', 0),
        'expired_files': len([f for f in cache_info.get('cache_files', []) if f.get('expired', False)])
    }
    
    # 전체 상태 결정
    critical_issues = []
    if not charter_valid:
        critical_issues.append('charter_integrity')
    if not notes_valid:
        critical_issues.append('notes_integrity')
    
    if critical_issues:
        health_status['overall_status'] = 'unhealthy'
        health_status['critical_issues'] = critical_issues
    elif not AI_SERVICE_AVAILABLE:
        health_status['overall_status'] = 'degraded'
        health_status['warning'] = 'AI 서비스가 비활성화되어 있습니다.'
    
    return health_status