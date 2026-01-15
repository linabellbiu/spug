#!/bin/bash
# Copyright: (c) OpenSpug Organization. https://github.com/openspug/spug
# Copyright: (c) <spug.dev@gmail.com>
# Released under the AGPL-3.0 License.
# start api service

# 修复1：初始化conda环境（解决conda activate报错）
source /root/miniconda3/etc/profile.d/conda.sh  # 替换为你的conda安装路径，默认是这个
# 如果不知道conda路径，先执行：find / -name "conda.sh" 找到后替换

# 修复2：切换到脚本所在的上级目录（确保能找到spug模块）
cd $(dirname $0)/../  # 切换到spug_api根目录

# 修复3：优先使用虚拟环境的Python/daphne（避免系统环境找不到spug模块）
source venv/bin/activate

# 可选：如果不需要conda的spug环境，注释掉下面这行（优先用venv）
 conda activate spug


exec gunicorn -b 0.0.0.0:9001 -w 2 --threads 8 --access-logfile - spug.wsgi
