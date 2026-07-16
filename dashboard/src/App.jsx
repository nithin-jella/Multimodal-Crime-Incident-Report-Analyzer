import { useEffect, useMemo, useState } from 'react'
import { audioResults } from './data/audioResults.js'
import { imageResults } from './data/imageResults.js'
import { textResults } from './data/textResults.js'
import { docResults } from './data/docResults.js'
import { videoResults } from './data/videoResults.js'
import Header from './components/Header.jsx'
import StatsBar from './components/StatsBar.jsx'
import SceneChart from './components/SceneChart.jsx'
import IncidentTable from './components/IncidentTable.jsx'
import IncidentModal from './components/IncidentModal.jsx'

const ITEMS_PER_PAGE = 25

const PREFIX_ORDER = { IMG: 0, INC: 0, AUD: 1, VID: 2, TXT: 3, DOC: 4 }

function sortByIncidentId(rows) {
  return [...rows].sort((a, b) => {
    const ma = String(a.incident_id || '').match(/^([A-Z]+)-(\d+)$/)
    const mb = String(b.incident_id || '').match(/^([A-Z]+)-(\d+)$/)
    const oa = ma ? (PREFIX_ORDER[ma[1]] ?? 50) : 99
    const ob = mb ? (PREFIX_ORDER[mb[1]] ?? 50) : 99
    if (oa !== ob) return oa - ob
    const na = ma ? parseInt(ma[2], 10) : 0
    const nb = mb ? parseInt(mb[2], 10) : 0
    return na - nb
  })
}

function locationFromEntities(entities) {
  if (!entities || typeof entities !== 'string') return 'N/A'
  const m = entities.match(/Locations:\s*([^;]+)/)
  const s = m ? m[1].trim() : ''
  if (!s || s === 'N/A') return 'N/A'
  return s
}

function severityFromConfidence(score) {
  const s = Number(score) || 0
  if (s >= 0.7) return 'High'
  if (s >= 0.3) return 'Medium'
  return 'Low'
}

function textSeverity(t) {
  const neg = String(t.sentiment || '').toUpperCase().includes('NEG')
  const sc = Number(t.sentiment_score) || 0
  if (neg && sc >= 0.7) return 'High'
  if (sc >= 0.7) return 'High'
  if (sc >= 0.3 || neg) return 'Medium'
  return 'Low'
}

function documentConfidence(incidentType) {
  const s = String(incidentType || '').toLowerCase()
  if (/homicide|shooting|weapon|assault|fire|arson/.test(s)) return 0.8
  if (/theft|robbery|burglary|disturbance|traffic|accident/.test(s)) return 0.52
  if (/administrative|training|law enforcement report/.test(s)) return 0.34
  return 0.42
}

function buildSearchText(obj) {
  return JSON.stringify(obj).toLowerCase()
}

function buildMergedIncidents() {
  const audio = audioResults.map((a) => {
    const row = {
      ...a,
      source: 'Audio',
      type: a.extracted_event || 'Unknown',
      location: a.location || 'Unknown',
      confidence: Number(a.urgency_score) || 0,
      severity: severityFromConfidence(a.urgency_score),
      details: a.transcript || '',
    }
    row.searchText = buildSearchText(row)
    return row
  })

  const image = imageResults.map((i) => {
    const row = {
      ...i,
      source: 'Image',
      type: i.scene_type || 'Unknown',
      location: 'N/A',
      confidence: Number(i.confidence_score) || 0,
      severity: severityFromConfidence(i.confidence_score),
      details: `${i.objects_detected ?? ''} | OCR: ${i.text_extracted ?? ''}`,
    }
    row.searchText = buildSearchText(row)
    return row
  })

  const video = videoResults.map((v) => {
    const row = {
      ...v,
      source: 'Video',
      type: v.event_detected || 'Unknown',
      location: `Frame ${v.frame_id ?? ''}`,
      confidence: Number(v.confidence) || 0,
      severity: severityFromConfidence(v.confidence),
      details: `t=${v.timestamp}s | ${v.objects ?? ''}`,
    }
    row.searchText = buildSearchText(row)
    return row
  })

  const text = textResults.map((t) => {
    const loc = locationFromEntities(t.entities)
    const row = {
      ...t,
      source: 'Text',
      type: t.topic || 'Unknown',
      location: loc !== 'N/A' ? loc : 'N/A',
      confidence: Number(t.sentiment_score) || 0,
      severity: textSeverity(t),
      details: t.raw_text || '',
    }
    row.searchText = buildSearchText(row)
    return row
  })

  const documents = docResults.map((t) => {
    const docConf = documentConfidence(t.incident_type)
    const row = {
      ...t,
      source: 'Document',
      type: t.incident_type || 'Unknown',
      location: t.location && String(t.location).trim() && t.location !== 'N/A' ? t.location : 'N/A',
      confidence: docConf,
      severity: severityFromConfidence(docConf),
      details: t.summary || '',
    }
    row.searchText = buildSearchText(row)
    return row
  })

  return sortByIncidentId([...audio, ...image, ...video, ...text, ...documents])
}

function uniqueTypes(rows) {
  const set = new Set(rows.map((r) => String(r.type || '').trim()).filter(Boolean))
  return ['All', ...Array.from(set).sort()]
}

function mostCommonType(rows) {
  if (!rows.length) return '—'
  const map = {}
  rows.forEach((r) => {
    const t = String(r.type || 'Unknown').trim() || 'Unknown'
    map[t] = (map[t] || 0) + 1
  })
  let best = '—'
  let n = 0
  Object.entries(map).forEach(([k, v]) => {
    if (v > n) {
      n = v
      best = k
    }
  })
  return best
}

export default function App() {
  const mergedIncidents = useMemo(() => buildMergedIncidents(), [])

  const [sourceFilter, setSourceFilter] = useState('All')
  const [typeFilter, setTypeFilter] = useState('All')
  const [severityFilter, setSeverityFilter] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)

  const typeOptions = useMemo(() => uniqueTypes(mergedIncidents), [mergedIncidents])

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return mergedIncidents.filter((i) => {
      if (sourceFilter !== 'All' && i.source !== sourceFilter) return false
      if (typeFilter !== 'All' && String(i.type) !== typeFilter) return false
      if (severityFilter !== 'All' && i.severity !== severityFilter) return false
      if (q && !i.searchText.includes(q)) return false
      return true
    })
  }, [mergedIncidents, sourceFilter, typeFilter, severityFilter, searchQuery])

  useEffect(() => {
    setCurrentPage(1)
  }, [sourceFilter, typeFilter, severityFilter, searchQuery])

  const stats = useMemo(() => {
    const total = filtered.length
    const highSeverity = filtered.filter((r) => r.severity === 'High').length
    const mediumSeverity = filtered.filter((r) => r.severity === 'Medium').length
    const lowSeverity = filtered.filter((r) => r.severity === 'Low').length
    return {
      total,
      highSeverity,
      mediumSeverity,
      lowSeverity,
      mostCommonType: mostCommonType(filtered),
    }
  }, [filtered])

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const safePage = Math.min(currentPage, totalPages)
  const startIdx = (safePage - 1) * ITEMS_PER_PAGE
  const paginated = filtered.slice(startIdx, startIdx + ITEMS_PER_PAGE)
  const start = filtered.length === 0 ? 0 : startIdx + 1
  const end = Math.min(startIdx + ITEMS_PER_PAGE, filtered.length)

  return (
    <div className="bg-gray-100 min-h-screen">
      <Header totalIncidents={mergedIncidents.length} />

      <div className="max-w-7xl mx-auto px-4 pb-10">
        <StatsBar stats={stats} />

        <SceneChart rows={filtered} />

        <div className="bg-white rounded-xl shadow p-4 my-6 flex flex-wrap gap-4 items-center">
          <input
            type="search"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="min-w-[200px] flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
          />
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
          >
            <option value="All">All sources</option>
            <option value="Audio">Audio</option>
            <option value="Image">Image</option>
            <option value="Video">Video</option>
            <option value="Text">Text</option>
            <option value="Document">Document</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm min-w-[160px] focus:outline-none focus:ring-2 focus:ring-gray-900"
          >
            {typeOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt === 'All' ? 'All types' : opt}
              </option>
            ))}
          </select>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
          >
            <option value="All">All severities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
          <button
            type="button"
            onClick={() => {
              setSourceFilter('All')
              setTypeFilter('All')
              setSeverityFilter('All')
              setSearchQuery('')
            }}
            className="rounded-lg border border-gray-300 bg-gray-50 px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-100"
          >
            Reset
          </button>
        </div>

        <IncidentTable incidents={paginated} onSelect={setSelectedIncident} />

        <div className="flex flex-wrap justify-between items-center gap-4 mt-4 bg-white rounded-xl shadow p-4">
          <span className="text-sm text-gray-700">
            Showing {start}–{end} of {filtered.length} incidents
          </span>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={safePage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-800 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600 px-2">
              Page {safePage} of {totalPages}
            </span>
            <button
              type="button"
              disabled={safePage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-800 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {selectedIncident && (
        <IncidentModal incident={selectedIncident} onClose={() => setSelectedIncident(null)} />
      )}
    </div>
  )
}
