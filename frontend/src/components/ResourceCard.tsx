import React from 'react'

type ResourceCardProps = {
  title: string
  subtitle: string
  description?: string
  tags?: string
  downloads?: number
  onClick?: () => void
  selected?: boolean
  resourceType?: 'model' | 'dataset'
}

const ResourceCard: React.FC<ResourceCardProps> = ({
  title,
  subtitle,
  description,
  tags,
  downloads,
  onClick,
  selected,
  resourceType = 'model',
}) => {
  const tagList = tags?.split(',').map((tag) => tag.trim()).filter(Boolean) ?? []

  return (
    <article
      onClick={onClick}
      style={{
        border: selected ? '2px solid #2563eb' : '1px solid #e5e7eb',
        borderRadius: 10,
        padding: 14,
        background: '#fff',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <div style={{ display: 'grid', gap: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: 12 }}>
          <div style={{ display: 'grid', gap: 4 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>{subtitle}</h3>
            <p style={{ margin: 0, color: '#6b7280', fontSize: 13 }}>{title}</p>
          </div>
          <span className="oa-chip">{resourceType}</span>
        </div>

        {description ? (
          <p
            style={{
              margin: 0,
              color: '#374151',
              fontSize: 14,
              lineHeight: 1.45,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {description}
          </p>
        ) : null}

        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {tagList.slice(0, 3).map((tag) => (
              <span key={tag} className="oa-chip">
                {tag}
              </span>
            ))}
          </div>
          <small style={{ color: '#374151' }}>Downloads {downloads ?? 0}</small>
        </div>
      </div>
    </article>
  )
}

export default ResourceCard
