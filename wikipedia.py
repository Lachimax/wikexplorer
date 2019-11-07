import urllib.request
from datetime import datetime
import numpy as np

final_places = ['Philosophy', 'Philosophical', 'Mathematics']


# TODO: Optimise so that get_title isn't accessing the page separate to the rest, as this is doubling the time taken

def detect_cycle(page, pages):
    if page in pages:
        pages = pages[pages.index(page):]
        return True, pages
    else:
        return False, []


def replace_space(text):
    while text.find(' ') != -1:
        text = text.replace(' ', '_')

    return text


def find_non_bracketed_link(text):
    # TODO: Fix Italics, example "Language family" page
    # TODO: Fix //, as in https://en.wikipedia.org/wiki/Exchange_(organized_market)
    # TODO: Fix no links in header eg "Report"
    # TODO: Attribution Needed eg https://en.wikipedia.org/wiki/Institution
    # TODO: Parse unusual characters, maybe different encoding?

    link_pos = text.find('<a href="/wiki/')
    while in_brackets(link_pos, text):
        link_pos += 15
        link_pos = text.find('<a href="/wiki/', link_pos)

    text = text[link_pos:]
    link = text[:text.find('" ')]
    link = link[9:]
    link = 'https://en.wikipedia.org' + link

    return link


def in_brackets(pos, text):
    brack = 0
    for pos, ch in enumerate(text[:pos]):
        if ch == '(':
            brack += 1
        if ch == ')':
            brack -= 1
    if brack == 0:
        return False
    else:
        return True


def get_title(url):
    text = get_page(url)
    text = text[text.find('<title>'):text.find(' - Wikipedia')]
    text = text[7:]
    return text


def get_page(url):
    a_page = urllib.request.urlopen(url)
    page_str = a_page.read()
    page_str = str(page_str, 'utf-8')
    return page_str


def get_header(url):
    page_str = get_page(url)
    page_header = page_str[page_str.find('<p>'):page_str.find('</p>') + 4]

    return page_header


def get_title_plus(text):
    text = text[text.find('<title>'):text.find(' - Wikipedia')]
    text = text[7:]
    return text


def get_page_plus(url):
    a_page = urllib.request.urlopen(url)
    page_str = a_page.read()
    page_str = str(page_str, 'utf-8')
    title = get_title_plus(page_str)
    return title, page_str


def get_header_plus(url):
    title, page_str = get_page_plus(url)
    page_header = page_str[page_str.find('<p>'):page_str.find('</p>') + 4]

    return title, page_header


def get_next(header):
    url = find_non_bracketed_link(header)
    return url


class WikiExplore:
    # TODO: Calculate average distance, max, min, median etc.
    def __init__(self):
        self.visited = {}
        self.cycles = []

    def show_cycles(self):
        self.cycles.clear()
        for p in self.visited:
            pg = self.visited[p]
            print(pg)
            if pg.in_cycle:
                self.cycles.append(pg)

        print()
        printed = []
        for p in self.cycles:
            print(p)
            printed.append(p.title)
            if p.nxt in printed:
                print()

    def find_cycle(self, name):
        name = replace_space(name)
        found_cycle = False
        dest = None
        count = 0
        pages = []
        cycle = []

        # date = datetime.now().strftime('%Y-%m-%d-%H:%M')

        url = 'https://en.wikipedia.org/wiki/' + name
        if name == 'Special:Random':
            name = get_title(url)
            name = replace_space(name)
            url = 'https://en.wikipedia.org/wiki/' + name
        first_title = name

        # page = WikiPage(name, url, date, None, None, None, False)
        # self.visited[name] = page

        page = WikiPage(None, None, None, None, None, None, None)

        while not found_cycle:

            name, header = get_header_plus(url)
            name = replace_space(name)
            page.nxt = name
            is_cycle, cycle = detect_cycle(name, pages)
            date = datetime.now().strftime('%Y-%m-%d-%H:%M')
            print(str(count) + ". " + url)

            if not is_cycle:

                if name not in self.visited:
                    page = WikiPage(name, url, date, None, None, None, False)
                    self.visited[name] = page


                else:
                    page = self.visited[name]
                    if not page.in_cycle:
                        print(name)
                        last, cycle, name = self.follow_to_cycle(name)
                        pages.extend(last)
                        for pg in last:
                            if pg is not name:
                                count += 1
                                print(str(count) + ". https://en.wikipedia.org/wiki/" + pg)
                        count += 1
                        print(str(count) + ". " + self.visited[name].url)
                    else:
                        cycle = page.cycle
                    found_cycle = True
                    is_cycle = True

            if is_cycle:
                dest = name
                print("Got from " + first_title + " to " + dest + " in " + str(count) + " steps")
                print(name + " is in a cycle of length " + str(len(cycle)) + ": ")
                print()
                for i, pg in enumerate(cycle):
                    self.visited[pg].in_cycle = True
                    print(str(i + 1) + ". " + pg)

                found_cycle = True

            count += 1

            url = get_next(header)
            count -= len(cycle)
            pages.append(name)

        for p in pages:
            pg = self.visited[p]
            if pg.in_cycle:
                pg.destination = pg.title
                pg.cycle = cycle
            else:
                pg.destination = dest
            if count >= 0:
                pg.distance = count
            else:
                pg.distance = 0
            count -= 1
        return pages, cycle

    def follow_to_cycle(self, page):
        this = self.visited[page].nxt
        pages = []

        while not self.visited[this].in_cycle:
            pages.append(self.visited[this].title)
            this = self.visited[this].nxt

        return pages, self.visited[this].cycle, this

    def run_many(self, titles):

        for title in titles:
            self.find_cycle(title)
            print()

    def run_random(self):
        self.find_cycle('Special:Random')

    def run_many_random(self, n):
        for i in range(n):
            self.run_random()
            print()


class WikiPage:
    def __init__(self, title, url, date, nxt, destination, distance, in_cycle):
        self.title = title
        self.url = url
        self.date = date
        self.nxt = nxt
        self.destination = destination
        self.distance = distance
        self.in_cycle = in_cycle
        self.cycle = ()

    def __str__(self):
        return str(self.title) + "; URL: " + str(self.url) + "; Date: " + str(self.date) + "; Next: " + str(
            self.nxt) + "; Destination: " + str(self.destination) + "; Distance: " + str(
            self.distance) + "; In Cycle: " + str(self.in_cycle)


w = WikiExplore()
# w.find_cycle('Richard Feynmann')
# print()
# w.find_cycle('Albert Einstein')
# print()
# w.find_cycle('Uhuru Kenyatta')
# print()
# w.find_cycle('Education')
# print()
# w.find_cycle('Physics')

pages = ['Giant Bomb', '!!!Fuck You!!!', 'Jurassic Park', 'Shoemakersville, Pennsylvania', 'William Wells (cricketer)',
         '1963 in Brazilian football', 'Kevin Bacon', 'African Elephant']
w.run_many(pages)
w.run_many_random(10)
w.show_cycles()
