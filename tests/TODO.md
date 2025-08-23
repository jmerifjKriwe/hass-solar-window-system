# Test-Reorganisation: To‑Do Liste

Diese Datei enthält die 11 Schritte, die als To‑Do Liste für die Reorganisation und Verbesserung der Tests im Projekt festgelegt wurden.

Status: Teilweise erledigt — 1–4 umgesetzt (siehe Commits auf branch `refactor/tests-reorg`)

1. Konsolidierung doppelter Tests — Done
   - Zusammenführen von duplizierten Tests in parametrisierte Tests (z. B. Services, Plattformen).

2. Zentralisierung gemeinsamer Fixtures — Done
   - Auslagern wiederverwendbarer Fixtures in `tests/helpers/fixtures_helpers.py`.

3. Exponieren der Helper als pytest‑Plugins — Done
   - `tests/conftest.py` so anpassen, dass die Helper‑Module über `pytest_plugins` geladen werden.

4. Parametrisierung von Plattform‑Tests — Done
   - Plattformtests über eine `PLATFORMS`‑Liste parametrieren und `collect_entities_for_setup` verwenden. Mehrere legacy platform test files wurden als konsolidiert markiert.

5. Nutzung öffentlicher Home‑Assistant APIs in Tests — Done
   - Tests so umschreiben, dass sie nur die öffentlichen HA‑APIs verwenden (z. B. `MockConfigEntry`, `entry.add_to_hass`, `async_setup_entry`) und keine privaten internals manipulieren.

6. Entfernen/Refaktorieren von Tests, die interne Zustände manipulieren
   - Tests entfernen oder umschreiben, die direkt auf private Attribute zugreifen (z. B. `_reconfigure_mode`) statt `async_step_reconfigure` zu verwenden.

7. Konsolidierung von Geräte‑Fixtures — Done
   - Eine standardisierte `global_device`‑Fixture bereitstellen, die überall verwendet wird.

8. Helfer: Rückgabe hinzugefügter Entitäten + einfacher Assert
   - `collect_entities_for_setup_with_assert` hinzufügen, die (entities, assert_non_empty) zurückgibt, um Boilerplate in Tests zu vermeiden.

9. Extrahieren wiederholter Konstanten
   - Gemeinsame Literale (z. B. Namen) in `tests/constants.py` auslagern (z. B. `GLOBAL_DEVICE_NAME`).

10. Snapshot‑Tests für Diagnostics
    - Syrupy‑basierte Snapshot‑Tests für `diagnostics` anlegen und Snapshots unter `tests/**/__snapshots__/` ablegen.

11. Linting & Dokumentation
    - `ruff` laufen lassen, sichere Fixes anwenden, verbleibende Issues dokumentieren; `tests/TESTING.md` → `tests/README.md` umbenennen und Snapshot‑Guidance ergänzen.

---

Nächste Schritte:
- Auf Wunsch kann ich jetzt die ersten 1–3 Items automatisch implementieren (Fixtures zentralisieren, helpers exposen, doppelte Tests zusammenführen). Bitte kurz bestätigen, mit welchen Punkten ich anfangen soll.
