#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import pygame
import sys
import threading
import math

BLACK = (0, 0, 0)
CYAN = (0, 255, 255)

class RobotFaceNode(Node):
    def __init__(self):
        super().__init__('robot_face_node')

def pygame_loop(node):
    pygame.init()
    pygame.mouse.set_visible(True) 
    
    # Chạy Fullscreen thực sự để NUỐT CHỬNG thanh Taskbar của Ubuntu khi mở
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    clock = pygame.time.Clock()

    left_eye_pos = (SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2 - int(SCREEN_HEIGHT * 0.05))
    right_eye_pos = ((SCREEN_WIDTH // 3) * 2, SCREEN_HEIGHT // 2 - int(SCREEN_HEIGHT * 0.05))
    mouth_rect_box = (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - int(SCREEN_HEIGHT * 0.42), 200, 100)

    eye_blink_counter = 0
    max_eye_height = int(SCREEN_HEIGHT * 0.18)
    eye_height = max_eye_height
    eye_width = int(SCREEN_WIDTH * 0.11)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()

            # 🌟 CHẠM 1 LẦN VÀO MẶT: Tắt ứng dụng hoàn toàn để lộ Ubuntu sạch sẽ không còn icon Taskbar
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)
        eye_blink_counter += 1
        if eye_blink_counter > 120:
            eye_height -= int(max_eye_height * 0.2)
            if eye_height <= 5: eye_blink_counter = 0
        else:
            if eye_height < max_eye_height: eye_height += int(max_eye_height * 0.2)

        pygame.draw.ellipse(screen, CYAN, (left_eye_pos[0] - eye_width//2, left_eye_pos[1] - eye_height//2, eye_width, eye_height))
        pygame.draw.ellipse(screen, CYAN, (right_eye_pos[0] - eye_width//2, right_eye_pos[1] - eye_height//2, eye_width, eye_height))
        pygame.draw.arc(screen, CYAN, mouth_rect_box, math.pi, 2 * math.pi, int(SCREEN_HEIGHT * 0.015))

        pygame.display.flip()
        clock.tick(30)

def main(args=None):
    rclpy.init(args=args)
    node = RobotFaceNode()
    threading.Thread(target=pygame_loop, args=(node,), daemon=True).start()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()