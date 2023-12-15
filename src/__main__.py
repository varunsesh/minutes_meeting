from src import ui_manager, audio_utils
import sys, logging, os
from PyQt5.QtWidgets import QApplication
from dotenv import load_dotenv

def setup_logging():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=os.path.join(log_dir, 'Minutes.log'),
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    # console handler to print the logs
    
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.INFO)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # console_handler.setFormatter(formatter)
    # logging.getLogger('').addHandler(console_handler)

def main():
    '''This function initializes the main window of the application'''

    load_dotenv()
    setup_logging()
    
    logging.info("Starting the recorder app...")
    try :
        app = QApplication(sys.argv)
        audio_utils.audio_setup()
        ui = ui_manager.UIManager()
        ui.show()
        sys.exit(app.exec_())
    except Exception as e :
        logging.error("Exception Failed to initialize application", e)

    
if __name__ == "__main__":
    main()