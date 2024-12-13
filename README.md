# 简介

常用的Python脚本

学习使用，请勿违规使用


## 发票PDF合并
先下载：https://github.com/oschwartz10612/poppler-windows/releases
打包命令
```bash
pyinstaller --onefile --add-data "C:/Users/xxx/Pictures/poppl
er-24.08.0;poppler" --add-data "C:/Users/xxx/Pictures/poppler-24.08.0/Library/bin;poppler/Library/bin"
  .\发票pdf合并.py
```
