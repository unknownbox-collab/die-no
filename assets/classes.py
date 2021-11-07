import pygame,sys,math,time,copy,datetime,json,random
import numpy as np

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500

WHITE = (255, 255, 255)
ORANGE = (255, 127, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
BLUE = (0,0,255)
RED = (255,0,0)
SKYBLUE = (135, 206, 235)
SPEED = 5

START_SCENE = 0
CHARACTER_CHOOSE_SCENE = 1
GAME_SCENE = 2
DIED_PROCESSING = 3
DIED_SCENE = 4

ITEM_IMG = pygame.image.load('./assets/pictures/item.png')    
ENERGY_EFFECT_IMG = pygame.image.load('./assets/pictures/EneryEffect.png')
ENERGY_EFFECT_IMG = pygame.transform.scale(ENERGY_EFFECT_IMG, (40, 40))

bullets = []
BGRects = []

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

class Item:
    def __init__(self,x,y,size,obstacle,type,shape = 0) -> None:
        self.x = x - obstacle.xSize/2
        self.y = -y + obstacle.ySize/2
        self.size = size
        self.shape = shape
        self.type = math.ceil(type)
        self.obstacle = obstacle
        self.img = pygame.transform.scale(ITEM_IMG, (self.size, self.size))
    
    def move(self):
        self.x -= SPEED
    
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
    
    def move(self):
        self.x -= SPEED

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
        pygame.draw.rect(screen,WHITE,pygame.Rect(self.obstacle.x - 20,-self.obstacle.y - self.obstacle.ySize + 10,40,10))
        width = (40-4) * self.obstacle.hp/self.obstacle.maxHP
        pygame.draw.rect(screen,RED,pygame.Rect(self.obstacle.x - 18,-self.obstacle.y - self.obstacle.ySize + 12,width,6))

class Pattern:
    def __init__(self) -> None:
        pattern = open("./assets/pattern.json",'r')
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

GROUND = -400

PLAYER_SIZE = 20
PLAYER_LIST = [Standard,Tech,Giant]
PLAYER_NAME_LIST = ['Standard','Tech','Giant']
