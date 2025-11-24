import asyncio
import json
import logging
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
        
        # 根据你的ESP8266代码配置
        self.bemfa_config = {
            "server": "bemfa.com",
            "port": 9501,
            "client_id": "1027eaa277d6457fa609c8286749e828",  # 你的巴法云UID
            "topic": "MasterLight002"  # 你的主题名
        }
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """返回可用的工具列表"""
            return [
                Tool(
                    name="connect_bemfa",
                    description="连接到巴法云MQTT服务器",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "string",
                                "description": "巴法云客户端ID，默认为1027eaa277d6457fa609c8286749e828"
                            },
                            "topic": {
                                "type": "string", 
                                "description": "MQTT主题，默认为MasterLight002"
                            }
                        }
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
                    description="设备管理功能",
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
                    name="get_device_info",
                    description="获取设备信息",
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
                if name == "connect_bemfa":
                    return await self._connect_bemfa(arguments)
                elif name == "control_light":
                    return await self._control_light(arguments)
                elif name == "device_management":
                    return await self._device_management(arguments)
                elif name == "get_device_info":
                    return await self._get_device_info(arguments)
                else:
                    raise ValueError(f"未知工具: {name}")
            except Exception as e:
                logger.error(f"工具调用错误: {e}")
                return [TextContent(type="text", text=f"错误: {str(e)}")]
    
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
        if self.mqtt_client and self.connected:
            return [TextContent(type="text", text="已经连接到巴法云MQTT服务器")]
        
        # 使用参数或默认配置
        client_id = arguments.get("client_id", self.bemfa_config["client_id"])
        topic = arguments.get("topic", self.bemfa_config["topic"])
        
        self.bemfa_config["client_id"] = client_id
        self.bemfa_config["topic"] = topic
        
        # 创建MQTT客户端
        self.mqtt_client = mqtt.Client(client_id=client_id)
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
                return [TextContent(type="text", text=f"成功连接到巴法云MQTT服务器，主题: {topic}")]
            else:
                return [TextContent(type="text", text="连接巴法云MQTT服务器超时")]
                
        except Exception as e:
            logger.error(f"连接错误: {e}")
            return [TextContent(type="text", text=f"连接失败: {str(e)}")]
    
    async def _control_light(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """控制灯光 - 完全匹配ESP8266代码"""
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
        """设备管理功能 - 匹配ESP8266的resetwifi和reconfig功能"""
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
            
            action_descriptions = {
                "resetwifi": "重置WiFi配置，设备将恢复出厂设置并等待重新配网",
                "reconfig": "重新启动配网模式，设备将进入SmartConfig等待状态"
            }
            
            return [TextContent(type="text", text=f"已发送设备管理命令: {message}\n{action_descriptions[action]}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"发送设备管理命令失败: {str(e)}")]
    
    async def _get_device_info(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """获取设备信息"""
        device_id = self.bemfa_config["topic"]
        
        info_lines = [
            "设备信息:",
            f"主题: {device_id}",
            f"MQTT服务器: {self.bemfa_config['server']}:{self.bemfa_config['port']}",
            f"连接状态: {'已连接' if self.connected else '未连接'}"
        ]
        
        if device_id in self.devices:
            status_info = self.devices[device_id]
            info_lines.append(f"设备状态: {status_info['status']}")
            info_lines.append(f"最后更新: {status_info['last_update']}")
        else:
            info_lines.append("设备状态: 未知")
        
        # 发送状态查询以获取最新状态
        if self.connected:
            try:
                self.mqtt_client.publish(device_id, "status")
                info_lines.append("\n已发送状态查询请求...")
            except Exception as e:
                info_lines.append(f"\n状态查询失败: {str(e)}")
        
        return [TextContent(type="text", text="\n".join(info_lines))]
    
    async def run(self):
        """运行MCP服务器"""
        # 自动连接（使用默认配置）
        logger.info("正在自动连接到巴法云MQTT服务器...")
        auto_connect_result = await self._connect_bemfa({})
        if "成功" in auto_connect_result[0].text:
            logger.info("自动连接成功")
        else:
            logger.warning("自动连接失败，需要手动连接")
        
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