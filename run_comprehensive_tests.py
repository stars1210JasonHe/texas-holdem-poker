#!/usr/bin/env python3
"""
全面测试脚本 - 运行所有扑克游戏项目的测试
包括Python后端测试和Playwright前端测试
"""

import os
import sys
import subprocess
import time
import signal
import psutil
import threading
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.results = {
            'python_tests': {},
            'playwright_tests': {},
            'server_process': None,
            'start_time': None,
            'end_time': None
        }
        self.server_running = False
        
    def print_header(self, title):
        """打印测试章节标题"""
        print("\n" + "=" * 80)
        print(f"🎯 {title}")
        print("=" * 80)
        
    def print_section(self, title):
        """打印小节标题"""
        print("\n" + "-" * 60)
        print(f"📋 {title}")
        print("-" * 60)
        
    def check_dependencies(self):
        """检查测试依赖"""
        self.print_section("检查测试依赖")
        
        # 检查Python依赖
        try:
            import flask
            import flask_socketio
            print("✅ Flask 依赖已安装")
        except ImportError:
            print("❌ Flask 依赖缺失，请运行: pip install -r requirements.txt")
            return False
            
        # 检查Node.js和Playwright
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js 版本: {result.stdout.strip()}")
            else:
                print("❌ Node.js 未安装")
                return False
        except FileNotFoundError:
            print("❌ Node.js 未安装")
            return False
            
        # 检查Playwright
        try:
            result = subprocess.run(['npx', 'playwright', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Playwright 版本: {result.stdout.strip()}")
            else:
                print("❌ Playwright 未安装")
                return False
        except FileNotFoundError:
            print("❌ Playwright 未安装")
            return False
            
        return True
        
    def start_test_server(self):
        """启动测试服务器"""
        self.print_section("启动测试服务器")
        
        # 检查端口是否已被占用
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5000))
            sock.close()
            
            if result == 0:
                print("⚠️  端口5000已被占用，尝试终止现有进程...")
                self.kill_existing_server()
                time.sleep(2)
        except Exception:
            pass
            
        try:
            # 启动服务器进程
            env = os.environ.copy()
            env['FLASK_ENV'] = 'testing'
            
            self.server_process = subprocess.Popen(
                [sys.executable, 'app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            # 等待服务器启动
            print("🚀 正在启动服务器...")
            for i in range(30):  # 最多等待30秒
                try:
                    import requests
                    response = requests.get('http://localhost:5000', timeout=1)
                    if response.status_code == 200:
                        print("✅ 服务器启动成功")
                        self.server_running = True
                        return True
                except:
                    time.sleep(1)
                    print(f"⏳ 等待服务器启动... ({i+1}/30)")
                    
            print("❌ 服务器启动失败")
            return False
            
        except Exception as e:
            print(f"❌ 启动服务器时出错: {e}")
            return False
            
    def kill_existing_server(self):
        """终止现有服务器进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'app.py' in ' '.join(cmdline):
                        print(f"🔪 终止进程 PID {proc.info['pid']}")
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            print(f"终止进程时出错: {e}")
            
    def run_python_test(self, test_file, description):
        """运行单个Python测试"""
        print(f"\n🐍 运行 {description}")
        print(f"   文件: {test_file}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {description} - 通过 ({duration:.2f}s)")
                self.results['python_tests'][test_file] = {
                    'status': 'PASSED',
                    'duration': duration,
                    'output': result.stdout,
                    'error': result.stderr
                }
                return True
            else:
                print(f"❌ {description} - 失败 ({duration:.2f}s)")
                print(f"   错误: {result.stderr}")
                self.results['python_tests'][test_file] = {
                    'status': 'FAILED',
                    'duration': duration,
                    'output': result.stdout,
                    'error': result.stderr
                }
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} - 超时")
            self.results['python_tests'][test_file] = {
                'status': 'TIMEOUT',
                'duration': 300,
                'output': '',
                'error': 'Test timed out after 5 minutes'
            }
            return False
        except Exception as e:
            print(f"💥 {description} - 异常: {e}")
            self.results['python_tests'][test_file] = {
                'status': 'ERROR',
                'duration': 0,
                'output': '',
                'error': str(e)
            }
            return False
            
    def run_playwright_test(self, test_file, description):
        """运行单个Playwright测试"""
        print(f"\n🎭 运行 {description}")
        print(f"   文件: {test_file}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                ['npx', 'playwright', 'test', test_file, '--reporter=line'],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {description} - 通过 ({duration:.2f}s)")
                self.results['playwright_tests'][test_file] = {
                    'status': 'PASSED',
                    'duration': duration,
                    'output': result.stdout,
                    'error': result.stderr
                }
                return True
            else:
                print(f"❌ {description} - 失败 ({duration:.2f}s)")
                print(f"   错误: {result.stderr}")
                self.results['playwright_tests'][test_file] = {
                    'status': 'FAILED',
                    'duration': duration,
                    'output': result.stdout,
                    'error': result.stderr
                }
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} - 超时")
            self.results['playwright_tests'][test_file] = {
                'status': 'TIMEOUT',
                'duration': 600,
                'output': '',
                'error': 'Test timed out after 10 minutes'
            }
            return False
        except Exception as e:
            print(f"💥 {description} - 异常: {e}")
            self.results['playwright_tests'][test_file] = {
                'status': 'ERROR',
                'duration': 0,
                'output': '',
                'error': str(e)
            }
            return False
            
    def run_python_tests(self):
        """运行所有Python测试"""
        self.print_header("Python 后端测试")
        
        python_tests = [
            ('test_fixes_comprehensive.py', '综合功能修复测试'),
            ('test_all_in_fix.py', 'ALL IN 逻辑修复测试'),
            ('test_ante_manual.py', '前注模式测试'),
            ('test_showdown_api.py', '摊牌API测试'),
            ('test_showdown.py', '摊牌逻辑测试'),
            ('test_two_humans.py', '双人游戏测试'),
            ('test_two_humans_one_bot.py', '人机混合游戏测试'),
        ]
        
        python_passed = 0
        python_total = len(python_tests)
        
        for test_file, description in python_tests:
            if os.path.exists(test_file):
                if self.run_python_test(test_file, description):
                    python_passed += 1
            else:
                print(f"⚠️  测试文件不存在: {test_file}")
                
        print(f"\n📊 Python测试总结: {python_passed}/{python_total} 通过")
        return python_passed, python_total
        
    def run_playwright_tests(self):
        """运行所有Playwright测试"""
        self.print_header("Playwright 前端测试")
        
        if not self.server_running:
            print("❌ 服务器未运行，跳过前端测试")
            return 0, 0
            
        playwright_tests = [
            ('tests/test_seat_selection.spec.ts', '基础选座功能测试'),
            ('tests/test_seat_selection_comprehensive.spec.ts', '综合选座功能测试'),
            ('tests/test_join_room_seat_selection.spec.ts', '加入房间选座测试'),
            ('tests/test_join_room_seat_selection_fixed.spec.ts', '修复版加入房间选座测试'),
            ('tests/test_join_room_seat_selection_final.spec.ts', '最终版加入房间选座测试'),
            ('tests/test_poker_game_simple.spec.ts', '简单扑克游戏测试'),
            ('tests/test_poker_game_comprehensive.spec.ts', '综合扑克游戏测试'),
            ('tests/test_ante_mode_logic.spec.ts', '前注模式逻辑测试'),
            ('tests/test_game_manual.spec.ts', '手动游戏测试'),
        ]
        
        playwright_passed = 0
        playwright_total = len(playwright_tests)
        
        for test_file, description in playwright_tests:
            if os.path.exists(test_file):
                if self.run_playwright_test(test_file, description):
                    playwright_passed += 1
            else:
                print(f"⚠️  测试文件不存在: {test_file}")
                
        print(f"\n📊 Playwright测试总结: {playwright_passed}/{playwright_total} 通过")
        return playwright_passed, playwright_total
        
    def cleanup(self):
        """清理测试环境"""
        self.print_section("清理测试环境")
        
        if self.server_process:
            try:
                print("🛑 终止测试服务器...")
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ 服务器已终止")
            except subprocess.TimeoutExpired:
                print("🔪 强制终止服务器...")
                self.server_process.kill()
            except Exception as e:
                print(f"终止服务器时出错: {e}")
                
        # 清理测试数据库
        test_dbs = ['test_*.db', 'poker_game.db.test']
        for pattern in test_dbs:
            try:
                import glob
                for db_file in glob.glob(pattern):
                    os.remove(db_file)
                    print(f"🗑️  删除测试数据库: {db_file}")
            except Exception:
                pass
                
    def generate_report(self):
        """生成测试报告"""
        self.print_header("测试报告")
        
        self.end_time = datetime.now()
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        # 统计结果
        python_passed = sum(1 for r in self.results['python_tests'].values() if r['status'] == 'PASSED')
        python_total = len(self.results['python_tests'])
        
        playwright_passed = sum(1 for r in self.results['playwright_tests'].values() if r['status'] == 'PASSED')
        playwright_total = len(self.results['playwright_tests'])
        
        total_passed = python_passed + playwright_passed
        total_tests = python_total + playwright_total
        
        print(f"📅 测试开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 测试结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  总耗时: {total_duration:.2f} 秒")
        print()
        
        print("📊 测试结果汇总:")
        print(f"   Python测试:     {python_passed}/{python_total} 通过")
        print(f"   Playwright测试: {playwright_passed}/{playwright_total} 通过")
        print(f"   总计:          {total_passed}/{total_tests} 通过")
        print()
        
        # 成功率
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"✅ 测试成功率: {success_rate:.1f}%")
        
        # 详细失败信息
        failed_tests = []
        for test_file, result in self.results['python_tests'].items():
            if result['status'] != 'PASSED':
                failed_tests.append(f"Python: {test_file} - {result['status']}")
                
        for test_file, result in self.results['playwright_tests'].items():
            if result['status'] != 'PASSED':
                failed_tests.append(f"Playwright: {test_file} - {result['status']}")
                
        if failed_tests:
            print("\n❌ 失败的测试:")
            for test in failed_tests:
                print(f"   {test}")
        else:
            print("\n🎉 所有测试都通过了！")
            
        # 保存详细报告到文件
        self.save_detailed_report()
        
    def save_detailed_report(self):
        """保存详细测试报告到文件"""
        try:
            report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("扑克游戏全面测试报告\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"测试开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"测试结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总耗时: {(self.end_time - self.start_time).total_seconds():.2f} 秒\n\n")
                
                # Python测试详情
                f.write("Python测试详情:\n")
                f.write("-" * 40 + "\n")
                for test_file, result in self.results['python_tests'].items():
                    f.write(f"测试: {test_file}\n")
                    f.write(f"状态: {result['status']}\n")
                    f.write(f"耗时: {result['duration']:.2f}s\n")
                    if result['error']:
                        f.write(f"错误: {result['error']}\n")
                    f.write("\n")
                
                # Playwright测试详情
                f.write("Playwright测试详情:\n")
                f.write("-" * 40 + "\n")
                for test_file, result in self.results['playwright_tests'].items():
                    f.write(f"测试: {test_file}\n")
                    f.write(f"状态: {result['status']}\n")
                    f.write(f"耗时: {result['duration']:.2f}s\n")
                    if result['error']:
                        f.write(f"错误: {result['error']}\n")
                    f.write("\n")
                    
            print(f"📄 详细报告已保存到: {report_filename}")
            
        except Exception as e:
            print(f"保存报告时出错: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = datetime.now()
        
        try:
            # 检查依赖
            if not self.check_dependencies():
                print("❌ 依赖检查失败，测试中止")
                return False
                
            # 启动服务器
            if not self.start_test_server():
                print("❌ 服务器启动失败，只运行Python测试")
                
            # 运行Python测试
            python_passed, python_total = self.run_python_tests()
            
            # 运行Playwright测试
            playwright_passed, playwright_total = self.run_playwright_tests()
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️  测试被用户中断")
            return False
        except Exception as e:
            print(f"\n💥 测试过程中出现异常: {e}")
            return False
        finally:
            self.cleanup()
            self.generate_report()

def main():
    """主函数"""
    print("🎮 扑克游戏全面测试工具")
    print("=" * 80)
    
    runner = TestRunner()
    
    try:
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 测试被中断")
        sys.exit(1)

if __name__ == '__main__':
    main() 