import re
import json 

import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_full_infomation(url: str):
    data = {}

    try:
        if 'zfcg' in url:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"[scrape_full_info] ⚠️ 请求失败: {url}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            contentbox = soup.find("div", class_="contentbox")
            if not contentbox:
                print(f"[scrape_full_info] ⚠️ 未找到 contentbox div: {url}")
                return None

            table = contentbox.find("table", class_="table-style")
            if not table:
                print(f"[scrape_full_info] ⚠️ 未找到 table-style 表格: {url}")
                return None

            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) == 2:
                    key = cells[0].text.strip().replace(":", "")
                    value = cells[1].text.strip()
                    data[key] = value

            source_div = soup.find('div', class_='source')
            if source_div:
                span_tag = source_div.find('span')
                if span_tag:
                    date = span_tag.text.strip().split(' ')[0]
                    data['发布日期'] = date

            info_title = soup.find('h3')
            if info_title:
                title = info_title.text.strip()
                data['项目标题'] = title

        else:
            match = re.search(r'\d+$', url)
            if not match:
                print(f"[scrape_full_info] ⚠️ URL 未提取到 contentId: {url}")
                return None

            number_str = match.group()
            api_url = 'https://www.szggzy.com/cms/api/v1/trade/content/detail?contentId=' + number_str

            response = requests.get(api_url, timeout=10)
            response.encoding = 'utf-8'
            if response.status_code != 200:
                print(f"[scrape_full_info] ⚠️ API 请求失败: {api_url}")
                return None

            try:
                result = response.json()
            except json.JSONDecodeError:
                print(f"[scrape_full_info] ⚠️ JSON 解析失败: {api_url}")
                return None

            detail = result.get('data', {})
            data['发布日期'] = detail.get('releaseTime', '')
            data['项目标题'] = detail.get('title', '')
            data['采购品目'] = detail.get('nodeList', '')
            data['项目名称'] = detail.get('title', '')

            soup = BeautifulSoup(detail.get('txt', ''), 'html.parser')
            target_td = soup.find("td", text="预计项目概况：")
            if target_td:
                project_desc = target_td.find_next("td").get_text(strip=True)
                data['采购需求概况'] = project_desc

    except Exception as e:
        print(f"[scrape_full_info] ❌ 异常: {e} | URL: {url}")
        return None

    return data if data else None

    # 有两种形式的url，需要分开处理
    # 需要包含字段内容：发布日期，项目标题，采购品目，项目名称，采购需求概况
    data = {}

    if 'zfcg' in url:
        response = requests.get(url)

        if response.status_code == 200:

            soup = BeautifulSoup(response.text, "html.parser")
            # 查找包含表格的 div
            contentbox = soup.find("div", class_="contentbox")
            if not contentbox:
                raise ValueError("未找到包含表格的 div")

            # 查找表格
            table = contentbox.find("table", class_="table-style")
            if not table:
                raise ValueError("未找到表格")

            # 提取表格内容
            rows = table.find_all("tr")
            for row in rows:
                # 获取每一行的标题和内容
                cells = row.find_all("td")
                if len(cells) == 2:  # 确保有两列
                    key = cells[0].text.strip().replace(":", "")  # 去掉冒号和空白
                    value = cells[1].text.strip()
                    data[key] = value

            # 查找 <div class="source"> 标签
            source_div = soup.find('div', class_='source')

            if source_div:
            # 查找 <span> 标签，并提取其中的日期部分
                span_tag = source_div.find('span')
                if span_tag:
                # 提取日期部分（假设格式始终是日期在字符串的开头）
                    date = span_tag.text.strip().split(' ')[0]
                    print('发布日期：', date)
                    data['发布日期'] = date

            # 查找项目标题
            info_title = soup.find('h3')
            if info_title:
                title = info_title.text.strip()
                print('抓取到的项目标题：', title)
                data['项目标题'] = title
    else:
        match = re.search(r'\d+$', url)

        if match:
            number_str = match.group()
            print("提取的数字字符串:", number_str)

            response = requests.get('https://www.szggzy.com/cms/api/v1/trade/content/detail?contentId=' + number_str)
            response.encoding = 'utf-8'
            # print(response.text)

            # 发布日期，项目标题，采购品目，项目名称，采购需求概况
            if response.status_code == 200:
                # result = json.dumps(response.json(), indent=4, ensure_ascii=False)
                # result = response.json()
                result = json.loads(response.text)
                data['发布日期'] = result['data']['releaseTime']
                data['项目标题'] = result['data']['title']
                data['采购品目'] = result['data']['nodeList']
                data['项目名称'] = result['data']['title']
                
                soup = BeautifulSoup(result['data']['txt'], 'html.parser')

                target_td = soup.find("td", text="预计项目概况：")
                if target_td:
                    project_desc = target_td.find_next("td").get_text(strip=True)
                    data['采购需求概况'] = project_desc

    return data