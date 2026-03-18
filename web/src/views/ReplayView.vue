<template>
  <div class="replay-view">
    <div class="replay-header">
      <div class="search-section">
        <StockSearch
          :watchlist="[]"
          @select="onSelectStock"
        />
      </div>
      <div class="selected-stocks">
        <span class="label">已选股票：</span>
        <div class="stock-tags">
          <span
            v-for="stock in selectedStocks"
            :key="stock.code"
            class="stock-tag"
          >
            {{ stock.name }}
            <button @click="removeSelectedStock(stock.code)">×</button>
          </span>
          <span v-if="selectedStocks.length === 0" class="empty-hint">
            请从上方搜索添加股票
          </span>
        </div>
      </div>
    </div>

    <div class="replay-main">
      <div class="control-section">
        <ReplayControl
          :startTime="startTime"
          :endTime="endTime"
          :currentTime="currentTime"
          :isPlaying="isPlaying"
          @update:currentTime="onTimeUpdate"
          @update:isPlaying="onPlayingUpdate"
          @dateChange="onDateChange"
          @speedChange="onSpeedChange"
        />
      </div>

      <div class="charts-section">
        <MultiReplayLayout
          :stocks="replayStocks"
          :currentTime="currentTime"
          @removeStock="onRemoveStock"
        />
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span>加载数据中...</span>
    </div>

    <div v-if="error" class="error-toast">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import StockSearch from '@/components/StockSearch.vue'
import ReplayControl from '@/components/Replay/ReplayControl.vue'
import MultiReplayLayout from '@/components/Replay/MultiReplayLayout.vue'
import { stockApi, type StockInfo } from '@/api/stock'

interface MinuteData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

interface StockItem {
  info: StockInfo | null
  data: MinuteData[]
}

const startTime = '09:30:00'
const endTime = '15:00:00'

const selectedStocks = ref<StockInfo[]>([])
const replayStocks = ref<StockItem[]>([])
const currentTime = ref(startTime)
const isPlaying = ref(false)
const loading = ref(false)
const error = ref('')
const selectedDate = ref('')
const playSpeed = ref(1)

let playTimer: number | null = null

const STOCKS_KEY = 'replay_stocks'

const saveStocks = () => {
  localStorage.setItem(STOCKS_KEY, JSON.stringify(selectedStocks.value))
}

const loadStocks = async () => {
  const saved = localStorage.getItem(STOCKS_KEY)
  if (!saved) return
  
  try {
    const stocks: StockInfo[] = JSON.parse(saved)
    for (const stock of stocks) {
      selectedStocks.value.push(stock)
      await loadStockData(stock)
    }
  } catch (e) {
    console.error('Failed to load stocks:', e)
  }
}

const onSelectStock = async (code: string) => {
  if (selectedStocks.value.some(s => s.code === code)) {
    showError('该股票已在列表中')
    return
  }

  try {
    const res = await stockApi.getInfo(code)
    if (res.data) {
      selectedStocks.value.push(res.data)
      saveStocks()
      await loadStockData(res.data)
    }
  } catch (e: any) {
    showError('获取股票信息失败')
    console.error(e)
  }
}

const loadStockData = async (stock: StockInfo) => {
  if (!selectedDate.value) return

  loading.value = true
  try {
    const res = await stockApi.getMinuteKlines(stock.code, {
      date: selectedDate.value.replace(/-/g, ''),
      period: '1'
    })
    
    const data = res.data.map((k: any) => ({
      time: String(k.datetime).slice(11, 19),
      open: k.open,
      high: k.high,
      low: k.low,
      close: k.close,
      volume: k.volume,
      amount: k.amount
    }))

    const existingIndex = replayStocks.value.findIndex(
      s => s.info?.code === stock.code
    )

    const newStockItem: StockItem = {
      info: stock,
      data: data
    }

    if (existingIndex >= 0) {
      replayStocks.value[existingIndex] = newStockItem
    } else {
      replayStocks.value.push(newStockItem)
    }
  } catch (e: any) {
    showError(`加载 ${stock.name} 数据失败`)
    console.error(e)
  } finally {
    loading.value = false
  }
}

const removeSelectedStock = (code: string) => {
  selectedStocks.value = selectedStocks.value.filter(s => s.code !== code)
  replayStocks.value = replayStocks.value.filter(s => s.info?.code !== code)
  saveStocks()
}

const onRemoveStock = (index: number) => {
  const stock = replayStocks.value[index]
  if (stock?.info) {
    removeSelectedStock(stock.info.code)
  }
}

const onTimeUpdate = (time: string) => {
  currentTime.value = time
}

const onPlayingUpdate = (playing: boolean) => {
  isPlaying.value = playing
}

const onDateChange = async (date: string) => {
  selectedDate.value = date
  for (const stock of selectedStocks.value) {
    await loadStockData(stock)
  }
}

const onSpeedChange = (speed: number) => {
  playSpeed.value = speed
  if (isPlaying.value) {
    stopPlay()
    startPlay()
  }
}

const startPlay = () => {
  if (playTimer) return
  
  const interval = 1000 / playSpeed.value
  playTimer = window.setInterval(() => {
    const [h, m, s] = currentTime.value.split(':').map(Number)
    let totalSeconds = h * 3600 + m * 60 + s
    totalSeconds += 60

    if (totalSeconds >= 15 * 3600) {
      stopPlay()
      isPlaying.value = false
      return
    }

    if (totalSeconds >= 12 * 3600 && totalSeconds < 13 * 3600) {
      totalSeconds = 13 * 3600
    }

    const newH = Math.floor(totalSeconds / 3600)
    const newM = Math.floor((totalSeconds % 3600) / 60)
    const newS = totalSeconds % 60
    currentTime.value = `${newH.toString().padStart(2, '0')}:${newM.toString().padStart(2, '0')}:${newS.toString().padStart(2, '0')}`
  }, interval)
}

const stopPlay = () => {
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
}

const showError = (msg: string) => {
  error.value = msg
  setTimeout(() => error.value = '', 3000)
}

watch(isPlaying, (playing) => {
  if (playing) {
    startPlay()
  } else {
    stopPlay()
  }
})

watch(() => selectedStocks.value.length, () => {
  while (replayStocks.value.length > selectedStocks.value.length) {
    replayStocks.value.pop()
  }
})

onMounted(async () => {
  const today = new Date()
  selectedDate.value = today.toISOString().split('T')[0]
  await loadStocks()
})

onUnmounted(() => {
  stopPlay()
})
</script>

<style scoped>
.replay-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.replay-header {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.search-section {
  margin-bottom: 12px;
}

.selected-stocks {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-stocks .label {
  font-size: 13px;
  color: #666;
  flex-shrink: 0;
}

.stock-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stock-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 4px;
  font-size: 13px;
}

.stock-tag button {
  background: none;
  border: none;
  color: #409eff;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
  margin-left: 2px;
}

.stock-tag button:hover {
  color: #66b1ff;
}

.empty-hint {
  color: #999;
  font-size: 13px;
}

.replay-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.control-section {
  flex-shrink: 0;
}

.charts-section {
  flex: 1;
  min-height: 0;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  z-index: 1000;
  color: #fff;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #f56c6c;
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
</style>
