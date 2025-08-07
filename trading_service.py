# trading_service.py
import pandas as pd
from datetime import datetime
import streamlit as st

def execute_trade(stock_name, trade_type, quantity, price, portfolio, cash):
    """거래 실행 함수"""
    total_amount = quantity * price
    
    if trade_type == "매수":
        if cash >= total_amount:
            cash -= total_amount
            
            if stock_name in portfolio:
                # 기존 보유 종목의 평균 단가 계산
                existing_shares = portfolio[stock_name]['shares']
                existing_avg_price = portfolio[stock_name]['avg_price']
                new_avg_price = (existing_shares * existing_avg_price + quantity * price) / (existing_shares + quantity)
                
                portfolio[stock_name]['shares'] += quantity
                portfolio[stock_name]['avg_price'] = new_avg_price
            else:
                portfolio[stock_name] = {
                    'shares': quantity,
                    'avg_price': price
                }
            
            return True, f"✅ {stock_name} {quantity}주를 {price:,}원에 매수했습니다.", None, portfolio, cash
        else:
            return False, "❌ 현금이 부족합니다.", None, portfolio, cash
    
    elif trade_type == "매도":
        if stock_name in portfolio and portfolio[stock_name]['shares'] >= quantity:
            avg_buy_price = portfolio[stock_name]['avg_price']
            cash += total_amount
            portfolio[stock_name]['shares'] -= quantity
            
            if portfolio[stock_name]['shares'] == 0:
                del portfolio[stock_name]
            
            # 손실 체크 (매도가 < 평균 매수가)
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
            
            return True, f"✅ {stock_name} {quantity}주를 {price:,}원에 매도했습니다.", loss_info, portfolio, cash
        else:
            return False, "❌ 보유 수량이 부족합니다.", None, portfolio, cash
    
    return False, "❌ 알 수 없는 오류가 발생했습니다.", None, portfolio, cash

def add_trade_to_history(history, stock_name, trade_type, quantity, price):
    """거래 내역 추가"""
    total_amount = quantity * price
    
    new_trade = pd.DataFrame({
        '거래일시': [datetime.now()],
        '종목명': [stock_name],
        '거래구분': [trade_type],
        '수량': [quantity],
        '가격': [price],
        '금액': [total_amount]
    })
    
    if history.empty:
        return new_trade
    else:
        return pd.concat([history, new_trade], ignore_index=True)

def calculate_portfolio_value(portfolio, market_data):
    """포트폴리오 가치 계산"""
    total_value = 0
    
    for stock_name, holdings in portfolio.items():
        current_price = market_data.get(stock_name, {'price': 50000})['price']
        total_value += holdings['shares'] * current_price
    
    return total_value

def get_portfolio_performance(portfolio, market_data):
    """포트폴리오 성과 계산"""
    portfolio_data = []
    
    for stock_name, holdings in portfolio.items():
        current_price = market_data.get(stock_name, {'price': 50000})['price']
        current_value = holdings['shares'] * current_price
        invested_value = holdings['shares'] * holdings['avg_price']
        pnl = current_value - invested_value
        pnl_pct = (pnl / invested_value) * 100 if invested_value > 0 else 0
        
        portfolio_data.append({
            '종목명': stock_name,
            '보유수량': f"{holdings['shares']:,}주",
            '평균매수가': f"₩ {holdings['avg_price']:,}",
            '현재가': f"₩ {current_price:,}",
            '평가금액': f"₩ {current_value:,}",
            '평가손익': f"₩ {pnl:,} ({pnl_pct:+.1f}%)"
        })
    
    return pd.DataFrame(portfolio_data)