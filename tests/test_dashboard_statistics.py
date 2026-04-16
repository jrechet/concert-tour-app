"""Tests for dashboard statistics calculations and tour progress."""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from src.models import Tour, Concert, Venue, TourStatus, ConcertStatus
from src.services.dashboard import DashboardService


class TestTourProgressCalculations:
    """Test tour progress calculation with various completion states."""
    
    @pytest.fixture
    async def sample_venues(self):
        """Create sample venues for testing."""
        venue1 = Venue(
            id=1,
            name="Test Arena 1",
            city="New York",
            state="NY",
            capacity=20000,
            created_at=datetime.now(timezone.utc)
        )
        venue2 = Venue(
            id=2,
            name="Test Arena 2", 
            city="Los Angeles",
            state="CA",
            capacity=15000,
            created_at=datetime.now(timezone.utc)
        )
        venue3 = Venue(
            id=3,
            name="Test Arena 3",
            city="Chicago", 
            state="IL",
            capacity=18000,
            created_at=datetime.now(timezone.utc)
        )
        return [venue1, venue2, venue3]
    
    @pytest.fixture
    async def tour_with_concerts(self, sample_venues):
        """Create a tour with concerts in various states."""
        now = datetime.now(timezone.utc)
        
        tour = Tour(
            id=1,
            name="Test Tour 2024",
            description="A test tour",
            status=TourStatus.ACTIVE,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30),
            created_at=now
        )
        
        # Past concert (completed)
        concert1 = Concert(
            id=1,
            tour_id=tour.id,
            venue_id=sample_venues[0].id,
            date=now - timedelta(days=15),
            status=ConcertStatus.COMPLETED,
            ticket_price=Decimal("50.00"),
            tickets_sold=15000,
            created_at=now
        )
        
        # Current/recent concert (completed)
        concert2 = Concert(
            id=2,
            tour_id=tour.id,
            venue_id=sample_venues[1].id,
            date=now - timedelta(days=2),
            status=ConcertStatus.COMPLETED,
            ticket_price=Decimal("60.00"),
            tickets_sold=12000,
            created_at=now
        )
        
        # Future concert (scheduled)
        concert3 = Concert(
            id=3,
            tour_id=tour.id,
            venue_id=sample_venues[2].id,
            date=now + timedelta(days=15),
            status=ConcertStatus.SCHEDULED,
            ticket_price=Decimal("55.00"),
            tickets_sold=0,
            created_at=now
        )
        
        return tour, [concert1, concert2, concert3], sample_venues
    
    @pytest.mark.asyncio
    async def test_tour_progress_0_percent(self, sample_venues):
        """Test tour progress calculation with 0% completion (all future concerts)."""
        now = datetime.now(timezone.utc)
        
        tour = Tour(
            id=1,
            name="Future Tour",
            description="All concerts in the future",
            status=TourStatus.ACTIVE,
            start_date=now + timedelta(days=10),
            end_date=now + timedelta(days=50),
            created_at=now
        )
        
        concerts = [
            Concert(
                id=1,
                tour_id=tour.id,
                venue_id=sample_venues[0].id,
                date=now + timedelta(days=15),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("50.00"),
                tickets_sold=0,
                created_at=now
            ),
            Concert(
                id=2,
                tour_id=tour.id,
                venue_id=sample_venues[1].id,
                date=now + timedelta(days=25),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("60.00"),
                tickets_sold=0,
                created_at=now
            )
        ]
        
        with patch('src.services.dashboard.get_tour_by_id') as mock_get_tour, \
             patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            
            mock_get_tour.return_value = tour
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            
            assert progress['total_concerts'] == 2
            assert progress['completed_concerts'] == 0
            assert progress['progress_percentage'] == 0.0
            assert progress['upcoming_concerts'] == 2
    
    @pytest.mark.asyncio
    async def test_tour_progress_50_percent(self, tour_with_concerts):
        """Test tour progress calculation with 50% completion."""
        tour, concerts, venues = tour_with_concerts
        
        # Modify one future concert to be completed to get exactly 50%
        concerts[2].status = ConcertStatus.SCHEDULED  # Keep as scheduled
        
        # Add one more scheduled concert to make it 2/4 = 50%
        now = datetime.now(timezone.utc)
        concerts.append(Concert(
            id=4,
            tour_id=tour.id,
            venue_id=venues[0].id,
            date=now + timedelta(days=25),
            status=ConcertStatus.SCHEDULED,
            ticket_price=Decimal("45.00"),
            tickets_sold=0,
            created_at=now
        ))
        
        with patch('src.services.dashboard.get_tour_by_id') as mock_get_tour, \
             patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            
            mock_get_tour.return_value = tour
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            
            assert progress['total_concerts'] == 4
            assert progress['completed_concerts'] == 2
            assert progress['progress_percentage'] == 50.0
            assert progress['upcoming_concerts'] == 2
    
    @pytest.mark.asyncio
    async def test_tour_progress_100_percent(self, sample_venues):
        """Test tour progress calculation with 100% completion (all past concerts)."""
        now = datetime.now(timezone.utc)
        
        tour = Tour(
            id=1,
            name="Completed Tour",
            description="All concerts completed",
            status=TourStatus.COMPLETED,
            start_date=now - timedelta(days=50),
            end_date=now - timedelta(days=10),
            created_at=now
        )
        
        concerts = [
            Concert(
                id=1,
                tour_id=tour.id,
                venue_id=sample_venues[0].id,
                date=now - timedelta(days=45),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("50.00"),
                tickets_sold=15000,
                created_at=now
            ),
            Concert(
                id=2,
                tour_id=tour.id,
                venue_id=sample_venues[1].id,
                date=now - timedelta(days=35),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("60.00"),
                tickets_sold=12000,
                created_at=now
            ),
            Concert(
                id=3,
                tour_id=tour.id,
                venue_id=sample_venues[2].id,
                date=now - timedelta(days=15),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("55.00"),
                tickets_sold=18000,
                created_at=now
            )
        ]
        
        with patch('src.services.dashboard.get_tour_by_id') as mock_get_tour, \
             patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            
            mock_get_tour.return_value = tour
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            
            assert progress['total_concerts'] == 3
            assert progress['completed_concerts'] == 3
            assert progress['progress_percentage'] == 100.0
            assert progress['upcoming_concerts'] == 0


class TestStatisticsCalculations:
    """Test statistics calculations for accuracy."""
    
    @pytest.mark.asyncio
    async def test_total_concerts_calculation(self, tour_with_concerts):
        """Test total concerts calculation."""
        tour, concerts, venues = tour_with_concerts
        
        with patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            stats = await dashboard_service.calculate_tour_statistics(tour.id)
            
            assert stats['total_concerts'] == 3
    
    @pytest.mark.asyncio
    async def test_completed_shows_calculation(self, tour_with_concerts):
        """Test completed shows calculation."""
        tour, concerts, venues = tour_with_concerts
        
        with patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            stats = await dashboard_service.calculate_tour_statistics(tour.id)
            
            # 2 completed concerts from the fixture
            assert stats['completed_concerts'] == 2
    
    @pytest.mark.asyncio
    async def test_revenue_totals_calculation(self, tour_with_concerts):
        """Test revenue totals calculation with known dataset."""
        tour, concerts, venues = tour_with_concerts
        
        with patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            stats = await dashboard_service.calculate_tour_statistics(tour.id)
            
            # Concert 1: 15000 * $50.00 = $750,000
            # Concert 2: 12000 * $60.00 = $720,000
            # Concert 3: 0 * $55.00 = $0 (not completed)
            # Total: $1,470,000
            expected_revenue = Decimal("1470000.00")
            assert stats['total_revenue'] == expected_revenue
            
            # Only completed concerts count for actual revenue
            assert stats['actual_revenue'] == expected_revenue
    
    @pytest.mark.asyncio
    async def test_potential_revenue_calculation(self, tour_with_concerts):
        """Test potential revenue calculation including future concerts."""
        tour, concerts, venues = tour_with_concerts
        
        # Set tickets sold for future concert to test potential revenue
        concerts[2].tickets_sold = 5000  # Some pre-sales
        
        with patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts, \
             patch('src.services.dashboard.get_venue_by_id') as mock_get_venue:
            
            mock_get_concerts.return_value = concerts
            # Mock venue capacity lookup
            mock_get_venue.side_effect = lambda venue_id: next(
                (v for v in venues if v.id == venue_id), None
            )
            
            dashboard_service = DashboardService()
            stats = await dashboard_service.calculate_tour_statistics(tour.id)
            
            # Concert 3 potential: 18000 capacity * $55.00 = $990,000
            # Total potential (all concerts at capacity):
            # 20000 * $50 + 15000 * $60 + 18000 * $55 = $2,890,000
            expected_potential = Decimal("2890000.00")
            assert stats['potential_revenue'] == expected_potential


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_zero_concerts_tour(self):
        """Test statistics with zero concerts."""
        now = datetime.now(timezone.utc)
        tour = Tour(
            id=1,
            name="Empty Tour",
            description="Tour with no concerts",
            status=TourStatus.PLANNING,
            start_date=now + timedelta(days=30),
            end_date=now + timedelta(days=60),
            created_at=now
        )
        
        with patch('src.services.dashboard.get_tour_by_id') as mock_get_tour, \
             patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            
            mock_get_tour.return_value = tour
            mock_get_concerts.return_value = []
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            stats = await dashboard_service.calculate_tour_statistics(tour.id)
            
            # Progress calculations
            assert progress['total_concerts'] == 0
            assert progress['completed_concerts'] == 0
            assert progress['progress_percentage'] == 0.0
            assert progress['upcoming_concerts'] == 0
            
            # Statistics calculations
            assert stats['total_concerts'] == 0
            assert stats['completed_concerts'] == 0
            assert stats['total_revenue'] == Decimal("0.00")
            assert stats['actual_revenue'] == Decimal("0.00")
            assert stats['potential_revenue'] == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_all_future_concerts(self, sample_venues):
        """Test scenario with all future concerts."""
        now = datetime.now(timezone.utc)
        tour = Tour(
            id=1,
            name="Future Tour",
            description="All concerts in future",
            status=TourStatus.ACTIVE,
            start_date=now + timedelta(days=10),
            end_date=now + timedelta(days=50),
            created_at=now
        )
        
        concerts = [
            Concert(
                id=1,
                tour_id=tour.id,
                venue_id=sample_venues[0].id,
                date=now + timedelta(days=15),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("50.00"),
                tickets_sold=1000,  # Some pre-sales
                created_at=now
            ),
            Concert(
                id=2,
                tour_id=tour.id,
                venue_id=sample_venues[1].id,
                date=now + timedelta(days=30),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("60.00"),
                tickets_sold=500,  # Some pre-sales
                created_at=now
            )
        ]
        
        with patch('src.services.dashboard.get_tour_by_id') as mock_get_tour, \
             patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts, \
             patch('src.services.dashboard.get_venue_by_id') as mock_get_venue:
            
            mock_get_tour.return_value = tour
            mock_get_concerts.return_value = concerts
            mock_get_venue.side_effect = lambda venue_id: next(
                (v for v in sample_venues if v.id == venue_id), None
            )
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            stats = await dashboard_service.calculate_tour_statistics(tour.id)
            
            # All concerts are future
            assert progress['completed_concerts'] == 0
            assert progress['progress_percentage'] == 0.0
            assert progress['upcoming_concerts'] == 2
            
            # No actual revenue yet, but potential revenue exists
            assert stats['actual_revenue'] == Decimal("0.00")
            assert stats['potential_revenue'] > Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_mixed_concert_statuses(self, sample_venues):
        """Test scenario with mixed concert statuses including cancelled."""
        now = datetime.now(timezone.utc)
        tour = Tour(
            id=1,
            name="Mixed Status Tour",
            description="Tour with various concert statuses",
            status=TourStatus.ACTIVE,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30),
            created_at=now
        )
        
        concerts = [
            Concert(
                id=1,
                tour_id=tour.id,
                venue_id=sample_venues[0].id,
                date=now - timedelta(days=15),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("50.00"),
                tickets_sold=15000,
                created_at=now
            ),
            Concert(
                id=2,
                tour_id=tour.id,
                venue_id=sample_venues[1].id,
                date=now - timedelta(days=5),
                status=ConcertStatus.CANCELLED,
                ticket_price=Decimal("60.00"),
                tickets_sold=0,  # Refunded
                created_at=now
            ),
            Concert(
                id=3,
                tour_id=tour.id,
                venue_id=sample_venues[2].id,
                date=now + timedelta(days=15),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("55.00"),
                tickets_sold=500,
                created_at=now
            )
        ]
        
        with patch('src.services.dashboard.get_tour_by_id') as mock_get_tour, \
             patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            
            mock_get_tour.return_value = tour
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            stats = await dashboard_service.calculate_tour_statistics(tour.id)
            
            # Only completed concerts count towards progress
            assert progress['completed_concerts'] == 1
            assert progress['total_concerts'] == 3
            assert progress['progress_percentage'] == pytest.approx(33.33, rel=1e-2)
            
            # Only completed concerts generate actual revenue
            expected_revenue = Decimal("750000.00")  # 15000 * $50
            assert stats['actual_revenue'] == expected_revenue


class TestDateBasedCalculations:
    """Test date filtering and grouping logic."""
    
    @pytest.mark.asyncio
    async def test_date_filtering_past_vs_future(self, sample_venues):
        """Test proper date-based filtering of past vs future concerts."""
        now = datetime.now(timezone.utc)
        tour = Tour(
            id=1,
            name="Date Test Tour",
            description="Tour for testing date logic",
            status=TourStatus.ACTIVE,
            start_date=now - timedelta(days=60),
            end_date=now + timedelta(days=60),
            created_at=now
        )
        
        concerts = [
            # Far past
            Concert(
                id=1,
                tour_id=tour.id,
                venue_id=sample_venues[0].id,
                date=now - timedelta(days=45),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("50.00"),
                tickets_sold=15000,
                created_at=now
            ),
            # Recent past (within last 7 days)
            Concert(
                id=2,
                tour_id=tour.id,
                venue_id=sample_venues[1].id,
                date=now - timedelta(days=3),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("60.00"),
                tickets_sold=12000,
                created_at=now
            ),
            # Near future (within next 7 days)
            Concert(
                id=3,
                tour_id=tour.id,
                venue_id=sample_venues[2].id,
                date=now + timedelta(days=5),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("55.00"),
                tickets_sold=2000,
                created_at=now
            ),
            # Far future
            Concert(
                id=4,
                tour_id=tour.id,
                venue_id=sample_venues[0].id,
                date=now + timedelta(days=30),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("65.00"),
                tickets_sold=1000,
                created_at=now
            )
        ]
        
        with patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            
            # Test recent concerts filter
            recent_stats = await dashboard_service.get_recent_concert_stats(tour.id, days=7)
            assert recent_stats['recent_completed'] == 1  # Only concert 2
            assert recent_stats['upcoming_soon'] == 1     # Only concert 3
            
            # Test monthly grouping
            monthly_stats = await dashboard_service.get_monthly_concert_stats(tour.id)
            current_month = now.strftime('%Y-%m')
            assert current_month in monthly_stats
    
    @pytest.mark.asyncio
    async def test_timezone_handling(self, sample_venues):
        """Test timezone handling in date calculations."""
        # Use different timezones for testing
        utc_now = datetime.now(timezone.utc)
        
        tour = Tour(
            id=1,
            name="Timezone Test Tour",
            description="Tour for testing timezone logic",
            status=TourStatus.ACTIVE,
            start_date=utc_now - timedelta(days=30),
            end_date=utc_now + timedelta(days=30),
            created_at=utc_now
        )
        
        # Concert at midnight UTC (edge case for date boundaries)
        midnight_concert = Concert(
            id=1,
            tour_id=tour.id,
            venue_id=sample_venues[0].id,
            date=utc_now.replace(hour=0, minute=0, second=0, microsecond=0),
            status=ConcertStatus.SCHEDULED,
            ticket_price=Decimal("50.00"),
            tickets_sold=1000,
            created_at=utc_now
        )
        
        with patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            mock_get_concerts.return_value = [midnight_concert]
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            
            # Ensure consistent date comparison regardless of timezone
            assert progress['total_concerts'] == 1


class TestMathematicalAccuracy:
    """Test mathematical accuracy of percentage calculations and aggregations."""
    
    @pytest.mark.asyncio
    async def test_percentage_calculation_precision(self, sample_venues):
        """Test precision of percentage calculations."""
        now = datetime.now(timezone.utc)
        tour = Tour(
            id=1,
            name="Precision Test Tour",
            description="Tour for testing mathematical precision",
            status=TourStatus.ACTIVE,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30),
            created_at=now
        )
        
        # Create scenario with 1/3 completion for testing precision
        concerts = [
            Concert(
                id=1,
                tour_id=tour.id,
                venue_id=sample_venues[0].id,
                date=now - timedelta(days=15),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("50.00"),
                tickets_sold=10000,
                created_at=now
            ),
            Concert(
                id=2,
                tour_id=tour.id,
                venue_id=sample_venues[1].id,
                date=now + timedelta(days=10),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("60.00"),
                tickets_sold=0,
                created_at=now
            ),
            Concert(
                id=3,
                tour_id=tour.id,
                venue_id=sample_venues[2].id,
                date=now + timedelta(days=20),
                status=ConcertStatus.SCHEDULED,
                ticket_price=Decimal("55.00"),
                tickets_sold=0,
                created_at=now
            )
        ]
        
        with patch('src.services.dashboard.get_tour_by_id') as mock_get_tour, \
             patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            
            mock_get_tour.return_value = tour
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            
            # 1/3 = 33.333...% - test precision
            expected_percentage = 100.0 / 3
            assert progress['progress_percentage'] == pytest.approx(expected_percentage, rel=1e-2)
    
    @pytest.mark.asyncio
    async def test_revenue_aggregation_precision(self, sample_venues):
        """Test precision of revenue aggregation with decimal values."""
        now = datetime.now(timezone.utc)
        tour = Tour(
            id=1,
            name="Revenue Precision Tour",
            description="Tour for testing revenue precision",
            status=TourStatus.ACTIVE,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30),
            created_at=now
        )
        
        # Use prices with decimal precision that could cause floating point issues
        concerts = [
            Concert(
                id=1,
                tour_id=tour.id,
                venue_id=sample_venues[0].id,
                date=now - timedelta(days=15),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("49.99"),  # Common pricing
                tickets_sold=12345,
                created_at=now
            ),
            Concert(
                id=2,
                tour_id=tour.id,
                venue_id=sample_venues[1].id,
                date=now - timedelta(days=5),
                status=ConcertStatus.COMPLETED,
                ticket_price=Decimal("75.50"),
                tickets_sold=8765,
                created_at=now
            )
        ]
        
        with patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            mock_get_concerts.return_value = concerts
            
            dashboard_service = DashboardService()
            stats = await dashboard_service.calculate_tour_statistics(tour.id)
            
            # Calculate expected revenue with exact decimal arithmetic
            expected_revenue = (
                Decimal("49.99") * Decimal("12345") + 
                Decimal("75.50") * Decimal("8765")
            )
            
            assert stats['total_revenue'] == expected_revenue
            assert isinstance(stats['total_revenue'], Decimal)  # Ensure decimal precision
    
    @pytest.mark.asyncio
    async def test_zero_division_handling(self, sample_venues):
        """Test handling of zero division in percentage calculations."""
        now = datetime.now(timezone.utc)
        tour = Tour(
            id=1,
            name="Zero Division Test Tour",
            description="Tour with no concerts",
            status=TourStatus.PLANNING,
            start_date=now + timedelta(days=30),
            end_date=now + timedelta(days=60),
            created_at=now
        )
        
        with patch('src.services.dashboard.get_tour_by_id') as mock_get_tour, \
             patch('src.services.dashboard.get_concerts_by_tour_id') as mock_get_concerts:
            
            mock_get_tour.return_value = tour
            mock_get_concerts.return_value = []  # No concerts
            
            dashboard_service = DashboardService()
            progress = await dashboard_service.calculate_tour_progress(tour.id)
            
            # Should handle zero division gracefully
            assert progress['progress_percentage'] == 0.0
            assert progress['total_concerts'] == 0
            assert progress['completed_concerts'] == 0
