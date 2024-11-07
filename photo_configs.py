class PhotoConfig:
    # Photo specifications for different document types
    SPECIFICATIONS = {
        "P.R.China Passport": {
            "width_mm": 33,
            "height_mm": 48,
            "dpi": 300,
            "bg_color": (255, 255, 255),  # White background
            "description": "Chinese Passport (33x48mm)",
            "guide_lines": {
                 "eyes_position_min": 28,  # 眼睛距离底部最小距离（mm）
                 "eyes_position_max": 35,  # 眼睛距离底部最大距离（mm）
                 "head_size_min": 25,      # 最小头部高度（mm）
                 "head_size_max": 35,      # 最大头部高度（mm）
             }
        },
         "US Passport": {
             "width_mm": 51,    # 2英寸
             "height_mm": 51,   # 2英寸
             "dpi": 300,
             "bg_color": (255, 255, 255),
             "description": "US Passport (51x51mm)",
             "guide_lines": {
                 "eyes_position_min": 28,  # 眼睛距离底部最小距离（mm）
                 "eyes_position_max": 35,  # 眼睛距离底部最大距离（mm）
                 "head_size_min": 25,      # 最小头部高度（mm）
                 "head_size_max": 35,      # 最大头部高度（mm）
             }
         },
    }

    # 添加照片纸尺寸配置
    PAPER_SIZES = {
        "4x6 inch": {
            "width_mm": 152.4,  # 6 inch
            "height_mm": 101.6, # 4 inch
            "dpi": 300,
            "description": "4x6 inch photo paper"
        },
        "5x7 inch": {
            "width_mm": 177.8,  # 7 inch
            "height_mm": 127.0, # 5 inch
            "dpi": 300,
            "description": "5x7 inch photo paper"
        }
    }