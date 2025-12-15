from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

camera_pos = [0, 500, 500]
fovY = 120
GRID_LENGTH = 600
rand_var = 423

cam_mode = 1

top_down_cam_height = 800
top_down_cam_angle = 0
top_down_cam_radius = 50 

WORLD_WIDTH = 1600
WORLD_HEIGHT = 1600
PARKING_SPOT_SIZE = 50
MAX_HEALTH = 100
OBSTACLE_COUNT = 45
PEDESTRIAN_COUNT = 24
MOVING_CAR_COUNT = 12

weather_types = ['SUNNY', 'RAIN', 'NIGHT']
current_weather_idx = 0
rain_drops = []
NUM_RAIN_DROPS = 250

vehicle_types = {
    'SEDAN': {
        'length': 40, 'width': 20, 'max_speed': 8, 'acceleration': 0.3,
        'turn_rate': 4, 'brake_power': 0.5, 'color': [0.8, 0.2, 0.2]
    },
    'SUV': {
        'length': 50, 'width': 25, 'max_speed': 6, 'acceleration': 0.2,
        'turn_rate': 3, 'brake_power': 0.7, 'color': [0.2, 0.6, 0.2]
    },
    'SPORTS_CAR': {
        'length': 35, 'width': 18, 'max_speed': 12, 'acceleration': 0.5,
        'turn_rate': 6, 'brake_power': 0.8, 'color': [0.8, 0.8, 0.2]
    },
    'TRUCK': {
        'length': 60, 'width': 30, 'max_speed': 4, 'acceleration': 0.15,
        'turn_rate': 2, 'brake_power': 0.4, 'color': [0.4, 0.4, 0.8]
    }
}

player_vehicle = {
    'pos': [0, 0, 5], 'angle': 0, 'speed': 0, 'max_speed': 8,
    'acceleration': 0.3, 'turn_rate': 4, 'brake_power': 0.5,
    'health': MAX_HEALTH, 'gear': 'DRIVE', 'type': 'SEDAN',
    'length': 40, 'width': 20, 'damage_level': 0
}

game_status = {
    'score': 0, 'level': 1, 'time_left': 60, 'game_over': False,
    'paused': False, 'level_complete': False, 'mode': 'CLASSIC',
    'collisions': 0, 'cheat_mode': False
}

parking_slots = []
current_parking_slot = None

static_barriers = []
moving_vehicles = []
walkers = []

skid_marks = []
collision_sparks = []

last_frame_time = 0

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def init_rain():
    global rain_drops
    rain_drops.clear()
    for _ in range(NUM_RAIN_DROPS):
        rain_drops.append({
            'pos': [random.uniform(-WORLD_WIDTH/2, WORLD_WIDTH/2),
                    random.uniform(-WORLD_HEIGHT/2, WORLD_HEIGHT/2),
                    random.uniform(10, 400)],
            'speed': random.uniform(10, 15)
        })

def init_level(level_num):
    global static_barriers, walkers, moving_vehicles, parking_slots, current_parking_slot
    
    static_barriers.clear()
    walkers.clear()
    moving_vehicles.clear()
    parking_slots.clear()
    
    for i in range(OBSTACLE_COUNT + level_num * 2):
        barrier = {
            'pos': [random.uniform(-WORLD_WIDTH//2 + 50, WORLD_WIDTH//2 - 50),
                    random.uniform(-WORLD_HEIGHT//2 + 50, WORLD_HEIGHT//2 - 50), 5],
            'type': random.choice(['CONE', 'BARRIER', 'WALL', 'PILLAR']),
            'size': random.uniform(10, 25),
            'color': [random.uniform(0.5, 1.0), random.uniform(0.3, 0.8), 0.2],
            'health': 100
        }
        static_barriers.append(barrier)
    
    for i in range(MOVING_CAR_COUNT):
        moving_vehicle = {
            'pos': [random.uniform(-WORLD_WIDTH//2 + 100, WORLD_WIDTH//2 - 100),
                    random.uniform(-WORLD_HEIGHT//2 + 100, WORLD_HEIGHT//2 - 100), 5],
            'angle': random.uniform(0, 360), 'speed': random.uniform(0.2, 0.5),
            'path': [[random.uniform(-WORLD_WIDTH//2 + 50, WORLD_WIDTH//2 - 50),
                      random.uniform(-WORLD_HEIGHT//2 + 50, WORLD_HEIGHT//2 - 50)] for _ in range(5)],
            'path_idx': 0, 'type': random.choice(list(vehicle_types.keys())), 'active': True
        }
        moving_vehicles.append(moving_vehicle)
    
    for i in range(PEDESTRIAN_COUNT):
        walker = {
            'pos': [random.uniform(-WORLD_WIDTH//2 + 50, WORLD_WIDTH//2 - 50),
                    random.uniform(-WORLD_HEIGHT//2 + 50, WORLD_HEIGHT//2 - 50), 2],
            'angle': random.uniform(0, 360), 'speed': random.uniform(0.5, 2.0),
            'path': [[random.uniform(-WORLD_WIDTH//2 + 30, WORLD_WIDTH//2 - 30),
                      random.uniform(-WORLD_HEIGHT//2 + 30, WORLD_HEIGHT//2 - 30)] for _ in range(3)],
            'path_idx': 0, 'active': True,
            'safety_distance': 60,
            'color': [random.uniform(0.3, 0.8), random.uniform(0.3, 0.8), random.uniform(0.3, 0.8)]
        }
        walkers.append(walker)
    
    parking_slot = {
        'pos': [random.uniform(-WORLD_WIDTH//2 + 100, WORLD_WIDTH//2 - 100),
                random.uniform(-WORLD_HEIGHT//2 + 100, WORLD_HEIGHT//2 - 100), 0],
        'angle': random.choice([0, 45, 90, 135, 180]),
        'size': [PARKING_SPOT_SIZE + 10, PARKING_SPOT_SIZE + 10]
    }
    current_parking_slot = parking_slot
    parking_slots.append(parking_slot)
    
    player_vehicle['pos'] = [0, -200, 5]
    init_rain()

def distance_2d(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def get_obb_corners(center, width, height, angle):
    corners = []
    angle_rad, cos_a, sin_a = math.radians(angle), math.cos(math.radians(angle)), math.sin(math.radians(angle))
    hw, hh = width / 2, height / 2
    local_corners = [[hw, hh], [-hw, hh], [-hw, -hh], [hw, -hh]]
    for lx, ly in local_corners:
        corners.append([center[0] + lx * cos_a - ly * sin_a, center[1] + lx * sin_a + ly * cos_a])
    return corners

def is_point_inside_obb(point, obb_center, obb_width, obb_height, obb_angle):
    dx, dy = point[0] - obb_center[0], point[1] - obb_center[1]
    angle_rad = math.radians(-obb_angle)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    local_x, local_y = dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a
    return abs(local_x) <= obb_width / 2 and abs(local_y) <= obb_height / 2

def apply_weather_color(original_color):
    weather = weather_types[current_weather_idx]
    if weather == 'NIGHT':
        return [c * 0.3 for c in original_color]
    elif weather == 'RAIN':
        return [c * 0.6 for c in original_color]
    return original_color

def draw_vehicle(vehicle_data, is_player=False):
    glPushMatrix()
    glTranslatef(vehicle_data['pos'][0], vehicle_data['pos'][1], vehicle_data['pos'][2])
    glRotatef(vehicle_data['angle'], 0, 0, 1)
    
    vehicle_type = vehicle_types[vehicle_data['type']]
    length, width, color = vehicle_type['length'], vehicle_type['width'], list(vehicle_type['color'])
    
    if is_player and player_vehicle['damage_level'] > 0:
        damage_factor = 1.0 - (player_vehicle['damage_level'] / MAX_HEALTH) * 0.5
        color = [c * damage_factor for c in color]
    
    final_color = apply_weather_color(color)
    glColor3f(*final_color)
    
    glPushMatrix()
    glScalef(length, width, 8)
    glutSolidCube(1)
    glPopMatrix()
    
    cabin_color = apply_weather_color([0.6, 0.8, 1.0])
    glColor3f(*cabin_color)
    glPushMatrix()
    glTranslatef(length * 0.1, 0, 6)
    glScalef(length * 0.5, width * 0.9, 6)
    glutSolidCube(1)
    glPopMatrix()
    
    wheel_color = apply_weather_color([0.1, 0.1, 0.1])
    glColor3f(*wheel_color)
    quad = gluNewQuadric()
    wheel_positions = [
        [length * 0.35, width * 0.5, 0], [length * 0.35, -width * 0.5, 0],
        [-length * 0.35, width * 0.5, 0], [-length * 0.35, -width * 0.5, 0]
    ]
    for wheel_pos in wheel_positions:
        glPushMatrix()
        glTranslatef(*wheel_pos)
        glRotatef(90, 0, 1, 0)
        gluCylinder(quad, 4, 4, 3, 12, 1)
        glPopMatrix()
    
    if is_player and weather_types[current_weather_idx] == 'NIGHT':
        glColor3f(1, 1, 0.5)
        glPushMatrix()
        glTranslatef(length * 0.5, width * 0.3, 2)
        glutSolidSphere(2.5, 8, 8)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(length * 0.5, -width * 0.3, 2)
        glutSolidSphere(2.5, 8, 8)
        glPopMatrix()

    glPopMatrix()

def draw_obstacle(obstacle):
    glPushMatrix()
    glTranslatef(obstacle['pos'][0], obstacle['pos'][1], 0)
    final_color = apply_weather_color(obstacle['color'])
    glColor3f(*final_color)
    quad = gluNewQuadric()
    if obstacle['type'] == 'CONE':
        gluCylinder(quad, obstacle['size'], 0, obstacle['size'] * 2, 8, 1)
    elif obstacle['type'] == 'BARRIER':
        glScalef(obstacle['size'] * 2, obstacle['size'] * 0.5, obstacle['size'])
        glutSolidCube(1)
    elif obstacle['type'] == 'WALL':
        glScalef(obstacle['size'], obstacle['size'] * 0.2, obstacle['size'] * 2)
        glutSolidCube(1)
    elif obstacle['type'] == 'PILLAR':
        gluCylinder(quad, obstacle['size'] * 0.5, obstacle['size'] * 0.5, obstacle['size'] * 3, 12, 1)
    glPopMatrix()

def draw_walker(walker):
    glPushMatrix()
    glTranslatef(walker['pos'][0], walker['pos'][1], 10)
    body_color = apply_weather_color(walker['color'])
    glColor3f(*body_color)
    glPushMatrix()
    glScalef(4, 4, 15)
    glutSolidCube(1)
    glPopMatrix()
    head_color = apply_weather_color([0.9, 0.7, 0.5])
    glColor3f(*head_color)
    glTranslatef(0, 0, 11)
    glutSolidSphere(4, 8, 8)
    glPopMatrix()

def draw_environment():
    road_color = apply_weather_color([0.3, 0.3, 0.3])
    glColor3f(*road_color)
    glPushMatrix()
    glTranslatef(0, 0, -1)
    glScalef(WORLD_WIDTH, WORLD_HEIGHT, 1)
    glutSolidCube(1)
    glPopMatrix()

    line_color = apply_weather_color([0.9, 0.9, 0.9])
    glColor3f(*line_color)
    for y in range(-WORLD_HEIGHT//2, WORLD_HEIGHT//2, 100):
        for x in range(-WORLD_WIDTH//2, WORLD_WIDTH//2, 50):
            glPushMatrix()
            glTranslatef(x + 12.5, y, 0.1)
            glScalef(25, 4, 1)
            glutSolidCube(1)
            glPopMatrix()

def draw_parking_slot():
    if not current_parking_slot: return
    slot = current_parking_slot
    glPushMatrix()
    glTranslatef(slot['pos'][0], slot['pos'][1], slot['pos'][2])
    glRotatef(slot['angle'], 0, 0, 1)
    brightness = 0.6 + 0.4 * math.sin(time.time() * 5)
    slot_color = apply_weather_color([0, brightness, 0])
    glColor3f(*slot_color)
    glScalef(slot['size'][0], slot['size'][1], 1)
    glutSolidCube(1)
    glPopMatrix()

def draw_skid_marks():
    debris_color = apply_weather_color([0.1, 0.1, 0.1])
    glColor3f(*debris_color)
    for mark in skid_marks:
        glPushMatrix()
        glTranslatef(mark['pos'][0], mark['pos'][1], 0.1)
        glScalef(2, 2, 0.5)
        glutSolidCube(1)
        glPopMatrix()

def draw_collision_sparks():
    for spark in collision_sparks:
        glPushMatrix()
        glColor3f(*spark['color'])
        glTranslatef(spark['pos'][0], spark['pos'][1], spark['pos'][2])
        glutSolidSphere(1.5, 6, 6)
        glPopMatrix()

def draw_rain():
    if weather_types[current_weather_idx] != 'RAIN':
        return
    glColor3f(0.5, 0.6, 0.8)
    quad = gluNewQuadric()
    for drop in rain_drops:
        glPushMatrix()
        glTranslatef(drop['pos'][0], drop['pos'][1], drop['pos'][2])
        gluCylinder(quad, 0.2, 0.2, 15, 4, 1)
        glPopMatrix()

def draw_hud():
    speed_kmh = abs(player_vehicle['speed']) * 10
    draw_text(10, 770, f"Speed: {speed_kmh:.0f} km/h")
    draw_text(10, 750, f"Health: {player_vehicle['health']:.0f}%")
    draw_text(10, 730, f"Gear: {player_vehicle['gear']}")
    draw_text(10, 710, f"Score: {game_status['score']}")
    draw_text(10, 690, f"Time: {game_status['time_left']:.1f}s")
    draw_text(10, 670, f"Weather: {weather_types[current_weather_idx]} (O)")
    
    cam_modes = ['Top-Down (Orbit)', 'Third-Person', 'First-Person']
    draw_text(800, 770, f"Camera: {cam_modes[cam_mode]} (C)")
    draw_text(800, 750, f"Vehicle: {player_vehicle['type']}")

    if game_status['game_over']:
        draw_text(450, 400, "GAME OVER")
        draw_text(430, 370, "Press R to restart")
    if game_status['level_complete']:
        draw_text(420, 400, "LEVEL COMPLETE!")
        draw_text(410, 370, "Press N for next level")
    if game_status['paused']:
        draw_text(470, 400, "PAUSED")

def update_vehicle_physics(dt):
    if game_status['paused'] or game_status['game_over']: return
    vehicle = player_vehicle
    time_factor = dt * 60

    if vehicle['gear'] == 'DRIVE' and vehicle['speed'] < 0: vehicle['speed'] = min(0, vehicle['speed'] + vehicle['brake_power'] * time_factor)
    elif vehicle['gear'] == 'REVERSE' and vehicle['speed'] > 0: vehicle['speed'] = max(0, vehicle['speed'] - vehicle['brake_power'] * time_factor)
    
    vehicle['speed'] *= (0.98 ** time_factor)
    if abs(vehicle['speed']) < 0.01: vehicle['speed'] = 0
    
    if abs(vehicle['speed']) > 0:
        rad = math.radians(vehicle['angle'])
        dx = math.cos(rad) * vehicle['speed'] * time_factor
        dy = math.sin(rad) * vehicle['speed'] * time_factor
        vehicle['pos'][0] += dx
        vehicle['pos'][1] += dy
        
        if abs(vehicle['speed']) > vehicle['max_speed'] * 0.7:
            add_skid_marks(vehicle['pos'], vehicle['angle'])
    
def update_ai_vehicles(dt):
    time_factor = dt * 60
    for vehicle in moving_vehicles:
        if not vehicle['active']: continue
        target = vehicle['path'][vehicle['path_idx']]
        dx, dy = target[0] - vehicle['pos'][0], target[1] - vehicle['pos'][1]
        distance = math.sqrt(dx*dx + dy*dy)
        if distance < 20:
            vehicle['path_idx'] = (vehicle['path_idx'] + 1) % len(vehicle['path'])
        elif distance > 0:
            vehicle['angle'] = math.degrees(math.atan2(dy, dx))
            rad = math.radians(vehicle['angle'])
            vehicle['pos'][0] += math.cos(rad) * vehicle['speed'] * time_factor
            vehicle['pos'][1] += math.sin(rad) * vehicle['speed'] * time_factor

def update_walkers(dt):
    time_factor = dt * 60
    for walker in walkers:
        if not walker['active']:
            continue
        
        player_distance = distance_2d(walker['pos'], player_vehicle['pos'])

        if player_distance < walker['safety_distance']:
            dx = walker['pos'][0] - player_vehicle['pos'][0]
            dy = walker['pos'][1] - player_vehicle['pos'][1]
            norm = math.sqrt(dx*dx + dy*dy)
            if norm > 0:
                walker['pos'][0] += (dx / norm) * walker['speed'] * 1.5 * time_factor
                walker['pos'][1] += (dy / norm) * walker['speed'] * 1.5 * time_factor
        else:
            if walker['path'] and len(walker['path']) > walker['path_idx']:
                target = walker['path'][walker['path_idx']]
                dx = target[0] - walker['pos'][0]
                dy = target[1] - walker['pos'][1]
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 10:
                    walker['path_idx'] = (walker['path_idx'] + 1) % len(walker['path'])
                elif distance > 0:
                    walker['pos'][0] += dx / distance * walker['speed'] * time_factor
                    walker['pos'][1] += dy / distance * walker['speed'] * time_factor

def check_collisions():
    vehicle_type = vehicle_types[player_vehicle['type']]
    for barrier in static_barriers:
        if distance_2d(player_vehicle['pos'], barrier['pos']) < (vehicle_type['width'] / 2 + barrier['size']):
            handle_collision('OBSTACLE', barrier)
    for vehicle in moving_vehicles:
        if vehicle['active'] and distance_2d(player_vehicle['pos'], vehicle['pos']) < (vehicle_type['width'] / 2 + vehicle_types[vehicle['type']]['width'] / 2):
            handle_collision('CAR', vehicle)
    for walker in walkers:
        if walker['active'] and distance_2d(player_vehicle['pos'], walker['pos']) < (vehicle_type['width'] / 2 + 5):
            handle_collision('PEDESTRIAN', walker)

def handle_collision(collision_type, object_hit):
    if game_status['cheat_mode']: return
    
    damage = abs(player_vehicle['speed']) * 2
    player_vehicle['health'] -= damage
    player_vehicle['damage_level'] += damage
    game_status['collisions'] += 1
    player_vehicle['speed'] *= -0.3
    
    if collision_type == 'PEDESTRIAN':
        object_hit['active'] = False
        for _ in range(15):
            collision_sparks.append({
                'pos': list(player_vehicle['pos']),
                'velocity': [random.uniform(-3, 3), random.uniform(-3, 3), random.uniform(2, 6)],
                'color': [1, 0, 0],
                'life': 60
            })
    elif collision_type == 'OBSTACLE' or collision_type == 'CAR':
        game_status['game_over'] = True

    if player_vehicle['health'] <= 0:
        player_vehicle['health'] = 0
        game_status['game_over'] = True

def check_parking_success():
    if not current_parking_slot or game_status['level_complete']: return
    slot, vehicle, vehicle_type = current_parking_slot, player_vehicle, vehicle_types[player_vehicle['type']]
    vehicle_corners = get_obb_corners(vehicle['pos'], vehicle_type['length'], vehicle_type['width'], vehicle['angle'])
    
    corners_inside = 0
    for corner in vehicle_corners:
        if is_point_inside_obb(corner, slot['pos'], slot['size'][0], slot['size'][1], slot['angle']):
            corners_inside += 1
    
    if corners_inside == 4 and abs(player_vehicle['speed']) < 0.5:
        game_status['level_complete'] = True
        game_status['score'] += max(0, int(1000 + game_status['time_left'] * 10 - game_status['collisions'] * 150))

def add_skid_marks(pos, angle):
    if len(skid_marks) > 100: skid_marks.pop(0)
    rad, offset_rad = math.radians(angle), math.radians(angle + 90)
    width = vehicle_types[player_vehicle['type']]['width'] * 0.4
    for side in [-1, 1]:
        debris_pos = [
            pos[0] - math.cos(offset_rad) * width * side - math.cos(rad) * 20,
            pos[1] - math.sin(offset_rad) * width * side - math.sin(rad) * 20
        ]
        skid_marks.append({'pos': debris_pos, 'life': 120})

def update_rain(dt):
    if weather_types[current_weather_idx] != 'RAIN':
        return
    time_factor = dt * 60
    for drop in rain_drops:
        drop['pos'][2] -= drop['speed'] * time_factor
        if drop['pos'][2] < 0:
            drop['pos'][0] = random.uniform(-WORLD_WIDTH/2, WORLD_WIDTH/2)
            drop['pos'][1] = random.uniform(-WORLD_HEIGHT/2, WORLD_HEIGHT/2)
            drop['pos'][2] = 400

def update_effects(dt):
    time_factor = dt * 60
    for mark in skid_marks[:]:
        mark['life'] -= 1 * time_factor
        if mark['life'] <= 0: skid_marks.remove(mark)
    
    for spark in collision_sparks[:]:
        spark['pos'][0] += spark['velocity'][0] * time_factor
        spark['pos'][1] += spark['velocity'][1] * time_factor
        spark['pos'][2] += spark['velocity'][2] * time_factor
        spark['velocity'][2] -= 0.15 * time_factor
        spark['life'] -= 1 * time_factor
        if spark['life'] <= 0 or spark['pos'][2] < 0:
            collision_sparks.remove(spark)

def reset_level():
    game_status['level'] += 1 if game_status['level_complete'] else 0
    init_level(game_status['level'])
    player_vehicle.update({'pos': [0,-200,5], 'speed': 0, 'angle': 0, 'health': MAX_HEALTH, 'damage_level': 0, 'gear': 'PARK'})
    game_status.update({'time_left': 60, 'collisions': 0, 'level_complete': False, 'game_over': False})
    skid_marks.clear()
    collision_sparks.clear()

def change_vehicle(vehicle_type):
    player_vehicle['type'] = vehicle_type
    vehicle_data = vehicle_types[vehicle_type]
    for key, value in vehicle_data.items():
        if key in player_vehicle:
            player_vehicle[key] = value

def keyboard_listener(key, x, y):
    global current_weather_idx

    if game_status['game_over'] or game_status['level_complete']:
        if key == b'r': reset_level()
        if key == b'n' and game_status['level_complete']: reset_level()
        return
    
    if key == b'p': game_status['paused'] = not game_status['paused']
    if key == b'o': current_weather_idx = (current_weather_idx + 1) % len(weather_types)
    
    if game_status['paused']: return

    vehicle, vehicle_type = player_vehicle, vehicle_types[player_vehicle['type']]
    if key == b'w':
        if vehicle['gear'] == 'DRIVE': vehicle['speed'] = min(vehicle_type['max_speed'], vehicle['speed'] + vehicle_type['acceleration'])
    elif key == b's':
        if vehicle['gear'] == 'DRIVE': vehicle['speed'] = max(0, vehicle['speed'] - vehicle_type['brake_power'])
        elif vehicle['gear'] == 'REVERSE': vehicle['speed'] = max(-vehicle_type['max_speed'] * 0.5, vehicle['speed'] - vehicle_type['acceleration'])
    elif key == b'a':
        if abs(vehicle['speed']) > 0.1: vehicle['angle'] += vehicle_type['turn_rate']
    elif key == b'd':
        if abs(vehicle['speed']) > 0.1: vehicle['angle'] -= vehicle_type['turn_rate']
    elif key == b'g':
        gears = ['DRIVE', 'REVERSE', 'PARK']
        vehicle['gear'] = gears[(gears.index(vehicle['gear']) + 1) % len(gears)]
    elif key == b't':
        game_status['cheat_mode'] = not game_status['cheat_mode']
    elif key == b'c':
        global cam_mode
        cam_mode = (cam_mode + 1) % 3
    elif key in [b'1', b'2', b'3', b'4']:
        vehicle_map = {b'1': 'SEDAN', b'2': 'SUV', b'3': 'SPORTS_CAR', b'4': 'TRUCK'}
        change_vehicle(vehicle_map[key])

def special_key_listener(key, x, y):
    global top_down_cam_height, top_down_cam_angle
    if cam_mode == 0:
        if key == GLUT_KEY_UP:
            top_down_cam_height += 20
        elif key == GLUT_KEY_DOWN:
            top_down_cam_height = max(50, top_down_cam_height - 20)
        elif key == GLUT_KEY_LEFT:
            top_down_cam_angle -= 5
        elif key == GLUT_KEY_RIGHT:
            top_down_cam_angle += 5

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 1.0, 4000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    vehicle_pos = player_vehicle['pos']
    vehicle_angle_rad = math.radians(player_vehicle['angle'])

    if cam_mode == 0:
        cam_x = top_down_cam_radius * math.cos(math.radians(top_down_cam_angle))
        cam_y = top_down_cam_radius * math.sin(math.radians(top_down_cam_angle))
        gluLookAt(cam_x, cam_y, top_down_cam_height,
                  0, 0, 0,
                  0, 0, 1)

    elif cam_mode == 1:
        cam_dist = 120
        cam_height = 60
        cam_x = vehicle_pos[0] - math.cos(vehicle_angle_rad) * cam_dist
        cam_y = vehicle_pos[1] - math.sin(vehicle_angle_rad) * cam_dist
        gluLookAt(cam_x, cam_y, cam_height, 
                  vehicle_pos[0], vehicle_pos[1], vehicle_pos[2] + 10, 
                  0, 0, 1)

    elif cam_mode == 2:
        cam_height = 15
        look_dist = 100
        cam_x = vehicle_pos[0] + math.cos(vehicle_angle_rad) * 10
        cam_y = vehicle_pos[1] + math.sin(vehicle_angle_rad) * 10
        look_x = vehicle_pos[0] + math.cos(vehicle_angle_rad) * look_dist
        look_y = vehicle_pos[1] + math.sin(vehicle_angle_rad) * look_dist
        gluLookAt(cam_x, cam_y, vehicle_pos[2] + cam_height,
                  look_x, look_y, vehicle_pos[2] + cam_height,
                  0, 0, 1)

def idle():
    global last_frame_time
    current_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    if last_frame_time == 0: last_frame_time = current_time
    delta_time = current_time - last_frame_time
    last_frame_time = current_time

    if not game_status['paused'] and not game_status['game_over']:
        if not game_status['level_complete']: game_status['time_left'] -= delta_time
        if game_status['time_left'] <= 0: game_status['game_over'] = True
        
        update_vehicle_physics(delta_time)
        update_ai_vehicles(delta_time)
        update_walkers(delta_time)
        update_effects(delta_time)
        update_rain(delta_time)
        
        if not game_status['level_complete']:
            check_collisions()
            check_parking_success()
    
    glutPostRedisplay()

def show_screen():
    weather = weather_types[current_weather_idx]
    if weather == 'NIGHT':
        glClearColor(0.05, 0.05, 0.15, 1.0)
    elif weather == 'RAIN':
        glClearColor(0.25, 0.3, 0.35, 1.0)
    else:
        glClearColor(0.4, 0.6, 0.9, 1.0)
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    setup_camera()
    
    draw_environment()
    draw_parking_slot()
    draw_skid_marks()
    draw_collision_sparks()
    draw_rain()

    for barrier in static_barriers: draw_obstacle(barrier)
    for vehicle in moving_vehicles:
        if vehicle['active']: draw_vehicle(vehicle)
    for walker in walkers:
        if walker['active']: draw_walker(walker)
    
    if cam_mode != 2:
        draw_vehicle(player_vehicle, True)
    
    draw_hud()
    
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"3D Car Parking Challenge")
    
    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard_listener)
    glutIdleFunc(idle)
    glutSpecialFunc(special_key_listener)
    
    init_level(1)
    
    glutMainLoop()

if __name__ == "__main__":
    main()