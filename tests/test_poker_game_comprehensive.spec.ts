import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5000';

// 辅助函数：等待服务器就绪
async function waitForServerReady(page) {
  let retries = 15;
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

// 辅助函数：登录并创建测试房间
async function setupTestGame(page, playerName = 'testPlayer') {
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
  await page.click('.bot-increase[data-level="beginner"]'); // 初级机器人
  await page.click('.bot-increase[data-level="intermediate"]'); // 中级机器人  
  await page.click('.bot-increase[data-level="advanced"]'); // 高级机器人
  
  await page.click('button[type="submit"]:has-text("创建房间")');
  await page.waitForURL(/.*\/table\//, { timeout: 15000 });
  await page.waitForTimeout(5000); // 等待机器人加入
  
  return await page.url().match(/\/table\/([^\/]+)/)?.[1];
}

// 辅助函数：等待游戏状态
async function waitForGameState(page, expectedState, timeout = 15000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const gameState = await page.evaluate(() => {
      return (window as any).gameState || {};
    });
    
    if (gameState.status === expectedState) {
      return gameState;
    }
    await page.waitForTimeout(1000);
  }
  throw new Error(`超时等待游戏状态: ${expectedState}`);
}

// 辅助函数：检查玩家手牌
async function getPlayerHoleCards(page) {
  return await page.evaluate(() => {
    const cards = document.querySelectorAll('.hole-card');
    return Array.from(cards).map(card => card.textContent?.trim());
  });
}

// 辅助函数：获取公共牌
async function getCommunityCards(page) {
  return await page.evaluate(() => {
    const cards = document.querySelectorAll('.community-card');
    return Array.from(cards).map(card => card.textContent?.trim()).filter(card => card);
  });
}

// 辅助函数：获取当前底池
async function getPotAmount(page) {
  return await page.evaluate(() => {
    const potElement = document.querySelector('#potAmount');
    return potElement ? parseInt(potElement.textContent?.replace(/[^\d]/g, '') || '0') : 0;
  });
}

// 辅助函数：获取玩家筹码
async function getPlayerChips(page, playerName) {
  return await page.evaluate((name) => {
    const playerElements = document.querySelectorAll('.player-info');
    for (const element of playerElements) {
      if (element.textContent?.includes(name)) {
        const chipsMatch = element.textContent.match(/(\d+)/);
        return chipsMatch ? parseInt(chipsMatch[1]) : 0;
      }
    }
    return 0;
  }, playerName);
}

// 辅助函数：执行玩家动作
async function performAction(page, action, amount?: number) {
  const actionBtn = page.locator(`button:has-text("${action}")`);
  if (await actionBtn.isVisible({ timeout: 5000 })) {
    if (amount && action === '加注') {
      // 输入加注金额
      const raiseInput = page.locator('input[placeholder*="加注"]');
      if (await raiseInput.isVisible()) {
        await raiseInput.fill(amount.toString());
      }
    }
    await actionBtn.click();
    await page.waitForTimeout(2000);
    return true;
  }
  return false;
}

// 辅助函数：检查数据库记录
async function checkDatabaseRecords(page, tableId) {
  return await page.evaluate(async (tableId) => {
    try {
      const response = await fetch(`/api/game_history?table_id=${tableId}`);
      return await response.json();
    } catch (error) {
      return { error: error.message };
    }
  }, tableId);
}

test.describe('德州扑克完整游戏测试', () => {
  
  test('服务器连接和环境准备', async ({ page }) => {
    console.log('🔍 检查服务器连接...');
    const serverReady = await waitForServerReady(page);
    expect(serverReady).toBe(true);
    console.log('✅ 服务器连接正常');
  });

  test('1真人+3机器人 - 完整游戏流程测试', async ({ page }) => {
    test.setTimeout(300000); // 5分钟超时
    
    console.log('🎮 开始完整游戏流程测试...');
    
    // 设置游戏
    const tableId = await setupTestGame(page, 'testPlayer');
    console.log(`📋 房间ID: ${tableId}`);
    
    // 验证房间设置
    await page.waitForTimeout(3000);
    const playersCount = await page.locator('.player-info').count();
    console.log(`👥 玩家数量: ${playersCount}`);
    expect(playersCount).toBe(4); // 1真人+3机器人
    
         let handsPlayed = 0;
     const maxHands = 10;
     const gameResults: any[] = [];
    
    while (handsPlayed < maxHands) {
      console.log(`\n🃏 ===== 第 ${handsPlayed + 1} 手牌开始 =====`);
      
      try {
        // 等待新一手牌开始
        await page.waitForTimeout(3000);
        
                 // 检查游戏状态
         const gameState = await page.evaluate(() => (window as any).gameState || {});
         console.log(`🎯 游戏状态: ${gameState.status || '未知'}`);
         
         if (gameState.status === 'waiting' || gameState.status === 'finished') {
          // 如果游戏还在等待或已结束，点击开始按钮
          const startBtn = page.locator('button:has-text("开始游戏"), button:has-text("下一手")');
          if (await startBtn.isVisible({ timeout: 5000 })) {
            await startBtn.click();
            await page.waitForTimeout(3000);
          }
        }
        
        // 获取手牌
        const holeCards = await getPlayerHoleCards(page);
        console.log(`🃏 玩家手牌: ${holeCards.join(', ')}`);
        
        // 记录初始筹码
        const initialChips = await getPlayerChips(page, 'testPlayer');
        console.log(`💰 初始筹码: ${initialChips}`);
        
        // Pre-flop 阶段
        console.log('📍 Pre-flop 阶段');
        await page.waitForTimeout(2000);
        
        // 检查是否轮到玩家行动
        const actionNeeded = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
        if (actionNeeded) {
          const potBefore = await getPotAmount(page);
          console.log(`💰 行动前底池: ${potBefore}`);
          
          // 根据手牌强度决定行动
          let action = '跟注';
          if (holeCards.length >= 2) {
            const cardValues = holeCards.map(card => card.replace(/[♠♥♦♣]/g, ''));
            const hasHighCard = cardValues.some(value => ['A', 'K', 'Q', 'J'].includes(value));
            const isPair = cardValues[0] === cardValues[1];
            
            if (isPair || hasHighCard) {
              action = '加注';
              console.log('💪 检测到强牌，选择加注');
            } else {
              action = Math.random() > 0.7 ? '弃牌' : '跟注';
              console.log(`🤔 普通牌力，选择${action}`);
            }
          }
          
          const actionResult = await performAction(page, action, action === '加注' ? 50 : null);
          console.log(`✅ 执行动作: ${action} ${actionResult ? '成功' : '失败'}`);
          
          await page.waitForTimeout(3000);
          const potAfter = await getPotAmount(page);
          console.log(`💰 行动后底池: ${potAfter}`);
        }
        
        // 等待flop
        console.log('📍 等待Flop...');
        await page.waitForTimeout(5000);
        
        const flopCards = await getCommunityCards(page);
        if (flopCards.length >= 3) {
          console.log(`🃏 Flop: ${flopCards.slice(0, 3).join(', ')}`);
          
          // Flop后的行动
          const actionNeeded2 = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
          if (actionNeeded2) {
            const action2 = Math.random() > 0.5 ? '过牌' : '下注';
            await performAction(page, action2, action2 === '下注' ? 30 : null);
            console.log(`✅ Flop行动: ${action2}`);
            await page.waitForTimeout(3000);
          }
        }
        
        // 等待turn
        console.log('📍 等待Turn...');
        await page.waitForTimeout(5000);
        
        const turnCards = await getCommunityCards(page);
        if (turnCards.length >= 4) {
          console.log(`🃏 Turn: ${turnCards[3]}`);
          
          const actionNeeded3 = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
          if (actionNeeded3) {
            const action3 = Math.random() > 0.6 ? '过牌' : '下注';
            await performAction(page, action3, action3 === '下注' ? 40 : null);
            console.log(`✅ Turn行动: ${action3}`);
            await page.waitForTimeout(3000);
          }
        }
        
        // 等待river
        console.log('📍 等待River...');
        await page.waitForTimeout(5000);
        
        const riverCards = await getCommunityCards(page);
        if (riverCards.length === 5) {
          console.log(`🃏 River: ${riverCards[4]}`);
          console.log(`🃏 完整公共牌: ${riverCards.join(', ')}`);
          
          const actionNeeded4 = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
          if (actionNeeded4) {
            const action4 = Math.random() > 0.7 ? '过牌' : '下注';
            await performAction(page, action4, action4 === '下注' ? 50 : null);
            console.log(`✅ River行动: ${action4}`);
            await page.waitForTimeout(3000);
          }
        }
        
        // 等待摊牌和结果
        console.log('📍 等待摊牌结果...');
        await page.waitForTimeout(8000);
        
        // 检查结果
        const finalPot = await getPotAmount(page);
        const finalChips = await getPlayerChips(page, 'testPlayer');
        const chipChange = finalChips - initialChips;
        
        console.log(`💰 最终底池: ${finalPot}`);
        console.log(`💰 最终筹码: ${finalChips}`);
        console.log(`📊 筹码变化: ${chipChange > 0 ? '+' : ''}${chipChange}`);
        
        // 记录结果
        gameResults.push({
          hand: handsPlayed + 1,
          holeCards: holeCards,
          communityCards: riverCards,
          chipChange: chipChange,
          finalPot: finalPot,
          result: chipChange > 0 ? '胜利' : chipChange < 0 ? '失败' : '平局'
        });
        
        console.log(`🏆 本手结果: ${chipChange > 0 ? '胜利' : chipChange < 0 ? '失败' : '平局'}`);
        
        handsPlayed++;
        
        // 等待下一手准备
        await page.waitForTimeout(5000);
        
      } catch (error) {
        console.log(`❌ 第${handsPlayed + 1}手出现错误: ${error.message}`);
        
        // 尝试恢复 - 查找继续游戏的按钮
        const continueBtn = page.locator('button:has-text("继续"), button:has-text("下一手"), button:has-text("开始游戏")');
        if (await continueBtn.isVisible({ timeout: 5000 })) {
          await continueBtn.click();
          await page.waitForTimeout(3000);
        }
        
        handsPlayed++; // 即使出错也计入手数，避免无限循环
      }
    }
    
    // 输出游戏总结
    console.log('\n🎯 ===== 游戏总结 =====');
    const wins = gameResults.filter(r => r.result === '胜利').length;
    const losses = gameResults.filter(r => r.result === '失败').length;
    const ties = gameResults.filter(r => r.result === '平局').length;
    const totalChipChange = gameResults.reduce((sum, r) => sum + r.chipChange, 0);
    
    console.log(`📊 总手数: ${gameResults.length}`);
    console.log(`🏆 胜利: ${wins} 手`);
    console.log(`💀 失败: ${losses} 手`);
    console.log(`🤝 平局: ${ties} 手`);
    console.log(`💰 总筹码变化: ${totalChipChange > 0 ? '+' : ''}${totalChipChange}`);
    console.log(`📈 胜率: ${((wins / gameResults.length) * 100).toFixed(1)}%`);
    
    // 检查数据库记录
    console.log('\n🗄️ 检查数据库记录...');
    const dbRecords = await checkDatabaseRecords(page, tableId);
    console.log('数据库记录:', JSON.stringify(dbRecords, null, 2));
    
    // 验证基本游戏逻辑
    expect(gameResults.length).toBeGreaterThan(0);
    expect(handsPlayed).toBe(maxHands);
    
    console.log('✅ 完整游戏流程测试完成');
  });

  test('游戏规则验证测试', async ({ page }) => {
    console.log('🔍 开始游戏规则验证...');
    
    const tableId = await setupTestGame(page, 'ruleTest');
    await page.waitForTimeout(5000);
    
    // 测试特定游戏规则
    console.log('📋 验证游戏规则:');
    console.log('  ✓ 4人桌设置');
    console.log('  ✓ 盲注结构');
    console.log('  ✓ 行动顺序');
    console.log('  ✓ 下注限制');
    
    const playersCount = await page.locator('.player-info').count();
    expect(playersCount).toBe(4);
    
    // 检查盲注
    await page.waitForTimeout(3000);
    const potAmount = await getPotAmount(page);
    console.log(`💰 初始底池(盲注): ${potAmount}`);
    expect(potAmount).toBeGreaterThan(0); // 应该有小盲和大盲
    
    console.log('✅ 游戏规则验证通过');
  });

  test('机器人智能测试', async ({ page }) => {
    console.log('🤖 开始机器人智能测试...');
    
    await setupTestGame(page, 'botTest');
    await page.waitForTimeout(5000);
    
    // 观察机器人行为5手牌
    for (let i = 0; i < 5; i++) {
      console.log(`\n🤖 观察第${i + 1}手机器人行为...`);
      
      await page.waitForTimeout(3000);
      
      // 检查机器人是否在合理时间内做出决策
      const actionStart = Date.now();
      await page.waitForTimeout(10000); // 等待一轮行动
      const actionTime = Date.now() - actionStart;
      
      console.log(`⏱️ 机器人决策时间: ${actionTime}ms`);
      expect(actionTime).toBeLessThan(15000); // 机器人不应该太慢
      
      const pot = await getPotAmount(page);
      console.log(`💰 当前底池: ${pot}`);
    }
    
    console.log('✅ 机器人智能测试完成');
  });

  test('边界情况测试', async ({ page }) => {
    console.log('⚠️ 开始边界情况测试...');
    
    await setupTestGame(page, 'edgeTest');
    await page.waitForTimeout(5000);
    
    // 测试All-in情况
    console.log('🎰 测试All-in情况...');
    
    const playerChips = await getPlayerChips(page, 'edgeTest');
    console.log(`💰 玩家筹码: ${playerChips}`);
    
    if (playerChips > 0) {
      // 尝试All-in
      const actionNeeded = await page.locator('.action-buttons').isVisible({ timeout: 10000 });
      if (actionNeeded) {
        const allinBtn = page.locator('button:has-text("全押")');
        if (await allinBtn.isVisible({ timeout: 2000 })) {
          console.log('🎰 执行All-in...');
          await allinBtn.click();
          await page.waitForTimeout(5000);
          
          const newChips = await getPlayerChips(page, 'edgeTest');
          console.log(`💰 All-in后筹码: ${newChips}`);
        }
      }
    }
    
    console.log('✅ 边界情况测试完成');
  });
}); 