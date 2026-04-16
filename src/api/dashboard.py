"""Dashboard API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from typing import List, Dict, Any

from ..database import get_db
from ..models import Concert, Ticket, Venue

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get dashboard statistics including concert counts and revenue."""
    now = datetime.now()
    
    # Get total concerts
    total_concerts = db.query(Concert).count()
    
    # Get upcoming concerts (future)
    upcoming_concerts = db.query(Concert).filter(Concert.date > now).count()
    
    # Get past concerts
    past_concerts = db.query(Concert).filter(Concert.date <= now).count()
    
    # Calculate total revenue from sold tickets
    total_revenue_result = db.query(
        func.sum(Concert.ticket_price)
    ).join(
        Ticket, Concert.id == Ticket.concert_id
    ).scalar()
    
    total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
    
    # Get recent concerts (latest 5) with venue names
    recent_concerts = db.query(
        Concert.id,
        Concert.title,
        Concert.artist,
        Concert.date,
        Venue.name.label('venue_name')
    ).join(
        Venue, Concert.venue_id == Venue.id
    ).order_by(
        Concert.date.desc()
    ).limit(5).all()
    
    # Format recent concerts for JSON response
    recent_concerts_data = [
        {
            "id": concert.id,
            "title": concert.title,
            "artist": concert.artist,
            "date": concert.date.isoformat(),
            "venue_name": concert.venue_name
        }
        for concert in recent_concerts
    ]
    
    return {
        "total_concerts": total_concerts,
        "upcoming_concerts": upcoming_concerts,
        "past_concerts": past_concerts,
        "total_revenue": total_revenue,
        "recent_concerts": recent_concerts_data
    }


@router.get("/stats/concerts")
def get_concert_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get detailed concert statistics."""
    now = datetime.now()
    
    # Concert counts by status
    total = db.query(Concert).count()
    upcoming = db.query(Concert).filter(Concert.date > now).count()
    past = db.query(Concert).filter(Concert.date <= now).count()
    
    # Concerts by month (last 6 months)
    monthly_stats = db.query(
        func.extract('year', Concert.date).label('year'),
        func.extract('month', Concert.date).label('month'),
        func.count(Concert.id).label('count')
    ).group_by(
        func.extract('year', Concert.date),
        func.extract('month', Concert.date)
    ).order_by(
        func.extract('year', Concert.date).desc(),
        func.extract('month', Concert.date).desc()
    ).limit(6).all()
    
    monthly_data = [
        {
            "year": int(stat.year),
            "month": int(stat.month),
            "count": stat.count
        }
        for stat in monthly_stats
    ]
    
    return {
        "total_concerts": total,
        "upcoming_concerts": upcoming,
        "past_concerts": past,
        "monthly_breakdown": monthly_data
    }


@router.get("/stats/revenue")
def get_revenue_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get detailed revenue statistics."""
    # Total revenue
    total_revenue_result = db.query(
        func.sum(Concert.ticket_price)
    ).join(
        Ticket, Concert.id == Ticket.concert_id
    ).scalar()
    
    total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
    
    # Revenue by concert
    concert_revenue = db.query(
        Concert.id,
        Concert.title,
        Concert.artist,
        Concert.ticket_price,
        func.count(Ticket.id).label('tickets_sold'),
        (Concert.ticket_price * func.count(Ticket.id)).label('concert_revenue')
    ).outerjoin(
        Ticket, Concert.id == Ticket.concert_id
    ).group_by(
        Concert.id,
        Concert.title,
        Concert.artist,
        Concert.ticket_price
    ).order_by(
        (Concert.ticket_price * func.count(Ticket.id)).desc()
    ).all()
    
    concert_revenue_data = [
        {
            "concert_id": concert.id,
            "title": concert.title,
            "artist": concert.artist,
            "ticket_price": float(concert.ticket_price),
            "tickets_sold": concert.tickets_sold,
            "revenue": float(concert.concert_revenue) if concert.tickets_sold > 0 else 0.0
        }
        for concert in concert_revenue
    ]
    
    return {
        "total_revenue": total_revenue,
        "revenue_by_concert": concert_revenue_data
    }


@router.get("/stats/venues")
def get_venue_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get venue usage statistics."""
    venue_stats = db.query(
        Venue.id,
        Venue.name,
        Venue.capacity,
        func.count(Concert.id).label('concerts_hosted')
    ).outerjoin(
        Concert, Venue.id == Concert.venue_id
    ).group_by(
        Venue.id,
        Venue.name,
        Venue.capacity
    ).order_by(
        func.count(Concert.id).desc()
    ).all()
    
    venue_data = [
        {
            "venue_id": venue.id,
            "name": venue.name,
            "capacity": venue.capacity,
            "concerts_hosted": venue.concerts_hosted
        }
        for venue in venue_stats
    ]
    
    total_venues = db.query(Venue).count()
    active_venues = db.query(Venue).join(Concert).distinct().count()
    
    return {
        "total_venues": total_venues,
        "active_venues": active_venues,
        "venue_details": venue_data
    }
