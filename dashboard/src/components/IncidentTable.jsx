function truncate(str, max = 50) {
  if (!str) return '—'
  const s = String(str)
  if (s.length <= max) return s
  return `${s.slice(0, max)}…`
}

function MiniConfidenceBar({ value }) {
  const pct = Math.min(100, Math.max(0, Number(value) * 100))
  return (
    <div className="w-24 h-2 rounded-full bg-gray-200 overflow-hidden shrink-0">
      <div className="h-full rounded-full bg-blue-600 transition-[width]" style={{ width: `${pct}%` }} />
    </div>
  )
}

const SOURCE_BADGE = {
  Audio: 'bg-blue-100 text-blue-800',
  Image: 'bg-green-100 text-green-800',
  Video: 'bg-purple-100 text-purple-800',
  Text: 'bg-orange-100 text-orange-800',
  Document: 'bg-teal-100 text-teal-800',
}

const SEVERITY_BADGE = {
  High: 'bg-red-100 text-red-800',
  Medium: 'bg-yellow-100 text-yellow-800',
  Low: 'bg-green-100 text-green-800',
}

function rowKey(row) {
  if (row.frame_id != null && row.frame_id !== '')
    return `${row.source}-${row.incident_id}-${row.frame_id}`
  if (row.text_id != null && row.text_id !== '')
    return `${row.source}-${row.incident_id}-${row.text_id}`
  if (row.call_id != null && row.call_id !== '')
    return `${row.source}-${row.incident_id}-${row.call_id}`
  if (row.image_id != null && row.image_id !== '')
    return `${row.source}-${row.incident_id}-${row.image_id}`
  return `${row.source}-${row.incident_id}`
}

function locationDetailsCell(row) {
  const loc = row.location || '—'
  const det = truncate(row.details, 50)
  if (loc === 'N/A' || loc === '—') return det
  return `${loc} · ${det}`
}

export default function IncidentTable({ incidents, onSelect }) {
  return (
    <div className="bg-white rounded-xl shadow overflow-hidden my-6">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {[
                'Incident ID',
                'Source',
                'Type',
                'Location / Details',
                'Confidence',
                'Severity',
                'Action',
              ].map((col) => (
                <th
                  key={col}
                  className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-600 whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {incidents.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No incidents match your filters.
                </td>
              </tr>
            ) : (
              incidents.map((row) => (
                <tr key={rowKey(row)} className="hover:bg-gray-50/80">
                  <td className="px-4 py-3 font-medium text-gray-900 whitespace-nowrap">
                    {row.incident_id}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${SOURCE_BADGE[row.source] || 'bg-gray-100 text-gray-800'}`}
                    >
                      {row.source}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-800 max-w-[140px] break-words">{row.type}</td>
                  <td className="px-4 py-3 text-gray-700 max-w-[280px] break-words">
                    {locationDetailsCell(row)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      <MiniConfidenceBar value={row.confidence} />
                      <span className="text-xs text-gray-500">
                        {(Number(row.confidence) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_BADGE[row.severity] || 'bg-gray-100 text-gray-800'}`}
                    >
                      {row.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => onSelect(row)}
                      className="rounded-lg bg-gray-900 text-white text-xs font-medium px-3 py-1.5 hover:bg-gray-800 transition-colors"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
