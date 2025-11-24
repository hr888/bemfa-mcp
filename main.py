import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
import paho.mqtt.client as mqtt
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.models as models

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BemfaMCP:
    def __init__(self):
        self.server = Server("bemfa-mcp")
        self.mqtt_client = None
        self.connected = False
        self.devices = {}  # 存储设备状态
        
        # 从环境变量或配置文件读取配置（不再硬编码）
        self.bemfa_config = {
            "server": os.getenv("BEMFA_SERVER", "bemfa.com"),
            "port": int(os.getenv("BEMFA_PORT", "9501")),
            "client_id": os.getenv("BEMFA_CLIENT_ID", ""),  # 必须由用户配置
            "topic": os.getenv("BEMFA_TOPIC", "light001")   # 默认主题
        }
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """返回可用的工具列表"""
            return [
                Tool(
                    name="configure_bemfa",
                    description="配置巴法云连接参数（首次使用必须调用）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "string",
                                "description": "巴法云客户端ID（必填）"
                            },
                            "topic": {
                                "type": "string", 
                                "description": "MQTT主题，默认为light001"
                            },
                            "server": {
                                "type": "string",
                                "description": "MQTT服务器，默认为bemfa.com"
                            },
                            "port": {
                                "type": "integer",
                                "description": "MQTT端口，默认为9501"
                            }
                        },
                        "required": ["client_id"]
                    }
                ),
                Tool(
                    name="connect_bemfa",
                    description="连接到巴法云MQTT服务器",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="control_light",
                    description="控制ESP8266灯光开关",
                    inputSchema={
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
                ),
                Tool(
                    name="device_management",
                    description="设备管理功能（谨慎使用）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["resetwifi", "reconfig"],
                                "description": "设备管理操作：重置WiFi(resetwifi)、重新配网(reconfig)"
                            }
                        },
                        "required": ["action"]
                    }
                ),
                Tool(
                    name="get_connection_status",
                    description="获取当前连接状态和配置信息",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            try:
                if name == "configure_bemfa":
                    return await self._configure_bemfa(arguments)
                elif name == "connect_bemfa":
                    return await self._connect_bemfa(arguments)
                elif name == "control_light":
                    return await self._control_light(arguments)
                elif name == "device_management":
                    return await self._device_management(arguments)
                elif name == "get_connection_status":
                    return await self._get_connection_status(arguments)
                else:
                    raise ValueError(f"未知工具: {name}")
            except Exception as e:
                logger.error(f"工具调用错误: {e}")
                return [TextContent(type="text", text=f"错误: {str(e)}")]
    
    async def _configure_bemfa(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """配置巴法云连接参数"""
        client_id = arguments.get("client_id")
        topic = arguments.get("topic", "light001")
        server = arguments.get("server", "bemfa.com")
        port = arguments.get("port", 9501)
        
        if not client_id:
            return [TextContent(type="text", text="错误: client_id 是必填参数")]
        
        # 更新配置
        self.bemfa_config.update({
            "client_id": client_id,
            "topic": topic,
            "server": server,
            "port": port
        })
        
        # 隐藏敏感信息的显示（只显示部分字符）
        masked_client_id = client_id[:8] + "***" + client_id[-8:] if len(client_id) > 16 else "***"
        
        config_info = f"""
巴法云配置已更新:
- 服务器: {server}:{port}
- 主题: {topic}
- 客户端ID: {masked_client_id}

请调用 connect_bemfa 工具进行连接。
        """
        
        return [TextContent(type="text", text=config_info)]
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.connected = True
            logger.info("成功连接到巴法云MQTT服务器")
            
            # 订阅设备状态主题
            status_topic = f"{self.bemfa_config['topic']}/status"
            client.subscribe(status_topic)
            logger.info(f"已订阅状态主题: {status_topic}")
            
            # 订阅主主题
            client.subscribe(self.bemfa_config['topic'])
            logger.info(f"已订阅主主题: {self.bemfa_config['topic']}")
        else:
            self.connected = False
            logger.error(f"MQTT连接失败，错误码: {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT消息回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.info(f"收到消息 - 主题: {topic}, 内容: {payload}")
            
            # 解析设备状态更新
            if topic.endswith("/status"):
                device_id = topic.split("/")[0]
                self.devices[device_id] = {
                    "status": payload,
                    "last_update": asyncio.get_event_loop().time()
                }
                logger.info(f"设备 {device_id} 状态更新为: {payload}")
        except Exception as e:
            logger.error(f"处理MQTT消息错误: {e}")
    
    async def _connect_bemfa(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """连接到巴法云MQTT服务器"""
        if not self.bemfa_config["client_id"]:
            return [TextContent(type="text", text="错误: 请先调用 configure_bemfa 工具配置连接参数")]
        
        if self.mqtt_client and self.connected:
            return [TextContent(type="text", text="已经连接到巴法云MQTT服务器")]
        
        # 创建MQTT客户端
        self.mqtt_client = mqtt.Client(client_id=self.bemfa_config["client_id"])
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        
        try:
            # 连接MQTT服务器（异步处理）
            def connect():
                self.mqtt_client.connect(
                    self.bemfa_config["server"],
                    self.bemfa_config["port"],
                    60
                )
                self.mqtt_client.loop_start()
            
            await asyncio.get_event_loop().run_in_executor(None, connect)
            
            # 等待连接建立
            for i in range(10):
                if self.connected:
                    break
                await asyncio.sleep(0.5)
            
            if self.connected:
                # 隐藏敏感信息显示
                masked_client_id = self.bemfa_config["client_id"][:8] + "***" + self.bemfa_config["client_id"][-8:] if len(self.bemfa_config["client_id"]) > 16 else "***"
                
                success_msg = f"""
成功连接到巴法云MQTT服务器!
- 服务器: {self.bemfa_config['server']}:{self.bemfa_config['port']}
- 主题: {self.bemfa_config['topic']}
- 客户端ID: {masked_client_id}

现在可以使用 control_light 工具控制设备了。
                """
                return [TextContent(type="text", text=success_msg)]
            else:
                return [TextContent(type="text", text="连接巴法云MQTT服务器超时")]
                
        except Exception as e:
            logger.error(f"连接错误: {e}")
            return [TextContent(type="text", text=f"连接失败: {str(e)}")]
    
    async def _control_light(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """控制灯光"""
        if not self.connected:
            return [TextContent(type="text", text="错误: 请先连接到巴法云MQTT服务器")]
        
        command = arguments["command"]
        
        # 根据ESP8266代码支持的命令
        command_map = {
            "on": ["on master light", "1", "on"],
            "off": ["off master light", "0", "off"],
            "toggle": ["toggle"],
            "status": ["status"]
        }
        
        if command not in command_map:
            valid_commands = list(command_map.keys())
            return [TextContent(type="text", text=f"错误: 无效命令。可用命令: {', '.join(valid_commands)}")]
        
        # 发送所有支持的命令格式（确保兼容性）
        messages = command_map[command]
        results = []
        
        for msg in messages:
            try:
                self.mqtt_client.publish(self.bemfa_config["topic"], msg)
                logger.info(f"发布命令: {self.bemfa_config['topic']} -> {msg}")
                results.append(f"已发送: {msg}")
                
                # 如果是状态查询，等待状态更新
                if command == "status":
                    await asyncio.sleep(1)  # 等待设备响应
                    
            except Exception as e:
                results.append(f"发送失败 {msg}: {str(e)}")
        
        # 获取当前状态（如果可用）
        status_info = ""
        device_id = self.bemfa_config["topic"]
        if device_id in self.devices:
            status = self.devices[device_id]["status"]
            status_info = f"\n当前状态: {status}"
        
        result_text = "命令执行结果:\n" + "\n".join(results) + status_info
        return [TextContent(type="text", text=result_text)]
    
    async def _device_management(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """设备管理功能"""
        if not self.connected:
            return [TextContent(type="text", text="错误: 请先连接到巴法云MQTT服务器")]
        
        action = arguments["action"]
        
        action_map = {
            "resetwifi": "resetwifi",
            "reconfig": "reconfig"
        }
        
        if action not in action_map:
            valid_actions = list(action_map.keys())
            return [TextContent(type="text", text=f"错误: 无效操作。可用操作: {', '.join(valid_actions)}")]
        
        message = action_map[action]
        
        try:
            self.mqtt_client.publish(self.bemfa_config["topic"], message)
            logger.info(f"发布设备管理命令: {self.bemfa_config['topic']} -> {message}")
            
            warning_msg = """
⚠️ 警告：设备管理命令已发送！

resetwifi: 设备将重置WiFi配置并恢复出厂设置
reconfig: 设备将重新进入配网模式

这些操作会影响设备连接，请谨慎使用！
            """
            
            return [TextContent(type="text", text=warning_msg)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"发送设备管理命令失败: {str(e)}")]
    
    async def _get_connection_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """获取连接状态"""
        # 隐藏敏感信息
        masked_client_id = "未配置"
        if self.bemfa_config["client_id"]:
            if len(self.bemfa_config["client_id"]) > 16:
                masked_client_id = self.bemfa_config["client_id"][:8] + "***" + self.bemfa_config["client_id"][-8:]
            else:
                masked_client_id = "***"
        
        info_lines = [
            "连接状态:",
            f"MQTT服务器: {self.bemfa_config['server']}:{self.bemfa_config['port']}",
            f"主题: {self.bemfa_config['topic']}",
            f"客户端ID: {masked_client_id}",
            f"连接状态: {'✅ 已连接' if self.connected else '❌ 未连接'}"
        ]
        
        device_id = self.bemfa_config["topic"]
        if device_id in self.devices:
            status_info = self.devices[device_id]
            info_lines.append(f"设备状态: {status_info['status']}")
        
        if not self.bemfa_config["client_id"]:
            info_lines.append("\n⚠️ 提示: 请先调用 configure_bemfa 工具配置连接参数")
        
        return [TextContent(type="text", text="\n".join(info_lines))]
    
    async def run(self):
        """运行MCP服务器"""
        async with self.server.run_stdio() as (read_stream, write_stream):
            await asyncio.gather(
                read_stream,
                write_stream,
            )

async def main():
    bemfa_mcp = BemfaMCP()
    await bemfa_mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
