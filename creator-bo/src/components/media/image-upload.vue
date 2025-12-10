<template>
  <div class="container">
    <div>{{ containerDesc }}</div>
    <div class="upload-list"
         :style="disabled ? {height: '70px', marginTop: '10px'} : null"
         v-for="item in uploadList">
      <template v-if="item.status === 'finished'">
        <div class="image-wrapper">
          <div class="image-tag" v-if="isPDF || itemIsPDF(item)">
            <div class="tag">PDF</div>
          </div>
          <div @click="handleView(item)"
               class="click">
            <img :src="getThumbnail(item)">
          </div>
          <div v-if="!disabled" class="manage-wrapper">
            <div class="replace" @click="handleEdit(item)">
              <img :src="require('../../assets/images/upload-replace.png')">
            </div>
            <div class="delete" @click="handleRemove(item)">
              <img :src="require('../../assets/images/upload-delete.png')">
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <Progress v-if="item.showProgress" :percent="item.percentage"
                  hide-info></Progress>
      </template>
    </div>
    <Upload v-show="showUploadButton"
            :class="disabled ? 'disabled-upload-block' : 'upload-block'"
            ref="upload"
            :show-upload-list="false"
            :default-file-list="defaultList"
            :on-success="handleSuccess"
            :on-error="handleError"
            accept="image/jpeg, application/pdf, image/png"
            :format="['jpg','jpeg','png', 'pdf']"
            :max-size="5120"
            :on-format-error="handleFormatError"
            :on-exceeded-size="handleMaxSize"
            :before-upload="handleBeforeUpload"
            :headers="extraHeaders"
            name="image"
            :multiple="canMultiple"
            type="drag"
            :action="`/v1/media?scope=${$config.isVotingSystem ? 'voting' : 'talent'}`">
      <div class="upload-icon">
        <Icon type="md-add" size="40" color="#089CF3"/>
      </div>
    </Upload>
    <div v-if="originPopup">
      <base-modal title="View Image" v-model="visible" :width="60" ok-text="Ok"
                  @on-ok="visible = false" @on-cancel="visible = false">
        <div class="image-preview-wrapper">
          <img :src="imgUrl" v-if="visible" class="origin-image">
        </div>
      </base-modal>
    </div>
    <div v-else>
      <img :src="imgUrl" v-if="visible" class="origin-image">
    </div>
  </div>
</template>
<script>
  import { getCSRFToken } from '../../libs/util'
  import Compressor from 'compressorjs'
  import { get } from 'lodash'
  import BaseModal from '../../components/modal/base-modal'


  export default {
    name: 'ImageUpload',

    components: {
      BaseModal,
    },

    data () {
      return {
        imgUrl: '',
        visible: false,
        loaded: false,
        currentEditItem: null,
        isPDF: false
      }
    },

    props: {
      disabled: {
        type: Boolean,
        default: false
      },

      containerDesc: {
        type: String,
        default: ''
      },

      uploaderTag: {
        type: String,
        default: ''
      },

      canMultiple: {
        type: Boolean,
        default: false
      },

      picCount: {
        type: Number,
        default: 1
      },

      defaultList: {
        type: Array,
        default: () => []
      },

      originPopup: {
        type: Boolean,
        default: true
      },

      showImageOnNewWindow: {
        type: Boolean,
        default: false
      }
    },

    computed: {
      extraHeaders () {
        return {
          'from-bo': true,
          'X-CSRF-TOKEN': getCSRFToken()
        }
      },

      uploadList () {
        if (this.loaded) {
          return this.$refs.upload.fileList
        } else {
          return []
        }
      },

      showUploadButton () {
        if (this.loaded) {
          return this.$refs.upload.fileList.length < this.picCount
        }
        return false
      }
    },
    methods: {
      handleView (item) {
        if (!item.url || !item.url.split('.').length) {
          this.$Message.error('Invalid URL')
          return
        }
        let isPDF = item.url.split('.').pop().toLowerCase() === 'pdf'
        if (this.showImageOnNewWindow || isPDF) {
          window.open(item.url)
        } else {
          this.imgUrl = item.url
          this.visible = true
        }
      },
      handleEdit (item) {
        this.currentEditItem = item
        this.$refs.upload.$refs.input.click()
      },
      handleRemove (file) {
        const fileList = this.$refs.upload.fileList
        this.$refs.upload.fileList.splice(fileList.indexOf(file), 1)
        this.visible = false
        this.$emit('delete', file)
      },
      handleSuccess (res, file) {
        file.url = res.media.url
        file.name = res.media.filename
        file.id = res.media.id
        this.$emit('success', file, this.uploaderTag)
      },

      handleError () {
        this.$Message.error('Upload file failed, try again.')
      },

      handleFormatError (file) {
        this.$Notice.warning({
          title: 'Unsupported file format',
          desc: `File ${file.name} is unsupported format, only support jpg, png, jpeg and pdf formats, check and re-upload please`
        })
      },

      handleMaxSize () {
        this.$Message.warning('Image size exceeds the max size 2M, check and re-upload please.')
      },

      handleBeforeUpload (file) {
        if (this.currentEditItem) {
          this.handleRemove(this.currentEditItem)
          this.currentEditItem = null
        }
        if (this.disabled) {
          return
        }
        const check = this.uploadList.length < this.picCount
        if (!check) {
          this.$Message.warning(`Up to ${this.picCount} files can be uploaded`)
        }
        // PDF 文件不压缩，直接上传（此压缩工具不支持 pdf 格式）
        this.isPDF = file.name && file.name.split('.').length && file.name.split('.').pop().toLowerCase() === 'pdf'
        if (file && file.type === 'application/pdf' || this.isPDF) {
          return file
        }

        new Promise((resolve, reject) => {
          new Compressor(file, {
            quality: 0.6,
            maxHeight: 800,
            maxWidth: 800,
            success (result) {
              resolve(result)
            },
            error: reject
          })
        }).then((file) => {
          return new File([file], file.name || 'image')
        })
      },

      clearFiles () {
        this.$refs.upload.clearFiles()
      },

      // 展示的优先展示缩略图
      getThumbnail (item) {
        if (item.thumbnail) {
          return item.thumbnail
        }
        let responseMedia = get(item, 'response.media.thumbnail')
        if (responseMedia) {
          return responseMedia
        }
        return item.url
      },

      itemIsPDF (item) {
        return item.url && item.url.split('.').length && item.url.split('.').pop().toLowerCase() === 'pdf'
      }
    },
    mounted () {
      this.loaded = true
    }
  }
</script>
<style lang="less" scoped>
  .container {
    display: flex;
    align-items: flex-start;
    justify-content: flex-start;
    position: relative;
  }

  .upload-list {
    display: inline-block;
    flex-direction: row;
    width: 80px;
    overflow: hidden;
    background: transparent;
    position: relative;
    margin-right: 4px;

    .image-wrapper {
      display: flex;
      align-content: space-between;
      justify-content: center;
      flex-direction: column;
      border: 1px solid #00adef;
      width: 100%;
      height: 80px;
      position: relative;

      .click {
        cursor: pointer;
        width: 100%;
        height: 100%;

        img {
          width: 78px;
          height: 78px;
          object-fit: cover;
        }
      }

      .manage-wrapper {
        position: absolute;
        width: 78px;
        height: 20px;
        bottom: 0;
        background-color: rgba(0, 173, 239, 0.2);
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding: 3px 5px;

        .replace {
          margin-top: 3px;
          cursor: pointer;

          img {
            width: 11px;
            height: auto;
          }
        }

        .delete {
          margin-top: 3px;
          margin-left: 6px;
          cursor: pointer;

          img {
            width: 15px;
            height: auto;
          }
        }
      }
    }
  }

  /deep/ .ivu-upload-drag {
    border-radius: 0;
    border: none;
    padding: 0;

    &:hover {
      border: none;
      padding: 0;
      border-radius: 0;
    }
  }

  .upload-list-cover {
    margin-top: 5px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .image-desc-wrapper {
    margin-top: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .upload-list-cover i {
    color: #fff;
    font-size: 20px;
    cursor: pointer;
    margin: 0 2px;
  }

  .upload-block {
    display: inline-block;
    width: 78px;
    height: 80px;
  }

  .disabled-upload-block {
    display: inline-block;
    width: 80px;
    pointer-events: none;
    height: 80px;
  }

  .upload-icon {
    width: 78px;
    height: 78px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .image-preview-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 60vh;
    padding: 10px;
  }

  .origin-image {
    max-width: 100%;
    max-height: 100%;
  }

  .upload-tip {
    color: #999;
    white-space: nowrap;
  }

  .image-tag {
    position: absolute;
    width: 20px;
    height: 25px;

    .tag {
      background: #00adef;
      font-size: 12px;
      transform: rotate(-45deg) translateY(-51px) translateX(1px);
      width: 80px;
      height: 30px;
      color: white;
      text-align: center;
      vertical-align: center;
      padding-top: 14px;
    }
  }

</style>
