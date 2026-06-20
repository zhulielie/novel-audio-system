<template>
  <div class="menus-container">
    <div class="app-container">
      <div class="filter-container">
        <el-input
          v-model="listQuery.name"
          placeholder="菜单名称"
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
          添加菜单
        </el-button>
        <el-button
          class="filter-item"
          type="info"
          icon="Refresh"
          @click="getList"
        >
          刷新
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
        <el-table-column label="菜单名称" prop="name" width="200px" />
        <el-table-column label="图标" align="center" width="80px">
          <template #default="{ row }">
            <el-icon v-if="row.icon">
              <component :is="row.icon" />
            </el-icon>
          </template>
        </el-table-column>
        <el-table-column label="排序" prop="sort" align="center" width="80px" />
        <el-table-column label="权限标识" prop="perms" />
        <el-table-column label="组件路径" prop="component" />
        <el-table-column label="路由地址" prop="path" />
        <el-table-column label="类型" align="center" width="80px">
          <template #default="{ row }">
            <el-tag :type="getMenuTypeColor(row.menu_type)">
              {{ getMenuTypeText(row.menu_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" align="center" width="80px">
          <template #default="{ row }">
            <el-tag :type="row.visible ? 'success' : 'danger'">
              {{ row.visible ? '显示' : '隐藏' }}
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

      <!-- 菜单编辑对话框 -->
      <el-dialog :title="textMap[dialogStatus]" v-model="dialogFormVisible" width="600px">
        <el-form
          ref="dataForm"
          :rules="rules"
          :model="temp"
          label-position="left"
          label-width="100px"
        >
          <el-row>
            <el-col :span="24">
              <el-form-item label="上级菜单" prop="parent">
                <el-tree-select
                  v-model="temp.parent"
                  :data="menuTreeData"
                  :props="menuTreeProps"
                  placeholder="选择上级菜单"
                  check-strictly
                  clearable
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row>
            <el-col :span="12">
              <el-form-item label="菜单类型" prop="menu_type">
                <el-radio-group v-model="temp.menu_type">
                  <el-radio label="M">目录</el-radio>
                  <el-radio label="C">菜单</el-radio>
                  <el-radio label="F">按钮</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="菜单图标" prop="icon">
                <el-input v-model="temp.icon" placeholder="请输入图标名称" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row>
            <el-col :span="12">
              <el-form-item label="菜单名称" prop="name">
                <el-input v-model="temp.name" placeholder="请输入菜单名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="显示排序" prop="sort">
                <el-input-number v-model="temp.sort" controls-position="right" :min="0" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row v-if="temp.menu_type !== 'F'">
            <el-col :span="12">
              <el-form-item label="路由地址" prop="path">
                <el-input v-model="temp.path" placeholder="请输入路由地址" />
              </el-form-item>
            </el-col>
            <el-col :span="12" v-if="temp.menu_type === 'C'">
              <el-form-item label="组件路径" prop="component">
                <el-input v-model="temp.component" placeholder="请输入组件路径" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row>
            <el-col :span="12">
              <el-form-item label="权限标识" prop="perms">
                <el-input v-model="temp.perms" placeholder="请输入权限标识" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="显示状态">
                <el-radio-group v-model="temp.visible">
                  <el-radio :label="true">显示</el-radio>
                  <el-radio :label="false">隐藏</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row v-if="temp.menu_type !== 'F'">
            <el-col :span="12">
              <el-form-item label="是否外链">
                <el-radio-group v-model="temp.is_frame">
                  <el-radio :label="true">是</el-radio>
                  <el-radio :label="false">否</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12" v-if="temp.menu_type === 'C'">
              <el-form-item label="是否缓存">
                <el-radio-group v-model="temp.is_cache">
                  <el-radio :label="true">缓存</el-radio>
                  <el-radio :label="false">不缓存</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
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
import { formatDate } from '@/utils/date'
import { systemApi } from '@/services/systemApi'

// 响应式数据
const tableKey = ref(0)
const list = ref([])
const listLoading = ref(true)
const dialogFormVisible = ref(false)
const dialogStatus = ref('')
const menuTreeData = ref([])

const listQuery = reactive({
  name: ''
})

const temp = reactive({
  id: undefined,
  name: '',
  parent: null,
  menu_type: 'M',
  path: '',
  component: '',
  perms: '',
  icon: '',
  sort: 0,
  visible: true,
  is_frame: false,
  is_cache: false
})

const textMap = {
  update: '编辑菜单',
  create: '创建菜单'
}

const rules = {
  name: [{ required: true, message: '菜单名称不能为空', trigger: 'blur' }],
  sort: [{ required: true, message: '菜单顺序不能为空', trigger: 'blur' }]
}

const menuTreeProps = {
  children: 'children',
  label: 'name',
  value: 'id'
}

// 方法
const getList = async () => {
  listLoading.value = true
  try {
    const response = await systemApi.getMenuTree()
    list.value = response
    menuTreeData.value = [{ id: 0, name: '主类目', children: response }]
  } catch (error) {
    console.error('获取菜单列表失败:', error)
    ElMessage.error('获取菜单列表失败')
  }
  listLoading.value = false
}

const handleFilter = () => {
  getList()
}

const resetTemp = () => {
  Object.assign(temp, {
    id: undefined,
    name: '',
    parent: null,
    menu_type: 'M',
    path: '',
    component: '',
    perms: '',
    icon: '',
    sort: 0,
    visible: true,
    is_frame: false,
    is_cache: false
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
    await systemApi.createMenu(temp)
    ElMessage.success('菜单创建成功')
    dialogFormVisible.value = false
    getList()
  } catch (error) {
    console.error('创建菜单失败:', error)
    ElMessage.error('创建菜单失败')
  }
}

const updateData = async () => {
  try {
    await systemApi.updateMenu(temp.id, temp)
    ElMessage.success('菜单更新成功')
    dialogFormVisible.value = false
    getList()
  } catch (error) {
    console.error('更新菜单失败:', error)
    ElMessage.error('更新菜单失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确认删除该菜单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await systemApi.deleteMenu(row.id)
    ElMessage.success('删除成功')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除菜单失败:', error)
      ElMessage.error('删除菜单失败')
    }
  }
}

const getMenuTypeText = (type: string) => {
  const typeMap = {
    'M': '目录',
    'C': '菜单',
    'F': '按钮'
  }
  return typeMap[type] || '未知'
}

const getMenuTypeColor = (type: string) => {
  const colorMap = {
    'M': 'info',
    'C': 'success',
    'F': 'warning'
  }
  return colorMap[type] || ''
}

// 生命周期
onMounted(() => {
  getList()
})
</script>

<style scoped>
.menus-container {
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
