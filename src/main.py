VERSION = "0.1"

import pygame
from logic import Game
from scene import SceneManager
from scenes.configuration import ConfigurationScene

# Setup do pygame
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Deep Sea")
clock = pygame.time.Clock()

# Deixa o objeto do jogo acessível como variável antes de ser configurado
game = Game()
game.running = True

def event_handler() -> list[pygame.event.Event]:
  """
    Gerencia os eventos padrões e retorna eles para\n
    serem usados por outros componentes.
  """
  global game
  global screen
  
  # Eventos do sistema
  events = pygame.event.get()
  for event in events:
    # O evento pygame.QUIT é ativo quando o usuário clica no botão de fechar janela
    if event.type == pygame.QUIT:
      game.running = False
 
  return events

scene_manager = SceneManager(game, screen)
scene_manager.add_scene(ConfigurationScene())

while game.running:
    events = event_handler()
    # Faz atualizações de lógica aqui

    # Lógica de renderização
    scene_manager.render(events)

    # Usa o flip() no display para atualizar a tela
    pygame.display.flip()

    clock.tick(60)  # Limita o fps para 60

pygame.quit()