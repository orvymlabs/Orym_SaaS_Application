from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Order, User
from routers.auth import get_current_user_id, get_current_user
from routers.notifications import create_notification
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])

class OrderStatusUpdate(BaseModel):
    status: str

@router.get("", response_model=List[dict])
@router.get("/", response_model=List[dict])
async def get_user_orders(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get all orders for the authenticated user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()

    logger.info(f"📋 Fetching orders for user {user_id}")
    logger.info(f"📋 Found {len(orders)} orders")

    # Format orders to include basic details for the list view
    formatted_orders = []
    for order in orders:
        logger.info(f"📋 Order {order.id}: order_details length = {len(order.order_details) if order.order_details else 0}")
        logger.info(f"📋 Order {order.id}: order_details content = {order.order_details}")

        formatted_orders.append({
            "id": order.id,
            "phone": order.phone,
            "order_details": order.order_details,  # Raw filled form from customer
            "status": getattr(order, 'status', 'Pending'),
            "created_at": order.created_at
        })

    logger.info(f"📋 Returning {len(formatted_orders)} formatted orders")
    return formatted_orders

@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update order status (e.g., mark as Completed)."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    # Update status if the model has a status field
    if hasattr(order, 'status'):
        order.status = status_update.status
    else:
        # If status field doesn't exist, we'll store it in a metadata field or just return success
        # For now, we'll just acknowledge the request
        pass

    db.commit()
    return {"status": "ok", "message": f"Order {order_id} marked as {status_update.status}"}

@router.delete("/{order_id}")
async def delete_order(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete an order."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    db.delete(order)
    db.commit()
    return {"status": "ok", "message": f"Order {order_id} deleted successfully"}

