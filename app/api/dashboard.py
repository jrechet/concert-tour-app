from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import calendar

from ..database import get_db
from ..models import Concert, Venue
from ..schemas import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    
    # Get total concerts
    total_concerts = db.query(Concert).count()
    
    # Get upcoming concerts
    now = datetime.now()
    upcoming_concerts = db.query(Concert).filter(Concert.date >= now).count()
    
    # Get total venues
    total_venues = db.query(Venue).count()
    
    # Get total capacity (sum of all venue capacities for upcoming concerts)
    total_capacity = db.query(Concert).join(Venue).filter(
        Concert.date >= now
    ).with_entities(db.func.sum(Venue.capacity)).scalar() or 0
    
    stats_html = f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{total_concerts}</div>
            <div class="stat-label">Total Concerts</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{upcoming_concerts}</div>
            <div class="stat-label">Upcoming Shows</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_venues}</div>
            <div class="stat-label">Venues</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_capacity:,}</div>
            <div class="stat-label">Total Capacity</div>
        </div>
    </div>
    """
    
    return stats_html


@router.get("/calendar")
def get_calendar_view(
    offset: int = Query(0, description="Month offset from current month"),
    current_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get calendar view with concert dates"""
    
    # Calculate target month
    now = datetime.now()
    target_date = now.replace(day=1) + timedelta(days=32 * offset)
    target_date = target_date.replace(day=1)  # First day of target month
    
    # Get month info
    year = target_date.year
    month = target_date.month
    month_name = calendar.month_name[month]
    
    # Get concerts for this month
    month_start = target_date
    next_month = month_start.replace(day=28) + timedelta(days=4)
    month_end = next_month - timedelta(days=next_month.day)
    
    concerts = db.query(Concert).join(Venue).filter(
        Concert.date >= month_start,
        Concert.date <= month_end
    ).all()
    
    # Create concert lookup by date
    concert_lookup = {}
    for concert in concerts:
        date_key = concert.date.strftime('%Y-%m-%d')
        if date_key not in concert_lookup:
            concert_lookup[date_key] = []
        concert_lookup[date_key].append(concert)
    
    # Generate calendar grid
    cal = calendar.Calendar(firstweekday=6)  # Start week on Sunday
    month_days = list(cal.itermonthdates(year, month))
    
    # Group days into weeks
    weeks = []
    for i in range(0, len(month_days), 7):
        weeks.append(month_days[i:i+7])
    
    # Build calendar HTML
    calendar_html = f"""
    <div class="calendar-grid">
        <div class="calendar-header-day">Sun</div>
        <div class="calendar-header-day">Mon</div>
        <div class="calendar-header-day">Tue</div>
        <div class="calendar-header-day">Wed</div>
        <div class="calendar-header-day">Thu</div>
        <div class="calendar-header-day">Fri</div>
        <div class="calendar-header-day">Sat</div>
    """
    
    for week in weeks:
        for day in week:
            date_str = day.strftime('%Y-%m-%d')
            day_concerts = concert_lookup.get(date_str, [])
            
            css_classes = ["calendar-day"]
            if day.month != month:
                css_classes.append("other-month")
            if day_concerts:
                css_classes.append("has-concert")
            
            concert_indicators = ""
            for concert in day_concerts[:2]:  # Show max 2 concerts
                venue_name = concert.venue.name if concert.venue else "Unknown"
                concert_indicators += f'<div class="concert-indicator">{venue_name}</div>'
            
            if len(day_concerts) > 2:
                concert_indicators += f'<div class="concert-indicator">+{len(day_concerts) - 2} more</div>'
            
            calendar_html += f"""
            <div class="{' '.join(css_classes)}" data-date="{date_str}">
                <div class="day-number">{day.day}</div>
                {concert_indicators}
            </div>
            """
    
    calendar_html += "</div>"
    
    # Update the title
    title_html = f'<script>document.getElementById("calendar-title").textContent = "{month_name} {year}";</script>'
    
    return calendar_html + title_html


@router.get("/concert-details")
def get_concert_details(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get concert details for a specific date"""
    
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return '<div class="no-concert">Invalid date format</div>'
    
    concerts = db.query(Concert).join(Venue).filter(
        db.func.date(Concert.date) == target_date
    ).all()
    
    if not concerts:
        return f'<div class="no-concert">No concerts scheduled for {target_date.strftime("%B %d, %Y")}</div>'
    
    details_html = f'<h3>Concerts on {target_date.strftime("%B %d, %Y")}</h3>'
    
    for i, concert in enumerate(concerts):
        if i > 0:
            details_html += '<hr style="margin: 1rem 0; border: 1px solid #e2e8f0;">'
        
        venue = concert.venue
        details_html += f"""
        <div class="concert-info">
            <div class="concert-info-item">
                <span class="concert-info-label">Venue:</span>
                <span class="concert-info-value">{venue.name}</span>
            </div>
            <div class="concert-info-item">
                <span class="concert-info-label">Location:</span>
                <span class="concert-info-value">{venue.city}, {venue.state}</span>
            </div>
            <div class="concert-info-item">
                <span class="concert-info-label">Capacity:</span>
                <span class="concert-info-value">{venue.capacity:,}</span>
            </div>
            <div class="concert-info-item">
                <span class="concert-info-label">Time:</span>
                <span class="concert-info-value">{concert.date.strftime("%I:%M %p")}</span>
            </div>
        """
        
        if concert.notes:
            details_html += f"""
            <div class="concert-info-item">
                <span class="concert-info-label">Notes:</span>
                <span class="concert-info-value">{concert.notes}</span>
            </div>
            """
        
        details_html += "</div>"
    
    return details_html
