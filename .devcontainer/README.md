# DevContainer Setup

Dieses Projekt nutzt einen [VS Code DevContainer](https://code.visualstudio.com/docs/devcontainers/containers) für eine konsistente Entwicklungsumgebung.

## Voraussetzungen

- [VS Code](https://code.visualstudio.com/) mit der [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (läuft im Hintergrund)

## Schnellstart

1. **Repository öffnen** in VS Code
2. **"Reopen in Container"** wählen:
   - `Strg+Shift+P` → "Dev Containers: Reopen in Container"
   - Oder klick auf das grüne Icon unten links

3. **Warten** - Beim ersten Start wird der Container gebaut (~2-3 Minuten)

4. **Home Assistant starten**:
   ```bash
   scripts/start-ha.sh
   # oder mit sauberer Datenbank:
   scripts/start-ha.sh --clean
   ```

5. **Home Assistant öffnen**: http://localhost:8123

## Enthaltene Tools

- Python 3.14
- Home Assistant (Version aus `requirements-test.txt`)
- pytest + pytest-homeassistant-custom-component
- ruff (Linting & Formatting)
- pyright (Type Checking)
- Pre-commit hooks

## VS Code Extensions (automatisch installiert)

- Python + Pylance
- Black Formatter
- Ruff
- YAML Support
- JSON Support

## Port Weiterleitung

- **8123** → Home Assistant (automatisch geöffnet)

## Wichtige Befehle

```bash
# Tests ausführen
pytest tests/ -v

# Alle Quality Checks
scripts/quality-gate.sh

# Home Assistant starten
scripts/start-ha.sh

# Mit sauberer Datenbank starten
scripts/start-ha.sh --clean
```

## Datenpersistenz

- Das `config/` Verzeichnis wird **nicht** im Container persistiert
- Für Tests wird es bei jedem Start neu angelegt
- Um Einstellungen zu behalten: In HA UI konfigurieren oder `configuration.yaml` im Projekt anpassen

## Fehlerbehebung

### Container startet nicht

```bash
# Docker prüfen
docker ps

# Container manuell rebuilden
Strg+Shift+P → "Dev Containers: Rebuild Container"
```

### Home Assistant startet nicht

```bash
# Config prüfen
ls -la config/

# Mit sauberem Start versuchen
scripts/start-ha.sh --clean
```

### Ports nicht erreichbar

In VS Code unter "Ports" prüfen ob 8123 weitergeleitet wird.

## Alternative: Lokale Entwicklung

Falls der DevContainer nicht funktioniert, geht auch:
- **WSL2** (Linux Subsystem für Windows)
- **Virtuelle Umgebung** mit Python 3.12+

Siehe `scripts/README.md` für Details.
