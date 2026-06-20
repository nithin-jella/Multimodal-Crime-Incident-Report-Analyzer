import { X } from 'lucide-react'
import { sceneBadgeClasses } from '../utils/sceneColors.js'

function isOcrUnavailableMessage(text) {
  return typeof text === 'string' && text.startsWith('OCR unavailable')
}

function ConfidenceBar({ score }) {
  const n = Number(score)
  const pct = Math.min(100, Math.max(0, n * 100))
  const isZero = n === 0

  return (
    <div>
      <div className="h-3 w-full max-w-md rounded-full bg-gray-200 overflow-hidden">
        {!isZero && (
          <div
            className="h-full rounded-full bg-emerald-500"
            style={{ width: `${pct}%` }}
          />
        )}
      </div>
      <p className="text-sm text-gray-600 mt-2">
        {isZero ? 'No detections' : `${pct.toFixed(1)}% confidence`}
      </p>
    </div>
  )
}

export default function IncidentModal({ incident, onClose }) {
  if (!incident) return null
  const isAudio = incident.source === 'Audio'
  const isVideo = incident.source === 'Video'
  const isText = incident.source === 'Text'
  const isDocument = incident.source === 'Document'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="incident-modal-title"
    >
      <button
        type="button"
        className="fixed inset-0 bg-black/50 transition-opacity duration-200"
        onClick={onClose}
        aria-label="Close modal"
      />
      <div className="relative z-10 w-full max-w-lg max-h-[90vh] overflow-y-auto bg-white rounded-xl shadow-xl p-6 animate-modal-in transition-opacity duration-200">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-900 transition-colors"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        <h2
          id="incident-modal-title"
          className="text-2xl font-bold text-gray-900 pr-10"
        >
          {incident.incident_id}
        </h2>
        <p className="text-gray-500 mt-1">
          Source: {incident.source}{' '}
          {isAudio
            ? `• ${incident.call_id}`
            : isVideo
              ? `• ${incident.frame_id}`
              : isDocument
                ? `• ${incident.report_id || incident.incident_id}`
                : isText
                  ? `• ${incident.text_id}`
                  : `• ${incident.image_id}`}
        </p>

        <div className="mt-6 space-y-4">
          {isAudio ? (
            <>
              <h3 className="text-sm font-semibold text-gray-700">Audio analysis</h3>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-gray-500">Transcript</dt>
                  <dd className="text-gray-900 mt-0.5 break-words">{incident.transcript}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Extracted event</dt>
                  <dd className="text-gray-900">{incident.extracted_event}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Location</dt>
                  <dd className="text-gray-900">{incident.location || 'Unknown'}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Sentiment</dt>
                  <dd className="text-gray-900">{incident.sentiment}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 mb-2">Urgency score</dt>
                  <dd>
                    <ConfidenceBar score={incident.urgency_score} />
                  </dd>
                </div>
              </dl>
            </>
          ) : isDocument ? (
            <>
              <h3 className="text-sm font-semibold text-gray-700">Document analysis</h3>
              <dl className="space-y-3 text-sm">
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Incident type</dt>
                  <dd className="text-gray-900">{incident.incident_type || '—'}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Date</dt>
                  <dd className="text-gray-900">{incident.date || '—'}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Location</dt>
                  <dd className="text-gray-900">{incident.location || '—'}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Officer</dt>
                  <dd className="text-gray-900">{incident.officer || '—'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Summary</dt>
                  <dd className="text-gray-900 mt-0.5 break-words whitespace-pre-wrap">
                    {incident.summary || '—'}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Suspect</dt>
                  <dd className="text-gray-900 mt-0.5 break-words">{incident.suspect_description || '—'}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Outcome</dt>
                  <dd className="text-gray-900">{incident.outcome || '—'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 mb-2">Heuristic confidence</dt>
                  <dd>
                    <ConfidenceBar score={incident.confidence} />
                  </dd>
                </div>
              </dl>
            </>
          ) : isText ? (
            <>
              <h3 className="text-sm font-semibold text-gray-700">Text analysis</h3>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-gray-500">Raw text</dt>
                  <dd className="text-gray-900 mt-0.5 break-words whitespace-pre-wrap">
                    {incident.raw_text}
                  </dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Sentiment</dt>
                  <dd className="text-gray-900">{incident.sentiment}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 mb-2">Sentiment score</dt>
                  <dd>
                    <ConfidenceBar score={incident.sentiment_score} />
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Entities</dt>
                  <dd className="text-gray-900 mt-0.5 break-words">{incident.entities}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Topic</dt>
                  <dd className="text-gray-900">{incident.topic}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Source dataset</dt>
                  <dd className="text-gray-900">{incident.source_dataset}</dd>
                </div>
              </dl>
            </>
          ) : isVideo ? (
            <>
              <h3 className="text-sm font-semibold text-gray-700">Video analysis</h3>
              <dl className="space-y-3 text-sm">
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Timestamp</dt>
                  <dd className="text-gray-900">{incident.timestamp}s</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Frame ID</dt>
                  <dd className="text-gray-900">{incident.frame_id}</dd>
                </div>
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Event detected</dt>
                  <dd className="text-gray-900">{incident.event_detected}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Objects</dt>
                  <dd className="text-gray-900 mt-0.5">{incident.objects || 'none'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 mb-2">Confidence</dt>
                  <dd>
                    <ConfidenceBar score={incident.confidence} />
                  </dd>
                </div>
              </dl>
            </>
          ) : (
            <>
              <h3 className="text-sm font-semibold text-gray-700">Image analysis</h3>
              <dl className="space-y-3 text-sm">
                <div className="flex flex-wrap gap-2 justify-between">
                  <dt className="text-gray-500">Scene type</dt>
                  <dd>
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${sceneBadgeClasses(incident.scene_type)}`}
                    >
                      {incident.scene_type}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Objects detected</dt>
                  <dd className="text-gray-900 mt-0.5">
                    {incident.objects_detected === 'none' ? (
                      <span className="text-gray-400 italic">—</span>
                    ) : (
                      incident.objects_detected
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Text extracted</dt>
                  <dd className="mt-0.5 break-words">
                    {isOcrUnavailableMessage(incident.text_extracted) ? (
                      <span className="inline-flex max-w-full items-start rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1 text-sm font-medium italic text-gray-500 break-words">
                        {incident.text_extracted}
                      </span>
                    ) : (
                      <span className="text-gray-900">{incident.text_extracted}</span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 mb-2">Confidence</dt>
                  <dd>
                    <ConfidenceBar score={incident.confidence_score} />
                  </dd>
                </div>
              </dl>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
