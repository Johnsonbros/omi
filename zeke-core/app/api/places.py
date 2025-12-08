from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging
import uuid

from ..services.place_service import PlaceService
from ..models.place import (
    PlaceCreate,
    PlaceUpdate,
    PlaceResponse,
    PlaceVisitResponse,
    PlaceCategory,
    PlaceContext,
    QuickAddPlaceRequest,
    PlaceTagDB,
    PlaceTagLinkDB,
    PlaceTriggerDB,
    PlaceListDB,
    PlaceListMemberDB,
    PlaceTagResponse,
    PlaceTriggerResponse,
    PlaceTriggerCreate,
    PlaceListResponse,
    PlaceListCreate,
    PlaceDB
)
from ..core.database import get_db_context
from ..models.place import PlaceVisitDB

router = APIRouter()
logger = logging.getLogger(__name__)

USER_ID = "default_user"


def get_place_service() -> PlaceService:
    return PlaceService()


@router.post("/", response_model=PlaceResponse)
async def create_place(
    place_data: PlaceCreate,
    place_service: PlaceService = Depends(get_place_service)
):
    place = await place_service.create_place(
        uid=USER_ID,
        name=place_data.name,
        latitude=place_data.latitude,
        longitude=place_data.longitude,
        radius_meters=place_data.radius_meters,
        category=place_data.category,
        address=place_data.address,
        is_auto_detected=place_data.is_auto_detected,
        metadata_json=place_data.metadata_json
    )
    logger.info(f"Created place: {place.name} (id={place.id})")
    return place


@router.get("/", response_model=List[PlaceResponse])
async def list_places(
    category: Optional[PlaceCategory] = None,
    place_service: PlaceService = Depends(get_place_service)
):
    places = await place_service.list_places(
        uid=USER_ID,
        category=category
    )
    return places


@router.get("/current", response_model=Optional[PlaceResponse])
async def get_current_place(
    place_service: PlaceService = Depends(get_place_service)
):
    place = await place_service.get_current_place(uid=USER_ID)
    return place


@router.get("/nearby", response_model=List[PlaceResponse])
async def find_nearby_places(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    max_distance: float = Query(200.0, description="Maximum distance in meters"),
    place_service: PlaceService = Depends(get_place_service)
):
    places = await place_service.find_nearby_places(
        uid=USER_ID,
        lat=lat,
        lon=lon,
        max_distance_meters=max_distance
    )
    return places


@router.get("/most-visited", response_model=List[PlaceResponse])
async def get_most_visited_places(
    limit: int = Query(10, ge=1, le=50, description="Number of places to return"),
    place_service: PlaceService = Depends(get_place_service)
):
    places = await place_service.get_most_visited_places(
        uid=USER_ID,
        limit=limit
    )
    return places


@router.get("/context", response_model=PlaceContext)
async def get_place_context(
    lat: Optional[float] = Query(None, description="Current latitude"),
    lon: Optional[float] = Query(None, description="Current longitude"),
    place_service: PlaceService = Depends(get_place_service)
):
    context = await place_service.get_place_context(
        uid=USER_ID,
        lat=lat,
        lon=lon
    )
    return context


@router.get("/discover")
async def discover_places(
    min_visits: int = Query(3, ge=1, description="Minimum visits to consider a location"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    place_service: PlaceService = Depends(get_place_service)
):
    """Discover frequently visited locations that aren't saved as places."""
    suggestions = await place_service.discover_frequent_locations(
        uid=USER_ID,
        min_visits=min_visits,
        days_back=days_back
    )
    return suggestions


@router.post("/discover/confirm", response_model=PlaceResponse)
async def confirm_discovered_place(
    request: PlaceCreate,
    place_service: PlaceService = Depends(get_place_service)
):
    """Confirm a discovered location as a saved place."""
    place = await place_service.confirm_discovered_place(
        uid=USER_ID,
        latitude=request.latitude,
        longitude=request.longitude,
        name=request.name,
        category=request.category.value if hasattr(request.category, 'value') else request.category
    )
    logger.info(f"Confirmed discovered place: {place.name} (id={place.id})")
    return place


@router.get("/routines")
async def get_routines(
    days_back: int = Query(28, ge=7, le=365, description="Number of days to analyze"),
    place_service: PlaceService = Depends(get_place_service)
):
    """Get detected routines based on visit patterns."""
    routines = await place_service.get_routines(uid=USER_ID, days_back=days_back)
    return routines


@router.get("/routines/deviation")
async def check_routine_deviation(
    place_service: PlaceService = Depends(get_place_service)
):
    """Check if user is deviating from their typical routine."""
    deviation = await place_service.check_routine_deviation(uid=USER_ID)
    return deviation or {"is_deviation": False}


@router.get("/tags", response_model=List[PlaceTagResponse])
async def list_tags():
    """List all tags for the user."""
    with get_db_context() as db:
        tags = db.query(PlaceTagDB).filter(PlaceTagDB.uid == USER_ID).all()
        return [PlaceTagResponse.model_validate(t) for t in tags]


@router.post("/tags", response_model=PlaceTagResponse)
async def create_tag(name: str, color: Optional[str] = None):
    """Create a new tag."""
    with get_db_context() as db:
        existing = db.query(PlaceTagDB).filter(
            PlaceTagDB.uid == USER_ID,
            PlaceTagDB.name == name
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Tag already exists")
        
        tag = PlaceTagDB(
            id=str(uuid.uuid4()),
            uid=USER_ID,
            name=name,
            color=color
        )
        db.add(tag)
        db.flush()
        return PlaceTagResponse.model_validate(tag)


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: str):
    """Delete a tag."""
    with get_db_context() as db:
        tag = db.query(PlaceTagDB).filter(
            PlaceTagDB.id == tag_id,
            PlaceTagDB.uid == USER_ID
        ).first()
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        db.delete(tag)
        return {"message": "Tag deleted"}


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(
    place_id: str,
    place_service: PlaceService = Depends(get_place_service)
):
    place = await place_service.get_place(place_id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place


@router.put("/{place_id}", response_model=PlaceResponse)
async def update_place(
    place_id: str,
    updates: PlaceUpdate,
    place_service: PlaceService = Depends(get_place_service)
):
    place = await place_service.update_place(
        place_id=place_id,
        updates=updates
    )
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    logger.info(f"Updated place: {place.name} (id={place.id})")
    return place


@router.delete("/{place_id}")
async def delete_place(
    place_id: str,
    place_service: PlaceService = Depends(get_place_service)
):
    deleted = await place_service.delete_place(place_id=place_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Place not found")
    logger.info(f"Deleted place: {place_id}")
    return {"message": "Place deleted successfully", "place_id": place_id}


@router.get("/{place_id}/stats")
async def get_place_stats(
    place_id: str,
    place_service: PlaceService = Depends(get_place_service)
):
    stats = await place_service.get_place_stats(place_id=place_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Place not found")
    return stats


@router.get("/{place_id}/visits", response_model=List[PlaceVisitResponse])
async def get_place_visits(
    place_id: str,
    limit: int = Query(50, ge=1, le=200, description="Number of visits to return")
):
    with get_db_context() as db:
        visits = db.query(PlaceVisitDB).filter(
            PlaceVisitDB.place_id == place_id
        ).order_by(PlaceVisitDB.entered_at.desc()).limit(limit).all()
        
        if not visits:
            place_exists = db.query(PlaceVisitDB).filter(
                PlaceVisitDB.place_id == place_id
            ).first()
            from ..models.place import PlaceDB
            place_exists = db.query(PlaceDB).filter(PlaceDB.id == place_id).first()
            if not place_exists:
                raise HTTPException(status_code=404, detail="Place not found")
        
        return [PlaceVisitResponse.model_validate(v) for v in visits]


@router.post("/quick-add", response_model=PlaceResponse)
async def quick_add_place(
    request: QuickAddPlaceRequest,
    place_service: PlaceService = Depends(get_place_service)
):
    """Quick add a place from current location with minimal info."""
    name = request.name or f"Location {datetime.now().strftime('%b %d %I:%M%p')}"
    
    place = await place_service.create_place(
        uid=USER_ID,
        name=name,
        latitude=request.latitude,
        longitude=request.longitude,
        radius_meters=100.0,
        category=request.category,
        is_auto_detected=False,
        metadata_json={"created_via": "quick_add"}
    )
    
    if request.tags:
        with get_db_context() as db:
            for tag_name in request.tags:
                tag = db.query(PlaceTagDB).filter(
                    PlaceTagDB.uid == USER_ID,
                    PlaceTagDB.name == tag_name
                ).first()
                if not tag:
                    tag = PlaceTagDB(
                        id=str(uuid.uuid4()),
                        uid=USER_ID,
                        name=tag_name
                    )
                    db.add(tag)
                    db.flush()
                
                link = PlaceTagLinkDB(place_id=place.id, tag_id=tag.id)
                db.add(link)
    
    logger.info(f"Quick added place: {place.name} (id={place.id})")
    return place


@router.get("/{place_id}/tags", response_model=List[PlaceTagResponse])
async def get_place_tags(place_id: str):
    """Get all tags for a place."""
    with get_db_context() as db:
        place = db.query(PlaceDB).filter(PlaceDB.id == place_id).first()
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        return [PlaceTagResponse.model_validate(t) for t in place.tags]


@router.post("/{place_id}/tags/{tag_id}")
async def add_tag_to_place(place_id: str, tag_id: str):
    """Add a tag to a place."""
    with get_db_context() as db:
        place = db.query(PlaceDB).filter(PlaceDB.id == place_id).first()
        tag = db.query(PlaceTagDB).filter(PlaceTagDB.id == tag_id).first()
        if not place or not tag:
            raise HTTPException(status_code=404, detail="Place or tag not found")
        
        existing = db.query(PlaceTagLinkDB).filter(
            PlaceTagLinkDB.place_id == place_id,
            PlaceTagLinkDB.tag_id == tag_id
        ).first()
        if not existing:
            link = PlaceTagLinkDB(place_id=place_id, tag_id=tag_id)
            db.add(link)
        return {"message": "Tag added to place"}


@router.delete("/{place_id}/tags/{tag_id}")
async def remove_tag_from_place(place_id: str, tag_id: str):
    """Remove a tag from a place."""
    with get_db_context() as db:
        link = db.query(PlaceTagLinkDB).filter(
            PlaceTagLinkDB.place_id == place_id,
            PlaceTagLinkDB.tag_id == tag_id
        ).first()
        if link:
            db.delete(link)
        return {"message": "Tag removed from place"}


@router.get("/{place_id}/triggers", response_model=List[PlaceTriggerResponse])
async def get_place_triggers(place_id: str):
    """Get all triggers for a place."""
    with get_db_context() as db:
        triggers = db.query(PlaceTriggerDB).filter(
            PlaceTriggerDB.place_id == place_id
        ).all()
        return [PlaceTriggerResponse.model_validate(t) for t in triggers]


@router.post("/{place_id}/triggers", response_model=PlaceTriggerResponse)
async def create_place_trigger(place_id: str, trigger: PlaceTriggerCreate):
    """Create a new trigger for a place."""
    with get_db_context() as db:
        place = db.query(PlaceDB).filter(PlaceDB.id == place_id).first()
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        new_trigger = PlaceTriggerDB(
            id=str(uuid.uuid4()),
            uid=USER_ID,
            place_id=place_id,
            name=trigger.name,
            trigger_type=trigger.trigger_type.value,
            action_type=trigger.action_type.value,
            action_payload=trigger.action_payload,
            enabled=trigger.enabled,
            cooldown_minutes=trigger.cooldown_minutes
        )
        db.add(new_trigger)
        db.flush()
        logger.info(f"Created trigger: {new_trigger.name} for place {place_id}")
        return PlaceTriggerResponse.model_validate(new_trigger)


@router.put("/{place_id}/triggers/{trigger_id}")
async def update_trigger(place_id: str, trigger_id: str, enabled: bool):
    """Enable or disable a trigger."""
    with get_db_context() as db:
        trigger = db.query(PlaceTriggerDB).filter(
            PlaceTriggerDB.id == trigger_id,
            PlaceTriggerDB.place_id == place_id
        ).first()
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")
        trigger.enabled = enabled
        return {"message": "Trigger updated"}


@router.delete("/{place_id}/triggers/{trigger_id}")
async def delete_trigger(place_id: str, trigger_id: str):
    """Delete a trigger."""
    with get_db_context() as db:
        trigger = db.query(PlaceTriggerDB).filter(
            PlaceTriggerDB.id == trigger_id,
            PlaceTriggerDB.place_id == place_id
        ).first()
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")
        db.delete(trigger)
        return {"message": "Trigger deleted"}


@router.get("/lists/all", response_model=List[PlaceListResponse])
async def list_place_lists():
    """List all place lists for the user."""
    with get_db_context() as db:
        lists = db.query(PlaceListDB).filter(PlaceListDB.uid == USER_ID).all()
        result = []
        for lst in lists:
            count = db.query(PlaceListMemberDB).filter(
                PlaceListMemberDB.list_id == lst.id
            ).count()
            resp = PlaceListResponse(
                id=lst.id,
                name=lst.name,
                description=lst.description,
                icon=lst.icon,
                color=lst.color,
                place_count=count,
                created_at=lst.created_at
            )
            result.append(resp)
        return result


@router.post("/lists", response_model=PlaceListResponse)
async def create_place_list(list_data: PlaceListCreate):
    """Create a new place list."""
    with get_db_context() as db:
        existing = db.query(PlaceListDB).filter(
            PlaceListDB.uid == USER_ID,
            PlaceListDB.name == list_data.name
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="List already exists")
        
        new_list = PlaceListDB(
            id=str(uuid.uuid4()),
            uid=USER_ID,
            name=list_data.name,
            description=list_data.description,
            icon=list_data.icon,
            color=list_data.color
        )
        db.add(new_list)
        db.flush()
        return PlaceListResponse(
            id=new_list.id,
            name=new_list.name,
            description=new_list.description,
            icon=new_list.icon,
            color=new_list.color,
            place_count=0,
            created_at=new_list.created_at
        )


@router.delete("/lists/{list_id}")
async def delete_place_list(list_id: str):
    """Delete a place list."""
    with get_db_context() as db:
        lst = db.query(PlaceListDB).filter(
            PlaceListDB.id == list_id,
            PlaceListDB.uid == USER_ID
        ).first()
        if not lst:
            raise HTTPException(status_code=404, detail="List not found")
        db.delete(lst)
        return {"message": "List deleted"}


@router.get("/lists/{list_id}/places", response_model=List[PlaceResponse])
async def get_list_places(
    list_id: str,
    place_service: PlaceService = Depends(get_place_service)
):
    """Get all places in a list."""
    with get_db_context() as db:
        lst = db.query(PlaceListDB).filter(PlaceListDB.id == list_id).first()
        if not lst:
            raise HTTPException(status_code=404, detail="List not found")
        
        place_ids = [m.place_id for m in db.query(PlaceListMemberDB).filter(
            PlaceListMemberDB.list_id == list_id
        ).all()]
        
        places = []
        for pid in place_ids:
            place = await place_service.get_place(pid)
            if place:
                places.append(place)
        return places


@router.post("/lists/{list_id}/places/{place_id}")
async def add_place_to_list(list_id: str, place_id: str):
    """Add a place to a list."""
    with get_db_context() as db:
        lst = db.query(PlaceListDB).filter(PlaceListDB.id == list_id).first()
        place = db.query(PlaceDB).filter(PlaceDB.id == place_id).first()
        if not lst or not place:
            raise HTTPException(status_code=404, detail="List or place not found")
        
        existing = db.query(PlaceListMemberDB).filter(
            PlaceListMemberDB.list_id == list_id,
            PlaceListMemberDB.place_id == place_id
        ).first()
        if not existing:
            member = PlaceListMemberDB(list_id=list_id, place_id=place_id)
            db.add(member)
        return {"message": "Place added to list"}


@router.delete("/lists/{list_id}/places/{place_id}")
async def remove_place_from_list(list_id: str, place_id: str):
    """Remove a place from a list."""
    with get_db_context() as db:
        member = db.query(PlaceListMemberDB).filter(
            PlaceListMemberDB.list_id == list_id,
            PlaceListMemberDB.place_id == place_id
        ).first()
        if member:
            db.delete(member)
        return {"message": "Place removed from list"}


@router.get("/{place_id}/lists", response_model=List[PlaceListResponse])
async def get_place_lists(place_id: str):
    """Get all lists a place belongs to."""
    with get_db_context() as db:
        place = db.query(PlaceDB).filter(PlaceDB.id == place_id).first()
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        list_ids = [m.list_id for m in db.query(PlaceListMemberDB).filter(
            PlaceListMemberDB.place_id == place_id
        ).all()]
        
        result = []
        for lid in list_ids:
            lst = db.query(PlaceListDB).filter(PlaceListDB.id == lid).first()
            if lst:
                count = db.query(PlaceListMemberDB).filter(
                    PlaceListMemberDB.list_id == lid
                ).count()
                result.append(PlaceListResponse(
                    id=lst.id,
                    name=lst.name,
                    description=lst.description,
                    icon=lst.icon,
                    color=lst.color,
                    place_count=count,
                    created_at=lst.created_at
                ))
        return result
