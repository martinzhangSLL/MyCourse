"""
安全工具模块 (Security Utilities)

此文件提供密码哈希和确认码生成的工具函数：

1. 密码哈希：
   - hash_password(): 使用 bcrypt 对密码进行单向哈希
   - verify_password(): 验证密码是否匹配

2. 确认码生成：
   - get_default_settlement_code(): 获取结算确认码
   - get_default_init_code(): 获取初始化确认码

架构说明：
- bcrypt: 目前最安全的密码哈希算法之一
  * 可配置的工作因子（cost factor）
  * 内置盐值（salt）生成
  * 设计为计算昂贵，难以被暴力破解

- secrets.token_hex(): 生成密码学安全的随机十六进制字符串
  * 用于生成结算码和初始化码
"""

import os
import secrets  # 密码学安全的随机数生成

import bcrypt  # 密码哈希库


# ========== 密码哈希函数 ==========

def hash_password(password: str) -> str:
    """
    对密码进行单向哈希处理

    使用 bcrypt 算法对密码进行哈希，这是业界标准的密码存储方式

    工作原理：
    1. 生成随机的盐值（salt）- 16字节
    2. 将盐值和密码组合在一起
    3. 使用 bcrypt 哈希函数进行多轮哈希计算
    4. 返回格式：$2b$12$<salt><hash>（bcrypt 特有的格式）

    为什么使用 bcrypt：
    - 单向性：无法从哈希值反推密码
    - 内置盐值：相同密码也会产生不同的哈希值（防止彩虹表攻击）
    - 可配置难度：可以通过 cost factor 调整计算成本
    - 计算缓慢：即使 GPU 也难以进行暴力破解

    参数：
        password: 明文密码字符串

    返回：
        str: bcrypt 哈希后的密码字符串
             格式：$2b$12$<salt><hash>
             例如：$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.S0O6C.6iHy8Hy
    """
    # Step 1: 生成 bcrypt 盐值
    # gensalt() 生成一个随机的盐值
    # bcrypt.gensalt() 默认工作因子为 12（2^12 = 4096 次迭代）
    salt = bcrypt.gensalt()

    # Step 2: 对密码进行哈希
    # hashpw() 函数：
    # - 将密码和盐值组合
    # - 执行多轮 bcrypt 哈希
    # - 返回哈希结果
    #
    # 注意：
    # - bcrypt.hashpw() 期望 bytes 类型输入
    # - 因此需要先将字符串编码为 UTF-8 字节
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Step 3: 将字节转换为字符串返回
    # decode('utf-8') 将字节转换回字符串
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否与哈希值匹配

    用于登录时验证用户输入的密码是否正确

    工作原理：
    1. 将用户输入的明文密码进行哈希
    2. 将哈希结果与存储的哈希值进行比较
    3. bcrypt 的特点：相同输入会产生相同输出（基于盐值存储）

    参数：
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的 bcrypt 哈希值

    返回：
        bool: True 表示密码匹配，False 表示不匹配

    注意：
        - 不应该告诉攻击者密码"不正确"还是"不存在"
        - 始终执行完整的验证流程（即使是不存在的用户也要执行哈希计算）
        - 这是为了防止时序攻击（timing attack）
    """
    # bcrypt.checkpw() 自动处理盐值提取和比较
    # 返回 True 如果匹配，False 如果不匹配

    # 同样需要将字符串编码为字节
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# ========== 确认码生成函数 ==========

def get_default_settlement_code() -> str:
    """
    获取结算确认码

    结算确认码用于验证结算操作的合法性，防止误操作

    获取顺序：
    1. 优先使用环境变量 SETTLEMENT_CODE（如果已设置）
    2. 否则自动生成一个随机的 16 位十六进制字符串

    用途：
    - 在进行学期结算时需要输入此码进行确认
    - 确保结算操作是有意为之，而不是误操作

    返回：
        str: 结算确认码
             - 如果设置了环境变量：返回环境变量的值
             - 否则：返回 secrets.token_hex(8) 生成的大写十六进制字符串
               例如："A3F7B2C1D4E59081"
    """
    return os.environ.get("SETTLEMENT_CODE", secrets.token_hex(8).upper())


def get_default_init_code() -> str:
    """
    获取初始化确认码

    初始化确认码用于验证系统初始化操作的合法性

    获取顺序：
    1. 优先使用环境变量 INIT_CODE（如果已设置）
    2. 否则自动生成一个随机的 16 位十六进制字符串

    用途：
    - 在进行系统初始化（重置数据）时需要输入此码进行确认
    - 防止未授权的初始化操作

    返回：
        str: 初始化确认码
             - 如果设置了环境变量：返回环境变量的值
             - 否则：返回 secrets.token_hex(8) 生成的大写十六进制字符串
               例如："B4C2D8E1F7A39056"
    """
    return os.environ.get("INIT_CODE", secrets.token_hex(8).upper())
