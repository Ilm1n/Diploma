from __future__ import annotations

from src.realtimev1.events import RealtimeDeliveryMessage


def serialize_delivery_message(message: RealtimeDeliveryMessage) -> str:
    return message.model_dump_json(by_alias=True, exclude_none=True)


def deserialize_delivery_message(raw: str) -> RealtimeDeliveryMessage:
    return RealtimeDeliveryMessage.model_validate_json(raw)
