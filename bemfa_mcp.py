#!/usr/bin/env python3
"""
巴法云MQTT MCP服务 - 环境变量配置版本
用户需要在魔搭平台配置环境变量
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
import paho.mqtt.client as mqtt
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bemfa-mcp")

# 从环境变量读取配置
CONFIG = {
    "bemfa_server": os.getenv("BEMFA_SERVER", "bemfa.com"),
    "bemfa_port": int(os.getenv("BEMFA_PORT", "9501")),
    "default_client_id": os.getenv("DEFAULT_CLIENT_ID", ""),
    "default_topic": os.getenv("DEFAULT_TOPIC", ""),
    "server_port": int(os.getenv("SERVER_PORT", "4000")),
}

class BemfaMCPClient:
    """巴法云MCP客户端 - 环境变量配置版本"""
    
    def __init__(self):
        self.mqtt_client = None
        self.connected = False
        self.config = CONFIG
        
        # 验证配置
        self._validate_config()
        
        logger.info("BemfaMCPClient初始化完成")
        logger.info(f"配置: 服务器={self.config['bemfa_server']}:{self.config['bemfa_port']}")
        logger.info(f"主题: {self.config['default_topic']}")
    
    def _validate_config(self):
        """验证环境变量配置"""
        if not self.config["default_client_id"]:
            raise ValueError("环境变量 DEFAULT_CLIENT_ID 未设置")
        if not self.config["default_topic"]:
            raise ValueError("环境变量 DEFAULT_TOPIC 未设置")
        
        logger.info("环境变量配置验证通过")
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        logger.info("处理初始化请求")
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
            },
            "serverInfo": {
                "name": "bemfa-mcp-env",
                "version": "1.0.0",
                "description": "巴法云MQTT控制服务（环境变量配置版）"
            }
        }
    
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """返回工具列表"""
        logger.info("返回工具列表")
        
        return {
            "tools": [
                {
                    "name": "connectBemfa",
                    "description": "连接到巴法云MQTT服务器（使用环境变量配置）",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "clientId": {
                                "type": "string", 
                                "description": "客户端ID（可选，默认使用环境变量配置）",
                                "default": self.config["default_client_id"]
                            },
                            "topic": {
                                "type": "string",
                                "description": "主题名称（可选，默认使用环境变量配置）",
                                "default": self.config["default_topic"]
                            }
                        }
                    }
                },
                {
                    "name": "controlLight",
                    "description": "控制智能灯光",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string", 
                                "enum": ["on", "off", "toggle", "status"],
                                "description": "控制命令：开灯(on)、关灯(off)、切换(toggle)、状态查询(status)" 
                            }
                        },
                        "required": ["command"]
                    }
                },
                {
                    "name": "getStatus",
                    "description": "获取当前连接状态和配置信息",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"处理工具调用: {tool_name}")
        
        try:
            if tool_name == "connectBemfa":
                return await self.connect_bemfa(arguments)
            elif tool_name == "controlLight":
                return await self.control_light(arguments)
            elif tool_name == "getStatus":
                return await self.get_status(arguments)
            else:
                return {
                    "isError": True, 
                    "content": [{"type": "text", "text": f"未知工具: {tool_name}"}]
                }
        except Exception as e:
            logger.error(f"工具调用错误: {e}")
            return {
                "isError": True, 
                "content": [{"type": "text", "text": f"错误: {str(e)}"}]
            }
    
    async def connect_bemfa(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """连接到巴法云MQTT服务器"""
        if self.connected and self.mqtt_client:
            return {
                "content": [{
                    "type": "text", 
                    "text": "✅ 已经连接到巴法云MQTT服务器"
                }]
            }
        
        # 使用参数或环境变量默认值
        client_id = args.get("clientId", self.config["default_client_id"])
        topic = args.get("topic", self.config["default_topic"])
        server = self.config["bemfa_server"]
        port = self.config["bemfa_port"]
        
        logger.info(f"连接参数: 客户端ID={client_id}, 主题={topic}")
        
        try:
            # 创建MQTT客户端
            self.mqtt_client = mqtt.Client(client_id=client_id)
            
            # 定义回调函数
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    self.connected = True
                    logger.info("MQTT连接成功")
                    # 订阅主题
                    client.subscribe(topic)
                    logger.info(f"已订阅主题: {topic}")
                else:
                    logger.error(f"MQTT连接失败，返回码: {rc}")
                    self.connected = False
            
            def on_message(client, userdata, msg):
                message = msg.payload.decode()
                logger.info(f"收到消息: {msg.topic} - {message}")
            
            def on_disconnect(client, userdata, rc):
                self.connected = False
                logger.info("MQTT连接已断开")
            
            # 设置回调
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_message = on_message
            self.mqtt_client.on_disconnect = on_disconnect
            
            # 连接服务器
            self.mqtt_client.connect_async(server, port)
            self.mqtt_client.loop_start()
            
            # 等待连接建立
            for i in range(10):
                if self.connected:
                    break
                await asyncio.sleep(0.5)
            
            if self.connected:
                return {
                    "content": [{
                        "type": "text", 
                        "text": f"✅ 成功连接到巴法云MQTT服务器\n服务器: {server}:{port}\n主题: {topic}\n客户端ID: {client_id}"
                    }]
                }
            else:
                return {
                    "isError": True,
                    "content": [{
                        "type": "text", 
                        "text": "❌ 连接超时，请检查网络连接和服务器配置"
                    }]
                }
                
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return {
                "isError": True,
                "content": [{
                    "type": "text", 
                    "text": f"❌ 连接失败: {str(e)}"
                }]
            }
    
    async def control_light(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """控制灯光"""
        if not self.connected or not self.mqtt_client:
            return {
                "isError": True,
                "content": [{
                    "type": "text", 
                    "text": "❌ 未连接到MQTT服务器，请先调用 connectBemfa"
                }]
            }
        
        command = args.get("command")
        valid_commands = ["on", "off", "toggle", "status"]
        
        if command not in valid_commands:
            return {
                "isError": True,
                "content": [{
                    "type": "text", 
                    "text": f"❌ 无效命令，可用命令: {', '.join(valid_commands)}"
                }]
            }
        
        topic = self.config["default_topic"]
        
        try:
            # 发布控制命令
            self.mqtt_client.publish(topic, command)
            
            action_text = {
                "on": "开灯",
                "off": "关灯", 
                "toggle": "切换灯光",
                "status": "状态查询"
            }[command]
            
            return {
                "content": [{
                    "type": "text", 
                    "text": f"✅ 已发送{action_text}命令到主题: {topic}"
                }]
            }
            
        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            return {
                "isError": True,
                "content": [{
                    "type": "text", 
                    "text": f"❌ 发送命令失败: {str(e)}"
                }]
            }
    
    async def get_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取状态信息"""
        status_info = [
            "=== 巴法云MCP服务状态 ===",
            f"服务器: {self.config['bemfa_server']}:{self.config['bemfa_port']}",
            f"主题: {self.config['default_topic']}",
            f"客户端ID: {self.config['default_client_id']}",
            f"连接状态: {'✅ 已连接' if self.connected else '❌ 未连接'}",
            f"运行环境: {os.getenv('NODE_ENV', 'unknown')}",
            "",
            "使用说明:",
            "1. 调用 connectBemfa 连接服务器",
            "2. 调用 controlLight 控制灯光",
            "3. 支持命令: on(开灯), off(关灯), toggle(切换), status(状态查询)"
        ]
        
        return {
            "content": [{
                "type": "text", 
                "text": "\n".join(status_info)
            }]
        }

async def main():
    """主函数 - 标准MCP服务器实现"""
    client = BemfaMCPClient()
    
    # 读取输入，写入输出（标准MCP协议）
    try:
        while True:
            # 读取一行输入
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
                
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            response = {"jsonrpc": "2.0", "id": request_id}
            
            try:
                if method == "initialize":
                    result = await client.handle_initialize(params)
                    response["result"] = result
                elif method == "tools/list":
                    result = await client.handle_tools_list(params)
                    response["result"] = result
                elif method == "tools/call":
                    result = await client.handle_tools_call(params)
                    response["result"] = result
                else:
                    response["error"] = {"code": -32601, "message": "方法不存在"}
                
                # 发送响应
                output = json.dumps(response) + "\n"
                sys.stdout.write(output)
                sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"处理请求时出错: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": "内部错误"}
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
                
    except Exception as e:
        logger.error(f"主循环错误: {e}")
    finally:
        # 清理资源
        if client.mqtt_client:
            client.mqtt_client.loop_stop()
            client.mqtt_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
