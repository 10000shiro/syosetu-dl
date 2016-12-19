# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 10:04:47 2016

@author: Bachelor03
"""

class Chapter():
    
    def __init__(self, novel_name, chapter_name, chapter_number, chapter_content, url, update_date):
        self.novel_name = novel_name
        self.chapter_name = chapter_name
        self.chapter_number = chapter_number
        self.chapter_content = chapter_content
        self.url = url
        self.update_date = update_date
        
        
        
class Novel():
    
    def __init__(self, novel_name, url, exposition, maximum_chapter_number, author_name, author_url):
        self.novel_name = novel_name
        self.url = url
        self.exposition = exposition
        self.maximum_chapter_number = maximum_chapter_number
        self.author_name = author_name
        self.author_url = author_url        
        
        self.last_downloaded_date = None
        self.chapters = []