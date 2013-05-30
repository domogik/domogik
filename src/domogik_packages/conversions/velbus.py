class velbusConversions():
    @staticmethod
    def from_DT_Switch_to_level(x):
        if x == '1':
            return 255
        else:
            return 0

    @staticmethod
    def from_level_to_DT_Scaling(x):
        # 0 - 255 translated to 0 - 100
        return round(int(x) / 255 * 100)
