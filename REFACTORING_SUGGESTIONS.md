# Refactoring Suggestions für config_flow.py

## Problem: Mehrfache `_ui_default` Funktionen
Aktuell gibt es 6 verschiedene `_ui_default` Funktionen im Code, was zu Inkonsistenzen führt.

## Lösung: Zentrale Utility-Funktion

```python
def make_ui_default_safe(defaults: dict, global_data: dict = None) -> callable:
    """
    Factory function to create a safe _ui_default function that always returns strings.

    Args:
        defaults: Local defaults dictionary
        global_data: Optional global defaults for inheritance logic

    Returns:
        Function that converts any value to string for Voluptuous compatibility
    """
    def _ui_default(key: str) -> str:
        cur = defaults.get(key, "")
        if global_data:
            gv = global_data.get(key, "")
            if cur in ("", None) and gv not in ("", None):
                return "-1"  # Inheritance indicator
        # CRITICAL: Always convert to string for Voluptuous schema compatibility
        return str(cur) if cur not in ("", None) else ""

    return _ui_default
```

## Verwendung:
```python
# Statt:
def _ui_default(key: str) -> str:
    cur = enhanced_defaults.get(key, "")
    return cur if cur not in ("", None) else ""  # BUG: Kann numerisch sein!

# Verwende:
_ui_default = make_ui_default_safe(enhanced_defaults, global_data)
```

## Weitere Verbesserungen:

### 1. Bessere Kommentierung an kritischen Stellen
```python
# CRITICAL: Voluptuous vol.Optional(default=X) requires X to be a string
# when used with string validation. Numeric values from saved data must
# be converted to strings to avoid "expected str" validation errors.
```

### 2. Type Hints für Klarheit
```python
def _page1_defaults(self, group_options_map: list[tuple[str, str]]) -> dict[str, str]:
    """Returns defaults as strings to prevent Voluptuous validation errors."""
```

### 3. Zentrale Konstanten
```python
# At top of file
INHERITANCE_INDICATOR = "-1"
EMPTY_STRING_VALUES = ("", None)
```

### 4. Schema Builder Helper
```python
def build_text_field_schema(key: str, ui_default_func: callable, required: bool = False) -> tuple:
    """Helper to build consistent text field schemas."""
    if required:
        return vol.Required(key, default=ui_default_func(key)), str
    else:
        return vol.Optional(key, default=ui_default_func(key)), str
```
