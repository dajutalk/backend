from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict

from stock.backend.database.connection import get_db
from stock.backend.auth.models import User
from stock.backend.stockDeal.models import MockBalance, TransactionHistory
from stock.backend.auth.auth_service import extract_user_id

router = APIRouter(prefix="/api/mock-investment", tags=["Mock Investment"])

class TradeRequest(BaseModel):
    symbol: str
    price: float
    quantity: int

@router.post("/start")
def start_mock_investment(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    try:
        user_id = extract_user_id(token)
    except Exception:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    existing = db.query(MockBalance).filter_by(user_id=user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 모의투자를 시작했습니다.")

    balance = MockBalance(user_id=user.id)
    db.add(balance)
    db.commit()

    return {"message": "모의투자 잔고가 생성되었습니다."}

@router.get("/balance")
def get_my_mock_balance(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    try:
        user_id = extract_user_id(token)
    except Exception:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

    balance = db.query(MockBalance).filter_by(user_id=user_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="잔고가 존재하지 않습니다.")

    return {"balance": balance.balance}

@router.post("/buy")
def buy_stock(req: TradeRequest, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    try:
        user_id = extract_user_id(token)
    except Exception:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

    balance = db.query(MockBalance).filter_by(user_id=user_id).first()
    if not balance:
        raise HTTPException(status_code=400, detail="모의투자를 시작하지 않았습니다.")

    total_cost = int(req.price * req.quantity)
    if balance.balance < total_cost:
        raise HTTPException(status_code=400, detail="잔고가 부족합니다.")

    balance.balance -= total_cost

    trade = TransactionHistory(
        trade_type="BUY",
        symbol=req.symbol,
        quantity=req.quantity,
        total_price=total_cost,
        user_id=user_id
    )
    db.add(trade)
    db.commit()

    return {"message": "매수 완료", "new_balance": balance.balance}

@router.post("/sell")
def sell_stock(req: TradeRequest, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    try:
        user_id = extract_user_id(token)
    except Exception:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

    symbol = req.symbol
    price = req.price
    quantity = req.quantity

    if not all([symbol, price, quantity]):
        raise HTTPException(status_code=400, detail="모든 항목이 필요합니다.")

    buy_sum = db.query(func.sum(TransactionHistory.quantity)).filter_by(user_id=user_id, symbol=symbol, trade_type="BUY").scalar() or 0
    sell_sum = db.query(func.sum(TransactionHistory.quantity)).filter_by(user_id=user_id, symbol=symbol, trade_type="SELL").scalar() or 0
    owned = buy_sum - sell_sum

    if quantity > owned:
        raise HTTPException(status_code=400, detail=f"보유 수량({owned})보다 많이 팔 수 없습니다.")

    total_price = int(price * quantity)
    tx = TransactionHistory(
        trade_type="SELL",
        symbol=symbol,
        quantity=quantity,
        total_price=total_price,
        user_id=user_id
    )
    db.add(tx)

    balance = db.query(MockBalance).filter_by(user_id=user_id).first()
    if not balance:
        raise HTTPException(status_code=400, detail="잔고 없음")

    balance.balance += total_price
    db.commit()

    return {"message": "매도 완료", "new_balance": balance.balance}

@router.get("/holdings")
def get_user_holdings(request: Request, symbol: str = Query(None), db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    try:
        user_id = extract_user_id(token)
    except Exception:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

    query = db.query(
        TransactionHistory.symbol,
        TransactionHistory.trade_type,
        func.sum(TransactionHistory.quantity).label("qty")
    ).filter(TransactionHistory.user_id == user_id)

    if symbol:
        query = query.filter(TransactionHistory.symbol == symbol)

    query = query.group_by(TransactionHistory.symbol, TransactionHistory.trade_type)
    results = query.all()

    holdings = defaultdict(int)
    for sym, trade_type, qty in results:
        if trade_type == "BUY":
            holdings[sym] += qty
        elif trade_type == "SELL":
            holdings[sym] -= qty

    if symbol:
        return {"quantity": holdings.get(symbol, 0)}
    return {"holdings": dict(holdings)}
