import os
from firebase_admin.db import reference
try:
    os.chdir(sys._MEIPASS)
except:
    os.chdir(os.getcwd())

import pygame,sys,math,copy,json,random,os
import numpy as np

from pygame import event
WIFI_STATUS = False

try:
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import db
    db_url = 'https://ham2021-bothe-default-rtdb.asia-southeast1.firebasedatabase.app/'
    cred = credentials.Certificate(os.path.join('.','assets','key.json'))
    default_app = firebase_admin.initialize_app(cred, {'databaseURL':db_url})
    db.reference().get()
    WIFI_STATUS = True
except:
    WIFI_STATUS = False

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500

WHITE   =  (255, 255, 255)
ORANGE  =  (255, 127, 0  )
YELLOW  =  (255, 255, 0  )
BLACK   =  (0,   0,   0  )
BLUE    =  (0,   0,   255)
RED     =  (255, 0,   0  )
SKYBLUE =  (135, 206, 235)
SLIVER  =  (192, 192, 192)
SPEED   =  5

SHIFTED = {
    '`' : '~',
    '1' : '!',
    '2' : '@',
    '3' : '#',
    '4' : '$',
    '5' : '%',
    '6' : '^',
    '7' : '&',
    '8' : '*',
    '9' : '(',
    '0' : ')',
    '-' : '_',
    '=' : '+',
    '[' : '{',
    ']' : '}',
    '\\' : '|',
    ';' : ':',
    '"' : "'",
    ',' : '<',
    '.' : '>',
    '/' : '?'
}
capsLock = False

START_SCENE = 0
CHARACTER_CHOOSE_SCENE = 1
GAME_SCENE = 2
DIED_PROCESSING = 3
DIED_SCENE = 4
RANK_PROCESS_SCENE = 5
DISPLAY_RANK_SCENE = 6

ITEM_IMG = pygame.image.load(os.path.join('.','assets','pictures','item.png'))    
ENERGY_EFFECT_IMG = pygame.image.load(os.path.join('.','assets','pictures','EneryEffect.png'))
ENERGY_EFFECT_IMG = pygame.transform.scale(ENERGY_EFFECT_IMG, (40, 40))

FONT = os.path.join('.','assets','Binggrae-Bold.ttf')
bullets = []
BGRects = []
scene = START_SCENE
character = 0

def move(pos,direct,x):
    return (pos[0] + math.cos(math.radians(direct))*x, pos[1] + math.sin(math.radians(direct))*x)

def getDistance(x1,y1,x2,y2):
    return math.sqrt((x1-x2)**2+(y1-y2)**2)

def isPointInCircle(pointX,pointY,circleX,circleY,circleR):
    return getDistance(pointX,pointY,circleX,circleY) <= circleR

def isPointInRect(pointX,pointY,rect):
    return rect.left <= pointX <= rect.right and rect.top <= pointY <= rect.bottom

def isCircleInCircle(circleX1,circleY1,circleR1,circleX2,circleY2,circleR2):
    return getDistance(circleX1,circleY1,circleX2,circleY2) <= (circleR1 + circleR2)

#https://stackoverflow.com/questions/403421/how-to-sort-a-list-of-objects-based-on-an-attribute-of-the-objects
def sortObjectBy(__Iter1,__attr,reverse = False):
    return np.array(sorted(__Iter1, key=lambda x: x.__getattribute__(__attr), reverse=reverse))

def write(screen,text,pos,font,size,color,center = None):
    try:
        myfont = pygame.font.Font(font, size)
    except:
        myfont = pygame.font.SysFont(font, size)

    textsurface = myfont.render(text, False, color)
    if center is None:
        text_rect = textsurface.get_rect(center=(pos[0], pos[1]))
        screen.blit(textsurface,text_rect)
    elif center:
        screen.blit(textsurface,pos)
    else:
        text_rect = textsurface.get_rect()
        text_rect.right = pos[0]
        screen.blit(textsurface,text_rect)

def rankProcess(screen,name,score,character):
    black = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    black.fill(BLACK)
    black.set_alpha(100)
    screen.blit(black,(0,0))
    write(screen,'LOADING...',(SCREEN_WIDTH/2,SCREEN_HEIGHT/2),FONT,75,WHITE)
    pygame.display.update()
    try:
        ref = db.reference()
        if ref.get() is None:
            ref.update({"rank":[[name,score,character]]})
        elif min(map(lambda x : x[1],ref.get()['rank'])) < score or len(ref.get()['rank'])<10:
            ref = db.reference()
            rank = ref.get()['rank']
            rank.append([name,score,character])
            ref.update({"rank":sorted(rank, key=lambda x: x[1],reverse=True)[:10]})
    except Exception as e:
        print(e)

class Player:
    def __init__(self,x,y,ground,hp,size) -> None:
        self.jumped = 0
        self.x = x
        self.y = y
        self.ground = ground
        self.Xforce = 0
        self.Yforce = 0
        self.size = size
        self.maxHP = hp
        self.hp = hp
        self.immune = 0
        self.effect = {}
        self.skin = pygame.Surface((self.size*2,self.size*2),pygame.SRCALPHA)
    
    def move(self):
        self.x += self.Xforce
        self.y += self.Yforce
        if self.Yforce != 0:
            self.Yforce -= 0.4
            if self.y <= self.ground + self.size:
                self.Yforce = 0
                self.y = self.ground + self.size
    
    def getEffect(self,effect,duration):
        if self.effect.get(effect) is None:
            self.effect[effect] = duration
        else:
            self.effect[effect] += duration
    
    def effectCounter(self,step):
        for i in self.effect.keys() :
            self.effect[i] -= step
        keys = list(self.effect.keys()).copy()
        for i in keys :
            if self.effect[i] <= 0:
                self.effect.pop(i)
    
    def collision(self,obstacles):
        for i in range(len(obstacles)):
            obstacle = obstacles[i]
            left = obstacle.x - obstacle.xSize - self.size
            right = obstacle.x + obstacle.xSize + self.size
            down = obstacle.y - 2*obstacle.ySize - self.size
            up = obstacle.y - self.size
            if left < self.x < right and down < self.y < up:
                return True
            if isPointInCircle(left,up,self.x,self.y,self.size-1) or isPointInCircle(left,down,self.x,self.y,self.size-1) or isPointInCircle(right,up,self.x,self.y,self.size-1) or isPointInCircle(right,down,self.x,self.y,self.size-1) :
                return True
        return False
    
    def draw(self,screen):
        if self.immune != 0 and self.immune % 50 <= 25:
            self.skin.set_alpha(200)
            screen.blit(self.skin,(self.x-self.size,-self.y-self.size))
        else:
            self.skin.set_alpha(255)
            screen.blit(self.skin,(self.x-self.size,-self.y-self.size))
    
    def attackDown(self):
        global bullets
    
    def attackCharging(self,screen):
        global bullets
    
    def attackUp(self):
        global bullets
    
    def displayItem(self,screen):
        write(screen,str(self.effect[1]),(250,50),FONT,20,WHITE)
    
    @staticmethod
    def repr():
        return 'Null'
    
    @staticmethod
    def info():
        return ['정보없음','정보없음','정보없음']

class Standard(Player):
    def __init__(self,x,y,ground,size) -> None:
        super().__init__(x,y,ground,70,size)
        pygame.draw.circle(self.skin,WHITE,(self.size,self.size),self.size)
    
    def attackDown(self):
        super().attackDown()
        if 1 in self.effect.keys():
            bullets.append(Bullet(self,1))
        else:
            bullets.append(Bullet(self))
        self.effectCounter(1)
    
    def attackCharging(self,screen):
        return super().attackCharging(screen)
    
    def attackUp(self):
        return super().attackUp()
    
    @staticmethod
    def repr():
        return 'Standard'
    
    @staticmethod
    def info():
        return ['흰 총알을 발사합니다.(atk : 1)','파괴적인 총알을 발사합니다.(atk : 3)(5발)','70']

class Tech(Player):
    def __init__(self, x, y, ground,size) -> None:
        super().__init__(x, y, ground, 40,size)
        self.power = 0
        pygame.draw.circle(self.skin,SKYBLUE,(self.size,self.size),self.size)
        pygame.draw.circle(self.skin,WHITE,(self.size,self.size),self.size*2/3)
    
    def attackDown(self):
        return super().attackDown()
    
    def attackCharging(self,screen):
        super().attackCharging(screen)
        self.power += 0.5 + (1 in self.effect.keys()) * 30
        Bullet(self,2,self.power).draw(screen)
        self.effectCounter(0.1)
    
    def attackUp(self):
        super().attackUp()
        if self.power > 0: bullets.append(Bullet(self,2,self.power))
        self.power = 0
    
    def displayItem(self,screen):
        write(screen,str(round(self.effect[1]*20)),(250,50),FONT,20,WHITE)
    
    @staticmethod
    def repr():
        return 'Tech'
    
    @staticmethod
    def info():
        return ['z키를 누르는동안 에너지를 충전하여 발사합니다.(atk : 1+α)','충전속도가 7배 빨라집니다.(50프레임)','40']


class Giant(Player):
    def __init__(self, x, y, ground,size) -> None:
        super().__init__(x, y, ground, 90,size*4/3)
        if size == PLAYER_SIZE : self.y = self.ground + self.size
        pygame.draw.circle(self.skin,ORANGE,(self.size,self.size),self.size)
        pygame.draw.circle(self.skin,YELLOW,(self.size,self.size),self.size*2/3)
    
    def attackDown(self):
        super().attackDown()
        if 1 in self.effect.keys():
            P = copy.copy(self)
            P.y += P.size*1/3
            bullets.append(Bullet(P,3))
            P.y -= P.size*2/3
            bullets.append(Bullet(P,3))
            self.effectCounter(1)
        else:
            bullets.append(Bullet(self,3))
        
    def attackCharging(self,screen):
        return super().attackCharging(screen)
    
    def attackUp(self):
        return super().attackUp()

    @staticmethod
    def repr():
        return 'Giant'
    
    @staticmethod
    def info():
        return ['강한 총알을 발사합니다.(atk : 2)','총알 2발 발사합니다.(atk : 2)(5×2발)','90 / 크기가 더 큽니다.']


class Gatling(Player):
    def __init__(self, x, y, ground, size) -> None:
        super().__init__(x, y, ground, 50, size)
        pygame.draw.circle(self.skin,SLIVER,(self.size,self.size),self.size)
        pygame.draw.circle(self.skin,BLACK,(self.size,self.size),self.size*2/3)

    def attackDown(self):
        super().attackDown()
        bullets.append(Bullet(self,0.6))
        
    def attackCharging(self,screen):
        super().attackUp()
        if 1 in self.effect.keys():
            bullets.append(Bullet(self,0.6))
            self.effectCounter(0.2)
    
    def attackUp(self):
        super().attackUp()
        bullets.append(Bullet(self,0.6))
    
    def displayItem(self, screen):
        write(screen,str(round(self.effect[1]*5)),(250,50),FONT,20,WHITE)

    @staticmethod
    def repr():
        return 'Gatling'

    @staticmethod
    def info():
        return ['은 총알을 발사합니다.(atk : 0.6)(z키를 땔 때 한 발 더 발사)','z키를 누르는 동안 총알이 발사됩니다.(atk : 0.6)(25발)','50']

class Subject(Player):
    def __init__(self, x, y, ground, size) -> None:
        super().__init__(x, y, ground, 10, size)
        pygame.draw.circle(self.skin,YELLOW,(self.size,self.size),self.size)
        pygame.draw.circle(self.skin,SLIVER,(self.size,self.size),self.size*2/3)

    def attackDown(self):
        super().attackDown()
        bullets.append(Bullet(self,100))
        
    def attackCharging(self,screen):
        super().attackUp()
    
    def attackUp(self):
        super().attackUp()
    
    def displayItem(self, screen):
        write(screen,str('-'),(250,50),FONT,20,WHITE)

    @staticmethod
    def repr():
        return '고인물'

    @staticmethod
    def info():
        return ['고인물을 위한 최소한의 투명총알을 드립니다!(1)','고인물에게 아이템이 필요한가요?','10 / 고인물이 과연 장애물에 맞을까요?']

class Item:
    def __init__(self,x,y,size,obstacle,type,shape = 0) -> None:
        self.x = x - obstacle.xSize/2
        self.y = -y + obstacle.ySize/2
        self.size = size
        self.shape = shape
        self.type = math.ceil(type)
        self.obstacle = obstacle
        self.img = pygame.transform.scale(ITEM_IMG, (self.size, self.size))
    
    def move(self,speed):
        self.x -= speed
    
    def eat(self,player):
        player.getEffect(self.type,5)
    
    def draw(self,screen):
        screen.blit(self.img,(self.x,self.y))
    
    def collision(self,player):
        if isCircleInCircle(self.x,-self.y,self.size,player.x,player.y,player.size):
            return True
        return False

class Obstacle:
    def __init__(self,x,y,size,hp,item = None,c = WHITE) -> None:
        self.x = x
        self.y = y
        self.xSize = size[0]
        self.ySize = size[1]
        self.hp = hp
        self.maxHP = hp
        self.c = c
        self.item = item
    
    def move(self,speed):
        self.x -= speed

    def draw(self,screen):
        pygame.draw.rect(screen,self.c,pygame.Rect(self.x-self.xSize,-self.y,self.xSize*2,2*self.ySize))

class Bullet:
    def __init__(self,player,type = 0,power = 0) -> None:
        self.x = player.x
        self.y = player.y
        self.type = type
        self.size = 5
        self.hp = 1
        if self.type == 1:
            self.hp = 3
            self.size = 7
        if self.type == 2:
            self.hp = int(math.log10(power)/math.log10(3))
            self.size = 3 + int(math.log10(power)/math.log10(3)) * 2
        if self.type == 3:
            self.hp = 2
            self.size = 10
        if 0 < self.type < 1:
            self.hp = self.type
            self.size = 3
    
    def move(self):
        self.x += 10
    
    def collision(self,obstacles):
        for i in range(len(obstacles)):
            obstacle = obstacles[i]
            left = obstacle.x - obstacle.xSize - self.size
            right = obstacle.x + obstacle.xSize + self.size
            down = obstacle.y - 2*obstacle.ySize - self.size
            up = obstacle.y - self.size
            if left < self.x < right and down < self.y < up:
                return i
            if isPointInCircle(left,up,self.x,self.y,self.size-1) or isPointInCircle(left,down,self.x,self.y,self.size-1) or isPointInCircle(right,up,self.x,self.y,self.size-1) or isPointInCircle(right,down,self.x,self.y,self.size-1) :
                return i
        return None

    def draw(self,screen):
        if self.type == 0:
            pygame.draw.circle(screen,WHITE,(self.x,-self.y),self.size)
        elif self.type == 1:
            pygame.draw.circle(screen,RED,(self.x,-self.y),self.size)
            pygame.draw.circle(screen,ORANGE,(self.x,-self.y),self.size-2)
        elif self.type == 2:
            pygame.draw.circle(screen,BLUE,(self.x,-self.y),self.size)
            pygame.draw.circle(screen,SKYBLUE,(self.x,-self.y),self.size*2/3)
        elif self.type == 3:
            pygame.draw.circle(screen,RED,(self.x,-self.y),self.size)
            pygame.draw.circle(screen,WHITE,(self.x,-self.y),self.size*2/3)
        elif self.type < 1:
            pygame.draw.circle(screen,SLIVER,(self.x,-self.y),self.size)

class PlayerHPBar:
    def __init__(self,player) -> None:
        self.player = player
    
    def draw(self,screen):
        pygame.draw.rect(screen,WHITE,pygame.Rect(10,10,200,30))
        width = (200-10) * self.player.hp/self.player.maxHP
        pygame.draw.rect(screen,RED,pygame.Rect(15,15,width,20))

class ObstacleHPBar:
    def __init__(self,obstacle) -> None:
        self.obstacle = obstacle
    
    def draw(self,screen):
        pygame.draw.rect(screen,WHITE,pygame.Rect(self.obstacle.x - 20,-(self.obstacle.y + self.obstacle.ySize - 10),40,10))
        width = (40-4) * self.obstacle.hp/self.obstacle.maxHP
        pygame.draw.rect(screen,RED,pygame.Rect(self.obstacle.x - 18,-(self.obstacle.y + self.obstacle.ySize - 12),width,6))

class Pattern:
    def __init__(self) -> None:
        pattern = open(os.path.join('.','assets','pattern.json'),'r')
        PATTERN = pattern.read()
        self.pattern = json.loads(PATTERN)
        temp = []
        for i in range(len(self.pattern)):
            temp.append([])
            for j in range(len(self.pattern[i])):
                nowPattern = self.pattern[i][j]
                if len(nowPattern)==5:
                    temp[i].append(Obstacle(SCREEN_WIDTH + 30,GROUND + nowPattern[2]*2 + nowPattern[0],(nowPattern[1],nowPattern[2]),nowPattern[3],nowPattern[4]))
                elif len(nowPattern)==6:
                    temp[i].append(Obstacle(SCREEN_WIDTH + 30,GROUND + nowPattern[2]*2 + nowPattern[0],(nowPattern[1],nowPattern[2]),nowPattern[3],nowPattern[4],nowPattern[5]))
                else:
                    temp[i].append(Obstacle(SCREEN_WIDTH + 30,GROUND + nowPattern[2]*2 + nowPattern[0],(nowPattern[1],nowPattern[2]),nowPattern[3]))
        self.pattern = temp

    def interpret(self,num):
        return map(copy.copy,self.pattern[num])

class BGRect:
    def __init__(self,pos,size,distance,angleSpeed) -> None:
        self.x = pos[0]
        self.y = pos[1]
        self.size = size
        self.color = WHITE
        self.distance = distance
        self.angleSpeed = angleSpeed

        self.skin = pygame.Surface((self.size,self.size),pygame.SRCALPHA)
        self.skin.set_alpha(70/400*self.distance)
        pygame.draw.rect(self.skin,WHITE,pygame.Rect(0,0,self.size,self.size),self.size//3)
        self.angle = 0

    def rotate(self,angle):
        self.angle += angle
    
    def move(self,speed):
        temp = self.angle
        self.angle = 0
        self.x -= speed / self.distance
        self.angle = temp
        self.rotate(self.angleSpeed)

    def draw(self,screen):
        skin = pygame.transform.rotate(self.skin, self.angle)
        self.skinRect = skin.get_rect(center = (self.x,self.y))
        screen.blit(skin, self.skinRect)

class TextInput:
    def __init__(self,x,y,fontSize,maxText,center = 0) -> None:
        self.x = x + center * fontSize * maxText/2
        self.y = y + center * fontSize/2
        self.center = center
        self.size = fontSize
        self.maxText = maxText
        self.text = ""
        self.click = False
        self.recentPressed = []
    
    def input(self):
        global capsLock

        pressed = pygame.key.get_pressed()
        click = []
        for i in range(len(pressed)):
            if pressed[i]: click.append(i)
        if len(click) != 0 :
            if pressed[pygame.K_TAB] and (not pygame.K_TAB in self.recentPressed):
                self.text += '    '
            elif pressed[pygame.K_CAPSLOCK] and (not pygame.K_CAPSLOCK in self.recentPressed):
                capsLock = not capsLock
            elif pressed[pygame.K_BACKSPACE] and (not pygame.K_BACKSPACE in self.recentPressed):
                if len(self.text) : self.text = self.text[:-1]
            elif pressed[pygame.K_SPACE] and (not pygame.K_SPACE in self.recentPressed):
                self.text += ' '
            else:
                shift = False
                for i in click:
                    if not i in self.recentPressed and pygame.K_SPACE<=i<=pygame.K_z:
                        shift = pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]
                        if capsLock : shift = not shift
                        shifted = i
                        if 97 <= i <= 122:
                            shifted -= shift * 32
                            self.text += pygame.key.name(shifted)
                        elif shift and pygame.key.name(i) in SHIFTED.keys():
                            shifted = SHIFTED[pygame.key.name(i)]
                            self.text += shifted
                        else:
                            self.text += pygame.key.name(shifted)
        if len(self.text) > self.maxText:
            self.text = self.text[:self.maxText]
        self.recentPressed = click.copy()
    
    def draw(self,screen,timer):
        pygame.draw.rect(screen,WHITE,pygame.Rect(self.x - self.size * self.maxText/3 - 5,self.y + self.size/2 + 5,self.size * self.maxText*2/3 + 10,self.size + 10))
        text = self.text
        if (timer//50)%2 : text+='|'
        write(screen,text,[5+ self.x - (not self.center) * self.size * self.maxText/3, 5+ self.y + (not self.center) * self.size/2],FONT,self.size,BLACK,1)

class Button:
    def __init__(self,x,y,size,img) -> None:
        self.x = x
        self.y = y
        self.preClick = False
        self.size = size
        IMG = pygame.image.load(os.path.join('.','assets','pictures',img))
        self.skin = pygame.transform.scale(IMG, (self.size, self.size))
    
    def setImg(self,img):
        IMG = pygame.image.load(os.path.join('.','assets','pictures',img))
        self.skin = pygame.transform.scale(IMG, (self.size, self.size))
    
    def clicked(self,mouse,**karg):
        x,y,clicked = mouse
        size = self.size/2
        if self.x - size <= x <= self.x + size and self.y - size <= y <= self.y + size and clicked:
            if not self.preClick:
                self.preClick = True
                return self.oriMethod(**karg)
        else:
            self.preClick = False

    
    def draw(self,screen):
        self.skinRect = self.skin.get_rect(center = (self.x,self.y))
        screen.blit(self.skin, self.skinRect)
    
    def oriMethod(self):
        pass

class VolumeButton(Button):
    def __init__(self, x, y) -> None:
        super().__init__(x, y, 50, 'volumeButton_1.png')
        self.volume = 1
    
    def oriMethod(self):
        self.volume += 1
        if self.volume > 3 : self.volume = 0
        self.setImg(f'volumeButton_{self.volume}.png')
        pygame.mixer.music.set_volume(0.25 * (3-self.volume))

class RankButton(Button):
    def __init__(self, x, y) -> None:
        super().__init__(x, y, 50, 'Ranking.png')
    
    def oriMethod(self,**option):
        if option:
            rankProcess(option['screen'],option['name'],option['score'],option['character'])
        return True

GROUND = -400

PLAYER_SIZE = 20
PLAYER_LIST = [Standard,Tech,Giant,Gatling,Subject]
PLAYER_NAME_LIST = list(map(lambda x: x.repr(),PLAYER_LIST))
