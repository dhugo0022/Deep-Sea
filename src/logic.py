import random
from enum import Enum
from typing import Dict
import sys
from lib.components import SpriteSource
import math

class EntityType(Enum):
  BOMB = 0
  TREASURE = 1
  PLAYER = 2

entity_sprites: Dict[EntityType, SpriteSource] = {}

class Entity:
  def __init__(
    self,
    type: EntityType,
    identifier_source: SpriteSource
  ):
    self.type = type
    if not type in entity_sprites:
      entity_sprites[type] = identifier_source

    self.identifier = entity_sprites[self.type].first_sprite()

class Bomb(Entity):
  def __init__(self):
    super().__init__(
      EntityType.BOMB,
      SpriteSource(["entities", "bomb.png"])
    )

class Treasure(Entity):
  def __init__(self, depth: int, map_size: int):
    super().__init__(
      EntityType.TREASURE,
      SpriteSource(["entities", "treasures.png"], (22, 19))
    )
    self.depth = depth
    self.weight = self.__calc_treasure_weight(depth, map_size)

    identifier_index = 0
    match self.weight:
      case 1:
        identifier_index = 0
      case 2:
        identifier_index = 1
      case 4:
        identifier_index = 2
    self.identifier = entity_sprites[self.type].sprites[identifier_index]

  def __calc_treasure_weight(self, depth: int, map_size: int):
      '''
        Calcula o peso do tesouro baseando-se na profundidade\n
        do mesmo.
      '''
      return math.trunc(math.pow(2, math.floor(3*depth/map_size)))

next_diver_sprite = 1

class Player(Entity):
  def __init__(self):
    super().__init__(
      EntityType.PLAYER, 
      SpriteSource(["entities", "divers.png"], (24, 39))
    )
    self.position = (-1, -1)
    self.playing = True
    self.disqualified = False # Se o player morrer por uma bomba, ele é desclassificado na hora
    self.has_already_left_the_submarine = False
    self.treasures: list[Treasure] = []
    self.stored_treasures: list[Treasure] = []


    # Pega um id e um sprite para o player e prepara tais coisas para o próximo
    global next_diver_sprite
    if (next_diver_sprite > 4):
      sys.exit("O sistema não suporta mais de 4 players!")
      return

    self.player_id = next_diver_sprite
    self.identifier = entity_sprites[self.type].sprites[next_diver_sprite - 1]
    next_diver_sprite += 1

  def get_player_x(self) -> int:
    return self.position[0]

  def get_player_y(self) -> int:
    return self.position[1]
  
  def is_on_the_submarine(self) -> bool:
    '''
      Retorna True se o jogador está no submarino
    '''
    return self.get_player_x() == -1 and self.get_player_y() == -1
  
  def can_leave_the_submarine(self) -> bool:
    """
      Return True se o jogador pode sair do submarino.\n
      Ele não poderá sair do submarine se ele já nadou\n
      e voltou pro submarino. Porém, se for a primeira\n
      vez dele saindo do submarino, ele pode.
    """
    return not self.has_already_left_the_submarine and self.is_on_the_submarine()

  def get_depth(self) -> int:
    '''
      Retorna a profundidade do jogador
    '''
    return 0 if self.is_on_the_submarine() else self.get_player_y() + 1
  
  def get_treasure_count(self) -> int:
    '''
      Retorna a quantidade de tesouros do jogador
    '''
    return len(self.treasures)
  
  def get_treasures_weight(self) -> int:
    '''
      Retorna a soma de peso dos tesouros do jogador
    '''
    sum_of_weight = 0
    for treasure in self.treasures:
      sum_of_weight += treasure.weight

    return sum_of_weight
  
  def get_stored_treasure_count(self) -> int:
    '''
      Retorna a quantidade de tesouros guardados do jogador
    '''
    return len(self.stored_treasures)

  def get_stored_treasures_weight(self) -> int:
    '''
      Retorna a soma de peso dos tesouros guardados do jogador
    '''
    sum_of_weight = 0
    for treasure in self.stored_treasures:
      sum_of_weight += treasure.weight

    return sum_of_weight
  
  def get_all_treasure_count(self) -> int:
    '''
      Retorna a toda a quantidade de tesouros do jogador
    '''
    return self.get_treasure_count() + self.get_stored_treasure_count()
  
  def get_all_treasures_weight(self) -> int:
    '''
      Retorna a soma de peso de todos os tesouros do jogador
    '''
    return self.get_treasures_weight() + self.get_stored_treasures_weight()


class GameState(Enum):
  CONFIGURATION = 0,
  PLAYING = 1

class Difficulty(Enum):
  EASY = {
    "index": 0,
    "odds": {
      "bomb": 0.01,
      "treasure": 0.4,
      "none": 0.59
    }
  },
  MEDIUM = {
    "index": 1,
    "odds": {
      "bomb": 0.05,
      "treasure": 0.4,
      "none": 0.55
    }
  },
  HARD = {
    "index": 2,
    "odds": {
      "bomb": 0.15,
      "treasure": 0.35,
      "none": 0.5
    }
  }

def get_difficulty_by_index(index: int) -> Difficulty:
  '''
    Retorna a dificuldade baseado no índice fornecido
  '''
  for difficulty in Difficulty:
    # O último item da lista não retorna como uma tupla
    # então temos que cuidar desse caso
    difficulty_value = difficulty.value[0] if type(difficulty.value) == tuple else difficulty.value
    if difficulty_value["index"] == index:
      return difficulty
  
  sys.exit(f"Não existe um nível de dificuldade para o índice que você deu: {index}.")

class Direction(Enum):
  UP = 0
  DOWN = 1,
  LEFT = 2,
  RIGHT = 3

class Game:
  
  '''
    Formato padrão de um objeto de jogo:
    game = {
      game_state: GameState,
      oxygen_tanks: int,
      map_size: int,
      map: list,
      player_count: list,
      difficulty: Difficulty
    }
  '''
  def __init__(self):
    self.running = False
    self.game_state = GameState.CONFIGURATION

  def game_has_been_configured(self) -> bool:
    '''
      Verifica se o jogo já foi configurado
    '''
    return self.game_state is not GameState.CONFIGURATION

  def configure_game(self, initial_oxygen_tanks: int, map_size: int, player_count: int, difficulty: Difficulty):
    '''
      Configura o objeto do jogo com os dados fornecidos pelo\n
      jogador caso o objeto ainda esteja em estado de configuração.
    '''	

    if self.game_has_been_configured():
      return

    self.oxygen_tanks = initial_oxygen_tanks

    self.map_size = map_size
    self.map = self.__generate_map_matrix(map_size)
    # Popula o mapa logo depois da criação
    
    self.player_count = player_count
    self.difficulty = difficulty
    
    # Tira do estado de configuração
    self.game_state = GameState.PLAYING

    self.turn = 1 # Contagem de turnos
    self.player_of_turn = 0 # Número do jogador para o turno
    self.first_player_sorted = False
    
    self.need_dice_sort = False # Indica se precisa rolar os dados
    self.sorted_dice_number = 0 # Número sorteado de passos
    self.current_possible_steps: Dict[str, list[tuple[int, int]]] = None # Os possíveis passos que o jogador pode tomar
    
    # Indica se, após o jogador sortear o número, ele precisa clicar no objeto 
    # dele no mapa ou no submarino (no início) para ativar o modo de interação
    self.need_player_activation = False 

    # Indica se, após o jogador ativar a interação, ele precisa clicar na casa
    # pra andar ou passar a vez
    self.need_player_action = False
    
    # Indica se, após o jogador andar, ele precisa escolher se vai pegar o 
    # tesouro ou não
    self.need_player_decision = False
    self.treasure_being_taken: Treasure = None

    # O submarino vai usar esses valores para calcular a celula abaixo dele
    self.map_object_rect_width = -1
    self.map_object_rect_left = -1
    self.need_submarine_option = False

    # No fim
    self.game_has_ended = False

  def __generate_map_matrix(self, size: int):
    '''
      Gera uma matriz bidimensional que serve como o mapa\n
      cujo o dominio é representado por:\n
      D = {(x, y) ∈ N² | x, y ∈ [0, size - 1]}.
    '''
    return [[None for _ in range(size)] for _ in range(size)]

  def populate_map(self):
    '''
      Preenche o mapa com bombas e tesouros.\n
      Caso o objeto do jogo ainda não tenha sido configurado\n
      essa função não faz nada.
    '''

    if not self.game_has_been_configured():
      sys.exit("Não é possível popular o mapa sem configurar o objeto do jogo primeiro.")
      return

    # O último item da lista não retorna como uma tupla
    # então temos que cuidar desse caso
    difficulty_value = self.difficulty.value[0] if type(self.difficulty.value) == tuple else self.difficulty.value
    odds = [*difficulty_value.values()][1]
 
    for x in range(self.map_size):
      for y in range(self.map_size):
        
        choice = random.choices(
          population=[*odds.keys()],
          weights=[*odds.values()],
          k=1
        )

        entity = None

        if choice[0] == "bomb" and y > 2: # Depois das três primeiras profundidades, as bombas podem ser spawnadas
          entity = Bomb()
        elif choice[0] == "treasure":
          entity = Treasure(y, self.map_size)
        else:
          # Não precisar definir a entidade como None já que
          # a inicialização padrão do objeto entity faz isso
          pass
        
        self.map[x][y] = entity

    # Coloca os jogadores logo depois da criação
    self.players = [Player() for _ in range(self.player_count)]

  def get_player_by_id(self, player_id: int) -> Player:
    """
      Retorna o jogador com o id fornecido\n
      Caso o objeto do jogo ainda não tenha sido configurado\n
      ou o jogador com esse id não exista, da um erro.
    """
    found_player: Player = None
    for player in self.players:
      if player.player_id == player_id:
        found_player = player
        break
    
    if found_player is None:
      sys.exit(f"O player com id {player_id} não foi encontrado.")
      return
    
    return found_player

  
  def has_everybody_left_the_submarine_already(self) -> bool:
    """
      Verifica se todos os jogadores já sairam\n
      pelo menos uma vez do submarino.
    """
    return all(player.has_already_left_the_submarine for player in self.players)
  
  def check_win_conditions(self):
    if not self.has_everybody_left_the_submarine_already():
      return False
    
    # Se todos os players voltarem para o submarino
    players_that_meet_conditions = 0
    for player in self.players:
      if player.is_on_the_submarine() and not player.can_leave_the_submarine():
        players_that_meet_conditions += 1
    
    if players_that_meet_conditions == self.player_count:
      self.game_has_ended = True
      return True
    
    players_that_meet_conditions = 0
    # Se sobrar só um jogador que não foi explodido por uma bomba
    for player in self.players:
      if player.is_on_the_submarine() and player.disqualified:
        players_that_meet_conditions += 1
    
    if players_that_meet_conditions == self.player_count - 1:
      self.game_has_ended = True
      return True
    
    players_that_meet_conditions = 0

    # O oxigênio acabou
    if self.oxygen_tanks <= 0:
      self.game_has_ended = True
      return True
    
    return False

  def get_winner_player(self) -> Player:
    """
      Pega o jogador com o player número de tesouro
    """
    max_treasure_weight = max(player.get_all_treasures_weight() for player in self.players)
    richest_player_filter = [player for player in self.players if player.get_all_treasures_weight() == max_treasure_weight and not player.disqualified]
    richest_player = richest_player_filter.pop()

    return richest_player

  def consume_oxygen(self):
    """
      Decrementa o oxigênio dos tanques
    """
    number_of_oxygens = 0
    for player in self.players:
      if not player.is_on_the_submarine():
        number_of_oxygens += (player.get_depth() + 1) * player.get_all_treasures_weight() + 1

    self.oxygen_tanks -= number_of_oxygens

  def go_to_next_player_turn(self):
    """
      Alterna o turno dos jogadores para o próximo
    """
    if self.game_has_ended:
      return
    
    if self.check_win_conditions():
      return

    self.player_of_turn = (self.player_of_turn % self.player_count) + 1

    # Pula para o próximo jogador caso o jogador do próximo turno
    # já está impossibilitado de jogar;
    # - Se ele voltar pro submarino
    # - Se ele morrer pra bomba
    if not self.get_current_player_of_turn().playing:
      self.go_to_next_player_turn()
    else:
      # Se o turno cair em um jogador válido, o turno aumenta
      self.turn += 1
      # Coloca para o próximo player pode sortear um número para o dado
      self.need_dice_sort = True
      # Consome o oxigênio pelo turno  
      self.consume_oxygen()

  
  def get_current_player_of_turn(self) -> Player:
    """
      Pega o atual jogador do turno
    """
    return self.get_player_by_id(self.player_of_turn)
  
  def dice(self) -> int:
    '''
      Gera um par de números aleatório entre 0, 3.
    '''
    return random.randint(0, 3)

  def entity_at(self, position: tuple[int, int]) -> Entity:
    '''
      Retorna a entidade presente na posição (x, y) do mapa\n
      Se a posição estiver vazia, retorna None.\n
      Caso o objeto do jogo ainda não tenha sido configurado\n
      retorna `None`.
    '''

    if not self.game_has_been_configured():
      return None

    x, y = position
    return self.map[x][y]

  def has_entity_at(self, position: tuple[int, int], type: EntityType) -> bool:
    '''
      Verifica se a entidade da posição (x, y) do mapa é do tipo especificado\n
      Se a entidade estiver do tipo especificado, retorna `True`, senão retorna `False`\n
      Caso não haja nenhuma entidade, retorna `False`.\n
      Caso o objeto do jogo ainda não tenha sido configurado\n
      retorna `False`.
    '''

    if not self.game_has_been_configured():
      return False

    entity = self.entity_at(position)

    if entity == None:
      return False
    
    return entity.type == type

  def get_player_at(self, position: tuple[int, int]) -> Player:
    """
      Retorna o jogador presente na posição (x, y) do mapa\n
      Se a posição estiver vazia, retorna None.\n
      Caso o objeto do jogo ainda não tenha sido configurado\n
      retorna `None`.\n
      Caso o objeto do jogo ainda não tenha sido configurado\n
      dá um falha, pois ele deveria estar configurado.
    """
    if not self.game_has_been_configured():
      sys.exit("Não é possível popular o mapa sem configurar o objeto do jogo primeiro.")
      return

    for player in self.players:
      if player.position == position:
        return player
    
    return None

  def has_player_at(self, position: tuple[int, int]) -> bool:
    """
      Verifica se o jogador está presente na posição (x, y) do mapa.
    """

    return self.get_player_at(position) is not None
  
  def is_player_at(self, player: Player, position: tuple[int, int]) -> bool:
    """
      Verifica se o jogador especificado está presente na posição (x, y) do mapa.
    """

    return self.get_player_at(position) == player

  def is_in_current_possible_steps(self, position: tuple[int, int]) -> bool:
    if not self.has_current_possible_steps():
      return False
    
    for direction in self.current_possible_steps.values():
      for step in direction:
        if step == position:
          return True
  
    return False
  
  def has_current_possible_steps(self) -> bool:
    """
      Verifica se há passos atuais computados
    """
    return self.current_possible_steps is not None
  
  def clear_current_possible_steps(self):
    """
      Limpa os passos atuais computados
    """
    self.current_possible_steps = None

  def clear_treasure_being_taken(self):
    """
      Desassocia o tesouro que o jogador está tentando pegar
    """
    self.treasure_being_taken = None
  
  def get_the_direction_of_step(self, destination: tuple[int, int]) -> Direction:
    for direction, positions in self.current_possible_steps.items():
      for position in positions:
        if destination == position:
          return direction
        
    return None
  
  def get_first_bomb_in_the_way(self, destination: tuple[int, int]) -> tuple[int, int] | None:
    step_direction = self.get_the_direction_of_step(destination)

    bomb_pos = None
    for direction, positions in self.current_possible_steps.items():
      if step_direction != direction:
        continue

      for position in positions:
        if self.has_entity_at(position, EntityType.BOMB):
          bomb_pos = position
          break

        if destination == position:
          break

    return bomb_pos



  def calculate_possible_steps(self, current_position: tuple[int, int], steps: int, search_for: list[Direction] = None) -> Dict[Direction, list[tuple[int, int]]]:
    '''
      Calcula as possíveis posições para um jogador se mover\n
      nas direções: cima, baixo, esquerda e direita. Baseado\n
      no número de passos.\n
      Caso haja a necessidade, também é possível pesquisar\n
      somente em direções especificas com `search_for`.\n
      Caso o objeto do jogo ainda não tenha sido configurado\n
      retorna `None`.
    '''

    if not self.game_has_been_configured():
      return None

    min_index = 0
    max_index = self.map_size - 1

    # Desestruturando a tupla em suas variáveis
    current_x, current_y = current_position
    possible_steps = {}
    
    # Se tiver um filtro, pesquisa pelo filtro. Caso contrário, pesquisa em todas as direções
    directions = search_for if search_for else [direction for direction in Direction]

    for direction in directions:

      remaining_steps = steps
      taken_steps = []
      
      if direction == Direction.UP or direction == Direction.DOWN:

        # Impede uma interação a toa caso o jogador já esteja no limite vertical do mapa
        if (direction == Direction.UP and current_y == min_index) or (direction == Direction.DOWN and current_y == max_index):
          continue
        

        # TODO: deixar essa lógica mais compacta e com menos if's
        offset = 1
        step = 1
        neighbours = 0
        while step < (steps + offset):
          new_y = max(current_y - step, min_index) if direction == Direction.UP else min(current_y + step, max_index)
          step_position = (current_x, new_y)
        
          if not self.has_player_at(step_position):
            taken_steps.append(step_position)
            remaining_steps -= 1

            # Reseta a contagem de vizinhos para não identificar de forma errônea
            neighbours = 0
          else:
            # Caso o lugar que o jogador esteja dando um passo seja um jogador
            # e já teve outro jogador na casa anterior, não há mais caminhos
            if neighbours == 1:
              break

            # Caso haja um jogador no lugar, ele salva pra verificar o próximo passo
            neighbours += 1

            # Caso o lugar que o jogador esteja dando um passo seja um jogador
            # ele não vai gastar esse passo
            offset += 1

          # A interação atingiu o final vertical do mapa
          if (direction == Direction.UP and new_y == min_index) or (direction == Direction.DOWN and new_y == max_index):
            break

          if remaining_steps == 0:
            break
            
          step += 1
      
      else: # Direções "left" ou "right"

        # Impede uma interação a toa caso o jogador já esteja no limite horizontal do mapa
        if (direction == Direction.LEFT and current_x == min_index) or (direction == Direction.RIGHT and current_x == max_index):
          continue
        
        offset = 1
        step = 1
        neighbours = 0
        while step < (steps + offset):
          new_x = max(current_x - step, min_index) if direction == Direction.LEFT else min(current_x + step, max_index)
          step_position = (new_x, current_y)
        
          if not self.has_player_at(step_position):
            taken_steps.append(step_position)
            remaining_steps -= 1

            neighbours = 0
          else:
              if neighbours == 1:
                break

              neighbours += 1

              offset += 1

          # A interação atingiu o final horizontal do mapa
          if (direction == Direction.LEFT and new_x == min_index) or (direction == Direction.RIGHT and new_x == max_index):
            break

          if remaining_steps == 0:
            break

          step += 1

      # Atualiza a lista de possíveis passos para a direção atual
      possible_steps[direction] = taken_steps
    
    return possible_steps


