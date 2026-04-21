import redis.asyncio as redis
from typing import Optional
import base64
from io import BytesIO
from PIL import Image

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0


class RedisManager:
    def __init__(self):
        self.redis = None

    async def connect(self):
        self.redis = await redis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
            decode_responses=True
        )
        print("✅ Redis подключен")

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            print("❌ Redis отключен")

    async def save_photo(self, photo_data: bytes, photo_id: str) -> str:
        """Сохранить фото в Redis"""
        key = f"photo:{photo_id}"

        # Конвертируем в RGB если нужно
        img = Image.open(BytesIO(photo_data))
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Оптимизация
        if img.size[0] > 1000 or img.size[1] > 1000:
            img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=80)
        optimized_data = buffer.getvalue()

        # Сохраняем в Redis на 7 дней
        await self.redis.setex(
            key,
            604800,  # 7 дней
            base64.b64encode(optimized_data).decode('utf-8')
        )

        return key

    async def get_photo(self, key: str) -> Optional[bytes]:
        """Получить фото из Redis"""
        data = await self.redis.get(key)
        if data:
            return base64.b64decode(data)
        return None


redis_manager = RedisManager()