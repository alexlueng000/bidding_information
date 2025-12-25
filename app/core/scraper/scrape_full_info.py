import re
import json 

import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_full_infomation(url: str, session: requests.Session | None = None, referer: str | None = None):
    data = {}

    # 复用外部 session；没有就临时建一个（但推荐外部传入）
    s = session or requests.Session()

    # 详情页通常更严格，给它单独补 referer（覆盖/补充）
    req_headers = {}
    if referer:
        req_headers["Referer"] = referer

    try:
        if 'zfcg' in url:
            resp = s.get(url, timeout=20, headers=req_headers)
            print(f"[scrape_full_info] detail status={resp.status_code} len={len(resp.text)} url={url}")
            if resp.status_code != 200:
                print(f"[scrape_full_info] ⚠️ 请求失败: {url} status={resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
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
                data['项目标题'] = info_title.text.strip()

        else:
            match = re.search(r'\d+$', url)
            if not match:
                print(f"[scrape_full_info] ⚠️ URL 未提取到 contentId: {url}")
                return None

            number_str = match.group()
            api_url = f"https://www.szggzy.com/cms/api/v1/trade/content/detail?contentId={number_str}"

            resp = s.get(api_url, timeout=20, headers=req_headers)
            print(f"[scrape_full_info] api status={resp.status_code} url={api_url}")
            if resp.status_code != 200:
                print(f"[scrape_full_info] ⚠️ API 请求失败: {api_url}")
                return None

            resp.encoding = 'utf-8'
            result = resp.json()

            detail = result.get('data', {}) or {}
            data['发布日期'] = detail.get('releaseTime', '')
            data['项目标题'] = detail.get('title', '')
            data['采购品目'] = detail.get('nodeList', '')
            data['项目名称'] = detail.get('title', '')

            soup = BeautifulSoup(detail.get('txt', ''), 'html.parser')
            target_td = soup.find("td", string="预计项目概况：")
            if target_td:
                project_desc = target_td.find_next("td").get_text(strip=True)
                data['采购需求概况'] = project_desc

    except Exception as e:
        print(f"[scrape_full_info] ❌ 异常: {e} | URL: {url}")
        return None

    return data if data else None
