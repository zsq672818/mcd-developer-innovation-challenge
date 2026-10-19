import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { Layout, Menu, Typography } from 'antd'
import {
  AppstoreOutlined,
  CheckSquareOutlined,
  MessageOutlined,
  FolderOpenOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import Dashboard from './pages/Dashboard'

const { Sider, Header, Content } = Layout

const MENU = [
  { key: '/dashboard', icon: <AppstoreOutlined />, label: '综合看板' },
  { key: '/tasks', icon: <CheckSquareOutlined />, label: '任务梳理' },
  { key: '/chat', icon: <MessageOutlined />, label: 'AI 对话' },
  { key: '/documents', icon: <FolderOpenOutlined />, label: '资料库' },
  { key: '/analytics', icon: <BarChartOutlined />, label: '数据分析' },
  { key: '/settings', icon: <SettingOutlined />, label: '设置' },
]

function Placeholder({ title }: { title: string }) {
  return <Typography.Title level={4}>{title}（建设中）</Typography.Title>
}

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0" theme="dark">
        <div
          style={{
            height: 56,
            margin: 16,
            color: '#fff',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            fontSize: 15,
          }}
        >
          AI 知识库办公平台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={MENU}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', paddingInline: 24 }}>
          <Typography.Text strong>{MENU.find((m) => m.key === location.pathname)?.label ?? ''}</Typography.Text>
        </Header>
        <Content style={{ margin: 24 }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/tasks" element={<Placeholder title="任务梳理" />} />
            <Route path="/chat" element={<Placeholder title="AI 对话" />} />
            <Route path="/documents" element={<Placeholder title="资料库" />} />
            <Route path="/analytics" element={<Placeholder title="数据分析" />} />
            <Route path="/settings" element={<Placeholder title="设置" />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}
