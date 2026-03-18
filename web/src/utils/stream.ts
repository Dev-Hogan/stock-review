/**
 * 流式请求工具
 * 支持 SSE (Server-Sent Events) 格式的流式响应
 */

const API_BASE = '' // 可配置 baseURL

export interface StreamData {
  content?: string
  error?: string
  [key: string]: any
}

export interface StreamOptions {
  onChunk: (data: StreamData) => void
  onComplete?: () => void
  onError?: (error: Error) => void
}

export async function streamRequest(
  url: string,
  options: {
    method?: string
    headers?: Record<string, string>
    body?: any
  } & StreamOptions
): Promise<void> {
  const { onChunk, onComplete, onError, method = 'POST', headers = {}, body } = options
  const fullUrl = url.startsWith('http') ? url : API_BASE + url
  
  try {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      },
      body: body ? JSON.stringify(body) : undefined
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }
    
    if (!response.body) {
      throw new Error('No response body')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        onComplete?.()
        break
      }
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      
      // 保留最后一行（可能不完整）
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          
          if (dataStr === '[DONE]') {
            onComplete?.()
            return
          }
          
          try {
            const data = JSON.parse(dataStr)
            onChunk(data)
          } catch (e) {
            console.error('Parse error:', e, 'line:', line)
          }
        }
      }
    }
  } catch (error) {
    onError?.(error instanceof Error ? error : new Error(String(error)))
    throw error
  }
}