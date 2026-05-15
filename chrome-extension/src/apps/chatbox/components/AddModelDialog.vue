<script setup>
import { ref, reactive, watch } from 'vue'
import { X } from 'lucide-vue-next'
import NeonButton from '@/shared/components/NeonButton.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  privateModelCount: { type: Number, default: 0 },
  maxPrivateModels: { type: Number, default: 2 },
  submitHandler: { type: Function, default: null },
  editMode: { type: Boolean, default: false },
  editData: { type: Object, default: null },
  updateHandler: { type: Function, default: null }
})

const emit = defineEmits(['close'])

const form = reactive({
  model_name: '',
  model_id: '',
  provider: 'openai',
  api_key: '',
  base_url: '',
  model_params: ''
})

const providers = [
  { value: 'openai', label: 'OpenAI', defaultUrl: 'https://api.openai.com/v1' },
  { value: 'anthropic', label: 'Anthropic', defaultUrl: 'https://api.anthropic.com' },
  { value: 'deepseek', label: 'DeepSeek', defaultUrl: 'https://api.deepseek.com/v1' },
  { value: 'minimax', label: 'MiniMax', defaultUrl: 'https://api.minimaxi.com/v1' },
  { value: 'qwen', label: 'Qwen', defaultUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
  { value: 'glm', label: 'GLM', defaultUrl: 'https://open.bigmodel.cn/api/paas/v4' },
  { value: 'moonshot', label: 'Moonshot', defaultUrl: 'https://api.moonshot.cn/v1' },
  { value: 'other', label: 'Other', defaultUrl: '' }
]

const providerDefaultUrls = Object.fromEntries(
  providers.map(p => [p.value, p.defaultUrl])
)

const errors = reactive({
  model_name: '',
  model_id: '',
  provider: '',
  api_key: '',
  base_url: '',
  model_params: '',
  submit: ''
})

const isSubmitting = ref(false)

function resetForm() {
  form.model_name = ''
  form.model_id = ''
  form.provider = 'openai'
  form.api_key = ''
  form.base_url = ''
  form.model_params = ''
  Object.keys(errors).forEach(k => { errors[k] = '' })
}

function validate() {
  let valid = true
  errors.model_name = ''
  errors.model_id = ''
  errors.provider = ''
  errors.api_key = ''
  errors.base_url = ''
  errors.model_params = ''
  errors.submit = ''

  if (!form.model_name.trim()) {
    errors.model_name = 'Model name is required'
    valid = false
  }
  if (!form.model_id.trim()) {
    errors.model_id = 'Model ID is required'
    valid = false
  }
  if (!form.provider) {
    errors.provider = 'Provider is required'
    valid = false
  }
  if (!form.api_key.trim()) {
    errors.api_key = 'API Key is required'
    valid = false
  }
  if (!form.base_url.trim()) {
    errors.base_url = 'Base URL is required'
    valid = false
  }
  if (form.model_params.trim()) {
    try {
      JSON.parse(form.model_params.trim())
    } catch {
      errors.model_params = 'Invalid JSON format'
      valid = false
    }
  }
  return valid
}

async function handleSubmit() {
  if (isSubmitting.value) return
  if (!validate()) return

  isSubmitting.value = true
  errors.submit = ''

  try {
    const payload = {
      model_name: form.model_name.trim(),
      model_id: form.model_id.trim(),
      provider: form.provider,
      api_key: form.api_key.trim(),
      base_url: form.base_url.trim(),
      model_params: form.model_params.trim() ? JSON.parse(form.model_params.trim()) : {}
    }

    if (props.submitHandler) {
      await props.submitHandler(payload)
    }
  } catch (err) {
    errors.submit = err.message || 'Failed to create model'
  } finally {
    isSubmitting.value = false
  }
}

async function handleEditSubmit() {
  if (isSubmitting.value) return
  if (!validate()) return

  isSubmitting.value = true
  errors.submit = ''

  try {
    const payload = {
      model_name: form.model_name.trim(),
      model_id: form.model_id.trim(),
      provider: form.provider,
      api_key: form.api_key.trim(),
      base_url: form.base_url.trim(),
      model_params: form.model_params.trim() ? JSON.parse(form.model_params.trim()) : {}
    }

    if (props.updateHandler) {
      await props.updateHandler(props.editData.id, payload)
    }
  } catch (err) {
    errors.submit = err.message || 'Failed to update model'
  } finally {
    isSubmitting.value = false
  }
}

function handleClose() {
  if (isSubmitting.value) return
  resetForm()
  emit('close')
}

watch(() => props.visible, (val) => {
  if (!val) return
  if (props.editMode && props.editData) {
    form.model_name = props.editData.modelName || props.editData.model_name || ''
    form.model_id = props.editData.modelId || props.editData.model_id || ''
    form.provider = props.editData.provider || 'openai'
    form.api_key = props.editData.apiKey || props.editData.api_key || ''
    form.base_url = props.editData.baseUrl || props.editData.base_url || ''
    const params = props.editData.modelParams || props.editData.model_params
    form.model_params = params ? (typeof params === 'string' ? params : JSON.stringify(params, null, 2)) : ''
    Object.keys(errors).forEach(k => { errors[k] = '' })
    return
  }
  resetForm()
})

watch(() => form.provider, (newProvider, oldProvider) => {
  const prevDefault = providerDefaultUrls[oldProvider] || ''
  const newDefault = providerDefaultUrls[newProvider] || ''
  if (!form.base_url || form.base_url === prevDefault) {
    form.base_url = newDefault
  }
})
</script>

<template>
  <transition name="add-model-fade">
    <div v-if="visible" class="add-model-overlay" @click.self="handleClose">
      <div class="add-model-dialog" @click.stop>
        <div class="add-model-header">
          <span class="add-model-title">{{ editMode ? 'Edit Private Model' : 'Add Private Model' }}</span>
          <button class="add-model-close" @click="handleClose" :disabled="isSubmitting">
            <X size="14" />
          </button>
        </div>

        <div v-if="!editMode" class="add-model-limit-hint">
          Private models: {{ privateModelCount }} / {{ maxPrivateModels }}
        </div>

        <form class="add-model-form" @submit.prevent="editMode ? handleEditSubmit() : handleSubmit()">
          <div class="add-model-field">
            <label class="add-model-label">Model Name <span class="required">*</span></label>
            <input
              v-model="form.model_name"
              type="text"
              class="add-model-input"
              placeholder="e.g. My GPT-4"
              :disabled="isSubmitting"
              autocomplete="off"
            />
            <span v-if="errors.model_name" class="add-model-error">{{ errors.model_name }}</span>
          </div>

          <div class="add-model-field">
            <label class="add-model-label">Model ID <span class="required">*</span></label>
            <input
              v-model="form.model_id"
              type="text"
              class="add-model-input"
              placeholder="e.g. gpt-4"
              :disabled="isSubmitting"
              autocomplete="off"
            />
            <span v-if="errors.model_id" class="add-model-error">{{ errors.model_id }}</span>
          </div>

          <div class="add-model-field">
            <label class="add-model-label">Provider <span class="required">*</span></label>
            <select
              v-model="form.provider"
              class="add-model-input add-model-select"
              :disabled="isSubmitting"
            >
              <option v-for="p in providers" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
            <span v-if="errors.provider" class="add-model-error">{{ errors.provider }}</span>
          </div>

          <div class="add-model-field">
            <label class="add-model-label">API Key <span class="required">*</span></label>
            <input
              v-model="form.api_key"
              type="password"
              class="add-model-input"
              placeholder="sk-..."
              :disabled="isSubmitting"
              autocomplete="off"
            />
            <span v-if="errors.api_key" class="add-model-error">{{ errors.api_key }}</span>
          </div>

          <div class="add-model-field">
            <label class="add-model-label">Base URL <span class="required">*</span></label>
            <input
              v-model="form.base_url"
              type="text"
              class="add-model-input"
              placeholder="e.g. https://api.openai.com/v1"
              :disabled="isSubmitting"
              autocomplete="off"
            />
            <span v-if="errors.base_url" class="add-model-error">{{ errors.base_url }}</span>
          </div>

          <div class="add-model-field">
            <label class="add-model-label">Model Params <span class="optional">(optional)</span></label>
            <textarea
              v-model="form.model_params"
              class="add-model-input add-model-textarea"
              placeholder='{"temperature": 0.7}'
              rows="2"
              :disabled="isSubmitting"
            ></textarea>
            <span v-if="errors.model_params" class="add-model-error">{{ errors.model_params }}</span>
          </div>

          <span v-if="errors.submit" class="add-model-error add-model-submit-error">{{ errors.submit }}</span>

          <div class="add-model-actions">
            <NeonButton
              type="button"
              :disabled="isSubmitting"
              @click="handleClose"
            >
              Cancel
            </NeonButton>
            <NeonButton
              type="submit"
              :disabled="isSubmitting"
            >
              {{ isSubmitting ? 'Saving...' : (editMode ? 'Update Model' : 'Add Model') }}
            </NeonButton>
          </div>
        </form>
      </div>
    </div>
  </transition>
</template>
