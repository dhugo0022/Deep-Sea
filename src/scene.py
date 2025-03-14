import pygame
from typing import Dict
from logic import Game
import sys
from libs.components import ComponentManager
from libs.utils import load_music

# Tanto os erros de renderização da cena, quanto do
# SceneManager vão acabar o programa utilizando:
# sys.exit(...). Isso é para mostrar logo de cara
# que há um erro crítico.

class Scene:

  def __init__(
      self,
      name: str,
      shared_state: Dict[str, str] = {},
      soundtrack_filename: list[str] | None = None
    ):
      # Esse parâmetros vão ser injetados pela SceneManager
    # que vai controlar essa cena
    self.screen: pygame.surface.Surface | None = None
    self.game: Game | None = None

    # Indica se a classe já foi inicializada
    self.is_injected = False

    # Indica se a cena já foi configurada
    self.is_setup = False

    self.name = name
    self.shared_state = shared_state

    if soundtrack_filename:
      load_music(*soundtrack_filename)
      self.has_soundtrack = True
    else:
      self.has_soundtrack = False
    self.component_manager = ComponentManager()

  def play_soundtrack(self):
    if self.has_soundtrack:
      pygame.mixer.music.play(-1) # Dá play em loop

  def stop_soundtrack(self):
    if self.has_soundtrack:
      pygame.mixer.music.stop()

  def is_soundtrack_playing(self) -> bool:
    result = pygame.mixer.music.get_busy()
    return result

  def inject(self, manager: "SceneManager", game: Game, screen: pygame.surface.Surface):
    """
      Função utilizada para injetar as dependencias padrões necessárias\n
      que a cena possa vir a utilizar.
    """
    if not self.is_injected:
      self.manager = manager
      self.game = game
      self.screen = screen
      self.is_injected = True

  def setup(self):
    """
      Função utilizada para configurar todos os recursos da cena.\n
      Essa função só é executada uma única vez na primeira vez que\n
      a cena é pedida para ser renderizada.
    """
    pass

  def draw(self):
    """
      Função utilizada para renderizar todos os elementos da cena.\n
      Essa função é chamada a cada frame.
    """
    if not self.is_injected:
      sys.exit("Você precisa injetar a cena antes de renderizar.")
      return

    if not self.is_setup:
      sys.exit("Você precisa configurar a cena antes de renderizar.")
    return

class SceneManager:

  def __init__(self, game: Game, screen: pygame.surface.Surface):
    self.game = game
    self.screen = screen
    self.scenes: dict[str, Scene] = {}
    self.current_scene = None

  def has_current_scene(self):
    return self.current_scene is not None

  def add_scene(self, scene: Scene, switch: bool = True):
    if scene.name in self.scenes:
      sys.exit(f"Você já possui uma cena com esse nome: {scene.name}.")
      return

    # Injeta os objetos game e screen na cena
    scene.inject(self, self.game, self.screen)

    self.scenes[scene.name] = scene
    if switch:
      if self.current_scene is None:
        self.current_scene = scene
      else:
        self.screen.fill('black')
        self.current_scene = scene

  def change_to_scene(self, scene_name: str):
    if scene_name not in self.scenes:
      sys.exit(f"Você está tentando mudar para uma cena que não existe: {scene_name}.")
      return

    if self.current_scene and self.current_scene.name == scene_name:
      sys.exit("Você não pode mudar para a mesma cena!")
      return

    if self.current_scene == None:
        self.current_scene = self.scenes[scene_name]
    else:
      self.current_scene.stop_soundtrack()
      self.screen.fill('black')
      self.current_scene = self.scenes[scene_name]
      if self.current_scene.is_setup:
        self.current_scene.play_soundtrack()


  def delete_scene(self, scene_name: str):
    if self.scenes[scene_name] == self.current_scene:
      sys.exit("Você não pode deletar uma cena que está sendo usada!")
      return

    try:
      self.scenes[scene_name].stop_soundtrack()
      del self.scenes[scene_name]
    except KeyError as _:
      sys.exit(f"Você está tentando deletar uma cena que não existe: {scene_name}.")

  def render(self, events: list[pygame.event.Event]):
    if self.current_scene:
      if not self.current_scene.is_setup:
        self.current_scene.setup()
        self.current_scene.is_setup = True
        self.current_scene.play_soundtrack()

      self.current_scene.draw()
      self.current_scene.component_manager.listen(events)

  def play_soundtrack(self):
    if self.has_current_scene():
      self.current_scene.play_soundtrack() # type: ignore

  def stop_soundtrack(self):
    if self.has_current_scene():
      self.current_scene.stop_soundtrack() # type: ignore

  def is_soundtrack_playing(self) -> bool:
    if self.has_current_scene():
      return self.current_scene.is_soundtrack_playing() # type: ignore

    return False
