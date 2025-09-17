#!/usr/bin/env python3
from pachacutin_unified.server import create_app
from pachacutin_unified.manager import ModuleManager
from pachacutin_unified import config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def main():
    mgr = ModuleManager()
    app = create_app(mgr)
    app.module_manager = mgr
    logging.info(f"Starting unified server on 0.0.0.0:{config.HTTP_PORT}")
    app.run(host='0.0.0.0', port=config.HTTP_PORT)

if __name__ == '__main__':
    main()
