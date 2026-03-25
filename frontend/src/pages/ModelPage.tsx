import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { fetchModel, type HubModel } from '../api/client'
import ModelDetailPanel from '../components/ModelDetailPanel'

const ModelPage: React.FC = () => {
  const location = useLocation()
  const decodedModelId = decodeURIComponent(location.pathname.replace('/models/', ''))
  const [model, setModel] = useState<HubModel | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const run = async () => {
      if (!decodedModelId) return
      setLoading(true)
      setError(null)
      try {
        const next = await fetchModel(decodedModelId)
        setModel(next)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load model'
        setError(message)
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [decodedModelId])

  return (
    <div className="oa-page">
      <div className="oa-container" style={{ display: 'grid', gap: 12 }}>
        <Link to="/" style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}>← Back to hub</Link>
        {loading ? <p>Loading model…</p> : null}
        {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}
        {!loading && !error ? <ModelDetailPanel model={model} /> : null}
      </div>
    </div>
  )
}

export default ModelPage
