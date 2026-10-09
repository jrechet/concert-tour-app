"""Concert-facing endpoints: the JSON list/detail API and the HTMX
dashboard concert-card fragments."""

from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..database import get_db, get_reference_time
from ..models import Concert, LineupEntry, Tour, Venue
from ..schemas import (
    CancelConcertRequest,
    ConcertNextResponse,
    ConcertNotesUpdate,
    ConcertPriceFilter,
    ConcertRescheduleRequest,
    ConcertResponse,
    LineupEntryCreate,
    LineupEntryOut,
    LineupEntryResponse,
    LineupReorderRequest,
    NextConcertCity,
    NextConcertVenue,
    OccupancyResponse,
    RefundRequest,
    TicketPriceUpdate,
    TicketPurchaseRequest,
)
from ..services.concerts_service import (
    ConcertCancelledError,
    ConcertCapacityExceededError,
    ConcertNotFoundError,
    InsufficientSoldTicketsError,
    InvalidDateError,
    apply_price_filter,
    generate_concerts_csv,
    get_concert_occupancy,
    get_concerts_between_dates,
    get_next_concert,
    get_sold_out_concerts,
    refund_tickets,
    reschedule_concert,
    sell_tickets,
    update_ticket_price,
)
from ..services.concerts_service import get_upcoming_concerts as fetch_upcoming_concerts
from ..services.lineup_service import (
    InvalidSetOrderError,
    LineupEntryNotFoundError,
    clear_lineup,
    delete_lineup_entry,
    reorder_lineup_entry,
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
api_router = APIRouter(prefix="/api/v1/concerts", tags=["concerts"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


TRUTHY_VALUES = {"true", "1", "yes", "on"}


def coerce_show_past(show_past: Optional[str] = Query(None, description="When 'true', past concerts are included alongside upcoming ones")) -> bool:
    """Coerce the raw `show_past` query string to a boolean, safely.

    Accepted as a raw string (rather than FastAPI's native `bool` query
    type) so any value other than a recognized truthy token — missing,
    blank, malformed, or unexpected — falls back to `False` rather than
    raising a 422/500, per the "hide past concerts by default" contract.
    """
    if show_past is None:
        return False
    return show_past.strip().lower() in TRUTHY_VALUES


def get_price_filter(
    min_price: Optional[float] = Query(None, ge=0, description="Only include concerts priced at or above this amount"),
    max_price: Optional[float] = Query(None, ge=0, description="Only include concerts priced at or below this amount"),
) -> ConcertPriceFilter:
    """Validate and bundle the `min_price`/`max_price` query params.

    Runs as a FastAPI dependency, ahead of the endpoint body, so an invalid
    combination (`min_price` above `max_price`) is rejected with a standard
    422 validation error rather than the endpoint having to check for it.
    """
    try:
        return ConcertPriceFilter(min_price=min_price, max_price=max_price)
    except ValidationError as exc:
        raise RequestValidationError(
            [{**error, "loc": ("query", *error["loc"])} for error in exc.errors()]
        )


@api_router.get("/", response_model=List[ConcertResponse])
def get_concerts(
    response: Response,
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Items per page, up to {MAX_PAGE_SIZE}",
    ),
    skip: Optional[int] = Query(
        None, ge=0, description="Deprecated alias for offset; overrides `page` when given"
    ),
    limit: Optional[int] = Query(
        None, ge=1, le=MAX_PAGE_SIZE, description="Deprecated alias for `page_size`; overrides it when given"
    ),
    city: Optional[str] = Query(
        None, description="Filter concerts to venues whose city contains this text (case-insensitive)"
    ),
    venue: Optional[str] = Query(
        None, description="Filter concerts to the venue whose name matches this text (case-insensitive)"
    ),
    artist_name: Optional[str] = Query(
        None, description="Filter concerts to tours whose artist name contains this text (case-insensitive)"
    ),
    include_cancelled: bool = Query(
        True, description="When false, cancelled concerts are excluded from the results"
    ),
    upcoming_only: bool = Query(
        False, description="When true, only concerts today or later are returned, soonest first, and past concerts are excluded rather than appended"
    ),
    price_filter: ConcertPriceFilter = Depends(get_price_filter),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve all concerts with pagination, including remaining ticket
    counts and sold-out status derived from each concert's venue.

    Pagination is 1-indexed via `page` (default 1) and `page_size` (default
    `DEFAULT_PAGE_SIZE`, capped at `MAX_PAGE_SIZE`); requesting a `page_size`
    above the cap, or a non-positive `page`/`page_size`, is rejected with a
    422 rather than silently clamped. The total number of matching concerts
    (after filters, before pagination) is returned in the `X-Total-Count`
    response header. `skip`/`limit` remain as deprecated offset/limit
    aliases for existing clients and, when given, take precedence over
    `page`/`page_size`.

    Results are ordered chronologically by default: upcoming concerts
    (today or later, compared by calendar date against `reference_time`)
    come first, soonest first, with past concerts appended afterward,
    oldest first.

    When `city` is provided and non-blank, results are narrowed to concerts
    whose venue city contains that text (case-insensitive substring match)
    before pagination is applied; a blank value is treated the same as
    omitting the filter. When `venue` is provided and non-blank, results are
    narrowed to concerts whose venue name exactly matches that text
    (case-insensitive) before pagination is applied; a blank value is
    treated the same as omitting the filter, and a name with no matching
    venue yields an empty list rather than an error. When `artist_name` is provided, results are narrowed to
    concerts whose tour artist name contains that text (case-insensitive
    substring match) before pagination is applied. When `include_cancelled`
    is false, cancelled concerts are excluded before pagination is applied;
    it defaults to true so existing clients see no change in behavior. When
    `upcoming_only` is true, past concerts are excluded entirely (rather than
    appended after upcoming ones), so the soonest concert is always first;
    it defaults to false so existing clients see no change in behavior.

    `min_price`/`max_price` are accepted and validated (each must be >= 0,
    and `min_price` may not exceed `max_price` when both are given, or the
    request is rejected with a 422) and applied to the results as an
    inclusive range before pagination. Concerts with no `ticket_price` set
    are excluded whenever either bound is given, since a null price can't be
    compared against a threshold; when neither bound is given, such concerts
    are still included, unchanged from prior behavior.
    """
    is_past = case(
        (func.date(Concert.date_time) < func.date(reference_time), 1),
        else_=0,
    )
    query = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .order_by(is_past, Concert.date_time)
    )

    if city or venue:
        query = query.join(Concert.venue)
        if city:
            query = query.filter(func.lower(Venue.city).contains(city.lower(), autoescape=True))
        if venue:
            query = query.filter(func.lower(Venue.name) == venue.lower())

    if artist_name is not None:
        query = query.join(Concert.tour).filter(func.lower(Tour.artist).contains(artist_name.lower()))

    if not include_cancelled:
        query = query.filter(Concert.is_cancelled.is_(False))

    if upcoming_only:
        query = query.filter(func.date(Concert.date_time) >= func.date(reference_time))

    query = apply_price_filter(query, price_filter)

    response.headers["X-Total-Count"] = str(query.count())

    offset = skip if skip is not None else (page - 1) * page_size
    effective_limit = limit if limit is not None else page_size
    concerts = query.offset(offset).limit(effective_limit).all()
    return concerts


@api_router.get("/cities", response_model=List[str])
def get_concert_cities(db: Session = Depends(get_db)):
    """Retrieve the distinct list of cities hosting at least one concert,
    sorted alphabetically, for populating a city filter control.
    """
    rows = (
        db.query(Venue.city)
        .join(Concert, Concert.venue_id == Venue.id)
        .distinct()
        .order_by(Venue.city)
        .all()
    )
    return [row[0] for row in rows]


@api_router.get("/upcoming", response_model=List[ConcertResponse])
def get_upcoming_concerts(
    show_past: bool = Depends(coerce_show_past),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve concerts ordered soonest first.

    By default (no `show_past` param, or any value other than a recognized
    truthy token), a concert is upcoming when its calendar date (compared
    against `reference_time`) is today or in the future; past concerts are
    excluded entirely rather than appended, unlike `GET /`. When
    `show_past=true`, past concerts are included too, still ordered
    chronologically.
    """
    return fetch_upcoming_concerts(db, reference_time, show_past=show_past)


@api_router.get(
    "/next",
    response_model=ConcertNextResponse,
    responses={
        404: {
            "description": "No upcoming, non-cancelled concert exists.",
            "content": {"application/json": {"example": {"detail": "No upcoming concert"}}},
        },
    },
)
def get_next_concert_endpoint(
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve the soonest upcoming, non-cancelled concert, with its venue
    and city nested.

    Registered ahead of `/{concert_id}` so the literal `next` path segment
    isn't swallowed as a concert ID. Returns 404 when no such concert exists.
    """
    concert = get_next_concert(db, reference_time)
    if concert is None:
        raise HTTPException(status_code=404, detail="No upcoming concert")
    return ConcertNextResponse(
        id=concert.id,
        date_time=concert.date_time,
        is_cancelled=concert.is_cancelled,
        venue=NextConcertVenue(name=concert.venue.name, capacity=concert.venue.capacity),
        city=NextConcertCity(name=concert.venue.city, country=concert.venue.country),
    )


@api_router.get("/export.csv")
def export_concerts_csv(db: Session = Depends(get_db)):
    """Stream every concert as a CSV file with columns date, city, venue, tour.

    Registered ahead of `/{concert_id}` so the literal `export.csv` path
    segment isn't swallowed as a concert ID.
    """
    return StreamingResponse(
        generate_concerts_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=concerts.csv"},
    )


@api_router.get("/sold-out", response_model=List[ConcertResponse])
def get_sold_out_concerts_endpoint(
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Retrieve upcoming, non-cancelled concerts that have sold out, soonest first.

    Registered ahead of `/{concert_id}` so the literal `sold-out` path
    segment isn't swallowed as a concert ID. Returns an empty list (not a
    404) when no concert is currently sold out.
    """
    return get_sold_out_concerts(db, reference_time)


@api_router.get(
    "/between",
    response_model=List[ConcertResponse],
    responses={
        422: {
            "description": "`start` is after `end`, or either is missing/malformed.",
            "content": {"application/json": {"example": {"detail": "start must not be after end"}}},
        },
    },
)
def get_concerts_between(
    start: date = Query(..., description="Start of the date range (YYYY-MM-DD), inclusive"),
    end: date = Query(..., description="End of the date range (YYYY-MM-DD), inclusive"),
    db: Session = Depends(get_db),
):
    """Retrieve concerts whose date falls within `start`/`end`, inclusive, soonest first.

    Registered ahead of `/{concert_id}` so the literal `between` path segment
    isn't swallowed as a concert ID. `start` and `end` are required `date`
    query parameters, so a missing or malformed value is rejected with a 422
    by FastAPI itself; a `start` after `end` is rejected with an explicit 422
    here.
    """
    if start > end:
        raise HTTPException(status_code=422, detail="start must not be after end")
    return get_concerts_between_dates(db, start, end)


@api_router.get("/{concert_id}", response_model=ConcertResponse)
def get_concert(concert_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific concert by ID."""
    concert = (
        db.query(Concert)
        .options(joinedload(Concert.venue))
        .filter(Concert.id == concert_id)
        .first()
    )
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    return concert


@api_router.patch(
    "/{concert_id}",
    response_model=ConcertResponse,
    responses={
        404: {
            "description": "No concert exists with the given `concert_id`.",
            "content": {"application/json": {"example": {"detail": "Concert not found"}}},
        },
        409: {
            "description": "The concert has been cancelled and cannot be rescheduled.",
            "content": {"application/json": {"example": {"detail": "Concert 1 is cancelled"}}},
        },
        422: {
            "description": "The requested `date_time` is not in the future.",
            "content": {
                "application/json": {
                    "example": {"detail": "new_date_time 2024-01-01 00:00:00 must be in the future"}
                }
            },
        },
    },
)
def reschedule_concert_endpoint(
    concert_id: int, payload: ConcertRescheduleRequest, db: Session = Depends(get_db)
):
    """Reschedule a concert to a new `date_time`.

    Returns 404 for an unknown concert, 409 if the concert has been
    cancelled, and 422 if the new `date_time` is not in the future.
    """
    try:
        return reschedule_concert(db, concert_id, payload.date_time)
    except ConcertNotFoundError:
        raise HTTPException(status_code=404, detail="Concert not found")
    except ConcertCancelledError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidDateError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@api_router.patch(
    "/{concert_id}/price",
    response_model=ConcertResponse,
    responses={
        404: {
            "description": "No concert exists with the given `concert_id`.",
            "content": {"application/json": {"example": {"detail": "Concert not found"}}},
        },
        409: {
            "description": "The concert has been cancelled and its price cannot be updated.",
            "content": {"application/json": {"example": {"detail": "Concert 1 is cancelled"}}},
        },
        422: {
            "description": "`ticket_price` is negative or missing.",
        },
    },
)
def update_concert_ticket_price(
    concert_id: int, payload: TicketPriceUpdate, db: Session = Depends(get_db)
):
    """Update the ticket price for a concert.

    Returns 404 for an unknown concert and 409 if the concert has been
    cancelled. A negative `ticket_price` is rejected with a 422 by
    `TicketPriceUpdate` itself.
    """
    try:
        return update_ticket_price(db, concert_id, payload.ticket_price)
    except ConcertNotFoundError:
        raise HTTPException(status_code=404, detail="Concert not found")
    except ConcertCancelledError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@api_router.put(
    "/{concert_id}/notes",
    response_model=ConcertResponse,
    responses={
        404: {
            "description": "No concert exists with the given `concert_id`.",
            "content": {"application/json": {"example": {"detail": "Concert not found"}}},
        },
        422: {
            "description": "`notes` exceeds the 500-character limit.",
        },
    },
)
def update_concert_notes(concert_id: int, payload: ConcertNotesUpdate, db: Session = Depends(get_db)):
    """Update the free-text `notes` for a concert.

    Returns 404 for an unknown concert. `notes` above 500 characters is
    rejected with a 422 by `ConcertNotesUpdate` itself.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")

    concert.notes = payload.notes
    db.commit()
    db.refresh(concert)
    return concert


@api_router.post("/{concert_id}/cancel", response_model=ConcertResponse)
def cancel_concert(concert_id: int, payload: CancelConcertRequest, db: Session = Depends(get_db)):
    """Cancel a concert, recording the reason.

    Returns 404 for an unknown concert and 409 if the concert is already
    cancelled.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    if concert.is_cancelled:
        raise HTTPException(status_code=409, detail="Concert is already cancelled")

    concert.is_cancelled = True
    concert.cancellation_reason = payload.reason
    db.commit()
    db.refresh(concert)
    return concert


@api_router.post("/{concert_id}/uncancel", response_model=ConcertResponse)
def uncancel_concert(concert_id: int, db: Session = Depends(get_db)):
    """Restore a cancelled concert, clearing the cancellation reason.

    Returns 404 for an unknown concert and 409 if the concert is not
    currently cancelled.
    """
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(status_code=404, detail="Concert not found")
    if not concert.is_cancelled:
        raise HTTPException(status_code=409, detail="Concert is not cancelled")

    concert.is_cancelled = False
    concert.cancellation_reason = None
    db.commit()
    db.refresh(concert)
    return concert


@api_router.post("/{concert_id}/tickets", response_model=ConcertResponse)
def buy_tickets(concert_id: int, payload: TicketPurchaseRequest, db: Session = Depends(get_db)):
    """Purchase `quantity` tickets for a concert.

    Returns 404 for an unknown concert, and 409 if the concert has been
    cancelled or the purchase would exceed the venue's capacity. Quantities
    below 1 are rejected with a 422 by `TicketPurchaseRequest` itself.
    """
    try:
        return sell_tickets(concert_id, payload.quantity, db)
    except ConcertNotFoundError:
        raise HTTPException(status_code=404, detail="Concert not found")
    except ConcertCancelledError:
        raise HTTPException(status_code=409, detail="Concert is cancelled")
    except ConcertCapacityExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@api_router.post("/{concert_id}/refunds", response_model=ConcertResponse)
def refund_tickets_endpoint(concert_id: int, payload: RefundRequest, db: Session = Depends(get_db)):
    """Refund `quantity` previously sold tickets for a concert.

    Returns 404 for an unknown concert, and 409 if the refund quantity
    exceeds the concert's currently sold tickets. Quantities below 1 are
    rejected with a 422 by `RefundRequest` itself.
    """
    try:
        return refund_tickets(concert_id, payload.quantity, db)
    except ConcertNotFoundError:
        raise HTTPException(status_code=404, detail="Concert not found")
    except InsufficientSoldTicketsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@api_router.get("/{concert_id}/lineup", response_model=List[LineupEntryResponse])
def get_concert_lineup(
    concert_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Retrieve the supporting-act lineup for a concert, in running order
    (ascending `set_order`), with pagination.

    Returns 404 when the concert itself doesn't exist, but an empty list
    (not an error) when the concert exists and simply has no lineup entries.
    """
    concert_exists = db.query(Concert.id).filter(Concert.id == concert_id).first()
    if not concert_exists:
        raise HTTPException(status_code=404, detail="Concert not found")

    entries = (
        db.query(LineupEntry)
        .filter(LineupEntry.concert_id == concert_id)
        .order_by(LineupEntry.set_order)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return entries


@api_router.post(
    "/{concert_id}/lineup",
    response_model=LineupEntryOut,
    status_code=201,
    responses={
        404: {
            "description": "No concert exists with the given `concert_id`.",
            "content": {"application/json": {"example": {"detail": "Concert not found"}}},
        },
        409: {
            "description": "A lineup entry already exists for this concert with the given `set_order`.",
            "content": {
                "application/json": {"example": {"detail": "set_order 1 is already taken for this concert"}}
            },
        },
    },
)
def create_concert_lineup_entry(
    concert_id: int, payload: LineupEntryCreate, db: Session = Depends(get_db)
):
    """Add a supporting act to a concert's lineup.

    Returns 404 when the concert doesn't exist and 409 when `set_order` is
    already taken for it. The 409 is both pre-checked (for the common case)
    and enforced as a fallback against the DB's unique constraint, so a
    concurrent insert for the same slot can never surface as a 500.
    """
    concert_exists = db.query(Concert.id).filter(Concert.id == concert_id).first()
    if not concert_exists:
        raise HTTPException(status_code=404, detail="Concert not found")

    conflict_detail = f"set_order {payload.set_order} is already taken for this concert"

    existing = (
        db.query(LineupEntry.id)
        .filter(
            LineupEntry.concert_id == concert_id,
            LineupEntry.set_order == payload.set_order,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=conflict_detail)

    entry = LineupEntry(
        concert_id=concert_id,
        artist_name=payload.artist_name,
        set_order=payload.set_order,
    )
    db.add(entry)
    try:
        db.commit()
    except (IntegrityError, ValueError):
        db.rollback()
        raise HTTPException(status_code=409, detail=conflict_detail)
    db.refresh(entry)
    return entry


@api_router.delete(
    "/{concert_id}/lineup",
    status_code=204,
    responses={
        404: {
            "description": "No concert exists with the given `concert_id`.",
            "content": {"application/json": {"example": {"detail": "Concert not found"}}},
        },
    },
)
def clear_concert_lineup(concert_id: int, db: Session = Depends(get_db)):
    """Remove every supporting-act lineup entry from a concert.

    Returns 404 when the concert doesn't exist. The concert's other data is
    left untouched.
    """
    try:
        clear_lineup(db, concert_id=concert_id)
    except ConcertNotFoundError:
        raise HTTPException(status_code=404, detail="Concert not found")
    return Response(status_code=204)


@api_router.delete(
    "/{concert_id}/lineup/{entry_id}",
    status_code=204,
    responses={
        404: {
            "description": "No concert exists with the given `concert_id`, no lineup entry exists with the given `entry_id`, or the entry belongs to a different concert.",
            "content": {"application/json": {"example": {"detail": "Concert not found"}}},
        },
    },
)
def delete_concert_lineup_entry(concert_id: int, entry_id: int, db: Session = Depends(get_db)):
    """Remove a supporting act from a concert's lineup.

    Returns 404 when the concert doesn't exist, when the entry doesn't
    exist, or when the entry belongs to a different concert.
    """
    try:
        delete_lineup_entry(db, concert_id=concert_id, entry_id=entry_id)
    except ConcertNotFoundError:
        raise HTTPException(status_code=404, detail="Concert not found")
    except LineupEntryNotFoundError:
        raise HTTPException(status_code=404, detail="Lineup entry not found")
    return Response(status_code=204)


@api_router.patch(
    "/{concert_id}/lineup/{entry_id}",
    response_model=LineupEntryOut,
    responses={
        404: {
            "description": "No concert exists with the given `concert_id`, no lineup entry exists with the given `entry_id`, or the entry belongs to a different concert.",
            "content": {"application/json": {"example": {"detail": "Concert not found"}}},
        },
        422: {
            "description": "`set_order` is zero or negative.",
            "content": {
                "application/json": {"example": {"detail": "new_set_order must be a positive integer"}}
            },
        },
    },
)
def reorder_concert_lineup_entry(
    concert_id: int, entry_id: int, payload: LineupReorderRequest, db: Session = Depends(get_db)
):
    """Move a supporting act to a new running-order position, shifting
    siblings to keep `set_order` contiguous within the concert.

    Returns 404 when the concert doesn't exist, when the entry doesn't
    exist, or when the entry belongs to a different concert. Returns 422
    when `set_order` is not a positive integer.
    """
    try:
        return reorder_lineup_entry(db, concert_id=concert_id, entry_id=entry_id, new_set_order=payload.set_order)
    except ConcertNotFoundError:
        raise HTTPException(status_code=404, detail="Concert not found")
    except LineupEntryNotFoundError:
        raise HTTPException(status_code=404, detail="Lineup entry not found")
    except InvalidSetOrderError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@api_router.get(
    "/{concert_id}/occupancy",
    response_model=OccupancyResponse,
    responses={
        200: {
            "description": "Ticket sales relative to venue capacity for the concert.",
            "content": {
                "application/json": {
                    "examples": {
                        "known_capacity": {
                            "summary": "Venue capacity is known",
                            "value": {
                                "concert_id": 1,
                                "tickets_sold": 15000,
                                "capacity": 20000,
                                "percentage_sold": 75.0,
                            },
                        },
                        "unknown_capacity": {
                            "summary": "Venue capacity is not set",
                            "value": {
                                "concert_id": 2,
                                "tickets_sold": 500,
                                "capacity": None,
                                "percentage_sold": None,
                            },
                        },
                    }
                }
            },
        },
        404: {
            "description": "No concert exists with the given `concert_id`.",
            "content": {
                "application/json": {"example": {"detail": "Concert not found"}}
            },
        },
    },
)
def get_concert_occupancy_endpoint(concert_id: int, db: Session = Depends(get_db)):
    """Retrieve ticket sales relative to venue capacity for a concert.

    Returns 404 when the concert doesn't exist. `capacity` and
    `percentage_sold` are null when the concert's venue has no capacity set.
    A venue capacity of 0 is treated the same as unknown, since a
    percentage can't be computed without dividing by zero.
    """
    occupancy = get_concert_occupancy(db, concert_id)
    if occupancy is None:
        raise HTTPException(status_code=404, detail="Concert not found")
    return occupancy


@router.get("/concerts")
def get_dashboard_concerts(
    request: Request,
    artist_name: Optional[str] = Query(
        None, description="Filter concerts to tours whose artist name contains this text (case-insensitive)"
    ),
    include_cancelled: bool = Query(
        True, description="When false, cancelled concerts are excluded from the results"
    ),
    upcoming_only: bool = Query(
        False, description="When true, only concerts today or later are returned, soonest first, for the public-facing view"
    ),
    show_past: bool = Depends(coerce_show_past),
    db: Session = Depends(get_db),
    reference_time: datetime = Depends(get_reference_time),
):
    """Render concert cards showing date, venue, and ticket availability.

    When `artist_name` is provided and non-blank, results are narrowed to
    concerts whose tour artist name contains that text (case-insensitive
    substring match). A blank value — e.g. a cleared search box — is
    treated the same as omitting the filter, restoring the full list.

    When `include_cancelled` is false, cancelled concerts are excluded.
    Defaults to true so the list shows everything unless the caller opts
    into hiding cancelled dates.

    When `upcoming_only` is true, past concerts are excluded and the list is
    ordered soonest first, so the first card is always the next upcoming
    show; the template highlights it accordingly. Defaults to false so
    existing callers see no change in behavior. When `show_past` is also
    true (via the "Show past concerts" toggle), it overrides
    `upcoming_only`'s date filter so past concerts are included again,
    still ordered chronologically; the "Next Show" badge is then withheld
    since the first card may no longer be an upcoming show.
    """
    query = db.query(Concert).options(joinedload(Concert.venue)).order_by(Concert.date_time)

    if artist_name:
        query = query.join(Concert.tour).filter(func.lower(Tour.artist).contains(artist_name.lower()))

    if not include_cancelled:
        query = query.filter(Concert.is_cancelled.is_(False))

    if upcoming_only and not show_past:
        query = query.filter(func.date(Concert.date_time) >= func.date(reference_time))

    concerts = query.all()
    return templates.TemplateResponse(
        request,
        "dashboard_concerts.html",
        {
            "concerts": concerts,
            "upcoming_only": upcoming_only,
            "show_past": show_past,
            "reference_time": reference_time,
        },
    )
