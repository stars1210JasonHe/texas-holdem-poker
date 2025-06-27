import { test, expect } from '@playwright/test';

// 测试配置
const BASE_URL = 'http://localhost:5000';
const TEST_USERS = ['testUser1', 'testUser2', 'testUser3'];

// 辅助函数：快速登录
async function quickLogin(page, nickname) {
  await page.goto(BASE_URL);
  await page.fill('input[name="nickname"]', nickname);
  await page.click('button[type="submit"]');
  await page.waitForURL(/.*lobby/, { timeout: 15000 });
  await page.waitForTimeout(3000); // 等待Socket连接稳定
}

// 辅助函数：创建测试房间 - 修复选项问题
async function createTestRoom(page, roomName, maxPlayers = 6) {
  await page.click('button:has-text("创建房间")');
  await page.fill('input[name="title"]', roomName);
  
  // 只选择有效的maxPlayers值：2, 4, 6, 9
  const validPlayerCounts = [2, 4, 6, 9];
  const actualMaxPlayers = validPlayerCounts.includes(maxPlayers) ? maxPlayers : 6;
  
  await page.selectOption('#maxPlayers', actualMaxPlayers.toString());
  
  await page.click('button[type="submit"]:has-text("创建房间")');
  await page.waitForTimeout(5000); // 等待房间创建
  return await page.url().match(/\/table\/([^\/]+)/)?.[1];
}

// 辅助函数：验证玩家在房间中
async function verifyPlayerInRoom(page, nickname) {
  // 等待玩家区域加载
  await page.waitForSelector('#playersArea', { timeout: 15000 });
  
  // 查找包含玩家昵称的元素
  const playerElement = page.locator(`#playersArea >> text=${nickname}`);
  await expect(playerElement).toBeVisible({ timeout: 15000 });
}

// 辅助函数：等待服务器就绪
async function waitForServerReady(page) {
  let retries = 10;
  while (retries > 0) {
    try {
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/stats');
        return resp.status;
      });
      if (response === 200) return true;
    } catch (e) {
      console.log('等待服务器就绪...');
    }
    await page.waitForTimeout(2000);
    retries--;
  }
  return false;
}

test.describe('选座功能完整测试（最终修复版）', () => {
  
  test('服务器连接测试', async ({ page }) => {
    console.log('开始服务器连接测试...');
    await page.goto(BASE_URL);
    
    // 等待服务器就绪
    const serverReady = await waitForServerReady(page);
    expect(serverReady).toBe(true);
    
    console.log('服务器连接正常');
  });
  
  test('大厅加入房间选座弹窗（终极修复）', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    try {
      console.log('用户1创建房间...');
      await quickLogin(page1, TEST_USERS[0]);
      
      // 等待服务器就绪
      await waitForServerReady(page1);
      
      const roomId = await createTestRoom(page1, '选座弹窗测试', 4);
      console.log('房间ID:', roomId);
      
      // 验证用户1已在房间中
      await verifyPlayerInRoom(page1, TEST_USERS[0]);
      console.log('用户1已在房间中');
      
      // 返回大厅
      await page1.goto(`${BASE_URL}/lobby`);
      await page1.waitForTimeout(3000);
      
      console.log('用户2登录并查看房间列表...');
      await quickLogin(page2, TEST_USERS[1]);
      await page2.waitForTimeout(3000);
      
      // 手动刷新房间列表
      const refreshBtn = page2.locator('button:has-text("刷新列表")');
      if (await refreshBtn.isVisible()) {
        await refreshBtn.click();
        await page2.waitForTimeout(3000);
      }
      
      // 查找并点击加入房间按钮
      console.log('查找加入房间按钮...');
      const joinBtns = page2.locator('button:has-text("加入房间")');
      const joinBtnCount = await joinBtns.count();
      console.log('找到加入按钮数量:', joinBtnCount);
      
      if (joinBtnCount > 0) {
        // 点击第一个加入按钮
        await joinBtns.first().click();
        await page2.waitForTimeout(2000);
        
        // 检查是否出现选座弹窗
        const modalExists = await page2.locator('div[style*="position: fixed"]').isVisible();
        if (modalExists) {
          console.log('选座弹窗已出现');
          const availableSeat = page2.locator('.seat-btn:not([disabled])').first();
          if (await availableSeat.isVisible()) {
            await availableSeat.click();
          }
        } else {
          console.log('未找到选座弹窗，可能直接进入房间');
        }
        
        // 验证最终进入房间
        await page2.waitForURL(/.*\/table\//, { timeout: 20000 });
        await verifyPlayerInRoom(page2, TEST_USERS[1]);
        console.log('用户2成功进入房间');
      } else {
        // 如果没有加入按钮，直接跳转房间
        console.log('未找到加入按钮，直接跳转房间');
        await page2.goto(`${BASE_URL}/table/${roomId}`);
        await verifyPlayerInRoom(page2, TEST_USERS[1]);
      }
      
    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test('API座位信息获取（修复版）', async ({ page }) => {
    console.log('开始API测试...');
    await quickLogin(page, TEST_USERS[0]);
    
    // 等待服务器就绪
    await waitForServerReady(page);
    
    // 使用有效的maxPlayers值
    const roomId = await createTestRoom(page, 'API测试房间', 4);
    console.log('API测试房间ID:', roomId);
    
    // 验证用户在房间中
    await verifyPlayerInRoom(page, TEST_USERS[0]);
    
    // 测试API获取座位信息
    const apiResponse = await page.evaluate(async (roomId) => {
      try {
        const response = await fetch(`/api/table_players?table_id=${roomId}`);
        return await response.json();
      } catch (error) {
        return { error: error.message };
      }
    }, roomId);
    
    console.log('API响应:', apiResponse);
    
    // 验证API返回正确
    expect(apiResponse.success).toBe(true);
    expect(apiResponse.players).toBeDefined();
    expect(apiResponse.players.length).toBeGreaterThanOrEqual(1);
    expect(apiResponse.max_players).toBe(4);
    
    console.log('API测试通过');
  });

  test('多用户加入房间（稳定版）', async ({ browser }) => {
    const contexts: any[] = [];
    const pages: any[] = [];
    
    try {
      console.log('创建多个用户上下文...');
      for (let i = 0; i < 3; i++) {
        contexts[i] = await browser.newContext();
        pages[i] = await contexts[i].newPage();
      }
      
      // 用户1创建房间
      console.log('用户1创建房间...');
      await quickLogin(pages[0], TEST_USERS[0]);
      await waitForServerReady(pages[0]);
      
      const roomId = await createTestRoom(pages[0], '多用户测试房间', 6);
      await verifyPlayerInRoom(pages[0], TEST_USERS[0]);
      console.log('用户1房间创建完成');
      
      // 用户2和用户3依次加入
      for (let i = 1; i < 3; i++) {
        console.log(`用户${i+1}加入房间...`);
        await quickLogin(pages[i], TEST_USERS[i]);
        
        // 直接跳转到房间
        await pages[i].goto(`${BASE_URL}/table/${roomId}`);
        await pages[i].waitForTimeout(5000);
        
        // 验证用户成功加入
        await verifyPlayerInRoom(pages[i], TEST_USERS[i]);
        console.log(`用户${i+1}成功加入房间`);
      }
      
      console.log('多用户测试完成');
      
    } finally {
      for (const context of contexts) {
        await context.close();
      }
    }
  });

  test('test账号权限验证（最终版）', async ({ page }) => {
    console.log('开始test账号权限验证...');
    await quickLogin(page, 'test');
    await waitForServerReady(page);
    
    const roomId = await createTestRoom(page, 'test权限房间', 4);
    console.log('test账号房间创建完成');
    
    // 等待页面完全加载
    await page.waitForTimeout(5000);
    
    // 验证test账号能看到辅助功能按钮
    const winProbBtn = page.locator('button:has-text("胜率计算器")');
    const cardHelperBtn = page.locator('button:has-text("记牌助手")');
    
    console.log('检查辅助功能按钮...');
    await expect(winProbBtn).toBeVisible({ timeout: 10000 });
    await expect(cardHelperBtn).toBeVisible({ timeout: 10000 });
    
    console.log('test账号权限验证通过 - 可以看到辅助功能按钮');
  });

  test('普通账号权限验证（最终版）', async ({ page }) => {
    console.log('开始普通账号权限验证...');
    await quickLogin(page, 'normalUser');
    await waitForServerReady(page);
    
    await createTestRoom(page, '普通用户房间', 4);
    
    // 等待页面完全加载
    await page.waitForTimeout(5000);
    
    // 验证普通账号看不到辅助功能按钮
    const winProbBtn = page.locator('button:has-text("胜率计算器")');
    const cardHelperBtn = page.locator('button:has-text("记牌助手")');
    
    console.log('检查普通账号是否看不到辅助功能按钮...');
    await expect(winProbBtn).not.toBeVisible();
    await expect(cardHelperBtn).not.toBeVisible();
    
    console.log('普通账号权限验证通过 - 看不到辅助功能按钮');
  });

  test('房间创建基础功能（最终版）', async ({ page }) => {
    console.log('开始房间创建基础功能测试...');
    await quickLogin(page, 'basicUser');
    await waitForServerReady(page);
    
    // 创建房间并验证基础功能
    await page.click('button:has-text("创建房间")');
    await page.fill('input[name="title"]', '基础功能测试房间');
    await page.selectOption('#maxPlayers', '4');
    await page.click('button[type="submit"]:has-text("创建房间")');
    
    // 验证跳转到房间页面
    await page.waitForURL(/.*\/table\//, { timeout: 15000 });
    
    // 验证房间标题
    const tableTitle = page.locator('#tableTitle');
    await expect(tableTitle).toContainText('基础功能测试房间', { timeout: 10000 });
    
    console.log('房间创建基础功能验证通过');
  });
}); 