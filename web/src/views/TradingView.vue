<template>
  <div class="trading-view">
    <Transition name="slide">
      <div v-if="showMsg" :class="['msg-bar', showMsg.type]">
        {{ showMsg.text }}
      </div>
    </Transition>
    <div class="layout">
      <aside class="left-panel">
        <div class="refresh-bar">
          <span>自选股</span>
          <button class="refresh-btn" @click="refreshStockList" :disabled="refreshing">
            {{ refreshing ? '刷新中...' : '刷新列表' }}
          </button>
        </div>
        <StockSearch
          :watchlist="watchlistCodes"
          @select="onSelectStock"
          @add-watchlist="addToWatchlist"
          @remove-watchlist="removeFromWatchlist"
        />
        <WatchList
          :watchlist="watchlistStocks"
          :selected-code="selectedStock?.code"
          @select="onSelectStock"
          @remove="removeFromWatchlist"
        />
      </aside>

      <main class="main-panel">
        <div v-if="selectedStock" class="stock-detail">
          <div class="stock-header">
            <div class="stock-title">
              <h2>{{ selectedStock.name }}</h2>
              <span class="stock-code">{{ selectedStock.code }}</span>
            </div>
            <div class="stock-quote">
              <span class="price">{{ selectedStock.close?.toFixed(2) }}</span>
              <span
                class="change"
                :class="(selectedStock.change_percent || 0) >= 0 ? 'up' : 'down'"
              >
                {{ (selectedStock.change_percent || 0) >= 0 ? '+' : '' }}{{ selectedStock.change_percent?.toFixed(2) }}%
              </span>
            </div>
          </div>

          <div class="chart-container">
            <div ref="chartRef" class="kline-chart"></div>
          </div>

          <div class="chart-controls">
            <button
              v-for="p in periods"
              :key="p.value"
              :class="{ active: currentPeriod === p.value }"
              @click="changePeriod(p.value)"
            >
              {{ p.label }}
            </button>
          </div>
        </div>
        <div v-else class="no-selection">
          <p>请搜索并选择一只股票</p>
        </div>
      </main>

      <aside class="right-panel">
        <div class="panel-section">
          <h3>实时行情</h3>
          <div v-if="selectedStock" class="quote-details">
            <div class="quote-row header-row">
              <span class="stock-name-lg">{{ selectedStock.name }}</span>
              <span class="stock-code-sm">{{ selectedStock.code }}</span>
            </div>
            <div class="quote-row price-row">
              <span class="price-lg">{{ selectedStock.close?.toFixed(2) }}</span>
              <span :class="['change-lg', (selectedStock.change_percent || 0) >= 0 ? 'up' : 'down']">
                {{ (selectedStock.change_percent || 0) >= 0 ? '+' : '' }}{{ selectedStock.change_percent?.toFixed(2) }}%
              </span>
            </div>
            <div class="divider"></div>
            <div class="quote-row">
              <span>开盘</span>
              <span>{{ selectedStock.open?.toFixed(2) }}</span>
            </div>
            <div class="quote-row">
              <span>最高</span>
              <span class="up">{{ selectedStock.high?.toFixed(2) }}</span>
            </div>
            <div class="quote-row">
              <span>最低</span>
              <span class="down">{{ selectedStock.low?.toFixed(2) }}</span>
            </div>
            <div class="quote-row">
              <span>成交量</span>
              <span>{{ formatVolume(selectedStock.volume) }}</span>
            </div>
            <div class="quote-row">
              <span>成交额</span>
              <span>{{ formatAmount(selectedStock.amount) }}</span>
            </div>
            <div class="quote-row">
              <span>行业</span>
              <span>{{ selectedStock.industry || '-' }}</span>
            </div>
            <div class="quote-row">
              <span>市值</span>
              <span>{{ formatAmount(selectedStock.market_cap) }}</span>
            </div>
          </div>
          <div v-else class="quote-empty">
            选择股票查看详情
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { createChart, type IChartApi } from 'lightweight-charts'
import StockSearch from '@/components/StockSearch.vue'
import WatchList from '@/components/WatchList.vue'
import { stockApi, type StockInfo } from '@/api/stock'

const showMsg = ref<{ text: string; type: 'success' | 'error' } | null>(null)

const watchlistCodes = ref<string[]>([])
const watchlistStocks = ref<StockInfo[]>([])
const selectedStock = ref<StockInfo | null>(null)
const chartRef = ref<HTMLElement | null>(null)
const refreshing = ref(false)
let chart: IChartApi | null = null

const periods = [
  { label: '日K', value: 'daily' },
  { label: '1分钟', value: '1' },
  { label: '5分钟', value: '5' },
  { label: '15分钟', value: '15' },
  { label: '30分钟', value: '30' },
  { label: '60分钟', value: '60' }
]
const currentPeriod = ref('daily')

onMounted(() => {
  loadWatchlist()
  initChart()
})

async function refreshStockList() {
  refreshing.value = true
  try {
    const res = await stockApi.refreshList()
    showMsg.value = { text: `股票列表刷新成功！共 ${res.data.count} 只股票`, type: 'success' }
    setTimeout(() => showMsg.value = null, 3000)
  } catch (e: any) {
    console.error('Refresh failed:', e)
    const msg = e.response?.data?.detail || '刷新失败'
    showMsg.value = { text: msg, type: 'error' }
    setTimeout(() => showMsg.value = null, 5000)
  } finally {
    refreshing.value = false
  }
}

function loadWatchlist() {
  const saved = localStorage.getItem('watchlist')
  if (saved) {
    watchlistCodes.value = JSON.parse(saved)
    loadWatchlistStocks()
  }
}

async function loadWatchlistStocks() {
  watchlistStocks.value = []
  for (const code of watchlistCodes.value) {
    try {
      const res = await stockApi.getInfo(code)
      watchlistStocks.value.push(res.data)
    } catch (e) {
      console.error(`Failed to load ${code}:`, e)
    }
  }
}

function initChart() {
  if (!chartRef.value) return
  chart = createChart(chartRef.value, {
    width: chartRef.value.clientWidth,
    height: 400,
    layout: {
      background: { color: '#ffffff' },
      textColor: '#333'
    },
    grid: {
      vertLines: { color: '#f0f0f0' },
      horzLines: { color: '#f0f0f0' }
    }
  })
}

function calculateMA(data: any[], period: number): { time: any; value: number }[] {
  const result: { time: any; value: number }[] = []
  for (let i = period - 1; i < data.length; i++) {
    let sum = 0
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close
    }
    result.push({
      time: data[i].time,
      value: parseFloat((sum / period).toFixed(2))
    })
  }
  return result
}

async function loadKlineData() {
  if (!selectedStock.value || !chartRef.value) return

  const code = selectedStock.value.code
  let klineData: any[] = []

  if (currentPeriod.value === 'daily') {
    const res = await stockApi.getDailyKlines(code, { limit: 250 })
    klineData = res.data.map(k => ({
      time: k.date.replace(/-/g, '') as any,
      open: k.open,
      high: k.high,
      low: k.low,
      close: k.close
    }))
  } else {
    const res = await stockApi.getMinuteKlines(code, { period: currentPeriod.value })
    klineData = res.data.map(k => ({
      time: k.datetime.replace('T', ' ').slice(0, 16) as any,
      open: k.open,
      high: k.high,
      low: k.low,
      close: k.close
    }))
  }

  chart.remove()
  chart = createChart(chartRef.value, {
    width: chartRef.value.clientWidth,
    height: 400,
    layout: {
      background: { color: '#ffffff' },
      textColor: '#333333'
    },
    grid: {
      vertLines: { color: '#f0f0f0' },
      horzLines: { color: '#f0f0f0' }
    },
    timeScale: {
      borderColor: '#e0e0e0'
    }
  })

  const candlestickSeries = chart.addCandlestickSeries({
    upColor: '#ef5350',
    downColor: '#26a69a',
    borderUpColor: '#ef5350',
    borderDownColor: '#26a69a',
    wickUpColor: '#ef5350',
    wickDownColor: '#26a69a'
  })
  candlestickSeries.setData(klineData)

  const ma5 = calculateMA(klineData, 5)
  const ma10 = calculateMA(klineData, 10)
  const ma20 = calculateMA(klineData, 20)

  chart.addLineSeries({
    color: '#2196f3',
    lineWidth: 1,
    title: 'MA5'
  }).setData(ma5)

  chart.addLineSeries({
    color: '#ff9800',
    lineWidth: 1,
    title: 'MA10'
  }).setData(ma10)

  chart.addLineSeries({
    color: '#9c27b0',
    lineWidth: 1,
    title: 'MA20'
  }).setData(ma20)

  chart.timeScale().fitContent()
}

async function onSelectStock(code: string) {
  try {
    const res = await stockApi.getInfo(code)
    selectedStock.value = res.data
    await nextTick()
    await loadKlineData()
  } catch (e) {
    console.error('Failed to select stock:', e)
  }
}

function addToWatchlist(code: string) {
  if (!watchlistCodes.value.includes(code)) {
    watchlistCodes.value.push(code)
    localStorage.setItem('watchlist', JSON.stringify(watchlistCodes.value))
    stockApi.getInfo(code).then(res => {
      watchlistStocks.value.push(res.data)
    })
  }
}

function removeFromWatchlist(code: string) {
  watchlistCodes.value = watchlistCodes.value.filter(c => c !== code)
  watchlistStocks.value = watchlistStocks.value.filter(s => s.code !== code)
  localStorage.setItem('watchlist', JSON.stringify(watchlistCodes.value))
}

async function changePeriod(period: string) {
  currentPeriod.value = period
  await loadKlineData()
}

function formatVolume(v: number | undefined) {
  if (!v) return '-'
  if (v >= 100000000) return (v / 100000000).toFixed(2) + '亿'
  if (v >= 10000) return (v / 10000).toFixed(2) + '万'
  return v.toString()
}

function formatAmount(a: number | undefined) {
  if (!a) return '-'
  if (a >= 100000000) return (a / 100000000).toFixed(2) + '亿'
  if (a >= 10000) return (a / 10000).toFixed(2) + '万'
  return a.toString()
}
</script>

<style scoped>
.trading-view {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.layout {
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  gap: 10px;
  height: 100%;
  padding: 10px;
}

.left-panel,
.right-panel {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;
}

.refresh-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.refresh-bar span {
  font-weight: bold;
  font-size: 14px;
}

.refresh-btn {
  padding: 4px 12px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.refresh-btn:hover {
  background: #66b1ff;
}

.refresh-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.main-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stock-detail {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stock-title h2 {
  margin: 0;
  font-size: 20px;
}

.stock-code {
  color: #999;
  font-size: 13px;
}

.stock-quote {
  text-align: right;
}

.price {
  font-size: 24px;
  font-weight: bold;
  margin-right: 10px;
}

.change {
  font-size: 16px;
}

.change.up {
  color: #f56c6c;
}

.change.down {
  color: #67c23a;
}

.chart-container {
  flex: 1;
  min-height: 300px;
}

.kline-chart {
  width: 100%;
  height: 100%;
}

.chart-controls {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.chart-controls button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}

.chart-controls button.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.no-selection {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 8px;
  color: #999;
}

.panel-section h3 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #333;
}

.quote-details {
  font-size: 13px;
}

.quote-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
}

.quote-row span:first-child {
  color: #999;
}

.quote-row span:last-child {
  font-weight: 500;
}

.quote-row .up {
  color: #f56c6c;
}

.quote-row .down {
  color: #67c23a;
}

.quote-empty {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.header-row {
  flex-direction: column;
  border-bottom: none;
  padding-bottom: 0;
}

.stock-name-lg {
  font-size: 18px;
  font-weight: bold;
}

.stock-code-sm {
  font-size: 12px;
  color: #999;
}

.price-row {
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.price-lg {
  font-size: 28px;
  font-weight: bold;
  margin-right: 8px;
}

.change-lg {
  font-size: 16px;
}

.change-lg.up {
  color: #f56c6c;
}

.change-lg.down {
  color: #67c23a;
}

.divider {
  height: 1px;
  background: #eee;
  margin: 8px 0;
}

.msg-bar {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  z-index: 1000;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.msg-bar.success {
  background: #67c23a;
  color: white;
}

.msg-bar.error {
  background: #f56c6c;
  color: white;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
