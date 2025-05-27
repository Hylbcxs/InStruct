<template>
    <div id="test">
      <el-row :gutter="20">
        <!-- 左侧文件列表 -->
        <el-col :span="4" class="fileList">
          <el-card shadow="hover">
            <div slot="header">
              <span>我的文件</span>
              <el-switch v-model="multiSelect" @change="handleSwitchChange"/>
            </div>
            <!-- 添加上传文件提示区域 -->
            <el-upload class="upload-hint" :action="`http://localhost:8002/invoice/upload`" multiple="true" :limit="10" :on-success="handleUploadSuccess" :accept="'.png,.jpg,.jpeg,.doc,.pdf'" :before-upload="beforeUpload" :show-file-list="false" :data="{ uploadDir: this.uploadDirectory }" :auto-upload="true">  
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
          <el-card shadow="hover" class="test-preview" style="display: flex; align-items: center; justify-content: center;">
            <div v-if="!(selectedFile?.thumbnail)">
              <el-upload drag :http-request="customUploadRequest" :multiple="true" :limit="10" :on-success="handleUploadSuccess" :accept="'.png,.jpg,.jpeg,.doc,.pdf'" :before-upload="beforeUpload" :show-file-list="false">
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">             
                  点击上传文件 / 拖拽文件到此处<br/>
                  <em>支持 png, jpg, jpeg, doc, pdf 等格式，上传单个文件大小不超过 50M</em>
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
          <el-card shadow="hover" class="test-extract">
            <div slot="header">
              <el-radio-group v-model="extractMode" @change="handleExtractModeChange">
                <el-radio-button label="auto">智能抽取</el-radio-button>
                <el-radio-button label="custom">自定义抽取</el-radio-button>
                <!-- <el-radio-button label="result">JSON 结果</el-radio-button> -->
              </el-radio-group>
              <div style="float: right;">
                <el-switch v-model="useOCRSwitch" @change="toggleOCR" />
                <span style="margin-right: 20px;">启用 OCR 辅助</span>
                <el-button type="primary" @click="exportToExcel">导出结果</el-button>
                <el-button type="primary" @click="reExtract">重新抽取</el-button>
              </div>
  
              <div v-if="extractMode === 'auto'">
                <el-table :data="selectedFile ? selectedFile.ExtractedDefaultField : extractedDefaultFields" stripe v-loading="selectedFile ? selectedFile.loading_auto : loading_auto" :element-loading-text="selectedFile ? selectedFile.loadingText : loadingText" element-loading-spinner="el-icon-loading">
                  <el-table-column label="字段名" width="200">
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
                </el-table>
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
                <el-table :data="selectedFile ? selectedFile.ExtractedDefaultField : extractedDefaultFields" stripe>
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
  import oboe from 'oboe'
  import * as XLSX from 'xlsx';
  
  export default {
    name: 'Test',
    data () {
      return {
        TestPrompt: `
          请分析图片内容和ocr识别结果，提取其中包含的所有指定字段及对应的值，并以 JSON 格式输出。
          要求如下：
          1. 每个字段作为 JSON 的一个键；
          2. 每个字段的值为图片中对应的语义内容；
          3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
          4. 不需要包含位置信息、类型或其他元数据；
          5. 注意：请只输出 JSON，不要添加任何解释或文本说明， 确保字段尽可能完整、语义准确, 保持 JSON 结构规范;

          ### 需要提取的字段：
          - **单据种类**：发票的标题，例如 "INVOICE"
          - **发票编号**：例如 "023746123"
          - **发票日期**：例如 "2020/01/01"
          - **卖方信息**：包括：
              - 公司名称: 有中文就使用中文
              - 地址
              - 电话
              - 传真
          - **买方信息**：包括：
              - 公司名称：有中文就使用中文
              - 地址
              - 电话
              - 传真
          - **货物信息**：如果有多条货物信息，用数组存储，每条货物信息是一个对象,包括：
              - 货物名称: 只提取货物名称，不包含机型等
              - 数量
              - 单价
              - 总价
          - **货物总数量**: 所有货物的数量之和
          - **货物总价**: 所有货物的总价之和

          ### 示例输出格式：
          {
              "单据种类": "INVOICE",
              "发票编号": "023746123",
              "发票日期": "2020/01/01",
              "卖方信息": {
              "公司名称": "Seller Company",
              "地址": "Suzhou city, Jiangsu province",
              "电话": "15062330857",
              "传真": "2649412"
              },
              "买方信息": {
              "公司名称": "Buyer Company",
              "地址": "Suzhou city, Jiangsu province",
              "电话": "15062330857",
              "传真": "2649412"
              },
              "货物信息": [
              {
                  "货物名称": "Flower",
                  "数量": "10,000",
                  "单价": "0.01 USD",
                  "总价": "100 USD"
              },
              {
                  "货物名称": "其他商品",
                  "数量": "100",
                  "单价": "10 USD",
                  "总价": "1000 USD"
              }
              ],
              "货物总数量": “10,100”,
              "货物总价格": ”1100 USD“,
          }
        `,
        newPrompt: `
        请分析图片内容和ocr识别结果，提取其中包含的所有指定字段及对应的值，并以 JSON 格式输出。
        要求如下：
        1. 每个字段作为 JSON 的一个键；
        2. 每个字段的值为图片中对应的语义内容；
        3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
        4. 不需要包含位置信息、类型或其他元数据；
        5. 注意：请只输出 JSON，不要添加任何解释或文本说明， 确保字段尽可能完整、语义准确, 保持 JSON 结构规范;
  
        ### 需要提取的字段：
        `,
        newPromptend: `
        ### 示例输出格式：
        {
          "单据种类": "INVOICE",
          "卖方信息": {
            "公司名称": "Seller Company",
            "地址": "Suzhou city, Jiangsu province",
            "电话": "15062330857",
            "传真": "2649412"
          },
          "货物信息": [
            {
              "货物名称": "Flower",
              "数量": "10,000",
              "单价": "0.01 USD",
              "总价": "100 USD"
            },
            {
              "货物名称": "其他商品",
              "数量": "100",
              "单价": "10 USD",
              "总价": "1000 USD"
            }
          ]
        }
        `,
  
        fields: [
          { fieldName: '单据种类', fieldType: '发票的标题，例如 "INVOICE"' },
          { fieldName: '发票编号', fieldType: '例如 "023746123"' },
          { fieldName: '发票日期', fieldType: '例如 "2020/01/01"' },
          {
            fieldName: "卖方信息",
            fieldType: "",
            nestedFields: [
              { fieldName: "公司名称", fieldType: "" },
              { fieldName: "地址", fieldType: "" },
              { fieldName: "电话", fieldType: "" },
              { fieldName: "传真", fieldType: ""},
            ],
          },
          {
            fieldName: "买方信息",
            fieldType: "",
            nestedFields: [
              { fieldName: "公司名称", fieldType: "" },
              { fieldName: "地址", fieldType: "" },
              { fieldName: "电话", fieldType: "" },
              { fieldName: "传真", fieldType: ""},
            ],
          },
          {
            fieldName: "货物信息",
            fieldType: "如果有多条货物信息，用数组存储，每条货物信息是一个对象",
            nestedFields: [
              { fieldName: "货物名称", fieldType: "" },
              { fieldName: "数量", fieldType: "" },
              { fieldName: "单价", fieldType: "" },
              { fieldName: "总价", fieldType: "" },
            ],
          },
          { fieldName: '货物总数量', fieldType: '所有货物的数量之和' },
          { fieldName: '货物总价', fieldType: '所有货物的总价之和' },
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
        currentTestImage: '',
        // uploadDirectory: '../frontend/public/测试',
        uploadDirectory: '../backend/upload/测试',
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
        useOCRSwitch: true // 控制是否使用 OCR，默认启用
      }
    },
    async created() {
      await this.fetchFiles();
    },
    methods: {
      async handleSelect(key) {
        const idx = Number(key)
        // 根据选中的文件名更新 selectedFile 和 currentInvoiceImage
        console.log(this.files)
        this.selectedFile = this.files.find(file => file.id === idx);
        console.log("当前选择：",this.selectedFile)
        if (this.selectedFile) {
          this.currentTestImage = this.selectedFile.thumbnail;
  
          if (this.extractMode === 'auto' || this.extractMode === "result") {
            this.extractedDefaultFields = [];
            const res = await axios.get(`http://localhost:8002/invoice/extracted-field/${idx}`);
            if (res.data.extracted_data) {
              this.selectedFile.ExtractedDefaultField = res.data.extracted_data;
            }        
          } else if (this.extractMode === 'custom') {
            // 切换图片时清空默认字段缓存
            this.extractedCustomFields = [];
            const res = await axios.get(`http://localhost:8002/invoice/extracted-custom-field/${idx}`);
            if (res.data.extracted_data) {
              this.selectedFile.ExtractedCustomField = res.data.extracted_data;
            }  
          }
          
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
              axios.post('http://localhost:8002/invoice/clear-files', {
                uploadDir: this.uploadDirectory
              },{
                headers: {
                  'Content-Type': 'application/json'
                }
              });
  
              this.selectedFile = null;
              this.currentTestImage = '';
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
            await axios.post('http://localhost:8002/invoice/delete-file', {
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
              this.currentTestImage = '';
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
        const res = await fetch('http://localhost:8002/invoice/files');
        const data = await res.json();
        console.log(data);
        this.files = data;
      },
      async fetchExtractedData(nowPrompt, fileObj) {
        // if (!this.currentInvoiceImage || !fileObj.thumbnail) {
        //   this.$message.warning('请先选择一张图片')
        //   return
        // }
        console.log("fileObj:", fileObj)
        console.log("fileObj.id:", fileObj.id)
  
        try {        
          if (this.extractMode === "auto") {
            fileObj.loading_auto = true;
            fileObj.loadingText = '正在抽取字段...';
            const res = await axios.post('http://localhost:8002/invoice/open-loading', {
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
  
          // 获取 reader
          // const reader = res.body.getReader();
          // const decoder = new TextDecoder();
          // let result = '';
  
          // while (true) {
          //   const { done, value } = await reader.read();
          //   if (done) break;
  
          //   // 接收到一块数据
          //   const chunk = decoder.decode(value, { stream: true });
          //   result += chunk;
  
          // }
          // console.log(result)
          // // 尝试匹配 ```json ... ```
          // const markdownMatch = result.match(/```json\n([\s\S]*?)\n```/);
          // if (markdownMatch?.[1]) {
          //   result = markdownMatch[1];
          // }
          // 尝试解析当前拼接的 JSON 数据
         // const parsed = JSON.parse(result);
          const parsed = await res.json();
          console.log("结果是：", parsed)
          // 先重置全局 index
          this.globalIndex = 0;
          // console.log(parsed)
          // 更新表格数据
          if (this.extractMode === "auto") {
            const res = await axios.post('http://localhost:8002/invoice/save-extracted', {
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
            const res = await axios.post('http://localhost:8002/invoice/save-custom-extracted',{
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
          // this.loading_auto = false; // 关闭加载动画
          // this.loading_custom = false;
          fileObj.loading_auto = false;
          fileObj.loadingText = '';
          const res = await axios.post('http://localhost:8002/invoice/close-loading', {
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
        let filename = ''
        let currentFile = ''
        if (!fileObj) {
          fileObj = this.selectedFile;
        }
        const idx = Number(fileObj.id)
        this.extractMode = mode;
        if (this.extractMode === "auto") {
          const res = await axios.get(`http://localhost:8002/invoice/extracted-field/${idx}`);
          if (res.data.extracted_data) {
            fileObj.ExtractedDefaultField = res.data.extracted_data;
          } else {
            await this.fetchExtractedData(this.TestPrompt, fileObj);
          
            // 否则才去请求模型
            // this.fetchExtractedData(this.TestPrompt, fileObj);
          }
          
        } else if (this.extractMode === "custom") {
          const res = await axios.get(`http://localhost:8002/invoice/extracted-custom-field/${idx}`);
          if (res.data.extracted_data) {
            fileObj.ExtractedCustomField = res.data.extracted_data;
          }
        } else if (this.extractMode === "result") {
          this.loadStandardJson(this.selectedFile);
        }
      },
  
      // 重新抽取
      reExtract() {
        if (this.extractMode === 'auto') {
          console.log(this.selectedFile)
          this.fetchExtractedData(this.TestPrompt, this.selectedFile)
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
  
        await axios.post('http://localhost:8002/invoice/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }).then(response => {
          //console.log("完整响应：", response);
          // this.selectedFile = response.data.file;
          // this.handleUploadSuccess();
        }).catch(error => {
          console.error('上传失败:', error);
        });
      },
  
      // 上传文件
      async handleUploadSuccess(response, file, fileList) {

        // 1. 更新文件列表
        this.fetchFiles();
        // 2. 将新文件加入队列
        // 1. 将新文件加入队列
        // this.processingQueue.push({
        //   fileData: response.file,
        //   rawFile: file
        // });

        // // 2. 触发队列处理（如果不在处理中）
        // if (!this.isProcessing) {
        //   this.processQueue();
        // }
        // await this.handleExtractModeChange("auto", response.file);
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

      async processQueue() {
        if (this.processingQueue.length === 0) return;
        
        this.isProcessing = true; // 加锁
        
        // 取出队列第一个任务
        const { fileData, rawFile } = this.processingQueue.shift();
        
        try {
          // 3. 顺序执行关键操作
          if (this.extractMode === "auto") {
            // fileObj.loading_auto = true;
            // fileObj.loadingText = '正在抽取字段...';
            const res = await axios.post('http://localhost:8002/invoice/open-loading', {
              file_id: Number(fileData.id),
            }, {
              headers: {
                'Content-Type': 'application/json'
              }
            });
            console.log("队列更新结果：",res)
          } else if (this.extractMode === "custom") {
            this.loading_custom = true;
          }
          this.selectedFile = fileData;
          await this.handleExtractModeChange("auto", this.selectedFile);
          
          // 4. 强制等待（确保状态更新）
          // await new Promise(resolve => this.$nextTick(resolve));
          
          // 5. 处理下一个任务
          this.processQueue();
        } catch (error) {
          console.error('文件处理失败:', error);
        } finally {
          this.isProcessing = false; // 解锁
        }
      },
  
      beforeUpload(file) {
        const isAllowedType = /\.(png|jpg|jpeg|doc|pdf)$/i.test(file.name);
        if (!isAllowedType) {
          this.$message.error('只能上传 .png, .jpg, .jpeg, .doc, .pdf 文件');
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
        console.log("新的字段", this.fields)
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
          extractedFields = this.extractedCustomFields
        };
        if (!extractedFields.length) {
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
  
        //const imagePath = this.currentInvoiceImage; // 如: "/发票/发票1.jpg"
        const imagePath = this.selectedFile.thumbnail;
        // 提取文件名（不带扩展名）
        const fileNameWithExt = imagePath.split('/').pop(); // => "发票1.jpg"
        const fileName = fileNameWithExt.split('.').slice(0, -1).join('.'); // => "发票1"
  
        // 构造最终文件名
        const excelFileName = `${fileName}_${this.extractMode}.xlsx`;
        XLSX.writeFile(wb, excelFileName);
      },
  
      // handleImageError(file) {
      //   // 加一个时间戳强制刷新图片
      //   file.thumbnail = `${file.thumbnail}?t=${Date.now()}`
      // }
      // 抽取标准字段
      async loadStandardJson(selectedFile=null) {
        try {
          let fileName = this.selectedFile.name; // 原始文件名：发票1.jpg
          let newFileName = fileName.replace(/\.\w+$/, '.json');
          const filename = "/standard/发票/" + newFileName;
          // console.log(filename)
          const response = await fetch(filename);
          if (!response.ok) throw new Error('无法加载标准 JSON 文件');
          const standardData = await response.json();
          this.standardFields = [];
          this.standardFields = standardData
          console.log(this.standardFields)
  
          const extractedFields = this.selectedFile.ExtractedDefaultField;
          // 调用后端接口进行准确率计算
          const accuracyRes = await fetch('http://localhost:8002/api/calculate-accuracy', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              standard_fields: this.standardFields,
              extracted_fields: extractedFields
            })
          });
  
          if (!accuracyRes.ok) throw new Error('准确率计算失败');
  
          const accuracyData = await accuracyRes.json();
  
          console.log('共对比字段数量:', accuracyData.totalCount);
          console.log('匹配字段数量:', accuracyData.matchCount);
          console.log('识别准确率:', accuracyData.accuracyRate + '%');
  
          // 可选：保存详细比对信息用于页面展示
          // this.accuracyDetails = accuracyData.details;
        } catch (err) {
          console.error(err);
        }
  
      },
  
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
      }
    }
  }
  </script>
  
  <style scoped>
  .el-card {
    height: 900px;
  }
  .test-preview {
    overflow: auto; /* 内容过多时滚动 */
  }
  .test-extract {
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
  
  </style>