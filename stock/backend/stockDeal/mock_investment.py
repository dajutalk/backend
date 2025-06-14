from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from stock.backend.database.connection import get_db
from stock.backend.auth.models import User
from stock.backend.stockDeal.models import MockBalance
from stock.backend.auth.auth_service import extract_user_id

router = APIRouter(prefix="/api/mock-investment", tags=["Mock Investment"])

@router.post("/start")
def start_mock_investment(
    request: Request,
    db: Session = Depends(get_db)
):
    # ✅ 쿠키에서 access_token 추출
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    try:
        user_id = extract_user_id(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

    # 2. 사용자 확인
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 3. 기존 잔고 확인
    existing = db.query(MockBalance).filter_by(user_id=user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 모의투자를 시작했습니다.")

    # 4. 잔고 생성
    balance = MockBalance(user_id=user.id)
    db.add(balance)
    db.commit()

    return {"message": "모의투자 잔고가 생성되었습니다."}
