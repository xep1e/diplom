from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.redis_client import redis_manager

router = APIRouter(prefix="/photo", tags=["photo"])


@router.get("/{photo_key}")
async def get_photo(photo_key: str):
    """Получить фото из Redis"""

    print(f"📸 Запрос фото: {photo_key}")

    photo_data = await redis_manager.get_photo(photo_key)

    if not photo_data:
        print(f"❌ Фото не найдено: {photo_key}")
        raise HTTPException(status_code=404, detail="Фото не найдено")

    print(f"✅ Фото отправлено: {len(photo_data)} байт")
    return StreamingResponse(BytesIO(photo_data), media_type="image/jpeg")