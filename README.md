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

