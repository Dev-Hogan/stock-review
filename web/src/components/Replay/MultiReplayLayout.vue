<template>
  <div class="multi-replay-layout">
    <div class="layout-header">
      <div class="layout-selector">
        <span>布局：</span>
        <button
          v-for="layout in layouts"
          :key="layout.key"
          :class="['layout-btn', { active: currentLayout === layout.key }]"
          @click="currentLayout = layout.key"
          :title="layout.label"
        >
          {{ layout.label }}
        </button>
      </div>
    </div>

    <div class="charts-grid" :class="`layout-${currentLayout}`">
      <div
        v-for="(stock, index) in props.stocks"
        :key="stock.info?.code"
        class="chart-cell"
      >
        <ReplayChart
          :stockInfo="stock.info"
          :minuteData="stock.data"
          :currentTime="currentTime"
        />
        <button
          class="btn-remove"
          @click="onRemoveStock(index)"
          title="移除"
        >
          ×
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import ReplayChart from './ReplayChart.vue'

interface StockInfo {
  code: string
  name: string
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

interface StockItem {
  info: StockInfo | null
  data: MinuteData[]
}

const props = defineProps<{
  stocks: StockItem[]
  currentTime: string
}>()

const emit = defineEmits<{
  (e: 'removeStock', index: number): void
}>()

const layouts = [
  { key: '1x1', label: '1×1', cols: 1, rows: 1 },
  { key: '2x1', label: '2×1', cols: 2, rows: 1 },
  { key: '2x2', label: '2×2', cols: 2, rows: 2 },
  { key: '3x2', label: '3×2', cols: 3, rows: 2 }
]

const currentLayout = ref('2x2')

const onRemoveStock = (index: number) => {
  emit('removeStock', index)
}
</script>

<style scoped>
.multi-replay-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 10px;
}

.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 0 4px;
}

.layout-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.layout-selector span {
  font-size: 13px;
  color: #666;
}

.layout-btn {
  padding: 4px 10px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.layout-btn:hover {
  border-color: #409eff;
}

.layout-btn.active {
  background: #409eff;
  color: #fff;
  border-color: #409eff;
}

.charts-grid {
  flex: 1;
  display: grid;
  gap: 10px;
  min-height: 0;
}

.charts-grid.layout-1x1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}

.charts-grid.layout-2x1 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: 1fr;
}

.charts-grid.layout-2x2 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

.charts-grid.layout-3x2 {
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

.chart-cell {
  position: relative;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  min-height: 200px;
}

.btn-remove {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 10;
}

.chart-cell:hover .btn-remove {
  opacity: 1;
}

.btn-remove:hover {
  background: rgba(0, 0, 0, 0.7);
}
</style>
