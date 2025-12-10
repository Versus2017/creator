<template>
  <div class="modal-container" v-if="value" @click="onModalClose" style="background-color: transparent">
    <div :class="customContent ? '' : 'content'" class="animation">
      <img v-if="loading" class="loading" src="../../assets/images/loading.png"
           alt="">
      <slot v-else></slot>
    </div>
    <img class="close" src="../../assets/images/modal-close.png"
         v-if="showClose"
         @click="onClose"
         alt="">
  </div>
</template>

<script>
  export default {
    name: 'base-modal',

    props: {
      value: {
        type: Boolean,
        default: false
      },
      customContent: {
        type: Boolean,
        default: false
      },
      loading: {
        type: Boolean,
        default: false
      },
      showClose: {
        type: Boolean,
        default: true
      },
      maskClosable: {
        type: Boolean,
        default: false,
      }
    },

    data () {
      return {
        visible: this.value
      }
    },

    methods: {
      onClose () {
        this.$emit('on-close')
      },
      onModalClose () {
        if (this.maskClosable) {
          this.$emit('on-close')
        }
      }
    },

    watch: {
      value (val) {
        this.visible = val
      }
    }
  }
</script>

<style scoped lang="less">
  .modal-container {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 123;
    width: 100vw;
    height: 100vh;
    background-color: rgba(35, 40, 49, .95) !important;
    transition: background-color 10s ease-in-out; /* 添加过渡效果 */
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: showIn .5s both;

    .content {
      background-color: white;
      border-radius: 8px;
      overflow-x: hidden;
    }

    .animation {
      animation: zoomIn .5s both;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: auto;
    }

    .close {
      width: 40px;
      height: 40px;
      margin-top: 30px;
    }
  }

  .loading {
    animation: spin 2s linear infinite;
    margin-bottom: 100px;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  @keyframes showIn {
    0% {
      opacity: 0;
    }
    100% {
      opacity: 1;
    }
  }


  @keyframes zoomIn {
    0% {
      opacity: 0;
      transform: scale(0);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  }

  .confirm {
    background-color: #333333;
    width: 100%;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    overflow: hidden;
    margin-top: 30px;
    cursor: pointer;

    span {
      font-size: 14px;
      font-weight: bold;
      color: white;
    }
  }

  @media screen and (max-width: 600px) {
    .container {
      .content {
        max-width: 80%;
      }
    }
  }
</style>