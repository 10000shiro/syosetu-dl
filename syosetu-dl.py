# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 18:55:39 2018

@author: manshiro
"""

import requests
import classes
import argparse
import datetime
#import io_handler  
import sys  
import platform
from threading import Thread
from threading import active_count
import time
import re
import os
import maru_replacement

def write_log(log_string):
    if sys.version_info[0] == 3:
        with open("log_file.txt", "a", encoding="utf-8") as logfile:
            logfile.write(log_string)
            logfile.close()
    else:
        with open("log_file.txt", "a") as logfile:
            logfile.write(log_string)
            logfile.close()
        
def print_info(to_console, to_file, log_string):
    if to_console:
        print(log_string)
    if not to_file:
        write_log(log_string)


class SyosetuReader(object):
    
    def __init__(self, save_directory="", verbose=False, disable_logging=False):
        self.operating_system = platform.system()
        self.python3 = (sys.version_info[0] == 3)
        self.verbose = verbose
        self.disable_logging = disable_logging
        self.save_directory = save_directory
        
        
        try:
            
            import pykakasi
        
            self.kakasi = pykakasi.kakasi()
        
            self.kakasi.setMode("H","a") # Hiragana to ascii, default: no conversion
            self.kakasi.setMode("K","a") # Katakana to ascii, default: no conversion
            self.kakasi.setMode("J","a") # Japanese to ascii, default: no conversion
            self.kakasi.setMode("E","a") # Japanese to ascii, default: no conversion
            self.kakasi.setMode("r","Hepburn") # default: use Hepburn Roman table
            self.kakasi.setMode("s", True) # add space, default: no separator
            #kakasi.setMode("C", True) # capitalize, default: no capitalize
            self.conv = self.kakasi.getConverter()
            
            self.use_kakasi = True
            
            log_string = "Using pykakasi to transcribe romaji.\n"
            print_info(self.verbose, self.disable_logging, log_string)
        
        except ImportError:
            self.use_kakasi = False
            
            log_string = ""
            log_string += ("Will not output romaji transcription as pykakasi is not istalled.\n")
            log_string += ("Use the following command to install pykakasi:\n")
            log_string += ("\n")
            log_string += ("pip install six semidbm\n")
            log_string += ("pip install pykakasi\n")
            log_string += ("\n")
            log_string += ("For more information see: https://github.com/miurahr/pykakasi\n")
        
            print_info(self.verbose, self.disable_logging, log_string)
                

    def grab_novel_info(self, url):
        
        log_string = ""
        log_string += ("--------------------------------------\n")
        log_string += ("Grabbing meta info for novel with shorthand: {}\n".format(url.split("/")[-2]))
        
        print_info(self.verbose, self.disable_logging, log_string)
        
        webpage = requests.get(url)
        webpage.encoding = "UTF-8"
        if self.python3:
            content = webpage.text#.decode("UTF-8")
        else:
            content = webpage.content
            
        if "Too many access" in content:
            log_string = ("*"*30 + "\n")
            log_string += ("Error:\n")
            log_string += ("Too many accesses to syosetu.com. Change IP to retry.\n")
            log_string += ("*"*30 + "\n")
            print_info(self.verbose, self.disable_logging, log_string)
        
        novel_name = ""
    
        author_name=""
        author_url = ""
    
        # extract meta data for the novel from the top page
        lines = content.split("\n")
        for line in lines:
            if "dc:title=" in line:
                novel_name = line.replace("dc:title=\"","")[:-1]
                
            if "作者：<a href=\"" in line:
                tagless_line = remove_tags(line)
                author_name = tagless_line[3:]
                author_name = author_name
                author_url_line = line
                author_url = author_url_line[12:-(6+len(author_name))]
                if not validate_url(author_url):
                    author_url = ""
                    
            #if "作者：".decode("utf-8")in line:
            if "作者：" in line:
                tagless_line = remove_tags(line)
                author_name = tagless_line.replace("作者：","")
                author_url = author_url_line[12:-(6+len(author_name))].split("\"")[0]
    
        log_string = ""
        log_string += ("Novel name: {}\n".format(novel_name))
        log_string += ("Author name: {}\n".format(author_name))
        log_string += ("--------------------------------------\n")
        print_info(self.verbose, self.disable_logging, log_string)
    
        # find exposition text
        exposition_start = 0
        exposition_end = 0                
        for x in range(len(lines)):
            if "<div id=\"novel_ex\">" in lines[x]:
                exposition_start = x
                 
            if "<div class=\"index_box\">" in lines[x] and exposition_start != 0:
                exposition_end = x
                break
             
        exposition_content = "".join(lines[exposition_start:exposition_end])
        html_free_exposition_content = remove_tags(exposition_content)   
        
        # find chapter urls and names
        chapter_meta_infos = self.get_chapter_meta_infos(url, lines)
        maximum_chapter_number= len(chapter_meta_infos)
        chapters = []    
        # only get chapters in specified range
        for x in range(len(chapter_meta_infos)):
            chapter_number = x + 1
            chapter_name = chapter_meta_infos[x][1]
            chapter_url = chapter_meta_infos[x][0]
            chapter_update_date = chapter_meta_infos[x][2]
            
            chapter = classes.Chapter(novel_name, chapter_name, chapter_number, chapter_url, chapter_update_date)
            chapters.append(chapter)
        
        
        novel = classes.Novel(novel_name, url, html_free_exposition_content,
                              maximum_chapter_number, author_name, author_url)
        novel.chapters = chapters
        
        """
        if self.save_directory == "":
            shorthand = novel.url.split("/")[-2]
            self.save_directory = os.path.join(os.getcwd(), shorthand)
    
        if not os.path.isdir(self.save_directory):
            os.mkdir(self.save_directory)
        """
            
        contents_file = "Title: {}".format(novel.novel_name) + "\n"
        contents_file = contents_file + "URL: {}".format(novel.url) + "\n"
        contents_file = contents_file + "Author name: {}".format(novel.author_name) + "\n"
        contents_file = contents_file + "Author URL: {}".format(novel.author_url) + "\n"
        contents_file = contents_file + "Date of last download: {}".format(datetime.date.today()) + "\n"
        contents_file = contents_file +  "------------------------------------------------------------\n"
        contents_file = contents_file + "Exposition:"+ "\n" + "\n"
        contents_file = contents_file + novel.exposition
        
        filepath = os.path.join(self.save_directory, "info.txt")
                
        log_string = "Saving novel meta info to {}\n".format(filepath)
        print_info(self.verbose, self.disable_logging, log_string)
    
        if reader.python3:
            with open(filepath ,"w", encoding="utf-8") as outfile:
                outfile.write(contents_file)
        if not reader.python3:
            with open(filepath ,"w") as outfile:
                outfile.write(contents_file)
        
        log_string = "Successfully saved novel meta info\n".format(filepath)
        print_info(self.verbose, self.disable_logging, log_string)
        
        return novel
    

    # filter main page for chapter urls, titles and update time
    def get_chapter_meta_infos(self, url, lines):
        
        chapter_meta_infos = []
        
        for x in range(len(lines)):
            if "<dl class=\"novel_sublist2\">" in lines[x]:
                if "<dd class=\"subtitle\">" in lines[x+1]:
                    chapter_number = lines[x+2].split("/")[2]
                    sub_url = url + chapter_number + "/"
                    
                    date = lines[x+5].split("/")
                    year = int(date[0][:4])
                    month = int(date[1][:2])
                    day = int(date[2][:2])
                    update_time = datetime.date(year, month, day)
        
                    chapter_name = remove_tags(lines[x+2])
                    
                    chapter_meta_infos.append([sub_url, chapter_name, update_time])
                    
                    
        return chapter_meta_infos

    def grab_chapters(self, novel, chapter_range, use_threading=True):
        
        
        log_string = ("--------------------------------------\n")
        first_chapter = max(1,args.range_start)
        if args.range_end == -1:
            last_chapter = novel.maximum_chapter_number
        else: 
            last_chapter = chapter_range[1]
        log_string += ("Grabbing chapters {} to {}:\n".format(first_chapter, last_chapter))
        print_info(self.verbose, self.disable_logging, log_string)
        
        self.chapter_range = chapter_range
        
        if use_threading == False:
            for chapter in novel.chapters[chapter_range[0]:chapter_range[1]]:
                self.grab_chapter(chapter)
                
        if use_threading == True:
            
            threads = [GrabChapterThread(self, chapter) for chapter in novel.chapters[chapter_range[0]:chapter_range[1]]]
            
            
            timeout = 2.0
            update_interval = 0.01
            
            #Need to throttle down the requests or syosetu.com will block the IP
            for thread in threads:
                timeout = 2.0
                while active_count() > 10 and timeout > 0.0:
                    timeout = timeout - update_interval
                    time.sleep(update_interval)
                
                thread.start()
                
            for thread in threads:
                thread.join()
            
        return novel
        
    def grab_chapter(self, chapter):
            
        log_string = "Grabbing chapter {}\n".format(chapter.chapter_number)
        print_info(self.verbose, self.disable_logging, log_string)
            
        webpage = requests.get(chapter.url)
        webpage.encoding = "UTF-8"
        if self.python3:
            content = webpage.text#.decode("UTF-8")
        else:
            content = webpage.content
        
        if "Too many access" in content:
            
            log_string = ("*"*30 + "\n")
            log_string += ("Error:\n")
            log_string += ("Too many accesses to syosetu.com. Change IP to retry.\n")
            log_string += ("*"*30 + "\n")
            print_info(self.verbose, self.disable_logging, log_string)
            return 
        # extract meta data for the chapter from the top page
        chapter_novel_name = ""
        lines = content.split("\n")
        for line in lines:
            if "dc:title=" in line:
                chapter_novel_name = line.replace("dc:title=\"","")[:-1]
                
        
        
    
        # raise an Exception if for some reason title in chapter webpage differs from the novel title
        
        if chapter_novel_name != chapter.novel_name:
            raise MismatchException(chapter.novel_name, chapter_novel_name)
    
    
        # find the novel content on the webpage
        start_index = 0            
        end_index = 0    
        
        for x in range(len(lines)):
            #print(x, ": ", lines[x])
            
            if "novel_honbun" in lines[x] and "novel_view" in lines[x]:
                start_index = x
            
            if "novel_bn" in lines[x]:
                end_index = x
        
        
        chapter_content = [] # "".join(lines[start_index:end_index])
        #html_free_chapter_content = remove_tags(chapter_content)
        #chapter = classes.Chapter(novel_name, chapter_name, chapter_number, html_free_chapter_content, url, update_date)
       
        # split the content into small enough chunks so that the google translate API will take them
        for x in range(end_index-start_index):
            line = remove_tags(lines[x+start_index])
            
            chapter_content.append(line)
            
        log_string = "Grabbed chapter {}\n".format(chapter.chapter_number)
        print_info(self.verbose, self.disable_logging, log_string)
            
        chapter.chapter_content = chapter_content
    
    def save_chapters(self, novel, tts=False, use_threading=True):
        
         
        if use_threading:
            
            threads = [SaveThread(self, chapter) for chapter in novel.chapters[chapter_range[0]:chapter_range[1]]]
            
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        else: 
            for chapter in novel.chapters[chapter_range[0]:chapter_range[1]]:
                self._save_chapter(chapter)
        
            
            
        if tts:
            try:
                from gtts import gTTS
                self.gTTS = gTTS
                
                if use_threading:
                    
                    threads = [SaveTTSThread(self, chapter) for chapter in novel.chapters[chapter_range[0]:chapter_range[1]]]
                
                
                    for thread in threads:
                        thread.start()
                    for thread in threads:
                        thread.join()
                        
                else:
                    for chapter in novel.chapters[chapter_range[0]:chapter_range[1]]:
                        self.save_chapter_tts(chapter)
                        
            except ImportError as e:
                log_string = "Python module gTTS is not installed, text-to-speech not available.\n"
                print_info(self.verbose, self.disable_logging, log_string)
            
            except Exception as e:
                print(e)
                
        
        log_string = "Finished saving chapters\n"
        print_info(self.verbose, self.disable_logging, log_string)

    
        
    # save tts version of chapter as mp3
    def save_chapter_tts(self, chapter):
        text = "\n".join(chapter.chapter_content)
        #text = text.encode("UTF-8")
        self.gTTS._tokenize = _tokenize
        #tts = gTTS(text=text, lang="ja", verbose=verbose)
        tts = self.gTTS(text=text, lang="ja")
            
        filename = "Chapter_{:03}.mp3".format(chapter.chapter_number)
        filepath = os.path.join(self.save_directory,filename)    
        
        log_string = "Saving Text-to-Speech for Chapter {}\n".format(chapter.chapter_number)
        print_info(self.verbose, self.disable_logging, log_string)
        
        finished_download = False
        while not finished_download:
            try:
                tts.save(filepath)
                finished_download = True
                
                log_string = "Finished saving Text-to-Speech for Chapter {}".format(chapter.chapter_number)
                print_info(self.verbose, self.disable_logging, log_string)
            
            except Exception:
                return False
                    
        
    def _save_chapter(self, chapter):
        
        filepath = os.path.join(self.save_directory, "Chapter_{:03d}.txt".format(chapter.chapter_number))
            
        if self.python3:
           filepath = os.path.join(self.save_directory, "Chapter_{:03d}.txt".format(chapter.chapter_number))
               
        if not self.python3:
            outfile = open(filepath ,"w")
        
        log_string = "Saving chapter {} to {}\n".format(chapter.chapter_number, outfile.name)
        print_info(self.verbose, self.disable_logging, log_string)

        
        header = "Title: {}".format(chapter.novel_name) + "\n"
        header = header + "Chapter Nr. {} : ".format(chapter.chapter_number) + chapter.chapter_name + "\n"
        header = header + "URL: {}".format(chapter.url) + "\n"
        header = header + "Updated: {}".format(chapter.update_date) + "\n"
        header = header + "-----------------------------------------------------------" + "\n" + "\n"
        outfile.write(header)
        
        
        
        for line in chapter.chapter_content:
            outfile.write(line + "\n")
            
            if self.use_kakasi:
                """
                Need to fix some problems with kakasi symbols
                """
                
                line = maru_replacement.replace_maru_numbers(line)
                
                if self.python3:
                    if "\uff1a" in line:
                        line = line.replace("\uff1a", ":")
                    try:
                        outfile.write(self.conv.do(line)+ "\n")
                    
                    except Exception as e:
                        log_string = ("Error: {}+\n".format(e))
                        log_string += ("in chapter {}".format(chapter.chapter_number) + "\n")
                        log_string += (line)
                        log_string += ("\n")
                        print_info(self.verbose, self.disable_logging, log_string)
                        
                        
                            
                else:
                    
                    if "：" in line:
                        line = line.replace("：", ":")
                    try:
                        decoded_line = line.decode("utf-8")
                        outfile.write(self.conv.do(decoded_line).encode("utf-8") + "\n")
                   
                    except Exception as e:
                        log_string = ("Error: {}+\n".format(e))
                        log_string += ("in chapter {}".format(chapter.chapter_number) + "\n")
                        log_string += (line)
                        log_string += ("\n")
                        print_info(self.verbose, self.disable_logging, log_string)
                            
                
                    
            outfile.write("\n")
        outfile.close()
        
        
        log_string = "Saved chapter {} to {}\n".format(chapter.chapter_number, outfile.name)
        print_info(self.verbose, self.disable_logging, log_string)
        
class SaveThread(Thread):
    def __init__(self, reader, chapter, ):
        super(SaveThread, self).__init__()
        self.reader = reader
        self.chapter = chapter

    def run(self):
        try:
            self.reader._save_chapter(self.chapter)
        except ImportError as e:
            print(e)
        
class SaveTTSThread(Thread):
    def __init__(self, reader, chapter):
        super(SaveTTSThread, self).__init__()
        self.reader = reader
        self.chapter = chapter

    def run(self):
        try:
            self.reader.save_chapter_tts(self.chapter)
        except ImportError as e:
            print(e)

class GrabChapterThread(Thread):
    def __init__(self, reader, chapter):
        super(GrabChapterThread, self).__init__()
        self.reader = reader
        self.chapter = chapter

    def run(self):
        try:
            self.reader.grab_chapter(self.chapter)
        except MismatchException as e:
            self.chapter.chapter_content = "Error when downloading chapter:\n" + e.message

def remove_tags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)   
    

def validate_url(url):
    
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
    if not regex.search(url):
        return False
    else:
        return True    
    
class MismatchException(Exception):
    
    def __init__(self, novel_name, chapter_novel_name ):
        
        self.message = "Novel name \"{}\" and novel name in chapter \"{}\" don't match!".format(novel_name, chapter_novel_name)
        # Call the base class constructor with the parameters it needs
        super(MismatchException, self).__init__(self.message)
        
class InvalidURLException(Exception):
    
    def __init__(self, url ):

        message = "Entered URL is not valid".format(url)
        # Call the base class constructor with the parameters it needs
        super(InvalidURLException, self).__init__(message)

# split the text at punctuation into minimum number of chuncks that can 
# pass through google translate API
        
def _tokenize(self, text, max_size):
        """ Tokenizer on basic roman punctuation """ 
        
        punc = "。、？！\n"#.decode("UTF-8")
        punc_list = [re.escape(c) for c in punc]
        pattern = '|'.join(punc_list)
        parts = re.split(pattern, text)

        min_parts = []
        for p in parts:
            min_parts += self._minimize(p, " ", max_size)
        return min_parts


if __name__=="__main__":
    
    
    #Set up the command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL of the novel you want to download")
    parser.add_argument('-o', '--output-dir', help='(Optional) Output folder for where to write the folder containing the downloaded files.', default="")
    parser.add_argument('-r1', '--range-start', help='(Optional) Start of range of chapters to be downloaded. Only existing chapters will be downloaded.', required=False, default=0)
    parser.add_argument('-r2', '--range-end', help='(Optional) End of range of chapters to be downloaded. Only existing chapters will be downloaded.', required=False, default=-1)
    parser.add_argument('-v', '--verbose', help='(Optional) Verbose command line output.', action="store_true")
    parser.add_argument('-tts', '--text-to-speech', help='(Optional) Make mp3 based on chapter content.', action="store_true")
    parser.add_argument('-t', '--dont-use-threading', help='(Optional) don\'t use threading for requests. Slows down significantly but more likely to work.', required=False, default=False)
    parser.add_argument('-l', '--disable-logging', help='(Optional) don\'t save activites to log file.', required=False, default=False)
    
    args = parser.parse_args()
    
    verbose = False
    if args.verbose:
        verbose = True
    
    if not validate_url(args.url):
        raise InvalidURLException(args.url)
    else:
        url = args.url
    
    
    output_directory = ""
    if args.output_dir == "":
        shorthand = url.split("/")[-2]
        output_directory = os.path.join(os.getcwd(), shorthand)
    else:
        output_directory = args.output_dir
        
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)
        
    disable_logging = args.disable_logging
    
    log_string = "\n"
    log_string += ("#"*30 + "\n")
    log_string += ("Program started with Python version: {}.\n".format(sys.version))
    log_string += ("Date: {}\n".format(datetime.datetime.now()))
    if verbose:
        log_string +=("Printing verbose output to command line.\n")
    else:
        log_string +=("Verbose output to command line suppressed.\n")
    first_chapter = max(1,args.range_start)
    if args.range_end == -1:
        last_chapter = "last" 
    else: 
        last_chapter = args.range_end
        
        
    log_string += ("Ordered to load chapters {} to {}\n".format(first_chapter, last_chapter))
    log_string += ("Saving chapters to {}\n".format(output_directory))
    log_string += ("Saving text-to-speech for chapters: {}\n".format(args.text_to_speech))
    log_string += ("Use threading for downloads: {}\n".format(not args.dont_use_threading))
    log_string += ("-"*30 + "\n")
    log_string += ("Starting novel grab of URL: {}\n".format(url))
    
    print_info(verbose, disable_logging, log_string)
        
    reader = SyosetuReader(save_directory = output_directory, verbose=verbose, disable_logging=disable_logging)
    
    novel = reader.grab_novel_info(url)
    
    chapter_range = [int(args.range_start), int(args.range_end)]
    if (args.range_end) == -1 or int(args.range_end) >= novel.maximum_chapter_number:
        chapter_range[1] = novel.maximum_chapter_number+1
    
    reader.grab_chapters(novel, chapter_range, use_threading=not args.dont_use_threading)
    
    reader.save_chapters(novel, tts=args.text_to_speech, use_threading=not args.dont_use_threading)
   
    log_string = ("Finished downloading novel\n")
    print_info(verbose, disable_logging, log_string)
    
