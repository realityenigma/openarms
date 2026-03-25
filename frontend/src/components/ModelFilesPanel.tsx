import React, { useEffect, useState } from 'react'
import { fetchModelFiles, uploadModelFile, type ModelFile } from '../api/client'
import AuthGate from './AuthGate'

type ModelFilesPanelProps = {
  modelId: string
  showUpload?: boolean
}

const formatBytes = (value?: number): string => {
  const bytes = value ?? 0
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const ModelFilesPanel: React.FC<ModelFilesPanelProps> = ({ modelId, showUpload = true }) => {
  const [files, setFiles] = useState<ModelFile[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const next = await fetchModelFiles(modelId)
      setFiles(next)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load files'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFiles()
  }, [modelId])

  const onUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0]
    if (!selected) return

    setUploading(true)
    setError(null)
    try {
      await uploadModelFile(modelId, selected)
      await loadFiles()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      setError(message)
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  return (
    <section style={{ border: '1px solid #e5e7eb', borderRadius: 10, padding: 0, background: '#fff', overflow: 'hidden' }}>
      <div style={{ padding: '14px 16px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0 }}>Files and versions</h4>
        {showUpload ? (
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <AuthGate>
              <input type="file" onChange={onUpload} disabled={uploading} />
              {uploading ? <small>Uploading…</small> : null}
            </AuthGate>
          </div>
        ) : null}
      </div>

      <div style={{ padding: 16 }}>
        {loading ? <p>Loading files…</p> : null}
        {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

        {!loading && files.length === 0 ? <p style={{ marginBottom: 0, color: '#6b7280' }}>No files yet.</p> : null}

        {files.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#4b5563' }}>
                <th style={{ borderBottom: '1px solid #e5e7eb', padding: '8px 6px' }}>File</th>
                <th style={{ borderBottom: '1px solid #e5e7eb', padding: '8px 6px' }}>Size</th>
                <th style={{ borderBottom: '1px solid #e5e7eb', padding: '8px 6px' }}>Updated</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr key={`${file.filename}-${file.created_at}`}>
                  <td style={{ borderBottom: '1px solid #f3f4f6', padding: '10px 6px' }}>
                    <a
                      href={`/api/v1/models/file?model_id=${encodeURIComponent(modelId)}&filename=${encodeURIComponent(file.filename)}`}
                      style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 500 }}
                    >
                      {file.filename}
                    </a>
                  </td>
                  <td style={{ borderBottom: '1px solid #f3f4f6', padding: '10px 6px', color: '#374151' }}>{formatBytes(file.file_size)}</td>
                  <td style={{ borderBottom: '1px solid #f3f4f6', padding: '10px 6px', color: '#374151' }}>
                    {new Date(file.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>
    </section>
  )
}

export default ModelFilesPanel
