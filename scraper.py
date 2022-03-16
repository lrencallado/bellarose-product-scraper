import asyncio
import re
from headers import *
from concurrent.futures import ThreadPoolExecutor
from requests_html import AsyncHTMLSession, HTML, HTMLSession
import firebase_admin
from firebase_admin import db

cred = firebase_admin.credentials.Certificate('serviceAccountKey.json')
firebase_admin = firebase_admin.initialize_app(cred, {'databaseURL': 'https://python-web-scraping-419e5-default-rtdb.asia-southeast1.firebasedatabase.app/'})
ref = db.reference("/Products")

product_urls = []
max_pages = 2

store_url = 'https://bellarose.pl/sklep/'

def get_product_urls():
    response = HTMLSession().get(store_url, headers=headers)
    response.html.render(timeout = 20)
    absolute_links = response.html.absolute_links
    print(response.html.next())
    
    for link in absolute_links:
        if '/product/' in link:
            product_urls.append(link)


async def fetch(session, url):
    r = await session.get(url, headers=headers)
    await r.html.arender(sleep = 2, timeout = 40)
    
    title= r.html.find('div.summary.entry-summary.col-md-6 > h2.product_title.entry-title')[0].text.strip()
    image_element = r.html.find('div.img-thumbnail > div.inner > img')
    image_url = image_element[0].attrs['src']
    description = r.html.find('div.description.woocommerce-product-details__short-description')[0].text.strip()
    price = r.html.find('p.price')[0].text.strip()
    availability = r.html.find('div.product_meta > span.product-stock')[0].text.strip()

    ref.push().set({'product_url': url, 'title': title, 'description': description, 'price': price, 'availability': availability})

def parseWebpage(page):
    pass

async def get_data_asynchronous():

    with ThreadPoolExecutor(max_workers=20) as executor:
        with AsyncHTMLSession() as session:

            loop = asyncio.get_event_loop()

            tasks = [
                await loop.run_in_executor(
                    executor,
                    fetch,
                    *(session, url)
                )
                for url in product_urls
            ]

            for response in await asyncio.gather(*tasks):
                parseWebpage(response)

def main():
    page_counter = 1
    while page_counter <= max_pages:
        store_url = get_product_urls()
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(get_data_asynchronous())
        loop.run_until_complete(future)
        page_counter += 1
        store_url = 'https://bellarose.pl/sklep/page/' + str(page_counter)
        print(store_url) 
        
main()