# 巴法云MQTT MCP服务（环境变量配置版）

基于魔搭平台的巴法云MQTT智能灯光控制服务，通过环境变量配置连接参数。

## 环境变量配置

在使用此服务前，请在魔搭平台配置以下环境变量：

| 环境变量 | 说明 | 示例值 |
|---------|------|--------|
| `BEMFA_SERVER` | 巴法云服务器地址 | `bemfa.com` |
| `BEMFA_PORT` | 巴法云MQTT端口 | `9501` |
| `DEFAULT_CLIENT_ID` | 您的巴法云客户端ID | `1027eaa277d6457fa609c8286749e828` |
| `DEFAULT_TOPIC` | 默认MQTT主题 | `MasterLight002` |
| `SERVER_PORT` | 服务器端口 | `4000` |

## 可用工具

1. **connectBemfa** - 连接到巴法云MQTT服务器
2. **controlLight** - 控制智能灯光（on/off/toggle/status）
3. **getStatus** - 获取当前连接状态

## 使用示例
json
{
"jsonrpc": "2.0",
"id": 1,
"method": "tools/call",
"params": {
"name": "connectBemfa"
}
}
{
"jsonrpc": "2.0",
"id": 2,
"method": "tools/call",
"params": {
"name": "controlLight",
"arguments": {
"command": "on"
}
}
}
## 部署说明

1. 在魔搭平台创建MCP服务器
2. 上传所有文件
3. 配置环境变量
4. 启动服务

## 获取巴法云参数

1. 访问 [巴法云官网](https://www.bemfa.com/)
2. 注册账号并登录控制台
3. 创建MQTT设备，获取客户端ID和主题
4. 在魔搭平台配置环境变量
6. 魔搭平台部署步骤
步骤1：创建MCP服务器
登录魔搭平台
进入MCP服务器创建页面
选择"自定义服务器"
步骤2：配置服务
在服务配置区域粘贴上面的JSON配置。
步骤3：设置环境变量
在环境变量配置区域设置以下变量：
BEMFA_SERVER=bemfa.com
BEMFA_PORT=9501
DEFAULT_CLIENT_ID=您的巴法云客户端ID
DEFAULT_TOPIC=您的MQTT主题
SERVER_PORT=4000
NODE_ENV=production
步骤4：上传文件
将以下文件打包为ZIP上传：
bemfa_mcp.py
requirements.txt
README.md（可选）
步骤5：启动服务
完成配置后启动服务器。
