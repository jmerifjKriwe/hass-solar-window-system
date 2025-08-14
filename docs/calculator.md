# Solar Window System Calculator - Dokumentation

## Überblick

Der Solar Window System Calculator ist das Herzstück der Integration und berechnet für jedes Fenster, ob eine Beschattung erforderlich ist. Er kombiniert physikalische Solarberechnungen mit intelligenter Schattenanalyse und berücksichtigt dabei drei verschiedene Beschattungsszenarien.

## Architektur

### SolarWindowSystemCoordinator

Das System verwendet einen zentralen Coordinator (`SolarWindowSystemCoordinator`), der:
- **Automatische Berechnungen** alle 60 Sekunden durchführt
- **Flow-basierte Berechnungen** mit `calculate_all_windows_from_flows()` ausführt
- **Binary Sensor Updates** mit den neuesten Berechnungsergebnissen versorgt
- **Fehlerbehandlung** und Logging zentral koordiniert

### Flow-basierte Konfiguration

Die Calculator-Architektur basiert ausschließlich auf modernen flow-basierten Methoden und dem HomeAssistant Sub-Entry System mit einer dreistufigen Hierarchie:

```
Global Configuration (Basis-Einstellungen)
    ↓ (vererbt an)
Group Configuration (Gruppierung ähnlicher Fenster)
    ↓ (vererbt an)
Window Configuration (individuelle Fenster-Parameter)
```

**Vererbungslogik:**
- Window-Einstellungen überschreiben Group-Einstellungen
- Group-Einstellungen überschreiben Global-Einstellungen
- Nicht gesetzte Werte werden von der nächsthöheren Ebene übernommen

**Modernisierte Methoden:**
Der Calculator arbeitet ausschließlich mit flow-basierten Methoden:
- Alle Berechnungen erfolgen über `calculate_all_windows_from_flows()`
- Parameter werden über `ShadeRequestFlow` NamedTuple strukturiert übertragen
- Vollständige Szenario-Vererbung (Window→Group→Global) ist implementiert

## Eingangsdaten

### 1. Externe Sensordaten

| Parameter | Quelle | Beschreibung | Einheit |
|-----------|--------|--------------|---------|
| `solar_radiation` | Sensor | Aktuelle Globalstrahlung | W/m² |
| `sun_azimuth` | sun.sun | Sonnen-Azimuthwinkel | Grad (0-360°) |
| `sun_elevation` | sun.sun | Sonnen-Elevationswinkel | Grad (0-90°) |
| `outdoor_temp` | Sensor | Außentemperatur | °C |
| `indoor_temp` | Sensor | Raumtemperatur pro Fenster | °C |
| `forecast_temp` | Sensor | Wettervorhersage-Temperatur | °C |
| `weather_warning` | Sensor | Wetterwarnung aktiv | boolean |

### 2. Fenster-spezifische Parameter

#### Geometrie
- **window_width** / **window_height**: Fensterabmessungen in Metern
- **azimuth**: Fensterausrichtung (0° = Nord, 90° = Ost, 180° = Süd, 270° = West)
- **tilt**: Fensterneigung (0° = vertikal, 90° = horizontal)
- **frame_width**: Rahmenbreite (reduziert die Glasfläche)

#### Sichtbereich
- **elevation_min** / **elevation_max**: Vertikaler Sichtbereich der Sonne
- **azimuth_min** / **azimuth_max**: Horizontaler Sichtbereich (relativ zur Fensterausrichtung)

#### Neue Schatten-Parameter
- **shadow_depth**: Fenster-Rückversetzung von der Fassade (0-5m)
- **shadow_offset**: Zusätzliche Beschattung durch Überstände etc. (0-5m)

#### Physikalische Eigenschaften
- **g_value**: Gesamtenergiedurchlassgrad des Glases (0.1-1.0)
- **diffuse_factor**: Anteil diffuser Strahlung (0.1-0.5)

## Calculator-Methoden

Der `SolarWindowCalculator` bietet folgende moderne, flow-basierte Methoden:

### Hauptmethoden
- **`from_flows(global_config_flow, group_flows, window_flows)`**: Erstellt Calculator-Instanz aus Flow-Konfigurationen
- **`calculate_all_windows_from_flows()`**: Führt komplette Berechnung für alle Fenster durch
- **`calculate_window_solar_power_with_shadow(window_flow, sun_data)`**: Berechnet Solarleistung mit Schattenberücksichtigung

### Hilfsmethoden
- **`get_effective_config_from_flows(window_flow)`**: Ermittelt effektive Konfiguration mit Vererbung
- **`_should_shade_window_from_flows(window_flow, power_data)`**: Beschattungsentscheidung basierend auf Szenarien
- **`apply_global_factors(power_data, global_flow)`**: Wendet globale Faktoren an

### Utility-Methoden
- **`get_safe_attr(entity_id, attribute, default)`**: Sichere Attribut-Abfrage mit Fallback
- **`get_safe_state(entity_id, default)`**: Sichere State-Abfrage mit Fallback

**Hinweis**: Alle veralteten Methoden (calculate_all_windows, should_shade_window, etc.) wurden entfernt. Der Calculator arbeitet ausschließlich mit den modernen flow-basierten Methoden.

## Berechnungslogik

### 1. Solarleistungsberechnung

#### Schritt 1: Sichtbarkeitscheck
```python
# Prüfung ob Sonne im definierten Sichtbereich
if elevation_min <= sun_elevation <= elevation_max:
    az_diff = ((sun_azimuth - window_azimuth + 180) % 360) - 180
    if azimuth_min <= az_diff <= azimuth_max:
        is_visible = True
```

#### Schritt 2: Glasflächenberechnung
```python
glass_width = max(0, window_width - 2 * frame_width)
glass_height = max(0, window_height - 2 * frame_width)
area = glass_width * glass_height
```

#### Schritt 3: Diffuse Strahlung (immer vorhanden)
```python
power_diffuse = solar_radiation * diffuse_factor * area * g_value
```

#### Schritt 4: Direkte Strahlung (nur bei Sichtbarkeit)
```python
# Einfallswinkel-Berechnung (trigonometrisch)
cos_incidence = (sin(sun_elevation) * cos(tilt) +
                cos(sun_elevation) * sin(tilt) *
                cos(sun_azimuth - window_azimuth))

if cos_incidence > 0:
    power_direct = (solar_radiation * (1 - diffuse_factor) *
                   cos_incidence / sin(sun_elevation)) * area * g_value
```

### 2. Geometrische Schattenberechnung

Die neue geometrische Schattenberechnung berücksichtigt realistische Gebäudeschatten:

#### Schritt 1: Effektive Schattentiefe
```python
effective_shadow_depth = shadow_depth + shadow_offset
```

#### Schritt 2: Trigonometrische Schattenberechnung
```python
if sun_elevation > 0 and effective_shadow_depth > 0:
    # Schattenlänge auf Fensterebene
    shadow_length = effective_shadow_depth / tan(sun_elevation)

    # Winkel zwischen Sonnenschatten und Fensternormale
    shadow_angle_diff = abs(sun_azimuth - window_azimuth)

    # Projizierte Schattenlänge auf Fenster
    projected_shadow = shadow_length * cos(shadow_angle_diff)

    # Annahme: Fensterhöhe als Referenz für Beschattungsgrad
    assumed_window_size = 1.5  # Meter

    if projected_shadow >= assumed_window_size:
        shadow_factor = 0.1  # Minimal 10% direkte Strahlung
    else:
        # Linearer Übergang von 1.0 (keine Beschattung) zu 0.1
        shadow_factor = max(0.1, 1.0 - (projected_shadow / assumed_window_size) * 0.9)
```

#### Schritt 3: Anwendung auf direkte Strahlung
```python
power_direct_shadowed = power_direct * shadow_factor
```

### 3. Beschattungslogik (Drei Szenarien)

#### Szenario A: Starke direkte Sonneneinstrahlung (immer aktiv)
```python
if (power_total > threshold_direct and
    indoor_temp >= temp_indoor_base and
    outdoor_temp >= temp_outdoor_base):
    return True, "Strong sun"
```

#### Szenario B: Diffuse Wärme (optional)
```python
if (scenario_b_enabled and
    power_total > threshold_diffuse and
    indoor_temp > temp_indoor_base + temp_indoor_offset_b and
    outdoor_temp > temp_outdoor_base + temp_outdoor_offset_b):
    return True, "Diffuse heat"
```

#### Szenario C: Hitzewarnung/Vorhersage (optional)
```python
if (scenario_c_enabled and
    forecast_temp > temp_forecast_threshold and
    indoor_temp >= temp_indoor_base and
    current_hour >= start_hour):
    return True, "Heatwave forecast"
```

### 4. Szenario-Vererbung

Die Aktivierung der Szenarien B und C folgt der Vererbungslogik:

```python
# Window Entity: "inherit" | "enable" | "disable"
# ↓ (wenn "inherit")
# Group Entity: "inherit" | "enable" | "disable"
# ↓ (wenn "inherit")
# Global Entity: "on" | "off"
```

## Ausgangsdaten

### Pro Fenster gespeicherte Werte

#### Berechnungsergebnisse
- **power_total**: Gesamte Solarleistung durch das Fenster (W)
- **power_direct**: Direkte Solarleistung (W)
- **power_diffuse**: Diffuse Solarleistung (W)
- **shadow_factor**: Angewendeter Schattenfaktor (0.1-1.0)
- **area_m2**: Effektive Glasfläche (m²)

#### Entscheidung
- **is_visible**: Ist die Sonne für das Fenster sichtbar (boolean)
- **shade_required**: Beschattung erforderlich (boolean)
- **shade_reason**: Begründung für die Entscheidung (Text)
- **effective_threshold**: Angewendeter Schwellwert (W)

**Hinweis**: Diese Daten werden in der `WindowCalculationResult`-Dataclass gespeichert und stehen für die Entität-Updates zur Verfügung. Die tatsächliche Speicherung erfolgt direkt in den entsprechenden HomeAssistant-Entitäten (siehe Entität-Updates).

#### Summary-Daten (für zukünftige Implementierung)
- **total_power**: Summe aller Fenster-Solarleistungen (W)
- **window_count**: Anzahl berechneter Fenster
- **shading_count**: Anzahl Fenster mit Beschattungsempfehlung
- **calculation_time**: Zeitstempel der Berechnung (ISO)

**Hinweis**: Summary-Daten sind in der `WindowCalculationResult`-Struktur vorbereitet, aber noch nicht vollständig in separaten Entitäten implementiert. Die Aggregation erfolgt derzeit über die Group-Entitäten.

### Entität-Updates

Der Calculator stellt die Berechnungsergebnisse über den `SolarWindowSystemCoordinator` bereit, der alle 60 Sekunden automatisch die Berechnungen durchführt und die HomeAssistant-Entitäten aktualisiert:

#### Coordinator-Architektur
- **Automatische Updates**: Alle 60 Sekunden wird `calculate_all_windows_from_flows()` ausgeführt
- **Binary Sensor Integration**: Binary Sensoren werden direkt über den Coordinator mit aktuellen Beschattungsempfehlungen versorgt
- **Zentrale Fehlerbehandlung**: Der Coordinator fängt Berechnungsfehler ab und sorgt für stabile Entität-Updates
- **Performance-Optimierung**: Intelligentes Caching und effiziente Batch-Verarbeitung

#### Window-Entitäten (pro Fenster)
**Sensoren (aus sensor.py):**
```
sensor.sws_window_{name}_total_power           # Gesamtleistung (W)
sensor.sws_window_{name}_total_power_direct    # Direkte Leistung (W)
sensor.sws_window_{name}_total_power_diffuse   # Diffuse Leistung (W)
sensor.sws_window_{name}_power_m2_total        # Leistung pro m² gesamt
sensor.sws_window_{name}_power_m2_direct       # Leistung pro m² direkt
sensor.sws_window_{name}_power_m2_diffuse      # Leistung pro m² diffus
sensor.sws_window_{name}_power_m2_raw          # Rohe Leistung pro m²
sensor.sws_window_{name}_total_power_raw       # Rohe Gesamtleistung
```

**Binary-Sensoren (aus binary_sensor.py):**
```
binary_sensor.sws_window_{name}_shading_required  # Beschattung empfohlen
```

**Select-Entitäten (aus select.py):**
```
select.sws_window_{name}_scenario_b_enable     # Szenario B aktivieren
select.sws_window_{name}_scenario_c_enable     # Szenario C aktivieren
```

#### Group-Entitäten (pro Gruppe)
**Sensoren:**
```
sensor.sws_group_{name}_total_power            # Summe Gruppenleistung (W)
sensor.sws_group_{name}_total_power_direct     # Summe direkte Leistung (W)
sensor.sws_group_{name}_total_power_diffuse    # Summe diffuse Leistung (W)
```

#### Global-Entitäten
Die globalen Konfigurationsentitäten werden über `global_config.py` bereitgestellt und umfassen verschiedene Einstellungen, Schwellwerte und Konfigurationsparameter.

## Performance-Optimierungen

### Coordinator-basierte Optimierungen
- **Zentrale Koordination**: SolarWindowSystemCoordinator führt alle Berechnungen zentral durch
- **60-Sekunden-Takt**: Ausbalanciert zwischen Aktualität und Systemlast
- **Intelligente Updates**: Nur bei tatsächlichen Änderungen werden Entitäten aktualisiert
- **Fehlerbehandlung**: Isolierung von Berechnungsfehlern pro Fenster

### Entity-Caching
- **Cache-Dauer**: 30 Sekunden pro Berechnungszyklus
- **Cache-Invalidierung**: Automatisch bei jedem neuen Berechnungslauf
- **Fallback-Handling**: Graceful degradation bei fehlenden Entitäten

### Berechnungseffizienz
- **Flow-basierte Architektur**: Moderne, strukturierte Parameterübergabe
- **Lazy Evaluation**: Schatten nur bei sichtbarer Sonne berechnet
- **Trigonometrische Optimierung**: Einmalige Winkelberechnung pro Fenster
- **Batch-Processing**: Alle Fenster in einem Durchlauf

## Fehlerbehandlung

### Coordinator-Robustheit
- **Zentrale Fehlerbehandlung**: SolarWindowSystemCoordinator fängt alle Berechnungsfehler ab
- **Graceful Degradation**: Bei Fehlern werden andere Fenster weiter berechnet
- **Retry-Mechanismus**: Automatische Wiederholung bei temporären Fehlern
- **Entität-Schutz**: Binary Sensoren bleiben stabil auch bei Berechnungsfehlern

### Calculator-Robustheit
- **Fehlende Sensoren**: Fallback auf Standardwerte
- **Ungültige Werte**: Automatische Korrektur oder Überspringen
- **Berechnungsfehler**: Isolierung pro Fenster, Weiterführung der anderen
- **Flow-Validierung**: Strukturvalidierung der Flow-Parameter

### Logging
- **Debug-Level**: Detaillierte Berechnungsschritte und Coordinator-Aktivitäten
- **Info-Level**: Zusammenfassungen und wichtige Entscheidungen
- **Warning-Level**: Fehlerhafte Konfigurationen oder Sensorwerte
- **Error-Level**: Schwerwiegende Berechnungsfehler und Coordinator-Probleme

## Konfigurationsbeispiel

### Typische Window-Konfiguration
```yaml
window_width: 1.5          # 1.5m breites Fenster
window_height: 2.0         # 2.0m hohes Fenster
azimuth: 180               # Südfenster
tilt: 0                    # Vertikal
shadow_depth: 0.3          # 30cm Rückversetzung
shadow_offset: 0.5         # 50cm Balkon-Überhang
elevation_min: 0           # Sonne ab Horizont
elevation_max: 90          # Bis Zenit
azimuth_min: -45           # 45° links
azimuth_max: 45            # 45° rechts
```

### Typische Schwellwerte
```yaml
thresholds:
  direct: 400              # 400W für Szenario A
  diffuse: 200             # 200W für Szenario B

temperatures:
  indoor_base: 24          # 24°C Basis-Innentemperatur
  outdoor_base: 25         # 25°C Basis-Außentemperatur
```

## Architektur-Modernisierung

### Von Legacy zu Flow-basiert

Das Solar Window System wurde vollständig modernisiert:

**Entfernte veraltete Methoden:**
- `calculate_all_windows()` → `calculate_all_windows_from_flows()`
- `should_shade_window()` → `_should_shade_window_from_flows()`
- `calculate_window_solar_power()` → `calculate_window_solar_power_with_shadow()`
- `get_effective_config()` → `get_effective_config_from_flows()`
- `_apply_entity_overrides()` → Eingebaut in Flow-System
- `init_from_flows()` → `from_flows()` (Klassenmethod)

**Vorteile der neuen Architektur:**
- **Coordinator-Integration**: Zentrale, automatisierte Berechnungen
- **Strukturierte Parameter**: Typisierte Flow-Objekte statt Dictionary-Parametern
- **Vollständige Vererbung**: Komplette Szenario-Vererbung implementiert
- **Bessere Testbarkeit**: Klare Interfaces und Abhängigkeiten
- **Performance**: Optimierte Batch-Verarbeitung und Caching

**Backward Compatibility:**
Die Integration funktioniert nahtlos mit bestehenden Konfigurationen. Alle bisherigen Einstellungen und Entitäten bleiben unverändert - nur die interne Berechnungslogik wurde modernisiert.

Diese Dokumentation bietet eine vollständige Übersicht über die Funktionsweise des modernisierten Calculators und hilft Anwendern beim Verständnis der komplexen Berechnungslogik.
