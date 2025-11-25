# 巴法云MQTT控制MCP服务

基于魔搭平台的MCP协议智能家居控制服务。

## 快速开始
python
from modelscope.pipelines import pipeline
创建管道
bemfa_pipe = pipeline('bemfa-mcp-pipeline', 'hr888/bemfa-mcp')
控制灯光
result = bemfa_pipe({
"action": "control_light",
"params": {"command": "on", "device_id": "light001"}
})
print(result)
## 功能特性

- ✅ MCP协议标准化
- ✅ 巴法云MQTT集成  
- ✅ 智能灯光控制
- ✅ 魔搭平台兼容

## 部署说明

本项目已适配魔搭平台，可直接部署使用。