<template>
  <div id="declaration">
    <el-row :gutter="20">
      <!-- 左侧文件列表 -->
      <el-col :span="4" class="fileList">
        <el-card shadow="hover">
          <div slot="header">
            <span>我的文件</span>
            <el-switch v-model="multiSelect" @change="handleSwitchChange"/>
          </div>
          <!-- 添加上传文件提示区域 -->
          <el-upload class="upload-hint" :action="`http://localhost:8002/declaration/upload`" multiple="true" :limit="10" :on-success="handleUploadSuccess" :accept="'.png,.jpg,.jpeg,.pdf'" :before-upload="beforeUpload" :show-file-list="false" :data="{ uploadDir: this.uploadDirectory }" :auto-upload="true">  
            <div slot="tip" class="el-upload__tip">
              <el-icon><UploadFilled /></el-icon>
              上传文件(支持单个/批量)
            </div>
          </el-upload>
          <el-menu :default-active="selectedFile?.name" @select="handleSelect" style="border: none;">
            <el-menu-item v-for="(file, index) in files" :key="index" :index="file.id" class="file-item" :class="{ 'selected': selectedFile?.name === file.name }" @mouseenter="currentHoverIndex = index"
            @mouseleave="currentHoverIndex = null" style="padding-left: 0; padding-right: 0;">
              <el-image :src="`http://localhost:8002/api/file${file.thumbnail}`" style="width: 50px; height: 50px; margin-right: 10px;" fit="cover"/>
              <span>{{ file.name }}</span>
              <!-- 删除按钮 -->
              <el-icon @click.stop="deleteFile(file.name, file.id)" v-show="currentHoverIndex === index" style="margin-left: auto;" size="small"><Delete /></el-icon>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 中间发票预览 -->
      <el-col :span="10">
        <el-card shadow="hover" class="declaration-preview" style="display: flex; align-items: center; justify-content: center;">
          <div v-if="!(selectedFile?.thumbnail)" >
                          <el-upload drag :http-request="customUploadRequest" :multiple="true" :limit="10" :on-success="handleUploadSuccess" :accept="'.png,.jpg,.jpeg,.pdf'" :before-upload="beforeUpload" :show-file-list="false">
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">             
                点击上传文件 / 拖拽文件到此处<br/>
                <em>支持 png, jpg, jpeg 等格式，上传单个文件大小不超过 50M</em>
              </div>
            </el-upload>
          </div>
          <div v-else>
            <el-image style="width: 100%;" :src="`http://localhost:8002/api/file${selectedFile.thumbnail}`" fit="cover" />
          </div>
          
        </el-card>
      </el-col>

      <!-- 右侧字段提取 -->
      <el-col :span="10">
        <el-card shadow="hover" class="declaration-extract">
          <div slot="header">
            <el-radio-group v-model="extractMode" @change="handleExtractModeChange">
              <el-radio-button label="auto">智能抽取</el-radio-button>
              <el-radio-button label="custom">自定义抽取</el-radio-button>
            </el-radio-group>
            <div style="float: right;">
              <el-switch v-model="useOCRSwitch" @change="toggleOCR" />
              <span style="margin-right: 20px;">启用 OCR 辅助</span>
              <el-button type="primary" @click="exportToExcel">导出结果</el-button>
              <el-button type="primary" @click="reExtract">重新抽取</el-button>
            </div>

            <div v-if="extractMode === 'auto'">
              <el-table :data="selectedFile ? selectedFile.ExtractedDefaultField : extractedDefaultFields" stripe v-loading="selectedFile ? selectedFile.loading_auto : loading_auto" :element-loading-text="selectedFile ? selectedFile.loadingText : loadingText" element-loading-spinner="el-icon-loading">
                <el-table-column label="字段名" width="150">
                  <template #default="{ row }">
                    <span :class="{ 'nested-field': row.level > 0 }">{{ row.fieldName }}</span>
                  </template>
                </el-table-column>

                <el-table-column label="值" min-idth="60%">
                  <template #default="{ row }">
                    <div @mouseenter="handleMouseEnter(row.fieldName, row.index)" @mouseleave="handleMouseLeave(row.fieldName, row.index)" style="display: flex; justify-content: space-between; align-items: center;" >
                      <!-- <span>{{ row.fieldValue }}</span> -->
                      <el-popconfirm :title="`字段: ${row.fieldName}`" :hide-after="0" placement="top" :show-arrow="true" :teleported="true" trigger="click">
                        <template #reference>
                          <el-input 
                            v-model="row.fieldValue" 
                            size="small" 
                            @change="handleFieldValueChange(row)" 
                            :class="{ 'confirmed-field': confirmedFields[`${row.fieldName}-${row.index}`] }"
                            :style="{ 
                              flex: 1,
                              backgroundColor: confirmedFields[`${row.fieldName}-${row.index}`] ? '#f0f9f0' : '',
                              borderColor: confirmedFields[`${row.fieldName}-${row.index}`] ? '#67c23a' : '',
                              color: confirmedFields[`${row.fieldName}-${row.index}`] ? '#67c23a !important' : '',
                              fontWeight: confirmedFields[`${row.fieldName}-${row.index}`] ? '600' : 'normal'
                            }" />
                        </template>
                        <template #actions="{ confirm, cancel }">
                          <el-button
                            type="danger"
                            size="small"
                            @click="handleFieldConfirm(row, selectedFile.ExtractedDefaultField)"
                          >
                            确认
                          </el-button>
                        </template>
                    
                      </el-popconfirm>
                      
                      <el-tooltip content="复制" placement="top">
                        <el-icon @click="copyToClipboard(row.fieldValue)" v-show="isMouseOverRow[`${row.fieldName}-${row.index}`]" style="margin-left: 8px;"><CopyDocument /></el-icon>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              <div style="text-align: right; margin-top: 20px;" v-if="selectedFile && selectedFile.ExtractedDefaultField && selectedFile.ExtractedDefaultField.length > 0">
                <el-button type="primary" @click="confirmAutoExtraction(selectedFile.id, selectedFile.ExtractedDefaultField)">确认</el-button>
              </div>
            </div>
            
            <div v-else-if="extractMode === 'custom'" style="padding-top: 10px; overflow: auto; ">
              <!-- 自定义抽取界面 -->
              <!-- 工具栏 -->
              <el-card style="height:400px; overflow: auto;">
                <div class="toolbar">
                  <el-button type="primary" @click="showAddDialog">新增配置</el-button>
                </div>
                <!-- 字段列表 -->
                <el-table :data="fields" stripe style="width: 100%">

                  <!-- <el-table-column prop="index" label="序号"></el-table-column> -->
                  <!-- 展开行显示嵌套字段 -->
                  <el-table-column type="expand">
                    <template #default="{ row }">
                      <el-table v-if="row.nestedFields && row.nestedFields.length" :data="row.nestedFields" size="small">

                        <el-table-column prop="fieldName" label="子字段名称"></el-table-column>
                        <el-table-column prop="fieldType" label="字段说明"></el-table-column>
                        <el-table-column label="操作">
                          <template #default="{ row }">
                            <el-button type="text" size="small" @click="viewField(row)">查看</el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                      <!-- <div v-else style="color: #999;">无嵌套字段</div> -->
                    </template>
                  </el-table-column>

                  <el-table-column prop="fieldName" label="关键信息名称"></el-table-column>
                  <el-table-column prop="fieldType" label="字段类型"></el-table-column>
                  <el-table-column label="操作">
                    <template #default="{ row }">
                      <el-button type="text" size="small" @click="deleteField(row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
      
                <!-- 底部按钮 -->
                <div class="button-group" style="float: right; padding-top:10px">
                  <el-button type="primary" @click="saveConfig">保存配置</el-button>
                  <el-button type="success" @click="fetchExtractedData(this.newPrompt,this.selectedFile)">开始抽取</el-button>
                </div>
              </el-card>  
              
              <!-- 新增卡片：展示抽取结果 -->
              <el-card shadow="hover" style="margin-top: 20px; height: 400px; overflow: auto;" v-loading="loading_custom" :element-loading-text="loadingText" element-loading-spinner="el-icon-loading">
                <div slot="header">
                  <span>抽取结果</span>
                </div>
                <el-table :data="selectedFile ? selectedFile.ExtractedCustomField : extractedCustomFields" stripe>
                  <el-table-column label="字段名" width="200">
                    <template #default="{ row }">
                      <span :class="{ 'nested-field': row.level > 0 }">{{ row.fieldName }}</span>
                    </template>
                  </el-table-column>

                  <el-table-column label="值" min-width="60%">
                    <template #default="{ row }">
                      <div @mouseenter="handleMouseEnter(row.fieldName, row.index)" @mouseleave="handleMouseLeave(row.fieldName, row.index)" style="display: flex; justify-content: space-between;">
                        <span>{{ row.fieldValue }}</span>
                        <el-tooltip content="复制" placement="top">
                          <el-icon @click="copyToClipboard(row.fieldValue)" v-show="isMouseOverRow[`${row.fieldName}-${row.index}`]"><CopyDocument /></el-icon>
                        </el-tooltip>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </div>

            <div v-else-if="extractMode === 'result'">
              <!-- JSON 结果界面 -->
              <el-table :data="selectedFile ? selectedFile.extractedDefaultFields : extractedDefaultFields" stripe>
                <el-table-column label="字段名" width="120">
                  <template #default="{ row }">
                    <span :class="{ 'nested-field': row.level > 0 }">{{ row.fieldName }}</span>
                  </template>
                </el-table-column>

                <el-table-column label="值" min-idth="60%">
                  <template #default="{ row }">
                    <div @mouseenter="handleMouseEnter(row.fieldName, row.index)" @mouseleave="handleMouseLeave(row.fieldName, row.index)" style="display: flex; justify-content: space-between;">
                      <span>{{ row.fieldValue }}</span>
                      <el-tooltip content="复制" placement="top"custom>
                      </el-tooltip>
                      <el-icon @click="copyToClipboard(row.fieldValue)" v-show="isMouseOverRow[`${row.fieldName}-${row.index}`]"><CopyDocument /></el-icon>
                    </div>
                  </template>
                </el-table-column>

                <el-table-column label="标准" min-idth="60%">
                  <template #default="{ row }">
                    <div @mouseenter="handleMouseEnter(row.fieldName, row.index)" @mouseleave="handleMouseLeave(row.fieldName, row.index)" style="display: flex; justify-content: space-between;">
                      <span>{{ matchedStandardField(row.index)?.fieldValue || '' }}</span>
                      <el-tooltip content="复制" placement="top"custom>
                      </el-tooltip>
                      <el-icon @click="copyToClipboard(row.fieldValue)" v-show="isMouseOverRow[`${row.fieldName}-${row.index}`]"><CopyDocument /></el-icon>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>

  <!-- 新增字段弹框 -->
  <el-dialog title="新增字段" v-model="addDialogVisible" width="600px">
    <el-form ref="addFieldForm" :model="newField" label-width="120px">
      <el-form-item label="字段名称">
        <el-input v-model="newField.fieldName"></el-input>
      </el-form-item>
      <el-form-item label="字段说明">
        <el-input v-model="newField.fieldType"></el-input>
      </el-form-item>
      <el-form-item label="是否嵌套字段">
        <el-switch v-model="isNested"></el-switch>
      </el-form-item>

      <template v-if="isNested">
        <h4>子字段配置</h4>
        <!-- 动态渲染所有子字段 -->
        <div v-for="(subField, subIndex) in newField.nestedFields" :key="subIndex" style="margin-bottom: 15px;">
          <el-form-item label="子字段名称">
            <el-input v-model="subField.fieldName" />
          </el-form-item>
          <el-form-item label="子字段说明">
            <el-input v-model="subField.fieldType" />
          </el-form-item>
          <div style="text-align: right;">
            <el-button type="danger" size="small" @click="removeSubField(subIndex)">删除</el-button>
          </div>
        </div>

        <el-button type="primary" @click="addNestedField">新增子字段</el-button>
      </template>
    </el-form>
    <template #footer>
      <div style="text-align: right;">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNewField">保存</el-button>
      </div>
    </template>
  </el-dialog>

</template>
  
<script>
import axios from 'axios'
import * as XLSX from 'xlsx';

export default {
  name: 'Declaration',
  data () {
    return {
      DeclarationPrompt: `
        请分析图片内容，并提取其中包含的所有指定字段及对应的值，以 JSON 格式输出。
        要求如下：
        1. 每个字段作为 JSON 的一个键；
        2. 每个字段的值为图片中对应的语义内容；
        3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
        4. 不需要包含位置信息、类型或其他元数据；
        
        ### 需要提取的字段：
        - **单据种类**
        - **报关单号**
        - **合同协议号**
        - **申报日期**
        - **境内发货人**
        - **境外收货人** 
        - **生产销售单位**
        - **运输方式**
        - **运抵国**
        - **商品信息**：如果有多条商品信息，用数组存储，每条商品信息是一个对象,包括：
          - 商品名称：只需要商品名称
          - 数量
          - 单价：单价+币制
          - 总价：总价+币制
        - **商品总数量**: 所有商品的数量之和
        - **商品总价格**: 所有商品的总价之和

        ### 示例输出格式：
        {
          "单据种类": "中华人民共和国海关出口货物报关单",
          "报关单号": "22312423846342",
          "合同协议号": "NDSEV2002404",
          "申报日期": "20200101",
          "境内发货人信息": "苏州科技有限公司",
          "境外收货人信息": "SuZhou Company",
          "生产销售单位信息": "苏州科技有限公司",
          "运输方式": "水路运输",
          "运抵国": "英国",
          "商品信息": [
            {
              "商品名称": "Flower",
              "数量及单位": "100件",
              "单价": "100.61 美元",
              "总价": "3452.34 美元"
            },
            {
              "商品名称": "其他商品",
              "数量": "100件",
              "单价": "10 美元",
              "总价": "1000 美元"
            }
          ],
          "商品总数量": "10,100件",
          "商品总价格": "1100 美元",
        }
        
      `,
      newPrompt: `
      请分析图片内容，并提取其中包含的所有指定字段及对应的值，以 JSON 格式输出。
      要求如下：
      1. 每个字段作为 JSON 的一个键；
      2. 每个字段的值为图片中对应的语义内容；
      3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
      4. 不需要包含位置信息、类型或其他元数据；

      ### 需要提取的字段：
      `,
      newPromptend: `
      ### 示例输出格式：
      {
          "单据种类": "中华人民共和国海关出口货物报关单",
          "报关单号": "22312423846342",
          "合同协议号": "023746123",
          "申报日期": "20200101",
          "境内发货人信息": {
            "名称": "苏州科技有限公司",
            "编码": "12334857632"
          },
          "境外收货人信息": {
            "名称": "Suzhou Company",
            "编码": "12334857632"
          },
          "生产销售单位信息": {
            "名称": "苏州科技有限公司",
            "编码": "12334857632"
          },
          "运输方式": "水路运输",
          "运抵国": "英国",
          "商品信息": [
            {
              "商品名称及规格型号": "Flower",
              "数量及单位": "100件",
              "单价": "100.61 USD",
              "总价": "3452.34 USD"
            },
            {
              "商品名称及规格型号": "其他商品",
              "数量及单位": "100件",
              "单价": "10 USD",
              "总价": "1000 USD"
            }
          ],
          "商品总数量": "10,100件",
          "商品总价格": "1100 USD",
        }
      `,

      fields: [
        { fieldName: '单据种类', fieldType: '报关单抬头，例如 "中华人民共和国海关出口货物报关单"' },
        { fieldName: '报关单号', fieldType: '例如"22312423846342"'},
        { fieldName: '合同协议号', fieldType: '例如 "023746123"' },
        { fieldName: '申报日期', fieldType: '例如 "20200101"' },
        // { fieldName: '出口日期', fieldType: '例如 "20200101"' },
        
        { fieldName: '境内发货人信息', 
          fieldType: '',
          nestedFields: [
            {fieldName: '名称', fieldType: '例如 "苏州科技有限公司"'},
            {fieldName: '编码', fieldType: '例如 "12334857632"'}
          ]
        },
        { fieldName: '境外收货人信息', 
          fieldType: '',
          nestedFields: [
            {fieldName: '名称', fieldType: '例如 "苏州科技有限公司"'},
            {fieldName: '编码', fieldType: '例如 "12334857632"'}
          ]
        },
        { fieldName: '生产销售单位信息', 
          fieldType: '',
          nestedFields: [
            {fieldName: '名称', fieldType: '例如 "苏州科技有限公司"'},
            {fieldName: '编码', fieldType: '例如 "12334857632"'}
          ]
        },
        { fieldName: '运输方式', fieldType: '例如 水路运输"'},
        // { fieldName: '运输工具名称及航次号', fieldType: '例如 "SM YANRIAN/2000E"'},
        // { fieldName: '贸易国', fieldType: '例如 "美国"' },  
        { fieldName: '运抵国', fieldType: '例如 "英国"' },
        {
          fieldName: "商品信息",
          fieldType: "如果有多条商品信息，用数组存储，每条商品信息是一个对象",
          nestedFields: [
            { fieldName: "商品名称", fieldType: "" },
            { fieldName: "数量", fieldType: "" },
            { fieldName: "单价", fieldType: "" },
            { fieldName: "总价", fieldType: "" },
          ],
        },
        { fieldName: '商品总数量', fieldType: '所有商品的数量之和' },
        { fieldName: '商品总价格', fieldType: '所有商品的总价之和' },
        // { fieldName: '印章信息', fieldType: '请提取出图中圆形印章中的文字内容' },
      ],
      addDialogVisible: false, // 控制新增字段弹框显示
      newField: {
        fieldName: "",
        fieldType: "",
        nestedFields: [],
      },
      isNested: false, // 是否是嵌套字段

      multiSelect: false,
      extractMode: 'auto',
      currentDeclarationImage: '',
      uploadDirectory: '../backend/upload/报关单',
      currentHoverIndex: null, // 当前鼠标中文件列表的位置
      selectedFile: {
        id: '',
        name: "",
        thumbnail: "",
        created_at: "",
        ExtractedDefaultField: [],
        ExtractedCustomField: [],
        loadingText: '',
        loading_auto: false,
        loading_custom: false
      },

      files: [],

      extractedDefaultFields: [], // 存储自动提取后的数据
      extractedCustomFields: [], // 存储自定义提取后的数据
      standardFields: [], // 标准数据

      loading_auto: false, // 新增加载状态
      loading_custom: false,
      loadingText: '正在抽取字段...',
      isMouseOverRow: {}, // 用于记录鼠标悬停状态
      globalIndex: 0,
      processingTasks: [],       // 当前待处理的任务队列
      activeTasks: 0,            // 当前正在执行的任务数
      maxConcurrency: 3,        // 最大并发数
      useOCRSwitch: true, // 控制是否使用 OCR，默认启用
      confirmedFields: {},
    }
  },
  async created() {
    await this.fetchFiles();
    if (this.$route.params.fileId) {
      this.autoSelectFile(this.$route.params.fileId);
    }
  },
  methods: {
    async handleSelect(key) {
      const idx = Number(key)
      // 根据选中的文件名更新 selectedFile 和 currentInvoiceImage
      console.log(this.files)
      this.selectedFile = this.files.find(file => file.id === idx);
      console.log("当前选择：",this.selectedFile)
      if (this.selectedFile) {
        if (this.extractMode === 'auto' || this.extractMode === "result") {
          this.extractedDefaultFields = [];
          const res = await axios.get(`http://localhost:8002/declaration/extracted-field/${idx}`);
          if (res.data.extracted_data) {
            this.selectedFile.ExtractedDefaultField = res.data.extracted_data;
          }        
        } else if (this.extractMode === 'custom') {
          // 切换图片时清空默认字段缓存
          this.extractedCustomFields = [];
          const res = await axios.get(`http://localhost:8002/declaration/extracted-custom-field/${idx}`);
          if (res.data.extracted_data) {
            this.selectedFile.ExtractedCustomField = res.data.extracted_data;
          }  
        }
        
      }
    },
    async autoSelectFile(fileId) {
      // 等待文件列表加载完成
      await this.$nextTick();
      if (this.files.length > 0) {
        await this.handleSelect(fileId);
      }
    },

    // 删除所有文件
    handleSwitchChange(checked) {
      if (checked) {
        this.$confirm('确定要清空所有文件吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          try {
            // 清空前端文件列表
            this.files = [];
            this.extractedDefaultFields = [];
            this.extractedCustomFields = [];

            // 调用后端接口删除服务器上所有文件
            axios.post('http://localhost:8002/declaration/clear-files', {
              uploadDir: this.uploadDirectory
            },{
              headers: {
                'Content-Type': 'application/json'
              }
            });

            this.selectedFile = null;
            this.$message.success('已清空所有文件');
          } catch (error) {
            console.error('清空失败:', error);
            this.$message.error('清空失败，请重试');
          }
        }).catch(() => {
          this.multiSelect = false; // 如果用户取消，保持开关关闭
          this.$message.info('已取消清空操作');
        });
      }
    },

    // 删除文件列表中的文件
    async deleteFile(file_name, file_id) {
      this.$confirm('确认删除此文件吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        // const fileToDelete = this.files[index];
        // 调用后端删除接口
        console.log(file_id)
        try {
          await axios.post('http://localhost:8002/declaration/delete-file', {
            filename: file_name,
            uploadDir: this.uploadDirectory,
            file_id: file_id
            // 你可以从 data() 获取这个路径
          }, {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
          });
          await this.fetchFiles();
          // 如果是当前选中文件，清空预览
          if (this.selectedFile && this.selectedFile.id === file_id) {
            this.selectedFile = null;
          }

          this.$message.success('删除成功');
        } catch (error) {
          console.error('删除失败:', error);
          this.$message.error('删除失败，请重试');
        }
      }).catch(() => {
        this.$message({
          type: 'info',
          message: '已取消删除'
        });
      });
    },
    async fetchFiles() {
      const res = await fetch('http://localhost:8002/declaration/files');
      const data = await res.json();
      console.log(data);
      this.files = data;
    },

    async fetchExtractedData(nowPrompt, fileObj) {
      // if (!this.currentDeclarationImage) {
      //   this.$message.warning('请先选择一张图片')
      //   return
      // }
      try {        
        if (this.extractMode === "auto") {
          fileObj.loading_auto = true;
          fileObj.loadingText = '正在抽取字段...';
          const res = await axios.post('http://localhost:8002/declaration/open-loading', {
            file_id: Number(fileObj.id),
          }, {
            headers: {
              'Content-Type': 'application/json'
            }
          });
          await this.fetchFiles()
        } else if (this.extractMode === "custom") {
          this.loading_custom = true;
        }
        console.log("现在的prompt：", nowPrompt)

        const res = await fetch('http://localhost:8002/api/extract', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            image_url: fileObj.thumbnail,
            prompt: nowPrompt,
            use_ocr: this.useOCRSwitch
          })
        });
        
        if (!res.ok) {
          throw new Error('请求失败');
        }

        const parsed = await res.json();
        console.log("结果是：", parsed)
        // 先重置全局 index
        this.globalIndex = 0;
        // console.log(parsed)
        // 更新表格数据
        if (this.extractMode === "auto") {
          const res = await axios.post('http://localhost:8002/declaration/save-extracted', {
            file_id: Number(fileObj.id),
            extracted_data: this.parseJsonToTable(parsed)
          }, {
            headers: {
              'Content-Type': 'application/json'
            }
          });
          fileObj.ExtractedDefaultField = this.parseJsonToTable(parsed);
        }
        else if (this.extractMode === "custom") {
          const res = await axios.post('http://localhost:8002/declaration/save-custom-extracted',{
            file_id: Number(fileObj.id),
            extracted_data: this.parseJsonToTable(parsed)
          }, {
            headers: {
              'Content-Type': 'application/json'
            }
          });
          this.selectedFile.ExtractedCustomField = this.parseJsonToTable(parsed)
        }      
      } catch (error) {
        console.error('字段提取失败:', error)
        this.$message.error('字段提取失败')
      } finally {
        fileObj.loading_auto = false;
        fileObj.loadingText = '';
        const res = await axios.post('http://localhost:8002/declaration/close-loading', {
            file_id: Number(fileObj.id),
          }, {
            headers: {
              'Content-Type': 'application/json'
            }
          });
        this.loading_custom = false;
        this.loadingText = '';
        await this.fetchFiles()
      }
    },

    parseJsonToTable(data, parentKey = '', level = 0) {
      let result = []

      for (const key in data) {
        const value = data[key]
        const newKey = parentKey ? `${parentKey}-${key}` : key

        if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
          result.push({
            fieldName: key,
            fieldValue: '',
            index: this.globalIndex++, // 动态生成唯一索引
            level: level
          })
          result = result.concat(this.parseJsonToTable(value, newKey, level + 1))
        } else if (Array.isArray(value)) {
          value.forEach((item, index) => {
            if (typeof item === 'object') {
              result.push({
                fieldName: `${newKey} ${index + 1}`,
                fieldValue: '',
                index: this.globalIndex++, // 动态生成唯一索引
                level: level
              })
              result = result.concat(this.parseJsonToTable(item, `${newKey}-${index}`, level + 1))
            } else {
              result.push({
                fieldName: `${newKey}-${index}`,
                fieldValue: item,
                index: this.globalIndex++, // 动态生成唯一索引
                level: level + 1
              })
            }
          })
        } else {
          result.push({
            fieldName: key,
            fieldValue: value,
            index: this.globalIndex++, // 动态生成唯一索引
            level: level
          })
        }
      }

      return result
    },

    async handleExtractModeChange(mode, fileObj=null) {
      if (!fileObj) {
        fileObj = this.selectedFile;
      }
      const idx = Number(fileObj.id)
      this.extractMode = mode;
      if (this.extractMode === "auto") {
        const res = await axios.get(`http://localhost:8002/declaration/extracted-field/${idx}`);
        if (res.data.extracted_data) {
          fileObj.ExtractedDefaultField = res.data.extracted_data;
        } else {
          await this.fetchExtractedData(this.DeclarationPrompt, fileObj);
        
        }
        
      } else if (this.extractMode === "custom") {
        const res = await axios.get(`http://localhost:8002/declaration/extracted-custom-field/${idx}`);
        if (res.data.extracted_data) {
          fileObj.ExtractedCustomField = res.data.extracted_data;
        }
      }
    },

    // 重新抽取
    reExtract() {
      if (this.extractMode === 'auto') {
        this.fetchExtractedData(this.DeclarationPrompt, this.selectedFile)
      } else if (this.extractMode === 'custom') {
        this.fetchExtractedData(this.newPrompt, this.selectedFile)
      }
    },

    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        this.$message.success('已复制到剪贴板');
      }).catch(err => {
        this.$message.error('复制失败');
      });
    },

    handleMouseEnter(fieldName, index) {
      this.isMouseOverRow[`${fieldName}-${index}`] = true;
    },

    handleMouseLeave(fieldName, index) {
      this.isMouseOverRow[`${fieldName}-${index}`] = false;
    },

    async customUploadRequest({ file }) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('uploadDir', this.uploadDirectory); // 动态设置 uploadDir

      await axios.post('http://localhost:8002/declaration/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }).then(response => {

      }).catch(error => {
        console.error('上传失败:', error);
      });
    },

    // 上传文件
    async handleUploadSuccess(response, file, fileLis) {
      // 1. 更新文件列表
      this.fetchFiles();
      const uploadedFile = response.file;
      this.selectedFile = uploadedFile;

      // 添加到任务队列
      this.processingTasks.push({
        file: uploadedFile,
        mode: "auto"
      });

      // 尝试启动新任务
      this.processNextTask();
    },

    async processNextTask() {
      if (this.processingTasks.length === 0 || this.activeTasks >= this.maxConcurrency) {
        return; // 队列为空 或 已达最大并发数时退出
      }

      const task = this.processingTasks.shift(); // 取出第一个任务
      this.activeTasks++;

      try {
        await this.handleExtractModeChange(task.mode, task.file);
      } catch (err) {
        console.error('任务失败:', err);
      } finally {
        this.activeTasks--;
        this.processNextTask(); // 继续下一个任务
      }
    },

    beforeUpload(file) {
      const isAllowedType = /\.(png|jpg|jpeg|pdf)$/i.test(file.name);
      if (!isAllowedType) {
        this.$message.error('只能上传 .png, .jpg, .jpeg, .pdf文件');
        return false;
      }
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        this.$message.error('文件大小不能超过 50MB!');
        return false;
      }
      return true;
    },

    showAddDialog() {
      this.addDialogVisible = true;
      this.newField = {
        fieldName: "",
        fieldType: "文本",
        nestedFields: [],
      };
      this.isNested = false;
    },

    addNestedField() {
      this.newField.nestedFields.push({
        fieldName: '',
        fieldType: ''
      });
    },

    // 保存新字段到字段列表
    saveNewField() {
      // 将新字段加入主字段列表
      this.fields.push({ ...this.newField });

      // 关闭弹窗并重置表单
      this.addDialogVisible = false;
      this.newField = {
        fieldName: '',
        fieldType: '',
        nestedFields: []
      };
      this.isNested = false;

      this.$message.success('字段已保存');
      console.log(this.fields)
    },

    // 删除子字段
    removeSubField(index) {
      this.newField.nestedFields.splice(index, 1);
    },

    deleteField(fieldToDelete) {
      const fieldName = this.fields.findIndex(fieldName => fieldName === fieldToDelete);
      if (fieldName !== '') {
        // 删除字段及其子字段
        this.fields.splice(fieldName, 1);  // 删除当前字段
        this.$message.success('字段已删除');
      }
    },

    saveConfig() {
      // 遍历 fields 并构建字段列表
      this.fields.forEach(field => {
        if (field.nestedFields && field.nestedFields.length) {
          // 嵌套字段
          this.newPrompt += `- **${field.fieldName}**：包括：\n`;
          field.nestedFields.forEach(subField => {
            this.newPrompt += `  - ${subField.fieldName}\n`;
          });
        } else {
          // 普通字段
          this.newPrompt += `- **${field.fieldName}**\n`;
        }
      });

      this.newPrompt += this.newPromptend
      this.$message.success("配置已更新！");
      console.log("新的prompt：", this.newPrompt);
    },

    exportToExcel() {
      let extractedFields = '';
      if (this.extractMode === "auto") {
        extractedFields = this.selectedFile.ExtractedDefaultField
      } else if (this.extractMode === "custom") {
        extractedFields = this.selectedFile.ExtractedCustomField
      };
      if (!extractedFields.length) {
        console.log(this.selectedFile)
        this.$message.warning('没有可导出的数据');
        return;
      }

      const exportData = extractedFields
        .map(row => ({
          字段名: '　'.repeat(row.level) + row.fieldName, // 按照 level 添加缩进
          值: row.fieldValue
        }));

      const ws = XLSX.utils.aoa_to_sheet([
        ['字段名', '值'],
        ...exportData.map(item => [item.字段名, item.值])
      ]);

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "字段提取");

      const imagePath = this.selectedFile.thumbnail;// 如: "/发票/发票1.jpg"
      // 提取文件名（不带扩展名）
      const fileNameWithExt = imagePath.split('/').pop(); // => "发票1.jpg"
      const fileName = fileNameWithExt.split('.').slice(0, -1).join('.'); // => "发票1"

      // 构造最终文件名
      const excelFileName = `${fileName}_${this.extractMode}.xlsx`;
      XLSX.writeFile(wb, excelFileName);
    },

    // 抽取标准字段

    matchedStandardField(index) {
      // console.log(this.standardFields)
      return this.standardFields.find(item => item.index === index);
    },

    buildFieldPath(allFields, currentField) {
      const path = [currentField.fieldName];
      let parentIndex = currentField.index - 1;

      // 向上查找父级字段（level 更高）
      while (parentIndex >= 0) {
        const parentField = allFields[parentIndex];
        if (parentField && parentField.level < currentField.level) {
          path.unshift(parentField.fieldName); // 把父级加到前面
          break; // 找到最近的一个父级即可
        }
        parentIndex--;
      }

      return path.join(' > ');
    },

    // 字段确认处理
    handleFieldConfirm(row, extracteddefaultfield) {
      const updatedExtractedFields = extracteddefaultfield.map(item => {
        if (item.index === row.index) {
          return {
            ...item,
            fieldValue: row.fieldValue
          };
        }
        return item;
      });

      // 更新确认状态，标记该字段为已确认
      const fieldKey = `${row.fieldName}-${row.index}`;
      this.confirmedFields = {
        ...this.confirmedFields,
        [fieldKey]: true
      };

      this.$message.success(`字段 "${row.fieldName}-${row.index}" 已确认`);
      console.log("更新后的提取字段：",extracteddefaultfield)
    },
     
    // 字段值变化处理
    handleFieldValueChange(row) {
      // 当字段值发生变化时，重置确认状态
      const fieldKey = `${row.fieldName}-${row.index}`;
      // 使用新对象来触发响应式更新
      this.confirmedFields = {
        ...this.confirmedFields,
        [fieldKey]: false
      };
    },

    async confirmAutoExtraction(file_id, extracteddefaultfield) {
      if (!this.selectedFile) {
        this.$message.warning('请先选择一个文件');
        return;
      }
      // 显示确认对话框
      this.$confirm('确认提交当前的字段抽取结果吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          const res = await axios.post('http://localhost:8002/declaration/save-standard-field', {
            file_id: Number(file_id),
            standard_data: extracteddefaultfield
          }, {
            headers: {
              'Content-Type': 'application/json'
            }
          });
          this.$message.success('字段数据保存成功！');
        } catch (error) {
          console.error('保存字段数据失败:', error);
          this.$message.error('保存字段数据失败，请重试');
        }
      }).catch(() => {
        this.$message.info('已取消提交');
      });
    },
  }
}
</script>

<style scoped>
.el-card {
  height: 900px;
}
.declaration-preview {
  overflow: auto; /* 内容过多时滚动 */
}
.declaration-extract {
  overflow: auto;
}
.nested-field {
  margin-left: 20px;
}
.upload-hint {
  border: 1px dashed #bbbec4;
  padding: 10px;
  margin-bottom: 10px;
}
.upload-hint:hover {
  border-color: #b2b5ba; /* 鼠标悬停时边框变深色 */
}
.file-item.selected {
  border: 2px solid #409EFF;
  border-radius: 2px;
}
.el-upload-dragger .el-upload__text em {
  color: #acafb2;
}
/* 已确认字段的绿色样式 */
.confirmed-field {
  background-color: #f0f9f0 !important;
  border-color: #67c23a !important;
}

.confirmed-field :deep(.el-input__wrapper) {
  background-color: #f0f9f0 !important;
  border-color: #67c23a !important;
  box-shadow: 0 0 0 1px #67c23a inset !important;
}

.confirmed-field :deep(.el-input__inner) {
  background-color: #f0f9f0 !important;
  color: #67c23a !important;
  font-weight: 500 !important;
}

.confirmed-field:focus :deep(.el-input__wrapper),
.confirmed-field.is-focus :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #67c23a inset !important;
}

/* 更强的样式覆盖 */
.confirmed-field input {
  background-color: #f0f9f0 !important;
  color: #67c23a !important;
  border-color: #67c23a !important;
  font-weight: 500 !important;
}

</style>