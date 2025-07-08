<template>
  <div id="documents">
    <el-row>
      <el-col :span="24">
        <el-card>
          <el-row :gutter="20">
            <!-- 左侧图表 -->
            <el-col :span="8">
              <div id="main" style="width: 100%; height: 300px;"></div>
            </el-col>
            <!-- 右侧表格 -->
            <el-col :span="12">
              <h3>总文件数量：{{ totalRecords }}</h3>
            </el-col>
          </el-row>
        </el-card>
        
      </el-col>
    </el-row>
    

    <el-row>
      <el-col :span="24">
        <el-card class="table-card">
          <div class="flex gap-4 mb-4 items-center">
            <el-input v-model="input1" style="width: 240px" placeholder="文件名称" :suffix-icon="Search"/>
            <el-button type="primary">
              <el-icon><Search /></el-icon>
            </el-button>
            <el-button type="primary" @click="dialogVisible = true" >
              上传<el-icon class="el-icon--right" ><Upload /></el-icon>
            </el-button>
            <el-button type="primary" @click="handleBatchDelete">
              <el-icon><Delete /></el-icon>
            </el-button>
            <el-button type="primart" @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="table-container">
            <el-table :data="paginatedFiles" style="width: 100%" @row-click="handleRowClick" @selection-change="handleSelectionChange" :scroll-container="'.table-container'">
              <el-table-column type="selection" width="55" />
              <el-table-column label="文件名称" width="300">
                <template #default="scope">
                  <div style="display: flex; align-items: center;">
                    <el-image 
                      :src="`http://localhost:8002/api/file${scope.row.thumbnail}`" 
                      style="width: 50px; height: 50px; margin-right: 10px; border-radius: 4px;" 
                      fit="cover"
                      :preview-src-list="[`http://localhost:8002/api/file${scope.row.thumbnail}`]"
                      preview-teleported
                    />
                    <span>{{ scope.row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="check" label="核对">
                <template #default="scope">
                <el-tag :type="scope.row.check ? 'success' : 'warning'">
                  {{ scope.row.check ? '已核对' : '未核对' }}
                </el-tag>
              </template>
              </el-table-column>
              <el-table-column label="识别状态">
                <template #default="scope">
                  <el-tag 
                    :type="getExtractionStatusType(scope.row)"
                    size="small"
                  >
                    <el-icon v-if="getExtractionStatus(scope.row.name) === 'extracting'" class="rotating" style="margin-right: 4px;">
                      <Loading />
                    </el-icon>
                    {{ getExtractionStatusText(scope.row) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="type" label="文件类型" />
              <el-table-column prop="upload_date" label="上传日期" />
              <el-table-column prop="modified_date" label="修改日期" />
            </el-table>
          </div>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 30, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="filteredFiles.length"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
          
        </el-card>
      </el-col>
    </el-row>

    <!-- 文件上传弹窗 -->
    <el-dialog v-model="dialogVisible" title="文件上传" width="550px" align-center :before-close="handleClose">
      <div class="upload-container">
        <el-switch v-model="useOCRSwitch" @change="toggleOCR" />
            <span style="margin-left: 10px;">启用 OCR 辅助</span>
        <!-- 文件上传区域 -->
        <el-upload ref="uploadRef" drag :auto-upload="false" :multiple="true" :limit="10" :accept="'.png,.jpg,.jpeg,.pdf,.zip,.rar'" :before-upload="beforeUpload" :show-file-list="true" :on-change="handleFileChange">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">             
            点击上传文件 / 拖拽文件到此处<br/>
            <em>支持 png, jpg, jpeg, pdf, zip, rar 等格式，上传单个文件大小不超过 50M</em>
          </div>
        </el-upload>

      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">取消</el-button>
          <el-button type="primary" @click="confirmUpload" :loading="uploading" :disabled="pendingFiles.length === 0">{{ uploading ? '上传中...' : '确认上传' }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>

</template>
<script>
import axios from 'axios'
import * as XLSX from 'xlsx';
import * as echarts from "echarts";

export default {
  name: 'Documents',
  data () {
    return {
      dialogVisible: false,
      chartData: [],   // 存储饼图数据 [{value: xxx, name: 'xxx'}, ...]
      totalRecords: 0,  // 总文件数量
      myChart: null,   // ECharts实例
      resizeHandler: null,  // 窗口大小变化处理函数
      pendingFiles: [],  // 待上传的文件列表
      uploading: false,  
      totalFiles: [],
      useOCRSwitch: true, // 控制是否使用 OCR，默认启用
      processingFiles: [], // 处理中的文件列表

      currentPage: 1,
      pageSize: 10,

      input1: '',
      selectedRows: [], // 选中的行数据

      refreshTimer: null,

      typeToEndpoint: {
        '发票': 'invoice',
        '合同': 'contract',
        '报关单': 'declaration',
        '提单': 'landing'
      },
      uploadDirMap: {
        '发票': '../backend/upload/发票',
        '合同': '../backend/upload/合同',
        '报关单': '../backend/upload/报关单',
        '提单': '../backend/upload/提单'
      },
      prompts: {
        "发票": `
        请分析图片内容，并提取其中包含的所有指定字段及对应的值，以 JSON 格式输出。
        要求如下：
        1. 每个字段作为 JSON 的一个键；
        2. 每个字段的值为图片中对应的语义内容；
        3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
        4. 不需要包含位置信息、类型或其他元数据；

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
      '报关单': `
        请分析图片内容，并提取其中包含的所有指定字段及对应的值，以 JSON 格式输出。
        要求如下：
        1. 每个字段作为 JSON 的一个键；
        2. 每个字段的值为图片中对应的语义内容；
        3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
        4. 不需要包含位置信息、类型或其他元数据；
        
        ### 需要提取的字段：
        - **单据种类**
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
      '合同': `
        请分析图片内容，并提取其中包含的所有指定字段及对应的值，以 JSON 格式输出。
        要求如下：
        1. 每个字段作为 JSON 的一个键；
        2. 每个字段的值为图片中对应的语义内容；
        3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
        4. 不需要包含位置信息、类型或其他元数据；

        ### 需要提取的字段：
        - **单据种类**：合同种类
        - **合同号**：例如 "023746123"
        - **日期**：例如 "20200101"
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
        - **商品信息**：如果有多条商品信息，用数组存储，每条商品信息是一个对象,包括：
          - 商品名称：只需要商品名称删除其他无关信息
          - 数量
          - 单价
          - 总价
        - **商品总数量**: 所有商品的数量之和
        - **商品总价格**: 所有商品的总价之和

        ### 示例输出格式：
        {
          "单据种类": "结转合同",
          "合同号": "023746123",
          "日期": "20200101",
          "卖方信息": {
            "公司名称": "Seller Company",
            "地址": "Suzhou city, Jiangsu province",
            "电话": "",
            "传真": ""
          },
          "买方信息": {
            "公司名称": "Buyer Company",
            "地址": "Suzhou city, Jiangsu province",
            "电话": "",
            "传真": ""
          },
          "商品信息": [
            {
              "商品名称": "Flower",
              "数量": "100件4422千克",
              "单价": "100.61",
              "总价": "3452.34"
            },
            {
              "商品名称": "其他商品",
              "数量": "100件1100千克",
              "单价": "10 USD",
              "总价": "1000 USD"
            }
          ],
          "商品总数量": “10,100”,
          "商品总价格": ”1100 USD“,
        }
      `,
      '提单': `
        请分析图片内容，并提取其中包含的所有指定字段及对应的值，以 JSON 格式输出。
        要求如下：
        1. 每个字段作为 JSON 的一个键；
        2. 每个字段的值为图片中对应的语义内容；
        3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
        4. 不需要包含位置信息、类型或其他元数据；

        ### 需要提取的字段：
        - **单据种类**：提单的标题，例如 "BILL OF LOADING"
        - **提单号**：例如 "023746123"
        - **收货人信息**
          - 公司名称
          - 地址
        - **发货人信息**
          - 公司名称
          - 地址
        - **通知方**
          - 公司名称
          - 地址
        - **运输方式**
        - **船只信息和编号**
        - **船舶航次信息**
        - **装货港**: 例如 "shanghai"
        - **卸货港**: 例如 "shanghai"
        - **货物信息**：如果有多条货物信息，用数组存储，每条货物信息是一个对象,包括：
          - 货物名称
          - 重量
          - 货物体积
        - **运费**
        - **装船日期**: 例如 "20240101"
        - **签发地点与日期**

        ### 示例输出格式：
        {
          "单据种类": "BILL OF LOADING",
          "提单号": "023746123",
          "收货人信息": "SUZHOU Company",
          "发货人信息": "Shanghai Company",
          "通知方": "SUZHOU Company",
          "运输方式": "OCEAN VESSEL",
          "船只信息和编号": "CHENGXING 3",
          "船舶航次信息": "H876N",
          "装货港": "Shanghai",
          "卸货港": "Suzhou",
          "货物信息": [
            {
              "货物名称": "Flower",
              "重量": "1000",
              "货物体积": "50"
            },
            {
              "货物名称": "其他商品",
              "重量": "100",
              "货物体积": "50"
            }
          ],
          "运费": 
          "装船日期": “20240101”,
          "签发地点与日期": ”20240101 Shanghai“,
        }
      `
      }
    }
  },
  mounted () {
    this.fetchChartData();
    this.fetchAllRecords();
    this.startAutoRefresh();
  },
  watch: {
    // 监听搜索输入，改变时重置到第一页
    input1() {
      this.currentPage = 1;
    }
  },
  methods: {
    async fetchChartData() {
      try {
        const res = await axios.get('http://localhost:8002/documents/total-records');
        const tableCounts = res.data.total_records;
        const pieData = Object.entries(tableCounts).map(([name, value]) => ({
          name,
          value
        }));
        this.chartData = pieData;
        this.totalRecords = res.data.counts;

        this.renderChart();
      } catch (error) {
        console.error('获取数据失败:', error);
      }
    },

    renderChart() {
      const chartDom = document.getElementById('main');
      const myChart = echarts.init(chartDom);
      let option;
      if (this.totalRecords > 0) {
        option = {
          tooltip: {
            trigger: 'item'
          },
          legend: {
            orient: 'vertical',
            left: 'left'
          },
          series: [
            {
              name: '文件类型分布',
              type: 'pie',
              radius: '50%',
              data: this.chartData,
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              }
            }
          ]
        };
      } else {
        option = {
          tooltip: {
            trigger: 'item'
          },
          legend: {
            orient: 'vertical',
            left: 'left'
          },
          series: [
            {
              name: '文件类型分布',
              type: 'pie',
              radius: '50%',
              data: [
                {
                  value: 100,
                  name: '暂无数据',
                  itemStyle: {
                    color: '#e0e0e0' // 灰色
                  },
                  label: {
                    show: true,
                    position: 'center',
                    formatter: '暂无数据',
                    fontSize: 16,
                    color: '#999'
                  },
                  labelLine: {
                    show: false
                  }
                }
              ],
              emphasis: {
                disabled: true // 禁用鼠标悬停效果
              }
            }
          ]
        };
      }
      myChart.setOption(option);
      // 自适应窗口大小
      window.addEventListener('resize', () => {
        myChart.resize();
      });
    },

    async fetchAllRecords() {
      try {
        const res = await axios.get('http://localhost:8002/documents/all-records');
        this.totalFiles = res.data.records;
      } catch (error) {
        console.error('获取所有记录失败:', error);
      }
    },

    handleRowClick(row, column, event) {
      // 点击选择框列时，不触发跳转
      if (column.type === 'selection') {
        return;
      }
      
      // 根据文件类型跳转到对应页面
      const routeMap = {
        '发票': 'Invoice',
        '合同': 'Contract', 
        '报关单': 'Declaration',
        '提单': 'Landing'
      };
      
      const routeName = routeMap[row.type];
      if (routeName) {
        this.$router.push({
          name: routeName,
          params: { fileId: row.id }
        });
      }
    },

    handleSelectionChange(selection) {
      this.selectedRows = selection;
    },

    async handleBatchDelete() {
      if (this.selectedRows.length === 0) {
        this.$message.warning('请选择要删除的文件');
        return;
      }

      const message = `确定要删除选中的 ${this.selectedRows.length} 个文件吗？`;
      try {
        await this.$confirm(message, "批量删除确认", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning"
        });

        // 按文件类型分组，调用不同的删除接口
        const deletePromises = []

        this.selectedRows.forEach(row => {
          const endpoint = this.typeToEndpoint[row.type];
          const uploadDir = this.uploadDirMap[row.type];
          if (endpoint && uploadDir) {
            deletePromises.push(
              axios.post(`http://localhost:8002/${endpoint}/delete-file`, {
                filename: row.name,
                uploadDir: uploadDir,
                file_id: row.id
              }, {
                headers: {
                  'Content-Type': 'multipart/form-data'
                }
              })
            );
          }
        });

        await Promise.all(deletePromises);
        
        this.$message.success(`成功删除 ${this.selectedRows.length} 个文件`);
        
        // 刷新数据
        await this.fetchAllRecords();
        await this.fetchChartData();
        
        // 清除选中状态
        this.selectedRows = [];
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error);
          this.$message.error('删除失败，请重试');
        }
      }
    },

    // 分页大小改变
    handleSizeChange(newSize) {
      this.pageSize = newSize;
      this.currentPage = 1; // 重置到第一页
    },

    // 当前页改变
    handleCurrentChange(newPage) {
      this.currentPage = newPage;
    },

    // 文件上传前的验证
    beforeUpload(file) {
      const allowedTypes = ['.png', '.jpg', '.jpeg', '.pdf', '.zip', '.rar'];
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
      
      if (!allowedTypes.includes(fileExtension)) {
        this.$message.error('只能上传图片、PDF或压缩包文件');
        return false;
      }
      
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        this.$message.error('文件大小不能超过 50MB!');
        return false;
      }
      
      return true;
    },

    handleFileChange(file, fileList) {
      if (this.beforeUpload(file.raw)) {
        this.pendingFiles.push(file.raw);
      }
    },

    handleClose() {
      this.pendingFiles = [];
      this.uploading = false;
      this.dialogVisible = false;
      this.$nextTick(() => {
        if (this.$refs.uploadRef) {
          this.$refs.uploadRef.clearFiles();
        }
      });
    },

    async confirmUpload() {
      if (this.pendingFiles.length === 0) {
        this.$message.warning('请先选择要上传的文件');
        return;
      }
      this.uploading = true;
      //console.log("filesToUpload",filesToUpload);
      let successCount = 0;
      let failCount = 0;

      try {
        // 逐个上传文件
        for (const file of this.pendingFiles) {
          try {
            const uploadResult = await this.uploadSingleFile(file);
            console.log("uploadResult",uploadResult);
            if (uploadResult) {
              successCount += uploadResult.file.length;
              this.startExtraction(uploadResult,file);
            }   
          } catch (error) {
            console.error(`文件 ${file.name} 上传失败:`, error);
            failCount++;
          }
        }

        // 显示上传结果
        if (successCount > 0) {
          this.$message.success(`成功上传 ${successCount} 个文件${failCount > 0 ? `，失败 ${failCount} 个` : ''}`);
          // 刷新数据
          await this.fetchAllRecords();
          await this.fetchChartData();
        }

        if (failCount > 0 && successCount === 0) {
          this.$message.error(`上传失败，共 ${failCount} 个文件上传失败`);
        }

        // 清空待上传文件并关闭弹窗
        this.pendingFiles = [];
        this.dialogVisible = false;

      } catch (error) {
        console.error('批量上传失败:', error);
        this.$message.error('上传失败，请重试');
      } finally {
        this.uploading = false;
      }
    },

    async uploadSingleFile(file) {
      const formData = new FormData();
      formData.append('file', file);
      try{
        const response = await axios.post('http://localhost:8002/documents/smart-upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        console.log("response",response);
        return response.data;
      } catch (error) {
        console.error('上传失败:', error);
        return error;
      }
    },

    async startExtraction(uploadResult,file){
      if (!uploadResult || !uploadResult.file) {
        return;
      }
      console.log("uploadResult",uploadResult);
      console.log("file",file);
      for (const [upload_file, document_type] of uploadResult.file) {
          this.processingFiles.push({
          fileName: upload_file.name,
          fileId: upload_file.id,
          status: 'extracting'
        });
        try {
          // 构建请求参数
          const extractPayload = {
            image_url: upload_file.thumbnail, // 使用上传返回的文件路径
            use_ocr: this.useOCRSwitch,
            prompt: this.prompts[document_type] // 使用默认提示词
          };

          console.log("upload_file",upload_file);

          // 异步调用 extract API，不等待结果
          this.callExtractAPI(extractPayload, this.typeToEndpoint[document_type], upload_file.id, upload_file.name);
          
        } catch (error) {
          console.error(`文件 ${file.name} 字段提取启动失败:`, error);
          // 从处理列表中移除
          this.processingFiles = this.processingFiles.filter(
            item => item.fileName !== upload_file.name
          );
        }
      }
    },
    
    async callExtractAPI(payload, fileType, fileId, fileName){
      try {
        const res_load = await axios.post(`http://localhost:8002/${fileType}/open-loading`, {
          file_id: Number(fileId),
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const response = await axios.post('http://localhost:8002/api/extract', payload, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        console.log(`文件字段提取成功`,response.data);

        const res_save = await axios.post(`http://localhost:8002/${fileType}/save-extracted`, {
          file_id: Number(fileId),
          extracted_data: this.parseJsonToTable(response.data)
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });

        const res_close = await axios.post(`http://localhost:8002/${fileType}/close-loading`, {
          file_id: Number(fileId),
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });

        const processingIndex = this.processingFiles.findIndex(
          item => item.fileName === fileName
        );
        if (processingIndex !== -1) {
          this.processingFiles[processingIndex].status = 'completed';
        }

      } catch (error) {
        console.error('提取字段失败:', error);
        // 更新处理状态为失败
        const processingIndex = this.processingFiles.findIndex(
          item => item.fileName === fileName
        );
        if (processingIndex !== -1) {
          this.processingFiles[processingIndex].status = 'failed';
        }
        this.$message.error(`文件字段提取失败: ${error.response?.data?.detail || error.message}`);
      } finally {
        this.processingFiles = this.processingFiles.filter(
          item => item.fileName !== fileName
        );
      }
    },

    toggleOCR(value) {
      this.useOCRSwitch = value;
    },

    // 获取文件的提取状态
    getExtractionStatus(row) {
      const defaultFields = Array.isArray(row.ExtractedDefaultField) ? row.ExtractedDefaultField : [];
      const customFields = Array.isArray(row.ExtractedCustomField) ? row.ExtractedCustomField : [];
      if (defaultFields.length > 0 || customFields.length > 0) {
        return 'completed';
      } else if (row.loading_auto === true) {
        return 'extracting';
      } else {
        return 'pending';
      }
    },

    // 获取提取状态的文本
    getExtractionStatusText(row) {
      const status = this.getExtractionStatus(row);
      const statusMap = {
        'extracting': '识别中',
        'completed': '已完成',
        'pending': '未开始',
      };
      return statusMap[status] || '未开始';
    },

    // 获取标签的类型（颜色）
    getExtractionStatusType(row) {
      const status = this.getExtractionStatus(row);
      const typeMap = {
        'extracting': 'warning',
        'completed': 'success',
        'pending': 'primary'
      };
      return typeMap[status] || 'primary';
    },

    parseJsonToTable(data, parentKey = '', level = 0, indexCounter = { value: 1 }) {
      let result = []
      for (const key in data) {
        const value = data[key]
        const newKey = parentKey ? `${parentKey}-${key}` : key

        if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
          result.push({
            fieldName: key,
            fieldValue: '',
            index: indexCounter.value++, // 使用局部计数器
            level: level
          })
          result = result.concat(this.parseJsonToTable(value, newKey, level + 1, indexCounter))
        } else if (Array.isArray(value)) {
          value.forEach((item, index) => {
            if (typeof item === 'object') {
              result.push({
                fieldName: `${newKey} ${index + 1}`,
                fieldValue: '',
                index: indexCounter.value++, // 使用局部计数器
                level: level
              })
              result = result.concat(this.parseJsonToTable(item, `${newKey}-${index}`, level + 1, indexCounter))
            } else {
              result.push({
                fieldName: `${newKey}-${index}`,
                fieldValue: item,
                index: indexCounter.value++, // 使用局部计数器
                level: level + 1
              })
            }
          })
        } else {
          result.push({
            fieldName: key,
            fieldValue: value,
            index: indexCounter.value++, // 使用局部计数器
            level: level
          })
        }
      }

      return result
    },

    handleRefresh() {
      this.fetchAllRecords();
    },
    startAutoRefresh() { 
      this.refreshTimer = setInterval(() => {
        this.fetchAllRecords();
        this.fetchChartData();
      }, 10000); // 每10秒刷新一次
    },
  },
  computed: {
    // 过滤后的文件（用于分页总数计算）
    filteredFiles() {
      if (this.input1.trim()) {
        return this.totalFiles.filter(file => 
          file.name.toLowerCase().includes(this.input1.toLowerCase()) ||
          file.type.toLowerCase().includes(this.input1.toLowerCase())
        );
      }
      return this.totalFiles;
    },

    // 分页后的文件数据
    paginatedFiles() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.filteredFiles.slice(start, end);
    }
  }
}

</script>

<style scoped>
.upload-container {
  text-align: center;
}

.upload-area {
  border: 2px dashed #ccc;
  border-radius: 10px;
  padding: 40px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.upload-area:hover {
  background-color: #f0f9eb;
}

.upload-area i {
  font-size: 48px;
  color: #409eff;
}

.table-card {
  height: 580px;
  display: flex;
  flex-direction: column;
}

.table-card :deep(.el-card__body) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.table-container {
  flex: 1;
  overflow: auto;
}

.pagination-container {
  padding: 20px 0 10px 0;
  display: flex;
  justify-content: center;
}

.rotating {
  animation: rotate 1s linear infinite;
  color: #e6a23c;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>