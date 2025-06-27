class MusicPlayer {
    constructor() {
        this.audio = null;
        this.isPlaying = false;
        this.volume = 0.3; // 默认音量30%
        this.currentTrack = null;
        this.position = 'top-right'; // 默认位置
        this.tracks = {
            lobby: '/static/audio/lobby-music.mp3',
            table: '/static/audio/table-music.mp3',
            action: '/static/audio/action-music.mp3'
        };
        
        this.init();
    }
    
    init() {
        // 从localStorage读取用户设置
        const savedVolume = localStorage.getItem('musicVolume');
        const savedMuted = localStorage.getItem('musicMuted') === 'true';
        const savedPosition = localStorage.getItem('musicPosition') || 'top-right';
        
        if (savedVolume !== null) {
            this.volume = parseFloat(savedVolume);
        }
        
        this.position = savedPosition;
        
        // 创建音频元素
        this.audio = new Audio();
        this.audio.loop = true;
        this.audio.volume = savedMuted ? 0 : this.volume;
        this.audio.preload = 'auto';
        
        // 创建音乐控制界面
        this.createControlPanel();
        
        // 添加事件监听器
        this.addEventListeners();
        
        // 检测页面类型并播放相应音乐
        this.autoPlay();
    }
    
    createControlPanel() {
        // 创建音乐控制面板
        const controlPanel = document.createElement('div');
        controlPanel.id = 'music-control-panel';
        controlPanel.className = 'music-control-panel';
        
        controlPanel.innerHTML = `
            <div class="music-control-content">
                <button id="music-toggle" class="music-btn" title="播放/暂停音乐">
                    <span class="music-icon">🎵</span>
                </button>
                <div class="volume-control">
                    <button id="volume-toggle" class="music-btn" title="静音/取消静音">
                        <span class="volume-icon">🔊</span>
                    </button>
                    <input type="range" id="volume-slider" class="volume-slider" 
                           min="0" max="1" step="0.1" value="${this.volume}">
                </div>
                <div class="music-info">
                    <span id="music-track-name">背景音乐</span>
                </div>
                <button id="music-settings" class="music-btn" title="音乐设置">
                    <span class="settings-icon">⚙️</span>
                </button>
            </div>
        `;
        
        // 设置面板位置
        this.updatePanelPosition(controlPanel);
        
        document.body.appendChild(controlPanel);
        
        // 绑定控制按钮事件
        this.bindControlEvents();
    }
    
    bindControlEvents() {
        // 播放/暂停按钮
        document.getElementById('music-toggle').addEventListener('click', () => {
            this.toggle();
        });
        
        // 音量控制
        document.getElementById('volume-toggle').addEventListener('click', () => {
            this.toggleMute();
        });
        
        // 音量滑块
        document.getElementById('volume-slider').addEventListener('input', (e) => {
            this.setVolume(parseFloat(e.target.value));
        });
        
        // 设置按钮
        document.getElementById('music-settings').addEventListener('click', () => {
            this.showSettings();
        });
    }
    
    addEventListeners() {
        // 音频加载完成
        this.audio.addEventListener('canplaythrough', () => {
            console.log('🎵 背景音乐加载完成');
        });
        
        // 音频播放出错
        this.audio.addEventListener('error', (e) => {
            console.warn('🎵 背景音乐加载失败:', e);
            this.handleError();
        });
        
        // 音频开始播放
        this.audio.addEventListener('play', () => {
            this.isPlaying = true;
            this.updatePlayButton();
        });
        
        // 音频暂停
        this.audio.addEventListener('pause', () => {
            this.isPlaying = false;
            this.updatePlayButton();
        });
        
        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pause();
            } else if (this.wasPlayingBeforeHide) {
                this.play();
            }
        });
    }
    
    autoPlay() {
        // 根据当前页面自动选择音乐
        const currentPage = this.detectCurrentPage();
        this.loadTrack(currentPage);
        
        // 延迟播放，避免浏览器自动播放限制
        setTimeout(() => {
            this.play();
        }, 1000);
    }
    
    detectCurrentPage() {
        const path = window.location.pathname;
        
        if (path.includes('/table/')) {
            return 'table';
        } else if (path.includes('/lobby')) {
            return 'lobby';
        } else {
            return 'lobby'; // 默认
        }
    }
    
    loadTrack(trackName) {
        if (this.tracks[trackName] && this.currentTrack !== trackName) {
            this.currentTrack = trackName;
            this.audio.src = this.tracks[trackName];
            this.updateTrackInfo(trackName);
        }
    }
    
    updateTrackInfo(trackName) {
        const trackNames = {
            lobby: '大厅背景音乐',
            table: '游戏桌音乐',
            action: '紧张刺激音乐'
        };
        
        const infoElement = document.getElementById('music-track-name');
        if (infoElement) {
            infoElement.textContent = trackNames[trackName] || '背景音乐';
        }
    }
    
    play() {
        if (this.audio && this.audio.src) {
            const playPromise = this.audio.play();
            
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    console.log('🎵 背景音乐开始播放');
                }).catch((error) => {
                    console.warn('🎵 自动播放被阻止:', error);
                    this.showPlayButton();
                });
            }
        }
    }
    
    pause() {
        if (this.audio) {
            this.wasPlayingBeforeHide = this.isPlaying;
            this.audio.pause();
        }
    }
    
    toggle() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        if (this.audio) {
            this.audio.volume = this.volume;
        }
        
        // 保存到localStorage
        localStorage.setItem('musicVolume', this.volume.toString());
        
        // 更新音量图标
        this.updateVolumeIcon();
        
        // 更新滑块
        const slider = document.getElementById('volume-slider');
        if (slider) {
            slider.value = this.volume;
        }
    }
    
    toggleMute() {
        const isMuted = this.audio.volume === 0;
        
        if (isMuted) {
            this.audio.volume = this.volume;
            localStorage.setItem('musicMuted', 'false');
        } else {
            this.audio.volume = 0;
            localStorage.setItem('musicMuted', 'true');
        }
        
        this.updateVolumeIcon();
    }
    
    updatePlayButton() {
        const button = document.getElementById('music-toggle');
        const icon = button ? button.querySelector('.music-icon') : null;
        
        if (icon) {
            icon.textContent = this.isPlaying ? '⏸️' : '🎵';
            button.title = this.isPlaying ? '暂停音乐' : '播放音乐';
        }
    }
    
    updateVolumeIcon() {
        const button = document.getElementById('volume-toggle');
        const icon = button ? button.querySelector('.volume-icon') : null;
        
        if (icon) {
            if (this.audio.volume === 0) {
                icon.textContent = '🔇';
                button.title = '取消静音';
            } else if (this.audio.volume < 0.5) {
                icon.textContent = '🔉';
                button.title = '静音';
            } else {
                icon.textContent = '🔊';
                button.title = '静音';
            }
        }
    }
    
    showPlayButton() {
        // 显示明显的播放提示
        const notification = document.createElement('div');
        notification.className = 'music-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <span>🎵</span>
                <p>点击播放背景音乐</p>
                <button onclick="musicPlayer.play(); this.parentElement.parentElement.remove();">播放</button>
            </div>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    handleError() {
        console.warn('🎵 音乐文件加载失败，使用静默模式');
        // 隐藏音乐控制面板或显示错误状态
        const panel = document.getElementById('music-control-panel');
        if (panel) {
            panel.style.opacity = '0.5';
            panel.title = '音乐文件不可用';
        }
    }
    
    showSettings() {
        // 创建设置弹窗
        const modal = document.createElement('div');
        modal.className = 'music-settings-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>🎵 音乐设置</h3>
                    <button class="close-btn" onclick="this.closest('.music-settings-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="setting-item">
                        <label>音量: <span id="volume-display">${Math.round(this.volume * 100)}%</span></label>
                        <input type="range" id="settings-volume" min="0" max="1" step="0.1" value="${this.volume}">
                    </div>
                    <div class="setting-item">
                        <label>
                            <input type="checkbox" id="auto-play" ${this.autoPlayEnabled ? 'checked' : ''}> 
                            自动播放
                        </label>
                    </div>
                    <div class="setting-item">
                        <label>选择音乐:</label>
                        <select id="track-selector">
                            <option value="lobby" ${this.currentTrack === 'lobby' ? 'selected' : ''}>大厅音乐</option>
                            <option value="table" ${this.currentTrack === 'table' ? 'selected' : ''}>游戏桌音乐</option>
                            <option value="action" ${this.currentTrack === 'action' ? 'selected' : ''}>紧张音乐</option>
                        </select>
                    </div>
                    <div class="setting-item">
                        <label>控制面板位置:</label>
                        <select id="position-selector">
                            <option value="top-right" ${this.position === 'top-right' ? 'selected' : ''}>右上角</option>
                            <option value="top-left" ${this.position === 'top-left' ? 'selected' : ''}>左上角</option>
                            <option value="bottom-right" ${this.position === 'bottom-right' ? 'selected' : ''}>右下角</option>
                            <option value="bottom-left" ${this.position === 'bottom-left' ? 'selected' : ''}>左下角</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button onclick="this.closest('.music-settings-modal').remove()">关闭</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 绑定设置面板事件
        modal.querySelector('#settings-volume').addEventListener('input', (e) => {
            const volume = parseFloat(e.target.value);
            this.setVolume(volume);
            modal.querySelector('#volume-display').textContent = Math.round(volume * 100) + '%';
        });
        
        modal.querySelector('#track-selector').addEventListener('change', (e) => {
            this.loadTrack(e.target.value);
            if (this.isPlaying) {
                this.play();
            }
        });
        
        modal.querySelector('#position-selector').addEventListener('change', (e) => {
            this.setPosition(e.target.value);
        });
        
        // 点击背景关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    // 切换到特定音乐（供外部调用）
    switchToTrack(trackName) {
        if (this.tracks[trackName]) {
            this.loadTrack(trackName);
            if (this.isPlaying) {
                this.play();
            }
        }
    }
    
    // 播放动作音效（短音效，不循环）
    playActionSound(soundType = 'action') {
        if (this.tracks[soundType]) {
            const actionAudio = new Audio(this.tracks[soundType]);
            actionAudio.volume = this.volume * 0.7; // 动作音效稍微小声一点
            actionAudio.play().catch(e => console.warn('动作音效播放失败:', e));
        }
    }
    
    // 设置控制面板位置
    setPosition(position) {
        this.position = position;
        localStorage.setItem('musicPosition', position);
        
        const panel = document.getElementById('music-control-panel');
        if (panel) {
            this.updatePanelPosition(panel);
        }
    }
    
    // 更新面板位置样式
    updatePanelPosition(panel) {
        // 清除所有位置类
        panel.classList.remove('position-left', 'position-bottom');
        
        // 重置样式
        panel.style.top = '';
        panel.style.bottom = '';
        panel.style.left = '';
        panel.style.right = '';
        
        // 根据位置设置样式
        switch(this.position) {
            case 'top-left':
                panel.style.top = '80px';
                panel.style.left = '20px';
                break;
            case 'top-right':
                panel.style.top = '80px';
                panel.style.right = '20px';
                break;
            case 'bottom-left':
                panel.style.bottom = '20px';
                panel.style.left = '20px';
                break;
            case 'bottom-right':
                panel.style.bottom = '20px';
                panel.style.right = '20px';
                break;
            default:
                // 默认右上角
                panel.style.top = '80px';
                panel.style.right = '20px';
        }
    }
}

// 全局音乐播放器实例
let musicPlayer;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    musicPlayer = new MusicPlayer();
});

// 导出供外部使用
window.musicPlayer = musicPlayer; 