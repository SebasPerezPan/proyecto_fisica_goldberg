import pygame
import pymunk
import sys
from pymunk import Vec2d
import math

# Inicialización de pygame y pymunk
pygame.init()
WIDTH = 1920
HEIGHT = 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Máquina de Goldberg - Simulación Mejorada")

# Configuración del espacio físico
space = pymunk.Space()
space.gravity = (0, 10000)

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.active = False
        self.knob = pygame.Rect(self.get_knob_pos(), y - 10, 20, height + 20)
        
    def get_knob_pos(self):
        return self.rect.x + (self.rect.width * (self.value - self.min_val) / (self.max_val - self.min_val))
    
    def update(self, pos):
        if self.active:
            x = max(self.rect.x, min(pos[0], self.rect.right))
            self.value = self.min_val + (x - self.rect.x) * (self.max_val - self.min_val) / self.rect.width
            self.knob.centerx = x
    
    def reset_to_initial(self, initial_val):
        self.value = initial_val
        self.knob.centerx = self.get_knob_pos()
            
    def draw(self, screen, font):
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.knob)
        label_text = font.render(f"{self.label}: {self.value:.1f}", True, BLACK)
        screen.blit(label_text, (self.rect.x, self.rect.y - 30))

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.active = False
        self.clicked = False
        
    def draw(self, screen, font):
        color = GREEN if self.clicked else RED
        pygame.draw.rect(screen, color, self.rect)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class SimulacionGoldberg:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        
        # Crear controles
        self.slider_fuerza = Slider(50, 50, 200, 10, 1000, 10000, 5000, "Fuerza")
        self.slider_masa = Slider(750, 50, 200, 10, 0.5, 5, 1, "Masa")
        self.slider_radio = Slider(750, 150, 200, 10, 10, 40, 20, "Radio")
        self.start_button = Button(WIDTH//2 - 50, 50, 100, 40, "Iniciar")
        self.reset_button = Button(50, HEIGHT - 50, 100, 40, "Reiniciar")
        
        # Variables de estado
        self.simulacion_iniciada = False
        self.simulacion_pausada = False
        self.resorte_disparado = False
        self.setup_inicial()

    def setup_inicial(self):
        # Limpiar el espacio
        if hasattr(self, 'cuerpo'):
            space.remove(self.cuerpo, self.forma)
        
        # Crear elementos
        self.crear_suelo()
        self.crear_esfera()
        self.crear_resorte()
        
        # Resetear estados
        self.simulacion_iniciada = False
        self.simulacion_pausada = False
        self.resorte_disparado = False
        self.start_button.clicked = False
        
        # Resetear sliders a valores iniciales
        self.slider_fuerza.reset_to_initial(5000)
        self.slider_masa.reset_to_initial(1)
        self.slider_radio.reset_to_initial(20)

    def crear_suelo(self):
        suelo = pymunk.Segment(space.static_body, (50, 500), (950, 500), 4)
        suelo.friction = 1.0
        suelo.elasticity = 0.5
        space.add(suelo)

    def crear_esfera(self):
        if hasattr(self, 'cuerpo'):
            space.remove(self.cuerpo, self.forma)
            
        momento = pymunk.moment_for_circle(self.slider_masa.value, 0, self.slider_radio.value)
        self.cuerpo = pymunk.Body(self.slider_masa.value, momento)
        self.cuerpo.position = (200, 500 - self.slider_radio.value)
        
        self.forma = pymunk.Circle(self.cuerpo, self.slider_radio.value)
        self.forma.friction = 0.7
        self.forma.elasticity = 0.5
        
        space.add(self.cuerpo, self.forma)

    def crear_resorte(self):
        self.resorte_pos = Vec2d(100, 500 - self.slider_radio.value)
        self.resorte_length = 80  # Longitud del resorte dibujado

    def dibujar_resorte(self, screen):
        # Dibujar base del resorte
        pygame.draw.rect(screen, BLACK, (90, 450, 20, 50))
        
        if not self.resorte_disparado:
            start_pos = self.resorte_pos
            end_pos = Vec2d(start_pos.x + self.resorte_length, start_pos.y)
            
            # Número de zigzags
            num_segments = 10
            segment_length = self.resorte_length / num_segments
            
            # Amplitud del zigzag
            amplitude = 10
            
            # Calcular puntos del zigzag
            points = [start_pos]
            for i in range(1, num_segments):
                t = i / num_segments
                x = start_pos.x + self.resorte_length * t
                y = start_pos.y
                
                # Añadir offset zigzag
                if i % 2:
                    y += amplitude
                else:
                    y -= amplitude
                    
                points.append(Vec2d(x, y))
            
            points.append(end_pos)
            
            # Dibujar líneas deml resorte
            for i in range(len(points)-1):
                pygame.draw.line(screen, BLACK, 
                               (points[i].x, points[i].y),
                               (points[i+1].x, points[i+1].y), 2)

    def disparar_resorte(self):
        if not self.resorte_disparado:
            impulso = self.slider_fuerza.value
            self.cuerpo.apply_impulse_at_local_point((impulso, 0))
            self.resorte_disparado = True

    def dibujar(self, screen):
        screen.fill(WHITE)
        
        # Dibujar suelo
        pygame.draw.line(screen, BLACK, (50, 500), (950, 500), 4)
        
        # Dibujar controles
        self.slider_fuerza.draw(screen, self.font)
        self.slider_masa.draw(screen, self.font)
        self.slider_radio.draw(screen, self.font)
        self.start_button.draw(screen, self.font)
        self.reset_button.draw(screen, self.font)
        
        # Dibujar resorte
        self.dibujar_resorte(screen)
        
        # Dibujar esfera
        pos = self.cuerpo.position
        pygame.draw.circle(screen, BLUE, (int(pos.x), int(pos.y)), int(self.slider_radio.value))
        
        # Mostrar estado de la simulación
        estado = "En Pausa" if self.simulacion_pausada else "En Ejecución" if self.simulacion_iniciada else "Esperando Inicio"
        estado_text = self.font.render(f"Estado: {estado}", True, BLACK)
        screen.blit(estado_text, (WIDTH//2 - 100, HEIGHT - 40))

def main():
    clock = pygame.time.Clock()
    sim = SimulacionGoldberg()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # Verificar click en sliders
                for slider in [sim.slider_fuerza, sim.slider_masa, sim.slider_radio]:
                    if slider.knob.collidepoint(mouse_pos):
                        slider.active = True
                
                # Verificar click en botón de inicio/pausa
                if sim.start_button.rect.collidepoint(mouse_pos):
                    if not sim.simulacion_iniciada:
                        sim.simulacion_iniciada = True
                        sim.start_button.clicked = True
                        sim.disparar_resorte()
                    else:
                        sim.simulacion_pausada = not sim.simulacion_pausada
                
                # Verificar click en botón de reinicio
                if sim.reset_button.rect.collidepoint(mouse_pos):
                    space.remove(space.shapes)
                    space.remove(space.bodies)
                    sim.setup_inicial()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                # Desactivar todos los sliders
                for slider in [sim.slider_fuerza, sim.slider_masa, sim.slider_radio]:
                    slider.active = False
            
            elif event.type == pygame.MOUSEMOTION:
                # Actualizar posición de sliders activos
                for slider in [sim.slider_fuerza, sim.slider_masa, sim.slider_radio]:
                    if slider.active and not sim.simulacion_iniciada:
                        slider.update(pygame.mouse.get_pos())
                        # Si se modifica masa o radio, actualizar esfera
                        if slider in [sim.slider_masa, sim.slider_radio]:
                            sim.crear_esfera()

        # Actualizar física solo si la simulación ha iniciado y no está pausada
        if sim.simulacion_iniciada and not sim.simulacion_pausada:
            space.step(1/60.0)
        
        # Dibujar
        sim.dibujar(screen)
        pygame.display.flip()
        
        # Controlar FPS
        clock.tick(60)

if __name__ == "__main__":
    main()