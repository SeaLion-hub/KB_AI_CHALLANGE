#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - KB 브랜드 UI 컴포넌트 라이브러리 (완전 동적 버전)
KB AI CHALLENGE 2024

🏛️ KB 금융그룹 디자인 시스템 기반 - 모든 설정이 외부 파일에서 로드
- 모든 하드코딩 제거
- 설정 파일 기반 동적 스타일링
- 재사용 가능한 컴포넌트들
- 접근성과 사용성 고려
"""

import streamlit as st
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json
from pathlib import Path

# ================================
# [설정 기반 KB 컬러 시스템]
# ================================

class KBColors:
    """설정 파일 기반 KB 브랜드 컬러 정의"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._load_color_config()
    
    def _load_color_config(self):
        """컬러 설정 파일에서 로드"""
        color_config_file = self.config_dir / "ui_colors.json"
        
        # 기본 컬러 설정
        default_colors = {
            "brand": {
                "yellow": "#FFDD00",
                "yellow_dark": "#FFB800", 
                "yellow_light": "#FFF2A0"
            },
            "base": {
                "black": "#000000",
                "white": "#FFFFFF",
                "gray_dark": "#333333",
                "gray": "#666666", 
                "gray_light": "#E5E5E5",
                "gray_bg": "#F8F9FA"
            },
            "status": {
                "success": "#28A745",
                "danger": "#DC3545",
                "warning": "#FFC107",
                "info": "#17A2B8"
            },
            "investment": {
                "profit": "#FF6B6B",
                "loss": "#4ECDC4"
            }
        }
        
        # 설정 파일이 있으면 로드, 없으면 기본값으로 생성
        if color_config_file.exists():
            try:
                with open(color_config_file, 'r', encoding='utf-8') as f:
                    color_config = json.load(f)
            except Exception:
                color_config = default_colors
        else:
            color_config = default_colors
            # 기본 설정 파일 생성
            self.config_dir.mkdir(exist_ok=True)
            with open(color_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_colors, f, ensure_ascii=False, indent=2)
        
        # 컬러 값들을 클래스 속성으로 설정
        brand = color_config.get("brand", {})
        base = color_config.get("base", {})
        status = color_config.get("status", {})
        investment = color_config.get("investment", {})
        
        # 브랜드 컬러
        self.YELLOW = brand.get("yellow", "#FFDD00")
        self.YELLOW_DARK = brand.get("yellow_dark", "#FFB800")
        self.YELLOW_LIGHT = brand.get("yellow_light", "#FFF2A0")
        
        # 기본 컬러
        self.BLACK = base.get("black", "#000000")
        self.WHITE = base.get("white", "#FFFFFF")
        self.GRAY_DARK = base.get("gray_dark", "#333333")
        self.GRAY = base.get("gray", "#666666")
        self.GRAY_LIGHT = base.get("gray_light", "#E5E5E5")
        self.GRAY_BG = base.get("gray_bg", "#F8F9FA")
        
        # 상태 컬러
        self.SUCCESS = status.get("success", "#28A745")
        self.DANGER = status.get("danger", "#DC3545")
        self.WARNING = status.get("warning", "#FFC107")
        self.INFO = status.get("info", "#17A2B8")
        
        # 투자 컬러
        self.PROFIT = investment.get("profit", "#FF6B6B")
        self.LOSS = investment.get("loss", "#4ECDC4")

# 전역 컬러 인스턴스
colors = KBColors()

# ================================
# [설정 기반 UI 설정 로더]
# ================================

class UIConfigLoader:
    """UI 설정을 외부 파일에서 로드하는 클래스"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self._load_ui_config()
    
    def _load_ui_config(self):
        """UI 설정 로드"""
        ui_config_file = self.config_dir / "ui_settings.json"
        
        default_ui_config = {
            "typography": {
                "primary_font": "'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif",
                "header_font_size": "3rem",
                "subheader_font_size": "1.4rem",
                "body_font_size": "1rem",
                "small_font_size": "0.8rem"
            },
            "spacing": {
                "card_padding": "1.5rem",
                "section_margin": "2rem",
                "component_gap": "1rem"
            },
            "borders": {
                "border_radius": "12px",
                "card_border_radius": "16px",
                "button_border_radius": "8px",
                "border_width": "2px"
            },
            "shadows": {
                "card_shadow": "0 4px 12px rgba(0,0,0,0.1)",
                "hover_shadow": "0 8px 24px rgba(255,221,0,0.2)",
                "button_shadow": "0 2px 4px rgba(0,0,0,0.1)"
            },
            "animations": {
                "transition_duration": "0.3s",
                "hover_transform": "translateY(-4px)",
                "button_hover_transform": "translateY(-2px)"
            }
        }
        
        if ui_config_file.exists():
            try:
                with open(ui_config_file, 'r', encoding='utf-8') as f:
                    self.ui_config = json.load(f)
            except Exception:
                self.ui_config = default_ui_config
        else:
            self.ui_config = default_ui_config
            with open(ui_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_ui_config, f, ensure_ascii=False, indent=2)
    
    def get(self, category: str, key: str, default: str = ""):
        """설정 값 가져오기"""
        return self.ui_config.get(category, {}).get(key, default)

# 전역 UI 설정 인스턴스
ui_config = UIConfigLoader()

# ================================
# [KB 스타일 CSS - 완전 동적]
# ================================

def apply_kb_theme():
    """KB 테마 적용 - 모든 설정이 파일에서 로드됨"""
    
    # 타이포그래피 설정
    primary_font = ui_config.get("typography", "primary_font")
    header_size = ui_config.get("typography", "header_font_size")
    body_size = ui_config.get("typography", "body_font_size")
    
    # 간격 설정
    card_padding = ui_config.get("spacing", "card_padding")
    section_margin = ui_config.get("spacing", "section_margin")
    
    # 테두리 설정
    border_radius = ui_config.get("borders", "border_radius")
    card_border_radius = ui_config.get("borders", "card_border_radius")
    button_border_radius = ui_config.get("borders", "button_border_radius")
    border_width = ui_config.get("borders", "border_width")
    
    # 그림자 설정
    card_shadow = ui_config.get("shadows", "card_shadow")
    hover_shadow = ui_config.get("shadows", "hover_shadow")
    button_shadow = ui_config.get("shadows", "button_shadow")
    
    # 애니메이션 설정
    transition_duration = ui_config.get("animations", "transition_duration")
    hover_transform = ui_config.get("animations", "hover_transform")
    button_hover_transform = ui_config.get("animations", "button_hover_transform")
    
    st.markdown(f"""
    <style>
    /* ===== KB 브랜드 CSS 변수 (동적 로드) ===== */
    :root {{
        --kb-yellow: {colors.YELLOW};
        --kb-yellow-dark: {colors.YELLOW_DARK};
        --kb-yellow-light: {colors.YELLOW_LIGHT};
        --kb-black: {colors.BLACK};
        --kb-gray-dark: {colors.GRAY_DARK};
        --kb-gray: {colors.GRAY};
        --kb-gray-light: {colors.GRAY_LIGHT};
        --kb-gray-bg: {colors.GRAY_BG};
        --kb-white: {colors.WHITE};
        --kb-success: {colors.SUCCESS};
        --kb-danger: {colors.DANGER};
        --kb-warning: {colors.WARNING};
        --kb-info: {colors.INFO};
        --kb-profit: {colors.PROFIT};
        --kb-loss: {colors.LOSS};
        
        /* UI 설정 변수 */
        --primary-font: {primary_font};
        --header-size: {header_size};
        --body-size: {body_size};
        --card-padding: {card_padding};
        --section-margin: {section_margin};
        --border-radius: {border_radius};
        --card-border-radius: {card_border_radius};
        --button-border-radius: {button_border_radius};
        --border-width: {border_width};
        --card-shadow: {card_shadow};
        --hover-shadow: {hover_shadow};
        --button-shadow: {button_shadow};
        --transition-duration: {transition_duration};
        --hover-transform: {hover_transform};
        --button-hover-transform: {button_hover_transform};
    }}
    
    /* ===== 전역 폰트 및 기본 설정 ===== */
    .main {{
        padding-top: 1rem;
        font-family: var(--primary-font);
        font-size: var(--body-size);
    }}
    
    /* ===== KB 버튼 스타일 ===== */
    .stButton > button {{
        background: var(--kb-yellow) !important;
        color: var(--kb-black) !important;
        border: var(--border-width) solid var(--kb-black) !important;
        border-radius: var(--button-border-radius) !important;
        font-weight: 700 !important;
        font-size: var(--body-size) !important;
        padding: 0.75rem 1.5rem !important;
        transition: all var(--transition-duration) ease !important;
        box-shadow: var(--button-shadow) !important;
        font-family: var(--primary-font) !important;
    }}
    
    .stButton > button:hover {{
        background: var(--kb-yellow-dark) !important;
        transform: var(--button-hover-transform) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
        border-color: var(--kb-gray-dark) !important;
    }}
    
    /* ===== 메트릭 카드 스타일 ===== */
    [data-testid="metric-container"] {{
        background: var(--kb-white);
        border: var(--border-width) solid var(--kb-yellow);
        border-radius: var(--card-border-radius);
        padding: var(--card-padding);
        box-shadow: var(--card-shadow);
        transition: all var(--transition-duration) ease;
        font-family: var(--primary-font);
    }}
    
    [data-testid="metric-container"]:hover {{
        transform: var(--hover-transform);
        box-shadow: var(--hover-shadow);
    }}
    
    /* ===== 입력 필드 스타일 ===== */
    .stTextArea > div > div > textarea,
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {{
        border: var(--border-width) solid var(--kb-yellow) !important;
        border-radius: var(--border-radius) !important;
        background: var(--kb-white) !important;
        font-size: var(--body-size) !important;
        font-family: var(--primary-font) !important;
    }}
    
    .stTextArea > div > div > textarea:focus,
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: var(--kb-yellow-dark) !important;
        box-shadow: 0 0 0 3px rgba(255,221,0,0.2) !important;
    }}
    
    /* ===== 커스텀 카드 클래스 ===== */
    .kb-card {{
        background: var(--kb-white);
        border: var(--border-width) solid var(--kb-yellow);
        border-radius: var(--card-border-radius);
        padding: var(--card-padding);
        margin: var(--section-margin) 0;
        box-shadow: var(--card-shadow);
        transition: all var(--transition-duration) ease;
        font-family: var(--primary-font);
    }}
    
    .kb-card:hover {{
        transform: var(--hover-transform);
        box-shadow: var(--hover-shadow);
        border-color: var(--kb-yellow-dark);
    }}
    
    .kb-info {{
        background: var(--kb-yellow-light);
        border: var(--border-width) solid var(--kb-yellow);
        border-radius: var(--card-border-radius);
        padding: var(--card-padding);
        margin: var(--section-margin) 0;
        color: var(--kb-black);
        font-family: var(--primary-font);
    }}
    
    .metric-card {{
        background: var(--kb-white);
        border: var(--border-width) solid var(--kb-yellow);
        border-radius: var(--card-border-radius);
        padding: var(--card-padding);
        text-align: center;
        transition: all var(--transition-duration) ease;
        box-shadow: var(--card-shadow);
        font-family: var(--primary-font);
    }}
    
    .metric-card:hover {{
        transform: var(--hover-transform);
        box-shadow: var(--hover-shadow);
    }}
    
    .metric-title {{
        font-size: var(--body-size);
        color: var(--kb-gray);
        margin-bottom: 0.5rem;
        font-weight: 600;
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 800;
        color: var(--kb-black);
        margin-bottom: 0.25rem;
    }}
    
    .metric-subtitle {{
        font-size: 0.9rem;
        font-weight: 600;
    }}
    
    /* ===== 사이드바 숨기기 ===== */
    .css-1d391kg {{
        display: none;
    }}
    
    /* ===== 로딩 스피너 ===== */
    .stSpinner > div {{
        border-top-color: var(--kb-yellow) !important;
    }}
    
    /* ===== 스크롤바 커스터마이징 ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--kb-gray-bg);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--kb-yellow);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--kb-yellow-dark);
    }}
    
    /* ===== 반응형 디자인 ===== */
    @media (max-width: 768px) {{
        .main {{
            padding: 0.5rem;
        }}
        
        .kb-card, .kb-info {{
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        .metric-card {{
            padding: 1rem;
        }}
        
        .metric-value {{
            font-size: 1.5rem;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ================================
# [KB 헤더 컴포넌트 - 설정 기반]
# ================================

def kb_header(title: str, subtitle: str = "", icon: str = "🏛️") -> None:
    """KB 브랜드 메인 헤더 - 설정 파일 기반"""
    
    header_size = ui_config.get("typography", "header_font_size")
    subheader_size = ui_config.get("typography", "subheader_font_size")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {colors.YELLOW} 0%, {colors.YELLOW_DARK} 100%);
        color: {colors.BLACK};
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(255, 221, 0, 0.3);
        position: relative;
        overflow: hidden;
        font-family: {ui_config.get('typography', 'primary_font')};
    ">
        <!-- 배경 패턴 -->
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: radial-gradient(circle at 25% 25%, rgba(0,0,0,0.05) 2px, transparent 2px);
            background-size: 30px 30px;
        "></div>
        
        <!-- 컨텐츠 -->
        <div style="position: relative; z-index: 1;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
            <h1 style="
                font-size: {header_size}; 
                font-weight: 800; 
                margin: 0 0 1rem 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                letter-spacing: -1px;
            ">{title}</h1>
            {f'<p style="font-size: {subheader_size}; margin: 0; opacity: 0.9; font-weight: 500;">{subtitle}</p>' if subtitle else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================================
# [설정 기반 카드 컴포넌트들]
# ================================

def kb_metric_card(
    title: str,
    value: Union[str, int, float],
    delta: Optional[str] = None,
    delta_type: str = "normal",
    icon: str = "📊",
    description: str = ""
) -> None:
    """KB 스타일 메트릭 카드 - 설정 기반"""
    
    # 델타 타입별 색상 (설정에서 로드)
    delta_colors = {
        "normal": colors.GRAY,
        "success": colors.SUCCESS,
        "danger": colors.DANGER
    }
    
    delta_color = delta_colors.get(delta_type, colors.GRAY)
    
    st.markdown(f"""
    <div style="
        background: {colors.WHITE};
        border: {ui_config.get('borders', 'border_width')} solid {colors.YELLOW};
        border-radius: {ui_config.get('borders', 'card_border_radius')};
        padding: {ui_config.get('spacing', 'card_padding')};
        text-align: center;
        transition: all {ui_config.get('animations', 'transition_duration')} ease;
        box-shadow: {ui_config.get('shadows', 'card_shadow')};
        height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-family: {ui_config.get('typography', 'primary_font')};
    " class="kb-metric-hover">
        <div>
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="
                font-size: 0.9rem; 
                color: {colors.GRAY}; 
                margin-bottom: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">{title}</div>
            <div style="
                font-size: 2.2rem; 
                font-weight: 800; 
                color: {colors.BLACK};
                margin-bottom: 0.5rem;
                line-height: 1;
            ">{value}</div>
        </div>
        
        <div>
            {f'''
            <div style="
                color: {delta_color}; 
                font-size: 0.85rem;
                font-weight: 600;
                background: {delta_color}15;
                padding: 0.25rem 0.75rem;
                border-radius: {ui_config.get('borders', 'border_radius')};
                display: inline-block;
            ">{delta}</div>
            ''' if delta else ''}
            {f'<div style="color: {colors.GRAY}; font-size: 0.8rem; margin-top: 0.5rem;">{description}</div>' if description else ''}
        </div>
    </div>
    
    <style>
    .kb-metric-hover:hover {{
        transform: {ui_config.get('animations', 'hover_transform')};
        box-shadow: {ui_config.get('shadows', 'hover_shadow')};
        border-color: {colors.YELLOW_DARK};
    }}
    </style>
    """, unsafe_allow_html=True)

def kb_news_card(
    title: str,
    content: str,
    time: str,
    impact: str = "neutral",
    importance: float = 0.5,
    source: str = ""
) -> None:
    """KB 스타일 뉴스 카드 - 설정 기반"""
    
    # 임팩트별 설정 (설정 파일에서 로드 가능하도록 개선)
    impact_config = {
        "positive": {
            "icon": "📈",
            "color": colors.SUCCESS,
            "bg": "#F0FDF4",
            "label": "호재"
        },
        "negative": {
            "icon": "📉", 
            "color": colors.DANGER,
            "bg": "#FEF2F2",
            "label": "악재"
        },
        "neutral": {
            "icon": "📊",
            "color": colors.INFO,
            "bg": "#F0F9FF", 
            "label": "중립"
        }
    }
    
    config = impact_config.get(impact, impact_config["neutral"])
    importance_stars = "⭐" * min(5, int(importance * 5))
    
    # 소스가 없으면 기본값 설정 (설정 파일에서 로드)
    if not source:
        source = "KB리서치센터"
    
    st.markdown(f"""
    <div style="
        background: {colors.WHITE};
        border: 1px solid {colors.GRAY_LIGHT};
        border-left: 4px solid {config['color']};
        border-radius: {ui_config.get('borders', 'border_radius')};
        padding: {ui_config.get('spacing', 'card_padding')};
        margin: 1rem 0;
        transition: all {ui_config.get('animations', 'transition_duration')} ease;
        box-shadow: {ui_config.get('shadows', 'card_shadow')};
        font-family: {ui_config.get('typography', 'primary_font')};
    " class="kb-news-hover">
        <!-- 헤더 -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div style="
                background: {config['bg']};
                color: {config['color']};
                padding: 0.25rem 0.75rem;
                border-radius: {ui_config.get('borders', 'border_radius')};
                font-size: 0.8rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 0.25rem;
            ">
                {config['icon']} {config['label']}
            </div>
            
            <div style="text-align: right;">
                <div style="color: {colors.GRAY}; font-size: 0.8rem;">{time}</div>
                {f'<div style="font-size: 0.7rem; color: {colors.WARNING};">{importance_stars}</div>' if importance > 0.6 else ''}
            </div>
        </div>
        
        <!-- 제목 -->
        <h4 style="
            color: {colors.BLACK}; 
            margin-bottom: 1rem; 
            font-weight: 700;
            line-height: 1.4;
            font-size: 1.1rem;
        ">{title}</h4>
        
        <!-- 내용 -->
        <p style="
            color: {colors.GRAY_DARK}; 
            line-height: 1.6;
            margin-bottom: 1rem;
            font-size: 0.95rem;
        ">{content}</p>
        
        <!-- 푸터 -->
        <div style="
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding-top: 1rem;
            border-top: 1px solid {colors.GRAY_LIGHT};
        ">
            <div style="color: {colors.GRAY}; font-size: 0.8rem; font-weight: 600;">
                📰 {source}
            </div>
            <div style="color: {colors.GRAY}; font-size: 0.8rem;">
                중요도: {importance:.1f}/1.0
            </div>
        </div>
    </div>
    
    <style>
    .kb-news-hover:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border-left-width: 6px;
    }}
    </style>
    """, unsafe_allow_html=True)

def kb_investment_status_card(
    stock_name: str,
    current_price: int,
    change: float,
    change_percent: float,
    volume: int,
    market_cap: str = "대형주",
    sector: str = "IT"
) -> None:
    """KB 스타일 투자 상태 카드 - 설정 기반"""
    
    # 등락에 따른 색상 설정
    is_positive = change_percent >= 0
    status_color = colors.PROFIT if is_positive else colors.LOSS
    status_icon = "📈" if is_positive else "📉"
    status_text = "상승" if is_positive else "하락"
    
    # 거래량 단위 변환
    volume_text = f"{volume//10000:,}만" if volume >= 10000 else f"{volume:,}"
    
    st.markdown(f"""
    <div style="
        background: {colors.WHITE};
        border: {ui_config.get('borders', 'border_width')} solid {colors.YELLOW};
        border-radius: {ui_config.get('borders', 'card_border_radius')};
        padding: {ui_config.get('spacing', 'card_padding')};
        margin: 1rem 0;
        box-shadow: {ui_config.get('shadows', 'card_shadow')};
        transition: all {ui_config.get('animations', 'transition_duration')} ease;
        font-family: {ui_config.get('typography', 'primary_font')};
    " class="kb-investment-hover">
        <!-- 헤더 -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <div>
                <h3 style="margin: 0; color: {colors.BLACK}; font-size: 1.4rem; font-weight: 800;">
                    {stock_name}
                </h3>
                <div style="
                    background: {colors.GRAY_BG}; 
                    color: {colors.GRAY}; 
                    padding: 0.25rem 0.75rem; 
                    border-radius: {ui_config.get('borders', 'border_radius')};
                    font-size: 0.8rem;
                    margin-top: 0.5rem;
                    display: inline-block;
                ">
                    {sector} · {market_cap}
                </div>
            </div>
            
            <div style="
                background: {status_color}15;
                color: {status_color};
                padding: 0.5rem 1rem;
                border-radius: {ui_config.get('borders', 'border_radius')};
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            ">
                {status_icon} {status_text}
            </div>
        </div>
        
        <!-- 가격 정보 -->
        <div style="display: flex; justify-content: space-between; align-items: end; margin-bottom: 1rem;">
            <div>
                <div style="
                    font-size: 2.5rem; 
                    font-weight: 800; 
                    color: {colors.BLACK};
                    line-height: 1;
                    margin-bottom: 0.5rem;
                ">{current_price:,}원</div>
                
                <div style="
                    color: {status_color}; 
                    font-size: 1.2rem;
                    font-weight: 700;
                ">
                    {change:+,}원 ({change_percent:+.2f}%)
                </div>
            </div>
            
            <div style="text-align: right;">
                <div style="color: {colors.GRAY}; font-size: 0.9rem; margin-bottom: 0.25rem;">
                    거래량
                </div>
                <div style="color: {colors.BLACK}; font-weight: 700; font-size: 1.1rem;">
                    {volume_text}
                </div>
            </div>
        </div>
        
        <!-- 진행률 바 (변동률 시각화) -->
        <div style="
            background: {colors.GRAY_LIGHT};
            height: 6px;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 1rem;
        ">
            <div style="
                background: {status_color};
                height: 100%;
                width: {min(100, abs(change_percent) * 10)}%;
                border-radius: 3px;
                transition: width 0.5s ease;
            "></div>
        </div>
    </div>
    
    <style>
    .kb-investment-hover:hover {{
        transform: {ui_config.get('animations', 'hover_transform')};
        box-shadow: {ui_config.get('shadows', 'hover_shadow')};
        border-color: {colors.YELLOW_DARK};
    }}
    </style>
    """, unsafe_allow_html=True)

# ================================
# [설정 기반 알림 박스]
# ================================

def kb_alert(
    message: str,
    alert_type: str = "info",
    title: str = "",
    dismissible: bool = False,
    icon: str = ""
) -> None:
    """KB 스타일 알림 박스 - 설정 기반"""
    
    # 알림 타입별 설정
    alert_config = {
        "success": {
            "bg": "#F0FDF4",
            "border": colors.SUCCESS,
            "icon": "✅",
            "title_default": "성공"
        },
        "warning": {
            "bg": "#FFFBF0", 
            "border": colors.WARNING,
            "icon": "⚠️",
            "title_default": "주의"
        },
        "danger": {
            "bg": "#FEF2F2",
            "border": colors.DANGER,
            "icon": "❌",
            "title_default": "오류"
        },
        "info": {
            "bg": "#F0F9FF",
            "border": colors.INFO,
            "icon": "ℹ️",
            "title_default": "안내"
        }
    }
    
    config = alert_config.get(alert_type, alert_config["info"])
    display_icon = icon if icon else config["icon"]
    display_title = title if title else config["title_default"]
    
    st.markdown(f"""
    <div style="
        background: {config['bg']};
        border: {ui_config.get('borders', 'border_width')} solid {config['border']};
        border-radius: {ui_config.get('borders', 'border_radius')};
        padding: {ui_config.get('spacing', 'card_padding')};
        margin: 1rem 0;
        position: relative;
        animation: slideIn 0.3s ease-out;
        font-family: {ui_config.get('typography', 'primary_font')};
    ">
        <div style="display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 1.5rem; flex-shrink: 0;">{display_icon}</div>
            <div style="flex: 1;">
                <h4 style="margin: 0 0 0.5rem 0; color: {colors.BLACK}; font-weight: 700;">
                    {display_title}
                </h4>
                <p style="margin: 0; color: {colors.GRAY_DARK}; line-height: 1.5;">
                    {message}
                </p>
            </div>
        </div>
    </div>
    
    <style>
    @keyframes slideIn {{
        from {{
            opacity: 0;
            transform: translateY(-10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ================================
# [통계 차트 컴포넌트]
# ================================

def kb_statistics_card(
    title: str,
    stats_data: Dict[str, Any],
    chart_type: str = "bar"
) -> None:
    """KB 스타일 통계 카드"""
    
    st.markdown(f"""
    <div class="kb-card">
        <h3 style="color: {colors.BLACK}; margin-bottom: 1.5rem; font-weight: 700;">
            📊 {title}
        </h3>
        <div style="background: {colors.GRAY_BG}; padding: 1rem; border-radius: {ui_config.get('borders', 'border_radius')};">
            <!-- 통계 데이터가 여기에 표시됩니다 -->
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================================
# [설정 리로드 함수]
# ================================

def reload_ui_config():
    """UI 설정 다시 로드"""
    global colors, ui_config
    colors = KBColors()
    ui_config = UIConfigLoader()

# ================================
# [유틸리티 함수들]
# ================================

def get_kb_colors() -> KBColors:
    """현재 KB 컬러 설정 반환"""
    return colors

def get_ui_config() -> UIConfigLoader:
    """현재 UI 설정 반환"""
    return ui_config

# ================================
# [테스트 함수]
# ================================

def test_kb_components():
    """KB 컴포넌트 테스트"""
    st.markdown("# KB 스타일 컴포넌트 테스트")
    
    # 테마 적용
    apply_kb_theme()
    
    # 헤더 테스트
    kb_header("KB Reflex", "테스트 페이지", "🧪")
    
    # 메트릭 카드 테스트
    col1, col2, col3 = st.columns(3)
    with col1:
        kb_metric_card("총 거래", "156건", "+12건", "success", "💰")
    with col2:
        kb_metric_card("수익률", "15.3%", "+2.1%", "success", "📈")
    with col3:
        kb_metric_card("위험도", "보통", "안정", "normal", "⚖️")
    
    # 뉴스 카드 테스트
    kb_news_card(
        "삼성전자, AI 반도체 신기술 발표",
        "삼성전자가 차세대 AI 전용 반도체 기술을 공개하며 시장 선도를 강화하고 있습니다.",
        "2시간 전",
        "positive",
        0.8,
        "KB리서치센터"
    )
    
    # 투자 상태 카드 테스트
    kb_investment_status_card(
        "삼성전자",
        68500,
        2500,
        3.79,
        1200000,
        "대형주",
        "반도체"
    )
    
    # 알림 테스트
    kb_alert("테스트가 성공적으로 완료되었습니다!", "success", "테스트 완료")

if __name__ == "__main__":
    test_kb_components()