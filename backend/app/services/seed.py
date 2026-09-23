from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import HangRail, RailPlacement, Store, WorkOrder


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(Store.id).limit(1)):
        return
    store = Store(name="清风干洗 · 滨江店")
    db.add(store)
    db.flush()
    # A 杆配置 5 cm 间隔缓冲；B 杆无缓冲，可贴边连续挂满。
    r1 = HangRail(store_id=store.id, label="A 杆", length_cm=200, buffer_cm=5)
    r2 = HangRail(store_id=store.id, label="B 杆", length_cm=160, buffer_cm=0)
    db.add_all([r1, r2])
    db.flush()
    now = datetime.utcnow()
    orders = [
        WorkOrder(store_id=store.id, ticket_code="HR-2001", garment_name="羊毛大衣", length_cm=45, status="hung", due_at=now + timedelta(days=1), hung_at=now - timedelta(hours=5)),
        WorkOrder(store_id=store.id, ticket_code="HR-2002", garment_name="西装套装", length_cm=35, status="hung", due_at=now + timedelta(days=2), hung_at=now - timedelta(hours=3)),
        WorkOrder(store_id=store.id, ticket_code="HR-2003", garment_name="羽绒服", length_cm=50, status="ready", due_at=now + timedelta(days=1)),
        WorkOrder(store_id=store.id, ticket_code="HR-2004", garment_name="连衣裙", length_cm=30, status="ready", due_at=now - timedelta(days=1)),
        WorkOrder(store_id=store.id, ticket_code="HR-2005", garment_name="风衣", length_cm=40, status="hung", due_at=now - timedelta(hours=12), hung_at=now - timedelta(days=3)),
        WorkOrder(store_id=store.id, ticket_code="HR-2006", garment_name="厚呢大衣", length_cm=60, status="hung", due_at=now + timedelta(days=2), hung_at=now - timedelta(hours=2)),
    ]
    db.add_all(orders)
    db.flush()
    # A 杆既有占位按 5 cm 缓冲间隔排开（0-45 / 50-85 / 90-150），
    # 尾隙 150-200 恰好 50 cm：羽绒服贴边可挂，加 5 cm 缓冲后起点须为 155、
    # 末端 205 超出杆长 → A 杆被缓冲封阻，First-Fit 改挂无缓冲的 B 杆 40-90。
    db.add_all(
        [
            RailPlacement(rail_id=r1.id, order_id=orders[0].id, start_cm=0, end_cm=45),
            RailPlacement(rail_id=r1.id, order_id=orders[1].id, start_cm=50, end_cm=85),
            RailPlacement(rail_id=r1.id, order_id=orders[5].id, start_cm=90, end_cm=150),
            RailPlacement(rail_id=r2.id, order_id=orders[4].id, start_cm=0, end_cm=40),
        ]
    )
    db.commit()
