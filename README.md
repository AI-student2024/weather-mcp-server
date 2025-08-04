# Weather MCP Server

一个基于美国国家气象局(NWS) API的MCP天气服务器，提供灵活的天气查询功能。

## 🌤️ 功能特性

- **实时天气数据**：基于美国国家气象局官方API
- **灵活日期查询**：支持多种日期格式和相对日期
- **多地区支持**：支持美国境内的任何地点
- **天气预警**：获取州级天气预警信息
- **详细预报**：包含温度、风力、详细天气描述

## 🚀 快速开始

### 安装依赖

```bash
# 使用uv安装依赖
uv add mcp[cli] httpx
```

### 启动服务器

```bash
# 启动MCP服务器
uv run weather.py
```

## 📋 支持的查询格式

### 1. 完整日期格式
- `"8月7日"` - 查询指定日期的天气
- `"8月7号"` - 查询指定日期的天气（号字版本）

### 2. 简化日期格式
- `"7号"` - 查询7号的天气（当前月或下个月）
- `"10号"` - 查询10号的天气（自动识别月份）

### 3. 相对日期
- `"今天"` - 查询今天的天气
- `"明天"` - 查询明天的天气
- `"后天"` - 查询后天的天气
- `"大后天"` - 查询大后天的天气

### 4. 未来天数
- `"未来3天"` - 查询未来3天的天气
- `"未来5天"` - 查询未来5天的天气

### 5. 天气预警
- `"CA"` - 查询加州的天气预警
- `"NY"` - 查询纽约州的天气预警

## 🔧 API工具

### get_forecast_by_date
根据日期描述获取天气预报。

**参数：**
- `latitude`: 地点的纬度
- `longitude`: 地点的经度
- `date_description`: 日期描述

**示例：**
```python
await get_forecast_by_date(37.3861, -122.0839, "8月7日")
```

### get_weather_flexible
灵活的天气查询工具，支持多种日期格式。

**参数：**
- `latitude`: 地点的纬度
- `longitude`: 地点的经度
- `query`: 查询字符串

**示例：**
```python
await get_weather_flexible(37.3861, -122.0839, "明天")
```

### get_forecast
获取指定地点的天气预报（默认未来5个周期）。

**参数：**
- `latitude`: 地点的纬度
- `longitude`: 地点的经度

**示例：**
```python
await get_forecast(37.3861, -122.0839)
```

### get_alerts
获取指定州的天气预警信息。

**参数：**
- `state`: 两个字母的美国州代码

**示例：**
```python
await get_alerts("CA")
```

## 📍 常用地点坐标

### 加州主要城市
- **山景城 (Mountain View)**: 37.3861, -122.0839
- **旧金山 (San Francisco)**: 37.7749, -122.4194
- **洛杉矶 (Los Angeles)**: 34.0522, -118.2437
- **圣地亚哥 (San Diego)**: 32.7157, -117.1611
- **萨克拉门托 (Sacramento)**: 38.5816, -121.4944

### 其他城市
- **纽约 (New York)**: 40.7128, -74.0060
- **芝加哥 (Chicago)**: 41.8781, -87.6298
- **西雅图 (Seattle)**: 47.6062, -122.3321

## 📊 返回数据格式

### 天气预报数据
```
Thursday:
温度: 80°F
风力: 2 to 10 mph W
预报: Mostly sunny, with a high near 80.

---

Thursday Night:
温度: 59°F
风力: 2 to 10 mph W
预报: Partly cloudy, with a low around 59.
```

### 天气预警数据
```
事件: Wind Advisory
区域: Santa Ynez Mountains Eastern Range
严重性: Moderate
描述: North winds 20 to 30 mph with gusts up to 45 mph expected.
指令: Winds this strong can make driving difficult.
```

## 🔍 使用示例

### 查询山景城明天天气
```python
await get_weather_flexible(37.3861, -122.0839, "明天")
```

### 查询旧金山8月7日天气
```python
await get_forecast_by_date(37.7749, -122.4194, "8月7日")
```

### 查询加州天气预警
```python
await get_alerts("CA")
```

### 查询未来3天天气
```python
await get_weather_flexible(37.3861, -122.0839, "未来3天")
```

## ⚠️ 注意事项

1. **数据源限制**：仅支持美国境内的天气数据
2. **历史天气**：不支持查询历史天气数据
3. **跨年查询**：暂不支持跨年日期查询
4. **API限制**：遵循NWS API的使用限制和频率

## 🛠️ 技术实现

- **API**: 美国国家气象局 (NWS) API
- **框架**: FastMCP
- **HTTP客户端**: httpx
- **日期处理**: Python datetime + calendar
- **正则表达式**: 日期格式解析

## 📝 更新日志

### v1.1.0 (2025-08-04)
- ✅ 新增完整日期格式支持（"8月7日"、"8月7号"）
- ✅ 优化月份计算逻辑
- ✅ 改进错误处理
- ✅ 增强日期解析功能

### v1.0.0 (2025-08-04)
- ✅ 基础天气查询功能
- ✅ 相对日期支持
- ✅ 天气预警功能
- ✅ MCP服务器集成

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目基于MIT许可证开源。
