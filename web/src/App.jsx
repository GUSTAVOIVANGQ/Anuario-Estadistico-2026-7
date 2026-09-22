import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Archive,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Circle,
  Download,
  FileImage,
  FileText,
  Layers3,
  LoaderCircle,
  Menu,
  MonitorPlay,
  PanelLeftClose,
  PanelLeftOpen,
  Play,
  Presentation,
  RefreshCw,
  Search,
  Settings2,
  Sparkles,
  SquareStack,
  X,
  Zap,
} from 'lucide-react'

const exportOptions = [
  { kind: 'pdf', label: 'PDF', detail: 'SVG vectorial · texto copiable', icon: FileText },
  { kind: 'pptx', label: 'PPTX', detail: 'SVG nativo · respaldo PNG', icon: Presentation },
  { kind: 'jpg', label: 'JPG', detail: 'Alta calidad · desde código', icon: FileImage },
  { kind: 'png', label: 'PNG', detail: 'Sin pérdida · desde código', icon: SquareStack },
  { kind: 'svg', label: 'SVG', detail: 'Vector editable · texto real', icon: Layers3 },
]

function App() {
  const [catalog, setCatalog] = useState({ project: 'Anuario Estadístico 2026', figures: [], available_count: 0 })
  const [selected, setSelected] = useState(new Set())
  const [activeId, setActiveId] = useState(null)
  const [section, setSection] = useState('Todas')
  const [query, setQuery] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [run, setRun] = useState(null)
  const [processing, setProcessing] = useState(false)
  const [generated, setGenerated] = useState([])
  const [refreshKey, setRefreshKey] = useState(0)
  const [showExport, setShowExport] = useState(false)
  const [downloadKind, setDownloadKind] = useState(null)
  const [toast, setToast] = useState(null)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    loadCatalog()
    return () => eventSourceRef.current?.close()
  }, [])

  async function loadCatalog() {
    try {
      const response = await fetch('/api/figures')
      if (!response.ok) throw new Error('No se pudo cargar el catálogo')
      const data = await response.json()
      setCatalog(data)
      const first = data.figures.find((item) => item.available) || data.figures[0]
      if (first) {
        setActiveId((current) => current || first.id)
        setSelected((current) => current.size ? current : new Set([first.id]))
      }
    } catch (error) {
      notify(error.message, 'error')
    }
  }

  const sections = useMemo(() => ['Todas', ...new Set(catalog.figures.map((item) => item.section))], [catalog.figures])
  const activeFigure = catalog.figures.find((item) => item.id === activeId)
  const filteredFigures = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return catalog.figures.filter((item) => {
      const sectionMatches = section === 'Todas' || item.section === section
      const textMatches = !normalized || `${item.id} ${item.title}`.toLowerCase().includes(normalized)
      return sectionMatches && textMatches
    })
  }, [catalog.figures, section, query])

  const progress = run?.total ? Math.min(100, (run.completed / run.total) * 100) : 0
  const isRunning = run?.status === 'running' || run?.status === 'queued'

  function notify(message, type = 'info') {
    setToast({ message, type })
    window.clearTimeout(window.__anuarioToast)
    window.__anuarioToast = window.setTimeout(() => setToast(null), 4200)
  }

  function toggleSelected(figure, event) {
    event?.stopPropagation()
    if (!figure.available || isRunning) return
    setSelected((current) => {
      const next = new Set(current)
      if (next.has(figure.id)) next.delete(figure.id)
      else next.add(figure.id)
      return next
    })
  }

  function selectSectionFigures(sectionId) {
    if (isRunning) return
    const ids = catalog.figures.filter((item) => item.available && (sectionId === 'Todas' || item.section === sectionId)).map((item) => item.id)
    setSelected(new Set(ids))
  }

  async function startRun(mode, ids = []) {
    if (isRunning) return
    eventSourceRef.current?.close()
    setShowExport(false)
    setGenerated([])
    setProcessing(false)
    try {
      const response = await fetch('/api/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode, figure_ids: ids }),
      })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.detail || 'No se pudo iniciar la corrida')
      setRun({ ...payload, completed: payload.completed || 0 })
      connectEvents(payload.run_id)
    } catch (error) {
      notify(error.message, 'error')
    }
  }

  function connectEvents(runId) {
    const source = new EventSource(`/api/runs/${runId}/events`)
    eventSourceRef.current = source
    source.onmessage = (event) => {
      const payload = JSON.parse(event.data)
      handleRunEvent(payload, source)
    }
    source.onerror = async () => {
      if (source.readyState === EventSource.CLOSED) return
      try {
        const response = await fetch(`/api/runs/${runId}`)
        if (!response.ok) return
        const snapshot = await response.json()
        setRun(snapshot)
        if (snapshot.status === 'finished') {
          source.close()
          setProcessing(false)
          setShowExport(true)
        }
      } catch {
        // El navegador intentará reconectar automáticamente.
      }
    }
  }

  function handleRunEvent(event, source) {
    if (event.type === 'run_started') {
      setRun((current) => ({ ...current, status: 'running', total: event.total, completed: current?.completed || 0 }))
    }
    if (event.type === 'figure_started') {
      setProcessing(true)
      setActiveId(event.figure_id)
      setRun((current) => ({ ...current, status: 'running', current_figure: event.figure_id, current_title: event.title }))
    }
    if (event.type === 'figure_finished') {
      setProcessing(false)
      setActiveId(event.figure_id)
      setRefreshKey(Date.now())
      if (event.status === 'OK') {
        setGenerated((current) => current.includes(event.figure_id) ? current : [...current, event.figure_id])
      }
      setRun((current) => {
        const statuses = { ...(current?.figure_statuses || {}), [event.figure_id]: event }
        return {
          ...current,
          completed: Object.keys(statuses).length,
          figure_statuses: statuses,
          current_figure: event.figure_id,
          current_title: event.title,
        }
      })
      if (event.status === 'ERROR') notify(`${event.figure_id}: ${event.message}`, 'error')
    }
    if (event.type === 'ui_complete') {
      source.close()
      setProcessing(false)
      setRun((current) => ({ ...current, status: 'finished', counts: event.counts, completed: event.completed, total: event.total }))
      setShowExport(true)
    }
    if (event.type === 'ui_error') {
      source.close()
      setProcessing(false)
      setRun((current) => ({ ...current, status: 'error', error: event.error }))
      notify(event.error, 'error')
    }
  }

  async function downloadExport(kind) {
    if (!run?.run_id || downloadKind) return
    setDownloadKind(kind)
    try {
      const response = await fetch(`/api/exports/${run.run_id}/${kind}`)
      if (!response.ok) {
        let detail = 'No se pudo preparar la descarga'
        try {
          const payload = await response.json()
          detail = payload.detail || detail
        } catch {}
        throw new Error(detail)
      }
      const blob = await response.blob()
      const disposition = response.headers.get('content-disposition') || ''
      const match = disposition.match(/filename="?([^";]+)"?/i)
      const filename = match?.[1] || `anuario_estadistico_2026.${kind === 'pptx' ? 'pptx' : kind === 'pdf' ? 'pdf' : 'zip'}`
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
      notify(`Descarga ${kind.toUpperCase()} lista`, 'success')
    } catch (error) {
      notify(error.message, 'error')
    } finally {
      setDownloadKind(null)
    }
  }

  function navigateFigure(direction) {
    if (!activeFigure) return
    const figures = catalog.figures
    const index = figures.findIndex((item) => item.id === activeFigure.id)
    const next = Math.max(0, Math.min(figures.length - 1, index + direction))
    setActiveId(figures[next]?.id || activeId)
  }

  return (
    <div className={`app-shell ${sidebarOpen ? '' : 'sidebar-collapsed'}`}>
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark"><span>CRT</span><Sparkles size={14} /></div>
          <button className="icon-button sidebar-toggle" onClick={() => setSidebarOpen(false)} title="Ocultar panel"><PanelLeftClose size={18} /></button>
        </div>

        <div className="sidebar-title">
          <p>Comisión Reguladora de Telecomunicaciones</p>
          <h1>Anuario<br /><span>Estadístico</span> 2026</h1>
        </div>

        <div className="action-stack">
          <button className="action-button primary" disabled={isRunning} onClick={() => startRun('all')}>
            {isRunning ? <LoaderCircle className="spin" size={19} /> : <MonitorPlay size={19} />}
            <span><strong>Corrida completa</strong><small>{catalog.available_count} figuras disponibles</small></span>
          </button>
          <button className="action-button" disabled={!activeFigure?.available || isRunning} onClick={() => startRun('single', activeFigure ? [activeFigure.id] : [])}>
            <Play size={18} />
            <span><strong>Crear figura actual</strong><small>{activeFigure?.id || 'Selecciona una figura'}</small></span>
          </button>
          <button className="action-button" disabled={!selected.size || isRunning} onClick={() => startRun('selection', [...selected])}>
            <Zap size={18} />
            <span><strong>Ejecutar selección</strong><small>{selected.size} figura{selected.size === 1 ? '' : 's'} seleccionada{selected.size === 1 ? '' : 's'}</small></span>
          </button>
        </div>

        <div className="catalog-head">
          <div><span>FIGURAS</span><b>{catalog.figures.length}</b></div>
          <button className="ghost-mini" onClick={() => selectSectionFigures(section)}>Seleccionar sección</button>
        </div>
        <div className="search-box"><Search size={15} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar A.1, conectividad…" /></div>
        <div className="section-tabs">
          {sections.map((item) => <button key={item} className={section === item ? 'active' : ''} onClick={() => setSection(item)}>{item}</button>)}
        </div>
        <div className="figure-list">
          {filteredFigures.map((figure) => {
            const checked = selected.has(figure.id)
            const runState = run?.figure_statuses?.[figure.id]?.status
            return (
              <button key={figure.id} className={`figure-row ${activeId === figure.id ? 'active' : ''} ${!figure.available ? 'disabled' : ''}`} onClick={() => setActiveId(figure.id)}>
                <span className={`checkbox ${checked ? 'checked' : ''}`} onClick={(event) => toggleSelected(figure, event)}>
                  {checked ? <Check size={12} /> : null}
                </span>
                <span className="figure-id">{figure.id}</span>
                <span className="figure-name">{figure.title}</span>
                <span className={`state-dot ${runState === 'OK' ? 'ok' : runState === 'ERROR' ? 'error' : figure.available ? 'ready' : 'pending'}`} />
              </button>
            )
          })}
        </div>
        <div className="sidebar-footer"><Settings2 size={14} /><span>Proyecto v{catalog.version || '0.27.0'}</span><span className="live-dot" />Local</div>
      </aside>

      {!sidebarOpen && <button className="sidebar-open-button" onClick={() => setSidebarOpen(true)}><PanelLeftOpen size={19} /></button>}

      <main className="workspace">
        <header className="topbar">
          <div className="topbar-title">
            <span className="eyebrow">ESTUDIO · FIGURAS · PRESENTACIÓN</span>
            <h2>Anuario Estadístico <span>2026</span></h2>
          </div>
          <div className="topbar-actions">
            <div className={`run-pill ${isRunning ? 'running' : run?.status === 'finished' ? 'done' : ''}`}>
              {isRunning ? <LoaderCircle className="spin" size={14} /> : run?.status === 'finished' ? <CheckCircle2 size={14} /> : <Circle size={10} />}
              {isRunning ? `${run.completed || 0}/${run.total || 0} procesadas` : run?.status === 'finished' ? 'Corrida finalizada' : 'Listo para ejecutar'}
            </div>
            <button className="export-top" disabled={!run || run.status !== 'finished'} onClick={() => setShowExport(true)}><Download size={17} /> Exportar</button>
          </div>
        </header>

        <section className="monitor-area">
          <div className={`monitor-card ${processing ? 'processing' : ''}`}>
            <div className="monitor-chrome">
              <div className="chrome-left"><span className="status-led" /><span>{processing ? `Procesando ${run?.current_figure || activeId}` : activeFigure ? `Vista · ${activeFigure.id}` : 'Vista de proyecto'}</span></div>
              <div className="chrome-center">{activeFigure?.title || 'Visualizador de figuras'}</div>
              <div className="chrome-right"><span>{activeFigure?.section ? `Sección ${activeFigure.section}` : '—'}</span><span className="resolution">PNG</span></div>
            </div>

            <div className="stage">
              <div className="stage-grid" />
              {activeFigure?.has_preview || generated.includes(activeFigure?.id) ? (
                <div className="image-frame" key={`${activeId}-${refreshKey}`}>
                  <img src={`${activeFigure.preview_url}?v=${refreshKey}`} alt={`Figura ${activeFigure.id}`} onError={(event) => { event.currentTarget.style.opacity = 0 }} />
                  {processing && run?.current_figure === activeFigure.id && <div className="scan-line" />}
                </div>
              ) : (
                <div className="empty-stage">
                  <div className="orb"><Archive size={34} /></div>
                  <span className="empty-kicker">PREVISUALIZACIÓN EN TIEMPO REAL</span>
                  <h3>{activeFigure ? `Figura ${activeFigure.id}` : 'Anuario Estadístico 2026'}</h3>
                  <p>{activeFigure?.available ? 'Ejecuta la figura para verla aparecer aquí al terminar su procesamiento.' : activeFigure ? 'Esta figura todavía no está disponible para ejecución automática.' : 'Selecciona una figura o inicia una corrida completa.'}</p>
                  {activeFigure?.available && <button className="stage-run" disabled={isRunning} onClick={() => startRun('single', [activeFigure.id])}><Play size={16} /> Crear figura</button>}
                </div>
              )}

              {processing && <div className="processing-badge"><LoaderCircle className="spin" size={16} /><span>Generando imagen</span><i /></div>}
              <button className="stage-nav left" onClick={() => navigateFigure(-1)}><ChevronLeft size={20} /></button>
              <button className="stage-nav right" onClick={() => navigateFigure(1)}><ChevronRight size={20} /></button>
            </div>

            <div className="monitor-footer">
              <div className="figure-meta">
                <span className="figure-counter">{activeFigure ? `${activeFigure.order} / ${catalog.figures.length}` : '—'}</span>
                <div><strong>{activeFigure ? `Figura ${activeFigure.id}` : 'Sin selección'}</strong><small>{activeFigure?.title || 'Selecciona una figura desde el panel lateral'}</small></div>
              </div>
              <div className="monitor-status">
                {run?.figure_statuses?.[activeId]?.status === 'OK' ? <><CheckCircle2 size={15} /><span>Generada correctamente</span></> : processing && run?.current_figure === activeId ? <><LoaderCircle className="spin" size={15} /><span>Procesando…</span></> : <><RefreshCw size={14} /><span>{activeFigure?.has_preview ? 'Imagen existente' : 'Pendiente'}</span></>}
              </div>
            </div>
          </div>

          <div className="progress-strip">
            <div className="progress-copy">
              <span>{isRunning ? 'CORRIDA EN PROGRESO' : run?.status === 'finished' ? 'ÚLTIMA CORRIDA' : 'SECUENCIA DE GENERACIÓN'}</span>
              <strong>{isRunning ? `${run.current_figure || 'Preparando'} · ${Math.round(progress)}%` : run?.status === 'finished' ? `${run.completed}/${run.total} figuras procesadas` : 'Las figuras aparecerán aquí conforme se generen'}</strong>
            </div>
            <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
            <div className="filmstrip">
              {generated.length ? generated.map((figureId, index) => {
                const figure = catalog.figures.find((item) => item.id === figureId)
                if (!figure) return null
                return <button key={figureId} onClick={() => setActiveId(figureId)} className={activeId === figureId ? 'active' : ''}><img src={`${figure.preview_url}?v=${refreshKey}-${index}`} alt={figureId} /><span>{figureId}</span></button>
              }) : <div className="filmstrip-empty"><span /><span /><span /><span /><em>Las miniaturas de la corrida aparecerán en secuencia</em></div>}
            </div>
          </div>
        </section>
      </main>

      {showExport && run?.status === 'finished' && (
        <div className="modal-backdrop" onMouseDown={() => setShowExport(false)}>
          <div className="export-modal" onMouseDown={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowExport(false)}><X size={19} /></button>
            <div className="success-animation"><div className="success-ring ring-1" /><div className="success-ring ring-2" /><div className="success-core"><Check size={34} /></div></div>
            <span className="modal-kicker">PROYECTO TERMINADO</span>
            <h3>Tu corrida está lista</h3>
            <p>Se procesaron <strong>{run.completed}</strong> de <strong>{run.total}</strong> figuras. Elige una opción para descargar el resultado.</p>
            <div className="export-grid">
              {exportOptions.map(({ kind, label, detail, icon: Icon }) => (
                <button key={kind} className="export-card" disabled={downloadKind !== null} onClick={() => downloadExport(kind)}>
                  <span className="export-icon">{downloadKind === kind ? <LoaderCircle className="spin" size={23} /> : <Icon size={23} />}</span>
                  <span><strong>{label}</strong><small>{detail}</small></span>
                  <Download size={17} className="card-download" />
                </button>
              ))}
            </div>
            <div className="modal-note"><Archive size={14} /> PDF y PPTX conservan vectores y texto copiable; los ZIP incluyen manifiesto de origen y posiciones SVG.</div>
          </div>
        </div>
      )}

      {toast && <div className={`toast ${toast.type}`}><span>{toast.type === 'success' ? <CheckCircle2 size={17} /> : toast.type === 'error' ? <X size={17} /> : <Sparkles size={17} />}</span>{toast.message}</div>}
    </div>
  )
}

export default App
