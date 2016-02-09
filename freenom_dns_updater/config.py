import yaml


class Config(dict):
    def __init__(self, file="freenom.yml", **kwargs):
        super().__init__(**kwargs)
        self.file = file
        self.reload(file)

    def reload(self, file):
        with open(file) as f:
            content = yaml.load(f)
        self.update(content)

    def save(self):
        with open(self.file, 'w') as f:
            yaml.dump(self, f)

    @property
    def login(self):
        return self['login']

    @property
    def password(self):
        return self['password']
