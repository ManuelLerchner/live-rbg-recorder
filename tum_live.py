import argparse
import re
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By

# From
# https://github.pcom/Valentin-Metz/tum_video_scraper


def enumerate_list(list_of_tuples):
    return [(f'{index:03d}', url) for index, url in enumerate(list_of_tuples)]


def login(tum_username: str, tum_password: str) -> webdriver.Chrome:
    driver_options = webdriver.ChromeOptions()
    driver_options.add_argument("--headless")
    driver = webdriver.Chrome(
        "/usr/lib/chromium-browser/chromedriver", options=driver_options)

    print("Logging in..")
    driver.get("https://live.rbg.tum.de/login")
    driver.find_element(
        By.XPATH, "/html/body/div[2]/div/div/div/button").click()
    driver.find_element(By.ID, "username").send_keys(tum_username)
    driver.find_element(By.ID, "password").send_keys(tum_password)
    driver.find_element(By.ID, "username").submit()
    sleep(2)
    if "Couldn't log in. Please double check your credentials." in driver.page_source:
        driver.close()
        raise argparse.ArgumentTypeError("Username or password incorrect")
    return driver


def get_video_links_of_subject(driver: webdriver.Chrome, subjects_identifier, camera_type):
    subject_url = "https://live.rbg.tum.de/course/" + subjects_identifier
    driver.get(subject_url)

    links_on_page = driver.find_elements(By.XPATH, "//a[@href]")
    video_urls = []
    for link in links_on_page:
        link_url = link.get_attribute("href")
        if link_url and "https://live.rbg.tum.de/w/" in link_url:
            video_urls.append(link_url)

    video_urls = [url for url in video_urls if (
        "/CAM" not in url and "/PRES" not in url)]
    video_urls = list(dict.fromkeys(video_urls))  # deduplicate

    video_playlists = []
    for video_url in video_urls:
        driver.get(video_url + "/" + camera_type)
        sleep(2)
        # find <i tag> with title "Copy HLS URL"
        copy_hls_url_button = driver.find_element(
            By.XPATH, "//i[@title='Copy HLS URL']")

        # extract html content of <i> tag
        copy_hls_url_button_html = copy_hls_url_button.get_attribute(
            'outerHTML')

        # extract url from html content
        playlist_url = re.search(
            r'copyToClipboard\(\'(.*?)\'.replaceAll', copy_hls_url_button_html).group(1)

        video_playlists.append(playlist_url)

    video_playlists.reverse()
    return video_playlists


def get_subjects(subjects, tum_username: str, tum_password: str):
    driver = login(tum_username, tum_password)
    queue = []
    for subject_name, (subjects_identifier, camera_type) in subjects.items():
        print(
            f"Scanning video links for: {subject_name} ({subjects_identifier}) of the {camera_type}..")
        m3u8_playlists = get_video_links_of_subject(
            driver, subjects_identifier, camera_type)
        m3u8_playlists = enumerate_list(m3u8_playlists)

        print(f'Found {len(m3u8_playlists)} videos for "{subject_name}"')
        queue.append((subject_name, m3u8_playlists))
    driver.close()
    return queue
