<template>
  <div class="app-container">
    <header class="app-header">
      <h1>Stock Review</h1>
      <nav class="main-nav">
        <router-link to="/screen">股票筛选</router-link>
        <router-link to="/trading">交易看板</router-link>
        <router-link to="/replay">盘口回放</router-link>
        <router-link to="/settings">系统设置</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.app-header {
  background: #1a1a2e;
  color: white;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.app-header h1 {
  font-size: 20px;
}

.main-nav {
  display: flex;
  gap: 20px;
}

.main-nav a {
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background 0.3s;
}

.main-nav a:hover {
  background: rgba(255, 255, 255, 0.1);
}

.main-nav a.router-link-active {
  background: #007bff;
}

.app-main {
  flex: 1;
  overflow: auto;
  background: #f5f5f5;
}
</style>
