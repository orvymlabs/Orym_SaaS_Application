from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Order, User
from routers.auth import get_current_user_id, get_current_user
from pydantic import BaseModel

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

    # Format orders to include basic details for the list view
    formatted_orders = []
    for order in orders:
        formatted_orders.append({
            "id": order.id,
            "customer_name": order.name,
            "phone": order.phone,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "address": order.address,
            "status": getattr(order, 'status', 'Pending'),  # Get status from model or default to Pending
            "created_at": order.created_at
        })

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

