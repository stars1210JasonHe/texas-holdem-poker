import { test, expect } from '@playwright/test';

// 测试账号信息
const TEST_USER = { nickname: 'test', password: 'test' };

// 测试房间ID（需提前创建或用API获取）
const TEST_TABLE_ID = '';

// 辅助函数：登录并进入大厅
async function loginAndGotoLobby(page) {
  await page.goto('http://localhost:5000/');
  await page.fill('input[name="nickname"]', TEST_USER.nickname);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*lobby/);
}

test.describe('选座功能', () => {
  test('test账号加入房间时可选座并进入', async ({ page }) => {
    await loginAndGotoLobby(page);
    // 假设房间已存在，点击加入房间按钮
    // 这里需根据实际房间列表结构定位
    const joinBtn = await page.locator('button:has-text("加入房间")').first();
    await joinBtn.click();
    // 弹窗出现，选择第一个可用座位
    const seatBtn = await page.locator('.seat-btn:not([disabled])').first();
    await seatBtn.click();
    // 应跳转到牌桌页面
    await expect(page).toHaveURL(/.*\/table\//);
    // 检查页面有"记牌助手"或"胜率计算器"按钮（test账号专属）
    await expect(page.locator('button', { hasText: '胜率计算器' })).toBeVisible();
    await expect(page.locator('button', { hasText: '记牌助手' })).toBeVisible();
  });
}); 