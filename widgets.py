#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB Reflex - 재사용 가능한 위젯 컴포넌트들
KB AI CHALLENGE 2024

🧩 재사용 가능한 UI 컴포넌트들:
1. 투자 통계 차트 위젯
2. 거래 내역 테이블 위젯  
3. AI 분석 결과 위젯
4. 투자 원칙 체크리스트 위젯
5. 설정 파일 기반 동적 컴포넌트들
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json
from pathlib import Path
from components.kb_style import get_kb_colors, get_ui_config, kb_metric_card, kb_alert, kb_news_card

# ================================
# [통계 차트 위젯들]
# ================================

def render_performance_overview(basic_stats: Dict[str, Any], height: int = 400) -> None:
    """투자 성과 개요 차트"""
    
    if not basic_stats or basic_stats.get("total_trades", 0) == 0:
        kb_alert("아직 거래 데이터가 없습니다.", "info")
        return
    
    colors = get_kb_colors()
    
    # 성과 지표들
    metrics = {
        "총 거래": basic_stats.get("total_trades", 0),
        "성공 거래": basic_stats.get("profitable_trades", 0),
        "실패 거래": basic_stats.get("total_trades", 0) - basic_stats.get("profitable_trades", 0)
    }
    
    # 도넛 차트
    fig = go.Figure(data=[
        go.Pie(
            labels=["성공 거래", "실패 거래"],
            values=[metrics["성공 거래"], metrics["실패 거래"]],
            hole=0.6,
            colors=[colors.SUCCESS, colors.DANGER],
            textinfo='label+percent',
            textposition='outside'
        )
    ])
    
    # 중앙에 성공률 표시
    success_rate = basic_stats.get("success_rate", 0)
    fig.add_annotation(
        text=f"<b>{success_rate:.1f}%</b><br>성공률",
        x=0.5, y=0.5,
        font_size=20,
        font_color=colors.BLACK,
        showarrow=False
    )
    
    fig.update_layout(
        title="<b>투자 성과 개요</b>",
        title_x=0.5,
        height=height,
        showlegend=True,
        font_family=get_ui_config().get("typography", "primary_font")
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_emotion_analysis_chart(emotion_stats: Dict[str, Any], height: int = 400) -> None:
    """감정별 투자 성과 분석 차트"""
    
    if not emotion_stats or not emotion_stats.get("emotion_counts"):
        kb_alert("감정 분석 데이터가 없습니다.", "info")
        return
    
    colors = get_kb_colors()
    
    # 감정별 데이터 준비
    emotions = list(emotion_stats["emotion_counts"].keys())
    counts = list(emotion_stats["emotion_counts"].values())
    returns = [emotion_stats["emotion_avg_returns"].get(emotion, 0) for emotion in emotions]
    
    # 색상 매핑 (수익률 기반)
    color_scale = []
    for ret in returns:
        if ret > 5:
            color_scale.append(colors.SUCCESS)
        elif ret > 0:
            color_scale.append(colors.WARNING)
        else:
            color_scale.append(colors.DANGER)
    
    # 병합 차트 (거래 횟수 + 수익률)
    fig = go.Figure()
    
    # 거래 횟수 바 차트
    fig.add_trace(go.Bar(
        name='거래 횟수',
        x=emotions,
        y=counts,
        marker_color=colors.YELLOW,
        opacity=0.7,
        yaxis='y',
        text=counts,
        textposition='auto'
    ))
    
    # 평균 수익률 라인 차트
    fig.add_trace(go.Scatter(
        name='평균 수익률 (%)',
        x=emotions,
        y=returns,
        mode='lines+markers',
        line=dict(color=colors.BLACK, width=3),
        marker=dict(size=10, color=color_scale),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="<b>감정별 거래 패턴 및 성과</b>",
        title_x=0.5,
        height=height,
        xaxis_title="감정 상태",
        yaxis=dict(title="거래 횟수", side='left'),
        yaxis2=dict(title="평균 수익률 (%)", side='right', overlaying='y'),
        hovermode='x unified',
        font_family=get_ui_config().get("typography", "primary_font")
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_monthly_performance_trend(user_trades: List[Dict], height: int = 400) -> None:
    """월별 투자 성과 트렌드"""
    
    if not user_trades:
        kb_alert("거래 데이터가 없습니다.", "info")
        return
    
    colors = get_kb_colors()
    
    # 월별 데이터 집계
    monthly_data = {}
    for trade in user_trades:
        try:
            date = datetime.strptime(trade["date"], "%Y-%m-%d")
            month_key = date.strftime("%Y-%m")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {"returns": [], "count": 0}
            
            monthly_data[month_key]["returns"].append(trade.get("result", 0))
            monthly_data[month_key]["count"] += 1
        except:
            continue
    
    if not monthly_data:
        kb_alert("날짜 데이터를 파싱할 수 없습니다.", "warning")
        return
    
    # 데이터 정리
    months = sorted(monthly_data.keys())
    avg_returns = [np.mean(monthly_data[month]["returns"]) for month in months]
    trade_counts = [monthly_data[month]["count"] for month in months]
    
    # 누적 수익률 계산
    cumulative_returns = np.cumsum(avg_returns)
    
    fig = go.Figure()
    
    # 월별 수익률 바 차트
    colors_bars = [colors.SUCCESS if ret > 0 else colors.DANGER for ret in avg_returns]
    fig.add_trace(go.Bar(
        name='월별 평균 수익률',
        x=months,
        y=avg_returns,
        marker_color=colors_bars,
        opacity=0.7,
        text=[f"{ret:+.1f}%" for ret in avg_returns],
        textposition='auto'
    ))
    
    # 누적 수익률 라인
    fig.add_trace(go.Scatter(
        name='누적 수익률',
        x=months,
        y=cumulative_returns,
        mode='lines+markers',
        line=dict(color=colors.BLACK, width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="<b>월별 투자 성과 트렌드</b>",
        title_x=0.5,
        height=height,
        xaxis_title="기간",
        yaxis=dict(title="월별 평균 수익률 (%)", side='left'),
        yaxis2=dict(title="누적 수익률 (%)", side='right', overlaying='y'),
        hovermode='x unified',
        font_family=get_ui_config().get("typography", "primary_font")
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_stock_performance_radar(user_trades: List[Dict], top_n: int = 6) -> None:
    """주요 종목별 성과 레이더 차트"""
    
    if not user_trades:
        kb_alert("거래 데이터가 없습니다.", "info")
        return
    
    colors = get_kb_colors()
    
    # 종목별 데이터 집계
    stock_data = {}
    for trade in user_trades:
        stock = trade.get("stock", "")
        if not stock:
            continue
            
        if stock not in stock_data:
            stock_data[stock] = {"returns": [], "count": 0, "amounts": []}
        
        stock_data[stock]["returns"].append(trade.get("result", 0))
        stock_data[stock]["count"] += 1
        stock_data[stock]["amounts"].append(trade.get("amount", 0))
    
    # 상위 N개 종목 선택
    top_stocks = sorted(stock_data.items(), 
                       key=lambda x: x[1]["count"], 
                       reverse=True)[:top_n]
    
    if not top_stocks:
        kb_alert("종목별 데이터가 충분하지 않습니다.", "warning")
        return
    
    # 레이더 차트 데이터 준비
    categories = ['평균 수익률', '거래 횟수', '성공률', '총 투자금액', '변동성', '일관성']
    
    fig = go.Figure()
    
    for stock, data in top_stocks:
        returns = data["returns"]
        avg_return = np.mean(returns)
        success_rate = len([r for r in returns if r > 0]) / len(returns) * 100
        volatility = np.std(returns) if len(returns) > 1 else 0
        consistency = 100 - volatility  # 변동성이 낮을수록 일관성 높음
        total_amount = sum(data["amounts"])
        
        # 정규화 (0-100 스케일)
        values = [
            max(0, min(100, avg_return + 50)),  # 수익률 (-50% ~ +50% -> 0~100)
            min(100, data["count"] * 10),       # 거래횟수 (10회 = 100점)
            success_rate,                       # 성공률 (그대로)
            min(100, total_amount / 10000000 * 100),  # 투자금액 (1억 = 100점)
            max(0, min(100, 100 - volatility * 2)),    # 변동성 (낮을수록 좋음)
            max(0, min(100, consistency))       # 일관성
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=stock,
            opacity=0.6
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="<b>주요 종목별 종합 성과</b>",
        title_x=0.5,
        height=500,
        font_family=get_ui_config().get("typography", "primary_font")
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ================================
# [거래 내역 위젯들]
# ================================

def render_trade_history_table(user_trades: List[Dict], max_rows: int = 10) -> None:
    """거래 내역 테이블"""
    
    if not user_trades:
        kb_alert("거래 내역이 없습니다.", "info")
        return
    
    # 최근 거래부터 표시
    recent_trades = sorted(user_trades, key=lambda x: x.get("date", ""), reverse=True)[:max_rows]
    
    # DataFrame 생성
    df_data = []
    for trade in recent_trades:
        df_data.append({
            "날짜": trade.get("date", ""),
            "종목": trade.get("stock", ""),
            "행동": trade.get("action", ""),
            "금액": f"{trade.get('amount', 0):,}원",
            "감정": trade.get("emotion", ""),
            "수익률": f"{trade.get('result', 0):+.1f}%",
            "이유": trade.get("reason", "")[:30] + "..." if len(trade.get("reason", "")) > 30 else trade.get("reason", "")
        })
    
    df = pd.DataFrame(df_data)
    
    # 스타일링 적용
    def style_dataframe(df):
        colors = get_kb_colors()
        
        def highlight_profit(val):
            if "+" in str(val):
                return f'background-color: {colors.SUCCESS}20; color: {colors.SUCCESS};'
            elif "-" in str(val):
                return f'background-color: {colors.DANGER}20; color: {colors.DANGER};'
            return ''
        
        return df.style.applymap(highlight_profit, subset=['수익률'])
    
    st.markdown("### 📊 최근 거래 내역")
    st.dataframe(style_dataframe(df), use_container_width=True, height=400)

def render_trade_summary_cards(user_trades: List[Dict]) -> None:
    """거래 요약 카드들"""
    
    if not user_trades:
        return
    
    # 요약 통계 계산
    total_trades = len(user_trades)
    profitable_trades = len([t for t in user_trades if t.get("result", 0) > 0])
    total_return = sum(t.get("result", 0) for t in user_trades)
    avg_return = total_return / total_trades if total_trades > 0 else 0
    
    best_trade = max(user_trades, key=lambda x: x.get("result", 0))
    worst_trade = min(user_trades, key=lambda x: x.get("result", 0))
    
    # 카드 배치
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        kb_metric_card(
            title="총 거래",
            value=f"{total_trades}건",
            icon="💼"
        )
    
    with col2:
        success_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        delta_type = "success" if success_rate > 50 else "danger"
        kb_metric_card(
            title="성공률",
            value=f"{success_rate:.1f}%",
            delta=f"{profitable_trades}/{total_trades}",
            delta_type=delta_type,
            icon="🎯"
        )
    
    with col3:
        delta_type = "success" if avg_return > 0 else "danger"
        kb_metric_card(
            title="평균 수익률",
            value=f"{avg_return:+.1f}%",
            delta_type=delta_type,
            icon="📈"
        )
    
    with col4:
        kb_metric_card(
            title="최고 수익",
            value=f"{best_trade.get('result', 0):+.1f}%",
            description=best_trade.get('stock', ''),
            delta_type="success",
            icon="🏆"
        )

# ================================
# [AI 분석 결과 위젯들]
# ================================

def render_ai_analysis_summary(coaching_result: Any) -> None:
    """AI 분석 결과 요약"""
    
    if not coaching_result:
        kb_alert("AI 분석 결과가 없습니다.", "warning")
        return
    
    colors = get_kb_colors()
    
    # 위험도 및 신뢰도 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_level = coaching_result.risk_level
        risk_color = "danger" if risk_level == "높음" else "warning" if risk_level == "보통" else "success"
        kb_metric_card(
            title="위험도",
            value=risk_level,
            delta_type=risk_color,
            icon="⚠️"
        )
    
    with col2:
        confidence = coaching_result.confidence
        confidence_color = "success" if confidence > 0.7 else "warning" if confidence > 0.4 else "danger"
        kb_metric_card(
            title="AI 신뢰도",
            value=f"{confidence:.0%}",
            delta_type=confidence_color,
            icon="🤖"
        )
    
    with col3:
        emotion = coaching_result.emotion_state.get("primary_emotion", "중립")
        emotion_icon = "😰" if emotion in ["불안", "두려움"] else "🤑" if emotion == "욕심" else "😊"
        kb_metric_card(
            title="감정 상태",
            value=emotion,
            icon=emotion_icon
        )

def render_risk_factors_chart(risk_factors: List[str]) -> None:
    """위험 요인 차트"""
    
    if not risk_factors:
        kb_alert("위험 요인이 감지되지 않았습니다.", "success")
        return
    
    colors = get_kb_colors()
    
    # 위험 요인 분류
    risk_categories = {
        "감정적": 0,
        "시장": 0,
        "패턴": 0,
        "기타": 0
    }
    
    for factor in risk_factors:
        if any(keyword in factor for keyword in ["감정", "불안", "욕심", "FOMO"]):
            risk_categories["감정적"] += 1
        elif any(keyword in factor for keyword in ["시장", "변동성", "주가"]):
            risk_categories["시장"] += 1
        elif any(keyword in factor for keyword in ["패턴", "과거", "경험"]):
            risk_categories["패턴"] += 1
        else:
            risk_categories["기타"] += 1
    
    # 도넛 차트
    categories = list(risk_categories.keys())
    values = list(risk_categories.values())
    
    # 0인 값들 제거
    non_zero_data = [(cat, val) for cat, val in zip(categories, values) if val > 0]
    
    if not non_zero_data:
        return
    
    categories, values = zip(*non_zero_data)
    
    fig = go.Figure(data=[
        go.Pie(
            labels=categories,
            values=values,
            hole=0.4,
            colors=[colors.DANGER, colors.WARNING, colors.INFO, colors.GRAY],
            textinfo='label+value',
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="<b>위험 요인 분석</b>",
        title_x=0.5,
        height=400,
        font_family=get_ui_config().get("typography", "primary_font")
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ================================
# [투자 원칙 위젯들]
# ================================

def render_investment_principles_checklist(principles: List[str], key_prefix: str = "principle") -> Dict[str, bool]:
    """투자 원칙 체크리스트"""
    
    if not principles:
        kb_alert("투자 원칙이 설정되지 않았습니다.", "info")
        return {}
    
    st.markdown("### ✅ 투자 원칙 체크리스트")
    st.markdown("*투자 전에 다음 원칙들을 확인해보세요:*")
    
    checks = {}
    
    with st.form(f"{key_prefix}_checklist"):
        for i, principle in enumerate(principles):
            checks[f"check_{i}"] = st.checkbox(
                principle,
                key=f"{key_prefix}_check_{i}"
            )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "✅ 체크 완료",
                use_container_width=True
            )
        
        if submitted:
            checked_count = sum(checks.values())
            total_count = len(checks)
            percentage = (checked_count / total_count * 100) if total_count > 0 else 0
            
            if percentage == 100:
                kb_alert("🎉 모든 원칙을 확인했습니다! 현명한 투자하세요!", "success")
            elif percentage >= 70:
                kb_alert("👍 대부분의 원칙을 확인했습니다. 조금 더 신중하게 검토해보세요.", "warning")
            else:
                kb_alert("⚠️ 더 많은 원칙들을 검토해보시기 바랍니다.", "danger")
            
            # 진행률 표시
            progress = st.progress(percentage / 100)
            st.caption(f"체크 완료율: {percentage:.0f}% ({checked_count}/{total_count})")
    
    return checks

def render_principle_performance_analysis(user_trades: List[Dict], principles: List[str]) -> None:
    """원칙 준수 성과 분석"""
    
    if not user_trades or not principles:
        return
    
    st.markdown("### 📊 투자 원칙 준수 분석")
    
    # 원칙별 키워드 매핑 (설정 파일에서 로드 가능)
    principle_keywords = {
        "분산투자": ["분산", "여러", "다양"],
        "손절": ["손절", "stop", "loss"],
        "익절": ["익절", "수익", "profit"],
        "감정": ["감정", "냉정", "객관"],
        "분석": ["분석", "연구", "공부"]
    }
    
    # 각 거래에서 원칙 준수 여부 분석
    principle_compliance = {principle: {"followed": 0, "not_followed": 0, "returns": []} 
                          for principle in principles}
    
    for trade in user_trades:
        reason = trade.get("reason", "").lower()
        trade_return = trade.get("result", 0)
        
        for principle in principles:
            # 원칙과 관련된 키워드가 있는지 확인
            keywords = []
            for key, words in principle_keywords.items():
                if key in principle.lower():
                    keywords = words
                    break
            
            if any(keyword in reason for keyword in keywords):
                principle_compliance[principle]["followed"] += 1
                principle_compliance[principle]["returns"].append(trade_return)
            else:
                principle_compliance[principle]["not_followed"] += 1
    
    # 결과 시각화
    compliance_data = []
    for principle, data in principle_compliance.items():
        total = data["followed"] + data["not_followed"]
        if total > 0:
            compliance_rate = data["followed"] / total * 100
            avg_return = np.mean(data["returns"]) if data["returns"] else 0
            
            compliance_data.append({
                "원칙": principle[:20] + "..." if len(principle) > 20 else principle,
                "준수율": compliance_rate,
                "평균수익률": avg_return
            })
    
    if compliance_data:
        df = pd.DataFrame(compliance_data)
        
        fig = go.Figure()
        
        # 준수율 바 차트
        fig.add_trace(go.Bar(
            name='원칙 준수율 (%)',
            x=df['원칙'],
            y=df['준수율'],
            marker_color=get_kb_colors().YELLOW,
            opacity=0.7,
            yaxis='y'
        ))
        
        # 평균 수익률 라인
        fig.add_trace(go.Scatter(
            name='평균 수익률 (%)',
            x=df['원칙'],
            y=df['평균수익률'],
            mode='lines+markers',
            line=dict(color=get_kb_colors().BLACK, width=3),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="원칙 준수율 vs 투자 성과",
            xaxis_title="투자 원칙",
            yaxis=dict(title="준수율 (%)", side='left'),
            yaxis2=dict(title="평균 수익률 (%)", side='right', overlaying='y'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ================================
# [대시보드 레이아웃 위젯들]
# ================================

def render_dashboard_overview(user_data: Dict, user_trades: List[Dict], 
                            coaching_results: Optional[Any] = None) -> None:
    """대시보드 메인 개요"""
    
    st.markdown("### 📊 투자 대시보드")
    
    # 상단 메트릭 카드들
    if user_trades:
        render_trade_summary_cards(user_trades)
    
    # 주요 차트들 (2열 레이아웃)
    col1, col2 = st.columns(2)
    
    with col1:
        if user_trades:
            # 기본 통계 계산
            basic_stats = {
                "total_trades": len(user_trades),
                "profitable_trades": len([t for t in user_trades if t.get("result", 0) > 0]),
                "success_rate": 0
            }
            basic_stats["success_rate"] = (basic_stats["profitable_trades"] / basic_stats["total_trades"] * 100) if basic_stats["total_trades"] > 0 else 0
            
            render_performance_overview(basic_stats)
    
    with col2:
        if user_trades:
            # 감정 통계 계산
            emotion_counts = {}
            emotion_returns = {}
            
            for trade in user_trades:
                emotion = trade.get("emotion", "중립")
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                
                if emotion not in emotion_returns:
                    emotion_returns[emotion] = []
                emotion_returns[emotion].append(trade.get("result", 0))
            
            emotion_avg_returns = {}
            for emotion, returns in emotion_returns.items():
                emotion_avg_returns[emotion] = np.mean(returns)
            
            emotion_stats = {
                "emotion_counts": emotion_counts,
                "emotion_avg_returns": emotion_avg_returns
            }
            
            render_emotion_analysis_chart(emotion_stats)
    
    # AI 분석 결과 (있는 경우)
    if coaching_results:
        st.markdown("---")
        render_ai_analysis_summary(coaching_results)

def render_settings_panel(config_dir: str = "config") -> None:
    """설정 패널"""
    
    st.markdown("### ⚙️ 시스템 설정")
    
    config_path = Path(config_dir)
    
    # 설정 파일 목록
    config_files = list(config_path.glob("*.json")) if config_path.exists() else []
    
    if not config_files:
        kb_alert("설정 파일이 없습니다.", "warning")
        return
    
    # 설정 파일 정보
    st.markdown("#### 📁 설정 파일 상태")
    
    for config_file in config_files:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            file_size = config_file.stat().st_size
            modified_time = datetime.fromtimestamp(config_file.stat().st_mtime)
            
            with st.expander(f"📄 {config_file.name}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**크기:** {file_size:,} bytes")
                    st.write(f"**수정일:** {modified_time.strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    st.write(f"**항목 수:** {len(config_data)} 개")
                    if st.button(f"🔄 {config_file.name} 다시 로드", key=f"reload_{config_file.name}"):
                        st.success(f"{config_file.name} 설정을 다시 로드했습니다.")
                        st.rerun()
                
                # 설정 내용 미리보기
                st.json(config_data, expanded=False)
        
        except Exception as e:
            st.error(f"{config_file.name} 로드 실패: {e}")

# ================================
# [유틸리티 함수들]
# ================================

def format_currency(amount: Union[int, float]) -> str:
    """통화 포맷팅"""
    if amount >= 100000000:  # 1억 이상
        return f"{amount/100000000:.1f}억원"
    elif amount >= 10000:    # 1만 이상
        return f"{amount/10000:.0f}만원"
    else:
        return f"{amount:,.0f}원"

def calculate_portfolio_diversity(user_trades: List[Dict]) -> Dict[str, Any]:
    """포트폴리오 다양성 계산"""
    if not user_trades:
        return {"diversity_score": 0, "unique_stocks": 0, "sectors": []}
    
    # 고유 종목 수
    unique_stocks = len(set(trade.get("stock", "") for trade in user_trades))
    
    # 다양성 점수 (간단한 계산)
    total_trades = len(user_trades)
    diversity_score = min(100, (unique_stocks / total_trades) * 100)
    
    return {
        "diversity_score": diversity_score,
        "unique_stocks": unique_stocks,
        "total_trades": total_trades
    }

def get_trading_insights(user_trades: List[Dict]) -> List[str]:
    """거래 패턴 인사이트 생성"""
    insights = []
    
    if not user_trades:
        return ["아직 거래 데이터가 충분하지 않습니다."]
    
    # 수익률 분석
    returns = [trade.get("result", 0) for trade in user_trades]
    avg_return = np.mean(returns)
    
    if avg_return > 10:
        insights.append("🎉 평균 수익률이 매우 우수합니다!")
    elif avg_return > 0:
        insights.append("👍 전반적으로 수익을 내고 있습니다.")
    else:
        insights.append("💡 손실을 줄이는 전략이 필요합니다.")
    
    # 거래 빈도 분석
    if len(user_trades) > 50:
        insights.append("⚠️ 거래가 너무 빈번할 수 있습니다. 장기 투자를 고려해보세요.")
    
    # 감정 패턴 분석
    emotions = [trade.get("emotion", "") for trade in user_trades]
    negative_emotions = ["불안", "두려움", "후회", "FOMO"]
    negative_count = sum(1 for emotion in emotions if emotion in negative_emotions)
    
    if negative_count > len(emotions) * 0.3:
        insights.append("😰 감정적 투자 비중이 높습니다. 더 객관적인 분석이 필요합니다.")
    
    return insights

# ================================
# [테스트 함수]
# ================================

def test_widgets():
    """위젯 테스트"""
    st.title("🧪 위젯 테스트")
    
    # 더미 데이터
    dummy_trades = [
        {"date": "2024-08-01", "stock": "삼성전자", "action": "매수", "amount": 1000000, 
         "emotion": "확신", "result": 5.2, "reason": "AI 반도체 호재"},
        {"date": "2024-07-15", "stock": "NAVER", "action": "매도", "amount": 800000,
         "emotion": "불안", "result": -3.1, "reason": "규제 우려"},
        {"date": "2024-07-01", "stock": "카카오", "action": "매수", "amount": 600000,
         "emotion": "욕심", "result": 8.7, "reason": "급등 추격"}
    ]
    
    # 기본 통계
    basic_stats = {
        "total_trades": 3,
        "profitable_trades": 2, 
        "success_rate": 66.7
    }
    
    # 위젯 테스트
    render_trade_summary_cards(dummy_trades)
    render_performance_overview(basic_stats)
    render_trade_history_table(dummy_trades)

if __name__ == "__main__":
    test_widgets()