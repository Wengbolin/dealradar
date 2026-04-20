import stripe
import sqlite3
from fastapi import APIRouter, Request
from pathlib import Path

router = APIRouter()

endpoint_secret = "whsec_exmx2KxQ5sIVyYrG1gqAq9nhiqOepseg"

# 数据库路径
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "market_data.db"


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # =========================
    # Checkout完成
    # =========================

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]
        customer_id = session.get("customer")

        if not customer_id:
            print("⚠️ 没有customer_id")
            return {"status": "error"}

        print("Stripe customer:", customer_id)

        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")

        if user_id:

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            plan = metadata.get("plan", "1")

            cursor.execute(
                "UPDATE users SET membership_level=?, stripe_customer_id=? WHERE id=?",
                (int(plan), customer_id, user_id)
            )

            conn.commit()
            conn.close()

            print("会员升级成功 user_id:", user_id)

    # =========================
    # 自动续费成功
    # =========================

    if event["type"] == "invoice.paid":

        invoice = event["data"]["object"]
        customer_id = invoice["customer"]

        print("自动续费成功:", customer_id)

    # =========================
    # 自动续费失败
    # =========================

    if event["type"] == "invoice.payment_failed":

        invoice = event["data"]["object"]
        customer_id = invoice["customer"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET membership_level=0 WHERE stripe_customer_id=?",
            (customer_id,)
        )

        conn.commit()
        conn.close()

        print("续费失败，会员降级:", customer_id)

    # =========================
    # 订阅取消
    # =========================

    if event["type"] == "customer.subscription.deleted":

        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET membership_level=1 WHERE stripe_customer_id=?",
            (customer_id,)
        )

        conn.commit()
        conn.close()

        print("订阅已取消，会员降级:", customer_id)

    return {"status": "success"}
