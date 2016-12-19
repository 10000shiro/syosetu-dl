# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 12:36:58 2016

@author: Bachelor03
"""

import os
import datetime
from gtts import gTTS
import subprocess

def save_chapter(directory, chapter, verbose=False):
    header = "Title: {}".format(chapter.novel_name) + "\n"
    header = header + "Chapter Nr. {} : ".format(chapter.chapter_number) + chapter.chapter_name + "\n"
    header = header + "URL: {}".format(chapter.url) + "\n"
    header = header + "Updated: {}".format(chapter.update_date) + "\n"
    header = header + "-----------------------------------------------------------" + "\n" + "\n"
    
    
    filename = "Chapter_{:03}.txt".format(chapter.chapter_number)
    filepath = os.path.join(directory,filename)
    
    
    if verbose:
        print("Saving {}  to {}".format(filename, directory))
    
    with open(filepath, "w") as text_file:
        text_file.write(header)
        for line in chapter.chapter_content:
            text_file.write(line.encode("UTF-8") + "\n")
            
        text_file.close()
        
# save tts version of chapter as mp3
def save_chapter_tts(directory, chapter, verbose=False):
    filenames = []
    for x in range(len(chapter.chapter_content)):
        line = chapter.chapter_content[x]
        
        if line.strip() == "":       
            continue
        
        tts = gTTS(text=line, lang='ja')
        
        filename = "Chapter_{:03}_Line_Nr_{}.mp3".format(chapter.chapter_number,x)
        filepath = os.path.join(directory,filename)    
        if verbose:
            print("Saving Text-to-Speech for Chapter {}, Line {}".format(chapter.chapter_number, x))
            print(line.encode("UTF-8"))
            
        tts.save(filepath)
        filenames.append(filename)

    # write txt file with all mp3s to be joined together
    filepath = os.path.join(directory,"tmp.txt").replace("\\", "/")          
    with open(filepath, "w") as text_file:
        for name in filenames:
            text_file.write("file {}".format(name) + "\n")
        text_file.close()
    
    output_file = os.path.join(directory,"Chapter_{:03}.mp3".format(chapter.chapter_number))
    
    # combine all mp3s via ffmpeg
    subprocess.call(
        "ffmpeg -f concat -safe 0 -i {} -c copy {}".format(filepath,output_file), shell=True)

    # remove all temporary files
    os.remove(filepath)
    for x in range(len(chapter.chapter_content)):
        filename = "Chapter_{:03}_Line_Nr_{}.mp3".format(chapter.chapter_number,x)
        filepath = os.path.join(directory,filename)  
        if(os.path.isfile(filepath)):
            os.remove(filepath)

    

def save_novel(directory=None, novel=None, save_tts=False, verbose = False):
    
    if directory == None:
        shorthand = novel.url.split("/")[-2]
        directory = os.path.join(os.getcwd(), shorthand)
    
    if not os.path.isdir(directory):
        os.mkdir(directory)
        
    contents_file = "Title: {}".format(novel.novel_name) + "\n"
    contents_file = contents_file + "URL: {}".format(novel.url) + "\n"
    contents_file = contents_file + "Author name: {}".format(novel.author_name) + "\n"
    contents_file = contents_file + "Author URL: {}".format(novel.author_url) + "\n"
    contents_file = contents_file + "Date of last download: {}".format(datetime.date.today()) + "\n"
    contents_file = contents_file +  "------------------------------------------------------------\n"
    contents_file = contents_file + "Exposition:"+ "\n" + "\n"
    contents_file = contents_file + novel.exposition
    
    if verbose:
        print("Saving info.txt to {}".format(directory))
    with open(os.path.join(directory,"info.txt"), "w") as text_file:
        text_file.write(contents_file)
        text_file.close()
        
    
    for chapter in novel.chapters:
        save_chapter(directory, chapter, verbose)
        if save_tts:
            save_chapter_tts(directory, chapter, verbose )
    
