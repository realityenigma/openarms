import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import ResourceCard from '../components/ResourceCard'
import AuthPanel from '../components/AuthPanel'
import { fetchDatasets, fetchModels, type Dataset, type HubModel } from '../api/client'

const HomePage: React.FC = () => {
  const loadFromStorage = useAuthStore((state) => state.loadFromStorage)
  const [tab, setTab] = useState<'models' | 'datasets'>('models')
  const [query, setQuery] = useState('')
  const [models, setModels] = useState<HubModel[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  useEffect(() => {
    loadFromStorage()
  }, [loadFromStorage])

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const [nextModels, nextDatasets] = await Promise.all([fetchModels(query), fetchDatasets(query)])
        setModels(nextModels)
        setDatasets(nextDatasets)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load resources'
        setError(message)
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [query])

  const activeCount = useMemo(
    () => (tab === 'models' ? models.length : datasets.length),
    [tab, models.length, datasets.length],
  )

  return (
    <div className="oa-page">
      <main className="oa-container" style={{ display: 'grid', gap: 16 }}>
        <section className="oa-card" style={{ padding: 20 }}>
          <h1 style={{ margin: 0, fontSize: 30, fontWeight: 700 }}>The AI community building the future.</h1>
          <p style={{ marginTop: 8, marginBottom: 0, color: '#4b5563', fontSize: 15 }}>
            Discover, create, and share models and datasets with Hugging Face-compatible APIs.
          </p>
        </section>

        {!isAuthenticated ? (
          <section className="oa-card" style={{ padding: 20 }}>
            <AuthPanel />
          </section>
        ) : null}

        <section className="oa-card" style={{ display: 'grid', gap: 0 }}>
          <div style={{ padding: 16, borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => setTab('models')}
              className={`oa-pill-btn ${tab === 'models' ? 'oa-pill-btn-primary' : ''}`}
            >
              Models
            </button>
            <button
              type="button"
              onClick={() => setTab('datasets')}
              className={`oa-pill-btn ${tab === 'datasets' ? 'oa-pill-btn-primary' : ''}`}
            >
              Datasets
            </button>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={`Search ${tab} by name or ID`}
              style={{ marginLeft: 'auto', width: 300, maxWidth: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: 999 }}
            />
          </div>

          <div style={{ padding: 16, display: 'grid', gap: 12 }}>
            <p style={{ margin: 0, color: '#4b5563' }}>
              Showing {activeCount} {tab}
            </p>
            {loading ? <p style={{ margin: 0 }}>Loading…</p> : null}
            {error ? <p style={{ margin: 0, color: '#b91c1c' }}>{error}</p> : null}
            <section style={{ display: 'grid', gap: 10 }}>
            {tab === 'models'
              ? models.map((model) => (
                  <Link key={model.id} to={`/models/${encodeURIComponent(model.model_id)}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    <ResourceCard
                      title={model.name}
                      subtitle={model.model_id}
                      description={model.description}
                      tags={model.tags}
                      downloads={model.downloads}
                      resourceType="model"
                    />
                  </Link>
                ))
              : datasets.map((dataset) => (
                  <Link key={dataset.id} to={`/datasets/${encodeURIComponent(dataset.dataset_id)}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    <ResourceCard
                      title={dataset.name}
                      subtitle={dataset.dataset_id}
                      description={dataset.description}
                      tags={dataset.tags}
                      downloads={dataset.downloads}
                      resourceType="dataset"
                    />
                  </Link>
                ))}
            </section>
          </div>
        </section>
      </main>
    </div>
  )
}

export default HomePage
