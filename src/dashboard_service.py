from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import logging

from .models import Tour, Concert, Ticket, Venue, TourStatus, ConcertStatus, TicketStatus
from .schemas import DashboardStats, TourProgress
from .cache import cache

logger = logging.getLogger(__name__)

# Cache keys
DASHBOARD_STATS_CACHE_KEY = "dashboard_stats"
TOUR_PROGRESS_CACHE_KEY_PREFIX = "tour_progress_"

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


class DashboardService:
    """Service for calculating and caching dashboard statistics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self, use_cache: bool = True) -> DashboardStats:
        """
        Get dashboard statistics with caching.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            DashboardStats object with all statistics
        """
        if use_cache:
            cached_stats = cache.get(DASHBOARD_STATS_CACHE_KEY)
            if cached_stats:
                logger.debug("Returning cached dashboard stats")
                return DashboardStats(**cached_stats)
        
        logger.debug("Calculating fresh dashboard stats")
        stats = self._calculate_dashboard_stats()
        
        # Cache the result
        cache.set(DASHBOARD_STATS_CACHE_KEY, stats.model_dump(), CACHE_TTL)
        
        return stats
    
    def _calculate_dashboard_stats(self) -> DashboardStats:
        """Calculate dashboard statistics using optimized database queries."""
        try:
            # Tour statistics
            tour_stats = self.db.query(
                func.count(Tour.id).label('total_tours'),
                func.count(Tour.id).filter(Tour.status == TourStatus.active).label('active_tours')
            ).first()
            
            total_tours = tour_stats.total_tours or 0
            active_tours = tour_stats.active_tours or 0
            
            # Concert statistics
            now = datetime.now(timezone.utc)
            concert_stats = self.db.query(
                func.count(Concert.id).label('total_concerts'),
                func.count(Concert.id).filter(Concert.date > now).label('upcoming_concerts'),
                func.count(Concert.id).filter(Concert.status == ConcertStatus.completed).label('completed_concerts')
            ).first()
            
            total_concerts = concert_stats.total_concerts or 0
            upcoming_concerts = concert_stats.upcoming_concerts or 0
            completed_concerts = concert_stats.completed_concerts or 0
            
            # Ticket statistics and revenue
            ticket_stats = self.db.query(
                func.count(Ticket.id).label('total_tickets'),
                func.count(Ticket.id).filter(Ticket.status == TicketStatus.sold).label('sold_tickets'),
                func.count(Ticket.id).filter(Ticket.status == TicketStatus.available).label('available_tickets'),
                func.coalesce(func.sum(Ticket.price).filter(Ticket.status == TicketStatus.sold), 0).label('total_revenue')
            ).first()
            
            total_tickets = ticket_stats.total_tickets or 0
            sold_tickets = ticket_stats.sold_tickets or 0
            available_tickets = ticket_stats.available_tickets or 0
            total_revenue = Decimal(str(ticket_stats.total_revenue or 0))
            
            # Venue count
            total_venues = self.db.query(func.count(Venue.id)).scalar() or 0
            
            return DashboardStats(
                total_tours=total_tours,
                active_tours=active_tours,
                total_concerts=total_concerts,
                upcoming_concerts=upcoming_concerts,
                completed_concerts=completed_concerts,
                total_tickets=total_tickets,
                sold_tickets=sold_tickets,
                available_tickets=available_tickets,
                total_revenue=total_revenue,
                total_venues=total_venues
            )
            
        except Exception as e:
            logger.error(f"Error calculating dashboard stats: {e}")
            # Return zero stats on error
            return DashboardStats(
                total_tours=0,
                active_tours=0,
                total_concerts=0,
                upcoming_concerts=0,
                completed_concerts=0,
                total_tickets=0,
                sold_tickets=0,
                available_tickets=0,
                total_revenue=Decimal('0'),
                total_venues=0
            )
    
    def get_tour_progress(self, tour_id: int, use_cache: bool = True) -> Optional[TourProgress]:
        """
        Get progress statistics for a specific tour.
        
        Args:
            tour_id: ID of the tour
            use_cache: Whether to use cached data if available
            
        Returns:
            TourProgress object or None if tour not found
        """
        cache_key = f"{TOUR_PROGRESS_CACHE_KEY_PREFIX}{tour_id}"
        
        if use_cache:
            cached_progress = cache.get(cache_key)
            if cached_progress:
                logger.debug(f"Returning cached tour progress for tour {tour_id}")
                return TourProgress(**cached_progress)
        
        logger.debug(f"Calculating fresh tour progress for tour {tour_id}")
        progress = self._calculate_tour_progress(tour_id)
        
        if progress:
            # Cache the result
            cache.set(cache_key, progress.model_dump(), CACHE_TTL)
        
        return progress
    
    def _calculate_tour_progress(self, tour_id: int) -> Optional[TourProgress]:
        """Calculate progress statistics for a specific tour."""
        try:
            # Get tour info
            tour = self.db.query(Tour).filter(Tour.id == tour_id).first()
            if not tour:
                logger.warning(f"Tour {tour_id} not found")
                return None
            
            now = datetime.now(timezone.utc)
            
            # Concert statistics for the tour
            concert_stats = self.db.query(
                func.count(Concert.id).label('total_concerts'),
                func.count(Concert.id).filter(Concert.status == ConcertStatus.completed).label('completed_concerts'),
                func.count(Concert.id).filter(Concert.date > now).label('upcoming_concerts')
            ).filter(Concert.tour_id == tour_id).first()
            
            total_concerts = concert_stats.total_concerts or 0
            completed_concerts = concert_stats.completed_concerts or 0
            upcoming_concerts = concert_stats.upcoming_concerts or 0
            
            # Calculate progress percentage
            progress_percentage = self._calculate_progress_percentage(
                total_concerts, completed_concerts
            )
            
            # Ticket statistics for the tour
            ticket_stats = self.db.query(
                func.count(Ticket.id).label('total_tickets'),
                func.count(Ticket.id).filter(Ticket.status == TicketStatus.sold).label('sold_tickets'),
                func.coalesce(func.sum(Ticket.price).filter(Ticket.status == TicketStatus.sold), 0).label('revenue')
            ).join(Concert).filter(Concert.tour_id == tour_id).first()
            
            total_tickets = ticket_stats.total_tickets or 0
            sold_tickets = ticket_stats.sold_tickets or 0
            revenue = Decimal(str(ticket_stats.revenue or 0))
            
            return TourProgress(
                tour_id=tour_id,
                tour_name=tour.name,
                total_concerts=total_concerts,
                completed_concerts=completed_concerts,
                upcoming_concerts=upcoming_concerts,
                progress_percentage=progress_percentage,
                total_tickets=total_tickets,
                sold_tickets=sold_tickets,
                revenue=revenue
            )
            
        except Exception as e:
            logger.error(f"Error calculating tour progress for tour {tour_id}: {e}")
            return None
    
    def _calculate_progress_percentage(self, total_concerts: int, completed_concerts: int) -> float:
        """
        Calculate tour progress percentage.
        
        Args:
            total_concerts: Total number of concerts in the tour
            completed_concerts: Number of completed concerts
            
        Returns:
            Progress percentage (0.0 to 100.0)
        """
        if total_concerts == 0:
            # No concerts planned - consider it 0% progress
            return 0.0
        
        return round((completed_concerts / total_concerts) * 100, 2)
    
    def get_all_tour_progress(self, use_cache: bool = True) -> List[TourProgress]:
        """
        Get progress statistics for all tours.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            List of TourProgress objects
        """
        try:
            # Get all tour IDs
            tour_ids = self.db.query(Tour.id).all()
            tour_progress_list = []
            
            for (tour_id,) in tour_ids:
                progress = self.get_tour_progress(tour_id, use_cache)
                if progress:
                    tour_progress_list.append(progress)
            
            return tour_progress_list
            
        except Exception as e:
            logger.error(f"Error getting all tour progress: {e}")
            return []
    
    def invalidate_cache(self, tour_id: Optional[int] = None) -> None:
        """
        Invalidate dashboard cache.
        
        Args:
            tour_id: If provided, only invalidate cache for this tour
        """
        if tour_id:
            cache_key = f"{TOUR_PROGRESS_CACHE_KEY_PREFIX}{tour_id}"
            cache.delete(cache_key)
            logger.debug(f"Invalidated cache for tour {tour_id}")
        else:
            cache.delete(DASHBOARD_STATS_CACHE_KEY)
            # Clear all tour progress caches
            # In a production system, you'd want a more sophisticated cache invalidation strategy
            logger.debug("Invalidated dashboard stats cache")
    
    def get_revenue_by_tour(self, use_cache: bool = True) -> List[dict]:
        """
        Get revenue breakdown by tour.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            List of dictionaries with tour_id, tour_name, and revenue
        """
        cache_key = "revenue_by_tour"
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug("Returning cached revenue by tour data")
                return cached_data
        
        try:
            revenue_data = self.db.query(
                Tour.id.label('tour_id'),
                Tour.name.label('tour_name'),
                func.coalesce(func.sum(Ticket.price).filter(Ticket.status == TicketStatus.sold), 0).label('revenue')
            ).join(Concert).join(Ticket, Concert.id == Ticket.concert_id, isouter=True)\
             .group_by(Tour.id, Tour.name)\
             .order_by(func.sum(Ticket.price).desc()).all()
            
            result = [
                {
                    'tour_id': row.tour_id,
                    'tour_name': row.tour_name,
                    'revenue': float(row.revenue or 0)
                }
                for row in revenue_data
            ]
            
            # Cache the result
            cache.set(cache_key, result, CACHE_TTL)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating revenue by tour: {e}")
            return []
