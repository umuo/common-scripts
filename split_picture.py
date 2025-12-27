import cv2
import numpy as np
import os

def split_stickers_final(image_path, output_folder='stickers_final', keep_top_n=24):
    # 1. 读取图片
    if not os.path.exists(image_path):
        print(f"错误: 找不到文件 {image_path}")
        return

    img = cv2.imread(image_path)
    if img is None:
        print("错误：无法读取图片。")
        return
        
    original_img = img.copy()
    h_img, w_img = img.shape[:2]
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 2. 预处理
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 阈值处理
    ret, thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY_INV)

    # 3. 膨胀 (保持较小的膨胀，防止粘连)
    kernel = np.ones((5, 5), np.uint8) 
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # 4. 查找轮廓
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. 收集所有可能的框
    candidates = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        # 只要不是极其微小的噪点，先都收录进来
        if w > 10 and h > 10:
            candidates.append({'box': (x, y, w, h), 'area': area})

    # ==========================================
    # 核心修改：只保留面积最大的 24 个
    # ==========================================
    # 按面积从大到小排序
    candidates.sort(key=lambda c: c['area'], reverse=True)
    
    # 截取前 24 个（如果你以后切别的图，表情数不一样，改 keep_top_n 即可）
    final_candidates = candidates[:keep_top_n]
    
    # 提取出 box 数据用于后续排序
    bounding_boxes = [c['box'] for c in final_candidates]

    print(f"原始检测到 {len(candidates)} 个区块，已通过面积筛选保留最大的 {len(bounding_boxes)} 个。")

    # 6. 位置排序 (从上到下，从左到右)
    def sort_boxes(boxes, max_height_diff=30):
        boxes.sort(key=lambda b: b[1]) # 先按Y排
        sorted_boxes = []
        current_row = []
        last_y = -1

        for box in boxes:
            x, y, w, h = box
            if last_y == -1:
                current_row.append(box)
                last_y = y
            else:
                if abs(y - last_y) < max_height_diff:
                    current_row.append(box)
                else:
                    current_row.sort(key=lambda b: b[0]) # 行内按X排
                    sorted_boxes.extend(current_row)
                    current_row = [box]
                    last_y = y
        
        if current_row:
            current_row.sort(key=lambda b: b[0])
            sorted_boxes.extend(current_row)
        return sorted_boxes

    sorted_boxes = sort_boxes(bounding_boxes)

    # 7. 切割并保存
    margin = 5
    for i, (x, y, w, h) in enumerate(sorted_boxes):
        x1 = max(0, x - margin)
        y1 = max(0, y - margin)
        x2 = min(w_img, x + w + margin)
        y2 = min(h_img, y + h + margin)
        
        roi = original_img[y1:y2, x1:x2]
        
        file_name = f"{output_folder}/sticker_{i+1:02d}.png"
        cv2.imwrite(file_name, roi)
        print(f"已保存: {file_name}")

    print("全部完成！那个多余的问号已经被自动过滤掉了。")

if __name__ == "__main__":
    # 使用你之前那张已经切好的图，或者原图都可以
    split_stickers_final('tmp/2.jpg')