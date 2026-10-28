"""Check the bookshelf and eight sibling reader repositories without a web server."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import json
import mimetypes

from playwright.sync_api import sync_playwright

SHELF = Path(__file__).resolve().parent
ROOT = SHELF.parent
OUT = ROOT / 'bookshelf-validation'
BASE = 'https://bookshelf.test'
PROJECTS = {
    'pytorch-apprentice': '连载',
    'ai-era-reader': '第一卷完',
    'data-empire-reader': '主线完成',
    'rag-empire-reader': '全书完结',
    'system-design-reader': '连载',
    'online-troubleshooting-reader': '连载',
    'coding-agent-reader': '第一卷完',
    'interview-proof-reader': '连载',
}


def local_file(url):
    path = unquote(urlsplit(url).path)
    for project in PROJECTS:
        prefix = f'/{project}/'
        if path.startswith(prefix):
            return ROOT / project / 'docs' / (path[len(prefix):] or 'index.html')
    file = SHELF / (path.lstrip('/') or 'index.html')
    return file / 'index.html' if file.is_dir() else file


class Links(HTMLParser):
    def __init__(self, file):
        super().__init__()
        self.links = []
        self.ids = set()
        self.feed(file.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag in ('a', 'link', 'script', 'img'):
            value = attrs.get('href') or attrs.get('src')
            if value:
                self.links.append(value)


def main():
    OUT.mkdir(exist_ok=True)
    pages = {'/': SHELF / 'index.html'}
    chapter_counts = {}
    for project in PROJECTS:
        docs = ROOT / project / 'docs'
        assert (docs / 'index.html').is_file(), f'Missing reader checkout: {docs}'
        chapters = json.loads((docs / 'chapters.json').read_text(encoding='utf-8'))
        chapter_counts[project] = len(chapters)
        assert len(chapters) == len(list(docs.glob('chapter-*.html'))), project
        pages.update({f'/{project}/{file.name}': file for file in sorted(docs.glob('*.html'))})

    # Parse query strings and URL-encoded fragments before checking local targets.
    parsers = {file: Links(file) for file in pages.values()}
    for path, file in pages.items():
        for link in parsers[file].links:
            target = urlsplit(urljoin(BASE + path, link))
            if target.scheme not in ('http', 'https') or target.netloc != 'bookshelf.test':
                continue
            destination = local_file(target.geturl())
            assert destination.is_file(), (path, link)
            if target.fragment and destination.suffix == '.html':
                if destination not in parsers:
                    parsers[destination] = Links(destination)
                assert unquote(target.fragment) in parsers[destination].ids, (path, link)

    expected_links = {f'/{project}/' for project in PROJECTS}
    errors = []
    missing = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width in (390, 768, 1440):
            context = browser.new_context(viewport={'width': width, 'height': 1000})

            def serve(route):
                if urlsplit(route.request.url).netloc != 'bookshelf.test':
                    route.abort()  # External illustrations must not affect acceptance.
                    return
                file = local_file(route.request.url)
                if file.is_file():
                    route.fulfill(path=str(file), content_type=mimetypes.guess_type(file)[0] or 'application/octet-stream')
                else:
                    missing.append(route.request.url)
                    route.fulfill(status=404, body='Missing file')

            context.route('**/*', serve)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(BASE + '/')
            assert page.title() == 'wupzl 的学习书架'
            cards = page.locator('.project')
            assert cards.count() == len(PROJECTS)
            assert set(cards.evaluate_all('(cards) => cards.map(card => card.getAttribute("href"))')) == expected_links
            for project, status in PROJECTS.items():
                card = page.locator(f'.project[href="/{project}/"]')
                assert card.locator('.project-status').inner_text() == status, project
                assert card.locator('.tags > span').first.inner_text().split(' · ')[0] == f'{chapter_counts[project]} 章', project
            assert '第十四章待续' in page.locator('.project[href="/pytorch-apprentice/"] .tags').inner_text()
            assert '第八章待续' in page.locator('.project[href="/interview-proof-reader/"] .tags').inner_text()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), ('home overflow', width)
            themes = set()
            for _ in range(3):
                page.locator('#theme').click()
                theme = page.locator('html').get_attribute('data-theme')
                themes.add(theme)
                page.reload()
                assert page.locator('html').get_attribute('data-theme') == theme
            assert themes == {'white', 'light', 'dark'}
            page.screenshot(path=str(OUT / f'home-{width}.png'), full_page=True)

            # Follow every home card, including RAG, and return through its header.
            for project in PROJECTS:
                page.locator(f'.project[href="/{project}/"]').click()
                assert page.url == f'{BASE}/{project}/'
                page.locator('.shelf-home').click()
                assert page.url == BASE + '/'

            # Walk a cycle through all eight projects using the actual switch menu.
            projects = list(PROJECTS)
            page.goto(f'{BASE}/{projects[0]}/')
            for project in projects[1:] + projects[:1]:
                page.locator('.shelf-switch summary').click()
                page.locator(f'.shelf-menu a[href="/{project}/"]').click()
                assert page.url == f'{BASE}/{project}/'

            for path in pages:
                if path == '/':
                    continue
                response = page.goto(BASE + path)
                assert response.status == 200, path
                assert page.locator('.shelf-nav').count() == 1, path
                assert page.locator('.shelf-home').get_attribute('href') == '/', path
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, path)
                links = page.locator('.shelf-menu a').evaluate_all('(links) => links.map(link => link.getAttribute("href"))')
                assert len(links) == len(PROJECTS) and set(links) == expected_links, path
                page.locator('.shelf-switch summary').click()
                box = page.locator('.shelf-menu').bounding_box()
                assert box and box['x'] >= 0 and box['x'] + box['width'] <= width, (width, path, box)
                page.locator('.shelf-switch summary').click()
                if path.endswith('/chapter-01.html'):
                    project = path.split('/')[1]
                    page.screenshot(path=str(OUT / f'{project}-{width}.png'))
            assert not missing, missing
            assert not errors, errors
            context.close()
            print(f'PASS: {len(pages)} pages at {width}px', flush=True)
        browser.close()
    print(f'PASS: home + {len(pages) - 1} reader pages; eight project counts/statuses, local links/anchors/resources, menus, cross-project navigation, home links, three themes, no overflow or JS errors.')


if __name__ == '__main__':
    main()
