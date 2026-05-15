import { authService } from '@/shared/services/auth.js'
import { backendClient } from '@/extension/runtime/backend-client.js'

async function buildAuthHeaders() {
  const token = await authService.getToken()
  return {
    'Content-Type': 'application/json',
    'Authorization': token || ''
  }
}

export async function getModelConfigs() {
  try {
    const headers = await buildAuthHeaders()
    const response = await backendClient.request({
      service: 'api',
      path: '/fastflow/api/v1/model_config/list',
      method: 'GET',
      headers
    })
    const result = response.data
    if (!response.ok || !result || result.code !== 200) {
      throw new Error(result?.message || 'get model config list failed')
    }
    return result.data || []
  } catch (error) {
    console.error('[FastFlow] Get model config list failed:', error)
    return []
  }
}

export async function createModel(modelData) {
  const headers = await buildAuthHeaders()
  const response = await backendClient.request({
    service: 'api',
    path: '/fastflow/api/v1/model_config',
    method: 'POST',
    headers,
    body: modelData
  })
  const result = response.data
  if (!response.ok || !result || result.code !== 200) {
    throw new Error(result?.message || 'create model config failed')
  }
  return result.data
}

export async function deleteModel(modelId) {
  const headers = await buildAuthHeaders()
  const response = await backendClient.request({
    service: 'api',
    path: `/fastflow/api/v1/model_config/${modelId}`,
    method: 'DELETE',
    headers
  })
  const result = response.data
  if (!response.ok || !result || result.code !== 200) {
    throw new Error(result?.message || 'delete model config failed')
  }
  return result.data
}

export async function getModelDetail(modelId) {
  const headers = await buildAuthHeaders()
  const response = await backendClient.request({
    service: 'api',
    path: `/fastflow/api/v1/model_config/${modelId}`,
    method: 'GET',
    headers
  })
  const result = response.data
  if (!response.ok || !result || result.code !== 200) {
    throw new Error(result?.message || 'get model detail failed')
  }
  return result.data
}

export async function updateModel(modelId, modelData) {
  const headers = await buildAuthHeaders()
  const response = await backendClient.request({
    service: 'api',
    path: `/fastflow/api/v1/model_config/${modelId}`,
    method: 'PUT',
    headers,
    body: modelData
  })
  const result = response.data
  if (!response.ok || !result || result.code !== 200) {
    throw new Error(result?.message || 'update model config failed')
  }
  return result.data
}
