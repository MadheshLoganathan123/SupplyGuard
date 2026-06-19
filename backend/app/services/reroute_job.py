import asyncio
from app.database.session import AsyncSessionLocal
from app.services.shipment_service import ShipmentService
from app.models.shipment import ShipmentStatus
import logging

logger = logging.getLogger(__name__)

async def run_reroute_job(shipment_id: str):
    logger.info(f"Starting reroute job for shipment {shipment_id}")
    await asyncio.sleep(4)  # Simulate AI computation
    
    async with AsyncSessionLocal() as db:
        svc = ShipmentService(db)
        shipment = await svc.get_by_id(shipment_id)
        if shipment:
            shipment.status = ShipmentStatus.REROUTED
            await db.commit()
            logger.info(f"Shipment {shipment_id} successfully rerouted.")
        else:
            logger.warning(f"Shipment {shipment_id} not found during reroute job.")
