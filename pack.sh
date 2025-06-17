#!/bin/sh

# 1. 生成系统日志
if command -v get_sysinfo.sh >/dev/null 2>&1; then
    get_sysinfo.sh > /tmp/log/sys.log && sync
else
    echo "未找到 get_sysinfo.sh，跳过系统信息收集"
fi

# 2. 获取设备SN
echo "正在获取设备SN..."
if command -v get_sn >/dev/null 2>&1; then
    DEV_SN=$(get_sn)
else
    echo "未找到 get_sn，使用默认SN"
    DEV_SN="UNKNOWN_SN"
fi

# 3. 收集日志文件
echo "正在收集日志文件..."
if command -v get_log_files >/dev/null 2>&1; then
    MANUAL_PACK_FILES=$(get_log_files)
else
    echo "未找到 get_log_files，打包内容为空"
    MANUAL_PACK_FILES=""
fi

# 4. 时间戳
TIME=$(date '+%Y-%m-%d-%H-%M-%S')

# 5. 生成文件名
if [ -z "$1" ]; then
    FILE_NAME=/data/manual_pack-${DEV_SN}-${TIME}.tar.gz
else
    FILE_NAME=/data/manual_pack-$1-${DEV_SN}-${TIME}.tar.gz
fi

# 6. 打包
if [ -z "$MANUAL_PACK_FILES" ]; then
    echo "没有需要打包的文件，退出"
    exit 1
fi

echo "开始打包日志到 $FILE_NAME"
tar -czf "${FILE_NAME}" ${MANUAL_PACK_FILES}
if [ $? -eq 0 ]; then
    echo "日志打包完成：$FILE_NAME"
else
    echo "日志打包失败"
    exit 2
fi

sync
echo "全部完成"