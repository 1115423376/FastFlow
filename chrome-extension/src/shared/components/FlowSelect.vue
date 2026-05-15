<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { ChevronDown, Lock, Plus, X, Pencil } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    required: true
  },
  options: {
    type: Array,
    required: true,
  },
  placeholder: {
    type: String,
    default: '请选择'
  },
  position: {
    type: String,
    default: 'top',
    validator: (value) => ['top', 'bottom'].includes(value)
  },
  width: {
    type: String,
    default: 'auto'
  },
  minWidth: {
    type: String,
    default: '140px'
  },
  dropdownAlign: {
    type: String,
    default: 'start',
    validator: (value) => ['start', 'end'].includes(value)
  },
  showAddButton: {
    type: Boolean,
    default: false
  },
  addLabel: {
    type: String,
    default: 'Add Model'
  },
  enableDelete: {
    type: Boolean,
    default: false
  },
  enableEdit: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'add', 'delete-option', 'edit-option'])

const containerRef = ref(null)
const isOpen = ref(false)
const hoveredItemId = ref(null)

const currentOption = computed(() => {
  return props.options.find(opt => opt.id === props.modelValue)
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const closeDropdown = () => {
  isOpen.value = false
}

const handleGlobalClick = (event) => {
  if (!isOpen.value) return
  const path = event.composedPath()
  if (containerRef.value && !path.includes(containerRef.value)) {
    closeDropdown()
  }
}

watch(isOpen, (val) => {
  if (val) {
    window.addEventListener('click', handleGlobalClick)
  } else {
    window.removeEventListener('click', handleGlobalClick)
    hoveredItemId.value = null
  }
})

onUnmounted(() => {
  window.removeEventListener('click', handleGlobalClick)
})

const selectOption = (option) => {
  emit('update:modelValue', option.id)
  closeDropdown()
}

const handleAdd = (e) => {
  e.stopPropagation()
  closeDropdown()
  emit('add')
}

const handleDelete = (e, option) => {
  e.stopPropagation()
  emit('delete-option', option)
}

const handleEdit = (e, option) => {
  e.stopPropagation()
  closeDropdown()
  emit('edit-option', option)
}
</script>

<template>
  <div 
    ref="containerRef"
    class="flow-select-container" 
    :class="{ 'is-open': isOpen }"
    :style="{ width: width, minWidth: minWidth }"
  >
    <div 
      class="select-trigger" 
      :class="{ active: isOpen }"
      @click="toggleDropdown"
    >
      <div class="trigger-content">
        <span class="select-icon" v-if="currentOption?.icon">
          <component :is="currentOption.icon" size="14" :color="currentOption.color" />
        </span>
        <span class="select-label">{{ currentOption ? currentOption.label : placeholder }}</span>
      </div>
      <ChevronDown size="12" class="chevron" :class="{ rotated: isOpen }" />
    </div>

    <transition name="fade-slide">
      <div 
        v-if="isOpen" 
        class="select-dropdown"
        :class="[position, `align-${dropdownAlign}`]"
      >
        <div 
          v-for="option in options" 
          :key="option.id"
          class="select-item"
          :class="{ active: modelValue === option.id }"
          @click.stop="selectOption(option)"
          @mouseenter="hoveredItemId = option.id"
          @mouseleave="hoveredItemId = null"
        >
          <span class="item-icon" v-if="option.icon">
            <component :is="option.icon" size="14" :color="option.color" />
          </span>
          <span class="item-label">{{ option.label }}</span>
          <Lock 
            v-if="option.isPrivate" 
            size="10" 
            class="item-private-icon"
          />
          <button
            v-if="enableEdit && option.isPrivate && hoveredItemId === option.id"
            class="item-edit-btn"
            @click.stop="handleEdit($event, option)"
            title="Edit private model"
          >
            <Pencil size="10" />
          </button>
          <button
            v-if="enableDelete && option.isPrivate && hoveredItemId === option.id"
            class="item-delete-btn"
            @click.stop="handleDelete($event, option)"
            title="Delete private model"
          >
            <X size="10" />
          </button>
        </div>

        <div v-if="showAddButton" class="select-divider"></div>
        <div 
          v-if="showAddButton"
          class="select-item select-item-add"
          @click.stop="handleAdd"
        >
          <Plus size="12" class="item-add-icon" />
          <span class="item-label">{{ addLabel }}</span>
        </div>
      </div>
    </transition>
  </div>
</template>
