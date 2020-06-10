import asyncio
from pyppeteer import launch
import random
from correct_rotation_for_angle import process_images


async def page_evaluate(page):
    await page.evaluate(
        '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } });window.screen.width=1366; }''')
    await page.evaluate('''() =>{ window.navigator.chrome = { runtime: {}, };}''')
    await page.evaluate('''() =>{ Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); }''')
    await page.evaluate('''() =>{ Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], }); }''')


async def main(username, password, width, height):

    browser = await launch({'headless': False,#可以无头
                            'slowMo':1.3,
                            'userDataDir': './userdata',
                            'args': [
                              f'--window-size={width},{height}'
                              '--disable-extensions',
                              '--hide-scrollbars',
                              '--disable-bundled-ppapi-flash',
                              '--mute-audio',
                              '--no-sandbox',
                              '--disable-setuid-sandbox',
                              '--disable-gpu',
                              '--disable-infobars'
                            ],
                            'dumpio': True
                            })
    page = await browser.newPage()
    # 设置浏览器头部
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36")

    # 设置浏览器大小
    await page.setViewport({'width': width, 'height': height})
    # 注入js，防反爬
    await page_evaluate(page)
    res=await page.goto('http://index.baidu.com/v2/index.html')

    await page.waitFor(2000)
    # 获取登录位置的文字，如果是登录就登录，不是就使用cookie
    elements = await (await(await page.querySelector('.username-text')).getProperty('textContent')).jsonValue()

    if elements == "登录":

        await page.click(".username-text")
        await asyncio.sleep(1.6)
        # 填写用户名
        await page.type('.pass-text-input-userName', username)
        # 填写密码
        await page.hover(".pass-text-input-password")
        await asyncio.sleep(0.5)
        await page.mouse.down()
        await asyncio.sleep(random.random())
        await page.mouse.up()
        # await page.click(".pass-text-input-password")
        await page.type('.pass-text-input-password', password)
        # 点击登录
        await page.mouse.move(page.mouse._x+random.randint(50,100), page.mouse._y+random.randint(100,200), options={"step": 3})
        await page.hover(".pass-button-submit")
        await page.mouse.down()
        await asyncio.sleep(random.random())
        await page.mouse.up()
        # await page.click(".pass-button-submit")
        await asyncio.sleep(2)
        rotImg = await page.querySelector('.vcode-spin-img')
        # 如果有验证码就去旋转
        while rotImg:
            img_url=await (await(rotImg).getProperty("src")).jsonValue()
            angle=process_images(img_url)[0]
            bottom_line=await (await(await page.querySelector(".vcode-spin-bottom")).getProperty("offsetWidth")).jsonValue()
            button_line = await (await(await page.querySelector(".vcode-spin-button")).getProperty("offsetWidth")).jsonValue()
            b=bottom_line-button_line
            move_line = angle/360*b
            await try_validation(page,move_line)
            # 停个3秒
            await asyncio.sleep(3)
            rotImg = await page.querySelector('.vcode-spin-img')

        #如果有需要短信验证码的弹窗的就费了
        no_in = await page.querySelector(".pass-forceverify-wrapper .forceverify-header-a")
        if no_in:
            print("有短信验证码，废了")
            await no_in.click()
    # 停个2秒
    await asyncio.sleep(2)
    cookies = await page.cookies()
    # 无头模式可以打印一下用户名看看能不能登录
    elements = await (await(await page.querySelector('.username-text')).getProperty('textContent')).jsonValue()
    print(elements)
    await browser.close()
    if elements == "登录":
        return None
    return cookies

async def try_validation(page, distance=308):
    # 将距离拆分成两段，模拟正常人的行为
    distance1 = distance - 10
    distance2 = 10
    btn_position = await page.evaluate('''
       () =>{
        return {
         x: document.querySelector('.vcode-spin-button').getBoundingClientRect().x,
         y: document.querySelector('.vcode-spin-button').getBoundingClientRect().y,
         width: document.querySelector('.vcode-spin-button').getBoundingClientRect().width,
         height: document.querySelector('.vcode-spin-button').getBoundingClientRect().height
         }}
        ''')
    x = btn_position['x'] + btn_position['width'] / 2
    y = btn_position['y'] + btn_position['height'] / 2
    # print(btn_position)
    await page.mouse.move(x, y)
    await page.mouse.down()
    await page.mouse.move(x + distance1, y, {'steps': 30})
    await page.waitFor(800)
    await page.mouse.move(x + distance1 + distance2, y, {'steps': 20})
    await page.waitFor(800)
    await page.mouse.up()

def baidu_login(username, password, width, height):
    return asyncio.get_event_loop().run_until_complete(main(username, password, width, height))


if __name__ == "__main__":

    width, height = 1366, 768
    username = '你的账户'
    password = '你的密码'

    cookies = baidu_login(username, password, width, height)
    print(cookies)
    if cookies:
        string_cookies = ""
        for each in cookies:
            string_cookies += f"{each['name']}={each['value']};"
