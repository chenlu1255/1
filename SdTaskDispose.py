'''
#Author: Wiliam
@Time   2023/6/11 0:08
@File   robot_down
@Desc: 
'''


import os
import random
import shutil
import time
from Config.Settings import BASE_DIR, PDF_DIR, logger
import my_fake_useragent as ua1
ua = ua1.UserAgent(family="chrome")
BASEDIR = os.path.dirname(os.path.abspath(__file__))

# from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage import WebPage, ChromiumOptions,SessionOptions


def get_edge_path():
    paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    for path in paths:
        if os.path.isfile(path):
            return path
    return None


def get_edge_user_data_dir():
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default")
    if os.path.exists(user_data_dir):
        return user_data_dir
    else:
        return None


class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password,extension_path=None):
        self._dir = os.path.join(BASEDIR, "ProxyExtension") if not extension_path else extension_path
        shutil.rmtree(self._dir, ignore_errors=True)
        if not os.path.exists(self._dir):
            os.mkdir(self._dir)
        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir


class SD():
    def __init__(self,proxy=None,download_path=None,ini_path=None,browserPath=None,Type='proxy',user_name=None,password=None):
        self.return_msg = None
        local_edge_path = get_edge_path()
        if not local_edge_path:
            logger.error(f'没有找到本地浏览器，请检查是否安装了浏览器，或者重新配置浏览器路径，找不到可以联系管理员')
        self.browserPath = local_edge_path if not browserPath else browserPath
        if not os.path.exists(self.browserPath):
            raise FileNotFoundError(f'浏览器路径不存在，请检查浏览器路径是否正确')
        self.download_path = PDF_DIR.replace('\\','/') if not download_path else download_path.replace('\\','/')
        if not os.path.exists(self.download_path):
            os.mkdir(self.download_path)

        self.proxy_extension_path = os.path.join(BASEDIR, "ProxyExtension").replace('\\','/')
        # 判断是否使用代理，如果使用代理，就在配置文件中添加加载代理插件
        disable_extensions_except = os.path.join(BASEDIR, "yescaptcha1.1.24_0").replace('\\','/')
        load_extension = os.path.join(BASEDIR, "yescaptcha1.1.24_0").replace('\\','/')
        if proxy:
            disable_extensions_except += f',{self.proxy_extension_path}'
            load_extension += f',{self.proxy_extension_path}'
            logger.debug(f'使用代理：{proxy} ，开始加载插件')
            self.generation_proxy_extension(proxy)

        self.user_data_dir = get_edge_user_data_dir().replace('\\','/')
        if not self.user_data_dir:
            raise FileNotFoundError(f'没有找到本地浏览器配置文件，请检查是否安装了浏览器，或者重新配置浏览器路径，找不到可以联系管理员')

        self.ini_path = os.path.join(BASEDIR, "DrssionPageConfig.ini") if not ini_path else ini_path
        if os.path.exists(self.ini_path):
            os.remove(self.ini_path)
        # ,'--user-data-dir=%(user_data_dir)s'
        self.port = random.choice(list(range(3000,33000)))
        logger.debug(f'现在用的端口为：{self.port}')
        ini_file_conent = '''[paths]
download_path = %(download_path)s
tmp_path = %(download_path)s

[chromium_options]
address = 127.0.0.1:%(port)s
browser_path = chrome
arguments = ['--no-default-browser-check', '--disable-suggestions-ui', '--no-first-run', '--disable-infobars', '--disable-popup-blocking', '--disable-popup-blocking','--disable-extensions-except=%(disable_extensions)s','--load-extension=%(load_extensions)s']
extensions = []
prefs = {'profile.default_content_settings.popups': 0, 'profile.default_content_setting_values': {'notifications': 2}, "plugins.always_open_pdf_externally": True,'download.default_directory': '%(download_path)s'}
flags = {}
load_mode = normal
user = Default
auto_port = False
system_user_path = False
existing_only = False

[session_options]
headers =

[timeouts]
base = 10
page_load = 30
script = 30

[proxies]
http = 
https = 

[others]
retry_times = 3
retry_interval = 2'''%{'download_path':self.download_path,'disable_extensions':disable_extensions_except,'load_extensions':load_extension,'user_data_dir':self.user_data_dir,'port':self.port}
        with open(self.ini_path,mode='w',encoding='utf-8') as f:
            f.write(ini_file_conent)

        logger.debug(f'删除缓存文件 ')
        try:
            if os.path.exists(os.path.join(PDF_DIR, 'userData_9222')):
                shutil.rmtree(os.path.join(PDF_DIR, 'userData_9222'))
                logger.success(f'删除缓存文件成功')
            self.download_num = 0
        except Exception as e:
            logger.error(f'删除缓存文件失败，失败原因为：{e}')
            pass
        self.init_browser(Type,user_name,password)

    def generation_proxy_extension(self,porxy):
        '''
        生成代理插件
        :param porxy: {"server": "http://proxy1.new66.net:6218", "username": "YingKe", "password": "%qq123456.."}
        :return:
        '''
        # 处理插件
        # 先判断插件文件存不存在，不存在就创建，配置文件里默认引用的固定路径 D:\pycharmProject\10临时处理\SD本地浏览器自动化\ProxyExtension
        server,port = porxy['server'].split('//')[-1].split(':')
        username = porxy['username']
        password = porxy['password']

        proxy = (server, int(port), username, password, self.proxy_extension_path)  # your proxy with auth, this one is obviously fake
        ProxyExtension(*proxy)

    # 初始化浏览器
    def init_browser(self,Type,user_name=None,password=None):

        # 调整浏览器可执行文件路径
        co = ChromiumOptions(ini_path=self.ini_path).set_browser_path(self.browserPath)
        co.set_argument('--window-size', '1920,1080')
        so = SessionOptions()
        so.set_a_header('user-agent', str(ua.random()))
        self.page = WebPage(chromium_options=co)
        self.page.set.download_path(self.download_path)
        # 休息 2-6 秒，等待浏览器启动，以及插件加载完成
        time.sleep(random.choice(range(5, 8)))
        if Type == 'login':
            try:
                # 需 执行登录问题
                self.page.get('https://www.sciencedirect.com/')
                self.page.wait.load_start()
                html = self.page.html
                num = 0
                while True:
                    if 'Are You A Robot' in html:
                        logger.debug(f'出现验证码,休息一会，等待验证码消失')
                        time.sleep(random.choice(range(3, 5)))
                        num += 1
                        if num > 5: break
                    else:
                        break

                self.page.wait.ele_loaded('text=Sign in', timeout=30)

                # 登录
                self.page.ele('text=Sign in').click()
                self.page.wait.load_start()
                try:
                    self.page.wait.ele_loaded('text=接受Cookies')
                    self.page.wait(2)
                    self.page.ele('text=接受Cookies').click()
                    self.page.wait(2)
                except Exception as e:
                    pass
                self.page.wait.ele_loaded('#bdd-email')
                self.page.wait(1)
                # xielingna001@163.com    Science@@2024
                self.page.ele('#bdd-email').input(user_name)

                try:
                    self.page.wait.ele_loaded('text=接受Cookies')
                    self.page.wait(2)
                    self.page.ele('text=接受Cookies').click()
                    self.page.wait(5)
                except Exception as e:
                    pass
                else:
                    self.page.ele('#bdd-email').input(user_name)
                    self.page.wait(2)

                self.page.ele('text=继续').click()
                self.page.wait.load_start()

                verify_acc_html = self.page.html
                if '您的帐户有问题，请联系管理员或客服中心。' in verify_acc_html  or '已发送一封电子邮件到' in verify_acc_html:
                    self.del_page()
                    self.return_msg = f'{user_name} 账户异常，或出现邮箱验证'
                    return f'{user_name} 账户异常，或出现邮箱验证'


                self.page.wait.ele_loaded('#bdd-password')
                self.page.wait(2)
                self.page.ele('#bdd-password').click()
                self.page.wait(2)

                self.page.ele('#bdd-password').input(password + '\n')
                self.page.wait(2)
                try:
                    self.page.ele('#bdd-elsPrimaryBtn').click()
                    self.page.wait.load_start()
                except Exception as e:
                    pass
                self.page.wait(10)
            except Exception as e:
                logger.exception(f'出现异常错误：{e}')
                self.del_page()

    def del_page(self):
        try:
            self.page.close_other_tabs()
            self.page.close()
            if os.path.exists(self.ini_path):
                os.remove(self.ini_path)
            if os.path.exists(self.proxy_extension_path):
                shutil.rmtree(self.proxy_extension_path, ignore_errors=True)
            logger.debug(f'关闭浏览器成功')
        except Exception as e:
            logger.error(f'关闭页面失败，失败原因为：{e}')

        logger.debug(f'删除缓存文件 ：{self.download_num}')
        try:
            shutil.rmtree(os.path.join(PDF_DIR, f'userData_{self.port}'))
            logger.success(f'删除缓存文件成功')
            self.download_num = 0
        except Exception as e:
            logger.error(f'删除缓存文件失败，失败原因为：{e}')
            pass


    def download(self,url,file_name,download_url_xpath=''):
        try:

            self.page.close_other_tabs()

            name,suffix = file_name.rsplit('.')

            if url.endswith('.pdf'):
                self.page.set.download_file_name(name,suffix)
                self.page.get(url)
                self.page.wait.download_begin()
                logger.debug(f'开始下载')
                self.page.wait.all_downloads_done()
                # try:self.page.close()
                # except:pass
                logger.debug(f'下载结束')
                result_file = os.path.join(self.download_path, file_name)
                if os.path.exists(result_file):
                    return True, self.download_path,''
                else:
                    logger.debug(f'正常下载完成，但是没有找到文件，关闭浏览器重新开启')
                    return False, '正常下载完成，但是没有找到文件，关闭浏览器重新开启',''
            else:
                # 先去访问主页
                self.page.get(url)
                # 等待页面渲染完成
                self.page.wait.load_start(timeout=5)
                # 判断页面是否有相关内容，是否可以点击
                html = self.page.html
                # 检测页面是否有验证码,有验证码就等待验证码消失(有插件在自动点击)
                num = 0
                while True:
                    if 'Are You A Robot' in html:
                        logger.debug(f'出现验证码,休息一会，等待验证码消失')
                        time.sleep(random.choice(range(3, 5)))
                        num += 1
                        if num > 3:break
                    else:break

                html = self.page.html
                element = self.page.eles(download_url_xpath,timeout=5)

                # 检测页面是否有pdf
                if element:
                    logger.debug(f'在页面找到下载按钮,开始点击下载按钮')
                    # 设置文件名
                    self.page.set.download_file_name(name,suffix)
                    # 点击下载按钮
                    self.page.ele(download_url_xpath).click()
                    # 等待页面加载完成
                    self.page.wait.load_start(timeout=8)
                    # 等待下载开始
                    self.page.wait.download_begin()
                    logger.debug(f'开始下载')
                    # 等待下载结束
                    self.page.wait.all_downloads_done()
                    logger.debug(f'下载结束')
                    # 关闭页面

                    # try:self.page.close()
                    # except:pass

                    result_file = os.path.join(self.download_path, file_name)
                    if os.path.exists(result_file):
                        return True,result_file,html
                    else:
                        logger.debug(f'正常下载完成，但是没有找到文件')
                        return False,'正常下载完成，但是没有找到文件',''
                else:
                    logger.debug(f'在页面没有根据提供的信息找到下载按钮')
                    return False,'在页面没有根据提供的信息找到下载按钮',''
        except Exception as e:
            # try:self.page.close()
            # except:pass
            logger.exception(f'下载出错：{e},关闭浏览器重新开启')
            return False,f'下载出错：{e}',''


if __name__ == '__main__':

    # 待下载的文件详情页链接
    art_url = 'https://www.sciencedirect.com/science/article/abs/pii/B9780443152863000035'
    # 文件命名
    file_name = 'test.pdf'
    # SD pdf位置对应的dp写法
    download_url_xpath = 'tag:li@class=ViewPDF'

    # 本地ip无法访问sd，需添加代理访问
    proxies = {"server": "http://proxy1.new66.net:6219", "username": "YingKe", "password": "%qq123456.."}
    brower_obj = SD(proxy=proxies, Type='login', user_name='roberto.buelvas@gmail.com', password='Buelvasg=2020')

    down_result_bool, down_result_file_path, response_html = brower_obj.download(art_url, file_name,download_url_xpath)
    brower_obj.del_page()

    logger.debug(down_result_file_path)

