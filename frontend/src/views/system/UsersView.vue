<template>
  <div class="users-container">
    <div class="app-container">
      <div class="filter-container">
        <el-input
          v-model="listQuery.username"
          placeholder="用户名"
          style="width: 200px"
          class="filter-item"
          @keyup.enter="handleFilter"
        />
        <el-select
          v-model="listQuery.is_active"
          placeholder="状态"
          clearable
          style="width: 120px"
          class="filter-item"
        >
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
        <el-button
          class="filter-item"
          type="primary"
          @click="handleFilter"
        >
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button
          class="filter-item"
          style="margin-left: 10px"
          type="primary"
          @click="handleCreate"
        >
          <el-icon><Plus /></el-icon>
          添加用户
        </el-button>
      </div>

      <el-table
        :key="tableKey"
        v-loading="listLoading"
        :data="list"
        border
        fit
        highlight-current-row
        style="width: 100%"
      >
        <el-table-column label="ID" prop="id" sortable="custom" align="center" width="80" />
        <el-table-column label="用户名" prop="username" width="150px" align="center" />
        <el-table-column label="昵称" prop="nickname" width="150px" align="center" />
        <el-table-column label="邮箱" prop="email" width="200px" align="center" />
        <el-table-column label="手机号" prop="phone" width="150px" align="center" />
        <el-table-column label="状态" class-name="status-col" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="200px" align="center">
          <template #default="{ row }">
            <el-tag
              v-for="role in row.roles_info"
              :key="role.id"
              size="small"
              style="margin-right: 5px"
            >
              {{ role.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="150px" align="center">
          <template #default="{ row }">
            <span>{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="230" class-name="small-padding fixed-width">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleUpdate(row)">
              编辑
            </el-button>
            <el-button
              v-if="row.is_active"
              size="small"
              type="danger"
              @click="handleModifyStatus(row, false)"
            >
              禁用
            </el-button>
            <el-button
              v-else
              size="small"
              type="success"
              @click="handleModifyStatus(row, true)"
            >
              启用
            </el-button>
            <el-button size="small" type="warning" @click="handleResetPassword(row)">
              重置密码
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container" v-show="total > 0">
        <el-pagination
          v-model:current-page="listQuery.page"
          v-model:page-size="listQuery.limit"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="getList"
          @current-change="getList"
        />
      </div>

      <el-dialog :title="textMap[dialogStatus]" v-model="dialogFormVisible">
        <el-form
          ref="dataForm"
          :rules="rules"
          :model="temp"
          label-position="left"
          label-width="100px"
          style="width: 400px; margin-left: 50px"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="temp.username" :disabled="dialogStatus === 'update'" />
          </el-form-item>
          <el-form-item label="昵称" prop="nickname">
            <el-input v-model="temp.nickname" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="temp.email" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="temp.phone" />
          </el-form-item>
          <el-form-item v-if="dialogStatus === 'create'" label="密码" prop="password">
            <el-input v-model="temp.password" type="password" />
          </el-form-item>
          <el-form-item label="状态">
            <el-switch v-model="temp.is_active" />
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="temp.roles" multiple placeholder="请选择角色">
              <el-option
                v-for="role in roleOptions"
                :key="role.id"
                :label="role.name"
                :value="role.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click="dialogFormVisible = false">
            取消
          </el-button>
          <el-button type="primary" @click="dialogStatus === 'create' ? createData() : updateData()">
            确认
          </el-button>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/date'
import { systemApi } from '@/services/api'

// 响应式数据
const tableKey = ref(0)
const list = ref([])
const total = ref(0)
const listLoading = ref(true)
const dialogFormVisible = ref(false)
const dialogStatus = ref('')
const roleOptions = ref([])

const listQuery = reactive({
  page: 1,
  limit: 20,
  username: '',
  is_active: undefined
})

const temp = reactive({
  id: undefined,
  username: '',
  nickname: '',
  email: '',
  phone: '',
  password: '',
  is_active: true,
  roles: []
})

const textMap = {
  update: '编辑用户',
  create: '创建用户'
}

const rules = {
  username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
  nickname: [{ required: true, message: '昵称不能为空', trigger: 'blur' }],
  email: [
    { required: true, message: '邮箱不能为空', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [{ required: true, message: '密码不能为空', trigger: 'blur' }]
}

// 方法
const getList = async () => {
  listLoading.value = true
  try {
    const response = await systemApi.getUsers(listQuery)
    list.value = response.results || response
    total.value = response.count || list.value.length
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  }
  listLoading.value = false
}

const getRoles = async () => {
  try {
    const response = await systemApi.getRoles()
    roleOptions.value = response.results || response
  } catch (error) {
    console.error('获取角色列表失败:', error)
  }
}

const handleFilter = () => {
  listQuery.page = 1
  getList()
}

const resetTemp = () => {
  Object.assign(temp, {
    id: undefined,
    username: '',
    nickname: '',
    email: '',
    phone: '',
    password: '',
    is_active: true,
    roles: []
  })
}

const handleCreate = () => {
  resetTemp()
  dialogStatus.value = 'create'
  dialogFormVisible.value = true
}

const handleUpdate = (row: any) => {
  Object.assign(temp, {
    ...row,
    roles: row.roles_info?.map((role: any) => role.id) || []
  })
  dialogStatus.value = 'update'
  dialogFormVisible.value = true
}

const createData = async () => {
  try {
    await systemApi.createUser(temp)
    ElMessage.success('用户创建成功')
    dialogFormVisible.value = false
    getList()
  } catch (error) {
    console.error('创建用户失败:', error)
    ElMessage.error('创建用户失败')
  }
}

const updateData = async () => {
  try {
    await systemApi.updateUser(temp.id, temp)
    ElMessage.success('用户更新成功')
    dialogFormVisible.value = false
    getList()
  } catch (error) {
    console.error('更新用户失败:', error)
    ElMessage.error('更新用户失败')
  }
}

const handleModifyStatus = async (row: any, status: boolean) => {
  try {
    await systemApi.updateUser(row.id, { is_active: status })
    row.is_active = status
    ElMessage.success(`用户${status ? '启用' : '禁用'}成功`)
  } catch (error) {
    console.error('修改用户状态失败:', error)
    ElMessage.error('修改用户状态失败')
  }
}

const handleResetPassword = async (row: any) => {
  try {
    await ElMessageBox.confirm('确认重置该用户密码?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await systemApi.resetUserPassword(row.id)
    ElMessage.success(`密码重置成功: ${response.message}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重置密码失败:', error)
      ElMessage.error('重置密码失败')
    }
  }
}

// 生命周期
onMounted(() => {
  getList()
  getRoles()
})
</script>

<style scoped>
.users-container {
  padding: 20px;
}

.filter-container {
  padding-bottom: 10px;
}

.filter-item {
  display: inline-block;
  vertical-align: middle;
  margin-bottom: 10px;
  margin-right: 10px;
}
</style>
