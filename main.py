import pygame
import pymunk
import sys
from pymunk import Vec2d
from pymunk.pygame_util import DrawOptions
import math
import matplotlib.pyplot as plt

## Cosas a mejorar: 

# Todo lo relacionado a los dominós.
# Las medidas de energía.

# Inicialización de pygame y pymunk
pygame.init()
WIDTH = 1280
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Máquina de Goldberg - Simulación")

# Configuración del espacio físico
space = pymunk.Space()
space.gravity = (0, 980)
draw_options = DrawOptions(screen)

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)

# Origen dinámico
custom_origin = [0, HEIGHT]  # Inicialmente en la esquina inferior izquierda
fixed_origin = None  # Una vez iniciado, se fija aquí


# Funciones de transformación de coordenadas
def pymunk_to_pygame(p):
    """Transforma coordenadas de Pymunk a Pygame según el origen."""
    origin = fixed_origin if fixed_origin else custom_origin
    x = p[0] - origin[0]
    y = origin[1] - p[1]
    return int(x), int(y)

def pygame_to_pymunk(p):
    """Transforma coordenadas de Pygame a Pymunk según el origen."""
    origin = fixed_origin if fixed_origin else custom_origin
    x = p[0] + origin[0]
    y = origin[1] - p[1]
    return x, y





# Funciones de transformación de coordenadas
def pymunk_to_pygame(p):
    """Transforma coordenadas de Pymunk a Pygame según el origen fijo."""
    origin = fixed_origin if fixed_origin else custom_origin
    # Ajustar para que el origen fijo sea (0, 0)
    x = p[0] - origin[0]
    y = origin[1] - p[1]
    return int(x), int(y)


def pygame_to_pymunk(p):
    """Transforma coordenadas de Pygame a Pymunk según el origen fijo."""
    origin = fixed_origin if fixed_origin else custom_origin
    x = p[0] + origin[0]
    y = origin[1] - p[1]
    return x, y


# Actualización del origen dinámico al fijarlo
def fix_origin():
    """Fija el origen actual como origen absoluto (0, 0)."""
    global fixed_origin
    if not fixed_origin:
        fixed_origin = custom_origin.copy()
        custom_origin[0] = 0
        custom_origin[1] = 0

        
# Dibujar el marco de referencia
def draw_reference_frame():
    """Dibuja los ejes X e Y del marco de referencia dinámico."""
    origin = fixed_origin if fixed_origin else custom_origin
    pygame.draw.line(screen, RED, pymunk_to_pygame((0, 0)), pymunk_to_pygame((WIDTH, 0)), 2)  # Eje X
    pygame.draw.line(screen, GREEN, pymunk_to_pygame((0, 0)), pymunk_to_pygame((0, HEIGHT)), 2)  # Eje Y
    font = pygame.font.Font(None, 24)
    origin_text = font.render(f"Origen: ({custom_origin[0]}, {custom_origin[1]})", True, BLACK)
    screen.blit(origin_text, (10, 10))


class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.initial_val = initial_val
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
    
    def reset_to_initial(self, initial_val=None):
        if initial_val is not None:
            self.value = initial_val
        else:
            self.value = self.initial_val
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
        
        self.puntos_plataforma_inicial = [
            (50, 200),
            (200, 200)
        ]        
        self.puntos_plataforma_media = [
            (200, 202),
            (400, 350),
            (500, 350)
        ]
        
        self.puntos_plataforma2 = [
            (700, 300),
            (400, 550),
            (100, 550)
        ]
        
        self.slider_k = Slider(50, 50, 200, 10, 0, 15, 7.5, "K (N/m)")  
        self.slider_x = Slider(500, 50, 200, 10, 0, 15, 7.5, "X (m)")           
        self.slider_masa = Slider(50, 150, 200, 10, 0.5, 5, 1, "Masa")
        self.slider_radio = Slider(500, 150, 200, 10, 10, 40, 20, "Radio")
        self.slider_gravedad = Slider(900, 150, 200, 10, 0, 2000, 980, "Gravedad")
        self.start_button = Button(50, HEIGHT - 100, 100, 40, "Iniciar")
        self.reset_button = Button(50, HEIGHT - 50, 100, 40, "Reiniciar")
        
        self.simulacion_iniciada = False
        self.simulacion_pausada = False
        self.resorte_disparado = False
        self.dominoes = []
        self.domino_records = []
        self.tiempo_actual = 0
        self.tiempo_datos = []
        self.energia_potencial_datos = []
        self.energia_cinetica_datos = []
        
        self.setup_inicial()

## Funciones para calcular:

# Energias. HAY QUE DARLE SENTIDO A ESTO!!!

    def calcular_energia_potencial(self):
        k = self.slider_k.value
        x = self.slider_x.value
        energia_potencial = 0.5 * k * (x ** 2)
        return energia_potencial

    def calcular_energia_potencial_gravitacional(self):
        """Calcula la energía potencial gravitacional de la esfera."""
        m = self.cuerpo.mass  # Masa de la esfera
        g = self.slider_gravedad.value / 100  # Gravedad ajustada

        # Determinar la altura relativa al marco, ajustada por el radio de la esfera
        if fixed_origin:
            h = max(0, (fixed_origin[1] - self.cuerpo.position[1]) - self.slider_radio.value-8)
        else:
            h = max(0, (custom_origin[1] - self.cuerpo.position[1]) - self.slider_radio.value-8)

        return m * g * h

# Puse el / 10 xd porque yolo

    def calcular_energia_cinetica(self):
        """Calcula la energía cinética de la esfera."""
        v = self.cuerpo.velocity.length / 10  # Escalar la velocidad
        m = self.cuerpo.mass
        return 0.5 * m * (v ** 2)


    def calcular_fuerza(self):
        k = self.slider_k.value
        x = self.slider_x.value
        energia = 0.5 * k * (x ** 2)
        energia = min(energia, 1200)
        return energia

    def calcular_peso(self):
        return self.slider_masa.value * (self.slider_gravedad.value / 100)

    def actualizar_energias(self, delta_t):
        """Actualizar las energías con el marco fijo."""
        self.tiempo_actual += delta_t
        energia_cinetica = self.calcular_energia_cinetica()
        energia_potencial = self.calcular_energia_potencial_gravitacional()

        # Almacenar datos para graficar
        self.energia_cinetica_datos.append(energia_cinetica)
        self.energia_potencial_datos.append(energia_potencial)
        self.tiempo_datos.append(self.tiempo_actual)



## Funciones para mostrar información:

    def mostrar_posiciones(self, screen):
        """Mostrar las posiciones de los objetos con base en el origen fijo."""
        pos_esfera = pymunk_to_pygame(self.cuerpo.position)
        pos_texto = self.font.render(f"Posición Esfera: ({pos_esfera[0]/10}, {pos_esfera[1]})", True, BLACK)
        screen.blit(pos_texto, (WIDTH - 500, 350))

        # Mostrar posiciones de los dominós
        for i, domino in enumerate(self.dominoes):
            pos_domino = pymunk_to_pygame(domino.position)
            pos_texto = self.font.render(f"Posición Domino {i+1}: ({pos_domino[0]/10}, {pos_domino[1]})", True, BLACK)
            screen.blit(pos_texto, (WIDTH - 500, 400 + i * 20))


    def mostrar_fuerzas(self, screen):
        """Mostrar las fuerzas actuales en pantalla."""
        fuerza_resorte = self.calcular_fuerza()
        peso = self.calcular_peso()
        
        fuerza_texto = self.font.render(f"Fuerza Resorte: {fuerza_resorte:.1f} N", True, BLACK)
        screen.blit(fuerza_texto, (WIDTH - 300, 200))
        
        peso_texto = self.font.render(f"Peso: {peso:.1f} N", True, BLACK)
        screen.blit(peso_texto, (WIDTH - 300, 250))

    

    def mostrar_registros(self, screen):
        y_pos = 50
        for i, record in enumerate(self.domino_records):
            tiempo = f"Domino {i+1} - T: {record['tiempo']:.2f}s"
            pos = f"Pos: ({record['posicion'][0]:.1f}, {record['posicion'][1]:.1f})"
            vel = f"Vel: ({record['velocidad'][0]:.1f}, {record['velocidad'][1]:.1f})"
            texto = self.font.render(f"{tiempo} | {pos} | {vel}", True, BLACK)
            screen.blit(texto, (700, y_pos + i * 30))

    def detectar_colisiones(self):
        """Detectar colisiones y mostrar información ajustada al origen fijo."""
        for shape in space.shapes:
            if hasattr(shape, "body") and shape.body.is_sleeping:
                pos = pymunk_to_pygame(shape.body.position)
                print(f"Colisión detectada en posición: {pos}")

    def limpiar_espacio(self):
        for body in space.bodies:
            space.remove(body)
        for shape in space.shapes:
            space.remove(shape)
        
        space.gravity = (0, self.slider_gravedad.value)

    def graficar_energias(self):
        """Graficar las energías almacenadas."""
        if not self.tiempo_datos:
            return
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.tiempo_datos, self.energia_cinetica_datos, label="Energía Cinética", color="blue")
        plt.plot(self.tiempo_datos, self.energia_potencial_datos, label="Energía Potencial Gravitacional", color="green")
        plt.title("Energías durante la simulación")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Energía (J)")
        plt.legend()
        plt.grid(True)
        plt.show()

## Objetos:

# Superficie de contacto:

    def crear_suelo(self):
        segmento = pymunk.Segment(
            space.static_body,
            self.puntos_plataforma_inicial[0],      
            self.puntos_plataforma_inicial[1],    
            4
        )
        segmento.friction = 10.0
        segmento.elasticity = 0.5
        space.add(segmento)
        
        for i in range(len(self.puntos_plataforma_media)-1):
            segmento = pymunk.Segment(
                space.static_body,
                self.puntos_plataforma_media[i],      
                self.puntos_plataforma_media[i+1],    
                4
            )
            segmento.friction = 10.0
            segmento.elasticity = 0.5
            space.add(segmento)
        
        for i in range(len(self.puntos_plataforma2)-1):
            segmento = pymunk.Segment(
                space.static_body,
                self.puntos_plataforma2[i],      
                self.puntos_plataforma2[i+1],    
                4
            )
            segmento.friction = 1.0
            segmento.elasticity = 0.5
            space.add(segmento)

    def crear_plataforma_circular(self):
        center = (645, 215)
        radius = 100
        start_angle = 1
        end_angle = -2.5
        
        num_segments = 20
        points = []
        for i in range(num_segments + 1):
            angle = start_angle + (end_angle - start_angle) * (i / num_segments)
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
        
        for i in range(len(points) - 1):
            segment = pymunk.Segment(
                space.static_body,
                points[i],
                points[i + 1],
                4
            )
            segment.friction = 1.0
            segment.elasticity = 0.5
            space.add(segment)

## Objetos de interacción.

# Esfera

    def crear_esfera(self):
        if hasattr(self, 'cuerpo'):
            if self.cuerpo in space.bodies:
                space.remove(self.cuerpo)
            if self.forma in space.shapes:
                space.remove(self.forma)
            
        momento = pymunk.moment_for_circle(self.slider_masa.value, 0, self.slider_radio.value)
        self.cuerpo = pymunk.Body(self.slider_masa.value, momento)
        self.cuerpo.position = (50, 202 - self.slider_radio.value)
        
        self.forma = pymunk.Circle(self.cuerpo, self.slider_radio.value)
        self.forma.friction = 1.0
        self.forma.elasticity = 0.5
        self.forma.collision_type = 0  # Tipo de colisión para la esfera
        
        space.add(self.cuerpo, self.forma)

# Obstaculo 

    def crear_resorte(self):
        self.resorte_pos = Vec2d(10, 200 - self.slider_radio.value)
        self.resorte_length = 30

    def crear_resorte_2(self):
        self.resorte_pos = Vec2d(10, 50 - self.slider_radio.value)
        self.resorte_length = 30

    def crear_dominos(self):
        self.dominoes.clear()
        domino_width = 10
        domino_height = 60
        spacing = 10
        x_pos = 150
        y_pos = 515
        num_dominos = 5  # Número de dominós

        for i in range(num_dominos):
            body = pymunk.Body(1, pymunk.moment_for_box(1, (domino_width, domino_height)))
            body.position = (x_pos + i * (domino_width + spacing), y_pos)

            shape = pymunk.Poly.create_box(body, (domino_width, domino_height))
            shape.friction = 0.5
            space.add(body, shape)
            self.dominoes.append(body)

        #self.dominoes[0].angle = math.radians(0)

    def dibujar_resorte(self, screen):
        pygame.draw.rect(screen, BLACK, (0, 150, 20, 50))
        
        if not self.resorte_disparado:
            start_pos = self.resorte_pos
            end_pos = Vec2d(start_pos.x + self.resorte_length, start_pos.y)
            
            num_segments = 14
            segment_length = self.resorte_length / num_segments
            amplitude = 20
            
            points = [start_pos]
            for i in range(1, num_segments):
                t = i / num_segments
                x = start_pos.x + self.resorte_length * t
                y = start_pos.y
                
                if i % 2:
                    y += amplitude
                else:
                    y -= amplitude
                    
                points.append(Vec2d(x, y))
            
            points.append(end_pos)
            
            for i in range(len(points)-1):
                pygame.draw.line(screen, BLACK, 
                               (points[i].x, points[i].y),
                               (points[i+1].x, points[i+1].y), 2)
    
    def disparar_resorte(self):
        if not self.resorte_disparado:
            impulso = self.calcular_fuerza()
            self.cuerpo.apply_impulse_at_local_point((impulso, 0))
            self.resorte_disparado = True

    def dibujar(self, screen):
        screen.fill(WHITE)
        draw_reference_frame()  # Dibuja el marco de referencia
        # Dibujar plataformas
        pygame.draw.line(
            screen, 
            BLACK, 
            self.puntos_plataforma_inicial[0],
            self.puntos_plataforma_inicial[1],
            4
        )
        
        for i in range(len(self.puntos_plataforma_media)-1):
            pygame.draw.line(
                screen, 
                BLACK, 
                self.puntos_plataforma_media[i],
                self.puntos_plataforma_media[i+1],
                4
            )
        
        for i in range(len(self.puntos_plataforma2)-1):
            pygame.draw.line(
                screen, 
                BLACK, 
                self.puntos_plataforma2[i],
                self.puntos_plataforma2[i+1],
                4
            )
        
        # Dibujar controles
        self.slider_k.draw(screen, self.font)
        self.slider_x.draw(screen, self.font)
        self.slider_masa.draw(screen, self.font)
        self.slider_radio.draw(screen, self.font)
        self.slider_gravedad.draw(screen, self.font)  # Dibujar slider de gravedad
        self.start_button.draw(screen, self.font)
        self.reset_button.draw(screen, self.font)
        
         # Mostrar energías
        energia_potencial = self.calcular_energia_potencial()  # Energía potencial elástica
        energia_potencial_gravitacional = self.calcular_energia_potencial_gravitacional()  # Energía potencial gravitacional
        energia_cinetica = self.calcular_energia_cinetica()  # Energía cinética
        
        energia_texto = self.font.render(f"Energia Potencial (resorte): {energia_potencial/10:.1f} J", True, BLACK)
        screen.blit(energia_texto, (WIDTH-500, 600))
        
        energia_gravitacional_texto = self.font.render(f"Energia Pot. Gravitacional: {energia_potencial_gravitacional/10:.1f} J", True, BLACK)
        screen.blit(energia_gravitacional_texto, (WIDTH-500, 570))
        
        energia_cinetica_texto = self.font.render(f"Energia Cinética: {energia_cinetica/10:.1f} J", True, BLACK)
        screen.blit(energia_cinetica_texto, (WIDTH-500, 540))

        # Mostrar las posiciones
        self.mostrar_posiciones(screen)
        
        # Mostrar fuerzas
        self.mostrar_fuerzas(screen)
        
        # Dibujar energía actual
        energia_text = self.font.render(f"Energía: {self.calcular_fuerza():.1f}", True, BLACK)
        screen.blit(energia_text, (WIDTH//2 - 360, 50))
        
        # Dibujar peso actual
        peso_text = self.font.render(f"Peso: {self.calcular_peso():.1f} N", True, BLACK)
        screen.blit(peso_text, (WIDTH//2 - 360, 100))
        
        # Dibujar resorte
        self.dibujar_resorte(screen)
        
        # Dibujar esfera
        pos = self.cuerpo.position
        pygame.draw.circle(screen, BLUE, (int(pos.x), int(pos.y)), int(self.slider_radio.value))
        
        # Mostrar estado
        estado = "En Pausa" if self.simulacion_pausada else "En Ejecución" if self.simulacion_iniciada else "Esperando Inicio"
        estado_text = self.font.render(f"Estado: {estado}", True, BLACK)
        screen.blit(estado_text, (WIDTH//2 - 100, HEIGHT - 40))
        space.debug_draw(draw_options)

    def setup_inicial(self):
        global fixed_origin
        # Limpiar completamente el espacio
        self.limpiar_espacio()
        # Restablecer el origen dinámico
        fixed_origin = None
        # Crear elementos
        self.crear_suelo()
        self.crear_esfera()
        self.crear_plataforma_circular()
        self.crear_resorte()
        self.crear_dominos()  # Crear los dominós
        
        # Resetear estados
        self.simulacion_iniciada = False
        self.simulacion_pausada = False
        self.resorte_disparado = False
        self.start_button.clicked = False
        
        # Resetear sliders a sus valores iniciales
        self.slider_k.reset_to_initial()
        self.slider_x.reset_to_initial()
        self.slider_masa.reset_to_initial()
        self.slider_radio.reset_to_initial()
        self.slider_gravedad.reset_to_initial()

        # Llamar al método graficar antes de reiniciar
        if self.energia_cinetica_datos and self.energia_potencial_datos:
            self.graficar_energias()    

        # Resetear datos de energía y tiempo
        self.energia_cinetica_datos.clear()
        self.energia_potencial_datos.clear()
        self.tiempo_datos.clear()
        self.tiempo_actual = 0


def main():
    global fixed_origin  # Permite fijar el origen dinámico

    clock = pygame.time.Clock()
    sim = SimulacionGoldberg()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for slider in [sim.slider_k, sim.slider_x, sim.slider_masa, sim.slider_radio, sim.slider_gravedad]:
                    if slider.knob.collidepoint(mouse_pos):
                        slider.active = True
                if sim.reset_button.rect.collidepoint(mouse_pos):
                    sim.setup_inicial()
                
                if sim.start_button.rect.collidepoint(mouse_pos):
                    if not sim.simulacion_iniciada:
                        sim.simulacion_iniciada = True
                        sim.start_button.clicked = True
                        sim.disparar_resorte()
                    else:
                        sim.simulacion_pausada = not sim.simulacion_pausada
                
                if sim.reset_button.rect.collidepoint(mouse_pos):
                    sim.setup_inicial()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                for slider in [sim.slider_k, sim.slider_x, sim.slider_masa, sim.slider_radio, sim.slider_gravedad]:
                    slider.active = False
            
            elif event.type == pygame.MOUSEMOTION:
                for slider in [sim.slider_k, sim.slider_x, sim.slider_masa, sim.slider_radio, sim.slider_gravedad]:
                    if slider.active and not sim.simulacion_iniciada:
                        slider.update(pygame.mouse.get_pos())
                        if slider in [sim.slider_masa, sim.slider_radio]:
                            sim.crear_esfera()
                        elif slider == sim.slider_gravedad:  # Añadir esta condición
                            space.gravity = (0, sim.slider_gravedad.value)
            elif event.type == pygame.KEYDOWN:
                # Permitir mover el marco solo antes de iniciar la simulación
                if not sim.simulacion_iniciada:
                    if event.key == pygame.K_UP:
                        custom_origin[1] -= 10  # Marco sube
                    elif event.key == pygame.K_DOWN:
                        custom_origin[1] += 10  # Marco baja
                    elif event.key == pygame.K_LEFT:
                        custom_origin[0] += 10  # Marco a la izquierda
                    elif event.key == pygame.K_RIGHT:
                        custom_origin[0] -= 10  # Marco a la derecha
                    elif event.key == pygame.K_RETURN:  # Fijar el origen
                        fix_origin()


                    
        if sim.simulacion_iniciada and not sim.simulacion_pausada:
            space.step(1/60.0)
            sim.actualizar_energias(1 / 60.0)  # Registrar energías en cada frame
       # sim.detectar_colisiones()
        sim.dibujar(screen)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
