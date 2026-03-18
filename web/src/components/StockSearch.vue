<template>
  <div class="stock-search">
    <div class="search-input-wrapper">
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索股票代码或名称..."
        class="search-input"
      />
      <button v-if="keyword" class="clear-btn" @click="clearSearch">×</button>
    </div>
    <div v-if="loading" class="search-loading">搜索中...</div>
    <div v-else-if="results.length > 0" class="search-results">
      <div
        v-for="stock in results"
        :key="stock.code"
        class="search-result-item"
        @click="selectStock(stock)"
      >
        <span class="stock-code">{{ stock.code }}</span>
        <span class="stock-name">{{ stock.name }}</span>
        <span v-if="stock.industry" class="stock-industry">{{ stock.industry }}</span>
        <button
          v-if="!isInWatchlist(stock.code)"
          class="add-btn"
          @click.stop="addToWatchlist(stock.code)"
        >+</button>
        <button
          v-else
          class="remove-btn"
          @click.stop="removeFromWatchlist(stock.code)"
        >-</button>
      </div>
    </div>
    <div v-else-if="keyword && !loading" class="search-empty">未找到相关股票</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { stockApi, type StockInfo } from '@/api/stock'

const emit = defineEmits<{
  select: [code: string]
  addWatchlist: [code: string]
  removeWatchlist: [code: string]
}>()

const props = defineProps<{
  watchlist: string[]
}>()

const keyword = ref('')
const results = ref<StockInfo[]>([])
const loading = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(keyword, (newVal) => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }

  if (!newVal.trim()) {
    results.value = []
    loading.value = false
    return
  }

  loading.value = true
  debounceTimer = setTimeout(async () => {
    try {
      const res = await stockApi.search(newVal.trim())
      results.value = res.data
    } catch (e) {
      console.error('Search failed:', e)
      results.value = []
    } finally {
      loading.value = false
    }
  }, 300)
})

function clearSearch() {
  keyword.value = ''
  results.value = []
}

function selectStock(stock: StockInfo) {
  emit('select', stock.code)
}

function isInWatchlist(code: string) {
  return props.watchlist.includes(code)
}

function addToWatchlist(code: string) {
  emit('addWatchlist', code)
}

function removeFromWatchlist(code: string) {
  emit('removeWatchlist', code)
}
</script>

<style scoped>
.stock-search {
  position: relative;
  width: 100%;
}

.search-input-wrapper {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 8px 30px 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #409eff;
}

.clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
}

.search-loading,
.search-empty {
  padding: 10px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 100;
}

.search-result-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  gap: 8px;
}

.search-result-item:hover {
  background: #f5f7fa;
}

.stock-code {
  font-weight: bold;
  color: #409eff;
  min-width: 70px;
}

.stock-name {
  flex: 1;
}

.stock-industry {
  font-size: 12px;
  color: #999;
}

.add-btn,
.remove-btn {
  padding: 2px 8px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 14px;
}

.add-btn {
  background: #409eff;
  color: white;
}

.add-btn:hover {
  background: #66b1ff;
}

.remove-btn {
  background: #f56c6c;
  color: white;
}

.remove-btn:hover {
  background: #f78989;
}
</style>
