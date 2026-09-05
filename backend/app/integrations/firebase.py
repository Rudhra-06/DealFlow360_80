import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FirebasePushService:
    """Fail-safe Firebase Cloud Messaging integration for mobile push notifications."""

    def __init__(self) -> None:
        self.enabled = os.getenv("FIREBASE_ENABLED", "false").lower() in ("true", "1", "yes")
        self.credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        self._app = None

        if self.enabled and self.credentials_path:
            try:
                import firebase_admin
                from firebase_admin import credentials
                if not firebase_admin._apps:
                    cred = credentials.Certificate(self.credentials_path)
                    self._app = firebase_admin.initialize_app(cred)
            except Exception as e:
                logger.warning(f"Failed to initialize Firebase Admin SDK: {e}")
                self.enabled = False

    async def send_push_notification(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not self.enabled or not device_tokens:
            return False

        try:
            from firebase_admin import messaging
            str_data = {k: str(v) for k, v in (data or {}).items()}
            message = messaging.MulticastMessage(
                tokens=device_tokens,
                notification=messaging.Notification(title=title, body=body),
                data=str_data,
            )
            response = messaging.send_each_for_multicast(message)
            logger.info(f"FCM push sent: {response.success_count} success, {response.failure_count} failure")
            return response.success_count > 0
        except Exception as e:
            logger.error(f"FCM push delivery failed: {e}")
            return False


firebase_push_service = FirebasePushService()
