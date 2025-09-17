#!/usr/bin/env python3
from pachacutin_gateway.server import create_app
from pachacutin_gateway.serial_writer import SerialWriter
from pachacutin_gateway import config
import queue
import threading

def main():
    q = queue.Queue()
    app = create_app()
    # inyecta la cola en app para que los handlers puedan usarla
    app.serial_queue = q
    # crea y arranca el escritor serial en background
    writer = SerialWriter(cmd_queue=q,
                          serial_path=config.SERIAL_PATH,
                          baud=config.BAUD,
                          reconnect_sleep=config.SERIAL_RECONNECT_S)
    writer.start()
    print(f"Starting Flask on 0.0.0.0:{config.HTTP_PORT}")
    app.run(host='0.0.0.0', port=config.HTTP_PORT)

if __name__ == '__main__':
    main()
