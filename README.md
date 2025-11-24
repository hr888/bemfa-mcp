# 1. 连接巴法云（使用默认配置，自动连接）
connect_bemfa({})

# 2. 控制灯光
control_light({"command": "on"})    # 开灯
control_light({"command": "off"})   # 关灯  
control_light({"command": "toggle"}) # 切换
control_light({"command": "status"}) # 查询状态

# 3. 设备管理
device_management({"action": "resetwifi"})  # 重置WiFi
device_management({"action": "reconfig"})   # 重新配网

# 4. 获取设备信息

get_device_info({})

# 巴法云MQTT控制MCP服务

## 安全说明
⚠️ **重要安全提示**: 此MCP服务不再包含任何硬编码的个人信息，每个用户需要配置自己的巴法云参数。

## 使用步骤

### 1. 配置连接参数
首先调用 `configure_bemfa` 工具配置你的巴法云参数：
