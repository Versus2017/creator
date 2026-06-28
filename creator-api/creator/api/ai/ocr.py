import os
import sys
import logging
from typing import List, Dict, Any, Tuple, Optional

from alibabacloud_ocr_api20210707.client import Client as ocr_api20210707Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ocr_api20210707 import models as ocr_api_20210707_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from ...config import config

logger = logging.getLogger(__name__)


class OcrModel:
    def __init__(self):
        base_config = open_api_models.Config(
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID。,
            access_key_id=config.OCR_ALY_ACCESS_KEY_ID,
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_SECRET。,
            access_key_secret=config.OCR_ALY_ACCESS_KEY_SECRET
        )
        base_config.endpoint = f'ocr-api.cn-hangzhou.aliyuncs.com'
        self.client = ocr_api20210707Client(base_config)

    async def get_text(self, filename: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        获取图片中的文本内容及坐标信息
        
        Args:
            filename (str): 图片文件名
            
        Returns:
            Tuple[Optional[str], Optional[Dict]]: 返回提取的文本内容和包含坐标的完整数据
        """
        logger.warning(f'get_text: {filename}')
        # body 为二进制图片数据，类型为：BinaryIO
        image_path = os.path.join(config.UPLOADS_DEFAULT_DEST, filename)
        if not os.path.exists(image_path):
            logger.warning(f"文件不存在：{image_path}")
            return None, None
        with open(image_path, 'rb') as f:
            body = f.read()
        ocr_model = ocr_api_20210707_models
        recognize_all_text_request = ocr_model.RecognizeAllTextRequest(
            body=body,
            # type 参数详情：
            # https://help.aliyun.com/zh/ocr/developer-reference/api-ocr-api-2021-07-07-recognizealltext?spm=a2c4g.11186623.help-menu-252763.d_3_2_4_0_0.270c78ea2K6K69&scm=20140722.H_2629927._.OR_help-T_cn~zh-V_1
            type='Advanced',
            # 设置坐标输出参数
            output_coordinate='points',  # 使用四点坐标模式，返回左上、右上、右下、左下四个角的坐标
            # output_oricoord=True,        # 返回原图坐标信息，而不是算法处理后的坐标
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            response = await self.client.recognize_all_text_with_options_async(
                recognize_all_text_request, runtime)
            
            response_data = response.body.to_map()
            logger.warning(f"OCR响应: {response_data}")
            
            # 提取文本内容
            content = response_data.get('Data', {}).get('Content')
            
            # 处理返回的坐标数据，整理为更易于使用的格式
            coordinates_data = self._process_coordinates(response_data)
            
            return content, coordinates_data
            
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
            logger.error(error.message)
            # 诊断地址
            logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            return None, None
    
    def _process_coordinates(self, response_data: Dict) -> Dict:
        """
        处理OCR返回的坐标数据，提取有用的信息
        
        Args:
            response_data (Dict): OCR API的原始响应数据
            
        Returns:
            Dict: 处理后的坐标数据
        """
        processed_data = {
            'image_info': {},
            'blocks': []
        }
        
        # 获取图片信息
        data = response_data.get('Data', {})
        processed_data['image_info'] = {
            'width': data.get('Width', 0),
            'height': data.get('Height', 0),
        }
        
        # 处理文本块信息
        sub_images = data.get('SubImages', [])
        if sub_images:
            for sub_image in sub_images:
                block_info = sub_image.get('BlockInfo', {})
                block_details = block_info.get('BlockDetails', [])
                
                for block in block_details:
                    block_data = {
                        'block_id': block.get('BlockId'),
                        'content': block.get('BlockContent', ''),
                        'confidence': block.get('BlockConfidence', 0),
                        'angle': block.get('BlockAngle', 0),
                        'points': block.get('BlockPoints', []),
                        'chars': []
                    }
                    
                    # 处理字符级别信息（如果有）
                    char_infos = block.get('CharInfos', [])
                    for char_info in char_infos:
                        char_data = {
                            'char': char_info.get('Char', ''),
                            'confidence': char_info.get('Confidence', 0),
                            'points': char_info.get('Points', [])
                        }
                        block_data['chars'].append(char_data)
                    
                    processed_data['blocks'].append(block_data)
        
        return processed_data

