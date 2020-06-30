import sys
import argparse
import quickfix
from application import Application

def main(config_file):
    try:
        settings = quickfix.SessionSettings(config_file)
        application = Application()
        storefactory = quickfix.FileStoreFactory(settings)
        logfactory = quickfix.FileLogFactory(settings)
        initiator = quickfix.SocketInitiator(application, storefactory, settings, logfactory)

        initiator.start()
        application.run()
        initiator.stop()

    except (KeyError, KeyboardInterrupt, quickfix.ConfigError, quickfix.RuntimeError) as e:
        print(e)
        initiator.stop()
        sys.exit(-1)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='FIX Client')
    parser.add_argument('-cfg', default='client.cfg', type=str, help='Name of configuration file')
    args = parser.parse_args()
    main(args.cfg)
