#!/usr/bin/env python3
"""
Home Assistant Custom Component Language File Manager.

Automatisiert die Erstellung und Verwaltung von Translation Files.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class HALanguageManager:
    """Manages language files for a Home Assistant custom component."""

    def __init__(self, component_path: str | None = None) -> None:
        """Initialize the language manager."""
        if component_path is None:
            component_path = self.find_component_directory()

        self.component_path = Path(component_path)
        self.translations_path = self.component_path / "translations"
        self.translations_path.mkdir(exist_ok=True)

        # Standard Sprachen für Home Assistant
        self.default_languages = ["en", "de", "fr", "es", "it", "nl", "pl", "pt", "ru"]

        # Standard Translation Keys für HA Components
        self.standard_keys: dict[str, dict[str, Any]] = {
            "config": {
                "step": {
                    "user": {
                        "title": "Setup",
                        "description": "Configure your component",
                        "data": {},
                    }
                },
                "error": {
                    "cannot_connect": "Failed to connect",
                    "invalid_auth": "Invalid authentication",
                    "unknown": "Unknown error occurred",
                },
                "abort": {"already_configured": "Device is already configured"},
            },
            "options": {"step": {"init": {"title": "Options", "data": {}}}},
            "entity": {},
            "device_automation": {},
        }

    def find_component_directory(self) -> str:
        """Findet automatisch das Component-Verzeichnis."""
        current_dir = Path.cwd()

        # Suche nach custom_components Verzeichnis
        search_paths = [
            current_dir,
            current_dir / "custom_components",
            current_dir.parent / "custom_components"
            if current_dir.parent != current_dir
            else None,
        ]

        search_paths = [p for p in search_paths if p is not None]

        for search_path in search_paths:
            if search_path.exists():
                if (search_path / "manifest.json").exists():
                    logger.info("Component gefunden: %s", search_path)
                    return str(search_path)

                if search_path.name == "custom_components":
                    components = [
                        d
                        for d in search_path.iterdir()
                        if d.is_dir() and (d / "manifest.json").exists()
                    ]

                    if len(components) == 1:
                        logger.info("Component automatisch erkannt: %s", components[0])
                        return str(components[0])
                    if len(components) > 1:
                        logger.info("Mehrere Components gefunden in %s:", search_path)
                        for i, comp in enumerate(components, 1):
                            logger.info("  %d. %s", i, comp.name)

                        try:
                            choice = (
                                int(input("Wählen Sie eine Component (Nummer): ")) - 1
                            )
                            if 0 <= choice < len(components):
                                logger.info("Component gewählt: %s", components[choice])
                                return str(components[choice])
                        except (ValueError, IndexError):
                            pass

                        err_msg = "Ungültige Auswahl"
                        raise ValueError(err_msg)

                for subdir in search_path.iterdir():
                    if subdir.is_dir() and (subdir / "manifest.json").exists():
                        logger.info("Component gefunden: %s", subdir)
                        return str(subdir)

        component_files = ["__init__.py", "manifest.json", "config_flow.py"]
        if any((current_dir / f).exists() for f in component_files):
            logger.info("Component im aktuellen Verzeichnis erkannt: %s", current_dir)
            return str(current_dir)

        err_msg = (
            "Kein Home Assistant Component gefunden!\n"
            "Führen Sie das Script aus:\n"
            "- Im Component-Verzeichnis\n"
            "- Im custom_components Verzeichnis\n"
            "- Oder geben Sie den Pfad explizit an"
        )
        raise ValueError(err_msg)

    def scan_translation_keys(self) -> set[str]:
        """Scannt den Component Code nach Translation Keys."""
        keys = set()

        patterns = [
            r"hass\.localize\([\'\\]\'([^\'\\]+)\'\'\)",
            r"translation_key\s*=\s*[\'\\]\'([^\'\\]+)\'\'\)",
            r"_attr_translation_key\s*=\s*[\'\\]\'([^\'\\]+)\'\'\)",
            r"async_translate\([\'\\]\'([^\'\\]+)\'\'\)",
            r"[\'\\]\'translation_key[\'\\][\'\\]:\s*[\'\\]\'([^\'\\]+)\'\'\)",
        ]

        for py_file in self.component_path.rglob("*.py"):
            try:
                with py_file.open(encoding="utf-8") as f:
                    content = f.read()

                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    keys.update(matches)

            except OSError as e:
                logger.warning("Fehler beim Lesen von %s: %s", py_file, e)

        return keys

    def extract_config_flow_keys(self) -> dict[str, Any]:
        """Extrahiert spezielle Keys aus config_flow.py."""
        config_flow_path = self.component_path / "config_flow.py"
        keys: dict[str, dict[str, Any]] = {
            "config": {"step": {}, "error": {}, "abort": {}}
        }

        if not config_flow_path.exists():
            return keys

        try:
            with config_flow_path.open(encoding="utf-8") as f:
                content = f.read()

            step_matches = re.findall(r"async def async_step_(\w+)", content)
            for step in step_matches:
                keys["config"][f"step_{step}"] = {
                    "title": f"{step.title()} Step",
                    "description": f"Configure {step} settings",
                    "data": {},
                }

            error_matches = re.findall(r"errors\[[\'\\]\'(\w+)[\'\\]\'\}", content)
            for error in error_matches:
                keys["config"]["error"][error] = f"Error: {error}"

            abort_matches = re.findall(
                r"async_abort\(reason=[\'\\]\'(\w+)[\'\\]\'\)", content
            )
            for abort in abort_matches:
                keys["config"]["abort"][abort] = f"Aborted: {abort}"

        except OSError as e:
            logger.warning("Fehler beim Parsen von config_flow.py: %s", e)

        return keys

    def load_existing_translations(self, language: str) -> dict[str, Any]:
        """Lädt existierende Übersetzungen für eine Sprache."""
        lang_file = self.translations_path / f"{language}.json"

        if lang_file.exists():
            try:
                with lang_file.open(encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("Fehler beim Laden von %s: %s", lang_file, e)

        return {}

    def save_translations(self, language: str, translations: dict[str, Any]) -> None:
        """Speichert Übersetzungen in eine Datei."""
        lang_file = self.translations_path / f"{language}.json"

        try:
            with lang_file.open("w", encoding="utf-8") as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
            logger.info("Gespeichert: %s", lang_file)
        except OSError:
            logger.exception("Fehler beim Speichern von %s", lang_file)

    def merge_translations(
        self,
        existing: dict[str, Any],
        new: dict[str, Any],
    ) -> dict[str, Any]:
        """Mergt neue Keys in existierende Übersetzungen."""

        def deep_merge(base: dict, update: dict) -> dict:
            result = base.copy()
            for key, value in update.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                elif key not in result:
                    result[key] = value
            return result

        return deep_merge(existing, new)

    def create_language_files(self, languages: list[str] | None = None) -> None:
        """Erstellt oder aktualisiert Language Files."""
        if languages is None:
            languages = self.default_languages

        scanned_keys = self.scan_translation_keys()
        logger.info("Gefundene Translation Keys: %d", len(scanned_keys))

        config_keys = self.extract_config_flow_keys()

        base_structure = self.standard_keys.copy()
        base_structure = self.merge_translations(base_structure, config_keys)

        for key in scanned_keys:
            if "." in key:
                parts = key.split(".")
                current = base_structure["entity"]
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = {"name": parts[-1].replace("_", " ").title()}
            else:
                base_structure["entity"][key] = {"name": key.replace("_", " ").title()}

        for lang in languages:
            existing = self.load_existing_translations(lang)
            merged = self.merge_translations(existing, base_structure)
            self.save_translations(lang, merged)

    def check_missing_keys(self) -> dict[str, list[str]]:
        """Prüft auf fehlende Keys zwischen verschiedenen Sprachen."""
        missing_keys: dict[str, list[str]] = {}
        lang_files = list(self.translations_path.glob("*.json"))

        if not lang_files:
            return missing_keys

        all_translations: dict[str, dict[str, Any]] = {}
        for lang_file in lang_files:
            lang = lang_file.stem
            all_translations[lang] = self.load_existing_translations(lang)

        all_keys: set[str] = set()

        def extract_keys(obj: Any, prefix: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    all_keys.add(current_key)
                    extract_keys(value, current_key)

        for translations in all_translations.values():
            extract_keys(translations)

        for lang, translations in all_translations.items():
            lang_keys: set[str] = set()
            extract_keys(translations, "")
            missing_keys[lang] = sorted(all_keys - lang_keys)

        return missing_keys

    def generate_report(self) -> None:
        """Generiert einen Bericht über den Status der Übersetzungen."""
        logger.info("\n=== Home Assistant Translation Report ===")
        logger.info("Component Path: %s", self.component_path)
        logger.info("Translations Path: %s", self.translations_path)

        scanned_keys = self.scan_translation_keys()
        logger.info("\nGefundene Translation Keys im Code: %d", len(scanned_keys))
        for key in sorted(scanned_keys):
            logger.info("  - %s", key)

        lang_files = list(self.translations_path.glob("*.json"))
        logger.info("\nVorhandene Sprachdateien: %d", len(lang_files))
        for lang_file in lang_files:
            translations = self.load_existing_translations(lang_file.stem)
            key_count = sum(1 for _ in self._count_keys(translations))
            logger.info("  - %s: %d Keys", lang_file.name, key_count)

        missing = self.check_missing_keys()
        if any(missing.values()):
            logger.info("\nFehlende Keys:")
            for lang, keys in missing.items():
                if keys:
                    logger.info("  %s: %d fehlende Keys", lang, len(keys))

    def _count_keys(self, obj: Any) -> Any:
        """Hilfsfunktion zum Zählen aller Keys in einem verschachtelten Dict."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                yield key
                yield from self._count_keys(value)


def main() -> int:
    """Return main function."""
    parser = argparse.ArgumentParser(
        description="Home Assistant Custom Component Language File Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    epilog = f"""
Beispiele:
  {parser.prog} --report
    Automatische Erkennung und Report für gefundene Component

  {parser.prog} /path/to/component --create
    Erstellt Standard Language Files für spezifische Component

  {parser.prog} /path/to/component --create -l en de
    Erstellt nur Englisch und Deutsch Language Files

  {parser.prog} /path/to/component --report
    Zeigt einen detaillierten Report über vorhandene Übersetzungen

  {parser.prog} /path/to/component --check
    Prüft auf fehlende Keys zwischen verschiedenen Sprachen

  {parser.prog} /path/to/component --create --report
    Erstellt Language Files und zeigt anschließend einen Report

Das Script scannt automatisch nach Translation Keys im Code und erstellt
die entsprechenden JSON-Strukturen für Home Assistant Components.
    """
    parser.epilog = epilog

    parser.add_argument(
        "component_path",
        nargs="?",
        help=(
            "Pfad zum Custom Component Verzeichnis "
            "(optional - wird automatisch erkannt)"
        ),
    )
    parser.add_argument(
        "--languages",
        "-l",
        nargs="+",
        help="Sprachen (Standard: en de fr es it nl pl pt ru)",
    )
    parser.add_argument(
        "--create",
        "-c",
        action="store_true",
        help="Erstelle/aktualisiere Language Files",
    )
    parser.add_argument(
        "--report",
        "-r",
        action="store_true",
        help="Zeige detaillierten Übersetzungsreport",
    )
    parser.add_argument(
        "--check", action="store_true", help="Prüfe auf fehlende Keys zwischen Sprachen"
    )

    args = parser.parse_args()

    if args.component_path and not Path(args.component_path).exists():
        logger.error("Component Pfad existiert nicht: %s", args.component_path)
        return 1

    if not any([args.create, args.report, args.check]):
        parser.print_help()
        return 1

    try:
        manager = HALanguageManager(args.component_path)
    except ValueError:
        logger.exception("Fehler beim Initialisieren des Language Managers")
        return 1

    if args.create:
        component_name = manager.component_path.name
        logger.info(
            "Erstelle Language Files für Component '%s': %s",
            component_name,
            manager.component_path,
        )
        manager.create_language_files(args.languages)
        logger.info("✓ Language Files erfolgreich erstellt/aktualisiert")

    if args.report:
        manager.generate_report()

    if args.check:
        missing = manager.check_missing_keys()
        if any(missing.values()):
            logger.warning("\n⚠️  Fehlende Keys gefunden:")
            for lang, keys in missing.items():
                if keys:
                    # Truncate long lists of keys for readability
                    max_keys_to_show = 5
                    truncated_keys = keys[:max_keys_to_show]
                    remaining_keys = len(keys) - max_keys_to_show

                    log_message = f"  {lang}: {', '.join(truncated_keys)}"
                    if remaining_keys > 0:
                        log_message += f" ... und {remaining_keys} weitere"

                    logger.warning(log_message)
        else:
            logger.info("\n✓ Keine fehlenden Keys gefunden!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
