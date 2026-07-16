export default function StatsBar({ stats }) {
  const { total, highSeverity, mediumSeverity, lowSeverity, mostCommonType } = stats

  const cards = [
    {
      label: 'Total Incidents',
      value: total,
      borderClass: 'border-l-4 border-gray-400',
      sub: null,
    },
    {
      label: '🔴 High Severity',
      value: highSeverity,
      borderClass: 'border-l-4 border-red-500',
      sub: null,
    },
    {
      label: '🟡 Medium Severity',
      value: mediumSeverity,
      borderClass: 'border-l-4 border-yellow-400',
      sub: null,
    },
    {
      label: '🟢 Low Severity',
      value: lowSeverity,
      borderClass: 'border-l-4 border-green-500',
      sub: null,
    },
    {
      label: 'Most Common Type',
      value: mostCommonType,
      borderClass: 'border-l-4 border-indigo-400',
      sub: 'in current filter',
    },
    {
      label: 'Modules Active',
      value: '5 / 5',
      borderClass: 'border-l-4 border-emerald-500',
      sub: 'Audio, image, video, text, documents',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 my-6">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`bg-white rounded-xl shadow p-4 ${card.borderClass}`}
        >
          <div className="text-2xl font-bold text-gray-900 break-words">{card.value}</div>
          <div className="text-sm text-gray-600 mt-1">{card.label}</div>
          {card.sub && <div className="text-xs text-gray-400 mt-0.5">{card.sub}</div>}
        </div>
      ))}
    </div>
  )
}
