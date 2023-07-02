import os
import json
import time
import threading
from argparse import ArgumentParser
from pprint import pprint
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def read_dataset(path: str) -> list:
    dataset = []
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            filepath = os.path.join(path, filename)
            with open(filepath, "r") as file:
                content = json.load(file)
            for entry in content:
                if entry["verified"] == "yes" and entry["target"] != "Other":
                    dataset.append(entry)
    return dataset


def collect_screenshot(driver: webdriver.Chrome, output_path: str, page_id: str) -> bool:
    filename = os.path.join(output_path, page_id + ".png")
    return driver.save_screenshot(filename)


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    visible_txt = soup.get_text()
    lines = (line.strip() for line in visible_txt.splitlines())
    visible_text = '\n'.join(line for line in lines if line)
    return visible_text


def collect_html(driver: webdriver.Chrome, output_path: str, page_id: str):
    filename = os.path.join(output_path, page_id + ".html")
    with open(filename, "w") as file:
        file.write(driver.page_source)


def thread_target(entry: dict):
    global cnt
    global phish
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(10)
    try:
        res = requests.get(entry["url"], timeout=10)
        if res.status_code != 200:
            print("Not 200")
            driver.quit()
            with lock:
                phish.remove(entry)
            return
        driver.get(entry["url"])
        time.sleep(5)
        visible_txt = extract_visible_text(driver.page_source)
        if visible_txt == "":
            print("No visible text")
            driver.quit()
            with lock:
                phish.remove(entry)
            return
        collect_html(driver, "datasets/htmls", entry["phish_id"])
        result = collect_screenshot(driver, "datasets/screenshots", entry["phish_id"])
        if not result:
            with lock:
                phish.remove(entry)
            return
        with lock:
            cnt += 1
        print(f"saved file {entry['phish_id']} : {cnt} / {len(phish)}")
    except:
        print("error")
        with lock:
            phish.remove(entry)
        driver.quit()
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--path", type=str, default="datasets/raw")
    args = parser.parse_args()

    phish = read_dataset(args.path)

    chrome_options = Options()
    chrome_options.add_argument("--headless")

    cnt = 0
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=10) as executor:
        for entry in phish:
            executor.submit(thread_target, entry)

    with open("datasets/phish.json", "w") as file:
        json.dump(phish, file, indent=4)

    print(f"Phish dataset size: {len(phish)}")

    analysis = {}
    for entry in phish:
        target = entry["target"]
        if target not in analysis:
            analysis[target] = 0
        analysis[target] += 1
    pprint(analysis)
