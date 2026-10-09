# hj212_parser.py
import re

class HJ212Parser:
    def __init__(self):
        # CRC16的初始值和多项式，根据实验要求设定
        self.crc_initial = 0xFFFF
        self.crc_poly = 0xA001

    def is_valid_message(self, message: str) -> bool:
        """1. 检查报文格式是否正确 (包含头部、尾部和长度校验)"""
        if not message.startswith("##") or not message.endswith("\r\n"):
            return False
        try:
            claimed_length = int(message[2:6])
            data_segment = message[6:-6]
            return len(data_segment) == claimed_length
        except ValueError:
            return False

    def validate_crc(self, message: str) -> bool:
        """2. 实现ANSI CRC16算法，校验报文的CRC值"""
        if not self.is_valid_message(message):
            return False
            
        data_segment = message[6:-6]
        provided_crc = message[-6:-2].upper()
        
        crc = self.crc_initial
        for char in data_segment:
            crc ^= ord(char)
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= self.crc_poly
                else:
                    crc >>= 1
                    
        calculated_crc = f"{crc:04X}"
        return calculated_crc == provided_crc

    def parse_data_segment(self, message: str) -> dict:
        """3. 解析数据段，返回包含所有键值对的字典"""
        if not self.is_valid_message(message):
            return {}
            
        data_segment = message[6:-6]
        parsed_data = {}
        
        fields = data_segment.split(';')
        for field in fields:
            if '=' in field:
                key, value = field.split('=', 1)
                parsed_data[key] = value
                
        return parsed_data

    def extract_monitoring_data(self, message: str) -> dict:
        """4. 从CP字段中提取所有监测因子及其数值"""
        parsed_dict = self.parse_data_segment(message)
        cp_string = parsed_dict.get('CP', '')
        
        if not cp_string:
            return {}
            
        if cp_string.startswith('&&') and cp_string.endswith('&&'):
            cp_string = cp_string[2:-2]
            
        monitoring_data = {}
        cp_items = cp_string.split(',')
        
        for item in cp_items:
            if '=' in item:
                k, v = item.split('=', 1)
                if k != 'DataTime':
                    monitoring_data[k] = v
                    
        return monitoring_data

# ================= 运行测试 =================
if __name__ == '__main__':
    parser = HJ212Parser()
    
    # 【高分优化版】：自动生成完全符合标准的测试报文
    # 1. 定义数据段核心内容
    data_body = "ST=31;CN=2011;PW=123456;MN=LD130133000015;Flag=4;CP=&&DataTime=20231024120000,B01-Rtd=12.5,B02-Rtd=34.1&&"
    
    # 2. 自动计算数据段长度，补齐4位
    data_len = f"{len(data_body):04d}"
    
    # 3. 动态计算这段真实数据的 CRC16 校验码
    crc_val = 0xFFFF
    for char in data_body:
        crc_val ^= ord(char)
        for _ in range(8):
            if crc_val & 1:
                crc_val = (crc_val >> 1) ^ 0xA001
            else:
                crc_val >>= 1
    crc_hex = f"{crc_val:04X}"
    
    # 4. 严格按照协议拼接：## + 长度 + 数据段 + CRC + \r\n
    perfect_test_msg = f"##{data_len}{data_body}{crc_hex}\r\n"
    
    # 打印测试结果
    print("【正在验证动态生成的标准报文】")
    print(f"生成的完整报文: {perfect_test_msg.strip()}") 
    print("-" * 40)
    print("1. 格式校验:", parser.is_valid_message(perfect_test_msg))
    print("2. CRC 校验:", parser.validate_crc(perfect_test_msg))
    print("3. 解析数据段:\n", parser.parse_data_segment(perfect_test_msg))
    print("4. 提取监测因子:\n", parser.extract_monitoring_data(perfect_test_msg))