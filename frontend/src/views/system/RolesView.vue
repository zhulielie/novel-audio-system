<template>
  <div class="roles-container">
    <div class="app-container">
      <div class="filter-container">
        <el-input
          v-model="listQuery.name"
          placeholder="角色名称"
          style="width: 200px"
          class="filter-item"
          @keyup.enter="handleFilter"
        />
        <el-button
          v-waves
          class="filter-item"
          type="primary"
          icon="Search"
          @click="handleFilter"
        >
          搜索
        </el-button>
        <el-button
          class="filter-item"
          style="margin-left: 10px"
          type="primary"
          icon="Plus"
          @click="handleCreate"
        >
          添加角色
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
        <el-table-column label="角色名称" prop="name" width="150px" align="center" />
        <el-table-column label="角色编码" prop="code" width="150px" align="center" />
        <el-table-column label="描述" prop="description" align="center" />
        <el-table-column label="数据范围" width="120px" align="center">
          <template #default="{ row }">
            <el-tag :type="getDataScopeType(row.data_scope)">
              {{ getDataScopeText(row.data_scope) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" class-name="status-col" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="150px" align="center">
          <template #default="{ row }">
            <span>{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="280" class-name="small-padding fixed-width">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleUpdate(row)">
              编辑
            </el-button>
            <el-button type="info" size="small" @click="handleAssignMenus(row)">
              分配权限
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
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        :total="total"
        :page.sync="listQuery.page"
        :limit.sync="listQuery.limit"
        @pagination="getList"
      />

      <!-- 角色编辑对话框 -->
      <el-dialog :title="textMap[dialogStatus]" :visible.sync="dialogFormVisible">
        <el-form
          ref="dataForm"
          :rules="rules"
          :model="temp"
          label-position="left"
          label-width="100px"
          style="width: 400px; margin-left: 50px"
        >
          <el-form-item label="角色名称" prop="name">
            <el-input v-model="temp.name" />
          </el-form-item>
          <el-form-item label="角色编码" prop="code">
            <el-input v-model="temp.code" :disabled="dialogStatus === 'update'" />
          </el-form-item>
          <el-form-item label="描述" prop="description">
            <el-input v-model="temp.description" type="textarea" />
          </el-form-item>
          <el-form-item label="数据范围" prop="data_scope">
            <el-select v-model="temp.data_scope" placeholder="请选择数据范围">
              <el-option label="全部数据权限" :value="1" />
              <el-option label="自定义数据权限" :value="2" />
              <el-option label="本部门数据权限" :value="3" />
              <el-option label="本部门及以下数据权限" :value="4" />
              <el-option label="仅本人数据权限" :value="5" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-switch v-model="temp.is_active" />
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

      <!-- 权限分配对话框 -->
      <el-dialog title="分配权限" :visible.sync="menuDialogVisible" width="600px">
        <el-tree
          ref="menuTree"
          :data="menuTreeData"
          :props="menuTreeProps"
          show-checkbox
          node-key="id"
          :default-expand-all="true"
        />
        <div slot="footer" class="dialog-footer">
          <el-button @click="menuDialogVisible = false">
            取消
          </el-button>
          <el-button type="primary" @click="saveMenuPermissions">
            确认
          </el-button>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDate } from '@/utils/date'
import { systemApi } from '@/services/systemApi'

// 响应式数据
const tableKey = ref(0)
const list = ref([])
const total = ref(0)
const listLoading = ref(true)
const dialogFormVisible = ref(false)
const menuDialogVisible = ref(false)
const dialogStatus = ref('')
const currentRole = ref<any>(null)
const menuTreeData = ref([])

const listQuery = reactive({
  page: 1,
  limit: 20,
  name: ''
})

const temp = reactive({
  id: undefined,
  name: '',
  code: '',
  description: '',
  data_scope: 1,
  is_active: true
})

const textMap = {
  update: '编辑角色',
  create: '创建角色'
}

const rules = {
  name: [{ required: true, message: '角色名称不能为空', trigger: 'blur' }],
  code: [{ required: true, message: '角色编码不能为空', trigger: 'blur' }]
}

const menuTreeProps = {
  children: 'children',
  label: 'name'
}

// 方法
const getList = async () => {
  listLoading.value = true
  try {
    const response = await systemApi.getRoles(listQuery)
    list.value = response.results || response
    total.value = response.count || list.value.length
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取角色列表失败')
  }
  listLoading.value = false
}

const handleFilter = () => {
  listQuery.page = 1
  getList()
}

const resetTemp = () => {
  Object.assign(temp, {
    id: undefined,
    name: '',
    code: '',
    description: '',
    data_scope: 1,
    is_active: true
  })
}

const handleCreate = () => {
  resetTemp()
  dialogStatus.value = 'create'
  dialogFormVisible.value = true
}

const handleUpdate = (row: any) => {
  Object.assign(temp, row)
  dialogStatus.value = 'update'
  dialogFormVisible.value = true
}

const createData = async () => {
  try {
    await systemApi.createRole(temp)
    ElMessage.success('角色创建成功')
    dialogFormVisible.value = false
    getList()
  } catch (error) {
    console.error('创建角色失败:', error)
    ElMessage.error('创建角色失败')
  }
}

const updateData = async () => {
  try {
    await systemApi.updateRole(temp.id, temp)
    ElMessage.success('角色更新成功')
    dialogFormVisible.value = false
    getList()
  } catch (error) {
    console.error('更新角色失败:', error)
    ElMessage.error('更新角色失败')
  }
}

const handleModifyStatus = async (row: any, status: boolean) => {
  try {
    await systemApi.updateRole(row.id, { is_active: status })
    row.is_active = status
    ElMessage.success(`角色${status ? '启用' : '禁用'}成功`)
  } catch (error) {
    console.error('修改角色状态失败:', error)
    ElMessage.error('修改角色状态失败')
  }
}

const handleAssignMenus = async (row: any) => {
  currentRole.value = row
  try {
    // 获取菜单树
    const menuTree = await systemApi.getMenuTree()
    menuTreeData.value = menuTree
    
    // 获取角色已有权限
    const roleMenus = await systemApi.getRoleMenus(row.id)
    
    menuDialogVisible.value = true
    
    // 设置选中的菜单
    setTimeout(() => {
      const menuTree = this.$refs.menuTree
      if (menuTree && roleMenus.menu_ids) {
        menuTree.setCheckedKeys(roleMenus.menu_ids)
      }
    }, 100)
  } catch (error) {
    console.error('获取权限数据失败:', error)
    ElMessage.error('获取权限数据失败')
  }
}

const saveMenuPermissions = async () => {
  try {
    const menuTree = this.$refs.menuTree
    const checkedKeys = menuTree.getCheckedKeys()
    const halfCheckedKeys = menuTree.getHalfCheckedKeys()
    const menuIds = [...checkedKeys, ...halfCheckedKeys]
    
    await systemApi.assignRoleMenus(currentRole.value.id, menuIds)
    ElMessage.success('权限分配成功')
    menuDialogVisible.value = false
  } catch (error) {
    console.error('分配权限失败:', error)
    ElMessage.error('分配权限失败')
  }
}

const getDataScopeText = (scope: number) => {
  const scopeMap = {
    1: '全部',
    2: '自定义',
    3: '本部门',
    4: '本部门及以下',
    5: '仅本人'
  }
  return scopeMap[scope] || '未知'
}

const getDataScopeType = (scope: number) => {
  const typeMap = {
    1: 'danger',
    2: 'warning',
    3: 'info',
    4: 'primary',
    5: 'success'
  }
  return typeMap[scope] || ''
}

// 生命周期
onMounted(() => {
  getList()
})
</script>

<style scoped>
.roles-container {
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
