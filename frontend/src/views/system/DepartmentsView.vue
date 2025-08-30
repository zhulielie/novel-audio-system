<template>
  <div class="departments-container">
    <div class="app-container">
      <div class="filter-container">
        <el-input
          v-model="listQuery.name"
          placeholder="部门名称"
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
          添加部门
        </el-button>
      </div>

      <el-table
        :key="tableKey"
        v-loading="listLoading"
        :data="list"
        row-key="id"
        border
        fit
        highlight-current-row
        style="width: 100%"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
        <el-table-column label="部门名称" prop="name" width="200px" />
        <el-table-column label="部门编码" prop="code" width="150px" align="center" />
        <el-table-column label="负责人" align="center" width="120px">
          <template #default="{ row }">
            <span>{{ row.leader?.nickname || row.leader?.username || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="联系电话" prop="phone" align="center" />
        <el-table-column label="邮箱" prop="email" align="center" />
        <el-table-column label="排序" prop="sort" align="center" width="80px" />
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
        <el-table-column label="操作" align="center" width="200" class-name="small-padding fixed-width">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleUpdate(row)">
              编辑
            </el-button>
            <el-button type="success" size="small" @click="handleCreate(row)">
              新增
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 部门编辑对话框 -->
      <el-dialog :title="textMap[dialogStatus]" :visible.sync="dialogFormVisible">
        <el-form
          ref="dataForm"
          :rules="rules"
          :model="temp"
          label-position="left"
          label-width="100px"
          style="width: 400px; margin-left: 50px"
        >
          <el-form-item label="上级部门" prop="parent">
            <el-tree-select
              v-model="temp.parent"
              :data="deptTreeData"
              :props="deptTreeProps"
              placeholder="选择上级部门"
              check-strictly
              clearable
            />
          </el-form-item>
          <el-form-item label="部门名称" prop="name">
            <el-input v-model="temp.name" />
          </el-form-item>
          <el-form-item label="部门编码" prop="code">
            <el-input v-model="temp.code" />
          </el-form-item>
          <el-form-item label="负责人" prop="leader">
            <el-select v-model="temp.leader" placeholder="请选择负责人" clearable>
              <el-option
                v-for="user in userOptions"
                :key="user.id"
                :label="user.nickname || user.username"
                :value="user.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="联系电话" prop="phone">
            <el-input v-model="temp.phone" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="temp.email" />
          </el-form-item>
          <el-form-item label="显示排序" prop="sort">
            <el-input-number v-model="temp.sort" controls-position="right" :min="0" />
          </el-form-item>
          <el-form-item label="部门描述" prop="description">
            <el-input v-model="temp.description" type="textarea" />
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
const listLoading = ref(true)
const dialogFormVisible = ref(false)
const dialogStatus = ref('')
const deptTreeData = ref([])
const userOptions = ref([])

const listQuery = reactive({
  name: ''
})

const temp = reactive({
  id: undefined,
  name: '',
  code: '',
  parent: null,
  leader: null,
  phone: '',
  email: '',
  sort: 0,
  description: '',
  is_active: true
})

const textMap = {
  update: '编辑部门',
  create: '创建部门'
}

const rules = {
  name: [{ required: true, message: '部门名称不能为空', trigger: 'blur' }],
  code: [{ required: true, message: '部门编码不能为空', trigger: 'blur' }]
}

const deptTreeProps = {
  children: 'children',
  label: 'name',
  value: 'id'
}

// 方法
const getList = async () => {
  listLoading.value = true
  try {
    const response = await systemApi.getDepartmentTree()
    list.value = response
    deptTreeData.value = [{ id: 0, name: '主部门', children: response }]
  } catch (error) {
    console.error('获取部门列表失败:', error)
    ElMessage.error('获取部门列表失败')
  }
  listLoading.value = false
}

const getUsers = async () => {
  try {
    const response = await systemApi.getUsers()
    userOptions.value = response.results || response
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

const handleFilter = () => {
  getList()
}

const resetTemp = () => {
  Object.assign(temp, {
    id: undefined,
    name: '',
    code: '',
    parent: null,
    leader: null,
    phone: '',
    email: '',
    sort: 0,
    description: '',
    is_active: true
  })
}

const handleCreate = (row?: any) => {
  resetTemp()
  if (row) {
    temp.parent = row.id
  }
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
    await systemApi.createDepartment(temp)
    ElMessage.success('部门创建成功')
    dialogFormVisible.value = false
    getList()
  } catch (error) {
    console.error('创建部门失败:', error)
    ElMessage.error('创建部门失败')
  }
}

const updateData = async () => {
  try {
    await systemApi.updateDepartment(temp.id, temp)
    ElMessage.success('部门更新成功')
    dialogFormVisible.value = false
    getList()
  } catch (error) {
    console.error('更新部门失败:', error)
    ElMessage.error('更新部门失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确认删除该部门吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await systemApi.deleteDepartment(row.id)
    ElMessage.success('删除成功')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除部门失败:', error)
      ElMessage.error('删除部门失败')
    }
  }
}

// 生命周期
onMounted(() => {
  getList()
  getUsers()
})
</script>

<style scoped>
.departments-container {
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
