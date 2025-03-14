from libs.components import Alignment, Component, SpriteSource, Text, align_rect, SpriteButton, AnimatedImage
from logic import Game, Player, Difficulty, Direction, EntityType
import pygame
import sys
from scene import SceneManager
from libs.utils import AnimCursor, Anim, MOUSE_LEFT_BUTTON, load_sound
import random
from timeit import default_timer as timer
import math

class Map(Component):
  """
    Cria o mapa do jogo
  """

  def __init__(
    self,
    position: tuple[int, int],
    tile_source: SpriteSource,
    selected_tile_source: SpriteSource,
    players_source: SpriteSource,
    game: Game,
    gap: int = 0,
    alignment: Alignment = Alignment.CENTER
  ):
    super().__init__(position, alignment)
    self._interactable = True

    self.tile_source = tile_source
    if not tile_source.get_real_sprite_width() == tile_source.get_real_sprite_height():
      sys.exit(f"Para criar o mapa, o sprite do piso tem que ser um quadrado. As dimensões dele não são iguais: ({self.tile_source.get_real_sprite_width()}, {self.tile_source.get_real_sprite_height()}).")
      return

    self.selected_tile_source = selected_tile_source
    if not selected_tile_source.get_real_sprite_width() == selected_tile_source.get_real_sprite_height():
      sys.exit(f"Para criar o mapa, o sprite selecionado do piso tem que ser um quadrado. As dimensões dele não são iguais: ({self.selected_tile_source.get_real_sprite_width()}, {self.selected_tile_source.get_real_sprite_height()}).")
      return

    self.players_source = players_source

    self.game = game
    self.gap = gap

    # Carrega os sons do botão
    self.bomb_dying_sound = load_sound("components", "bomb_dying.ogg")

    self.__setup()

  def __generate_map_surface(self) -> pygame.Surface:
    """
      Gera a superfície padrão do mapa
    """

    map_size = self.game.map_size

    # É usado somente a largura pois ela tem o mesmo tamanho da altura
    sprite_size = self.tile_source.get_real_sprite_width()

    # Equação: Ts = n(s+g) - g
    # Ela vai dar o tamanho do mapa, em uma direção, baseado no número de pisos e no espaço de sobra("gap")
    # Ts("total size") = tamanho do mapa, n("number of tiles") = número de pisos , s("size") = tamanho do sprite, g("gap") = espaço de sobra
    map_surface_size = (map_size * (sprite_size + self.gap) - self.gap, map_size * (sprite_size + self.gap) - self.gap)

    # Ao adicionar a flag SCRALPHA, o pygame nos permite a fazer blit levando em conta
    # a opacidade do sprite
    map_surface = pygame.Surface(map_surface_size, pygame.SRCALPHA)

    depth = 0
    for x in range(0, map_size):
      for y in range(0, map_size):
        x_gap = self.gap * x
        y_gap = self.gap * y
        tile_position = (x * sprite_size + x_gap, y * sprite_size + y_gap)
        tile_surface = self.tile_source.sprites[depth].copy()

        tile_surface_rect = tile_surface.get_rect()
        tile_surface_rect.center = (tile_surface.get_width() // 2, tile_surface.get_height() // 2)
        map_surface.blit(tile_surface, tile_position)

      depth += 2 if map_size == 15 else 1

    return map_surface

  def get_map_size(self) -> tuple[int, int]:
    return self.map_object.get_size()

  def __setup(self):
    self.default_map_object = self.__generate_map_surface()
    self.map_object = self.default_map_object.copy()
    self.map_object_rect = self.map_object.get_rect()
    align_rect(self.map_object_rect, self.alignment, self.position)
    self.request_map_update()
    # Para o submarino
    self.game.map_object_rect_width = self.map_object_rect.width
    self.game.map_object_rect_left = self.map_object_rect.left

  def request_map_update(self) -> pygame.Surface:
    """
      Atualiza, se precisar, a superfície do mapa com bombas, passos, etc.
    """

    map_size = self.game.map_size
    sprite_size = self.tile_source.get_real_sprite_width()

    map_object_copy = self.default_map_object.copy()

    depth = 0
    for x in range(0, map_size):
      for y in range(0, map_size):
        entity_at = self.game.entity_at((x, y))
        possible_player_at = self.game.get_player_at((x, y))

        if possible_player_at == None and entity_at == None and not self.game.has_current_possible_steps():
          continue

        x_gap = self.gap * x
        y_gap = self.gap * y
        tile_position = (x * sprite_size + x_gap, y * sprite_size + y_gap)

        # Caso tenha um passo para aquele lugar, mostra o caminho de uma maneira diferente
        real_tile_source = self.selected_tile_source if self.game.is_in_current_possible_steps((x, y)) else self.tile_source
        tile_surface = real_tile_source.sprites[depth].copy()

        tile_surface_rect = tile_surface.get_rect()
        tile_surface_rect.center = (tile_surface.get_width() // 2, tile_surface.get_height() // 2)

        # Coloca a entidade no quadrado
        if entity_at != None:
          entity_identifier = pygame.transform.scale_by(entity_at.identifier, (sprite_size * 0.80 / entity_at.identifier.get_width(), sprite_size * 0.80 / entity_at.identifier.get_height()))

          entity_identifier_rect = entity_identifier.get_rect()
          entity_identifier_rect.center = tile_surface_rect.center

          tile_surface.blit(entity_identifier, entity_identifier_rect.topleft)


        # Colocar o player separado pra uma maior facilidade de manter o tesouro
        # no mesmo lugar caso o player não pegue
        if possible_player_at != None:
          player_identifier = pygame.transform.scale_by(possible_player_at.identifier, (sprite_size * 0.80 / possible_player_at.identifier.get_width(), sprite_size * 0.80 / possible_player_at.identifier.get_height()))

          player_identifier_rect = player_identifier.get_rect()
          player_identifier_rect.center = tile_surface_rect.center

          tile_surface.blit(player_identifier, player_identifier_rect.topleft)


        map_object_copy.blit(tile_surface, tile_position)

      depth += 2 if map_size == 15 else 1

    self.map_object = map_object_copy

  def is_mouse_within_bounding_box(self, mouse_pos):
    return self.map_object_rect.collidepoint(mouse_pos)

  def draw(self, screen: pygame.Surface):
    self.request_map_update()
    screen.blit(self.map_object, self.map_object_rect.topleft)

  def listen(self, event: pygame.event.Event):
    if not (event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_LEFT_BUTTON):
      return

    # Isso nós permite dizer que qualquer clique vai estar, pelo menos, dentro da área do mapa
    if not self.is_mouse_within_bounding_box(event.pos):
      return

    # Se ainda está no sorteio de primeiro jogador ou está no sorteio de dados
    if not self.game.first_player_sorted:
      return

    if (not self.game.need_player_activation and not self.game.need_player_action) or self.game.need_player_decision or self.game.need_submarine_option or self.game.game_has_ended:
      return

    map_width, map_height = self.map_object_rect.size
    # Por algum motivo, na desestruturação, o "topleft" do rect tá com a ordem invertida
    # então é preciso separar a definição de variável, ao invés de fazer por desestruturação.
    map_top  = self.map_object_rect.top
    map_left = self.map_object_rect.left
    # Posição do mouse
    pos_x, pos_y = event.pos
    map_size = self.game.map_size

    # Isso dá o resultado em índice 0 até (map-size - 1)
    # Essa posição não leva em conta a separação de gaps. Então, se for clicado entre os gaps
    # o click ainda pode ser processado.
    x = (map_size * (pos_x - map_left) // map_width)
    y = (map_size * (pos_y - map_top) // map_height)

    # TODO: se o player ir para uma bomba, ele vai sair do estado de playing
    # TODO: e vai ficar desclassificado.
    player = self.game.get_current_player_of_turn()

    # Se o jogador clicado precisar a primeira interação
    if self.game.need_player_activation:
      # Verifica se está o atual jogador está interagindo com ele mesmo #
      if self.game.is_player_at(player, (x, y)):
        # Essa parte, quando o jogador estiver no submarino, vai ser tratada
        # dentro da classe do submarino. Essa aqui só dá conta de quando o
        # jogador já estiver no mapa.
        self.game.need_player_activation = False
        self.game.need_player_action = True

        self.game.current_possible_steps = self.game.calculate_possible_steps(
          (x, y),
          self.game.sorted_dice_number,
        )

      return


    ## Fora da interação pessoal ##

    # Se o jogador precisar realizar ação de andar
    if self.game.need_player_action:
      # Se ele clicou em si mesmo:
      if self.game.is_player_at(player, (x, y)):
        # passa a vez
        self.game.need_player_action = False
        self.game.clear_current_possible_steps()
        self.game.go_to_next_player_turn()
        return

      # Se não há nenhum passo no local clicado, não há nada a fazer.
      if not self.game.is_in_current_possible_steps((x, y)):
        return

      clicked_step = (x, y)
      bomb_pos = self.game.get_first_bomb_in_the_way(clicked_step)

      # Pega a entidade antes de mudar o jogador pra lá
      player.position = clicked_step
      player.has_already_left_the_submarine = True
      entity_at_clicked_step = self.game.entity_at(clicked_step)
      self.game.need_player_action = False
      self.game.clear_current_possible_steps()

      if bomb_pos != None:
        # Deixa o jogador desqualificado da partida
        bomb_x, bomb_y = bomb_pos
        self.game.map[bomb_x][bomb_y] = None # Tira a bomba de lá
        player.position = (-1, -1)
        player.playing = False
        player.disqualified = True
        self.game.go_to_next_player_turn()
        self.bomb_dying_sound.play()

        # TODO: Verificar se todo mundo morreu e acabar a partida
        return

      if entity_at_clicked_step == None:
        # Se não há nada no local clicado, não há nada a fazer.
        # Só passa para o próximo jogador
        self.game.go_to_next_player_turn()
        return

      if entity_at_clicked_step.type == EntityType.TREASURE:
        # Abre o menu para caso o jogador queira pegar o tesouro ou não
        self.game.need_player_decision = True
        self.game.treasure_being_taken = entity_at_clicked_step
        return


class PlayerBoard(Component):
  """
    Criar um quadro com as informações do jogador na partida.
  """

  def __init__(
    self,
    position: tuple[int, int],
    sprite_source: SpriteSource,
    player: Player,
    game: Game,
    alignment: Alignment = Alignment.CENTER,
  ):
    super().__init__(position, alignment)
    self.sprite_source = sprite_source
    self.player = player
    self.game = game

    self.__setup()

  def __setup(self):
    self.board_object = self.sprite_source.sprites[self.player.player_id - 1]
    self.board_object_rect = self.board_object.get_rect()

    align_rect(self.board_object_rect, self.alignment, self.position)

    board_w, board_h = self.board_object.get_size()
    self.player_name_text = Text(
      (board_w * 0.20, board_h * 0.30),
      f"Jogador {self.player.player_id}",
      24,
      "white",
      alignment=Alignment.LEFT
    )

    self.player_treasure_count = Text(
      (board_w * 0.20, board_h * 0.75),
      f"{self.player.get_treasure_count()}({self.player.get_treasures_weight()}kg)",
      24,
      "white",
      alignment=Alignment.LEFT
    )

    self.player_depth = Text(
      (board_w * 0.76, board_h * 0.75),
      f"{self.player.get_depth()}",
      24,
      "white",
      alignment=Alignment.LEFT
    )

    self.turn_indicator_source = SpriteSource (
      ["turn_indicator.png"],
      (24, 16),
      (1.5, 1.5)
    )

    self.turn_indicator_rect = self.turn_indicator_source.generate_sprite_rect(
      (self.get_x_position() + self.board_object_rect.width + 5, self.get_y_position()),
      alignment=Alignment.LEFT
    )

    indicator_anim = Anim([(sprite, 1) for sprite in self.turn_indicator_source.sprites])
    self.indicator_anim_cursor = AnimCursor()
    self.indicator_anim_cursor.use_anim(indicator_anim)


  def draw(self, screen):
    self.player_treasure_count.text = f"{self.player.get_treasure_count()}({self.player.get_treasures_weight()}kg)"
    self.player_depth.text = f"{self.player.get_depth()}"

    board_copy = self.board_object.copy()
    self.player_name_text.draw(board_copy)
    self.player_treasure_count.draw(board_copy)
    self.player_depth.draw(board_copy)
    screen.blit(board_copy, self.board_object_rect.topleft)

    if self.game.player_of_turn == self.player.player_id:
      dt = 10 / 60 # (número de animação por 60fps) # Quanto maior, mais rápido
      self.indicator_anim_cursor.update(dt)
      indicator = self.indicator_anim_cursor.current
      screen.blit(indicator, self.turn_indicator_rect.topleft)

class SoundtrackToggle(Component):
  """
    Botão utilizado para ativar ou desativar a trilha\n
    sonora do jogo.
  """
  def __init__(
    self,
    position: tuple[int, int],
    on_sprite_source: SpriteSource,
    off_sprite_source: SpriteSource,
    scene_manager: SceneManager,
    alignment: Alignment = Alignment.CENTER
  ):
    super().__init__(position, alignment)
    self._interactable = True
    self._animated = True

    self.on_sprite_source = on_sprite_source
    self.off_sprite_source = off_sprite_source
    self.scene_manager = scene_manager
    self.alignment = alignment

    self.__setup()

  def __setup(self):

    self.on_button = SpriteButton(
      self.position,
      self.on_sprite_source,
      alignment=self.alignment,
      on_click=lambda _: self.scene_manager.stop_soundtrack()
    )

    self.off_button = SpriteButton(
      self.position,
      self.off_sprite_source,
      alignment=self.alignment,
      on_click=lambda _: self.scene_manager.play_soundtrack()
    )

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    # Só uma verificação tá bom, já que o butão de on deve ser identico ao de off
    return self.on_button.is_mouse_within_bounding_box(mouse_pos)

  def draw(self, screen):
    if self.scene_manager.is_soundtrack_playing():
      self.on_button.draw(screen)
    else:
      self.off_button.draw(screen)

  def listen(self, event):
    if self.scene_manager.is_soundtrack_playing():
      self.on_button.listen(event)
    else:
      self.off_button.listen(event)

  def animate(self, animation_reset = False):
    if self.scene_manager.is_soundtrack_playing():
      self.on_button.animate(animation_reset)
    else:
      self.off_button.animate(animation_reset)

class Submarine(Component):

  def __init__(
      self,
      position: tuple[int, int],
      submarine_source: SpriteSource,
      game_map_x: int,
      game_map_width: int,
      game: Game,
      alignment: Alignment = Alignment.CENTER
  ):
    super().__init__(position, alignment)
    self._interactable = True

    self.submarine_source = submarine_source
    self.game_map_x = game_map_x
    self.game_map_width = game_map_width
    self.game = game

    self.__setup()

  def __setup(self):
    self.submarine_image = AnimatedImage(
      self.position,
      self.submarine_source,
      flip_rule=(True, False),
      on_click=self.handle_submarine_click
    )

    # Configuração inicial do submarino
    half_real_sprite_width = self.submarine_image.sprite_source.get_real_sprite_width() / 2
    if self.game.difficulty == Difficulty.HARD:
      # Ajeita a posição inicial efinal para ficar dentro das bordas do mapa
      self.submarine_image.move_by(half_real_sprite_width, 0)
      self.initial_x_position = self.submarine_image.position[0]
      self.final_x_position = (self.game_map_x + (self.game_map_width / 2)) - half_real_sprite_width
      self.at_the_end = False
      # Volta com o submarino para o meio
      self.submarine_image.move_by(-half_real_sprite_width, 0)
      self.submarine_image.move_by(self.game_map_width / 2, 0)
    else:
      self.submarine_image.move_by(self.game_map_width / 2, 0)
      self.submarine_image.disabled = True

    self.submarine_speed = 2 if self.game.map_size == 15 else 1

  def handle_submarine_click(self):
    if not self.game.first_player_sorted:
      return

    player = self.game.get_current_player_of_turn()

    if player.is_on_the_submarine():

      # Se ele não pode sair do submarino, não faz nada.
      # Na realidade essa condicão nunca deve chegar a ser verdadeira
      # pois isso quebraria a linearidade da partida. Por meio de outros
      # métodos, nós temos que ter certeza que um jogador que esteja assim
      # nunca vai ter nem a chance de ter seu turno.
      # Porém, isso fica aqui só de precaução.
      if not player.can_leave_the_submarine():
        return

      # Se a pessoa ainda não sorteou o dado, não faz nada
      if self.game.need_dice_sort:
        return

      # Se ainda não precisa da ativação do jogador, não faz nada
      if not self.game.need_player_activation:
        return

      # Se já tem um número sorteado e precisa de interação, procede.

      # Tira ele do modo de ativação de interação e coloca ele no modo de ação
      self.game.need_player_activation = False
      self.game.need_player_action = True

      # Calcula os possíveis passos para baixo, considerando o dado sorteado
      # Até aqui, o número de dados sorteados deve ser maior que 0
      middle_x = self.game.map_size // 2
      self.game.current_possible_steps = self.game.calculate_possible_steps(
        (middle_x, -1),
        self.game.sorted_dice_number,
        search_for=[Direction.DOWN] # Só pesquisa os possíveis caminho para baixo
      )

    else:
      # TODO: colocar pra voltar pro submarino, guardar tesouros, etc...
      # TODO: quanto voltar para o submarino, ele vai perder o status de "playing".
      # TODO: Nós vamos tratar do need_player_activation do jogador no mapa aqui.
      # TODO: e não lá no mapa em sí

      #Só vai poder interagir com o submarino dessa maneira se estiver no início do turno
      if not self.game.need_player_activation:
        return

      player = self.game.get_current_player_of_turn()
      player_x, player_y = player.position

      # O player deve esta no topo para fazer isso
      if player_y != 0:
        return

      map_width = self.game.map_object_rect_width
      map_left = self.game.map_object_rect_left
      # Posição do mouse
      pos_x = self.submarine_image.get_x_position()
      map_size = self.game.map_size

      # Isso dá o resultado em índice 0 até (map-size - 1)
      # Essa posição não leva em conta a separação de gaps. Então, se for clicado entre os gaps
      # o click ainda pode ser processado.
      submarine_x = (map_size * (pos_x - map_left) // map_width)
      # O do meio, o anterio e o posterior, respectivamente
      possible_on_board_positions = [submarine_x, max(0, submarine_x - 1), min(map_size - 1, submarine_x + 1)]

      # O player não está nas localizações possíveis de entrar no submarino
      if player_x not in possible_on_board_positions:
        return

      self.game.need_submarine_option = True

  def update_submarine_animation(self):

    if self.at_the_end:
      self.submarine_image.move_by(-self.submarine_speed, 0)
      if self.submarine_image.get_x_position() <= self.initial_x_position:
        self.at_the_end = False
        self.submarine_image.set_use_flip(False)
    else:
      self.submarine_image.move_by(self.submarine_speed, 0)
      if self.submarine_image.get_x_position() >= self.final_x_position:
        self.at_the_end = True
        self.submarine_image.set_use_flip(True)

  def draw(self, screen):
    if self.game.difficulty == Difficulty.HARD and self.game.has_everybody_left_the_submarine_already():
      self.update_submarine_animation()

    self.submarine_image.draw(screen)

  def listen(self, event):
    self.submarine_image.listen(event)

class FirstPlayerSorter(Component):

  def __init__(
    self,
    position: tuple[int, int],
    game: Game,
    alignment: Alignment = Alignment.CENTER
  ):
    super().__init__(position, alignment=alignment)
    self._interactable = True
    self._animated = True
    self._expandable = True
    self._expanded = True

    self.game = game

    self.time_before_closure = float

    self.__setup()

  def __setup(self):
    self.background_source = SpriteSource(
      ["square_banner.png"],
      scale_by_size=(3, 3)
    )

    middle_x = self.background_source.get_real_sprite_width() // 2
    middle_y = self.background_source.get_real_sprite_height() // 2

    text_pos = (middle_x, self.background_source.get_real_sprite_height() * 0.10)

    self.first_title = Text(
      text_pos,
      "Clique para sortear",
      32,
      "white",
    )

    self.second_title = Text(
      (text_pos[0], text_pos[1] + 30),
      "o primeiro jogador",
      32,
      "white",
    )

    self.background_rect = self.background_source.generate_sprite_rect(self.position, alignment=self.alignment)

    self.players_source = SpriteSource(
      ["entities", "divers.png"],
      (24, 39),
      (4, 4)
    )

    player_pos = (middle_x, middle_y)
    self.players_rect = self.players_source.generate_sprite_rect(player_pos, alignment=self.alignment)

    # Animação
    self.anim_cursor = AnimCursor()
    frame_list = list([sprite, 1] for sprite in self.players_source.sprites)
    anim = Anim(frame_list[:self.game.player_count]) # Pega a quantidade de sprites equivalente a quantidade de players
    self.anim_cursor.use_anim(anim)
    self.anim_cursor.play()

    def sort_player():
      self.game.first_player_sorted = True
      self.game.player_of_turn = random.randint(1, len(self.anim_cursor.anim.frames))
      self.anim_cursor.reset()

      self.first_title.text = "Primeiro jogador sorteado:"
      self.second_title.text = f"{self.game.player_of_turn}"

      self.time_before_closure = timer()

    self.draw_button = SpriteButton(
      (middle_x, self.background_source.get_real_sprite_height() * 0.85),
      SpriteSource(
        ["buttons", "draw.png"],
        (64, 26),
        (2, 2)
      ),
      on_click=lambda _: sort_player()
    )

    # Só vai ter a hitbox do botão, como a posição é relativa a posição
    # geral passada na classe. Temos que acontar a ela
    sprite_width, sprite_height = self.draw_button.sprite_source.real_sprite_size

    remaining_background_left = self.get_x_position() - self.background_source.get_real_sprite_width() // 2
    remaining_background_top = self.get_y_position() - self.background_source.get_real_sprite_height() // 2

    button_left = remaining_background_left + self.draw_button.get_x_position() - (sprite_width // 2)
    button_top = remaining_background_top + self.draw_button.get_y_position() - (sprite_height // 2)

    self.virtual_draw_button_rect = pygame.Rect(button_left, button_top, sprite_width, sprite_height)

    # Muda hitbox do botão pra ser a dessa classe
    self.draw_button.is_mouse_within_bounding_box = self.virtual_is_mouse_within_bounding_box

  def virtual_is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.virtual_draw_button_rect.collidepoint(mouse_pos)

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.background_rect.collidepoint(mouse_pos)

  def listen(self, event):
    if not self._expanded:
      return

    if self.game.first_player_sorted:
      return

    mouse_pos = pygame.mouse.get_pos()
    if self.virtual_is_mouse_within_bounding_box(mouse_pos):
      self.draw_button.listen(event)

  def animate(self, animation_reset = False):
    if not self._expanded:
      return

    self.draw_button.animate(animation_reset)

  def draw(self, screen):
    if not self._expanded:
      return

    player: pygame.Surface = None
    if self.game.first_player_sorted:
      player = self.players_source.sprites[self.game.player_of_turn - 1]

      current_time = timer()
      time_to_close = math.trunc(current_time - self.time_before_closure)

      if time_to_close >= 3:
        self._expanded = False
        self.disabled = True
        self.game.need_dice_sort = True
        # Desativa o botão para ele não atrapalhar o click dos botões em baixo dele
        self.disabled = True
        return
    else:
      dt = 10 / 60 # (número de animação por 60fps) # Quanto maior, mais rápido
      self.anim_cursor.update(dt)
      player = self.anim_cursor.current

    # Fundo
    background = self.background_source.first_sprite().copy()

    # Animação e Jogador
    background.blit(player, self.players_rect.topleft)

    # Titulo
    self.first_title.draw(background)
    self.second_title.draw(background)

    # Botão
    self.draw_button.draw(background)

    screen.blit(background, self.background_rect.topleft)


class DiceRoller(Component):
  def __init__(
    self,
    position: tuple[int, int],
    game: Game,
    alignment: Alignment = Alignment.CENTER
  ):
    super().__init__(position, alignment=alignment)
    self._interactable = True
    self._animated = True
    self._expandable = True
    self._expanded = True

    self.game = game

    self.dice_sorted = False
    self.__setup()


  def __setup(self):
    self.background_source = SpriteSource(
      ["square_banner.png"],
      scale_by_size=(1.9, 1.5)
    )

    middle_x = self.background_source.get_real_sprite_width() // 2
    middle_y = self.background_source.get_real_sprite_height() // 2

    text_pos = (middle_x, self.background_source.get_real_sprite_height() * 0.10)

    self.first_title = Text(
      text_pos,
      "Clique para sortear",
      24,
      "white",
    )

    self.second_title = Text(
      (text_pos[0], text_pos[1] + 25),
      "um número de dado",
      24,
      "white",
    )

    self.background_rect = self.background_source.generate_sprite_rect(self.position, alignment=self.alignment)

    self.dice_3d_source = SpriteSource(
      ["dice_3d.png"],
      (51, 54),
      (1.25, 1.25)
    )

    self.dice_faces_source = SpriteSource(
      ["dice_faces.png"],
      (64, 64),
      (1.20, 1.20)
    )

    dice_pos = (middle_x, middle_y)
    self.dice3d_rect = self.dice_3d_source.generate_sprite_rect(dice_pos, alignment=self.alignment)
    self.dice_faces_rect = self.dice_faces_source.generate_sprite_rect(dice_pos, alignment=self.alignment)

    def sort_dice():
      self.time_before_closure = timer()

      self.game.sorted_dice_number = self.game.dice()
      self.dice_sorted = True

      self.first_title.text = "Número sorteado:"
      self.second_title.text = f"{self.game.sorted_dice_number}"


    self.roll_button = SpriteButton(
      (middle_x, self.background_source.get_real_sprite_height() * 0.85),
      SpriteSource(
        ["buttons", "draw.png"],
        (64, 26),
        (1.5, 1.5)
      ),
      on_click=lambda _: sort_dice()
    )

    # Só vai ter a hitbox do botão, como a posição é relativa a posição
    # geral passada na classe. Temos que acontar a ela
    sprite_width, sprite_height = self.roll_button.sprite_source.real_sprite_size

    remaining_background_left = self.get_x_position() - self.background_source.get_real_sprite_width() // 2
    remaining_background_top = self.get_y_position() - self.background_source.get_real_sprite_height() // 2

    button_left = remaining_background_left + self.roll_button.get_x_position() - (sprite_width // 2)
    button_top = remaining_background_top + self.roll_button.get_y_position() - (sprite_height // 2)

    self.virtual_roll_button_rect = pygame.Rect(button_left, button_top, sprite_width, sprite_height)

    # Muda hitbox do botão pra ser a dessa classe
    self.roll_button.is_mouse_within_bounding_box = self.virtual_is_mouse_within_bounding_box

  def virtual_is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.virtual_roll_button_rect.collidepoint(mouse_pos)

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.background_rect.collidepoint(mouse_pos)

  def listen(self, event):
    if not self.game.need_dice_sort:
      return

    if self.dice_sorted:
      return

    mouse_pos = pygame.mouse.get_pos()
    if self.virtual_is_mouse_within_bounding_box(mouse_pos):
      self.roll_button.listen(event)

  def animate(self, animation_reset = False):
    # Por algum motivo, quando tinha essa verificação
    # a animação não continuava depois no próximo turno

    # if not self.game.need_dice_sort:
    #   print("not dice sort")
    #   return

    self.roll_button.animate(animation_reset)

  def draw(self, screen):
    if not self.game.need_dice_sort:
      return

    # Fundo
    background = self.background_source.first_sprite().copy()

    # Jogador

    dice_surface: pygame.Surface = self.dice_3d_source.first_sprite()
    if self.dice_sorted:
      dice_surface = self.dice_faces_source.sprites[self.game.sorted_dice_number]

      current_time = timer()
      time_to_close = math.trunc(current_time - self.time_before_closure)

      if time_to_close >= 3:
        self.game.need_dice_sort = False
        self.dice_sorted = False

        # Reseta o texto no dado para ficar intuitivo
        self.first_title.text = "Clique para sortear"
        self.second_title.text = "um número de dado"

        player = self.game.get_current_player_of_turn()

        # Se ele estiver no submarino e tirar zero, ele não pode fazer nada.
        # Só esperar pela próxima vez dele.
        if self.game.sorted_dice_number == 0:
          self.game.go_to_next_player_turn()
        else:
          # Se o jogador tirar 0, ele não pode ser mover, mas pode
          # interar com a casa que ele está. Por exemplo, se, na casa
          # que ele está, ainda tem um tesouro, ele pode escolher
          # pegar o tesouro dessa vez. Fora isso, ele pode jogar
          # normalmente.
          self.game.need_player_activation = True

        return

      background.blit(dice_surface, self.dice_faces_rect.topleft)

    else:
      dice_surface = self.dice_3d_source.first_sprite()
      background.blit(dice_surface, self.dice3d_rect.topleft)

    # Titulo
    self.first_title.draw(background)
    self.second_title.draw(background)

    # Botão
    self.roll_button.draw(background)

    screen.blit(background, self.background_rect.topleft)

class PlayerDecision(Component):

  def __init__(
    self,
    position: tuple[int, int],
    game: Game
  ):
    super().__init__(position)
    self._interactable = True
    self._animated = True
    self.disabled = True # Ele começa desativado para não atrapalhar o click do FirstPlayerSorter

    self.game = game
    self.__setup()

  def __setup(self):

    self.background_source = SpriteSource(
      ["square_banner.png"],
      scale_by_size=(3.5, 2.5)
    )

    self.background_rect = self.background_source.generate_sprite_rect(self.position)

    middle_x = self.background_source.get_real_sprite_width() // 2
    middle_y = self.background_source.get_real_sprite_height() // 2

    self.first_title = Text(
      (middle_x, self.background_source.get_real_sprite_height() * 0.15),
      "Você deseja pegar o tesouro?",
      32,
      "white",
    )

    error_color = pygame.Color(227, 66, 52)

    self.first_warning_title = Text(
      (middle_x, middle_y - 30),
      "",
      32,
      error_color,
    )


    self.second_warning_title = Text(
      (middle_x, self.first_warning_title.get_y_position() + 30),
      "",
      32,
      error_color,
    )

    yes_button_source = SpriteSource(
      ["buttons", "yes.png"],
      (64, 26),
      scale_by_size=(2, 2)
    )

    no_button_source = SpriteSource(
      ["buttons", "no.png"],
      (64, 26),
      scale_by_size=(2, 2)
    )

    half_of_real_width = yes_button_source.get_real_sprite_width() // 2
    button_gap = 30

    def clean_warning_titles():
      self.first_warning_title.text = ""
      self.second_warning_title.text = ""

    def on_yes():
      player = self.game.get_current_player_of_turn()
      player_treasures_weight = player.get_treasures_weight()

      treasure = self.game.treasure_being_taken
      treasure_weight = treasure.weight

      if player_treasures_weight + treasure_weight > 15:
        self.first_warning_title.text = "O peso dos tesouros não"
        self.second_warning_title.text = "podem ser maior que 15kg!"
        return

      clean_warning_titles()

      player_x, player_y = player.position

      player.treasures.append(treasure)
      # Até esse momento, a nova posição do jogador já condiz com a posição do tesouro
      # na matriz do mapa.
      self.game.map[player_x][player_y] = None
      self.game.need_player_decision = False
      self.game.clear_treasure_being_taken()

      self.game.go_to_next_player_turn()

    self.yes_button = SpriteButton(
      (middle_x - half_of_real_width - button_gap, self.background_source.get_real_sprite_height() * 0.85),
      yes_button_source,
      on_click=lambda _: on_yes()
    )

    def on_no():
      clean_warning_titles()
      self.game.need_player_decision = False
      self.game.clear_treasure_being_taken()
      self.game.go_to_next_player_turn()

    self.no_button = SpriteButton(
      (middle_x + half_of_real_width + button_gap, self.background_source.get_real_sprite_height() * 0.85),
      no_button_source,
      on_click=lambda _: on_no()
    )

    # Só vai ter a hitbox do botão, como a posição é relativa a posição
    # geral passada na classe. Temos que acontar a ela
    sprite_width, sprite_height = self.yes_button.sprite_source.real_sprite_size

    remaining_background_left = self.get_x_position() - self.background_source.get_real_sprite_width() // 2
    remaining_background_top = self.get_y_position() - self.background_source.get_real_sprite_height() // 2

    yes_button_left = remaining_background_left + self.yes_button.get_x_position() - (sprite_width // 2)
    yes_button_top = remaining_background_top + self.yes_button.get_y_position() - (sprite_height // 2)

    no_button_left = remaining_background_left + self.no_button.get_x_position() - (sprite_width // 2)
    no_button_top = remaining_background_top + self.no_button.get_y_position() - (sprite_height // 2)

    self.virtual_yes_button_rect = pygame.Rect(yes_button_left, yes_button_top, sprite_width, sprite_height)
    self.virtual_no_button_rect = pygame.Rect(no_button_left, no_button_top, sprite_width, sprite_height)

    # Muda hitbox do botão pra ser a dessa classe
    self.yes_button.is_mouse_within_bounding_box = self.yes_virtual_is_mouse_within_bounding_box
    self.no_button.is_mouse_within_bounding_box = self.no_virtual_is_mouse_within_bounding_box

  def yes_virtual_is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.virtual_yes_button_rect.collidepoint(mouse_pos)

  def no_virtual_is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.virtual_no_button_rect.collidepoint(mouse_pos)

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.background_rect.collidepoint(mouse_pos)

  def animate(self, animation_reset = False):
    # Ativa ou desativa o componente para que ele não atrapalhe o click
    # de outros componentes em baixo dele.
    if self.game.need_player_decision:
      if self.disabled:
        self.disabled = False
    else:
      if not self.disabled:
        self.disabled = True

    self.yes_button.animate(animation_reset)
    self.no_button.animate(animation_reset)

  def listen(self, event):
    if not self.game.need_player_decision:
      return

    mouse_pos = pygame.mouse.get_pos()
    if self.yes_virtual_is_mouse_within_bounding_box(mouse_pos):
      self.yes_button.listen(event)
      return

    if self.no_virtual_is_mouse_within_bounding_box(mouse_pos):
      self.no_button.listen(event)
      return

  def draw(self, screen):
    if not self.game.need_player_decision:
      return

    background = self.background_source.first_sprite().copy()

    self.first_title.draw(background)
    self.first_warning_title.draw(background)
    self.second_warning_title.draw(background)


    self.yes_button.draw(background)
    self.no_button.draw(background)
    screen.blit(background, self.background_rect.topleft)


class SubmarineOptions(Component):

  def __init__(
    self,
    position: tuple[int, int],
    game: Game
  ):
    super().__init__(position)
    self._interactable = True
    self._animated = True
    self.disabled = True # Ele começa desativado para não atrapalhar o click do FirstPlayerSorter

    self.game = game
    self.__setup()

  def __setup(self):

    self.background_source = SpriteSource(
      ["square_banner.png"],
      scale_by_size=(2.5, 2)
    )

    self.background_rect = self.background_source.generate_sprite_rect(self.position)

    middle_x = self.background_source.get_real_sprite_width() // 2

    self.first_title = Text(
      (middle_x, self.background_source.get_real_sprite_height() * 0.10),
      "Escolha uma opção",
      32,
      "white",
    )

    store_treasures_button_source = SpriteSource(
      ["buttons", "store_treasures.png"],
      (128, 26),
      scale_by_size=(2, 2)
    )

    get_on_board_button_source = SpriteSource(
      ["buttons", "get_on_board.png"],
      (128, 26),
      scale_by_size=(2, 2)
    )

    quit_button_source = SpriteSource(
      ["buttons", "long_quit.png"],
      (128, 26),
      scale_by_size=(2, 2)
    )

    button_height = store_treasures_button_source.get_real_sprite_height()
    button_gap = 10

    def on_store_treasures():
      self.game.need_submarine_option = False
      player = self.game.get_current_player_of_turn()
      if player.get_treasure_count() > 0:
        for treasure in player.treasures:
          player.stored_treasures.append(treasure)

        player.treasures.clear()


    self.store_treasures_button = SpriteButton(
      (middle_x, self.background_source.get_real_sprite_height() * 0.25 + button_gap),
      store_treasures_button_source,
      on_click=lambda _: on_store_treasures()
    )

    def on_get_on_board():
      self.game.need_submarine_option = False
      player = self.game.get_current_player_of_turn()
      player.position = (-1, -1)
      player.playing = False
      self.game.go_to_next_player_turn()

    self.get_on_board_button = SpriteButton(
      (middle_x, self.store_treasures_button.get_y_position() + button_height + button_gap),
      get_on_board_button_source,
      on_click=lambda _: on_get_on_board()
    )

    def on_quit():
      self.game.need_submarine_option = False

    self.quit_button = SpriteButton(
      (middle_x, self.get_on_board_button.get_y_position() + button_height + button_gap),
      quit_button_source,
      on_click=lambda _: on_quit()
    )

    # Só vai ter a hitbox do botão, como a posição é relativa a posição
    # geral passada na classe. Temos que acontar a ela
    sprite_width, sprite_height = self.store_treasures_button.sprite_source.real_sprite_size

    remaining_background_left = self.get_x_position() - self.background_source.get_real_sprite_width() // 2
    remaining_background_top = self.get_y_position() - self.background_source.get_real_sprite_height() // 2

    store_treasures_button_left = remaining_background_left + self.store_treasures_button.get_x_position() - (sprite_width // 2)
    store_treasures_button_top = remaining_background_top + self.store_treasures_button.get_y_position() - (sprite_height // 2)

    get_on_board_button_left = remaining_background_left + self.get_on_board_button.get_x_position() - (sprite_width // 2)
    get_on_board_button_top = remaining_background_top + self.get_on_board_button.get_y_position() - (sprite_height // 2)

    quit_button_left = remaining_background_left + self.quit_button.get_x_position() - (sprite_width // 2)
    quit_button_top = remaining_background_top + self.quit_button.get_y_position() - (sprite_height // 2)

    self.virtual_store_treasures_button_rect = pygame.Rect(store_treasures_button_left, store_treasures_button_top, sprite_width, sprite_height)
    self.virtual_get_on_board_button_rect = pygame.Rect(get_on_board_button_left, get_on_board_button_top, sprite_width, sprite_height)
    self.virtual_quit_button_rect = pygame.Rect(quit_button_left, quit_button_top, sprite_width, sprite_height)

    # Muda hitbox do botão pra ser a dessa classe
    self.store_treasures_button.is_mouse_within_bounding_box = self.store_treasures_virtual_is_mouse_within_bounding_box
    self.get_on_board_button.is_mouse_within_bounding_box = self.get_on_board_virtual_is_mouse_within_bounding_box
    self.quit_button.is_mouse_within_bounding_box = self.quit_virtual_is_mouse_within_bounding_box


  def store_treasures_virtual_is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.virtual_store_treasures_button_rect.collidepoint(mouse_pos)

  def get_on_board_virtual_is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.virtual_get_on_board_button_rect.collidepoint(mouse_pos)

  def quit_virtual_is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.virtual_quit_button_rect.collidepoint(mouse_pos)

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.background_rect.collidepoint(mouse_pos)

  def animate(self, animation_reset = False):
    # Ativa ou desativa o componente para que ele não atrapalhe o click
    # de outros componentes em baixo dele.
    if self.game.need_submarine_option:
      if self.disabled:
        self.disabled = False
    else:
      if not self.disabled:
        self.disabled = True

    self.store_treasures_button.animate(animation_reset)
    self.get_on_board_button.animate(animation_reset)
    self.quit_button.animate(animation_reset)

  def listen(self, event):
    if not self.game.need_submarine_option:
      return

    mouse_pos = pygame.mouse.get_pos()
    if self.store_treasures_virtual_is_mouse_within_bounding_box(mouse_pos):
      self.store_treasures_button.listen(event)
      return

    if self.get_on_board_virtual_is_mouse_within_bounding_box(mouse_pos):
      self.get_on_board_button.listen(event)
      return

    if self.quit_virtual_is_mouse_within_bounding_box(mouse_pos):
      self.quit_button.listen(event)
      return

  def draw(self, screen):
    if not self.game.need_submarine_option:
      return

    background = self.background_source.first_sprite().copy()

    self.first_title.draw(background)

    self.store_treasures_button.draw(background)
    self.get_on_board_button.draw(background)
    self.quit_button.draw(background)
    screen.blit(background, self.background_rect.topleft)


class WinnerDisplay(Component):

  def __init__(
    self,
    position: tuple[int, int],
    game: Game,
    alignment: Alignment = Alignment.CENTER
  ):
    super().__init__(position, alignment=alignment)
    self._interactable = True
    self._animated = True
    self.disabled = True

    self.game = game

    self.__setup()

  def __setup(self):
    self.winner = self.game.get_winner_player()

    self.background_source = SpriteSource(
      ["square_banner.png"],
      scale_by_size=(3, 3)
    )

    middle_x = self.background_source.get_real_sprite_width() // 2
    middle_y = self.background_source.get_real_sprite_height() // 2

    text_pos = (middle_x, self.background_source.get_real_sprite_height() * 0.10)

    self.first_title = Text(
      text_pos,
      "O vencedor é",
      32,
      "white",
    )

    self.second_title = Text(
      (text_pos[0], text_pos[1] + 30),
      "",
      32,
      "white",
    )

    self.background_rect = self.background_source.generate_sprite_rect(self.position, alignment=self.alignment)

    self.players_source = SpriteSource(
      ["entities", "divers.png"],
      (24, 39),
      (4, 4)
    )

    player_pos = (middle_x, middle_y)
    self.winner_rect = self.players_source.generate_sprite_rect(player_pos, alignment=self.alignment)

    def quit_game():
      self.game.running = False

    self.quit_button = SpriteButton(
      (middle_x, self.background_source.get_real_sprite_height() * 0.85),
      SpriteSource(
        ["buttons", "draw.png"],
        (64, 26),
        (2, 2)
      ),
      on_click=lambda _: quit_game()
    )

    # Só vai ter a hitbox do botão, como a posição é relativa a posição
    # geral passada na classe. Temos que acontar a ela
    sprite_width, sprite_height = self.quit_button.sprite_source.real_sprite_size

    remaining_background_left = self.get_x_position() - self.background_source.get_real_sprite_width() // 2
    remaining_background_top = self.get_y_position() - self.background_source.get_real_sprite_height() // 2

    button_left = remaining_background_left + self.quit_button.get_x_position() - (sprite_width // 2)
    button_top = remaining_background_top + self.quit_button.get_y_position() - (sprite_height // 2)

    self.virtual_quit_button_rect = pygame.Rect(button_left, button_top, sprite_width, sprite_height)

    # Muda hitbox do botão pra ser a dessa classe
    self.quit_button.is_mouse_within_bounding_box = self.virtual_is_mouse_within_bounding_box

  def virtual_is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.virtual_quit_button_rect.collidepoint(mouse_pos)

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.background_rect.collidepoint(mouse_pos)

  def listen(self, event):
    if not self.game.game_has_ended:
      return

    mouse_pos = pygame.mouse.get_pos()
    if self.virtual_is_mouse_within_bounding_box(mouse_pos):
      self.quit_button.listen(event)

  def animate(self, animation_reset = False):
    if self.game.game_has_ended:
      if self.disabled:
        self.disabled = False
        self.winner = self.game.get_winner_player()
        self.second_title.text = f"jogador {self.winner.player_id}"
    else:
      if not self.disabled:
        self.disabled = True

    self.quit_button.animate(animation_reset)

  def draw(self, screen):
    if not self.game.game_has_ended:
      return

    background = self.background_source.first_sprite().copy()

    # vencedor
    background.blit(self.players_source.sprites[self.winner.player_id - 1], self.winner_rect.topleft)

    # Titulo
    self.first_title.draw(background)
    self.second_title.draw(background)

    # Botão
    self.quit_button.draw(background)

    screen.blit(background, self.background_rect.topleft)
