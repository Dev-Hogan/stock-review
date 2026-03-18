<template>
  <div class="watch-list">
    <div class="watch-list-header">
      <span>自选股</span>
      <span class="count">{{ watchlist.length }}</span>
    </div>
    <div v-if="watchlist.length === 0" class="watch-list-empty">
      暂无自选股<br />搜索添加
    </div>
    <div v-else class="watch-list-items">
      <div
        v-for="(stock, index) in watchlist"
        :key="stock.code"
        class="watch-list-item"
        :class="{ active: selectedCode === stock.code }"
        @click="$emit('select', stock.code)"
      >
        <div class="stock-info">
          <span class="stock-name">{{ stock.name }}</span>
          <span class="stock-code">{{ stock.code }}</span>
        </div>
        <div class="stock-price" v-if="stock.close">
          <span class="price">{{ stock.close.toFixed(2) }}</span>
          <span
            class="change"
            :class="stock.change_percent >= 0 ? 'up' : 'down'"
          >
            {{ stock.change_percent >= 0 ? '+' : '' }}{{ stock.change_percent?.toFixed(2) }}%
          </span>
        </div>
        <button class="remove-btn" @click.stop="$emit('remove', stock.code)">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { StockInfo } from '@/api/stock'

defineProps<{
  watchlist: StockInfo[]
  selectedCode?: string
}>()

defineEmits<{
  select: [code: string]
  remove: [code: string]
}>()
</script>

<style scoped>
.watch-list {
  background: #fff;
  border-radius: 4px;
  overflow: hidden;
}

.watch-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  font-weight: bold;
  border-bottom: 1px solid #eee;
}

.count {
  background: #409eff;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.watch-list-empty {
  padding: 40px 20px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

.watch-list-items {
  max-height: 400px;
  overflow-y: auto;
}

.watch-list-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  position: relative;
}

.watch-list-item:hover {
  background: #f5f7fa;
}

.watch-list-item.active {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.stock-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-weight: bold;
  font-size: 14px;
}

.stock-code {
  font-size: 11px;
  color: #999;
}

.stock-price {
  text-align: right;
  margin-right: 20px;
}

.price {
  display: block;
  font-weight: bold;
  font-size: 14px;
}

.change {
  font-size: 12px;
}

.change.up {
  color: #f56c6c;
}

.change.down {
  color: #67c23a;
}

.remove-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 18px;
  color: #ccc;
  cursor: pointer;
  display: none;
}

.watch-list-item:hover .remove-btn {
  display: block;
}

.remove-btn:hover {
  color: #f56c6c;
}
</style>
