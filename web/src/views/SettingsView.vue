<template>
  <div class="settings-view">
    <h2>系统设置</h2>
    
    <!-- 大模型配置 -->
    <div class="section">
      <h3>大模型配置</h3>
      
      <div class="form-group">
        <label>提供商</label>
        <select v-model="config.llm.provider" @change="onProviderChange">
          <option value="ollama">Ollama (本地)</option>
          <option value="openai">OpenAI</option>
          <option value="deepseek">DeepSeek</option>
          <option value="custom">自定义</option>
        </select>
      </div>

      <!-- Ollama 配置 -->
      <div v-if="config.llm.provider === 'ollama'" class="provider-config">
        <div class="form-group">
          <label>API 地址</label>
          <input v-model="config.llm.ollama.base_url" type="text" placeholder="http://localhost:11434" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="config.llm.ollama.model" type="text" placeholder="qwen2.5:7b" />
        </div>
      </div>

      <!-- OpenAI 配置 -->
      <div v-if="config.llm.provider === 'openai'" class="provider-config">
        <div class="form-group">
          <label>API Key</label>
          <input v-model="config.llm.openai.api_key" type="password" placeholder="sk-..." />
        </div>
        <div class="form-group">
          <label>API 地址</label>
          <input v-model="config.llm.openai.base_url" type="text" placeholder="https://api.openai.com/v1" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="config.llm.openai.model" type="text" placeholder="gpt-4o-mini" />
        </div>
      </div>

      <!-- DeepSeek 配置 -->
      <div v-if="config.llm.provider === 'deepseek'" class="provider-config">
        <div class="form-group">
          <label>API Key</label>
          <input v-model="config.llm.deepseek.api_key" type="password" placeholder="sk-..." />
        </div>
        <div class="form-group">
          <label>API 地址</label>
          <input v-model="config.llm.deepseek.base_url" type="text" placeholder="https://api.deepseek.com" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="config.llm.deepseek.model" type="text" placeholder="deepseek-chat" />
        </div>
      </div>

      <!-- 自定义配置 -->
      <div v-if="config.llm.provider === 'custom'" class="provider-config">
        <div class="form-group">
          <label>自定义名称</label>
          <input v-model="config.llm.custom.name" type="text" placeholder="例如：My LLM" />
        </div>
        <div class="form-group">
          <label>API Key</label>
          <input v-model="config.llm.custom.api_key" type="password" placeholder="可选" />
        </div>
        <div class="form-group">
          <label>API 地址</label>
          <input v-model="config.llm.custom.base_url" type="text" placeholder="https://api.example.com" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="config.llm.custom.model" type="text" placeholder="model-name" />
        </div>
        <div class="form-group">
          <label>Chat 接口路径 <span class="hint">(预留字段，OpenAI 兼容 API 无需修改)</span></label>
          <input v-model="config.llm.custom.chat_path" type="text" placeholder="/chat/completions" />
        </div>
      </div>

      <div class="action-group">
        <button @click="testConnection" :disabled="testing" class="btn btn-secondary">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        <button @click="saveConfig" :disabled="saving" class="btn btn-primary">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>

      <div v-if="testResult" :class="['test-result', testResult.success ? 'success' : 'error']">
        {{ testResult.message }}
      </div>
    </div>

    <!-- 对话测试 -->
    <div class="section">
      <h3>对话测试</h3>
      
      <div class="chat-box">
        <div class="chat-messages" ref="chatMessages">
          <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
            <div class="message-content">{{ msg.content }}</div>
          </div>
        </div>
        
        <div class="chat-input">
          <input 
            v-model="inputMessage" 
            type="text" 
            @keyup.enter="sendMessage"
            placeholder="输入消息..." 
          />
          <button @click="sendMessage" :disabled="sending" class="btn btn-primary">
            {{ sending ? '发送中...' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import api from '@/api'
import { streamRequest } from '@/utils/stream'

const config = reactive({
  llm: {
    provider: 'ollama',
    ollama: { base_url: 'http://localhost:11434', model: 'qwen2.5:7b' },
    openai: { api_key: '', base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
    deepseek: { api_key: '', base_url: 'https://api.deepseek.com', model: 'deepseek-chat' },
    custom: { name: '', api_key: '', base_url: '', model: '', chat_path: '/chat/completions' }
  }
})

const testing = ref(false)
const saving = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

const messages = ref<Array<{ role: string; content: string }>>([])
const inputMessage = ref('')
const sending = ref(false)
const chatMessages = ref<HTMLElement | null>(null)

onMounted(async () => {
  await loadConfig()
})

const loadConfig = async () => {
  try {
    const res = await api.get('/config/')
    Object.assign(config, res.data)
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

const onProviderChange = () => {
  testResult.value = null
}

const testConnection = async () => {
  testing.value = true
  testResult.value = null
  
  try {
    const res = await api.post('/config/test-connection/', config)
    testResult.value = res.data
  } catch (error: any) {
    testResult.value = { success: false, message: error.response?.data?.detail || '测试失败' }
  } finally {
    testing.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  
  try {
    await api.put('/config/', config)
    testResult.value = { success: true, message: '配置已保存' }
  } catch (error: any) {
    testResult.value = { success: false, message: error.response?.data?.detail || '保存失败' }
  } finally {
    saving.value = false
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  const userMsg = { role: 'user', content: inputMessage.value }
  messages.value.push(userMsg)
  inputMessage.value = ''
  sending.value = true
  
  scrollToBottom()
  
  const assistantIndex = messages.value.push({ role: 'assistant', content: '' }) - 1
  let fullContent = ''
  
  try {
    await streamRequest('/api/llm/chat', {
      body: {
        messages: [...messages.value],
        stream: true
      },
      onChunk: (data) => {
        if (data.content) {
          fullContent += data.content
          messages.value[assistantIndex].content = fullContent
          scrollToBottom()
        }
        if (data.error) {
          messages.value[assistantIndex].content = `错误：${data.error}`
        }
      },
      onError: (error) => {
        messages.value[assistantIndex].content = `错误：${error.message}`
      }
    })
  } catch (error: any) {
    // 错误已在 streamRequest 中处理
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.settings-view {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 30px;
  color: #333;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h3 {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 16px;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: #333;
  font-weight: 500;
}

input, select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

input:focus, select:focus {
  outline: none;
  border-color: #007bff;
}

.provider-config {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.action-group {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.test-result {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
}

.test-result.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.test-result.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* 对话测试样式 */
.chat-box {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.chat-messages {
  height: 300px;
  overflow-y: auto;
  padding: 16px;
  background: #f8f9fa;
}

.message {
  margin-bottom: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  max-width: 80%;
}

.message.user {
  background: #007bff;
  color: white;
  margin-left: auto;
}

.message.assistant {
  background: white;
  border: 1px solid #ddd;
}

.message-content {
  word-wrap: break-word;
  white-space: pre-wrap;
}

.chat-input {
  display: flex;
  gap: 10px;
  padding: 12px;
  background: white;
  border-top: 1px solid #ddd;
}

.chat-input input {
  flex: 1;
}
</style>
