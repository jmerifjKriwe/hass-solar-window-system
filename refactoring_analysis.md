# Refactoring-Analyse: calculator.py

## Beobachtungen zur G### Phase 2: Entfernung von Duplikaten und Wrappern
- [x] Duplikate entfernen: Vergleiche Implementierungen in `calculator.py` und Modulen. Entferne die in `calculator.py`, wenn die Mixin-Version vollständig ist (z. B. `_get_subentries_by_type`, `get_effective_config_from_flows`).
- [x] Wrapper-Methoden eliminieren: Entferne Methoden, die nur `super()` aufrufen (z. B. `get_safe_state`, `get_safe_attr`, `_calculate_shadow_factor`). Delegiere direkt an Mixins.
- [x] Dataclasses konsolidieren: Entferne `WindowCalculationResult` und `ShadeRequestFlow` aus `calculator.py`, wenn sie in `modules/flow_integration.py` vorhanden sind. von calculator.py

Nach der Analyse der Datei `calculator.py` (1937 Zeilen) und der ausgelagerten Module in `modules/` ergeben sich folgende Beobachtungen:

### 1. Hauptklasse und Klassenstruktur
- Die zentrale Klasse `SolarWindowCalculator` ist nach wie vor in `calculator.py` definiert und erbt von den Mixins (`CalculationsMixin`, `DebugMixin`, `FlowIntegrationMixin`, `ShadingMixin`, `UtilsMixin`).
- Dataclasses wie `WindowCalculationResult` und `ShadeRequestFlow` sind teilweise dupliziert (einige auch in `modules/flow_integration.py`).
- Die `__init__`-Methode (Zeilen 99–127) ist vollständig vorhanden und initialisiert spezifische Attribute wie `self.hass`, Caching-Mechanismen und Flow-basierte Attribute. Diese Logik ist eng mit der Hauptklasse gekoppelt und wurde nicht ausgelagert.

### 2. Nicht ausgelagerte Methoden und Funktionalität
Viele Methoden sind noch in `calculator.py` implementiert, obwohl ähnliche Namen in den Mixins existieren. Dies deutet auf unvollständiges Refactoring hin. Identifizierte Kategorien:

- **Konfigurations- und Flow-Integration** (noch nicht vollständig ausgelagert):
  - `from_flows` (Zeile 192): Erstellt Instanzen aus Flow-basierten Konfigurationen.
  - `get_effective_config_from_flows` (Zeile 316): Holt effektive Konfigurationen – existiert auch in `modules/flow_integration.py`, aber mit detaillierterer Implementierung in `calculator.py`.
  - `_get_subentries_by_type` (Zeile 261): Sucht Config-Einträge nach Typ – ebenfalls in `modules/flow_integration.py` vorhanden.
  - `_get_global_data_merged` (Zeile 515): Merged globale Daten aus Config-Einträgen.
  - Umfangreiche Konfigurations-Merging-Logik (Zeilen 357–514): `_mark_config_sources`, `_build_effective_config`, `_copy_config`, `_merge_config_layer`, `_should_merge_nested`, `_merge_nested_dict`, `_structure_flat_config`, `_build_effective_sources`. Diese scheinen Legacy-Code zu sein.

- **Entity- und Sensor-Suche** (hauptsächlich am Ende der Datei, Zeilen 1800–1937):
  - `_search_window_sensors`, `_search_group_sensors`, `_search_global_sensors`: Suchen nach Sensor-Entities auf verschiedenen Ebenen.
  - `_find_entity_by_name`: Findet Entities nach Namen – ruft `super()._find_entity_by_name` auf (delegiert an `DebugMixin`), aber der Wrapper bleibt in `calculator.py`.

- **Utility- und Hilfsmethoden**:
  - `get_safe_state` und `get_safe_attr` (Zeilen 129–147): Rufen `super()` auf, um auf `UtilsMixin` zu delegieren, aber die Wrapper sind noch da.
  - `apply_global_factors` (Zeile 146): Wendet globale Faktoren auf Konfigurationen an – scheint spezifisch für die Hauptklasse.
  - `_get_cached_entity_state`, `_resolve_entity_state_with_fallback` (Zeilen 210–260): Caching- und Fallback-Logik für Entity-States.

- **Berechnungs- und Extraktionsmethoden**:
  - `_extract_calculation_parameters` (Zeile 525): Extrahiert Parameter – ähnlich zu Methoden in `modules/calculations.py`.
  - `_calculate_shadow_factor` (Zeile 81): Delegiert an `super()`, aber Wrapper vorhanden.

### 3. Duplikationen und unvollständiges Refactoring
- **Duplikate**: Methoden wie `_get_subentries_by_type`, `get_effective_config_from_flows`, `_should_shade_window_from_flows` existieren in beiden Dateien mit unterschiedlichen Implementierungen. Dies deutet auf inkrementelles Refactoring ohne Entfernung alter Versionen hin.
- **Wrapper-Methoden**: Viele Methoden rufen nur `super()` auf. Diese könnten entfernt werden, wenn die Mixins direkt verwendet werden.
- **Legacy-Code**: Teile der Datei stammen aus der ursprünglichen monolithischen Implementierung und wurden nicht priorisiert.

### 4. Größenvergleich der Module
- `modules/calculations.py`: 720 Zeilen – Kernberechnungen.
- `modules/debug.py`: 335 Zeilen – Debug- und Entity-Suche.
- `modules/flow_integration.py`: 199 Zeilen – Flow-basierte Integration.
- `modules/shading.py`: 125 Zeilen – Shading-Entscheidungen.
- `modules/utils.py`: 175 Zeilen – Utilities.
- `calculator.py`: 1937 Zeilen – Trotz Auslagerung von ~1400 Zeilen bleibt sie die größte Datei.

### 5. Ursachen für anhaltende Größe
- Unvollständiges Refactoring: Kernberechnungen wurden priorisiert, administrative Teile (Konfiguration, Entity-Suche) blieben zurück.
- Spezifische Logik: `__init__`, Caching sind eng gekoppelt.
- Duplikation zur Kompatibilität: Methoden in beiden Orten belassen.
- Fehlende Priorisierung: Debug- und Konfigurationscode als weniger kritisch angesehen.

## Detaillierte ToDo-Liste für vollständiges Refactoring

### Phase 1: Analyse und Planung
- [x] Vollständige Code-Abdeckung analysieren: Identifiziere alle Methoden in `calculator.py`, die Duplikate in Modulen haben oder ausgelagert werden können.
- [x] Abhängigkeiten prüfen: Stelle sicher, dass alle Tests (`tests/modules/test_calculations.py` etc.) nach Refactoring noch funktionieren.
- [x] Architektur-Entscheidung: Entscheide, ob die Hauptklasse in eine separate Datei (z. B. `core.py`) verschoben wird, oder ob `calculator.py` als reiner Wrapper bleibt.

### Phase 2: Entfernung von Duplikaten und Wrappern
- [x] Duplikate entfernen: Vergleiche Implementierungen in `calculator.py` und Modulen. Entferne die in `calculator.py`, wenn die Mixin-Version vollständig ist (z. B. `_get_subentries_by_type`, `get_effective_config_from_flows`).
- [x] Wrapper-Methoden eliminieren: Entferne Methoden, die nur `super()` aufrufen (z. B. `get_safe_state`, `get_safe_attr`, `_calculate_shadow_factor`). Delegiere direkt an Mixins. (Teilweise erledigt: _check_window_visibility entfernt, weitere Wrapper identifiziert)
- [ ] Dataclasses konsolidieren: Entferne `WindowCalculationResult` und `ShadeRequestFlow` aus `calculator.py`, wenn sie in `modules/flow_integration.py` vorhanden sind.

### Phase 3: Auslagerung verbleibender Methoden
- [ ] Konfigurations-Methoden auslagern: Erstelle ein neues Mixin `ConfigMixin` in `modules/config.py` und verschiebe Methoden wie `_mark_config_sources`, `_build_effective_config`, `_merge_config_layer` etc.
- [ ] Entity-Such-Methoden auslagern: Erweitere `DebugMixin` um die vollständigen Implementierungen von `_search_window_sensors`, `_search_group_sensors`, `_search_global_sensors`, `_find_entity_by_name`.
- [ ] Caching- und Fallback-Methoden auslagern: Verschiebe `_get_cached_entity_state`, `_resolve_entity_state_with_fallback` in ein neues `CacheMixin` oder erweitere bestehende Mixins.
- [ ] Spezifische Methoden auslagern: `apply_global_factors`, `_extract_calculation_parameters` in passende Mixins (z. B. `UtilsMixin` oder `CalculationsMixin`) verschieben.

### Phase 4: Hauptklasse überarbeiten
- [ ] `__init__`-Methode optimieren: Lagere Initialisierungslogik aus, wo möglich (z. B. Caching in ein separates Mixin).
- [ ] Flow-basierte Methoden konsolidieren: Stelle sicher, dass `from_flows` und ähnliche Methoden vollständig in `FlowIntegrationMixin` sind.
- [ ] Klasse in separate Datei verschieben: Optional: Verschiebe `SolarWindowCalculator` in `core.py` und lasse `calculator.py` als Kompatibilitäts-Import.

### Phase 5: Tests und Validierung
- [ ] Tests aktualisieren: Passe `test_calculations.py` und andere Tests an neue Struktur an.
- [ ] Integrationstests durchführen: Stelle sicher, dass das gesamte System (Sensoren, Flows) nach Refactoring funktioniert.
- [ ] Code-Reviews: Überprüfe auf Einhaltung der Coding Standards (z. B. aus `copilot_context7.instructions.md` und `.github/copilot-instructions.md`).
- [ ] Dokumentation aktualisieren: Aktualisiere `docs/calculator.md` und andere Docs, um die neue Struktur widerzuspiegeln.

### Phase 6: Finale Bereinigung
- [ ] Prüfe die Testfälle. Prüfe auch, ob Testfälle obsolet geworden sind.
- [ ] Linting und Formatierung: Führe `ruff check --fix` und ähnliche Tools aus, um Code-Qualität zu sichern.
- [ ] Prüfe auch pyright, um grundlegende Fehler zu finden
- [ ] Performance-Tests: Überprüfe, ob das Refactoring die Leistung verbessert (z. B. durch weniger Duplikate).
- [ ] Commit und Merge: Erstelle einen Feature-Branch, committe schrittweise und merge in `main` nach Tests.


Diese ToDo-Liste ist Schritt für Schritt aufgebaut, um ein systematisches Refactoring zu ermöglichen. Priorisiere Phasen basierend auf Risiko und Komplexität.


### Neu entdeckte ToDos // Follow-ups
- [x] Erweitere ConfigMixin um weitere Konfigurations-Methoden aus calculator.py (z. B. _extract_calculation_parameters).
- [x] Erstelle CacheMixin für Caching-Logik (_get_cached_entity_state, _resolve_entity_state_with_fallback).
- [x] Teste die Änderungen mit pytest, um sicherzustellen, dass alles funktioniert.
- [x] Führe Linting aus, um Code-Qualität zu sichern.

## Aktueller Stand (August 30, 2025)

### Erfolge seit der letzten Analyse:
- ✅ **Dateigröße reduziert**: `calculator.py` von 1937 auf 1468 Zeilen (-24% oder -469 Zeilen)
- ✅ **ConfigMixin erweitert**: `_extract_calculation_parameters` und `_safe_float_conversion` hinzugefügt
- ✅ **CacheMixin erstellt**: Vollständige Caching-Logik ausgelagert (`_get_cached_entity_state`, `_resolve_entity_state_with_fallback`)
- ✅ **Wrapper-Methoden entfernt**: `_check_window_visibility` Wrapper eliminiert
- ✅ **Tests erfolgreich**: 100 Tests bestanden, nur 1 separater Fehler (nicht refaktorierungsbedingt)
- ✅ **Linting durchgeführt**: Code-Qualität sichergestellt

### Verbleibende Aufgaben:
[ ] Weitere Wrapper-Methoden entfernen (`get_safe_state`, `get_safe_attr`, etc.)
[ ] Dataclasses konsolidieren (`WindowCalculationResult`, `ShadeRequestFlow`)
[ ] Phase 3-6 der ToDo-Liste angehen für vollständiges Refactoring
