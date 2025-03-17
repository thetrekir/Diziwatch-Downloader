import os
import time
import requests
from tqdm import tqdm
from colorama import init, Fore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import re

init(autoreset=True)

service = Service(ChromeDriverManager().install())
print(ChromeDriverManager().install())
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('log-level=3')
chrome_options.add_argument("--mute-audio")

def is_valid_url(url):
    pattern = re.compile(r'https://(?:www\.)?diziwatch\.net/.+')
    return bool(pattern.match(url))

url = input("Diziwatch anime bölümü linki: ")
while not is_valid_url(url):
    print(Fore.RED + "Geçersiz URL. Lütfen geçerli bir URL girin.")
    url = input("Diziwatch anime bölümü linki: ")

print("")
mode = input("Linkteki bölümü indirmek için '1', Linkteki bölümün dahil olduğu sezonu indirmek için '2' girin: ")

driver = webdriver.Chrome(service=service, options=chrome_options)

print(Fore.YELLOW + 'Sayfa yükleniyor...')

driver.get(url)
time.sleep(5)

print(Fore.GREEN + 'Sayfa yüklendi.')

def download_video(video_url, file_name, referer_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': referer_url
    }
    response = session.get(video_url, headers=headers, stream=True)

    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        t = tqdm(total=total_size, unit='iB', unit_scale=True, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]")
        
        with open(file_name, 'wb') as file:
            for data in response.iter_content(block_size):
                t.update(len(data))
                file.write(data)
                progress = t.n / total_size * 100
                print(Fore.CYAN + f'\r%{progress:.2f} İndiriliyor...', end='', flush=True)
        t.close()
        print(Fore.GREEN + f'\nBölüm başarıyla indirildi')
        return True
    else:
        return False

def get_video_info(video_url):
    match = re.search(r'/([^/]+)/(\d+)/(\d+)/(\d+)\.mp4', video_url)
    if match:
        show_name = match.group(1).replace('-', ' ').title()
        season = match.group(2)
        episode = match.group(3)
        quality = match.group(4)
        file_name = f'{show_name} S{season.zfill(2)} Ep{episode.zfill(2)} {quality}p.mp4'
        return show_name, season, episode, quality, file_name
    else:
        print(Fore.RED + 'URL formatı hatalı.')
        exit()

def process_video(video_url, referer_url, folder_name=None, episode_number=None):
    show_name, season, episode, quality, file_name = get_video_info(video_url)
    if folder_name:
        file_name = os.path.join(folder_name, file_name)
    if episode_number:
        print(Fore.YELLOW + f'{episode_number}. bölüm indiriliyor...')
    else:
        print(Fore.YELLOW + f'{episode}. bölüm indiriliyor...')
    
    video_url_1080 = re.sub(r'/(\d+)\.mp4', '/1080.mp4', video_url)
    video_url_720 = re.sub(r'/(\d+)\.mp4', '/720.mp4', video_url)
    video_url_480 = re.sub(r'/(\d+)\.mp4', '/480.mp4', video_url)
    
    if download_video(video_url_1080, file_name.replace(f'{quality}p', '1080p'), referer_url):
        print(Fore.GREEN + 'İndirildiği kalite: 1080p')
    elif download_video(video_url_720, file_name.replace(f'{quality}p', '720p'), referer_url):
        print(Fore.GREEN + 'İndirildiği kalite: 720p')
    else:
        download_video(video_url_480, file_name.replace(f'{quality}p', '480p'), referer_url)
        print(Fore.YELLOW + 'İndirildiği kalite: 480p')

if mode == '1':
    # Tek bölüm indirme
    print(Fore.YELLOW + 'Video URL si alınıyor...')
    video_element = driver.find_element(By.XPATH, '//*[@id="player"]/div[2]/div[4]/video')
    video_url = video_element.get_attribute('src')
    cookies = driver.get_cookies()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    show_name, season, episode, quality, file_name = get_video_info(video_url)
    process_video(video_url, url, episode_number=episode)
elif mode == '2':
    # Sezon indirme
    print(Fore.YELLOW + 'Sezon URL leri alınıyor...')
    episode_divs = driver.find_elements(By.XPATH, '//*[@class="season-episode"]//*[@class="bolumust"]//a')
    episode_urls = [url] + [episode.get_attribute('href') for episode in episode_divs]

    if episode_urls:
        print(Fore.GREEN + f'{len(episode_urls)} bölüm bulundu. İndirilmeye başlanıyor...')
        cookies = driver.get_cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
            
        folder_name = ""
        for i, episode_url in enumerate(episode_urls, start=1):
            driver.get(episode_url)
            time.sleep(5)
            video_element = driver.find_element(By.XPATH, '//*[@id="player"]/div[2]/div[4]/video')
            video_url = video_element.get_attribute('src')
            show_name, season, episode, _, file_name = get_video_info(video_url)
            if not folder_name:
                folder_name = f'{show_name} S{season.zfill(2)}'
                os.makedirs(folder_name, exist_ok=True)
            process_video(video_url, episode_url, folder_name, episode_number=i)
    else:
        print(Fore.RED + 'Bölüm URL leri bulunamadı.')
else:
    print(Fore.RED + 'Geçersiz seçenek. Lütfen "1" veya "2" girin.')

driver.quit()
