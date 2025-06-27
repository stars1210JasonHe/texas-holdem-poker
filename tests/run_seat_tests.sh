#!/bin/bash

echo "🚀 开始选座功能测试..."

# 检查后端服务是否运行
echo "📡 检查后端服务状态..."
if ! curl -s http://localhost:5000 > /dev/null; then
    echo "❌ 后端服务未启动，请先运行: python app.py"
    exit 1
fi

echo "✅ 后端服务运行正常"

# 运行基础选座测试
echo "🎯 运行基础选座功能测试..."
npx playwright test tests/test_seat_selection.spec.ts --headed

# 运行详细的选座模式测试
echo "🎯 运行加入房间选座模式测试..."
npx playwright test tests/test_join_room_seat_selection.spec.ts --headed

# 运行综合测试
echo "🎯 运行选座功能综合测试..."
npx playwright test tests/test_seat_selection_comprehensive.spec.ts --headed

echo "🎉 所有选座功能测试完成！" 