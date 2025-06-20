'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Send, BookOpen, MessageSquare, ThumbsUp, ThumbsDown, RefreshCw, Search, Tag, Clock, User, Trash2, Download, FileDown } from 'lucide-react'

interface KnowledgeItem {
  id: number
  title: string
  content: string
  summary?: string
  source_file?: string
  source_type: string
  tags?: string
  view_count: number
  created_at: string
  updated_at?: string
  created_by: number
  is_active: boolean
}

interface PresetQuestion {
  id: number
  question: string
  category?: string
  click_count: number
}

interface QARecord {
  id: number
  question: string
  answer: string
  knowledge_id?: number
  response_time?: number
  created_at: string
}

interface KnowledgeStats {
  total_knowledge: number
  total_qa: number
  active_knowledge: number
  popular_tags: string[]
  recent_questions: string[]
}

export default function KnowledgePage() {
  const router = useRouter()
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([])
  const [presetQuestions, setPresetQuestions] = useState<PresetQuestion[]>([])
  const [qaHistory, setQaHistory] = useState<QARecord[]>([])
  const [stats, setStats] = useState<KnowledgeStats | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedKnowledge, setSelectedKnowledge] = useState<KnowledgeItem | null>(null)
  const [currentUser, setCurrentUser] = useState<any>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authLoading, setAuthLoading] = useState(true)
  const [sessionId, setSessionId] = useState<string>('')
  
  // 新增状态
  const [selectedDocuments, setSelectedDocuments] = useState<Set<number>>(new Set())
  const [showDocumentDetail, setShowDocumentDetail] = useState(false)
  const [detailDocument, setDetailDocument] = useState<KnowledgeItem | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [streamingAnswer, setStreamingAnswer] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 检查认证状态并处理游客跳转
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        // 检查localStorage和sessionStorage中的token
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        const userData = localStorage.getItem('user') || sessionStorage.getItem('user')
        
        // 检查是否是游客用户
        const guestToken = sessionStorage.getItem('guestToken')
        const isGuest = guestToken && !token
        
        if (!token || !userData || isGuest) {
          // 游客用户或未登录用户自动跳转到登录页面
          setAuthLoading(false)
          router.push('/login')
          return
        }

        const response = await fetch('http://localhost:8000/api/auth/verify', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const verifyData = await response.json()
          if (verifyData.valid) {
            const user = JSON.parse(userData)
            // 检查是否是游客用户
            if (user.is_guest === true) {
              router.push('/login')
              return
            }
            setCurrentUser(user)
            setIsAuthenticated(true)
          } else {
            // Token无效，跳转到登录页面
            router.push('/login')
            return
          }
        } else {
          // 验证失败，跳转到登录页面
          router.push('/login')
          return
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 出错时也跳转到登录页面
        router.push('/login')
        return
      } finally {
        setAuthLoading(false)
      }
    }

    fetchCurrentUser()
  }, [router])

  // 获取知识库统计
  useEffect(() => {
    const fetchStats = async () => {
      if (!isAuthenticated) return
      
      try {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        if (!token) return

        const response = await fetch('http://localhost:8000/api/knowledge/stats', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const statsData = await response.json()
          setStats(statsData)
        }
      } catch (error) {
        console.error('获取统计信息失败:', error)
      }
    }

    fetchStats()
  }, [isAuthenticated])

  // 获取预设问题
  useEffect(() => {
    const fetchPresetQuestions = async () => {
      if (!isAuthenticated) return
      
      try {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        if (!token) return

        const response = await fetch('http://localhost:8000/api/knowledge/preset-questions', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const questions = await response.json()
          setPresetQuestions(questions)
        }
      } catch (error) {
        console.error('获取预设问题失败:', error)
      }
    }

    fetchPresetQuestions()
  }, [isAuthenticated])

  // 获取用户上传的文档（自动显示最近上传的文档）
  useEffect(() => {
    const fetchRecentDocuments = async () => {
      if (!isAuthenticated) return
      
      try {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        if (!token) return

        // 搜索最近的文档分析结果
        const response = await fetch('http://localhost:8000/api/knowledge/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            source_type: 'document_analysis',
            limit: 10
          })
        })

        if (response.ok) {
          const result = await response.json()
          setKnowledgeItems(result.knowledge_items || [])
        }
      } catch (error) {
        console.error('获取文档失败:', error)
      }
    }

    fetchRecentDocuments()
  }, [isAuthenticated])

  // 搜索知识库
  const searchKnowledge = async (query: string) => {
    if (!isAuthenticated) {
      alert('请先登录后使用知识库功能')
      return
    }

    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      if (!token) return

      // 构建请求体
      const requestBody: any = {
        limit: 10,
        include_inactive: false  // 只显示活跃的文档
      }
      
      // 只有当查询不为空时才添加查询字段
      if (query && query.trim()) {
        requestBody.query = query.trim()
      } else {
        // 如果没有查询，显示文档分析类型的知识
        requestBody.source_type = 'document_analysis'
      }

      const response = await fetch('http://localhost:8000/api/knowledge/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const result = await response.json()
        setKnowledgeItems(result.knowledge_items || [])
      }
    } catch (error) {
      console.error('搜索失败:', error)
    }
  }

  // 流式提问
  const askQuestion = async (question: string) => {
    if (!question.trim() || isLoading || isStreaming) return

    if (!isAuthenticated) {
      alert('请先登录后使用知识库功能')
      return
    }

    setIsLoading(true)
    setIsStreaming(true)
    setStreamingAnswer('')
    
    // 先将问题添加到历史
    const questionRecord: QARecord = {
      id: Date.now(),
      question: question,
      answer: '',
      created_at: new Date().toISOString()
    }
    
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      if (!token) {
        alert('请先登录')
        setIsLoading(false)
        setIsStreaming(false)
        return
      }
      
      setQaHistory(prev => [...prev, questionRecord])
      setCurrentQuestion('')

      // 创建EventSource进行流式请求
      const response = await fetch('http://localhost:8000/api/knowledge/ask-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          question: question,
          knowledge_ids: Array.from(selectedDocuments)
        })
      })

      if (!response.ok) {
        throw new Error('请求失败')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法获取响应流')
      }

      let fullAnswer = ''
      
      try {
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            break
          }
          
          const chunk = new TextDecoder().decode(value)
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              
              if (data.trim()) {
                try {
                  const parsed = JSON.parse(data)
                  
                  if (parsed.type === 'content') {
                    fullAnswer += parsed.data
                    setStreamingAnswer(fullAnswer)
                  } else if (parsed.type === 'done') {
                    // 流式输出完成，更新最后的记录
                    setQaHistory(prev => 
                      prev.map(qa => 
                        qa.id === questionRecord.id 
                          ? { ...qa, answer: fullAnswer, response_time: Date.now() - qa.id }
                          : qa
                      )
                    )
                    setStreamingAnswer('')
                  } else if (parsed.type === 'error') {
                    throw new Error(parsed.data)
                  }
                } catch (parseError) {
                  console.error('解析响应失败:', parseError)
                }
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
      
      // 滚动到底部
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
      
    } catch (error) {
      console.error('提问失败:', error)
      alert('提问失败，请重试')
      
      // 移除失败的问题记录
      setQaHistory(prev => prev.filter(qa => qa.id !== questionRecord.id))
      setStreamingAnswer('')
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
    }
  }

  // 点击预设问题
  const handlePresetQuestion = async (question: PresetQuestion) => {
    try {
      const token = localStorage.getItem('token') || sessionStorage.getItem('guestToken')
      if (token) {
        // 记录点击
        await fetch(`http://localhost:8000/api/knowledge/preset-questions/${question.id}/click`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      }
      
      // 执行提问
      await askQuestion(question.question)
    } catch (error) {
      console.error('处理预设问题失败:', error)
    }
  }

  // 处理文档选择
  const handleDocumentSelect = (documentId: number, checked: boolean) => {
    const newSelected = new Set(selectedDocuments)
    if (checked) {
      newSelected.add(documentId)
    } else {
      newSelected.delete(documentId)
    }
    setSelectedDocuments(newSelected)
  }

  // 查看文档详情
  const handleViewDocumentDetail = (document: KnowledgeItem) => {
    setDetailDocument(document)
    setShowDocumentDetail(true)
  }

  // 关闭文档详情
  const handleCloseDocumentDetail = () => {
    setShowDocumentDetail(false)
    setDetailDocument(null)
  }

  // 删除文档
  const handleDeleteDocument = async (documentId: number) => {
    if (!confirm('确定要删除这个文档吗？此操作不可恢复。')) {
      return
    }

    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      if (!token) {
        alert('请先登录')
        return
      }

      const response = await fetch(`http://localhost:8000/api/knowledge/items/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        // 从列表中移除文档
        setKnowledgeItems(prev => prev.filter(item => item.id !== documentId))
        // 从选择中移除
        setSelectedDocuments(prev => {
          const newSet = new Set(prev)
          newSet.delete(documentId)
          return newSet
        })
        alert('文档删除成功')
      } else {
        const error = await response.json()
        alert(`删除失败: ${error.detail}`)
      }
    } catch (error) {
      console.error('删除文档失败:', error)
      alert('删除失败，请重试')
    }
  }

  // 导出选中文档
  const handleExportDocuments = async () => {
    if (selectedDocuments.size === 0) {
      alert('请先选择要导出的文档')
      return
    }

    setIsExporting(true)
    
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      if (!token) {
        alert('请先登录')
        setIsExporting(false)
        return
      }

      const response = await fetch('http://localhost:8000/api/knowledge/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(Array.from(selectedDocuments))
      })

      if (response.ok) {
        // 获取文件名
        const contentDisposition = response.headers.get('Content-Disposition')
        let filename = '文档分析合集.zip'
        if (contentDisposition) {
          const matches = contentDisposition.match(/filename=([^;]+)/)
          if (matches) {
            filename = matches[1]
          }
        }

        // 下载文件
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        alert('文档导出成功')
      } else {
        const error = await response.json()
        alert(`导出失败: ${error.detail}`)
      }
    } catch (error) {
      console.error('导出文档失败:', error)
      alert('导出失败，请重试')
    } finally {
      setIsExporting(false)
    }
  }

  // 搜索输入处理
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      searchKnowledge(searchQuery)
    }, 500)

    return () => clearTimeout(debounceTimer)
  }, [searchQuery, isAuthenticated])

  // 如果正在加载认证状态，显示加载页面
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">正在验证用户身份...</p>
        </div>
      </div>
    )
  }

  // 如果未认证，不渲染任何内容（因为会被重定向）
  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <BookOpen className="h-8 w-8 text-blue-600" />
              <h1 className="text-xl font-semibold text-gray-900">企业知识库问答</h1>
            </div>
            <div className="flex items-center space-x-4">
              {currentUser && (
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <User className="h-4 w-4" />
                  <span>{currentUser.username}</span>
                </div>
              )}
              {stats && (
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>知识: {stats.total_knowledge}</span>
                  <span>问答: {stats.total_qa}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 左侧知识库区域 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 知识搜索 */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Search className="h-5 w-5 mr-2 text-blue-600" />
                知识搜索
              </h3>
              <div className="relative">
                <input
                  type="text"
                  placeholder="搜索知识库..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              </div>
            </div>

            {/* 知识来源 */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <BookOpen className="h-5 w-5 mr-2 text-blue-600" />
                  来源指南
                </h3>
                <button
                  onClick={() => window.location.reload()}
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                  title="刷新文档列表"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>
              
              {knowledgeItems.length > 0 ? (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {knowledgeItems.map((item) => (
                    <div
                      key={item.id}
                      className={`p-3 rounded-lg border transition-colors ${
                        selectedDocuments.has(item.id)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        {/* 选择框 */}
                        <input
                          type="checkbox"
                          checked={selectedDocuments.has(item.id)}
                          onChange={(e) => handleDocumentSelect(item.id, e.target.checked)}
                          className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        
                        {/* 文档内容 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div 
                              className="cursor-pointer flex-1"
                              onClick={() => handleViewDocumentDetail(item)}
                            >
                              <h4 className="font-medium text-gray-900 text-sm mb-1 hover:text-blue-600 transition-colors">
                                {item.title}
                              </h4>
                              {item.summary && (
                                <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                                  {item.summary}
                                </p>
                              )}
                            </div>
                            
                            {/* 删除按钮 */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteDocument(item.id)
                              }}
                              className="ml-2 p-1 text-gray-400 hover:text-red-600 transition-colors"
                              title="删除文档"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                          
                          <div className="flex items-center justify-between text-xs text-gray-500">
                            <div className="flex items-center space-x-2">
                              {item.tags && (
                                <div className="flex items-center">
                                  <Tag className="h-3 w-3 mr-1" />
                                  <span>{item.tags.split(',').slice(0, 2).join(', ')}</span>
                                </div>
                              )}
                            </div>
                            <div className="flex items-center space-x-2">
                              <div className="flex items-center">
                                <Clock className="h-3 w-3 mr-1" />
                                <span>{item.view_count} 次查看</span>
                              </div>
                              {item.source_file && (
                                <div className="flex items-center">
                                  <span className="text-blue-500">📄 {item.source_file}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="text-xs text-gray-400 mt-1">
                            上传时间: {new Date(item.created_at).toLocaleString('zh-CN')}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <BookOpen className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">搜索关键词查看相关知识</p>
                </div>
              )}
            </div>

            {/* 热门标签 */}
            {stats?.popular_tags && stats.popular_tags.length > 0 && (
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <Tag className="h-5 w-5 mr-2 text-blue-600" />
                  热门标签
                </h3>
                <div className="flex flex-wrap gap-2">
                  {stats.popular_tags.map((tag, index) => (
                    <button
                      key={index}
                      onClick={() => setSearchQuery(tag)}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors"
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 右侧对话区域 */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow h-[calc(100vh-12rem)] flex flex-col">
              {/* 对话头部 */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900 flex items-center">
                    <MessageSquare className="h-5 w-5 mr-2 text-blue-600" />
                    智能问答
                  </h2>
                  <div className="flex items-center space-x-2">
                    {/* 导出按钮 */}
                    {selectedDocuments.size > 0 && (
                      <button
                        onClick={handleExportDocuments}
                        disabled={isExporting}
                        className="flex items-center px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        title="导出选中文档"
                      >
                        {isExporting ? (
                          <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                        ) : (
                          <Download className="h-3 w-3 mr-1" />
                        )}
                        导出({selectedDocuments.size})
                      </button>
                    )}
                    
                    <button
                      onClick={() => setQaHistory([])}
                      className="text-gray-500 hover:text-gray-700 transition-colors"
                      title="清空对话"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                {/* 选中的文档显示 */}
                {selectedDocuments.size > 0 && (
                  <div className="mt-3 p-2 bg-blue-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-blue-700 font-medium">
                        已选择 {selectedDocuments.size} 个文档作为上下文
                      </span>
                      <button
                        onClick={() => setSelectedDocuments(new Set())}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        清空选择
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {knowledgeItems
                        .filter(item => selectedDocuments.has(item.id))
                        .map(item => (
                          <span 
                            key={item.id}
                            className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                          >
                            {item.title.length > 20 ? item.title.substring(0, 20) + '...' : item.title}
                            <button
                              onClick={() => handleDocumentSelect(item.id, false)}
                              className="ml-1 text-blue-600 hover:text-blue-800"
                            >
                              ×
                            </button>
                          </span>
                        ))
                      }
                    </div>
                  </div>
                )}
              </div>

              {/* 对话内容 */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {qaHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <MessageSquare className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">开始您的智能问答</h3>
                    <p className="text-gray-600 mb-6">基于企业知识库，为您提供准确的答案</p>
                    
                    {/* 预设问题 */}
                    {presetQuestions.length > 0 && (
                      <div className="max-w-2xl mx-auto">
                        <h4 className="text-sm font-medium text-gray-700 mb-3">热门问题</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {presetQuestions.slice(0, 6).map((question) => (
                            <button
                              key={question.id}
                              onClick={() => handlePresetQuestion(question)}
                              className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors"
                            >
                              <p className="text-sm text-gray-700">{question.question}</p>
                              {question.category && (
                                <span className="inline-block mt-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                                  {question.category}
                                </span>
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                    {qaHistory.map((qa, index) => (
                      <div key={qa.id || index} className="space-y-4">
                        {/* 用户问题 */}
                        <div className="flex justify-end">
                          <div className="max-w-3xl bg-blue-600 text-white rounded-lg px-4 py-2">
                            <p className="text-sm">{qa.question}</p>
                          </div>
                        </div>
                        
                        {/* AI回答 */}
                        <div className="flex justify-start">
                          <div className="max-w-3xl bg-gray-100 rounded-lg px-4 py-3">
                            <div className="prose prose-sm max-w-none">
                              <p className="text-gray-800 whitespace-pre-wrap">
                                {qa.answer || (qa.id === qaHistory[qaHistory.length - 1]?.id && isStreaming ? streamingAnswer : '')}
                                {qa.id === qaHistory[qaHistory.length - 1]?.id && isStreaming && (
                                  <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1"></span>
                                )}
                              </p>
                            </div>
                            <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-200">
                              <div className="flex items-center space-x-2 text-xs text-gray-500">
                                {qa.response_time && (
                                  <span>响应时间: {qa.response_time}ms</span>
                                )}
                                <span>{new Date(qa.created_at).toLocaleTimeString()}</span>
                                {qa.id === qaHistory[qaHistory.length - 1]?.id && isStreaming && (
                                  <span className="text-blue-600">正在思考中...</span>
                                )}
                              </div>
                              <div className="flex items-center space-x-2">
                                <button className="text-gray-400 hover:text-green-600 transition-colors">
                                  <ThumbsUp className="h-4 w-4" />
                                </button>
                                <button className="text-gray-400 hover:text-red-600 transition-colors">
                                  <ThumbsDown className="h-4 w-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* 输入区域 */}
              <div className="p-4 border-t border-gray-200">
                <div className="flex space-x-3">
                  <div className="flex-1">
                    <textarea
                      value={currentQuestion}
                      onChange={(e) => setCurrentQuestion(e.target.value)}
                      placeholder="请输入您的问题..."
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          askQuestion(currentQuestion)
                        }
                      }}
                    />
                  </div>
                  <button
                    onClick={() => askQuestion(currentQuestion)}
                    disabled={!currentQuestion.trim() || isLoading || isStreaming}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                  >
                    {isLoading || isStreaming ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  按 Enter 发送，Shift + Enter 换行
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* 文档详情弹窗 */}
      {showDocumentDetail && detailDocument && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            {/* 背景遮罩 */}
            <div 
              className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
              onClick={handleCloseDocumentDetail}
            ></div>

            {/* 弹窗内容 */}
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              {/* 头部 */}
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    文档详情
                  </h3>
                  <button
                    onClick={handleCloseDocumentDetail}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <span className="sr-only">关闭</span>
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* 文档信息 */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">文档标题</label>
                    <p className="text-base text-gray-900">{detailDocument.title}</p>
                  </div>

                  {detailDocument.source_file && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">源文件</label>
                      <p className="text-sm text-gray-600">{detailDocument.source_file}</p>
                    </div>
                  )}

                  {detailDocument.summary && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">摘要</label>
                      <p className="text-sm text-gray-600">{detailDocument.summary}</p>
                    </div>
                  )}

                  {detailDocument.tags && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">标签</label>
                      <div className="flex flex-wrap gap-2">
                        {detailDocument.tags.split(',').map((tag, index) => (
                          <span 
                            key={index}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {tag.trim()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">查看次数</label>
                      <p className="text-sm text-gray-600">{detailDocument.view_count} 次</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">上传时间</label>
                      <p className="text-sm text-gray-600">
                        {new Date(detailDocument.created_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">文档内容</label>
                    <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                        {detailDocument.content}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>

              {/* 底部按钮 */}
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => {
                    handleDocumentSelect(detailDocument.id, !selectedDocuments.has(detailDocument.id))
                    handleCloseDocumentDetail()
                  }}
                  className={`w-full inline-flex justify-center rounded-md border px-4 py-2 text-base font-medium shadow-sm sm:ml-3 sm:w-auto sm:text-sm ${
                    selectedDocuments.has(detailDocument.id)
                      ? 'border-red-300 bg-red-600 text-white hover:bg-red-700'
                      : 'border-blue-300 bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {selectedDocuments.has(detailDocument.id) ? '取消选择' : '选择为上下文'}
                </button>
                
                <button
                  type="button"
                  onClick={() => {
                    handleDeleteDocument(detailDocument.id)
                    handleCloseDocumentDetail()
                  }}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-red-300 bg-red-600 text-white px-4 py-2 text-base font-medium shadow-sm hover:bg-red-700 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  删除文档
                </button>
                
                <button
                  type="button"
                  onClick={handleCloseDocumentDetail}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 