import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const SOURCE_ORDER = ['Audio', 'Image', 'Video', 'Text', 'Document']
const SOURCE_COLORS = {
  Audio: '#3b82f6',
  Image: '#10b981',
  Video: '#a855f7',
  Text: '#f97316',
  Document: '#0d9488',
}

const SEVERITY_ORDER = ['High', 'Medium', 'Low']
const SEVERITY_COLORS = {
  High: '#ef4444',
  Medium: '#eab308',
  Low: '#22c55e',
}

function incidentsBySource(rows) {
  const map = { Audio: 0, Image: 0, Video: 0, Text: 0, Document: 0 }
  rows.forEach((r) => {
    if (map[r.source] !== undefined) map[r.source] += 1
  })
  return SOURCE_ORDER.map((name) => ({
    name,
    count: map[name],
    fill: SOURCE_COLORS[name],
  }))
}

function topTypes(rows, limit = 8) {
  const map = {}
  rows.forEach((r) => {
    const t = String(r.type || 'Unknown').trim() || 'Unknown'
    map[t] = (map[t] || 0) + 1
  })
  return Object.entries(map)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name, count]) => ({ name, count }))
}

function severityDistribution(rows) {
  const map = { High: 0, Medium: 0, Low: 0 }
  rows.forEach((r) => {
    if (map[r.severity] !== undefined) map[r.severity] += 1
  })
  return SEVERITY_ORDER.map((name) => ({
    name,
    count: map[name],
    fill: SEVERITY_COLORS[name],
  }))
}

export default function SceneChart({ rows }) {
  const bySource = incidentsBySource(rows)
  const byType = topTypes(rows, 8)
  const bySeverity = severityDistribution(rows)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 my-6">
      <div className="bg-white rounded-xl shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Incidents by Source</h2>
        <div className="w-full" style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bySource} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" name="Count" radius={[4, 4, 0, 0]}>
                {bySource.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 8 Types</h2>
        <div className="w-full" style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={byType}
              layout="vertical"
              margin={{ top: 8, right: 8, left: 8, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="name"
                width={100}
                tick={{ fontSize: 10 }}
                interval={0}
              />
              <Tooltip />
              <Bar dataKey="count" name="Count" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Severity Distribution</h2>
        <div className="w-full" style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bySeverity} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" name="Count" radius={[4, 4, 0, 0]}>
                {bySeverity.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
