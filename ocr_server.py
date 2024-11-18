# app.py
from flask import Flask, request, jsonify
import ddddocr
import requests
from io import BytesIO

app = Flask(__name__)
ocr = ddddocr.DdddOcr()


@app.route('/ocr', methods=['POST'])
def ocr_recognition():
    # 获取图片的 URL
    image_url = request.json.get('image_url')
    if not image_url:
        return jsonify({'error': 'No image URL provided'}), 400

    try:
        # 从 URL 下载图片
        response = requests.get(image_url)
        response.raise_for_status()  # 检查请求是否成功

        # 将下载的图片数据转为二进制流
        image_data = BytesIO(response.content)

        # 使用 ddddocr 识别图片
        result = ocr.classification(image_data.read())

        return jsonify({'result': result})

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to download image: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred during OCR processing: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
