import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ui_components import apply_toss_css
from db.principles_db import get_investment_principles, get_principle_details

class InvestmentCharter:
    """투자 헌장 관리 클래스"""
    
    def __init__(self, username):
        self.username = username
        self.charter_key = f"investment_charter_{username}"
        self.initialize_charter()
    
    def initialize_charter(self):
        """투자 헌장 초기화"""
        if self.charter_key not in st.session_state:
            st.session_state[self.charter_key] = {
                'basic_rules': self.get_default_basic_rules(),
                'personal_rules': [],
                'selected_principle': st.session_state.get('selected_principle'),
                'created_date': datetime.now(),
                'last_updated': datetime.now()
            }
    
    def get_default_basic_rules(self):
        """기본 투자 원칙들"""
        return [
            {
                'title': '손실 한도 설정',
                'description': '총 투자금액의 10% 이상 손실 시 매도 검토',
                'category': '위험관리',
                'active': True
            },
            {
                'title': '감정적 거래 금지',
                'description': '공포, 욕심에 의한 급작스러운 매매 금지',
                'category': '심리관리',
                'active': True
            },
            {
                'title': '분산 투자',
                'description': '한 종목에 전체 자산의 20% 이상 집중 금지',
                'category': '포트폴리오관리',
                'active': True
            },
            {
                'title': '투자 일지 작성',
                'description': '모든 거래에 대해 이유와 감정 상태 기록',
                'category': '기록관리',
                'active': True
            }
        ]
    
    def add_personal_rule(self, title, description, category="개인원칙"):
        """개인 투자 원칙 추가"""
        new_rule = {
            'title': title,
            'description': description,
            'category': category,
            'active': True,
            'created_date': datetime.now(),
            'source': 'personal'
        }
        
        st.session_state[self.charter_key]['personal_rules'].append(new_rule)
        st.session_state[self.charter_key]['last_updated'] = datetime.now()
        
        return True
    
    def update_rule_status(self, rule_index, is_personal=False, active=True):
        """투자 원칙 활성화/비활성화"""
        if is_personal:
            if rule_index < len(st.session_state[self.charter_key]['personal_rules']):
                st.session_state[self.charter_key]['personal_rules'][rule_index]['active'] = active
        else:
            if rule_index < len(st.session_state[self.charter_key]['basic_rules']):
                st.session_state[self.charter_key]['basic_rules'][rule_index]['active'] = active
        
        st.session_state[self.charter_key]['last_updated'] = datetime.now()
    
    def get_all_active_rules(self):
        """모든 활성 투자 원칙 반환"""
        charter = st.session_state[self.charter_key]
        
        active_rules = []
        
        # 기본 원칙
        for rule in charter['basic_rules']:
            if rule['active']:
                active_rules.append(rule)
        
        # 개인 원칙
        for rule in charter['personal_rules']:
            if rule['active']:
                active_rules.append(rule)
        
        return active_rules
    
    def get_charter_summary(self):
        """투자 헌장 요약 정보"""
        charter = st.session_state[self.charter_key]
        
        total_rules = len(charter['basic_rules']) + len(charter['personal_rules'])
        active_rules = len(self.get_all_active_rules())
        
        return {
            'total_rules': total_rules,
            'active_rules': active_rules,
            'selected_principle': charter.get('selected_principle'),
            'created_date': charter['created_date'],
            'last_updated': charter['last_updated']
        }

def show_investment_charter_ui(username):
    """투자 헌장 UI 표시"""
    st.markdown(f'''
    <h1 class="main-header">📜 {username}님의 투자 헌장</h1>
    <p class="sub-header">나만의 투자 원칙을 세우고 지켜나가세요</p>
    ''', unsafe_allow_html=True)
    
    # 투자 헌장 객체 생성
    charter = InvestmentCharter(username)
    summary = charter.get_charter_summary()
    
    # 헌장 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 원칙 수", summary['total_rules'])
    
    with col2:
        st.metric("활성 원칙", summary['active_rules'])
    
    with col3:
        selected_principle = summary.get('selected_principle', '미설정')
        st.metric("선택한 투자 철학", selected_principle)
    
    with col4:
        st.metric("마지막 업데이트", summary['last_updated'].strftime('%m/%d'))
    
    # 탭으로 구성
    tab1, tab2, tab3 = st.tabs(["📋 현재 헌장", "➕ 원칙 추가", "📊 준수 현황"])
    
    with tab1:
        show_current_charter(charter, username)
    
    with tab2:
        show_add_rule_interface(charter)
    
    with tab3:
        show_compliance_status(charter, username)

def show_current_charter(charter, username):
    """현재 투자 헌장 표시"""
    st.markdown("### 📋 나의 투자 헌장")
    
    # 선택한 투자 철학 표시
    selected_principle = st.session_state.get('selected_principle')
    if selected_principle:
        principle_data = get_principle_details(selected_principle)
        if principle_data:
            st.markdown(f'''
            <div class="card" style="background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); border: 1px solid #3182F6;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="font-size: 2rem; margin-right: 1rem;">{principle_data['icon']}</span>
                    <div>
                        <h3 style="margin: 0; color: var(--primary-blue);">선택한 투자 철학: {selected_principle}</h3>
                        <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-style: italic;">
                            "{principle_data['philosophy']}"
                        </p>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("💡 투자 철학을 선택하면 더 체계적인 헌장을 구성할 수 있습니다.")
    
    # 기본 투자 원칙
    st.markdown("#### 🎯 기본 투자 원칙")
    
    charter_data = st.session_state[charter.charter_key]
    
    for i, rule in enumerate(charter_data['basic_rules']):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            status = "✅" if rule['active'] else "❌"
            st.markdown(f'''
            <div class="charter-rule">
                <div class="charter-rule-title">{status} {rule['title']}</div>
                <div class="charter-rule-description">{rule['description']}</div>
                <div style="margin-top: 0.5rem; color: var(--text-light); font-size: 12px;">
                    📂 {rule['category']}
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            current_status = rule['active']
            new_status = st.checkbox(
                "활성화", 
                value=current_status, 
                key=f"basic_rule_{i}",
                label_visibility="collapsed"
            )
            
            if new_status != current_status:
                charter.update_rule_status(i, is_personal=False, active=new_status)
                st.rerun()
    
    # 개인 투자 원칙
    if charter_data['personal_rules']:
        st.markdown("#### 💡 개인 투자 원칙")
        
        for i, rule in enumerate(charter_data['personal_rules']):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                status = "✅" if rule['active'] else "❌"
                st.markdown(f'''
                <div class="charter-rule" style="border-left-color: var(--success-color);">
                    <div class="charter-rule-title">{status} {rule['title']}</div>
                    <div class="charter-rule-description">{rule['description']}</div>
                    <div style="margin-top: 0.5rem; color: var(--text-light); font-size: 12px;">
                        📂 {rule['category']} | ⏰ {rule['created_date'].strftime('%Y-%m-%d')}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                current_status = rule['active']
                new_status = st.checkbox(
                    "활성화", 
                    value=current_status, 
                    key=f"personal_rule_{i}",
                    label_visibility="collapsed"
                )
                
                if new_status != current_status:
                    charter.update_rule_status(i, is_personal=True, active=new_status)
                    st.rerun()

def show_add_rule_interface(charter):
    """원칙 추가 인터페이스"""
    st.markdown("### ➕ 새로운 투자 원칙 추가")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✍️ 직접 작성")
        
        with st.form("add_personal_rule"):
            rule_title = st.text_input("원칙 제목", placeholder="예: 급등한 종목은 하루 더 관찰하기")
            
            rule_description = st.text_area(
                "상세 설명", 
                height=100,
                placeholder="예: 전일 5% 이상 급등한 종목은 당일 매수하지 않고 하루 더 지켜본 후 판단한다."
            )
            
            rule_category = st.selectbox(
                "카테고리",
                ["위험관리", "심리관리", "포트폴리오관리", "타이밍", "정보수집", "기타"]
            )
            
            if st.form_submit_button("원칙 추가", type="primary"):
                if rule_title.strip() and rule_description.strip():
                    success = charter.add_personal_rule(rule_title, rule_description, rule_category)
                    if success:
                        st.success("✅ 새로운 투자 원칙이 추가되었습니다!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("제목과 설명을 모두 입력해주세요.")
    
    with col2:
        st.markdown("#### 🎯 추천 원칙 템플릿")
        
        # 선택한 투자 철학에 따른 추천 원칙
        selected_principle = st.session_state.get('selected_principle')
        
        if selected_principle:
            principle_rules = get_recommended_rules_by_principle(selected_principle)
            
            st.markdown(f"**{selected_principle} 스타일 추천 원칙:**")
            
            for rule in principle_rules:
                st.markdown(f'''
                <div style="background-color: #F8FAFC; border-radius: 8px; padding: 12px; margin: 8px 0;">
                    <div style="font-weight: 600; margin-bottom: 4px;">{rule['title']}</div>
                    <div style="font-size: 13px; color: var(--text-secondary);">{rule['description']}</div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"이 원칙 추가", key=f"add_template_{rule['title']}", type="secondary"):
                    charter.add_personal_rule(rule['title'], rule['description'], "투자철학")
                    st.success(f"✅ '{rule['title']}' 원칙이 추가되었습니다!")
                    st.rerun()
        else:
            st.info("💡 먼저 투자 철학을 선택하면 맞춤형 원칙을 추천받을 수 있습니다.")
            
            if st.button("🎯 투자 철학 선택하러 가기"):
                st.switch_page("main_app.py")

def show_compliance_status(charter, username):
    """헌장 준수 현황"""
    st.markdown("### 📊 투자 헌장 준수 현황")
    
    # 최근 거래 데이터 불러오기
    try:
        from db.user_db import UserDatabase
        user_db = UserDatabase()
        trades_data = user_db.get_user_trades(username)
        
        if trades_data is not None and len(trades_data) > 0:
            # 최근 10개 거래 분석
            recent_trades = trades_data.tail(10)
            
            compliance_scores = []
            
            for _, trade in recent_trades.iterrows():
                score = analyze_trade_compliance(trade, charter)
                compliance_scores.append({
                    'date': trade['거래일시'].strftime('%m/%d'),
                    'stock': trade['종목명'],
                    'emotion': trade['감정태그'],
                    'return': trade['수익률'],
                    'score': score
                })
            
            # 평균 준수율
            avg_compliance = sum([s['score'] for s in compliance_scores]) / len(compliance_scores)
            
            st.metric("평균 헌장 준수율", f"{avg_compliance:.0f}%")
            
            # 최근 거래별 준수 현황
            st.markdown("#### 📈 최근 거래별 준수 현황")
            
            for trade_info in compliance_scores:
                color = "success" if trade_info['score'] >= 80 else "warning" if trade_info['score'] >= 60 else "error"
                color_value = "#16A34A" if color == "success" else "#F59E0B" if color == "warning" else "#DC2626"
                
                st.markdown(f'''
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; margin: 8px 0; background-color: var(--card-bg); border-radius: 8px; border-left: 4px solid {color_value};">
                    <div>
                        <div style="font-weight: 600;">{trade_info['date']} - {trade_info['stock']}</div>
                        <div style="font-size: 13px; color: var(--text-secondary);">
                            {trade_info['emotion']} | 수익률: {trade_info['return']:+.1f}%
                        </div>
                    </div>
                    <div style="font-weight: 700; color: {color_value};">
                        {trade_info['score']}%
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 개선 제안
            st.markdown("#### 💡 개선 제안")
            
            if avg_compliance < 70:
                st.warning("⚠️ 투자 헌장 준수율이 낮습니다. 감정적 거래를 줄이고 원칙을 지키려 노력하세요.")
            elif avg_compliance < 85:
                st.info("📈 꽤 좋은 준수율입니다. 조금 더 신경쓰면 더 나은 결과를 얻을 수 있어요.")
            else:
                st.success("✅ 훌륭한 헌장 준수율입니다! 현재의 원칙적 투자를 계속 유지하세요.")
        
        else:
            st.info("📊 거래 데이터가 없어서 준수 현황을 분석할 수 없습니다.")
            
    except Exception as e:
        st.error(f"❌ 데이터 분석 중 오류가 발생했습니다: {str(e)}")

def get_recommended_rules_by_principle(principle_name):
    """투자 철학별 추천 원칙"""
    rules = {
        "워런 버핏": [
            {
                'title': '완전히 이해할 수 있는 기업에만 투자',
                'description': '사업모델을 명확히 이해하지 못하는 기업은 투자 대상에서 제외'
            },
            {
                'title': '최소 5년 이상 보유 관점으로 투자',
                'description': '단기적 가격 변동에 흔들리지 않고 장기 가치 창조에 집중'
            },
            {
                'title': '경영진의 정직성과 능력 평가',
                'description': '투자 전 기업 경영진의 과거 실적과 투명성을 반드시 검토'
            }
        ],
        "피터 린치": [
            {
                'title': '일상에서 경험한 기업 우선 검토',
                'description': '직접 사용해본 제품이나 서비스의 기업을 투자 후보로 우선 고려'
            },
            {
                'title': 'PEG 비율 1.0 이하 종목 선별',
                'description': '성장률 대비 주가가 저평가된 종목에 집중 투자'
            },
            {
                'title': '분기별 실적 모니터링 의무화',
                'description': '보유 종목의 분기 실적을 반드시 확인하고 투자 논리 재검토'
            }
        ],
        "벤저민 그레이엄": [
            {
                'title': '30% 이상 안전 마진 확보 후 매수',
                'description': '계산된 내재가치 대비 최소 30% 할인된 가격에서만 매수'
            },
            {
                'title': '재무제표 기반 정량적 분석 우선',
                'description': '감정이나 추측보다는 재무 데이터를 바탕으로 투자 결정'
            },
            {
                'title': '포트폴리오 분산을 통한 위험 관리',
                'description': '개별 종목 위험을 줄이기 위해 최소 10개 이상 종목에 분산 투자'
            }
        ]
    }
    
    return rules.get(principle_name, [])

def analyze_trade_compliance(trade, charter):
    """개별 거래의 헌장 준수도 분석"""
    score = 100
    memo = trade['메모'].lower()
    emotion = trade['감정태그']
    
    # 감정적 거래 패널티
    if emotion in ['#공포', '#패닉', '#욕심', '#추격매수']:
        score -= 20
    
    # 급한 판단 패널티
    if any(word in memo for word in ['급히', '서둘러', '패닉', '무서워서']):
        score -= 15
    
    # 타인 의존 패널티
    if any(word in memo for word in ['추천받고', '유튜버', '친구가', '커뮤니티']):
        score -= 10
    
    # 과도한 확신 패널티
    if any(word in memo for word in ['확실', '100%', '대박', '올인']):
        score -= 25
    
    # 합리적 분석 보너스
    if any(word in memo for word in ['분석', '펀더멘털', '기술적', '밸류에이션']):
        score += 10
    
    return max(0, min(100, score))

# 페이지에서 직접 호출할 때 사용하는 함수들
def show_charter_compliance_check(username: str, memo: str) -> dict:
    """
    투자 헌장 준수 체크 (외부에서 호출용)
    """
    compliance_issues = []
    warnings = []
    recommendation = ""
    
    # 선택된 투자 원칙 확인
    selected_principle = st.session_state.get('selected_principle')
    
    if not selected_principle:
        return {
            'compliance_issues': [],
            'warnings': ["💡 투자 원칙을 설정하면 더 정확한 검증을 받을 수 있습니다."],
            'recommendation': "투자 헌장 페이지에서 투자 원칙을 선택해보세요."
        }
    
    memo_lower = memo.lower()
    
    # 공통 위험 패턴 체크
    if any(word in memo_lower for word in ['급히', '서둘러', '패닉', '무서워서']):
        compliance_issues.append("⚠️ 감정적 급한 판단으로 보입니다.")
    
    if any(word in memo_lower for word in ['추천받고', '유튜버', '친구가', '커뮤니티']):
        warnings.append("🤔 타인의 추천에 의존한 투자는 위험할 수 있습니다.")
    
    if any(word in memo_lower for word in ['확실', '100%', '대박', '올인']):
        compliance_issues.append("🚨 과도한 확신이나 올인 투자는 위험합니다.")
    
    # 원칙별 특별 체크
    if selected_principle == "워런 버핏":
        if not any(word in memo_lower for word in ['분석', '펀더멘털', '기업', '가치']):
            warnings.append("🎯 워런 버핏의 원칙: 철저한 기업 분석을 했나요?")
        
        if any(word in memo_lower for word in ['단기', '빨리']):
            compliance_issues.append("⏰ 워런 버핏 원칙 위배: 장기 투자 관점을 유지하세요.")
        
        recommendation = "기업의 내재가치를 분석하고 장기적 관점에서 투자하세요."
    
    elif selected_principle == "피터 린치":
        if not any(word in memo_lower for word in ['성장', '실적', '매출', '실생활']):
            warnings.append("🔍 피터 린치의 원칙: 성장 스토리를 파악했나요?")
        
        recommendation = "일상에서 경험한 기업의 성장 가능성을 분석해보세요."
    
    elif selected_principle == "벤저민 그레이엄":
        if not any(word in memo_lower for word in ['밸류에이션', '저평가', '안전마진', '재무제표']):
            warnings.append("⚖️ 벤저민 그레이엄의 원칙: 안전 마진을 확보했나요?")
        
        recommendation = "내재가치 대비 충분한 할인가에서 매수했는지 확인하세요."
    
    if not compliance_issues and not warnings:
        recommendation = "✅ 투자 원칙에 잘 부합하는 거래입니다!"
    
    return {
        'compliance_issues': compliance_issues,
        'warnings': warnings,
        'recommendation': recommendation
    }