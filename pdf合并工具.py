# --coding: utf-8--
import PyPDF2

def merge_pdfs(paths, output):
  """
  合并多个PDF文件。

  Args:
    paths: 一个包含要合并的PDF文件路径的列表。
    output: 合并后的PDF文件的输出路径。
  """

  pdf_writer = PyPDF2.PdfMerger()

  for path in paths:
    try:
      pdf_reader = PyPDF2.PdfReader(path)
      pdf_writer.append(pdf_reader)
    except PyPDF2.errors.PdfReadError:
      print(f"Error: 无法读取文件 '{path}'。请确保它是一个有效的PDF文件。")
      return
    except FileNotFoundError:
      print(f"Error: 找不到文件 '{path}'。")
      return

  with open(output, 'wb') as out:
    pdf_writer.write(out)

  print(f"已成功合并PDF文件到 '{output}'")

# 使用示例：
pdf_paths = ["脱敏.pdf", "24秋新七上历史64天早背晚默.pdf"]  # 替换为你的PDF文件路径
output_path = "merged_file.pdf"  # 替换为你想要的输出文件路径

merge_pdfs(pdf_paths, output_path)
