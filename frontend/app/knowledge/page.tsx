'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, BookOpen, MessageSquare, ThumbsUp, ThumbsDown, RefreshCw, Search, Tag, Clock, User } from 'lucide-react'

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
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 获取当前用户信息
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        // 检查localStorage和sessionStorage中的token
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        const userData = localStorage.getItem('user') || sessionStorage.getItem('user')
        
        if (!token || !userData) {
          setIsAuthenticated(false)
          setAuthLoading(false)
          return
        }

        const response = await fetch('http://localhost:8081/api/auth/verify', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const verifyData = await response.json()
          if (verifyData.valid) {
            setCurrentUser(JSON.parse(userData))
            setIsAuthenticated(true)
          } else {
            setIsAuthenticated(false)
          }
        } else {
          setIsAuthenticated(false)
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        setIsAuthenticated(false)
      } finally {
        setAuthLoading(false)
      }
    }

    fetchCurrentUser()
  }, [])

  // 获取知识库统计
  useEffect(() => {
    const fetchStats = async () => {
      if (!isAuthenticated) return
      
      try {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        if (!token) return

        const response = await fetch('http://localhost:8081/api/knowledge/stats', {
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

        const response = await fetch('http://localhost:8081/api/knowledge/preset-questions', {
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
        const response = await fetch('http://localhost:8081/api/knowledge/search', {
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
        limit: 10
      }
      
      // 只有当查询不为空时才添加查询字段
      if (query && query.trim()) {
        requestBody.query = query.trim()
      } else {
        // 如果没有查询，显示文档分析类型的知识
        requestBody.source_type = 'document_analysis'
      }

      const response = await fetch('http://localhost:8081/api/knowledge/search', {
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

  // 提问
  const askQuestion = async (question: string) => {
    if (!question.trim() || isLoading) return

    if (!isAuthenticated) {
      alert('请先登录后使用知识库功能')
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      if (!token) {
        alert('请先登录')
        setIsLoading(false)
        return
      }

      const response = await fetch('http://localhost:8081/api/knowledge/ask', {
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

      if (response.ok) {
        const result = await response.json()
        
        // 添加到对话历史
        const newQA: QARecord = {
          id: result.id,
          question: result.question,
          answer: result.answer,
          knowledge_id: result.knowledge_id,
          response_time: result.response_time,
          created_at: new Date().toISOString()
        }
        
        setQaHistory(prev => [...prev, newQA])
        setCurrentQuestion('')
        
        // 滚动到底部
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }, 100)
      } else {
        const error = await response.json()
        alert(`提问失败: ${error.detail}`)
      }
    } catch (error) {
      console.error('提问失败:', error)
      alert('提问失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  // 点击预设问题
  const handlePresetQuestion = async (question: PresetQuestion) => {
    try {
      const token = localStorage.getItem('token') || sessionStorage.getItem('guestToken')
      if (token) {
        // 记录点击
        await fetch(`http://localhost:8081/api/knowledge/preset-questions/${question.id}/click`, {
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

  // 搜索输入处理
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      searchKnowledge(searchQuery)
    }, 500)

    return () => clearTimeout(debounceTimer)
  }, [searchQuery, isAuthenticated])

  // 如果正在检查认证状态，显示加载界面
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">企业知识库问答</h1>
          <p className="text-gray-600">正在验证登录状态...</p>
        </div>
      </div>
    )
  }

  // 如果用户未登录，显示登录提示
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <BookOpen className="h-16 w-16 text-blue-600 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-4">企业知识库问答</h1>
          <p className="text-gray-600 mb-6">
            知识库功能仅对注册用户开放，请先登录后使用。
          </p>
          <div className="space-y-3">
            <button
              onClick={() => window.location.href = '/login?redirect=/knowledge'}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
            >
              用户登录
            </button>
            <button
              onClick={() => window.location.href = '/register'}
              className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors"
            >
              注册账户
            </button>
            <button
              onClick={() => window.location.href = '/'}
              className="w-full text-blue-600 py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors"
            >
              返回首页
            </button>
          </div>
        </div>
      </div>
    )
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
                          <div 
                            className="cursor-pointer"
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
                  <button
                    onClick={() => setQaHistory([])}
                    className="text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
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
                              <p className="text-gray-800 whitespace-pre-wrap">{qa.answer}</p>
                            </div>
                            <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-200">
                              <div className="flex items-center space-x-2 text-xs text-gray-500">
                                {qa.response_time && (
                                  <span>响应时间: {qa.response_time}ms</span>
                                )}
                                <span>{new Date(qa.created_at).toLocaleTimeString()}</span>
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
                    disabled={!currentQuestion.trim() || isLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                  >
                    {isLoading ? (
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