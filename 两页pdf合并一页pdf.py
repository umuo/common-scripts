# --coding: utf-8--

import os
import PyPDF2
from PyPDF2 import Transformation


def merge_two_pages_to_one_a4(page1, page2):
    """
    将两个页面合并成一个 A4 页面。

    Args:
        page1: 第一页 (PageObject)。
        page2: 第二页 (PageObject)，可以为 None。

    Returns:
        合并后的 A4 页面 (PageObject)。
    """
    # A4 纸的尺寸 (单位：点)
    a4_width = 595
    a4_height = 842

    # 如果 page2 为 None，创建一个空白页
    if page2 is None:
        page2 = PyPDF2.PageObject.create_blank_page(width=a4_width, height=a4_height)

    # 获取原始页面的尺寸
    page1_width = float(page1.mediabox.width)
    page1_height = float(page1.mediabox.height)
    page2_width = float(page2.mediabox.width)
    page2_height = float(page2.mediabox.height)
    print(f"page1_width: {page1_width}, page1_height: {page1_height}, \npage2_width: {page2_width}, page2_height: {page2_height}")

    # 获取原始页面的尺寸和 mediabox 的左下角坐标
    page1_width = page1.mediabox.width
    page1_height = page1.mediabox.height
    page1_llx = page1.mediabox.lower_left[0]
    page1_lly = page1.mediabox.lower_left[1]

    page2_width = page2.mediabox.width
    page2_height = page2.mediabox.height
    page2_llx = page2.mediabox.lower_left[0]
    page2_lly = page2.mediabox.lower_left[1]

    print(f"page1_width: {page1_width}, page1_height: {page1_height}, page1_llx: {page1_llx}, page1_lly: {page1_lly}")
    print(f"page2_width: {page2_width}, page2_height: {page2_height}, page2_llx: {page2_llx}, page2_lly: {page2_lly}")

    # 计算宽高比
    page1_aspect_ratio = page1_width / page1_height
    page2_aspect_ratio = page2_width / page2_height

    # 确定主导尺寸和计算缩放比例
    scale_by_width = a4_width / (page1_width + page2_width)
    scaled_height1_by_width = page1_height * scale_by_width
    scaled_height2_by_width = page2_height * scale_by_width

    if max(scaled_height1_by_width, scaled_height2_by_width) > a4_height:
        scale = a4_height / max(page1_height, page2_height)
    else:
        scale = scale_by_width

    # 创建一个新的 A4 页面
    new_page = PyPDF2.PageObject.create_blank_page(width=float(a4_width), height=float(a4_height))

    # 对第一页进行缩放和平移，考虑 mediabox 偏移
    page1_tx = -page1_llx * scale
    page1_ty = -page1_lly * scale
    op1 = Transformation().scale(sx=float(scale), sy=float(scale)).translate(tx=float(page1_tx), ty=float(page1_ty))
    new_page.add_transformation(op1)
    new_page.merge_page(page1, expand=True)

    # 对第二页进行缩放和平移，考虑 mediabox 偏移
    page2_tx = (page1_width * scale) - page2_llx * scale
    page2_ty = -page2_lly * scale
    op2 = Transformation().scale(sx=float(scale), sy=float(scale)).translate(tx=float(page2_tx), ty=float(page2_ty))
    new_page.add_transformation(op2)
    new_page.merge_page(page2, expand=True)


    return new_page


def process_pdf_files(directory, output_pdf):
    """
    遍历目录下的所有 PDF 文件，将每个文件的第一页合并，第二页合并，依此类推。

    Args:
        directory: 要遍历的目录路径。
        output_pdf: 输出的 PDF 文件路径。
    """
    writer = PyPDF2.PdfWriter()
    readers = []
    files_to_process = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".pdf"):
                file_path = os.path.join(root, file)
                files_to_process.append(file_path)
                print(f"正在处理文件: {file_path}")

    # 打开所有需要处理的 PDF 文件
    for file_path in files_to_process:
        try:
            infile = open(file_path, 'rb')
            readers.append(PyPDF2.PdfReader(infile))
        except PyPDF2.errors.PdfReadError:
            print(f"错误：无法读取文件 {file_path}，可能已损坏或不是有效的 PDF 文件。")
            infile.close()  # 关闭文件
            return
        except Exception as e:
            print(f"处理文件 {file_path} 时发生错误：{e}")
            infile.close()  # 关闭文件
            return

    # 获取最大页数
    max_pages = max(len(reader.pages) for reader in readers)

    # 循环每一页
    for page_num in range(max_pages):
        pages_to_merge = []
        for reader in readers:
            if page_num < len(reader.pages):
                pages_to_merge.append(reader.pages[page_num])
            else:
                pages_to_merge.append(None)  # 使用 None 表示空白页

        # 每次合并两个文件的一页
        for i in range(0, len(pages_to_merge), 2):
            page1 = pages_to_merge[i]
            page2 = pages_to_merge[i + 1] if i + 1 < len(pages_to_merge) else None
            new_page = merge_two_pages_to_one_a4(page1, page2)
            writer.add_page(new_page)

    # 写入到输出文件
    try:
        with open(output_pdf, 'wb') as outfile:
            writer.write(outfile)
        print(f"所有 PDF 文件已成功合并到 {output_pdf}")
    except Exception as e:
        print(f"写入输出文件时发生错误：{e}")
    finally:
        # 关闭所有打开的文件
        for reader in readers:
            reader.stream.close()


# 使用示例
directory_to_process = r'C:\Users\nbh\Pictures\dy-jd'  # 替换为你要处理的 PDF 文件所在的目录
output_file = 'merged_output.pdf'  # 替换为你希望保存的输出 PDF 文件路径

# 检查目录是否存在
if not os.path.exists(directory_to_process):
    print(f"错误：目录 {directory_to_process} 不存在。")
else:
    process_pdf_files(directory_to_process, output_file)
