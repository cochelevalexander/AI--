<template>
  <div class="container">
    <header>
      <h1>AI-помощник контент-менеджера</h1>
      <p>Введите данные прибора для генерации карточки товара</p>
    </header>

    <div class="layout">
      <!-- ЛЕВАЯ ЧАСТЬ: Ввод -->
      <div class="panel">
        <form @submit.prevent="generateCard" class="form">
          <div class="form-group">
            <label for="name">Название товара</label>
            <input id="name" v-model="form.name" type="text" placeholder="Например: Манометр показывающий ДМ 02" required />
          </div>

          <div class="form-group">
            <label for="manufacturer">Производитель</label>
            <input id="manufacturer" v-model="form.manufacturer" type="text" placeholder="Например: Манотомь" required />
          </div>

          <div class="form-group">
            <label>Характеристики (specs) *</label>
            <div v-for="(spec, index) in form.specs" :key="index" class="spec-row">
              <input v-model="spec.key" type="text" placeholder="Название (напр., класс точности)" />
              <input v-model="spec.value" type="text" placeholder="Значение (напр., 1,5)" />
              <button type="button" @click="removeSpec(index)" class="btn-remove">✕</button>
            </div>
            <button type="button" @click="addSpec" class="btn-add">+ Добавить характеристику</button>
            <small class="hint">Заполните хотя бы одну характеристику (и название, и значение).</small>
          </div>

          <div class="form-group">
            <label for="description">Текстовое описание / паспорт</label>
            <textarea id="description" v-model="form.description" rows="4" placeholder="Прибор предназначен для..." required></textarea>
          </div>

          <button type="submit" class="btn-submit" :disabled="isLoading">
            {{ isLoading ? 'Генерация...' : 'Сгенерировать карточку' }}
          </button>
        </form>
      </div>

      <!-- ПРАВАЯ ЧАСТЬ: Результат -->
      <div class="panel">
        <div v-if="error" class="error-box">
          {{ error }}
        </div>

        <div v-if="!result && !error" class="placeholder">
          Здесь появится готовый черновик карточки товара.
        </div>

        <div v-if="result" class="result">
          <div v-if="result.missing_fields && result.missing_fields.length" class="warning-box">
            <strong>Не хватает данных:</strong> {{ result.missing_fields.join(', ') }}
          </div>

          <div class="field">
            <div class="field-header">
              <span>SEO-заголовок</span>
              <button @click="copy(result.seo_title)" class="btn-copy">Копировать</button>
            </div>
            <div class="field-value">{{ result.seo_title }}</div>
          </div>

          <div class="field">
            <div class="field-header">
              <span>SEO-описание</span>
              <button @click="copy(result.seo_description)" class="btn-copy">Копировать</button>
            </div>
            <div class="field-value">{{ result.seo_description }}</div>
          </div>

          <div class="field">
            <div class="field-header">
              <span>Ключевые характеристики</span>
              <button @click="copy(result.key_features?.join('\n') || '')" class="btn-copy">Копировать</button>
            </div>
            <ul class="field-value">
              <li v-for="(f, i) in result.key_features" :key="i">{{ f }}</li>
            </ul>
          </div>

          <div class="field">
            <div class="field-header">
              <span>Поисковые запросы</span>
              <button @click="copy(result.search_queries?.join('\n') || '')" class="btn-copy">Копировать</button>
            </div>
            <div class="field-value">
              <span v-for="(q, i) in result.search_queries" :key="i" class="tag">{{ q }}</span>
            </div>
          </div>

          <div class="field">
            <div class="field-header">
              <span>Commercial-блок для менеджера</span>
              <button @click="copy(result.commercial_block)" class="btn-copy">Копировать</button>
            </div>
            <div class="field-value">{{ result.commercial_block }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const config = useRuntimeConfig()

const form = reactive({
  name: '',
  manufacturer: '',
  specs: [{ key: '', value: '' }],
  description: ''
})

const isLoading = ref(false)
const error = ref('')
const result = ref(null)
const validationError = ref('')

const addSpec = () => form.specs.push({ key: '', value: '' })
const removeSpec = (index) => form.specs.splice(index, 1)

const copy = async (text) => {
  try {
    await navigator.clipboard.writeText(text || '')
  } catch (e) {
    console.error('Не удалось скопировать', e)
  }
}

const generateCard = async () => {
  error.value = ''
  validationError.value = ''
  result.value = null

  const filledSpecs = form.specs.filter(
    s => s.key.trim() && s.value.trim()
  )

  if (filledSpecs.length === 0) {
    validationError.value = 'Заполните хотя бы одну характеристику.'
    error.value = validationError.value
    return
  }

  isLoading.value = true

  const formattedSpecs = {}
  filledSpecs.forEach(item => {
    formattedSpecs[item.key.trim()] = item.value.trim()
  })

  const payload = {
    name: form.name,
    manufacturer: form.manufacturer,
    specs: formattedSpecs,
    description: form.description
  }

  try {
    const response = await $fetch(`${config.public.apiBase}/api/generate`, {
      method: 'POST',
      body: payload
    })
    result.value = response
    console.log(response)
  } catch (err) {
    error.value = err.data?.detail || 'Ошибка соединения с сервером.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.container {
  max-width: 1100px;
  margin: 40px auto;
  padding: 0 20px;
  font-family: system-ui, sans-serif;
  color: #333;
}
header {
  margin-bottom: 25px;
}
header h1 {
  margin: 0 0 5px 0;
  font-size: 26px;
}
header p {
  margin: 0;
  color: #666;
}


.layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 25px;
}
@media (max-width: 800px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

.panel {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  min-height: 300px;
}

.form-group {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
}
label {
  font-weight: bold;
  margin-bottom: 5px;
  font-size: 14px;
}
input, textarea {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}
.spec-row {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}
.spec-row input { flex: 1; }
.btn-remove {
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  padding: 0 10px;
}
.btn-add {
  background: #e0e0e0;
  border: none;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  align-self: flex-start;
  margin-top: 5px;
}
.btn-submit {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 10px;
}
.btn-submit:disabled {
  background: #999;
  cursor: not-allowed;
}
.hint {
  color: #888;
  font-size: 12px;
  margin-top: 5px;
}


.placeholder {
  color: #999;
  text-align: center;
  margin-top: 100px;
  font-size: 14px;
}
.result .field {
  margin-bottom: 20px;
}
.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  margin-bottom: 6px;
  font-size: 14px;
}
.field-value {
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  background: #fafafa;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #eee;
}
.btn-copy {
  background: #007bff;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-copy:hover {
  background: #0056b3;
}
.tag {
  display: inline-block;
  background: #e3f2fd;
  color: #0d47a1;
  padding: 3px 8px;
  border-radius: 12px;
  margin-right: 6px;
  margin-bottom: 6px;
  font-size: 13px;
}


.error-box {
  padding: 15px;
  background: #ffe6e6;
  color: #d32f2f;
  border-radius: 4px;
  border: 1px solid #ffcaca;
  margin-bottom: 15px;
}
.warning-box {
  margin-bottom: 15px;
  padding: 10px 15px;
  background: #fff8e1;
  border: 1px solid #ffe082;
  border-radius: 4px;
  color: #8a6d3b;
  font-size: 14px;
}
</style>