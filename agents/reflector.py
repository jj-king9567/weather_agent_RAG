class ReflectorAgent:
    def __init__(self):
        self.name = "质检员"

    def check(self, answer):
        print(f"[{self.name}] 正在检查答案是否靠谱...")
        if answer:
            return True
        return False