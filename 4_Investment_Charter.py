import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
from main_app import SessionKeys
# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from db.principles_db import get_investment_principles, get_principle_details
from utils.ui_components import apply_toss_css, create_mirror_coaching_card
from db.central_data_manager import get_data_manager, get_user_profile

# 페이지 설정
st.set_page_config(
    page_title="KB Reflex - 투자 헌장",
    page_icon="📜",
    layout="wide"
)

# Toss 스타일 CSS 적용
apply_toss_css()

# ✅ 수정된 코드 (이것으로 교체)
# 로그인 상태 확인 (main_app.py와 동일한 키 사용)
def get_current_user():
    # 1차: 메인 키 확인
    user = st.session_state.get('REFLEX_USER')
    if user:
        return user
    
    # 2차: 백업 키 확인
    backup_user = st.session_state.get('current_user')
    if backup_user:
        # 메인 키에 복사
        st.session_state['REFLEX_USER'] = backup_user
        return backup_user
    
    return None

# 로그인 체크
current_user = get_current_user()
if current_user is None:
    st.error("⚠️ 로그인이 필요합니다.")
    if st.button("🏠 홈으로 돌아가기"):
        try:
            st.switch_page("main_app.py")
        except:
            st.rerun()
    st.stop()

user = current_user
username = user['username']

def initialize_user_charter():
    """사용자별 투자 헌장 초기화"""
    if 'investment_charter' not in st.session_state:
        # 중앙 데이터 매니저에서 사용자 프로필 로드
        user_profile = get_user_profile(username)
        
        if not user_profile:
            # 기본 헌장 생성
            st.session_state.investment_charter = create_default_charter("벤저민 그레이엄")
            return
        
        if user_profile.username == "이거울":
            # 신규 사용자 - 선택된 원칙 기반 기본 헌장
            selected_principle = st.session_state.get('selected_principle', '벤저민 그레이엄')
            st.session_state.investment_charter = create_default_charter(selected_principle)
        elif user_profile.username == "박투자":
            # 기존 사용자 - 일부 원칙만 설정된 상태
            st.session_state.investment_charter = {
                'core_philosophy': '장기적 관점에서 가치투자를 추구합니다.',
                'risk_management': [
                    '한 종목에 포트폴리오의 10% 이상 투자하지 않기',
                    '손실 한도 -20%에서 반드시 재검토'
                ],
                'emotional_rules': [
                    '급락장에서 24시간 냉각기간 갖기',
                    '뉴스 기반 투자 시 최소 1일 검토 시간 갖기'
                ],
                'decision_criteria': [
                    'PER 20 이하, PBR 2 이하인 종목 우선 고려',
                    '기술적 분석 최소 3가지 지표 확인'
                ],
                'learning_goals': [
                    '월 1회 이상 복기 노트 작성',
                    'FOMO 매수 패턴 개선하기'
                ],
                'created_date': '2024-07-01',
                'last_updated': '2024-08-15',
                'version': 2
            }
        else:  # 김국민
            # 경험 많은 사용자 - 완성도 높은 헌장
            st.session_state.investment_charter = {
                'core_philosophy': '감정을 배제하고 데이터 기반으로 의사결정하며, 장기적 관점에서 우량 기업에 분산투자합니다.',
                'risk_management': [
                    '포트폴리오의 60% 이상을 현금으로 보유하지 않기',
                    '한 종목 비중 15% 이하 유지',
                    '손절선 -15%, 익절 목표 +30% 설정',
                    '시장 급변동 시 무조건 24시간 대기 원칙'
                ],
                'emotional_rules': [
                    '공포나 욕심이 느껴질 때는 투자 규모를 50% 축소',
                    '연속 3회 손실 시 1주일 투자 중단',
                    '미디어 노이즈에 흔들리지 않기'
                ],
                'decision_criteria': [
                    '기업 가치 > 현재 주가인 종목만 투자',
                    'ROE 10% 이상, 부채비율 200% 이하',
                    '최소 3년 이상 안정적 성장 기업',
                    '경영진 변화나 사업구조 변화 면밀 검토'
                ],
                'learning_goals': [
                    '월 2회 포트폴리오 리뷰',
                    '분기별 투자 성과 분석 및 전략 수정',
                    '연간 투자 서적 12권 이상 독서'
                ],
                'created_date': '2023-12-01',
                'last_updated': '2024-08-01',
                'version': 5
            }

def create_default_charter(principle_name):
    """선택된 원칙 기반 기본 헌장 생성"""
    principle_details = get_principle_details(principle_name)
    
    if principle_name == "벤저민 그레이엄":
        return {
            'core_philosophy': '안전마진을 확보한 가치투자를 통해 장기적으로 안정적인 수익을 추구합니다.',
            'risk_management': [
                '분산투자를 통해 위험 최소화',
                '안전마진 30% 이상 확보된 종목만 투자'
            ],
            'emotional_rules': [
                '시장의 감정에 휩쓸리지 않기',
                '충분한 검토 시간 갖기'
            ],
            'decision_criteria': [
                'PBR 1.5 이하, 부채비율 낮은 기업',
                '안정적인 수익성과 배당 기록'
            ],
            'learning_goals': [
                '기업 분석 능력 향상',
                '인내심 기르기'
            ],
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'version': 1
        }
    elif principle_name == "피터 린치":
        return {
            'core_philosophy': '일상에서 발견한 좋은 기업에 성장투자하여 장기적으로 큰 수익을 추구합니다.',
            'risk_management': [
                '이해할 수 있는 기업에만 투자',
                '성장성과 가격의 균형 고려 (PEG < 1)'
            ],
            'emotional_rules': [
                '스토리에만 의존하지 않기',
                '숫자로 검증하기'
            ],
            'decision_criteria': [
                '매출 성장률 20% 이상 기업',
                '시장 지배력이 있는 기업'
            ],
            'learning_goals': [
                '생활 속 투자 아이디어 발굴',
                '성장주 분석 능력 향상'
            ],
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'version': 1
        }
    else:  # 워런 버핏
        return {
            'core_philosophy': '위대한 기업을 합리적인 가격에 매수하여 영구 보유합니다.',
            'risk_management': [
                '집중투자를 통한 최적화',
                '경제적 해자가 있는 기업만 투자'
            ],
            'emotional_rules': [
                '장기적 관점 유지',
                '시장 타이밍 맞추려 하지 않기'
            ],
            'decision_criteria': [
                'ROE 15% 이상 지속 기업',
                '이해 가능한 비즈니스 모델'
            ],
            'learning_goals': [
                '기업 내재가치 평가 능력',
                '장기 투자 인내심'
            ],
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'version': 1
        }

def show_charter_overview():
    """투자 헌장 개요"""
    st.markdown(f'''
    <div class="main-header-enhanced">
        📜 {username}님의 투자 헌장
    </div>
    <div class="sub-header-enhanced">
        나만의 투자 원칙과 철학을 정리하여 일관된 투자를 실행하세요
    </div>
    ''', unsafe_allow_html=True)
    
    charter = st.session_state.investment_charter
    
    # 헌장 정보 카드
    col1, col2, col3 = st.columns(3)
    
    with col1:
        from utils.ui_components import create_enhanced_metric_card
        create_enhanced_metric_card(
            "헌장 버전",
            f"v{charter['version']}",
            f"생성일: {charter['created_date']}"
        )
    
    with col2:
        total_rules = (len(charter.get('risk_management', [])) + 
                      len(charter.get('emotional_rules', [])) + 
                      len(charter.get('decision_criteria', [])))
        create_enhanced_metric_card(
            "투자 원칙",
            f"{total_rules}개",
            f"최종 수정: {charter['last_updated']}"
        )
    
    with col3:
        create_enhanced_metric_card(
            "학습 목표",
            f"{len(charter.get('learning_goals', []))}개",
            "지속적 개선"
        )

def show_charter_content():
    """투자 헌장 내용 표시"""
    st.markdown("### 📋 투자 헌장 내용")
    
    charter = st.session_state.investment_charter
    
    # 핵심 철학
    st.markdown('''
    <div class="premium-card">
        <div class="premium-card-title">🎯 투자 철학</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown(f'''
    <div style="
        background: linear-gradient(135deg, #EBF4FF 0%, #DBEAFE 100%);
        border: 2px solid #93C5FD;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    ">
        <div style="font-size: 1.2rem; color: #1D4ED8; font-weight: 600; font-style: italic; line-height: 1.6;">
            "{charter['core_philosophy']}"
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 투자 원칙들
    col1, col2 = st.columns(2)
    
    with col1:
        show_charter_section("🛡️ 위험 관리", charter.get('risk_management', []), "#EF4444")
        show_charter_section("🎯 투자 기준", charter.get('decision_criteria', []), "#10B981")
    
    with col2:
        show_charter_section("🧠 감정 관리", charter.get('emotional_rules', []), "#F59E0B")
        show_charter_section("📚 학습 목표", charter.get('learning_goals', []), "#8B5CF6")

def show_charter_section(title, items, color):
    """헌장 섹션 표시"""
    st.markdown(f'''
    <div class="premium-card">
        <div class="premium-card-title" style="color: {color};">{title}</div>
        <div style="margin-top: 1rem;">
    ''', unsafe_allow_html=True)
    
    for item in items:
        st.markdown(f'''
        <div style="
            background: {color}10;
            border: 1px solid {color}30;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
        ">
            <div style="
                width: 6px;
                height: 6px;
                background: {color};
                border-radius: 50%;
                margin-right: 0.75rem;
                flex-shrink: 0;
            "></div>
            <div style="color: var(--text-primary); line-height: 1.4;">{item}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)

def show_charter_actions():
    """헌장 관련 액션"""
    st.markdown("---")
    st.markdown("### ⚙️ 헌장 관리")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✏️ 헌장 수정", key="edit_charter", use_container_width=True, type="primary"):
            st.session_state.editing_charter = True
            st.rerun()
    
    with col2:
        if st.button("📊 준수도 체크", key="check_compliance", use_container_width=True):
            show_compliance_check()
    
    with col3:
        if st.button("💡 AI 제안", key="ai_suggestions", use_container_width=True):
            show_ai_charter_suggestions()
    
    with col4:
        if st.button("📄 헌장 내보내기", key="export_charter", use_container_width=True):
            export_charter()

def show_charter_editor():
    """헌장 수정 인터페이스"""
    st.markdown("### ✏️ 투자 헌장 수정")
    
    charter = st.session_state.investment_charter
    
    with st.form("edit_charter_form"):
        # 핵심 철학
        st.markdown("#### 🎯 핵심 투자 철학")
        new_philosophy = st.text_area(
            "당신의 투자 철학을 한 문장으로 표현해주세요",
            value=charter['core_philosophy'],
            height=80
        )
        
        # 각 섹션 편집
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🛡️ 위험 관리 원칙")
            new_risk_rules = []
            for i, rule in enumerate(charter.get('risk_management', []) + ['']):
                new_rule = st.text_input(f"위험 관리 #{i+1}", value=rule, key=f"risk_{i}")
                if new_rule.strip():
                    new_risk_rules.append(new_rule.strip())
            
            # 추가 입력 필드
            for i in range(2):
                new_rule = st.text_input(f"위험 관리 #{len(new_risk_rules)+i+1}", key=f"risk_new_{i}")
                if new_rule.strip():
                    new_risk_rules.append(new_rule.strip())
        
        with col2:
            st.markdown("#### 🧠 감정 관리 원칙")
            new_emotion_rules = []
            for i, rule in enumerate(charter.get('emotional_rules', []) + ['']):
                new_rule = st.text_input(f"감정 관리 #{i+1}", value=rule, key=f"emotion_{i}")
                if new_rule.strip():
                    new_emotion_rules.append(new_rule.strip())
            
            # 추가 입력 필드
            for i in range(2):
                new_rule = st.text_input(f"감정 관리 #{len(new_emotion_rules)+i+1}", key=f"emotion_new_{i}")
                if new_rule.strip():
                    new_emotion_rules.append(new_rule.strip())
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### 🎯 투자 판단 기준")
            new_decision_rules = []
            for i, rule in enumerate(charter.get('decision_criteria', []) + ['']):
                new_rule = st.text_input(f"판단 기준 #{i+1}", value=rule, key=f"decision_{i}")
                if new_rule.strip():
                    new_decision_rules.append(new_rule.strip())
            
            # 추가 입력 필드
            for i in range(2):
                new_rule = st.text_input(f"판단 기준 #{len(new_decision_rules)+i+1}", key=f"decision_new_{i}")
                if new_rule.strip():
                    new_decision_rules.append(new_rule.strip())
        
        with col4:
            st.markdown("#### 📚 학습 및 개선 목표")
            new_learning_goals = []
            for i, goal in enumerate(charter.get('learning_goals', []) + ['']):
                new_goal = st.text_input(f"학습 목표 #{i+1}", value=goal, key=f"learning_{i}")
                if new_goal.strip():
                    new_learning_goals.append(new_goal.strip())
            
            # 추가 입력 필드
            for i in range(2):
                new_goal = st.text_input(f"학습 목표 #{len(new_learning_goals)+i+1}", key=f"learning_new_{i}")
                if new_goal.strip():
                    new_learning_goals.append(new_goal.strip())
        
        # 제출 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.form_submit_button("💾 저장", type="primary", use_container_width=True):
                # 헌장 업데이트
                st.session_state.investment_charter.update({
                    'core_philosophy': new_philosophy,
                    'risk_management': new_risk_rules,
                    'emotional_rules': new_emotion_rules,
                    'decision_criteria': new_decision_rules,
                    'learning_goals': new_learning_goals,
                    'last_updated': datetime.now().strftime('%Y-%m-%d'),
                    'version': charter['version'] + 1
                })
                
                st.session_state.editing_charter = False
                st.success("투자 헌장이 업데이트되었습니다!")
                st.balloons()
                st.rerun()
        
        with col2:
            if st.form_submit_button("🔄 초기화", use_container_width=True):
                # 원칙 기반 헌장으로 초기화
                principle = st.session_state.get('selected_principle', '벤저민 그레이엄')
                st.session_state.investment_charter = create_default_charter(principle)
                st.session_state.editing_charter = False
                st.success("기본 헌장으로 초기화되었습니다!")
                st.rerun()
        
        with col3:
            if st.form_submit_button("❌ 취소", use_container_width=True):
                st.session_state.editing_charter = False
                st.rerun()

def show_compliance_check():
    """헌장 준수도 체크"""
    st.markdown("---")
    st.markdown("### 📊 투자 헌장 준수도 분석")
    
    # 복기 노트 데이터를 기반으로 준수도 분석
    review_notes = st.session_state.get('review_notes', [])
    
    if not review_notes:
        st.info("📝 복기 노트가 없어서 준수도를 분석할 수 없습니다. 거래 복기를 먼저 해보세요!")
        return
    
    # 감정 관리 준수도 분석
    emotional_violations = 0
    recent_notes = review_notes[-10:] if len(review_notes) >= 10 else review_notes
    
    for note in recent_notes:
        if note['emotion_control_score'] < 5:  # 감정조절 점수가 낮으면 위반
            emotional_violations += 1
    
    emotion_compliance = max(0, (len(recent_notes) - emotional_violations) / len(recent_notes) * 100)
    
    # 의사결정 준수도 분석
    decision_violations = 0
    for note in recent_notes:
        if note['decision_score'] < 5:  # 의사결정 점수가 낮으면 위반
            decision_violations += 1
    
    decision_compliance = max(0, (len(recent_notes) - decision_violations) / len(recent_notes) * 100)
    
    # 전체 준수도
    overall_compliance = (emotion_compliance + decision_compliance) / 2
    
    # 시각화
    col1, col2, col3 = st.columns(3)
    
    with col1:
        compliance_color = "#10B981" if overall_compliance >= 80 else "#F59E0B" if overall_compliance >= 60 else "#EF4444"
        st.markdown(f'''
        <div style="
            background: white;
            border: 2px solid {compliance_color};
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{overall_compliance:.0f}%</div>
            <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.5rem;">전체 준수도</div>
            <div style="color: {compliance_color}; font-size: 0.85rem;">
                {'우수' if overall_compliance >= 80 else '보통' if overall_compliance >= 60 else '개선 필요'}
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div style="
            background: white;
            border: 2px solid #8B5CF6;
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{emotion_compliance:.0f}%</div>
            <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.5rem;">감정 관리</div>
            <div style="color: #8B5CF6; font-size: 0.85rem;">
                최근 {len(recent_notes)}건 거래 기준
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div style="
            background: white;
            border: 2px solid #3B82F6;
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{decision_compliance:.0f}%</div>
            <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.5rem;">의사결정</div>
            <div style="color: #3B82F6; font-size: 0.85rem;">
                객관적 근거 기반 판단
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # 개선 제안
    if overall_compliance < 80:
        improvement_tips = []
        if emotion_compliance < decision_compliance:
            improvement_tips.append("🧘‍♂️ 감정 관리 기술 향상이 우선 필요합니다")
            improvement_tips.append("⏰ 투자 전 충분한 냉각 시간을 가져보세요")
        else:
            improvement_tips.append("📊 더 체계적인 분석 방법을 익혀보세요")
            improvement_tips.append("📚 투자 관련 지식을 더 쌓아보세요")
        
        create_mirror_coaching_card(
            "헌장 준수도 개선 방안",
            improvement_tips + [f"💯 목표: 준수도 80% 이상 달성 (현재 {overall_compliance:.0f}%)"],
            [
                "가장 자주 어기는 원칙은 무엇인가요?",
                "어떤 상황에서 헌장을 무시하게 되나요?",
                "헌장을 더 지키기 쉽게 만들려면?"
            ]
        )

def show_ai_charter_suggestions():
    """AI 헌장 개선 제안"""
    st.markdown("---")
    st.markdown("### 💡 AI 투자 헌장 개선 제안")
    
    # 사용자 프로필에 따른 맞춤 제안
    user_profile = get_user_profile(username)
    
    if not user_profile:
        suggestions = [
            "📚 초보자를 위한 '투자 전 체크리스트' 활용",
            "💰 초기 자본 보호를 위한 '종목당 최대 5% 투자' 원칙",
            "📖 월 1권 투자 서적 독서 목표 설정",
            "🎯 분산투자를 위한 '최소 5개 종목 보유' 원칙"
        ]
    elif user_profile.username == "박투자":
        suggestions = [
            "🎯 FOMO 매수 방지를 위한 '24시간 대기' 원칙 강화",
            "📰 뉴스 기반 투자 시 '3가지 독립 소스 확인' 규칙 추가", 
            "💰 추격매수 방지를 위한 '상승률 10% 초과 시 투자 금지' 원칙",
            "🧘‍♂️ 감정적 투자 방지를 위한 '명상 5분 후 투자' 습관"
        ]
    elif user_profile.username == "김국민":
        suggestions = [
            "🛡️ 공포매도 방지를 위한 '손절 전 펀더멘털 재검토' 의무화",
            "📈 시장 타이밍보다 기업 가치에 집중하는 원칙 강화",
            "⏰ 급락장 대응 매뉴얼 세분화 (5%, 10%, 15% 구간별)",
            "📊 정량적 지표 기반 매수/매도 기준 명문화"
        ]
    else:  # 이거울
        suggestions = [
            "📚 초보자를 위한 '투자 전 체크리스트' 활용",
            "💰 초기 자본 보호를 위한 '종목당 최대 5% 투자' 원칙",
            "📖 월 1권 투자 서적 독서 목표 설정",
            "🎯 분산투자를 위한 '최소 5개 종목 보유' 원칙"
        ]
    
    create_mirror_coaching_card(
        "AI 분석 기반 헌장 개선 제안",
        suggestions,
        [
            "이 제안들 중 가장 필요하다고 생각하는 것은?",
            "현재 헌장에서 부족한 부분이 있다고 느끼시나요?",
            "실제로 지키기 어려운 원칙이 있나요?"
        ]
    )
    
    # 제안 적용 버튼들
    st.markdown("#### 🔧 제안 적용")
    for i, suggestion in enumerate(suggestions):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"• {suggestion}")
        with col2:
            if st.button("✅ 적용", key=f"apply_suggestion_{i}", use_container_width=True):
                apply_ai_suggestion(suggestion)

def apply_ai_suggestion(suggestion):
    """AI 제안 적용"""
    charter = st.session_state.investment_charter
    
    # 제안 내용에 따라 적절한 섹션에 추가
    if "위험" in suggestion or "손실" in suggestion or "비중" in suggestion:
        charter['risk_management'].append(suggestion.split('🎯 ')[-1].split('🛡️ ')[-1].split('💰 ')[-1])
    elif "감정" in suggestion or "FOMO" in suggestion or "공포" in suggestion or "명상" in suggestion:
        charter['emotional_rules'].append(suggestion.split('🧘‍♂️ ')[-1].split('🎯 ')[-1].split('🛡️ ')[-1])
    elif "분석" in suggestion or "기준" in suggestion or "지표" in suggestion:
        charter['decision_criteria'].append(suggestion.split('📊 ')[-1].split('📰 ')[-1].split('⏰ ')[-1])
    else:
        charter['learning_goals'].append(suggestion.split('📚 ')[-1].split('📖 ')[-1])
    
    # 버전 업데이트
    charter['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    charter['version'] += 1
    
    st.success(f"✅ '{suggestion[:30]}...' 제안이 헌장에 적용되었습니다!")
    st.rerun()

def export_charter():
    """헌장 내보내기"""
    charter = st.session_state.investment_charter
    
    # 텍스트 포맷으로 헌장 생성
    charter_text = f"""
📜 {username}님의 투자 헌장 (v{charter['version']})
생성일: {charter['created_date']} | 최종수정: {charter['last_updated']}

🎯 핵심 투자 철학
{charter['core_philosophy']}

🛡️ 위험 관리 원칙
"""
    for i, rule in enumerate(charter.get('risk_management', []), 1):
        charter_text += f"{i}. {rule}\n"
    
    charter_text += f"""
🧠 감정 관리 원칙
"""
    for i, rule in enumerate(charter.get('emotional_rules', []), 1):
        charter_text += f"{i}. {rule}\n"
    
    charter_text += f"""
🎯 투자 판단 기준
"""
    for i, rule in enumerate(charter.get('decision_criteria', []), 1):
        charter_text += f"{i}. {rule}\n"
    
    charter_text += f"""
📚 학습 및 개선 목표
"""
    for i, goal in enumerate(charter.get('learning_goals', []), 1):
        charter_text += f"{i}. {goal}\n"
    
    charter_text += f"""

────────────────────────────────
이 헌장은 KB Reflex에서 생성되었습니다.
지속적인 학습과 개선을 통해 더 나은 투자자가 되어보세요.
"""
    
    st.download_button(
        label="📄 투자 헌장 다운로드",
        data=charter_text,
        file_name=f"{username}_투자헌장_v{charter['version']}.txt",
        mime="text/plain",
        use_container_width=True
    )

def show_principle_learning_section():
    """투자 원칙 학습 섹션"""
    st.markdown("---")
    st.markdown("### 📚 투자 대가들의 원칙 학습")
    
    principles = get_investment_principles()
    
    # 탭으로 각 대가별 원칙 표시
    tabs = st.tabs(list(principles.keys()))
    
    for i, (principle_name, principle_data) in enumerate(principles.items()):
        with tabs[i]:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f'''
                <div style="text-align: center; padding: 2rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">{principle_data['icon']}</div>
                    <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">{principle_name}</h3>
                    <p style="color: var(--text-secondary); font-size: 0.9rem;">
                        {principle_data['description']}
                    </p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"#### 💭 핵심 철학")
                st.info(f'"{principle_data["philosophy"]}"')
                
                st.markdown("#### 🎯 주요 원칙")
                for principle in principle_data["core_principles"]:
                    st.markdown(f"• {principle}")
                
                # 헌장에 적용 버튼
                if st.button(f"📜 {principle_name} 원칙을 내 헌장에 적용", key=f"apply_principle_{i}"):
                    apply_principle_to_charter(principle_name, principle_data)

def apply_principle_to_charter(principle_name, principle_data):
    """선택한 원칙을 헌장에 적용"""
    charter = st.session_state.investment_charter
    
    # 기존 헌장에 새로운 원칙 추가
    new_rules = principle_data["core_principles"][:3]  # 상위 3개 원칙만
    
    for rule in new_rules:
        # 중복 방지
        if rule not in charter.get('decision_criteria', []):
            charter['decision_criteria'].append(rule)
    
    # 철학도 업데이트 (기존 철학과 병합)
    if principle_data["philosophy"] not in charter['core_philosophy']:
        charter['core_philosophy'] += f" {principle_data['philosophy']}"
    
    # 버전 업데이트
    charter['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    charter['version'] += 1
    
    st.success(f"✅ {principle_name}의 원칙이 투자 헌장에 적용되었습니다!")
    st.rerun()

# 메인 로직
def main():
    initialize_user_charter()
    
    # 헌장 수정 모드
    if st.session_state.get('editing_charter', False):
        show_charter_editor()
        return
    
    # 메인 화면
    show_charter_overview()
    show_charter_content()
    show_charter_actions()
    show_principle_learning_section()

if __name__ == "__main__":
    main()