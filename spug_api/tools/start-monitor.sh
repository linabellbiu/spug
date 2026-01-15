#!/bin/bash
# Copyright: (c) OpenSpug Organization. https://github.com/openspug/spug
# Copyright: (c) <spug.dev@gmail.com>
# Released under the AGPL-3.0 License.
# start monitor service

# 修复1：初始化conda环境（解决conda activate报错）
source /root/miniconda3/etc/profile.d/conda.sh  # 替换为你的conda安装路径，默认是这个
# 如果不知道conda路径，先执行：find / -name "conda.sh" 找到后替换

# 修复2：切换到脚本所在的上级目录（确保能找到spug模块）
cd $(dirname $0)/../  # 切换到spug_api根目录

# 可选：如果不需要conda的spug环境，注释掉下面这行（优先用venv）
conda activate spug

if command -v python3 &> /dev/null; then
  PYTHON=python3
else
  PYTHON=python
fi

exec python manage.py runmonitor
