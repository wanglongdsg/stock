"""
数据加载工具
负责从Excel文件加载股票数据
"""

import pandas as pd


def load_stock_data(file_path: str) -> pd.DataFrame:
    """
    加载股票数据
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        包含股票数据的DataFrame
    """
    # 先读取原始数据，不设置header
    df_raw = pd.read_excel(file_path, header=None)
    
    # 查找列名行（通常包含"时间"、"开盘"等关键词）
    header_row = None
    for i in range(min(10, len(df_raw))):
        row_str = ' '.join([str(x) for x in df_raw.iloc[i].tolist() if pd.notna(x)])
        if '时间' in row_str or '开盘' in row_str or '日期' in row_str:
            header_row = i
            break
    
    if header_row is None:
        # 如果找不到列名行，尝试使用第2行（常见格式）
        header_row = 2
    
    # 读取数据，使用找到的列名行作为header
    df = pd.read_excel(file_path, header=header_row)
    
    # 删除空行
    df = df.dropna(how='all')
    
    # 重置索引
    df = df.reset_index(drop=True)
    
    # 尝试自动识别列名（常见的中文和英文列名）
    column_mapping = {}
    
    # 日期列 - 检查所有列
    date_keywords = ['时间', '日期', 'date', 'Date', 'time', 'Time', '交易日期']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in date_keywords):
            column_mapping[col] = 'date'
            break
    
    # 开盘价
    open_keywords = ['开盘', 'open', 'Open', '开盘价']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in open_keywords):
            column_mapping[col] = 'open'
            break
    
    # 最高价
    high_keywords = ['最高', 'high', 'High', '最高价']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in high_keywords):
            column_mapping[col] = 'high'
            break
    
    # 最低价
    low_keywords = ['最低', 'low', 'Low', '最低价']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in low_keywords):
            column_mapping[col] = 'low'
            break
    
    # 收盘价
    close_keywords = ['收盘', 'close', 'Close', '收盘价', '价格', 'price']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in close_keywords):
            column_mapping[col] = 'close'
            break
    
    # 成交量
    volume_keywords = ['成交量', 'volume', 'Volume', '成交额', 'amount']
    for col in df.columns:
        col_str = str(col).strip()
        if any(keyword in col_str for keyword in volume_keywords):
            column_mapping[col] = 'volume'
            break
    
    # 重命名列
    df = df.rename(columns=column_mapping)
    
    # 如果列名映射失败，尝试按位置映射（常见格式：时间、开盘、最高、最低、收盘）
    if 'open' not in df.columns and len(df.columns) >= 5:
        # 假设标准格式：第0列=时间，第1列=开盘，第2列=最高，第3列=最低，第4列=收盘
        df.columns.values[0] = 'date'
        df.columns.values[1] = 'open'
        df.columns.values[2] = 'high'
        df.columns.values[3] = 'low'
        df.columns.values[4] = 'close'
        if len(df.columns) >= 6:
            df.columns.values[5] = 'volume'
    
    # 确保必需的列存在
    required_cols = ['open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        # 打印当前列名以便调试
        print(f"当前列名: {df.columns.tolist()[:10]}")
        raise ValueError(f"缺少必需的列: {missing_cols}。请确保数据包含: {required_cols}")
    
    # 转换数据类型
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            # 尝试转换为数值类型
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 删除包含NaN的行（数据不完整）
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    
    # 重置索引
    df = df.reset_index(drop=True)
    
    return df



