import os
import shutil
from tqdm import tqdm

def extract_files(source_dir, target_dir):
    """
    将源目录下所有子文件夹中的文件提取到目标目录
    
    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径
    """
    # 确保目标目录存在
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    # 获取所有文件
    all_files = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)
            
    print(f"找到 {len(all_files)} 个文件")
    
    # 复制文件
    for file_path in tqdm(all_files, desc="正在提取文件"):
        try:
            # 获取文件名
            file_name = os.path.basename(file_path)
            # 构建目标路径
            target_path = os.path.join(target_dir, file_name)
            
            # 如果目标文件已存在，添加序号
            counter = 1
            while os.path.exists(target_path):
                name, ext = os.path.splitext(file_name)
                target_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
                counter += 1
                
            # 复制文件
            shutil.copy2(file_path, target_path)
            
        except Exception as e:
            print(f"\n处理文件时出错 {file_path}: {str(e)}")
            
    print(f"\n文件提取完成！共处理 {len(all_files)} 个文件")

if __name__ == "__main__":
    # 源目录
    source_dir = r"D:\emailpachong\attachments111111"
    # 目标目录
    target_dir = r"D:\emailpachong\extracted_files"
    
    # 执行提取
    extract_files(source_dir, target_dir) 