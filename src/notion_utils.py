from notion_client import Client
import streamlit as st

def parse_markdown_text(text: str) -> list:
    """
    Parse Markdown text into Notion rich text format
    
    Args:
        text: Markdown formatted text
    
    Returns:
        list: Notion rich text array
    """
    rich_text = []
    current_pos = 0
    
    while current_pos < len(text):
        # Find next special marker
        next_bold = text.find('**', current_pos)
        next_italic = text.find('*', current_pos)
        next_code = text.find('`', current_pos)
        
        # Find the nearest marker
        next_pos = min(
            pos for pos in [next_bold, next_italic, next_code] 
            if pos != -1
        ) if any(pos != -1 for pos in [next_bold, next_italic, next_code]) else len(text)
        
        # Add plain text
        if next_pos > current_pos:
            rich_text.append({
                "type": "text",
                "text": {"content": text[current_pos:next_pos]}
            })
        
        # Process special markers
        if next_pos < len(text):
            if text[next_pos:next_pos+2] == '**':
                # Bold text
                end_pos = text.find('**', next_pos + 2)
                if end_pos != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[next_pos+2:end_pos]},
                        "annotations": {"bold": True}
                    })
                    current_pos = end_pos + 2
                    continue
            elif text[next_pos] == '*':
                # Italic text
                end_pos = text.find('*', next_pos + 1)
                if end_pos != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[next_pos+1:end_pos]},
                        "annotations": {"italic": True}
                    })
                    current_pos = end_pos + 1
                    continue
            elif text[next_pos] == '`':
                # Code text
                end_pos = text.find('`', next_pos + 1)
                if end_pos != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[next_pos+1:end_pos]},
                        "annotations": {"code": True}
                    })
                    current_pos = end_pos + 1
                    continue
        
        current_pos = next_pos + 1
    
    return rich_text

def convert_markdown_to_notion_blocks(analysis: str) -> list:
    """
    Convert Markdown text to Notion block format
    
    Args:
        analysis: Markdown formatted analysis text
    
    Returns:
        list: Notion block array
    """
    blocks = []
    current_list_items = []
    
    for line in analysis.split('\n'):
        line = line.strip()
        if not line:
            if current_list_items:
                # Process accumulated list items
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": parse_markdown_text(current_list_items[0])
                    }
                })
                for item in current_list_items[1:]:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": parse_markdown_text(item)
                        }
                    })
                current_list_items = []
            continue
            
        # Process headings
        if line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": parse_markdown_text(line[2:])
                }
            })
        elif line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": parse_markdown_text(line[3:])
                }
            })
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": parse_markdown_text(line[4:])
                }
            })
        # Process divider
        elif line.strip() == '---':
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        # Process list items
        elif line.startswith('- '):
            current_list_items.append(line[2:])
        elif line.startswith('1. '):
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": parse_markdown_text(line[3:])
                }
            })
        else:
            # Process regular paragraphs
            if current_list_items:
                # Process any remaining list items first
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": parse_markdown_text(current_list_items[0])
                    }
                })
                for item in current_list_items[1:]:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": parse_markdown_text(item)
                        }
                    })
                current_list_items = []
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": parse_markdown_text(line)
                }
            })
    
    # Process any remaining list items
    if current_list_items:
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": parse_markdown_text(current_list_items[0])
            }
        })
        for item in current_list_items[1:]:
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": parse_markdown_text(item)
                }
            })
    
    return blocks

def upload_to_notion(analysis: str, podcast_info: dict, notion_token: str, db_id: str) -> bool:
    """
    使用新版 Notion API 上传分析结果
    
    Args:
        analysis: 分析结果文本（Markdown格式）
        podcast_info: 播客信息字典，包含 title, host, date, url
        notion_token: Notion API 密钥（以 secret_ 开头）
        db_id: Notion 数据库ID
    
    Returns:
        bool: 是否上传成功
    """
    try:
        # 初始化客户端
        notion = Client(auth=notion_token)
        
        # 获取数据库信息
        database = notion.databases.retrieve(database_id=db_id)
        
        # 检查 Host 字段是否存在
        host_field = None
        for prop_name, prop in database["properties"].items():
            if prop_name == "Host" and prop["type"] == "select":
                host_field = prop
                break
        
        # 如果 Host 字段不存在，创建它
        if not host_field:
            # 更新数据库属性
            notion.databases.update(
                database_id=db_id,
                properties={
                    "Host": {
                        "select": {
                            "options": []
                        }
                    }
                }
            )
        
        # 创建页面属性
        properties = {
            "Title": {
                "title": [
                    {
                        "text": {"content": podcast_info['title']}
                    }
                ]
            },
            "Host": {
                "select": {
                    "name": podcast_info['host'] if podcast_info['host'] else "未知主播"
                }
            },
            "Date": {
                "date": {
                    "start": podcast_info['date']
                }
            },
            "URL": {
                "url": podcast_info['url']
            }
        }
        
        # 创建基础页面
        new_page = notion.pages.create(
            parent={"database_id": db_id},
            properties=properties
        )
        
        # 转换Markdown为Notion区块
        blocks = convert_markdown_to_notion_blocks(analysis)
        
        # 批量添加内容区块
        notion.blocks.children.append(
            block_id=new_page["id"],
            children=blocks
        )
        
        return True
    except Exception as e:
        error_detail = getattr(e, "body", str(e))
        st.error(f"Notion 上传失败：{error_detail}")
        return False 