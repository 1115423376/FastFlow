const SETTINGS_KEY = 'fastflow_server_settings'

const DEFAULT_SETTINGS = {
  serverUrl: ''
}

export async function getServerSettings() {
  const stored = await chrome.storage.local.get(SETTINGS_KEY)
  if (stored[SETTINGS_KEY]) {
    return { ...DEFAULT_SETTINGS, ...stored[SETTINGS_KEY] }
  }
  return { ...DEFAULT_SETTINGS }
}

export async function saveServerSettings({ serverUrl }) {
  const normalized = {
    serverUrl: (serverUrl || '').trim().replace(/\/+$/, ''),
  }
  await chrome.storage.local.set({ [SETTINGS_KEY]: normalized })
  return normalized
}

export async function clearServerSettings() {
  await chrome.storage.local.remove(SETTINGS_KEY)
}
