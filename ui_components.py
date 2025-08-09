"""
UI 컴포넌트 모듈 - 고도화 버전 (V2.0)
안정적이고 아름다운 UI 컴포넌트들을 제공하는 모듈

개선사항:
- HTML 렌더링 안정성 개선
- CSS 스타일 충돌 방지
- 타입 힌트 정확성 향상
- 반응형 디자인 강화
- 접근성 개선
- 성능 최적화
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import streamlit.components.v1 as components
import html
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# [SAFE HTML RENDERING] 안전한 HTML 렌더링
# ================================

def render_html(html_string: str, height: Optional[int] = None, scrolling: bool = False, key: Optional[str] = None):
    """
    안전한 HTML 렌더링 유틸리티 (고도화 버전)
    
    Args:
        html_string: 렌더링할 HTML 문자열
        height: 컴포넌트 높이 (px)
        scrolling: 스크롤 허용 여부
        key: 고유 키 (중복 방지)
    """
    try:
        # HTML 문자열 검증 및 정제
        if not html_string or not isinstance(html_string, str):
            logger.warning("유효하지 않은 HTML 문자열")
            return
        
        # 안전성 검사 - 잠재적 위험 태그 제거
        dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<link']
        for tag in dangerous_tags:
            if tag in html_string.lower():
                logger.warning(f"위험한 태그 감지: {tag}")
                html_string = html_string.replace(tag, f'&lt;{tag[1:]}')
        
        # 복잡한 레이아웃인지 판단
        complex_indicators = [
            '<div' in html_string,
            '<section' in html_string,
            '<article' in html_string,
            'style=' in html_string and len(html_string) > 500,
            'class=' in html_string and len(html_string) > 500
        ]
        
        is_complex = any(complex_indicators) or height is not None
        
        if is_complex:
            # 복잡한 HTML은 components.html로 렌더링
            components.html(
                html_string, 
                height=height or 400, 
                scrolling=scrolling,
                key=key
            )
        else:
            # 간단한 HTML은 markdown으로 렌더링
            st.markdown(html_string, unsafe_allow_html=True)
            
    except Exception as e:
        logger.error(f"HTML 렌더링 오류: {str(e)}")
        st.error("컴포넌트 렌더링 중 오류가 발생했습니다.")

def escape_html(text: str) -> str:
    """HTML 이스케이프 처리"""
    if not isinstance(text, str):
        text = str(text)
    return html.escape(text)

# ================================
# [ENHANCED CSS] 향상된 CSS 시스템
# ================================

def apply_toss_css():
    """Toss 스타일의 CSS 적용 (고도화 버전)"""
    css = """
    <style>
        /* 폰트 및 기본 스타일 */
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        :root {
            /* 컬러 시스템 */
            --bg-color: #F2F4F6;
            --sidebar-bg: #FFFFFF;
            --card-bg: #FFFFFF;
            --primary-blue: #3182F6;
            --primary-blue-hover: #2563EB;
            --text-primary: #191919;
            --text-secondary: #505967;
            --text-light: #8B95A1;
            --border-color: #E5E8EB;
            --positive-color: #D91A2A;
            --negative-color: #1262D7;
            --success-color: #14AE5C;
            --warning-color: #FF9500;
            --error-color: #DC2626;
            
            /* 간격 시스템 */
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            
            /* 그림자 시스템 */
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.05);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.1);
            
            /* 애니메이션 */
            --transition-fast: 0.15s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
        }

        /* 전역 스타일 */
        * {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            box-sizing: border-box;
        }

        /* Streamlit 기본 스타일 오버라이드 */
        .stApp {
            background-color: var(--bg-color);
        }

        .css-1d391kg, .stSidebar > div {
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
        }

        .main .block-container {
            padding-top: var(--spacing-lg);
            padding-bottom: var(--spacing-lg);
            max-width: 1200px;
        }

        /* 카드 컴포넌트 */
        .ui-card {
            background-color: var(--card-bg);
            border-radius: 20px;
            padding: var(--spacing-lg);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            margin-bottom: var(--spacing-lg);
            transition: var(--transition-normal);
        }

        .ui-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .ui-card-title {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: var(--spacing-md);
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
        }

        /* 메트릭 카드 */
        .ui-metric-card {
            background-color: var(--card-bg);
            border-radius: 16px;
            padding: var(--spacing-lg);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            text-align: center;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: var(--transition-normal);
        }

        .ui-metric-card:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }

        .ui-metric-label {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-light);
            margin-bottom: var(--spacing-sm);
        }

        .ui-metric-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.2;
        }

        .ui-metric-value.positive {
            color: var(--positive-color);
        }

        .ui-metric-value.negative {
            color: var(--negative-color);
        }

        .ui-metric-subtitle {
            font-size: 12px;
            color: var(--text-light);
            margin-top: var(--spacing-xs);
        }

        /* 버튼 스타일 */
        .stButton > button {
            background-color: var(--primary-blue) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            height: 48px !important;
            font-size: 15px !important;
            transition: var(--transition-fast) !important;
            width: 100% !important;
        }

        .stButton > button:hover {
            background-color: var(--primary-blue-hover) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(49, 130, 246, 0.3) !important;
        }

        /* 인풋 스타일 */
        .stSelectbox > div > div,
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 10px !important;
            font-size: 15px !important;
            transition: var(--transition-fast) !important;
        }

        .stSelectbox > div > div:focus-within,
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--primary-blue) !important;
            box-shadow: 0 0 0 3px rgba(49, 130, 246, 0.1) !important;
        }

        /* 헤더 스타일 */
        .ui-main-header {
            font-size: 28px;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: var(--spacing-sm);
        }

        .ui-sub-header {
            font-size: 16px;
            color: var(--text-secondary);
            margin-bottom: var(--spacing-xl);
        }

        /* AI 코칭 카드 */
        .ui-ai-card {
            background: linear-gradient(135deg, #EBF4FF 0%, #E0F2FE 100%);
            border: 1px solid #BFDBFE;
            border-radius: 20px;
            padding: var(--spacing-lg);
            margin-bottom: var(--spacing-lg);
        }

        .ui-ai-title {
            font-size: 18px;
            font-weight: 700;
            color: var(--primary-blue);
            margin-bottom: var(--spacing-md);
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
        }

        /* 알림 카드들 */
        .ui-info-card {
            background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
            border: 1px solid #7DD3FC;
            border-radius: 16px;
            padding: var(--spacing-lg);
            margin: var(--spacing-md) 0;
        }

        .ui-warning-card {
            background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
            border: 1px solid #F59E0B;
            border-radius: 16px;
            padding: var(--spacing-lg);
            margin: var(--spacing-md) 0;
        }

        .ui-error-card {
            background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
            border: 1px solid #F87171;
            border-radius: 16px;
            padding: var(--spacing-lg);
            margin: var(--spacing-md) 0;
        }

        .ui-success-card {
            background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
            border: 1px solid #86EFAC;
            border-radius: 16px;
            padding: var(--spacing-lg);
            margin: var(--spacing-md) 0;
        }

        /* 거래 아이템 */
        .ui-trade-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: var(--spacing-md) 0;
            border-bottom: 1px solid var(--border-color);
            transition: var(--transition-fast);
        }

        .ui-trade-item:hover {
            background-color: rgba(49, 130, 246, 0.05);
            margin: 0 calc(-1 * var(--spacing-md));
            padding-left: var(--spacing-md);
            padding-right: var(--spacing-md);
            border-radius: 8px;
        }

        .ui-trade-item:last-child {
            border-bottom: none;
        }

        /* 감정 태그 */
        .ui-emotion-tag {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-right: var(--spacing-sm);
        }

        .ui-emotion-fear { background: #FEF2F2; color: #DC2626; }
        .ui-emotion-greed { background: #FFF7ED; color: #EA580C; }
        .ui-emotion-rational { background: #F0FDF4; color: #16A34A; }
        .ui-emotion-default { background: #F8FAFC; color: #64748B; }

        /* 프로그레스 바 */
        .ui-progress-container {
            width: 100%;
            background-color: var(--border-color);
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin: var(--spacing-sm) 0;
        }

        .ui-progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--primary-blue), var(--success-color));
            transition: width var(--transition-normal);
        }

        /* 라이브 인디케이터 */
        .ui-live-indicator {
            display: inline-flex;
            align-items: center;
            font-size: 14px;
            color: var(--success-color);
            font-weight: 600;
        }

        .ui-live-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success-color);
            border-radius: 50%;
            margin-right: 6px;
            animation: ui-pulse 2s infinite;
        }

        @keyframes ui-pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* 반응형 디자인 */
        @media (max-width: 768px) {
            .main .block-container {
                padding: var(--spacing-md);
            }
            
            .ui-card {
                padding: var(--spacing-md);
                border-radius: 16px;
            }
            
            .ui-metric-card {
                height: 120px;
                padding: var(--spacing-md);
            }
            
            .ui-metric-value {
                font-size: 24px;
            }
        }

        /* 다크모드 지원 준비 */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #0F172A;
                --card-bg: #1E293B;
                --text-primary: #F8FAFC;
                --text-secondary: #CBD5E1;
                --border-color: #334155;
            }
        }

        /* 접근성 개선 */
        .ui-card:focus-within,
        .ui-metric-card:focus-within {
            outline: 2px solid var(--primary-blue);
            outline-offset: 2px;
        }

        /* 애니메이션 감소 요청 시 */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
    </style>
    """
    try:
        st.markdown(css, unsafe_allow_html=True)
        logger.debug("CSS 스타일 적용 완료")
    except Exception as e:
        logger.error(f"CSS 적용 오류: {str(e)}")

# ================================
# [SAFE COMPONENT CREATION] 안전한 컴포넌트 생성
# ================================

def create_metric_card(
    label: str, 
    value: Union[str, int, float], 
    color_class: str = "",
    subtitle: str = "",
    icon: str = ""
) -> None:
    """
    안전한 메트릭 카드 생성
    
    Args:
        label: 라벨 텍스트
        value: 메트릭 값
        color_class: 색상 클래스 (positive, negative)
        subtitle: 부제목
        icon: 아이콘 (이모지)
    """
    try:
        # 입력값 검증 및 이스케이프
        safe_label = escape_html(str(label))
        safe_value = escape_html(str(value))
        safe_subtitle = escape_html(str(subtitle))
        safe_icon = escape_html(str(icon))
        
        # 색상 클래스 검증
        allowed_classes = ['positive', 'negative', '']
        color_class = color_class if color_class in allowed_classes else ''
        
        # 아이콘 HTML
        icon_html = f'<span style="margin-right: 8px; font-size: 1.2em;">{safe_icon}</span>' if icon else ''
        
        # 부제목 HTML
        subtitle_html = f'<div class="ui-metric-subtitle">{safe_subtitle}</div>' if subtitle else ''
        
        html = f'''
        <div class="ui-metric-card">
            <div class="ui-metric-label">{icon_html}{safe_label}</div>
            <div class="ui-metric-value {color_class}">{safe_value}</div>
            {subtitle_html}
        </div>
        '''
        
        render_html(html)
        
    except Exception as e:
        logger.error(f"메트릭 카드 생성 오류: {str(e)}")
        st.error("메트릭 카드를 생성할 수 없습니다.")

def show_info_card(title: str, content: str, icon: str = "💡") -> None:
    """안전한 정보 카드 표시"""
    try:
        safe_title = escape_html(str(title))
        safe_content = escape_html(str(content)).replace('\n', '<br>')
        safe_icon = escape_html(str(icon))
        
        html = f'''
        <div class="ui-info-card">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{safe_icon}</span>
                <h4 style="margin: 0; color: var(--primary-blue);">{safe_title}</h4>
            </div>
            <div style="color: var(--text-secondary); line-height: 1.6;">
                {safe_content}
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"정보 카드 생성 오류: {str(e)}")
        st.info(f"{title}: {content}")

def show_warning_card(title: str, content: str, icon: str = "⚠️") -> None:
    """안전한 경고 카드 표시"""
    try:
        safe_title = escape_html(str(title))
        safe_content = escape_html(str(content)).replace('\n', '<br>')
        safe_icon = escape_html(str(icon))
        
        html = f'''
        <div class="ui-warning-card">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{safe_icon}</span>
                <h4 style="margin: 0; color: var(--warning-color);">{safe_title}</h4>
            </div>
            <div style="color: var(--text-secondary); line-height: 1.6;">
                {safe_content}
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"경고 카드 생성 오류: {str(e)}")
        st.warning(f"{title}: {content}")

def show_error_card(title: str, content: str, icon: str = "❌") -> None:
    """안전한 오류 카드 표시"""
    try:
        safe_title = escape_html(str(title))
        safe_content = escape_html(str(content)).replace('\n', '<br>')
        safe_icon = escape_html(str(icon))
        
        html = f'''
        <div class="ui-error-card">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{safe_icon}</span>
                <h4 style="margin: 0; color: var(--error-color);">{safe_title}</h4>
            </div>
            <div style="color: var(--text-secondary); line-height: 1.6;">
                {safe_content}
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"오류 카드 생성 오류: {str(e)}")
        st.error(f"{title}: {content}")

def show_success_card(title: str, content: str, icon: str = "✅") -> None:
    """안전한 성공 카드 표시"""
    try:
        safe_title = escape_html(str(title))
        safe_content = escape_html(str(content)).replace('\n', '<br>')
        safe_icon = escape_html(str(icon))
        
        html = f'''
        <div class="ui-success-card">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{safe_icon}</span>
                <h4 style="margin: 0; color: var(--success-color);">{safe_title}</h4>
            </div>
            <div style="color: var(--text-secondary); line-height: 1.6;">
                {safe_content}
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"성공 카드 생성 오류: {str(e)}")
        st.success(f"{title}: {content}")

# ================================
# [ENHANCED CHARTS] 향상된 차트 컴포넌트
# ================================

def create_safe_chart(chart_type: str, data: Any, **kwargs) -> Optional[go.Figure]:
    """안전한 차트 생성 래퍼"""
    try:
        if chart_type == "line":
            return create_line_chart(data, **kwargs)
        elif chart_type == "bar":
            return create_bar_chart(data, **kwargs)
        elif chart_type == "pie":
            return create_pie_chart(data, **kwargs)
        else:
            logger.warning(f"지원하지 않는 차트 타입: {chart_type}")
            return None
    except Exception as e:
        logger.error(f"차트 생성 오류: {str(e)}")
        return None

def create_line_chart(
    data: Union[Dict, pd.DataFrame, List], 
    x_col: str = "x",
    y_col: str = "y", 
    title: str = "",
    height: int = 400
) -> Optional[go.Figure]:
    """안전한 라인 차트 생성"""
    try:
        fig = go.Figure()
        
        if isinstance(data, dict):
            x_data = data.get(x_col, [])
            y_data = data.get(y_col, [])
        elif isinstance(data, pd.DataFrame):
            x_data = data[x_col] if x_col in data.columns else data.index
            y_data = data[y_col] if y_col in data.columns else []
        else:
            logger.error("지원하지 않는 데이터 형식")
            return None
        
        if not x_data or not y_data:
            logger.warning("차트 데이터가 비어있습니다")
            return None
        
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines+markers',
            name=title or 'Data',
            line=dict(color='#3182F6', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=title,
            height=height,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Pretendard", color="#191919"),
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(gridcolor='rgba(229, 232, 235, 0.5)'),
            yaxis=dict(gridcolor='rgba(229, 232, 235, 0.5)')
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"라인 차트 생성 오류: {str(e)}")
        return None

def create_bar_chart(
    data: Union[Dict, pd.DataFrame], 
    x_col: str = "x",
    y_col: str = "y",
    title: str = "",
    height: int = 400,
    orientation: str = "v"
) -> Optional[go.Figure]:
    """안전한 바 차트 생성"""
    try:
        fig = go.Figure()
        
        if isinstance(data, dict):
            x_data = data.get(x_col, [])
            y_data = data.get(y_col, [])
        elif isinstance(data, pd.DataFrame):
            x_data = data[x_col] if x_col in data.columns else data.index
            y_data = data[y_col] if y_col in data.columns else []
        else:
            logger.error("지원하지 않는 데이터 형식")
            return None
        
        if not x_data or not y_data:
            logger.warning("차트 데이터가 비어있습니다")
            return None
        
        # 색상 맵핑 (양수/음수)
        colors = ['#14AE5C' if val >= 0 else '#DC2626' for val in y_data]
        
        if orientation == "h":
            fig.add_trace(go.Bar(
                x=y_data,
                y=x_data,
                orientation='h',
                marker=dict(color=colors),
                name=title or 'Data'
            ))
        else:
            fig.add_trace(go.Bar(
                x=x_data,
                y=y_data,
                marker=dict(color=colors),
                name=title or 'Data'
            ))
        
        fig.update_layout(
            title=title,
            height=height,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Pretendard", color="#191919"),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"바 차트 생성 오류: {str(e)}")
        return None

def create_pie_chart(
    data: Union[Dict, pd.DataFrame],
    labels_col: str = "labels",
    values_col: str = "values", 
    title: str = "",
    height: int = 400
) -> Optional[go.Figure]:
    """안전한 파이 차트 생성"""
    try:
        fig = go.Figure()
        
        if isinstance(data, dict):
            labels = data.get(labels_col, [])
            values = data.get(values_col, [])
        elif isinstance(data, pd.DataFrame):
            labels = data[labels_col] if labels_col in data.columns else data.index
            values = data[values_col] if values_col in data.columns else []
        else:
            logger.error("지원하지 않는 데이터 형식")
            return None
        
        if not labels or not values:
            logger.warning("차트 데이터가 비어있습니다")
            return None
        
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(
                colors=['#3182F6', '#14AE5C', '#FF9500', '#DC2626', '#8B5CF6'],
                line=dict(color='#FFFFFF', width=2)
            )
        ))
        
        fig.update_layout(
            title=title,
            height=height,
            showlegend=True,
            font=dict(family="Pretendard", color="#191919"),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"파이 차트 생성 오류: {str(e)}")
        return None

# ================================
# [ADVANCED COMPONENTS] 고급 컴포넌트
# ================================

def create_progress_bar(
    current: Union[int, float], 
    total: Union[int, float], 
    label: str = "진행률",
    show_percentage: bool = True,
    color: str = "var(--primary-blue)"
) -> None:
    """안전한 진행률 바 생성"""
    try:
        # 입력값 검증
        current = max(0, float(current))
        total = max(1, float(total))
        progress = min(current / total, 1.0)
        
        safe_label = escape_html(str(label))
        percentage_text = f"{progress*100:.1f}% 완료" if show_percentage else ""
        
        html = f'''
        <div class="ui-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-weight: 600; color: var(--text-primary);">{safe_label}</span>
                <span style="color: var(--text-secondary);">{current:.0f}/{total:.0f}</span>
            </div>
            <div class="ui-progress-container">
                <div class="ui-progress-bar" style="width: {progress*100}%; background-color: {color};"></div>
            </div>
            <div style="text-align: center; margin-top: 0.5rem; color: var(--text-secondary); font-size: 0.9rem;">
                {percentage_text}
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"진행률 바 생성 오류: {str(e)}")
        st.progress(min(current / total, 1.0))

def create_stat_comparison(
    stats_dict: Dict[str, Union[str, int, float]], 
    title: str = "통계 비교"
) -> None:
    """안전한 통계 비교 카드 생성"""
    try:
        safe_title = escape_html(str(title))
        items_html = ""
        
        for key, value in stats_dict.items():
            safe_key = escape_html(str(key))
            safe_value = escape_html(str(value))
            
            # 값에 따른 아이콘 및 색상 결정
            if isinstance(value, (int, float)):
                try:
                    num_value = float(value)
                    if num_value > 0:
                        color = "var(--success-color)"
                        icon = "📈"
                    elif num_value < 0:
                        color = "var(--error-color)"
                        icon = "📉"
                    else:
                        color = "var(--text-secondary)"
                        icon = "➖"
                except (ValueError, TypeError):
                    color = "var(--text-primary)"
                    icon = ""
            else:
                color = "var(--text-primary)"
                icon = ""
            
            items_html += f'''
            <div class="ui-trade-item" style="border-bottom: 1px solid var(--border-color);">
                <span style="color: var(--text-secondary);">{safe_key}</span>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    {f'<span>{icon}</span>' if icon else ''}
                    <span style="color: {color}; font-weight: 600;">{safe_value}</span>
                </div>
            </div>
            '''
        
        html = f'''
        <div class="ui-card">
            <h4 class="ui-card-title">{safe_title}</h4>
            <div>
                {items_html}
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"통계 비교 카드 생성 오류: {str(e)}")
        st.write(f"**{title}**")
        for key, value in stats_dict.items():
            st.write(f"- {key}: {value}")

def create_timeline_item(
    date: str, 
    title: str, 
    description: str, 
    status: str = "completed"
) -> None:
    """안전한 타임라인 아이템 생성"""
    try:
        safe_date = escape_html(str(date))
        safe_title = escape_html(str(title))
        safe_description = escape_html(str(description))
        
        # 상태에 따른 아이콘 및 색상
        status_config = {
            "completed": {"icon": "✅", "color": "var(--success-color)"},
            "in_progress": {"icon": "🔄", "color": "var(--warning-color)"},
            "pending": {"icon": "⏳", "color": "var(--text-light)"},
        }
        
        config = status_config.get(status, status_config["pending"])
        
        html = f'''
        <div style="
            display: flex; 
            margin-bottom: 1rem; 
            padding: 1rem; 
            background-color: var(--card-bg); 
            border-radius: 12px; 
            border-left: 4px solid {config['color']};
            box-shadow: var(--shadow-sm);
        ">
            <div style="margin-right: 1rem; font-size: 1.5rem;">{config['icon']}</div>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <h4 style="margin: 0; color: var(--text-primary);">{safe_title}</h4>
                    <span style="color: var(--text-light); font-size: 0.9rem;">{safe_date}</span>
                </div>
                <p style="margin: 0; color: var(--text-secondary); line-height: 1.5;">{safe_description}</p>
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"타임라인 아이템 생성 오류: {str(e)}")
        st.write(f"**{date}** - {title}: {description}")

def create_feature_highlight(
    features_list: List[str], 
    title: str = "주요 기능"
) -> None:
    """안전한 기능 하이라이트 카드 생성"""
    try:
        safe_title = escape_html(str(title))
        features_html = ""
        
        for feature in features_list:
            safe_feature = escape_html(str(feature))
            features_html += f'''
            <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                <div style="
                    width: 8px; 
                    height: 8px; 
                    background-color: var(--primary-blue); 
                    border-radius: 50%; 
                    margin-right: 1rem;
                    flex-shrink: 0;
                "></div>
                <span style="color: var(--text-secondary);">{safe_feature}</span>
            </div>
            '''
        
        html = f'''
        <div class="ui-card" style="background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);">
            <h4 class="ui-card-title">{safe_title}</h4>
            <div>
                {features_html}
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"기능 하이라이트 생성 오류: {str(e)}")
        st.write(f"**{title}**")
        for feature in features_list:
            st.write(f"• {feature}")

def create_quote_card(
    quote: str, 
    author: str, 
    context: str = ""
) -> None:
    """안전한 명언 카드 생성"""
    try:
        safe_quote = escape_html(str(quote))
        safe_author = escape_html(str(author))
        safe_context = escape_html(str(context))
        
        context_html = f'<div style="color: var(--text-light); font-size: 0.9rem; margin-top: 0.5rem;">{safe_context}</div>' if context else ''
        
        html = f'''
        <div class="ui-card" style="
            background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); 
            border: 1px solid #FDBA74; 
            text-align: center;
        ">
            <div style="font-size: 2rem; color: var(--warning-color); margin-bottom: 1rem;">💭</div>
            <blockquote style="
                font-style: italic; 
                font-size: 1.1rem; 
                color: var(--text-primary); 
                margin-bottom: 1rem; 
                line-height: 1.6;
                border: none;
                padding: 0;
            ">
                "{safe_quote}"
            </blockquote>
            <div style="color: var(--text-secondary); font-weight: 600;">- {safe_author}</div>
            {context_html}
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"명언 카드 생성 오류: {str(e)}")
        st.info(f'"{quote}" - {author}')

def create_mirror_coaching_card(
    title: str, 
    insights: List[str], 
    questions: List[str]
) -> None:
    """안전한 AI 거울 코칭 결과 카드 생성"""
    try:
        safe_title = escape_html(str(title))
        
        # 인사이트 HTML 생성
        insights_html = ""
        for insight in insights:
            safe_insight = escape_html(str(insight))
            insights_html += f'''
            <div style="
                display: flex; 
                align-items: flex-start; 
                margin-bottom: 0.5rem; 
                color: var(--text-secondary); 
                line-height: 1.6;
            ">
                <span style="margin-right: 0.5rem; color: var(--primary-blue);">•</span>
                <span>{safe_insight}</span>
            </div>
            '''
        
        # 질문 HTML 생성
        questions_html = ""
        for question in questions:
            safe_question = escape_html(str(question))
            questions_html += f'''
            <div style="
                display: flex; 
                align-items: flex-start; 
                margin-bottom: 0.5rem; 
                color: var(--text-secondary); 
                line-height: 1.6; 
                background: rgba(255,255,255,0.5); 
                padding: 0.75rem; 
                border-radius: 8px;
                border-left: 3px solid var(--primary-blue);
            ">
                <span style="margin-right: 0.5rem; font-size: 1.1em;">❓</span>
                <span style="font-style: italic;">{safe_question}</span>
            </div>
            '''
        
        html = f'''
        <div class="ui-ai-card">
            <div class="ui-ai-title">
                <span style="font-size: 1.5rem;">🪞</span>
                {safe_title}
            </div>
            
            <div style="margin-bottom: 1.5rem;">
                <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.75rem;">
                    💡 AI 분석 인사이트
                </div>
                {insights_html}
            </div>
            
            <div>
                <div style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.75rem;">
                    🤔 성찰을 위한 질문
                </div>
                {questions_html}
            </div>
        </div>
        '''
        render_html(html, height=None)
        
    except Exception as e:
        logger.error(f"거울 코칭 카드 생성 오류: {str(e)}")
        st.info(f"**{title}**")
        st.write("**인사이트:**")
        for insight in insights:
            st.write(f"• {insight}")
        st.write("**질문:**")
        for question in questions:
            st.write(f"❓ {question}")

def create_enhanced_metric_card(
    title: str, 
    value: str, 
    subtitle: str = "", 
    tone: Optional[str] = None
) -> None:
    """향상된 메트릭 카드 컴포넌트"""
    try:
        safe_title = escape_html(str(title))
        safe_value = escape_html(str(value))
        safe_subtitle = escape_html(str(subtitle))
        
        # 톤에 따른 색상 및 아이콘
        tone_config = {
            "positive": {"color": "#10B981", "icon": "▲"},
            "negative": {"color": "#EF4444", "icon": "▼"},
            None: {"color": "var(--text-primary)", "icon": ""}
        }
        
        config = tone_config.get(tone, tone_config[None])
        icon_html = f'<span style="color:{config["color"]}; font-size:0.9rem; font-weight:700;">{config["icon"]}</span>' if config["icon"] else ""
        
        html = f'''
        <div style="
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 16px;
            box-shadow: var(--shadow-md);
            height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: var(--transition-normal);
        ">
            <div style="font-size: 0.9rem; color: var(--text-secondary);">{safe_title}</div>
            <div style="display:flex; align-items: baseline; gap: 8px;">
                <div style="font-size: 1.6rem; font-weight: 800; color: var(--text-primary); line-height: 1;">
                    {safe_value}
                </div>
                {icon_html}
            </div>
            <div style="font-size: 0.85rem; color: {config['color'] if tone in ('positive','negative') else 'var(--text-light)'};">
                {safe_subtitle}
            </div>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"향상된 메트릭 카드 생성 오류: {str(e)}")
        # 폴백 UI
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            st.metric(title, value, subtitle)

# ================================
# [UTILITY FUNCTIONS] 유틸리티 함수들
# ================================

def show_loading_spinner(message: str = "처리 중...") -> None:
    """로딩 스피너 표시"""
    try:
        with st.spinner(escape_html(str(message))):
            import time
            time.sleep(0.5)  # 짧은 지연으로 사용자 경험 개선
    except Exception as e:
        logger.error(f"로딩 스피너 표시 오류: {str(e)}")

def show_success_message(message: str, show_balloons: bool = True) -> None:
    """성공 메시지 표시"""
    try:
        safe_message = escape_html(str(message))
        st.success(safe_message)
        if show_balloons:
            st.balloons()
    except Exception as e:
        logger.error(f"성공 메시지 표시 오류: {str(e)}")
        st.write(f"✅ {message}")

def create_emotion_tag(emotion: str) -> str:
    """감정 태그 HTML 생성"""
    try:
        safe_emotion = escape_html(str(emotion))
        
        # 감정별 CSS 클래스 매핑
        emotion_classes = {
            '#공포': 'ui-emotion-fear',
            '#패닉': 'ui-emotion-fear',
            '#불안': 'ui-emotion-fear',
            '#욕심': 'ui-emotion-greed',
            '#추격매수': 'ui-emotion-greed',
            '#흥분': 'ui-emotion-greed',
            '#냉정': 'ui-emotion-rational',
            '#확신': 'ui-emotion-rational',
            '#합리적': 'ui-emotion-rational'
        }
        
        css_class = emotion_classes.get(emotion, 'ui-emotion-default')
        
        return f'<span class="ui-emotion-tag {css_class}">{safe_emotion}</span>'
        
    except Exception as e:
        logger.error(f"감정 태그 생성 오류: {str(e)}")
        return escape_html(str(emotion))

def create_live_indicator(text: str = "실시간") -> str:
    """라이브 인디케이터 HTML 생성"""
    try:
        safe_text = escape_html(str(text))
        return f'''
        <span class="ui-live-indicator">
            <span class="ui-live-dot"></span>
            {safe_text}
        </span>
        '''
    except Exception as e:
        logger.error(f"라이브 인디케이터 생성 오류: {str(e)}")
        return f"🔴 {text}"

def format_currency(amount: Union[int, float], currency: str = "₩") -> str:
    """통화 포맷팅"""
    try:
        amount = float(amount)
        if amount >= 1e8:  # 1억 이상
            return f"{currency}{amount/1e8:.1f}억"
        elif amount >= 1e4:  # 1만 이상
            return f"{currency}{amount/1e4:.0f}만"
        else:
            return f"{currency}{amount:,.0f}"
    except (ValueError, TypeError):
        return str(amount)

def format_percentage(value: Union[int, float], decimals: int = 2) -> str:
    """퍼센티지 포맷팅"""
    try:
        value = float(value)
        return f"{value:+.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)

# ================================
# [RESPONSIVE UTILITIES] 반응형 유틸리티
# ================================

def get_responsive_columns(
    mobile_cols: int = 1, 
    tablet_cols: int = 2, 
    desktop_cols: int = 3
) -> List:
    """반응형 컬럼 생성 (간단한 버전)"""
    try:
        # Streamlit에서는 정확한 화면 크기를 알 수 없으므로
        # 기본적으로 desktop_cols 사용
        return st.columns(desktop_cols)
    except Exception as e:
        logger.error(f"반응형 컬럼 생성 오류: {str(e)}")
        return st.columns(3)

def create_grid_layout(items: List[Any], cols: int = 3) -> None:
    """그리드 레이아웃 생성"""
    try:
        if not items:
            return
        
        columns = st.columns(cols)
        
        for i, item in enumerate(items):
            col_index = i % cols
            with columns[col_index]:
                if callable(item):
                    item()
                else:
                    st.write(item)
                    
    except Exception as e:
        logger.error(f"그리드 레이아웃 생성 오류: {str(e)}")
        for item in items:
            if callable(item):
                item()
            else:
                st.write(item)

# ================================
# [ACCESSIBILITY] 접근성 개선
# ================================

def add_screen_reader_text(text: str) -> str:
    """스크린 리더용 텍스트 추가"""
    try:
        safe_text = escape_html(str(text))
        return f'<span class="sr-only" style="position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0;">{safe_text}</span>'
    except Exception as e:
        logger.error(f"스크린 리더 텍스트 생성 오류: {str(e)}")
        return ""

def create_accessible_button(
    text: str, 
    onclick: Optional[str] = None, 
    aria_label: Optional[str] = None
) -> str:
    """접근성이 개선된 버튼 HTML 생성"""
    try:
        safe_text = escape_html(str(text))
        safe_aria_label = escape_html(str(aria_label)) if aria_label else safe_text
        onclick_attr = f'onclick="{escape_html(str(onclick))}"' if onclick else ''
        
        return f'''
        <button 
            class="ui-accessible-button"
            aria-label="{safe_aria_label}"
            {onclick_attr}
            style="
                background-color: var(--primary-blue);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: var(--transition-fast);
            "
        >
            {safe_text}
        </button>
        '''
    except Exception as e:
        logger.error(f"접근 가능한 버튼 생성 오류: {str(e)}")
        return f'<button>{text}</button>'

# ================================
# [DASHBOARD COMPONENTS] 대시보드 컴포넌트
# ================================

def create_dashboard_header(title: str, subtitle: str = "", live: bool = False) -> None:
    """대시보드 헤더 생성"""
    try:
        safe_title = escape_html(str(title))
        safe_subtitle = escape_html(str(subtitle))
        
        live_indicator = create_live_indicator() if live else ""
        subtitle_html = f'<div class="ui-sub-header">{safe_subtitle}</div>' if subtitle else ""
        
        html = f'''
        <div style="margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                <h1 class="ui-main-header" style="margin: 0;">{safe_title}</h1>
                {live_indicator}
            </div>
            {subtitle_html}
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"대시보드 헤더 생성 오류: {str(e)}")
        st.title(title)
        if subtitle:
            st.caption(subtitle)

def create_kpi_row(kpis: List[Dict[str, Any]], columns: int = 4) -> None:
    """KPI 행 생성"""
    try:
        cols = st.columns(columns)
        
        for i, kpi in enumerate(kpis):
            if i >= columns:
                break
                
            with cols[i]:
                create_enhanced_metric_card(
                    title=kpi.get('title', ''),
                    value=kpi.get('value', ''),
                    subtitle=kpi.get('subtitle', ''),
                    tone=kpi.get('tone', None)
                )
                
    except Exception as e:
        logger.error(f"KPI 행 생성 오류: {str(e)}")
        for kpi in kpis:
            st.metric(
                kpi.get('title', ''),
                kpi.get('value', ''),
                kpi.get('subtitle', '')
            )

def create_section_divider(title: str, icon: str = "") -> None:
    """섹션 구분선 생성"""
    try:
        safe_title = escape_html(str(title))
        safe_icon = escape_html(str(icon))
        
        icon_html = f'<span style="margin-right: 0.5rem;">{safe_icon}</span>' if icon else ''
        
        html = f'''
        <div style="
            margin: 2rem 0 1.5rem 0;
            padding: 1rem 0;
            border-bottom: 2px solid var(--border-color);
            position: relative;
        ">
            <h3 style="
                margin: 0;
                font-size: 1.25rem;
                font-weight: 700;
                color: var(--text-primary);
                display: flex;
                align-items: center;
            ">
                {icon_html}{safe_title}
            </h3>
        </div>
        '''
        render_html(html)
        
    except Exception as e:
        logger.error(f"섹션 구분선 생성 오류: {str(e)}")
        st.subheader(f"{icon} {title}")

# ================================
# [ERROR HANDLING] 에러 처리
# ================================

def safe_render_component(component_func, fallback_func=None, **kwargs):
    """안전한 컴포넌트 렌더링 래퍼"""
    try:
        return component_func(**kwargs)
    except Exception as e:
        logger.error(f"컴포넌트 렌더링 실패: {str(e)}")
        if fallback_func:
            try:
                return fallback_func(**kwargs)
            except Exception as fallback_error:
                logger.error(f"폴백 컴포넌트도 실패: {str(fallback_error)}")
                st.error("컴포넌트를 로드할 수 없습니다.")
        else:
            st.error("컴포넌트를 로드할 수 없습니다.")

def handle_chart_error(chart_func, data, **kwargs):
    """차트 렌더링 에러 처리"""
    try:
        fig = chart_func(data, **kwargs)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("차트 데이터가 없습니다.")
    except Exception as e:
        logger.error(f"차트 렌더링 실패: {str(e)}")
        st.error("차트를 생성할 수 없습니다.")

# ================================
# [ANIMATION UTILITIES] 애니메이션 유틸리티
# ================================

def create_loading_animation() -> str:
    """로딩 애니메이션 HTML 생성"""
    return '''
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    ">
        <div style="
            width: 40px;
            height: 40px;
            border: 4px solid var(--border-color);
            border-top: 4px solid var(--primary-blue);
            border-radius: 50%;
            animation: ui-spin 1s linear infinite;
        "></div>
    </div>
    <style>
        @keyframes ui-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    '''

def create_fade_in_animation(content: str, delay: float = 0) -> str:
    """페이드인 애니메이션 래퍼"""
    return f'''
    <div style="
        animation: ui-fadeIn 0.5s ease-in-out {delay}s both;
    ">
        {content}
    </div>
    <style>
        @keyframes ui-fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
    '''

# ================================
# [INITIALIZATION] 초기화
# ================================

def initialize_ui():
    """UI 시스템 초기화"""
    try:
        # CSS 적용
        apply_toss_css()
        
        # 페이지 설정
        if 'ui_initialized' not in st.session_state:
            st.session_state.ui_initialized = True
            logger.info("UI 시스템 초기화 완료")
            
    except Exception as e:
        logger.error(f"UI 초기화 실패: {str(e)}")

def get_ui_version():
    """UI 컴포넌트 버전 정보"""
    return {
        "version": "2.0",
        "last_updated": "2024-08-10",
        "features": [
            "안전한 HTML 렌더링",
            "Toss 스타일 디자인 시스템",
            "반응형 컴포넌트",
            "접근성 개선",
            "에러 처리 강화"
        ]
    }

# 모듈 로드 시 자동 초기화 (선택적)
# initialize_ui()  # 필요에 따라 주석 해제

# ================================
# [MODULE EXPORTS] 모듈 내보내기
# ================================

__all__ = [
    # 기본 렌더링
    'render_html', 'escape_html', 'apply_toss_css',
    
    # 기본 컴포넌트
    'create_metric_card', 'show_info_card', 'show_warning_card', 
    'show_error_card', 'show_success_card',
    
    # 차트 컴포넌트
    'create_safe_chart', 'create_line_chart', 'create_bar_chart', 'create_pie_chart',
    
    # 고급 컴포넌트
    'create_progress_bar', 'create_stat_comparison', 'create_timeline_item',
    'create_feature_highlight', 'create_quote_card', 'create_mirror_coaching_card',
    'create_enhanced_metric_card',
    
    # 유틸리티
    'show_loading_spinner', 'show_success_message', 'create_emotion_tag',
    'create_live_indicator', 'format_currency', 'format_percentage',
    
    # 레이아웃
    'get_responsive_columns', 'create_grid_layout',
    
    # 접근성
    'add_screen_reader_text', 'create_accessible_button',
    
    # 대시보드
    'create_dashboard_header', 'create_kpi_row', 'create_section_divider',
    
    # 에러 처리
    'safe_render_component', 'handle_chart_error',
    
    # 애니메이션
    'create_loading_animation', 'create_fade_in_animation',
    
    # 초기화
    'initialize_ui', 'get_ui_version'
]

if __name__ == "__main__":
    print("UI Components Module V2.0 - 테스트 모드")
    print("사용 가능한 컴포넌트:")
    for component in __all__:
        print(f"  - {component}")