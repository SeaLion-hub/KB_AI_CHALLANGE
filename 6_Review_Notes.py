import streamlit as st
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ui_components import apply_toss_css
from db.central_data_manager import get_data_manager, get_user_profile

# 페이지 설정
st.set_page_config(
    page_title="KB Reflex - 복기 노트",
    page_icon="📝",
    layout="wide"
)

# Toss 스타일 CSS 적용
apply_toss_css()

# 로그인 확인
if 'current_user' not in st.session_state or st.session_state.current_user is None:
    st.error("⚠️ 로그인이 필요합니다.")
    if st.button("🏠 홈으로 돌아가기"):
        st.switch_page("main_app.py")
    st.stop()

user = st.session_state.current_user
username = user['username']

def initialize_sample_notes():
    """샘플 복기 노트 초기화"""
    if 'review_notes' not in st.session_state:
        # 중앙 데이터 매니저에서 사용자 프로필 확인
        user_profile = get_user_profile(username)
        
        if not user_profile or user_profile.username == "이거울":
            st.session_state.review_notes = []
        elif user_profile.username == "박투자":
            st.session_state.review_notes = [
                {
                    'trade_date': '2024-07-15',
                    'stock_name': '삼성전자',
                    'original_emotion': '#욕심',
                    'reviewed_emotion': '#후회',
                    'decision_basis': ['뉴스/정보', '주변 권유'],
                    'lessons_learned': '급등 뉴스만 보고 충분한 분석 없이 매수했다. 다음번에는 최소 1일은 검토 시간을 갖자.',
                    'future_principles': '1) 뉴스 기반 투자 시 24시간 냉각기간 갖기 2) 기술적 분석 최소 3가지 지표 확인',
                    'decision_score': 3,
                    'emotion_control_score': 2,
                    'is_favorite': True,
                    'review_date': '2024-07-20 14:30:00'
                },
                {
                    'trade_date': '2024-08-03',
                    'stock_name': 'NAVER',
                    'original_emotion': '#확신',
                    'reviewed_emotion': '#만족',
                    'decision_basis': ['기술적 분석', '기본적 분석'],
                    'lessons_learned': '충분한 분석 후 투자했더니 좋은 결과가 나왔다. 이런 접근을 계속 유지해야겠다.',
                    'future_principles': '성공 요인을 체크리스트로 만들어서 매번 확인하기',
                    'decision_score': 8,
                    'emotion_control_score': 7,
                    'is_favorite': True,
                    'review_date': '2024-08-08 09:15:00'
                },
                {
                    'trade_date': '2024-08-20',
                    'stock_name': 'SK하이닉스',
                    'original_emotion': '#불안',
                    'reviewed_emotion': '#불안',
                    'decision_basis': ['감정적 충동', '뉴스/정보'],
                    'lessons_learned': '반도체 급락 소식에 불안해서 손절했는데, 며칠 뒤 반등했다. 감정보다 팩트를 봐야 한다.',
                    'future_principles': '손절 전 반드시 펀더멘털 재검토하기',
                    'decision_score': 4,
                    'emotion_control_score': 3,
                    'is_favorite': False,
                    'review_date': '2024-08-25 16:45:00'
                }
            ]
        else:  # 김국민
            st.session_state.review_notes = [
                {
                    'trade_date': '2024-06-10',
                    'stock_name': 'LG화학',
                    'original_emotion': '#공포',
                    'reviewed_emotion': '#냉정',
                    'decision_basis': ['감정적 충동'],
                    'lessons_learned': '시장 급락에 패닉셀링했지만, 냉정히 보니 회사 펀더멘털은 여전히 견고했다.',
                    'future_principles': '급락장에서는 무조건 24시간 기다리기',
                    'decision_score': 2,
                    'emotion_control_score': 2,
                    'is_favorite': True,
                    'review_date': '2024-06-15 10:20:00'
                },
                {
                    'trade_date': '2024-07-25',
                    'stock_name': '현대차',
                    'original_emotion': '#냉정',
                    'reviewed_emotion': '#냉정',
                    'decision_basis': ['기본적 분석', '기술적 분석'],
                    'decision_score': 9,
                    'lessons_learned': '체계적 분석을 통한 투자가 결국 가장 안전하다.',
                    'future_principles': '감정이 개입되면 체크리스트 확인하기',
                    'emotion_control_score': 8,
                    'is_favorite': True,
                    'review_date': '2024-07-30 15:30:00'
                },
                {
                    'trade_date': '2024-08-12',
                    'stock_name': 'POSCO홀딩스',
                    'original_emotion': '#확신',
                    'reviewed_emotion': '#후회',
                    'decision_basis': ['기본적 분석'],
                    'lessons_learned': '좋은 회사지만 타이밍이 안 좋았다. 매크로 환경도 고려해야 한다.',
                    'future_principles': '개별 종목 분석만큼 시장 환경 분석도 중요',
                    'decision_score': 6,
                    'emotion_control_score': 7,
                    'is_favorite': False,
                    'review_date': '2024-08-18 11:00:00'
                }
            ]

def show_notes_dashboard():
    """노트 대시보드"""
    st.markdown(f'''
    <div class="main-header-enhanced">
        📝 {username}님의 복기 노트
    </div>
    <div class="sub-header-enhanced">
        과거의 경험을 미래의 지혜로 바꾸는 투자 성장 일지
    </div>
    ''', unsafe_allow_html=True)
    
    notes = st.session_state.review_notes
    
    if not notes:
        show_empty_notes_state()
        return
    
    # 통계 카드
    show_notes_statistics(notes)
    
    # 필터 및 검색
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        emotion_filter = st.selectbox(
            "감정별 필터",
            ["전체"] + list(set([note['reviewed_emotion'] for note in notes]))
        )
    
    with col2:
        favorite_filter = st.selectbox(
            "즐겨찾기",
            ["전체", "즐겨찾기만", "일반 노트"]
        )
    
    with col3:
        score_filter = st.selectbox(
            "점수별 정렬",
            ["최신순", "의사결정 점수 높은순", "의사결정 점수 낮은순", "감정조절 점수 높은순", "감정조절 점수 낮은순"]
        )
    
    with col4:
        search_query = st.text_input("검색", placeholder="종목명 또는 내용 검색")
    
    # 필터링
    filtered_notes = filter_notes(notes, emotion_filter, favorite_filter, search_query)
    
    # 정렬
    filtered_notes = sort_notes(filtered_notes, score_filter)
    
    # 노트 카드들 표시
    show_notes_list(filtered_notes)

def show_empty_notes_state():
    """빈 노트 상태"""
    st.markdown('''
    <div class="premium-card" style="text-align: center; padding: 4rem;">
        <div style="font-size: 4rem; margin-bottom: 2rem;">📝</div>
        <h3 style="color: var(--text-primary); margin-bottom: 1rem;">첫 복기 노트를 작성해보세요!</h3>
        <p style="color: var(--text-secondary); margin-bottom: 2rem;">
            거래 복기를 통해 투자 실력을 한 단계 업그레이드할 수 있습니다.
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🪞 거래 복기하러 가기", key="goto_review_from_empty", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Trade_Review.py")

def show_notes_statistics(notes):
    """노트 통계"""
    st.markdown("### 📊 복기 인사이트")
    
    # 기본 통계
    total_notes = len(notes)
    favorite_notes = len([n for n in notes if n.get('is_favorite', False)])
    avg_decision_score = np.mean([n['decision_score'] for n in notes])
    avg_emotion_score = np.mean([n['emotion_control_score'] for n in notes])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        from utils.ui_components import create_enhanced_metric_card
        create_enhanced_metric_card("총 복기 노트", f"{total_notes}개", f"{favorite_notes}개 즐겨찾기")
    
    with col2:
        create_enhanced_metric_card("의사결정 점수", f"{avg_decision_score:.1f}/10", get_score_grade(avg_decision_score))
    
    with col3:
        create_enhanced_metric_card("감정조절 점수", f"{avg_emotion_score:.1f}/10", get_score_grade(avg_emotion_score))
    
    with col4:
        # 가장 빈번한 감정
        emotions = [n['reviewed_emotion'] for n in notes]
        most_common_emotion = max(set(emotions), key=emotions.count) if emotions else "N/A"
        create_enhanced_metric_card("주요 감정 패턴", most_common_emotion, f"{emotions.count(most_common_emotion)}회")

def get_score_grade(score):
    """점수를 등급으로 변환"""
    if score >= 8:
        return "우수"
    elif score >= 6:
        return "양호"
    elif score >= 4:
        return "보통"
    else:
        return "개선 필요"

def filter_notes(notes, emotion_filter, favorite_filter, search_query):
    """노트 필터링"""
    filtered = notes.copy()
    
    # 감정 필터
    if emotion_filter != "전체":
        filtered = [n for n in filtered if n['reviewed_emotion'] == emotion_filter]
    
    # 즐겨찾기 필터
    if favorite_filter == "즐겨찾기만":
        filtered = [n for n in filtered if n.get('is_favorite', False)]
    elif favorite_filter == "일반 노트":
        filtered = [n for n in filtered if not n.get('is_favorite', False)]
    
    # 검색
    if search_query:
        search_lower = search_query.lower()
        filtered = [
            n for n in filtered 
            if search_lower in n['stock_name'].lower() or 
               search_lower in n.get('lessons_learned', '').lower() or
               search_lower in n.get('future_principles', '').lower()
        ]
    
    return filtered

def sort_notes(notes, sort_option):
    """노트 정렬"""
    if sort_option == "최신순":
        return sorted(notes, key=lambda x: x['review_date'], reverse=True)
    elif sort_option == "의사결정 점수 높은순":
        return sorted(notes, key=lambda x: x['decision_score'], reverse=True)
    elif sort_option == "의사결정 점수 낮은순":
        return sorted(notes, key=lambda x: x['decision_score'])
    elif sort_option == "감정조절 점수 높은순":
        return sorted(notes, key=lambda x: x['emotion_control_score'], reverse=True)
    else:  # 감정조절 점수 낮은순
        return sorted(notes, key=lambda x: x['emotion_control_score'])

def show_notes_list(notes):
    """노트 리스트 표시"""
    st.markdown("---")
    st.markdown(f"### 📋 복기 노트 ({len(notes)}개)")
    
    if not notes:
        st.info("🔍 검색 조건에 맞는 노트가 없습니다.")
        return
    
    for i, note in enumerate(notes):
        show_note_card(note, i)

def show_note_card(note, index):
    """개별 노트 카드"""
    # 감정에 따른 색상
    emotion_colors = {
        '#공포': '#EF4444', '#불안': '#F87171', '#후회': '#DC2626',
        '#욕심': '#F59E0B', '#확신': '#10B981', '#냉정': '#047857', '#만족': '#059669'
    }
    
    emotion = note['reviewed_emotion']
    emotion_color = emotion_colors.get(emotion, '#6B7280')
    
    # 점수에 따른 카드 테두리 색상
    avg_score = (note['decision_score'] + note['emotion_control_score']) / 2
    if avg_score >= 7:
        border_color = "#10B981"
    elif avg_score >= 5:
        border_color = "#F59E0B"
    else:
        border_color = "#EF4444"
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f'''
        <div style="
            background: white;
            border: 2px solid {border_color};
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        " class="note-card-{index}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <div>
                    <h3 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.75rem;">
                        {note['stock_name']}
                        {'⭐' if note.get('is_favorite', False) else ''}
                    </h3>
                    <div style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 0.5rem;">
                        거래일: {note['trade_date']} • 복기일: {note['review_date'][:10]}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span style="
                            background: {emotion_color}15;
                            color: {emotion_color};
                            padding: 0.5rem 1rem;
                            border-radius: 16px;
                            font-size: 0.85rem;
                            font-weight: 600;
                            border: 1px solid {emotion_color}30;
                        ">{emotion}</span>
                    </div>
                </div>
            </div>
            
            <!-- 감정 변화 -->
            <div style="
                background: #F8FAFC;
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                border-left: 4px solid {emotion_color};
            ">
                <div style="font-size: 0.85rem; color: var(--text-light); margin-bottom: 0.5rem;">감정 변화</div>
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <span style="color: var(--text-secondary);">{note['original_emotion']}</span>
                    <span style="color: var(--text-light);">→</span>
                    <span style="color: {emotion_color}; font-weight: 600;">{note['reviewed_emotion']}</span>
                </div>
            </div>
            
            <!-- 점수 -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
                <div style="text-align: center; background: #F0F9FF; padding: 1rem; border-radius: 12px;">
                    <div style="color: var(--text-light); font-size: 0.85rem;">의사결정</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #3B82F6;">{note['decision_score']}/10</div>
                </div>
                <div style="text-align: center; background: #F0FDF4; padding: 1rem; border-radius: 12px;">
                    <div style="color: var(--text-light); font-size: 0.85rem;">감정조절</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">{note['emotion_control_score']}/10</div>
                </div>
            </div>
            
            <!-- 판단 근거 -->
            <div style="margin-bottom: 1.5rem;">
                <div style="color: var(--text-light); font-size: 0.85rem; margin-bottom: 0.5rem;">판단 근거</div>
                <div>
                    {' '.join([f'<span style="background: #EBF4FF; color: #3B82F6; padding: 0.25rem 0.5rem; border-radius: 8px; font-size: 0.8rem; margin-right: 0.5rem;">{basis}</span>' for basis in note.get('decision_basis', [])])}
                </div>
            </div>
            
            <!-- 배운 점 -->
            <div style="margin-bottom: 1.5rem;">
                <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.75rem;">💡 배운 점</div>
                <div style="color: var(--text-secondary); line-height: 1.6; font-style: italic;">
                    "{note.get('lessons_learned', '')}"
                </div>
            </div>
            
            <!-- 향후 원칙 -->
            <div>
                <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.75rem;">📜 향후 원칙</div>
                <div style="color: var(--text-secondary); line-height: 1.6;">
                    {note.get('future_principles', '')}
                </div>
            </div>
        </div>
        
        <style>
        .note-card-{index}:hover {{
            transform: translateY(-4px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        }}
        </style>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 간격 맞추기
        
        if st.button("📝 수정", key=f"edit_note_{index}", use_container_width=True):
            st.session_state.editing_note = note
            st.session_state.editing_index = index
            st.rerun()
        
        if st.button("🗑️ 삭제", key=f"delete_note_{index}", use_container_width=True):
            st.session_state.review_notes.pop(index)
            st.success("노트가 삭제되었습니다.")
            time.sleep(1)
            st.rerun()
        
        if note.get('is_favorite', False):
            if st.button("⭐ 즐겨찾기 해제", key=f"unfav_note_{index}", use_container_width=True):
                st.session_state.review_notes[index]['is_favorite'] = False
                st.rerun()
        else:
            if st.button("☆ 즐겨찾기", key=f"fav_note_{index}", use_container_width=True):
                st.session_state.review_notes[index]['is_favorite'] = True
                st.rerun()

def show_edit_note_modal():
    """노트 수정 모달"""
    if 'editing_note' not in st.session_state:
        return
    
    note = st.session_state.editing_note
    index = st.session_state.editing_index
    
    st.markdown("### ✏️ 복기 노트 수정")
    
    with st.form("edit_note_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_emotion = st.selectbox(
                "재평가된 감정",
                ['#공포', '#욕심', '#확신', '#불안', '#냉정', '#후회', '#만족'],
                index=['#공포', '#욕심', '#확신', '#불안', '#냉정', '#후회', '#만족'].index(note['reviewed_emotion'])
            )
            
            new_decision_score = st.slider("의사결정 점수", 1, 10, note['decision_score'])
        
        with col2:
            new_decision_basis = st.multiselect(
                "판단 근거",
                ['기술적 분석', '기본적 분석', '뉴스/정보', '주변 권유', '직감', '감정적 충동', '기타'],
                default=note.get('decision_basis', [])
            )
            
            new_emotion_score = st.slider("감정조절 점수", 1, 10, note['emotion_control_score'])
        
        new_lessons = st.text_area(
            "배운 점과 개선점",
            value=note.get('lessons_learned', ''),
            height=100
        )
        
        new_principles = st.text_area(
            "향후 투자 원칙",
            value=note.get('future_principles', ''),
            height=100
        )
        
        new_is_favorite = st.checkbox("⭐ 즐겨찾기", value=note.get('is_favorite', False))
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.form_submit_button("💾 저장", type="primary", use_container_width=True):
                st.session_state.review_notes[index].update({
                    'reviewed_emotion': new_emotion,
                    'decision_basis': new_decision_basis,
                    'lessons_learned': new_lessons,
                    'future_principles': new_principles,
                    'decision_score': new_decision_score,
                    'emotion_control_score': new_emotion_score,
                    'is_favorite': new_is_favorite,
                    'review_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                del st.session_state.editing_note
                del st.session_state.editing_index
                
                st.success("노트가 수정되었습니다!")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ 취소", use_container_width=True):
                del st.session_state.editing_note
                del st.session_state.editing_index
                st.rerun()

def show_insights_summary():
    """인사이트 요약"""
    notes = st.session_state.review_notes
    if not notes or len(notes) < 3:
        return
    
    st.markdown("---")
    st.markdown("### 🧠 AI 패턴 분석")
    
    # 감정 패턴 분석
    emotions = [n['reviewed_emotion'] for n in notes]
    emotion_counts = {}
    for emotion in emotions:
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    most_common_emotion = max(emotion_counts, key=emotion_counts.get)
    
    # 점수 추이 분석
    recent_notes = sorted(notes, key=lambda x: x['review_date'])[-5:]  # 최근 5개
    decision_scores = [n['decision_score'] for n in recent_notes]
    emotion_scores = [n['emotion_control_score'] for n in recent_notes]
    
    decision_trend = "상승" if len(decision_scores) > 1 and decision_scores[-1] > decision_scores[0] else "하락" if len(decision_scores) > 1 and decision_scores[-1] < decision_scores[0] else "보합"
    emotion_trend = "상승" if len(emotion_scores) > 1 and emotion_scores[-1] > emotion_scores[0] else "하락" if len(emotion_scores) > 1 and emotion_scores[-1] < emotion_scores[0] else "보합"
    
    from utils.ui_components import create_mirror_coaching_card
    
    insights = [
        f"🎯 가장 빈번한 감정 패턴: {most_common_emotion} ({emotion_counts[most_common_emotion]}회)",
        f"📈 의사결정 능력 추이: {decision_trend} (평균 {np.mean(decision_scores):.1f}점)",
        f"🧘‍♂️ 감정조절 능력 추이: {emotion_trend} (평균 {np.mean(emotion_scores):.1f}점)"
    ]
    
    questions = [
        f"왜 {most_common_emotion} 감정이 자주 나타날까요?",
        "점수가 낮은 거래들의 공통점은 무엇인가요?",
        "가장 성공적이었던 거래의 특징을 다른 거래에도 적용할 수 있을까요?"
    ]
    
    create_mirror_coaching_card(
        "복기 노트 패턴 분석",
        insights,
        questions
    )

# 메인 로직
def main():
    initialize_sample_notes()
    
    # 노트 수정 모달 우선 표시
    if 'editing_note' in st.session_state:
        show_edit_note_modal()
        return
    
    # 메인 화면
    show_notes_dashboard()
    show_insights_summary()

if __name__ == "__main__":
    main()