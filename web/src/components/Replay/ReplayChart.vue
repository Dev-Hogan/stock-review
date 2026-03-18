<template>
  <div class="replay-chart" ref="containerRef">
    <div class="chart-header">
      <div class="stock-info" v-if="stockInfo">
        <span class="stock-name">{{ stockInfo.name }}</span>
        <span class="stock-code">{{ stockInfo.code }}</span>
      </div>
      <div class="quote-info" v-if="currentQuote">
        <span class="price" :class="priceColorClass">
          {{ currentQuote.close?.toFixed(2) }}
        </span>
        <span class="change" :class="priceColorClass">
          {{ currentQuote.change >= 0 ? '+' : '' }}{{ currentQuote.change?.toFixed(2) }}
          ({{ currentQuote.changePercent >= 0 ? '+' : '' }}{{ currentQuote.changePercent?.toFixed(2) }}%)
        </span>
      </div>
    </div>
    <div ref="chartRef" class="chart-area"></div>
    <div class="chart-footer" v-if="currentQuote">
      <div class="footer-item">
        <span class="label">开盘</span>
        <span class="value">{{ currentQuote.open?.toFixed(2) }}</span>
      </div>
      <div class="footer-item">
        <span class="label">最高</span>
        <span class="value up">{{ currentQuote.high?.toFixed(2) }}</span>
      </div>
      <div class="footer-item">
        <span class="label">最低</span>
        <span class="value down">{{ currentQuote.low?.toFixed(2) }}</span>
      </div>
      <div class="footer-item">
        <span class="label">成交量</span>
        <span class="value">{{ formatVolume(currentQuote.volume) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { createChart, type IChartApi, type ISeriesApi, type LineData, type Time } from 'lightweight-charts'

interface StockInfo {
  code: string
  name: string
}

interface Quote {
  open: number
  high: number
  low: number
  close: number
  volume: number
  change: number
  changePercent: number
}

interface MinuteData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

const props = defineProps<{
  stockInfo: StockInfo | null
  minuteData: MinuteData[]
  currentTime: string
}>()

const containerRef = ref<HTMLElement | null>(null)
const chartRef = ref<HTMLElement | null>(null)
let chart: IChartApi | null = null
let lineSeries: ISeriesApi<'Line'> | null = null
let areaSeries: ISeriesApi<'Area'> | null = null

const currentQuote = ref<Quote | null>(null)

const priceColorClass = computed(() => {
  if (!currentQuote.value) return ''
  return currentQuote.value.change >= 0 ? 'up' : 'down'
})

const initChart = () => {
  if (!chartRef.value) return
  
  if (chart) {
    chart.remove()
  }

  chart = createChart(chartRef.value, {
    width: chartRef.value.clientWidth,
    height: chartRef.value.clientHeight || 300,
    layout: {
      background: { color: '#ffffff' },
      textColor: '#666666'
    },
    grid: {
      vertLines: { color: '#f0f0f0' },
      horzLines: { color: '#f0f0f0' }
    },
    timeScale: {
      borderColor: '#e0e0e0',
      timeVisible: true,
      secondsVisible: false
    },
    crosshair: {
      mode: 0
    }
  })

  lineSeries = chart.addLineSeries({
    color: '#2196f3',
    lineWidth: 2,
    priceLineVisible: false,
    lastValueVisible: true
  })

  areaSeries = chart.addAreaSeries({
    topColor: 'rgba(33, 150, 243, 0.4)',
    bottomColor: 'rgba(33, 150, 243, 0.0)',
    lineColor: '#2196f3',
    lineWidth: 2,
    priceLineVisible: false,
    lastValueVisible: false
  })

  chart.subscribeCrosshairMove((param) => {
    if (param.time) {
      const data = param.seriesData.get(lineSeries!)
      if (data && 'value' in data) {
        const timeStr = String(param.time)
        const quote = findQuoteAtTime(timeStr)
        if (quote) {
          currentQuote.value = quote
        }
      }
    }
  })
}

const formatMinuteData = () => {
  if (!props.minuteData || props.minuteData.length === 0) return { lineData: [], areaData: [] }

  const lineData: LineData[] = props.minuteData.map(d => ({
    time: d.time.replace(' ', 'T') as Time,
    value: d.close
  }))

  const areaData = lineData.map(d => ({
    time: d.time,
    value: d.value
  }))

  return { lineData, areaData }
}

const findQuoteAtTime = (timeStr: string): Quote | null => {
  if (!props.minuteData || props.minuteData.length === 0) return null

  const targetMinutes = timeToMinutes(timeStr)
  
  for (let i = 0; i < props.minuteData.length; i++) {
    const dataMinutes = timeToMinutes(props.minuteData[i].time)
    if (dataMinutes >= targetMinutes) {
      const d = props.minuteData[i]
      const prevClose = i > 0 ? props.minuteData[i - 1].close : d.open
      const change = d.close - prevClose
      const changePercent = prevClose > 0 ? (change / prevClose) * 100 : 0
      return {
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
        change,
        changePercent
      }
    }
  }
  return null
}

const timeToMinutes = (timeStr: string): number => {
  const parts = timeStr.split(/[:T]/)
  if (parts.length < 2) return 0
  return parseInt(parts[0]) * 60 + parseInt(parts[1])
}

const updateChart = () => {
  if (!chart || !lineSeries || !areaSeries) return

  const { lineData, areaData } = formatMinuteData()
  
  if (lineData.length > 0) {
    lineSeries.setData(lineData)
    areaSeries.setData(areaData)
    chart.timeScale().fitContent()
  }
}

const updateCurrentQuote = () => {
  if (!props.currentTime || !props.minuteData || props.minuteData.length === 0) {
    currentQuote.value = null
    return
  }

  currentQuote.value = findQuoteAtTime(props.currentTime)

  if (chart && lineSeries && currentQuote.value) {
    const timeStr = props.currentTime.replace(' ', 'T')
    chart.setCrosshairPosition(currentQuote.value.close, timeStr as Time, lineSeries)
  }
}

const formatVolume = (v: number | undefined) => {
  if (!v) return '-'
  if (v >= 100000000) return (v / 100000000).toFixed(2) + '亿'
  if (v >= 10000) return (v / 10000).toFixed(2) + '万'
  return v.toString()
}

const handleResize = () => {
  if (chart && containerRef.value) {
    chart.resize(containerRef.value.clientWidth, containerRef.value.clientHeight || 300)
  }
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  initChart()
  
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(containerRef.value)
  }
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

watch(() => props.minuteData, () => {
  updateChart()
}, { deep: true })

watch(() => props.currentTime, () => {
  updateCurrentQuote()
})

watch(() => props.stockInfo, () => {
  if (chart) {
    chart.remove()
    chart = null
  }
  initChart()
  if (props.minuteData.length > 0) {
    updateChart()
  }
})
</script>

<style scoped>
.replay-chart {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.stock-info {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stock-name {
  font-weight: bold;
  font-size: 16px;
}

.stock-code {
  color: #999;
  font-size: 12px;
}

.quote-info {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.price {
  font-size: 20px;
  font-weight: bold;
}

.change {
  font-size: 14px;
}

.price.up,
.change.up {
  color: #f56c6c;
}

.price.down,
.change.down {
  color: #67c23a;
}

.chart-area {
  flex: 1;
  min-height: 200px;
}

.chart-footer {
  display: flex;
  justify-content: space-around;
  padding: 12px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.footer-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.footer-item .label {
  font-size: 11px;
  color: #999;
}

.footer-item .value {
  font-size: 13px;
  font-weight: 500;
}

.footer-item .value.up {
  color: #f56c6c;
}

.footer-item .value.down {
  color: #67c23a;
}
</style>
