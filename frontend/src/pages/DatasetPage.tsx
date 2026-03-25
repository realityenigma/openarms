import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  fetchDataset,
  fetchDatasetFiles,
  fetchDatasetPreview,
  uploadDatasetFile,
  type Dataset,
  type DatasetFile,
  type DatasetPreview,
} from '../api/client'
import { useAuthStore } from '../store/auth'

const DatasetPage: React.FC = () => {
  const location = useLocation()
  const decodedDatasetId = decodeURIComponent(location.pathname.replace('/datasets/', ''))
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'viewer' | 'card' | 'activity'>('card')
  const [files, setFiles] = useState<DatasetFile[]>([])
  const [selectedFile, setSelectedFile] = useState('')
  const [preview, setPreview] = useState<DatasetPreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)

  useEffect(() => {
    const run = async () => {
      if (!decodedDatasetId) return
      setLoading(true)
      setError(null)
      try {
        const next = await fetchDataset(decodedDatasetId)
        setDataset(next)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load dataset'
        setError(message)
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [decodedDatasetId])

  useEffect(() => {
    const run = async () => {
      if (!decodedDatasetId) return
      try {
        const nextFiles = await fetchDatasetFiles(decodedDatasetId)
        setFiles(nextFiles)
        if (nextFiles.length > 0) {
          setSelectedFile((current) => current || nextFiles[0].filename)
        } else {
          setSelectedFile('')
        }
      } catch {
        setFiles([])
      }
    }
    run()
  }, [decodedDatasetId])

  useEffect(() => {
    const run = async () => {
      if (!decodedDatasetId || !selectedFile || activeTab !== 'viewer') return
      setPreviewLoading(true)
      setPreviewError(null)
      try {
        const nextPreview = await fetchDatasetPreview(decodedDatasetId, selectedFile)
        setPreview(nextPreview)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load dataset preview'
        setPreviewError(message)
        setPreview(null)
      } finally {
        setPreviewLoading(false)
      }
    }
    run()
  }, [decodedDatasetId, selectedFile, activeTab])

  const owner = dataset?.dataset_id.split('/')[0] || ''
  const canUpload = Boolean(isAuthenticated && user?.username === owner)

  const onUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0]
    if (!selected || !dataset) return
    setUploading(true)
    setPreviewError(null)
    try {
      await uploadDatasetFile(dataset.dataset_id, selected)
      const nextFiles = await fetchDatasetFiles(dataset.dataset_id)
      setFiles(nextFiles)
      if (nextFiles.length > 0) {
        setSelectedFile(nextFiles[0].filename)
      }
      setActiveTab('viewer')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      setPreviewError(message)
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  return (
    <div className="oa-page">
      <div className="oa-container" style={{ display: 'grid', gap: 12 }}>
        <Link to="/" style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}>← Back to hub</Link>
        {loading ? <p>Loading dataset…</p> : null}
        {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}
        {dataset ? (
          <section style={{ display: 'grid', gap: 14 }}>
            <section className="oa-card" style={{ padding: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'start', flexWrap: 'wrap' }}>
                <div style={{ display: 'grid', gap: 8 }}>
                  <p style={{ margin: 0, color: '#4b5563', fontSize: 14 }}>Dataset</p>
                  <h2 style={{ margin: 0, fontSize: 28 }}>{dataset.dataset_id}</h2>
                  <p style={{ margin: 0, color: '#374151' }}>{dataset.name}</p>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ border: '1px solid #d1d5db', borderRadius: 999, padding: '4px 10px', fontSize: 12 }}>downloads {dataset.downloads}</span>
                    {dataset.tags?.split(',').map((tag) => tag.trim()).filter(Boolean).map((tag) => (
                      <span key={tag} style={{ border: '1px solid #d1d5db', borderRadius: 999, padding: '4px 10px', fontSize: 12 }}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <aside style={{ minWidth: 250, border: '1px solid #e5e7eb', borderRadius: 10, padding: 12, background: '#fafafa' }}>
                  <h4 style={{ marginTop: 0, marginBottom: 10 }}>Use this dataset</h4>
                  <p style={{ margin: '0 0 10px 0', color: '#4b5563', fontSize: 14 }}>Repository ID</p>
                  <code style={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: 12, background: '#fff', border: '1px solid #e5e7eb', padding: 8, borderRadius: 8 }}>
{dataset.dataset_id}
                  </code>
                  <p style={{ margin: '10px 0 8px 0', color: '#4b5563', fontSize: 14 }}>Python</p>
                  <code style={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: 12, background: '#fff', border: '1px solid #e5e7eb', padding: 8, borderRadius: 8 }}>
{`from datasets import load_dataset\nload_dataset("${dataset.dataset_id}")`}
                  </code>
                  <p style={{ margin: '10px 0 8px 0', color: '#4b5563', fontSize: 14 }}>Updated</p>
                  <code style={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: 12, background: '#fff', border: '1px solid #e5e7eb', padding: 8, borderRadius: 8 }}>
{new Date(dataset.updated_at || dataset.created_at).toLocaleString()}
                  </code>
                  {canUpload ? (
                    <>
                      <p style={{ margin: '10px 0 8px 0', color: '#4b5563', fontSize: 14 }}>Upload file</p>
                      <input type="file" onChange={onUpload} disabled={uploading} />
                    </>
                  ) : null}
                </aside>
              </div>
            </section>

            <section className="oa-card" style={{ overflow: 'hidden' }}>
              <div className="oa-tabs">
                <button
                  type="button"
                  onClick={() => setActiveTab('viewer')}
                  className={`oa-tab ${activeTab === 'viewer' ? 'oa-tab-active' : ''}`}
                >
                  Dataset viewer
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('card')}
                  className={`oa-tab ${activeTab === 'card' ? 'oa-tab-active' : ''}`}
                >
                  Dataset card
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('activity')}
                  className={`oa-tab ${activeTab === 'activity' ? 'oa-tab-active' : ''}`}
                >
                  Activity
                </button>
              </div>

              {activeTab === 'viewer' ? (
                <div style={{ padding: 16 }}>
                  {files.length === 0 ? <p style={{ margin: 0, color: '#6b7280' }}>No dataset files uploaded yet.</p> : null}
                  {files.length > 0 ? (
                    <div style={{ display: 'grid', gap: 12 }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <label htmlFor="dataset-file-select" style={{ fontWeight: 600 }}>File</label>
                        <select
                          id="dataset-file-select"
                          value={selectedFile}
                          onChange={(event) => setSelectedFile(event.target.value)}
                          style={{ padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 8 }}
                        >
                          {files.map((file) => (
                            <option key={file.filename} value={file.filename}>
                              {file.filename}
                            </option>
                          ))}
                        </select>
                      </div>

                      {previewLoading ? <p style={{ margin: 0 }}>Loading preview…</p> : null}
                      {previewError ? <p style={{ margin: 0, color: '#b91c1c' }}>{previewError}</p> : null}
                      {preview ? (
                        <div style={{ overflowX: 'auto' }}>
                          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                            <thead>
                              <tr>
                                {preview.columns.map((column) => (
                                  <th key={column} style={{ textAlign: 'left', borderBottom: '1px solid #e5e7eb', padding: '8px 6px' }}>
                                    {column}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {preview.rows.map((row, index) => (
                                <tr key={`${preview.filename}-${index}`}>
                                  {preview.columns.map((column) => (
                                    <td key={`${index}-${column}`} style={{ borderBottom: '1px solid #f3f4f6', padding: '8px 6px', color: '#374151' }}>
                                      {String((row as Record<string, unknown>)[column] ?? '')}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {preview.truncated ? <p style={{ marginTop: 8, color: '#6b7280' }}>Preview truncated to first 50 rows.</p> : null}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ) : null}

              {activeTab === 'card' ? (
                <div style={{ padding: 16 }}>
                  <h3 style={{ marginTop: 0 }}>About</h3>
                  {dataset.description?.trim() ? (
                    <p style={{ margin: 0, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{dataset.description}</p>
                  ) : (
                    <p style={{ margin: 0, color: '#6b7280' }}>No description has been provided for this dataset.</p>
                  )}
                </div>
              ) : null}

              {activeTab === 'activity' ? (
                <div style={{ padding: 16 }}>
                  <p style={{ margin: 0, color: '#6b7280' }}>No activity has been recorded for this dataset yet.</p>
                </div>
              ) : null}
            </section>
          </section>
        ) : null}
      </div>
    </div>
  )
}

export default DatasetPage
