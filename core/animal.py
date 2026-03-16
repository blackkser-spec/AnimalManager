class Animal:
    def __init__(self, id, name, type_en=None, type_jp=None, ability=None, ex_ability=None, voice_msg=None):
        self.id          = id
        self.name        = name
        self.type_en     = type_en        
        self.type_jp     = type_jp
        self.ability     = ability or {}
        self.ex_ability  = ex_ability or {}
        self.voice_msg   = voice_msg

    def get_all_ability(self):
        combined = dict(self.ability)
        combined.update(self.ex_ability)
        return combined

    def has_ability(self, ability_name):
        if ability_name not in self.get_all_ability():
            return False
        return True
    
    def voice(self):
        return f"{self.name} は{self.voice_msg}"

    def fly(self):
        fly_data = self.get_all_ability().get("fly")
        if fly_data:
            return f"{self.name} は{fly_data['msg']}"
        return None
    def swim(self):
        swim_data = self.get_all_ability().get("swim")
        if swim_data:
            return f"{self.name} は{swim_data['msg']}"
        return None

class Bird(Animal):
    def __init__(self, id, name):
        super().__init__(id, name, type_en="bird", type_jp="鳥",
                         ability  ={"fly":{"msg": "空高く飛んでいる"}},
                         voice_msg="チュンチュンと鳴いた")

class Cat(Animal):
    def __init__(self, id, name):
        super().__init__(id, name, type_en="cat", type_jp="猫",
                         voice_msg="ニャアと鳴いた")

class Dog(Animal):
    def __init__(self, id, name):
        super().__init__(id, name, type_en="dog", type_jp="犬",
                         voice_msg="ワンワンと吠えた")

class Duck(Animal):
    def __init__(self, id, name):
        super().__init__(id, name, type_en="duck", type_jp="アヒル",
                         ability={"fly":{"msg":"低空を飛んでいる"},
                                  "swim":{"msg":"水面を漂うように泳いでいる"}},
                         voice_msg="ガアガアと鳴いた")

class Fish(Animal):
    def __init__(self, id, name):
        super().__init__(id, name, type_en="fish", type_jp="魚",
                         ability={"swim":{"msg":"静かに水中を泳いでいる"}},
                         voice_msg="静かにしている")

class Penguin(Animal):
    def __init__(self, id, name):
        super().__init__(id, name, type_en="penguin", type_jp="ペンギン",
                         ability={"swim":{"msg":"水中を泳いでいる"}},
                         voice_msg="ぷーぷーと鳴いた")