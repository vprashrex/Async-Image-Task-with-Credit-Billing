import redis
import json
import asyncio
import time
from typing import Optional, Any
from app.config import settings


class RedisManager:
    """Redis manager for pub/sub operations with enhanced performance"""
    
    def __init__(self):
        # Connection pool for better performance
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL, 
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        self.pubsub = self.redis_client.pubsub()
    
    def publish_task_update(self, user_id: int, task_data: dict):
        """Publish task update to user-specific channel with enhanced logging"""
        channel = f"task_updates:{user_id}"
        
        # Add timestamp and ensure all required fields
        enhanced_data = {
            **task_data,
            'timestamp': time.time(),
            'user_id': user_id,
            'channel': channel
        }
        
        message = json.dumps(enhanced_data)
        result = self.redis_client.publish(channel, message)
        
        print(f"📡 Published to Redis - Channel: {channel}, Subscribers: {result}, Status: {task_data.get('status', 'unknown')}")
        return result
    
    def subscribe_to_user_tasks(self, user_id: int):
        """Subscribe to user-specific task updates with immediate setup"""
        channel = f"task_updates:{user_id}"
        self.pubsub.subscribe(channel)
        
        # Consume the subscription confirmation message
        confirmation = self.pubsub.get_message(timeout=1.0)
        if confirmation and confirmation['type'] == 'subscribe':
            print(f"✅ Subscribed to Redis channel: {channel}")
        
        return self.pubsub
    
    def unsubscribe_from_user_tasks(self, user_id: int):
        """Unsubscribe from user-specific task updates"""
        channel = f"task_updates:{user_id}"
        self.pubsub.unsubscribe(channel)
        print(f"🔌 Unsubscribed from Redis channel: {channel}")
    
    def get_message(self, timeout: Optional[float] = None):
        """Get message from subscribed channels with better error handling"""
        try:
            message = self.pubsub.get_message(timeout=timeout)
            if message and message['type'] == 'message':
                print(f"📥 Received Redis message: {message['channel']}")
            return message
        except Exception as e:
            print(f"❌ Redis get_message error: {e}")
            return None
    
    def close(self):
        """Close the pubsub connection safely"""
        try:
            self.pubsub.close()
            print("🔒 Redis pubsub connection closed")
        except Exception as e:
            print(f"⚠️ Error closing Redis connection: {e}")


# Global Redis manager instance
redis_manager = RedisManager()
