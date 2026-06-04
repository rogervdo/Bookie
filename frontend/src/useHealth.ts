import { useEffect, useState } from 'react'
import { fetchHealth } from './api'

export interface HealthState {
  modelLoaded: boolean
  loading: boolean
  device: string | null
  voices: string[]
  status: string
}

export function useHealth(): HealthState | null {
  const [health, setHealth] = useState<HealthState | null>(null)

  useEffect(() => {
    let active = true

    const poll = async () => {
      try {
        const data = await fetchHealth()
        if (!active) return
        setHealth({
          modelLoaded: data.model_loaded,
          loading: data.loading,
          device: data.device,
          voices: data.voices,
          status: data.status,
        })
        if (data.loading && !data.model_loaded) {
          window.setTimeout(poll, 2000)
        }
      } catch {
        if (!active) return
        setHealth(null)
        window.setTimeout(poll, 3000)
      }
    }

    poll()
    return () => {
      active = false
    }
  }, [])

  return health
}
