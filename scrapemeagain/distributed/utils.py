def get_class_from_path(path):
    """
    Get class

    :argument path: dotted path to the target class
    :type path: str

    :returns: class
    """
    module_path, class_name = path.rsplit('.', 1)
    module = __import__(module_path, fromlist=[class_name])

    return getattr(module, class_name)
