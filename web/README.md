# Interfaz web - Anuario Estadístico 2026

Frontend React/Vite para visualizar las figuras mientras el pipeline las genera.

## Compilar

```powershell
cd web
npm install
npm run build
```

El comando principal `..\preparar_entorno.ps1` hace estos pasos automáticamente.
Después, desde la raíz del proyecto:

```powershell
.\ejecutar.ps1 web
```

La API local corre por defecto en `http://127.0.0.1:8765`. Durante desarrollo se puede
usar `npm run dev`; Vite redirige `/api` al backend local.
