# trading_service.py

__all__ = [
    "format_currency_smart",
    "calculate_expected_pnl",
    "execute_trade",
    "add_trade_to_history",
    "calculate_portfolio_value",
    "get_portfolio_performance"
]

import pandas as pd
from datetime import datetime
import streamlit as st

def format_currency_smart(amount):
    """스마트 통화 포맷팅 - 억/만 단위 자동 변환"""
    try:
        if pd.isna(amount) or amount is None:
            return "0원"
            
        amount = int(float(amount))
        
        if amount >= 100_000_000:  # 1억 이상
            eok = amount // 100_000_000
            man = (amount % 100_000_000) // 10_000
            return f"{eok}억 {man:,}만원" if man > 0 else f"{eok}억원"
        elif amount >= 10_000:  # 1만 이상
            man = amount // 10_000
            remainder = amount % 10_000
            return f"{man:,}만 {remainder:,}원" if remainder > 0 else f"{man:,}만원"
        else:
            return f"{amount:,}원"
    except (ValueError, TypeError):
        return f"{amount:,}원" if amount else "0원"

def calculate_expected_pnl(stock_name, trade_type, quantity, price, portfolio):
    """매도 전 예상 손익 계산"""
    try:
        if not stock_name or not trade_type or not quantity or not price:
            return None
        if trade_type != "매도" or stock_name not in portfolio:
            return None
        
        holdings = portfolio[stock_name]
        if holdings.get('shares', 0) < quantity:
            return None
        
        avg_buy_price = holdings.get('avg_price', 0)
        if avg_buy_price <= 0:
            return None
            
        expected_revenue = quantity * price
        invested_amount = quantity * avg_buy_price
        expected_pnl = expected_revenue - invested_amount
        pnl_percentage = (expected_pnl / invested_amount) * 100 if invested_amount > 0 else 0
        
        return {
            'expected_pnl': expected_pnl,
            'pnl_percentage': pnl_percentage,
            'avg_buy_price': avg_buy_price,
            'sell_price': price,
            'quantity': quantity
        }
    except Exception as exc:
        st.error(f"예상 손익 계산 중 오류: {exc}")
        return None

def execute_trade(stock_name, trade_type, quantity, price, portfolio, cash):
    """거래 실행 함수"""
    _portfolio = portfolio.copy() if isinstance(portfolio, dict) else {}
    _cash = float(cash) if cash is not None else 0.0
    
    try:
        if not all([stock_name, trade_type, quantity, price]):
            return False, "❌ 잘못된 거래 정보입니다.", None, _portfolio, _cash
        if quantity <= 0 or price <= 0:
            return False, "❌ 수량과 가격은 0보다 커야 합니다.", None, _portfolio, _cash
        if trade_type not in ["매수", "매도"]:
            return False, "❌ 거래 유형은 매수 또는 매도여야 합니다.", None, _portfolio, _cash
        
        total_amount = quantity * price
        
        if trade_type == "매수":
            if _cash >= total_amount:
                _cash -= total_amount
                if stock_name in _portfolio:
                    existing_shares = _portfolio[stock_name].get('shares', 0)
                    existing_avg_price = _portfolio[stock_name].get('avg_price', 0)
                    if existing_shares > 0 and existing_avg_price > 0:
                        new_avg_price = (
                            existing_shares * existing_avg_price + quantity * price
                        ) / (existing_shares + quantity)
                    else:
                        new_avg_price = price
                    _portfolio[stock_name]['shares'] = existing_shares + quantity
                    _portfolio[stock_name]['avg_price'] = new_avg_price
                else:
                    _portfolio[stock_name] = {'shares': quantity, 'avg_price': price}
                return True, f"✅ {stock_name} {quantity:,}주를 {format_currency_smart(price)}에 매수했습니다.", None, _portfolio, _cash
            else:
                needed = total_amount - _cash
                return False, f"❌ 현금이 {format_currency_smart(needed)} 부족합니다.", None, _portfolio, _cash
        
        elif trade_type == "매도":
            if stock_name in _portfolio and _portfolio[stock_name].get('shares', 0) >= quantity:
                avg_buy_price = _portfolio[stock_name].get('avg_price', 0)
                _cash += total_amount
                _portfolio[stock_name]['shares'] -= quantity
                if _portfolio[stock_name]['shares'] == 0:
                    del _portfolio[stock_name]
                
                loss_info = None
                if price < avg_buy_price:
                    loss_amount = (avg_buy_price - price) * quantity
                    loss_percentage = ((price - avg_buy_price) / avg_buy_price) * 100
                    loss_info = {
                        'stock_name': stock_name,
                        'loss_amount': loss_amount,
                        'loss_percentage': loss_percentage,
                        'buy_price': avg_buy_price,
                        'sell_price': price,
                        'quantity': quantity
                    }
                return True, f"✅ {stock_name} {quantity:,}주를 {format_currency_smart(price)}에 매도했습니다.", loss_info, _portfolio, _cash
            else:
                if stock_name not in _portfolio:
                    return False, f"❌ {stock_name}을(를) 보유하고 있지 않습니다.", None, _portfolio, _cash
                else:
                    current_shares = _portfolio[stock_name].get('shares', 0)
                    shortage = quantity - current_shares
                    return False, f"❌ {shortage:,}주가 부족합니다. (보유: {current_shares:,}주)", None, _portfolio, _cash
        
        return False, "❌ 알 수 없는 오류가 발생했습니다.", None, _portfolio, _cash
    except Exception as exc:
        error_msg = f"❌ 거래 실행 중 오류: {str(exc)}"
        return False, error_msg, None, _portfolio, _cash

def add_trade_to_history(history, stock_name, trade_type, quantity, price):
    """거래 내역 추가"""
    try:
        if not all([stock_name, trade_type, quantity, price]):
            return history
        total_amount = quantity * price
        new_trade = pd.DataFrame({
            '거래일시': [datetime.now()],
            '종목명': [stock_name],
            '거래구분': [trade_type],
            '수량': [quantity],
            '가격': [price],
            '금액': [total_amount]
        })
        return new_trade if history.empty else pd.concat([history, new_trade], ignore_index=True)
    except Exception as exc:
        st.error(f"거래 내역 추가 중 오류: {exc}")
        return history

def calculate_portfolio_value(portfolio, market_data):
    """포트폴리오 가치 계산"""
    try:
        if not portfolio or not market_data:
            return 0
        total_value = 0
        for stock_name, holdings in portfolio.items():
            if not isinstance(holdings, dict):
                continue
            shares = holdings.get('shares', 0)
            if shares <= 0:
                continue
            current_price = market_data.get(stock_name, {}).get('price', 50000)
            total_value += shares * current_price
        return total_value
    except Exception as exc:
        st.error(f"포트폴리오 가치 계산 중 오류: {exc}")
        return 0

def get_portfolio_performance(portfolio, market_data):
    """포트폴리오 성과 계산"""
    try:
        if not portfolio or not market_data:
            return pd.DataFrame()
        portfolio_data = []
        for stock_name, holdings in portfolio.items():
            if not isinstance(holdings, dict):
                continue
            shares = holdings.get('shares', 0)
            avg_price = holdings.get('avg_price', 0)
            if shares <= 0 or avg_price <= 0:
                continue
            current_price = market_data.get(stock_name, {}).get('price', 50000)
            current_value = shares * current_price
            invested_value = shares * avg_price
            pnl = current_value - invested_value
            pnl_pct = (pnl / invested_value) * 100 if invested_value > 0 else 0
            pnl_display = (
                f"{format_currency_smart(abs(pnl))} (+{pnl_pct:.1f}%)"
                if pnl >= 0 else
                f"-{format_currency_smart(abs(pnl))} ({pnl_pct:.1f}%)"
            )
            portfolio_data.append({
                '종목명': stock_name,
                '보유수량': f"{shares:,}주",
                '평균매수가': format_currency_smart(avg_price),
                '현재가': format_currency_smart(current_price),
                '평가금액': format_currency_smart(current_value),
                '평가손익': pnl_display
            })
        return pd.DataFrame(portfolio_data)
    except Exception as exc:
        st.error(f"포트폴리오 성과 계산 중 오류: {exc}")
        return pd.DataFrame()

# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("Trading Service Functions Available:")
    for func in __all__:
        print(f"- {func}")
    print(f"Test format_currency_smart: {format_currency_smart(1500000)}")
    print("All functions loaded successfully!")
