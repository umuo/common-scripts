# --coding: utf-8--

import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pdf2image import convert_from_path
from io import BytesIO
import sys
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import subprocess
from PIL import Image



def load_fonts():
    """加载字体并注册到 ReportLab"""
    font_dir = get_fonts_path()
    font_path = os.path.join(font_dir, "aaa.ttf")  # 替换为你需要的字体文件
    print(f"字体路径：{font_path}") # 打印字体路径
    pdfmetrics.registerFont(TTFont("aaa", font_path))


def get_poppler_path():
    # 获取当前脚本所在目录
    if hasattr(sys, '_MEIPASS'):  # PyInstaller 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "poppler/Library/bin")


def get_fonts_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "fonts")
    return os.path.abspath("fonts")


os.environ['POPPLER_FONTS_DIR'] = r"C:\Windows\Fonts"


def convert_pdf_to_image_with_pdftocairo(pdf_path, dpi=300, image_format='png', poppler_path=None):
    """使用 pdftocairo 命令将 PDF 转换为图片"""
    output_folder = os.path.dirname(pdf_path)
    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    exec_path = os.path.join(poppler_path, "pdftocairo.exe")
    # 构建 pdftocairo 命令
    command = [
        exec_path,
        "-r", str(dpi),  # 设置 DPI
        f"-{image_format}",  # 设置输出格式
        pdf_path,
        os.path.join(output_folder, os.path.basename(pdf_path))  # 输出文件名前缀
    ]
    print(" ".join(command))

    # 执行命令
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"PDF converted to images successfully using pdftocairo. Output in {output_folder}")
        print("pdftocairo stdout:", subprocess.run(command, capture_output=True, text=True).stdout)
        print("pdftocairo stderr:", subprocess.run(command, capture_output=True, text=True).stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error during PDF to image conversion with pdftocairo: {e}")
        print("pdftocairo stdout:", e.stdout)
        print("pdftocairo stderr:", e.stderr)
    # 获取生成的文件列表
    output_file_list = sorted([
        f for f in os.listdir(output_folder)
        if
        os.path.isfile(os.path.join(output_folder, f)) and f.startswith("output") and f.endswith(f".{image_format}")
    ])

    # 读取图片文件并转换为 PIL.Image 对象
    images = []
    for output_file in output_file_list:
        image_path = os.path.join(output_folder, output_file)
        try:
            img = Image.open(image_path)
            images.append(img)
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")

    return images

def merge_pdfs_to_a4(input_dir, output_file):
    # load_fonts()  # 确保字体已加载
    # print(f"已注册字体：{pdfmetrics.getRegisteredFontNames()}") # 打印已注册字体
    poppler_path = get_poppler_path()
    # 获取所有 PDF 文件的路径
    pdf_paths = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.pdf'):
                pdf_paths.append(os.path.join(root, file))

    pdf_paths.sort()  # 排序以保持一致的处理顺序

    writer = PdfWriter()

    # 每两个 PDF 合并成一页
    for i in range(0, len(pdf_paths), 2):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # 获取当前两个 PDF
        pdf1_path = pdf_paths[i]
        pdf2_path = pdf_paths[i + 1] if i + 1 < len(pdf_paths) else None

        # 渲染第一个 PDF 为图像并绘制

        images1 = convert_from_path(pdf1_path, dpi=500, use_pdftocairo=True, poppler_path=poppler_path)
        # images1 = convert_pdf_to_image_with_pdftocairo(pdf1_path, dpi=500, poppler_path=poppler_path)
        if images1:
            img1 = images1[0]
            img1_width, img1_height = img1.size
            img1_bytes = BytesIO()
            img1.save(img1_bytes, format="PNG")
            img1_bytes.seek(0)
            # with open(f'{os.path.dirname(pdf1_path)}/img1_tmp.png', 'wb') as f:
            #     f.write(img1_bytes.getvalue())
            c.drawImage(ImageReader(img1_bytes), 0, A4[1] / 2, width=A4[0], height=A4[1] / 2)

        # 如果有第二个 PDF，渲染为图像并绘制
        if pdf2_path:
            images2 = convert_from_path(pdf2_path, dpi=500, poppler_path=poppler_path)
            if images2:
                img2 = images2[0]
                img2_width, img2_height = img2.size
                img2_bytes = BytesIO()
                img2.save(img2_bytes, format="PNG")
                img2_bytes.seek(0)
                c.drawImage(ImageReader(img2_bytes), 0, 0, width=A4[0], height=A4[1] / 2)

        c.save()

        # 将缓冲区 PDF 写入 PyPDF2
        buffer.seek(0)
        temp_reader = PdfReader(buffer)
        writer.add_page(temp_reader.pages[0])

    # 写入输出文件
    with open(output_file, 'wb') as f:
        writer.write(f)


if __name__ == "__main__":
    input_directory = input("请输入PDF目录路径：").strip()
    output_pdf = os.path.join(os.getcwd(), "merged_output.pdf")
    merge_pdfs_to_a4(input_directory, output_pdf)
    print(f"合并完成，输出文件为: {output_pdf}")
