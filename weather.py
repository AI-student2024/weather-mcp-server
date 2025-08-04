from typing import Any
import httpx
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 1. 初始化 FastMCP 服务器
# 创建一个名为 "weather" 的服务器实例。这个名字有助于识别这套工具。
mcp = FastMCP("weather")

# --- 常量定义 ---
# 美国国家气象局 (NWS) API 的基础 URL
NWS_API_BASE = "https://api.weather.gov"
# 设置请求头中的 User-Agent，很多公共 API 要求提供此信息以识别客户端
USER_AGENT = "weather-app/1.0"


# --- 辅助函数 ---

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """
    一个通用的异步函数，用于向 NWS API 发起请求并处理常见的错误。

    Args:
        url (str): 要请求的完整 URL。

    Returns:
        dict[str, Any] | None: 成功时返回解析后的 JSON 字典，失败时返回 None。
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"  # NWS API 推荐的 Accept 头
    }
    # 使用 httpx.AsyncClient 来执行异步 HTTP GET 请求
    async with httpx.AsyncClient() as client:
        try:
            # 发起请求，设置了30秒的超时
            response = await client.get(url, headers=headers, timeout=30.0)
            # 如果响应状态码是 4xx 或 5xx（表示客户端或服务器错误），则会引发一个异常
            response.raise_for_status()
            # 如果请求成功，返回 JSON 格式的响应体
            return response.json()
        except Exception:
            # 捕获所有可能的异常（如网络问题、超时、HTTP错误等），并返回 None
            return None

def format_alert(feature: dict) -> str:
    """将单个天气预警的 JSON 数据格式化为人类可读的字符串。"""
    props = feature["properties"]
    # 使用 .get() 方法安全地访问字典键，如果键不存在则返回默认值，避免程序出错
    return f"""
事件: {props.get('event', '未知')}
区域: {props.get('areaDesc', '未知')}
严重性: {props.get('severity', '未知')}
描述: {props.get('description', '无描述信息')}
指令: {props.get('instruction', '无具体指令')}
"""

# --- MCP 工具定义 ---

@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    获取美国某个州当前生效的天气预警信息。
    这个函数被 @mcp.tool() 装饰器标记，意味着它可以被大模型作为工具来调用。

    参数:
        state: 两个字母的美国州代码 (例如: CA, NY)。
    """
    # 构造请求特定州天气预警的 URL
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    # 健壮性检查：如果请求失败或返回的数据格式不正确
    if not data or "features" not in data:
        return "无法获取预警信息或未找到相关数据。"

    # 如果 features 列表为空，说明该州当前没有生效的预警
    if not data["features"]:
        return "该州当前没有生效的天气预警。"

    # 使用列表推导和 format_alert 函数来格式化所有预警信息
    alerts = [format_alert(feature) for feature in data["features"]]
    # 将所有预警信息用分隔线连接成一个字符串并返回
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    根据给定的经纬度获取天气预报。
    同样，这个函数也是一个可被调用的 MCP 工具。

    参数:
        latitude: 地点的纬度
        longitude: 地点的经度
    """
    # NWS API 获取预报需要两步
    # 第一步：根据经纬度获取一个包含具体预报接口 URL 的网格点信息
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "无法获取该地点的预报数据。"

    # 第二步：从上一步的响应中提取实际的天气预报接口 URL
    forecast_url = points_data["properties"]["forecast"]
    # 第三步：请求详细的天气预报数据
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "无法获取详细的预报信息。"

    # 提取预报周期数据
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    # 遍历接下来的5个预报周期（例如：今天下午、今晚、明天...）
    for period in periods[:5]:
        forecast = f"""
{period['name']}:
温度: {period['temperature']}°{period['temperatureUnit']}
风力: {period['windSpeed']} {period['windDirection']}
预报: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    # 将格式化后的预报信息连接成一个字符串并返回
    return "\n---\n".join(forecasts)


@mcp.tool()
async def get_forecast_by_date(latitude: float, longitude: float, date_description: str) -> str:
    """
    根据日期描述获取天气预报。
    
    参数:
        latitude: 地点的纬度
        longitude: 地点的经度
        date_description: 日期描述，支持以下格式：
            - "8月7日" 或 "8月7号" - 指定具体日期
            - "7号" - 指定日期（当前月或下个月）
            - "未来3天" - 未来几天
            - "明天"、"后天"、"大后天" - 相对日期
    """
    # 获取基础预报数据
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    
    if not points_data:
        return "无法获取该地点的预报数据。"
    
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    
    if not forecast_data:
        return "无法获取详细的预报信息。"
    
    periods = forecast_data["properties"]["periods"]
    
    # 解析日期描述
    target_periods = parse_date_description(date_description, periods)
    
    if isinstance(target_periods, str):
        return target_periods  # 返回错误信息
    
    if not target_periods:
        return f"无法找到{date_description}的天气信息。"
    
    # 格式化结果
    forecasts = []
    for period in target_periods:
        forecast = f"""
{period['name']}:
温度: {period['temperature']}°{period['temperatureUnit']}
风力: {period['windSpeed']} {period['windDirection']}
预报: {period['detailedForecast']}
"""
        forecasts.append(forecast)
    
    return "\n---\n".join(forecasts)

def parse_date_description(description: str, periods: list) -> list | str:
    """解析日期描述并返回对应的预报周期"""
    today = datetime.now()
    
    # 处理"X月X日"或"X月X号"格式（如"8月7日"、"8月7号"）
    full_date_pattern = r'(\d+)月(\d+)[日号]'
    full_date_match = re.search(full_date_pattern, description)
    if full_date_match:
        target_month = int(full_date_match.group(1))
        target_day = int(full_date_match.group(2))
        current_month = today.month
        current_day = today.day
        
        # 计算天数差
        if target_month == current_month:
            # 同月
            if target_day > current_day:
                days_ahead = target_day - current_day
            else:
                return f"抱歉，无法查询过去的日期（{target_month}月{target_day}日）。"
        elif target_month > current_month:
            # 下个月
            # 计算当前月剩余天数 + 目标月天数
            import calendar
            days_in_current_month = calendar.monthrange(today.year, current_month)[1]
            days_ahead = (days_in_current_month - current_day) + target_day
        else:
            # 假设是明年的月份
            return f"抱歉，暂不支持跨年查询（{target_month}月{target_day}日）。"
        
        return get_periods_by_days_ahead(periods, days_ahead)
    
    # 处理"X号"格式（简化日期，假设是当前月或下个月）
    if "号" in description:
        day_match = re.search(r'(\d+)号', description)
        if day_match:
            target_day = int(day_match.group(1))
            current_day = today.day
            
            # 计算天数差
            if target_day > current_day:
                days_ahead = target_day - current_day
            else:
                # 假设是下个月
                import calendar
                days_in_current_month = calendar.monthrange(today.year, today.month)[1]
                days_ahead = (days_in_current_month - current_day) + target_day
            
            return get_periods_by_days_ahead(periods, days_ahead)
    
    # 处理"未来X天"格式
    if "未来" in description and "天" in description:
        days_match = re.search(r'未来(\d+)天', description)
        if days_match:
            days = int(days_match.group(1))
            return get_periods_by_days_ahead(periods, days)
    
    # 处理相对日期
    relative_dates = {
        "今天": 0, "明天": 1, "后天": 2, "大后天": 3,
        "昨天": -1, "前天": -2, "大前天": -3
    }
    
    for date_key, days_offset in relative_dates.items():
        if date_key in description:
            if days_offset < 0:
                return f"抱歉，NWS API不支持历史天气查询，无法获取{date_key}的天气信息。"
            return get_periods_by_days_ahead(periods, days_offset)
    
    return []

def get_periods_by_days_ahead(periods: list, days_ahead: int) -> list:
    """根据天数获取对应的预报周期"""
    if days_ahead == 0:
        # 今天 - 返回第一个白天周期
        for period in periods:
            if not period.get('name', '').endswith('Night') and period.get('name') != 'Tonight':
                return [period]
        return []
    
    # 查找目标日期的周期
    target_periods = []
    current_day = None
    
    for period in periods:
        name = period.get('name', '')
        
        # 跳过"Tonight"等特殊周期
        if name == 'Tonight':
            continue
            
        # 根据当前日期计算目标日期
        from datetime import datetime, timedelta
        today = datetime.now()
        target_date = today + timedelta(days=days_ahead)
        target_weekday = target_date.strftime('%A')  # 获取星期几的英文名称
        
        # 检查周期名称是否匹配目标日期
        if target_weekday in name:
            target_periods.append(period)
            current_day = target_weekday
        elif current_day is not None and target_weekday not in name:
            # 已经收集完目标日期的周期，退出
            break
    
    return target_periods

@mcp.tool()
async def get_weather_flexible(latitude: float, longitude: float, query: str) -> str:
    """
    灵活的天气查询工具。
    
    支持的查询格式：
    - "8月7日" 或 "8月7号" - 查询指定日期的天气
    - "7号" - 查询7号的天气（当前月或下个月）
    - "未来3天" - 查询未来3天的天气
    - "后天" - 查询后天的天气
    - "明天" - 查询明天的天气
    """
    return await get_forecast_by_date(latitude, longitude, query)


# --- 服务器启动 ---

# 这是一个标准的 Python 入口点检查
# 确保只有当这个文件被直接运行时，以下代码才会被执行
if __name__ == "__main__":
    # 初始化并运行 MCP 服务器
    # transport='stdio' 表示服务器将通过标准输入/输出(stdin/stdout)与客户端（如大模型）进行通信。
    # 这是与本地模型或调试工具交互的常见方式。
    mcp.run(transport='stdio')
