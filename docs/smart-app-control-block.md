# Bloqueo de Smart App Control

Al intentar iniciar el sandbox desde la raíz del proyecto:

```powershell
uv run streamlit run examples/debug_app.py
```

Windows bloquea el ejecutable `streamlit` con el error:

```text
An Application Control policy has blocked this file. (os error 4551)
```

El entorno virtual había funcionado anteriormente. Activarlo y ajustar la
política de ejecución de PowerShell no impiden el bloqueo, porque esta afecta
a los scripts de PowerShell, no a Smart App Control.

Un evento del registro `Microsoft-Windows-CodeIntegrity/Operational` con el
ID 3118 confirma que Smart App Control también bloqueó
`.venv\Scripts\python.exe`. El evento no explica por qué cambió el
comportamiento ni demuestra que el archivo sea malicioso.

## Acción realizada - 27/11/2026

Posteriormente se deshabilitó Smart App Control en el equipo. No se ha
registrado si se volvió a probar el comando después de deshabilitarlo.
