import pygame
import random
import const
import NeuralNetwork
import time
from pygame.locals import *
from threading import Thread

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 800
SPEED = 10
GRAVITY = 1
GAME_SPEED = 10

GROUND_WIDTH = 2 * SCREEN_WIDTH
GROUND_HEIGHT = 100
PIPE_WIDTH = 80
PIPE_HEIGHT = 700 

PIPE_GAP = 150

AMOUNT_HIDDEN = 3
AMOUNT_NEURON_INPUT = 4
AMOUNT_NEURON_HIDDEN = 6
AMOUNT_NEURON_OUTPUT = 1

pipesList = []

class Bird(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.score = 0

        self.images = [pygame.image.load(const.BLUEBIRD_TOP).convert_alpha(),
                       pygame.image.load(const.BLUEBIRD_MID).convert_alpha(),
                       pygame.image.load(const.BLUEBIRD_BOT).convert_alpha()]

        self.speed = SPEED
        self.currentImage = 0
        self.image = pygame.image.load(const.BLUEBIRD_TOP).convert_alpha()

        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDTH / 2
        self.rect[1] = SCREEN_HEIGHT / 2

        self.brain = NeuralNetwork.NeuralNetwork(AMOUNT_HIDDEN, AMOUNT_NEURON_INPUT, AMOUNT_NEURON_HIDDEN, AMOUNT_NEURON_OUTPUT)

    def update(self):
        self.currentImage = (self.currentImage + 1) % 3
        self.image = self.images[ self.currentImage ]

        self.speed += GRAVITY

        # Update height
        self.rect[1] += self.speed

    def bump(self):
        self.speed = -SPEED

    def getDistHorizontalPipe(self):
        return self.rect[0] - pipesList[0][0].rect[0]

    def getDistVerticalPipe(self):
        center = (pipesList[0][1].rect[1] + 700) + PIPE_GAP/2
        return self.rect[1] - center

    def getInputs(self):
        return [self.getDistHorizontalPipe(), self.getDistVerticalPipe(), GAME_SPEED, PIPE_GAP]

class Pipe(pygame.sprite.Sprite):

    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load(const.CANO).convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDTH, PIPE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect[0] -= GAME_SPEED

class Ground(pygame.sprite.Sprite):

    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load(const.BASE).convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDTH, GROUND_HEIGHT))

        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT

    def update(self):
        self.rect[0] -= GAME_SPEED

def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])

def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return (pipe, pipe_inverted)

def getBestBird(birds):
    bestBird = birds[0]
    for bird in birds:
        if bestBird.score < bird.score:
            bestBird = bird

    return bestBird

def changeWeights(bird):
    for n in range(0, AMOUNT_HIDDEN):
        for k in range(0, AMOUNT_NEURON_HIDDEN):
            if n == 0:
                for i in range(0, AMOUNT_NEURON_INPUT):
                    bird.brain.hiddenLayerList[n].neuronList[k].weights[i] = random.randrange(-1000, 1000)
            else:
                for i in range(0, AMOUNT_NEURON_HIDDEN):
                    bird.brain.hiddenLayerList[n].neuronList[k].weights[i] = random.randrange(-1000, 1000)

    for j in range(0, AMOUNT_NEURON_OUTPUT):
        for l in range(0, AMOUNT_NEURON_HIDDEN):
            bird.brain.outputLayer.neuronList[j].weights[l] = random.randrange(-1000, 1000)

def main():
    birds = []
    birdsCollision = []
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    BACKGROUND = pygame.image.load(const.BACKGROUND)
    BACKGROUND = pygame.transform.scale(BACKGROUND, (SCREEN_WIDTH, SCREEN_HEIGHT))

    bird_group = pygame.sprite.Group()
    for n in range(0, 10):
        bird = Bird()
        birds.append(bird)
        bird_group.add(bird)
        changeWeights(bird)

    ground_group = pygame.sprite.Group()
    for i in range(2):
        ground = Ground(GROUND_WIDTH * i)
        ground_group.add(ground)

    pipe_group = pygame.sprite.Group()

    pipes = get_random_pipes(600)
    pipe_group.add(pipes[0])
    pipe_group.add(pipes[1])

    listaPipe = [pipes[0], pipes[1]]
    pipesList.append(listaPipe)

    clock = pygame.time.Clock()
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()

            # if event.type == KEYDOWN:
            #     if event.key == K_SPACE:
            #         bird.bump()

        # Executação Rede Neural
        for bird in birds:
            sensorList = bird.getInputs()

            bird.brain.addNeuronInput(sensorList)
            bird.brain.calculateOutput()
            output = bird.brain.getOutput()

            if output[0] == 0:
                bird.bump()

        screen.blit(BACKGROUND, (0, 0))

        if is_off_screen(ground_group.sprites()[0]):
            ground_group.remove(ground_group.sprites()[0])

            new_ground = Ground(GROUND_WIDTH - 20)
            ground_group.add(new_ground)

        # Criar novos Pipes quando melhor Bird passar por eles
        bird = getBestBird(birds)
        if bird.getDistHorizontalPipe() == 0:
            pipes = get_random_pipes(SCREEN_WIDTH + 100)
            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])

            pipesList.remove(pipesList[0])
            pipesList.append([pipes[0], pipes[1]])

        # Remover quando tiver fora da tela
        if is_off_screen(pipe_group.sprites()[0]):
            pipe_group.remove(pipe_group.sprites()[0])
            pipe_group.remove(pipe_group.sprites()[0])

        bird_group.update()
        ground_group.update()
        pipe_group.update()

        bird_group.draw(screen)
        pipe_group.draw(screen)
        ground_group.draw(screen)

        pygame.display.update()

        # Checa colisões remove do sprite.group e birds, adiciona em birdsCollision
        birdCollisionGround = pygame.sprite.groupcollide(bird_group, ground_group, True, False, pygame.sprite.collide_mask)
        if birdCollisionGround:
            birdsColl = birdCollisionGround.keys()
            for bird in birdsColl:
                # birds.remove(bird)
                birdsCollision.append(bird)
        birdCollisionPipe = pygame.sprite.groupcollide(bird_group, pipe_group, True, False, pygame.sprite.collide_mask)
        if birdCollisionPipe:
            birdsColl = birdCollisionPipe.keys()
            for bird in birdsColl:
                # birds.remove(bird)
                birdsCollision.append(bird)

        # if len(birds) == 0:
        #     pygame.quit()
        #     quit()
        #     break

        for bird in birds:
            bird.score += 1


if __name__ == '__main__':
    main()