import os
import operator
import sys
import pygame
import csv
from pathlib import Path
from itertools import product
from pygame.locals import *

srcdir = Path(__file__).resolve().parent
os.chdir(srcdir)

def csv_to_lists(file):
	with open(file, encoding="utf-8") as f:
		lists = list(csv.reader(f, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True))
	c = int(lists[0][0])
	tesu = int(lists[0][1])
	lists = lists[1:]
	return c, tesu, lists


class Sprite(pygame.sprite.Sprite):

	def __init__(self, img, pos):
		pygame.sprite.Sprite.__init__(self, self.containers)
		self.image = pygame.image.load(img).convert_alpha()
		self.rect = self.image.get_rect()
		self.rect.topleft = pos


class Block(Sprite):

	def __init__(self, pos):
		Sprite.__init__(self, "img/block2.png", pos)


class Player(Sprite):

	def __init__(self, img, pos, blocks):
		Sprite.__init__(self, img, pos)
		self.blocks = blocks
		self.direction = ""
		self.d_cache = "d"
		self.speed = 32

	def update_(self):
		if self.direction == "u":
			vy = -self.speed
			collision = self.coll_block(0, vy)
			if collision is None:
				self.rect.y += vy
			else:
				self.rect.midtop = collision.midbottom
				self.direction = ""

		elif self.direction == "d":
			vy = self.speed
			collision = self.coll_block(0, vy)
			if collision is None:
				self.rect.y += vy
			else:
				self.rect.midbottom = collision.midtop
				self.direction = ""

		elif self.direction == "r":
			vx = self.speed
			collision = self.coll_block(vx, 0)
			if collision is None:
				self.rect.x += vx
			else:
				self.rect.midright = collision.midleft
				self.direction = ""

		elif self.direction == "l":
			vx = -self.speed
			collision = self.coll_block(vx, 0)
			if collision is None:
				self.rect.x += vx
			else:
				self.rect.midleft = collision.midright
				self.direction = ""

	def coll_block(self, vx, vy):
		for i in self.blocks:
			if Rect(self.rect.x + vx, self.rect.y + vy, *self.rect.size).colliderect(i.rect):
				if i != self:
					return i.rect
		return None


class Parent(Player):

	def __init__(self, pos, blocks, players, goals, c, tesu):
		Player.__init__(self, "img/parent.png", pos, blocks)
		self.restart_pos = pos
		self.players = players
		self.goals = goals
		self.goals_len = len(goals)
		self.arrow_keys = [K_UP, K_DOWN, K_RIGHT, K_LEFT]
		self.direction_list = ["u", "d", "r", "l"]
		self.key_direction_dict = {k: v for k, v in zip(self.arrow_keys, self.direction_list)}
		self.child_count_init = self.child_count = c
		self.all_tesu_init = self.all_tesu = tesu + c
		self.dead = False

	def events(self, key):
		if self.key_available() and self.all_tesu > 0:
			if key in [K_UP, K_DOWN, K_RIGHT, K_LEFT]:
				self.d_cache = self.direction = self.key_direction_dict[key]
				self.set_direction(self.direction)
				self.all_tesu -= 1
			elif key == K_SPACE:
				vx = vy = 0
				if self.d_cache == "u":
					vy = 32
				elif self.d_cache == "d":
					vy = -32
				elif self.d_cache == "r":
					vx = -32
				elif self.d_cache == "l":
					vx = 32
				child_rect = self.coll_block(vx, vy)
				if child_rect is None:
					if self.child_count > 0:
						Child((self.rect.left + vx, self.rect.top + vy), self.blocks)
						self.child_count -= 1
						self.all_tesu -= 1
		if key == K_r:
			self.restart()

	def key_available(self):
		return {c.direction for c in self.players} == {""}

	def set_direction(self, d):
		for c in self.players:
			c.direction = d

	def is_goal(self):
		g_s = set()
		for g, p in product(self.goals, self.players):
			if p.rect.colliderect(g.rect):
				g_s.add(g)
		return len(g_s) == self.goals_len

	def restart(self):
		for p in self.players:
			if p != self:
				p.kill()

		self.direction = ""
		self.d_cache = "d"

		self.rect.topleft = self.restart_pos
		self.child_count = self.child_count_init
		self.all_tesu = self.all_tesu_init
		self.dead = False

	def update(self):
		direction = ""
		for d in {c.direction for c in self.players} - {""}:
			direction = d

		if direction == "":
			if self.all_tesu == 0 and not self.is_goal():
				self.dead = True
			return False
		elif direction == "u":
			ys = [(p, p.rect.y) for p in self.players]
			pls = sorted(ys, key=operator.itemgetter(1))
		elif direction == "d":
			ys = [(p, p.rect.y) for p in self.players]
			pls = sorted(ys, key=operator.itemgetter(1), reverse=True)
		elif direction == "r":
			ys = [(p, p.rect.x) for p in self.players]
			pls = sorted(ys, key=operator.itemgetter(1), reverse=True)
		elif direction == "l":
			ys = [(p, p.rect.x) for p in self.players]
			pls = sorted(ys, key=operator.itemgetter(1))

		for p in pls:
			p[0].update_()


class Child(Player):

	def __init__(self, pos, blocks):
		Player.__init__(self, "img/child.png", pos, blocks)

	def update(self):
		pass


class Goal(Sprite):

	def __init__(self, pos):
		Sprite.__init__(self, "img/goal1.png", pos)
		self.count = 0
		self.fps = 1

	def update(self):
		if self.count == self.fps * 7:
			self.image = pygame.image.load("img/goal8.png").convert_alpha()
			self.count = 0
		elif self.count == self.fps * 6:
			self.image = pygame.image.load("img/goal7.png").convert_alpha()
		elif self.count == self.fps * 5:
			self.image = pygame.image.load("img/goal6.png").convert_alpha()
		elif self.count == self.fps * 4:
			self.image = pygame.image.load("img/goal5.png").convert_alpha()
		elif self.count == self.fps * 3:
			self.image = pygame.image.load("img/goal4.png").convert_alpha()
		elif self.count == self.fps * 2:
			self.image = pygame.image.load("img/goal3.png").convert_alpha()
		elif self.count == self.fps:
			self.image = pygame.image.load("img/goal2.png").convert_alpha()
		self.count += 1


class Map:

	def __init__(self, stage, wid, hei):
		self.all = pygame.sprite.RenderUpdates()
		self.blocks = pygame.sprite.Group()
		self.players = pygame.sprite.Group()
		self.goals = pygame.sprite.Group()
		Block.containers = self.all, self.blocks
		Parent.containers = self.all, self.blocks, self.players
		Child.containers = self.all, self.blocks, self.players
		Goal.containers = self.all, self.goals
		self.stage = stage
		self.GS = 32
		self.load()
		self.surface = pygame.Surface(
			(self.row * self.GS, self.col * self.GS)).convert_alpha()
		surface_rect = self.surface.get_rect()
		left = (wid - surface_rect.width) / 2
		top = (hei - surface_rect.height) / 2
		self.surface_topleft = (left, top)
		self.surface.set_colorkey((255, 0, 0))

	def draw(self):
		self.surface.fill((255, 255, 255))
		self.all.draw(self.surface)

	def load(self):
		c, tesu, self.map = csv_to_lists(f"maps/stage-{self.stage}.csv")
		self.row, self.col = len(self.map[0]), len(self.map)
		self.height = self.col * self.GS
		self.width = self.row * self.GS
		for x, y in product(range(self.row), range(self.col)):
			if self.map[y][x] == "B":
				Block((x * self.GS, y * self.GS))
			elif self.map[y][x] == "G":
				Goal((x * self.GS, y * self.GS))
		for x, y in product(range(self.row), range(self.col)):
			if self.map[y][x] == "P":
				self.parent = Parent((x * self.GS, y * self.GS), self.blocks, self.players, self.goals, c, tesu)


class Game:

	def __init__(self, stage):
		pygame.init()
		pygame.mixer.init()
		self.wid, self.hei = 600, 500
		self.base = Rect(0, 0, self.wid, self.hei)
		self.screen = pygame.display.set_mode(self.base.size)
		self.stage = stage

		self.font = pygame.font.Font("font/UDDigiKyokashoN-B.ttc", 20)
		self.font_start = pygame.font.Font("font/UDDigiKyokashoN-B.ttc", 25)
		self.font_big = pygame.font.SysFont("font/UDDigiKyokashoN-B.ttc", 80)
		self.font_end = pygame.font.SysFont("font/OCRB.TTF", 25)
		self.child_img = pygame.transform.scale(pygame.image.load("img/child.png"), (16, 16)).convert_alpha()
		self.fps = 20
		self.is_goal = False
		self.is_gaming = False
		self.is_starting = True
		self.init_config()
		self.surf_alpha = 250
		
		clock = pygame.time.Clock()
		while True:
			if self.is_starting:
				self.screen.fill((0, 0, 0))
				self.screen.blit(self.font_big.render("iPPO", True, (140, 255, 255)), (230, 90))
				self.screen.blit(self.font_start.render("PRESS ENTER TO START", True, (255, 255, 255)), (180, 180))
				pygame.display.update()
				self.satrt_events()
			elif self.is_gaming:
				clock.tick(self.fps)
				self.map.all.update()
				if self.map.parent.is_goal():
					self.is_goal = True
				if self.is_goal:
					self.map.surface.set_alpha(self.surf_alpha)
					self.surf_alpha -= 10
					if self.surf_alpha == 0:
						self.surf_alpha = 250
						self.is_goal = False
						self.next_stage()
						continue
				self.draw()
				pygame.display.update()
				self.game_events()
			else:
				self.screen.fill((0, 0, 0))
				self.screen.blit(self.font_big.render("Clear", True, (255, 140, 255)), (200, 80))
				self.screen.blit(self.font_end.render("Created by: ForestSep", True, (255, 255, 255)), (150, 200))
				self.screen.blit(self.font_end.render("Language: Python", True, (255, 255, 255)), (150, 230))
				self.screen.blit(self.font_end.render("For the Eikou Gakuen Festival", True, (255, 255, 255)), (220, 300))
				pygame.display.update()
				self.events()

	def init_config(self):
		pygame.display.set_caption(f"iPPO ステージ{self.stage}")
		self.map = Map(self.stage, self.wid, self.hei)
		self.surface_topleft = self.map.surface_topleft

	def next_stage(self):
		self.stage += 1
		if Path(f"maps/stage-{self.stage}.csv").exists():
			self.map = Map(self.stage, self.wid, self.hei)
			self.init_config()
			self.screen.fill((0, 0, 0))
		else:
			self.is_gaming = False


	def draw(self):
		self.screen.fill((0, 0, 0))
		self.map.draw()
		self.screen.blit(self.map.surface, self.surface_topleft)
		for i in range(self.map.parent.child_count):
			self.screen.blit(self.child_img, (20 * i + 10, 10))
		self.screen.blit(self.font.render(f"あと{self.map.parent.all_tesu}手", True, (255, 255, 255)), (10, 30))

		if self.map.parent.dead and not self.is_goal:
			self.screen.blit(self.font.render(f"再開するにはRキーを押してください", True, (255, 0, 0)), (150, 20))


	def events(self):
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == KEYDOWN:
				self.map.parent.events(event.key)

	def game_events(self):
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == KEYDOWN:
				self.map.parent.events(event.key)
	def satrt_events(self):
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == KEYDOWN:
				if event.key == K_RETURN:
					self.is_starting = False
					self.is_gaming = True



Game(1)
