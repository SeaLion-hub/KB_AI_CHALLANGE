#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 거울 코칭 시스템 (AI Challenge 핵심 기능)
과거 경험을 현재 상황과 매칭하여 "거울"처럼 반성할 수 있게 도와주는 AI 시스템
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import sentence_transformers.util
import re
from pathlib import Path
import sys

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 통합된 데이터 소스 import
from db.central_data_manager import get_user_trading_history

class MirrorCoaching:
    """
    거울 코칭 시스템
    
    사용자의 과거 거래 경험을 바탕으로:
    1. 현재 상황과 유사한 과거 경험 찾기 (Semantic Similarity)
    2. 성공/실패 패턴 분석
    3. 객관적인 인사이트 제공 (절대 매매 추천 안 함!)
    4. 스스로 답을 찾도록 유도하는 질문 생성
    """
    
    def __init__(self):
        # 최신 한국어 Sentence Transformer 모델 초기화
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        
        # 한국어 불용어 설정
        self.korean_stopwords = {
            '그리고', '하지만', '그런데', '그래서', '그것', '이것', '저것',
            '있다', '없다', '되다', '하다', '있는', '없는', '된다'
        }
        
        # 감정 키워드 매핑
        self.emotion_keywords = {
            '공포': ['무서워', '두려워', '불안', '걱정', '패닉', '폭락'],
            '욕심': ['욕심', '더', '추가', '풀매수', '올인', '대박'],
            '후회': ['후회', '아쉬워', '잘못', '실수', '놓쳤'],
            '확신': ['확신', '확실', '틀림없', '분명', '100%'],
            '냉정': ['분석', '판단', '근거', '데이터', '객관적']
        }
    
    def _convert_to_dataframe(self, trades_list: List[Dict]) -> pd.DataFrame:
        """거래 데이터 리스트를 DataFrame으로 변환"""
        if not trades_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades_list)
        
        # 날짜 컬럼이 있으면 datetime으로 변환
        if '거래일시' in df.columns:
            df['거래일시'] = pd.to_datetime(df['거래일시'])
        
        return df
    
    def initialize_for_user(self, username: str) -> Dict:
        """사용자 초기화 및 기본 인사이트 생성"""
        try:
            # 통합된 데이터 소스에서 거래 데이터 가져오기
            trades_list = get_user_trading_history(username)
            trades_data = self._convert_to_dataframe(trades_list)
            
            if trades_data.empty:
                return {
                    'status': 'no_data',
                    'message': f'{username}님의 거래 데이터가 없습니다.',
                    'insights': {}
                }
            
            # 기본 패턴 분석
            base_insights = self._analyze_base_patterns(trades_data)
            
            return {
                'status': 'initialized',
                'message': f'{username}님의 거래 패턴 분석 완료',
                'insights': base_insights,
                'total_trades': len(trades_data)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'초기화 중 오류: {str(e)}',
                'insights': {}
            }
    
    def find_similar_experiences(
        self, 
        current_situation: str, 
        username: str, 
        top_k: int = 3
    ) -> List[Dict]:
        """
        현재 상황과 유사한 과거 경험 찾기 (Semantic Similarity 사용)
        
        Args:
            current_situation: 현재 투자 상황/생각
            username: 사용자명
            top_k: 반환할 유사 경험 개수
        
        Returns:
            유사한 과거 경험 리스트
        """
        try:
            # 통합된 데이터 소스에서 거래 데이터 가져오기
            trades_list = get_user_trading_history(username)
            trades_data = self._convert_to_dataframe(trades_list)
            
            if trades_data.empty:
                return []
            
            # 메모 텍스트 전처리
            past_memos = trades_data['메모'].fillna('').tolist()
            cleaned_memos = [self._clean_text(memo) for memo in past_memos]
            cleaned_current = self._clean_text(current_situation)
            
            # 빈 메모 필터링
            valid_indices = [i for i, memo in enumerate(cleaned_memos) if memo.strip()]
            valid_memos = [cleaned_memos[i] for i in valid_indices]
            
            if not valid_memos:
                return []
            
            # Sentence Embeddings 생성
            current_embedding = self.model.encode([cleaned_current])
            past_embeddings = self.model.encode(valid_memos)
            
            # 코사인 유사도 계산
            similarities = sentence_transformers.util.pytorch_cos_sim(
                current_embedding, past_embeddings
            )[0]
            
            # NumPy 배열로 변환하여 정렬
            similarities_np = similarities.cpu().numpy()
            
            # 유사도 순으로 정렬하고 상위 k개 선택
            top_indices = np.argsort(similarities_np)[::-1][:top_k]
            
            similar_experiences = []
            for idx in top_indices:
                similarity_score = float(similarities_np[idx])
                if similarity_score > 0.3:  # 최소 유사도 임계값 (Semantic 기반으로 높게 설정)
                    original_idx = valid_indices[idx]
                    trade_info = trades_data.iloc[original_idx]
                    similar_experiences.append({
                        'trade_data': trade_info.to_dict(),
                        'similarity_score': similarity_score,
                        'insight_type': self._determine_insight_type(trade_info),
                        'key_lesson': self._extract_key_lesson(trade_info)
                    })
            
            return similar_experiences
            
        except Exception as e:
            print(f"유사 경험 탐색 중 오류: {str(e)}")
            return []
    
    def generate_hybrid_coaching(self, current_trade: dict, similar_experiences: list) -> dict:
        """
        하이브리드 데이터 주입형 코칭 메시지 생성
        
        사용자의 실제 과거 거래 데이터를 규칙 기반 템플릿에 동적으로 삽입하여
        개인화된 코칭 메시지를 생성합니다. 외부 LLM이나 API를 사용하지 않고,
        순수하게 데이터 기반의 지능형 템플릿 시스템을 활용합니다.
        
        Args:
            current_trade: 현재 거래/상황 정보 딕셔너리
            similar_experiences: 유사한 과거 경험 리스트
        
        Returns:
            분석, 메시지, 질문이 포함된 코칭 딕셔너리
            {
                "analysis": "상황 분석 메시지",
                "message": "개인화된 코칭 메시지", 
                "question": "성찰을 유도하는 질문"
            }
        """
        # 1. 유사 경험이 없는 경우 - 기본 코칭 메시지 제공
        if not similar_experiences:
            return {
                "analysis": "새로운 패턴의 거래가 감지되었습니다.",
                "message": "이번 거래는 당신만의 투자 원칙을 만들어갈 좋은 기회입니다.",
                "question": "이번 결정에 가장 큰 영향을 미친 단 하나의 요인은 무엇인가요?"
            }
        
        # 2. 가장 유사한 과거 거래 데이터 추출 (첫 번째 요소가 가장 유사함)
        past_trade = similar_experiences[0]['trade_data']
        
        # 3. 규칙 기반 템플릿 선택 및 동적 메시지 구성
        if past_trade['수익률'] >= 0:
            # 과거 성공 경험을 바탕으로 한 성찰 템플릿
            analysis = (
                f"지금 '{current_trade.get('종목명', '해당 종목')}'에 대한 고민은, "
                f"과거 '{past_trade['종목명']}'에서 '{past_trade.get('감정태그', '특정 감정')}' "
                f"감정으로 성공했던 경험과 유사합니다."
            )
            
            message = (
                f"과거 해당 거래에서 '{past_trade.get('메모', '특별한 판단')}' 라는 판단으로 "
                f"{past_trade['수익률']:.1f}%의 좋은 결과를 얻으셨습니다. "
                f"이번에도 그때의 성공 요인을 적용할 수 있을까요?"
            )
            
            question = (
                f"과거의 성공 경험과 비교했을 때, 현재 상황의 가장 큰 차이점은 "
                f"무엇이라고 생각하시나요?"
            )
            
        else:
            # 과거 실패 경험으로부터의 학습 템플릿
            analysis = (
                f"현재 '{current_trade.get('종목명', '해당 종목')}'을 보며 느끼는 "
                f"'{current_trade.get('감정태그', '현재 감정')}' 감정은, "
                f"과거 '{past_trade['종목명']}' 거래에서 손실을 보셨을 때와 매우 흡사합니다."
            )
            
            message = (
                f"데이터에 따르면, 과거 '{past_trade.get('메모', '당시의 판단')}' 라고 "
                f"판단했던 거래는 {abs(past_trade['수익률']):.1f}%의 손실로 이어졌습니다. "
                f"과거의 경험이 현재의 결정에 어떤 경고를 보내고 있나요?"
            )
            
            question = (
                f"과거의 실수를 반복하지 않기 위해 지금 당장 다르게 행동해야 할 "
                f"한 가지는 무엇일까요?"
            )
        
        # 4. 최종 코칭 딕셔너리 반환
        return {
            "analysis": analysis,
            "message": message,
            "question": question
        }
    
    def generate_mirror_questions(
        self, 
        similar_experiences: List[Dict],
        current_situation: str
    ) -> List[str]:
        """
        거울 질문 생성 - 사용자가 스스로 답하도록 유도하는 질문들
        
        Args:
            similar_experiences: 유사한 과거 경험들
            current_situation: 현재 상황
        
        Returns:
            거울 질문 리스트
        """
        questions = []
        
        if not similar_experiences:
            questions.extend([
                "🤔 이번 투자 결정의 가장 큰 근거는 무엇인가요?",
                "⚖️ 이 투자의 위험과 기회를 어떻게 평가하시나요?",
                "🎯 만약 6개월 후의 나에게 이 결정을 설명한다면?"
            ])
            return questions
        
        # 과거 경험 기반 맞춤형 질문
        for exp in similar_experiences[:2]:  # 상위 2개 경험만 사용
            trade = exp['trade_data']
            
            if trade['수익률'] < 0:  # 손실 경험
                questions.append(
                    f"📉 과거 {trade['종목명']} 거래에서 {abs(trade['수익률']):.1f}% 손실을 본 경험이 있습니다. "
                    f"그때와 지금 상황에서 다른 점은 무엇인가요?"
                )
                
                if '공포' in trade.get('감정태그', ''):
                    questions.append("😰 감정적 판단으로 인한 과거 손실을 어떻게 방지할 수 있을까요?")
                
            else:  # 수익 경험
                questions.append(
                    f"📈 과거 {trade['종목명']} 거래에서 {trade['수익률']:.1f}% 수익을 낸 성공 요인을 "
                    f"이번에도 적용할 수 있을까요?"
                )
        
        # 패턴 기반 질문
        emotion_pattern = self._detect_emotion_pattern(similar_experiences)
        if emotion_pattern:
            questions.append(f"🧠 과거 '{emotion_pattern}' 패턴이 반복되고 있습니다. 이번엔 어떻게 다르게 접근하시겠나요?")
        
        # 기본 성찰 질문
        questions.extend([
            "⏰ 이 투자 결정을 24시간 후에도 같은 마음으로 할 수 있나요?",
            "📊 객관적 데이터와 주관적 느낌 중 어느 쪽에 더 의존하고 있나요?",
            "🎪 만약 이 투자가 실패한다면, 가장 큰 원인은 무엇일 것 같나요?"
        ])
        
        return questions[:5]  # 최대 5개까지
    
    def generate_insights_for_trade(self, trade_data: pd.Series, username: str) -> Dict:
        """특정 거래에 대한 거울 인사이트 생성"""
        try:
            # 통합된 데이터 소스에서 거래 데이터 가져오기
            trades_list = get_user_trading_history(username)
            all_trades = self._convert_to_dataframe(trades_list)
            
            if all_trades.empty:
                return {}
            
            insights = {}
            
            # 1. 동일 종목 과거 거래 패턴
            same_stock_trades = all_trades[all_trades['종목명'] == trade_data['종목명']]
            if len(same_stock_trades) > 1:
                insights['same_stock_pattern'] = self._analyze_same_stock_pattern(same_stock_trades)
            
            # 2. 유사한 감정 상태 거래들
            same_emotion_trades = all_trades[all_trades['감정태그'] == trade_data.get('감정태그')]
            if len(same_emotion_trades) > 1:
                insights['emotion_pattern'] = self._analyze_emotion_pattern(same_emotion_trades)
            
            # 3. 시기적 패턴 (같은 달, 같은 요일 등)
            trade_month = pd.to_datetime(trade_data['거래일시']).month
            same_month_trades = all_trades[pd.to_datetime(all_trades['거래일시']).dt.month == trade_month]
            if len(same_month_trades) > 3:
                insights['seasonal_pattern'] = self._analyze_seasonal_pattern(same_month_trades, trade_month)
            
            # 4. 거래 규모 패턴
            trade_amount = trade_data.get('수량', 0) * trade_data.get('가격', 0)
            insights['amount_pattern'] = self._analyze_amount_pattern(all_trades, trade_amount)
            
            return insights
            
        except Exception as e:
            print(f"거래 인사이트 생성 중 오류: {str(e)}")
            return {}
    
    def get_recommended_review_trades(self, username: str) -> Optional[pd.DataFrame]:
        """복기 추천 거래 선별"""
        try:
            # 통합된 데이터 소스에서 거래 데이터 가져오기
            trades_list = get_user_trading_history(username)
            trades_data = self._convert_to_dataframe(trades_list)
            
            if trades_data.empty:
                return None
            
            # 복기 가치가 높은 거래 선별 기준:
            # 1. 극단적 수익률 (±20% 이상)
            # 2. 강한 감정 태그 (#공포, #욕심, #패닉 등)
            # 3. 최근 3개월 내 거래
            
            extreme_returns = trades_data[abs(trades_data['수익률']) > 15]
            emotional_trades = trades_data[trades_data['감정태그'].isin(['#공포', '#욕심', '#패닉', '#추격매수'])]
            recent_cutoff = datetime.now() - timedelta(days=90)
            recent_trades = trades_data[pd.to_datetime(trades_data['거래일시']) > recent_cutoff]
            
            # 점수 기반 추천 시스템
            trades_copy = trades_data.copy()
            trades_copy['review_score'] = 0
            
            # 극단적 수익률에 높은 점수
            trades_copy.loc[abs(trades_copy['수익률']) > 20, 'review_score'] += 3
            trades_copy.loc[abs(trades_copy['수익률']) > 10, 'review_score'] += 2
            
            # 감정적 거래에 점수 추가
            emotional_tags = ['#공포', '#욕심', '#패닉', '#추격매수', '#불안']
            trades_copy.loc[trades_copy['감정태그'].isin(emotional_tags), 'review_score'] += 2
            
            # 최근 거래에 점수 추가
            trades_copy.loc[pd.to_datetime(trades_copy['거래일시']) > recent_cutoff, 'review_score'] += 1
            
            # 상위 점수 거래들 반환
            return trades_copy.nlargest(10, 'review_score')
            
        except Exception as e:
            print(f"추천 거래 선별 중 오류: {str(e)}")
            return None
    
    def generate_learning_scenarios(self) -> List[Dict]:
        """
        신규 사용자를 위한 학습 시나리오 생성
        다른 사용자들의 패턴을 익명화하여 학습 자료로 제공
        """
        scenarios = [
            {
                'scenario_id': 'fear_selling_lesson',
                'title': '공포매도의 교훈',
                'description': '시장 급락 시 감정적 매도의 위험성을 보여주는 시나리오',
                'example_trades': [
                    {
                        '상황': '코스피 3% 급락 상황',
                        '투자자_반응': '무서워서 전량 매도',
                        '결과': '-15% 손실',
                        '교훈': '시장 변동성은 일시적일 수 있음'
                    }
                ],
                'key_questions': [
                    "이런 상황에서 24시간 기다렸다면 어떻게 되었을까요?",
                    "감정적 판단과 합리적 분석의 차이는 무엇일까요?"
                ]
            },
            {
                'scenario_id': 'fomo_buying_lesson', 
                'title': 'FOMO 매수의 함정',
                'description': '급등주 추격매수의 위험성을 보여주는 시나리오',
                'example_trades': [
                    {
                        '상황': '특정 종목 연속 상한가',
                        '투자자_반응': '놓치기 아까워서 추격매수',
                        '결과': '-20% 손실',
                        '교훈': '급등 후에는 조정이 올 수 있음'
                    }
                ],
                'key_questions': [
                    "왜 모든 사람이 사고 있을 때 경계해야 할까요?",
                    "적정 매수 타이밍을 어떻게 판단할 수 있을까요?"
                ]
            },
            {
                'scenario_id': 'rational_success',
                'title': '합리적 투자의 성과',
                'description': '차분한 분석을 통한 성공 사례',
                'example_trades': [
                    {
                        '상황': '시장 불안정 속 저평가 종목 발견',
                        '투자자_반응': '펀더멘털 분석 후 신중한 매수',
                        '결과': '+25% 수익',
                        '교훈': '위기가 기회가 될 수 있음'
                    }
                ],
                'key_questions': [
                    "시장이 불안할 때 기회를 찾는 방법은?",
                    "다른 사람이 팔 때 사는 용기는 어디서 나올까요?"
                ]
            }
        ]
        
        return scenarios
    
    def get_investment_principles_learning_path(self, selected_principle: str) -> Dict:
        """
        선택한 투자 원칙에 따른 학습 경로 제공
        """
        learning_paths = {
            "워런 버핏": {
                'level_1': {
                    'title': '기업 이해하기',
                    'tasks': [
                        '관심 있는 기업 3개의 사업모델 조사',
                        '각 기업의 경쟁우위 요소 파악',
                        '최근 3년간 재무제표 간단 분석'
                    ],
                    'simulation_scenario': '가상의 우량기업 분석 실습'
                },
                'level_2': {
                    'title': '장기 관점 기르기',
                    'tasks': [
                        '10년 후 각 기업이 어떻게 될지 예측',
                        '단기 변동에 흔들리지 않는 연습',
                        '내재가치 계산 기초 학습'
                    ],
                    'simulation_scenario': '시장 변동성 속에서도 보유 연습'
                }
            },
            "피터 린치": {
                'level_1': {
                    'title': '일상에서 투자 아이디어 찾기',
                    'tasks': [
                        '자주 이용하는 서비스/제품 회사 조사',
                        '성장하는 트렌드 파악하기',
                        'PEG 비율 계산 방법 학습'
                    ],
                    'simulation_scenario': '생활 속 발견한 기업 분석 실습'
                },
                'level_2': {
                    'title': '성장주 발굴하기',
                    'tasks': [
                        '매출 성장률 20% 이상 기업 찾기',
                        '산업 내 경쟁 상황 분석',
                        '성장 지속 가능성 평가'
                    ],
                    'simulation_scenario': '고성장 기업 투자 시뮬레이션'
                }
            },
            "벤저민 그레이엄": {
                'level_1': {
                    'title': '안전 마진 이해하기',
                    'tasks': [
                        '내재가치 계산 기초 학습',
                        'PBR, PER 등 밸류에이션 지표 이해',
                        '재무 건전성 체크리스트 작성'
                    ],
                    'simulation_scenario': '저평가 종목 발굴 실습'
                },
                'level_2': {
                    'title': '분산 투자 실습',
                    'tasks': [
                        '10-15개 종목으로 포트폴리오 구성',
                        '섹터별 분산 전략 수립',
                        '위험 관리 원칙 정립'
                    ],
                    'simulation_scenario': '안전한 포트폴리오 구축 연습'
                }
            }
        }
        
        return learning_paths.get(selected_principle, {})
    
    def create_mirror_report(
        self, 
        username: str, 
        current_situation: str,
        similar_experiences: List[Dict] = None
    ) -> Dict:
        """종합 거울 리포트 생성"""
        report = {
            'timestamp': datetime.now(),
            'username': username,
            'current_situation': current_situation,
            'mirror_analysis': {}
        }
        
        try:
            # 유사 경험이 제공되지 않았다면 찾기
            if similar_experiences is None:
                similar_experiences = self.find_similar_experiences(current_situation, username)
            
            if similar_experiences:
                report['mirror_analysis']['similar_count'] = len(similar_experiences)
                report['mirror_analysis']['experiences'] = similar_experiences
                
                # 패턴 요약
                success_count = sum(1 for exp in similar_experiences if exp['trade_data']['수익률'] > 0)
                failure_count = len(similar_experiences) - success_count
                
                report['mirror_analysis']['pattern_summary'] = {
                    'success_cases': success_count,
                    'failure_cases': failure_count,
                    'dominant_emotion': self._detect_emotion_pattern(similar_experiences)
                }
                
                # 거울 질문 생성
                report['mirror_questions'] = self.generate_mirror_questions(
                    similar_experiences, current_situation
                )
                
                # 핵심 인사이트
                report['key_insights'] = self._generate_key_insights(similar_experiences)
                
            else:
                report['mirror_analysis']['message'] = "유사한 과거 경험을 찾을 수 없습니다."
                report['mirror_questions'] = self.generate_mirror_questions([], current_situation)
            
            return report
            
        except Exception as e:
            report['error'] = f"리포트 생성 중 오류: {str(e)}"
            return report
    
    def _clean_text(self, text: str) -> str:
        """텍스트 전처리"""
        if not isinstance(text, str):
            return ""
        
        # 기본 정제
        text = text.lower().strip()
        
        # 특수문자 제거 (한글, 영문, 숫자, 공백만 유지)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 중복 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 불용어 제거
        words = text.split()
        words = [word for word in words if word not in self.korean_stopwords]
        
        return ' '.join(words)
    
    def _analyze_base_patterns(self, trades_data: pd.DataFrame) -> Dict:
        """기본 거래 패턴 분석"""
        patterns = {}
        
        # 1. 감정별 성과 분석
        emotion_performance = trades_data.groupby('감정태그')['수익률'].agg(['mean', 'count']).round(2)
        patterns['emotion_performance'] = emotion_performance.to_dict('index')
        
        # 2. 월별 거래 패턴
        trades_data['month'] = pd.to_datetime(trades_data['거래일시']).dt.month
        monthly_pattern = trades_data.groupby('month')['수익률'].agg(['mean', 'count']).round(2)
        patterns['monthly_pattern'] = monthly_pattern.to_dict('index')
        
        # 3. 종목별 성과
        stock_performance = trades_data.groupby('종목명')['수익률'].agg(['mean', 'count']).round(2)
        patterns['stock_performance'] = stock_performance.to_dict('index')
        
        # 4. 거래 구분별 성과
        trade_type_performance = trades_data.groupby('거래구분')['수익률'].agg(['mean', 'count']).round(2)
        patterns['trade_type_performance'] = trade_type_performance.to_dict('index')
        
        return patterns
    
    def _determine_insight_type(self, trade_info: pd.Series) -> str:
        """인사이트 유형 결정"""
        if trade_info['수익률'] > 10:
            return "success_pattern"
        elif trade_info['수익률'] < -10:
            return "failure_pattern" 
        elif trade_info.get('감정태그') in ['#공포', '#패닉']:
            return "emotional_pattern"
        else:
            return "neutral_pattern"
    
    def _extract_key_lesson(self, trade_info: pd.Series) -> str:
        """핵심 교훈 추출"""
        memo = trade_info.get('메모', '')
        emotion = trade_info.get('감정태그', '')
        return_pct = trade_info.get('수익률', 0)
        
        if return_pct > 15:
            return f"성공 요인: {emotion} 상태에서도 좋은 결과"
        elif return_pct < -15:
            return f"주의 사항: {emotion} 감정이 손실로 이어짐"
        else:
            return f"평범한 결과: {emotion} 감정의 영향 분석 필요"
    
    def _detect_emotion_pattern(self, similar_experiences: List[Dict]) -> str:
        """감정 패턴 감지"""
        emotions = [exp['trade_data'].get('감정태그', '') for exp in similar_experiences]
        emotion_counts = pd.Series(emotions).value_counts()
        
        if len(emotion_counts) > 0:
            return emotion_counts.index[0]  # 가장 빈번한 감정
        return ""
    
    def _analyze_same_stock_pattern(self, same_stock_trades: pd.DataFrame) -> Dict:
        """동일 종목 거래 패턴 분석"""
        return {
            'total_trades': len(same_stock_trades),
            'avg_return': round(same_stock_trades['수익률'].mean(), 2),
            'win_rate': round((same_stock_trades['수익률'] > 0).mean() * 100, 1),
            'best_return': round(same_stock_trades['수익률'].max(), 2),
            'worst_return': round(same_stock_trades['수익률'].min(), 2),
            'most_common_emotion': same_stock_trades['감정태그'].mode().iloc[0] if len(same_stock_trades) > 0 else None
        }
    
    def _analyze_emotion_pattern(self, emotion_trades: pd.DataFrame) -> Dict:
        """감정별 거래 패턴 분석"""
        return {
            'total_trades': len(emotion_trades),
            'avg_return': round(emotion_trades['수익률'].mean(), 2),
            'win_rate': round((emotion_trades['수익률'] > 0).mean() * 100, 1),
            'volatility': round(emotion_trades['수익률'].std(), 2),
            'advice': self._get_emotion_advice(emotion_trades['감정태그'].iloc[0])
        }
    
    def _analyze_seasonal_pattern(self, month_trades: pd.DataFrame, month: int) -> Dict:
        """계절적/월별 거래 패턴 분석"""
        month_names = {
            1: '1월', 2: '2월', 3: '3월', 4: '4월', 5: '5월', 6: '6월',
            7: '7월', 8: '8월', 9: '9월', 10: '10월', 11: '11월', 12: '12월'
        }
        
        return {
            'month_name': month_names.get(month, f'{month}월'),
            'total_trades': len(month_trades),
            'avg_return': round(month_trades['수익률'].mean(), 2),
            'pattern_strength': 'strong' if len(month_trades) > 10 else 'weak'
        }
    
    def _analyze_amount_pattern(self, all_trades: pd.DataFrame, current_amount: float) -> Dict:
        """거래 금액별 패턴 분석"""
        all_trades = all_trades.copy()
        all_trades['거래금액'] = all_trades['수량'] * all_trades['가격']
        
        # 거래 금액 구간별 분석
        percentiles = all_trades['거래금액'].quantile([0.25, 0.5, 0.75])
        
        if current_amount <= percentiles[0.25]:
            size_category = "소액"
        elif current_amount <= percentiles[0.75]:
            size_category = "보통"
        else:
            size_category = "대액"
        
        # 해당 구간의 평균 수익률
        if size_category == "소액":
            similar_amount_trades = all_trades[all_trades['거래금액'] <= percentiles[0.25]]
        elif size_category == "보통":
            similar_amount_trades = all_trades[
                (all_trades['거래금액'] > percentiles[0.25]) & 
                (all_trades['거래금액'] <= percentiles[0.75])
            ]
        else:
            similar_amount_trades = all_trades[all_trades['거래금액'] > percentiles[0.75]]
        
        return {
            'size_category': size_category,
            'avg_return_in_category': round(similar_amount_trades['수익률'].mean(), 2),
            'trades_in_category': len(similar_amount_trades),
            'risk_level': 'high' if size_category == "대액" else 'medium' if size_category == "보통" else 'low'
        }
    
    def _get_emotion_advice(self, emotion: str) -> str:
        """감정별 조언"""
        advice_map = {
            '#공포': "공포 감정은 종종 비합리적 판단으로 이어집니다. 객관적 근거를 다시 검토해보세요.",
            '#욕심': "욕심은 위험 관리를 소홀히 만들 수 있습니다. 적정 투자 규모를 지키세요.",
            '#패닉': "패닉 상태에서는 24시간 냉각기간을 갖는 것이 도움이 됩니다.",
            '#추격매수': "급등 후 추격매수는 고점매수 위험이 높습니다. 신중하게 접근하세요.",
            '#불안': "불안감이 클 때는 투자 비중을 줄이는 것도 좋은 전략입니다.",
            '#확신': "확신이 과도할 때도 위험합니다. 반대 시나리오도 고려해보세요.",
            '#합리적': "합리적 접근을 유지하되, 감정을 완전히 배제할 필요는 없습니다."
        }
        return advice_map.get(emotion, "감정과 이성의 균형을 잘 맞춰보세요.")
    
    def _generate_key_insights(self, similar_experiences: List[Dict]) -> List[str]:
        """핵심 인사이트 생성"""
        insights = []
        
        if not similar_experiences:
            return ["과거 유사 경험이 부족합니다. 신중한 접근을 권장합니다."]
        
        # 수익률 기반 인사이트
        returns = [exp['trade_data']['수익률'] for exp in similar_experiences]
        avg_return = np.mean(returns)
        
        if avg_return > 5:
            insights.append(f"🎯 유사한 상황에서 평균 {avg_return:.1f}%의 수익을 기록했습니다.")
        elif avg_return < -5:
            insights.append(f"⚠️ 유사한 상황에서 평균 {abs(avg_return):.1f}%의 손실이 발생했습니다.")
        else:
            insights.append("📊 유사한 상황에서 보통의 결과를 보였습니다.")
        
        # 감정 패턴 인사이트
        emotions = [exp['trade_data'].get('감정태그', '') for exp in similar_experiences]
        emotion_series = pd.Series(emotions)
        if len(emotion_series) > 0:
            most_common_emotion = emotion_series.mode().iloc[0]
            insights.append(f"🧠 과거 유사 상황에서 주로 '{most_common_emotion}' 감정이 나타났습니다.")
        
        # 시기적 패턴
        dates = [pd.to_datetime(exp['trade_data']['거래일시']) for exp in similar_experiences]
        if len(dates) > 1:
            months = [d.month for d in dates]
            if len(set(months)) == 1:
                month_name = f"{months[0]}월"
                insights.append(f"📅 {month_name}에 유사한 패턴이 반복되는 경향이 있습니다.")
        
        return insights[:3]  # 최대 3개까지