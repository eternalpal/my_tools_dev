import requests
import re
import base64
import os
import csv
import time
from urllib.parse import urljoin

# ================= 配置与常量 =================
# 大图判定阈值：30KB (对 png/jpg 等静态图生效，GIF 无视此阈值)
SIZE_THRESHOLD = 30 * 1024 
INPUT_FILE = 'url-list.txt'
OUTPUT_FILE = 'result.csv'

def get_headers(token=None):
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 GitHub-Repo-Analyzer'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    return headers

def is_badge_or_icon(url):
    """预过滤：屏蔽徽章和统计图标，防止被当成有用的图片"""
    keywords =[
        'shields.io', 'travis-ci.org', 'badge.svg', 'badges.svg', 
        'github-readme-stats', 'buymeacoffee.com', 'ko-fi.com', 
        'hitcounter', 'codacy.com', 'codecov.io', 'sonarcloud.io', 
        'img.shields', 'workflow/status'
    ]
    return any(k in url.lower() for k in keywords)

def get_remote_image_info(url):
    """
    获取远程图片信息。
    返回: (是否为GIF, 是否为大尺寸静态图)
    """
    if is_badge_or_icon(url):
        return False, False
        
    # 辅助判断：如果URL明确以 .gif 结尾（去掉参数后）
    url_no_query = url.split('?')[0].lower()
    is_gif_ext = url_no_query.endswith('.gif')

    try:
        if 'github.com' in url and '/blob/' in url:
            url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')

        # 使用 stream=True 只拉取 Header，不下载图片实体，极大提升速度
        response = requests.get(url, stream=True, timeout=6, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            content_length = response.headers.get('Content-Length')
            response.close()

            # 1. 判断是否为 GIF (通过Header类型或后缀)
            if 'image/gif' in content_type or is_gif_ext:
                return True, False  # 是GIF，直接放行，无视大小
                
            # 2. 判断是否为普通图片 (png, jpg, jpeg 等)
            is_image_type = 'image' in content_type or 'octet-stream' in content_type
            if is_image_type and content_length:
                size = int(content_length)
                if size > SIZE_THRESHOLD:
                    return False, True # 不是GIF，但是满足大小的大图
                    
    except Exception as e:
        pass
        
    return False, False

def extract_all_links_from_markdown(content, base_url):
    """暴力提取所有可能属于图片的链接"""
    links = set()
    md_matches = re.findall(r'!\[.*?\]\((.*?)\)', content)
    html_matches = re.findall(r'<img[^>]+src=["\'](.*?)["\']', content, re.IGNORECASE)
    source_matches = re.findall(r'<source[^>]+srcset=["\'](.*?)["\']', content, re.IGNORECASE)

    for link in (md_matches + html_matches + source_matches):
        clean_link = link.strip().split(' ')[0].split('"')[0].strip("'")
        if not clean_link: continue
        
        full_url = clean_link
        if not clean_link.startswith(('http://', 'https://')):
            full_url = urljoin(base_url, clean_link)
            
        links.add(full_url)
    return links

def analyze_repo(repo_url, token):
    repo_url = repo_url.strip()
    if not repo_url: return None
    
    match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
    if not match:
        return {"项目名称": repo_url, "状态": "URL格式错误"}
    
    owner, repo_name = match.groups()
    repo_full_name = f"{owner}/{repo_name}"
    print(f"\n正在分析: {repo_full_name} ...")

    api_base = f"https://api.github.com/repos/{owner}/{repo_name}"
    headers = get_headers(token)
    
    try:
        # 1. 获取基本信息 (包含简介和 Homepage)
        resp = requests.get(api_base, headers=headers, timeout=10)
        if resp.status_code != 200:
            return {"项目名称": repo_full_name, "状态": f"无法访问(Code {resp.status_code})"}
        
        data = resp.json()
        default_branch = data.get('default_branch', 'main')
        
        # 提取简介和Homepage，清洗换行符防止CSV错乱
        description = str(data.get('description') or "无").replace('\n', ' ').replace('\r', '')
        homepage = str(data.get('homepage') or "无").strip()
        
        # 2. 获取 README 进行图片分析
        readme_url = f"{api_base}/readme"
        resp_readme = requests.get(readme_url, headers=headers, timeout=10)
        
        gif_count = 0
        large_static_count = 0
        
        if resp_readme.status_code == 200:
            try:
                content = base64.b64decode(resp_readme.json()['content']).decode('utf-8', errors='ignore')
                raw_base_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{default_branch}/"
                
                candidate_urls = extract_all_links_from_markdown(content, raw_base_url)
                print(f"  -> 发现 {len(candidate_urls)} 个多媒体链接，验证中...")
                
                for url in candidate_urls:
                    is_gif, is_large_static = get_remote_image_info(url)
                    if is_gif:
                        gif_count += 1
                    if is_large_static:
                        large_static_count += 1
                        
            except Exception as e:
                print(f"  -> Readme 解析出错: {e}")
                
        # 判断是否符合条件 (大图数 + GIF数 >= 3)
        total_valid_imgs = large_static_count + gif_count
        has_many = "是" if total_valid_imgs >= 3 else "否"
                
        return {
            "项目名称": repo_full_name,
            "项目简介": description,
            "Homepage链接": homepage,
            "发布时间": data.get('created_at', 'N/A')[:10],
            "Star数": data.get('stargazers_count', 0),
            "Fork数": data.get('forks_count', 0),
            "中大图数量(不含GIF)": large_static_count,
            "GIF数量": gif_count,
            "是否符合(>3图)": has_many,
            "状态": "成功",
            "URL": repo_url
        }
        
    except Exception as e:
        return {"项目名称": repo_full_name, "状态": "网络/脚本异常"}

def main():
    print("="*80)
    print(" GitHub 项目深度分析工具 (V5 增加简介与GIF特判版)")
    print("="*80)
    
    token = input("请输入 GitHub Token (直接回车跳过): ").strip() or None

    if not os.path.exists(INPUT_FILE):
        print(f"\n[错误] 未找到 {INPUT_FILE}，请先创建文件并填入链接。")
        input("按回车退出...")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        repo_urls = [line.strip() for line in f if line.strip()]

    print(f"\n读取到 {len(repo_urls)} 个项目，开始执行...")
    print("-" * 105)
    # 为保证控制台美观，控制台打印的简介会进行截断
    print(f"{'项目名称':<22} | {'Star':<6} | {'大图':<4} | {'GIF':<4} | {'符合':<4} | {'Homepage':<20} | {'简介(截断)'}")
    print("-" * 105)

    results =[]
    
    for url in repo_urls:
        info = analyze_repo(url, token)
        if info:
            if info.get('状态') == '成功':
                # 控制台输出时截断过长的简介和链接，以免换行乱版 (CSV中会保存完整版)
                short_desc = info['项目简介'][:15] + ".." if len(info['项目简介']) > 15 else info['项目简介']
                short_hp = info['Homepage链接'][:20] + ".." if len(info['Homepage链接']) > 20 else info['Homepage链接']
                
                print(f"{info['项目名称']:<22} | {info['Star数']:<6} | {info['中大图数量(不含GIF)']:<4} | {info['GIF数量']:<4} | {info['是否符合(>3图)']:<4} | {short_hp:<22} | {short_desc}")
            else:
                print(f"{info['项目名称']:<22} | {info['状态']}")
            results.append(info)
        time.sleep(0.5)

    try:
        keys =["项目名称", "项目简介", "Homepage链接", "发布时间", "Star数", "Fork数", "中大图数量(不含GIF)", "GIF数量", "是否符合(>3图)", "状态", "URL"]
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n[完成] 完整数据已保存至: {os.path.abspath(OUTPUT_FILE)}")
    except Exception as e:
        print(f"\n[错误] 保存CSV失败: {e}")

    input("\n所有任务已完成，按回车键退出程序...")

if __name__ == "__main__":
    main()