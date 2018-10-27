import argparse
import requests
import logging
from bs4 import BeautifulSoup
import os
import shutil

archiveURL = 'https://xkcd.com/archive/'

class Crawler:
    def __init__(self, archiveURL, outputDir, saveRawComics):
        self.archiveURL = archiveURL
        self.outputDir = outputDir
        self.saveRawComics = saveRawComics

    def get_archive(self):
        r = requests.get(self.archiveURL)
        html = BeautifulSoup(r.content, 'html.parser')
        archive = html.find(id='middleContainer').findAll('a')

        comics = []

        for comic in archive:
            c = {
                'id': comic['href'].replace('/', ''),
                'title': comic.get_text()
                }
            comics.append(c)

        print("Found " + str(len(comics)) + " comics to download.")
        return comics

    def setup_data_directory(self):
        if os.path.isdir(self.outputDir):
            print('Cleaning existing `' + self.outputDir + '` as the output directory.')
            shutil.rmtree(self.outputDir)
        else:
            print('Using newly created `' + self.outputDir + '` as the output directory.')

        os.makedirs(self.outputDir)

        if self.saveRawComics:
            os.makedirs(self.outputDir + '/raw')

    def download_comics(self, comics):
        f = open(self.outputDir + '/xkcd.json', 'w')
        counter = 0

        for comic in comics:
            url = 'https://xkcd.com/' + str(comic['id']) + '/info.0.json'
            r = requests.get(url)

            if self.saveRawComics:
                rf = open(self.outputDir + '/raw/' + str(comic['id']) + '.json', 'w')
                rf.write(r.text)
                rf.close()

            f.write(r.text)
            f.write('\r\n')

            counter = counter + 1

        f.close()
        print('Successfully downloaded ' + str(counter) + ' comics.')

def main():
    parser = argparse.ArgumentParser(description="""The XKCD crawler can gather
            the current list of published comics from the XKCD website and
            download their meta data for further processing.""")
    parser.add_argument("output", help="""the directory the comics will be
            saved to (the directory will be created if it does not exist yet
            and cleaned if it does)""")
    parser.add_argument("--save-raw-comics", help="""also save the raw json files
            before concatenation""", action="store_true")

    args = parser.parse_args()

    crawler = Crawler(archiveURL, args.output, args.save_raw_comics)
    comics = crawler.get_archive()
    crawler.setup_data_directory()
    crawler.download_comics(comics)

if __name__ == '__main__':
    main()
