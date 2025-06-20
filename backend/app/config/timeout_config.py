# 超时配置文件
# 统一管理所有服务的超时设置

# OpenAI API 超时设置
OPENAI_TIMEOUT = 120.0  # OpenAI API调用超时时间（秒）
OPENAI_MAX_RETRIES = 3  # OpenAI API最大重试次数
OPENAI_RETRY_DELAY = 2  # OpenAI API重试延迟（秒）

# 数据库操作超时设置
DB_TIMEOUT = 30.0  # 数据库操作超时时间（秒）
DB_CONNECTION_TIMEOUT = 10.0  # 数据库连接超时时间（秒）

# HTTP请求超时设置
HTTP_TIMEOUT = 60.0  # HTTP请求超时时间（秒）
HTTP_CONNECT_TIMEOUT = 10.0  # HTTP连接超时时间（秒）

# 文件操作超时设置
FILE_UPLOAD_TIMEOUT = 300.0  # 文件上传超时时间（秒）
FILE_PROCESS_TIMEOUT = 180.0  # 文件处理超时时间（秒）

# FastAPI服务器超时设置
SERVER_TIMEOUT = 300.0  # 服务器请求超时时间（秒）
SERVER_KEEP_ALIVE_TIMEOUT = 30.0  # Keep-Alive超时时间（秒）

# 文本处理限制
MAX_TEXT_LENGTH = 8000  # 最大文本长度（字符）
MAX_TOKENS = 3000  # OpenAI最大token数

# 重试配置
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0 