import React, { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createDataset } from '../api/client'
import { useAuthStore } from '../store/auth'

const NewDatasetPage: React.FC = () => {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [privateRepo, setPrivateRepo] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const datasetIdPreview = useMemo(() => {
    if (!user?.username || !name.trim()) return ''
    return `${user.username}/${name.trim()}`
  }, [name, user?.username])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!user?.username) return

    setSubmitting(true)
    setError(null)
    try {
      const created = await createDataset({
        dataset_id: `${user.username}/${name.trim()}`,
        name: name.trim(),
        description: description.trim() || undefined,
        tags: tags.trim() || undefined,
        is_private: privateRepo,
      })
      navigate(`/datasets/${encodeURIComponent(created.dataset_id)}`)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create dataset repository'
      setError(message)
      setSubmitting(false)
    }
  }

  return (
    <div className="oa-page">
      <div className="oa-container">
        <div className="oa-create-wrap">
        <Link to="/" style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}>
          ← Back to hub
        </Link>

        <section className="oa-card oa-create-panel">
          {!isAuthenticated ? (
            <p style={{ margin: 0, color: '#b91c1c' }}>
              You must be logged in to create a dataset. If you were logged in before, please sign in again.
            </p>
          ) : (
            <>
              <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 14 }}>
                <div>
                  <h2 style={{ margin: '0 0 6px 0' }}>Create new dataset</h2>
                  <p style={{ margin: 0, color: '#4b5563' }}>Create a dataset repository.</p>
                </div>

                <div className="oa-create-field">
                  <label htmlFor="dataset-name" style={{ fontWeight: 600 }}>Dataset name</label>
                <input
                  className="oa-create-input"
                  id="dataset-name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="my-awesome-dataset"
                  required
                  pattern="^[a-zA-Z0-9._-]+$"
                  title="Use letters, numbers, dot, underscore, or hyphen"
                />
                {datasetIdPreview ? <small style={{ color: '#4b5563' }}>Dataset ID: {datasetIdPreview}</small> : null}
                </div>

                <div className="oa-create-field">
                  <label htmlFor="dataset-desc" style={{ fontWeight: 600 }}>Description</label>
                <textarea
                  className="oa-create-textarea"
                  id="dataset-desc"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  rows={4}
                />
                </div>

                <div className="oa-create-field">
                  <label htmlFor="dataset-tags" style={{ fontWeight: 600 }}>Tags (comma-separated)</label>
                <input
                  className="oa-create-input"
                  id="dataset-tags"
                  value={tags}
                  onChange={(event) => setTags(event.target.value)}
                  placeholder="nlp,classification,benchmark"
                />
                </div>

                <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#374151' }}>
                  <input type="checkbox" checked={privateRepo} onChange={(event) => setPrivateRepo(event.target.checked)} />
                  Private dataset
                </label>

                {error ? <p style={{ margin: 0, color: '#b91c1c' }}>{error}</p> : null}

                <div style={{ display: 'flex', gap: 10 }}>
                  <button type="submit" disabled={submitting || !name.trim()} className="oa-pill-btn oa-pill-btn-primary">
                    {submitting ? 'Creating…' : 'Create dataset'}
                  </button>
                  <button type="button" onClick={() => navigate('/')} className="oa-pill-btn">
                    Cancel
                  </button>
                </div>
              </form>

              <aside className="oa-create-side">
                <h4 style={{ margin: '0 0 8px 0' }}>Repository path</h4>
                <code style={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: 12 }}>
                  {datasetIdPreview || '<your-username>/<dataset-name>'}
                </code>
                <p style={{ margin: '10px 0 0 0', color: '#6b7280', fontSize: 13 }}>
                  Use lowercase names with letters, numbers, `.`, `_`, or `-`.
                </p>
              </aside>
            </>
          )}
        </section>
      </div>
      </div>
    </div>
  )
}

export default NewDatasetPage
