import pygame,sys,math,time,copy,datetime,json
import numpy as np

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

db_url = 'https://ham2021-bothe-default-rtdb.asia-southeast1.firebasedatabase.app/'
cred = credentials.Certificate("./key.json")
default_app = firebase_admin.initialize_app(cred, {'databaseURL':db_url})

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

WHITE = (255, 255, 255)
ORANGE = (255, 127, 0)
BLACK = (0, 0, 0)
RED = (255,0,0)

class Player:
    def __init__(self,x,y,P) -> None:
        self.x = x
        self.y = y
        self.P = P
        self.Xforce = 0
        self.Yforce = 0
    
    def move(self):
        self.x += self.Xforce
        self.y += self.Yforce
        if self.Xforce >= 0 :
            self.Xforce = max(0,self.Xforce-0.75)
        else:
            self.Xforce = min(0,self.Xforce+0.75)
        if self.Yforce >= 0 :
            self.Yforce = max(0,self.Yforce-0.75)
        else:
            self.Yforce = min(0,self.Yforce+0.75)

p1 = Player(100,-250,1)
p2 = Player(400,-250,2)
if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("GARGANTUA")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()
    while True:
        clock.tick(1000000)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_UP]:
            p1.Yforce = min(10,p1.Yforce+3)
        if pressed_keys[pygame.K_DOWN]:
            p1.Yforce = max(-10,p1.Yforce-3)
        if pressed_keys[pygame.K_RIGHT]:
            p1.Xforce = min(10,p1.Xforce+3)
        if pressed_keys[pygame.K_LEFT]:
            p1.Xforce = max(-10,p1.Xforce-3)

        screen.fill(BLACK)
        pygame.draw.circle(screen,WHITE,(p1.x,-p1.y),20)
        pygame.draw.circle(screen,RED,(p2.x,-p2.y),20)
        ref = db.reference()
        ref.update({1:{"x":p1.x,"y":p1.y}})
        p1.move()
        #p2.move()
        reader = ref.get()
        p2.x = 500 - reader[1]["x"]
        p2.y = -500 - reader[1]["y"]
        pygame.display.update()