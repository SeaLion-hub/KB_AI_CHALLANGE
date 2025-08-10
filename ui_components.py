"""
UI 컴포넌트 모듈 - 안정성 개선 버전 (V2.1)
HTML 렌더링 문제 해결 및 컴포넌트 안정성 강화

수정사항:
- render_html() 함수 단순화 및 안정성 개선
- HTML 렌더링 로직 일원화
- 에러 처리 구체화
- Streamlit 기본 함수 우선 사용
- 폴백 메커니즘 강화
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
# [SAFE HTML RENDERING] 안전한 HTML 렌더링 - 개선 버전
# ================================

def render_html(html_string: str, height: Optional[int] = None, scrolling: bool = False, key: Optional[str] = None):
    """
    안전하고 단순한 HTML 렌더링 (문제 해결 버전)
    
    Args:
        html_string: 렌더링할 HTML 문자열
        height: 컴포넌트 높이 (px) - None이면 자동
        scrolling: 스크롤 허용 여부
        key: 고유 키
    """
    try:
        # 입력값 검증
        if not html_string or not isinstance(html_string, str):
            logger.warning("유효하지 않은 HTML 문자열")
            return
        
        # 위험한 태그 제거 (보안)
        dangerous_tags = ['<script', '<iframe', '<object', '<embed']
        clean_html = html_string
        for tag in dangerous_tags:
            if tag in clean_html.lower():
                logger.warning(f"위험한 태그 제거: {tag}")
                clean_html = clean_html.replace(tag, f'&lt;{tag[1:]}')
        
        # **핵심 수정: 단순화된 렌더링 로직**
        # height가 지정되었거나 매우 긴 HTML만 components.html 사용
        if height is not None or len(clean_html) > 2000:
            # 복잡한 컴포넌트용 (iframe 기반)
            components.html(
                clean_html, 
                height=height or 400, 
                scrolling=scrolling,
                key=key
            )
        else:
            # 간단한 HTML은 markdown으로 (더 안정적)
            st.markdown(clean_html, unsafe_allow_html=True)
            
    except Exception as e:
        # 구체적인 에러 정보 제공
        logger.error(f"HTML 렌더링 실패: {str(e)}")
        logger.error(f"HTML 길이: {len(html_string) if html_string else 0}")
        
        # 폴백: Streamlit 기본 함수로 대체
        try:
            if "style=" in html_string:
                # 스타일이 있는 경우 간단한 형태로 변환
                st.markdown("⚠️ 스타일 컴포넌트 렌더링 중...")
            else:
                st.write(html_string)
        except:
            st.error("⚠️ 컴포넌트를 표시할 수 없습니다.")

def escape_html(text: str) -> str:
    """HTML 이스케이프 처리 - 개선"""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return html.escape(text)

# ================================
# [ENHANCED CSS] CSS 시스템 - 단순화
# ================================

def apply_toss_css():
    """Toss 스타일 CSS - 안정성 우선 버전"""
    try:
        # 핵심 CSS만 포함 (문제 요소 제거)
        css = """
        <style>
            /* 기본 폰트 및 색상 */
            :root {
                --bg-color: #F2F4F6;
                --card-bg: #FFFFFF;
                --primary-blue: #3182F6;
                --text-primary: #191919;
                --text-secondary: #505967;
                --text-light: #8B95A1;
                --border-color: #E5E8EB;
                --positive-color: #14AE5C;
                --negative-color: #DC2626;
                --shadow-md: 0 4px 12px rgba(0,0,0,0.05);
            }

            .main .block-container {
                padding-top: 2rem;
                max-width: 1200px;
            }

            /* 메트릭 카드 - 단순화 */
            .ui-metric-card {
                background: white;
                border-radius: 16px;
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                box-shadow: var(--shadow-md);
                text-align: center;
                min-height: 120px;
            }

            .ui-metric-label {
                font-size: 14px;
                color: var(--text-light);
                margin-bottom: 0.5rem;
            }

            .ui-metric-value {
                font-size: 28px;
                font-weight: 700;
                color: var(--text-primary);
            }

            .ui-metric-value.positive { color: var(--positive-color); }
            .ui-metric-value.negative { color: var(--negative-color); }

            /* 카드 컴포넌트 - 기본 */
            .ui-card {
                background: white;
                border-radius: 16px;
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                box-shadow: var(--shadow-md);
                margin-bottom: 1rem;
            }

            .ui-card-title {
                font-size: 18px;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 1rem;
            }

            /* 버튼 스타일 개선 */
            .stButton > button {
                border-radius: 12px !important;
                font-weight: 600 !important;
                transition: all 0.2s ease !important;
            }

            /* 알림 카드들 - 단순화 */
            .ui-info-card {
                background: #F0F9FF;
                border: 1px solid #BFDBFE;
                border-radius: 12px;
                padding: 1rem;
                margin: 1rem 0;
            }

            .ui-warning-card {
                background: #FFFBEB;
                border: 1px solid #F59E0B;
                border-radius: 12px;
                padding: 1rem;
                margin: 1rem 0;
            }

            .ui-error-card {
                background: #FEF2F2;
                border: 1px solid #F87171;
                border-radius: 12px;
                padding: 1rem;
                margin: 1rem 0;
            }

            .ui-success-card {
                background: #F0FDF4;
                border: 1px solid #86EFAC;
                border-radius: 12px;
                padding: 1rem;
                margin: 1rem 0;
            }
        </style>
        """
        
        # 기본 st.markdown 사용 (더 안정적)
        st.markdown(css, unsafe_allow_html=True)
        logger.debug("CSS 적용 완료")
        
    except Exception as e:
        logger.error(f"CSS 적용 실패: {str(e)}")
        # CSS 실패해도 앱은 계속 동작

# ================================
# [SAFE COMPONENT CREATION] 안전한 컴포넌트 - 개선
# ================================

def create_metric_card(label: str, value: Union[str, int, float], color_class: str = "", subtitle: str = "", icon: str = "") -> None:
    """안전한 메트릭 카드 - Streamlit 기본 함수 우선 사용"""
    try:
        # Streamlit 기본 메트릭 사용 (가장 안전)
        if color_class in ["positive", "negative"] and isinstance(value, (int, float)):
            delta_value = f"+{value}" if color_class == "positive" else f"{value}"
            st.metric(
                label=f"{icon} {label}" if icon else label,
                value=value,
                delta=subtitle if subtitle else None
            )
        else:
            # 간단한 HTML만 사용
            safe_label = escape_html(str(label))
            safe_value = escape_html(str(value))
            safe_subtitle = escape_html(str(subtitle))
            safe_icon = escape_html(str(icon))
            
            st.markdown(f"""
            <div class="ui-metric-card">
                <div class="ui-metric-label">{safe_icon} {safe_label}</div>
                <div class="ui-metric-value {color_class}">{safe_value}</div>
                {f'<div style="font-size: 12px; color: #8B95A1; margin-top: 4px;">{safe_subtitle}</div>' if subtitle else ''}
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        logger.error(f"메트릭 카드 생성 실패: {str(e)}")
        # 폴백: 기본 Streamlit 컴포넌트
        st.metric(label, value, subtitle)

def show_info_card(title: str, content: str, icon: str = "💡") -> None:
    """안전한 정보 카드"""
    try:
        # 간단한 st.info 사용 (더 안정적)
        st.info(f"{icon} **{title}**\n\n{content}")
    except Exception as e:
        logger.error(f"정보 카드 생성 실패: {str(e)}")
        st.info(f"{title}: {content}")

def show_warning_card(title: str, content: str, icon: str = "⚠️") -> None:
    """안전한 경고 카드"""
    try:
        st.warning(f"{icon} **{title}**\n\n{content}")
    except Exception as e:
        logger.error(f"경고 카드 생성 실패: {str(e)}")
        st.warning(f"{title}: {content}")

def show_error_card(title: str, content: str, icon: str = "❌") -> None:
    """안전한 오류 카드"""
    try:
        st.error(f"{icon} **{title}**\n\n{content}")
    except Exception as e:
        logger.error(f"오류 카드 생성 실패: {str(e)}")
        st.error(f"{title}: {content}")

def show_success_card(title: str, content: str, icon: str = "✅") -> None:
    """안전한 성공 카드"""
    try:
        st.success(f"{icon} **{title}**\n\n{content}")
    except Exception as e:
        logger.error(f"성공 카드 생성 실패: {str(e)}")
        st.success(f"{title}: {content}")

# ================================
# [ENHANCED METRIC CARD] 핵심 컴포넌트 개선
# ================================

def create_enhanced_metric_card(title: str, value: str, subtitle: str = "", tone: Optional[str] = None) -> None:
    """향상된 메트릭 카드 - 안정성 우선"""
    try:
        # 텍스트 안전 처리
        safe_title = escape_html(str(title))
        safe_value = escape_html(str(value))
        safe_subtitle = escape_html(str(subtitle))
        
        # 톤에 따른 색상
        if tone == "positive":
            color = "#10B981"
            icon = "▲"
        elif tone == "negative":
            color = "#EF4444"
            icon = "▼"
        else:
            color = "#374151"
            icon = ""
        
        # 단순한 HTML 구조 사용
        html = f"""
        <div style="
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
            min-height: 100px;
        ">
            <div style="font-size: 14px; color: #6B7280; margin-bottom: 8px;">
                {safe_title}
            </div>
            <div style="font-size: 24px; font-weight: 700; color: {color}; margin-bottom: 4px;">
                {safe_value} {icon}
            </div>
            {f'<div style="font-size: 12px; color: #9CA3AF;">{safe_subtitle}</div>' if subtitle else ''}
        </div>
        """
        
        # 안전한 렌더링 (height 없이)
        st.markdown(html, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"향상된 메트릭 카드 실패: {str(e)}")
        # 완전한 폴백: Streamlit 기본
        st.metric(title, value, subtitle)

# ================================
# [MIRROR COACHING CARD] 거울 코칭 카드 개선
# ================================

def create_mirror_coaching_card(title: str, insights: List[str], questions: List[str]) -> None:
    """거울 코칭 카드 - 안정성 개선"""
    try:
        # Streamlit 기본 컴포넌트 조합 사용
        st.markdown(f"### 🪞 {title}")
        
        # 인사이트 섹션
        st.markdown("**💡 AI 분석 인사이트**")
        for insight in insights:
            st.markdown(f"• {insight}")
        
        # 질문 섹션
        if questions:
            st.markdown("**🤔 성찰을 위한 질문**")
            for question in questions:
                st.markdown(f"❓ {question}")
                
    except Exception as e:
        logger.error(f"거울 코칭 카드 실패: {str(e)}")
        # 폴백
        st.info(f"**{title}**")
        for insight in insights:
            st.write(f"• {insight}")
        for question in questions:
            st.write(f"❓ {question}")

# ================================
# [CHART FUNCTIONS] 차트 함수 - 안정성 개선
# ================================

def create_safe_chart(chart_type: str, data: Any, **kwargs) -> Optional[go.Figure]:
    """안전한 차트 생성"""
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
        logger.error(f"차트 생성 실패: {str(e)}")
        return None

def create_line_chart(data: Union[Dict, pd.DataFrame, List], x_col: str = "x", y_col: str = "y", title: str = "", height: int = 400) -> Optional[go.Figure]:
    """안전한 라인 차트"""
    try:
        fig = go.Figure()
        
        # 데이터 처리
        if isinstance(data, dict):
            x_data = data.get(x_col, [])
            y_data = data.get(y_col, [])
        elif isinstance(data, pd.DataFrame):
            x_data = data[x_col] if x_col in data.columns else data.index
            y_data = data[y_col] if y_col in data.columns else []
        else:
            return None
        
        if not x_data or not y_data:
            return None
        
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines+markers',
            line=dict(color='#3182F6', width=2),
            marker=dict(size=4)
        ))
        
        fig.update_layout(
            title=title,
            height=height,
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"라인 차트 생성 실패: {str(e)}")
        return None

def create_bar_chart(data: Union[Dict, pd.DataFrame], x_col: str = "x", y_col: str = "y", title: str = "", height: int = 400, orientation: str = "v") -> Optional[go.Figure]:
    """안전한 바 차트"""
    try:
        fig = go.Figure()
        
        if isinstance(data, dict):
            x_data = data.get(x_col, [])
            y_data = data.get(y_col, [])
        elif isinstance(data, pd.DataFrame):
            x_data = data[x_col] if x_col in data.columns else data.index
            y_data = data[y_col] if y_col in data.columns else []
        else:
            return None
        
        if not x_data or not y_data:
            return None
        
        colors = ['#14AE5C' if val >= 0 else '#DC2626' for val in y_data]
        
        if orientation == "h":
            fig.add_trace(go.Bar(x=y_data, y=x_data, orientation='h', marker=dict(color=colors)))
        else:
            fig.add_trace(go.Bar(x=x_data, y=y_data, marker=dict(color=colors)))
        
        fig.update_layout(
            title=title,
            height=height,
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"바 차트 생성 실패: {str(e)}")
        return None

def create_pie_chart(data: Union[Dict, pd.DataFrame], labels_col: str = "labels", values_col: str = "values", title: str = "", height: int = 400) -> Optional[go.Figure]:
    """안전한 파이 차트"""
    try:
        fig = go.Figure()
        
        if isinstance(data, dict):
            labels = data.get(labels_col, [])
            values = data.get(values_col, [])
        elif isinstance(data, pd.DataFrame):
            labels = data[labels_col] if labels_col in data.columns else data.index
            values = data[values_col] if values_col in data.columns else []
        else:
            return None
        
        if not labels or not values:
            return None
        
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(colors=['#3182F6', '#14AE5C', '#FF9500', '#DC2626', '#8B5CF6'])
        ))
        
        fig.update_layout(
            title=title,
            height=height,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"파이 차트 생성 실패: {str(e)}")
        return None

# ================================
# [UTILITY FUNCTIONS] 유틸리티 - 단순화
# ================================

def show_loading_spinner(message: str = "처리 중...") -> None:
    """로딩 스피너"""
    try:
        with st.spinner(escape_html(str(message))):
            import time
            time.sleep(0.1)  # 매우 짧은 지연
    except Exception as e:
        logger.error(f"로딩 스피너 실패: {str(e)}")

def show_success_message(message: str, show_balloons: bool = True) -> None:
    """성공 메시지"""
    try:
        st.success(escape_html(str(message)))
        if show_balloons:
            st.balloons()
    except Exception as e:
        logger.error(f"성공 메시지 실패: {str(e)}")
        st.write(f"✅ {message}")

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
# [DASHBOARD COMPONENTS] 대시보드 전용
# ================================

def create_dashboard_header(title: str, subtitle: str = "", live: bool = False) -> None:
    """대시보드 헤더"""
    try:
        st.title(f"📊 {title}")
        if subtitle:
            st.caption(subtitle)
        if live:
            st.caption("🔴 실시간 업데이트")
    except Exception as e:
        logger.error(f"대시보드 헤더 실패: {str(e)}")
        st.title(title)

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
        logger.error(f"KPI 행 생성 실패: {str(e)}")
        # 폴백: 기본 메트릭
        for kpi in kpis:
            st.metric(
                kpi.get('title', ''),
                kpi.get('value', ''),
                kpi.get('subtitle', '')
            )

def create_section_divider(title: str, icon: str = "") -> None:
    """섹션 구분선"""
    try:
        if icon:
            st.subheader(f"{icon} {title}")
        else:
            st.subheader(title)
    except Exception as e:
        logger.error(f"섹션 구분선 실패: {str(e)}")
        st.write(f"## {title}")

# ================================
# [ERROR HANDLING] 강화된 에러 처리
# ================================

def safe_render_component(component_func, fallback_func=None, **kwargs):
    """안전한 컴포넌트 렌더링"""
    try:
        return component_func(**kwargs)
    except Exception as e:
        logger.error(f"컴포넌트 렌더링 실패 [{component_func.__name__}]: {str(e)}")
        
        if fallback_func:
            try:
                return fallback_func(**kwargs)
            except Exception as fallback_error:
                logger.error(f"폴백도 실패: {str(fallback_error)}")
                st.error("⚠️ 컴포넌트를 표시할 수 없습니다.")
        else:
            st.error("⚠️ 컴포넌트를 표시할 수 없습니다.")

def handle_chart_error(chart_func, data, **kwargs):
    """차트 에러 처리"""
    try:
        fig = chart_func(data, **kwargs)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 차트 데이터가 없습니다.")
    except Exception as e:
        logger.error(f"차트 렌더링 실패: {str(e)}")
        st.error("📊 차트를 생성할 수 없습니다.")

# ================================
# [INITIALIZATION] 초기화
# ================================

def initialize_ui():
    """UI 초기화"""
    try:
        apply_toss_css()
        if 'ui_initialized' not in st.session_state:
            st.session_state.ui_initialized = True
            logger.info("UI 시스템 초기화 완료")
    except Exception as e:
        logger.error(f"UI 초기화 실패: {str(e)}")

# ================================
# [EXPORTS] 모듈 내보내기
# ================================

__all__ = [
    # 기본 렌더링
    'render_html', 'escape_html', 'apply_toss_css',
    
    # 기본 컴포넌트
    'create_metric_card', 'show_info_card', 'show_warning_card', 
    'show_error_card', 'show_success_card',
    
    # 차트
    'create_safe_chart', 'create_line_chart', 'create_bar_chart', 'create_pie_chart',
    
    # 고급 컴포넌트
    'create_enhanced_metric_card', 'create_mirror_coaching_card',
    
    # 유틸리티
    'show_loading_spinner', 'show_success_message', 'format_currency', 'format_percentage',
    
    # 대시보드
    'create_dashboard_header', 'create_kpi_row', 'create_section_divider',
    
    # 에러 처리
    'safe_render_component', 'handle_chart_error',
    
    # 초기화
    'initialize_ui'
]

# 자동 초기화
initialize_ui()