'use client'

import { useState, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { DocumentArrowUpIcon, CloudArrowUpIcon, DocumentTextIcon, ClockIcon, UserIcon, ArrowRightOnRectangleIcon, BookOpenIcon } from '@heroicons/react/24/outline'
import { CheckCircleIcon } from '@heroicons/react/24/solid'
import axios from 'axios'

interface AnalysisResult {
  status: string
  message: string
  analysis?: string
  xml_analysis?: string
  xml_file?: string
  download_url?: string
  processed_files?: string[]
  filename?: string
  size?: number
  total_files?: number
  knowledge_id?: number
}

interface HistoryFile {
  filename: string
  size: number
  created_time: string
  download_url: string
}

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  role?: {
    name: string
    display_name: string
  }
}

export default function Home() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isGuest, setIsGuest] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [historyFiles, setHistoryFiles] = useState<HistoryFile[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [outputFormat, setOutputFormat] = useState<'text' | 'xml'>('text')

  // 拖拽处理 - 移到useEffect之前
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    const validFiles = files.filter(file => {
      const extension = file.name.split('.').pop()?.toLowerCase()
      return ['txt', 'pdf', 'docx', 'doc'].includes(extension || '')
    })
    setSelectedFiles(prev => [...prev, ...validFiles])
  }, [])

  // 登出功能
  const handleLogout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token')
      if (refreshToken && !isGuest) {
        await axios.post('/api/auth/logout', { refresh_token: refreshToken })
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 清除本地存储和session存储
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
      sessionStorage.removeItem('user')
      sessionStorage.removeItem('is_guest')
      delete axios.defaults.headers.common['Authorization']
      
      // 跳转到登录页
      router.push('/login')
    }
  }

  // 检查登录状态
  useEffect(() => {
    const checkAuth = async () => {
      // 检查localStorage和sessionStorage中的token
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      const userData = localStorage.getItem('user') || sessionStorage.getItem('user')
      const guestFlag = sessionStorage.getItem('is_guest')
      
      if (!token || !userData) {
        router.push('/login')
        return
      }

      try {
        // 验证令牌有效性
        const response = await axios.get('/api/auth/verify', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (response.data.valid) {
          setUser(JSON.parse(userData))
          setIsAuthenticated(true)
          setIsGuest(guestFlag === 'true' || response.data.is_guest === true)
          // 设置 axios 默认 header
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        } else {
          // 令牌无效，清除存储并跳转到登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          sessionStorage.removeItem('access_token')
          sessionStorage.removeItem('refresh_token')
          sessionStorage.removeItem('user')
          sessionStorage.removeItem('is_guest')
          router.push('/login')
        }
      } catch (error) {
        console.error('验证令牌失败:', error)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
        sessionStorage.removeItem('user')
        sessionStorage.removeItem('is_guest')
        router.push('/login')
      }
    }

    checkAuth()
  }, [router])

  // 如果未认证，显示加载状态
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // 文件选择处理
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      setSelectedFiles(prev => [...prev, ...files])
    }
  }

  // 移除文件
  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  // 清空文件列表
  const clearFiles = () => {
    setSelectedFiles([])
  }

  // 单文件分析
  const analyzeSingleFile = async () => {
    if (selectedFiles.length === 0) return

    setIsAnalyzing(true)
    setAnalysisResult(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFiles[0])

      // 根据输出格式选择API端点
      const endpoint = outputFormat === 'xml' ? '/api/document/upload-xml' : '/api/document/upload'
      const response = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setAnalysisResult(response.data)
      setSelectedFiles([])
    } catch (error: any) {
      setAnalysisResult({
        status: 'error',
        message: error.response?.data?.detail || '分析失败，请重试',
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  // 批量分析
  const analyzeBatchFiles = async () => {
    if (selectedFiles.length === 0) return

    setIsAnalyzing(true)
    setAnalysisResult(null)

    try {
      const formData = new FormData()
      selectedFiles.forEach(file => {
        formData.append('files', file)
      })

      // 根据选择的格式调用不同的API端点
      const endpoint = outputFormat === 'xml' ? '/api/document/batch-upload-xml' : '/api/document/batch-upload'
      const response = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setAnalysisResult(response.data)
      setSelectedFiles([])
    } catch (error: any) {
      setAnalysisResult({
        status: 'error',
        message: error.response?.data?.detail || '批量分析失败，请重试',
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  // 获取历史记录
  const loadHistory = async () => {
    try {
      const response = await axios.get('/api/document/results')
      setHistoryFiles(response.data.results || [])
      setShowHistory(true)
    } catch (error) {
      console.error('获取历史记录失败:', error)
    }
  }

  // 下载文件
  const downloadFile = (filename: string) => {
    window.open(`/api/document/download/${filename}`, '_blank')
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* 游客模式提醒 */}
        {isGuest && (
          <div className="mb-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="animate-pulse">
                  <span className="text-xl">⚠️</span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  游客模式体验
                </h3>
                <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                  您正在使用游客模式。分析结果和历史记录不会保存，刷新页面后数据将清空。
                  如需保存分析结果，请{' '}
                  <a 
                    href="/register" 
                    className="font-medium underline hover:text-amber-600 dark:hover:text-amber-200"
                  >
                    注册账户
                  </a>{' '}
                  或{' '}
                  <a 
                    href="/login" 
                    className="font-medium underline hover:text-amber-600 dark:hover:text-amber-200"
                  >
                    登录
                  </a>。
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 头部 */}
        <div className="flex justify-between items-center mb-12">
          <div className="text-center flex-1">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              企业文档智能分析系统
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              基于 GPT-4o 的文档分析和 XML 生成工具
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              由 laladoko (徐洪森) 开发
            </p>
            
            {/* 功能导航 */}
            <div className="mt-6 flex flex-wrap gap-4 justify-center">
              <Link 
                href="/knowledge"
                className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                <BookOpenIcon className="h-5 w-5" />
                <span>进入知识库问答</span>
              </Link>
              <Link 
                href="/graphrag"
                className="inline-flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V7.618a1 1 0 01.553-.894L9 4l6 3 6-3 .553.894A1 1 0 0122 7.618v8.764a1 1 0 01-.553.894L15 20l-6-3z" />
                </svg>
                <span>GraphRAG 知识图谱</span>
              </Link>
            </div>
          </div>
          
          {/* 用户信息和登出 */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-white dark:bg-gray-800 rounded-lg px-4 py-2 shadow-md">
              <UserIcon className="h-5 w-5 text-gray-500" />
              <div className="text-sm">
                <p className="font-medium text-gray-900 dark:text-white">
                  {user?.full_name || user?.username}
                </p>
                <p className="text-gray-500 dark:text-gray-400">
                  {user?.role?.display_name || '普通用户'}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center space-x-2 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 px-4 py-2 rounded-lg transition-colors duration-200"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
              <span className="text-sm font-medium">登出</span>
            </button>
          </div>
        </div>

        {/* 文件上传区域 */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mb-8">
          <div
            className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center hover:border-blue-500 dark:hover:border-blue-400 transition-colors duration-300"
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                拖拽文件到此处或点击选择
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                支持 TXT、PDF、DOCX、DOC 格式，最大 16MB
              </p>
            </div>
            <input
              type="file"
              multiple
              accept=".txt,.pdf,.docx,.doc"
              onChange={handleFileSelect}
              className="mt-4 block w-full text-sm text-gray-500 dark:text-gray-400
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                dark:file:bg-blue-900 dark:file:text-blue-300
                dark:hover:file:bg-blue-800"
            />
          </div>

          {/* 已选择的文件列表 */}
          {selectedFiles.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-gray-900 dark:text-white">
                  已选择 {selectedFiles.length} 个文件
                </h4>
                <button
                  onClick={clearFiles}
                  className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 text-sm"
                >
                  清空所有
                </button>
              </div>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <DocumentTextIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      <span className="text-sm text-gray-900 dark:text-white">{file.name}</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                    >
                      移除
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 输出格式选择 */}
          {selectedFiles.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                选择输出格式：
              </h4>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="text"
                    checked={outputFormat === 'text'}
                    onChange={(e) => setOutputFormat(e.target.value as 'text' | 'xml')}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    普通文本分析
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="xml"
                    checked={outputFormat === 'xml'}
                    onChange={(e) => setOutputFormat(e.target.value as 'text' | 'xml')}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    XML结构化格式
                  </span>
                </label>
              </div>
            </div>
          )}

          {/* 分析按钮 */}
          {selectedFiles.length > 0 && (
            <div className="mt-6 flex space-x-4">
              {selectedFiles.length === 1 ? (
                <button
                  onClick={analyzeSingleFile}
                  disabled={isAnalyzing}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>分析中...</span>
                    </>
                  ) : (
                    <>
                      <DocumentArrowUpIcon className="h-5 w-5" />
                      <span>开始分析</span>
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={analyzeBatchFiles}
                  disabled={isAnalyzing}
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>综合分析中...</span>
                    </>
                  ) : (
                    <>
                      <DocumentArrowUpIcon className="h-5 w-5" />
                      <span>
                        {outputFormat === 'xml' ? '生成XML结构化分析' : '综合分析'}
                      </span>
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </div>

        {/* 分析结果 */}
        {analysisResult && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mb-8">
            <div className="flex items-center space-x-3 mb-6">
              {analysisResult.status === 'success' ? (
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              ) : (
                <div className="h-8 w-8 bg-red-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm">!</span>
                </div>
              )}
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                分析结果
              </h3>
            </div>

            <div className="mb-4">
              <p className={`font-medium ${
                analysisResult.status === 'success' ? 'text-green-600' : 'text-red-600'
              }`}>
                {analysisResult.message}
              </p>
              
              {analysisResult.status === 'success' && analysisResult.processed_files && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                  已处理文件: {analysisResult.processed_files.join(', ')}
                </p>
              )}

              {/* 知识库保存成功提示 */}
              {analysisResult.status === 'success' && !isGuest && (
                <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <p className="text-sm text-blue-700 dark:text-blue-300 flex items-center">
                    <BookOpenIcon className="h-4 w-4 mr-2" />
                    文档已自动保存到知识库！您可以在 
                    <Link href="/knowledge" className="mx-1 text-blue-600 dark:text-blue-400 underline hover:text-blue-800 dark:hover:text-blue-300">
                      知识库问答页面
                    </Link> 
                    中查看和使用这个文档进行智能问答。
                  </p>
                </div>
              )}
            </div>

            {analysisResult.status === 'success' && (analysisResult.analysis || analysisResult.xml_analysis) && (
              <>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 mb-6">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-4">
                    AI 分析结果 ({outputFormat === 'xml' ? 'XML格式' : '文本格式'}):
                  </h4>
                  <div className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap text-sm max-h-96 overflow-y-auto">
                    {analysisResult.xml_analysis || analysisResult.analysis}
                  </div>
                </div>

                <div className="flex space-x-4">
                  {analysisResult.xml_file && (
                    <button
                      onClick={() => downloadFile(analysisResult.xml_file!)}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                    >
                      下载 XML 文件
                    </button>
                  )}
                  
                  <button
                    onClick={() => navigator.clipboard.writeText(analysisResult.xml_analysis || analysisResult.analysis || '')}
                    className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                  >
                    复制结果
                  </button>
                  
                  {isGuest && (
                    <div className="text-xs text-amber-600 dark:text-amber-400 self-center ml-4">
                      💡 游客模式下分析结果不会保存
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* 历史记录按钮 */}
        <div className="text-center">
          {isGuest ? (
            <div className="bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg p-4 mx-auto max-w-md">
              <ClockIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                游客模式下无法查看历史记录
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 text-center mt-1">
                注册或登录账户以保存和查看分析历史
              </p>
            </div>
          ) : (
            <button
              onClick={loadHistory}
              className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-6 rounded-lg transition-colors duration-200 flex items-center space-x-2 mx-auto"
            >
              <ClockIcon className="h-5 w-5" />
              <span>查看历史记录</span>
            </button>
          )}
        </div>

        {/* 历史记录列表 */}
        {showHistory && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mt-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                历史分析记录
              </h3>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              >
                关闭
              </button>
            </div>

            {historyFiles.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                暂无历史记录
              </p>
            ) : (
              <div className="space-y-3">
                {historyFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <DocumentTextIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {file.filename}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {file.created_time} • {(file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => downloadFile(file.filename)}
                      className="bg-blue-600 hover:bg-blue-700 text-white text-sm py-1 px-3 rounded transition-colors duration-200"
                    >
                      下载
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
} 