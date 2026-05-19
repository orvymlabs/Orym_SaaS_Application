import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal
from models import User, Plan, Message, Lead
import json

def test_stats():
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.plan != "free").count()
        total_messages = db.query(Message).count()
        total_contacts = db.query(Lead).count()
        
        plans = db.query(Plan).all()
        print(f"Found {len(plans)} plans in DB.")
        plan_prices = {p.plan_name: p.monthly_price for p in plans}
        print(f"Plan prices: {plan_prices}")
        
        users = db.query(User).all()
        revenue_total = sum(plan_prices.get(u.plan, 0.0) for u in users)
        
        plan_dist = {}
        for u in users:
            plan_dist[u.plan] = plan_dist.get(u.plan, 0) + 1
            
        recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
        recent_signups = []
        for u in recent_users:
            recent_signups.append({
                "id": u.id,
                "email": u.email,
                "plan": u.plan,
                "created_at": u.created_at.isoformat() if u.created_at else None
            })
            
        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "total_messages": total_messages,
            "total_contacts": total_contacts,
            "revenue_total": revenue_total,
            "plan_distribution": plan_dist,
            "recent_signups": recent_signups
        }
        
        print("SUCCESS: Stats generated successfully!")
        print(json.dumps(stats, indent=2))
        
    except Exception as e:
        print(f"ERROR in stats: {e}")
    finally:
        db.close()

def test_financials():
    db = SessionLocal()
    try:
        plans = db.query(Plan).all()
        plan_prices = {p.plan_name: p.monthly_price for p in plans}
        
        users = db.query(User).all()
        
        revenue_by_plan = {}
        for u in users:
            price = plan_prices.get(u.plan, 0.0)
            revenue_by_plan[u.plan] = revenue_by_plan.get(u.plan, 0.0) + price
            
        total_revenue = sum(revenue_by_plan.values())
        
        financials = {
            "total_revenue": total_revenue,
            "revenue_by_plan": revenue_by_plan,
            "user_count": len(users)
        }
        
        print("\nSUCCESS: Financials generated successfully!")
        print(json.dumps(financials, indent=2))
        
    except Exception as e:
        print(f"ERROR in financials: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_stats()
    test_financials()
