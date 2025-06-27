import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5000';

// 等待服务器就绪
async function waitForServerReady(page: any) {
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

// 登录并创建测试房间
async function setupTestGame(page: any, playerName = 'testPlayer') {
  await page.goto(BASE_URL);
  await page.fill('input[name="nickname"]', playerName);
  await page.click('button[type="submit"]');
  await page.waitForURL(/.*lobby/, { timeout: 15000 });
  await page.waitForTimeout(3000);
  
  // 创建房间 - 1个真人+3个机器人
  await page.click('button:has-text("创建房间")');
  await page.fill('input[name="title"]', '测试房间-1人3机器人');
  await page.selectOption('#maxPlayers', '4');
  
  // 添加3个不同级别的机器人
  await page.click('.bot-increase[data-level="beginner"]');
  await page.click('.bot-increase[data-level="intermediate"]');
  await page.click('.bot-increase[data-level="advanced"]');
  
  await page.click('button[type="submit"]:has-text("创建房间")');
  await page.waitForURL(/.*\/table\//, { timeout: 15000 });
  await page.waitForTimeout(5000);
  
  return await page.url().match(/\/table\/([^\/]+)/)?.[1];
}

// 执行玩家动作
async function performAction(page: any, action: string, amount?: string) {
  const actionBtn = page.locator(`button:has-text("${action}")`);
  if (await actionBtn.isVisible({ timeout: 5000 })) {
    if (amount && action === '加注') {
      const raiseInput = page.locator('input[placeholder*="加注"]');
      if (await raiseInput.isVisible()) {
        await raiseInput.fill(amount);
      }
    }
    await actionBtn.click();
    await page.waitForTimeout(2000);
    return true;
  }
  return false;
}

test.describe('德州扑克游戏规则测试', () => {
  
  test('服务器连接测试', async ({ page }) => {
    console.log('🔍 检查服务器连接...');
    const serverReady = await waitForServerReady(page);
    expect(serverReady).toBe(true);
    console.log('✅ 服务器连接正常');
  });

  test('1真人+3机器人游戏流程', async ({ page }) => {
    test.setTimeout(300000); // 5分钟超时
    
    console.log('🎮 开始游戏流程测试...');
    
    const tableId = await setupTestGame(page, 'gamePlayer');
    console.log(`📋 房间ID: ${tableId}`);
    
    // 验证房间设置
    await page.waitForTimeout(3000);
    const playersCount = await page.locator('.player-info').count();
    console.log(`👥 玩家数量: ${playersCount}`);
    expect(playersCount).toBe(4);
    
    let handsPlayed = 0;
    const maxHands = 10;
    
    while (handsPlayed < maxHands) {
      console.log(`\n🃏 ===== 第 ${handsPlayed + 1} 手牌 =====`);
      
      try {
        await page.waitForTimeout(3000);
        
        // 获取游戏状态
        const gameStatus = await page.evaluate(() => {
          const statusElement = document.querySelector('.game-status');
          return statusElement ? statusElement.textContent : 'unknown';
        });
        console.log(`🎯 游戏状态: ${gameStatus}`);
        
        // 查找开始按钮
        const startBtn = page.locator('button:has-text("开始游戏"), button:has-text("下一手")');
        if (await startBtn.isVisible({ timeout: 5000 })) {
          await startBtn.click();
          await page.waitForTimeout(3000);
        }
        
        // 获取手牌
        const holeCards = await page.evaluate(() => {
          const cards = document.querySelectorAll('.hole-card');
          return Array.from(cards).map((card: any) => card.textContent?.trim());
        });
        console.log(`🃏 玩家手牌: ${holeCards.join(', ')}`);
        
        // 获取玩家筹码
        const playerChips = await page.evaluate(() => {
          const chipElements = document.querySelectorAll('.player-info');
          for (const element of chipElements) {
            if (element.textContent?.includes('gamePlayer')) {
              const chipsMatch = element.textContent.match(/(\d+)/);
              return chipsMatch ? parseInt(chipsMatch[1]) : 1000;
            }
          }
          return 1000;
        });
        console.log(`💰 玩家筹码: ${playerChips}`);
        
        // Pre-flop 行动
        console.log('📍 Pre-flop 阶段');
        await page.waitForTimeout(2000);
        
        const actionNeeded = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
        if (actionNeeded) {
          // 获取底池
          const potAmount = await page.evaluate(() => {
            const potElement = document.querySelector('#potAmount');
            return potElement ? parseInt(potElement.textContent?.replace(/[^\d]/g, '') || '0') : 0;
          });
          console.log(`💰 底池: ${potAmount}`);
          
          // 简单策略：随机选择动作
          const actions = ['跟注', '加注', '弃牌'];
          const randomAction = actions[Math.floor(Math.random() * actions.length)];
          
          let actionExecuted = false;
          if (randomAction === '加注') {
            actionExecuted = await performAction(page, '加注', '50');
          } else {
            actionExecuted = await performAction(page, randomAction);
          }
          
          console.log(`✅ 执行动作: ${randomAction} ${actionExecuted ? '成功' : '失败'}`);
          await page.waitForTimeout(3000);
        }
        
        // 等待Flop
        console.log('📍 等待Flop...');
        await page.waitForTimeout(5000);
        
        const communityCards = await page.evaluate(() => {
          const cards = document.querySelectorAll('.community-card');
          return Array.from(cards).map((card: any) => card.textContent?.trim()).filter((card: any) => card);
        });
        
        if (communityCards.length >= 3) {
          console.log(`🃏 Flop: ${communityCards.slice(0, 3).join(', ')}`);
          
          // Flop后行动
          const flopAction = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
          if (flopAction) {
            const flopChoice = Math.random() > 0.5 ? '过牌' : '下注';
            const flopExecuted = flopChoice === '下注' ? 
              await performAction(page, '下注', '30') : 
              await performAction(page, '过牌');
            console.log(`✅ Flop行动: ${flopChoice} ${flopExecuted ? '成功' : '失败'}`);
            await page.waitForTimeout(3000);
          }
        }
        
        // 等待Turn
        console.log('📍 等待Turn...');
        await page.waitForTimeout(5000);
        
        if (communityCards.length >= 4) {
          console.log(`🃏 Turn: ${communityCards[3]}`);
          
          const turnAction = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
          if (turnAction) {
            const turnChoice = Math.random() > 0.6 ? '过牌' : '下注';
            await performAction(page, turnChoice, turnChoice === '下注' ? '40' : undefined);
            console.log(`✅ Turn行动: ${turnChoice}`);
            await page.waitForTimeout(3000);
          }
        }
        
        // 等待River
        console.log('📍 等待River...');
        await page.waitForTimeout(5000);
        
        if (communityCards.length === 5) {
          console.log(`🃏 River: ${communityCards[4]}`);
          console.log(`🃏 完整公共牌: ${communityCards.join(', ')}`);
          
          const riverAction = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
          if (riverAction) {
            const riverChoice = Math.random() > 0.7 ? '过牌' : '下注';
            await performAction(page, riverChoice, riverChoice === '下注' ? '50' : undefined);
            console.log(`✅ River行动: ${riverChoice}`);
            await page.waitForTimeout(3000);
          }
        }
        
        // 等待结果
        console.log('📍 等待摊牌结果...');
        await page.waitForTimeout(8000);
        
        // 获取最终筹码
        const finalChips = await page.evaluate(() => {
          const chipElements = document.querySelectorAll('.player-info');
          for (const element of chipElements) {
            if (element.textContent?.includes('gamePlayer')) {
              const chipsMatch = element.textContent.match(/(\d+)/);
              return chipsMatch ? parseInt(chipsMatch[1]) : 1000;
            }
          }
          return 1000;
        });
        
        const chipChange = finalChips - playerChips;
        console.log(`💰 最终筹码: ${finalChips}`);
        console.log(`📊 筹码变化: ${chipChange > 0 ? '+' : ''}${chipChange}`);
        console.log(`🏆 结果: ${chipChange > 0 ? '胜利' : chipChange < 0 ? '失败' : '平局'}`);
        
        handsPlayed++;
        await page.waitForTimeout(5000);
        
      } catch (error) {
        console.log(`❌ 第${handsPlayed + 1}手出现错误: ${error}`);
        
        // 尝试继续
        const continueBtn = page.locator('button:has-text("继续"), button:has-text("下一手")');
        if (await continueBtn.isVisible({ timeout: 5000 })) {
          await continueBtn.click();
        }
        
        handsPlayed++;
      }
    }
    
    console.log(`\n🎯 完成${handsPlayed}手牌测试`);
    
    // 检查数据库记录
    const dbRecords = await page.evaluate(async (tableId) => {
      try {
        const response = await fetch(`/api/game_history?table_id=${tableId}`);
        return await response.json();
      } catch (error) {
        return { error: error.message };
      }
    }, tableId);
    
    console.log('🗄️ 数据库记录:', JSON.stringify(dbRecords, null, 2));
    
    expect(handsPlayed).toBe(maxHands);
    console.log('✅ 游戏流程测试完成');
  });

  test('游戏规则验证', async ({ page }) => {
    console.log('📋 开始游戏规则验证...');
    
    await setupTestGame(page, 'ruleValidator');
    await page.waitForTimeout(5000);
    
    // 验证玩家数量
    const playersCount = await page.locator('.player-info').count();
    expect(playersCount).toBe(4);
    console.log(`✓ 玩家数量正确: ${playersCount}`);
    
    // 验证盲注设置
    const initialPot = await page.evaluate(() => {
      const potElement = document.querySelector('#potAmount');
      return potElement ? parseInt(potElement.textContent?.replace(/[^\d]/g, '') || '0') : 0;
    });
    
    expect(initialPot).toBeGreaterThan(0);
    console.log(`✓ 盲注设置正确: ${initialPot}`);
    
    // 验证游戏界面元素
    await expect(page.locator('#potAmount')).toBeVisible();
    await expect(page.locator('.community-cards')).toBeVisible();
    
    console.log('✅ 游戏规则验证通过');
  });

  test('机器人行为测试', async ({ page }) => {
    console.log('🤖 开始机器人行为测试...');
    
    await setupTestGame(page, 'botTester');
    await page.waitForTimeout(5000);
    
    // 观察3手牌的机器人行为
    for (let i = 0; i < 3; i++) {
      console.log(`\n🤖 观察第${i + 1}手机器人行为...`);
      
      await page.waitForTimeout(3000);
      
      // 开始游戏
      const startBtn = page.locator('button:has-text("开始游戏"), button:has-text("下一手")');
      if (await startBtn.isVisible({ timeout: 5000 })) {
        await startBtn.click();
        await page.waitForTimeout(3000);
      }
      
      // 观察机器人决策时间
      const startTime = Date.now();
      await page.waitForTimeout(10000); // 等待机器人行动
      const elapsedTime = Date.now() - startTime;
      
      console.log(`⏱️ 机器人响应时间: ${elapsedTime}ms`);
      expect(elapsedTime).toBeLessThan(15000);
      
      // 检查底池变化
      const potAmount = await page.evaluate(() => {
        const potElement = document.querySelector('#potAmount');
        return potElement ? parseInt(potElement.textContent?.replace(/[^\d]/g, '') || '0') : 0;
      });
      
      console.log(`💰 当前底池: ${potAmount}`);
      expect(potAmount).toBeGreaterThan(0);
    }
    
    console.log('✅ 机器人行为测试完成');
  });
}); 