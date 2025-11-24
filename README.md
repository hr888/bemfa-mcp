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