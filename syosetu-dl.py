# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 09:38:10 2016

@author: Bachelor03
"""

import requests
import classes
import argparse
import validators
import datetime
import io_handler    


def grab_chapter(url, novel_name, update_date, verbose=False):
    
    if verbose:
        print("Grabbing chapter {}".format(url.split("/")[-2]))
        
    chapter_name = ""
    chapter_number = 0
    
    webpage = requests.get(url)
    content = webpage.content

    # extract meta data for the chapter from the top page
    lines = content.split("\n")
    for line in lines:
        if "dc:title=" in line:
            chapter_novel_name = line[14:-1]
            
        if "<div id=\"novel_no\">" in line:
            temp = line[19:-6]
            temp = temp.split("/")
            chapter_number = int(temp[0])
            #max_chapters = temp[1]
            
        
        if "<p class=\"novel_subtitle\">" in line:
            chapter_name = line[26:-4]
    
    if verbose:
        print("Chapter name {}".format(chapter_name))

    # raise an Exception if for some reason title in chapter webpage differs from the novel title
    if chapter_novel_name != novel_name:
        raise MismatchException(novel_name, chapter_novel_name)


    # find the novel content on the webpage
    start_index = 0            
    end_index = 0    
    for x in range(len(lines)):
        if "<div id=\"novel_honbun\" class=\"novel_view\">" in lines[x]:
            start_index = x
        
        if "<div class=\"novel_bn\">" in lines[x]:
            end_index = x
        
    chapter_content = [] # "".join(lines[start_index:end_index])
    #html_free_chapter_content = remove_tags(chapter_content)
    #chapter = classes.Chapter(novel_name, chapter_name, chapter_number, html_free_chapter_content, url, update_date)


    # split the content into small enough chunks so that the google translate API will take them
    max_line_length = 100
    for x in range(end_index-start_index):
        line = remove_tags(lines[x+start_index])
        line = line.decode("UTF-8")
        if len(line) > max_line_length:
            temp_lines = tokenize(line, max_line_length)
            
            for temp_line in temp_lines:
                chapter_content.append(temp_line)
            
        else:
            chapter_content.append(line)
        
        
    chapter = classes.Chapter(novel_name, chapter_name, chapter_number, chapter_content, url, update_date)

    return chapter


def grab_novel(url, from_chapter=0, to_chapter=-1, verbose=False):
    if verbose:
        print("--------------------------------------")
        print("Grabbing novel with shorthand: {}".format(url.split("/")[-2]))
    webpage = requests.get(url)
    content = webpage.content

    novel_name = ""



    # extract meta data for the novel from the top page
    lines = content.split("\n")
    for line in lines:
        if "dc:title=" in line:
            novel_name = line[14:-1]
        if "作者：<a href=\"" in line:
            tagless_line = remove_tags(line).decode("UTF-8")
            author_name = tagless_line[3:]
            author_name = author_name.encode("UTF-8")
            author_url_line = line.decode("UTF-8")
            author_url = author_url_line[12:-(6+len(author_name.decode("UTF-8")))]
            if not validate_url(author_url):
                author_url = ""

    if verbose:
        print("Novel name: {}".format(novel_name))
        print("Author name: {}".format(author_name))
        print("--------------------------------------")

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
    chapter_urls_dates = get_chapter_urls_dates(url, lines)
    maximum_chapter_number= len(chapter_urls_dates)
    if to_chapter == -1:
        to_chapter = len(chapter_urls_dates)
    
    chapters = []    
    
    # only get chapters in specified range
    for x in range(len(chapter_urls_dates)):
        chapter_number = x + 1
        if chapter_number < from_chapter or chapter_number > to_chapter:    
            continue
        
        chapter_data = chapter_urls_dates[x]
        chapter = grab_chapter(chapter_data[0], novel_name, chapter_data[1], verbose)
        chapters.append(chapter)
        
    novel = classes.Novel(novel_name, url, html_free_exposition_content,
                          maximum_chapter_number, author_name, author_url )
    novel.chapters = chapters
                          
    return novel
    
# filter main page for chapter urls, titles and update time
def get_chapter_urls_dates(url, lines):
    
    chapter_urls_dates = []
    
    for x in range(len(lines)):
        if "<dl class=\"novel_sublist2\">" in lines[x]:
            if "<dd class=\"subtitle\">" in lines[x+1]:
                chapter_number = lines[x+1].split("/")[2]
                sub_url = url + chapter_number + "/"
                
                date = lines[x+3].split(" ")
                year = int(date[0][:4])
                month = int(date[1][:2])
                day = int(date[2][:2])
                update_time = datetime.date(year, month, day)
    
                chapter_urls_dates.append([sub_url, update_time])
                
    return chapter_urls_dates
    
    
# remove html parts from text
import re
TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(text):
    return TAG_RE.sub('', text)   
    
"""  
###############################################################################

# Both tokenize and minimize are taken and modified from gTTS by pndurette

############################################################################### 
"""

# split the text at punctuation into minimum number of chuncks that can 
# pass through google translate API
def tokenize(text, max_size):
    """ Tokenizer on basic roman punctuation """ 
        
    punc = "。、？！\n"
    punc_list = [re.escape(c) for c in punc]
    pattern = '|'.join(punc_list)
    parts = re.split(pattern, text)
    
    min_parts = []
    for p in parts:
        min_parts += minimize(p, " ", max_size)
    return min_parts
    
def minimize(thestring, delim, max_size):
    """ Recursive function that splits `thestring` in chunks
    of maximum `max_size` chars delimited by `delim`. Returns list. """ 
        
    if len(thestring) > max_size:
        idx = thestring.rfind(delim, 0, max_size)
        return [thestring[:idx]] + minimize(thestring[idx:], delim, max_size)
    else:
        return [thestring]    
"""
###############################################################################
###############################################################################
"""

def validate_url(url):
    is_valid = validators.url(url)
    if not is_valid:
        return False
    else:
        return True    
    
class MismatchException(Exception):
    
    def __init__(self, novel_name, chapter_novel_name ):

        message = "Novel name \"{}\" and novel name in chapter \"{}\" don't match!".format(novel_name, chapter_novel_name)
        # Call the base class constructor with the parameters it needs
        super(MismatchException, self).__init__(message)
        
class InvalidURLException(Exception):
    
    def __init__(self, url ):

        message = "Entered URL is not valid".format(url)
        # Call the base class constructor with the parameters it needs
        super(InvalidURLException, self).__init__(message)
        
    

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL of the novel you want to download")
    parser.add_argument('-o', '--output-dir', help='(Optional) Output folder for where to write the folder containing the downloaded files.', default=None)
    parser.add_argument('-r1', '--range-start', help='(Optional) Start of range of chapters to be downloaded. Only existing chapters will be downloaded.', required=False, default=None)
    parser.add_argument('-r2', '--range-end', help='(Optional) End of range of chapters to be downloaded. Only existing chapters will be downloaded.', required=False, default=None)
    parser.add_argument('-v', '--verbose', help='(Optional) Verbose command line output.', action="store_true")
    parser.add_argument('-tts', '--text-to-speech', help='(Optional) Make mp3 based on chapter content.', action="store_true")
    
    args = parser.parse_args()
    
    if args.verbose:
        verbose = True
    
    if not validate_url(args.url):
        raise InvalidURLException(args.url)
    else:
        url = args.url
        
    chapter_range = [0, -1]
    if args.range_start != None:
        chapter_range[0] = int(args.range_start)
    if args.range_end != None:
        chapter_range[1] = int(args.range_end)
    
    if args.output_dir != None:
        output_directory = args.output_dir
    else:
        output_directory = None
    
    novel = grab_novel(url, chapter_range[0], chapter_range[1], verbose)
    
    save_tts = False
    if args.text_to_speech:
        save_tts = True
    
    io_handler.save_novel(output_directory, novel, save_tts, verbose)
    
    
