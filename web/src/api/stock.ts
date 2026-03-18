import api from './index'

export interface StockInfo {
  code: string
  name: string
  industry?: string
  market_cap?: number
  open?: number
  high?: number
  low?: number
  close?: number
  volume?: number
  amount?: number
  price_change?: number
  change_percent?: number
}

export interface DailyKline {
  stock_code: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

export interface MinuteKline {
  stock_code: string
  datetime: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

export interface RealtimeQuote {
  code: string
  name: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  price_change: number
  change_percent: number
}

export const stockApi = {
  search(keyword: string, limit = 20) {
    return api.get<StockInfo[]>('/data/stocks/search', { params: { keyword, limit } })
  },

  getInfo(code: string) {
    return api.get<StockInfo>(`/data/stocks/${code}/info`)
  },

  getDailyKlines(code: string, params?: { start_date?: string; end_date?: string; limit?: number }) {
    return api.get<DailyKline[]>(`/data/stocks/${code}/daily`, { params })
  },

  getMinuteKlines(code: string, params?: { date?: string; period?: string }) {
    return api.get<MinuteKline[]>(`/data/stocks/${code}/minute`, { params })
  },

  getRealtimeQuote(code: string) {
    return api.get<RealtimeQuote>(`/data/stocks/${code}/realtime`)
  },

  refreshList() {
    return api.post('/data/stocks/refresh-list')
  },

  updateStock(code: string, includeMinute = true) {
    return api.post(`/data/stocks/${code}/update`, null, { params: { include_minute: includeMinute } })
  }
}
