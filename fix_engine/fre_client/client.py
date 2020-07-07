import sys
import argparse
import quickfix
import application

def main(config_file):
    try:
        settings = quickfix.SessionSettings(config_file)
        app = application.Application(quickfix.Session)
        storefactory = quickfix.FileStoreFactory(settings)
        logfactory = quickfix.FileLogFactory(settings)
        initiator = quickfix.SocketInitiator(app, storefactory, settings, logfactory)

        initiator.start()
        app.run()
        initiator.stop()

    except (KeyError, KeyboardInterrupt, quickfix.ConfigError, quickfix.RuntimeError) as e:
        print(e)
        sys.exit(-1)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='FIX Client')
    parser.add_argument('-cfg', default='client.cfg', type=str, help='Name of configuration file')
    args = parser.parse_args()
    main(args.cfg)
