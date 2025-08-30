<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-image">
        <img src="/404.svg" alt="404" />
      </div>
      <div class="error-info">
        <h1>404</h1>
        <h2>页面不存在</h2>
        <p>抱歉，您访问的页面不存在或已被删除</p>
        <div class="error-actions">
          <el-button type="primary" @click="goHome">
            返回首页
          </el-button>
          <el-button @click="goBack">
            返回上页
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style lang="scss" scoped>
.error-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.error-content {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 10px;
  padding: 40px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  max-width: 600px;
}

.error-image {
  margin-right: 40px;
  
  img {
    width: 200px;
    height: 200px;
  }
}

.error-info {
  h1 {
    font-size: 72px;
    font-weight: bold;
    color: #409eff;
    margin: 0;
    line-height: 1;
  }
  
  h2 {
    font-size: 24px;
    color: #303133;
    margin: 10px 0;
  }
  
  p {
    font-size: 16px;
    color: #606266;
    margin-bottom: 30px;
  }
  
  .error-actions {
    .el-button {
      margin-right: 15px;
    }
  }
}

@media (max-width: 768px) {
  .error-content {
    flex-direction: column;
    text-align: center;
    padding: 30px 20px;
  }
  
  .error-image {
    margin-right: 0;
    margin-bottom: 30px;
    
    img {
      width: 150px;
      height: 150px;
    }
  }
  
  .error-info {
    h1 {
      font-size: 48px;
    }
  }
}
</style>
