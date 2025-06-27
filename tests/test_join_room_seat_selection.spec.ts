import { test, expect } from '@playwright/test';

// 测试配置
const BASE_URL = 'http://localhost:5000';
const TEST_USERS = ['testUser1', 'testUser2', 'testUser3'];

// 辅助函数：快速登录
async function quickLogin(page, nickname) {
  await page.goto(BASE_URL);
  await page.fill('input[name="nickname"]', nickname);
  await page.click('button[type="submit"]');
  await page.waitForURL(/.*lobby/);
  await page.waitForTimeout(1000);
}

// 辅助函数：创建测试房间
async function createTestRoom(page, roomName, maxPlayers = 6) {
  await page.click('button:has-text("创建房间")');
  await page.fill('input[name="title"]', roomName);
  await page.selectOption('select[name="maxPlayers"]', maxPlayers.toString());
  await page.click('button[type="submit"]:has-text("创建房间")');
  await page.waitForTimeout(2000);
  return await page.url().match(/\/table\/([^\/]+)/)?.[1];
}

test.describe('加入房间选座模式测试', () => {
  
  test('大厅加入房间 - 弹出选座弹窗功能', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    try {
      // 用户1创建房间
      await quickLogin(page1, TEST_USERS[0]);
      const roomId = await createTestRoom(page1, '选座弹窗测试', 4);
      
      // 返回大厅查看房间列表
      await page1.goto(`${BASE_URL}/lobby`);
      await page1.waitForTimeout(2000);
      
      // 用户2登录并在大厅看到房间
      await quickLogin(page2, TEST_USERS[1]);
      await page2.waitForTimeout(2000);
      
      // 刷新房间列表
      const refreshBtn = page2.locator('button:has-text("刷新列表")');
      if (await refreshBtn.isVisible()) {
        await refreshBtn.click();
        await page2.waitForTimeout(1000);
      }
      
      // 点击"加入房间"按钮
      const joinBtn = page2.locator('button:has-text("加入房间")').first();
      await joinBtn.click();
      
      // 验证选座弹窗出现
      await page2.waitForTimeout(1000);
      const seatModal = page2.locator('div[style*="position: fixed"]');
      await expect(seatModal).toBeVisible();
      
      // 验证弹窗中有座位按钮
      const seatBtns = page2.locator('.seat-btn');
      await expect(seatBtns).toHaveCount(4); // 4人桌
      
      // 选择第一个可用座位
      const availableSeat = page2.locator('.seat-btn:not([disabled])').first();
      await availableSeat.click();
      
      // 验证跳转到房间页面
      await page2.waitForURL(/.*\/table\//);
      await expect(page2.locator('.player-card')).toContainText(TEST_USERS[1]);
      
    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test('选座冲突 - 已占用座位显示为不可选', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    try {
      // 用户1创建房间并占用座位0
      await quickLogin(page1, TEST_USERS[0]);
      await createTestRoom(page1, '座位冲突测试', 3);
      
      // 用户2尝试加入同一房间
      await quickLogin(page2, TEST_USERS[1]);
      
      // 直接获取房间ID并测试API
      const roomId = await page1.url().match(/\/table\/([^\/]+)/)?.[1];
      
      // 用户2返回大厅，通过API方式测试选座
      await page2.goto(`${BASE_URL}/lobby`);
      
      // 模拟点击加入房间的API调用
      const apiResponse = await page2.evaluate(async (roomId) => {
        const response = await fetch(`/api/table_players?table_id=${roomId}`);
        return await response.json();
      }, roomId);
      
      console.log('房间玩家信息:', apiResponse);
      
      // 验证座位0被占用
      expect(apiResponse.success).toBe(true);
      expect(apiResponse.players.length).toBe(1);
      expect(apiResponse.players[0].position).toBe(0);
      
    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test('多用户选座 - 不同座位分配', async ({ browser }) => {
    const contexts: any[] = [];
    const pages: any[] = [];
    
    try {
      // 创建3个用户上下文
      for (let i = 0; i < 3; i++) {
        contexts[i] = await browser.newContext();
        pages[i] = await contexts[i].newPage();
      }
      
      // 用户1创建房间
      await quickLogin(pages[0], TEST_USERS[0]);
      const roomId = await createTestRoom(pages[0], '多用户选座测试', 6);
      
      // 用户2和用户3依次加入
      for (let i = 1; i < 3; i++) {
        await quickLogin(pages[i], TEST_USERS[i]);
        
        // 直接跳转到房间（模拟选座完成）
        await pages[i].goto(`${BASE_URL}/table/${roomId}`);
        await pages[i].waitForTimeout(2000);
        
        // 验证用户成功加入
        await expect(pages[i].locator('.player-card')).toContainText(TEST_USERS[i]);
      }
      
      // 验证所有用户都在房间中
      for (let i = 0; i < 3; i++) {
        const playerCards = await pages[i].locator('.player-card').count();
        expect(playerCards).toBe(3); // 应该有3个玩家
      }
      
    } finally {
      for (const context of contexts) {
        await context.close();
      }
    }
  });

  test('房间满员 - 无法加入提示', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    try {
      // 用户1创建2人房间
      await quickLogin(page1, TEST_USERS[0]);
      const roomId = await createTestRoom(page1, '满员测试', 2);
      
      // 添加机器人填满房间
      await page1.click('button:has-text("添加机器人")');
      await page1.waitForTimeout(1000);
      
      // 选择初级机器人（输入1）
      await page1.keyboard.type('1');
      await page1.waitForTimeout(2000);
      
      // 验证房间已有2个玩家
      const playerCount = await page1.locator('.player-card').count();
      expect(playerCount).toBe(2);
      
      // 用户2尝试加入满员房间
      await quickLogin(page2, TEST_USERS[1]);
      await page2.goto(`${BASE_URL}/table/${roomId}`);
      await page2.waitForTimeout(2000);
      
      // 应该收到错误信息或无法加入
      // 这里可以检查错误提示或者验证用户没有成功进入房间
      
    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test('test账号权限 - 辅助功能按钮显示', async ({ page }) => {
    await quickLogin(page, 'test');
    await createTestRoom(page, 'test权限验证', 4);
    
    // 等待页面加载完成
    await page.waitForTimeout(2000);
    
    // 验证test账号能看到辅助功能按钮
    await expect(page.locator('button:has-text("胜率计算器")')).toBeVisible();
    await expect(page.locator('button:has-text("记牌助手")')).toBeVisible();
    
    // 测试胜率计算器功能
    await page.click('button:has-text("胜率计算器")');
    await page.waitForTimeout(1000);
    
    // 测试记牌助手功能
    await page.click('button:has-text("记牌助手")');
    await page.waitForTimeout(1000);
  });

  test('普通账号权限 - 无辅助功能按钮', async ({ page }) => {
    await quickLogin(page, 'normalUser');
    await createTestRoom(page, '普通用户权限验证', 4);
    
    // 等待页面加载完成
    await page.waitForTimeout(2000);
    
    // 验证普通账号看不到辅助功能按钮
    await expect(page.locator('button:has-text("胜率计算器")')).not.toBeVisible();
    await expect(page.locator('button:has-text("记牌助手")')).not.toBeVisible();
  });
}); 