'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  PlayIcon, 
  StopIcon, 
  DocumentMagnifyingGlassIcon, 
  CpuChipIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ClockIcon,
  ArrowLeftIcon,
  ArrowPathIcon,
  TrashIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

interface GraphRAGStatus {
  graphrag_available: boolean
  api_key_configured: boolean
  index_exists: boolean
  workspace_path: string
  artifact_count?: number
  last_modified?: number
}

interface SearchResult {
  success: boolean
  query: string
  response?: string
  global_search?: any
  local_search?: any
  search_type: string
  error?: string
}

interface KnowledgeItem {
  id: number
  title: string
  content: string
  summary?: string
  source_file?: string
  source_type: string
  created_at: string
}

export default function GraphRAGPage() {
  const router = useRouter()
  const [status, setStatus] = useState<GraphRAGStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [isBuilding, setIsBuilding] = useState(false)
  const [buildProgress, setBuildProgress] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchType, setSearchType] = useState<'global' | 'local' | 'hybrid'>('hybrid')
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([])
  const [selectedKnowledgeIds, setSelectedKnowledgeIds] = useState<number[]>([])
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // 检查认证状态
  useEffect(() => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    setIsAuthenticated(true)
  }, [router])

  // 获取GraphRAG状态
  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/graphrag/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setStatus(data)
      }
    } catch (error) {
      console.error('获取GraphRAG状态失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 获取知识库数据
  const fetchKnowledgeItems = async () => {
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/knowledge/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          source_type: 'document_analysis',
          limit: 50
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setKnowledgeItems(data.knowledge_items || [])
      }
    } catch (error) {
      console.error('获取知识库数据失败:', error)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchStatus()
      fetchKnowledgeItems()
    }
  }, [isAuthenticated])

  // 构建GraphRAG索引
  const buildIndex = async () => {
    if (!status?.api_key_configured) {
      alert('请先配置OpenAI API密钥')
      return
    }

    setIsBuilding(true)
    setBuildProgress('正在启动索引构建...')
    
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/graphrag/build-index', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          knowledge_ids: selectedKnowledgeIds.length > 0 ? selectedKnowledgeIds : null,
          rebuild: true
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setBuildProgress(`索引构建已启动，处理文档: ${data.documents_count}`)
        
        // 定期检查状态
        const checkInterval = setInterval(async () => {
          await fetchStatus()
          setBuildProgress('正在构建知识图谱索引...')
        }, 5000)
        
        // 20分钟后停止检查
        setTimeout(() => {
          clearInterval(checkInterval)
          setIsBuilding(false)
          setBuildProgress('')
          fetchStatus()
        }, 1200000)
        
      } else {
        const error = await response.json()
        alert(`构建失败: ${error.detail}`)
      }
    } catch (error) {
      console.error('构建索引失败:', error)
      alert('构建索引失败，请重试')
    } finally {
      if (!isBuilding) {
        setIsBuilding(false)
        setBuildProgress('')
      }
    }
  }

  // 执行GraphRAG搜索
  const performSearch = async () => {
    if (!searchQuery.trim()) {
      alert('请输入搜索查询')
      return
    }

    setIsSearching(true)
    setSearchResult(null)
    
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/graphrag/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: searchQuery,
          search_type: searchType,
          max_tokens: 2000
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setSearchResult(data)
      } else {
        const error = await response.json()
        setSearchResult({
          success: false,
          query: searchQuery,
          search_type: searchType,
          error: error.detail
        })
      }
    } catch (error) {
      console.error('搜索失败:', error)
      setSearchResult({
        success: false,
        query: searchQuery,
        search_type: searchType,
        error: '搜索请求失败'
      })
    } finally {
      setIsSearching(false)
    }
  }

  // 删除索引
  const deleteIndex = async () => {
    if (!confirm('确定要删除GraphRAG索引吗？此操作不可恢复。')) {
      return
    }

    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/graphrag/index', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        alert('索引已删除')
        fetchStatus()
      } else {
        const error = await response.json()
        alert(`删除失败: ${error.detail}`)
      }
    } catch (error) {
      console.error('删除索引失败:', error)
      alert('删除索引失败，请重试')
    }
  }

  // 处理文档选择
  const handleKnowledgeSelect = (id: number, selected: boolean) => {
    if (selected) {
      setSelectedKnowledgeIds(prev => [...prev, id])
    } else {
      setSelectedKnowledgeIds(prev => prev.filter(item => item !== id))
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/knowledge')}
              className="flex items-center space-x-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
            >
              <ArrowLeftIcon className="h-5 w-5" />
              <span>返回知识库</span>
            </button>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              GraphRAG 知识图谱
            </h1>
          </div>
          <button
            onClick={fetchStatus}
            className="flex items-center space-x-2 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-4 py-2 rounded-lg transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>刷新状态</span>
          </button>
        </div>

        {/* 状态卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CpuChipIcon className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">GraphRAG 可用性</p>
                <p className={`text-lg font-semibold ${status?.graphrag_available ? 'text-green-600' : 'text-red-600'}`}>
                  {status?.graphrag_available ? '可用' : '不可用'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className={`h-8 w-8 ${status?.api_key_configured ? 'text-green-600' : 'text-gray-400'}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">API 密钥</p>
                <p className={`text-lg font-semibold ${status?.api_key_configured ? 'text-green-600' : 'text-red-600'}`}>
                  {status?.api_key_configured ? '已配置' : '未配置'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DocumentMagnifyingGlassIcon className={`h-8 w-8 ${status?.index_exists ? 'text-green-600' : 'text-gray-400'}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">索引状态</p>
                <p className={`text-lg font-semibold ${status?.index_exists ? 'text-green-600' : 'text-red-600'}`}>
                  {status?.index_exists ? '已构建' : '未构建'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <SparklesIcon className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">工件数量</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {status?.artifact_count || 0}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 说明信息 */}
        <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <InformationCircleIcon className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-medium text-blue-900 dark:text-blue-200 mb-2">
                关于 GraphRAG
              </h3>
              <div className="text-blue-800 dark:text-blue-300 space-y-2">
                <p>
                  GraphRAG 是微软开发的基于图的检索增强生成(RAG)系统，通过构建知识图谱来提供更准确和全面的答案。
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>全局搜索：</strong>适合概览性问题，能够整合多个文档的信息</li>
                  <li><strong>本地搜索：</strong>适合具体细节查询，基于实体关系进行精确匹配</li>
                  <li><strong>混合搜索：</strong>结合两种搜索方式的优势，提供最全面的答案</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
