import React from 'react'
import type { HubModel } from '../api/client'
import ModelFilesPanel from './ModelFilesPanel'
import { useAuthStore } from '../store/auth'

type ModelDetailPanelProps = {
  model: HubModel | null
}

const ModelDetailPanel: React.FC<ModelDetailPanelProps> = ({ model }) => {
  const user = useAuthStore((state) => state.user)
  const [activeTab, setActiveTab] = React.useState<'card' | 'files' | 'activity'>('card')

  if (!model) {
    return (
      <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, background: '#fff' }}>
        <p style={{ margin: 0 }}>Select a model to inspect details and files.</p>
      </section>
    )
  }

  const owner = model.model_id.split('/')[0] || 'unknown'
  const readmeBody = model.description?.trim()
  const canUpload = Boolean(user?.username && user.username === owner)
  const tags = model.tags?.split(',').map((tag) => tag.trim()).filter(Boolean) ?? []
  const updatedAt = model.updated_at ? new Date(model.updated_at).toLocaleString() : new Date(model.created_at).toLocaleString()
  const createdAt = new Date(model.created_at).toLocaleString()

  return (
    <section style={{ display: 'grid', gap: 14 }}>
      <section className="oa-card" style={{ padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'start', flexWrap: 'wrap' }}>
          <div style={{ display: 'grid', gap: 8 }}>
            <p style={{ margin: 0, color: '#4b5563', fontSize: 14 }}>Model</p>
            <h2 style={{ margin: 0, fontSize: 28 }}>{model.model_id}</h2>
            <p style={{ margin: 0, color: '#374151' }}>{model.name}</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ border: '1px solid #d1d5db', borderRadius: 999, padding: '4px 10px', fontSize: 12 }}>downloads {model.downloads}</span>
              {model.model_type ? (
                <span style={{ border: '1px solid #d1d5db', borderRadius: 999, padding: '4px 10px', fontSize: 12 }}>type {model.model_type}</span>
              ) : null}
              <span style={{ border: '1px solid #d1d5db', borderRadius: 999, padding: '4px 10px', fontSize: 12 }}>
                latest {model.latest_revision ? `${model.latest_revision.slice(0, 8)}` : 'none'}
              </span>
              {tags.map((tag) => (
                <span key={tag} style={{ border: '1px solid #d1d5db', borderRadius: 999, padding: '4px 10px', fontSize: 12 }}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
          <aside style={{ minWidth: 250, border: '1px solid #e5e7eb', borderRadius: 10, padding: 12, background: '#fafafa' }}>
            <h4 style={{ marginTop: 0, marginBottom: 10 }}>Use this model</h4>
            <p style={{ margin: '0 0 10px 0', color: '#4b5563', fontSize: 14 }}>Repository ID</p>
            <code style={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: 12, background: '#fff', border: '1px solid #e5e7eb', padding: 8, borderRadius: 8 }}>
{model.model_id}
            </code>
            <p style={{ margin: '10px 0 8px 0', color: '#4b5563', fontSize: 14 }}>Created</p>
            <code style={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: 12, background: '#fff', border: '1px solid #e5e7eb', padding: 8, borderRadius: 8 }}>
{createdAt}
            </code>
            <p style={{ margin: '10px 0 8px 0', color: '#4b5563', fontSize: 14 }}>Updated</p>
            <code style={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: 12, background: '#fff', border: '1px solid #e5e7eb', padding: 8, borderRadius: 8 }}>
{updatedAt}
            </code>
            <p style={{ margin: '10px 0 8px 0', color: '#4b5563', fontSize: 14 }}>Python</p>
            <code style={{ display: 'block', whiteSpace: 'pre-wrap', fontSize: 12, background: '#fff', border: '1px solid #e5e7eb', padding: 8, borderRadius: 8 }}>
{`from huggingface_hub import HfApi\napi = HfApi()\ninfo = api.model_info("${model.model_id}")`}
            </code>
          </aside>
        </div>
      </section>

      <section className="oa-card" style={{ overflow: 'hidden' }}>
        <div className="oa-tabs">
          <button
            type="button"
            onClick={() => setActiveTab('card')}
            className={`oa-tab ${activeTab === 'card' ? 'oa-tab-active' : ''}`}
          >
            Model card
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('files')}
            className={`oa-tab ${activeTab === 'files' ? 'oa-tab-active' : ''}`}
          >
            Files
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('activity')}
            className={`oa-tab ${activeTab === 'activity' ? 'oa-tab-active' : ''}`}
          >
            Activity
          </button>
        </div>
        {activeTab === 'card' ? (
          <div style={{ padding: 16 }}>
            <h3 style={{ marginTop: 0 }}>About</h3>
            {readmeBody ? <p style={{ margin: 0, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{readmeBody}</p> : <p style={{ margin: 0, color: '#6b7280' }}>No description has been provided for this repository.</p>}
          </div>
        ) : null}
        {activeTab === 'files' ? (
          <div style={{ padding: 16 }}>
            <ModelFilesPanel modelId={model.model_id} showUpload={canUpload} />
          </div>
        ) : null}
        {activeTab === 'activity' ? (
          <div style={{ padding: 16 }}>
            <p style={{ margin: 0, color: '#6b7280' }}>No activity has been recorded for this repository yet.</p>
          </div>
        ) : null}
      </section>
    </section>
  )
}

export default ModelDetailPanel
