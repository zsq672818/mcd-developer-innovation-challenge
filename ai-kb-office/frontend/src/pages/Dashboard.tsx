import { useEffect, useState } from 'react'
import { Button, Card, Col, Row, Space, Tag, Typography, message } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import {
  getHealth,
  getLlmHealth,
  getReady,
  type HealthResp,
  type LlmHealthResp,
  type ReadyResp,
} from '../api/client'

const { Title, Paragraph } = Typography

function StatusTag({ ok, text }: { ok: boolean; text: string }) {
  return <Tag color={ok ? 'green' : 'red'}>{text}</Tag>
}

export default function Dashboard() {
  const [health, setHealth] = useState<HealthResp | null>(null)
  const [ready, setReady] = useState<ReadyResp | null>(null)
  const [llm, setLlm] = useState<LlmHealthResp | null>(null)
  const [loading, setLoading] = useState(false)

  const refresh = async () => {
    setLoading(true)
    try {
      const [h, r, l] = await Promise.allSettled([getHealth(), getReady(), getLlmHealth()])
      if (h.status === 'fulfilled') setHealth(h.value)
      if (r.status === 'fulfilled') setReady(r.value)
      if (l.status === 'fulfilled') setLlm(l.value)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh().catch(() => message.error('获取服务状态失败'))
  }, [])

  return (
    <>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          综合看板 · 服务状态
        </Title>
        <Button icon={<ReloadOutlined />} loading={loading} onClick={refresh}>
          刷新
        </Button>
      </Space>

      <Row gutter={16}>
        <Col xs={24} md={8}>
          <Card title="后端服务" variant="borderless">
            <Paragraph>
              状态：<StatusTag ok={health?.status === 'ok'} text={health?.status ?? '未知'} />
            </Paragraph>
            <Paragraph type="secondary" style={{ margin: 0 }}>
              {health?.app} · env={health?.env}
            </Paragraph>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="数据库" variant="borderless">
            <Paragraph>
              状态：<StatusTag ok={ready?.database === 'up'} text={ready?.database ?? '未知'} />
            </Paragraph>
            <Paragraph type="secondary" style={{ margin: 0 }}>
              驱动：{ready?.database_url_scheme ?? '—'}
            </Paragraph>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="大模型" variant="borderless">
            <Paragraph>
              状态：<StatusTag ok={!!llm?.ok} text={llm?.ok ? '可达' : '不可达'} />
            </Paragraph>
            <Paragraph type="secondary" style={{ margin: 0 }}>
              provider={llm?.provider ?? '—'}
            </Paragraph>
          </Card>
        </Col>
      </Row>

      {llm && !llm.ok && (
        <Card style={{ marginTop: 16 }} variant="borderless">
          <Paragraph type="secondary" style={{ margin: 0 }}>
            模型提示：{llm.detail}
          </Paragraph>
        </Card>
      )}
    </>
  )
}
