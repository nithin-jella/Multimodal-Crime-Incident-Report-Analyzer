export function sceneFill(sceneType) {
  switch (sceneType) {
    case 'Fire':
      return '#ef4444'
    case 'Accident':
      return '#f59e0b'
    case 'Public Disturbance':
      return '#3b82f6'
    case 'Assault or Theft':
      return '#a855f7'
    default:
      return '#9ca3af'
  }
}

export function sceneBadgeClasses(sceneType) {
  switch (sceneType) {
    case 'Fire':
      return 'bg-red-100 text-red-800 border border-red-200'
    case 'Accident':
      return 'bg-yellow-100 text-yellow-900 border border-yellow-200'
    case 'Public Disturbance':
      return 'bg-blue-100 text-blue-800 border border-blue-200'
    case 'Assault or Theft':
      return 'bg-purple-100 text-purple-800 border border-purple-200'
    default:
      return 'bg-gray-100 text-gray-800 border border-gray-200'
  }
}
