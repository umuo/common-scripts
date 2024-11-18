import requests
from lxml import etree
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
import tempfile
import os

# 获取网页内容
url = 'https://www.mxqe.com/xxsnj/129187.html'  # 替换成你要爬取的网页地址
response = requests.get(url)
html = response.text

# 使用 lxml 解析 HTML
html_tree = etree.HTML(html)

# 获取所有图片链接
image_urls = html_tree.xpath('//div[@class="m-cmsinfo-cont"]/p/img/@src')

# 创建 PDF 文件
pdf_buffer = BytesIO()
c = canvas.Canvas(pdf_buffer, pagesize=A4)
# https://www.mxqe.com/d/file/20230406/1680747408369403.png
# 将图片添加到 PDF 文件中
x_offset = 50
y_offset = 50
for image_url in image_urls:
    # 获取图片内容
    url = 'https://www.mxqe.com' + image_url
    print(url)
    img_response = requests.get(url)
    img = Image.open(BytesIO(img_response.content))

    img_data = BytesIO(img_response.content)
    temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_img.write(img_data.getvalue())
    temp_img.close()
    # 将图片添加到 PDF 文件中
    c.drawImage(temp_img.name, x_offset, y_offset, width=A4[0] - 2 * x_offset, height=A4[1] - 2 * y_offset,
                preserveAspectRatio=True)  # 设置图片大小和位置
    c.showPage()  # 新建一页
    # 删除临时文件
    img.close()
    os.unlink(temp_img.name)

# 保存 PDF 文件
c.save()

# 将 PDF 文件保存到本地
with open('images.pdf', 'wb') as f:
    f.write(pdf_buffer.getvalue())

