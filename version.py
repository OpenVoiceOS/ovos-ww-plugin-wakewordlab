VERSION_MAJOR = 0
VERSION_MINOR = 0
VERSION_BUILD = 1
VERSION_ALPHA = 0

__version__ = "{}.{}.{}{}".format(VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD,
                                   "a{}".format(VERSION_ALPHA) if VERSION_ALPHA else "")

if __name__ == "__main__":
    print(__version__)
# START_VERSION_BLOCK
VERSION_MAJOR = 0
VERSION_MINOR = 0
VERSION_BUILD = 1
VERSION_ALPHA = 1
# END_VERSION_BLOCKVERSION_MAJOR = 0
VERSION_MINOR = 0
VERSION_BUILD = 1
VERSION_ALPHA = 0

__version__ = "{}.{}.{}{}".format(VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD,
                                   "a{}".format(VERSION_ALPHA) if VERSION_ALPHA else "")

if __name__ == "__main__":
    print(__version__)
