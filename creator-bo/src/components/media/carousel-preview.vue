<template>
  <div class="container">
    <div class="upload-list" ref="container">
      <div class="image-wrapper" v-if="images && images.length">
        <div @click="handleView(item, index)"
             v-for="(item, index) in images"
             :key="item.id"
             class="click"
             style="height: 60px">
          <img :src="getThumbnail(item)">
        </div>
      </div>
      <div v-else>-</div>
    </div>
    <base-modal title="查看图片" v-model="visible" :width="60" ok-text="确定"
                @on-ok="visible = false" @on-cancel="visible = false">
      <div class="image" v-if="visible">
        <Carousel height="500px" v-model="currentIndex"
                  :style="{width: '700px'}">
          <CarouselItem class="image"
                        :style="{width: '700px'}"
                        v-for="(item, index) in images" :key="index">
            <div class="image" :style="{width: '700px', height: '420px'}">
              <img :src="item.url"
                   :style="{maxWidth: '100%', maxHeight: '100%'}">
            </div>
          </CarouselItem>
        </Carousel>
      </div>
    </base-modal>
  </div>
</template>
<script>
  import { getCSRFToken } from '@/libs/util'
  import { get } from 'lodash'
  import BaseModal from '../../components/modal/base-modal'


  export default {
    name: 'carousel-preview',

    components: {
      BaseModal
    },

    data () {
      return {
        visible: false,
        currentIndex: this.index
      }
    },

    props: {
      index: {
        type: Number,
        default: 0
      },

      images: {
        type: Array,
        default: null
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
      }

    },
    methods: {
      handleView (item, index) {
        if (!item.url || !item.url.split('.').length) {
          this.$Message.error('Invalid URL')
          return
        }
        if (this.showImageOnNewWindow || this.isPDF) {
          window.open(item.url)
        } else {
          this.currentIndex = index
          this.visible = true
        }
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
      }
    },
    mounted () {
      this.loaded = true
      let container = this.$refs.container
      this.$emit('actionWidthChanged', container.offsetWidth + 40)
    }
  }
</script>
<style lang="less" scoped>
  .container {
    position: relative;
    display: inline-block;
    white-space: nowrap;

    > * {
      margin-right: 4px;
      display: inline;
    }

    > *:last-child {
      margin-right: 0;
    }
  }

  .upload-list {
    display: inline-block;
    flex-direction: row;
    position: relative;
    margin-right: 4px;
    height: 70px;
    margin-top: 10px;

    .image-wrapper {
      display: flex;
      align-content: space-between;
      justify-content: center;

      .click {
        cursor: pointer;

        img {
          width: 60px;
          height: 60px;
          object-fit: cover;
          border-radius: 3px;
          margin-right: 5px;
          box-shadow: 0 1px 1px rgba(0, 0, 0, .2);
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

  .image {
    display: flex;
    align-items: center;
    justify-content: center;
  }

</style>

<style lang="less">

</style>
