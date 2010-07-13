#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Mooiter
# Copyright 2010 Christopher Massey
# See LICENCE for details.

import re

class LinkParser:
    def parse_links(self, text):
        return self.parse_tag(self.parse_url(text))
        
        
    def parse_url(self, text):
        """Parse text for url statements, outputs text with html url links.

        Args:
            text: String

        Returns:
            String of html formatted urls.
        """
    
        new_text = ''
        exp_url = re.compile(r"((https?|ftp)://+[\S\w\d:#@%/;$()~_?\+-=|.&]+)")
            
        result_url = exp_url.finditer(text)

        if result_url:
            start_url = 0
            for match_url in result_url:
                link_url = u'<a href="%s">%s</a>' % (match_url.group(),
                                                     match_url.group())
                #Grab all text before the url
                new_text += u"%s%s" % (text[start_url:\
                                       int(match_url.start())], link_url)
                start_url = int(match_url.end())
            #Grab the rest of the text after the url
            new_text += u"%s" % (text[start_url:])
            return new_text
        
    def parse_tag(self, text):
        """Parse text for tag/@ statements, outputs text with html tag/@ links.

        Args:
            text: String

        Returns:
            String of html formatted tag/@.
        """
         
        new_text = ''
        exp_tag = re.compile(r"((#|@)\w+)")
          
        result_tag = exp_tag.finditer(text)
             
        if result_tag:
            start_tag = 0
            
            for match_tag in result_tag:
                if match_tag.group(2) == "#":
                    link_tag = u'#<a class="internal" href="hash://%s">%s</a>'\
                                     % (match_tag.group(), match_tag.group()[1:])
                    new_text += u"%s%s" % (text[start_tag:\
                                           int(match_tag.start())], link_tag)
                    start_tag = int(match_tag.end())
                 
                else:
                    link_tag = u'<a class="internal" href="user://%s">%s</a>'\
                                     % (match_tag.group(), match_tag.group())
                    new_text += u"%s%s" % (text[start_tag:\
                                           int(match_tag.start())], link_tag)
                    start_tag = int(match_tag.end())
            new_text += u"%s" % (text[start_tag:])
            return new_text
          
            
if __name__ == "__main__":
    print LinkParser().parse_links("fuu @Tordf: #funny | #xkcd: iPad http://goo.gl/Q1nn")