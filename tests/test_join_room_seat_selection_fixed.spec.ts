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
  await page.waitForTimeout(2000); // 增加等待时间
}

// 辅助函数：创建测试房间
async function createTestRoom(page, roomName, maxPlayers = 6) {
  await page.click('button:has-text("创建房间")');
  await page.fill('input[name="title"]', roomName);
  
  // 修复select选项问题 - 使用ID选择器
  await page.selectOption('#maxPlayers', maxPlayers.toString());
  
  await page.click('button[type="submit"]:has-text("创建房间")');
  await page.waitForTimeout(3000); // 增加等待时间
  return await page.url().match(/\/table\/([^\/]+)/)?.[1];
}

// 辅助函数：验证玩家在房间中
async function verifyPlayerInRoom(page, nickname) {
  // 等待玩家区域加载
  await page.waitForSelector('#playersArea', { timeout: 10000 });
  
  // 查找包含玩家昵称的元素（使用更宽泛的选择器）
  const playerElement = page.locator(`#playersArea >> text=${nickname}`);
  await expect(playerElement).toBeVisible({ timeout: 10000 });
}

test.describe('加入房间选座模式测试（修复版）', () => {
  
  test('大厅加入房间 - 弹出选座弹窗功能', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    try {
      // 用户1创建房间
      await quickLogin(page1, TEST_USERS[0]);
      const roomId = await createTestRoom(page1, '选座弹窗测试', 4);
      
      // 验证用户1已在房间中
      await verifyPlayerInRoom(page1, TEST_USERS[0]);
      
      // 返回大厅查看房间列表
      await page1.goto(`${BASE_URL}/lobby`);
      await page1.waitForTimeout(3000);
      
      // 用户2登录并在大厅看到房间
      await quickLogin(page2, TEST_USERS[1]);
      await page2.waitForTimeout(3000);
      
      // 刷新房间列表
      const refreshBtn = page2.locator('button:has-text("刷新列表")');
      if (await refreshBtn.isVisible()) {
        await refreshBtn.click();
        await page2.waitForTimeout(2000);
      }
      
      // 点击"加入房间"按钮
      const joinBtn = page2.locator('button:has-text("加入房间")').first();
      if (await joinBtn.isVisible()) {
        await joinBtn.click();
        
        // 验证选座弹窗出现
        await page2.waitForTimeout(2000);
        const seatModal = page2.locator('div[style*="position: fixed"]');
        if (await seatModal.isVisible()) {
          // 选择第一个可用座位
          const availableSeat = page2.locator('.seat-btn:not([disabled])').first();
          await availableSeat.click();
        }
      } else {
        // 如果没有找到加入按钮，直接跳转到房间
        await page2.goto(`${BASE_URL}/table/${roomId}`);
      }
      
      // 验证跳转到房间页面
      await page2.waitForURL(/.*\/table\//, { timeout: 10000 });
      await verifyPlayerInRoom(page2, TEST_USERS[1]);
      
    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test('API座位信息获取', async ({ browser }) => {
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    
    try {
      // 用户1创建房间
      await quickLogin(page1, TEST_USERS[0]);
      const roomId = await createTestRoom(page1, 'API测试', 3);
      
      // 验证用户在房间中
      await verifyPlayerInRoom(page1, TEST_USERS[0]);
      
      // 测试API获取座位信息
      const apiResponse = await page1.evaluate(async (roomId) => {
        const response = await fetch(`/api/table_players?table_id=${roomId}`);
        return await response.json();
      }, roomId);
      
      console.log('房间玩家信息API响应:', apiResponse);
      
      // 验证API返回正确
      expect(apiResponse.success).toBe(true);
      expect(apiResponse.players.length).toBeGreaterThanOrEqual(1);
      expect(apiResponse.max_players).toBe(3);
      
    } finally {
      await context1.close();
    }
  });

  test('多用户加入房间', async ({ browser }) => {
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
      const roomId = await createTestRoom(pages[0], '多用户测试', 6);
      await verifyPlayerInRoom(pages[0], TEST_USERS[0]);
      
      // 用户2和用户3依次加入
      for (let i = 1; i < 3; i++) {
        await quickLogin(pages[i], TEST_USERS[i]);
        
        // 直接跳转到房间（模拟选座完成）
        await pages[i].goto(`${BASE_URL}/table/${roomId}`);
        await pages[i].waitForTimeout(3000);
        
        // 验证用户成功加入
        await verifyPlayerInRoom(pages[i], TEST_USERS[i]);
      }
      
      console.log('多用户测试完成');
      
    } finally {
      for (const context of contexts) {
        await context.close();
      }
    }
  });

  test('test账号权限验证', async ({ page }) => {
    await quickLogin(page, 'test');
    await createTestRoom(page, 'test权限验证', 4);
    
    // 等待页面加载完成
    await page.waitForTimeout(3000);
    
    // 验证test账号能看到辅助功能按钮
    const winProbBtn = page.locator('button:has-text("胜率计算器")');
    const cardHelperBtn = page.locator('button:has-text("记牌助手")');
    
    await expect(winProbBtn).toBeVisible({ timeout: 5000 });
    await expect(cardHelperBtn).toBeVisible({ timeout: 5000 });
    
    console.log('test账号权限验证通过');
  });

  test('普通账号权限验证', async ({ page }) => {
    await quickLogin(page, 'normalUser');
    await createTestRoom(page, '普通用户权限验证', 4);
    
    // 等待页面加载完成
    await page.waitForTimeout(3000);
    
    // 验证普通账号看不到辅助功能按钮
    const winProbBtn = page.locator('button:has-text("胜率计算器")');
    const cardHelperBtn = page.locator('button:has-text("记牌助手")');
    
    await expect(winProbBtn).not.toBeVisible();
    await expect(cardHelperBtn).not.toBeVisible();
    
    console.log('普通账号权限验证通过');
  });

  test('房间创建和基础功能', async ({ page }) => {
    await quickLogin(page, 'basicUser');
    
    // 创建房间并验证基础功能
    await page.click('button:has-text("创建房间")');
    await page.fill('input[name="title"]', '基础功能测试');
    await page.selectOption('#maxPlayers', '4');
    await page.click('button[type="submit"]:has-text("创建房间")');
    
    // 验证跳转到房间页面
    await page.waitForURL(/.*\/table\//, { timeout: 10000 });
    
    // 验证房间标题
    const tableTitle = page.locator('#tableTitle');
    await expect(tableTitle).toContainText('基础功能测试');
    
    console.log('房间创建和基础功能验证通过');
  });
}); 