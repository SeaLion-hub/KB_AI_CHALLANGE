import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

def apply_toss_css():
    """Toss 스타일의 CSS 적용"""
    st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        :root {
            --bg-color: #F2F4F6;
            --sidebar-bg: #FFFFFF;
            --card-bg: #FFFFFF;
            --primary-blue: #3182F6;
            --text-primary: #191919;
            --text-secondary: #505967;
            --text-light: #8B95A1;
            --border-color: #E5E8EB;
            --positive-color: #D91A2A;
            --negative-color: #1262D7;
            --success-color: #14AE5C;
            --warning-color: #FF9500;
        }

        * {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }

        .stApp {
            background-color: var(--bg-color);
        }

        .css-1d391kg {
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        .metric-card {
            background-color: var(--card-bg);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
            text-align: center;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .metric-label {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-light);
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .metric-value.positive {
            color: var(--positive-color);
        }

        .metric-value.negative {
            color: var(--negative-color);
        }

        .card {
            background-color: var(--card-bg);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
        }

        .card-title {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 16px;
        }

        .stButton > button {
            background-color: var(--primary-blue);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            height: 48px;
            font-size: 15px;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background-color: #2563EB;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(49, 130, 246, 0.3);
        }

        .buy-button {
            background-color: var(--positive-color) !important;
        }

        .sell-button {
            background-color: var(--negative-color) !important;
        }

        .stSelectbox > div > div {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            height: 48px;
        }

        .stTextInput > div > div > input {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            height: 48px;
            font-size: 15px;
        }

        .stNumberInput > div > div > input {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            height: 48px;
            font-size: 15px;
        }

        .stTextArea > div > div > textarea {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            font-size: 15px;
        }

        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        .main-header {
            font-size: 28px;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .sub-header {
            font-size: 16px;
            color: var(--text-secondary);
            margin-bottom: 32px;
        }

        .ai-coaching-card {
            background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%);
            border: 1px solid #BFDBFE;
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
        }

        .ai-coaching-title {
            font-size: 18px;
            font-weight: 700;
            color: var(--primary-blue);
            margin-bottom: 12px;
        }

        .ai-coaching-content {
            font-size: 15px;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        .trade-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            border-bottom: 1px solid var(--border-color);
        }

        .trade-item:last-child {
            border-bottom: none;
        }

        .trade-info {
            display: flex;
            flex-direction: column;
        }

        .trade-stock-name {
            font-weight: 700;
            color: var(--text-primary);
            font-size: 16px;
        }

        .trade-details {
            font-size: 13px;
            color: var(--text-light);
            margin-top: 4px;
        }

        .trade-amount {
            font-weight: 700;
            font-size: 16px;
        }

        .trade-amount.buy {
            color: var(--positive-color);
        }

        .trade-amount.sell {
            color: var(--negative-color);
        }

        .live-indicator {
            display: inline-flex;
            align-items: center;
            font-size: 14px;
            color: var(--success-color);
            font-weight: 600;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success-color);
            border-radius: 50%;
            margin-right: 6px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .emotion-tag {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
        }

        .emotion-fear, .emotion-공포, .emotion-패닉, .emotion-불안 {
            background-color: #FEF2F2;
            color: #DC2626;
        }

        .emotion-fomo, .emotion-추격매수, .emotion-욕심 {
            background-color: #FFF7ED;
            color: #EA580C;
        }

        .emotion-rational, .emotion-합리적, .emotion-확신 {
            background-color: #F0FDF4;
            color: #16A34A;
        }

        .charter-rule {
            background-color: #F8FAFC;
            border-left: 4px solid var(--primary-blue);
            padding: 16px;
            margin: 12px 0;
            border-radius: 0 8px 8px 0;
        }

        .charter-rule-title {
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .charter-rule-description {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        .price-update {
            animation: price-pulse 1s ease-in-out;
        }

        @keyframes price-pulse {
            0% { background-color: rgba(49, 130, 246, 0.1); }
            50% { background-color: rgba(49, 130, 246, 0.3); }
            100% { background-color: rgba(49, 130, 246, 0.1); }
        }

        .loss-alert {
            background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
            border: 2px solid #F87171;
            border-radius: 16px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }

        .loss-alert-title {
            font-size: 18px;
            font-weight: 700;
            color: #DC2626;
            margin-bottom: 12px;
        }

        .loss-alert-content {
            font-size: 14px;
            color: #7F1D1D;
            margin-bottom: 16px;
        }

        /* 탭 스타일 개선 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: var(--card-bg);
            border-radius: 10px;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }

        .stTabs [aria-selected="true"] {
            background-color: var(--primary-blue);
            color: white;
            border-color: var(--primary-blue);
        }

        /* 슬라이더 스타일 개선 */
        .stSlider > div > div > div > div {
            background-color: var(--primary-blue);
        }

        /* 체크박스 스타일 개선 */
        .stCheckbox > label > div:first-child {
            background-color: var(--card-bg);
            border-color: var(--border-color);
        }

        .stCheckbox > label > div[data-checked="true"] > div:first-child {
            background-color: var(--primary-blue);
            border-color: var(--primary-blue);
        }

        /* 멀티셀렉트 스타일 개선 */
        .stMultiSelect > div > div {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

def create_metric_card(label, value, color_class=""):
    """메트릭 카드 생성"""
    color_class_html = f" {color_class}" if color_class else ""
    
    st.markdown(f'''
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value{color_class_html}">{value}</div>
    </div>
    ''', unsafe_allow_html=True)

def create_live_chart(chart_data, cash, portfolio, market_data):
    """실시간 차트 생성"""
    # 새로운 데이터 포인트 추가
    current_time = datetime.now()
    portfolio_value = cash + sum([
        holdings['shares'] * market_data.get(stock, {'price': 50000})['price']
        for stock, holdings in portfolio.items()
    ])
    
    # 약간의 랜덤 변동 추가
    portfolio_value += np.random.normal(0, 50000)
    
    chart_data['time'].append(current_time)
    chart_data['value'].append(portfolio_value)
    
    # 최근 30개 데이터만 유지
    if len(chart_data['time']) > 30:
        chart_data['time'] = chart_data['time'][-30:]
        chart_data['value'] = chart_data['value'][-30:]
    
    # 차트 생성
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=chart_data['time'],
        y=chart_data['value'],
        mode='lines',
        name='포트폴리오 가치',
        line=dict(color='#3182F6', width=3),
        fill='tonexty',
        fillcolor='rgba(49, 130, 246, 0.1)'
    ))
    
    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="자산 가치 (원)",
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Pretendard", color="#191919"),
        margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(
            tickformat=',.0f',
            gridcolor='rgba(229, 232, 235, 0.5)'
        ),
        xaxis=dict(
            gridcolor='rgba(229, 232, 235, 0.5)'
        )
    )
    
    return fig

def create_emotion_chart(emotion_data):
    """감정별 성과 차트 생성"""
    if emotion_data.empty:
        return None
    
    fig = go.Figure(data=[
        go.Bar(
            x=emotion_data['mean'],
            y=emotion_data['감정태그'],
            orientation='h',
            marker=dict(
                color=emotion_data['mean'],
                colorscale=['red', 'yellow', 'green'],
                showscale=False
            )
        )
    ])
    
    fig.update_layout(
        title="감정별 평균 수익률",
        xaxis_title="평균 수익률 (%)",
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Pretendard", color="#191919"),
        showlegend=False
    )
    
    return fig

def create_trend_chart(monthly_data):
    """월별 트렌드 차트 생성"""
    if monthly_data.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_data.index.astype(str),
        y=monthly_data['수익률']['sum'],
        mode='lines+markers',
        name='월별 누적 수익률',
        line=dict(color='#3182F6', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="월별 수익률 트렌드",
        xaxis_title="월",
        yaxis_title="누적 수익률 (%)",
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Pretendard", color="#191919"),
        showlegend=False
    )
    
    return fig

def show_loading_spinner(message="처리 중..."):
    """로딩 스피너 표시"""
    with st.spinner(message):
        import time
        time.sleep(1)

def show_success_message(message, show_balloons=True):
    """성공 메시지 표시"""
    st.success(message)
    if show_balloons:
        st.balloons()

def show_info_card(title, content, icon="💡"):
    """정보 카드 표시"""
    st.markdown(f'''
    <div class="card" style="background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); border: 1px solid #7DD3FC;">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h4 style="margin: 0; color: var(--primary-blue);">{title}</h4>
        </div>
        <div style="color: var(--text-secondary); line-height: 1.6;">
            {content}
        </div>
    </div>
    ''', unsafe_allow_html=True)

def show_warning_card(title, content, icon="⚠️"):
    """경고 카드 표시"""
    st.markdown(f'''
    <div class="card" style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); border: 1px solid #F59E0B;">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h4 style="margin: 0; color: var(--warning-color);">{title}</h4>
        </div>
        <div style="color: var(--text-secondary); line-height: 1.6;">
            {content}
        </div>
    </div>
    ''', unsafe_allow_html=True)

def show_error_card(title, content, icon="❌"):
    """오류 카드 표시"""
    st.markdown(f'''
    <div class="card" style="background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%); border: 1px solid #F87171;">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h4 style="margin: 0; color: #DC2626;">{title}</h4>
        </div>
        <div style="color: var(--text-secondary); line-height: 1.6;">
            {content}
        </div>
    </div>
    ''', unsafe_allow_html=True)

def create_progress_bar(current, total, label="진행률"):
    """진행률 바 생성"""
    progress = current / total if total > 0 else 0
    
    st.markdown(f'''
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-weight: 600;">{label}</span>
            <span style="color: var(--text-secondary);">{current}/{total}</span>
        </div>
        <div style="width: 100%; background-color: var(--border-color); border-radius: 10px; height: 8px; overflow: hidden;">
            <div style="width: {progress*100}%; background-color: var(--primary-blue); height: 100%; transition: width 0.3s ease;"></div>
        </div>
        <div style="text-align: center; margin-top: 0.5rem; color: var(--text-secondary); font-size: 0.9rem;">
            {progress*100:.1f}% 완료
        </div>
    </div>
    ''', unsafe_allow_html=True)

def create_stat_comparison(stats_dict, title="통계 비교"):
    """통계 비교 카드 생성"""
    st.markdown(f'''
    <div class="card">
        <h4 style="margin-bottom: 1rem; color: var(--text-primary);">{title}</h4>
    ''', unsafe_allow_html=True)
    
    for key, value in stats_dict.items():
        if isinstance(value, (int, float)):
            if value > 0:
                color = "var(--success-color)"
                icon = "📈"
            elif value < 0:
                color = "#DC2626"
                icon = "📉"
            else:
                color = "var(--text-secondary)"
                icon = "➖"
            
            st.markdown(f'''
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                <span style="color: var(--text-secondary);">{key}</span>
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 0.5rem;">{icon}</span>
                    <span style="color: {color}; font-weight: 600;">{value}</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                <span style="color: var(--text-secondary);">{key}</span>
                <span style="color: var(--text-primary); font-weight: 600;">{value}</span>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_timeline_item(date, title, description, status="completed"):
    """타임라인 아이템 생성"""
    if status == "completed":
        icon = "✅"
        color = "var(--success-color)"
    elif status == "in_progress":
        icon = "🔄" 
        color = "var(--warning-color)"
    else:  # pending
        icon = "⏳"
        color = "var(--text-light)"
    
    st.markdown(f'''
    <div style="display: flex; margin-bottom: 1rem; padding: 1rem; background-color: var(--card-bg); border-radius: 12px; border-left: 4px solid {color};">
        <div style="margin-right: 1rem; font-size: 1.5rem;">{icon}</div>
        <div style="flex: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <h4 style="margin: 0; color: var(--text-primary);">{title}</h4>
                <span style="color: var(--text-light); font-size: 0.9rem;">{date}</span>
            </div>
            <p style="margin: 0; color: var(--text-secondary); line-height: 1.5;">{description}</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def create_feature_highlight(features_list, title="주요 기능"):
    """기능 하이라이트 카드 생성"""
    st.markdown(f'''
    <div class="card" style="background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);">
        <h4 style="margin-bottom: 1rem; color: var(--text-primary);">{title}</h4>
    ''', unsafe_allow_html=True)
    
    for feature in features_list:
        st.markdown(f'''
        <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
            <div style="width: 8px; height: 8px; background-color: var(--primary-blue); border-radius: 50%; margin-right: 1rem;"></div>
            <span style="color: var(--text-secondary);">{feature}</span>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_quote_card(quote, author, context=""):
    """명언 카드 생성"""
    st.markdown(f'''
    <div class="card" style="background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); border: 1px solid #FDBA74; text-align: center;">
        <div style="font-size: 2rem; color: var(--warning-color); margin-bottom: 1rem;">💭</div>
        <blockquote style="font-style: italic; font-size: 1.1rem; color: var(--text-primary); margin-bottom: 1rem; line-height: 1.6;">
            "{quote}"
        </blockquote>
        <div style="color: var(--text-secondary); font-weight: 600;">- {author}</div>
        {f'<div style="color: var(--text-light); font-size: 0.9rem; margin-top: 0.5rem;">{context}</div>' if context else ''}
    </div>
    ''', unsafe_allow_html=True)