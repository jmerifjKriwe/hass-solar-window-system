# Konzept: Umstrukturierung der Solar Window System Integration mit Sub-Entries

Dieses Dokument beschreibt einen Ansatz zur Implementierung der Solar Window System Integration unter Verwendung von Home Assistant's Sub-Entries Funktionalität.

## Ziel

Eine hierarchische Struktur schaffen, die globale Einstellungen, Gruppen und Fenster logisch organisiert und dabei die Beschränkungen der Home Assistant API berücksichtigt.

## Ausgangssituation

Aktuell gibt es drei Arten von Config Entries:
1. Globaler Entry (einer pro Installation)
2. Gruppen-Entries (beliebig viele)
3. Fenster-Entries (beliebig viele, optional einer Gruppe zugeordnet)

## Herausforderung

Home Assistant unterstützt nur eine Ebene von Sub-Entries, keine Sub-Sub-Entries. Dies bedeutet, dass wir keine echte dreistufige Hierarchie (Global → Gruppen → Fenster) implementieren können.

## Bevorzugter Umbau-Vorschlag: Flache Hierarchie mit Referenzierung

### Übersicht der Struktur:

1. **Ein globaler Config Entry** - Enthält alle systemweiten Einstellungen
2. **Window-Sub-Entries direkt unter dem globalen Entry** - Jedes Fenster als Sub-Entry
3. **Group-Sub-Entries direkt unter dem globalen Entry** - Jede Gruppe als Sub-Entry
4. **Referenz-System für die Zuordnung** - Fenster referenzieren ihre Gruppe über eine Group-ID

### Vorteile dieses Ansatzes:

- **Natürliche Integration** mit Home Assistant's Sub-Entry-Konzept
- **Einfache Implementierung** ohne komplizierte Workarounds
- **Flexibilität** bei der Zuordnung von Fenstern zu Gruppen
- **Klare UI-Struktur** in der Integrationsübersicht
- **Gute Performance** durch flache Hierarchie

## Implementierungsdetails

### 1. Sub-Entry-Typen definieren

Erweiterung der `SolarWindowConfigFlow` Klasse in `config_flow.py`:

```python
@classmethod
@callback
def async_get_supported_subentry_types(cls, config_entry: ConfigEntry) -> dict[str, type[ConfigSubentryFlow]]:
    """Return subentries supported by this integration."""
    return {
        "group": GroupSubentryFlowHandler,
        "window": WindowSubentryFlowHandler
    }
```

### 2. Flow Handler für Gruppen

```python
class GroupSubentryFlowHandler(ConfigSubentryFlow):
    """Handler für Gruppen Sub-Entry Flow."""

    async def async_step_user(self, user_input=None):
        """Erster Schritt beim Hinzufügen einer Gruppe."""
        errors = {}

        if user_input is not None:
            # Eindeutige ID für die Gruppe generieren
            group_id = str(uuid.uuid4())

            # Bei Erfolg: Gruppe als Sub-Entry erstellen
            return self.async_create_subentry(
                title=user_input["name"],
                data={
                    "name": user_input["name"],
                    "id": group_id,
                    # Weitere gruppenspezifische Einstellungen
                    "room_temperature_sensor": user_input.get("room_temperature_sensor"),
                    "max_temperature": user_input.get("max_temperature", 25),
                    # ...weitere Einstellungen...
                }
            )

        # Form anzeigen
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Optional("room_temperature_sensor"): selector.EntitySelector(
                    {"domain": "sensor", "device_class": "temperature"}
                ),
                vol.Optional("max_temperature", default=25): selector.NumberSelector(
                    {"min": 18, "max": 30, "mode": "box"}
                ),
                # ...weitere Felder...
            }),
            errors=errors,
        )
```

### 3. Flow Handler für Fenster

```python
class WindowSubentryFlowHandler(ConfigSubentryFlow):
    """Handler für Fenster Sub-Entry Flow."""

    async def async_step_user(self, user_input=None):
        """Erster Schritt beim Hinzufügen eines Fensters."""
        errors = {}

        # Alle verfügbaren Gruppen aus dem System holen
        groups = []
        entry = _get_global_entry(self.hass)
        for subentry in entry.subentries.values():
            if subentry.subentry_type == "group":
                groups.append({
                    "id": subentry.data.get("id", subentry.subentry_id),
                    "name": subentry.title
                })

        group_choices = {g["id"]: g["name"] for g in groups}
        group_choices["none"] = "Keine Gruppe"

        if user_input is not None:
            # Validierung hier...

            # Bei Erfolg: Sub-Entry erstellen mit Referenz zur Gruppe
            group_id = user_input.get("group_id")
            if group_id == "none":
                group_id = None

            return self.async_create_subentry(
                title=user_input["name"],
                data={
                    "name": user_input["name"],
                    "group_id": group_id,
                    "azimuth": user_input["azimuth"],
                    "width": user_input.get("width", 1.0),
                    "height": user_input.get("height", 1.0),
                    "own_temperature_sensor": user_input.get("own_temperature_sensor"),
                    "use_group_settings": user_input.get("use_group_settings", True),
                    # weitere Fenster-spezifische Eigenschaften...
                }
            )

        # Form anzeigen mit Gruppenauswahl
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Optional("group_id", default="none"): vol.In(group_choices),
                vol.Required("azimuth", default=180): selector.NumberSelector(
                    {"min": 0, "max": 359, "mode": "box"}
                ),
                vol.Optional("width", default=1.0): selector.NumberSelector(
                    {"min": 0.1, "step": 0.1, "mode": "box"}
                ),
                vol.Optional("height", default=1.0): selector.NumberSelector(
                    {"min": 0.1, "step": 0.1, "mode": "box"}
                ),
                vol.Optional("own_temperature_sensor"): selector.EntitySelector(
                    {"domain": "sensor", "device_class": "temperature"}
                ),
                vol.Optional("use_group_settings", default=True): selector.BooleanSelector(),
                # weitere Felder...
            }),
            errors=errors,
        )
```

### 4. Options Flow für Fenster

```python
class WindowOptionsFlowHandler(OptionsFlow):
    """Handler für Fenster Options Flow."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            # Fenster-Sub-Entry aktualisieren

            # Falls Gruppe geändert wurde
            old_group_id = self.config_entry.data.get("group_id")
            new_group_id = user_input.get("group_id")
            if new_group_id == "none":
                new_group_id = None

            if old_group_id != new_group_id:
                # Hier Code für das Umziehen des Fensters zwischen Gruppen
                pass

            return self.async_create_entry(title="", data=user_input)

        # Alle verfügbaren Gruppen aus dem System holen
        groups = []
        entry = _get_global_entry(self.hass)
        for subentry in entry.subentries.values():
            if subentry.subentry_type == "group":
                groups.append({
                    "id": subentry.data.get("id", subentry.subentry_id),
                    "name": subentry.title
                })

        group_choices = {g["id"]: g["name"] for g in groups}
        group_choices["none"] = "Keine Gruppe"

        # Aktuelle Werte als Defaults verwenden
        current_data = self.config_entry.data
        current_group_id = current_data.get("group_id", "none")
        if current_group_id is None:
            current_group_id = "none"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("group_id", default=current_group_id): vol.In(group_choices),
                vol.Optional("own_temperature_sensor", default=current_data.get("own_temperature_sensor")):
                    selector.EntitySelector({"domain": "sensor", "device_class": "temperature"}),
                vol.Optional("use_group_settings", default=current_data.get("use_group_settings", True)):
                    selector.BooleanSelector(),
                # weitere Felder...
            }),
        )
```

### 5. Hilfsfunktion für Werte-Vererbung

```python
def get_effective_setting(hass, window_subentry, setting_name):
    """Holt den effektiven Wert für eine Einstellung mit Vererbung."""
    # 1. Prüfen, ob Fenster eigene Einstellung hat
    if setting_name in window_subentry.data:
        return window_subentry.data[setting_name]

    # 2. Von Gruppe erben, falls vorhanden und aktiviert
    if window_subentry.data.get("use_group_settings", True):
        group_id = window_subentry.data.get("group_id")
        if group_id:
            entry = _get_global_entry(hass)
            for subentry in entry.subentries.values():
                if (subentry.subentry_type == "group" and
                    subentry.data.get("id") == group_id):
                    if setting_name in subentry.data:
                        return subentry.data[setting_name]

    # 3. Von globaler Konfiguration erben (sollte immer definiert sein)
    entry = _get_global_entry(hass)
    if setting_name in entry.options:
        return entry.options[setting_name]

    # 4. Falls wider Erwarten kein Wert gefunden wurde, Fehler loggen
    _LOGGER.error(
        f"Keine Einstellung für '{setting_name}' in der globalen Konfiguration gefunden. "
        f"Dies deutet auf einen Konfigurationsfehler hin."
    )
    return None
```

### 6. Hilfsfunktion zum Finden des globalen Entries

```python
def _get_global_entry(hass):
    """Findet den globalen Config Entry."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_ENTRY_TYPE) == "global":
            return entry
    return None
```

### 7. Migration bestehender Daten

```python
async def async_migrate_entry(hass, config_entry):
    """Migriere alte Config Entries zur neuen Sub-Entry Struktur."""
    if config_entry.version == 1:
        # Migration von v1 zu v2 (Sub-Entry Struktur)
        old_data = dict(config_entry.data)
        entry_type = old_data.get(CONF_ENTRY_TYPE)

        if entry_type == "global":
            # Global Entry bleibt erhalten, aber bekommt neue Version
            new_data = dict(old_data)
            new_data["version"] = 2
            hass.config_entries.async_update_entry(
                config_entry,
                data=new_data,
                version=2
            )
            return True

        elif entry_type == "group":
            # Gruppe als Sub-Entry unter global umwandeln
            global_entry = _get_global_entry(hass)
            if not global_entry:
                return False

            hass.config_entries.async_add_subentry(
                global_entry,
                ConfigSubentry(
                    data=old_data,
                    subentry_type="group",
                    title=old_data.get("name", "Unbenannte Gruppe"),
                    unique_id=config_entry.unique_id
                )
            )

            # Alten Entry entfernen
            hass.config_entries.async_remove(config_entry.entry_id)
            return False  # Originaler Entry wurde entfernt

        elif entry_type == "window":
            # Fenster als Sub-Entry unter global umwandeln
            global_entry = _get_global_entry(hass)
            if not global_entry:
                return False

            hass.config_entries.async_add_subentry(
                global_entry,
                ConfigSubentry(
                    data=old_data,
                    subentry_type="window",
                    title=old_data.get("name", "Unbenanntes Fenster"),
                    unique_id=config_entry.unique_id
                )
            )

            # Alten Entry entfernen
            hass.config_entries.async_remove(config_entry.entry_id)
            return False  # Originaler Entry wurde entfernt

    return False
```

### 8. Anpassung des Coordinators

```python
class SolarWindowDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator für Solar Window System."""

    def __init__(self, hass, config_entry, config_data):
        """Initialize the coordinator with config data."""
        self.config_entry = config_entry
        self.config_data = config_data
        self.windows = {}
        self.groups = {}

        # Lade alle Fenster und Gruppen
        self._load_windows_and_groups()

        super().__init__(
            hass,
            _LOGGER,
            name="Solar Window System",
            update_interval=timedelta(
                minutes=config_data.get("update_interval", 5)
            ),
        )

    def _load_windows_and_groups(self):
        """Lade alle Fenster- und Gruppen-Sub-Entries."""
        self.windows = {}
        self.groups = {}

        for subentry in self.config_entry.subentries.values():
            if subentry.subentry_type == "window":
                self.windows[subentry.subentry_id] = subentry
            elif subentry.subentry_type == "group":
                self.groups[subentry.data.get("id", subentry.subentry_id)] = subentry

    async def _async_update_data(self):
        """Update data for all windows."""
        # Aktualisiere Fenster- und Gruppendaten
        self._load_windows_and_groups()

        data = {}
        # Global
        data["global"] = {
            "solar_radiation": self._get_state(
                self.config_data.get("solar_radiation_sensor")
            ),
            "outdoor_temperature": self._get_state(
                self.config_data.get("outdoor_temperature_sensor")
            ),
            "min_solar_radiation": self.config_data.get("min_solar_radiation", 50),
            "min_sun_elevation": self.config_data.get("min_sun_elevation", 10),
        }

        # Gruppen
        data["groups"] = {}
        for group_id, group_subentry in self.groups.items():
            group_data = group_subentry.data
            data["groups"][group_id] = {
                "name": group_data.get("name", "Unbenannte Gruppe"),
                "room_temperature": self._get_state(
                    group_data.get("room_temperature_sensor")
                ),
                "max_temperature": group_data.get("max_temperature", 25),
                # ...weitere Eigenschaften...
            }

        # Fenster
        data["windows"] = {}
        for window_id, window_subentry in self.windows.items():
            window_data = window_subentry.data
            window_name = window_data.get("name", "Unbenanntes Fenster")
            group_id = window_data.get("group_id")

            # Kalkuliere die effektiven Einstellungen für dieses Fenster
            room_temp_sensor = get_effective_setting(
                self.hass, window_subentry, "own_temperature_sensor"
            )
            if room_temp_sensor is None and group_id:
                # Verwende den Raumtemperatursensor der Gruppe
                group = self.groups.get(group_id)
                if group:
                    room_temp_sensor = group.data.get("room_temperature_sensor")

                # Falls kein Raumtemperatursensor in der Gruppe, verwende den globalen
                if room_temp_sensor is None:
                    room_temp_sensor = self.config_data.get("default_room_temperature_sensor")

            data["windows"][window_id] = {
                "name": window_name,
                "group_id": group_id,
                "azimuth": window_data.get("azimuth", 180),
                "width": window_data.get("width", 1.0),
                "height": window_data.get("height", 1.0),
                "room_temperature": self._get_state(room_temp_sensor),
                # ...weitere berechnete Eigenschaften...
            }

        return data

    def _get_state(self, entity_id):
        """Hilfsmethode um den State eines Sensors abzufragen."""
        if not entity_id:
            return None
        if state := self.hass.states.get(entity_id):
            try:
                return float(state.state)
            except (ValueError, TypeError):
                return None
        return None
```

## UI-Darstellung und Benennung der Sub-Entries

Da Home Assistant Sub-Entries in der UI als flache Liste unter dem Haupt-Entry anzeigt, ist es wichtig, eine klare visuelle Unterscheidung zwischen verschiedenen Sub-Entry-Typen zu schaffen. Eine effektive Strategie ist die Verwendung von Typ-Präfixen in den Titeln der Sub-Entries.

### Automatische Typ-Präfixe

In den Flow-Handlern können wir automatisch Typ-Präfixe zu den Titeln hinzufügen:

```python
class GroupSubentryFlowHandler(ConfigSubentryFlow):
    """Handler für Gruppen Sub-Entry Flow."""

    async def async_step_user(self, user_input=None):
        """Erster Schritt beim Hinzufügen einer Gruppe."""
        # ...
        if user_input is not None:
            # Titel mit Typ-Präfix
            title = f"Gruppe: {user_input['name']}"

            return self.async_create_subentry(
                title=title,
                data={
                    "name": user_input["name"],
                    # ...
                }
            )
        # ...

class WindowSubentryFlowHandler(ConfigSubentryFlow):
    """Handler für Fenster Sub-Entry Flow."""

    async def async_step_user(self, user_input=None):
        """Erster Schritt beim Hinzufügen eines Fensters."""
        # ...
        if user_input is not None:
            # Titel mit Typ-Präfix
            title = f"Fenster: {user_input['name']}"

            return self.async_create_subentry(
                title=title,
                data={
                    "name": user_input["name"],
                    # ...
                }
            )
        # ...
```

### Vorteile der Typ-Präfixe

1. **Visuelle Gruppierung** - Gleichartige Sub-Entries werden in der UI-Liste zusammenbleiben, da Home Assistant die Einträge alphabetisch sortiert
2. **Bessere Übersicht** - Auf den ersten Blick ist erkennbar, um welchen Typ von Sub-Entry es sich handelt
3. **Konsistente Benennung** - Einheitliche Darstellung über alle Sub-Entries hinweg

### Berücksichtigung bei der Migration

Bei der Migration bestehender Einträge sollten die Typ-Präfixe ebenfalls hinzugefügt werden:

```python
async def async_migrate_entry(hass, config_entry):
    # ...
    elif entry_type == "group":
        # Gruppe als Sub-Entry unter global umwandeln
        # ...
        name = old_data.get("name", "Unbenannte Gruppe")
        title = f"Gruppe: {name}"

        hass.config_entries.async_add_subentry(
            global_entry,
            ConfigSubentry(
                data=old_data,
                subentry_type="group",
                title=title,
                unique_id=config_entry.unique_id
            )
        )
        # ...

    elif entry_type == "window":
        # Fenster als Sub-Entry unter global umwandeln
        # ...
        name = old_data.get("name", "Unbenanntes Fenster")
        title = f"Fenster: {name}"

        hass.config_entries.async_add_subentry(
            global_entry,
            ConfigSubentry(
                data=old_data,
                subentry_type="window",
                title=title,
                unique_id=config_entry.unique_id
            )
        )
        # ...
```

### Anpassung der Anzeigetitel bei Änderungen

Wenn der Name eines Sub-Entries geändert wird, muss auch der Anzeigetitel mit dem Typ-Präfix aktualisiert werden:

```python
class WindowOptionsFlowHandler(OptionsFlow):
    # ...
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Falls der Name geändert wurde
            if "name" in user_input and user_input["name"] != self.config_entry.data.get("name"):
                new_title = f"Fenster: {user_input['name']}"
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=new_title
                )
            # ...
```

## Zusammenfassung

Dieser Ansatz bietet eine saubere und wartbare Lösung für die Integration von Solar Window System in Home Assistant unter Verwendung von Sub-Entries. Die flache Hierarchie mit Referenzierung ermöglicht eine flexible Gruppierung von Fenstern, ohne auf technisch nicht unterstützte Sub-Sub-Entries angewiesen zu sein.

Die automatische Hinzufügung von Typ-Präfixen in den Titeln sorgt für eine übersichtliche Darstellung und visuelle Gruppierung in der UI, was die Benutzererfahrung verbessert und die Navigation erleichtert.

Die Migration bestehender Installationen sollte reibungslos funktionieren, da alle Daten aus den alten Config Entries in die neue Struktur übertragen werden.
