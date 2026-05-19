from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User, Plan, Bot, Message, Lead, AuditLog, Order, Announcement, Notification, SystemSetting
from schemas.admin import PlanCreate, PlanUpdate, PlanOut, AdminStats, BroadcastCreate
from schemas.auth import UserOut
from routers.auth import get_current_user, admin_required, super_admin_required
from typing import List, Optional
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

def log_action(db: Session, user_id: int, action: str, target_type: str = None, target_id: str = None, details: dict = None, request: Request = None):
    ip = request.client.host if request else None
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip
    )
    db.add(log)
    db.commit()

# --- DASHBOARD STATS ---

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    """Get platform-wide statistics for the admin dashboard."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.plan != "free").count()
    total_messages = db.query(Message).count()
    total_contacts = db.query(Lead).count()
    
    # Revenue estimation (simple sum based on plan prices)
    # In a real app, this would come from a payments table
    plans = db.query(Plan).all()
    plan_prices = {p.plan_name: p.monthly_price for p in plans}
    
    users = db.query(User).all()
    revenue_total = sum(plan_prices.get(u.plan, 0.0) for u in users)
    
    # Plan distribution
    plan_dist = {}
    for u in users:
        plan_dist[u.plan] = plan_dist.get(u.plan, 0) + 1
        
    # Recent signups
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
    recent_signups = []
    for u in recent_users:
        recent_signups.append({
            "id": u.id,
            "email": u.email,
            "plan": u.plan,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
        
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_messages": total_messages,
        "total_contacts": total_contacts,
        "revenue_total": revenue_total,
        "plan_distribution": plan_dist,
        "recent_signups": recent_signups
    }

# --- PLAN MANAGEMENT ---

@router.get("/plans", response_model=List[PlanOut])
async def get_plans(db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    return db.query(Plan).all()

@router.post("/plans", response_model=PlanOut)
async def create_plan(data: PlanCreate, request: Request, db: Session = Depends(get_db), admin: User = Depends(super_admin_required)):
    existing = db.query(Plan).filter(Plan.plan_name == data.plan_name).first()
    if existing:
        raise HTTPException(400, "Plan name already exists")
    
    plan = Plan(**data.dict())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    log_action(db, admin.id, "create_plan", "plan", str(plan.id), data.dict(), request)
    return plan

@router.put("/plans/{plan_id}", response_model=PlanOut)
async def update_plan(plan_id: int, data: PlanUpdate, request: Request, db: Session = Depends(get_db), admin: User = Depends(super_admin_required)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan not found")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    db.commit()
    db.refresh(plan)
    
    log_action(db, admin.id, "update_plan", "plan", str(plan_id), update_data, request)
    return plan

@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(super_admin_required)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan not found")
    
    # Check if users are using this plan
    user_count = db.query(User).filter(User.plan == plan.plan_name).count()
    if user_count > 0:
        raise HTTPException(400, f"Cannot delete plan. {user_count} users are currently on this plan.")
    
    db.delete(plan)
    db.commit()
    
    log_action(db, admin.id, "delete_plan", "plan", str(plan_id), {"plan_name": plan.plan_name}, request)
    return {"status": "ok", "message": "Plan deleted"}

# --- USER REGISTRY ---

@router.get("/users", response_model=List[UserOut])
async def get_all_users(db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    return db.query(User).all()

@router.put("/users/{user_id}/plan")
async def change_user_plan(user_id: int, plan_name: str, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    plan = db.query(Plan).filter(Plan.plan_name == plan_name).first()
    if not plan:
        raise HTTPException(400, "Invalid plan name")
    
    old_plan = user.plan
    user.plan = plan_name
    db.commit()
    
    log_action(db, admin.id, "change_user_plan", "user", str(user_id), {"old_plan": old_plan, "new_plan": plan_name}, request)
    return {"status": "ok", "message": f"User plan updated to {plan_name}"}

@router.put("/users/{user_id}/suspend")
async def suspend_user(user_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.bot:
        raise HTTPException(404, "User or bot not found")
    
    user.bot.status = False
    db.commit()
    
    log_action(db, admin.id, "suspend_user", "user", str(user_id), {}, request)
    return {"status": "ok", "message": "User bot suspended"}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(super_admin_required)):
    if user_id == admin.id:
        raise HTTPException(400, "Cannot delete yourself")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    email = user.email
    db.delete(user)
    db.commit()
    
    log_action(db, admin.id, "delete_user", "user", str(user_id), {"email": email}, request)
    return {"status": "ok", "message": "User deleted"}

# --- BROADCASTS ---

@router.post("/broadcast")
async def send_broadcast(data: BroadcastCreate, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    """Send a broadcast notification to users."""
    target_users_query = db.query(User)
    if data.recipients == "all":
        pass
    elif data.recipients in ["free", "starter", "premium"]:
        target_users_query = target_users_query.filter(User.plan == data.recipients)
    else:
        # Assume it's an email
        user = db.query(User).filter(User.email == data.recipients).first()
        if user:
            target_users_query = target_users_query.filter(User.id == user.id)
        else:
            raise HTTPException(400, "Invalid recipient selector or email")
            
    target_users = target_users_query.all()
    
    # Create notifications for these users
    for u in target_users:
        notif = Notification(
            user_id=u.id,
            type="broadcast",
            title=data.title,
            message=data.message
        )
        db.add(notif)
    
    # Also create a global announcement for visibility in the announcements feed
    new_announcement = Announcement(
        title=data.title,
        message=data.message,
        created_by=admin.id,
        priority=data.priority
    )
    db.add(new_announcement)
    db.commit()
    
    log_action(db, admin.id, "send_broadcast", "announcement", str(new_announcement.id), data.dict(), request)
    return {"status": "ok", "message": f"Broadcast sent to {len(target_users)} users"}

# --- AUDIT TRAILS ---

@router.get("/audit", response_model=List[dict])
async def get_audit_logs(db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        result.append({
            "id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "user": user.email if user else "System",
            "action": log.action,
            "target": f"{log.target_type}:{log.target_id}" if log.target_type else "N/A",
            "details": log.details
        })
    return result

# --- FINANCIALS ---

@router.get("/financials")
async def get_financials(db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    """Get financial overview."""
    # In a real app, this would query a 'payments' or 'subscriptions' table.
    # For now, we'll estimate based on current user plans.
    plans = db.query(Plan).all()
    plan_prices = {p.plan_name: p.monthly_price for p in plans}
    
    users = db.query(User).all()
    
    revenue_by_plan = {}
    for u in users:
        price = plan_prices.get(u.plan, 0.0)
        revenue_by_plan[u.plan] = revenue_by_plan.get(u.plan, 0.0) + price
        
    total_revenue = sum(revenue_by_plan.values())
    
    # Mock some recent payments
    recent_payments = []
    paid_users = [u for u in users if plan_prices.get(u.plan, 0.0) > 0]
    for u in paid_users[:10]:
        recent_payments.append({
            "user_email": u.email,
            "plan": u.plan,
            "amount": plan_prices.get(u.plan, 0.0),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "Succeeded"
        })
        
    return {
        "total_revenue": total_revenue,
        "revenue_by_plan": revenue_by_plan,
        "recent_payments": recent_payments
    }

# --- GLOBAL SETTINGS ---

@router.get("/settings")
async def get_system_settings(db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    settings = db.query(SystemSetting).all()
    return {s.key: s.value for s in settings}

@router.patch("/settings")
async def update_system_settings(data: dict, request: Request, db: Session = Depends(get_db), admin: User = Depends(super_admin_required)):
    for key, value in data.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(key=key, value=value)
            db.add(setting)
    
    db.commit()
    log_action(db, admin.id, "update_settings", "system", "global", data, request)
    return {"status": "ok", "message": "Settings updated"}
