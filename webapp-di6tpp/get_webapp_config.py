
import toml

config = None
def get_config():
    global config
    
    if config is not None:
        return config
    try:
        config = toml.load("config.toml")
    except FileNotFoundError:
        print("Configuration file 'config.toml' not found. Exiting.")
        exit(1)
    return config

def get_config_value(key):
    return get_config().get(key)

def get_webapp_config():
    return get_config_value("webapp")