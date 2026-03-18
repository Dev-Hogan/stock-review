import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { stockApi, type StockInfo, type RealtimeQuote } from '@/api/stock'

export const useStockStore = defineStore('stock', () => {
  const stocks = ref<StockInfo[]>([])
  const selectedStock = ref<StockInfo | null>(null)
  const watchlist = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function searchStocks(keyword: string) {
    if (!keyword) {
      stocks.value = []
      return
    }
    loading.value = true
    error.value = null
    try {
      const res = await stockApi.search(keyword)
      stocks.value = res.data
    } catch (e) {
      error.value = '搜索失败'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function selectStock(code: string) {
    loading.value = true
    error.value = null
    try {
      const res = await stockApi.getInfo(code)
      selectedStock.value = res.data
    } catch (e) {
      error.value = '获取股票信息失败'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  function addToWatchlist(code: string) {
    if (!watchlist.value.includes(code)) {
      watchlist.value.push(code)
      localStorage.setItem('watchlist', JSON.stringify(watchlist.value))
    }
  }

  function removeFromWatchlist(code: string) {
    watchlist.value = watchlist.value.filter(c => c !== code)
    localStorage.setItem('watchlist', JSON.stringify(watchlist.value))
  }

  function loadWatchlist() {
    const saved = localStorage.getItem('watchlist')
    if (saved) {
      watchlist.value = JSON.parse(saved)
    }
  }

  return {
    stocks,
    selectedStock,
    watchlist,
    loading,
    error,
    searchStocks,
    selectStock,
    addToWatchlist,
    removeFromWatchlist,
    loadWatchlist
  }
})
