import { runtimeConfig } from '@/extension/config/runtime'
import { AUTHORIZATION_KEY, authService } from '@/shared/services/auth.js'
import { cache } from '@/shared/utils/cache.js'

const MAX_NETWORK_FAILURES = 3

/**
 * 统一登录态守卫
 * 职责：
 * 1) 定时校验登录状态
 * 2) 监听 Authorization 变化
 * 3) 监听登录过期事件
 */
export function createAuthGuard(options = {}) {
  const {
    // 定时校验间隔，默认走配置
    intervalMs = runtimeConfig.authCheckIntervalMs,
    // 登录态变化回调：true=已登录，false=未登录/过期
    onAuthedChange
  } = options

  let timer = null
  let unsubscribe = null
  let authed = null
  let networkFailureCount = 0

  // 统一设置登录态，避免重复触发
  function setAuthed(val) {
    if (authed === val) return
    authed = val
    if (onAuthedChange) onAuthedChange(val)
  }

  // 统一校验逻辑：无 token 直接判定未登录；有 token 则服务端校验
  async function verify() {
    const token = await cache.get(AUTHORIZATION_KEY)
    if (!token) {
      networkFailureCount = 0
      setAuthed(false)
      return false
    }

    try {
      // 尝试刷新 Token（如果即将过期）
      try {
        if (await authService.shouldRefreshToken()) {
          await authService.refreshToken()
        }
      } catch (refreshError) {
        console.warn('[FastFlow] Token refresh failed, continuing with checkLogin:', refreshError)
      }

      await authService.checkLogin()
      networkFailureCount = 0
      setAuthed(true)
      return true
    } catch (e) {
      // 网络错误：保留当前登录状态，累计失败次数
      if (e.isNetworkError || e.status === 0) {
        networkFailureCount++
        if (networkFailureCount < MAX_NETWORK_FAILURES) {
          return authed
        }
      }
      // 认证失败或网络失败次数过多：清除登录状态
      networkFailureCount = 0
      setAuthed(false)
      return false
    }
  }

  function handleAuthExpired() {
    networkFailureCount = 0
    setAuthed(false)
  }

  // 启动守卫（幂等）
  async function start() {
    await verify()

    if (!timer) {
      timer = setInterval(() => {
        verify()
      }, intervalMs)
    }

    if (!unsubscribe) {
      unsubscribe = cache.onChanged((changes) => {
        const authChange = changes?.[AUTHORIZATION_KEY]
        if (!authChange) return

        if (!authChange.newValue) {
          networkFailureCount = 0
          setAuthed(false)
          return
        }

        setAuthed(true)
        verify()
      })
    }

    window.addEventListener(authService.getAuthExpiredEventName(), handleAuthExpired)
  }

  // 停止守卫
  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    if (unsubscribe) {
      unsubscribe()
      unsubscribe = null
    }
    window.removeEventListener(authService.getAuthExpiredEventName(), handleAuthExpired)
  }

  return {
    start,
    stop,
    verify,
    getAuthed: () => authed
  }
}
