import logging

from celery import shared_task

logger = logging.getLogger("kreo.media")


@shared_task
def scan_asset(asset_id: str):
    """Scan antivirus. Un scanner (ClamAV) se branche ici ; sans scanner, le fichier est marqué sain
    après validation du type MIME par signature et de l'image par Pillow."""
    from .models import MediaAsset

    asset = MediaAsset.objects.filter(id=asset_id).first()
    if asset is None:
        return
    asset.scan_status = MediaAsset.ScanStatus.CLEAN
    asset.save(update_fields=["scan_status"])
    logger.info("asset scanned", extra={"event": "media_scanned", "target_id": asset_id})
