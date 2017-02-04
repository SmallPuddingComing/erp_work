#-*-coding:utf-8-*-

import random

from PIL import Image, ImageDraw, ImageFont
import os

from flask import Flask, render_template

class RandomChar():

  @staticmethod
  def Unicode():
    val = random.randint(0x4E00, 0x9FBB)
    return unichr(val)

  @staticmethod
  def GB2312():
    head = random.randint(0xB0, 0xCF)
    body = random.randint(0xA, 0xF)
    tail = random.randint(0, 0xF)
    val = ( head << 8 ) | (body << 4) | tail
    str = "%x" % val
    #
    return str.decode('hex').decode('gb2312','ignore')

  @staticmethod
  def Alphabet():
    upper_char = chr(random.randint(65, 90))
    lower_char = chr(random.randint(97, 122))
    one = random.choice([upper_char, lower_char])
    return one

class ImageChar():
  def __init__(self, fontColor = (0, 0, 0),
                     size = (80, 33),
                     fontPath = os.path.dirname(os.path.abspath(__file__))+'/simfang.ttf',
                     bgColor = (255, 255, 0, 0),
                     fontSize = 22):
    self.size = size
    self.fontPath = fontPath
    self.bgColor = bgColor
    self.fontSize = fontSize
    self.fontColor = fontColor
    self.font = ImageFont.truetype(self.fontPath, self.fontSize)
    #self.font = ImageFont.truetype( self.fontSize)
    self.image = Image.new('RGBA', size, bgColor)

  def rotate(self):
    img1 = self.image.rotate(random.randint(-5, 5), expand=0)
    img = Image.new('RGBA', img1.size, (255,)*4)
    self.image = Image.composite(img1, img, img1)

  def drawText(self, pos, txt, fill):
    draw = ImageDraw.Draw(self.image)
    draw.text(pos, txt, font=self.font, fill=fill)
    del draw

  def randRGB(self):
    return(0, 0, 0)
    # return (random.randint(0, 255),
    #        random.randint(0, 255),
    #        random.randint(0, 255))

  def randPoint(self):
    (width, height) = self.size
    return (random.randint(0, width), random.randint(0, height))

  def randLine(self, num):
    draw = ImageDraw.Draw(self.image)
    for i in range(0, num):
      draw.line([self.randPoint(), self.randPoint()], self.randRGB())
    del draw

  def randChar(self, num, type='chinese'):
    gap = 0
    start = 1
    strRes = ''
    for i in range(0, num):
      if type == 'chinese':
        char = RandomChar().GB2312()
      elif type == 'number':
        char = str(random.randint(0, 9))
      elif type == 'alphabet':
        char = RandomChar().Alphabet()
      strRes += char
      x = start + self.fontSize * i + random.randint(0, gap) + gap * i
      self.drawText((x, random.randint(5, 10)), char, (0,0,0))
      # self.rotate()
    self.randLine(3)
    return strRes, self.image