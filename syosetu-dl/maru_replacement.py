# -*- coding: utf-8 -*-
"""
Created on Sun Apr 29 10:40:52 2018

@author: manshiro
"""


def detect_maru_numbers(input_string):
    
    numerals = [u"〇", u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九"]
    
    if not "〇" in input_string:
        return []
    
    indices = [i for i, x in enumerate(input_string) if x == "〇"]
        
    numbers =[]
    
    covered_ranges = []
    
    for index in indices:
        index_already_covered = False
        for covered_range in covered_ranges:
            if index in covered_range:
                index_already_covered = True
                break
        if index_already_covered:
            continue
            
        number_start = 0
        number_stop = len(input_string)
        for i in range(index, -1, -1):
            if not input_string[i] in numerals:
                number_start = i+1
                break
        
        for i in range(index, len(input_string), 1):
            if not input_string[i] in numerals:
                number_stop = i
                break
                
            
        number = input_string[number_start:number_stop]
        
        if len(number) < 2:
            continue
        
        if not set(numerals[1:]).intersection(number):
            continue
        
        covered_ranges.append(range(number_start, number_stop, 1))
        
        numbers.append([number, number_start, number_stop])
        
    return numbers
            

def convert_maru_number(number_string):

    ten_numerals = ["", u"十", u"百", u"千"]
    ten_thousand_numerals = ["", u"万", u"億", u"兆", u"京"]
    
    text = list(number_string)
    
    text_length = len(text)
    for i in range(text_length-1, 0, -1):
        text.insert(i, ten_numerals[(text_length - i) % 4])
        
        if (text_length - i)*1.0/4 in range(len(ten_thousand_numerals)):
            text.insert(i, ten_thousand_numerals[int((text_length - i)/4)])
    
    for i in range(len(text) - 2, -1,-1):
        if text[i] == u"一" and not text[i+1] in ten_thousand_numerals:
            text = text[:i] + text[i+1:]
            
            
    for i in range(len(text) - 1, -1,-1):
        if i == len(text) - 1:
            if text[i] == u"〇":
                text = text[:i] + text[i+1:]
            continue
        
        if i < len(text):
            if text[i] == u"〇" and not text[i+1] in ten_thousand_numerals:
                text = text[:i] + text[i+2:]
        if i < len(text) - 1:
            if text[i] == u"〇" and text[i+1] in ten_thousand_numerals:
                text = text[:i] + text[i+1:]
            
    if text[-1] == u"〇":
        text == text[0:-1]
    
    text = "".join(text)
    
    return text


def replace_maru_numbers(input_string):
    
    maru_numbers = detect_maru_numbers(input_string)
    
    result = input_string
    
    for i in range(len(maru_numbers)):
        maru_number = maru_numbers[i]
        converted_number = convert_maru_number(maru_number[0])
        result = result[:maru_number[1]] + converted_number + result[maru_number[2]:]
        
        index_offset = len(converted_number) - (maru_number[2]-maru_number[1])
        
        for k in range(i+1, len(maru_numbers),1):
            maru_numbers[k][1] += index_offset
            maru_numbers[k][2] += index_offset
        
    return result
    
if __name__ == "__main__":
    
    test_string = u"試しに一〇〇や一〇二〇三〇を百と十万二千三十に変えましょう"
    
    text = replace_maru_numbers(test_string)
    
    import pykakasi
    
    kakasi = pykakasi.kakasi()
    kakasi.setMode("H","a") # Hiragana to ascii, default: no conversion
    kakasi.setMode("K","a") # Katakana to ascii, default: no conversion
    kakasi.setMode("J","a") # Japanese to ascii, default: no conversion
    kakasi.setMode("r","Hepburn") # default: use Hepburn Roman table
    kakasi.setMode("s", True) # add space, default: no separator
    kakasi.setMode("C", True) # capitalize, default: no capitalize
    conv = kakasi.getConverter()
    result = conv.do(text)
    
    print(result)
    