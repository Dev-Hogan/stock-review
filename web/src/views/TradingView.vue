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
            <div v-if="tooltipData" class="kline-tooltip">
              <div class="tooltip-date">{{ tooltipData.date }}</div>
              <div class="tooltip-row">
                <span>开盘</span>
                <span>{{ tooltipData.open?.toFixed(2) }}</span>
              </div>
              <div class="tooltip-row">
                <span>开盘涨幅</span>
                <span :class="tooltipData.openChange >= 0 ? 'up' : 'down'">{{ tooltipData.openChange >= 0 ? '+' : '' }}{{ tooltipData.openChange?.toFixed(2) }}%</span>
              </div>
              <div class="tooltip-row">
                <span>最高</span>
                <span class="up">{{ tooltipData.high?.toFixed(2) }}</span>
              </div>
              <div class="tooltip-row">
                <span>最低</span>
                <span class="down">{{ tooltipData.low?.toFixed(2) }}</span>
              </div>
              <div class="tooltip-row">
                <span>收盘</span>
                <span>{{ tooltipData.close?.toFixed(2) }}</span>
              </div>
              <div class="tooltip-row">
                <span>涨幅</span>
                <span :class="tooltipData.changePercent >= 0 ? 'up' : 'down'">{{ tooltipData.changePercent >= 0 ? '+' : '' }}{{ tooltipData.changePercent?.toFixed(2) }}%</span>
              </div>
              <div class="tooltip-row">
                <span>振幅</span>
                <span>{{ tooltipData.amplitude?.toFixed(2) }}%</span>
              </div>
              <div class="tooltip-row">
                <span>成交量</span>
                <span>{{ formatVolume(tooltipData.volume) }}</span>
              </div>
              <div class="tooltip-row">
                <span>成交额</span>
                <span>{{ formatAmount(tooltipData.amount) }}</span>
              </div>
              <div class="tooltip-row">
                <span>换手</span>
                <span>{{ tooltipData.turnover ? tooltipData.turnover.toFixed(2) + '%' : '-' }}</span>
              </div>
              <div class="tooltip-row">
                <span>市值</span>
                <span>{{ formatAmount(tooltipData.marketCap) }}</span>
              </div>
              <div class="tooltip-row">
                <span>MA5</span>
                <span>{{ tooltipData.ma5?.toFixed(2) || '-' }}</span>
              </div>
              <div class="tooltip-row">
                <span>MA10</span>
                <span>{{ tooltipData.ma10?.toFixed(2) || '-' }}</span>
              </div>
              <div class="tooltip-row">
                <span>MA20</span>
                <span>{{ tooltipData.ma20?.toFixed(2) || '-' }}</span>
              </div>
            </div>
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
          <h3>实时行情（暂不需要开发）</h3>
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
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { createChart, type IChartApi, type ISeriesApi } from 'lightweight-charts'
import StockSearch from '@/components/StockSearch.vue'
import WatchList from '@/components/WatchList.vue'
import { stockApi, type StockInfo } from '@/api/stock'

const showMsg = ref<{ text: string; type: 'success' | 'error' } | null>(null)

const watchlistCodes = ref<string[]>([])
const watchlistStocks = ref<StockInfo[]>([])
const selectedStock = ref<StockInfo | null>(null)
const chartRef = ref<HTMLElement | null>(null)
const refreshing = ref(false)
const tooltipData = ref<any>(null)
let chart: IChartApi | null = null
let resizeObserver: ResizeObserver | null = null
let candlestickSeries: ISeriesApi<'Candlestick'> | null = null
let ma5Series: ISeriesApi<'Line'> | null = null
let ma10Series: ISeriesApi<'Line'> | null = null
let ma20Series: ISeriesApi<'Line'> | null = null
let klineDataStore: any[] = []

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

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chart) {
    chart.remove()
    chart = null
  }
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
  if (chart) {
    chart.remove()
  }
  chart = createChart(chartRef.value, {
    width: chartRef.value.clientWidth,
    height: chartRef.value.clientHeight || 400,
    layout: {
      background: { color: '#ffffff' },
      textColor: '#333'
    },
    grid: {
      vertLines: { color: '#f0f0f0' },
      horzLines: { color: '#f0f0f0' }
    },
    timeScale: {
      borderColor: '#e0e0e0',
      timeVisible: false
    }
  })

  resizeObserver = new ResizeObserver(() => {
    if (chart && chartRef.value) {
      chart.resize(chartRef.value.clientWidth, chartRef.value.clientHeight)
    }
  })
  resizeObserver.observe(chartRef.value)
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

function calculateMAAt(data: any[], idx: number, period: number): number | null {
  if (idx < period - 1) return null
  let sum = 0
  for (let j = 0; j < period; j++) {
    sum += data[idx - j].close
  }
  return parseFloat((sum / period).toFixed(2))
}

async function loadKlineData() {
  if (!selectedStock.value || !chartRef.value) return

  const code = selectedStock.value.code
  let klineData: any[] = []

  if (currentPeriod.value === 'daily') {
    const res = await stockApi.getDailyKlines(code, { limit: 250 })
    const seen = new Set()
    klineData = []
    for (const k of res.data) {
      const dateStr = String(k.date).slice(0, 10)
      if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) continue
      if (seen.has(dateStr)) continue
      seen.add(dateStr)
      klineData.push({
        time: dateStr,
        open: k.open,
        high: k.high,
        low: k.low,
        close: k.close,
        volume: k.volume,
        amount: k.amount,
        turnover: k.turnover,
        date: dateStr
      })
    }
    klineData.sort((a, b) => a.time.localeCompare(b.time))
    klineDataStore = [...klineData]
  } else {
    const res = await stockApi.getMinuteKlines(code, { period: currentPeriod.value })
    klineData = res.data
      .map(k => ({
        time: String(k.datetime).replace('T', ' ').slice(0, 16),
        open: k.open,
        high: k.high,
        low: k.low,
        close: k.close,
        volume: k.volume,
        amount: k.amount,
        date: String(k.datetime).slice(0, 16)
      }))
      .sort((a, b) => a.time.localeCompare(b.time))
    klineDataStore = [...klineData]
  }

  if (!chart || !chartRef.value) {
    initChart()
  }
  if (!chart) return

  const containerWidth = chartRef.value.clientWidth
  const containerHeight = chartRef.value.clientHeight || 500
  chart.resize(containerWidth, containerHeight)

  chart.timeScale().resetTimeScale()

  if (candlestickSeries) chart.removeSeries(candlestickSeries)
  if (ma5Series) chart.removeSeries(ma5Series)
  if (ma10Series) chart.removeSeries(ma10Series)
  if (ma20Series) chart.removeSeries(ma20Series)

  const ma5 = calculateMA(klineData, 5)
  const ma10 = calculateMA(klineData, 10)
  const ma20 = calculateMA(klineData, 20)

  candlestickSeries = chart.addCandlestickSeries({
    upColor: '#ef5350',
    downColor: '#26a69a',
    borderUpColor: '#ef5350',
    borderDownColor: '#26a69a',
    wickUpColor: '#ef5350',
    wickDownColor: '#26a69a'
  })
  candlestickSeries.setData(klineData)

  ma5Series = chart.addLineSeries({
    color: '#2196f3',
    lineWidth: 1,
    title: 'MA5'
  })
  ma5Series.setData(ma5)

  ma10Series = chart.addLineSeries({
    color: '#ff9800',
    lineWidth: 1,
    title: 'MA10'
  })
  ma10Series.setData(ma10)

  ma20Series = chart.addLineSeries({
    color: '#9c27b0',
    lineWidth: 1,
    title: 'MA20'
  })
  ma20Series.setData(ma20)

  chart.timeScale().fitContent()
  chart.timeScale().scrollToRealTime()

  chart.subscribeCrosshairMove((param) => {
    if (!param.time || !param.seriesData.size) {
      tooltipData.value = null
      return
    }
    
    const candleData = param.seriesData.get(candlestickSeries!)
    if (!candleData || !('open' in candleData)) {
      tooltipData.value = null
      return
    }

    const data = candleData as any
    const currentTime = typeof param.time === 'string' ? param.time : String(param.time)
    const idx = klineDataStore.findIndex(k => k.time === currentTime)
    const prevKline = idx > 0 ? klineDataStore[idx - 1] : null
    const prevClose = prevKline ? prevKline.close : data.close
    
    const change = prevClose > 0 ? data.close - prevClose : 0
    const changePercent = prevClose > 0 ? (change / prevClose) * 100 : 0
    const openChange = prevClose > 0 ? ((data.open - prevClose) / prevClose) * 100 : 0
    const amplitude = prevClose > 0 ? ((data.high - data.low) / prevClose) * 100 : 0
    
    tooltipData.value = {
      date: currentTime,
      open: data.open,
      high: data.high,
      low: data.low,
      close: data.close,
      volume: idx >= 0 ? klineDataStore[idx].volume : 0,
      amount: idx >= 0 ? klineDataStore[idx].amount : 0,
      turnover: idx >= 0 ? klineDataStore[idx].turnover : null,
      change: change,
      changePercent: changePercent,
      openChange: openChange,
      amplitude: amplitude,
      marketCap: selectedStock.value?.market_cap,
      ma5: idx >= 4 ? calculateMAAt(klineDataStore, idx, 5) : null,
      ma10: idx >= 9 ? calculateMAAt(klineDataStore, idx, 10) : null,
      ma20: idx >= 19 ? calculateMAAt(klineDataStore, idx, 20) : null
    }
  })
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
  min-height: 500px;
  height: 500px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.kline-chart {
  width: 100%;
  flex: 1;
  min-height: 500px;
}

.kline-tooltip {
  position: absolute;
  top: 10px;
  left: 70px;
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  z-index: 100;
  pointer-events: none;
  min-width: 180px;
}

.kline-tooltip .tooltip-date {
  font-weight: bold;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #444;
}

.kline-tooltip .tooltip-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
}

.kline-tooltip .tooltip-row span:first-child {
  color: #999;
  margin-right: 12px;
}

.kline-tooltip .tooltip-row span:last-child {
  font-weight: 500;
}

.kline-tooltip .up {
  color: #f56c6c;
}

.kline-tooltip .down {
  color: #67c23a;
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
