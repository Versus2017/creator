<template>
  <div class="container">
    <div class="upload-list">
      <template>
        <div class="image-wrapper" v-if="imageObj">
          <div class="image-tag" v-if="isPDF">
            <div class="tag">PDF</div>
          </div>
          <div @click="handleView"
               class="click"
               style="height: 60px">
            <img :src="getThumbnail()">
          </div>
        </div>
      </template>
    </div>
    <base-modal title="View Image" v-model="visible" :width="60" ok-text="Ok"
                @on-ok="visible = false" @on-cancel="visible = false">
      <div class="image-preview-wrapper">
        <img :src="imgUrl" v-if="visible" class="origin-image">
      </div>
    </base-modal>
  </div>
</template>
<script>
  import { getCSRFToken } from '../../libs/util'
  import { get } from 'lodash'
  import BaseModal from '../../components/modal/base-modal'


  export default {
    name: 'image-preview',

    components: {
      BaseModal,
    },

    data () {
      return {
        imgUrl: '',
        visible: false
      }
    },

    props: {
      imageObj: {
        type: Object,
        default: () => {
        }
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

      isPDF () {
        if (this.imageObj && this.imageObj.url && this.imageObj.url.split('.').length) {
          return this.imageObj.url.split('.').pop().toLowerCase() === 'pdf'
        }
        return false
      }
    },
    methods: {
      handleView () {
        let item = this.imageObj
        if (!item.url || !item.url.split('.').length) {
          this.$Message.error('Invalid URL')
          return
        }
        if (this.showImageOnNewWindow || this.isPDF) {
          window.open(item.url)
        } else {
          this.imgUrl = item.url
          this.visible = true
        }
      },
      // 展示的优先展示缩略图
      getThumbnail () {
        let item = this.imageObj
        if (item.thumbnail) {
          return item.thumbnail
        }
        let responseMedia = get(item, 'response.media.thumbnail')
        if (responseMedia) {
          return responseMedia
        }
        return item.url
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
    width: 60px;
    overflow: hidden;
    position: relative;
    margin-right: 4px;
    height: 70px;
    margin-top: 10px;

    .image-wrapper {
      display: flex;
      align-content: space-between;
      justify-content: center;
      flex-direction: column;
      border-radius: 3px;
      box-shadow: 0 1px 1px rgba(0, 0, 0, .2);

      .click {
        cursor: pointer;

        img {
          width: 60px;
          height: 60px;
          object-fit: cover;
          border-radius: 3px;
        }
      }
    }
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

  .image-tag {
    position: absolute;
    width: 20px;
    height: 25px;

    .tag {
      background: #00adef;
      font-size: 12px;
      transform: rotate(-45deg) translateY(-44px) translateX(-4px);
      width: 80px;
      height: 30px;
      color: white;
      text-align: center;
      vertical-align: center;
      padding-top: 14px;
    }
  }

</style>
