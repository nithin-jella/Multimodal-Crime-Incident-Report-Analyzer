export default function Header({ totalIncidents = 0 }) {
  return (
    <header className="w-full bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">🚨 Multimodal Incident Analyzer</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            🎙️ Audio · 🖼️ Images · 🎥 Video · 💬 Text · 📄 Documents
          </p>
        </div>
        <span className="inline-flex items-center rounded-full bg-emerald-700/40 text-emerald-100 text-sm font-medium px-3 py-1.5 border border-emerald-500/50">
          {totalIncidents} Incidents · 5 Modules Active
        </span>
      </div>
    </header>
  )
}
