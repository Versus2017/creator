<template>
  <div class="upload-container">
    <Upload
      :multiple="false"
      :default-file-list="fileList"
      :show-file-list="false"
      accept="image/jpeg, application/pdf, image/png"
      :format="['jpg','jpeg','png', 'pdf']"
      :on-remove="handleRemove"
      :on-success="handleSuccess"
      :before-upload="beforeUpload"
      :headers="extraHeaders"
      :action="url"
      name="image"
    >
      <Button :style="{background:color,borderColor:color}"
              size="small" type="primary"
              @click="
              dialogVisible=true">
        上传图片
      </Button>
    </Upload>
  </div>
</template>

<script>
// import { getToken } from 'api/qiniu'

import { getCSRFToken } from '@/libs/util'

export default {
  name: 'EditorSlideUpload',
  props: {
    color: {
      type: String,
      default: '#1890ff'
    },
    url: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      dialogVisible: false,
      listObj: {},
      fileList: []
    }
  },

  computed: {
    extraHeaders () {
        return {
          'from-bo': true,
          'X-CSRF-TOKEN': getCSRFToken()
        }
      },
  },

  methods: {
    checkAllSuccess() {
      return Object.keys(this.listObj).every(item => this.listObj[item].hasSuccess)
    },
    handleSubmit() {
      const arr = Object.keys(this.listObj).map(v => this.listObj[v])
      if (!this.checkAllSuccess()) {
        this.$message('Please wait for all images to be uploaded successfully. If there is a network problem, please refresh the page and upload again!')
        return
      }
      this.$emit('successCBK', arr)
      this.listObj = {}
      this.fileList = []
      this.dialogVisible = false
    },
    handleSuccess(response, file) {
      console.log(file, '------ upload success', response)
      const uid = file.uid
      const objKeyArr = Object.keys(this.listObj)
      for (let i = 0, len = objKeyArr.length; i < len; i++) {
        if (this.listObj[objKeyArr[i]].uid === uid) {
          this.listObj[objKeyArr[i]].url = _.get(response, 'media.url')
          this.listObj[objKeyArr[i]].hasSuccess = true
        }
      }

      setTimeout(() => {
        this.handleSubmit()
      }, 200)
    },
    handleRemove(file) {
      const uid = file.uid
      const objKeyArr = Object.keys(this.listObj)
      for (let i = 0, len = objKeyArr.length; i < len; i++) {
        if (this.listObj[objKeyArr[i]].uid === uid) {
          delete this.listObj[objKeyArr[i]]
          return
        }
      }
    },
    beforeUpload(file) {
      const _self = this
      const _URL = window.URL || window.webkitURL
      const fileName = file.uid
      this.listObj[fileName] = {}
      return new Promise((resolve, reject) => {
        const img = new Image()
        img.src = _URL.createObjectURL(file)
        img.onload = function() {
          _self.listObj[fileName] = { hasSuccess: false, uid: file.uid, width: this.width, height: this.height }
        }
        resolve(true)
      })
    }
  }
}
</script>

<style lang="less" scoped>
.editor-slide-upload {
  margin-bottom: 20px;
  ::v-deep .el-upload--picture-card {
    width: 100%;
  }
}
</style>
