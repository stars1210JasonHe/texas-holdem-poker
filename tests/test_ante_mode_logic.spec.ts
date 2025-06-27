import { test, expect } from '@playwright/test';

test.describe('Ante模式游戏逻辑测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.waitForSelector('#createTableBtn', { timeout: 10000 });
  });

  test('按比例下注模式 - 庄家轮换和行动顺序测试', async ({ page }) => {
    console.log('开始测试按比例下注模式的游戏逻辑...');

    // 1. 创建ante模式房间
    await page.click('#createTableBtn');
    await page.waitForSelector('#createTableModal');

    // 选择ante模式
    await page.click('input[name="gameMode"][value="ante"]');
    await page.waitForSelector('#anteSettings');

    // 设置房间参数
    await page.fill('#tableTitle', 'Ante模式测试');
    await page.selectOption('#maxPlayers', '4');
    await page.fill('#initialChips', '1000');
    
    // 设置ante为5%（更明显的测试效果）
    await page.locator('#antePercentage').fill('5');
    
    // 添加3个机器人
    await page.click('.bot-increase[data-level="beginner"]');
    await page.click('.bot-increase[data-level="beginner"]');
    await page.click('.bot-increase[data-level="beginner"]');

    await page.click('#submitCreateTable');
    await page.waitForURL('**/table/**', { timeout: 10000 });

    console.log('房间创建成功，开始游戏测试...');

    // 2. 等待游戏开始
    await page.waitForSelector('#startHandBtn', { state: 'visible', timeout: 5000 });
    await page.click('#startHandBtn');

    // 3. 验证ante下注逻辑
    await page.waitForSelector('#potDisplay', { timeout: 5000 });
    
    // 验证ante金额计算（4个玩家 * 1000筹码 * 5% = 200底池）
    const expectedAnte = 4 * 1000 * 0.05; // 200
    
    let potValue = 0;
    for (let i = 0; i < 10; i++) {
      const potText = await page.textContent('#potDisplay');
      potValue = parseInt(potText || '0');
      if (potValue === expectedAnte) break;
      await page.waitForTimeout(500);
    }
    
    console.log(`底池金额: ${potValue}, 期望: ${expectedAnte}`);
    expect(potValue).toBe(expectedAnte);

    // 4. 验证游戏模式显示
    const gameModeText = await page.textContent('#gameModeInfo');
    expect(gameModeText).toContain('按比例');
    expect(gameModeText).toContain('5.0%');

         // 5. 记录第一手牌的庄家
     let dealerPlayers: string[] = [];
     let actionOrders: string[] = [];
     
     for (let hand = 0; hand < 3; hand++) {
       console.log(`\n=== 第${hand + 1}手牌开始 ===`);
       
       // 等待游戏状态稳定
       await page.waitForTimeout(1000);
       
       // 记录庄家信息
       const playerElements = await page.locator('.player-card').all();
       let currentDealer = '';
       let currentActionPlayer = '';
       
       for (const playerEl of playerElements) {
         const nickname = await playerEl.locator('.player-name').textContent();
         const isDealerVisible = await playerEl.locator('.dealer-chip').isVisible().catch(() => false);
         const isCurrentPlayer = await playerEl.getAttribute('class').then(cls => cls?.includes('current-player'));
         
         if (isDealerVisible) {
           currentDealer = nickname || '';
         }
         if (isCurrentPlayer) {
           currentActionPlayer = nickname || '';
         }
       }
       
       dealerPlayers.push(currentDealer);
       actionOrders.push(currentActionPlayer);
      
      console.log(`庄家: ${currentDealer}, 当前行动玩家: ${currentActionPlayer}`);
      
      // 6. 模拟一轮下注（让机器人自动处理，人类玩家简单过牌或跟注）
      let actionCount = 0;
      while (actionCount < 20) { // 防止无限循环
        // 检查是否轮到人类玩家行动
        const actionButtons = await page.locator('#actionButtons').isVisible().catch(() => false);
        
        if (actionButtons) {
          console.log('轮到人类玩家行动');
          
          // 检查可用的操作
          const canCheck = await page.locator('#checkBtn').isVisible().catch(() => false);
          const canCall = await page.locator('#callBtn').isVisible().catch(() => false);
          
          if (canCheck) {
            console.log('人类玩家选择过牌');
            await page.click('#checkBtn');
          } else if (canCall) {
            console.log('人类玩家选择跟注');
            await page.click('#callBtn');
          }
          
          await page.waitForTimeout(500);
        }
        
        // 等待机器人行动
        await page.waitForTimeout(1000);
        
        // 检查手牌是否结束
        const handNumber = await page.textContent('#handNumber');
        if (parseInt(handNumber || '0') > hand + 1) {
          console.log(`第${hand + 1}手牌结束`);
          break;
        }
        
        actionCount++;
      }
      
      // 7. 开始下一手牌（如果还没结束）
      if (hand < 2) {
        await page.waitForTimeout(2000);
        
        // 检查是否需要点击开始下一手牌
        const startNextHandBtn = await page.locator('#startHandBtn').isVisible().catch(() => false);
        if (startNextHandBtn) {
          await page.click('#startHandBtn');
          console.log('开始下一手牌');
        }
      }
    }

    // 8. 验证庄家轮换
    console.log('\n=== 庄家轮换验证 ===');
    console.log('庄家序列:', dealerPlayers);
    console.log('行动序列:', actionOrders);
    
    // 验证庄家确实在轮换（不是每次都是同一个）
    const uniqueDealers = [...new Set(dealerPlayers.filter(d => d))];
    console.log('不同的庄家数量:', uniqueDealers.length);
    expect(uniqueDealers.length).toBeGreaterThan(1);

    // 9. 验证行动顺序轮换
    const uniqueFirstActors = [...new Set(actionOrders.filter(a => a))];
    console.log('不同的首位行动玩家数量:', uniqueFirstActors.length);
    expect(uniqueFirstActors.length).toBeGreaterThan(1);

    console.log('Ante模式游戏逻辑测试完成！');
  });

  test('Ante模式下注逻辑测试', async ({ page }) => {
    console.log('开始测试Ante模式的下注逻辑...');

    // 1. 创建2人ante模式房间（更容易控制测试）
    await page.click('#createTableBtn');
    await page.waitForSelector('#createTableModal');

    await page.click('input[name="gameMode"][value="ante"]');
    await page.fill('#tableTitle', 'Ante下注测试');
    await page.selectOption('#maxPlayers', '2');
    await page.fill('#initialChips', '1000');
    await page.locator('#antePercentage').fill('2'); // 2%
    
    // 添加1个机器人
    await page.click('.bot-increase[data-level="beginner"]');

    await page.click('#submitCreateTable');
    await page.waitForURL('**/table/**', { timeout: 10000 });

    // 2. 开始游戏
    await page.click('#startHandBtn');
    await page.waitForTimeout(2000);

    // 3. 验证初始ante下注
    const potValue = await page.textContent('#potDisplay');
    const expectedPot = 2 * 1000 * 0.02; // 40
    expect(parseInt(potValue || '0')).toBe(expectedPot);

    // 4. 测试在ante基础上的下注
    const actionButtons = await page.locator('#actionButtons').isVisible().catch(() => false);
    if (actionButtons) {
      // 检查是否可以下注
      const canBet = await page.locator('#betBtn').isVisible().catch(() => false);
      if (canBet) {
        console.log('测试在ante基础上下注');
        await page.click('#betBtn');
        await page.waitForSelector('#betInput', { state: 'visible' });
        
        // 下注50筹码
        await page.fill('#betAmount', '50');
        await page.click('#confirmBetBtn');
        
        await page.waitForTimeout(1000);
        
        // 验证底池增加
        const newPotValue = await page.textContent('#potDisplay');
        expect(parseInt(newPotValue || '0')).toBeGreaterThan(expectedPot);
        console.log(`下注后底池: ${newPotValue}`);
      }
    }

    console.log('Ante模式下注逻辑测试完成！');
  });

  test('庄家位置和第一行动玩家验证', async ({ page }) => {
    console.log('开始验证庄家位置和第一行动玩家的关系...');

    // 创建3人房间进行测试
    await page.click('#createTableBtn');
    await page.waitForSelector('#createTableModal');

    await page.click('input[name="gameMode"][value="ante"]');
    await page.fill('#tableTitle', '庄家行动测试');
    await page.selectOption('#maxPlayers', '3');
    await page.fill('#initialChips', '1000');
    
    // 添加2个机器人
    await page.click('.bot-increase[data-level="beginner"]');
    await page.click('.bot-increase[data-level="beginner"]');

    await page.click('#submitCreateTable');
    await page.waitForURL('**/table/**', { timeout: 10000 });

    // 开始游戏并观察3手牌
    for (let hand = 0; hand < 3; hand++) {
      console.log(`\n=== 验证第${hand + 1}手牌 ===`);
      
      await page.click('#startHandBtn');
      await page.waitForTimeout(2000);

             // 获取所有玩家信息
       const playerElements = await page.locator('.player-card').all();
       
       interface PlayerInfo {
         position: number;
         nickname: string;
         isDealer: boolean;
         isCurrentPlayer: boolean;
       }
       
       const players: PlayerInfo[] = [];
       
       for (let i = 0; i < playerElements.length; i++) {
         const playerEl = playerElements[i];
         const nickname = await playerEl.locator('.player-name').textContent();
         const isDealerVisible = await playerEl.locator('.dealer-chip').isVisible().catch(() => false);
         const isCurrentPlayer = await playerEl.getAttribute('class').then(cls => cls?.includes('current-player')) || false;
         
         players.push({
           position: i,
           nickname: nickname || '',
           isDealer: isDealerVisible,
           isCurrentPlayer: isCurrentPlayer
         });
       }
       
       const dealer = players.find(p => p.isDealer);
       const firstActor = players.find(p => p.isCurrentPlayer);
       
       console.log('玩家信息:', players.map(p => 
         `${p.nickname}(位置${p.position}${p.isDealer ? ',庄家' : ''}${p.isCurrentPlayer ? ',行动中' : ''})`
       ).join(', '));
       
       if (dealer && firstActor) {
         // 验证第一行动玩家是庄家的下一位
         const expectedFirstActorPosition = (dealer.position + 1) % players.length;
         console.log(`庄家位置: ${dealer.position}, 第一行动玩家位置: ${firstActor.position}, 期望: ${expectedFirstActorPosition}`);
         
         expect(firstActor.position).toBe(expectedFirstActorPosition);
       }

      // 让游戏进行一轮（简单处理）
      if (await page.locator('#actionButtons').isVisible().catch(() => false)) {
        const canCheck = await page.locator('#checkBtn').isVisible().catch(() => false);
        if (canCheck) {
          await page.click('#checkBtn');
        } else {
          const canCall = await page.locator('#callBtn').isVisible().catch(() => false);
          if (canCall) {
            await page.click('#callBtn');
          }
        }
      }
      
      // 等待手牌结束
      await page.waitForTimeout(3000);
    }

    console.log('庄家位置和第一行动玩家验证完成！');
  });
}); 