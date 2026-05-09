# Issues — mazda-port-to-sunnypilot

## 2026-05-09 Initial

- numpy not installed at system Python level (must use opendbc venv or pip3 --break-system-packages)
- macOS-only available: Linux required for full safety pytest and scons build; rely on py_compile + import smoke for code-completion sign-off
