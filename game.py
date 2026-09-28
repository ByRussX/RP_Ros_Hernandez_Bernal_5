"""
Tetris en Python con Pygame
============================
Características:
- Sistema de rotación y detección de colisiones fluido.
- Sistema de generación 7-Bag (estándar de Tetris).
- Proyección / Pieza fantasma (Ghost piece).
- Mecánica de Hold (Guardar pieza con 'C' o 'Shift').
- Previsualización de las siguientes 3 piezas.
- Animación de eliminación de líneas.
- Sistema de niveles, puntuación y récord local.
- Efectos de sonido retro sintetizados proceduralmente.
- Interfaz gráfica moderna con estilo arcade oscuro y bloques biselados 3D.
"""

import math
import random
import sys
import pygame
import numpy as np

# -------------------------------------------------------------
# Configuración y Constantes
# -------------------------------------------------------------
COLS = 10
ROWS = 20
BLOCK_SIZE = 32

BOARD_WIDTH = COLS * BLOCK_SIZE    # 320 px
BOARD_HEIGHT = ROWS * BLOCK_SIZE   # 640 px

SIDE_PANEL_LEFT_W = 160
SIDE_PANEL_RIGHT_W = 200
MARGIN = 24

SCREEN_WIDTH = SIDE_PANEL_LEFT_W + BOARD_WIDTH + SIDE_PANEL_RIGHT_W + MARGIN * 4
SCREEN_HEIGHT = BOARD_HEIGHT + MARGIN * 2
FPS = 60

# Paleta de colores (Estilo Cyberpunk / Neon Arcade)
COLOR_BG = (15, 17, 26)
COLOR_PANEL_BG = (22, 26, 40)
COLOR_PANEL_BORDER = (45, 55, 80)
COLOR_GRID_BG = (10, 12, 20)
COLOR_GRID_LINES = (25, 30, 48)
COLOR_TEXT_PRIMARY = (240, 243, 250)
COLOR_TEXT_MUTED = (140, 150, 175)
COLOR_ACCENT = (255, 180, 50)

# Colores de las piezas (Tetrominoes)
TETROMINO_COLORS = {
    'I': (0, 240, 240),     # Cyan
    'J': (0, 100, 255),     # Azul
    'L': (255, 140, 0),     # Naranja
    'O': (255, 220, 0),     # Amarillo
    'S': (50, 220, 50),     # Verde
    'T': (160, 40, 240),    # Morado / Violeta
    'Z': (240, 40, 40)      # Rojo
}

# Formas de las piezas (representadas como matrices 4x4 o 3x3)
SHAPES = {
    'I': [
        [[0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0]],
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0]]
    ],
    'J': [
        [[1, 0, 0],
         [1, 1, 1],
         [0, 0, 0]],
        [[0, 1, 1],
         [0, 1, 0],
         [0, 1, 0]],
        [[0, 0, 0],
         [1, 1, 1],
         [0, 0, 1]],
        [[0, 1, 0],
         [0, 1, 0],
         [1, 1, 0]]
    ],
    'L': [
        [[0, 0, 1],
         [1, 1, 1],
         [0, 0, 0]],
        [[0, 1, 0],
         [0, 1, 0],
         [0, 1, 1]],
        [[0, 0, 0],
         [1, 1, 1],
         [1, 0, 0]],
        [[1, 1, 0],
         [0, 1, 0],
         [0, 1, 0]]
    ],
    'O': [
        [[1, 1],
         [1, 1]]
    ],
    'S': [
        [[0, 1, 1],
         [1, 1, 0],
         [0, 0, 0]],
        [[0, 1, 0],
         [0, 1, 1],
         [0, 0, 1]],
        [[0, 0, 0],
         [0, 1, 1],
         [1, 1, 0]],
        [[1, 0, 0],
         [1, 1, 0],
         [0, 1, 0]]
    ],
    'T': [
        [[0, 1, 0],
         [1, 1, 1],
         [0, 0, 0]],
        [[0, 1, 0],
         [0, 1, 1],
         [0, 1, 0]],
        [[0, 0, 0],
         [1, 1, 1],
         [0, 1, 0]],
        [[0, 1, 0],
         [1, 1, 0],
         [0, 1, 0]]
    ],
    'Z': [
        [[1, 1, 0],
         [0, 1, 1],
         [0, 0, 0]],
        [[0, 0, 1],
         [0, 1, 1],
         [0, 1, 0]],
        [[0, 0, 0],
         [1, 1, 0],
         [0, 1, 1]],
        [[0, 1, 0],
         [1, 1, 0],
         [1, 0, 0]]
    ]
}


# -------------------------------------------------------------
# Generador de Sonidos Sintetizados (Retro SFX)
# -------------------------------------------------------------
class SoundManager:
    """Genera sonidos de estilo retro en memoria usando numpy y pygame.sndarray."""
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.sample_rate = 44100
            self.enabled = True
            self._generate_sounds()
        except Exception as e:
            print(f"Aviso: Sonido desactivado ({e})")
            self.enabled = False

    def _create_tone(self, freq_start, freq_end, duration_s, vol=0.25, waveform="sine"):
        n_samples = int(self.sample_rate * duration_s)
        t = np.linspace(0, duration_s, n_samples, False)
        freqs = np.linspace(freq_start, freq_end, n_samples)
        phase = 2 * np.pi * np.cumsum(freqs) / self.sample_rate

        if waveform == "sine":
            signal = np.sin(phase)
        elif waveform == "square":
            signal = np.sign(np.sin(phase))
        elif waveform == "sawtooth":
            signal = 2 * (phase / (2 * np.pi) - np.floor(phase / (2 * np.pi) + 0.5))
        elif waveform == "noise":
            signal = np.random.uniform(-1, 1, n_samples)
        else:
            signal = np.sin(phase)

        envelope = np.exp(-3 * t / duration_s)
        audio = (signal * envelope * vol * 32767).astype(np.int16)
        stereo = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound(stereo)

    def _generate_sounds(self):
        try:
            self.sounds['move'] = self._create_tone(320, 260, 0.04, vol=0.15, waveform="sine")
            self.sounds['rotate'] = self._create_tone(440, 580, 0.06, vol=0.18, waveform="sine")
            self.sounds['drop'] = self._create_tone(180, 80, 0.08, vol=0.25, waveform="sine")
            self.sounds['clear'] = self._create_tone(523, 784, 0.18, vol=0.28, waveform="square")
            self.sounds['tetris'] = self._create_tone(659, 1046, 0.35, vol=0.32, waveform="square")
            self.sounds['gameover'] = self._create_tone(300, 80, 0.5, vol=0.35, waveform="sawtooth")
            self.sounds['hold'] = self._create_tone(350, 480, 0.08, vol=0.18, waveform="sine")
        except Exception:
            self.enabled = False

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass


# -------------------------------------------------------------
# Clase Pieza (Tetromino)
# -------------------------------------------------------------
class Piece:
    def __init__(self, shape_name):
        self.shape_name = shape_name
        self.rotations = SHAPES[shape_name]
        self.color = TETROMINO_COLORS[shape_name]
        self.rotation_index = 0
        self.matrix = self.rotations[0]
        # Posición inicial centrada arriba
        self.x = (COLS - len(self.matrix[0])) // 2
        self.y = 0

    def rotate(self, clockwise=True):
        num_rot = len(self.rotations)
        if clockwise:
            new_index = (self.rotation_index + 1) % num_rot
        else:
            new_index = (self.rotation_index - 1) % num_rot
        return self.rotations[new_index], new_index

    def set_rotation(self, new_index):
        self.rotation_index = new_index
        self.matrix = self.rotations[self.rotation_index]


# -------------------------------------------------------------
# Clase Principal del Juego
# -------------------------------------------------------------
class TetrisGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris Arcade")
        self.clock = pygame.time.Clock()

        # Fuentes
        self.font_large = pygame.font.SysFont("segoeui,arial", 32, bold=True)
        self.font_medium = pygame.font.SysFont("segoeui,arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("segoeui,arial", 14)
        self.font_title = pygame.font.SysFont("segoeui,arial", 40, bold=True)

        self.sound = SoundManager()
        self.high_score = 0
        self.reset()

    def reset(self):
        # Tablero 20x10 lleno de None (vacío)
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.bag = []
        self.next_pieces = [self._draw_from_bag() for _ in range(3)]
        self.current_piece = self._draw_from_bag()
        self.hold_piece = None
        self.can_hold = True

        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False

        self.fall_time = 0
        self.clearing_lines = []
        self.clear_anim_time = 0

    def _draw_from_bag(self):
        """Bolsa de 7 piezas aleatorias (Random Generator Tetris Guideline)."""
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        shape = self.bag.pop()
        return Piece(shape)

    def _get_fall_speed(self):
        """Milisegundos entre caídas por gravedad según el nivel."""
        speed = max(100, 800 - (self.level - 1) * 65)
        return speed

    def valid_position(self, piece, offset_x=0, offset_y=0, test_matrix=None):
        matrix = test_matrix if test_matrix is not None else piece.matrix
        for r, row in enumerate(matrix):
            for c, val in enumerate(row):
                if val:
                    new_x = piece.x + c + offset_x
                    new_y = piece.y + r + offset_y
                    if new_x < 0 or new_x >= COLS:
                        return False
                    if new_y >= ROWS:
                        return False
                    if new_y >= 0 and self.board[new_y][new_x] is not None:
                        return False
        return True

    def rotate_current(self, clockwise=True):
        new_matrix, new_index = self.current_piece.rotate(clockwise)
        # Intentos de Wall-Kick básico (desplazamientos de ajuste)
        kicks = [(0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0)]
        for kx, ky in kicks:
            if self.valid_position(self.current_piece, offset_x=kx, offset_y=ky, test_matrix=new_matrix):
                self.current_piece.x += kx
                self.current_piece.y += ky
                self.current_piece.set_rotation(new_index)
                self.sound.play('rotate')
                return True
        return False

    def hold(self):
        if not self.can_hold or self.game_over or self.paused:
            return
        self.sound.play('hold')
        current_shape = self.current_piece.shape_name
        if self.hold_piece is None:
            self.hold_piece = Piece(current_shape)
            self.spawn_next_piece()
        else:
            prev_hold = self.hold_piece.shape_name
            self.hold_piece = Piece(current_shape)
            self.current_piece = Piece(prev_hold)
        self.can_hold = False

    def get_ghost_y(self):
        """Calcula la fila de aterrizaje de la pieza fantasma."""
        offset_y = 0
        while self.valid_position(self.current_piece, offset_y=offset_y + 1):
            offset_y += 1
        return self.current_piece.y + offset_y

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        drop_dist = 0
        while self.valid_position(self.current_piece, offset_y=1):
            self.current_piece.y += 1
            drop_dist += 1
        self.score += drop_dist * 2
        self.sound.play('drop')
        self.lock_piece()

    def lock_piece(self):
        # Bloquear pieza actual en el tablero
        matrix = self.current_piece.matrix
        for r, row in enumerate(matrix):
            for c, val in enumerate(row):
                if val:
                    bx = self.current_piece.x + c
                    by = self.current_piece.y + r
                    if by < 0:
                        self.game_over = True
                    else:
                        self.board[by][bx] = self.current_piece.color

        if not self.game_over:
            # Comprobar líneas completas
            lines_to_clear = [i for i, row in enumerate(self.board) if all(cell is not None for cell in row)]
            if lines_to_clear:
                self.clearing_lines = lines_to_clear
                self.clear_anim_time = 180  # ms de animación de flash
                # Sonido correspondiente
                if len(lines_to_clear) >= 4:
                    self.sound.play('tetris')
                else:
                    self.sound.play('clear')
            else:
                self.spawn_next_piece()
        else:
            self.sound.play('gameover')

    def spawn_next_piece(self):
        self.current_piece = self.next_pieces.pop(0)
        self.next_pieces.append(self._draw_from_bag())
        self.can_hold = True
        self.fall_time = 0

        # Si al aparecer ya colisiona, se termina el juego
        if not self.valid_position(self.current_piece):
            self.game_over = True
            self.sound.play('gameover')

    def clear_full_lines(self):
        lines_count = len(self.clearing_lines)
        if lines_count == 0:
            return

        # Puntuaciones clásicas de Tetris
        pts = {1: 100, 2: 300, 3: 500, 4: 800}.get(lines_count, 100 * lines_count)
        self.score += pts * self.level
        if self.score > self.high_score:
            self.high_score = self.score

        self.lines_cleared += lines_count
        self.level = (self.lines_cleared // 10) + 1

        # Eliminar y desplazar líneas hacia abajo
        new_board = [row for i, row in enumerate(self.board) if i not in self.clearing_lines]
        for _ in range(lines_count):
            new_board.insert(0, [None for _ in range(COLS)])
        self.board = new_board
        self.clearing_lines = []

        self.spawn_next_piece()

    # ---------------------------------------------------------
    # Renderizado y Gráficos
    # ---------------------------------------------------------
    def draw_block(self, surface, x, y, color, is_ghost=False, size=BLOCK_SIZE):
        """Dibuja un bloque con efecto de bisel 3D e iluminación."""
        rect = pygame.Rect(x, y, size, size)
        if is_ghost:
            # Dibujar contorno elegante para la pieza fantasma
            ghost_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(ghost_surface, (*color, 80), (2, 2, size - 4, size - 4), border_radius=4)
            pygame.draw.rect(ghost_surface, (*color, 180), (2, 2, size - 4, size - 4), width=2, border_radius=4)
            surface.blit(ghost_surface, (x, y))
            return

        # Color base del bloque
        pygame.draw.rect(surface, color, rect, border_radius=4)

        # Colores de brillo y sombra
        light_color = [min(255, int(c * 1.35) + 30) for c in color]
        dark_color = [max(0, int(c * 0.65)) for c in color]

        # Resaltado superior e izquierdo
        pygame.draw.polygon(surface, light_color, [
            (x, y),
            (x + size, y),
            (x + size - 4, y + 4),
            (x + 4, y + 4),
            (x + 4, y + size - 4),
            (x, y + size)
        ])

        # Sombra inferior y derecha
        pygame.draw.polygon(surface, dark_color, [
            (x + size, y),
            (x + size, y + size),
            (x, y + size),
            (x + 4, y + size - 4),
            (x + size - 4, y + size - 4),
            (x + size - 4, y + 4)
        ])

        # Centro suave
        inner_rect = pygame.Rect(x + 4, y + 4, size - 8, size - 8)
        pygame.draw.rect(surface, color, inner_rect, border_radius=2)

    def draw_piece_preview(self, surface, piece, center_x, center_y, box_size=20):
        if not piece:
            return
        matrix = piece.rotations[0]
        rows = len(matrix)
        cols = len(matrix[0])
        start_x = center_x - (cols * box_size) // 2
        start_y = center_y - (rows * box_size) // 2

        for r, row in enumerate(matrix):
            for c, val in enumerate(row):
                if val:
                    bx = start_x + c * box_size
                    by = start_y + r * box_size
                    self.draw_block(surface, bx, by, piece.color, size=box_size)

    def draw_panel(self, surface, rect, title=""):
        """Dibuja un panel redondeado con estilo oscuro y borde suave."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=2, border_radius=10)
        if title:
            lbl = self.font_medium.render(title, True, COLOR_TEXT_MUTED)
            surface.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.y + 12))

    def render(self):
        self.screen.fill(COLOR_BG)

        board_x = MARGIN + SIDE_PANEL_LEFT_W + MARGIN
        board_y = MARGIN

        # 1. Panel Izquierdo: HOLD y TECLAS
        hold_rect = pygame.Rect(MARGIN, MARGIN, SIDE_PANEL_LEFT_W, 140)
        self.draw_panel(self.screen, hold_rect, "HOLD (C)")
        if self.hold_piece:
            self.draw_piece_preview(self.screen, self.hold_piece, hold_rect.centerx, hold_rect.y + 80)

        # Panel de Controles
        controls_rect = pygame.Rect(MARGIN, MARGIN + 160, SIDE_PANEL_LEFT_W, BOARD_HEIGHT - 160)
        self.draw_panel(self.screen, controls_rect, "CONTROLES")

        controls_list = [
            ("← / →", "Mover"),
            ("↑ / X", "Rotar Der."),
            ("Z", "Rotar Izq."),
            ("↓", "Bajar suave"),
            ("ESPACIO", "Caída rápida"),
            ("C / Shift", "Guardar"),
            ("P / Esc", "Pausar"),
            ("R", "Reiniciar")
        ]
        curr_y = controls_rect.y + 50
        for key_text, desc_text in controls_list:
            k_surf = self.font_small.render(key_text, True, COLOR_ACCENT)
            d_surf = self.font_small.render(desc_text, True, COLOR_TEXT_MUTED)
            self.screen.blit(k_surf, (controls_rect.x + 14, curr_y))
            self.screen.blit(d_surf, (controls_rect.x + 14, curr_y + 16))
            curr_y += 42

        # 2. Tablero Central de Juego
        board_rect = pygame.Rect(board_x, board_y, BOARD_WIDTH, BOARD_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_GRID_BG, board_rect, border_radius=6)

        # Líneas de cuadrícula sutiles
        for c in range(COLS + 1):
            gx = board_x + c * BLOCK_SIZE
            pygame.draw.line(self.screen, COLOR_GRID_LINES, (gx, board_y), (gx, board_y + BOARD_HEIGHT), 1)
        for r in range(ROWS + 1):
            gy = board_y + r * BLOCK_SIZE
            pygame.draw.line(self.screen, COLOR_GRID_LINES, (board_x, gy), (board_x + BOARD_WIDTH, gy), 1)

        # Bloques fijados en el tablero
        for r in range(ROWS):
            for c in range(COLS):
                cell_color = self.board[r][c]
                if cell_color is not None:
                    # Si la fila está siendo eliminada, parpadea en blanco
                    if r in self.clearing_lines:
                        flash_rect = pygame.Rect(board_x + c * BLOCK_SIZE, board_y + r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                        pygame.draw.rect(self.screen, (255, 255, 255), flash_rect, border_radius=2)
                    else:
                        self.draw_block(self.screen, board_x + c * BLOCK_SIZE, board_y + r * BLOCK_SIZE, cell_color)

        # Si no hay animación de borrado y el juego sigue, dibujar fantasma y pieza activa
        if not self.clearing_lines and not self.game_over:
            # Pieza fantasma (Ghost piece)
            ghost_y = self.get_ghost_y()
            for r, row in enumerate(self.current_piece.matrix):
                for c, val in enumerate(row):
                    if val:
                        bx = board_x + (self.current_piece.x + c) * BLOCK_SIZE
                        by = board_y + (ghost_y + r) * BLOCK_SIZE
                        self.draw_block(self.screen, bx, by, self.current_piece.color, is_ghost=True)

            # Pieza actual
            for r, row in enumerate(self.current_piece.matrix):
                for c, val in enumerate(row):
                    if val:
                        bx = board_x + (self.current_piece.x + c) * BLOCK_SIZE
                        by = board_y + (self.current_piece.y + r) * BLOCK_SIZE
                        if by >= board_y:
                            self.draw_block(self.screen, bx, by, self.current_piece.color)

        # Borde exterior del tablero
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, board_rect, width=3, border_radius=6)

        # 3. Panel Derecho: NEXT, SCORE, NIVEL, LÍNEAS
        right_panel_x = board_x + BOARD_WIDTH + MARGIN

        # Panel Siguiente (Next)
        next_rect = pygame.Rect(right_panel_x, MARGIN, SIDE_PANEL_RIGHT_W, 250)
        self.draw_panel(self.screen, next_rect, "SIGUIENTES")
        preview_y = next_rect.y + 60
        for i, npiece in enumerate(self.next_pieces):
            self.draw_piece_preview(self.screen, npiece, next_rect.centerx, preview_y, box_size=18)
            preview_y += 65

        # Panel de Puntuación
        stats_rect = pygame.Rect(right_panel_x, MARGIN + 270, SIDE_PANEL_RIGHT_W, BOARD_HEIGHT - 270)
        self.draw_panel(self.screen, stats_rect, "ESTADÍSTICAS")

        stat_items = [
            ("PUNTOS", f"{self.score:,}"),
            ("RÉCORD", f"{self.high_score:,}"),
            ("NIVEL", str(self.level)),
            ("LÍNEAS", str(self.lines_cleared))
        ]
        sy = stats_rect.y + 55
        for label, val in stat_items:
            lbl_surf = self.font_small.render(label, True, COLOR_TEXT_MUTED)
            val_surf = self.font_large.render(val, True, COLOR_TEXT_PRIMARY)
            self.screen.blit(lbl_surf, (stats_rect.x + 18, sy))
            self.screen.blit(val_surf, (stats_rect.x + 18, sy + 18))
            sy += 65

        # 4. Mensajes Overlay: Pausa o Fin de Partida (Game Over)
        if self.game_over:
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (board_x, board_y))

            t1 = self.font_title.render("GAME OVER", True, (255, 60, 60))
            t2 = self.font_medium.render(f"Puntos: {self.score:,}", True, COLOR_TEXT_PRIMARY)
            t3 = self.font_small.render("Pulsa 'R' para reiniciar", True, COLOR_ACCENT)

            self.screen.blit(t1, (board_x + (BOARD_WIDTH - t1.get_width()) // 2, board_y + 220))
            self.screen.blit(t2, (board_x + (BOARD_WIDTH - t2.get_width()) // 2, board_y + 280))
            self.screen.blit(t3, (board_x + (BOARD_WIDTH - t3.get_width()) // 2, board_y + 330))

        elif self.paused:
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (board_x, board_y))

            t1 = self.font_title.render("PAUSA", True, COLOR_ACCENT)
            t2 = self.font_small.render("Pulsa 'P' para continuar", True, COLOR_TEXT_PRIMARY)

            self.screen.blit(t1, (board_x + (BOARD_WIDTH - t1.get_width()) // 2, board_y + 250))
            self.screen.blit(t2, (board_x + (BOARD_WIDTH - t2.get_width()) // 2, board_y + 310))

        pygame.display.flip()

    # ---------------------------------------------------------
    # Bucle Principal de Eventos y Lógica
    # ---------------------------------------------------------
    def run(self):
        # Repetición de teclas (DAS - Delayed Auto Shift): 160ms inicio, 40ms repetición
        pygame.key.set_repeat(160, 40)

        running = True
        while running:
            delta_ms = self.clock.tick(FPS)

            # Manejo de animación de líneas eliminadas
            if self.clearing_lines:
                self.clear_anim_time -= delta_ms
                if self.clear_anim_time <= 0:
                    self.clear_full_lines()
                self.render()
                continue

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        if not self.game_over:
                            self.paused = not self.paused

                    elif event.key == pygame.K_r:
                        self.reset()

                    elif not self.game_over and not self.paused:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            if self.valid_position(self.current_piece, offset_x=-1):
                                self.current_piece.x -= 1
                                self.sound.play('move')

                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            if self.valid_position(self.current_piece, offset_x=1):
                                self.current_piece.x += 1
                                self.sound.play('move')

                        elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_x):
                            self.rotate_current(clockwise=True)

                        elif event.key == pygame.K_z:
                            self.rotate_current(clockwise=False)

                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            if self.valid_position(self.current_piece, offset_y=1):
                                self.current_piece.y += 1
                                self.score += 1
                                self.fall_time = 0

                        elif event.key == pygame.K_SPACE:
                            self.hard_drop()

                        elif event.key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
                            self.hold()

            # Lógica de caída por gravedad
            if not self.game_over and not self.paused and not self.clearing_lines:
                self.fall_time += delta_ms
                if self.fall_time >= self._get_fall_speed():
                    self.fall_time = 0
                    if self.valid_position(self.current_piece, offset_y=1):
                        self.current_piece.y += 1
                    else:
                        self.lock_piece()

            self.render()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = TetrisGame()
    game.run()
