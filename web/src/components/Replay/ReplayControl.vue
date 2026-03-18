<template>
  <div class="replay-control">
    <div class="control-header">
      <div class="date-picker">
        <label>回放日期：</label>
        <input 
          type="date" 
          v-model="selectedDate" 
          :max="maxDate"
          @change="onDateChange"
        />
      </div>
      <div class="speed-control">
        <label>播放速度：</label>
        <select v-model="speed" @change="onSpeedChange">
          <option :value="0.5">0.5x</option>
          <option :value="1">1x</option>
          <option :value="2">2x</option>
          <option :value="4">4x</option>
          <option :value="8">8x</option>
        </select>
      </div>
    </div>

    <div class="timeline-container">
      <div class="time-display">
        <span class="current-time">{{ formatTime(currentTime) }}</span>
        <span class="separator">/</span>
        <span class="total-time">{{ formatTime(endTime) }}</span>
      </div>

      <div class="progress-container" @click="onProgressClick">
        <div class="progress-bar" ref="progressBar">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            <div class="progress-thumb" :style="{ left: progressPercent + '%' }"></div>
          </div>
          <div class="time-markers">
            <span v-for="marker in timeMarkers" :key="marker.time" 
                  class="marker" 
                  :style="{ left: marker.percent + '%' }">
              {{ marker.label }}
            </span>
          </div>
        </div>
      </div>

      <div class="control-buttons">
        <button class="btn-control" @click="onSkipToStart" title="跳过到开始">
          <span class="icon">⏮</span>
        </button>
        <button class="btn-control btn-play" @click="togglePlay" :title="isPlaying ? '暂停' : '播放'">
          <span class="icon">{{ isPlaying ? '⏸' : '▶' }}</span>
        </button>
        <button class="btn-control" @click="onSkipToEnd" title="跳过到结束">
          <span class="icon">⏭</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'

const props = defineProps<{
  startTime: string
  endTime: string
  currentTime: string
  isPlaying: boolean
}>()

const emit = defineEmits<{
  (e: 'update:currentTime', value: string): void
  (e: 'update:isPlaying', value: boolean): void
  (e: 'dateChange', value: string): void
  (e: 'speedChange', value: number): void
}>()

const selectedDate = ref('')
const speed = ref(1)
const progressBar = ref<HTMLElement | null>(null)

const maxDate = computed(() => {
  const now = new Date()
  return now.toISOString().split('T')[0]
})

const parseTimeToMinutes = (timeStr: string): number => {
  const parts = timeStr.split(':')
  if (parts.length !== 3) return 0
  return parseInt(parts[0]) * 60 + parseInt(parts[1])
}

const totalMinutes = computed(() => {
  return parseTimeToMinutes(props.endTime) - parseTimeToMinutes(props.startTime)
})

const currentMinutes = computed(() => {
  return parseTimeToMinutes(props.currentTime) - parseTimeToMinutes(props.startTime)
})

const progressPercent = computed(() => {
  if (totalMinutes.value === 0) return 0
  return Math.min(100, Math.max(0, (currentMinutes.value / totalMinutes.value) * 100))
})

const timeMarkers = computed(() => {
  const markers = []
  const startH = parseInt(props.startTime.split(':')[0])
  const endH = parseInt(props.endTime.split(':')[0])
  
  for (let h = startH; h <= endH; h += 1) {
    const timeStr = `${h.toString().padStart(2, '0')}:00`
    const mins = parseTimeToMinutes(timeStr) - parseTimeToMinutes(props.startTime)
    const percent = (mins / totalMinutes.value) * 100
    if (percent >= 0 && percent <= 100) {
      markers.push({
        time: timeStr,
        label: timeStr.slice(0, 5),
        percent
      })
    }
  }
  return markers
})

const formatTime = (timeStr: string | undefined): string => {
  if (!timeStr) return '--:--'
  return timeStr.slice(0, 5)
}

const togglePlay = () => {
  emit('update:isPlaying', !props.isPlaying)
}

const onProgressClick = (event: MouseEvent) => {
  if (!progressBar.value) return
  
  const rect = progressBar.value.getBoundingClientRect()
  const percent = (event.clientX - rect.left) / rect.width
  const targetMinutes = Math.round(totalMinutes.value * percent)
  const baseMinutes = parseTimeToMinutes(props.startTime)
  const targetTotalMinutes = baseMinutes + targetMinutes
  
  const hours = Math.floor(targetTotalMinutes / 60)
  const mins = targetTotalMinutes % 60
  const timeStr = `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:00`
  
  emit('update:currentTime', timeStr)
}

const onSkipToStart = () => {
  emit('update:currentTime', props.startTime)
}

const onSkipToEnd = () => {
  emit('update:currentTime', props.endTime)
}

const onDateChange = () => {
  emit('dateChange', selectedDate.value)
}

const onSpeedChange = () => {
  emit('speedChange', speed.value)
}

watch(() => props.currentTime, (newTime) => {
  const datePart = selectedDate.value || maxDate.value
  emit('update:currentTime', newTime)
})
</script>

<style scoped>
.replay-control {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.date-picker,
.speed-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-picker label,
.speed-control label {
  font-size: 13px;
  color: #666;
}

.date-picker input {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.speed-control select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
}

.timeline-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.time-display {
  text-align: center;
  font-size: 14px;
  font-family: monospace;
}

.current-time {
  font-weight: bold;
  color: #409eff;
  font-size: 18px;
}

.separator {
  color: #999;
  margin: 0 8px;
}

.total-time {
  color: #666;
}

.progress-container {
  padding: 8px 0;
  cursor: pointer;
}

.progress-bar {
  position: relative;
  height: 24px;
}

.progress-track {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 4px;
  transform: translateY(-50%);
  background: #e0e0e0;
  border-radius: 2px;
}

.progress-fill {
  height: 100%;
  background: #409eff;
  border-radius: 2px;
  transition: width 0.1s linear;
}

.progress-thumb {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background: #409eff;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  transition: left 0.1s linear;
}

.time-markers {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  height: 20px;
}

.marker {
  position: absolute;
  transform: translateX(-50%);
  font-size: 10px;
  color: #999;
  white-space: nowrap;
}

.control-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 8px;
}

.btn-control {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: #f0f0f0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-control:hover {
  background: #e0e0e0;
}

.btn-control.btn-play {
  width: 50px;
  height: 50px;
  background: #409eff;
  color: white;
}

.btn-control.btn-play:hover {
  background: #66b1ff;
}

.icon {
  font-size: 16px;
}

.btn-control.btn-play .icon {
  font-size: 20px;
}
</style>
