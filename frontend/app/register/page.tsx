'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { EyeIcon, EyeSlashIcon, UserIcon, EnvelopeIcon, LockClosedIcon, PhoneIcon, UserPlusIcon } from '@heroicons/react/24/outline'

interface RegisterForm {
  username: string
  email: string
  password: string
  confirm_password: string
  full_name: string
  phone: string
}

interface RegisterResponse {
  message: string
  user_id: number
  username: string
  email: string
}

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState<RegisterForm>({
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    full_name: '',
    phone: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [fieldErrors, setFieldErrors] = useState<{[key: string]: string}>({})

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')
    setFieldErrors({})

    // 客户端验证
    if (!form.username || form.username.length < 3) {
      setError('用户名至少需要3个字符')
      setLoading(false)
      return
    }

    if (!form.email || !form.email.includes('@')) {
      setError('请输入有效的邮箱地址')
      setLoading(false)
      return
    }

    if (!form.password || form.password.length < 6) {
      setError('密码长度至少6位')
      setLoading(false)
      return
    }

    // 检查密码是否包含字母和数字
    const hasLetter = /[a-zA-Z]/.test(form.password)
    const hasNumber = /\d/.test(form.password)
    if (!hasLetter || !hasNumber) {
      setError('密码必须包含至少一个字母和一个数字')
      setLoading(false)
      return
    }

    if (form.password !== form.confirm_password) {
      setError('两次输入的密码不一致')
      setLoading(false)
      return
    }

    try {
      const response = await axios.post<RegisterResponse>('/api/auth/register', form)
      setSuccess('注册成功！请登录您的账户')
      
      // 3秒后跳转到登录页
      setTimeout(() => {
        router.push('/login')
      }, 3000)
    } catch (error: any) {
      console.error('注册失败:', error)
      if (error.response?.data?.detail) {
        // 处理422验证错误
        if (Array.isArray(error.response.data.detail)) {
          // 如果是验证错误数组，将错误映射到对应字段
          const newFieldErrors: {[key: string]: string} = {}
          let hasFieldError = false
          
          error.response.data.detail.forEach((err: any) => {
            if (err.loc && err.loc.length > 1) {
              const fieldName = err.loc[1] // 获取字段名
              newFieldErrors[fieldName] = err.msg
              hasFieldError = true
            }
          })
          
          if (hasFieldError) {
            setFieldErrors(newFieldErrors)
            setError('请检查输入信息')
          } else {
            // 如果没有字段错误，显示第一个错误
            const firstError = error.response.data.detail[0]
            setError(firstError.msg || '输入数据验证失败')
          }
        } else if (typeof error.response.data.detail === 'string') {
          // 如果是字符串错误消息
          setError(error.response.data.detail)
        } else {
          setError('注册失败，请检查输入信息')
        }
      } else {
        setError('注册失败，请检查网络连接')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setForm(prev => ({
      ...prev,
      [name]: value
    }))

    // 清除错误状态
    setError('')
    setFieldErrors(prev => ({
      ...prev,
      [name]: ''
    }))

    // 实时验证
    let fieldError = ''
    if (name === 'username' && value && value.length < 3) {
      fieldError = '用户名至少需要3个字符'
    } else if (name === 'email' && value && !value.includes('@')) {
      fieldError = '请输入有效的邮箱地址'
    } else if (name === 'password' && value) {
      if (value.length < 6) {
        fieldError = '密码长度至少6位'
      } else {
        const hasLetter = /[a-zA-Z]/.test(value)
        const hasNumber = /\d/.test(value)
        if (!hasLetter || !hasNumber) {
          fieldError = '密码必须包含至少一个字母和一个数字'
        }
      }
    } else if (name === 'confirm_password' && value && value !== form.password) {
      fieldError = '两次输入的密码不一致'
    }

    if (fieldError) {
      setFieldErrors(prev => ({
        ...prev,
        [name]: fieldError
      }))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* 头部 */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-emerald-600 rounded-full flex items-center justify-center">
            <UserPlusIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900 dark:text-white">
            注册账户
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            加入企业文档智能分析系统
          </p>
        </div>

        {/* 注册表单 */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="bg-white dark:bg-gray-800 shadow-xl rounded-lg p-8">
            {/* 错误提示 */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* 成功提示 */}
            {success && (
              <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                <p className="text-sm text-green-600 dark:text-green-400">{success}</p>
              </div>
            )}

            <div className="space-y-4">
              {/* 用户名输入 */}
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  用户名 *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <UserIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    required
                    value={form.username}
                    onChange={handleInputChange}
                    className={`block w-full pl-10 pr-3 py-3 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none dark:bg-gray-700 dark:text-white ${
                      fieldErrors.username 
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
                        : 'border-gray-300 dark:border-gray-600 focus:ring-emerald-500 focus:border-emerald-500'
                    }`}
                    placeholder="请输入用户名"
                  />
                </div>
                {fieldErrors.username && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{fieldErrors.username}</p>
                )}
              </div>

              {/* 邮箱输入 */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  邮箱 *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={form.email}
                    onChange={handleInputChange}
                    className={`block w-full pl-10 pr-3 py-3 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none dark:bg-gray-700 dark:text-white ${
                      fieldErrors.email 
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
                        : 'border-gray-300 dark:border-gray-600 focus:ring-emerald-500 focus:border-emerald-500'
                    }`}
                    placeholder="请输入邮箱地址"
                  />
                </div>
                {fieldErrors.email && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{fieldErrors.email}</p>
                )}
              </div>

              {/* 全名输入 */}
              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  姓名
                </label>
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  value={form.full_name}
                  onChange={handleInputChange}
                  className="block w-full px-3 py-3 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 dark:bg-gray-700 dark:text-white"
                  placeholder="请输入真实姓名"
                />
              </div>

              {/* 手机号输入 */}
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  手机号
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <PhoneIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    value={form.phone}
                    onChange={handleInputChange}
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 dark:bg-gray-700 dark:text-white"
                    placeholder="请输入手机号"
                  />
                </div>
              </div>

              {/* 密码输入 */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  密码 *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LockClosedIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={form.password}
                    onChange={handleInputChange}
                    className={`block w-full pl-10 pr-10 py-3 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none dark:bg-gray-700 dark:text-white ${
                      fieldErrors.password 
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
                        : 'border-gray-300 dark:border-gray-600 focus:ring-emerald-500 focus:border-emerald-500'
                    }`}
                    placeholder="请输入密码（至少6位，包含字母和数字）"
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>
                </div>
                {fieldErrors.password && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{fieldErrors.password}</p>
                )}
              </div>

              {/* 确认密码输入 */}
              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  确认密码 *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LockClosedIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="confirm_password"
                    name="confirm_password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    required
                    value={form.confirm_password}
                    onChange={handleInputChange}
                    className={`block w-full pl-10 pr-10 py-3 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none dark:bg-gray-700 dark:text-white ${
                      fieldErrors.confirm_password 
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
                        : 'border-gray-300 dark:border-gray-600 focus:ring-emerald-500 focus:border-emerald-500'
                    }`}
                    placeholder="请再次输入密码"
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>
                </div>
                {fieldErrors.confirm_password && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{fieldErrors.confirm_password}</p>
                )}
              </div>
            </div>

            {/* 注册按钮 */}
            <div className="mt-6">
              <button
                type="submit"
                disabled={loading || success !== ''}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    注册中...
                  </div>
                ) : success ? (
                  '注册成功，即将跳转...'
                ) : (
                  '注册'
                )}
              </button>
            </div>

            {/* 登录链接 */}
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                已有账户？{' '}
                <a href="/login" className="font-medium text-emerald-600 hover:text-emerald-500 dark:text-emerald-400">
                  立即登录
                </a>
              </p>
            </div>
          </div>
        </form>

        {/* 底部信息 */}
        <div className="text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            注册即表示您同意我们的服务条款和隐私政策
          </p>
        </div>
      </div>
    </div>
  )
} 