"""Solar Window System integration package."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN, ENTITY_PREFIX_GLOBAL, GLOBAL_CONFIG_ENTITIES


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry."""
    _LOGGER.warning("🔧 async_setup_entry called for entry: %s", entry.title)
    _LOGGER.warning("🔧 Entry data: %s", entry.data)
    _LOGGER.warning("🔧 Entry ID: %s", entry.entry_id)

    device_registry = dr.async_get(hass)

    # Create device for global config
    if entry.title == "Solar Window System":
        _LOGGER.warning("🔧 Creating device for global config")
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System",
            manufacturer="SolarWindowSystem",
            model="GlobalConfig",
        )

        # Set up all platforms for this entry
        await hass.config_entries.async_forward_entry_setups(
            entry, ["sensor", "number", "text", "select", "switch"]
        )
        # Ensure entities register before attempting migrations
        await hass.async_block_till_done()
        await _migrate_entity_ids(hass, entry)

    # Handle group configurations entry (subentry parent)
    elif entry.data.get("entry_type") == "group_configs":
        _LOGGER.warning(
            "🔧 Handling group_configs entry - this is the parent for subentries"
        )

        # Create devices for existing subentries
        await _create_subentry_devices(hass, entry)

        # Set up platforms for group configurations
        await hass.config_entries.async_forward_entry_setups(entry, ["select"])
        await hass.async_block_till_done()
        await _migrate_entity_ids(hass, entry)

        # Add update listener to handle new subentries
        entry.add_update_listener(_handle_config_entry_update)

        # Register service for manual device creation
        if not hass.services.has_service(DOMAIN, "create_subentry_devices"):

            async def create_subentry_devices_service(
                _call: ServiceCall,
            ) -> None:
                """Service to manually create subentry devices."""
                _LOGGER.warning("🔧 Manual service called: create_subentry_devices")
                for config_entry in hass.config_entries.async_entries(DOMAIN):
                    if config_entry.data.get("entry_type") in [
                        "group_configs",
                        "window_configs",
                    ]:
                        await _create_subentry_devices(hass, config_entry)

            hass.services.async_register(
                DOMAIN, "create_subentry_devices", create_subentry_devices_service
            )

    # Handle window configurations entry (subentry parent)
    elif entry.data.get("entry_type") == "window_configs":
        _LOGGER.warning(
            "🔧 Handling window_configs entry - this is the parent for subentries"
        )

        # Create devices for existing subentries
        await _create_subentry_devices(hass, entry)

        # Set up platforms for window configurations
        await hass.config_entries.async_forward_entry_setups(entry, ["select"])
        await hass.async_block_till_done()
        await _migrate_entity_ids(hass, entry)

        # Add update listener to handle new subentries
        entry.add_update_listener(_handle_config_entry_update)

        # (select setup for window_configs is handled inside that branch above)

    _LOGGER.warning("🔧 async_setup_entry completed for: %s", entry.title)
    return True


@callback
async def _handle_config_entry_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle config entry updates to create devices for new subentries."""
    _LOGGER.warning("🔧 Config entry update detected for: %s", entry.title)
    if entry.data.get("entry_type") in ["group_configs", "window_configs"]:
        await _create_subentry_devices(hass, entry)

        # Reload select platform to pick up new entities for new subentries
        _LOGGER.warning(
            "🔧 Reloading select platform for updated entry: %s", entry.title
        )
        if entry.data.get("entry_type") in ("group_configs", "window_configs"):
            await hass.config_entries.async_unload_platforms(entry, ["select"])
            await hass.config_entries.async_forward_entry_setups(entry, ["select"])
            await hass.async_block_till_done()
            await _migrate_entity_ids(hass, entry)


async def _create_subentry_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create devices for all subentries using proper Device Registry API."""
    _LOGGER.warning("🔧 _create_subentry_devices called for entry: %s", entry.title)
    device_registry = dr.async_get(hass)

    # The correct way to access subentries is through entry.subentries
    # This is a dict where keys are subentry IDs and values are ConfigSubentry objects
    _LOGGER.warning("🔧 Entry subentries: %s", entry.subentries)
    _LOGGER.warning("🔧 Subentries type: %s", type(entry.subentries))

    if entry.subentries:
        for subentry_id, subentry in entry.subentries.items():
            _LOGGER.warning("🔧 Processing subentry ID: %s", subentry_id)
            _LOGGER.warning("🔧 Subentry object: %s", subentry)
            _LOGGER.warning("🔧 Subentry title: %s", subentry.title)
            _LOGGER.warning("🔧 Subentry data: %s", subentry.data)
            _LOGGER.warning("🔧 Subentry type: %s", subentry.subentry_type)

            if subentry.subentry_type == "group":
                group_name = subentry.title
                _LOGGER.warning("🔧 Creating device for group subentry: %s", group_name)

                # This is the key: use config_subentry_id parameter
                # to link device to subentry
                device = device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    config_subentry_id=subentry_id,  # Links device to subentry!
                    identifiers={(DOMAIN, f"group_{subentry_id}")},
                    name=group_name,
                    manufacturer="SolarWindowSystem",
                    model="GroupConfig",
                )
                _LOGGER.warning(
                    "🔧 Device created for subentry: %s (%s)",
                    device.name,
                    device.id,
                )
                _LOGGER.warning(
                    "🔧 Device config_entries_subentries: %s",
                    device.config_entries_subentries,
                )
            elif subentry.subentry_type == "window":
                window_name = subentry.title
                _LOGGER.warning(
                    "🔧 Creating device for window subentry: %s", window_name
                )

                # Create device for window subentry
                device = device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    config_subentry_id=subentry_id,  # Links device to subentry!
                    identifiers={(DOMAIN, f"window_{subentry_id}")},
                    name=window_name,
                    manufacturer="SolarWindowSystem",
                    model="WindowConfig",
                )
                _LOGGER.warning(
                    "🔧 Device created for subentry: %s (%s)",
                    device.name,
                    device.id,
                )
                _LOGGER.warning(
                    "🔧 Device config_entries_subentries: %s",
                    device.config_entries_subentries,
                )
            else:
                _LOGGER.warning(
                    "🔧 Skipping subentry (unknown type): %s",
                    subentry.subentry_type,
                )
    else:
        _LOGGER.warning("🔧 No subentries found in entry")


async def _migrate_entity_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Migrate entity_ids to the sws_* patterns if they don't match yet."""
    entity_registry = er.async_get(hass)
    if entry.title == "Solar Window System":
        await _migrate_global_entity_ids(entity_registry)
    else:
        await _migrate_subentry_select_ids(hass, entry, entity_registry)


async def _migrate_global_entity_ids(entity_registry: er.EntityRegistry) -> None:
    """Rename global entities to domain.sws_global_<key>."""
    platform_to_domain = {
        "input_number": "number",
        "input_text": "text",
        "input_boolean": "switch",
        "input_select": "select",
        "sensor": "sensor",
    }

    for key, cfg in GLOBAL_CONFIG_ENTITIES.items():
        domain = platform_to_domain.get(cfg["platform"])  # type: ignore[index]
        if not domain:
            continue
        unique_id = f"{ENTITY_PREFIX_GLOBAL}_{key}"
        current_eid = entity_registry.async_get_entity_id(domain, DOMAIN, unique_id)
        desired_eid = f"{domain}.{unique_id}"
        if (
            current_eid
            and current_eid != desired_eid
            and not entity_registry.async_get(desired_eid)
        ):
            entity_registry.async_update_entity(
                current_eid,
                new_entity_id=desired_eid,
            )


async def _migrate_subentry_select_ids(
    hass: HomeAssistant,
    entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Rename group/window select entities to select.sws_group|window_<slug>_<key>."""
    device_registry = dr.async_get(hass)
    eligible_devices: set[str] = set()
    for device in device_registry.devices.values():
        if device.config_entries and entry.entry_id in device.config_entries:
            eligible_devices.add(device.id)

    def _slug(text: str) -> str:
        return text.lower().replace(" ", "_").replace("-", "_")

    for ent in list(entity_registry.entities.values()):
        if ent.platform != DOMAIN or not ent.entity_id.startswith("select."):
            continue
        if ent.device_id not in eligible_devices:
            continue

        # If entity already has sws_* object id, align entity_id to it
        uid = ent.unique_id or ""
        if uid.startswith(("sws_group_", "sws_window_")):
            desired = f"select.{uid}"
            if ent.entity_id != desired and not entity_registry.async_get(desired):
                entity_registry.async_update_entity(
                    ent.entity_id, new_entity_id=desired
                )
            continue

        # Handle old IDs like select.enable_scenario_b / select.enable_scenario_c
        object_id = ent.entity_id.split(".", 1)[1]
        if object_id not in {"enable_scenario_b", "enable_scenario_c"}:
            continue

        device = device_registry.async_get(ent.device_id) if ent.device_id else None
        if not device or not device.name:
            continue
        slug = _slug(device.name)
        prefix = (
            "sws_group"
            if entry.data.get("entry_type") == "group_configs"
            else "sws_window"
        )
        desired_object_id = f"{prefix}_{slug}_{object_id}"
        desired = f"select.{desired_object_id}"
        if ent.entity_id != desired and not entity_registry.async_get(desired):
            entity_registry.async_update_entity(ent.entity_id, new_entity_id=desired)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.warning("🔧 async_unload_entry called for: %s", entry.title)

    # Unload platforms if this is the global config entry
    if entry.title == "Solar Window System":
        return await hass.config_entries.async_unload_platforms(
            entry, ["sensor", "number", "text", "select", "switch"]
        )

    return True
