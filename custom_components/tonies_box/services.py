from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError

from .const import DOMAIN


async def handle_upload_file(hass: HomeAssistant, call: ServiceCall) -> None:
    tonie_id = call.data.get("tonie_id")
    file_path = call.data.get("file_path")
    title = call.data.get("title")

    if not tonie_id:
        raise ServiceValidationError("tonie_id is required")
    if not file_path:
        raise ServiceValidationError("file_path is required")
    if not title:
        raise ServiceValidationError("title is required")

    for coordinator in hass.data[DOMAIN].values():
        if tonie_id in coordinator.data.get("creative_tonies", {}):
            await coordinator.client.async_upload_file(tonie_id, file_path, title)
            await coordinator.async_request_refresh()
            return

    raise ServiceValidationError(f"Tonie ID {tonie_id} not found")


async def handle_add_chapter(hass: HomeAssistant, call: ServiceCall) -> None:
    tonie_id = call.data.get("tonie_id")
    file_id = call.data.get("file_id")
    title = call.data.get("title")

    if not tonie_id:
        raise ServiceValidationError("tonie_id is required")
    if not file_id:
        raise ServiceValidationError("file_id is required")
    if not title:
        raise ServiceValidationError("title is required")

    for coordinator in hass.data[DOMAIN].values():
        if tonie_id in coordinator.data.get("creative_tonies", {}):
            await coordinator.client.async_add_chapter(tonie_id, file_id, title)
            await coordinator.async_request_refresh()
            return

    raise ServiceValidationError(f"Tonie ID {tonie_id} not found")


async def handle_sort_chapters(hass: HomeAssistant, call: ServiceCall) -> None:
    tonie_id = call.data.get("tonie_id")
    chapters = call.data.get("chapters")

    if not tonie_id:
        raise ServiceValidationError("tonie_id is required")
    if chapters is None:
        raise ServiceValidationError("chapters is required")

    for coordinator in hass.data[DOMAIN].values():
        if tonie_id in coordinator.data.get("creative_tonies", {}):
            await coordinator.client.async_sort_chapters(tonie_id, chapters)
            await coordinator.async_request_refresh()
            return

    raise ServiceValidationError(f"Tonie ID {tonie_id} not found")


async def handle_clear_chapters(hass: HomeAssistant, call: ServiceCall) -> None:
    tonie_id = call.data.get("tonie_id")

    if not tonie_id:
        raise ServiceValidationError("tonie_id is required")

    for coordinator in hass.data[DOMAIN].values():
        if tonie_id in coordinator.data.get("creative_tonies", {}):
            await coordinator.client.async_clear_chapters(tonie_id)
            await coordinator.async_request_refresh()
            return

    raise ServiceValidationError(f"Tonie ID {tonie_id} not found")


async def handle_set_volume(hass: HomeAssistant, call: ServiceCall) -> None:
    box_id = call.data.get("box_id")
    volume_raw = call.data.get("volume")

    if volume_raw is None:
        raise ServiceValidationError(
            "Volume must be specified for set_volume service call"
        )

    try:
        volume = int(volume_raw)
    except (ValueError, TypeError) as e:
        raise ServiceValidationError(f"Invalid volume value: {volume_raw}") from e

    for coordinator in hass.data[DOMAIN].values():
        if box_id in coordinator.data.get("boxes", {}):
            await coordinator.client.async_set_volume(box_id, volume)
            await coordinator.async_request_refresh()
            return

    raise ServiceValidationError(f"Toniebox ID {box_id} not found")
