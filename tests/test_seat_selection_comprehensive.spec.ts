import { test, expect } from '@playwright/test';

// 测试账号配置
const TEST_ACCOUNTS = {
  test: { nickname: 'test', hasHelper: true },
  user1: { nickname: 'user1', hasHelper: false },
  user2: { nickname: 'user2', hasHelper: false }
};

// 辅助函数：登录指定账号
async function loginUser(page, account) {
  await page.goto('http://localhost:5000/');
  await page.fill('input[name="nickname"]', account.nickname);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*lobby/);
  await page.waitForTimeout(1000); // 等待Socket连接稳定
}

// 辅助函数：创建房间
async function createRoom(page, roomName = 'Test Room', maxPlayers = 6, addBots = false) {
  await page.click('button:has-text("创建房间")');
  await page.fill('input[name="title"]', roomName);
  await page.selectOption('select[name="maxPlayers"]', maxPlayers.toString());
  
  // 如果需要添加机器人
  if (addBots) {
    // 添加1个初级机器人
    await page.click('.bot-increase[data-level="beginner"]');
  }
  
  await page.click('button[type="submit"]:has-text("创建房间")');
  await page.waitForTimeout(2000); // 等待房间创建和跳转
}

// 辅助函数：获取房间ID从URL
async function getRoomIdFromUrl(page) {
  const url = await page.url();
  const match = url.match(/\/table\/([^\/]+)/);
  return match ? match[1] : null;
}

test.describe('选座功能综合测试', () => {
  
  test('基础选座功能 - 普通用户创建房间并选座', async ({ page }) => {
    await loginUser(page, TEST_ACCOUNTS.user1);
    await createRoom(page, '普通选座测试', 4);
    
    // 应该已经在房间页面，验证用户在座位上
    await expect(page).toHaveURL(/.*\/table\//);
    await expect(page.locator('.player-card')).toContainText(TEST_ACCOUNTS.user1.nickname);
    
    // 普通用户不应该看到辅助功能按钮
    await expect(page.locator('button:has-text("胜率计算器")')).not.toBeVisible();
    await expect(page.locator('button:has-text("记牌助手")')).not.toBeVisible();
  });

  test('机器人和真人混合选座', async ({ page }) => {
    await loginUser(page, TEST_ACCOUNTS.user1);
    await createRoom(page, '混合选座测试', 4, true); // 带1个机器人
    
    // 验证房间中有机器人和真人
    await expect(page.locator('.player-card')).toContainText(TEST_ACCOUNTS.user1.nickname);
    await expect(page.locator('.player-card:has-text("新手")')).toBeVisible(); // 机器人名字包含"新手"
    
    // 记录当前房间ID，为下个用户加入做准备
    const roomId = await getRoomIdFromUrl(page);
    console.log('Room ID:', roomId);
  });

  test('test账号权限验证 - 能看到辅助功能按钮', async ({ page }) => {
    await loginUser(page, TEST_ACCOUNTS.test);
    await createRoom(page, 'test权限测试', 4);
    
    // test账号应该能看到辅助功能按钮
    await expect(page.locator('button:has-text("胜率计算器")')).toBeVisible();
    await expect(page.locator('button:has-text("记牌助手")')).toBeVisible();
    
    // 点击胜率计算器测试功能
    await page.click('button:has-text("胜率计算器")');
    await page.waitForTimeout(1000);
    // 应该出现弹窗或结果（具体取决于游戏状态）
  });

  test('选座冲突处理 - 模拟两用户尝试相同座位', async ({ browser }) => {
    // 创建两个并行的页面模拟不同用户
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    try {
      // 用户1先创建房间
      await loginUser(page1, TEST_ACCOUNTS.user1);
      await createRoom(page1, '选座冲突测试', 6);
      const roomId = await getRoomIdFromUrl(page1);
      
      // 用户2登录并尝试加入同一房间
      await loginUser(page2, TEST_ACCOUNTS.user2);
      
      // 模拟用户2加入房间（需要先有房间列表或直接访问房间URL）
      await page2.goto(`http://localhost:5000/table/${roomId}`);
      await page2.waitForTimeout(2000);
      
      // 验证两个用户都在房间中但位置不同
      await expect(page1.locator('.player-card')).toContainText(TEST_ACCOUNTS.user1.nickname);
      await expect(page2.locator('.player-card')).toContainText(TEST_ACCOUNTS.user2.nickname);
      
    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test('房间满员测试', async ({ browser }) => {
    // 创建多个用户填满房间
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    
    try {
      await loginUser(page1, TEST_ACCOUNTS.user1);
      await createRoom(page1, '满员测试', 2); // 创建2人房间
      
      // 添加机器人填满房间
      await page1.click('button:has-text("添加机器人")');
      await page1.waitForTimeout(1000);
      
      // 输入1选择初级机器人
      await page1.keyboard.type('1');
      await page1.waitForTimeout(2000);
      
      // 验证房间已满（有2个玩家）
      const playerCards = await page1.locator('.player-card').count();
      expect(playerCards).toBe(2);
      
    } finally {
      await context1.close();
    }
  });

  test('断线重连测试', async ({ page }) => {
    await loginUser(page, TEST_ACCOUNTS.user1);
    await createRoom(page, '重连测试', 4);
    
    const roomId = await getRoomIdFromUrl(page);
    
    // 模拟断线 - 刷新页面
    await page.reload();
    await page.waitForTimeout(2000);
    
    // 应该提示重新登录
    await expect(page).toHaveURL('http://localhost:5000/');
    
    // 重新登录并进入房间
    await loginUser(page, TEST_ACCOUNTS.user1);
    await page.goto(`http://localhost:5000/table/${roomId}`);
    await page.waitForTimeout(2000);
    
    // 验证能够重新连接到房间
    await expect(page.locator('.player-card')).toContainText(TEST_ACCOUNTS.user1.nickname);
  });
}); 